"""Pruebas de la cebolla: cada relay abre solo su capa, el destino recibe intacto."""
import pytest
from nacl.public import PrivateKey

from mesh.onion import (
    CANAL_UDP,
    OnionError,
    abrir_como_destino,
    abrir_como_relay,
    construir_cebolla,
    direccion_udp,
    leer_direccion_udp,
)


def _escenario():
    """Genera 3 relays y un destino, devuelve todo listo para usar."""
    r1, r2, r3, d = (PrivateKey.generate() for _ in range(4))
    dir_r2 = direccion_udp("192.168.0.12", 6002)
    dir_r3 = direccion_udp("192.168.0.13", 6003)
    dir_d = direccion_udp("192.168.0.14", 6004)
    saltos = [
        (r1.public_key, CANAL_UDP, dir_r2),   # R1 -> R2
        (r2.public_key, CANAL_UDP, dir_r3),   # R2 -> R3
        (r3.public_key, CANAL_UDP, dir_d),    # R3 -> D
    ]
    return r1, r2, r3, d, saltos, dir_r2, dir_r3, dir_d


def test_cebolla_llega_al_destino():
    r1, r2, r3, d, saltos, _, _, _ = _escenario()
    mensaje = b"hola destino final"
    celda = construir_cebolla(d.public_key, saltos, mensaje)
    _, _, interno = abrir_como_relay(celda, r1)
    _, _, interno = abrir_como_relay(interno, r2)
    _, _, interno = abrir_como_relay(interno, r3)
    assert abrir_como_destino(interno, d) == mensaje


def test_relay_no_ve_el_mensaje():
    """R1 no debe poder leer el contenido que le pasa a R2."""
    r1, r2, r3, d, saltos, _, _, _ = _escenario()
    celda = construir_cebolla(d.public_key, saltos, b"secreto muy privado")
    _, _, contenido = abrir_como_relay(celda, r1)
    assert b"secreto" not in contenido
    with pytest.raises(OnionError):
        abrir_como_destino(contenido, r1)


def test_relay_ve_solo_su_siguiente_salto():
    """R1 solo ve la direccion de R2, no la de R3 ni la del destino."""
    r1, r2, r3, d, saltos, dir_r2, dir_r3, dir_d = _escenario()
    celda = construir_cebolla(d.public_key, saltos, b"hola")
    _, dir_sig_r1, _ = abrir_como_relay(celda, r1)
    assert dir_sig_r1 == dir_r2
    assert dir_sig_r1 != dir_r3
    assert dir_sig_r1 != dir_d


def test_direccion_udp_ida_y_vuelta():
    d = direccion_udp("192.168.1.42", 7000)
    assert len(d) == 6
    assert leer_direccion_udp(d) == ("192.168.1.42", 7000)