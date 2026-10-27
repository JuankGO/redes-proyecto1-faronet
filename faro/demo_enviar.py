"""Envia un mensaje por el Faro y espera la confirmacion.

El destino es la direccion que imprime demo_recibir en el otro Faro.
Con --destino ffffffff se manda a difusion, sin esperar ACK.

Faro real:   python3 -m faro.demo_enviar --uart /dev/ttyAMA0 --destino 0a0b0c0d
Simulacion:  python3 -m faro.demo_enviar --puerto 5001 --vecino 127.0.0.1:5000 --destino 0a0b0c0d
"""
import argparse

from faro import direccion
from faro.dispositivo_luz_adaptador import DispositivoLuzAdaptador
from faro.gpio import Indicadores
from faro.medio import MedioSimUDP, MedioUART

p = argparse.ArgumentParser(description="Envia un mensaje por el Faro")
p.add_argument("--uart", help="puerto serie del Faro real, por ejemplo /dev/ttyAMA0")
p.add_argument("--baudios", type=int, default=9600)
p.add_argument("--puerto", type=int, default=5000, help="puerto UDP local (simulacion)")
p.add_argument("--vecino", help="IP:PUERTO del otro Faro (simulacion)")
p.add_argument("--destino", required=True, help="direccion fisica en hex, 8 letras")
p.add_argument("--mensaje", default="hola faro")
a = p.parse_args()

try:
    destino = bytes.fromhex(a.destino)
    if len(destino) != 4:
        raise ValueError
except ValueError:
    p.error("--destino debe ser hex de 8 letras")

if a.uart:
    medio, indicadores = MedioUART(a.uart, a.baudios), Indicadores()
else:
    if not a.vecino or ":" not in a.vecino:
        p.error("sin --uart hay que dar --vecino IP:PUERTO")
    ip, puerto = a.vecino.rsplit(":", 1)
    medio, indicadores = MedioSimUDP(a.puerto, [(ip, int(puerto))]), None

faro = DispositivoLuzAdaptador(medio, direccion.cargar_o_crear(), indicadores=indicadores)
datos = a.mensaje.encode()[:114]
if destino == b"\xff\xff\xff\xff":
    faro.enviar(destino, datos)
    print("Enviado a difusion (sin confirmacion)")
else:
    ok = faro.enviar_confiable(destino, datos)
    print("Entregado y confirmado" if ok else "Sin confirmacion")
medio.cerrar()
