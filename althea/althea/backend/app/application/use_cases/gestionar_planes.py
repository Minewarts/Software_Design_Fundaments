"""Casos de uso sobre planes: creación, consulta, personalización y valoraciones."""
from __future__ import annotations

from uuid import UUID

from app.application.ports.plan_repository import PlanRepository
from app.domain.entities.enums import EstadoPlan, TipoRecurso
from app.domain.entities.plan_turistico import PlanTuristico
from app.domain.exceptions.errores import DominioError, PlanNoEncontradoError


class GestionarPlanes:
    def __init__(self, planes: PlanRepository) -> None:
        self._p = planes

    def _editable(self, id_plan: UUID) -> PlanTuristico:
        plan = self._p.obtener_por_id(id_plan)
        if plan is None:
            raise PlanNoEncontradoError(str(id_plan))
        return plan

    def crear_manual(
        self, titulo: str, viajeros: int, items: list[tuple[int, TipoRecurso, UUID]],
        id_destino: UUID | None = None,
    ) -> UUID:
        if not items:
            raise DominioError("Agrega al menos un recurso al plan")
        plan = PlanTuristico(titulo=titulo, cantidad_viajeros=viajeros, id_destino=id_destino)
        for dia, tipo, rid in items:
            plan.agregar_item(dia, rid, tipo)
        self._p.guardar(plan)
        self._p.recalcular_costo(plan.id)
        return plan.id

    def listar(self, filtros: dict) -> list[dict]:
        return self._p.listar(filtros)

    def ficha(self, id_plan: UUID) -> dict:
        f = self._p.ficha(id_plan)
        if f is None:
            raise PlanNoEncontradoError(str(id_plan))
        return f

    def duplicar(self, id_plan: UUID) -> UUID:
        self.ficha(id_plan)
        return self._p.duplicar(id_plan)

    def agregar_item(self, id_plan: UUID, dia: int, tipo: TipoRecurso, id_recurso: UUID) -> None:
        self._editable(id_plan)
        self._p.agregar_item(id_plan, dia, tipo, id_recurso)
        self._p.recalcular_costo(id_plan)

    def quitar_item(self, id_plan: UUID, id_item: UUID) -> None:
        self._editable(id_plan)
        self._p.quitar_item(id_plan, id_item)
        self._p.recalcular_costo(id_plan)

    def mover_item(self, id_plan: UUID, id_item: UUID, dia: int) -> None:
        self._editable(id_plan)
        self._p.mover_item(id_plan, id_item, dia)
        self._p.recalcular_costo(id_plan)

    def actualizar_completo(
        self, id_plan: UUID, titulo: str, viajeros: int,
        id_destinos: list[UUID], items: list[dict],
    ) -> None:
        self._editable(id_plan)
        titulo = titulo.strip()
        if not titulo:
            raise DominioError("El título del plan es obligatorio")
        self._p.actualizar_completo(id_plan, titulo, viajeros, id_destinos, items)

    def cambiar_estado(self, id_plan: UUID, estado: EstadoPlan) -> None:
        plan = self._p.obtener_por_id(id_plan)
        if plan is None:
            raise PlanNoEncontradoError(str(id_plan))
        if estado is EstadoPlan.APROBADO:
            plan.aprobar()  # regla de dominio: no aprobar planes vacíos
        self._p.cambiar_estado(id_plan, estado)

    def valoraciones(self, id_plan: UUID) -> list[dict]:
        return self._p.valoraciones(id_plan)

    def calificar(self, id_plan: UUID, autor: str, puntuacion: int, comentario: str) -> None:
        self.ficha(id_plan)
        self._p.calificar(id_plan, autor, puntuacion, comentario)
