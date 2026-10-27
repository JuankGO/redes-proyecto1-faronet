"""Formato del mensaje de la app: 256 bytes fijos con padding aleatorio.

El tamano fijo evita que un observador deduzca cuanto se dijo por el
tamano del paquete. El TEMA se guarda como hash (8 bytes), no como
nombre en claro, para que quien vea la celda no sepa de que se habla.

Formato (256 bytes):
    | VER 1B | VISIBILIDAD 1B | TEMA 8B | HORA 4B | LARGO 2B | TEXTO ... | RELLENO |

Los mensajes viven poco: al recibirse se comprueba que no hayan vencido
segun TTL_POR_DEFECTO (y que no vengan del futuro). Se guardan solo en
memoria.

Mensajes publicos (VIS = 1, RFC seccion 4.4): el TEXTO empieza con el
nombre del tema, porque el gateway lo necesita para publicarlo:
    | N 1B | NOMBRE N bytes | texto |
"""
import re
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
TOLERANCIA_RELOJ = 300       # segundos que se acepta HORA en el futuro
MAX_NOMBRE_TEMA = 32
# Igual que el Worker: letras, numeros, _ y -, hasta 32 bytes (RFC 4.4).
_NOMBRE_TEMA = re.compile(r"[\w-]+")
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
    if hora > ahora + TOLERANCIA_RELOJ:
        raise MensajeError("mensaje con hora en el futuro")
    texto = datos[LARGO_CABECERA:LARGO_CABECERA + largo]
    return {
        "v": ver,
        "visibilidad": visibilidad,
        "tema": tema,
        "hora": hora,
        "largo": largo,
        "texto": texto,
    }

def nombre_tema_valido(nombre) -> bool:
    """Nombre de tema publico aceptable para la mesh y para el Worker."""
    return (isinstance(nombre, str) and 1 <= len(nombre.encode("utf-8")) <= MAX_NOMBRE_TEMA
            and _NOMBRE_TEMA.fullmatch(nombre) is not None)


def empaquetar_publico(nombre: str, texto: str, hora: int = None) -> bytes:
    """Arma un mensaje publico: TEXTO = N | NOMBRE | texto."""
    if not nombre_tema_valido(nombre):
        raise MensajeError(f"el nombre del tema debe tener 1-{MAX_NOMBRE_TEMA} bytes "
                           "de letras, numeros, _ o -")
    nombre_b = nombre.encode("utf-8")
    texto_b = texto.encode("utf-8")
    cuerpo = bytes([len(nombre_b)]) + nombre_b + texto_b
    if len(cuerpo) > MAX_TEXTO:
        raise MensajeError(f"texto demasiado largo: maximo {MAX_TEXTO - 1 - len(nombre_b)} bytes")
    return empaquetar_mensaje(PUBLICO, hash_tema(nombre), cuerpo, hora)


def leer_publico(d: dict):
    """Devuelve (nombre, texto) de un mensaje publico ya desempaquetado.

    Verifica que TEMA sea el hash del nombre. Lanza MensajeError si no.
    """
    if d.get("visibilidad") != PUBLICO:
        raise MensajeError("no es un mensaje publico")
    cuerpo = d["texto"]
    if not cuerpo:
        raise MensajeError("mensaje publico vacio")
    n = cuerpo[0]
    if not (1 <= n <= MAX_NOMBRE_TEMA) or len(cuerpo) < 1 + n:
        raise MensajeError("nombre de tema invalido")
    try:
        nombre = cuerpo[1:1 + n].decode("utf-8")
        texto = cuerpo[1 + n:].decode("utf-8")
    except UnicodeDecodeError:
        raise MensajeError("el mensaje publico no es UTF-8")
    if not nombre_tema_valido(nombre):
        raise MensajeError("nombre de tema invalido")
    if hash_tema(nombre) != d["tema"]:
        raise MensajeError("el TEMA no corresponde al nombre")
    return nombre, texto
