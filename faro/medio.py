"""Interfaz Medio y el medio simulado por UDP."""
import socket
from abc import ABC, abstractmethod


class Medio(ABC):
    @abstractmethod
    def enviar(self, medios: list) -> None: ...

    @abstractmethod
    def recibir(self, timeout: float):
        """Devuelve una lista de 0/1 o None si vence el tiempo."""

    def ocupado(self) -> bool:
        """True si alguien mas esta transmitiendo (el medio real lo mide)."""
        return False


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
        self.sock.settimeout(timeout)
        try:
            datos, _ = self.sock.recvfrom(8192)
        except socket.timeout:
            return None
        return list(datos)

    def cerrar(self):
        self.sock.close()
