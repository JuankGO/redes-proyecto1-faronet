"""Directorio de nodos: entradas firmadas con Ed25519 y TTL.

Cada nodo publica una entrada que dice quien es, como llegar a el y hasta
cuando vale. La entrada la firma el propio nodo, asi que nadie puede
inventar la de otro. El directorio se puede compartir entre vecinos o
publicar en el Worker sin perder seguridad: la firma se verifica siempre.

Formato de una entrada (dict):
    v        version del formato (int, empezamos en 1)
    id       clave publica de firma en hex (str, 64 chars)
    cifrado  clave publica de cifrado en hex (str, 64 chars)
    canal    'udp' o 'faro' (str)
    direccion  'IP:PUERTO' o direccion fisica hex (str)
    creado   timestamp Unix de creacion (int)
    ttl      segundos de vida (int)

El JSON que se firma usa las mismas claves ordenadas y sin espacios para
que los mismos datos produzcan siempre los mismos bytes.
"""
import json
import time

from nacl.exceptions import BadSignatureError
from nacl.public import PrivateKey
from nacl.signing import SigningKey, VerifyKey

VERSION = 1
TTL_POR_DEFECTO = 3600          # 1 hora
TTL_MAXIMO = 86400              # 24 horas


class DirectorioError(Exception):
    """Entrada mal formada, firma invalida o version no soportada."""


def a_bytes(entrada: dict) -> bytes:
    """Serializa una entrada a bytes canonicos (JSON ordenado y compacto)."""
    return json.dumps(
        entrada, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def crear_entrada(clave_firma: SigningKey, clave_cifrado: PrivateKey,
                  canal: str, direccion: str,
                  ttl: int = TTL_POR_DEFECTO) -> dict:
    """Arma una entrada nueva SIN firmar."""
    if canal not in ("udp", "faro"):
        raise DirectorioError(f"canal invalido: {canal}")
    if not isinstance(direccion, str) or not direccion:
        raise DirectorioError("direccion vacia")
    if not (0 < ttl <= TTL_MAXIMO):
        raise DirectorioError(f"ttl fuera de rango: {ttl}")
    return {
        "v": VERSION,
        "id": clave_firma.verify_key.encode().hex(),
        "cifrado": bytes(clave_cifrado.public_key).hex(),
        "canal": canal,
        "direccion": direccion,
        "creado": int(time.time()),
        "ttl": int(ttl),
    }


def firmar(entrada: dict, clave_firma: SigningKey) -> str:
    """Firma la entrada. Devuelve la firma en hex."""
    if clave_firma.verify_key.encode().hex() != entrada["id"]:
        raise DirectorioError("la clave de firma no corresponde al campo id")
    firma = clave_firma.sign(a_bytes(entrada))
    return firma.signature.hex()


def verificar(entrada: dict, firma_hex: str) -> bool:
    """Verifica la firma de una entrada contra su propio campo id.

    Devuelve True si es valida, False si no. No lanza excepciones: quien
    llama decide que hacer con las invalidas.
    """
    try:
        clave = VerifyKey(bytes.fromhex(entrada["id"]))
        clave.verify(a_bytes(entrada), bytes.fromhex(firma_hex))
        return True
    except (BadSignatureError, KeyError, ValueError, TypeError):
        return False


def esta_vigente(entrada: dict, ahora: float = None) -> bool:
    """True si la entrada no ha vencido segun su TTL."""
    if ahora is None:
        ahora = time.time()
    try:
        creado = int(entrada["creado"])
        ttl = int(entrada["ttl"])
    except (KeyError, ValueError, TypeError):
        return False
    return (ahora - creado) < ttl


def validar(entrada: dict, firma_hex: str, ahora: float = None) -> None:
    """Valida formato, version, firma y vigencia. Lanza DirectorioError si algo falla."""
    if not isinstance(entrada, dict):
        raise DirectorioError("la entrada debe ser un dict")
    for campo in ("v", "id", "cifrado", "canal", "direccion", "creado", "ttl"):
        if campo not in entrada:
            raise DirectorioError(f"falta el campo {campo}")
    if entrada["v"] > VERSION:
        raise DirectorioError(f"version {entrada['v']} no soportada")
    if entrada["canal"] not in ("udp", "faro"):
        raise DirectorioError("canal invalido")
    try:
        bytes.fromhex(entrada["id"])
        bytes.fromhex(entrada["cifrado"])
        bytes.fromhex(firma_hex)
    except ValueError as e:
        raise DirectorioError(f"hex invalido: {e}")
    if not verificar(entrada, firma_hex):
        raise DirectorioError("firma invalida")
    if not esta_vigente(entrada, ahora):
        raise DirectorioError("entrada vencida")


def serializar_para_transporte(entrada: dict, firma_hex: str) -> dict:
    """Empaqueta la entrada y su firma para mandarla por la red."""
    return {"entrada": entrada, "firma": firma_hex}