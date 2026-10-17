"""Cliente de chat: capa encima del Nodo para mandar y recibir mensajes.

Directo: se manda el mensaje de 256B dentro de la cebolla. El onion ya
cifra de punta a punta, no hace falta mas.

Tema: el mensaje de 256B se cifra ADEMAS con SecretBox y una clave
derivada del nombre del tema. Solo quien tenga esa clave lo lee.

Recepcion: los mensajes directos miden 256B exactos, los de tema miden
mas (SecretBox agrega nonce + MAC). La ambiguedad se resuelve por tamano.
"""
import hashlib

from nacl.secret import SecretBox

from app.mensaje import (
    PRIVADO,
    PUBLICO,
    TAMANO_MENSAJE,
    MensajeError,
    desempaquetar_mensaje,
    empaquetar_mensaje,
    hash_tema,
)


class ClienteError(Exception):
    """Operacion invalida del cliente de chat."""


def clave_de_tema(nombre: str) -> bytes:
    """Deriva 32B del nombre del tema.

    Para la demo derivamos del nombre. En produccion, el creador del tema
    genera una clave aleatoria y la comparte por un canal aparte. Esto se
    anota en el RFC.
    """
    if not nombre:
        raise ClienteError("el nombre del tema no puede estar vacio")
    return hashlib.blake2b(
        f"faronet-tema:{nombre}".encode("utf-8"), digest_size=32
    ).digest()


class Cliente:
    """Envuelve un Nodo y ofrece operaciones de chat."""

    def __init__(self, alias: str, nodo):
        if not alias or not alias.strip():
            raise ClienteError("el alias no puede estar vacio")
        self.alias = alias.strip()
        self.nodo = nodo
        self._leidos = 0                # indice en nodo.recibidos ya procesado
        self._temas = {}                # nombre -> SecretBox

    # ----- Temas -----

    def unirse_a_tema(self, nombre: str) -> None:
        self._temas[nombre] = SecretBox(clave_de_tema(nombre))

    def temas(self) -> list:
        return sorted(self._temas.keys())

    # ----- Envio -----

    def enviar_privado(self, destino_id: str, texto: str) -> int:
        if not texto:
            raise ClienteError("el texto no puede estar vacio")
        if len(texto.encode("utf-8")) > 240:
            raise ClienteError("el texto excede 240 bytes")
            
        # Usamos un hash de nuestro ID como "tema" para que el receptor sepa quién somos.
        # Es un hash de 8 bytes, no el ID truncado.
        hash_emisor = hash_tema(f"dm:{self.nodo.mi_id}")
        
        msj = empaquetar_mensaje(PRIVADO, hash_emisor, texto.encode("utf-8"))
        return self.nodo.mandar_a(destino_id, msj)

    def enviar_tema(self, nombre_tema: str, texto: str,
                    suscriptores: list = None) -> int:
        """Manda un mensaje a un tema cifrado con la clave compartida.
        
        Si 'suscriptores' es None, se manda a todos los nodos conocidos
        en el directorio (menos a mi mismo).
        """
        if nombre_tema not in self._temas:
            raise ClienteError(f"no estas en el tema '{nombre_tema}'")
        if not texto:
            raise ClienteError("el texto no puede estar vacio")
        if len(texto.encode("utf-8")) > 240:
            raise ClienteError("el texto excede 240 bytes")
            
        box = self._temas[nombre_tema]
        msj_plano = empaquetar_mensaje(PRIVADO, hash_tema(nombre_tema),
                                       texto.encode("utf-8"))
        cifrado = box.encrypt(msj_plano)   # nonce + ciphertext + MAC
        
        if suscriptores is None:
            # Todos en el directorio, menos yo
            suscriptores = [id_hex for id_hex in self.nodo.directorio.keys()
                            if id_hex != self.nodo.mi_id]

        enviados = 0
        for sub_id in suscriptores:
            if sub_id == self.nodo.mi_id:
                continue
            self.nodo.mandar_a(sub_id, cifrado)
            enviados += 1
        return enviados

    def empaquetar_publico(self, nombre_tema: str, texto: str) -> bytes:
        """Devuelve el mensaje publico listo para mandar al gateway.

        No se envia aqui: el gateway vive en la Parte 11.
        """
        if not texto:
            raise ClienteError("el texto no puede estar vacio")
        if len(texto.encode("utf-8")) > 240:
            raise ClienteError("el texto excede 240 bytes")
        return empaquetar_mensaje(PUBLICO, hash_tema(nombre_tema),
                                  texto.encode("utf-8"))

    # ----- Recepcion -----

    def recibir_pendientes(self) -> list:
        """Devuelve los mensajes nuevos ya decodificados."""
        nuevos = []
        while self._leidos < len(self.nodo.recibidos):
            crudo = self.nodo.recibidos[self._leidos]
            self._leidos += 1
            dec = self._decodificar(crudo)
            if dec is not None:
                nuevos.append(dec)
        return nuevos

    def _decodificar(self, crudo: bytes):
        # 1. Mensaje directo: mide exactamente 256B.
        if len(crudo) == TAMANO_MENSAJE:
            try:
                d = desempaquetar_mensaje(crudo)
            except MensajeError:
                return None
            return {
                "tipo": "privado" if d["visibilidad"] == PRIVADO else "publico",
                "tema_hex": d["tema"].hex(),
                "texto": d["texto"].decode("utf-8", errors="replace"),
                "hora": d["hora"],
            }
        # 2. Mensaje de tema: cifrado con SecretBox, probar cada clave.
        for nombre, box in self._temas.items():
            try:
                plano = box.decrypt(crudo)
                d = desempaquetar_mensaje(plano)
            except Exception:
                continue
            return {
                "tipo": "tema",
                "tema": nombre,
                "tema_hex": d["tema"].hex(),
                "texto": d["texto"].decode("utf-8", errors="replace"),
                "hora": d["hora"],
            }
        return None