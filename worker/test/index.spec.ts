import { SELF, env, createScheduledController, createExecutionContext, waitOnExecutionContext } from "cloudflare:test";
import { describe, it, expect, beforeAll } from "vitest";
import worker, { entradaValida, escaparXml, jsonCanonico } from "../src/index";

// Llave privada de prueba del gateway (semilla 00 01 ... 1f). Su publica esta en vitest.config.mts.
const JWK_GATEWAY = {
	kty: "OKP",
	crv: "Ed25519",
	d: "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8",
	x: "A6EHv_POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg",
};

// Entrada firmada por Python (mesh/directorio.py) para comprobar que ambos lados
// producen el mismo JSON canonico y verifican la misma firma.
const ENTRADA_PY = {
	v: 1,
	id: "29acbae141bccaf0b22e1a94d34d0bc7361e526d0bfe12c89794bc9322966dd7",
	cifrado: "79a631eede1bf9c98f12032cdeadd0e7a079398fc786b88cc846ec89af85a51a",
	canal: "udp",
	direccion: "10.0.0.5:6001",
	creado: 1760000000,
	ttl: 3600,
	rol: "gateway",
	nota: "cañón",
};
const CANON_PY =
	'{"canal":"udp","cifrado":"79a631eede1bf9c98f12032cdeadd0e7a079398fc786b88cc846ec89af85a51a","creado":1760000000,' +
	'"direccion":"10.0.0.5:6001","id":"29acbae141bccaf0b22e1a94d34d0bc7361e526d0bfe12c89794bc9322966dd7",' +
	'"nota":"ca\\u00f1\\u00f3n","rol":"gateway","ttl":3600,"v":1}';
const FIRMA_PY =
	"350d5ac1a4cea2a869d9f31c927017d509bde5381b6179fd4cdec1a06f3d8d0c285f5955e6fe6472f792c87bfa0f5e435f4f657ec811c4f8868292e895a80d08";

const hex = (b: ArrayBuffer | Uint8Array) => [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("");
const ahora = () => Math.floor(Date.now() / 1000);

let llaveGw: CryptoKey;
beforeAll(async () => {
	llaveGw = await crypto.subtle.importKey("jwk", JWK_GATEWAY, { name: "Ed25519" }, false, ["sign"]);
});

async function firmar(llave: CryptoKey, datos: string | Uint8Array) {
	const b = typeof datos === "string" ? new TextEncoder().encode(datos) : datos;
	return hex(await crypto.subtle.sign({ name: "Ed25519" }, llave, b));
}

async function postFirmado(ruta: string, objeto: unknown, opciones: { ts?: number; nonce?: string; llave?: CryptoKey } = {}) {
	const cuerpo = new TextEncoder().encode(JSON.stringify(objeto));
	const ts = String(opciones.ts ?? ahora());
	const nonce = opciones.nonce ?? hex(crypto.getRandomValues(new Uint8Array(16)));
	const resumen = hex(await crypto.subtle.digest("SHA-256", cuerpo));
	const firma = await firmar(opciones.llave ?? llaveGw, ["FARONET-GW-1", "POST", ruta, ts, nonce, resumen].join("\n"));
	return SELF.fetch(`https://faronet.test${ruta}`, {
		method: "POST",
		headers: { "content-type": "application/json", "X-FaroNet-Ts": ts, "X-FaroNet-Nonce": nonce, "X-FaroNet-Firma": firma },
		body: cuerpo,
	});
}

describe("compatibilidad con Python", () => {
	it("el JSON canonico es igual al de mesh/directorio.py", () => {
		expect(jsonCanonico(ENTRADA_PY)).toBe(CANON_PY);
	});

	it("verifica una firma hecha en Python", async () => {
		const llave = await crypto.subtle.importKey(
			"raw",
			Uint8Array.from(ENTRADA_PY.id.match(/../g)!.map((h) => parseInt(h, 16))),
			{ name: "Ed25519" },
			false,
			["verify"],
		);
		const firma = Uint8Array.from(FIRMA_PY.match(/../g)!.map((h) => parseInt(h, 16)));
		expect(await crypto.subtle.verify({ name: "Ed25519" }, llave, firma, new TextEncoder().encode(CANON_PY))).toBe(true);
	});
});

describe("relay del gateway", () => {
	it("acepta una peticion firmada y la publica en el feed", async () => {
		const r = await postFirmado("/api/relay", { v: 1, tema: "noticias", texto: "hola <clearnet> & más", hora: ahora() });
		expect(r.status).toBe(200);
		const feed = await SELF.fetch("https://faronet.test/feed/noticias.atom");
		expect(feed.headers.get("content-type")).toContain("application/atom+xml");
		const xml = await feed.text();
		expect(xml).toContain("hola &lt;clearnet&gt; &amp; más");
		expect(xml).not.toContain("<clearnet>");
		expect(xml).toContain("<id>urn:faronet:tema:noticias</id>");
		expect(xml).toContain("<updated>");
	});

	it("rechaza peticiones sin firma", async () => {
		const r = await SELF.fetch("https://faronet.test/api/relay", { method: "POST", body: JSON.stringify({ tema: "x", texto: "y" }) });
		expect(r.status).toBe(401);
	});

	it("rechaza una firma de otra llave", async () => {
		const otra = (await crypto.subtle.generateKey({ name: "Ed25519" }, false, ["sign", "verify"])) as CryptoKeyPair;
		const r = await postFirmado("/api/relay", { tema: "noticias", texto: "falso" }, { llave: otra.privateKey });
		expect(r.status).toBe(401);
	});

	it("rechaza marcas de tiempo viejas", async () => {
		const r = await postFirmado("/api/relay", { tema: "noticias", texto: "viejo" }, { ts: ahora() - 600 });
		expect(r.status).toBe(401);
		expect(await r.text()).toContain("ventana");
	});

	it("rechaza la repeticion de un nonce", async () => {
		const nonce = hex(crypto.getRandomValues(new Uint8Array(16)));
		expect((await postFirmado("/api/relay", { tema: "noticias", texto: "uno" }, { nonce })).status).toBe(200);
		const r = await postFirmado("/api/relay", { tema: "noticias", texto: "uno" }, { nonce });
		expect(r.status).toBe(401);
		expect(await r.text()).toContain("nonce");
	});

	it("valida tema y texto", async () => {
		expect((await postFirmado("/api/relay", { tema: "../etc", texto: "x" })).status).toBe(400);
		expect((await postFirmado("/api/relay", { tema: "noticias", texto: "x".repeat(241) })).status).toBe(400);
		expect((await postFirmado("/api/relay", { tema: "noticias", texto: "" })).status).toBe(400);
	});

	it("JSON invalido da 400 y no 500", async () => {
		const cuerpo = new TextEncoder().encode("{no es json");
		const ts = String(ahora());
		const nonce = hex(crypto.getRandomValues(new Uint8Array(16)));
		const resumen = hex(await crypto.subtle.digest("SHA-256", cuerpo));
		const firma = await firmar(llaveGw, ["FARONET-GW-1", "POST", "/api/relay", ts, nonce, resumen].join("\n"));
		const r = await SELF.fetch("https://faronet.test/api/relay", {
			method: "POST",
			headers: { "X-FaroNet-Ts": ts, "X-FaroNet-Nonce": nonce, "X-FaroNet-Firma": firma },
			body: cuerpo,
		});
		expect(r.status).toBe(400);
	});
});

describe("salas publicas", () => {
	it("la pagina de la sala tiene cliente WebSocket y CSP", async () => {
		const r = await SELF.fetch("https://faronet.test/sala/noticias");
		expect(r.status).toBe(200);
		expect(r.headers.get("content-security-policy")).toContain("default-src 'none'");
		expect(await r.text()).toContain("new WebSocket");
	});

	it("un navegador conectado recibe el historial y los mensajes nuevos en tiempo real", async () => {
		await postFirmado("/api/relay", { tema: "envivo", texto: "antes de conectar" });
		const r = await SELF.fetch("https://faronet.test/sala/envivo/ws", { headers: { Upgrade: "websocket" } });
		expect(r.status).toBe(101);
		const ws = r.webSocket!;
		const llegados: any[] = [];
		ws.addEventListener("message", (e) => llegados.push(JSON.parse(e.data as string)));
		ws.accept();
		const esperar = async (cond: () => boolean) => {
			for (let i = 0; i < 50 && !cond(); i++) await new Promise((res) => setTimeout(res, 20));
		};
		await esperar(() => llegados.length >= 1);
		expect(llegados[0].historial[0].texto).toBe("antes de conectar");
		// Lo que manda el navegador se ignora (sala de solo lectura).
		ws.send(JSON.stringify({ texto: "intento de escribir" }));
		await postFirmado("/api/relay", { tema: "envivo", texto: "en vivo" });
		await esperar(() => llegados.length >= 2);
		expect(llegados.map((m) => m.texto)).toEqual([undefined, "en vivo"]);
		ws.close();
	});

	it("tema invalido en la URL da 400", async () => {
		expect((await SELF.fetch("https://faronet.test/sala/%3Cscript%3E")).status).toBe(400);
	});
});

describe("buzon muerto", () => {
	const id = "ab".repeat(32);

	it("guarda un blob de 1024 bytes y lo borra al leerlo", async () => {
		const blob = crypto.getRandomValues(new Uint8Array(1024));
		expect((await SELF.fetch(`https://faronet.test/buzon/${id}`, { method: "PUT", body: blob })).status).toBe(201);
		const r = await SELF.fetch(`https://faronet.test/buzon/${id}`);
		expect(r.status).toBe(200);
		expect(new Uint8Array(await r.arrayBuffer())).toEqual(blob);
		expect((await SELF.fetch(`https://faronet.test/buzon/${id}`)).status).toBe(404);
	});

	it("rechaza blobs que no midan 1024 bytes", async () => {
		expect((await SELF.fetch(`https://faronet.test/buzon/${id}`, { method: "PUT", body: new Uint8Array(10) })).status).toBe(413);
		expect((await SELF.fetch(`https://faronet.test/buzon/${id}`, { method: "PUT", body: new Uint8Array(2000) })).status).toBe(413);
	});

	it("rechaza identificadores que no sean 64 hex", async () => {
		expect((await SELF.fetch("https://faronet.test/buzon/mi_id_secreto_123")).status).toBe(400);
	});

	it("un blob vencido no se entrega", async () => {
		const otro = "cd".repeat(32);
		await env.DB.prepare("INSERT INTO buzon (id, blob, expira) VALUES (?, ?, ?)").bind(otro, new Uint8Array(1024), ahora() - 1).run();
		expect((await SELF.fetch(`https://faronet.test/buzon/${otro}`)).status).toBe(404);
	});
});

describe("directorio publico", () => {
	async function entradaFirmada(ttl = 3600) {
		const par = (await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"])) as CryptoKeyPair;
		const pub = hex(await crypto.subtle.exportKey("raw", par.publicKey) as ArrayBuffer);
		const entrada = { v: 1, id: pub, cifrado: "11".repeat(32), canal: "udp", direccion: "192.168.1.9:6001", creado: ahora(), ttl };
		return { entrada, firma: await firmar(par.privateKey, jsonCanonico(entrada)) };
	}

	it("guarda solo entradas con firma valida y las publica con su firma", async () => {
		const buena = await entradaFirmada();
		const mala = { ...(await entradaFirmada()), firma: "00".repeat(64) };
		const r = await postFirmado("/api/directorio", { v: 1, entradas: [buena, mala] });
		expect(await r.json()).toEqual({ aceptadas: 1, rechazadas: 1 });
		const d = (await (await SELF.fetch("https://faronet.test/directorio")).json()) as any;
		const ids = d.entradas.map((x: any) => x.entrada.id);
		expect(ids).toContain(buena.entrada.id);
		expect(ids).not.toContain(mala.entrada.id);
		expect(d.entradas.find((x: any) => x.entrada.id === buena.entrada.id).firma).toBe(buena.firma);
	});

	it("subir el directorio exige la firma del gateway", async () => {
		const r = await SELF.fetch("https://faronet.test/api/directorio", { method: "POST", body: "{}" });
		expect(r.status).toBe(401);
	});

	it("valida las entradas como mesh/directorio.py", () => {
		const base = { ...ENTRADA_PY, creado: ahora() };
		expect(entradaValida(base)).toBe(true);
		expect(entradaValida({ ...base, creado: ahora() + 10_000 })).toBe(false);
		expect(entradaValida({ ...base, ttl: 999_999 })).toBe(false);
		expect(entradaValida({ ...base, canal: "paloma" })).toBe(false);
		expect(entradaValida({ ...base, direccion: "999.1.1.1:1" })).toBe(false);
	});
});

describe("mantenimiento y no registro", () => {
	it("el cron borra los mensajes vencidos", async () => {
		await env.DB.prepare("INSERT INTO mensajes (tema, texto, creado, expira) VALUES ('viejo', 'x', 1, 2)").run();
		const ctx = createExecutionContext();
		await worker.scheduled(createScheduledController(), env as any, ctx);
		await waitOnExecutionContext(ctx);
		const r = await env.DB.prepare("SELECT COUNT(*) AS n FROM mensajes WHERE tema = 'viejo'").first();
		expect(r!.n).toBe(0);
	});

	it("ninguna tabla tiene columnas de IP o User-Agent", async () => {
		const { results } = await env.DB.prepare("SELECT name, sql FROM sqlite_master WHERE type = 'table'").all();
		const esquema = results.map((r) => String(r.sql).toLowerCase()).join("\n");
		expect(esquema).not.toMatch(/ip|agent|addr/);
	});

	it("escapa XML", () => {
		expect(escaparXml(`<a href="x">'&'</a>`)).toBe("&lt;a href=&quot;x&quot;&gt;&apos;&amp;&apos;&lt;/a&gt;");
	});

	it("rutas desconocidas dan 404", async () => {
		expect((await SELF.fetch("https://faronet.test/no-existe")).status).toBe(404);
	});
});
