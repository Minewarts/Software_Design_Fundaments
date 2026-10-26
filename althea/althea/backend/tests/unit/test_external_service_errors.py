import asyncio
import json

import httpx
from starlette.requests import Request

from app.main import _external_service_error


def invoke_error_handler(url: str, status: int):
    request = httpx.Request("POST", url)
    response = httpx.Response(status, request=request)
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

    assert response.status_code == 502
    assert "Supabase" in json.loads(response.body)["detail"]
