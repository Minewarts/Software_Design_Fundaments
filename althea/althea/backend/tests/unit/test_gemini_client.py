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
