"""Demo: celda de 512B, padding aleatorio, fragmentacion para el Faro.

Uso:
    python -m mesh.demo_celda
"""
from mesh.celda import (
    TAMANO_CELDA,
    desempaquetar_celda,
    empaquetar_celda,
    fragmentar,
    reensamblar,
)


def main():
    # 1. Celda con un contenido corto.
    contenido = b"hola, esto es un mensaje secreto"
    celda = empaquetar_celda(contenido)
    print(f"Contenido    : {len(contenido)} bytes")
    print(f"Celda        : {len(celda)} bytes (siempre {TAMANO_CELDA})")
    print(f"Padding      : {len(celda) - 2 - len(contenido)} bytes aleatorios")
    print()

    # 2. Otra celda con el MISMO contenido: el padding cambia.
    celda2 = empaquetar_celda(contenido)
    print(f"Otra celda con el mismo contenido, primeros bytes:")
    print(f"  celda1[2:10] = {celda[2:10].hex()}")
    print(f"  celda2[2:10] = {celda2[2:10].hex()}")
    print("  (distintos: el padding es aleatorio)")
    print()

    # 3. Desempaquetar devuelve el original.
    assert desempaquetar_celda(celda) == contenido
    assert desempaquetar_celda(celda2) == contenido
    print("Desempaquetar: OK")
    print()

    # 4. Fragmentar para el Faro.
    fragmentos = fragmentar(celda)
    print(f"Fragmentos   : {len(fragmentos)}")
    print(f"  tamano max : {max(len(f) for f in fragmentos)} bytes")
    print(f"  (deben caber en {114} bytes de payload del Faro)")
    print()

    # 5. Reensamblar (incluso si llegan desordenados o duplicados).
    desordenados = list(reversed(fragmentos)) + [fragmentos[0]]
    reensamblada = reensamblar(desordenados)
    assert reensamblada == celda
    print("Reensamblado desordenado con duplicado: OK")
    print()

    # 6. Detectar fragmentos faltantes.
    from mesh.celda import CeldaError
    try:
        reensamblar(fragmentos[:-1])
    except CeldaError as e:
        print(f"Faltan fragmentos -> CeldaError: {e}")


if __name__ == "__main__":
    main()