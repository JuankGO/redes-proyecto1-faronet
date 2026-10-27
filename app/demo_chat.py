"""Demo automatica de la app de chat: 7 nodos en la misma PC, Ana y Beto conversan.

Hacen falta al menos 5 candidatos a relay para armar la cebolla de 3 saltos,
por eso se levantan 7 nodos.

Uso:
    python -m app.demo_chat
"""
import time

from nacl.public import PrivateKey
from nacl.signing import SigningKey

from app.cliente import Cliente, pista_emisor
from mesh.nodo import Nodo

NOMBRES = list("ABCDEFG")
PUERTO_BASE = 8100
FRASE = "frase secreta compartida"


def _esperar(condicion, timeout=8.0, paso=0.1):
    limite = time.time() + timeout
    while time.time() < limite:
        if condicion():
            return True
        time.sleep(paso)
    return False


def main():
    print("Arrancando 7 nodos en la red local...")
    puertos = {n: PUERTO_BASE + i for i, n in enumerate(NOMBRES)}
    nodos = {}
    for nombre, puerto in puertos.items():
        semillas = [("127.0.0.1", p) for n, p in puertos.items() if n != nombre]
        nodos[nombre] = Nodo(puerto, SigningKey.generate(), PrivateKey.generate(), semillas=semillas)

    try:
        for n in nodos.values():
            n.arrancar()
        time.sleep(0.5)

        def todos_se_conocen():
            for n in nodos.values():
                n.enviar_ahora()
            return all(len(n.directorio) >= len(NOMBRES) for n in nodos.values())

        if not _esperar(todos_se_conocen, timeout=10, paso=0.3):
            raise SystemExit("La red no convergio a tiempo.")

        ana = Cliente("ana", nodos["A"])
        beto = Cliente("beto", nodos["B"])
        print(f"Red lista. Ana ID: {ana.nodo.mi_id[:8]}, Beto ID: {beto.nodo.mi_id[:8]}\n")

        # 1. Mensaje privado por 3 relays.
        print("1. Ana manda un mensaje privado a Beto...")
        relays = ana.enviar_privado(beto.nodo.mi_id, "hola beto, esto es privado")
        print(f"   Relays usados: {[r[:8] for r in relays]}")
        assert _esperar(lambda: len(beto.nodo.recibidos) > 0), "El mensaje privado no llego"
        msg = beto.recibir_pendientes()[0]
        print(f"   Beto recibio: tipo={msg['tipo']}, texto='{msg['texto']}'")
        # La pista del emisor NO esta firmada: cualquiera podria poner la de Ana.
        if msg["tema_hex"] == pista_emisor(ana.nodo.mi_id):
            print(f"   Posible emisor: {ana.nodo.mi_id[:8]} (pista sin verificar, ver docs/amenazas.md)\n")

        # 2. Mensaje a un tema protegido con frase.
        print("2. Ana y Beto se unen al tema 'amigos' con la misma frase...")
        ana.unirse_a_tema("amigos", FRASE)
        beto.unirse_a_tema("amigos", FRASE)
        print("   Beto manda un mensaje al tema...")
        beto.enviar_tema("amigos", "hola a todos en el tema")
        assert _esperar(lambda: len(ana.nodo.recibidos) > 0), "El mensaje del tema no llego"
        msg2 = ana.recibir_pendientes()[0]
        print(f"   Ana recibio: tema='{msg2['tema']}', texto='{msg2['texto']}'")
        assert msg2["tema"] == "amigos"
        print("   OK: solo quien conoce la frase puede leer el tema.\n")

        print("Demo terminada con exito.")
    finally:
        for n in nodos.values():
            n.detener()


if __name__ == "__main__":
    main()
