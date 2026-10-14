"""Demo del directorio: crear, firmar, verificar, detectar manipulacion.

Uso:
    python -m mesh.demo_directorio
"""
from nacl.public import PrivateKey
from nacl.signing import SigningKey

from mesh.directorio import (
    DirectorioError,
    a_bytes,
    crear_entrada,
    firmar,
    validar,
    verificar,
)


def main():
    # 1. Un nodo cualquiera genera su identidad.
    firma = SigningKey.generate()
    cifrado = PrivateKey.generate()

    # 2. Arma su entrada y la firma.
    entrada = crear_entrada(firma, cifrado, "udp", "192.168.0.10:6001", ttl=600)
    firma_hex = firmar(entrada, firma)
    print("Entrada:")
    for k, v in sorted(entrada.items()):
        print(f"  {k:10s} = {v}")
    print(f"  firma      = {firma_hex[:32]}...")
    print()

    # 3. La firma se verifica.
    print("Verificacion directa:", verificar(entrada, firma_hex))
    validar(entrada, firma_hex)
    print("Validacion completa: OK")
    print()

    # 4. Si alguien cambia UN byte, la firma deja de valer.
    manipulada = dict(entrada)
    manipulada["direccion"] = "10.0.0.99:6001"
    print("Tras manipular la direccion:")
    print("  verificar ->", verificar(manipulada, firma_hex))
    try:
        validar(manipulada, firma_hex)
        print("  ERROR: no debio pasar la validacion")
    except DirectorioError as e:
        print(f"  validar -> DirectorioError: {e}")
    print()

    # 5. Una entrada con otra clave privada no pasa.
    otra_firma = SigningKey.generate()
    entrada_impostora = dict(entrada)
    entrada_impostora["id"] = otra_firma.verify_key.encode().hex()
    print("Entrada impostora (id cambiado):")
    print("  verificar ->", verificar(entrada_impostora, firma_hex))
    print()

    # 6. Los mismos datos dan los mismos bytes (necesario para firmar).
    print("Bytes canonicos (primeros 80):")
    print(" ", a_bytes(entrada)[:80])


if __name__ == "__main__":
    main()