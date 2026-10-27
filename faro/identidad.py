"""Identidad criptografica de un nodo: par de firma (Ed25519) y par de cifrado (X25519).

Las llaves se guardan en la memoria no volatil del Faro (la microSD de la
Raspberry), en la carpeta del nodo, con permisos 0600. El boton de panico
las sobrescribe con ceros y las borra (faro/panico.py).
"""
import os
from pathlib import Path

from nacl.public import PrivateKey
from nacl.signing import SigningKey

from faro.panico import panico

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


def _leer_llave(ruta: Path) -> bytes:
    datos = ruta.read_bytes()
    if len(datos) != 32:
        raise ValueError(f"llave danada en {ruta}: mide {len(datos)} bytes")
    return datos


def cargar_o_crear_firma(ruta: Path = RUTA_FIRMA) -> SigningKey:
    """Devuelve la llave de firma del nodo, creandola si no existe."""
    if ruta.exists():
        return SigningKey(_leer_llave(ruta))
    clave = SigningKey.generate()
    _escribir_privado(ruta, bytes(clave))
    return clave


def cargar_o_crear_cifrado(ruta: Path = RUTA_CIFRADO) -> PrivateKey:
    """Devuelve la llave de cifrado del nodo, creandola si no existe."""
    if ruta.exists():
        return PrivateKey(_leer_llave(ruta))
    clave = PrivateKey.generate()
    _escribir_privado(ruta, bytes(clave))
    return clave


def cargar_o_crear(carpeta: Path = CARPETA):
    """Devuelve (llave_firma, llave_cifrado) de la carpeta del nodo."""
    carpeta = Path(carpeta)
    return (cargar_o_crear_firma(carpeta / "firma.key"),
            cargar_o_crear_cifrado(carpeta / "cifrado.key"))


def borrar_todo(carpeta: Path = CARPETA) -> list:
    """Sobrescribe con ceros y borra todos los archivos de llaves. Parte del panico."""
    return panico(Path(carpeta))
