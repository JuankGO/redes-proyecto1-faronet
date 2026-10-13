import argparse
from faro import direccion
from faro.medio import MedioSimUDP
from faro.dispositivo_luz_adaptador import DispositivoLuzAdaptador

p = argparse.ArgumentParser()
p.add_argument('--puerto', type=int, default=5000)
p.add_argument('--vecino', required=True, help='IP:PUERTO del otro Faro')
a = p.parse_args()
ip, puerto = a.vecino.split(':')
faro = DispositivoLuzAdaptador(
    MedioSimUDP(a.puerto, [(ip, int(puerto))]), direccion.cargar_o_crear())
print('Mi direccion fisica:', faro.direccion.hex())
while True:
    t = faro.recibir(5.0)
    if t:
        print('Recibido de', t.src.hex(), ':', t.payload.decode(errors='replace'))