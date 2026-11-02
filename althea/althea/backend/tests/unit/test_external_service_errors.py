import asyncio
import json

import httpx
from starlette.requests import Request

from app.main import _external_service_error


def invoke_error_handler(url: str, status: int, payload=None):
    request = httpx.Request("POST", url)
    response = httpx.Response(status, request=request, json=payload) if payload else httpx.Response(status, request=request)
    error = httpx.HTTPStatusError("request failed", request=request, response=response)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/planes/generar",
        "raw_path": b"/api/planes/generar",
        "query_string": b"",
        "headers": [],
        "client": ("test", 123),
        "server": ("test", 80),
    }
    return asyncio.run(_external_service_error(Request(scope), error))


def test_gemini_auth_error_is_not_reported_as_supabase_failure():
    response = invoke_error_handler(
        "https://generativelanguage.googleapis.com/v1beta/models/model:generateContent",
        401,
    )

    assert response.status_code == 502
    assert "GEMINI_API_KEY" in json.loads(response.body)["detail"]


def test_supabase_auth_error_keeps_supabase_context():
    response = invoke_error_handler("https://project.supabase.co/rest/v1/destino", 401)

    assert response.status_code == 503
    detail = json.loads(response.body)["detail"]
    assert "Supabase" in detail
    assert "SUPABASE_SECRET_KEY" in detail
    assert "SUPABASE_URL" in detail


def test_missing_full_plan_update_rpc_explains_required_migration():
    response = invoke_error_handler(
        "https://project.supabase.co/rest/v1/rpc/actualizar_plan_completo",
        404,
        {"code": "PGRST202"},
    )

    assert response.status_code == 503
    assert "007_edicion_completa_planes.sql" in json.loads(response.body)["detail"]


def test_missing_plan_destination_column_explains_required_migration():
    response = invoke_error_handler(
        "https://project.supabase.co/rest/v1/plan_turistico",
        400,
        {"code": "42703", "message": "column plan_turistico.id_destino does not exist"},
    )

    assert response.status_code == 503
    assert "007_edicion_completa_planes.sql" in json.loads(response.body)["detail"]
