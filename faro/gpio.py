import threading
import time

PIN_LED_TX = 22
PIN_LED_RX = 23
PIN_PANICO = 24


def _gpiozero():
    try:
        import gpiozero
        return gpiozero
    except Exception:
        return None


class Indicadores:


    def __init__(self, pin_tx: int = PIN_LED_TX, pin_rx: int = PIN_LED_RX,
                 usar_gpio: bool = True):
        gz = _gpiozero() if usar_gpio else None
        self._tx = gz.LED(pin_tx) if gz else None
        self._rx = gz.LED(pin_rx) if gz else None
        self.estado = {"tx": False, "rx": False}

    @property
    def real(self) -> bool:
        return self._tx is not None

    def tx(self, encendido: bool) -> None:
        self.estado["tx"] = encendido
        if self._tx:
            self._tx.on() if encendido else self._tx.off()

    def rx_pulso(self, segundos: float = 0.05) -> None:

        self.estado["rx"] = True
        if self._rx:
            self._rx.blink(on_time=segundos, off_time=0, n=1, background=True)

    def parpadear_panico(self, veces: int = 5, hz: float = 5.0) -> None:

        medio = 0.5 / hz
        for _ in range(veces):
            self.tx(True); self._set_rx(True)
            time.sleep(medio)
            self.tx(False); self._set_rx(False)
            time.sleep(medio)

    def _set_rx(self, encendido: bool) -> None:
        self.estado["rx"] = encendido
        if self._rx:
            self._rx.on() if encendido else self._rx.off()


class BotonPanico:


    def __init__(self, al_presionar, pin: int = PIN_PANICO, usar_gpio: bool = True):
        self._al_presionar = al_presionar
        self._ocupado = threading.Lock()
        gz = _gpiozero() if usar_gpio else None
        self._boton = None
        if gz:
            self._boton = gz.Button(pin, pull_up=True, bounce_time=0.05)
            self._boton.when_pressed = self.disparar

    @property
    def real(self) -> bool:
        return self._boton is not None

    def disparar(self) -> None:

        if not self._ocupado.acquire(blocking=False):
            return
        try:
            self._al_presionar()
        finally:
            self._ocupado.release()
