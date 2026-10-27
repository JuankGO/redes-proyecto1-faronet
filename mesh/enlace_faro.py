"""Enlace Faro para la mesh (RFC, seccion 3.9).

Lleva los mismos mensajes JSON de la mesh por el Faro. Como un mensaje
puede medir mas que el payload de una trama (114 bytes), se parte en
fragmentos:

    | INDICE 2B | TOTAL 2B | DATOS hasta 110B |

Cada fragmento viaja en una trama DATA. Si se conoce la direccion fisica
del vecino se usa entrega confiable (ACK); si no (HELLO inicial), se
manda a difusion sin ACK.

Un solo hilo usa el DispositivoLuzAdaptador, porque la biblioteca no se
puede usar desde dos hilos a la vez. Los demas hilos solo encolan.
"""
import queue
import struct
import threading
import time

from faro import frame
from mesh.celda import MAX_FRAGMENTO

TIMEOUT_REENSAMBLADO = 10.0
MAX_MENSAJE = 64 * 1024


class EnlaceFaro:
    def __init__(self, adaptador, al_recibir=None):
        """al_recibir(datos: bytes, mac_origen: bytes) se llama al completar un mensaje."""
        self.adaptador = adaptador
        self.al_recibir = al_recibir
        self._salida = queue.Queue(maxsize=256)
        self._parcial = {}      # mac -> {"total", "piezas", "visto"}
        self._corriendo = False
        self._hilo = None
        self.perdidos = 0

    @property
    def direccion(self) -> bytes:
        return self.adaptador.direccion

    # ----- API -----

    def arrancar(self) -> None:
        self._corriendo = True
        self._hilo = threading.Thread(target=self._loop, daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._corriendo = False
        if self._hilo:
            self._hilo.join(timeout=3.0)

    def enviar(self, datos: bytes, dst: bytes = None) -> bool:
        """Encola un mensaje. dst = direccion fisica del vecino o None (difusion)."""
        if len(datos) > MAX_MENSAJE:
            return False
        try:
            self._salida.put_nowait(("msg", bytes(datos), dst))
            return True
        except queue.Full:
            self.perdidos += 1
            return False

    def rotar_direccion(self, nueva: bytes) -> None:
        """Cambia la direccion fisica desde el hilo del enlace."""
        self._salida.put(("rotar", nueva, None))

    # ----- hilo del enlace -----

    @staticmethod
    def fragmentar(datos: bytes) -> list:
        total = max(1, (len(datos) + MAX_FRAGMENTO - 1) // MAX_FRAGMENTO)
        return [struct.pack(">HH", i, total) + datos[i * MAX_FRAGMENTO:(i + 1) * MAX_FRAGMENTO]
                for i in range(total)]

    def _enviar_ahora(self, datos: bytes, dst) -> None:
        for frag in self.fragmentar(datos):
            if dst is None:
                self.adaptador.enviar(frame.BROADCAST, frag)
            elif not self.adaptador.enviar_confiable(dst, frag):
                self.perdidos += 1
                return   # el receptor descarta el mensaje incompleto

    def _recibir_fragmento(self, mac: bytes, frag: bytes) -> None:
        if len(frag) < 4:
            return
        indice, total = struct.unpack(">HH", frag[:4])
        if total == 0 or indice >= total or total * MAX_FRAGMENTO > MAX_MENSAJE:
            return
        ahora = time.monotonic()
        estado = self._parcial.get(mac)
        if indice == 0 or estado is None or estado["total"] != total:
            estado = {"total": total, "piezas": {}, "visto": ahora}
            self._parcial[mac] = estado
        estado["piezas"][indice] = frag[4:]
        estado["visto"] = ahora
        if len(estado["piezas"]) == total:
            del self._parcial[mac]
            datos = b"".join(estado["piezas"][i] for i in range(total))
            if self.al_recibir:
                try:
                    self.al_recibir(datos, mac)
                except Exception:
                    pass   # un mensaje malo no debe tumbar el enlace

    def _purgar(self) -> None:
        ahora = time.monotonic()
        for mac in [m for m, e in self._parcial.items()
                    if ahora - e["visto"] > TIMEOUT_REENSAMBLADO]:
            del self._parcial[mac]

    def _loop(self) -> None:
        while self._corriendo:
            try:
                tipo, datos, dst = self._salida.get_nowait()
            except queue.Empty:
                tipo = None
            try:
                if tipo == "msg":
                    self._enviar_ahora(datos, dst)
                elif tipo == "rotar":
                    self._parcial.clear()
                    self.adaptador.cambiar_direccion(datos)
                t = self.adaptador.recibir(0.05)
                while t is not None:
                    if t.tipo == frame.TIPO_DATA:
                        self._recibir_fragmento(t.src, t.payload)
                    t = self.adaptador.recibir(0.0) if self.adaptador._pendientes else None
                self._purgar()
            except Exception:
                time.sleep(0.05)   # error del medio: se sigue intentando
