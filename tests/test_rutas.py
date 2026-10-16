"""Pruebas de la tabla de rutas: aprendizaje, convergencia, olvido."""
import pytest

from mesh.rutas import INFINITO, RutaError, TablaRutas


def test_vecino_directo_es_un_salto():
    t = TablaRutas("A")
    t.aprender_vecino_directo("B", ahora=0)
    assert t.ruta_hacia("B")["saltos"] == 1
    assert t.ruta_hacia("B")["siguiente"] == "B"


def test_nodo_no_es_vecino_de_si_mismo():
    t = TablaRutas("A")
    with pytest.raises(RutaError):
        t.aprender_vecino_directo("A", ahora=0)


def test_aprender_ruta_de_vecino():
    t = TablaRutas("A")
    t.aprender_vecino_directo("B", ahora=0)
    # B me dice que llega a C en 1.
    cambios = t.actualizar_desde("B", {"C": 1}, ahora=1)
    assert cambios == [("C", 2, "B")]
    assert t.ruta_hacia("C")["saltos"] == 2
    assert t.ruta_hacia("C")["siguiente"] == "B"


def test_no_acepta_costo_infinito():
    t = TablaRutas("A")
    t.aprender_vecino_directo("B", ahora=0)
    cambios = t.actualizar_desde("B", {"X": INFINITO - 1}, ahora=1)
    # INFINITO - 1 + 1 = INFINITO -> no se acepta.
    assert cambios == []
    assert t.ruta_hacia("X") is None


def test_prefiere_ruta_mas_corta():
    t = TablaRutas("A")
    t.aprender_vecino_directo("B", ahora=0)
    t.aprender_vecino_directo("C", ahora=0)
    # B dice: llego a X en 5.
    t.actualizar_desde("B", {"X": 5}, ahora=1)
    assert t.ruta_hacia("X")["saltos"] == 6
    # C dice: llego a X en 2. Mejor, cambio.
    t.actualizar_desde("C", {"X": 2}, ahora=2)
    assert t.ruta_hacia("X")["saltos"] == 3
    assert t.ruta_hacia("X")["siguiente"] == "C"


def test_no_empeora_ruta_existente():
    t = TablaRutas("A")
    t.aprender_vecino_directo("B", ahora=0)
    t.aprender_vecino_directo("C", ahora=0)
    t.actualizar_desde("C", {"X": 2}, ahora=1)      # X en 3 via C
    # B anuncia X en 5: peor, no cambio.
    cambios = t.actualizar_desde("B", {"X": 5}, ahora=2)
    assert cambios == []
    assert t.ruta_hacia("X")["saltos"] == 3
    assert t.ruta_hacia("X")["siguiente"] == "C"


def test_refresca_ruta_del_mismo_siguiente():
    t = TablaRutas("A")
    t.aprender_vecino_directo("B", ahora=0)
    t.actualizar_desde("B", {"X": 3}, ahora=1)
    # B anuncia lo mismo otra vez: no es cambio, pero refresca el timestamp.
    cambios = t.actualizar_desde("B", {"X": 3}, ahora=10)
    assert cambios == []
    assert t.ruta_hacia("X")["actualizado"] == 10


def test_ignora_su_propio_id_en_el_anuncio():
    t = TablaRutas("A")
    t.aprender_vecino_directo("B", ahora=0)
    # B dice que llega a A en 1 (lo cual es cierto, pero yo soy A).
    cambios = t.actualizar_desde("B", {"A": 1}, ahora=1)
    assert cambios == []
    assert t.ruta_hacia("A") is None


def test_anuncio_excluye_propio_id():
    t = TablaRutas("A")
    t.aprender_vecino_directo("B", ahora=0)
    anuncio = t.anuncio()
    assert "A" not in anuncio
    assert anuncio == {"B": 1}


def test_olvidar_rutas_vencidas():
    t = TablaRutas("A")
    t.aprender_vecino_directo("B", ahora=0)
    t.actualizar_desde("B", {"X": 3}, ahora=0)
    vencidas = t.olvidar_vencidas(timeout=10, ahora=100)
    assert set(vencidas) == {"B", "X"}
    assert len(t) == 0


def test_convergencia_lineal():
    """Aprender en cadena: A -- B -- C -- D. Tras 3 rondas A llega a D en 3."""
    nodos = ["A", "B", "C", "D"]
    enlaces = [("A", "B"), ("B", "C"), ("C", "D")]
    tablas = {n: TablaRutas(n) for n in nodos}
    for a, b in enlaces:
        tablas[a].aprender_vecino_directo(b, ahora=0)
        tablas[b].aprender_vecino_directo(a, ahora=0)

    for ronda in range(1, 5):
        pendientes = {n: [] for n in nodos}
        for a, b in enlaces:
            pendientes[a].append((b, tablas[b].anuncio()))
            pendientes[b].append((a, tablas[a].anuncio()))
        for n in nodos:
            for vecino, anuncio in pendientes[n]:
                tablas[n].actualizar_desde(vecino, anuncio, ahora=ronda)

    assert tablas["A"].ruta_hacia("D")["saltos"] == 3
    assert tablas["A"].ruta_hacia("D")["siguiente"] == "B"
    assert tablas["D"].ruta_hacia("A")["saltos"] == 3
    assert tablas["D"].ruta_hacia("A")["siguiente"] == "C"