from __future__ import annotations
import math
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from app.domain.entities.enums import TipoViajero
from app.domain.exceptions.errores import PerfilInvalidoError

@dataclass(frozen=True)
class PerfilViaje:
    """Parámetros de entrada configurados por el asesor turístico."""
    presupuesto_max: Decimal
    duracion_dias: int
    cantidad_viajeros: int
    tipo_viajero: TipoViajero
    intereses: tuple[str, ...] = ()
    id_destino: UUID | None = None  # Opcional: restringe el catálogo a un destino

    def __post_init__(self) -> None:
        if self.presupuesto_max <= 0:
            raise PerfilInvalidoError("El presupuesto debe ser mayor a 0")
        if self.duracion_dias < 1:
            raise PerfilInvalidoError("La duración mínima es 1 día")
        if self.cantidad_viajeros < 1:
            raise PerfilInvalidoError("Debe haber al menos 1 viajero")

    @property
    def noches(self) -> int:
        return max(self.duracion_dias - 1, 1)

    @property
    def habitaciones(self) -> int:
        """Regla: 2 viajeros por habitación."""
        return math.ceil(self.cantidad_viajeros / 2)
