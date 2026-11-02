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

    ts = int(time.time()) if ts is None else int(ts)
    nonce = secrets.token_hex(16) if nonce is None else nonce
    firma = llave.sign(cadena_a_firmar(metodo, ruta, ts, nonce, cuerpo)).signature
    return {
        "X-FaroNet-Ts": str(ts),
        "X-FaroNet-Nonce": nonce,
        "X-FaroNet-Firma": firma.hex(),
    }
