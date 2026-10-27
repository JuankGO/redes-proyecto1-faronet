"""Pruebas del cliente de chat: envio, recepcion, temas."""
import pytest

from app.cliente import Cliente, ClienteError, clave_de_tema
from app.mensaje import (
    PRIVADO,
    TAMANO_MENSAJE,
    desempaquetar_mensaje,
    empaquetar_mensaje,
    hash_tema,
)


FRASE = "frase secreta del grupo"


class FakeNodo:
    """Nodo de mentira: guarda lo enviado y lo que debe entregar."""
    def __init__(self, mi_id="aa" * 32, gateways=()):
        self.mi_id = mi_id
        self.enviados = []      # [(destino, mensaje)]
        self.recibidos = []     # mensajes que el cliente va a decodificar
        self.directorio = {}
        self._gateways = list(gateways)

    def mandar_a(self, destino_id, mensaje):
        self.enviados.append((destino_id, mensaje))
        return ["relay1", "relay2", "relay3"]

    def gateways(self):
        return self._gateways


def test_clave_de_tema_es_estable():
    assert clave_de_tema("amigos", FRASE) == clave_de_tema("amigos", FRASE)
    assert clave_de_tema("amigos", FRASE) != clave_de_tema("enemigos", FRASE)
    assert clave_de_tema("amigos", FRASE) != clave_de_tema("amigos", "otra frase distinta")
    assert len(clave_de_tema("amigos", FRASE)) == 32


def test_clave_de_tema_vacia_se_rechaza():
    with pytest.raises(ClienteError):
        clave_de_tema("", FRASE)
    with pytest.raises(ClienteError, match="frase"):
        clave_de_tema("amigos", "corta")


def test_adivinar_el_nombre_no_alcanza_para_leer():
    """El bug original: la llave salia solo del nombre del tema."""
    from nacl.exceptions import CryptoError
    from nacl.secret import SecretBox
    import hashlib
    c = Cliente("ana", FakeNodo())
    c.unirse_a_tema("futbol", FRASE)
    n = FakeNodo()
    c.nodo = n
    c.enviar_tema("futbol", "secreto", ["bb" * 32])
    cifrado = n.enviados[0][1]
    llave_vieja = hashlib.blake2b(b"faronet-tema:futbol", digest_size=32).digest()
    with pytest.raises(CryptoError):
        SecretBox(llave_vieja).decrypt(cifrado)


def test_cliente_alias_vacio_se_rechaza():
    with pytest.raises(ClienteError):
        Cliente("", FakeNodo())


def test_enviar_privado_produce_mensaje_de_256b():
    nodo = FakeNodo()
    c = Cliente("ana", nodo)
    c.enviar_privado("bb" * 32, "hola")
    assert len(nodo.enviados) == 1
    destino, msj = nodo.enviados[0]
    assert destino == "bb" * 32
    assert len(msj) == TAMANO_MENSAJE
    d = desempaquetar_mensaje(msj)
    assert d["visibilidad"] == PRIVADO
    assert d["texto"] == b"hola"


def test_enviar_privado_vacio_se_rechaza():
    c = Cliente("ana", FakeNodo())
    with pytest.raises(ClienteError, match="vacio"):
        c.enviar_privado("bb" * 32, "")


def test_enviar_privado_muy_largo_se_rechaza():
    c = Cliente("ana", FakeNodo())
    with pytest.raises(ClienteError, match="240"):
        c.enviar_privado("bb" * 32, "x" * 241)


def test_enviar_tema_sin_unirse_se_rechaza():
    c = Cliente("ana", FakeNodo())
    with pytest.raises(ClienteError, match="no estas"):
        c.enviar_tema("amigos", "hola", ["bb" * 32])


def test_enviar_tema_cifra_con_secretbox():
    nodo = FakeNodo()
    c = Cliente("ana", nodo)
    c.unirse_a_tema("amigos", FRASE)
    n = c.enviar_tema("amigos", "nos vemos a las 8", ["bb" * 32])
    assert n == 1
    destino, cifrado = nodo.enviados[0]
    assert destino == "bb" * 32
    # El cifrado es mas grande que 256B y NO contiene el texto en claro.
    assert len(cifrado) > TAMANO_MENSAJE
    assert b"nos vemos" not in cifrado
    # Al descifrar con la clave del tema, se recupera el mensaje.
    from nacl.secret import SecretBox
    box = SecretBox(clave_de_tema("amigos", FRASE))
    plano = box.decrypt(cifrado)
    d = desempaquetar_mensaje(plano)
    assert d["texto"] == b"nos vemos a las 8"


def test_enviar_tema_excluye_al_emisor():
    nodo = FakeNodo(mi_id="aa" * 32)
    c = Cliente("ana", nodo)
    c.unirse_a_tema("amigos", FRASE)
    n = c.enviar_tema("amigos", "hola", ["aa" * 32, "bb" * 32])
    assert n == 1     # solo bb, no aa (yo mismo)
    assert nodo.enviados[0][0] == "bb" * 32


def test_recibir_mensaje_directo():
    nodo = FakeNodo()
    c = Cliente("ana", nodo)
    msj = empaquetar_mensaje(PRIVADO, hash_tema("directo"), b"hola")
    nodo.recibidos.append(msj)
    nuevos = c.recibir_pendientes()
    assert len(nuevos) == 1
    assert nuevos[0]["tipo"] == "privado"
    assert nuevos[0]["texto"] == "hola"


def test_recibir_mensaje_de_tema():
    nodo = FakeNodo()
    c = Cliente("ana", nodo)
    c.unirse_a_tema("amigos", FRASE)
    # Alguien cifra un mensaje con la clave del tema y lo deja en recibidos.
    msj = empaquetar_mensaje(PRIVADO, hash_tema("amigos"), b"hola grupo")
    from nacl.secret import SecretBox
    box = SecretBox(clave_de_tema("amigos", FRASE))
    nodo.recibidos.append(box.encrypt(msj))
    nuevos = c.recibir_pendientes()
    assert len(nuevos) == 1
    assert nuevos[0]["tipo"] == "tema"
    assert nuevos[0]["tema"] == "amigos"
    assert nuevos[0]["texto"] == "hola grupo"


def test_recibir_no_duplica():
    nodo = FakeNodo()
    c = Cliente("ana", nodo)
    msj = empaquetar_mensaje(PRIVADO, hash_tema("directo"), b"hola")
    nodo.recibidos.append(msj)
    assert len(c.recibir_pendientes()) == 1
    assert len(c.recibir_pendientes()) == 0     # ya leido
    nodo.recibidos.append(msj)
    assert len(c.recibir_pendientes()) == 0     # repeticion (RFC 8.6): se descarta
    nodo.recibidos.append(empaquetar_mensaje(PRIVADO, hash_tema("directo"), b"hola"))
    assert len(c.recibir_pendientes()) == 1     # otro mensaje, aunque diga lo mismo


def test_mensaje_no_descifrable_se_ignora():
    nodo = FakeNodo()
    c = Cliente("ana", nodo)
    nodo.recibidos.append(b"basura" * 100)
    assert c.recibir_pendientes() == []


def test_empaquetar_publico_marca_bien():
    c = Cliente("ana", FakeNodo())
    msj = c.empaquetar_publico("noticias", "algo nuevo")
    d = desempaquetar_mensaje(msj)
    from app.mensaje import PUBLICO, leer_publico
    assert d["visibilidad"] == PUBLICO
    assert leer_publico(d) == ("noticias", "algo nuevo")


def test_enviar_publico_va_a_un_gateway():
    nodo = FakeNodo(gateways=["cc" * 32])
    c = Cliente("ana", nodo)
    assert len(c.enviar_publico("noticias", "hola mundo")) == 3
    assert nodo.enviados[0][0] == "cc" * 32


def test_enviar_publico_sin_gateway_se_rechaza():
    c = Cliente("ana", FakeNodo())
    with pytest.raises(ClienteError, match="gateway"):
        c.enviar_publico("noticias", "hola")


def test_olvidar_todo_borra_llaves_de_temas():
    c = Cliente("ana", FakeNodo())
    c.unirse_a_tema("amigos", FRASE)
    c.olvidar_todo()
    assert c.temas() == []