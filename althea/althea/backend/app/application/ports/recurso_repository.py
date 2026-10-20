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


