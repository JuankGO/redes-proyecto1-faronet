import pytest
from faro import frame, linea


def test_crc_valor_conocido():
    assert frame.crc16(b"123456789") == 0x29B1


def test_ida_y_vuelta():
    t = frame.Trama(frame.TIPO_DATA, b"\x01\x02\x03\x04", b"\x0a\x0b\x0c\x0d", 7, b"hola")
    assert frame.decodificar(frame.codificar(t)) == t


def test_maximo_128():
    t = frame.Trama(frame.TIPO_DATA, b"\x01" * 4, b"\x02" * 4, 0, b"x" * frame.MAX_PAYLOAD)
    assert len(frame.codificar(t)) == 128
    with pytest.raises(frame.TramaError):
        frame.codificar(frame.Trama(1, b"\x01" * 4, b"\x02" * 4, 0, b"x" * 115))


def test_un_bit_cambiado_se_detecta():
    crudo = bytearray(frame.codificar(frame.Trama(1, b"\x01" * 4, b"\x02" * 4, 1, b"hola")))
    crudo[13] ^= 0x01
    with pytest.raises(frame.TramaError):
        frame.decodificar(bytes(crudo))


def test_version_futura_rechazada():
    t = frame.Trama(1, b"\x01" * 4, b"\x02" * 4, 1, b"hi", version=9)
    with pytest.raises(frame.TramaError):
        frame.decodificar(frame.codificar(t))


def test_manchester_y_sincronizacion():
    crudo = frame.codificar(frame.Trama(1, b"\x01" * 4, b"\x02" * 4, 1, b"hola mundo"))
    senal = linea.armar_senal(crudo)
    assert linea.extraer_trama(senal) == crudo
    assert linea.extraer_trama([0, 0, 1] + senal) == crudo   # ruido al inicio
    assert linea.extraer_trama([1] + senal) == crudo         # desfase de medio bit
