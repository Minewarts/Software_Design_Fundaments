from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.entities.enums import EstadoPlan, TipoRecurso
from app.domain.exceptions.errores import DominioError, PresupuestoExcedidoError

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
    cantidad_viajeros: int = 1
    id: UUID = field(default_factory=uuid4)
    id_destino: UUID | None = None
    duracion_dias: int = 1
    id_destinos: tuple[UUID, ...] = ()

    def agregar_item(self, numero_dia: int, id_recurso: UUID,
                     tipo: TipoRecurso) -> ItemItinerario:
        orden = 1 + sum(1 for i in self.items if i.numero_dia == numero_dia)
        item = ItemItinerario(self.id, numero_dia, id_recurso, tipo, orden)
        self.items.append(item)
        self.duracion_dias = max(self.duracion_dias, numero_dia)
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
