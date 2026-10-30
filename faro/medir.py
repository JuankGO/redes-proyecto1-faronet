"""Medicion de tasa efectiva y BER del enlace Faro (RFC, seccion 2.12).

Se corre en los dos Faros a la vez: uno con 'recibir' y el otro con
'enviar' (BER) o 'tasa' (tasa efectiva con ACK).

Con un solo Faro, 'loopback' manda tramas y las lee de vuelta por el mismo
UART (el LED IR apuntando a su propio fototransistor):
    python3 -m faro.medir loopback --uart /dev/ttyAMA0 --tramas 20

Ejemplos en la Raspberry (UART real):
    python3 -m faro.medir recibir --uart /dev/ttyAMA0 --baudios 9600 --tramas 200
    python3 -m faro.medir enviar  --uart /dev/ttyAMA0 --baudios 9600 --tramas 200

Ejemplos sin hardware (simulacion UDP):
    python3 -m faro.medir recibir --udp 5001 --vecino 127.0.0.1:5002
    python3 -m faro.medir enviar  --udp 5002 --vecino 127.0.0.1:5001

BER: el emisor manda tramas DATA a difusion con un payload pseudoaleatorio
conocido (semilla fija + SEQ). El receptor reconstruye la trama esperada y
cuenta los bits distintos SIN mirar el CRC. Las tramas que no llegan
cuentan como todos sus bits erroneos.
"""
import argparse
import random
import sys
import time

from faro import direccion as dirmod
from faro import frame, linea
from faro.dispositivo_luz_adaptador import DispositivoLuzAdaptador
from faro.medio import MedioSimUDP, MedioUART

SEMILLA = 2026
LARGO_PAYLOAD = frame.MAX_PAYLOAD
DIR_EMISOR = b"\x0b\xe0\x00\x01"   # direcciones fijas solo para la prueba
DIR_RECEPTOR = b"\x0b\xe0\x00\x02"


def payload_esperado(seq: int) -> bytes:
    rng = random.Random(SEMILLA * 1000 + seq)
    return bytes(rng.getrandbits(8) for _ in range(LARGO_PAYLOAD))


def trama_esperada(seq: int) -> bytes:
    return frame.codificar(frame.Trama(frame.TIPO_DATA, frame.BROADCAST,
                                       DIR_EMISOR, seq, payload_esperado(seq)))


def bits_distintos(a: bytes, b: bytes) -> int:
    largo = max(len(a), len(b))
    a = a.ljust(largo, b"\x00")
    b = b.ljust(largo, b"\x00")
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))


def crear_medio(a):
    if a.uart:
        return MedioUART(a.uart, a.baudios)
    if a.udp is None or not a.vecino:
        sys.exit("usa --uart PUERTO o --udp PUERTO --vecino IP:PUERTO")
    ip, p = a.vecino.rsplit(":", 1)
    return MedioSimUDP(a.udp, [(ip, int(p))])


def cmd_enviar(a):
    medio = crear_medio(a)
    adaptador = DispositivoLuzAdaptador(medio, DIR_EMISOR)
    inicio = time.monotonic()
    for i in range(a.tramas):
        adaptador._transmitir_bytes(trama_esperada(i % 256))
        time.sleep(a.pausa)
    duracion = time.monotonic() - inicio
    print(f"Enviadas {a.tramas} tramas en {duracion:.2f} s")
    medio.cerrar()


def cmd_recibir(a):
    medio = crear_medio(a)
    largo = len(trama_esperada(0))
    total_bits = a.tramas * largo * 8
    errores, recibidas, vistas = 0, 0, set()
    limite = time.monotonic() + a.espera
    while recibidas < a.tramas and time.monotonic() < limite:
        medios = medio.recibir(0.5)
        if medios is None:
            continue
        try:
            crudo = linea.extraer_trama(medios)
        except linea.LineaError:
            continue
        seq = crudo[10] if len(crudo) > 10 else -1
        if seq < 0 or seq in vistas:
            continue
        vistas.add(seq)
        recibidas += 1
        errores += bits_distintos(crudo, trama_esperada(seq))
        limite = time.monotonic() + a.espera   # se reinicia con cada trama
    perdidas = a.tramas - recibidas
    errores += perdidas * largo * 8
    ber = errores / total_bits if total_bits else 0.0
    print(f"Distancia: {a.distancia}")
    print(f"Tramas recibidas: {recibidas}/{a.tramas} (perdidas {perdidas})")
    print(f"Bits erroneos: {errores}/{total_bits}")
    print(f"BER: {ber:.2e}")
    medio.cerrar()


def cmd_tasa(a):
    medio = crear_medio(a)
    adaptador = DispositivoLuzAdaptador(medio, DIR_EMISOR, espera_ack=a.espera_ack)
    entregados = 0
    inicio = time.monotonic()
    for i in range(a.tramas):
        if adaptador.enviar_confiable(DIR_RECEPTOR, payload_esperado(i % 256)):
            entregados += LARGO_PAYLOAD
    duracion = time.monotonic() - inicio
    print(f"Distancia: {a.distancia}")
    print(f"Payload confirmado: {entregados} bytes en {duracion:.2f} s")
    print(f"Tasa efectiva: {entregados / duracion:.1f} bytes/s "
          f"({entregados * 8 / duracion:.0f} bit/s)")
    print(f"Reintentos: {adaptador.estadisticas['reintentos']}")
    medio.cerrar()


def cmd_eco(a):
    """Lado receptor de 'tasa': confirma todo lo que llega."""
    medio = crear_medio(a)
    adaptador = DispositivoLuzAdaptador(medio, DIR_RECEPTOR)
    print("Confirmando tramas (Ctrl+C para salir)...")
    try:
        while True:
            adaptador.recibir(1.0)
    except KeyboardInterrupt:
        pass
    medio.cerrar()


def cmd_loopback(a):
    """Un solo Faro: manda cada trama y la lee de vuelta por su propio receptor."""
    medio = crear_medio(a)
    ser = getattr(medio, "ser", None)
    largo = len(trama_esperada(0))
    errores, recibidas = 0, 0
    inicio = time.monotonic()
    for i in range(a.tramas):
        seq = i % 256
        if ser is not None:
            ser.reset_input_buffer()          # descarta basura vieja
        medio.enviar(linea.armar_senal(trama_esperada(seq)))
        medios = medio.recibir(a.espera_ack)
        try:
            crudo = linea.extraer_trama(medios) if medios else None
        except linea.LineaError:
            crudo = None
        if crudo is None:
            errores += largo * 8
            print(f"Trama {seq}: no llego")
            continue
        malos = bits_distintos(crudo, trama_esperada(seq))
        errores += malos
        recibidas += 1
        try:
            frame.decodificar(crudo)
            estado = "OK" if malos == 0 else f"{malos} bits malos"
        except Exception:
            estado = f"CRC malo ({malos} bits malos)"
        print(f"Trama {seq}: {estado}")
        time.sleep(a.pausa)
    duracion = time.monotonic() - inicio
    total_bits = a.tramas * largo * 8
    print(f"Recibidas: {recibidas}/{a.tramas} en {duracion:.2f} s")
    print(f"Bits erroneos: {errores}/{total_bits}")
    print(f"BER: {errores / total_bits if total_bits else 0.0:.2e}")
    medio.cerrar()
    return recibidas, errores


def main(argv=None):
    p = argparse.ArgumentParser(prog="faro.medir", description=__doc__.split("\n")[0])
    p.add_argument("modo", choices=["enviar", "recibir", "tasa", "eco", "loopback"],
                   help="enviar/recibir: BER. tasa/eco: tasa efectiva con ACK. loopback: un solo Faro")
    p.add_argument("--uart", help="puerto serie, por ejemplo /dev/ttyAMA0")
    p.add_argument("--baudios", type=int, default=9600)
    p.add_argument("--udp", type=int, help="puerto UDP local (simulacion)")
    p.add_argument("--vecino", help="IP:PUERTO del otro Faro (simulacion)")
    p.add_argument("--tramas", type=int, default=200)
    p.add_argument("--pausa", type=float, default=0.05,
                   help="segundos entre tramas al medir BER")
    p.add_argument("--espera", type=float, default=10.0,
                   help="segundos sin tramas antes de terminar (recibir)")
    p.add_argument("--espera-ack", type=float, default=1.0)
    p.add_argument("--distancia", default="sin indicar", help="solo para el reporte")
    a = p.parse_args(argv)
    {"enviar": cmd_enviar, "recibir": cmd_recibir, "tasa": cmd_tasa, "eco": cmd_eco,
     "loopback": cmd_loopback}[a.modo](a)


if __name__ == "__main__":
    main()
