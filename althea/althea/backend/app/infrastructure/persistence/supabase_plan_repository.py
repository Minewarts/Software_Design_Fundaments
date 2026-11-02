"""Repositorio de planes, itinerarios y actividad mediante PostgREST."""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.application.ports.plan_repository import PlanRepository
from app.domain.entities.enums import EstadoPlan, TipoRecurso
from app.domain.entities.plan_turistico import ItemItinerario, PlanTuristico
from app.infrastructure.persistence.rest import SupabaseRest, supabase


class SupabasePlanRepository(PlanRepository):
    def __init__(self, client: SupabaseRest = supabase) -> None:
        self._db = client

    @staticmethod
    def _items_payload(plan: PlanTuristico) -> list[dict]:
        return [
            {
                "id": str(item.id),
                "numero_dia": item.numero_dia,
                "orden": item.orden,
                "tipo_recurso": TipoRecurso(item.tipo_recurso).value,
                "id_recurso": str(item.id_recurso_asociado),
            }
            for item in plan.items
        ]

    def guardar(self, plan: PlanTuristico) -> PlanTuristico:
        self._db.rpc(
            "crear_plan_con_items",
            {
                "p_plan": {
                    "id": str(plan.id),
                    "titulo": plan.titulo,
                    "estado": plan.estado.value,
                    "costo_estimado": str(plan.costo_estimado),
                    "cantidad_viajeros": plan.cantidad_viajeros,
                    "id_destino": str(plan.id_destino) if plan.id_destino else None,
                    "duracion_dias": plan.duracion_dias,
                    "id_destinos": [str(id_destino) for id_destino in plan.id_destinos],
                },
                "p_items": self._items_payload(plan),
            },
        )
        return plan

    def obtener_por_id(self, id_plan: UUID):
        rows = self._db.select(
            "plan_turistico",
            select="id,titulo,estado,costo_estimado,cantidad_viajeros,id_destino,duracion_dias",
            id=f"eq.{id_plan}",
            limit="1",
        )
        if not rows:
            return None

        row = rows[0]
        plan = PlanTuristico(
            titulo=row["titulo"],
            estado=EstadoPlan(row["estado"]),
            costo_estimado=Decimal(str(row["costo_estimado"])),
            cantidad_viajeros=int(row["cantidad_viajeros"]),
            id=UUID(row["id"]),
            id_destino=UUID(row["id_destino"]) if row.get("id_destino") else None,
            duracion_dias=int(row.get("duracion_dias") or 1),
            id_destinos=tuple(
                UUID(destination["id_destino"])
                for destination in self._db.select(
                    "plan_destino",
                    select="id_destino",
                    id_plan=f"eq.{row['id']}",
                    order="orden.asc",
                )
            ),
        )
        items = self._db.select(
            "plan_items_detalle",
            select="id,id_plan,numero_dia,orden,tipo_recurso,id_recurso",
            id_plan=f"eq.{id_plan}",
            order="numero_dia.asc,orden.asc",
        )
        for item in items:
            plan.items.append(
                ItemItinerario(
                    id_plan=plan.id,
                    numero_dia=int(item["numero_dia"]),
                    orden=int(item["orden"]),
                    id_recurso_asociado=UUID(item["id_recurso"]),
                    tipo_recurso=TipoRecurso(item["tipo_recurso"]),
                    id=UUID(item["id"]),
                )
            )
        return plan

    def ficha(self, id_plan: UUID):
        rows = self._db.select("plan_directorio", id=f"eq.{id_plan}", limit="1")
        if not rows:
            return None
        ficha = rows[0]
        ficha["items"] = self._db.select(
            "plan_items_detalle",
            id_plan=f"eq.{id_plan}",
            order="numero_dia.asc,orden.asc",
        )
        return ficha

    def listar(self, filtros: dict) -> list[dict]:
        params = {"select": "*", "order": "titulo.asc"}
        if filtros.get("estado"):
            params["estado"] = f"eq.{filtros['estado']}"
        if filtros.get("destino"):
            params["destino"] = f"ilike.*{filtros['destino']}*"
        precio_min = filtros.get("precio_min")
        precio_max = filtros.get("precio_max")
        if precio_min is not None and precio_max is not None:
            params["and"] = (
                f"(costo_estimado.gte.{precio_min},costo_estimado.lte.{precio_max})"
            )
        elif precio_min is not None:
            params["costo_estimado"] = f"gte.{precio_min}"
        elif precio_max is not None:
            params["costo_estimado"] = f"lte.{precio_max}"
        if filtros.get("dias_max") is not None:
            params["duracion"] = f"lte.{filtros['dias_max']}"
        return self._db.select("plan_directorio", **params)

    def duplicar(self, id_plan: UUID) -> UUID:
        result = self._db.rpc("duplicar_plan", {"p_id_plan": str(id_plan)})
        return UUID(str(result))

    def agregar_item(self, id_plan, numero_dia, tipo, id_recurso):
        self._db.rpc(
            "agregar_item_plan",
            {
                "p_id_plan": str(id_plan),
                "p_numero_dia": numero_dia,
                "p_tipo_recurso": TipoRecurso(tipo).value,
                "p_id_recurso": str(id_recurso),
            },
        )

    def quitar_item(self, id_plan, id_item):
        self._db.delete(
            "item_itinerario",
            {"id": f"eq.{id_item}", "id_plan": f"eq.{id_plan}"},
        )

    def mover_item(self, id_plan, id_item, numero_dia):
        self._db.rpc(
            "mover_item_plan",
            {
                "p_id_plan": str(id_plan),
                "p_id_item": str(id_item),
                "p_numero_dia": numero_dia,
            },
        )

    def actualizar_completo(
        self, id_plan: UUID, titulo: str, cantidad_viajeros: int,
        id_destinos: list[UUID], items: list[dict],
    ) -> None:
        self._db.rpc(
            "actualizar_plan_completo",
            {
                "p_id_plan": str(id_plan),
                "p_titulo": titulo,
                "p_cantidad_viajeros": cantidad_viajeros,
                "p_id_destinos": [str(id_destino) for id_destino in id_destinos],
                "p_items": [
                    {
                        "id": str(item["id"]) if item.get("id") else None,
                        "numero_dia": item["numero_dia"],
                        "tipo_recurso": TipoRecurso(item["tipo_recurso"]).value,
                        "id_recurso": str(item["id_recurso"]),
                    }
                    for item in items
                ],
            },
        )

    def cambiar_estado(self, id_plan, estado):
        self._db.update(
            "plan_turistico",
            {"id": f"eq.{id_plan}"},
            {"estado": EstadoPlan(estado).value},
        )

    def recalcular_costo(self, id_plan):
        self._db.rpc("recalcular_costo_plan", {"p_id_plan": str(id_plan)})

    def valoraciones(self, id_plan):
        return self._db.select(
            "valoracion",
            select="id,autor,puntuacion,comentario,created_at",
            id_plan=f"eq.{id_plan}",
            order="created_at.desc",
        )

    def calificar(self, id_plan, autor, puntuacion, comentario):
        self._db.insert(
            "valoracion",
            {
                "id_plan": str(id_plan),
                "autor": autor,
                "puntuacion": puntuacion,
                "comentario": comentario,
            },
        )
