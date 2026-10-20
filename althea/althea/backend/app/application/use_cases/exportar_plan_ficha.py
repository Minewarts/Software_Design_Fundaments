"""Caso de uso HU-13: exportar la ficha del plan a PDF."""
from uuid import UUID

from app.application.ports.exportador_plan import ExportadorPlan
from app.application.ports.plan_repository import PlanRepository
from app.domain.exceptions.errores import PlanNoEncontradoError


class ExportarPlanFicha:
    def __init__(self, planes: PlanRepository, exportador: ExportadorPlan) -> None:
        self._planes, self._exp = planes, exportador

    def ejecutar(self, id_plan: UUID) -> bytes:
        ficha = self._planes.ficha(id_plan)
        if ficha is None:
            raise PlanNoEncontradoError(str(id_plan))
        return self._exp.exportar(ficha)
