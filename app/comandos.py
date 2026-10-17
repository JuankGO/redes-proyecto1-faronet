"""Parsing de comandos del chat: /priv, /tema, /publico, /salir.

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


@dataclass
class Comando:
    """Un comando del chat ya parseado."""
    tipo: str                 # "priv", "tema", "publico", "salir", "ayuda"
    argumentos: dict          # por ejemplo {"destino": "...", "texto": "..."}


def _parsear_destino_hex(valor: str) -> str:
    """Valida que sea una direccion fisica en hex de 8 letras (4 bytes)."""
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


def parsear_argumentos_programa(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="app.chat",
        description="Cliente de chat anonimo de FaroNet",
    )
    p.add_argument("--nodo", required=True,
                   help="IP:PUERTO del nodo local al que conectarse")
    p.add_argument("--alias", required=True,
                   help="Nombre local para mostrarte en pantalla (no se envia)")
    # NUEVO: nodo semilla para conectarse a la mesh
    p.add_argument("--semilla", default=None,
                   help="IP:PUERTO de un nodo ya existente en la mesh (opcional)")
    
    a = p.parse_args(argv)
    
    # Validaciones de --nodo
    if ":" not in a.nodo:
        p.error("--nodo debe tener el formato IP:PUERTO")
    ip, puerto_str = a.nodo.rsplit(":", 1)
    if not ip:
        p.error("--nodo: la IP no puede estar vacia")
    try:
        puerto = int(puerto_str)
        if not (0 < puerto < 65536):
            raise ValueError
    except ValueError:
        p.error("--nodo: el puerto debe ser un numero entre 1 y 65535")
    if not a.alias.strip():
        p.error("--alias no puede estar vacio")
        
    # Validaciones de --semilla si se proporciona
    if a.semilla:
        if ":" not in a.semilla:
            p.error("--semilla debe tener el formato IP:PUERTO")
        ip_s, puerto_s_str = a.semilla.rsplit(":", 1)
        try:
            puerto_s = int(puerto_s_str)
            if not (0 < puerto_s < 65536):
                raise ValueError
        except ValueError:
            p.error("--semilla: el puerto debe ser un numero entre 1 y 65535")
            
    return a


MENSAJE_AYUDA = """Comandos disponibles:
  /priv DESTINO TEXTO    Mensaje privado a una direccion fisica (8 hex)
  /tema NOMBRE TEXTO     Mensaje a un tema privado compartido
  /publico NOMBRE TEXTO  Mensaje a un tema publico (sale al Worker)
  /ayuda                 Muestra esta ayuda
  /salir                 Termina el programa
"""