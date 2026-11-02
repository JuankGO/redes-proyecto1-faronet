import argparse
import base64
import json
import socket
import threading
import time
from collections import deque
from pathlib import Path

from nacl.public import PrivateKey, PublicKey
from nacl.signing import SigningKey

from faro import identidad
from faro.panico import panico as borrar_archivos
from mesh.celda import (
    CeldaError,
    desempaquetar_celda,
    empaquetar_celda,
    fragmentar,
    reensamblar,
)
from mesh.directorio import Directorio, DirectorioError, crear_entrada, es_hex64, firmar
from mesh.onion import (
    OnionError,
    abrir_como_destino,
    abrir_como_relay,
    construir_cebolla,
    direccion_a_texto,
    direccion_de_entrada,
)
from mesh.rutas import TablaRutas
from mesh.saltos import MINIMO_NODOS, SaltosError, elegir_saltos
from mesh.vecinos import TablaVecinos, VecinoError, validar_hello

VERSION = 1
INTERVALO_PERIODICO = 10.0
INTERVALO_DIR_FARO = 60.0
INTERVALO_ROTACION = 86400.0
TAMANO_DATAGRAMA = 65535
TTL_RECIBIDO = 3600
MAX_RECIBIDOS = 1000


class Nodo:


    def __init__(self, puerto: int, firma: SigningKey, cifrado: PrivateKey,
                 semillas: list = None, canal: str = "udp",
                 ip_publica: str = "127.0.0.1", ttl_entrada: int = 3600,
                 rol: str = None, enlace_faro=None, permitir_directo: bool = False,
                 carpeta: Path = None):
        if canal != "udp":
            raise ValueError("el canal principal del nodo es udp; el Faro se agrega con enlace_faro")
        self.puerto = puerto
        self.ip_publica = ip_publica
        self.mi_direccion = f"{ip_publica}:{puerto}"
        self.canal = canal
        self.rol = rol
        self.ttl_entrada = ttl_entrada
        self.semillas = list(semillas or [])
        self.permitir_directo = permitir_directo
        self.carpeta = Path(carpeta) if carpeta else None
        self.enlace = enlace_faro
        self._ultima_rotacion = time.time()
        if self.enlace is not None:
            self.enlace.al_recibir = self._al_recibir_faro

        self._lock = threading.RLock()
        self.directorio = Directorio()
        self.vecinos = TablaVecinos()
        self.recibidos = []
        self._horas_recibidos = deque()
        self.al_recibir_mensaje = None
        self.al_panico = None
        self.descartados = 0
        self._dir_enviado_faro = 0.0
        self._huella_dir_faro = frozenset()
        self._usar_identidad(firma, cifrado)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._corriendo = False
        self._hilo = None



    def _usar_identidad(self, firma: SigningKey, cifrado: PrivateKey) -> None:
        self.firma = firma
        self.cifrado = cifrado
        self.mi_id = firma.verify_key.encode().hex()
        self.rutas = TablaRutas(self.mi_id)
        self._renovar_entrada()

    def _renovar_entrada(self) -> None:
        self.entrada = crear_entrada(self.firma, self.cifrado, self.canal,
                                     self.mi_direccion, ttl=self.ttl_entrada, rol=self.rol)
        self.firma_entrada = firmar(self.entrada, self.firma)
        self.directorio[self.mi_id] = (self.entrada, self.firma_entrada)



    def arrancar(self) -> None:
        self.sock.bind(("0.0.0.0", self.puerto))
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
        except OSError:
            pass
        self._corriendo = True
        if self.enlace is not None:
            self.enlace.arrancar()
        self._hilo = threading.Thread(target=self._loop, daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        self._corriendo = False
        if self.enlace is not None:
            self.enlace.detener()
        try:
            self.sock.close()
        except OSError:
            pass
        if self._hilo:
            self._hilo.join(timeout=2.0)

    def _loop(self) -> None:
        self._periodico()
        ultimo_periodico = time.time()
        while self._corriendo:
            try:
                self.sock.settimeout(0.5)
                datos, addr = self.sock.recvfrom(TAMANO_DATAGRAMA)
                self._procesar(datos, ("udp", addr))
            except socket.timeout:
                pass
            except OSError:
                if not self._corriendo:
                    break
                continue
            except Exception:
                self.descartados += 1
            ahora = time.time()
            if ahora - ultimo_periodico >= INTERVALO_PERIODICO:
                try:
                    self._periodico()
                except Exception:
                    pass
                ultimo_periodico = ahora
            self._mantenimiento(ahora)

    def _mantenimiento(self, ahora: float) -> None:
        with self._lock:
            for perdido in self.vecinos.olvidar_vencidos(ahora):
                self.rutas.olvidar_via(perdido)
            self.rutas.olvidar_vencidas(ahora=ahora)
            self.directorio.purgar(ahora)
            if ahora - self.entrada["creado"] >= self.ttl_entrada / 2:
                self._renovar_entrada()
            while self._horas_recibidos and ahora - self._horas_recibidos[0] >= TTL_RECIBIDO:
                self._horas_recibidos.popleft()
                if self.recibidos:
                    self.recibidos.pop(0)
        if self.enlace is not None and ahora - self._ultima_rotacion >= INTERVALO_ROTACION:
            self.rotar_direccion_faro()

    def rotar_direccion_faro(self) -> None:

        if self.enlace is None:
            return
        from faro import direccion as dirmod
        ruta = (self.carpeta / "direccion.bin") if self.carpeta else None
        self.enlace.rotar_direccion(dirmod.rotar(ruta) if ruta else dirmod.nueva())
        self._ultima_rotacion = time.time()



    def _mensajes_periodicos(self, canal: str, direccion: str) -> list:
        hello = {"t": "hello", "v": VERSION, "id": self.mi_id, "canal": canal,
                 "dir": direccion, "ts": int(time.time())}
        dir_msg = {"t": "dir", "v": VERSION, "entradas": self.directorio.para_transporte()}
        ruta_msg = {"t": "ruta", "v": VERSION, "id": self.mi_id, "tabla": self.rutas.anuncio()}
        return [hello, dir_msg, ruta_msg]

    def _periodico(self) -> None:
        with self._lock:
            mensajes = self._mensajes_periodicos("udp", self.mi_direccion)
            destinos = self._destinos_udp()
        for destino in destinos:
            for m in mensajes:
                self._mandar_udp(m, destino)
            time.sleep(0.002)
        if self.enlace is not None:
            self._periodico_faro()

    def _periodico_faro(self) -> None:
        with self._lock:
            hello, dir_msg, ruta_msg = self._mensajes_periodicos("faro", self.enlace.direccion.hex())
            vecinos_faro = [bytes.fromhex(d) for _, c, d, _ in self.vecinos.listar() if c == "faro"]
        dst = vecinos_faro[0] if len(vecinos_faro) == 1 else None
        self.enlace.enviar(self._codificar(hello), None)
        self.enlace.enviar(self._codificar(ruta_msg), dst)

        huella = frozenset((e["id"], e["creado"]) for e in self.directorio.entradas())
        ahora = time.time()
        if huella != self._huella_dir_faro or ahora - self._dir_enviado_faro >= INTERVALO_DIR_FARO:
            self._dir_enviado_faro = ahora
            self._huella_dir_faro = huella
            self.enlace.enviar(self._codificar(dir_msg), dst)

    def _destinos_udp(self) -> list:
        destinos = set(self.semillas)
        for _, canal, direccion, _ in self.vecinos.listar():
            if canal != "udp":
                continue
            ip, puerto = direccion.rsplit(":", 1)
            destinos.add((ip, int(puerto)))
        destinos.discard((self.ip_publica, self.puerto))
        return sorted(destinos)

    @staticmethod
    def _codificar(mensaje: dict) -> bytes:
        return json.dumps(mensaje, separators=(",", ":")).encode("utf-8")

    def _mandar_udp(self, mensaje: dict, destino: tuple) -> None:
        try:
            self.sock.sendto(self._codificar(mensaje), destino)
        except OSError:
            pass

    def enviar_ahora(self) -> None:

        self._periodico()



    def _al_recibir_faro(self, datos: bytes, mac: bytes) -> None:
        self._procesar(datos, ("faro", mac))

    def _procesar(self, datos: bytes, origen) -> None:

        try:
            mensaje = json.loads(datos.decode("utf-8"))
            if not isinstance(mensaje, dict):
                raise ValueError("no es objeto")
            v = mensaje.get("v", VERSION)
            if not isinstance(v, int) or isinstance(v, bool) or not (1 <= v <= VERSION):
                raise ValueError("version no soportada")
            t = mensaje.get("t")
            with self._lock:
                if t == "hello":
                    self._on_hello(mensaje, origen)
                elif t == "dir":
                    self._on_dir(mensaje)
                elif t == "ruta":
                    self._on_ruta(mensaje)
                elif t == "celda":
                    pass
                else:
                    raise ValueError("tipo desconocido")
            if t == "celda":
                self._on_celda(mensaje)
        except Exception:
            self.descartados += 1

    def _on_hello(self, mensaje: dict, origen) -> None:
        try:
            validar_hello(mensaje)
        except VecinoError:
            self.descartados += 1
            return
        if mensaje["id"] == self.mi_id:
            return
        canal_origen = origen[0]
        if mensaje["canal"] != canal_origen:
            return
        self.vecinos.registrar(mensaje)
        self.rutas.aprender_vecino_directo(mensaje["id"])

    def _on_dir(self, mensaje: dict) -> None:
        if "entradas" in mensaje:
            lista = mensaje["entradas"]
        else:
            lista = [{"entrada": mensaje.get("entrada"), "firma": mensaje.get("firma")}]
        if not isinstance(lista, list):
            self.descartados += 1
            return
        for item in lista[:500]:
            if not isinstance(item, dict):
                continue
            entrada, firma_hex = item.get("entrada"), item.get("firma")
            if isinstance(entrada, dict) and entrada.get("id") == self.mi_id:
                continue
            try:
                self.directorio.agregar(entrada, firma_hex)
            except DirectorioError:
                self.descartados += 1

    def _on_ruta(self, mensaje: dict) -> None:
        vecino_id = mensaje.get("id")
        tabla = mensaje.get("tabla")
        if not es_hex64(vecino_id) or not isinstance(tabla, dict):
            self.descartados += 1
            return
        if vecino_id == self.mi_id or self.vecinos.obtener(vecino_id) is None:
            return
        self.rutas.actualizar_desde(vecino_id, tabla)

    def _on_celda(self, mensaje: dict) -> None:
        hacia = mensaje.get("hacia", self.mi_id)
        frags_b64 = mensaje.get("frags")
        if not es_hex64(hacia) or not isinstance(frags_b64, list) or len(frags_b64) > 64:
            self.descartados += 1
            return
        if hacia != self.mi_id:

            self._entregar(hacia, mensaje)
            return
        frags = [base64.b64decode(f, validate=True) for f in frags_b64]
        try:
            onion_cell = desempaquetar_celda(reensamblar(frags))
        except CeldaError:
            return
        self._procesar_onion(onion_cell)

    def _procesar_onion(self, onion_cell: bytes) -> None:
        try:
            canal, dir_sig, interno = abrir_como_relay(onion_cell, self.cifrado)
        except OnionError:
            pass
        else:
            self._reenviar_capa(canal, dir_sig, interno)
            return
        try:
            texto = abrir_como_destino(onion_cell, self.cifrado)
        except OnionError:
            return
        with self._lock:
            self.recibidos.append(texto)
            self._horas_recibidos.append(time.time())
            while len(self.recibidos) > MAX_RECIBIDOS:
                self.recibidos.pop(0)
                self._horas_recibidos.popleft()
        if self.al_recibir_mensaje:
            try:
                self.al_recibir_mensaje(texto)
            except Exception:
                pass

    def _reenviar_capa(self, canal: int, dir_sig: bytes, interno: bytes) -> None:
        try:
            canal_txt, direccion = direccion_a_texto(canal, dir_sig)
        except OnionError:
            return
        with self._lock:
            entrada = self.directorio.buscar_por_direccion(canal_txt, direccion)
        if entrada is None:
            return
        self._mandar_celda(entrada["id"], interno)



    def _mandar_celda(self, hacia: str, contenido: bytes) -> None:
        frags = fragmentar(empaquetar_celda(contenido))
        mensaje = {"t": "celda", "v": VERSION, "hacia": hacia,
                   "frags": [base64.b64encode(f).decode("ascii") for f in frags]}
        if hacia == self.mi_id:
            self._on_celda(mensaje)
        else:
            self._entregar(hacia, mensaje)

    def _entregar(self, hacia: str, mensaje: dict) -> bool:

        with self._lock:
            siguiente = hacia
            vecino = self.vecinos.obtener(hacia)
            if vecino is None:
                ruta = self.rutas.ruta_hacia(hacia)
                if ruta is not None:
                    siguiente = ruta["siguiente"]
                    vecino = self.vecinos.obtener(siguiente)
            if vecino is not None:
                canal, direccion = vecino["canal"], vecino["dir"]
            else:

                e = self.directorio.get(hacia)
                if e is None or e[0]["canal"] != "udp":
                    return False
                canal, direccion = "udp", e[0]["direccion"]
        if canal == "udp":
            ip, puerto = direccion.rsplit(":", 1)
            self._mandar_udp(mensaje, (ip, int(puerto)))
            return True
        if canal == "faro" and self.enlace is not None:
            return self.enlace.enviar(self._codificar(mensaje), bytes.fromhex(direccion))
        return False



    def candidatos_relay(self, destino_id: str) -> list:
        return [e for e in self.directorio.entradas()
                if e["id"] not in (self.mi_id, destino_id)]

    def mandar_a(self, destino_id: str, mensaje: bytes,
                 permitir_directo: bool = None) -> list:

        if permitir_directo is None:
            permitir_directo = self.permitir_directo
        with self._lock:
            entrada_destino = self.directorio.get(destino_id)
            if entrada_destino is None:
                raise SaltosError(f"no conozco al destino {destino_id[:8]}")
            lista = self.directorio.entradas()
            if len(self.candidatos_relay(destino_id)) >= MINIMO_NODOS:
                saltos_entradas = elegir_saltos(lista, self.mi_id, destino_id, cantidad=3)
            elif permitir_directo:
                saltos_entradas = []
            else:
                raise SaltosError(
                    f"solo hay {len(self.candidatos_relay(destino_id))} relays posibles; "
                    f"se necesitan {MINIMO_NODOS} para un circuito anonimo de 3 saltos")
            cadena = saltos_entradas + [entrada_destino[0]]
            saltos = []
            for i, entrada in enumerate(saltos_entradas):
                pub = PublicKey(bytes.fromhex(entrada["cifrado"]))
                sig = cadena[i + 1]
                canal_sig, dir_sig = direccion_de_entrada(sig["canal"], sig["direccion"])
                saltos.append((pub, canal_sig, dir_sig))
            destino_pub = PublicKey(bytes.fromhex(entrada_destino[0]["cifrado"]))
        onion_cell = construir_cebolla(destino_pub, saltos, mensaje)
        self._mandar_celda(cadena[0]["id"], onion_cell)
        return [e["id"] for e in saltos_entradas]

    def gateways(self) -> list:
        with self._lock:
            return [e["id"] for e in self.directorio.gateways() if e["id"] != self.mi_id]

    def panico(self, indicadores=None) -> list:

        borrados = borrar_archivos(self.carpeta) if self.carpeta else []
        with self._lock:
            self.directorio.limpiar()
            self.vecinos.limpiar()
            self.recibidos.clear()
            self._horas_recibidos.clear()
            if self.carpeta:
                firma, cifrado = identidad.cargar_o_crear(self.carpeta)
            else:
                firma, cifrado = SigningKey.generate(), PrivateKey.generate()
            self._usar_identidad(firma, cifrado)
        self.rotar_direccion_faro()
        if self.al_panico:
            try:
                self.al_panico()
            except Exception:
                pass
        if indicadores is not None:
            indicadores.parpadear_panico()
        return borrados


def crear_nodo_desde_args(a) -> Nodo:

    semillas = []
    for s in a.semilla:
        ip, puerto = s.rsplit(":", 1)
        semillas.append((ip, int(puerto)))
    carpeta = Path(a.carpeta).expanduser()
    firma, cifrado = identidad.cargar_o_crear(carpeta)
    enlace = None
    if getattr(a, "uart", None):
        from faro import direccion as dirmod
        from faro.dispositivo_luz_adaptador import DispositivoLuzAdaptador
        from faro.gpio import Indicadores
        from faro.medio import MedioUART
        from mesh.enlace_faro import EnlaceFaro
        mac = dirmod.rotar(carpeta / "direccion.bin")
        adaptador = DispositivoLuzAdaptador(MedioUART(a.uart, a.baudios), mac,
                                            indicadores=Indicadores())
        enlace = EnlaceFaro(adaptador)
    return Nodo(a.puerto, firma, cifrado, semillas=semillas,
                ip_publica=a.ip_publica, rol=getattr(a, "rol", None),
                enlace_faro=enlace, permitir_directo=getattr(a, "permitir_directo", False),
                carpeta=carpeta)


def agregar_argumentos_nodo(p: argparse.ArgumentParser) -> None:
    p.add_argument("--puerto", type=int, required=True, help="puerto UDP local")
    p.add_argument("--semilla", action="append", default=[],
                   help="IP:PUERTO de un nodo semilla (puede repetirse)")
    p.add_argument("--ip-publica", default="127.0.0.1",
                   help="IP con la que los demas nodos llegan a este")
    p.add_argument("--carpeta", default="~/.faronet",
                   help="carpeta de llaves y direccion fisica")
    p.add_argument("--uart", default=None,
                   help="puerto serie del Faro (por ejemplo /dev/ttyAMA0); activa el enlace por luz")
    p.add_argument("--baudios", type=int, default=9600)
    p.add_argument("--permitir-directo", action="store_true",
                   help="SOLO PRUEBAS: permite mandar sin relays si la red es chica")


def main():
    p = argparse.ArgumentParser(description="Nodo de FaroNet")
    agregar_argumentos_nodo(p)
    a = p.parse_args()
    nodo = crear_nodo_desde_args(a)
    boton = None
    if a.uart:
        from faro.gpio import BotonPanico, Indicadores
        indicadores = Indicadores()
        boton = BotonPanico(lambda: print("PANICO: borrados", nodo.panico(indicadores)))
    print(f"Mi id    : {nodo.mi_id}")
    print(f"Escucho  : 0.0.0.0:{nodo.puerto}")
    nodo.arrancar()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo...")
        nodo.detener()
    del boton


if __name__ == "__main__":
    main()
