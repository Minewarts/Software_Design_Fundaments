"""Caso de uso: alimentar el catálogo (HU-01..04)."""
from __future__ import annotations

from dataclasses import fields
from decimal import Decimal
from uuid import UUID

from app.application.ports.recurso_repository import RecursoRepository
from app.domain.entities.recursos import Actividad, Alojamiento, Destino, Transporte
from app.domain.exceptions.errores import DominioError

FABRICAS = {"destinos": Destino, "alojamientos": Alojamiento, "actividades": Actividad, "transportes": Transporte}


class CrearRecursoTuristico:
    def __init__(self, recursos: RecursoRepository) -> None:
        self._r = recursos

    def ejecutar(self, tipo: str, datos: dict):
        cls = FABRICAS.get(tipo)
        if cls is None:
            raise DominioError(f"Tipo de recurso desconocido: {tipo}")
        d = {k: v for k, v in datos.items() if k in {f.name for f in fields(cls)} - {"id"}}
        try:
            for k in ("tarifa_noche", "costo_persona", "tarifa_estimada"):
                if k in d:
                    d[k] = Decimal(str(d[k]))
            if "categoria_estrellas" in d:
                d["categoria_estrellas"] = int(d["categoria_estrellas"])
            if "id_destino" in d:
                d["id_destino"] = UUID(str(d["id_destino"]))
            return self._r.guardar(cls(**d))
        except (TypeError, ValueError, ArithmeticError) as e:
            raise DominioError(f"Datos inválidos: {e}") from e
