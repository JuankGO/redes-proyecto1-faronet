export interface Env {
  DB: D1Database;
  SALA: DurableObjectNamespace;
}

export class Sala implements DurableObject {
  state: DurableObjectState;
  constructor(state: DurableObjectState) {
    this.state = state;
  }
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/ws" && request.headers.get("Upgrade") === "websocket") {
      const pair = new WebSocketPair();
      const [client, server] = Object.values(pair);
      this.state.acceptWebSocket(server);
      return new Response(null, { status: 101, webSocket: client });
    }
    return new Response("<h1>Sala FaroNet</h1>", { headers: { "content-type": "text/html" } });
  }
  webSocketMessage(ws: WebSocket, msg: string | ArrayBuffer) {
    for (const s of this.state.getWebSockets()) s.send(msg);
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const partes = url.pathname.split("/").filter(Boolean);

    // 1. Ruta para las Salas (Durable Object)
    if (partes[0] === "sala" && partes[1]) {
      const id = env.SALA.idFromName(partes[1]);
      return env.SALA.get(id).fetch(request);
    }

    // 2. Feed Atom (Lectura de la DB)
    if (partes[0] === "feed" && partes[1]) {
      const tema = partes[1].replace(".atom", "");
      const { results } = await env.DB.prepare(
        "SELECT texto, creado FROM mensajes WHERE tema = ? ORDER BY creado DESC LIMIT 20"
      ).bind(tema).all();
      
      let xml = `<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">\n<title>Feed de ${tema}</title>\n`;
      for (const row of results) {
        xml += `  <entry>\n    <title>Mensaje</title>\n    <updated>${new Date(Number(row.creado) * 1000).toISOString()}</updated>\n    <content>${row.texto}</content>\n  </entry>\n`;
      }
      xml += `</feed>`;
      
      return new Response(xml, { headers: { "content-type": "application/atom+xml" } });
    }

    // 3. Recibir mensajes públicos (Gateway) - Relé
    if (request.method === "POST" && url.pathname === "/api/relay") {
      const body = await request.json() as any;
      if (!body.tema || !body.texto) {
        return new Response("Faltan datos", { status: 400 });
      }
      await env.DB.prepare(
        "INSERT INTO mensajes (tema, texto, creado) VALUES (?, ?, ?)"
      ).bind(body.tema, body.texto, Math.floor(Date.now() / 1000)).run();
      
      const id = env.SALA.idFromName(body.tema);
      await env.SALA.get(id).fetch("http://dummy/ws-publish", {
        method: "POST",
        body: JSON.stringify({ texto: body.texto })
      }).catch(() => {});

      return new Response("OK", { status: 200 });
    }

    // 4. Buzón muerto
    if (url.pathname.startsWith("/buzon/")) {
      const id = partes[1];
      if (request.method === "PUT") {
        const blob = await request.arrayBuffer();
        const expira = Math.floor(Date.now() / 1000) + 86400;
        await env.DB.prepare(
          "INSERT OR REPLACE INTO buzon (id, blob, expira) VALUES (?, ?, ?)"
        ).bind(id, blob, expira).run();
        return new Response("Guardado", { status: 201 });
      }
      if (request.method === "GET") {
        const result = await env.DB.prepare(
          "DELETE FROM buzon WHERE id = ? AND expira > ? RETURNING blob"
        ).bind(id, Math.floor(Date.now() / 1000)).first();
        if (!result) return new Response("No encontrado", { status: 404 });
        return new Response(new Uint8Array(result.blob as any));
      }
    }

    return new Response("Bienvenido a FaroNet API", { status: 200 });
  },
};