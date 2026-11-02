import time

from nacl.public import PrivateKey
from nacl.signing import SigningKey

from mesh.nodo import Nodo

NOMBRES = list("ABCDEFG")
PUERTO_BASE = 7600


def _esperar(condicion, timeout=5.0, paso=0.1):

    limite = time.time() + timeout
    while time.time() < limite:
        if condicion():
            return True
        time.sleep(paso)
    return False


def test_a_manda_a_f_por_3_relays():
    puertos = {n: PUERTO_BASE + i for i, n in enumerate(NOMBRES)}
    nodos = {}
    for nombre, puerto in puertos.items():
        semillas = [("127.0.0.1", p) for n, p in puertos.items() if n != nombre]
        nodos[nombre] = Nodo(
            puerto,
            SigningKey.generate(),
            PrivateKey.generate(),
            semillas=semillas,
            canal="udp",
        )

    try:

        for n in nodos.values():
            n.arrancar()
        time.sleep(0.3)
        for n in nodos.values():
            n.enviar_ahora()


        a = nodos["A"]
        assert _esperar(lambda: len(a.directorio) >= len(NOMBRES) - 1), \
            f"A solo conoce {len(a.directorio) - 1} nodos de {len(NOMBRES) - 1}"


        f = nodos["G"]
        relays = a.mandar_a(f.mi_id, b"mensaje de prueba")
        assert len(relays) == 3
        assert len(set(relays)) == 3
        assert f.mi_id not in relays
        assert a.mi_id not in relays


        assert _esperar(lambda: len(f.recibidos) > 0, timeout=5.0), \
            "el mensaje no llego a F"

        assert f.recibidos[0] == b"mensaje de prueba"
    finally:
        for n in nodos.values():
            n.detener()
