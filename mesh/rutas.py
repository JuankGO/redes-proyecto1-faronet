import time

INFINITO = 16
TIMEOUT_RUTA = 40.0


class RutaError(Exception):
    pass


class TablaRutas:


    def __init__(self, mi_id: str):
        if not mi_id:
            raise RutaError("el id del nodo no puede estar vacio")
        self.mi_id = mi_id
        self._rutas = {}

    def aprender_vecino_directo(self, vecino_id: str, ahora: float = None) -> None:

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

        return {
            destino: info["saltos"]
            for destino, info in self._rutas.items()
            if destino != self.mi_id and info["saltos"] < INFINITO
        }

    def actualizar_desde(self, vecino_id: str, anuncio: dict,
                         ahora: float = None) -> list:

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

                continue
            nuevos_saltos = saltos_vecino + 1
            if nuevos_saltos >= INFINITO:
                continue
            actual = self._rutas.get(destino)


            aceptar = (
                actual is None
                or nuevos_saltos < actual["saltos"]
                or actual["siguiente"] == vecino_id
            )
            if not aceptar:
                continue

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

        caidas = [d for d, info in self._rutas.items() if info["siguiente"] == vecino_id]
        for d in caidas:
            del self._rutas[d]
        return caidas

    def limpiar(self) -> None:
        self._rutas.clear()

    def ruta_hacia(self, destino_id: str):

        return self._rutas.get(destino_id)

    def listar(self) -> list:

        return sorted(
            [(d, info["siguiente"], info["saltos"])
             for d, info in self._rutas.items()],
            key=lambda x: x[0],
        )

    def olvidar_vencidas(self, timeout: float = TIMEOUT_RUTA,
                         ahora: float = None) -> list:

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
