"""Pruebas del parsing de comandos del chat."""
import pytest

from app.comandos import (
    CMD_AYUDA,
    CMD_PRIV,
    CMD_PUBLICO,
    CMD_SALIR,
    CMD_TEMA,
    ComandoError,
    parsear_comando,
)


def test_priv_valido():
    cmd = parsear_comando("/priv A1B2C3D4 hola mundo")
    assert cmd.tipo == CMD_PRIV
    assert cmd.argumentos["destino"] == "a1b2c3d4"
    assert cmd.argumentos["texto"] == "hola mundo"


def test_priv_normaliza_destino_a_minusculas():
    cmd = parsear_comando("/priv AbCdEf12 texto")
    assert cmd.argumentos["destino"] == "abcdef12"


def test_priv_destino_corto_se_rechaza():
    with pytest.raises(ComandoError, match="8 letras"):
        parsear_comando("/priv a1b2 hola")


def test_priv_destino_no_hex_se_rechaza():
    with pytest.raises(ComandoError, match="hex"):
        parsear_comando("/priv zzzzzzzz hola")


def test_priv_sin_texto_se_rechaza():
    with pytest.raises(ComandoError, match="uso"):
        parsear_comando("/priv a1b2c3d4")


def test_tema_valido():
    cmd = parsear_comando("/tema amigos hola a todos")
    assert cmd.tipo == CMD_TEMA
    assert cmd.argumentos["tema"] == "amigos"
    assert cmd.argumentos["texto"] == "hola a todos"


def test_tema_con_texto_largo_se_acepta():
    texto = "x" * 200
    cmd = parsear_comando(f"/tema general {texto}")
    assert cmd.argumentos["texto"] == texto


def test_publico_valido():
    cmd = parsear_comando("/publico noticias algo nuevo")
    assert cmd.tipo == CMD_PUBLICO
    assert cmd.argumentos["tema"] == "noticias"


def test_salir_sin_argumentos():
    cmd = parsear_comando("/salir")
    assert cmd.tipo == CMD_SALIR


def test_salir_con_argumentos_se_rechaza():
    with pytest.raises(ComandoError):
        parsear_comando("/salir ya")


def test_ayuda():
    cmd = parsear_comando("/ayuda")
    assert cmd.tipo == CMD_AYUDA


def test_comando_desconocido():
    with pytest.raises(ComandoError, match="desconocido"):
        parsear_comando("/magia x y")


def test_linea_vacia_se_rechaza():
    with pytest.raises(ComandoError, match="vacia"):
        parsear_comando("")
    with pytest.raises(ComandoError, match="vacia"):
        parsear_comando("   ")


def test_linea_sin_slash_se_rechaza():
    with pytest.raises(ComandoError, match="empiezan"):
        parsear_comando("hola mundo")


def test_mayusculas_en_comando():
    cmd = parsear_comando("/PRIV a1b2c3d4 hola")
    assert cmd.tipo == CMD_PRIV


def test_tema_con_nombre_muy_largo_se_rechaza():
    nombre = "x" * 33
    with pytest.raises(ComandoError, match="1-32"):
        parsear_comando(f"/tema {nombre} hola")