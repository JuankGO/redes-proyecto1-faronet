"""Boton de panico: borra la direccion fisica y todas las llaves, sobrescribiendo con ceros.

La idea: si solo se borra el archivo, los bytes siguen en el disco hasta que
se reutilice el espacio. Sobrescribir con ceros primero hace que no queden
recuperables. Es parte del protocolo de panico.
"""
import os
from pathlib import Path

CARPETA = Path.home() / ".faronet"


def _sobrescribir_y_borrar(ruta: Path) -> None:
    """Sobrescribe el archivo con ceros y despues lo borra."""
    if not ruta.is_file():
        return
    largo = ruta.stat().st_size
    with open(ruta, "r+b") as f:
        f.write(b"\x00" * largo)
        f.flush()
        os.fsync(f.fileno())
    ruta.unlink()


def panico(carpeta: Path = CARPETA) -> list:
    """Borra todo lo que hay en la carpeta de FaroNet.

    Devuelve la lista de nombres de archivos borrados.
    Si la carpeta no existe, no falla: devuelve lista vacia.
    """
    borrados = []
    if not carpeta.exists():
        return borrados
    for archivo in sorted(carpeta.glob("*")):
        if archivo.is_file():
            _sobrescribir_y_borrar(archivo)
            borrados.append(archivo.name)
    return borrados


if __name__ == "__main__":
    # Si lo corres directo, te pide confirmacion. Asi no borras tus llaves por accidente.
    print("Esto va a borrar TODAS tus llaves y tu direccion fisica.")
    print(f"Carpeta: {CARPETA}")
    respuesta = input("Escribe SI en mayusculas para confirmar: ")
    if respuesta == "SI":
        borrados = panico()
        print("Borrados:", borrados)
    else:
        print("Cancelado.")