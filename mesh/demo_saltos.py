"""Demo: elegir 3 saltos al azar de un directorio ficticio.

Uso:
    python -m mesh.demo_saltos
"""
from mesh.saltos import SaltosError, elegir_saltos


def _directorio_ficticio(n):
    return [
        {
            "v": 1,
            "id": f"{i:02x}" * 32,
            "cifrado": f"{i:02x}" * 32,
            "canal": "udp",
            "direccion": f"192.168.0.{i}:60{i:02d}",
            "creado": 0,
            "ttl": 600,
        }
        for i in range(1, n + 1)
    ]


def main():
    directorio = _directorio_ficticio(8)
    mi_id = f"{1:02x}" * 32        # nodo 1
    destino_id = f"{2:02x}" * 32   # nodo 2

    print(f"Directorio: {len(directorio)} nodos")
    print(f"Yo soy el nodo 1, el destino es el nodo 2")
    print()

    for intento in range(3):
        saltos = elegir_saltos(directorio, mi_id, destino_id)
        ids = [s["id"][:4] for s in saltos]
        dirs = [s["direccion"] for s in saltos]
        print(f"Intento {intento + 1}: ids={ids} dirs={dirs}")

    print()

    # Con solo 4 nodos no hay suficiente anonimato.
    directorio_chico = _directorio_ficticio(4)
    try:
        elegir_saltos(directorio_chico, mi_id, destino_id)
        print("ERROR: no debio permitir directorio chico")
    except SaltosError as e:
        print(f"Directorio chico -> SaltosError: {e}")


if __name__ == "__main__":
    main()