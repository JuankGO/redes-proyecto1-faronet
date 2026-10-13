"""Codificacion de linea Manchester y deteccion del inicio de trama."""
PREAMBULO = b"\xAA\xAA\xAA\xAA"
SFD = b"\xD5"


class LineaError(Exception):
    pass


def bytes_a_bits(datos: bytes) -> list:
    return [(b >> i) & 1 for b in datos for i in range(7, -1, -1)]


def bits_a_bytes(bits: list) -> bytes:
    if len(bits) % 8:
        raise LineaError("la cantidad de bits no es multiplo de 8")
    salida = bytearray()
    for i in range(0, len(bits), 8):
        valor = 0
        for bit in bits[i:i + 8]:
            valor = (valor << 1) | bit
        salida.append(valor)
    return bytes(salida)


def manchester_codificar(bits: list) -> list:
    """1 -> [0,1] (sube) ; 0 -> [1,0] (baja)."""
    medios = []
    for bit in bits:
        medios += [0, 1] if bit == 1 else [1, 0]
    return medios


def manchester_decodificar(medios: list) -> list:
    if len(medios) % 2:
        raise LineaError("cantidad impar de medios bits")
    bits = []
    for i in range(0, len(medios), 2):
        par = (medios[i], medios[i + 1])
        if par == (0, 1):
            bits.append(1)
        elif par == (1, 0):
            bits.append(0)
        else:
            raise LineaError("par invalido: no hay transicion")
    return bits


def armar_senal(trama_bytes: bytes) -> list:
    """Preambulo + SFD + trama, todo en Manchester."""
    return manchester_codificar(bytes_a_bits(PREAMBULO + SFD + trama_bytes))


_SYNC = bytes_a_bits(b"\xAA" + SFD)


def _buscar(bits: list, patron: list):
    n = len(patron)
    for i in range(len(bits) - n + 1):
        if bits[i:i + n] == patron:
            return i
    return None


def extraer_trama(medios: list) -> bytes:
    """Devuelve los bytes de la trama (cabecera+payload+CRC) dentro de una senal."""
    for desfase in (0, 1):
        util = medios[desfase:]
        util = util[:len(util) - (len(util) % 2)]
        try:
            bits = manchester_decodificar(util)
        except LineaError:
            continue
        pos = _buscar(bits, _SYNC)
        if pos is None:
            continue
        resto = bits[pos + len(_SYNC):]
        if len(resto) < 12 * 8:
            continue
        largo = bits_a_bytes(resto[:12 * 8])[11]
        total = (12 + largo + 2) * 8
        if len(resto) < total:
            continue
        return bits_a_bytes(resto[:total])
    raise LineaError("no se encontro ninguna trama")
