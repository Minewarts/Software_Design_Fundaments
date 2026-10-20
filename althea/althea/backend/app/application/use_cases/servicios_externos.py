"""HU-15 clima histórico y HU-18 traducción de la ficha."""
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


class TraducirTextos:
    def __init__(self, traductor: Traductor) -> None:
        self._t = traductor

    def ejecutar(self, textos: dict[str, str], idioma: str) -> dict[str, str]:
        return self._t.traducir(textos, idioma)
