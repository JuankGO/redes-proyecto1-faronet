"""Gateway de FaroNet (RFC, secciones 3.10, 4.4 y 5).

El gateway es un nodo de la mesh con rol "gateway" que ademas:

1. Publica en el Worker los mensajes publicos que le llegan por cebolla.
   Solo los mensajes con VIS = 1 salen a clearnet; los privados se ignoran.
   El gateway no sabe quien origino el mensaje (lo recibe por 3 relays).
2. Sube cada 60 s el directorio de nodos al Worker (directorio publico).
3. Si se le da --uart, une su comunidad con otra por el Faro: las rutas que
   aprende por la luz las anuncia por UDP y al reves.

Todas las peticiones van firmadas con la llave Ed25519 del gateway
(gateway/firma.py). La llave publica se configura en el Worker con:
    npx wrangler secret put GATEWAY_PUB

Uso en la Raspberry del Faro B:
    python3 -m gateway.gateway --puerto 6000 --ip-publica 192.168.1.30 \\
        --uart /dev/ttyAMA0 --worker https://faronet-worker.SUBDOMINIO.workers.dev

El gateway no guarda bitacoras: no imprime IPs, direcciones fisicas ni ids.
"""
import argparse
import json
import queue
import threading
import time
import urllib.error
import urllib.request

from app.mensaje import MensajeError, desempaquetar_mensaje, leer_publico
from gateway.firma import encabezados_firmados
from mesh.nodo import agregar_argumentos_nodo, crear_nodo_desde_args

INTERVALO_DIRECTORIO = 60.0
TIMEOUT_HTTP = 10.0


class ClienteWorker:
    """Hace las peticiones firmadas al Worker."""

    def __init__(self, url_base: str, llave_firma, abrir=urllib.request.urlopen):
        self.url_base = url_base.rstrip("/")
        self.llave = llave_firma
        self._abrir = abrir

    def _post(self, ruta: str, objeto) -> int:
        cuerpo = json.dumps(objeto, separators=(",", ":")).encode("utf-8")
        encabezados = {"Content-Type": "application/json"}
        encabezados.update(encabezados_firmados(self.llave, "POST", ruta, cuerpo))
        peticion = urllib.request.Request(self.url_base + ruta, data=cuerpo,
                                          headers=encabezados, method="POST")
        try:
            with self._abrir(peticion, timeout=TIMEOUT_HTTP) as r:
                return r.status
        except urllib.error.HTTPError as e:
            return e.code
        except (urllib.error.URLError, OSError, ValueError):
            return 0

    def publicar(self, tema: str, texto: str, hora: int) -> int:
        return self._post("/api/relay", {"v": 1, "tema": tema, "texto": texto, "hora": int(hora)})

    def subir_directorio(self, entradas: list) -> int:
        return self._post("/api/directorio", {"v": 1, "entradas": entradas})


class Gateway:
    def __init__(self, nodo, worker: ClienteWorker):
        self.nodo = nodo
        self.worker = worker
        self.publicados = 0
        self.ignorados = 0
        self._cola = queue.Queue(maxsize=200)
        self._corriendo = False
        nodo.al_recibir_mensaje = self._al_recibir

    def _al_recibir(self, crudo: bytes) -> None:
        """Se llama desde el hilo del nodo: solo encola."""
        try:
            d = desempaquetar_mensaje(crudo)
            tema, texto = leer_publico(d)
        except MensajeError:
            self.ignorados += 1       # privados, temas cifrados o basura: no salen
            return
        try:
            self._cola.put_nowait((tema, texto, d["hora"]))
        except queue.Full:
            self.ignorados += 1

    def _loop(self) -> None:
        ultimo_dir = 0.0
        espera = 1.0
        while self._corriendo:
            try:
                tema, texto, hora = self._cola.get(timeout=1.0)
            except queue.Empty:
                tema = None
            if tema is not None:
                estado = self.worker.publicar(tema, texto, hora)
                if estado == 200:
                    self.publicados += 1
                    espera = 1.0
                elif estado in (0, 429) or estado >= 500:
                    # Worker caido o limite: se reintenta mas tarde.
                    try:
                        self._cola.put_nowait((tema, texto, hora))
                    except queue.Full:
                        pass
                    time.sleep(espera)
                    espera = min(espera * 2, 60.0)
                else:
                    self.ignorados += 1   # 400/401: no tiene sentido reintentar
            ahora = time.time()
            if ahora - ultimo_dir >= INTERVALO_DIRECTORIO:
                ultimo_dir = ahora
                with self.nodo._lock:
                    entradas = self.nodo.directorio.para_transporte()
                self.worker.subir_directorio(entradas)

    def arrancar(self) -> None:
        self._corriendo = True
        self.nodo.arrancar()
        threading.Thread(target=self._loop, daemon=True).start()

    def detener(self) -> None:
        self._corriendo = False
        self.nodo.detener()


def main(argv=None):
    p = argparse.ArgumentParser(description="Gateway de FaroNet (mesh <-> Worker)")
    agregar_argumentos_nodo(p)
    p.add_argument("--worker", required=True,
                   help="URL del Worker, por ejemplo https://faronet-worker.x.workers.dev")
    a = p.parse_args(argv)
    if not a.worker.startswith(("https://", "http://localhost", "http://127.0.0.1")):
        p.error("--worker debe usar https (http solo para localhost)")
    a.rol = "gateway"
    nodo = crear_nodo_desde_args(a)
    gw = Gateway(nodo, ClienteWorker(a.worker, nodo.firma))
    boton = None
    if a.uart:
        from faro.gpio import BotonPanico, Indicadores
        indicadores = Indicadores()
        boton = BotonPanico(lambda: nodo.panico(indicadores))
    print("Gateway de FaroNet")
    print(f"  Llave publica (GATEWAY_PUB del Worker): {nodo.mi_id}")
    print(f"  Worker: {a.worker}")
    print(f"  Enlace Faro: {'si' if a.uart else 'no'}")
    gw.arrancar()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo...")
        gw.detener()
    del boton


if __name__ == "__main__":
    main()
