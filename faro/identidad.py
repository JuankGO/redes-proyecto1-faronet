"""Identidad criptografica de un nodo: par de firma (Ed25519) y par de cifrado (Curve25519)."""
import os
from pathlib import Path

from nacl.public import PrivateKey
from nacl.signing import SigningKey

CARPETA = Path.home() / ".faronet"
RUTA_FIRMA = CARPETA / "firma.key"
RUTA_CIFRADO = CARPETA / "cifrado.key"


def _escribir_privado(ruta: Path, datos: bytes) -> None:
    """Escribe con permisos 0600 (solo el dueno puede leer)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(datos)
        f.flush()
        os.fsync(f.fileno())


def _leer_privado(ruta: Path) -> bytes:
    return ruta.read_bytes()


def cargar_o_crear_firma(ruta: Path = RUTA_FIRMA) -> SigningKey:
    """Devuelve la llave de firma del nodo, creandola si no existe."""
    if ruta.exists():
        return SigningKey(_leer_privado(ruta))
    clave = SigningKey.generate()
    _escribir_privado(ruta, bytes(clave))
    return clave


def cargar_o_crear_cifrado(ruta: Path = RUTA_CIFRADO) -> PrivateKey:
    """Devuelve la llave de cifrado del nodo, creandola si no existe."""
    if ruta.exists():
        return PrivateKey(_leer_privado(ruta))
    clave = PrivateKey.generate()
    _escribir_privado(ruta, bytes(clave))
    return clave


def borrar_todo(carpeta: Path = CARPETA) -> None:
    """Sobrescribe con ceros y borra todos los archivos de llaves. Parte del panico."""
    if not carpeta.exists():
        return
    for archivo in carpeta.glob("*"):
        if archivo.is_file():
            largo = archivo.stat().st_size
            with open(archivo, "r+b") as f:
                f.write(b"\x00" * largo)
                f.flush()
                os.fsync(f.fileno())
            archivo.unlink()