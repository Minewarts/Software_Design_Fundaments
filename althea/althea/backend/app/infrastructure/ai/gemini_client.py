"""Cliente HTTP para la API Gemini generateContent."""
import json
import re

import httpx

from app.domain.exceptions.errores import DominioError


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._key, self._model = api_key.strip(), model.strip()

    def json(self, system: str, user: str, max_tokens: int = 3000) -> dict:
        if not self._key:
            raise DominioError("Falta GEMINI_API_KEY en backend/.env")

        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent",
            timeout=90,
            params={"key": self._key},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "maxOutputTokens": max_tokens,
                },
            },
        )
        response.raise_for_status()
        try:
            text = "".join(
                part.get("text", "")
                for part in response.json()["candidates"][0]["content"]["parts"]
            )
        except (KeyError, IndexError, TypeError) as error:
            raise DominioError("Gemini no devolvió contenido utilizable.") from error

        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        try:
            result = json.loads(text)
        except json.JSONDecodeError as error:
            raise DominioError(f"Respuesta de IA no es JSON válido: {error}") from error
        if not isinstance(result, dict):
            raise DominioError("La respuesta JSON de Gemini debe ser un objeto.")
        return result
