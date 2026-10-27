"""Prueba manual del buzon muerto contra el Worker (local o desplegado).

Hace lo mismo que haria un cliente real (RFC 5.5):
    id   = HEX(BLAKE2b-256(clave = secreto_compartido, mensaje = "faronet-buzon-v1"))
    blob = crypto_secretbox(texto rellenado) -> exactamente 1024 bytes

Uso:
    cd worker && npx wrangler dev          # en otra terminal
    python3 tools/prueba_buzon.py                       # usa http://localhost:8787
    python3 tools/prueba_buzon.py https://faronet-worker.TU-CUENTA.workers.dev
"""
import os
import struct
import sys
import urllib.error
import urllib.request

from nacl.encoding import HexEncoder
from nacl.hash import blake2b
from nacl.secret import SecretBox

TAMANO_BLOB = 1024
LARGO_PLANO = TAMANO_BLOB - SecretBox.NONCE_SIZE - SecretBox.MACBYTES   # 984


def id_buzon(secreto: bytes) -> str:
    return blake2b(b"faronet-buzon-v1", digest_size=32, key=secreto, encoder=HexEncoder).decode()


def cerrar(secreto: bytes, texto: bytes) -> bytes:
    """2 bytes de largo + texto + relleno aleatorio, cifrado: siempre 1024 bytes."""
    if len(texto) > LARGO_PLANO - 2:
        raise ValueError("texto demasiado largo para el buzon")
    plano = struct.pack(">H", len(texto)) + texto
    plano += os.urandom(LARGO_PLANO - len(plano))
    return bytes(SecretBox(secreto).encrypt(plano))


def abrir(secreto: bytes, blob: bytes) -> bytes:
    plano = SecretBox(secreto).decrypt(blob)
    (largo,) = struct.unpack(">H", plano[:2])
    return plano[2:2 + largo]


def pedir(metodo, url, datos=None):
    req = urllib.request.Request(url, data=datos, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main():
    base = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8787"
    secreto = os.urandom(32)            # lo comparten emisor y receptor por otro canal
    url = f"{base}/buzon/{id_buzon(secreto)}"
    blob = cerrar(secreto, "nos vemos a las 8".encode())

    print("=== PRUEBA DEL BUZON MUERTO ===\n")
    print(f"1. Guardando un blob cifrado de {len(blob)} bytes...")
    estado, cuerpo = pedir("PUT", url, blob)
    print(f"   {estado} {cuerpo.decode(errors='replace')}  (esperado 201)\n")

    print("2. Leyendo el buzon (primera vez)...")
    estado, cuerpo = pedir("GET", url)
    texto = abrir(secreto, cuerpo).decode() if estado == 200 else None
    print(f"   {estado}, texto descifrado: {texto!r}  (esperado 200)\n")

    print("3. Leyendo de nuevo (se borro al leerlo)...")
    estado, _ = pedir("GET", url)
    print(f"   {estado}  (esperado 404)\n")

    print("4. Blob de tamano incorrecto...")
    estado, _ = pedir("PUT", url, b"muy corto")
    print(f"   {estado}  (esperado 413)")


if __name__ == "__main__":
    main()
