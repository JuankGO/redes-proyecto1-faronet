"""Demo automatica de la app de chat: 7 nodos, Ana y Beto conversan.

Levanta 7 nodos en la misma PC para que haya suficientes relays (3)
y se pueda usar la cebolla completa.

Uso:
    python -m app.demo_chat
"""
import time

from nacl.public import PrivateKey
from nacl.signing import SigningKey

from app.cliente import Cliente
from mesh.nodo import Nodo

NOMBRES = list("ABCDEFG")
PUERTO_BASE = 8100


def _esperar(condicion, timeout=5.0, paso=0.1):
    limite = time.time() + timeout
    while time.time() < limite:
        if condicion():
            return True
        time.sleep(paso)
    return False


def main():
    print("Arrancando 7 nodos en la red local...")
    nodos = {}
    for nombre, puerto in zip(NOMBRES, range(PUERTO_BASE, PUERTO_BASE + len(NOMBRES))):
        semillas = [("127.0.0.1", p) for n, p in zip(NOMBRES, range(PUERTO_BASE, PUERTO_BASE + len(NOMBRES))) if n != nombre]
        nodos[nombre] = Nodo(
            puerto,
            SigningKey.generate(),
            PrivateKey.generate(),
            semillas=semillas,
            canal="udp",
        )
    
    for n in nodos.values():
        n.arrancar()
    time.sleep(0.5)
    for n in nodos.values():
        n.enviar_ahora()
    time.sleep(1.5)

    # Creamos los clientes de chat
    ana = Cliente("ana", nodos["A"])
    beto = Cliente("beto", nodos["B"])

    print(f"Red lista. Ana ID: {ana.nodo.mi_id[:8]}, Beto ID: {beto.nodo.mi_id[:8]}")
    print()

    # --- PRUEBA 1: Mensaje privado ---
    print("1. Ana manda un mensaje privado a Beto...")
    ana.enviar_privado(beto.nodo.mi_id, "hola beto, esto es privado")
    
    # Esperamos a que llegue
    assert _esperar(lambda: len(beto.nodo.recibidos) > 0), "El mensaje privado no llego"
    msjs_beto = beto.recibir_pendientes()
    assert len(msjs_beto) == 1
    msg = msjs_beto[0]
    print(f"   Beto recibio: tipo={msg['tipo']}, texto='{msg['texto']}'")
    
    # Verificamos que Beto sepa que es de Ana
    # El hash debe coincidir con el de Ana
    from app.mensaje import hash_tema
    hash_ana = hash_tema(f"dm:{ana.nodo.mi_id}").hex()
    assert msg['tema_hex'] == hash_ana, "El hash del emisor no coincide"
    print("   OK: Beto sabe que el mensaje es de Ana.\n")

    # --- PRUEBA 2: Mensaje a un tema ---
    print("2. Ana y Beto se unen al tema 'amigos'...")
    ana.unirse_a_tema("amigos")
    beto.unirse_a_tema("amigos")
    
    print("   Beto manda un mensaje al tema...")
    beto.enviar_tema("amigos", "hola a todos en el tema")
    
    # Esperamos a que llegue a Ana
    assert _esperar(lambda: len(ana.nodo.recibidos) > 0), "El mensaje del tema no llego"
    msjs_ana = ana.recibir_pendientes()
    assert len(msjs_ana) == 1
    msg2 = msjs_ana[0]
    print(f"   Ana recibio: tipo={msg2['tipo']}, tema='{msg2['tema']}', texto='{msg2['texto']}'")
    assert msg2['tema'] == "amigos"
    print("   OK: Ana descifro el mensaje usando la clave del tema.\n")

    # --- Limpieza ---
    for n in nodos.values():
        n.detener()
    print("Demo terminada con exito.")

if __name__ == "__main__":
    main()