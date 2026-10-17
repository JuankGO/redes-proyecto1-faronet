"""Demo del formato del mensaje: empaquetar, desempaquetar, detectar danos.

Uso:
    python -m app.demo_mensaje
"""
from app.mensaje import (
    MAX_TEXTO,
    PRIVADO,
    PUBLICO,
    TAMANO_MENSAJE,
    MensajeError,
    desempaquetar_mensaje,
    empaquetar_mensaje,
    hash_tema,
)


def main():
    tema = hash_tema("amigos")
    print(f"Tema 'amigos' -> {tema.hex()} (8 bytes)")
    print()

    # 1. Un mensaje privado corto.
    m = empaquetar_mensaje(PRIVADO, tema, b"hola, como estas")
    print(f"Mensaje privado : {len(m)} bytes (siempre {TAMANO_MENSAJE})")
    leido = desempaquetar_mensaje(m)
    print(f"  visibilidad = {leido['visibilidad']} (PRIVADO={PRIVADO})")
    print(f"  texto       = {leido['texto'].decode()!r}")
    print()

    # 2. Dos mensajes con el MISMO contenido: los bytes cambian por el padding.
    a = empaquetar_mensaje(PRIVADO, tema, b"hola")
    b = empaquetar_mensaje(PRIVADO, tema, b"hola")
    print(f"Dos mensajes con el mismo texto, bytes distintos: {a != b}")
    print()

    # 3. Un mensaje publico.
    pub = empaquetar_mensaje(PUBLICO, tema, b"aviso publico")
    leido = desempaquetar_mensaje(pub)
    print(f"Mensaje publico : visibilidad={leido['visibilidad']} (PUBLICO={PUBLICO})")
    print()

    # 4. Texto al maximo.
    grande = empaquetar_mensaje(PRIVADO, tema, b"x" * MAX_TEXTO)
    print(f"Texto maximo    : {MAX_TEXTO} bytes, total {len(grande)}B")
    print()

    # 5. Cosas que se rechazan.
    print("Cosas que se rechazan:")
    try:
        empaquetar_mensaje(PRIVADO, tema, b"x" * (MAX_TEXTO + 1))
    except MensajeError as e:
        print(f"  texto muy largo -> {e}")
    try:
        desempaquetar_mensaje(b"corto")
    except MensajeError as e:
        print(f"  mensaje corto   -> {e}")
    try:
        desempaquetar_mensaje(m, ahora=9999999999)   # muy en el futuro
    except MensajeError as e:
        print(f"  mensaje vencido -> {e}")


if __name__ == "__main__":
    main()