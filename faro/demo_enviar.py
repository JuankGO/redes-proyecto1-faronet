import argparse
from faro import direccion
from faro.medio import MedioSimUDP
from faro.dispositivo_luz_adaptador import DispositivoLuzAdaptador

p = argparse.ArgumentParser()
p.add_argument('--puerto', type=int, default=5000)
p.add_argument('--vecino', required=True, help='IP:PUERTO del otro Faro')
p.add_argument('--destino', required=True, help='direccion fisica en hex, 8 letras')
p.add_argument('--mensaje', default='hola faro')
a = p.parse_args()
ip, puerto = a.vecino.split(':')
faro = DispositivoLuzAdaptador(
    MedioSimUDP(a.puerto, [(ip, int(puerto))]), direccion.cargar_o_crear())
ok = faro.enviar_confiable(bytes.fromhex(a.destino), a.mensaje.encode())
print('Entregado y confirmado' if ok else 'Sin confirmacion')