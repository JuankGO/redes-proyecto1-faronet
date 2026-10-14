"""Demo de la tabla de vecinos: HELLO, registro, olvido por timeout.

Uso:
    python -m mesh.demo_vecinos
"""
import time

from mesh.vecinos import (
    TIMEOUT_VECINO,
    TablaVecinos,
    crear_hello,
    parsear_hello,
)


def main():
    # Dos nodos ficticios mandan HELLO.
    hello_a = crear_hello("aa" * 32, "udp", "192.168.0.10:6001")
    hello_b = crear_hello("bb" * 32, "faro", "aabbccdd")

    tabla = TablaVecinos()
    ahora = time.time()

    print("Llega HELLO de A:")
    print("  nuevo ->", tabla.registrar(parsear_hello(hello_a), ahora=ahora))

    print("Llega HELLO de B:")
    print("  nuevo ->", tabla.registrar(parsear_hello(hello_b), ahora=ahora))

    print("Vuelve a llegar HELLO de A (ya lo conociamos):")
    print("  nuevo ->", tabla.registrar(parsear_hello(hello_a), ahora=ahora + 1))

    print()
    print("Vecinos actuales:")
    for id_hex, canal, direccion, visto in tabla.listar():
        print(f"  {id_hex[:16]}... canal={canal} dir={direccion}")

    print()
    print(f"Pasan {TIMEOUT_VECINO + 5}s sin senal de nadie:")
    vencidos = tabla.olvidar_vencidos(ahora=ahora + TIMEOUT_VECINO + 5)
    print("  olvidados:", [v[:16] + "..." for v in vencidos])
    print("  vecinos restantes:", len(tabla))

    # Un HELLO mal formado se rechaza sin romper.
    print()
    print("Llega un HELLO corrupto:")
    try:
        parsear_hello(b"no soy json")
    except Exception as e:
        print(f"  rechazado -> {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()