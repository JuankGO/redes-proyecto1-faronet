"""Demo del parsing de comandos: validos e invalidos.

Uso:
    python -m app.demo_comandos
"""
from app.comandos import ComandoError, parsear_comando


LINEAS_VALIDAS = [
    "/priv a1b2c3d4 hola, como estas?",
    "/tema amigos chicos, nos vemos a las 8",
    "/publico noticias nuevo articulo en el blog",
    "/ayuda",
    "/salir",
]

LINEAS_INVALIDAS = [
    "",
    "   ",
    "hola sin slash",
    "/",
    "/desconocido x y",
    "/priv a1b2 hola",                # destino muy corto
    "/priv zzzzzzzz hola",            # no es hex
    "/priv a1b2c3d4",                 # falta texto
    "/tema solo-uno",                 # falta texto
    "/salir con argumento",
]


def main():
    print("Lineas validas:")
    for linea in LINEAS_VALIDAS:
        cmd = parsear_comando(linea)
        print(f"  {linea!r}")
        print(f"    -> tipo={cmd.tipo} args={cmd.argumentos}")
    print()

    print("Lineas invalidas (deben lanzar ComandoError):")
    for linea in LINEAS_INVALIDAS:
        try:
            parsear_comando(linea)
            print(f"  {linea!r}  ERROR: no debio pasar")
        except ComandoError as e:
            print(f"  {linea!r}  -> {e}")


if __name__ == "__main__":
    main()