"""Celdas de tamano fijo (512 bytes) con padding, y fragmentacion para el Faro.

Una celda es la unidad que viaja por la red. Todas miden igual (512 bytes)
para que el tamano no delate en que salto va una celda ni cuanto se dijo.

Cuando la celda cruza un enlace del Faro (tramas de 128B con 114B de
payload), se fragmenta en varias tramas y el receptor la reensambla.

Formato de una celda:
    | LARGO 2B | CONTENIDO ... | PADDING aleatorio hasta 512B |

LARGO dice cuantos bytes del contenido son reales. El receptor ignora el
padding. El padding es aleatorio para que no se pueda distinguir de datos.
"""
import os
import struct

TAMANO_CELDA = 1024
LARGO_PREFIJO = 2                       # 2 bytes para el largo
MAX_CONTENIDO = TAMANO_CELDA - LARGO_PREFIJO  # 510 bytes
FORMATO_LARGO = ">H"

# Para fragmentacion en el Faro:
MAX_PAYLOAD_FARO = 114                  # viene de frame.MAX_PAYLOAD
MAX_FRAGMENTO = MAX_PAYLOAD_FARO - 4    # 2B indice + 2B total    


class CeldaError(Exception):
    """Celda mal formada o secuencia de fragmentos incompleta."""


def empaquetar_celda(contenido: bytes) -> bytes:
    """Mete el contenido en una celda de 512B con padding aleatorio."""
    if len(contenido) > MAX_CONTENIDO:
        raise CeldaError(
            f"contenido de {len(contenido)} bytes; maximo {MAX_CONTENIDO}"
        )
    prefijo = struct.pack(FORMATO_LARGO, len(contenido))
    relleno = os.urandom(TAMANO_CELDA - LARGO_PREFIJO - len(contenido))
    return prefijo + contenido + relleno


def desempaquetar_celda(celda: bytes) -> bytes:
    """Saca el contenido real de una celda, ignorando el padding."""
    if len(celda) != TAMANO_CELDA:
        raise CeldaError(f"la celda debe medir {TAMANO_CELDA}B, mide {len(celda)}")
    (largo,) = struct.unpack(FORMATO_LARGO, celda[:LARGO_PREFIJO])
    if largo > MAX_CONTENIDO:
        raise CeldaError(f"largo declarado ({largo}) excede el maximo")
    return celda[LARGO_PREFIJO:LARGO_PREFIJO + largo]


def fragmentar(celda: bytes, tamano_fragmento: int = MAX_FRAGMENTO) -> list:
    """Parte una celda en fragmentos con un indice de 2B al inicio.

    Cada fragmento mide a lo sumo (2 + tamano_fragmento) bytes, para que
    quepa en el payload de una trama del Faro.
    """
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
    """Junta los fragmentos en la celda original.

    Verifica que esten todos y en el orden correcto. Descarta duplicados
    silenciosamente (UDP puede duplicar).
    """
    if not fragmentos:
        raise CeldaError("no hay fragmentos")
    piezas = {}
    total = None
    for frag in fragmentos:
        if len(frag) < 4:
            raise CeldaError("fragmento demasiado corto")
        indice, t = struct.unpack(">HH", frag[:4])
        if total is None:
            total = t
        elif t != total:
            raise CeldaError("los fragmentos declaran totales distintos")
        piezas[indice] = frag[4:]
    if total is None or len(piezas) != total:
        raise CeldaError(f"faltan fragmentos: {len(piezas)}/{total}")
    return b"".join(piezas[i] for i in range(total))