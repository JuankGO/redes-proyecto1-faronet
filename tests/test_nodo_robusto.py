"""Pruebas de los arreglos del nodo: robustez, propagacion, anonimato, panico
y el enlace Faro entre dos comunidades (simulado por UDP)."""
import json
import socket
import time

import pytest
from nacl.public import PrivateKey
from nacl.signing import SigningKey

from faro.dispositivo_luz_adaptador import DispositivoLuzAdaptador
from faro.medio import MedioSimUDP
from mesh.directorio import DirectorioError, crear_entrada, firmar, validar
from mesh.enlace_faro import EnlaceFaro
from mesh.nodo import Nodo
from mesh.saltos import SaltosError


def _nodo(puerto, semillas=(), **kw):
    return Nodo(puerto, SigningKey.generate(), PrivateKey.generate(),
                semillas=list(semillas), **kw)


def _esperar(condicion, timeout=8.0, paso=0.1):
    limite = time.time() + timeout
    while time.time() < limite:
        if condicion():
            return True
        time.sleep(paso)
    return False


def _mandar(puerto, obj):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    datos = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
    s.sendto(datos, ("127.0.0.1", puerto))
    s.close()


@pytest.mark.parametrize("basura", [
    {"t": "ruta", "id": "x" * 64, "tabla": {"y" * 64: "no-soy-numero"}},
    {"t": "dir", "entrada": {"v": "1"}, "firma": None},
    {"t": "dir", "entradas": "no es lista"},
    {"t": "hello", "id": 5},
    {"t": "celda", "hacia": None, "frags": [1, 2]},
    {"t": "celda", "frags": ["@@no-base64@@"]},
    {"t": "hello", "v": 99},
    [1, 2, 3],
    b"\xff\xfe no es utf8",
])
def test_paquete_mal_formado_no_tumba_el_nodo(basura):
    n = _nodo(9201)
    n.arrancar()
    try:
        time.sleep(0.2)
        _mandar(9201, basura)
        time.sleep(0.4)
        assert n._hilo.is_alive()
        assert n.descartados >= 1
    finally:
        n.detener()


def test_entrada_con_creado_en_el_futuro_se_rechaza():
    k = SigningKey.generate()
    e = crear_entrada(k, PrivateKey.generate(), "udp", "1.2.3.4:1", ttl=60)
    e["creado"] = int(time.time()) + 10 * 365 * 86400
    with pytest.raises(DirectorioError, match="futuro"):
        validar(e, firmar(e, k))


def test_directorio_se_propaga_mas_alla_del_vecino():
    b = _nodo(9212)
    a = _nodo(9211, [("127.0.0.1", 9212)])
    c = _nodo(9213, [("127.0.0.1", 9212)])
    nodos = (a, b, c)
    try:
        for n in nodos:
            n.arrancar()
        time.sleep(0.2)

        def ronda():
            for n in nodos:
                n.enviar_ahora()
            return c.mi_id in a.directorio and a.mi_id in c.directorio
        assert _esperar(ronda, timeout=5.0, paso=0.3)
        # A y C no son vecinos directos: la ruta pasa por B.
        assert a.vecinos.obtener(c.mi_id) is None
        assert _esperar(lambda: (ronda() or True) and a.rutas.ruta_hacia(c.mi_id) is not None,
                        timeout=5.0, paso=0.3)
        assert a.rutas.ruta_hacia(c.mi_id)["siguiente"] == b.mi_id
    finally:
        for n in nodos:
            n.detener()


def test_sin_relays_suficientes_no_manda_sin_anonimato():
    b = _nodo(9232)
    a = _nodo(9231, [("127.0.0.1", 9232)])
    b.semillas = [("127.0.0.1", 9231)]
    try:
        a.arrancar(); b.arrancar(); time.sleep(0.2)
        a.enviar_ahora(); b.enviar_ahora()
        assert _esperar(lambda: b.mi_id in a.directorio)
        with pytest.raises(SaltosError, match="relays posibles"):
            a.mandar_a(b.mi_id, b"hola")
        # En modo de prueba explicito si se permite.
        assert a.mandar_a(b.mi_id, b"hola", permitir_directo=True) == []
        assert _esperar(lambda: b.recibidos == [b"hola"])
    finally:
        a.detener(); b.detener()


def test_panico_borra_estado_y_cambia_identidad(tmp_path):
    (tmp_path / "firma.key").write_bytes(b"F" * 32)
    (tmp_path / "cifrado.key").write_bytes(b"C" * 32)
    n = _nodo(9241, carpeta=tmp_path)
    viejo = n.mi_id
    n.recibidos.append(b"algo")
    llamado = []
    n.al_panico = lambda: llamado.append(True)
    borrados = n.panico()
    assert set(borrados) == {"firma.key", "cifrado.key"}
    assert n.mi_id != viejo
    assert n.recibidos == []
    assert list(n.directorio.keys()) == [n.mi_id]
    assert llamado == [True]
    n.sock.close()


def test_dos_comunidades_unidas_por_faro():
    """Comunidad A (5 nodos + gateway) y comunidad B (gateway + 1 nodo).

    Los gateways solo se hablan por el Faro (simulado por UDP). Un nodo de
    A manda a un nodo de B por una cebolla de 3 relays.
    """
    base = 9300
    medio_a = MedioSimUDP(base + 90, [("127.0.0.1", base + 91)])
    medio_b = MedioSimUDP(base + 91, [("127.0.0.1", base + 90)])
    enlace_a = EnlaceFaro(DispositivoLuzAdaptador(medio_a, b"\xaa\x00\x00\x01", espera_ack=0.3))
    enlace_b = EnlaceFaro(DispositivoLuzAdaptador(medio_b, b"\xbb\x00\x00\x02", espera_ack=0.3))

    puertos_a = [base + i for i in range(5)]
    gw_a = _nodo(base + 10, [("127.0.0.1", p) for p in puertos_a], enlace_faro=enlace_a, rol="gateway")
    com_a = [_nodo(p, [("127.0.0.1", q) for q in puertos_a if q != p] + [("127.0.0.1", base + 10)])
             for p in puertos_a]
    gw_b = _nodo(base + 20, [("127.0.0.1", base + 21)], enlace_faro=enlace_b, rol="gateway")
    destino = _nodo(base + 21, [("127.0.0.1", base + 20)])
    todos = com_a + [gw_a, gw_b, destino]
    try:
        for n in todos:
            n.arrancar()
        time.sleep(0.3)
        origen = com_a[0]

        def listo():
            for n in todos:
                n.enviar_ahora()
            return destino.mi_id in origen.directorio and origen.rutas.ruta_hacia(destino.mi_id)
        assert _esperar(listo, timeout=40.0, paso=1.0), "la ruta entre comunidades no se formo"
        # El destino esta del otro lado del Faro: la ruta pasa por el gateway A.
        assert origen.rutas.ruta_hacia(destino.mi_id)["siguiente"] == gw_a.mi_id

        relays = origen.mandar_a(destino.mi_id, b"hola desde la comunidad A")
        assert len(relays) == 3
        assert _esperar(lambda: destino.recibidos, timeout=30.0)
        assert destino.recibidos[0] == b"hola desde la comunidad A"
    finally:
        for n in todos:
            n.detener()
        medio_a.cerrar(); medio_b.cerrar()


class _EnlaceFalso:
    def __init__(self):
        self.al_recibir = None
        self.direcciones = []

    def rotar_direccion(self, nueva):
        self.direcciones.append(nueva)


def test_direccion_faro_rota_cada_24_horas(tmp_path):
    from mesh.nodo import INTERVALO_ROTACION
    enlace = _EnlaceFalso()
    n = _nodo(9690, enlace_faro=enlace, carpeta=tmp_path)
    try:
        n._mantenimiento(time.time())
        assert enlace.direcciones == []            # todavia no toca
        n._ultima_rotacion -= INTERVALO_ROTACION + 1
        n._mantenimiento(time.time())
        assert len(enlace.direcciones) == 1
        assert (tmp_path / "direccion.bin").read_bytes() == enlace.direcciones[0]
        n._mantenimiento(time.time())
        assert len(enlace.direcciones) == 1        # no rota dos veces seguidas
    finally:
        n.sock.close()
