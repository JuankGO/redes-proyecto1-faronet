"""Pruebas de celda: tamano fijo, padding, fragmentacion, reensamblado."""
import pytest

from mesh.celda import (
    MAX_CONTENIDO,
    MAX_FRAGMENTO,
    TAMANO_CELDA,
    CeldaError,
    desempaquetar_celda,
    empaquetar_celda,
    fragmentar,
    reensamblar,
)


def test_celda_siempre_mide_512():
    for n in (0, 1, 100, 400, MAX_CONTENIDO):
        celda = empaquetar_celda(b"x" * n)
        assert len(celda) == TAMANO_CELDA


def test_padding_es_aleatorio():
    a = empaquetar_celda(b"hola")
    b = empaquetar_celda(b"hola")
    # Mismo contenido, padding distinto -> celdas distintas.
    assert a != b
    # Pero ambas desempaquetan al mismo contenido.
    assert desempaquetar_celda(a) == b"hola"
    assert desempaquetar_celda(b) == b"hola"


def test_contenido_muy_grande_se_rechaza():
    with pytest.raises(CeldaError, match="maximo"):
        empaquetar_celda(b"x" * (MAX_CONTENIDO + 1))


def test_celda_de_tamano_incorrecto_se_rechaza():
    with pytest.raises(CeldaError, match="512"):
        desempaquetar_celda(b"x" * 100)


def test_fragmentar_y_reensamblar():
    contenido = b"y" * 400
    celda = empaquetar_celda(contenido)
    fragmentos = fragmentar(celda)
    assert all(len(f) <= 2 + 2 + MAX_FRAGMENTO for f in fragmentos)
    assert reensamblar(fragmentos) == celda


def test_reensamblar_en_desorden():
    celda = empaquetar_celda(b"z" * 500)
    fragmentos = fragmentar(celda)
    desorden = list(reversed(fragmentos))
    assert reensamblar(desorden) == celda


def test_reensamblar_ignora_duplicados():
    celda = empaquetar_celda(b"w" * 500)
    fragmentos = fragmentar(celda)
    duplicados = fragmentos + [fragmentos[0], fragmentos[1]]
    assert reensamblar(duplicados) == celda


def test_faltan_fragmentos():
    celda = empaquetar_celda(b"v" * 500)
    fragmentos = fragmentar(celda)
    with pytest.raises(CeldaError, match="faltan"):
        reensamblar(fragmentos[:-1])


def test_celda_vacia_no_se_fragmenta():
    with pytest.raises(CeldaError, match="vacia"):
        fragmentar(b"")