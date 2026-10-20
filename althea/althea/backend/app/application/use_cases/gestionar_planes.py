"""Casos de uso sobre planes: HU-06 crear manual, HU-09 personalizar, HU-10/11 consultar,
HU-14 duplicar, HU-16 notificar, HU-17 calificar."""
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
        if plan.estado is EstadoPlan.ARCHIVADO:
            raise DominioError("El plan está archivado; restáuralo para editarlo")
        return plan

    # HU-06
    def crear_manual(self, titulo: str, viajeros: int, items: list[tuple[int, TipoRecurso, UUID]]) -> UUID:
        if not items:
            raise DominioError("Agrega al menos un recurso al plan")
        plan = PlanTuristico(titulo=titulo, cantidad_viajeros=viajeros)
        for dia, tipo, rid in items:
            plan.agregar_item(dia, rid, tipo)
        self._p.guardar(plan)
        self._p.recalcular_costo(plan.id)
        return plan.id

    # HU-10 / HU-11 / HU-12
    def listar(self, filtros: dict) -> list[dict]:
        return self._p.listar(filtros)

    def ficha(self, id_plan: UUID) -> dict:
        f = self._p.ficha(id_plan)
        if f is None:
            raise PlanNoEncontradoError(str(id_plan))
        return f

    # HU-14
    def duplicar(self, id_plan: UUID) -> UUID:
        self.ficha(id_plan)
        nuevo = self._p.duplicar(id_plan)
        self._p.notificar(nuevo, "Plan creado como copia de otro plan")
        return nuevo

    # HU-09 (+ HU-16)
    def agregar_item(self, id_plan: UUID, dia: int, tipo: TipoRecurso, id_recurso: UUID) -> None:
        self._editable(id_plan)
        self._p.agregar_item(id_plan, dia, tipo, id_recurso)
        self._tras_cambio(id_plan, f"Se agregó un recurso al día {dia}")

    def quitar_item(self, id_plan: UUID, id_item: UUID) -> None:
        self._editable(id_plan)
        self._p.quitar_item(id_plan, id_item)
        self._tras_cambio(id_plan, "Se quitó un recurso del itinerario")

    def mover_item(self, id_plan: UUID, id_item: UUID, dia: int) -> None:
        self._editable(id_plan)
        self._p.mover_item(id_plan, id_item, dia)
        self._tras_cambio(id_plan, f"Un recurso se movió al día {dia}")

    def cambiar_estado(self, id_plan: UUID, estado: EstadoPlan) -> None:
        plan = self._p.obtener_por_id(id_plan)
        if plan is None:
            raise PlanNoEncontradoError(str(id_plan))
        if estado is EstadoPlan.APROBADO:
            plan.aprobar()  # regla de dominio: no aprobar planes vacíos
        self._p.cambiar_estado(id_plan, estado)
        self._p.notificar(id_plan, f"El plan pasó a estado {estado.value}")

    def _tras_cambio(self, id_plan: UUID, mensaje: str) -> None:
        self._p.recalcular_costo(id_plan)
        self._p.notificar(id_plan, mensaje)

    # HU-17
    def valoraciones(self, id_plan: UUID) -> list[dict]:
        return self._p.valoraciones(id_plan)

    def calificar(self, id_plan: UUID, autor: str, puntuacion: int, comentario: str) -> None:
        self.ficha(id_plan)
        self._p.calificar(id_plan, autor, puntuacion, comentario)
        self._p.notificar(id_plan, f"Nueva valoración de {autor}: {puntuacion}★")

    # HU-16
    def notificaciones(self) -> list[dict]:
        return self._p.notificaciones()

    def marcar_leidas(self) -> None:
        self._p.marcar_leidas()
