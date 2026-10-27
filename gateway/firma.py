"""Firma de las peticiones del gateway al Worker (RFC, seccion 5.2).

Cada peticion lleva:
    X-FaroNet-Ts     hora del gateway en segundos Unix
    X-FaroNet-Nonce  16 bytes aleatorios en hex
    X-FaroNet-Firma  firma Ed25519 en hex

La firma se calcula sobre:
    "FARONET-GW-1" LF METODO LF RUTA LF TS LF NONCE LF HEX(SHA256(CUERPO))

El Worker verifica la firma con GATEWAY_PUB, rechaza si |ahora - TS| > 60 s
y si el nonce ya se uso. Asi nadie puede repetir una peticion capturada.
"""
import hashlib
import secrets
import time

from nacl.signing import SigningKey

PREFIJO = "FARONET-GW-1"


def cadena_a_firmar(metodo: str, ruta: str, ts: int, nonce: str, cuerpo: bytes) -> bytes:
    resumen = hashlib.sha256(cuerpo).hexdigest()
    return "\n".join([PREFIJO, metodo.upper(), ruta, str(ts), nonce, resumen]).encode("ascii")


def encabezados_firmados(llave: SigningKey, metodo: str, ruta: str, cuerpo: bytes,
                         ts: int = None, nonce: str = None) -> dict:
    """Devuelve los tres encabezados X-FaroNet-* para una peticion."""
    ts = int(time.time()) if ts is None else int(ts)
    nonce = secrets.token_hex(16) if nonce is None else nonce
    firma = llave.sign(cadena_a_firmar(metodo, ruta, ts, nonce, cuerpo)).signature
    return {
        "X-FaroNet-Ts": str(ts),
        "X-FaroNet-Nonce": nonce,
        "X-FaroNet-Firma": firma.hex(),
    }
