"""Direccion fisica de 4 bytes: se guarda en un archivo, se puede rotar y borrar."""
import os
import secrets
from pathlib import Path

RUTA = Path.home() / ".faronet" / "direccion.bin"


def _escribir(ruta: Path, valor: bytes) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(ruta, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(valor)
        f.flush()
        os.fsync(f.fileno())


def cargar_o_crear(ruta: Path = RUTA) -> bytes:
    if ruta.exists():
        return ruta.read_bytes()
    return rotar(ruta)


def rotar(ruta: Path = RUTA) -> bytes:
    nueva = secrets.token_bytes(4)
    while nueva in (b"\xff\xff\xff\xff", b"\x00\x00\x00\x00"):
        nueva = secrets.token_bytes(4)
    _escribir(ruta, nueva)
    return nueva


def borrar_seguro(ruta: Path = RUTA) -> None:
    """Zeroize: sobreescribe con ceros y luego borra."""
    if ruta.exists():
        _escribir(ruta, b"\x00" * 4)
        ruta.unlink()
