"""Trama Faro v1: construir (codificar) y leer (decodificar) tramas de maximo 128 bytes."""
import struct
from dataclasses import dataclass

VERSION = 1
MAX_TRAMA = 128
FORMATO_CABECERA = ">BB4s4sBB"          # VER, TIPO, DST, SRC, SEQ, LEN
LARGO_CABECERA = struct.calcsize(FORMATO_CABECERA)   # 12 bytes
LARGO_CRC = 2
MAX_PAYLOAD = MAX_TRAMA - LARGO_CABECERA - LARGO_CRC # 114 bytes
BROADCAST = b"\xff\xff\xff\xff"

TIPO_DATA = 1
TIPO_ACK = 2
TIPO_BEACON = 3


class TramaError(Exception):
    """La trama esta mal formada, danada o es de una version desconocida."""


def crc16(datos: bytes) -> int:
    """CRC-16/CCITT-FALSE (polinomio 0x1021, valor inicial 0xFFFF)."""
    crc = 0xFFFF
    for byte in datos:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


@dataclass
class Trama:
    tipo: int
    dst: bytes
    src: bytes
    seq: int
    payload: bytes = b""
    version: int = VERSION


def codificar(t: Trama) -> bytes:
    if len(t.payload) > MAX_PAYLOAD:
        raise TramaError(f"payload de {len(t.payload)} bytes; maximo {MAX_PAYLOAD}")
    if len(t.dst) != 4 or len(t.src) != 4:
        raise TramaError("las direcciones deben medir 4 bytes")
    cabecera = struct.pack(FORMATO_CABECERA, t.version, t.tipo,
                           t.dst, t.src, t.seq, len(t.payload))
    cuerpo = cabecera + t.payload
    return cuerpo + struct.pack(">H", crc16(cuerpo))


def decodificar(crudo: bytes) -> Trama:
    if len(crudo) < LARGO_CABECERA + LARGO_CRC:
        raise TramaError("trama demasiado corta")
    if len(crudo) > MAX_TRAMA:
        raise TramaError("trama demasiado larga")
    version, tipo, dst, src, seq, largo = struct.unpack(
        FORMATO_CABECERA, crudo[:LARGO_CABECERA])
    if version < 1 or version > VERSION:
        raise TramaError(f"version {version} no soportada")
    if len(crudo) != LARGO_CABECERA + largo + LARGO_CRC:
        raise TramaError("el largo declarado no coincide")
    (crc_recibido,) = struct.unpack(">H", crudo[-2:])
    if crc16(crudo[:-2]) != crc_recibido:
        raise TramaError("CRC incorrecto (trama danada)")
    return Trama(tipo, dst, src, seq,
                 crudo[LARGO_CABECERA:LARGO_CABECERA + largo], version)
