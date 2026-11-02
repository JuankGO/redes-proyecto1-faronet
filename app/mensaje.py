import re
import hashlib
import os
import struct
import time

VERSION = 1
TAMANO_MENSAJE = 256
LARGO_CABECERA = 16
MAX_TEXTO = TAMANO_MENSAJE - LARGO_CABECERA

PRIVADO = 0
PUBLICO = 1

TTL_POR_DEFECTO = 3600
TOLERANCIA_RELOJ = 300
MAX_NOMBRE_TEMA = 32

_NOMBRE_TEMA = re.compile(r"[\w-]+")
FORMATO_CABECERA = ">BB8sIH"


class MensajeError(Exception):
    pass


def hash_tema(nombre: str) -> bytes:

    if not isinstance(nombre, str) or not nombre:
        raise MensajeError("el nombre del tema no puede estar vacio")
    return hashlib.blake2b(nombre.encode("utf-8"), digest_size=8).digest()


def empaquetar_mensaje(visibilidad: int, tema: bytes, texto: bytes,
                       hora: int = None) -> bytes:

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

    return (isinstance(nombre, str) and 1 <= len(nombre.encode("utf-8")) <= MAX_NOMBRE_TEMA
            and _NOMBRE_TEMA.fullmatch(nombre) is not None)


def empaquetar_publico(nombre: str, texto: str, hora: int = None) -> bytes:

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
