import os
import struct

TAMANO_CELDA = 1024
LARGO_PREFIJO = 2
MAX_CONTENIDO = TAMANO_CELDA - LARGO_PREFIJO
FORMATO_LARGO = ">H"


MAX_PAYLOAD_FARO = 114
MAX_FRAGMENTO = MAX_PAYLOAD_FARO - 4


class CeldaError(Exception):
    pass


def empaquetar_celda(contenido: bytes) -> bytes:

    if len(contenido) > MAX_CONTENIDO:
        raise CeldaError(
            f"contenido de {len(contenido)} bytes; maximo {MAX_CONTENIDO}"
        )
    prefijo = struct.pack(FORMATO_LARGO, len(contenido))
    relleno = os.urandom(TAMANO_CELDA - LARGO_PREFIJO - len(contenido))
    return prefijo + contenido + relleno


def desempaquetar_celda(celda: bytes) -> bytes:

    if len(celda) != TAMANO_CELDA:
        raise CeldaError(f"la celda debe medir {TAMANO_CELDA}B, mide {len(celda)}")
    (largo,) = struct.unpack(FORMATO_LARGO, celda[:LARGO_PREFIJO])
    if largo > MAX_CONTENIDO:
        raise CeldaError(f"largo declarado ({largo}) excede el maximo")
    return celda[LARGO_PREFIJO:LARGO_PREFIJO + largo]


def fragmentar(celda: bytes, tamano_fragmento: int = MAX_FRAGMENTO) -> list:

    if tamano_fragmento < 1:
        raise CeldaError("tamano de fragmento invalido")
    if len(celda) == 0:
        raise CeldaError("celda vacia")
    fragmentos = []
    total = (len(celda) + tamano_fragmento - 1) // tamano_fragmento
    if total > 0xFFFF:
        raise CeldaError("demasiados fragmentos")
    for i in range(total):
        trozo = celda[i * tamano_fragmento:(i + 1) * tamano_fragmento]
        prefijo = struct.pack(">HH", i, total)
        fragmentos.append(prefijo + trozo)
    return fragmentos


def reensamblar(fragmentos: list) -> bytes:

    if not fragmentos:
        raise CeldaError("no hay fragmentos")
    piezas = {}
    total = None
    for frag in fragmentos:
        if len(frag) < 4:
            raise CeldaError("fragmento demasiado corto")
        indice, t = struct.unpack(">HH", frag[:4])
        if t == 0 or indice >= t:
            raise CeldaError("indice de fragmento fuera de rango")
        if total is None:
            total = t
        elif t != total:
            raise CeldaError("los fragmentos declaran totales distintos")
        piezas[indice] = frag[4:]
    if total is None or len(piezas) != total:
        raise CeldaError(f"faltan fragmentos: {len(piezas)}/{total}")
    return b"".join(piezas[i] for i in range(total))
