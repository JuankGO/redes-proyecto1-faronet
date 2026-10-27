"""Cliente de chat interactivo de FaroNet.

Uso (una terminal por persona; los parametros vienen de la terminal):
    python3 -m app.chat --nodo 192.168.1.20:7001 --alias ana
    python3 -m app.chat --nodo 192.168.1.21:7002 --alias beto --semilla 192.168.1.20:7001

Con el Faro conectado (Raspberry Pi):
    python3 -m app.chat --nodo 192.168.1.20:7001 --alias ana --uart /dev/ttyAMA0

La identidad se guarda en --carpeta (por defecto ~/.faronet). El boton de
panico fisico (si hay --uart) y el comando /panico la borran.
"""
import threading
import time
from pathlib import Path

from app.cliente import Cliente, ClienteError, pista_emisor
from app.comandos import (
    CMD_AYUDA, CMD_NODOS, CMD_PANICO, CMD_PRIV, CMD_PUBLICO, CMD_SALIR,
    CMD_TEMA, CMD_UNIRSE, ComandoError, MENSAJE_AYUDA,
    parsear_argumentos_programa, parsear_comando,
)
from mesh.nodo import crear_nodo_desde_args
from mesh.saltos import SaltosError


def _posible_emisor(cliente: Cliente, tema_hex: str) -> str:
    for id_nodo in cliente.nodo.directorio.keys():
        if pista_emisor(id_nodo) == tema_hex:
            return id_nodo[:8]
    return "desconocido"


def _hilo_recepcion(cliente: Cliente, parar: threading.Event):
    """Hilo en segundo plano que imprime los mensajes que llegan."""
    while not parar.is_set():
        time.sleep(0.5)
        for msg in cliente.recibir_pendientes():
            hora = time.strftime("%H:%M:%S", time.localtime(msg["hora"]))
            if msg["tipo"] == "privado":
                emisor = _posible_emisor(cliente, msg["tema_hex"])
                print(f"\n[{hora}] PRIVADO (posible emisor {emisor}, no verificado): {msg['texto']}")
            elif msg["tipo"] == "tema":
                print(f"\n[{hora}] TEMA {msg['tema']}: {msg['texto']}")
            else:
                print(f"\n[{hora}] PUBLICO: {msg['texto']}")
            print(f"{cliente.alias}> ", end="", flush=True)


def _buscar_id(cliente: Cliente, prefijo: str):
    coincidencias = [i for i in cliente.nodo.directorio.keys()
                     if i.startswith(prefijo) and i != cliente.nodo.mi_id]
    if len(coincidencias) == 1:
        return coincidencias[0]
    return None if not coincidencias else "ambiguo"


def ejecutar(cliente: Cliente, cmd, indicadores=None) -> bool:
    """Ejecuta un comando. Devuelve False si hay que salir."""
    if cmd.tipo == CMD_SALIR:
        return False
    if cmd.tipo == CMD_AYUDA:
        print(MENSAJE_AYUDA)
    elif cmd.tipo == CMD_NODOS:
        for id_nodo in sorted(cliente.nodo.directorio.keys()):
            entrada = cliente.nodo.directorio[id_nodo][0]
            yo = " (yo)" if id_nodo == cliente.nodo.mi_id else ""
            rol = " gateway" if entrada.get("rol") == "gateway" else ""
            print(f"  {id_nodo[:8]}{rol}{yo}")
    elif cmd.tipo == CMD_PRIV:
        destino = _buscar_id(cliente, cmd.argumentos["destino"])
        if destino is None:
            print(f"Error: no conozco ningun nodo que empiece con {cmd.argumentos['destino']}")
        elif destino == "ambiguo":
            print("Error: hay varios nodos con ese inicio; usa mas letras del id")
        else:
            relays = cliente.enviar_privado(destino, cmd.argumentos["texto"])
            print(f"Enviado por {len(relays)} relays.")
    elif cmd.tipo == CMD_UNIRSE:
        print("Derivando la llave del tema (tarda un momento)...")
        cliente.unirse_a_tema(cmd.argumentos["tema"], cmd.argumentos["frase"])
        print(f"Te uniste al tema '{cmd.argumentos['tema']}'.")
    elif cmd.tipo == CMD_TEMA:
        n = cliente.enviar_tema(cmd.argumentos["tema"], cmd.argumentos["texto"])
        print(f"Enviado a {n} nodos (solo los que tienen la frase lo leen).")
    elif cmd.tipo == CMD_PUBLICO:
        relays = cliente.enviar_publico(cmd.argumentos["tema"], cmd.argumentos["texto"])
        print(f"Enviado al gateway por {len(relays)} relays. Saldra en la sala publica.")
    elif cmd.tipo == CMD_PANICO:
        borrados = cliente.nodo.panico(indicadores)
        cliente.olvidar_todo()
        print(f"PANICO: borrados {len(borrados)} archivos. Tu id nuevo es {cliente.nodo.mi_id[:8]}.")
    return True


def bucle_principal(cliente: Cliente, indicadores=None):
    """Lee lineas de la terminal y ejecuta los comandos."""
    print(f"Bienvenido a FaroNet, {cliente.alias}.")
    print(f"Tu ID es: {cliente.nodo.mi_id}")
    print("Escribe /ayuda para ver los comandos.\n")
    while True:
        try:
            linea = input(f"{cliente.alias}> ")
        except (KeyboardInterrupt, EOFError):
            print("\nSaliendo...")
            break
        if not linea.strip():
            continue
        try:
            if not ejecutar(cliente, parsear_comando(linea), indicadores):
                print("Saliendo...")
                break
        except (ComandoError, ClienteError, SaltosError) as e:
            print(f"Error: {e}")
        except Exception as e:   # nunca se cae el chat por una entrada rara
            print(f"Error inesperado: {e}")


def main(argv=None):
    a = parsear_argumentos_programa(argv)
    ip, puerto = a.nodo.rsplit(":", 1)
    a.puerto, a.ip_publica = int(puerto), ip
    a.carpeta = str(Path(a.carpeta).expanduser())
    nodo = crear_nodo_desde_args(a)
    cliente = Cliente(a.alias, nodo)
    nodo.al_panico = cliente.olvidar_todo

    indicadores = boton = None
    if a.uart:
        from faro.gpio import BotonPanico, Indicadores
        indicadores = Indicadores()
        boton = BotonPanico(lambda: (nodo.panico(indicadores),
                                     print("\nPANICO: llaves borradas desde el boton fisico.")))

    nodo.arrancar()
    parar = threading.Event()
    threading.Thread(target=_hilo_recepcion, args=(cliente, parar), daemon=True).start()
    try:
        bucle_principal(cliente, indicadores)
    finally:
        parar.set()
        nodo.detener()
        del boton


if __name__ == "__main__":
    main()
