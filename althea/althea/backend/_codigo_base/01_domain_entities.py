"""
Capa DOMAIN — entidades y reglas de negocio puras (sin dependencias de framework).
Se reparte así:
  app/domain/entities/enums.py          -> Enums
  app/domain/entities/recursos.py       -> Destino, Alojamiento, Actividad, Transporte
  app/domain/entities/perfil_viaje.py   -> PerfilViaje
  app/domain/entities/plan_turistico.py -> PlanTuristico, ItemItinerario
  app/domain/exceptions/errores.py      -> Excepciones
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


# ───────────────────────── enums.py ─────────────────────────
class TipoRecurso(str, Enum):
    ALOJAMIENTO = "ALOJAMIENTO"
    ACTIVIDAD = "ACTIVIDAD"
    TRANSPORTE = "TRANSPORTE"


class EstadoPlan(str, Enum):
    BORRADOR = "BORRADOR"
    APROBADO = "APROBADO"
    EXPORTADO = "EXPORTADO"
    ARCHIVADO = "ARCHIVADO"


class TipoViajero(str, Enum):
    SOLO = "SOLO"
    PAREJA = "PAREJA"
    FAMILIA = "FAMILIA"
    AMIGOS = "AMIGOS"
    CORPORATIVO = "CORPORATIVO"


# ───────────────────────── errores.py ─────────────────────────
class DominioError(Exception):
    """Base de errores de dominio."""


class PerfilInvalidoError(DominioError): ...
class RecursosInsuficientesError(DominioError): ...
class PresupuestoExcedidoError(DominioError): ...
class PropuestaIAInvalidaError(DominioError): ...
class PlanNoEncontradoError(DominioError): ...


# ───────────────────────── recursos.py ─────────────────────────
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

    def __post_init__(self) -> None:
        if self.tarifa_estimada < 0:
            raise ValueError("tarifa_estimada no puede ser negativa")


# ───────────────────────── perfil_viaje.py ─────────────────────────
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


# ───────────────────────── plan_turistico.py ─────────────────────────
@dataclass
class ItemItinerario:
    id_plan: UUID
    numero_dia: int
    id_recurso_asociado: UUID
    tipo_recurso: TipoRecurso
    orden: int = 1
    id: UUID = field(default_factory=uuid4)


@dataclass
class PlanTuristico:
    titulo: str
    estado: EstadoPlan = EstadoPlan.BORRADOR
    costo_estimado: Decimal = Decimal("0")
    items: list[ItemItinerario] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def agregar_item(self, numero_dia: int, id_recurso: UUID,
                     tipo: TipoRecurso) -> ItemItinerario:
        orden = 1 + sum(1 for i in self.items if i.numero_dia == numero_dia)
        item = ItemItinerario(self.id, numero_dia, id_recurso, tipo, orden)
        self.items.append(item)
        return item

    def validar_presupuesto(self, presupuesto_max: Decimal) -> None:
        if self.costo_estimado > presupuesto_max:
            raise PresupuestoExcedidoError(
                f"Costo {self.costo_estimado} supera el presupuesto {presupuesto_max}"
            )

    def aprobar(self) -> None:
        if not self.items:
            raise DominioError("No se puede aprobar un plan sin ítems")
        self.estado = EstadoPlan.APROBADO
