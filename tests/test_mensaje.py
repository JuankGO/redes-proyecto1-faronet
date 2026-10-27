"""Pruebas del formato del mensaje: tamano fijo, padding, TTL, validaciones."""
import time

import pytest

from app.mensaje import (
    MAX_TEXTO,
    PRIVADO,
    PUBLICO,
    TAMANO_MENSAJE,
    TTL_POR_DEFECTO,
    MensajeError,
    desempaquetar_mensaje,
    empaquetar_mensaje,
    hash_tema,
)


TEMA = hash_tema("prueba")


def test_mensaje_siempre_mide_256():
    for n in (0, 1, 100, MAX_TEXTO):
        m = empaquetar_mensaje(PRIVADO, TEMA, b"x" * n)
        assert len(m) == TAMANO_MENSAJE


def test_ida_y_vuelta():
    m = empaquetar_mensaje(PRIVADO, TEMA, b"hola mundo")
    leido = desempaquetar_mensaje(m)
    assert leido["visibilidad"] == PRIVADO
    assert leido["tema"] == TEMA
    assert leido["texto"] == b"hola mundo"


def test_padding_es_aleatorio():
    a = empaquetar_mensaje(PRIVADO, TEMA, b"hola")
    b = empaquetar_mensaje(PRIVADO, TEMA, b"hola")
    assert a != b
    assert desempaquetar_mensaje(a)["texto"] == b"hola"
    assert desempaquetar_mensaje(b)["texto"] == b"hola"


def test_visibilidad_se_conserva():
    priv = desempaquetar_mensaje(empaquetar_mensaje(PRIVADO, TEMA, b"x"))
    pub = desempaquetar_mensaje(empaquetar_mensaje(PUBLICO, TEMA, b"x"))
    assert priv["visibilidad"] == PRIVADO
    assert pub["visibilidad"] == PUBLICO


def test_texto_muy_largo_se_rechaza():
    with pytest.raises(MensajeError, match="maximo"):
        empaquetar_mensaje(PRIVADO, TEMA, b"x" * (MAX_TEXTO + 1))


def test_tema_de_tamano_incorrecto_se_rechaza():
    with pytest.raises(MensajeError, match="8 bytes"):
        empaquetar_mensaje(PRIVADO, b"corto", b"x")


def test_visibilidad_invalida_se_rechaza():
    with pytest.raises(MensajeError, match="visibilidad"):
        empaquetar_mensaje(9, TEMA, b"x")


def test_mensaje_de_tamano_incorrecto_se_rechaza():
    with pytest.raises(MensajeError, match="256"):
        desempaquetar_mensaje(b"x" * 100)


def test_mensaje_vencido_se_rechaza():
    m = empaquetar_mensaje(PRIVADO, TEMA, b"hola")
    futuro = time.time() + TTL_POR_DEFECTO + 60
    with pytest.raises(MensajeError, match="vencido"):
        desempaquetar_mensaje(m, ahora=futuro)


def test_mensaje_recien_creado_no_esta_vencido():
    m = empaquetar_mensaje(PRIVADO, TEMA, b"hola")
    leido = desempaquetar_mensaje(m)   # ahora por defecto
    assert leido["texto"] == b"hola"


def test_hash_tema_es_estable():
    assert hash_tema("amigos") == hash_tema("amigos")
    assert hash_tema("amigos") != hash_tema("enemigos")
    assert len(hash_tema("x")) == 8


def test_hash_tema_vacio_se_rechaza():
    with pytest.raises(MensajeError):
        hash_tema("")

def test_nombre_de_tema_publico_igual_que_el_worker():
    import pytest
    from app.mensaje import MensajeError, empaquetar_publico, nombre_tema_valido
    for bueno in ["noticias", "fútbol", "tema_1-2", "ñ" * 16]:
        assert nombre_tema_valido(bueno)
    for malo in ["", "mi tema", "a/b", "<script>", "x" * 33, "ñ" * 17, "ok\n"]:
        assert not nombre_tema_valido(malo)
    with pytest.raises(MensajeError):
        empaquetar_publico("mi tema", "hola")
