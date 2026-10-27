"""Cebolla de N saltos: capas con SealedBox y cabecera de siguiente salto (RFC 3.6).

- Capa del destino: SealedBox(0x00 || mensaje).
- Capa de cada relay: SealedBox(0x01 || cabecera(9B) || capa_interna).
- Cada capa de relay agrega 1 + 9 + 48 = 58 bytes.

La cabecera dice por que canal y a que direccion va la capa interna:
    CANAL 1B (0 = UDP, 1 = Faro) | SIGUIENTE 6B | LARGO 2B
SIGUIENTE es IPv4 (4B) + puerto (2B) para UDP, o direccion fisica (4B) +
0x0000 para Faro.

El relleno a 1024 bytes despues de quitar cada capa lo hace mesh/celda.py
y la fragmentacion para el Faro, mesh/enlace_faro.py.
"""
import struct

from nacl.public import PrivateKey, PublicKey, SealedBox

CANAL_UDP = 0
CANAL_FARO = 1

FORMATO_CABECERA = ">B6sH"          # canal, direccion, largo del contenido
LARGO_CABECERA = struct.calcsize(FORMATO_CABECERA)   # 9 bytes
LARGO_SOBRE = 48                    # overhead de SealedBox


class OnionError(Exception):
    """La celda esta mal formada o no se puede descifrar."""


def direccion_udp(ip: str, puerto: int) -> bytes:
    """Empaqueta una IP y un puerto en 6 bytes: 4 de IP + 2 de puerto."""
    partes = ip.split(".")
    if len(partes) != 4:
        raise OnionError(f"IP invalida: {ip}")
    try:
        ip_bytes = bytes(int(p) for p in partes)
    except ValueError:
        raise OnionError(f"IP invalida: {ip}")
    return ip_bytes + struct.pack(">H", puerto)


def direccion_faro(mac: bytes) -> bytes:
    """Empaqueta una direccion fisica de 4 bytes en los 6 de la cabecera."""
    if len(mac) != 4:
        raise OnionError("la direccion fisica debe medir 4 bytes")
    return mac + b"\x00\x00"


def direccion_de_entrada(canal: str, direccion: str):
    """Convierte (canal, direccion) del directorio en (CANAL, 6 bytes)."""
    if canal == "udp":
        ip, puerto = direccion.rsplit(":", 1)
        return CANAL_UDP, direccion_udp(ip, int(puerto))
    if canal == "faro":
        return CANAL_FARO, direccion_faro(bytes.fromhex(direccion))
    raise OnionError(f"canal desconocido: {canal}")


def direccion_a_texto(canal: int, dirs_6B: bytes):
    """Inverso de direccion_de_entrada: devuelve ('udp'|'faro', texto)."""
    if canal == CANAL_UDP:
        ip, puerto = leer_direccion_udp(dirs_6B)
        return "udp", f"{ip}:{puerto}"
    if canal == CANAL_FARO:
        return "faro", dirs_6B[:4].hex()
    raise OnionError(f"canal desconocido: {canal}")


def leer_direccion_udp(dirs_6B: bytes):
    """Desempaqueta los 6 bytes en (ip, puerto)."""
    if len(dirs_6B) != 6:
        raise OnionError("la direccion debe medir 6 bytes")
    ip = ".".join(str(b) for b in dirs_6B[:4])
    (puerto,) = struct.unpack(">H", dirs_6B[4:])
    return ip, puerto


def _empaquetar(canal: int, direccion: bytes, contenido: bytes) -> bytes:
    if len(direccion) != 6:
        raise OnionError("la direccion debe medir 6 bytes")
    if len(contenido) > 0xFFFF:
        raise OnionError("contenido demasiado grande para una sola celda")
    return struct.pack(FORMATO_CABECERA, canal, direccion, len(contenido)) + contenido


def _desempaquetar(plaintext: bytes):
    if len(plaintext) < LARGO_CABECERA:
        raise OnionError("celda demasiado corta")
    canal, direccion, largo = struct.unpack(
        FORMATO_CABECERA, plaintext[:LARGO_CABECERA])
    if len(plaintext) < LARGO_CABECERA + largo:
        raise OnionError("el largo declarado no coincide con el contenido")
    contenido = plaintext[LARGO_CABECERA:LARGO_CABECERA + largo]
    return canal, direccion, contenido


def construir_cebolla(destino_pubkey: PublicKey, saltos: list, mensaje: bytes) -> bytes:
    """Construye una cebolla de N saltos.

    Marca: 0x00 = capa del destino, 0x01 = capa de relay.
    """
    # Capa del destino.
    contenido_destino = b"\x00" + mensaje
    cell = SealedBox(destino_pubkey).encrypt(contenido_destino)
    # Capas de los relays, de adentro hacia afuera.
    for pubkey, canal, direccion in reversed(saltos):
        plaintext = b"\x01" + _empaquetar(canal, direccion, cell)
        cell = SealedBox(pubkey).encrypt(plaintext)
    return cell


def abrir_como_relay(cell: bytes, mi_privkey: PrivateKey):
    """Un relay abre su capa. Devuelve (canal, dir_siguiente, contenido_interno)."""
    try:
        plaintext = SealedBox(mi_privkey).decrypt(cell)
    except Exception as e:
        raise OnionError(f"no se pudo descifrar: {e}")
    if not plaintext or plaintext[0] != 0x01:
        raise OnionError("no es una capa de relay")
    return _desempaquetar(plaintext[1:])


def abrir_como_destino(cell: bytes, mi_privkey: PrivateKey) -> bytes:
    """El destinatario abre la capa final. Devuelve el mensaje."""
    try:
        plaintext = SealedBox(mi_privkey).decrypt(cell)
    except Exception as e:
        raise OnionError(f"no se pudo descifrar: {e}")
    if not plaintext or plaintext[0] != 0x00:
        raise OnionError("no es un mensaje para mi")
    return plaintext[1:]