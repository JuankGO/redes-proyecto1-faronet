"""Demo interactivo de la cebolla de 3 saltos.

Simula el camino: emisor -> R1 -> R2 -> R3 -> D.
Muestra cuantos bytes crece la celda con cada capa, que cada relay solo
ve el siguiente salto, y que D recibe el mensaje intacto.

Uso:
    python -m mesh.demo_onion
"""
from nacl.public import PrivateKey

from mesh.onion import (
    CANAL_UDP,
    abrir_como_destino,
    abrir_como_relay,
    construir_cebolla,
    direccion_udp,
)


def main():
    # 1. Llaves de los tres relays y del destino.
    r1, r2, r3, d = (PrivateKey.generate() for _ in range(4))

    # 2. Direcciones ficticias.
    dir_r2 = direccion_udp("192.168.0.12", 6002)
    dir_r3 = direccion_udp("192.168.0.13", 6003)
    dir_d = direccion_udp("192.168.0.14", 6004)

    # 3. Lista de saltos: pubkey del relay, canal y direccion del SIGUIENTE.
    saltos = [
        (r1.public_key, CANAL_UDP, dir_r2),   # R1 -> R2
        (r2.public_key, CANAL_UDP, dir_r3),   # R2 -> R3
        (r3.public_key, CANAL_UDP, dir_d),    # R3 -> D
    ]

    # 4. Armar la cebolla.
    mensaje = b"hola desde el emisor, esto es privado"
    celda = construir_cebolla(d.public_key, saltos, mensaje)
    print(f"Mensaje original : {len(mensaje)} bytes")
    print(f"Celda exterior   : {len(celda)} bytes")
    print(f"Overhead         : {len(celda) - len(mensaje)} bytes")
    print()

    # 5. R1 abre su capa.
    canal, dir_sig, contenido = abrir_como_relay(celda, r1)
    print(f"R1 -> canal={canal}, siguiente={dir_sig.hex()}, ve {len(contenido)} bytes")
    # 6. R2 abre su capa.
    canal, dir_sig, contenido = abrir_como_relay(contenido, r2)
    print(f"R2 -> canal={canal}, siguiente={dir_sig.hex()}, ve {len(contenido)} bytes")
    # 7. R3 abre su capa.
    canal, dir_sig, contenido = abrir_como_relay(contenido, r3)
    print(f"R3 -> canal={canal}, siguiente={dir_sig.hex()}, ve {len(contenido)} bytes")
    print()

    # 8. D abre el mensaje final.
    texto = abrir_como_destino(contenido, d)
    print(f"D  -> mensaje = {texto.decode()!r}")
    assert texto == mensaje
    print()
    print("OK: la cebolla llego intacta y cada relay solo vio su siguiente salto.")


if __name__ == "__main__":
    main()