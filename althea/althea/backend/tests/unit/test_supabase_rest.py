from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from app.domain.entities.enums import EstadoPlan
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
