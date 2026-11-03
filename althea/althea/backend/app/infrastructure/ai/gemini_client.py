"""Cliente HTTP para la API Gemini generateContent."""
import json
import re
import time

import httpx

from app.domain.exceptions.errores import DominioError


class GeminiClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._key, self._model = api_key.strip(), model.strip()

    def json(self, system: str, user: str, max_tokens: int = 3000) -> dict:
        if not self._key:
            raise DominioError("Falta GEMINI_API_KEY en backend/.env")

        user_prompt = user
        for generation_attempt in range(3):
            for service_attempt in range(3):
                response = httpx.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent",
                    timeout=90,
                    params={"key": self._key},
                    json={
                        "systemInstruction": {"parts": [{"text": system}]},
                        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                        "generationConfig": {
                            "responseMimeType": "application/json",
                            "maxOutputTokens": min(max_tokens * 2**generation_attempt, 12000),
                        },
                    },
                )
                if response.status_code != 503 or service_attempt == 2:
                    response.raise_for_status()
                    break
                time.sleep(service_attempt + 1)

            try:
                candidate = response.json()["candidates"][0]
                text = "".join(
                    part.get("text", "")
                    for part in candidate["content"]["parts"]
                )
            except (KeyError, IndexError, TypeError) as error:
                raise DominioError("Gemini no devolvió contenido utilizable.") from error

            text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
            try:
                result = json.loads(text)
            except json.JSONDecodeError as error:
                if generation_attempt < 2:
                    user_prompt = (
                        f"{user}\n\n"
                        "La respuesta anterior quedó incompleta o no era JSON válido. "
                        "Genera el itinerario de nuevo desde cero, con una respuesta breve, "
                        "completa y válida según el formato JSON solicitado."
                    )
                    continue
                raise DominioError(
                    "Gemini devolvió JSON incompleto o inválido después de 3 intentos. "
                    "Intenta de nuevo o reduce la duración o cantidad de destinos."
                ) from error

            if not isinstance(result, dict):
                raise DominioError("La respuesta JSON de Gemini debe ser un objeto.")
            return result
