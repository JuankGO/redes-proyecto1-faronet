"""Pruebas del directorio: firma valida, firma falsa, TTL, manipulacion."""
import time

import pytest
from nacl.public import PrivateKey
from nacl.signing import SigningKey

from mesh.directorio import (
    DirectorioError,
    a_bytes,
    crear_entrada,
    esta_vigente,
    firmar,
    validar,
    verificar,
)


def _entrada_valida(ttl=600):
    firma = SigningKey.generate()
    cifrado = PrivateKey.generate()
    entrada = crear_entrada(firma, cifrado, "udp", "192.168.0.10:6001", ttl=ttl)
    return entrada, firmar(entrada, firma), firma


def test_entrada_valida_pasa_validacion():
    entrada, firma_hex, _ = _entrada_valida()
    assert verificar(entrada, firma_hex) is True
    validar(entrada, firma_hex)  # no lanza


def test_firma_falsa_se_rechaza():
    entrada, firma_hex, _ = _entrada_valida()
    firma_mala = "00" * 64
    assert verificar(entrada, firma_mala) is False
    with pytest.raises(DirectorioError, match="firma invalida"):
        validar(entrada, firma_mala)


def test_manipulacion_se_detecta():
    entrada, firma_hex, _ = _entrada_valida()
    entrada["direccion"] = "10.0.0.99:6001"
    assert verificar(entrada, firma_hex) is False
    with pytest.raises(DirectorioError):
        validar(entrada, firma_hex)


def test_entrada_vencida_se_rechaza():
    entrada, firma_hex, _ = _entrada_valida(ttl=10)
    futuro = time.time() + 60
    assert esta_vigente(entrada, ahora=futuro) is False
    with pytest.raises(DirectorioError, match="vencida"):
        validar(entrada, firma_hex, ahora=futuro)


def test_version_futura_se_rechaza():
    entrada, firma_hex, firma = _entrada_valida()
    entrada["v"] = 99
    firma_hex = firmar(entrada, firma)   # refirmamos con la nueva version
    with pytest.raises(DirectorioError, match="version"):
        validar(entrada, firma_hex)


def test_bytes_canonicos_son_estables():
    entrada, _, _ = _entrada_valida()
    # Mismo dict, orden de claves distinto -> mismos bytes.
    reordenada = {k: entrada[k] for k in sorted(entrada, reverse=True)}
    assert a_bytes(entrada) == a_bytes(reordenada)


def test_canal_invalido_se_rechaza():
    firma = SigningKey.generate()
    cifrado = PrivateKey.generate()
    with pytest.raises(DirectorioError, match="canal"):
        crear_entrada(firma, cifrado, "paloma", "x", ttl=100)


def test_ttl_fuera_de_rango_se_rechaza():
    firma = SigningKey.generate()
    cifrado = PrivateKey.generate()
    with pytest.raises(DirectorioError, match="ttl"):
        crear_entrada(firma, cifrado, "udp", "x", ttl=0)
    with pytest.raises(DirectorioError, match="ttl"):
        crear_entrada(firma, cifrado, "udp", "x", ttl=999999)