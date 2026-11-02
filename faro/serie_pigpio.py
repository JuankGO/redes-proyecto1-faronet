"""Puerto serie por software con pigpio, para un Faro cableado a GPIO17/GPIO27.

Se usa con --uart pigpio en lugar de /dev/ttyAMA0. Se comporta como el
objeto serial de pyserial que espera MedioUART (write, flush, in_waiting,
read, reset_input_buffer, close), asi el resto del codigo no cambia.

Diferencias con el Faro de la UART de hardware:
    GPIO17 (pin 11) TX hacia el 2N2222A del LED IR
    GPIO27 (pin 13) RX desde el colector del fototransistor, con 10 k a 3V3:
                    con luz lee 0, por eso la lectura se invierte.

Requiere el servicio pigpiod: sudo systemctl enable --now pigpiod
"""
import time

PIN_TX = 17
PIN_RX = 27
# Byte extra al final: el lector de pigpio cierra cada byte con el siguiente
# cambio de luz. Sin el, los ultimos bits en 1 de la senal se leian como 0.
# 0x55 son cuatro pares Manchester validos, asi no ensucia la senal.
RELLENO = b"\x55"


class SeriePigpio:
    def __init__(self, baudios: int = 9600, pin_tx: int = PIN_TX,
                 pin_rx: int = PIN_RX, invertir_rx: bool = True, pi=None):
        if pi is None:
            import pigpio  # solo se necesita en la Raspberry
            pi = pigpio.pi()
            if not pi.connected:
                raise RuntimeError("no se pudo conectar con pigpiod "
                                   "(sudo systemctl enable --now pigpiod)")
        self.pi = pi
        self.baudios = baudios
        self.pin_tx, self.pin_rx = pin_tx, pin_rx
        self._buf = bytearray()
        self.pi.set_mode(pin_tx, 1)          # salida
        self.pi.write(pin_tx, 1)             # reposo UART = LED IR encendido
        self.pi.bb_serial_read_open(pin_rx, baudios, 8)
        if invertir_rx:
            self.pi.bb_serial_invert(pin_rx, 1)

    def _leer_pendiente(self) -> None:
        cantidad, datos = self.pi.bb_serial_read(self.pin_rx)
        if cantidad > 0:
            self._buf += datos

    @property
    def in_waiting(self) -> int:
        self._leer_pendiente()
        return len(self._buf)

    def read(self, n: int) -> bytes:
        self._leer_pendiente()
        datos = bytes(self._buf[:n])
        del self._buf[:n]
        return datos

    def write(self, datos: bytes) -> int:
        """Transmite y espera a que salga el ultimo bit."""
        self.pi.wave_add_new()
        self.pi.wave_add_serial(self.pin_tx, self.baudios, bytes(datos) + RELLENO)
        onda = self.pi.wave_create()
        try:
            self.pi.wave_send_once(onda)
            while self.pi.wave_tx_busy():
                time.sleep(0.005)
        finally:
            self.pi.wave_delete(onda)
        return len(datos)

    def flush(self) -> None:
        pass   # write ya espera a que termine la onda

    def reset_input_buffer(self) -> None:
        self._leer_pendiente()
        self._buf.clear()

    def close(self) -> None:
        try:
            self.pi.bb_serial_read_close(self.pin_rx)
            self.pi.write(self.pin_tx, 0)
        finally:
            self.pi.stop()
