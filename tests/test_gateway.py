"""Pruebas del gateway: firma de peticiones y publicacion de mensajes publicos."""
import hashlib
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from nacl.public import PrivateKey
from nacl.signing import SigningKey, VerifyKey

from app.cliente import Cliente
from app.mensaje import PRIVADO, empaquetar_mensaje, hash_tema
from gateway.firma import cadena_a_firmar, encabezados_firmados
from gateway.gateway import ClienteWorker, Gateway
from mesh.nodo import Nodo


def test_firma_verificable_con_la_llave_publica():
    llave = SigningKey.generate()
    cuerpo = b'{"tema":"x"}'
    h = encabezados_firmados(llave, "POST", "/api/relay", cuerpo, ts=1760000000, nonce="ab" * 16)
    mensaje = cadena_a_firmar("POST", "/api/relay", 1760000000, "ab" * 16, cuerpo)
    assert mensaje == ("FARONET-GW-1\nPOST\n/api/relay\n1760000000\n" + "ab" * 16 + "\n"
                       + hashlib.sha256(cuerpo).hexdigest()).encode()
    VerifyKey(llave.verify_key.encode()).verify(mensaje, bytes.fromhex(h["X-FaroNet-Firma"]))


class _WorkerFalso(BaseHTTPRequestHandler):
    recibidas = []

    def do_POST(self):
        cuerpo = self.rfile.read(int(self.headers["Content-Length"]))
        self.recibidas.append((self.path, {k.lower(): v for k, v in self.headers.items()}, cuerpo))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):   # sin bitacoras
        pass


def test_mensaje_publico_llega_firmado_al_worker():
    _WorkerFalso.recibidas = []
    servidor = HTTPServer(("127.0.0.1", 0), _WorkerFalso)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{servidor.server_port}"

    base = 9400
    puertos = [base + i for i in range(7)]
    nodos = []
    for i, p in enumerate(puertos):
        semillas = [("127.0.0.1", q) for q in puertos if q != p]
        nodos.append(Nodo(p, SigningKey.generate(), PrivateKey.generate(), semillas=semillas,
                          rol="gateway" if i == 6 else None))
    gw_nodo = nodos[6]
    gw = Gateway(gw_nodo, ClienteWorker(url, gw_nodo.firma))
    try:
        for n in nodos[:6]:
            n.arrancar()
        gw.arrancar()
        time.sleep(0.3)
        limite = time.time() + 8
        while time.time() < limite and len(nodos[0].directorio) < 7:
            for n in nodos:
                n.enviar_ahora()
            time.sleep(0.3)
        ana = Cliente("ana", nodos[0])
        relays = ana.enviar_publico("noticias", "hola clearnet")
        assert len(relays) == 3
        # Un privado al gateway NO debe salir a clearnet.
        nodos[0].mandar_a(gw_nodo.mi_id, empaquetar_mensaje(PRIVADO, hash_tema("x"), b"secreto"))

        limite = time.time() + 10
        while time.time() < limite and not any(r[0] == "/api/relay" for r in _WorkerFalso.recibidas):
            time.sleep(0.1)
        time.sleep(1.0)
        relay = [r for r in _WorkerFalso.recibidas if r[0] == "/api/relay"]
        assert len(relay) == 1
        ruta, h, cuerpo = relay[0]
        datos = json.loads(cuerpo)
        assert datos["tema"] == "noticias" and datos["texto"] == "hola clearnet"
        mensaje = cadena_a_firmar("POST", ruta, int(h["x-faronet-ts"]), h["x-faronet-nonce"], cuerpo)
        VerifyKey(bytes.fromhex(gw_nodo.mi_id)).verify(mensaje, bytes.fromhex(h["x-faronet-firma"]))
        assert b"secreto" not in b"".join(r[2] for r in _WorkerFalso.recibidas)
        assert gw.ignorados >= 1
        # El directorio publico tambien se sube firmado.
        assert any(r[0] == "/api/directorio" for r in _WorkerFalso.recibidas)
    finally:
        for n in nodos[:6]:
            n.detener()
        gw.detener()
        servidor.shutdown()
