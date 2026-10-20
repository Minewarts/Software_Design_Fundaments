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


