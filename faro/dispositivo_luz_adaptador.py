import random
import time
from collections import deque

from faro import frame, linea
from faro.medio import Medio


class DispositivoLuzAdaptador:
    def __init__(self, medio: Medio, direccion: bytes,
                 max_reintentos: int = 3, espera_ack: float = 1.0,
                 indicadores=None):
        if len(direccion) != 4 or direccion in (b"\x00" * 4, frame.BROADCAST):
            raise ValueError("direccion fisica invalida")
        self.medio = medio
        self.direccion = direccion
        self.max_reintentos = max_reintentos
        self.espera_ack = espera_ack
        self.indicadores = indicadores
        self._seq = 0
        self._pendientes = deque()
        self._ultimo_de = {}
        self.estadisticas = {"enviadas": 0, "recibidas": 0, "descartadas": 0,
                             "reintentos": 0}



    def _esperar_canal_libre(self) -> None:
        intento = 0
        while self.medio.ocupado():
            intento += 1
            time.sleep(random.uniform(0, 0.05 * 2 ** min(intento, 6)))

    def _transmitir_bytes(self, trama_bytes: bytes) -> None:
        self._esperar_canal_libre()
        if self.indicadores:
            self.indicadores.tx(True)
        try:
            self.medio.enviar(linea.armar_senal(trama_bytes))
        finally:
            if self.indicadores:
                self.indicadores.tx(False)
        self.estadisticas["enviadas"] += 1

    def _transmitir(self, trama: frame.Trama) -> None:
        self._transmitir_bytes(frame.codificar(trama))

    def _siguiente_seq(self) -> int:
        self._seq = (self._seq + 1) % 256
        return self._seq

    def enviar(self, dst: bytes, payload: bytes, tipo: int = frame.TIPO_DATA) -> int:

        seq = self._siguiente_seq()
        self._transmitir(frame.Trama(tipo, dst, self.direccion, seq, payload))
        return seq

    def enviar_crudo(self, trama_bytes: bytes) -> None:

        frame.decodificar(bytes(trama_bytes))
        self._transmitir_bytes(bytes(trama_bytes))

    def enviar_confiable(self, dst: bytes, payload: bytes) -> bool:

        seq = self._siguiente_seq()
        trama = frame.Trama(frame.TIPO_DATA, dst, self.direccion, seq, payload)
        for intento in range(1 + self.max_reintentos):
            if intento:
                self.estadisticas["reintentos"] += 1
            self._transmitir(trama)
            limite = time.monotonic() + self.espera_ack
            while time.monotonic() < limite:
                t = self._leer_una(max(0.01, limite - time.monotonic()))
                if t is None:
                    continue
                if t.tipo == frame.TIPO_ACK and t.seq == seq and t.src == dst:
                    return True
                if t.tipo != frame.TIPO_ACK:


                    if self._aceptar(t):
                        self._pendientes.append(t)
        return False

    def _aceptar(self, t) -> bool:

        if t.tipo == frame.TIPO_DATA and t.dst == self.direccion:
            self._transmitir(frame.Trama(frame.TIPO_ACK, t.src, self.direccion, t.seq))
            if self._ultimo_de.get(t.src) == t.seq:
                return False
            self._ultimo_de[t.src] = t.seq
        return True

    def cambiar_direccion(self, nueva: bytes) -> None:

        if len(nueva) != 4 or nueva in (b"\x00" * 4, frame.BROADCAST):
            raise ValueError("direccion fisica invalida")
        self.direccion = nueva
        self._ultimo_de.clear()
        self._pendientes.clear()
        self.enviar(frame.BROADCAST, b"", frame.TIPO_BEACON)



    def _leer_una(self, timeout: float):
        medios = self.medio.recibir(timeout)
        if medios is None:
            return None
        try:
            trama = frame.decodificar(linea.extraer_trama(medios))
        except (linea.LineaError, frame.TramaError):
            self.estadisticas["descartadas"] += 1
            return None
        if trama.src == self.direccion:

            return None
        if trama.dst not in (self.direccion, frame.BROADCAST):
            return None
        if trama.tipo not in (frame.TIPO_DATA, frame.TIPO_ACK, frame.TIPO_BEACON):
            return None
        self.estadisticas["recibidas"] += 1
        if self.indicadores:
            self.indicadores.rx_pulso()
        return trama

    def recibir(self, timeout: float = 1.0):

        limite = time.monotonic() + timeout
        while True:
            if self._pendientes:
                return self._pendientes.popleft()
            restante = limite - time.monotonic()
            if restante <= 0:
                return None
            t = self._leer_una(restante)
            if t is None:
                return None
            if t.tipo == frame.TIPO_ACK:
                continue
            if not self._aceptar(t):
                continue
            return t
