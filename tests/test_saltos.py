"""Pruebas de la eleccion de saltos: filtros, minimo de nodos, aleatoriedad."""
import pytest

from mesh.saltos import MINIMO_NODOS, SaltosError, elegir_saltos


def _entrada(i: int) -> dict:
    return {
        "v": 1,
        "id": f"{i:02x}" * 32,
        "cifrado": f"{i:02x}" * 32,
        "canal": "udp",
        "direccion": f"192.168.0.{i}:6000",
        "creado": 0,
        "ttl": 600,
    }


def _directorio(n: int) -> list:
    return [_entrada(i) for i in range(1, n + 1)]


def test_elige_la_cantidad_pedida():
    d = _directorio(10)
    saltos = elegir_saltos(d, _entrada(1)["id"], _entrada(2)["id"], cantidad=3)
    assert len(saltos) == 3


def test_los_saltos_son_distintos_entre_si():
    d = _directorio(10)
    saltos = elegir_saltos(d, _entrada(1)["id"], _entrada(2)["id"])
    ids = [s["id"] for s in saltos]
    assert len(set(ids)) == 3


def test_no_incluye_mi_id_ni_el_destino():
    d = _directorio(10)
    mi_id = _entrada(1)["id"]
    destino_id = _entrada(2)["id"]
    for _ in range(20):   # varias veces para reducir la chance de falso negativo
        saltos = elegir_saltos(d, mi_id, destino_id)
        ids = [s["id"] for s in saltos]
        assert mi_id not in ids
        assert destino_id not in ids


def test_falla_si_hay_pocos_nodos():
    d = _directorio(4)   # 2 utiles despues de quitar mi id y el destino
    with pytest.raises(SaltosError, match="anonimato"):
        elegir_saltos(d, _entrada(1)["id"], _entrada(2)["id"])


def test_ignora_duplicados_en_el_directorio():
    d = _directorio(8) + _directorio(8)   # todo duplicado
    saltos = elegir_saltos(d, _entrada(1)["id"], _entrada(2)["id"])
    ids = [s["id"] for s in saltos]
    assert len(set(ids)) == 3


def test_cantidad_invalida():
    d = _directorio(10)
    with pytest.raises(SaltosError, match="cantidad"):
        elegir_saltos(d, _entrada(1)["id"], _entrada(2)["id"], cantidad=0)


def test_entradas_sin_id_se_ignoran():
    d = _directorio(10) + [{"canal": "udp", "direccion": "x"}]   # sin id
    saltos = elegir_saltos(d, _entrada(1)["id"], _entrada(2)["id"])
    assert len(saltos) == 3