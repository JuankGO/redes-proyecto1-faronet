"""Prueba cruda del emisor: manda texto por la UART (pin 8, GPIO14) sin tramas ni CRC.

Solo para probar el hardware. Uso:
    python3 tools/emisor.py "hola faro" --baud 1200
"""
import argparse

import serial
from gpiozero import LED

p = argparse.ArgumentParser()
p.add_argument("mensaje")
p.add_argument("--baud", type=int, default=1200)
args = p.parse_args()

# LED verde TX en GPIO23 (pin 16). Los datos salen por TXD (GPIO14).
tx_led = LED(23)

with serial.Serial("/dev/serial0", args.baud) as ser:
    tx_led.on()
    ser.write(args.mensaje.encode("utf-8"))
    ser.flush()
    tx_led.off()
