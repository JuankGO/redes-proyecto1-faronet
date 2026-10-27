"""Direccion fisica de 4 bytes (RFC, seccion 2.7).

Se guarda en la memoria no volatil del Faro (archivo en la microSD), se
rota en cada arranque y bajo demanda, y el panico la borra con ceros.
"""
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
        valor = ruta.read_bytes()
        if len(valor) == 4 and valor not in (b"\xff" * 4, b"\x00" * 4):
            return valor
    return rotar(ruta)


def nueva() -> bytes:
    """Genera una direccion aleatoria valida (sin guardarla)."""
    valor = secrets.token_bytes(4)
    while valor in (b"\xff\xff\xff\xff", b"\x00\x00\x00\x00"):
        valor = secrets.token_bytes(4)
    return valor


def rotar(ruta: Path = RUTA) -> bytes:
    """Genera una direccion nueva y la guarda sobrescribiendo la anterior."""
    valor = nueva()
    _escribir(ruta, valor)
    return valor


def borrar_seguro(ruta: Path = RUTA) -> None:
    """Zeroize: sobreescribe con ceros y luego borra."""
    if ruta.exists():
        _escribir(ruta, b"\x00" * 4)
        ruta.unlink()
