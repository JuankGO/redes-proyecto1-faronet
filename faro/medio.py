"""Medios fisicos del Faro.

Un Medio mueve listas de medios bits (0/1) entre dos Faros. Hay dos:

- MedioUART: el Faro real. Usa la UART de hardware de la Raspberry Pi
  (GPIO14 TXD -> LED IR, GPIO15 RXD <- comparador). Los medios bits se
  empaquetan de 8 en 8 en bytes y viajan como 8N1.
- MedioSimUDP: simulacion por UDP para probar sin hardware.
"""
import socket
import time
from abc import ABC, abstractmethod

from faro import linea


class Medio(ABC):
    @abstractmethod
    def enviar(self, medios: list) -> None: ...

    @abstractmethod
    def recibir(self, timeout: float):
        """Devuelve una lista de 0/1 o None si vence el tiempo."""

    def ocupado(self) -> bool:
        """True si alguien mas esta transmitiendo (el medio real lo mide)."""
        return False

    def cerrar(self) -> None:
        pass


def empaquetar_medios(medios: list) -> bytes:
    """Agrupa medios bits de 8 en 8 (el primero en el bit mas alto).

    Si sobran bits, se completa con 1 (nivel de reposo de la linea).
    """
    resto = len(medios) % 8
    if resto:
        medios = list(medios) + [1] * (8 - resto)
    return linea.bits_a_bytes(medios)


def desempaquetar_medios(datos: bytes) -> list:
    return linea.bytes_a_bits(datos)


class MedioUART(Medio):
    """Faro real sobre la UART de la Raspberry Pi.

    La UART en reposo queda en 1, asi que el LED IR queda encendido entre
    tramas. El receptor da por terminada una senal cuando pasan
    'silencio_bytes' tiempos de byte sin recibir nada.
    """

    def __init__(self, puerto: str = "/dev/ttyAMA0", baudios: int = 9600,
                 silencio_bytes: int = 20, serial_obj=None):
        if serial_obj is None:
            import serial  # pyserial; solo se necesita en la Raspberry
            serial_obj = serial.Serial(puerto, baudios, bytesize=8,
                                       parity="N", stopbits=1, timeout=0)
        self.ser = serial_obj
        self.baudios = baudios
        # 10 bits por byte en 8N1
        self.tiempo_byte = 10.0 / baudios
        self.silencio = max(0.005, silencio_bytes * self.tiempo_byte)
        self._ultimo_rx = 0.0

    def enviar(self, medios: list) -> None:
        self.ser.write(empaquetar_medios(medios))
        self.ser.flush()   # espera a que salga el ultimo byte

    def recibir(self, timeout: float):
        limite = time.monotonic() + timeout
        datos = bytearray()
        while True:
            pendiente = self.ser.in_waiting
            if pendiente:
                datos += self.ser.read(pendiente)
                self._ultimo_rx = time.monotonic()
                continue
            ahora = time.monotonic()
            if datos and ahora - self._ultimo_rx >= self.silencio:
                return desempaquetar_medios(bytes(datos))
            if not datos and ahora >= limite:
                return None
            time.sleep(min(self.tiempo_byte, 0.002))

    def ocupado(self) -> bool:
        if self.ser.in_waiting:
            return True
        return (time.monotonic() - self._ultimo_rx) < self.silencio

    def cerrar(self) -> None:
        try:
            self.ser.close()
        except Exception:
            pass


class MedioSimUDP(Medio):
    def __init__(self, puerto_local: int, destinos: list):
        self.destinos = destinos
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", puerto_local))

    def enviar(self, medios: list) -> None:
        datos = bytes(medios)
        for destino in self.destinos:
            self.sock.sendto(datos, destino)

    def recibir(self, timeout: float):
        self.sock.settimeout(max(timeout, 0.001))
        try:
            datos, _ = self.sock.recvfrom(8192)
        except (socket.timeout, OSError):
            return None
        return list(datos)

    def cerrar(self):
        self.sock.close()
