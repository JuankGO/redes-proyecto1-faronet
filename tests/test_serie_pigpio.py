"""SeriePigpio sin hardware: un pigpio falso que devuelve por RX lo que sale por TX,
imitando el defecto real del lector de pigpio en el ultimo byte."""
from faro import frame, linea
from faro.medio import MedioUART
from faro.serie_pigpio import RELLENO, SeriePigpio

A, B = b"\xaa\xaa\xaa\xaa", b"\xbb\xbb\xbb\xbb"


def _perder_unos_finales(byte: int) -> int:
    """Asi llego el ultimo byte en la Raspberry: d5 -> 15, ff -> 00."""
    for bit in range(7, -1, -1):
        if not byte & (1 << bit):
            break
        byte &= ~(1 << bit)
    return byte


class PigpioEspejo:
    def __init__(self):
        self.rx = bytearray()
        self.niveles = {}

    def set_mode(self, pin, modo): pass
    def write(self, pin, nivel): self.niveles[pin] = nivel
    def bb_serial_read_open(self, pin, baudios, bits): pass
    def bb_serial_invert(self, pin, invertir): pass
    def bb_serial_read_close(self, pin): pass
    def wave_add_new(self): pass
    def wave_create(self): return 0
    def wave_send_once(self, onda): pass
    def wave_tx_busy(self): return False
    def wave_delete(self, onda): pass
    def stop(self): pass

    def wave_add_serial(self, pin, baudios, datos):
        datos = bytearray(datos)
        datos[-1] = _perder_unos_finales(datos[-1])
        self.rx += datos

    def bb_serial_read(self, pin):
        datos, self.rx = bytes(self.rx), bytearray()
        return len(datos), datos


def test_defecto_simulado_coincide_con_la_raspberry():
    assert _perder_unos_finales(0xD5) == 0x15
    assert _perder_unos_finales(0xFF) == 0x00


def test_relleno_es_manchester_valido():
    assert linea.manchester_decodificar(linea.bytes_a_bits(RELLENO)) == [1, 1, 1, 1]


def test_trama_llega_completa_aunque_se_dane_el_ultimo_byte():
    medio = MedioUART(baudios=1200, serial_obj=SeriePigpio(1200, pi=PigpioEspejo()))
    for payload in (b"", b"hola faro", b"\xff" * frame.MAX_PAYLOAD):
        trama = frame.codificar(frame.Trama(frame.TIPO_DATA, A, B, 7, payload))
        medio.enviar(linea.armar_senal(trama))
        assert linea.extraer_trama(medio.recibir(1.0)) == trama


def test_reposo_enciende_el_led_y_cerrar_lo_apaga():
    pi = PigpioEspejo()
    serie = SeriePigpio(pi=pi)
    assert pi.niveles[17] == 1
    serie.close()
    assert pi.niveles[17] == 0


def test_loopback_de_medir_con_pigpio(monkeypatch):
    from faro import medir
    monkeypatch.setattr(medir, "crear_medio",
                        lambda a: MedioUART(serial_obj=SeriePigpio(pi=PigpioEspejo())))
    a = type("A", (), {"tramas": 3, "espera_ack": 0.5, "pausa": 0.0})()
    recibidas, errores = medir.cmd_loopback(a)
    assert recibidas == 3 and errores == 0
