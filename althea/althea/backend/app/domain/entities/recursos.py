from __future__ import annotations
import math
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

@dataclass(frozen=True)
class Destino:
    nombre: str
    ubicacion: str
    clima_promedio: str
    id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class Alojamiento:
    id_destino: UUID
    nombre: str
    categoria_estrellas: int
    tarifa_noche: Decimal
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not 1 <= self.categoria_estrellas <= 5:
            raise ValueError("categoria_estrellas debe estar entre 1 y 5")
        if self.tarifa_noche < 0:
            raise ValueError("tarifa_noche no puede ser negativa")


@dataclass(frozen=True)
class Actividad:
    id_destino: UUID
    nombre: str
    tipo_actividad: str
    costo_persona: Decimal
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.costo_persona < 0:
            raise ValueError("costo_persona no puede ser negativo")


@dataclass(frozen=True)
class Transporte:
    tipo_vehiculo: str
    tarifa_estimada: Decimal
    id: UUID = field(default_factory=uuid4)
    ids_destinos: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        if self.tarifa_estimada < 0:
            raise ValueError("tarifa_estimada no puede ser negativa")
