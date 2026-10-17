"""Cliente de chat interactivo de FaroNet.

Uso:
    python -m app.chat --nodo 127.0.0.1:7001 --alias ana
    python -m app.chat --nodo 127.0.0.1:7002 --alias beto --semilla 127.0.0.1:7001
"""
import sys
import threading
import time

from nacl.public import PrivateKey
from nacl.signing import SigningKey

from app.cliente import Cliente, ClienteError
from app.comandos import (
    CMD_AYUDA, CMD_PRIV, CMD_PUBLICO, CMD_SALIR, CMD_TEMA,
    ComandoError, MENSAJE_AYUDA, parsear_argumentos_programa,
    parsear_comando,
)
from mesh.nodo import Nodo
from app.mensaje import hash_tema


def _hilo_recepcion(cliente: Cliente):
    """Hilo en segundo plano que imprime los mensajes que llegan."""
    while True:
        time.sleep(0.5)
        for msg in cliente.recibir_pendientes():
            hora = time.strftime("%H:%M:%S", time.localtime(msg["hora"]))
            if msg["tipo"] == "privado":
                # Intentar descubrir quién lo mandó
                emisor = "Desconocido"
                for id_nodo in cliente.nodo.directorio.keys():
                    if hash_tema(f"dm:{id_nodo}").hex() == msg['tema_hex']:
                        emisor = id_nodo[:8]
                        break
                print(f"\n[{hora}] PRIVADO de {emisor}: {msg['texto']}")
            elif msg["tipo"] == "tema":
                print(f"\n[{hora}] TEMA {msg['tema']}: {msg['texto']}")
            elif msg["tipo"] == "publico":
                print(f"\n[{hora}] PUBLICO: {msg['texto']}")
            print(f"{cliente.alias}> ", end="", flush=True)


def bucle_principal(cliente: Cliente):
    """Lee lineas de la terminal y ejecuta los comandos."""
    print(f"Bienvenido a FaroNet, {cliente.alias}.")
    print(f"Tu ID es: {cliente.nodo.mi_id}")
    print("Escribe /ayuda para ver los comandos.\n")
    
    while True:
        try:
            linea = input(f"{cliente.alias}> ")
            cmd = parsear_comando(linea)
            
            if cmd.tipo == CMD_SALIR:
                print("Saliendo...")
                break
                
            elif cmd.tipo == CMD_AYUDA:
                print(MENSAJE_AYUDA)
                
            elif cmd.tipo == CMD_PRIV:
                destino = cmd.argumentos["destino"]
                # Comprobamos si el destino en realidad es el ID completo del nodo.
                # Como pedimos 8 letras, buscamos en el directorio a quien empiece asi.
                id_completo = None
                for id_nodo in cliente.nodo.directorio.keys():
                    if id_nodo.startswith(destino):
                        id_completo = id_nodo
                        break
                
                if id_completo is None:
                    print(f"Error: no encuentro ningun nodo que empiece con {destino}")
                    continue
                    
                try:
                    relays = cliente.enviar_privado(id_completo, cmd.argumentos["texto"])
                    print(f"Enviado por {len(relays)} saltos.")
                except ClienteError as e:
                    print(f"Error: {e}")
                    
            elif cmd.tipo == CMD_TEMA:
                tema = cmd.argumentos["tema"]
                if tema not in cliente.temas():
                    cliente.unirse_a_tema(tema)
                    print(f"(Te has unido al tema '{tema}')")
                try:
                    n = cliente.enviar_tema(tema, cmd.argumentos["texto"])
                    print(f"Enviado a {n} nodos en el tema '{tema}'.")
                except ClienteError as e:
                    print(f"Error: {e}")
                    
            elif cmd.tipo == CMD_PUBLICO:
                tema = cmd.argumentos["tema"]
                msj_publico = cliente.empaquetar_publico(tema, cmd.argumentos["texto"])
                # En la parte 11 esto se manda al gateway.
                print(f"[SIMULADO] Mensaje publico preparado ({len(msj_publico)} bytes).")
                print("En la parte 11 se enviara al gateway.")
                
        except ComandoError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break
        except Exception as e:
            print(f"Error inesperado: {e}")


def main():
    args = parsear_argumentos_programa()
    
    ip, puerto_str = args.nodo.rsplit(":", 1)
    puerto = int(puerto_str)
    
    semillas = []
    if args.semilla:
        ip_s, puerto_s = args.semilla.rsplit(":", 1)
        semillas.append((ip_s, int(puerto_s)))
    
    # Creamos la identidad del nodo
    firma = SigningKey.generate()
    cifrado = PrivateKey.generate()
    
    # Arrancamos el nodo
    nodo = Nodo(puerto, firma, cifrado, semillas=semillas, ip_publica=ip)
    nodo.arrancar()
    
    # Envolvemos en el cliente
    cliente = Cliente(args.alias, nodo)
    
    # Arrancamos el hilo que recibe
    hilo = threading.Thread(target=_hilo_recepcion, args=(cliente,), daemon=True)
    hilo.start()
    
    try:
        bucle_principal(cliente)
    finally:
        nodo.detener()

if __name__ == "__main__":
    main()