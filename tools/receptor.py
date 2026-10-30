"""Prueba cruda del receptor: muestra el texto que llega por la UART (pin 10, GPIO15).

Solo para probar el hardware. Uso:
    python3 tools/receptor.py --baud 1200
"""
import argparse

import serial

p = argparse.ArgumentParser()
p.add_argument("--baud", type=int, default=1200)
args = p.parse_args()

# Los datos entran por RXD (GPIO15), donde va conectado el fototransistor.
with serial.Serial("/dev/serial0", args.baud, timeout=1) as ser:
    print("Esperando mensajes... (Ctrl+C para salir)")
    buffer = b""
    try:
        while True:
            datos = ser.read(64)
            if datos:
                buffer += datos
            elif buffer:
                # 1 segundo de silencio = fin del mensaje
                print(buffer.decode("utf-8", errors="replace"))
                buffer = b""
    except KeyboardInterrupt:
        pass
