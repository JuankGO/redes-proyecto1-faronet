"""Nodo de FaroNet: junta medio, directorio, vecinos, rutas, cebolla y celdas.

Un nodo es un programa autonomo que:
- Se identifica con un par Ed25519 + Curve25519.
- Publica su entrada al directorio (firmada).
- Manda HELLO cada 10s y olvida vecinos a los 30s.
- Intercambia tablas de rutas con sus vecinos.
- Recibe celdas, las reenvia al siguiente salto o las entrega al destino.

Este es el programa que se corre con:
    python -m mesh.nodo --puerto 6001 --semilla 127.0.0.1:6002
"""
import argparse
import base64
import json
import socket
import threading
import time

from nacl.public import PrivateKey, PublicKey
from nacl.signing import SigningKey

from mesh.celda import (
    CeldaError,
    desempaquetar_celda,
    empaquetar_celda,
    fragmentar,
    reensamblar,
)
from mesh.directorio import (
    DirectorioError,
    crear_entrada,
    firmar,
    validar,
)
from mesh.onion import (
    CANAL_UDP,
    OnionError,
    abrir_como_destino,
    abrir_como_relay,
    construir_cebolla,
    direccion_udp,
    leer_direccion_udp,
)
from mesh.rutas import TablaRutas
from mesh.saltos import SaltosError, elegir_saltos
from mesh.vecinos import TablaVecinos

INTERVALO_PERIODICO = 10.0
TAMANO_DATAGRAMA = 65535


class Nodo:
    """Un nodo de FaroNet."""

    def __init__(self, puerto: int, firma: SigningKey, cifrado: PrivateKey,
                 semillas: list = None, canal: str = "udp",
                 ip_publica: str = "127.0.0.1", ttl_entrada: int = 3600):
        self.puerto = puerto
        self.firma = firma
        self.cifrado = cifrado
        self.mi_id = firma.verify_key.encode().hex()
        self.ip_publica = ip_publica
        self.mi_direccion = f"{ip_publica}:{puerto}"
        self.canal = canal
        self.semillas = list(semillas or [])

        # Mi propia entrada al directorio, ya firmada.
        self.entrada = crear_entrada(firma, cifrado, canal, self.mi_direccion,
                                     ttl=ttl_entrada)
        self.firma_entrada = firmar(self.entrada, firma)

        # Estado de la red.
        self.directorio = {self.mi_id: (self.entrada, self.firma_entrada)}
        self.vecinos = TablaVecinos()
        self.rutas = TablaRutas(self.mi_id)
        self.recibidos = []

        # Socket y hilo.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._corriendo = False
        self._hilo = None

    # ----- Ciclo de vida -----

    def arrancar(self) -> None:
        self.sock.bind(("0.0.0.0", self.puerto))
        # Buffer grande para aguantar la rafaga inicial de gossip.
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
        except OSError:
            pass
        self._corriendo = True
        self._hilo = threading.Thread(target=self._loop, daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._corriendo = False
        try:
            self.sock.close()
        except OSError:
            pass
        if self._hilo:
            self._hilo.join(timeout=2.0)

    def _loop(self) -> None:
        self._periodico()   # primer envio inmediato
        ultimo_periodico = time.time()
        while self._corriendo:
            try:
                self.sock.settimeout(0.5)
                datos, addr = self.sock.recvfrom(TAMANO_DATAGRAMA)
                self._procesar(datos, addr)
            except socket.timeout:
                pass
            except OSError:
                break
            ahora = time.time()
            if ahora - ultimo_periodico >= INTERVALO_PERIODICO:
                self._periodico()
                ultimo_periodico = ahora
            # Olvidar vecinos y rutas vencidas.
            self.vecinos.olvidar_vencidos()
            self.rutas.olvidar_vencidas()

    # ----- Envio periodico -----

    def _periodico(self) -> None:
        destinos = self._destinos_periodicos()
        if not destinos:
            return
        hello = {
            "t": "hello", "id": self.mi_id, "canal": self.canal,
            "dir": self.mi_direccion, "ts": int(time.time()),
        }
        dir_msg = {"t": "dir", "entrada": self.entrada, "firma": self.firma_entrada}
        ruta_msg = {"t": "ruta", "id": self.mi_id, "tabla": self.rutas.anuncio()}
        for destino in destinos:
            self._mandar_raw(hello, destino)
            self._mandar_raw(dir_msg, destino)
            self._mandar_raw(ruta_msg, destino)
            time.sleep(0.005)   # respiro para no saturar el buffer del receptor

    def _destinos_periodicos(self) -> list:
        destinos = list(self.semillas)
        for _, _, direccion, _ in self.vecinos.listar():
            try:
                ip, puerto = direccion.rsplit(":", 1)
                destinos.append((ip, int(puerto)))
            except (ValueError, AttributeError):
                continue
        return destinos

    def _mandar_raw(self, mensaje: dict, destino: tuple) -> None:
        datos = json.dumps(mensaje, separators=(",", ":")).encode("utf-8")
        try:
            self.sock.sendto(datos, destino)
        except OSError:
            pass

    # ----- Recepcion -----

    def _procesar(self, datos: bytes, addr) -> None:
        try:
            mensaje = json.loads(datos.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return
        if not isinstance(mensaje, dict):
            return
        t = mensaje.get("t")
        if t == "hello":
            self._on_hello(mensaje)
        elif t == "dir":
            self._on_dir(mensaje)
        elif t == "ruta":
            self._on_ruta(mensaje)
        elif t == "celda":
            self._on_celda(mensaje)

    def _on_hello(self, mensaje: dict) -> None:
        try:
            self.vecinos.registrar(mensaje)
        except Exception:
            pass

    def _on_dir(self, mensaje: dict) -> None:
        entrada = mensaje.get("entrada")
        firma_hex = mensaje.get("firma")
        try:
            validar(entrada, firma_hex)
        except DirectorioError as e:
            print(f"[{self.mi_id[:6]}] dir rechazado: {e}")
            return
        id_hex = entrada["id"]
        if id_hex == self.mi_id:
            return
        self.directorio[id_hex] = (entrada, firma_hex)
        # Tambien lo anoto como vecino directo si su canal es accesible.
        if entrada["canal"] == "udp":
            self.vecinos.registrar({
                "t": "hello", "id": id_hex, "canal": "udp",
                "dir": entrada["direccion"], "ts": int(time.time()),
            })
            self.rutas.aprender_vecino_directo(id_hex)

    def _on_ruta(self, mensaje: dict) -> None:
        vecino_id = mensaje.get("id")
        tabla = mensaje.get("tabla")
        if not vecino_id or not isinstance(tabla, dict):
            return
        if vecino_id == self.mi_id:
            return
        self.rutas.actualizar_desde(vecino_id, tabla)

    def _on_celda(self, mensaje: dict) -> None:
        frags_b64 = mensaje.get("frags")
        if not isinstance(frags_b64, list):
            return
        try:
            frags = [base64.b64decode(f) for f in frags_b64]
        except Exception:
            return
        try:
            celda_bytes = reensamblar(frags)
        except CeldaError:
            return
        try:
            onion_cell = desempaquetar_celda(celda_bytes)
        except CeldaError:
            return
        self._procesar_onion(onion_cell)

    def _procesar_onion(self, onion_cell: bytes) -> None:
        # Intento como relay.
        try:
            canal, dir_sig, interno = abrir_como_relay(onion_cell, self.cifrado)
            print(f"[{self.mi_id[:6]}] relay -> {dir_sig.hex()}")
            self._enviar_al_siguiente(canal, dir_sig, interno)
            return
        except OnionError:
            pass
        # Intento como destino.
        try:
            texto = abrir_como_destino(onion_cell, self.cifrado)
            self.recibidos.append(texto)
            print(f"[{self.mi_id[:6]}] DESTINO: {texto.decode(errors='replace')}")
            return
        except OnionError:
            print(f"[{self.mi_id[:6]}] celda no descifrable")

    def _enviar_al_siguiente(self, canal: int, dir_6B: bytes,
                             contenido_interno: bytes) -> None:
        if canal != CANAL_UDP:
            print(f"[{self.mi_id[:6]}] canal Faro aun no soportado en nodo")
            return
        try:
            ip, puerto = leer_direccion_udp(dir_6B)
        except OnionError:
            return
        self._mandar_celda(contenido_interno, (ip, puerto))

    def _mandar_celda(self, contenido_interno: bytes, destino: tuple) -> None:
        celda_bytes = empaquetar_celda(contenido_interno)
        frags = fragmentar(celda_bytes)
        frags_b64 = [base64.b64encode(f).decode("ascii") for f in frags]
        self._mandar_raw({"t": "celda", "frags": frags_b64}, destino)

    # ----- API publica -----

    def mandar_a(self, destino_id: str, mensaje: bytes) -> list:
        """Arma una cebolla de 3 saltos y la manda al destino.

        Devuelve la lista de ids de los relays elegidos (para depuracion).
        """
        entrada_destino = self.directorio.get(destino_id)
        if entrada_destino is None:
            raise RuntimeError(f"no conozco al destino {destino_id[:8]}")
        lista = [e for e, _ in self.directorio.values()]
        saltos_entradas = elegir_saltos(lista, self.mi_id, destino_id, cantidad=3)
        ids_cadena = [e["id"] for e in saltos_entradas] + [destino_id]
        saltos = []
        for i, entrada in enumerate(saltos_entradas):
            pub = PublicKey(bytes.fromhex(entrada["cifrado"]))
            dir_sig = self._direccion_de(ids_cadena[i + 1])
            saltos.append((pub, CANAL_UDP, dir_sig))
        destino_pub = PublicKey(bytes.fromhex(entrada_destino[0]["cifrado"]))
        onion_cell = construir_cebolla(destino_pub, saltos, mensaje)
        # Enviar al primer relay.
        dir_primero = self._direccion_de(saltos_entradas[0]["id"])
        self._enviar_al_siguiente(CANAL_UDP, dir_primero, onion_cell)
        return [e["id"] for e in saltos_entradas]

    def _direccion_de(self, id_hex: str) -> bytes:
        entrada, _ = self.directorio[id_hex]
        ip, puerto = entrada["direccion"].rsplit(":", 1)
        return direccion_udp(ip, int(puerto))
    
    def enviar_ahora(self) -> None:
        """Fuerza un envio periodico inmediato (util para demos y pruebas)."""
        self._periodico()


def main():
    p = argparse.ArgumentParser(description="Nodo de FaroNet")
    p.add_argument("--puerto", type=int, required=True)
    p.add_argument("--semilla", action="append", default=[],
                   help="IP:PUERTO de un nodo semilla (puede repetirse)")
    p.add_argument("--canal", default="udp", choices=["udp", "faro"])
    p.add_argument("--ip-publica", default="127.0.0.1")
    a = p.parse_args()

    semillas = []
    for s in a.semilla:
        ip, puerto = s.rsplit(":", 1)
        semillas.append((ip, int(puerto)))

    firma = SigningKey.generate()
    cifrado = PrivateKey.generate()
    nodo = Nodo(a.puerto, firma, cifrado, semillas=semillas,
                canal=a.canal, ip_publica=a.ip_publica)
    print(f"Mi id    : {nodo.mi_id}")
    print(f"Escucho  : 0.0.0.0:{nodo.puerto}")
    print(f"Semillas : {semillas}")
    nodo.arrancar()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo...")
        nodo.detener()


if __name__ == "__main__":
    main()