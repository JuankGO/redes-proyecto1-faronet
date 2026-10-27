/**
 * Worker de FaroNet: aplicacion publica en el edge (RFC, seccion 5).
 *
 * Rutas:
 *   POST /api/relay          (firma del gateway)  publica un mensaje en una sala
 *   POST /api/directorio     (firma del gateway)  sube entradas del directorio
 *   GET  /directorio                              replica de solo lectura, con firmas
 *   GET  /sala/{tema}                             pagina de la sala en tiempo real
 *   GET  /sala/{tema}/ws                          WebSocket de solo lectura
 *   GET  /feed/{tema}.atom                        feed Atom del tema
 *   PUT  /buzon/{id}  GET /buzon/{id}             buzon muerto (blobs de 1024 B)
 *
 * Politica de no registro: este codigo no guarda ni escribe en bitacoras
 * CF-Connecting-IP, User-Agent ni ningun otro identificador. La IP solo se
 * usa en memoria como clave del limite de peticiones.
 */
import { DurableObject } from "cloudflare:workers";

export interface Env {
	DB: D1Database;
	SALA: DurableObjectNamespace<Sala>;
	LIMITE?: RateLimit;
	GATEWAY_PUB?: string;
}

// ----- Constantes del protocolo -----

const VENTANA_FIRMA = 60; // segundos de tolerancia del reloj del gateway
const VIDA_NONCE = 120; // segundos que se recuerdan los nonces
const VIDA_MENSAJE = 7 * 86400; // los mensajes publicos viven 7 dias
const VIDA_BLOB = 86400; // el buzon guarda 24 horas
const TAMANO_BLOB = 1024; // tamano fijo de los blobs
const MAX_TEXTO = 240; // bytes UTF-8 del texto publico
const MAX_CUERPO = 256 * 1024; // tamano maximo de una peticion del gateway
const MAX_ENTRADAS = 500;
const TTL_MAXIMO_ENTRADA = 86400;
const TOLERANCIA_RELOJ = 300;
const HISTORIAL_SALA = 20;
const RE_TEMA = /^[\p{L}\p{N}_-]{1,32}$/u;
const RE_HEX64 = /^[0-9a-f]{64}$/;
const RE_HEX32 = /^[0-9a-f]{32}$/;
const RE_HEX128 = /^[0-9a-f]{128}$/;

// ----- Utilidades -----

const ahora = () => Math.floor(Date.now() / 1000);

function texto(cuerpo: string, status = 200, extra: Record<string, string> = {}): Response {
	return new Response(cuerpo, {
		status,
		headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store", ...extra },
	});
}

function json(datos: unknown, status = 200): Response {
	return new Response(JSON.stringify(datos), {
		status,
		headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
	});
}

function hexABytes(hex: string): Uint8Array {
	const salida = new Uint8Array(hex.length / 2);
	for (let i = 0; i < salida.length; i++) salida[i] = parseInt(hex.substr(i * 2, 2), 16);
	return salida;
}

function bytesAHex(b: ArrayBuffer | Uint8Array): string {
	return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
}

export function escaparXml(s: string): string {
	return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" })[c]!);
}

const largoUtf8 = (s: string) => new TextEncoder().encode(s).length;

async function verificarEd25519(pubHex: string, firmaHex: string, datos: Uint8Array): Promise<boolean> {
	if (!RE_HEX64.test(pubHex) || !RE_HEX128.test(firmaHex)) return false;
	try {
		const llave = await crypto.subtle.importKey("raw", hexABytes(pubHex), { name: "Ed25519" }, false, ["verify"]);
		return await crypto.subtle.verify({ name: "Ed25519" }, llave, hexABytes(firmaHex), datos);
	} catch {
		return false;
	}
}

/** JSON canonico igual al de Python: claves ordenadas, sin espacios, solo ASCII. */
export function jsonCanonico(valor: unknown): string {
	if (valor === null || typeof valor !== "object") {
		let salida = "";
		for (const c of JSON.stringify(valor)) {
			// Igual que ensure_ascii de Python: todo lo que no es ASCII va como \\uXXXX.
			for (let k = 0; k < c.length; k++) {
				const codigo = c.charCodeAt(k);
				salida += codigo < 0x80 ? c[k] : "\\u" + codigo.toString(16).padStart(4, "0");
			}
		}
		return salida;
	}
	if (Array.isArray(valor)) return "[" + valor.map(jsonCanonico).join(",") + "]";
	const obj = valor as Record<string, unknown>;
	return "{" + Object.keys(obj).sort().map((k) => jsonCanonico(k) + ":" + jsonCanonico(obj[k])).join(",") + "}";
}

// ----- Limite de peticiones (en memoria) -----

async function limitar(env: Env, request: Request, grupo: string): Promise<Response | null> {
	if (!env.LIMITE) return null;
	const cliente = request.headers.get("CF-Connecting-IP") ?? "local";
	const { success } = await env.LIMITE.limit({ key: `${grupo}:${cliente}` });
	return success ? null : texto("Demasiadas peticiones", 429, { "retry-after": "60" });
}

// ----- Autenticacion del gateway -----

async function autenticarGateway(env: Env, request: Request, ruta: string, cuerpo: Uint8Array): Promise<string | null> {
	const pub = (env.GATEWAY_PUB ?? "").trim().toLowerCase();
	if (!RE_HEX64.test(pub)) return "el Worker no tiene GATEWAY_PUB configurado";
	const ts = request.headers.get("X-FaroNet-Ts") ?? "";
	const nonce = (request.headers.get("X-FaroNet-Nonce") ?? "").toLowerCase();
	const firma = (request.headers.get("X-FaroNet-Firma") ?? "").toLowerCase();
	if (!/^\d{1,12}$/.test(ts) || !RE_HEX32.test(nonce) || !RE_HEX128.test(firma)) return "encabezados de firma ausentes o invalidos";
	if (Math.abs(ahora() - Number(ts)) > VENTANA_FIRMA) return "marca de tiempo fuera de la ventana";
	const resumen = bytesAHex(await crypto.subtle.digest("SHA-256", cuerpo));
	const mensaje = new TextEncoder().encode(["FARONET-GW-1", request.method.toUpperCase(), ruta, ts, nonce, resumen].join("\n"));
	if (!(await verificarEd25519(pub, firma, mensaje))) return "firma invalida";
	// El nonce se guarda despues de verificar la firma: un atacante no puede llenar la tabla.
	const r = await env.DB.prepare("INSERT INTO nonces (nonce, expira) VALUES (?, ?) ON CONFLICT(nonce) DO NOTHING")
		.bind(nonce, ahora() + VIDA_NONCE)
		.run();
	if (!r.meta.changes) return "nonce repetido";
	return null;
}

async function leerCuerpo(request: Request): Promise<Uint8Array | null> {
	const largo = Number(request.headers.get("content-length") ?? "0");
	if (largo > MAX_CUERPO) return null;
	const datos = new Uint8Array(await request.arrayBuffer());
	return datos.length > MAX_CUERPO ? null : datos;
}

function parsearJson(datos: Uint8Array): any {
	try {
		return JSON.parse(new TextDecoder("utf-8", { fatal: true, ignoreBOM: false }).decode(datos));
	} catch {
		return undefined;
	}
}

// ----- Validacion de entradas del directorio (RFC 3.3) -----

const RE_UDP = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3}):(\d{1,5})$/;

export function entradaValida(e: any, momento = ahora()): boolean {
	if (!e || typeof e !== "object" || Array.isArray(e)) return false;
	for (const k of ["v", "id", "cifrado", "canal", "direccion", "creado", "ttl"]) if (!(k in e)) return false;
	if (!Number.isInteger(e.v) || e.v !== 1) return false;
	if (!RE_HEX64.test(e.id) || !RE_HEX64.test(e.cifrado)) return false;
	if (e.canal === "udp") {
		const m = RE_UDP.exec(e.direccion ?? "");
		if (!m || m.slice(1, 5).some((o) => Number(o) > 255) || !(Number(m[5]) > 0 && Number(m[5]) < 65536)) return false;
	} else if (e.canal === "faro") {
		if (!/^[0-9a-f]{8}$/.test(e.direccion ?? "") || e.direccion === "00000000" || e.direccion === "ffffffff") return false;
	} else return false;
	if (!Number.isInteger(e.creado) || !Number.isInteger(e.ttl)) return false;
	if (e.ttl <= 0 || e.ttl > TTL_MAXIMO_ENTRADA) return false;
	if (e.creado > momento + TOLERANCIA_RELOJ || momento >= e.creado + e.ttl) return false;
	if ("rol" in e && e.rol !== "gateway") return false;
	return true;
}

// ----- Rutas -----

async function apiRelay(request: Request, env: Env): Promise<Response> {
	const cuerpo = await leerCuerpo(request);
	if (!cuerpo) return texto("Cuerpo demasiado grande", 413);
	const error = await autenticarGateway(env, request, "/api/relay", cuerpo);
	if (error) return texto(`No autorizado: ${error}`, 401);
	const b = parsearJson(cuerpo);
	if (!b || typeof b !== "object") return texto("JSON invalido", 400);
	if (b.v !== undefined && b.v !== 1) return texto("Version no soportada", 400);
	if (typeof b.tema !== "string" || !RE_TEMA.test(b.tema)) return texto("Tema invalido: 1-32 letras, numeros, _ o -", 400);
	if (typeof b.texto !== "string" || !b.texto || largoUtf8(b.texto) > MAX_TEXTO) return texto(`Texto invalido: 1-${MAX_TEXTO} bytes`, 400);
	const momento = ahora();
	const hora = Number.isInteger(b.hora) && Math.abs(b.hora - momento) < 3600 ? b.hora : momento;
	const r = await env.DB.prepare("INSERT INTO mensajes (tema, texto, creado, expira) VALUES (?, ?, ?, ?)")
		.bind(b.tema, b.texto, hora, momento + VIDA_MENSAJE)
		.run();
	const sala = env.SALA.get(env.SALA.idFromName(b.tema));
	await sala.publicar({ id: r.meta.last_row_id, tema: b.tema, texto: b.texto, hora });
	return texto("OK");
}

async function apiDirectorio(request: Request, env: Env): Promise<Response> {
	const cuerpo = await leerCuerpo(request);
	if (!cuerpo) return texto("Cuerpo demasiado grande", 413);
	const error = await autenticarGateway(env, request, "/api/directorio", cuerpo);
	if (error) return texto(`No autorizado: ${error}`, 401);
	const b = parsearJson(cuerpo);
	if (!b || !Array.isArray(b.entradas)) return texto("Se esperaba {entradas: [...]}", 400);
	const momento = ahora();
	let aceptadas = 0;
	const sentencias: D1PreparedStatement[] = [];
	for (const item of b.entradas.slice(0, MAX_ENTRADAS)) {
		const e = item?.entrada;
		const firma = item?.firma;
		if (!entradaValida(e, momento) || typeof firma !== "string") continue;
		// La firma se verifica en el edge: un gateway malicioso no puede inventar entradas.
		if (!(await verificarEd25519(e.id, firma, new TextEncoder().encode(jsonCanonico(e))))) continue;
		sentencias.push(
			env.DB.prepare(
				"INSERT INTO directorio (nodo, entrada, firma, expira) VALUES (?, ?, ?, ?) " +
					"ON CONFLICT(nodo) DO UPDATE SET entrada = excluded.entrada, firma = excluded.firma, expira = excluded.expira " +
					"WHERE json_extract(excluded.entrada, '$.creado') >= json_extract(directorio.entrada, '$.creado')",
			).bind(e.id, JSON.stringify(e), firma, e.creado + e.ttl),
		);
		aceptadas++;
	}
	if (sentencias.length) await env.DB.batch(sentencias);
	return json({ aceptadas, rechazadas: Math.min(b.entradas.length, MAX_ENTRADAS) - aceptadas });
}

async function verDirectorio(env: Env): Promise<Response> {
	const { results } = await env.DB.prepare("SELECT entrada, firma FROM directorio WHERE expira > ? ORDER BY nodo").bind(ahora()).all();
	return json({ v: 1, entradas: results.map((r) => ({ entrada: JSON.parse(r.entrada as string), firma: r.firma })) });
}

async function feed(tema: string, url: URL, env: Env): Promise<Response> {
	const { results } = await env.DB.prepare(
		"SELECT id, texto, creado FROM mensajes WHERE tema = ? AND expira > ? ORDER BY creado DESC, id DESC LIMIT 20",
	)
		.bind(tema, ahora())
		.all();
	const t = escaparXml(tema);
	const fecha = (s: number) => new Date(s * 1000).toISOString();
	const actualizado = results.length ? fecha(Number(results[0].creado)) : fecha(ahora());
	const base = escaparXml(`${url.origin}/feed/${encodeURIComponent(tema)}.atom`);
	let xml =
		`<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">\n` +
		`  <id>urn:faronet:tema:${t}</id>\n  <title>FaroNet: ${t}</title>\n  <updated>${actualizado}</updated>\n` +
		`  <author><name>FaroNet</name></author>\n  <link rel="self" href="${base}"/>\n`;
	for (const r of results) {
		const contenido = escaparXml(String(r.texto));
		const titulo = escaparXml(String(r.texto).slice(0, 60));
		xml +=
			`  <entry>\n    <id>urn:faronet:mensaje:${Number(r.id)}</id>\n    <title>${titulo}</title>\n` +
			`    <updated>${fecha(Number(r.creado))}</updated>\n    <content type="text">${contenido}</content>\n  </entry>\n`;
	}
	xml += "</feed>\n";
	return new Response(xml, { headers: { "content-type": "application/atom+xml; charset=utf-8", "cache-control": "no-store" } });
}

async function buzon(request: Request, id: string, env: Env): Promise<Response> {
	if (!RE_HEX64.test(id)) return texto("Identificador invalido: 64 caracteres hex", 400);
	if (request.method === "PUT") {
		const largo = Number(request.headers.get("content-length") ?? "-1");
		if (largo > TAMANO_BLOB) return texto(`El blob debe medir ${TAMANO_BLOB} bytes`, 413);
		const blob = new Uint8Array(await request.arrayBuffer());
		if (blob.length !== TAMANO_BLOB) return texto(`El blob debe medir ${TAMANO_BLOB} bytes`, 413);
		await env.DB.prepare("INSERT OR REPLACE INTO buzon (id, blob, expira) VALUES (?, ?, ?)").bind(id, blob, ahora() + VIDA_BLOB).run();
		return texto("Guardado", 201);
	}
	if (request.method === "GET") {
		// Se lee y se borra en la misma operacion.
		const r = await env.DB.prepare("DELETE FROM buzon WHERE id = ? RETURNING blob, expira").bind(id).first();
		if (!r || Number(r.expira) <= ahora()) return texto("No encontrado", 404);
		return new Response(new Uint8Array(r.blob as ArrayBuffer), {
			headers: { "content-type": "application/octet-stream", "cache-control": "no-store" },
		});
	}
	return texto("Metodo no permitido", 405, { allow: "GET, PUT" });
}

const CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'";

function paginaSala(tema: string): Response {
	const t = escaparXml(tema);
	const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sala ${t}</title><style>
:root{--bg:#fff;--fg:#111;--m:#666;--l:#ddd}@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eee;--m:#aaa;--l:#333}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif}main{max-width:720px;margin:0 auto;padding:16px}
h1{font-size:22px;margin:0 0 4px}p{color:var(--m);margin:0 0 16px}ul{list-style:none;padding:0;margin:0}
li{border-top:1px solid var(--l);padding:10px 0}time{color:var(--m);font-size:13px;display:block}#estado{font-size:13px}</style></head>
<body><main><h1>Sala pública: ${t}</h1><p>Mensajes publicados desde FaroNet en tiempo real. <a href="/feed/${encodeURIComponent(tema)}.atom">Feed Atom</a> · <span id="estado">conectando…</span></p>
<ul id="lista"></ul></main><script>
const lista=document.getElementById("lista"),estado=document.getElementById("estado");
function agregar(m){const li=document.createElement("li"),t=document.createElement("time"),d=document.createElement("div");
t.textContent=new Date(m.hora*1000).toLocaleString();d.textContent=m.texto;li.append(t,d);lista.prepend(li);}
function conectar(){const ws=new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+location.pathname.replace(/\\/$/,"")+"/ws");
ws.onopen=()=>estado.textContent="en vivo";ws.onclose=()=>{estado.textContent="reconectando…";setTimeout(conectar,3000);};
ws.onmessage=e=>{try{const d=JSON.parse(e.data);(d.historial||[d]).slice().reverse().forEach(agregar);}catch(_){}};}
conectar();</script></body></html>`;
	return new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "content-security-policy": CSP, "cache-control": "no-store" } });
}

function paginaInicio(): Response {
	const html = `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FaroNet</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:720px;margin:0 auto;padding:16px}code{font-size:14px}</style></head><body>
<h1>FaroNet</h1><p>Aplicación pública de FaroNet en el edge.</p><ul>
<li><code>GET /sala/{tema}</code>: sala en tiempo real</li><li><code>GET /feed/{tema}.atom</code>: feed Atom</li>
<li><code>GET /directorio</code>: directorio público de nodos con firmas</li><li><code>PUT|GET /buzon/{id}</code>: buzón muerto</li></ul></body></html>`;
	return new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "content-security-policy": CSP } });
}

function decodificarTema(segmento: string): string | null {
	try {
		const t = decodeURIComponent(segmento);
		return RE_TEMA.test(t) ? t : null;
	} catch {
		return null;
	}
}

async function enrutar(request: Request, env: Env): Promise<Response> {
	const url = new URL(request.url);
	const partes = url.pathname.split("/").filter(Boolean);
	const metodo = request.method;

	if (partes[0] === "api") {
		const limitado = await limitar(env, request, "gw");
		if (limitado) return limitado;
		if (metodo !== "POST") return texto("Metodo no permitido", 405, { allow: "POST" });
		if (url.pathname === "/api/relay") return apiRelay(request, env);
		if (url.pathname === "/api/directorio") return apiDirectorio(request, env);
		return texto("No encontrado", 404);
	}

	const limitado = await limitar(env, request, "pub");
	if (limitado) return limitado;

	if (partes[0] === "buzon" && partes.length === 2) return buzon(request, partes[1].toLowerCase(), env);
	if (metodo !== "GET") return texto("Metodo no permitido", 405, { allow: "GET" });
	if (partes.length === 0) return paginaInicio();
	if (partes[0] === "directorio" && partes.length === 1) return verDirectorio(env);
	if (partes[0] === "feed" && partes.length === 2 && partes[1].endsWith(".atom")) {
		const tema = decodificarTema(partes[1].slice(0, -".atom".length));
		return tema ? feed(tema, url, env) : texto("Tema invalido", 400);
	}
	if (partes[0] === "sala" && (partes.length === 2 || (partes.length === 3 && partes[2] === "ws"))) {
		const tema = decodificarTema(partes[1]);
		if (!tema) return texto("Tema invalido", 400);
		if (partes.length === 2) return paginaSala(tema);
		if (request.headers.get("Upgrade")?.toLowerCase() !== "websocket") return texto("Se esperaba WebSocket", 426);
		const sala = env.SALA.get(env.SALA.idFromName(tema));
		return sala.fetch(new Request(`https://sala/ws?tema=${encodeURIComponent(tema)}`, request));
	}
	return texto("No encontrado", 404);
}

// ----- Sala (Durable Object) -----

export class Sala extends DurableObject<Env> {
	async fetch(request: Request): Promise<Response> {
		const url = new URL(request.url);
		if (url.pathname !== "/ws" || request.headers.get("Upgrade")?.toLowerCase() !== "websocket") {
			return texto("No encontrado", 404);
		}
		const tema = url.searchParams.get("tema") ?? "";
		const par = new WebSocketPair();
		const [cliente, servidor] = Object.values(par);
		this.ctx.acceptWebSocket(servidor);
		const { results } = await this.env.DB.prepare(
			"SELECT id, texto, creado FROM mensajes WHERE tema = ? AND expira > ? ORDER BY creado DESC, id DESC LIMIT ?",
		)
			.bind(tema, ahora(), HISTORIAL_SALA)
			.all();
		servidor.send(JSON.stringify({ historial: results.map((r) => ({ id: r.id, tema, texto: r.texto, hora: r.creado })) }));
		return new Response(null, { status: 101, webSocket: cliente });
	}

	/** Lo llama el Worker (RPC) cuando el gateway publica: se reenvia a todos. */
	async publicar(mensaje: { id: unknown; tema: string; texto: string; hora: number }): Promise<number> {
		const datos = JSON.stringify(mensaje);
		let enviados = 0;
		for (const ws of this.ctx.getWebSockets()) {
			try {
				ws.send(datos);
				enviados++;
			} catch {
				/* conexion cerrada */
			}
		}
		return enviados;
	}

	/** Los navegadores son solo de lectura: lo que manden se ignora. */
	async webSocketMessage(_ws: WebSocket, _msg: string | ArrayBuffer): Promise<void> {}

	async webSocketClose(ws: WebSocket, code: number): Promise<void> {
		try {
			ws.close(code === 1005 ? 1000 : code, "cerrado");
		} catch {
			/* ya cerrado */
		}
	}
}

// ----- Limpieza de vencidos (cron) -----

export async function limpiar(env: Env): Promise<void> {
	const t = ahora();
	await env.DB.batch([
		env.DB.prepare("DELETE FROM mensajes WHERE expira <= ?").bind(t),
		env.DB.prepare("DELETE FROM buzon WHERE expira <= ?").bind(t),
		env.DB.prepare("DELETE FROM directorio WHERE expira <= ?").bind(t),
		env.DB.prepare("DELETE FROM nonces WHERE expira <= ?").bind(t),
	]);
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		try {
			return await enrutar(request, env);
		} catch {
			// Sin console.log: no se registra nada del cliente.
			return texto("Error interno", 500);
		}
	},
	async scheduled(_evento: ScheduledController, env: Env, _ctx?: ExecutionContext): Promise<void> {
		await limpiar(env);
	},
} satisfies ExportedHandler<Env>;
