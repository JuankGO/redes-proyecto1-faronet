"""DispositivoLuzAdaptador: la biblioteca que usa el nodo para hablar con el Faro."""
import random
import time
from collections import deque

from faro import frame, linea
from faro.medio import Medio


class DispositivoLuzAdaptador:
    def __init__(self, medio: Medio, direccion: bytes,
                 max_reintentos: int = 3, espera_ack: float = 1.0):
        self.medio = medio
        self.direccion = direccion
        self.max_reintentos = max_reintentos
        self.espera_ack = espera_ack
        self._seq = 0
        self._pendientes = deque()

    def _esperar_canal_libre(self) -> None:
        intento = 0
        while self.medio.ocupado():
            intento += 1
            time.sleep(random.uniform(0, 0.05 * 2 ** min(intento, 6)))

    def _transmitir(self, trama: frame.Trama) -> None:
        self._esperar_canal_libre()
        self.medio.enviar(linea.armar_senal(frame.codificar(trama)))

    def _leer_una(self, timeout: float):
        medios = self.medio.recibir(timeout)
        if medios is None:
            return None
        try:
            trama = frame.decodificar(linea.extraer_trama(medios))
        except (linea.LineaError, frame.TramaError):
            return None
        if trama.dst not in (self.direccion, frame.BROADCAST):
            return None
        return trama

    def enviar(self, dst: bytes, payload: bytes, tipo: int = frame.TIPO_DATA) -> int:
        """Envia una vez, sin esperar confirmacion. Devuelve el SEQ usado."""
        self._seq = (self._seq + 1) % 256
        self._transmitir(frame.Trama(tipo, dst, self.direccion, self._seq, payload))
        return self._seq

    def enviar_confiable(self, dst: bytes, payload: bytes) -> bool:
        """Envia y espera un ACK; reintenta si no llega."""
        seq = self.enviar(dst, payload)
        for _ in range(self.max_reintentos):
            limite = time.time() + self.espera_ack
            while time.time() < limite:
                t = self._leer_una(max(0.01, limite - time.time()))
                if t is None:
                    continue
                if t.tipo == frame.TIPO_ACK and t.seq == seq and t.src == dst:
                    return True
                self._pendientes.append(t)
            self._transmitir(frame.Trama(frame.TIPO_DATA, dst, self.direccion, seq, payload))
        return False

    def recibir(self, timeout: float = 1.0):
        """Devuelve la siguiente trama DATA/BEACON para este nodo (o None)."""
        while True:
            t = self._pendientes.popleft() if self._pendientes else self._leer_una(timeout)
            if t is None:
                return None
            if t.tipo == frame.TIPO_ACK:
                continue
            if t.tipo == frame.TIPO_DATA and t.dst == self.direccion:
                self._transmitir(frame.Trama(frame.TIPO_ACK, t.src, self.direccion, t.seq))
            return t
        

        
"""class MedioGPIO(Medio):
    def enviar(self, medios):   # prende y apaga el LED según los bits
    def recibir(self, timeout): # lee el LDR """