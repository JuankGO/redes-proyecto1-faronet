"""Pruebas de la capa 1 sin hardware: MedioUART con un puerto serie falso,
tramas externas, duplicados, LEDs, boton y medicion de BER."""
import threading
import time

import pytest

from faro import frame, linea
from faro.dispositivo_luz_adaptador import DispositivoLuzAdaptador
from faro.gpio import BotonPanico, Indicadores
from faro.medio import MedioSimUDP, MedioUART, desempaquetar_medios, empaquetar_medios
from faro.medir import bits_distintos, trama_esperada

A, B = b"\xaa\xaa\xaa\xaa", b"\xbb\xbb\xbb\xbb"


class CableSerie:
    """Dos puertos serie falsos unidos: lo que escribe uno lo lee el otro."""

    class Punta:
        def __init__(self, cable, lado):
            self.cable, self.lado = cable, lado

        @property
        def in_waiting(self):
            with self.cable.lock:
                return len(self.cable.buf[self.lado])

        def read(self, n):
            with self.cable.lock:
                b = self.cable.buf[self.lado]
                datos, self.cable.buf[self.lado] = b[:n], b[n:]
                return bytes(datos)

        def write(self, datos):
            with self.cable.lock:
                self.cable.buf[1 - self.lado] += datos

        def flush(self):
            pass

        def close(self):
            pass

    def __init__(self):
        self.lock = threading.Lock()
        self.buf = [bytearray(), bytearray()]
        self.puntas = (self.Punta(self, 0), self.Punta(self, 1))


def test_empaquetar_medios_ida_y_vuelta():
    senal = linea.armar_senal(frame.codificar(frame.Trama(1, A, B, 3, b"hola")))
    assert desempaquetar_medios(empaquetar_medios(senal)) == senal
    # Una trama de 128 bytes ocupa 266 bytes de UART (RFC, seccion 2.2).
    maxima = frame.codificar(frame.Trama(1, A, B, 0, b"x" * frame.MAX_PAYLOAD))
    assert len(empaquetar_medios(linea.armar_senal(maxima))) == 266


def test_envio_confiable_por_uart_simulada():
    cable = CableSerie()
    ma = MedioUART(baudios=115200, serial_obj=cable.puntas[0])
    mb = MedioUART(baudios=115200, serial_obj=cable.puntas[1])
    ind_a, ind_b = Indicadores(usar_gpio=False), Indicadores(usar_gpio=False)
    fa = DispositivoLuzAdaptador(ma, A, indicadores=ind_a)
    fb = DispositivoLuzAdaptador(mb, B, indicadores=ind_b)
    recibido = []
    hilo = threading.Thread(target=lambda: recibido.append(fb.recibir(3.0)))
    hilo.start()
    assert fa.enviar_confiable(B, b"hola por luz") is True
    hilo.join()
    assert recibido[0].payload == b"hola por luz"
    assert ind_b.estado["rx"] is True          # el LED RX se encendio
    assert ind_a.estado["tx"] is False         # y el TX se apago al terminar


def test_medio_uart_ocupado_mientras_llegan_bytes():
    cable = CableSerie()
    m = MedioUART(baudios=9600, serial_obj=cable.puntas[0])
    assert m.ocupado() is False
    cable.puntas[1].write(b"\x55")
    assert m.ocupado() is True


def test_enviar_crudo_valida_la_trama():
    ma = MedioSimUDP(50011, [("127.0.0.1", 50012)])
    mb = MedioSimUDP(50012, [("127.0.0.1", 50011)])
    try:
        fa, fb = DispositivoLuzAdaptador(ma, A), DispositivoLuzAdaptador(mb, B)
        externa = frame.codificar(frame.Trama(frame.TIPO_DATA, frame.BROADCAST, A, 9, b"scapy"))
        fa.enviar_crudo(externa)
        t = fb.recibir(2.0)
        assert t.payload == b"scapy" and t.seq == 9
        danada = bytearray(externa); danada[-1] ^= 1
        with pytest.raises(frame.TramaError):
            fa.enviar_crudo(bytes(danada))
    finally:
        ma.cerrar(); mb.cerrar()


def test_retransmision_no_se_entrega_dos_veces():
    ma = MedioSimUDP(50021, [("127.0.0.1", 50022)])
    mb = MedioSimUDP(50022, [("127.0.0.1", 50021)])
    try:
        fa, fb = DispositivoLuzAdaptador(ma, A), DispositivoLuzAdaptador(mb, B)
        t = frame.Trama(frame.TIPO_DATA, B, A, 5, b"una vez")
        fa._transmitir(t)
        fa._transmitir(t)   # como si el ACK se hubiera perdido
        assert fb.recibir(1.0).payload == b"una vez"
        assert fb.recibir(0.5) is None
    finally:
        ma.cerrar(); mb.cerrar()


def test_version_cero_se_rechaza():
    crudo = bytearray(frame.codificar(frame.Trama(1, A, B, 1, b"x")))
    crudo[0] = 0
    crudo[-2:] = frame.crc16(bytes(crudo[:-2])).to_bytes(2, "big")
    with pytest.raises(frame.TramaError):
        frame.decodificar(bytes(crudo))


def test_direccion_reservada_se_rechaza():
    with pytest.raises(ValueError):
        DispositivoLuzAdaptador(None, frame.BROADCAST)


def test_boton_panico_no_se_dispara_dos_veces_a_la_vez():
    llamadas = []

    def lento():
        llamadas.append(1)
        time.sleep(0.2)

    boton = BotonPanico(lento, usar_gpio=False)
    hilos = [threading.Thread(target=boton.disparar) for _ in range(3)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert llamadas == [1]


def test_bits_distintos_y_trama_esperada():
    t = trama_esperada(7)
    assert bits_distintos(t, t) == 0
    mal = bytearray(t); mal[20] ^= 0b101
    assert bits_distintos(t, bytes(mal)) == 2
    assert frame.decodificar(t).seq == 7


class _SerieEspejo:
    """Puerto serie falso donde lo que se escribe vuelve al mismo puerto (loopback)."""

    def __init__(self):
        self.buf = bytearray()

    @property
    def in_waiting(self):
        return len(self.buf)

    def read(self, n):
        datos, self.buf = bytes(self.buf[:n]), self.buf[n:]
        return datos

    def write(self, datos):
        self.buf += datos

    def flush(self):
        pass

    def reset_input_buffer(self):
        self.buf = bytearray()

    def close(self):
        pass


def test_loopback_de_un_solo_faro(monkeypatch):
    from faro import medir
    from faro.medio import MedioUART
    monkeypatch.setattr(medir, "crear_medio", lambda a: MedioUART(serial_obj=_SerieEspejo()))
    a = type("A", (), {"tramas": 3, "espera_ack": 0.5, "pausa": 0.0})()
    recibidas, errores = medir.cmd_loopback(a)
    assert recibidas == 3 and errores == 0
