"""Repositorios de recursos y administración del catálogo mediante PostgREST."""
from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.application.ports.recurso_repository import RecursoRepository
from app.domain.entities.recursos import Actividad, Alojamiento, Destino, Transporte
from app.domain.exceptions.errores import DominioError
from app.infrastructure.persistence.rest import SupabaseRest, supabase

_TABLA = {
    Destino: "destino",
    Alojamiento: "alojamiento",
    Actividad: "actividad",
    Transporte: "transporte",
}


def _uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(value)


def _destino(row: dict[str, Any]) -> Destino:
    return Destino(row["nombre"], row["ubicacion"], row["clima_promedio"], _uuid(row["id"]))


def _alojamiento(row: dict[str, Any]) -> Alojamiento:
    return Alojamiento(
        _uuid(row["id_destino"]),
        row["nombre"],
        int(row["categoria_estrellas"]),
        Decimal(str(row["tarifa_noche"])),
        _uuid(row["id"]),
    )


def _actividad(row: dict[str, Any]) -> Actividad:
    return Actividad(
        _uuid(row["id_destino"]),
        row["nombre"],
        row["tipo_actividad"],
        Decimal(str(row["costo_persona"])),
        _uuid(row["id"]),
    )


def _transporte(row: dict[str, Any]) -> Transporte:
    return Transporte(
        row["tipo_vehiculo"],
        Decimal(str(row["tarifa_estimada"])),
        _uuid(row["id"]),
        tuple(_uuid(id_destino) for id_destino in row.get("ids_destinos", [])),
    )


class SupabaseRecursoRepository(RecursoRepository):
    def __init__(self, client: SupabaseRest = supabase) -> None:
        self._db = client

    def guardar(self, recurso):
        datos = asdict(recurso)
        if isinstance(recurso, Transporte):
            datos.pop("ids_destinos", None)
        self._db.insert(_TABLA[type(recurso)], datos)
        return recurso

    def buscar_destinos(self, id_destino: UUID | None = None):
        filters = {"select": "id,nombre,ubicacion,clima_promedio"}
        if id_destino is not None:
            filters["id"] = f"eq.{id_destino}"
        return [_destino(row) for row in self._db.select("destino", **filters)]

    def buscar_alojamientos(self, id_destino, tarifa_max_noche: Decimal):
        filters = {
            "select": "id,id_destino,nombre,categoria_estrellas,tarifa_noche",
            "tarifa_noche": f"lte.{tarifa_max_noche}",
        }
        if id_destino is not None:
            filters["id_destino"] = f"eq.{id_destino}"
        return [_alojamiento(row) for row in self._db.select("alojamiento", **filters)]

    def buscar_actividades(self, id_destino, costo_max_persona: Decimal, tipos: tuple = ()):
        filters = {
            "select": "id,id_destino,nombre,tipo_actividad,costo_persona",
            "costo_persona": f"lte.{costo_max_persona}",
        }
        if id_destino is not None:
            filters["id_destino"] = f"eq.{id_destino}"
        rows = self._db.select("actividad", **filters)
        if tipos:
            terms = tuple(term.casefold() for term in tipos)
            matches = [
                row
                for row in rows
                if any(
                    term in f"{row['tipo_actividad']} {row['nombre']}".casefold()
                    for term in terms
                )
            ]
            if matches:
                rows = matches
        return [_actividad(row) for row in rows]

    def buscar_transportes(self, tarifa_max: Decimal):
        rows = self._db.select(
            "transporte",
            select="id,tipo_vehiculo,tarifa_estimada",
            tarifa_estimada=f"lte.{tarifa_max}",
        )
        links = self._db.select("destino_transporte", select="id_transporte,id_destino")
        destinos_por_transporte: dict[str, list[str]] = {}
        for link in links:
            destinos_por_transporte.setdefault(link["id_transporte"], []).append(link["id_destino"])
        for row in rows:
            row["ids_destinos"] = destinos_por_transporte.get(row["id"], [])
        return [_transporte(row) for row in rows]


TABLAS = {
    "destinos": ("destino", ["nombre", "ubicacion", "clima_promedio"]),
    "alojamientos": ("alojamiento", ["id_destino", "nombre", "categoria_estrellas", "tarifa_noche"]),
    "actividades": ("actividad", ["id_destino", "nombre", "tipo_actividad", "costo_persona"]),
    "transportes": ("transporte", ["tipo_vehiculo", "tarifa_estimada"]),
}


def _cfg(tipo: str):
    if tipo not in TABLAS:
        raise DominioError(f"Tipo de recurso desconocido: {tipo}")
    return TABLAS[tipo]


class CatalogoAdmin:
    """Listado, edición, borrado y relaciones del catálogo."""

    def __init__(self, client: SupabaseRest = supabase) -> None:
        self._db = client

    def listar(self, tipo: str):
        tabla, _ = _cfg(tipo)
        order = "tipo_vehiculo.asc" if tipo == "transportes" else "nombre.asc"
        rows = self._db.select(tabla, select="*", order=order)
        if tipo != "transportes":
            return rows

        links = self._db.select("destino_transporte", select="id_transporte,id_destino")
        destinos_por_transporte: dict[str, list[str]] = {}
        for link in links:
            destinos_por_transporte.setdefault(link["id_transporte"], []).append(link["id_destino"])
        for row in rows:
            row["ids_destinos"] = destinos_por_transporte.get(row["id"], [])
        return rows

    def actualizar(self, tipo: str, id_: UUID, datos: dict):
        tabla, cols = _cfg(tipo)
        values = {column: datos[column] for column in cols if column in datos}
        if values:
            self._db.update(tabla, {"id": f"eq.{id_}"}, values)
        if tipo == "transportes" and "ids_destinos" in datos:
            self.sincronizar_destinos(id_, datos["ids_destinos"])

    def eliminar(self, tipo: str, id_: UUID):
        tabla, _ = _cfg(tipo)
        self._db.delete(tabla, {"id": f"eq.{id_}"})

    def sincronizar_destinos(self, id_transporte, ids_destinos):
        self._db.rpc(
            "sincronizar_transporte_destinos",
            {
                "p_id_transporte": str(id_transporte),
                "p_ids_destinos": [str(id_destino) for id_destino in (ids_destinos or [])],
            },
        )

    def relaciones(self):
        destinos = self._db.select("destino", select="id,nombre", order="nombre.asc")
        alojamientos = self._db.select("alojamiento", select="id_destino,nombre")
        actividades = self._db.select("actividad", select="id_destino,nombre")
        transportes = self._db.select("transporte", select="id,tipo_vehiculo")
        links = self._db.select("destino_transporte", select="id_destino,id_transporte")

        transporte_por_id = {row["id"]: row["tipo_vehiculo"] for row in transportes}
        por_destino: dict[str, list[dict[str, str]]] = {}
        for link in links:
            nombre = transporte_por_id.get(link["id_transporte"])
            if nombre is not None:
                por_destino.setdefault(link["id_destino"], []).append({"nombre": nombre})

        return [
            {
                "id": destino["id"],
                "destino": destino["nombre"],
                "alojamientos": [
                    {"nombre": row["nombre"]}
                    for row in alojamientos
                    if row["id_destino"] == destino["id"]
                ],
                "actividades": [
                    {"nombre": row["nombre"]}
                    for row in actividades
                    if row["id_destino"] == destino["id"]
                ],
                "transportes": por_destino.get(destino["id"], []),
            }
            for destino in destinos
        ]
