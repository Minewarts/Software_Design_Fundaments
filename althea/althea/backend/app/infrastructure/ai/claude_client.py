"""Cliente HTTP mínimo de la API de Anthropic (Messages)."""
import json
import re

import httpx

from app.domain.exceptions.errores import DominioError


class ClaudeClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._key, self._model = api_key, model

    def json(self, system: str, user: str, max_tokens: int = 3000) -> dict:
        if not self._key:
            raise DominioError("Falta ANTHROPIC_API_KEY en backend/.env")
        r = httpx.post("https://api.anthropic.com/v1/messages", timeout=90,
                       headers={"x-api-key": self._key, "anthropic-version": "2023-06-01"},
                       json={"model": self._model, "max_tokens": max_tokens, "system": system,
                             "messages": [{"role": "user", "content": user}]})
        r.raise_for_status()
        texto = "".join(b.get("text", "") for b in r.json()["content"])
        texto = re.sub(r"^```(?:json)?|```$", "", texto.strip(), flags=re.M).strip()
        try:
            return json.loads(texto)
        except json.JSONDecodeError as e:
            raise DominioError(f"Respuesta de IA no es JSON válido: {e}") from e
