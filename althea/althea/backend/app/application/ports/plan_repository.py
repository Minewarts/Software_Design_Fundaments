from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.entities.enums import TipoRecurso
from app.domain.entities.perfil_viaje import PerfilViaje
from app.domain.entities.plan_turistico import PlanTuristico
from app.domain.entities.recursos import Actividad, Alojamiento, Destino, Transporte

Recurso = Destino | Alojamiento | Actividad | Transporte



class PlanRepository(ABC):
    @abstractmethod
    def guardar(self, plan: PlanTuristico) -> PlanTuristico:
        """Persiste el plan y sus ítems en una sola transacción."""

    @abstractmethod
    def obtener_por_id(self, id_plan: UUID) -> PlanTuristico | None: ...

    @abstractmethod
    def ficha(self, id_plan: UUID) -> dict | None:
        """Plan con ítems y nombres de recurso resueltos (vistas, PDF, traducción)."""
    @abstractmethod
    def listar(self, filtros: dict) -> list[dict]: ...
    @abstractmethod
    def duplicar(self, id_plan: UUID) -> UUID: ...
    @abstractmethod
    def agregar_item(self, id_plan: UUID, numero_dia: int, tipo, id_recurso: UUID) -> None: ...
    @abstractmethod
    def quitar_item(self, id_plan: UUID, id_item: UUID) -> None: ...
    @abstractmethod
    def mover_item(self, id_plan: UUID, id_item: UUID, numero_dia: int) -> None: ...
    @abstractmethod
    def actualizar_completo(
        self, id_plan: UUID, titulo: str, cantidad_viajeros: int,
        id_destinos: list[UUID], items: list[dict],
    ) -> None: ...
    @abstractmethod
    def cambiar_estado(self, id_plan: UUID, estado) -> None: ...
    @abstractmethod
    def recalcular_costo(self, id_plan: UUID) -> None: ...
    @abstractmethod
    def valoraciones(self, id_plan: UUID) -> list[dict]: ...
    @abstractmethod
    def calificar(self, id_plan: UUID, autor: str, puntuacion: int, comentario: str) -> None: ...
