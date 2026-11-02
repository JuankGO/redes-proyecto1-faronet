import os
from pathlib import Path

from nacl.public import PrivateKey
from nacl.signing import SigningKey

from faro.panico import panico

CARPETA = Path.home() / ".faronet"
RUTA_FIRMA = CARPETA / "firma.key"
RUTA_CIFRADO = CARPETA / "cifrado.key"


def _escribir_privado(ruta: Path, datos: bytes) -> None:

    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(datos)
        f.flush()
        os.fsync(f.fileno())


def _leer_llave(ruta: Path) -> bytes:
    datos = ruta.read_bytes()
    if len(datos) != 32:
        raise ValueError(f"llave danada en {ruta}: mide {len(datos)} bytes")
    return datos


def cargar_o_crear_firma(ruta: Path = RUTA_FIRMA) -> SigningKey:

    if ruta.exists():
        return SigningKey(_leer_llave(ruta))
    clave = SigningKey.generate()
    _escribir_privado(ruta, bytes(clave))
    return clave


def cargar_o_crear_cifrado(ruta: Path = RUTA_CIFRADO) -> PrivateKey:

    if ruta.exists():
        return PrivateKey(_leer_llave(ruta))
    clave = PrivateKey.generate()
    _escribir_privado(ruta, bytes(clave))
    return clave


def cargar_o_crear(carpeta: Path = CARPETA):

    carpeta = Path(carpeta)
    return (cargar_o_crear_firma(carpeta / "firma.key"),
            cargar_o_crear_cifrado(carpeta / "cifrado.key"))


def borrar_todo(carpeta: Path = CARPETA) -> list:

    return panico(Path(carpeta))
