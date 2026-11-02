from nacl.public import PrivateKey

from mesh.onion import (
    CANAL_UDP,
    abrir_como_destino,
    abrir_como_relay,
    construir_cebolla,
    direccion_udp,
)


def main():

    r1, r2, r3, d = (PrivateKey.generate() for _ in range(4))


    dir_r2 = direccion_udp("192.168.0.12", 6002)
    dir_r3 = direccion_udp("192.168.0.13", 6003)
    dir_d = direccion_udp("192.168.0.14", 6004)


    saltos = [
        (r1.public_key, CANAL_UDP, dir_r2),
        (r2.public_key, CANAL_UDP, dir_r3),
        (r3.public_key, CANAL_UDP, dir_d),
    ]


    mensaje = b"hola desde el emisor, esto es privado"
    celda = construir_cebolla(d.public_key, saltos, mensaje)
    print(f"Mensaje original : {len(mensaje)} bytes")
    print(f"Celda exterior   : {len(celda)} bytes")
    print(f"Overhead         : {len(celda) - len(mensaje)} bytes")
    print()


    canal, dir_sig, contenido = abrir_como_relay(celda, r1)
    print(f"R1 -> canal={canal}, siguiente={dir_sig.hex()}, ve {len(contenido)} bytes")

    canal, dir_sig, contenido = abrir_como_relay(contenido, r2)
    print(f"R2 -> canal={canal}, siguiente={dir_sig.hex()}, ve {len(contenido)} bytes")

    canal, dir_sig, contenido = abrir_como_relay(contenido, r3)
    print(f"R3 -> canal={canal}, siguiente={dir_sig.hex()}, ve {len(contenido)} bytes")
    print()


    texto = abrir_como_destino(contenido, d)
    print(f"D  -> mensaje = {texto.decode()!r}")
    assert texto == mensaje
    print()
    print("OK: la cebolla llego intacta y cada relay solo vio su siguiente salto.")


if __name__ == "__main__":
    main()
