"""Tabla de vecinos directos: HELLO cada 10s, olvido a los 30s sin senal.

Un vecino es un nodo que esta a un salto de distancia. No confundir con el
directorio (que lista toda la red) ni con la tabla de rutas (que dice como
llegar a cualquier nodo pasando por vecinos).

Formato del HELLO (JSON canonico, sin firmar en v1; RFC seccion 3.2):
    t     tipo del mensaje ('hello')
    v     version (1; si falta se asume 1)
    id    id del emisor (hex, 64 chars)
    canal 'udp' o 'faro'
    dir   direccion de contacto del emisor
    ts    timestamp de envio (int)

El HELLO no va firmado en la version 1 (RFC, seccion 8.3): un atacante en
la red local podria anunciar un vecino falso, pero no leer ni alterar las
celdas, que van cifradas y autenticadas.
"""
import json
import time

from mesh.directorio import direccion_valida, es_hex64

VERSION = 1

INTERVALO_HELLO = 10.0      # segundos entre HELLO
TIMEOUT_VECINO = 30.0       # segundos sin senal para olvidar


class VecinoError(Exception):
    """HELLO mal formado."""


def crear_hello(mi_id_hex: str, canal: str, direccion: str) -> bytes:
    """Arma un HELLO listo para mandar por el medio."""
    if canal not in ("udp", "faro"):
        raise VecinoError(f"canal invalido: {canal}")
    mensaje = {
        "t": "hello",
        "v": VERSION,
        "id": mi_id_hex,
        "canal": canal,
        "dir": direccion,
        "ts": int(time.time()),
    }
    return json.dumps(mensaje, sort_keys=True, separators=(",", ":")).encode("utf-8")


def parsear_hello(datos: bytes) -> dict:
    """Lee un HELLO. Lanza VecinoError si no es valido."""
    try:
        mensaje = json.loads(datos.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise VecinoError(f"no es JSON valido: {e}")
    return validar_hello(mensaje)


def validar_hello(mensaje) -> dict:
    """Valida un HELLO ya decodificado. Lanza VecinoError si no es valido."""
    if not isinstance(mensaje, dict):
        raise VecinoError("el HELLO debe ser un objeto JSON")
    for campo in ("t", "id", "canal", "dir", "ts"):
        if campo not in mensaje:
            raise VecinoError(f"falta el campo {campo}")
    if mensaje["t"] != "hello":
        raise VecinoError(f"tipo inesperado: {mensaje['t']}")
    if mensaje["canal"] not in ("udp", "faro"):
        raise VecinoError("canal invalido")
    if not es_hex64(mensaje["id"]):
        raise VecinoError("id debe ser hex de 64 chars")
    v = mensaje.get("v", VERSION)
    if not isinstance(v, int) or isinstance(v, bool) or not (1 <= v <= VERSION):
        raise VecinoError("version no soportada")
    if not direccion_valida(mensaje["canal"], mensaje["dir"]):
        raise VecinoError("direccion invalida para el canal")
    if not isinstance(mensaje["ts"], int) or isinstance(mensaje["ts"], bool):
        raise VecinoError("ts debe ser entero")
    return mensaje


class TablaVecinos:
    """Mantiene los vecinos vistos recientemente, con su ultima senal."""

    def __init__(self, timeout: float = TIMEOUT_VECINO):
        self.timeout = timeout
        self._tabla = {}   # id_hex -> {'canal', 'dir', 'visto'}

    def registrar(self, mensaje: dict, ahora: float = None) -> bool:
        """Anota un HELLO. Devuelve True si es nuevo, False si ya lo conocia."""
        if ahora is None:
            ahora = time.time()
        id_hex = mensaje["id"]
        es_nuevo = id_hex not in self._tabla
        self._tabla[id_hex] = {
            "canal": mensaje["canal"],
            "dir": mensaje["dir"],
            "visto": ahora,
        }
        return es_nuevo

    def olvidar_vencidos(self, ahora: float = None) -> list:
        """Borra los vecinos que llevan mucho sin mandar HELLO. Devuelve sus ids."""
        if ahora is None:
            ahora = time.time()
        vencidos = [
            id_hex for id_hex, info in self._tabla.items()
            if (ahora - info["visto"]) >= self.timeout
        ]
        for id_hex in vencidos:
            del self._tabla[id_hex]
        return vencidos

    def listar(self) -> list:
        """Devuelve [(id_hex, canal, dir, visto)] ordenado por id."""
        return [
            (id_hex, info["canal"], info["dir"], info["visto"])
            for id_hex, info in sorted(self._tabla.items())
        ]

    def obtener(self, id_hex: str):
        """Devuelve {'canal', 'dir', 'visto'} o None si no es vecino."""
        return self._tabla.get(id_hex)

    def limpiar(self) -> None:
        self._tabla.clear()

    def __len__(self):
        return len(self._tabla)