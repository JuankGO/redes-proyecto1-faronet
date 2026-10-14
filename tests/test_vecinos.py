"""Pruebas de la tabla de vecinos: registro, actualizacion y olvido."""
import pytest

from mesh.vecinos import (
    TablaVecinos,
    VecinoError,
    crear_hello,
    parsear_hello,
)

ID_A = "aa" * 32
ID_B = "bb" * 32


def test_hello_ida_y_vuelta():
    hello = crear_hello(ID_A, "udp", "192.168.0.10:6001")
    mensaje = parsear_hello(hello)
    assert mensaje["t"] == "hello"
    assert mensaje["id"] == ID_A
    assert mensaje["canal"] == "udp"
    assert mensaje["dir"] == "192.168.0.10:6001"
    assert isinstance(mensaje["ts"], int)


def test_canal_invalido_se_rechaza():
    with pytest.raises(VecinoError, match="canal"):
        crear_hello(ID_A, "paloma", "x")


def test_hello_mal_formado_se_rechaza():
    with pytest.raises(VecinoError):
        parsear_hello(b"esto no es json")
    with pytest.raises(VecinoError):
        parsear_hello(b'{"t":"hello"}')      # faltan campos
    with pytest.raises(VecinoError):
        parsear_hello(b'{"t":"otro","id":"aa","canal":"udp","dir":"x","ts":1}')


def test_registrar_y_listar():
    tabla = TablaVecinos()
    hello_a = crear_hello(ID_A, "udp", "10.0.0.1:6001")
    hello_b = crear_hello(ID_B, "faro", "deadbeef")

    assert tabla.registrar(parsear_hello(hello_a), ahora=100.0) is True
    assert tabla.registrar(parsear_hello(hello_b), ahora=100.0) is True
    assert len(tabla) == 2

    vecinos = tabla.listar()
    assert vecinos[0][0] == ID_A
    assert vecinos[1][0] == ID_B


def test_registrar_repetido_no_es_nuevo():
    tabla = TablaVecinos()
    hello = crear_hello(ID_A, "udp", "10.0.0.1:6001")
    assert tabla.registrar(parsear_hello(hello), ahora=100.0) is True
    assert tabla.registrar(parsear_hello(hello), ahora=105.0) is False
    # El "visto" se actualiza.
    assert tabla.obtener(ID_A)["visto"] == 105.0


def test_olvidar_vencidos():
    tabla = TablaVecinos(timeout=30.0)
    tabla.registrar(parsear_hello(crear_hello(ID_A, "udp", "10.0.0.1:6001")), ahora=100.0)
    tabla.registrar(parsear_hello(crear_hello(ID_B, "faro", "deadbeef")), ahora=120.0)

    # A los 135s: A lleva 35s sin senal (vencido), B solo 15s (vivo).
    vencidos = tabla.olvidar_vencidos(ahora=135.0)
    assert vencidos == [ID_A]
    assert len(tabla) == 1
    assert tabla.obtener(ID_B) is not None


def test_obtener_vecino_inexistente():
    tabla = TablaVecinos()
    assert tabla.obtener("ff" * 32) is None