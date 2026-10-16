"""Demo de enrutamiento por vector de distancias.

Topologia lineal:  A -- B -- C -- D -- E
Al inicio cada nodo solo conoce a sus vecinos directos.
Tras varias rondas de anuncios, A aprende a llegar a E en 4 saltos.

Uso:
    python -m mesh.demo_rutas
"""
from mesh.rutas import TablaRutas

NODOS = ["A", "B", "C", "D", "E"]
ENLACES = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")]


def _imprimir(tablas, ronda):
    print(f"\nRonda {ronda}:")
    for n in NODOS:
        rutas = tablas[n].listar()
        if rutas:
            filas = ", ".join(f"{d}->{sig}({s})" for d, sig, s in rutas)
            print(f"  {n}: {filas}")
        else:
            print(f"  {n}: (vacia)")


def main():
    # 1. Cada nodo con su tabla, y aprende a sus vecinos directos.
    tablas = {n: TablaRutas(n) for n in NODOS}
    for a, b in ENLACES:
        tablas[a].aprender_vecino_directo(b, ahora=0)
        tablas[b].aprender_vecino_directo(a, ahora=0)

    _imprimir(tablas, 0)

    # 2. Rondas sincronicas de anuncios. En cada ronda, todos anuncian
    #    su tabla actual y todos aplican los anuncios que reciben.
    for ronda in range(1, 6):
        # Recolectamos los anuncios con la tabla del inicio de la ronda.
        pendientes = {n: [] for n in NODOS}
        for a, b in ENLACES:
            pendientes[a].append((b, tablas[b].anuncio()))
            pendientes[b].append((a, tablas[a].anuncio()))
        # Aplicamos.
        for n in NODOS:
            for vecino, anuncio in pendientes[n]:
                tablas[n].actualizar_desde(vecino, anuncio, ahora=ronda)
        _imprimir(tablas, ronda)

    # 3. Verificacion: A llega a E en 4 saltos via B.
    ruta = tablas["A"].ruta_hacia("E")
    print()
    print(f"A -> E: siguiente={ruta['siguiente']}, saltos={ruta['saltos']}")
    assert ruta["saltos"] == 4
    assert ruta["siguiente"] == "B"
    print("OK: convergencia alcanzada.")


if __name__ == "__main__":
    main()