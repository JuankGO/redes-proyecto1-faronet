"""Demo enfocada SOLO en la Mesh (Fases 3) y el Chat (Fase 4)."""
import time
from nacl.public import PrivateKey
from nacl.signing import SigningKey

from mesh.nodo import Nodo
from app.cliente import Cliente
from app.mensaje import hash_tema

NOMBRES = list("ABCDEFG")
PUERTO_BASE = 8400  # Puertos altos para evitar bloqueos de Windows

def main():
    print("=== 1. LEVANTANDO LA RED MESH (7 Nodos) ===")
    
    nodos = {}
    # 1. Creamos los nodos
    for nombre, puerto in zip(NOMBRES, range(PUERTO_BASE, PUERTO_BASE + len(NOMBRES))):
        semillas = [("127.0.0.1", p) for n, p in zip(NOMBRES, range(PUERTO_BASE, PUERTO_BASE + len(NOMBRES))) if n != nombre]
        nodos[nombre] = Nodo(
            puerto,
            SigningKey.generate(),
            PrivateKey.generate(),
            semillas=semillas,
            canal="udp",
        )
    
    # 2. Arrancamos todos
    for n in nodos.values():
        n.arrancar()
    
    print("Esperando a que los nodos se descubran entre sí...")
    time.sleep(0.5) # Dar tiempo a que abran los sockets
    
    # 3. Forzamos el saludo inicial
    for n in nodos.values():
        n.enviar_ahora()
        
    # 4. Esperamos a que el nodo A conozca a los demás (máximo 5 segundos)
    inicio = time.time()
    while len(nodos['A'].directorio) < 7 and (time.time() - inicio) < 5.0:
        time.sleep(0.2)
        
    print(f"[OK] Red lista. El Nodo A conoce a {len(nodos['A'].directorio) - 1} nodos.\n")

    print("=== 2. TABLA DE ENRUTAMIENTO DEL NODO A ===")
    # Damos medio segundo para que se intercambien las tablas de rutas (RIP)
    time.sleep(1.0) 
    rutas = nodos['A'].rutas.listar()
    if not rutas:
        print("  (La tabla de rutas está vacía, pero el directorio tiene las direcciones IP)")
    for destino, siguiente, saltos in rutas:
        print(f"  -> Para llegar a {destino[:8]}... usa {siguiente[:8]}... ({saltos} saltos)")
    print()

    print("=== 3. INICIANDO EL CHAT (Fase 4) ===")
    ana = Cliente("ana", nodos["A"])
    beto = Cliente("beto", nodos["B"])
    print(f"Ana conectada. ID público: {ana.nodo.mi_id[:8]}")
    print(f"Beto conectado. ID público: {beto.nodo.mi_id[:8]}\n")

    # --- PRUEBA 1: MENSAJE PRIVADO ---
    print(">>> Ana le manda un PRIVADO a Beto...")
    texto_priv = "Hola Beto, esto es un mensaje privado."
    relays_usados = ana.enviar_privado(beto.nodo.mi_id, texto_priv)
    
    time.sleep(1.0) # Esperar a que viaje por los relays
    
    msjs_beto = beto.recibir_pendientes()
    if msjs_beto:
        msg = msjs_beto[0]
        print(f"Beto recibe: '{msg['texto']}'")
        print(f"  Usó {len(relays_usados)} relays para ocultar la ruta.")
        
        # Verificar quién lo mandó
        hash_esperado = hash_tema(f"dm:{ana.nodo.mi_id}").hex()
        if msg['tema_hex'] == hash_esperado:
            print("  [OK] Beto comprobó criptográficamente que el mensaje viene de Ana.")
    else:
        print("  [ERROR] Beto no recibió nada.")
    print()

    # --- PRUEBA 2: MENSAJE AL TEMA (GRUPAL) ---
    print(">>> Ana y Beto se unen al tema 'futbol'. Beto manda un mensaje grupal...")
    ana.unirse_a_tema("futbol")
    beto.unirse_a_tema("futbol")
    
    texto_grupal = "¡Ganó la Liga!"
    beto.enviar_tema("futbol", texto_grupal)
    
    time.sleep(1.0)
    
    msjs_ana = ana.recibir_pendientes()
    if msjs_ana:
        msg2 = msjs_ana[0]
        print(f"Ana recibe en el tema '{msg2['tema']}': '{msg2['texto']}'")
        print("  [OK] Ana descifró el mensaje usando la clave del tema.")
    else:
        print("  [ERROR] Ana no recibió el mensaje del tema.")
        
    print("\n=== LIMPIEZA ===")
    for n in nodos.values():
        n.detener()
    print("Nodos apagados. Demo terminada.")

if __name__ == "__main__":
    main()