"""Formato del mensaje de la app: 256 bytes fijos con padding aleatorio.

El tamano fijo evita que un observador deduzca cuanto se dijo por el
tamano del paquete. El TEMA se guarda como hash (8 bytes), no como
nombre en claro, para que quien vea la celda no sepa de que se habla.

Formato (256 bytes):
    | VER 1B | VISIBILIDAD 1B | TEMA 8B | HORA 4B | LARGO 2B | TEXTO ... | RELLENO |

Los mensajes viven poco: al recibirse se comprueba que no hayan vencido
segun TTL_POR_DEFECTO. Se guardan solo en memoria.
"""
import hashlib
import os
import struct
import time

VERSION = 1
TAMANO_MENSAJE = 256
LARGO_CABECERA = 16          # 1+1+8+4+2
MAX_TEXTO = TAMANO_MENSAJE - LARGO_CABECERA   # 240

PRIVADO = 0
PUBLICO = 1

TTL_POR_DEFECTO = 3600       # 1 hora
FORMATO_CABECERA = ">BB8sIH"  # ver, visibilidad, tema, hora, largo


class MensajeError(Exception):
    """El mensaje esta mal formado, vencido o tiene una version desconocida."""


def hash_tema(nombre: str) -> bytes:
    """Devuelve 8 bytes de hash del nombre del tema."""
    if not isinstance(nombre, str) or not nombre:
        raise MensajeError("el nombre del tema no puede estar vacio")
    return hashlib.blake2b(nombre.encode("utf-8"), digest_size=8).digest()


def empaquetar_mensaje(visibilidad: int, tema: bytes, texto: bytes,
                       hora: int = None) -> bytes:
    """Arma un mensaje de 256 bytes con padding aleatorio."""
    if visibilidad not in (PRIVADO, PUBLICO):
        raise MensajeError(f"visibilidad invalida: {visibilidad}")
    if len(tema) != 8:
        raise MensajeError("el tema debe medir 8 bytes")
    if not isinstance(texto, (bytes, bytearray)):
        raise MensajeError("el texto debe ser bytes")
    if len(texto) > MAX_TEXTO:
        raise MensajeError(f"texto de {len(texto)}B; maximo {MAX_TEXTO}")
    if hora is None:
        hora = int(time.time())
    cabecera = struct.pack(FORMATO_CABECERA, VERSION, visibilidad,
                           tema, hora, len(texto))
    relleno = os.urandom(TAMANO_MENSAJE - LARGO_CABECERA - len(texto))
    return cabecera + bytes(texto) + relleno


def desempaquetar_mensaje(datos: bytes, ahora: float = None) -> dict:
    """Lee un mensaje. Lanza MensajeError si algo no cuadra."""
    if len(datos) != TAMANO_MENSAJE:
        raise MensajeError(
            f"el mensaje debe medir {TAMANO_MENSAJE}B, mide {len(datos)}"
        )
    ver, visibilidad, tema, hora, largo = struct.unpack(
        FORMATO_CABECERA, datos[:LARGO_CABECERA])
    if ver > VERSION:
        raise MensajeError(f"version {ver} no soportada")
    if visibilidad not in (PRIVADO, PUBLICO):
        raise MensajeError(f"visibilidad invalida: {visibilidad}")
    if largo > MAX_TEXTO:
        raise MensajeError(f"largo declarado ({largo}) excede el maximo")
    if ahora is None:
        ahora = time.time()
    if (ahora - hora) >= TTL_POR_DEFECTO:
        raise MensajeError("mensaje vencido")
    texto = datos[LARGO_CABECERA:LARGO_CABECERA + largo]
    return {
        "v": ver,
        "visibilidad": visibilidad,
        "tema": tema,
        "hora": hora,
        "largo": largo,
        "texto": texto,
    }