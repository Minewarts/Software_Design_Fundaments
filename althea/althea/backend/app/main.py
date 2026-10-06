from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
import os

import httpx
from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TABLES = {
	"destinos": "destino",
	"alojamientos": "alojamiento",
	"actividades": "actividad",
	"transportes": "transporte",
}
RESOURCE_COLUMNS = {
	"ALOJAMIENTO": ("alojamiento", "id_alojamiento", "tarifa_noche"),
	"ACTIVIDAD": ("actividad", "id_actividad", "costo_persona"),
	"TRANSPORTE": ("transporte", "id_transporte", "tarifa_estimada"),
}


class SupabaseRest:
	def __init__(self, url: str, key: str):
		self.client = httpx.AsyncClient(
			base_url=f"{url.rstrip('/')}/rest/v1/",
			headers={"apikey": key, "Authorization": f"Bearer {key}"},
			timeout=20,
		)

	async def request(
		self,
		method: str,
		table: str,
		*,
		params: dict[str, str] | None = None,
		payload: Any = None,
		prefer: str | None = None,
	) -> Any:
		headers = {"Prefer": prefer} if prefer else None
		try:
			response = await self.client.request(
				method, table, params=params, json=payload, headers=headers
			)
			response.raise_for_status()
		except httpx.HTTPStatusError as exc:
			try:
				detail = exc.response.json().get("message", "Error de base de datos")
			except (ValueError, AttributeError):
				detail = "Error de base de datos"
			status = exc.response.status_code
			raise HTTPException(status_code=status if status in (400, 404, 409) else 502, detail=detail) from exc
		except httpx.RequestError as exc:
			raise HTTPException(status_code=502, detail="No se pudo conectar con Supabase") from exc
		if response.status_code == 204 or not response.content:
			return None
		return response.json()

	async def rows(self, table: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
		return await self.request("GET", table, params=params) or []

	async def insert(self, table: str, payload: Any) -> list[dict[str, Any]]:
		return await self.request("POST", table, payload=payload, prefer="return=representation") or []

	async def close(self) -> None:
		await self.client.aclose()


@asynccontextmanager
async def lifespan(app: FastAPI):
	url = os.getenv("SUPABASE_URL", "").strip()
	key = os.getenv("SUPABASE_SECRET_KEY", "").strip()
	app.state.supabase = SupabaseRest(url, key) if url and key else None
	yield
	if app.state.supabase:
		await app.state.supabase.close()


app = FastAPI(title="Althea API", lifespan=lifespan)
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
)


def database(request: Request) -> SupabaseRest:
	db = getattr(request.app.state, "supabase", None)
	if db is None:
		raise HTTPException(status_code=503, detail="Configura SUPABASE_URL y SUPABASE_SECRET_KEY en backend/.env")
	return db


def resource_table(kind: str) -> str:
	table = TABLES.get(kind)
	if table is None:
		raise HTTPException(status_code=404, detail="Tipo de recurso desconocido")
	return table


@app.get("/api/health")
async def health(request: Request) -> dict[str, bool]:
	return {"ok": True, "supabase_configured": getattr(request.app.state, "supabase", None) is not None}


@app.get("/api/recursos/{kind}")
async def list_resources(kind: str, request: Request) -> list[dict[str, Any]]:
	db = database(request)
	table = resource_table(kind)
	rows = await db.rows(table, {"select": "*", "order": "created_at.asc"})
	if kind == "transportes":
		relations = await db.rows("destino_transporte", {"select": "id_transporte,id_destino"})
		ids_by_transport: dict[str, list[str]] = {}
		for relation in relations:
			ids_by_transport.setdefault(relation["id_transporte"], []).append(relation["id_destino"])
		for row in rows:
			row["ids_destinos"] = ids_by_transport.get(row["id"], [])
	return rows


@app.post("/api/recursos/{kind}")
async def create_resource(kind: str, payload: dict[str, Any] = Body(...), request: Request = None) -> dict[str, Any]:
	db = database(request)
	table = resource_table(kind)
	data = dict(payload)
	destination_ids = data.pop("ids_destinos", []) if kind == "transportes" else []
	rows = await db.insert(table, data)
	if not rows:
		raise HTTPException(status_code=502, detail="Supabase no devolvió el recurso creado")
	row = rows[0]
	if kind == "transportes" and destination_ids:
		await db.insert("destino_transporte", [
			{"id_transporte": row["id"], "id_destino": destination_id}
			for destination_id in destination_ids
		])
		row["ids_destinos"] = destination_ids
	return row


@app.put("/api/recursos/{kind}/{resource_id}")
async def update_resource(
	kind: str, resource_id: str, payload: dict[str, Any] = Body(...), request: Request = None
) -> dict[str, Any]:
	db = database(request)
	table = resource_table(kind)
	data = dict(payload)
	destination_ids = data.pop("ids_destinos", None) if kind == "transportes" else None
	rows = await db.request(
		"PATCH", table, params={"id": f"eq.{resource_id}"}, payload=data, prefer="return=representation"
	)
	if not rows:
		raise HTTPException(status_code=404, detail="Recurso no encontrado")
	row = rows[0]
	if kind == "transportes" and destination_ids is not None:
		await db.request("DELETE", "destino_transporte", params={"id_transporte": f"eq.{resource_id}"})
		if destination_ids:
			await db.insert("destino_transporte", [
				{"id_transporte": resource_id, "id_destino": destination_id}
				for destination_id in destination_ids
			])
		row["ids_destinos"] = destination_ids
	return row


@app.delete("/api/recursos/{kind}/{resource_id}", status_code=204)
async def delete_resource(kind: str, resource_id: str, request: Request) -> Response:
	db = database(request)
	table = resource_table(kind)
	if kind == "transportes":
		await db.request("DELETE", "destino_transporte", params={"id_transporte": f"eq.{resource_id}"})
	await db.request("DELETE", table, params={"id": f"eq.{resource_id}"})
	return Response(status_code=204)


@app.get("/api/catalogo/relaciones")
async def catalog_relations(request: Request) -> list[dict[str, Any]]:
	db = database(request)
	destinos = await db.rows("destino", {"select": "*", "order": "nombre.asc"})
	alojamientos = await db.rows("alojamiento", {"select": "*"})
	actividades = await db.rows("actividad", {"select": "*"})
	transportes = await db.rows("transporte", {"select": "*"})
	relaciones = await db.rows("destino_transporte", {"select": "id_destino,id_transporte"})
	transport_by_id = {row["id"]: row for row in transportes}
	transport_by_destination: dict[str, list[dict[str, Any]]] = {}
	for relation in relaciones:
		transport = transport_by_id.get(relation["id_transporte"])
		if transport:
			transport_by_destination.setdefault(relation["id_destino"], []).append(transport)
	return [
		{
			"destino": destino["nombre"],
			"alojamientos": [row for row in alojamientos if row["id_destino"] == destino["id"]],
			"actividades": [row for row in actividades if row["id_destino"] == destino["id"]],
			"transportes": transport_by_destination.get(destino["id"], []),
		}
		for destino in destinos
	]


async def create_plan(db: SupabaseRest, payload: dict[str, Any]) -> dict[str, Any]:
	title = str(payload.get("titulo", "")).strip()
	items = payload.get("items", [])
	if not title or not isinstance(items, list) or not items:
		raise HTTPException(status_code=400, detail="El plan requiere título y al menos un recurso")

	rows_to_insert = []
	total = 0.0
	order_by_day: dict[int, int] = {}
	for item in items:
		kind = str(item.get("tipo_recurso", "")).upper()
		table_info = RESOURCE_COLUMNS.get(kind)
		if table_info is None:
			raise HTTPException(status_code=400, detail="Tipo de recurso inválido")
		table, foreign_key, price_key = table_info
		resource_id = item.get("id_recurso")
		found = await db.rows(table, {"select": f"id,{price_key}", "id": f"eq.{resource_id}"})
		if not found:
			raise HTTPException(status_code=400, detail="Uno de los recursos seleccionados ya no existe")
		day = int(item.get("numero_dia", 1))
		if day < 1:
			raise HTTPException(status_code=400, detail="El día debe ser mayor a cero")
		order_by_day[day] = order_by_day.get(day, 0) + 1
		rows_to_insert.append({
			"numero_dia": day,
			"orden": order_by_day[day],
			"tipo_recurso": kind,
			foreign_key: resource_id,
		})
		total += float(found[0].get(price_key) or 0)

	plans = await db.insert("plan_turistico", {"titulo": title, "costo_estimado": total})
	if not plans:
		raise HTTPException(status_code=502, detail="Supabase no devolvió el plan creado")
	plan = plans[0]
	for item in rows_to_insert:
		item["id_plan"] = plan["id"]
	try:
		await db.insert("item_itinerario", rows_to_insert)
	except HTTPException:
		await db.request("DELETE", "plan_turistico", params={"id": f"eq.{plan['id']}"})
		raise
	return plan


@app.get("/api/planes")
async def list_plans(request: Request) -> list[dict[str, Any]]:
	return await database(request).rows("plan_turistico", {"select": "*", "order": "created_at.desc"})


@app.post("/api/planes")
async def create_manual_plan(payload: dict[str, Any] = Body(...), request: Request = None) -> dict[str, Any]:
	return await create_plan(database(request), payload)


@app.post("/api/planes/generar")
async def generate_plan(payload: dict[str, Any] = Body(...), request: Request = None) -> dict[str, Any]:
	db = database(request)
	destination_id = payload.get("id_destino")
	activities_params = {"select": "*", "order": "created_at.asc"}
	accommodations_params = {"select": "*", "order": "created_at.asc"}
	if destination_id:
		activities_params["id_destino"] = f"eq.{destination_id}"
		accommodations_params["id_destino"] = f"eq.{destination_id}"
	activities = await db.rows("actividad", activities_params)
	accommodations = await db.rows("alojamiento", accommodations_params)
	if not activities and not accommodations:
		raise HTTPException(status_code=400, detail="No hay actividades ni alojamientos para ese destino")
	days = max(1, min(int(payload.get("duracion_dias", 1)), 30))
	items = []
	for day in range(1, days + 1):
		if accommodations:
			accommodation = accommodations[(day - 1) % len(accommodations)]
			items.append({"numero_dia": day, "tipo_recurso": "ALOJAMIENTO", "id_recurso": accommodation["id"]})
		if activities:
			activity = activities[(day - 1) % len(activities)]
			items.append({"numero_dia": day, "tipo_recurso": "ACTIVIDAD", "id_recurso": activity["id"]})
	destination = "viaje"
	if destination_id:
		found = await db.rows("destino", {"select": "nombre", "id": f"eq.{destination_id}"})
		if found:
			destination = found[0]["nombre"]
	return await create_plan(db, {"titulo": f"Plan en {destination}", "items": items})


@app.get("/api/planes/{plan_id}")
async def get_plan(plan_id: str, request: Request) -> dict[str, Any]:
	db = database(request)
	plans = await db.rows("plan_turistico", {"select": "*", "id": f"eq.{plan_id}"})
	if not plans:
		raise HTTPException(status_code=404, detail="Plan no encontrado")
	items = await db.rows("item_itinerario", {"select": "*", "id_plan": f"eq.{plan_id}", "order": "numero_dia.asc,orden.asc"})
	resource_tables = {column: table for _, (table, column, _) in RESOURCE_COLUMNS.items()}
	for item in items:
		foreign_key = next((key for key in resource_tables if item.get(key)), None)
		if foreign_key:
			table = resource_tables[foreign_key]
			resources = await db.rows(table, {"select": "*", "id": f"eq.{item[foreign_key]}"})
			if resources:
				resource = resources[0]
				item["nombre"] = resource.get("nombre") or resource.get("tipo_vehiculo")
				item["id_recurso"] = resource["id"]
	return {**plans[0], "items": items}


@app.get("/api/planes/{plan_id}/valoraciones")
async def list_ratings(plan_id: str, request: Request) -> list[dict[str, Any]]:
	return await database(request).rows(
		"valoracion", {"select": "*", "id_plan": f"eq.{plan_id}", "order": "created_at.desc"}
	)


@app.post("/api/planes/{plan_id}/valoraciones")
async def create_rating(plan_id: str, payload: dict[str, Any] = Body(...), request: Request = None) -> dict[str, Any]:
	author = str(payload.get("autor", "")).strip()
	score = int(payload.get("puntuacion", 0))
	if not author or score not in range(1, 6):
		raise HTTPException(status_code=400, detail="Se requiere autor y puntuación de 1 a 5")
	rows = await database(request).insert("valoracion", {
		"id_plan": plan_id,
		"autor": author,
		"puntuacion": score,
		"comentario": payload.get("comentario") or None,
	})
	if not rows:
		raise HTTPException(status_code=502, detail="Supabase no devolvió la valoración creada")
	return rows[0]
