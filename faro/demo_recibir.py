"""Muestra lo que llega por el Faro.

Faro real:   python3 -m faro.demo_recibir --uart /dev/ttyAMA0
Simulacion:  python3 -m faro.demo_recibir --puerto 5000 --vecino 127.0.0.1:5001
"""
import argparse

from faro import direccion
from faro.dispositivo_luz_adaptador import DispositivoLuzAdaptador
from faro.gpio import Indicadores
from faro.medio import MedioSimUDP, MedioUART

p = argparse.ArgumentParser(description="Recibe tramas del Faro")
p.add_argument("--uart", help="puerto serie del Faro real, por ejemplo /dev/ttyAMA0")
p.add_argument("--baudios", type=int, default=9600)
p.add_argument("--puerto", type=int, default=5000, help="puerto UDP local (simulacion)")
p.add_argument("--vecino", help="IP:PUERTO del otro Faro (simulacion)")
a = p.parse_args()

if a.uart:
    medio, indicadores = MedioUART(a.uart, a.baudios), Indicadores()
else:
    if not a.vecino or ":" not in a.vecino:
        p.error("sin --uart hay que dar --vecino IP:PUERTO")
    ip, puerto = a.vecino.rsplit(":", 1)
    medio, indicadores = MedioSimUDP(a.puerto, [(ip, int(puerto))]), None

faro = DispositivoLuzAdaptador(medio, direccion.cargar_o_crear(), indicadores=indicadores)
print("Mi direccion fisica:", faro.direccion.hex())
try:
    while True:
        t = faro.recibir(5.0)
        if t:
            print("Recibido de", t.src.hex(), ":", t.payload.decode(errors="replace"))
except KeyboardInterrupt:
    print("\nSaliendo.")
finally:
    medio.cerrar()
