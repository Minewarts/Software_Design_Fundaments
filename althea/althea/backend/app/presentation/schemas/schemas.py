from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.entities.enums import EstadoPlan, TipoRecurso, TipoViajero


class PerfilIn(BaseModel):
    id_destino: UUID | None = None
    duracion_dias: int = Field(ge=1)
    presupuesto_max: Decimal = Field(gt=0)
    cantidad_viajeros: int = Field(ge=1)
    tipo_viajero: TipoViajero
    intereses: list[str] = []


class ItemIn(BaseModel):
    numero_dia: int = Field(ge=1)
    tipo_recurso: TipoRecurso
    id_recurso: UUID


class PlanManualIn(BaseModel):
    titulo: str = Field(min_length=1)
    cantidad_viajeros: int = Field(default=1, ge=1)
    items: list[ItemIn]


class MoverIn(BaseModel):
    numero_dia: int = Field(ge=1)


class EstadoIn(BaseModel):
    estado: EstadoPlan


class ValoracionIn(BaseModel):
    autor: str = Field(min_length=1)
    puntuacion: int = Field(ge=1, le=5)
    comentario: str = ""


class TraducirIn(BaseModel):
    idioma: str
    textos: dict[str, str]
