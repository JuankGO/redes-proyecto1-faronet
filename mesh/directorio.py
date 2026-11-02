import json
import re
import time

from nacl.exceptions import BadSignatureError
from nacl.public import PrivateKey
from nacl.signing import SigningKey, VerifyKey

VERSION = 1
TTL_POR_DEFECTO = 3600
TTL_MAXIMO = 86400
TOLERANCIA_RELOJ = 300
ROLES = ("gateway",)
CAMPOS = ("v", "id", "cifrado", "canal", "direccion", "creado", "ttl")

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEX128 = re.compile(r"^[0-9a-f]{128}$")
_HEX8 = re.compile(r"^[0-9a-f]{8}$")
_UDP = re.compile(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3}):(\d{1,5})$")


class DirectorioError(Exception):
    pass


def a_bytes(entrada: dict) -> bytes:

    return json.dumps(
        entrada, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def es_hex64(valor) -> bool:
    return isinstance(valor, str) and bool(_HEX64.match(valor))


def direccion_valida(canal: str, direccion) -> bool:

    if not isinstance(direccion, str):
        return False
    if canal == "faro":
        return bool(_HEX8.match(direccion)) and direccion not in ("00000000", "ffffffff")
    if canal == "udp":
        m = _UDP.match(direccion)
        if not m:
            return False
        octetos = [int(x) for x in m.groups()[:4]]
        puerto = int(m.group(5))
        return all(0 <= o <= 255 for o in octetos) and 0 < puerto < 65536
    return False


def crear_entrada(clave_firma: SigningKey, clave_cifrado: PrivateKey,
                  canal: str, direccion: str,
                  ttl: int = TTL_POR_DEFECTO, rol: str = None) -> dict:

    if canal not in ("udp", "faro"):
        raise DirectorioError(f"canal invalido: {canal}")
    if not isinstance(direccion, str) or not direccion:
        raise DirectorioError("direccion vacia")
    if not (0 < ttl <= TTL_MAXIMO):
        raise DirectorioError(f"ttl fuera de rango: {ttl}")
    if rol is not None and rol not in ROLES:
        raise DirectorioError(f"rol invalido: {rol}")
    entrada = {
        "v": VERSION,
        "id": clave_firma.verify_key.encode().hex(),
        "cifrado": bytes(clave_cifrado.public_key).hex(),
        "canal": canal,
        "direccion": direccion,
        "creado": int(time.time()),
        "ttl": int(ttl),
    }
    if rol:
        entrada["rol"] = rol
    return entrada


def firmar(entrada: dict, clave_firma: SigningKey) -> str:

    if clave_firma.verify_key.encode().hex() != entrada["id"]:
        raise DirectorioError("la clave de firma no corresponde al campo id")
    firma = clave_firma.sign(a_bytes(entrada))
    return firma.signature.hex()


def verificar(entrada: dict, firma_hex: str) -> bool:

    try:
        clave = VerifyKey(bytes.fromhex(entrada["id"]))
        clave.verify(a_bytes(entrada), bytes.fromhex(firma_hex))
        return True
    except Exception:
        return False


def esta_vigente(entrada: dict, ahora: float = None) -> bool:

    if ahora is None:
        ahora = time.time()
    try:
        creado = int(entrada["creado"])
        ttl = int(entrada["ttl"])
    except (KeyError, ValueError, TypeError):
        return False
    return (ahora - creado) < ttl


def _es_entero(valor) -> bool:
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar(entrada: dict, firma_hex: str, ahora: float = None) -> None:

    if ahora is None:
        ahora = time.time()
    if not isinstance(entrada, dict):
        raise DirectorioError("la entrada debe ser un dict")
    for campo in CAMPOS:
        if campo not in entrada:
            raise DirectorioError(f"falta el campo {campo}")
    if not _es_entero(entrada["v"]):
        raise DirectorioError("el campo v debe ser entero")
    if entrada["v"] > VERSION or entrada["v"] < 1:
        raise DirectorioError(f"version {entrada['v']} no soportada")
    if entrada["canal"] not in ("udp", "faro"):
        raise DirectorioError("canal invalido")
    if not es_hex64(entrada["id"]) or not es_hex64(entrada["cifrado"]):
        raise DirectorioError("id y cifrado deben ser hex de 64 caracteres")
    if not isinstance(firma_hex, str) or not _HEX128.match(firma_hex):
        raise DirectorioError("la firma debe ser hex de 128 caracteres")
    if not direccion_valida(entrada["canal"], entrada["direccion"]):
        raise DirectorioError("direccion invalida para el canal")
    if not _es_entero(entrada["creado"]) or not _es_entero(entrada["ttl"]):
        raise DirectorioError("creado y ttl deben ser enteros")
    if not (0 < entrada["ttl"] <= TTL_MAXIMO):
        raise DirectorioError("ttl fuera de rango")
    if entrada["creado"] > ahora + TOLERANCIA_RELOJ:
        raise DirectorioError("entrada creada en el futuro")
    if "rol" in entrada and entrada["rol"] not in ROLES:
        raise DirectorioError("rol invalido")
    if not verificar(entrada, firma_hex):
        raise DirectorioError("firma invalida")
    if not esta_vigente(entrada, ahora):
        raise DirectorioError("entrada vencida")


def serializar_para_transporte(entrada: dict, firma_hex: str) -> dict:

    return {"entrada": entrada, "firma": firma_hex}


class Directorio:


    def __init__(self):
        self._entradas = {}

    def agregar(self, entrada: dict, firma_hex: str, ahora: float = None) -> bool:

        validar(entrada, firma_hex, ahora)
        actual = self._entradas.get(entrada["id"])
        if actual is not None and actual[0]["creado"] >= entrada["creado"]:
            return False
        self._entradas[entrada["id"]] = (entrada, firma_hex)
        return True

    def purgar(self, ahora: float = None) -> list:
        vencidas = [i for i, (e, _) in self._entradas.items() if not esta_vigente(e, ahora)]
        for i in vencidas:
            del self._entradas[i]
        return vencidas

    def obtener(self, id_hex: str):
        return self._entradas.get(id_hex)

    def entradas(self) -> list:
        return [e for e, _ in self._entradas.values()]

    def para_transporte(self) -> list:
        return [serializar_para_transporte(e, f) for e, f in self._entradas.values()]

    def buscar_por_direccion(self, canal: str, direccion: str):
        for e, _ in self._entradas.values():
            if e["canal"] == canal and e["direccion"] == direccion:
                return e
        return None

    def gateways(self) -> list:
        return [e for e, _ in self._entradas.values() if e.get("rol") == "gateway"]

    def limpiar(self) -> None:
        self._entradas.clear()


    def __contains__(self, id_hex):
        return id_hex in self._entradas

    def __getitem__(self, id_hex):
        return self._entradas[id_hex]

    def __setitem__(self, id_hex, valor):
        self._entradas[id_hex] = valor

    def get(self, id_hex, defecto=None):
        return self._entradas.get(id_hex, defecto)

    def keys(self):
        return list(self._entradas.keys())

    def values(self):
        return list(self._entradas.values())

    def items(self):
        return list(self._entradas.items())

    def __len__(self):
        return len(self._entradas)

    def __iter__(self):
        return iter(list(self._entradas.keys()))
