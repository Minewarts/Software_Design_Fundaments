import httpx
import pytest

from app.domain.exceptions.errores import DominioError
from app.infrastructure.ai.gemini_client import GeminiClient


def test_sends_json_generation_request_to_gemini(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        request = httpx.Request("POST", url)
        return httpx.Response(
            200,
            request=request,
            json={
                "candidates": [{
                    "content": {"parts": [{"text": '{"titulo":"Viaje"}'}]}
                }]
            },
        )

    monkeypatch.setattr("app.infrastructure.ai.gemini_client.httpx.post", fake_post)

    result = GeminiClient("test-key", "gemini-2.5-flash").json("system", "user")

    assert result == {"titulo": "Viaje"}
    assert calls[0][0].endswith("/models/gemini-2.5-flash:generateContent")
    assert calls[0][1]["params"] == {"key": "test-key"}
    assert calls[0][1]["json"]["generationConfig"]["responseMimeType"] == "application/json"


def test_requires_gemini_api_key(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.infrastructure.ai.gemini_client.httpx.post",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    with pytest.raises(DominioError, match="GEMINI_API_KEY"):
        GeminiClient("", "gemini-2.5-flash").json("system", "user")

    assert calls == []


def test_rejects_non_object_json_response(monkeypatch):
    request = httpx.Request("POST", "https://generativelanguage.googleapis.com/")
    monkeypatch.setattr(
        "app.infrastructure.ai.gemini_client.httpx.post",
        lambda *args, **kwargs: httpx.Response(
            200,
            request=request,
            json={"candidates": [{"content": {"parts": [{"text": "[]"}]}}]},
        ),
    )

    with pytest.raises(DominioError, match="debe ser un objeto"):
        GeminiClient("test-key", "gemini-2.5-flash").json("system", "user")


def test_retries_temporary_gemini_503(monkeypatch):
    calls = []
    sleeps = []

    def fake_post(url, **kwargs):
        calls.append(url)
        request = httpx.Request("POST", url)
        if len(calls) == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(
            200,
            request=request,
            json={"candidates": [{"content": {"parts": [{"text": '{"titulo":"Ruta"}'}]}}]},
        )

    monkeypatch.setattr("app.infrastructure.ai.gemini_client.httpx.post", fake_post)
    monkeypatch.setattr("app.infrastructure.ai.gemini_client.time.sleep", sleeps.append)

    result = GeminiClient("test-key", "gemini-2.5-flash").json("system", "user")

    assert result == {"titulo": "Ruta"}
    assert len(calls) == 2
    assert sleeps == [1]


def test_stops_after_three_gemini_503_responses(monkeypatch):
    calls = []
    sleeps = []

    def fake_post(url, **kwargs):
        calls.append(url)
        return httpx.Response(503, request=httpx.Request("POST", url))

    monkeypatch.setattr("app.infrastructure.ai.gemini_client.httpx.post", fake_post)
    monkeypatch.setattr("app.infrastructure.ai.gemini_client.time.sleep", sleeps.append)

    with pytest.raises(httpx.HTTPStatusError):
        GeminiClient("test-key", "gemini-2.5-flash").json("system", "user")

    assert len(calls) == 3
    assert sleeps == [1, 2]


def test_retries_incomplete_json_with_a_larger_output_limit(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        request = httpx.Request("POST", url)
        text = '{"titulo":"Ruta incompleta' if len(calls) == 1 else '{"titulo":"Ruta","items":[]}'
        return httpx.Response(
            200,
            request=request,
            json={"candidates": [{"content": {"parts": [{"text": text}]}}]},
        )

    monkeypatch.setattr("app.infrastructure.ai.gemini_client.httpx.post", fake_post)

    result = GeminiClient("test-key", "gemini-2.5-flash").json("system", "user")

    assert result == {"titulo": "Ruta", "items": []}
    assert len(calls) == 2
    assert calls[0]["generationConfig"]["maxOutputTokens"] == 3000
    assert calls[1]["generationConfig"]["maxOutputTokens"] == 6000
    assert "Genera el itinerario de nuevo desde cero" in calls[1]["contents"][0]["parts"][0]["text"]


def test_reports_incomplete_json_after_all_generation_attempts(monkeypatch):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"candidates": [{"content": {"parts": [{"text": '{"titulo":"incompleto'}]}}]},
        )

    monkeypatch.setattr("app.infrastructure.ai.gemini_client.httpx.post", fake_post)

    with pytest.raises(DominioError, match="JSON incompleto o inválido después de 3 intentos"):
        GeminiClient("test-key", "gemini-2.5-flash").json("system", "user")

    assert len(calls) == 3
    assert [call["generationConfig"]["maxOutputTokens"] for call in calls] == [3000, 6000, 12000]
