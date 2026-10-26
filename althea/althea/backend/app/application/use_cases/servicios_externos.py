"""Casos de uso para consultar el clima y traducir fichas."""
from uuid import UUID

from app.application.ports.recurso_repository import RecursoRepository
from app.application.ports.servicio_clima import ServicioClima
from app.application.ports.traductor import Traductor
from app.domain.exceptions.errores import DominioError


class ConsultarClimaHistorico:
    def __init__(self, recursos: RecursoRepository, clima: ServicioClima) -> None:
        self._r, self._c = recursos, clima

    def ejecutar(self, id_destino: UUID, mes: int) -> dict:
        destinos = self._r.buscar_destinos(id_destino)
        if not destinos:
            raise DominioError("Destino no encontrado")
        return self._c.historico_mensual(destinos[0].nombre, mes)

    def actual(self, id_destino: UUID) -> dict:
        destinos = self._r.buscar_destinos(id_destino)
        if not destinos:
            raise DominioError("Destino no encontrado")
        return self._c.actual(f"{destinos[0].nombre}, {destinos[0].ubicacion}")

    def actual_por_ubicacion(self, ubicacion: str) -> dict:
        if not ubicacion.strip():
            raise DominioError("La ubicación es obligatoria para consultar el clima")
        return self._c.actual(ubicacion)


class TraducirTextos:
    def __init__(self, traductor: Traductor) -> None:
        self._t = traductor

    def ejecutar(self, textos: dict[str, str], idioma: str) -> dict[str, str]:
        return self._t.traducir(textos, idioma)
