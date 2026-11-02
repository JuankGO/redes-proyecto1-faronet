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

    tablas = {n: TablaRutas(n) for n in NODOS}
    for a, b in ENLACES:
        tablas[a].aprender_vecino_directo(b, ahora=0)
        tablas[b].aprender_vecino_directo(a, ahora=0)

    _imprimir(tablas, 0)



    for ronda in range(1, 6):

        pendientes = {n: [] for n in NODOS}
        for a, b in ENLACES:
            pendientes[a].append((b, tablas[b].anuncio()))
            pendientes[b].append((a, tablas[a].anuncio()))

        for n in NODOS:
            for vecino, anuncio in pendientes[n]:
                tablas[n].actualizar_desde(vecino, anuncio, ahora=ronda)
        _imprimir(tablas, ronda)


    ruta = tablas["A"].ruta_hacia("E")
    print()
    print(f"A -> E: siguiente={ruta['siguiente']}, saltos={ruta['saltos']}")
    assert ruta["saltos"] == 4
    assert ruta["siguiente"] == "B"
    print("OK: convergencia alcanzada.")


if __name__ == "__main__":
    main()
