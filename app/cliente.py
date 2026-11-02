import hashlib
import random
import time

from nacl import pwhash
from nacl.secret import SecretBox

from app.mensaje import (
    MAX_TEXTO,
    PRIVADO,
    PUBLICO,
    TAMANO_MENSAJE,
    MensajeError,
    desempaquetar_mensaje,
    empaquetar_mensaje,
    empaquetar_publico,
    hash_tema,
)

TTL_VISTOS = 3600


class ClienteError(Exception):
    pass


def clave_de_tema(nombre: str, frase: str) -> bytes:

    if not nombre:
        raise ClienteError("el nombre del tema no puede estar vacio")
    if not frase or len(frase) < 8:
        raise ClienteError("la frase secreta del tema debe tener al menos 8 caracteres")
    sal = hashlib.blake2b(f"faronet-tema:{nombre}".encode("utf-8"), digest_size=16).digest()
    return pwhash.argon2id.kdf(
        SecretBox.KEY_SIZE, frase.encode("utf-8"), sal,
        opslimit=pwhash.argon2id.OPSLIMIT_INTERACTIVE,
        memlimit=pwhash.argon2id.MEMLIMIT_INTERACTIVE,
    )


def pista_emisor(id_hex: str) -> str:

    return hash_tema(f"dm:{id_hex}").hex()


class Cliente:


    def __init__(self, alias: str, nodo):
        if not alias or not alias.strip():
            raise ClienteError("el alias no puede estar vacio")
        self.alias = alias.strip()
        self.nodo = nodo
        self._temas = {}
        self._vistos = {}



    def unirse_a_tema(self, nombre: str, frase: str) -> None:
        self._temas[nombre] = SecretBox(clave_de_tema(nombre, frase))

    def salir_de_tema(self, nombre: str) -> None:
        self._temas.pop(nombre, None)

    def temas(self) -> list:
        return sorted(self._temas.keys())

    def olvidar_todo(self) -> None:

        self._temas.clear()
        self._vistos.clear()



    @staticmethod
    def _validar_texto(texto: str, maximo: int = MAX_TEXTO) -> bytes:
        if not texto:
            raise ClienteError("el texto no puede estar vacio")
        datos = texto.encode("utf-8")
        if len(datos) > maximo:
            raise ClienteError(f"el texto excede {maximo} bytes")
        return datos

    def enviar_privado(self, destino_id: str, texto: str) -> list:
        datos = self._validar_texto(texto)
        msj = empaquetar_mensaje(PRIVADO, bytes.fromhex(pista_emisor(self.nodo.mi_id)), datos)
        return self.nodo.mandar_a(destino_id, msj)

    def enviar_tema(self, nombre_tema: str, texto: str, suscriptores: list = None) -> int:

        if nombre_tema not in self._temas:
            raise ClienteError(f"no estas en el tema '{nombre_tema}' (usa /unirse)")
        datos = self._validar_texto(texto)
        cifrado = self._temas[nombre_tema].encrypt(
            empaquetar_mensaje(PRIVADO, hash_tema(nombre_tema), datos))
        if suscriptores is None:
            suscriptores = [i for i in self.nodo.directorio.keys()
                            if i != self.nodo.mi_id and not self._es_gateway(i)]
        enviados = 0
        for sub_id in suscriptores:
            if sub_id == self.nodo.mi_id:
                continue
            self.nodo.mandar_a(sub_id, cifrado)
            enviados += 1
        return enviados

    def _es_gateway(self, id_hex: str) -> bool:
        e = self.nodo.directorio.get(id_hex) if hasattr(self.nodo, "directorio") else None
        return bool(e and e[0].get("rol") == "gateway")

    def empaquetar_publico(self, nombre_tema: str, texto: str) -> bytes:

        self._validar_texto(texto)
        try:
            return empaquetar_publico(nombre_tema, texto)
        except MensajeError as e:
            raise ClienteError(str(e))

    def enviar_publico(self, nombre_tema: str, texto: str) -> list:

        gateways = self.nodo.gateways()
        if not gateways:
            raise ClienteError("no hay ningun gateway en el directorio todavia")
        msj = self.empaquetar_publico(nombre_tema, texto)
        return self.nodo.mandar_a(random.SystemRandom().choice(gateways), msj)



    def _repetido(self, crudo: bytes) -> bool:
        ahora = time.time()
        for k in [k for k, t in self._vistos.items() if ahora - t > TTL_VISTOS]:
            del self._vistos[k]
        resumen = hashlib.blake2b(crudo, digest_size=16).digest()
        if resumen in self._vistos:
            return True
        self._vistos[resumen] = ahora
        return False

    def recibir_pendientes(self) -> list:

        nuevos = []
        while self.nodo.recibidos:
            crudo = self.nodo.recibidos.pop(0)
            if self._repetido(crudo):
                continue
            dec = self._decodificar(crudo)
            if dec is not None:
                nuevos.append(dec)
        return nuevos

    def _decodificar(self, crudo: bytes):

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
