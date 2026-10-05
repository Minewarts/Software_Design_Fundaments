"""
Capa APPLICATION — puertos (interfaces abstractas).
Se reparte así:
  app/application/ports/recurso_repository.py
  app/application/ports/plan_repository.py
  app/application/ports/servicio_ia.py
  app/application/ports/exportador_plan.py
"""
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


# ── recurso_repository.py ──
class RecursoRepository(ABC):
    @abstractmethod
    def guardar(self, recurso: Recurso) -> Recurso: ...

    @abstractmethod
    def buscar_destinos(self, id_destino: UUID | None = None) -> list[Destino]: ...

    @abstractmethod
    def buscar_alojamientos(self, id_destino: UUID | None,
                            tarifa_max_noche: Decimal) -> list[Alojamiento]: ...

    @abstractmethod
    def buscar_actividades(self, id_destino: UUID | None,
                           costo_max_persona: Decimal,
                           tipos: tuple[str, ...] = ()) -> list[Actividad]: ...

    @abstractmethod
    def buscar_transportes(self, tarifa_max: Decimal) -> list[Transporte]: ...


# ── plan_repository.py ──
class PlanRepository(ABC):
    @abstractmethod
    def guardar(self, plan: PlanTuristico) -> PlanTuristico:
        """Persiste el plan y sus ítems en una sola transacción."""

    @abstractmethod
    def obtener_por_id(self, id_plan: UUID) -> PlanTuristico | None: ...


# ── servicio_ia.py ──
@dataclass(frozen=True)
class CatalogoCandidato:
    """Recursos pre-filtrados que la IA puede usar (y solo estos)."""
    alojamientos: list[Alojamiento]
    actividades: list[Actividad]
    transportes: list[Transporte]


@dataclass(frozen=True)
class ItemPropuesto:
    numero_dia: int
    tipo_recurso: TipoRecurso
    id_recurso: UUID


@dataclass(frozen=True)
class PropuestaIA:
    titulo: str
    items: list[ItemPropuesto]


class ServicioIA(ABC):
    @abstractmethod
    def generar_itinerario(self, perfil: PerfilViaje,
                           catalogo: CatalogoCandidato) -> PropuestaIA:
        """Devuelve una propuesta referenciando IDs del catálogo recibido."""


# ── exportador_plan.py ──
class ExportadorPlan(ABC):
    @abstractmethod
    def exportar(self, plan: PlanTuristico,
                 recursos: dict[UUID, Recurso]) -> bytes:
        """Genera el documento (p. ej. PDF) y retorna sus bytes."""
