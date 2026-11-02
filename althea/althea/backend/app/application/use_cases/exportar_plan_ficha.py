"""Caso de uso para exportar la ficha del plan a PDF."""
from collections.abc import Callable
from uuid import UUID

from app.application.ports.exportador_plan import ExportadorPlan
from app.application.ports.plan_repository import PlanRepository
from app.domain.exceptions.errores import PlanNoEncontradoError


class ExportarPlanFicha:
    def __init__(
        self,
        planes: PlanRepository,
        exportador: ExportadorPlan,
        clima_actual: Callable[[UUID], dict],
    ) -> None:
        self._planes, self._exp, self._clima_actual = planes, exportador, clima_actual

    def ejecutar(self, id_plan: UUID) -> bytes:
        ficha = self._planes.ficha(id_plan)
        if ficha is None:
            raise PlanNoEncontradoError(str(id_plan))
        id_destino = ficha.get("id_destino")
        ficha["clima"] = self._clima_actual(UUID(str(id_destino))) if id_destino else None
        return self._exp.exportar(ficha)
