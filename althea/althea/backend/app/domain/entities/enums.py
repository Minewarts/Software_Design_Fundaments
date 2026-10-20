from __future__ import annotations
import math
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

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
