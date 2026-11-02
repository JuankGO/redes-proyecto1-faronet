import os
from pathlib import Path

CARPETA = Path.home() / ".faronet"


def _sobrescribir_y_borrar(ruta: Path) -> None:

    if not ruta.is_file():
        return
    largo = ruta.stat().st_size
    with open(ruta, "r+b") as f:
        f.write(b"\x00" * largo)
        f.flush()
        os.fsync(f.fileno())
    ruta.unlink()


def panico(carpeta: Path = CARPETA) -> list:

    borrados = []
    if not carpeta.exists():
        return borrados
    for archivo in sorted(carpeta.glob("*")):
        if archivo.is_file():
            _sobrescribir_y_borrar(archivo)
            borrados.append(archivo.name)
    return borrados


if __name__ == "__main__":

    print("Esto va a borrar TODAS tus llaves y tu direccion fisica.")
    print(f"Carpeta: {CARPETA}")
    respuesta = input("Escribe SI en mayusculas para confirmar: ")
    if respuesta == "SI":
        borrados = panico()
        print("Borrados:", borrados)
    else:
        print("Cancelado.")
