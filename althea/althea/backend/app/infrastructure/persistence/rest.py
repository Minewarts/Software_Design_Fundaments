"""Cliente privado para la API REST de Supabase (PostgREST)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

import httpx

from app.infrastructure.config.settings import settings


class SupabaseConfigError(RuntimeError):
    """La configuración privada necesaria para acceder a Supabase falta o es inválida."""


def _json_value(value: Any) -> Any:
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


class SupabaseRest:
    def __init__(
        self,
        url: str | None = None,
        secret_key: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._url = (settings.supabase_url if url is None else url).rstrip("/")
        self._secret_key = settings.supabase_secret_key if secret_key is None else secret_key
        self._client = client or httpx.Client(timeout=20)

    def request(
        self,
        method: str,
        resource: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any = None,
        prefer: str | None = None,
    ) -> Any:
        if not self._url:
            raise SupabaseConfigError("Configura SUPABASE_URL en backend/.env.")
        if not self._secret_key:
            raise SupabaseConfigError(
                "Configura SUPABASE_SECRET_KEY en backend/.env con una clave "
                "secreta vigente de Supabase."
            )

        headers = {
            "apikey": self._secret_key,
            "Authorization": f"Bearer {self._secret_key}",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        if prefer:
            headers["Prefer"] = prefer

        response = self._client.request(
            method,
            f"{self._url}/rest/v1/{resource.lstrip('/')}",
            params=params,
            json=_json_value(body) if body is not None else None,
            headers=headers,
        )
        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def select(self, table: str, **params: Any) -> list[dict[str, Any]]:
        rows = self.request("GET", table, params=params)
        if not isinstance(rows, list):
            raise TypeError(f"Supabase devolvió una respuesta inválida para {table}.")
        return rows

    def insert(self, table: str, values: Any, *, select: str = "*") -> list[dict[str, Any]]:
        rows = self.request(
            "POST",
            table,
            params={"select": select},
            body=values,
            prefer="return=representation",
        )
        return rows or []

    def update(self, table: str, filters: dict[str, str], values: dict[str, Any]) -> None:
        self.request(
            "PATCH",
            table,
            params=filters,
            body=values,
            prefer="return=minimal",
        )

    def delete(self, table: str, filters: dict[str, str]) -> None:
        self.request("DELETE", table, params=filters, prefer="return=minimal")

    def rpc(self, function: str, arguments: dict[str, Any]) -> Any:
        return self.request("POST", f"rpc/{function}", body=arguments)


supabase = SupabaseRest()
