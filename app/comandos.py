"""Parsing de comandos del chat: /priv, /unirse, /tema, /publico, /nodos,
/panico, /ayuda, /salir.

Separamos el parsing de la ejecucion para que sea testeable sin red.
"""
import argparse
from dataclasses import dataclass


class ComandoError(Exception):
    """Comando mal formado o desconocido."""


# Tipos de comando soportados.
CMD_PRIV = "priv"
CMD_TEMA = "tema"
CMD_PUBLICO = "publico"
CMD_SALIR = "salir"
CMD_AYUDA = "ayuda"
CMD_UNIRSE = "unirse"
CMD_NODOS = "nodos"
CMD_PANICO = "panico"


@dataclass
class Comando:
    """Un comando del chat ya parseado."""
    tipo: str                 # "priv", "tema", "publico", "salir", "ayuda"
    argumentos: dict          # por ejemplo {"destino": "...", "texto": "..."}


def _parsear_destino_hex(valor: str) -> str:
    """Valida que sea el inicio del id de un nodo: 8 letras hex."""
    v = valor.lower()
    if len(v) != 8:
        raise ComandoError(
            f"el destino debe ser hex de 8 letras, recibido: {valor!r}"
        )
    try:
        int(v, 16)
    except ValueError:
        raise ComandoError(f"el destino no es hex valido: {valor!r}")
    return v


def parsear_comando(linea: str) -> Comando:
    """Convierte una linea escrita por el usuario en un Comando.

    Lanza ComandoError si el comando es desconocido o esta mal formado.
    Una linea vacia produce ComandoError.
    """
    if not isinstance(linea, str):
        raise ComandoError("la linea debe ser un string")
    texto = linea.strip()
    if not texto:
        raise ComandoError("linea vacia")
    if not texto.startswith("/"):
        raise ComandoError("los comandos empiezan con /")
    partes = texto[1:].split(None, 2)   # maximo 3 tokens: cmd + arg1 + resto
    if not partes:
        raise ComandoError("comando vacio")
    nombre = partes[0].lower()

    if nombre == CMD_SALIR:
        if len(partes) != 1:
            raise ComandoError("/salir no acepta argumentos")
        return Comando(CMD_SALIR, {})

    if nombre == CMD_AYUDA:
        return Comando(CMD_AYUDA, {})

    if nombre in (CMD_NODOS, CMD_PANICO):
        if len(partes) != 1:
            raise ComandoError(f"/{nombre} no acepta argumentos")
        return Comando(nombre, {})

    if nombre == CMD_UNIRSE:
        if len(partes) < 3:
            raise ComandoError("uso: /unirse NOMBRE FRASE_SECRETA")
        nombre_tema = partes[1]
        if len(nombre_tema) > 32:
            raise ComandoError("el nombre del tema debe medir 1-32 caracteres")
        if len(partes[2]) < 8:
            raise ComandoError("la frase secreta debe tener al menos 8 caracteres")
        return Comando(CMD_UNIRSE, {"tema": nombre_tema, "frase": partes[2]})

    if nombre == CMD_PRIV:
        if len(partes) < 3:
            raise ComandoError("uso: /priv DESTINO TEXTO")
        destino = _parsear_destino_hex(partes[1])
        return Comando(CMD_PRIV, {"destino": destino, "texto": partes[2]})

    if nombre == CMD_TEMA:
        if len(partes) < 3:
            raise ComandoError("uso: /tema NOMBRE TEXTO")
        nombre_tema = partes[1]
        if not nombre_tema or len(nombre_tema) > 32:
            raise ComandoError("el nombre del tema debe medir 1-32 caracteres")
        return Comando(CMD_TEMA, {"tema": nombre_tema, "texto": partes[2]})

    if nombre == CMD_PUBLICO:
        if len(partes) < 3:
            raise ComandoError("uso: /publico NOMBRE TEXTO")
        nombre_tema = partes[1]
        if not nombre_tema or len(nombre_tema) > 32:
            raise ComandoError("el nombre del tema debe medir 1-32 caracteres")
        return Comando(CMD_PUBLICO, {"tema": nombre_tema, "texto": partes[2]})

    raise ComandoError(f"comando desconocido: /{nombre}")


def _validar_ip_puerto(p, opcion: str, valor: str) -> None:
    if ":" not in valor:
        p.error(f"{opcion} debe tener el formato IP:PUERTO")
    ip, puerto_str = valor.rsplit(":", 1)
    if not ip:
        p.error(f"{opcion}: la IP no puede estar vacia")
    try:
        puerto = int(puerto_str)
        if not (0 < puerto < 65536):
            raise ValueError
    except ValueError:
        p.error(f"{opcion}: el puerto debe ser un numero entre 1 y 65535")


def parsear_argumentos_programa(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="app.chat",
        description="Cliente de chat anonimo de FaroNet",
    )
    p.add_argument("--nodo", required=True,
                   help="IP:PUERTO de este nodo (IP con la que los demas te alcanzan)")
    p.add_argument("--alias", required=True,
                   help="Nombre local para mostrarte en pantalla (no se envia)")
    p.add_argument("--semilla", action="append", default=[],
                   help="IP:PUERTO de un nodo ya existente en la mesh (puede repetirse)")
    p.add_argument("--carpeta", default="~/.faronet",
                   help="carpeta de llaves y direccion fisica (una por nodo)")
    p.add_argument("--uart", default=None,
                   help="puerto serie del Faro (por ejemplo /dev/ttyAMA0)")
    p.add_argument("--baudios", type=int, default=9600)
    p.add_argument("--permitir-directo", action="store_true",
                   help="SOLO PRUEBAS: permite mandar sin relays si la red es chica")

    a = p.parse_args(argv)
    _validar_ip_puerto(p, "--nodo", a.nodo)
    if not a.alias.strip():
        p.error("--alias no puede estar vacio")
    for s in a.semilla:
        _validar_ip_puerto(p, "--semilla", s)
    if a.baudios <= 0:
        p.error("--baudios debe ser positivo")
    return a


MENSAJE_AYUDA = """Comandos disponibles:
  /nodos                  Lista los nodos que conoces (id corto y rol)
  /priv ID TEXTO          Mensaje privado; ID = primeros 8 hex del id del nodo
  /unirse NOMBRE FRASE    Entra a un tema privado con su frase secreta
  /tema NOMBRE TEXTO      Mensaje a un tema privado (antes usa /unirse)
  /publico NOMBRE TEXTO   Mensaje publico: sale al Worker por un gateway
  /panico                 Borra llaves y estado (igual que el boton fisico)
  /ayuda                  Muestra esta ayuda
  /salir                  Termina el programa
"""