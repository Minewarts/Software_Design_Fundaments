from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from app.domain.entities.enums import EstadoPlan
from app.domain.entities.plan_turistico import PlanTuristico
from app.infrastructure.persistence.rest import SupabaseConfigError, SupabaseRest
from app.infrastructure.persistence.supabase_plan_repository import SupabasePlanRepository


def test_postgrest_auth_and_json_serialization():
    captured = {}

    def respond(request):
        captured["request"] = request
        return httpx.Response(201, json=[{"id": "ok"}])

    client = httpx.Client(transport=httpx.MockTransport(respond))
    rest = SupabaseRest("https://project.supabase.co", "test-only-key", client)
    rest.insert(
        "destino",
        {"id": uuid4(), "costo": Decimal("12.50"), "estado": EstadoPlan.BORRADOR},
    )

    request = captured["request"]
    assert request.url == "https://project.supabase.co/rest/v1/destino?select=%2A"
    assert request.headers["apikey"] == "test-only-key"
    assert request.headers["Authorization"] == "Bearer test-only-key"
    assert request.headers["Prefer"] == "return=representation"
    body = request.read().decode()
    assert '"costo":"12.50"' in body
    assert '"estado":"BORRADOR"' in body


def test_postgrest_fails_clearly_without_secret():
    rest = SupabaseRest("https://project.supabase.co", "")

    with pytest.raises(SupabaseConfigError, match="SUPABASE_SECRET_KEY"):
        rest.select("destino")


def test_postgrest_does_not_hide_http_errors():
    def reject(_request):
        return httpx.Response(401, json={"message": "Unauthorized"})

    client = httpx.Client(transport=httpx.MockTransport(reject))
    rest = SupabaseRest("https://project.supabase.co", "test-only-key", client)

    with pytest.raises(httpx.HTTPStatusError):
        rest.select("destino")


def test_plan_repository_combines_price_limits_in_one_postgrest_filter():
    class RecordingClient:
        params = None

        def select(self, table, **params):
            self.params = (table, params)
            return []

    client = RecordingClient()
    repository = SupabasePlanRepository(client)

    assert repository.listar({"precio_min": 100, "precio_max": 500}) == []
    table, params = client.params
    assert table == "plan_directorio"
    assert params["and"] == "(costo_estimado.gte.100,costo_estimado.lte.500)"
    assert "costo_estimado" not in params


def test_plan_repository_sends_full_itinerary_update_to_rpc():
    class RecordingClient:
        call = None

        def rpc(self, function, arguments):
            self.call = (function, arguments)

    client = RecordingClient()
    repository = SupabasePlanRepository(client)
    plan_id, destination_id, second_destination_id, item_id, resource_id = (
        uuid4(), uuid4(), uuid4(), uuid4(), uuid4(),
    )

    repository.actualizar_completo(
        plan_id,
        "Plan nuevo",
        3,
        [destination_id, second_destination_id],
        [{
            "id": item_id,
            "numero_dia": 2,
            "tipo_recurso": "ACTIVIDAD",
            "id_recurso": resource_id,
        }],
    )

    function, arguments = client.call
    assert function == "actualizar_plan_completo"
    assert arguments == {
        "p_id_plan": str(plan_id),
        "p_titulo": "Plan nuevo",
        "p_cantidad_viajeros": 3,
        "p_id_destinos": [str(destination_id), str(second_destination_id)],
        "p_items": [{
            "id": str(item_id),
            "numero_dia": 2,
            "tipo_recurso": "ACTIVIDAD",
            "id_recurso": str(resource_id),
        }],
    }


def test_plan_repository_persists_duration_for_free_days():
    class RecordingClient:
        arguments = None

        def rpc(self, _function, arguments):
            self.arguments = arguments

    client = RecordingClient()
    repository = SupabasePlanRepository(client)
    plan = PlanTuristico("Plan", duracion_dias=6)

    repository.guardar(plan)

    assert client.arguments["p_plan"]["duracion_dias"] == 6


def test_plan_repository_reads_destinations_in_route_order():
    plan_id, first_destination, second_destination = uuid4(), uuid4(), uuid4()

    class RecordingClient:
        def select(self, table, **params):
            if table == "plan_turistico":
                return [{
                    "id": str(plan_id),
                    "titulo": "Ruta",
                    "estado": "BORRADOR",
                    "costo_estimado": "0",
                    "cantidad_viajeros": 2,
                    "id_destino": str(first_destination),
                    "duracion_dias": 2,
                }]
            if table == "plan_destino":
                assert params["order"] == "orden.asc"
                return [
                    {"id_destino": str(first_destination)},
                    {"id_destino": str(second_destination)},
                ]
            if table == "plan_items_detalle":
                return []
            raise AssertionError(f"Unexpected table: {table}")

    plan = SupabasePlanRepository(RecordingClient()).obtener_por_id(plan_id)

    assert plan.id_destinos == (first_destination, second_destination)
