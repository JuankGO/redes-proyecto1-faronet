"""Elegir los 3 saltos de la cebolla a partir del directorio.

Reglas:
- No puede ser yo mismo.
- No puede ser el destino.
- Tienen que ser 3 nodos distintos.
- Aleatoriedad criptografica (SystemRandom), no la del modulo random normal.

Si el directorio tiene menos de MINIMO_NODOS, la red no es suficientemente
anonima: se lanza un aviso claro en lugar de elegir mal.
"""
import random

MINIMO_NODOS = 5


class SaltosError(Exception):
    """No hay suficientes nodos para armar una cebolla anonima."""


def _candidatos(directorio: list, mi_id: str, destino_id: str) -> list:
    """Filtra el directorio: quita mi id, el destino y duplicados."""
    vistos = set()
    candidatos = []
    for entrada in directorio:
        id_hex = entrada.get("id")
        if not id_hex:
            continue
        if id_hex == mi_id or id_hex == destino_id:
            continue
        if id_hex in vistos:
            continue
        vistos.add(id_hex)
        candidatos.append(entrada)
    return candidatos


def elegir_saltos(directorio: list, mi_id: str, destino_id: str,
                  cantidad: int = 3) -> list:
    """Devuelve 'cantidad' entradas distintas del directorio, al azar.

    Lanza SaltosError si no hay suficientes nodos para garantizar anonimato.
    """
    if cantidad < 1:
        raise SaltosError("cantidad debe ser al menos 1")
    candidatos = _candidatos(directorio, mi_id, destino_id)
    if len(candidatos) < MINIMO_NODOS:
        raise SaltosError(
            f"directorio con {len(candidatos)} nodos utiles; "
            f"se necesitan al menos {MINIMO_NODOS} para anonimato aceptable"
        )
    if len(candidatos) < cantidad:
        raise SaltosError(
            f"no hay suficientes candidatos ({len(candidatos)}) "
            f"para elegir {cantidad} saltos"
        )
    rng = random.SystemRandom()
    return rng.sample(candidatos, cantidad)