"""Demo: 8 nodos en threads, A manda un mensaje privado a H via 3 relays.

Uso:
    python -m mesh.demo_nodo

Notas de la version con fix:
- Se espera a que TODOS los nodos abran su socket antes de forzar el primer
  anuncio (enviar_ahora). Sin esto, el primer HELLO/DIR/RUTA se pierde
  porque los demas nodos todavia no estaban escuchando.
- Se da mas tiempo antes de detener, para que la cadena de relays complete.
"""
import time

from nacl.public import PrivateKey
from nacl.signing import SigningKey

from mesh.nodo import Nodo

NOMBRES = list("ABCDEFGH")
PUERTO_BASE = 7100


def main():
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

    print("Arrancando 8 nodos...")
    for n in nodos.values():
        n.arrancar()

    # Damos tiempo a que todos abran el socket.
    time.sleep(0.5)

    # Forzamos un anuncio inmediato para que todos se conozcan ya.
    for n in nodos.values():
        n.enviar_ahora()

    # Damos tiempo a que lleguen los DIR/RUTA cruzados.
    time.sleep(1.5)

    a = nodos["A"]
    h = nodos["H"]
    print(f"A conoce {len(a.directorio) - 1} nodos (esperado 7)")
    print(f"A ve {len(a.vecinos)} vecinos")
    print()

    print("A manda un mensaje privado a H...")
    relays = a.mandar_a(h.mi_id, b"hola H, esto es privado")
    print("Relays elegidos:", [r[:6] + "..." for r in relays])
    print()

    # Esperar a que el mensaje recorra la cadena de relays.
    time.sleep(3)

    for n in nodos.values():
        n.detener()
    print()
    print("Demo terminada.")


if __name__ == "__main__":
    main()