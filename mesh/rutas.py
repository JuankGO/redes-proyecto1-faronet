"""Tabla de rutas por vector de distancias (estilo RIP).

Cada nodo mantiene una tabla: destino -> (siguiente_salto, saltos).
Cada pocos segundos cada nodo manda su tabla a sus vecinos.
Un vecino que anuncia "llego a X en N saltos" me ensena que yo llego
en N+1 pasando por el.

Infinito = 16 (como en RIP). Una ruta con costo >= 16 se considera
inutilizable. Las rutas que no se renuevan se olvidan.

Nota v1: no usamos split horizon ni poison reverse. Eso puede causar
"contar hasta infinito" si un enlace se cae; lo limitan INFINITO = 16 y el
vencimiento de TIMEOUT_RUTA (RFC, seccion 3.4).

Los anuncios llegan de la red: actualizar_desde() ignora entradas con
tipos incorrectos o costos fuera de rango en vez de fallar.
"""
import time

INFINITO = 16
TIMEOUT_RUTA = 40.0     # segundos sin refresco antes de olvidar una ruta


class RutaError(Exception):
    """Operacion invalida sobre la tabla de rutas."""


class TablaRutas:
    """Tabla de rutas de un nodo."""

    def __init__(self, mi_id: str):
        if not mi_id:
            raise RutaError("el id del nodo no puede estar vacio")
        self.mi_id = mi_id
        self._rutas = {}   # destino_id -> {"siguiente", "saltos", "actualizado"}

    def aprender_vecino_directo(self, vecino_id: str, ahora: float = None) -> None:
        """Registra un vecino directo: 1 salto, via si mismo."""
        if vecino_id == self.mi_id:
            raise RutaError("un nodo no puede ser vecino de si mismo")
        if ahora is None:
            ahora = time.time()
        self._rutas[vecino_id] = {
            "siguiente": vecino_id,
            "saltos": 1,
            "actualizado": ahora,
        }

    def anuncio(self) -> dict:
        """Lo que este nodo le cuenta a sus vecinos: {destino: saltos}.

        No incluye rutas con costo >= INFINITO (no sirven) ni su propio id.
        """
        return {
            destino: info["saltos"]
            for destino, info in self._rutas.items()
            if destino != self.mi_id and info["saltos"] < INFINITO
        }

    def actualizar_desde(self, vecino_id: str, anuncio: dict,
                         ahora: float = None) -> list:
        """Aplica el anuncio de un vecino. Devuelve la lista de cambios.

        Un cambio es una tupla (destino, saltos_nuevos, siguiente).
        """
        if ahora is None:
            ahora = time.time()
        cambios = []
        if not isinstance(anuncio, dict):
            return cambios
        for destino, saltos_vecino in anuncio.items():
            if not isinstance(destino, str) or not destino:
                continue
            if (not isinstance(saltos_vecino, int) or isinstance(saltos_vecino, bool)
                    or not (0 <= saltos_vecino <= INFINITO)):
                continue
            if destino == self.mi_id:
                continue
            if destino == vecino_id:
                # Ya es mi vecino directo, no necesito aprenderlo por aqui.
                continue
            nuevos_saltos = saltos_vecino + 1
            if nuevos_saltos >= INFINITO:
                continue
            actual = self._rutas.get(destino)
            # Acepto si: es nueva, es mejor, o viene del mismo siguiente
            # (refresco: la sigo usando aunque no mejore).
            aceptar = (
                actual is None
                or nuevos_saltos < actual["saltos"]
                or actual["siguiente"] == vecino_id
            )
            if not aceptar:
                continue
            # Solo cuenta como cambio si algo distinto a antes.
            if (actual is None
                    or actual["saltos"] != nuevos_saltos
                    or actual["siguiente"] != vecino_id):
                cambios.append((destino, nuevos_saltos, vecino_id))
            self._rutas[destino] = {
                "siguiente": vecino_id,
                "saltos": nuevos_saltos,
                "actualizado": ahora,
            }
        return cambios

    def olvidar_via(self, vecino_id: str) -> list:
        """Borra las rutas que pasan por un vecino que se perdio."""
        caidas = [d for d, info in self._rutas.items() if info["siguiente"] == vecino_id]
        for d in caidas:
            del self._rutas[d]
        return caidas

    def limpiar(self) -> None:
        self._rutas.clear()

    def ruta_hacia(self, destino_id: str):
        """Devuelve {'siguiente', 'saltos', 'actualizado'} o None."""
        return self._rutas.get(destino_id)

    def listar(self) -> list:
        """Devuelve [(destino, siguiente, saltos)] ordenado por destino."""
        return sorted(
            [(d, info["siguiente"], info["saltos"])
             for d, info in self._rutas.items()],
            key=lambda x: x[0],
        )

    def olvidar_vencidas(self, timeout: float = TIMEOUT_RUTA,
                         ahora: float = None) -> list:
        """Borra las rutas que llevan mucho sin refrescarse. Devuelve sus destinos."""
        if ahora is None:
            ahora = time.time()
        vencidas = [
            d for d, info in self._rutas.items()
            if (ahora - info["actualizado"]) >= timeout
        ]
        for d in vencidas:
            del self._rutas[d]
        return vencidas

    def __len__(self):
        return len(self._rutas)