"""Adaptador ServicioClima (HU-15) con Open-Meteo: geocoding + archivo histórico (sin API key)."""
from __future__ import annotations

from datetime import date, timedelta
from statistics import mean

import httpx

from app.application.ports.servicio_clima import ServicioClima
from app.domain.exceptions.errores import DominioError


class OpenMeteoClima(ServicioClima):
    def historico_mensual(self, lugar: str, mes: int) -> dict:
        geo = httpx.get("https://geocoding-api.open-meteo.com/v1/search", timeout=20,
                        params={"name": lugar, "count": 1, "language": "es"}).json().get("results")
        if not geo:
            raise DominioError(f"No se pudo ubicar «{lugar}» para consultar el clima")
        g, anio = geo[0], date.today().year - 1          # último año completo
        ini = date(anio, mes, 1)
        fin = date(anio + (mes == 12), mes % 12 + 1, 1) - timedelta(days=1)
        r = httpx.get("https://archive-api.open-meteo.com/v1/archive", timeout=30, params={
            "latitude": g["latitude"], "longitude": g["longitude"], "start_date": ini.isoformat(),
            "end_date": fin.isoformat(), "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "timezone": "auto"})
        r.raise_for_status()
        d = r.json()["daily"]
        ok = lambda xs: [x for x in xs if x is not None]  # noqa: E731
        return {"lugar": g["name"], "mes": mes, "anio": anio,
                "temp_max": round(mean(ok(d["temperature_2m_max"])), 1),
                "temp_min": round(mean(ok(d["temperature_2m_min"])), 1),
                "lluvia_mm": round(sum(ok(d["precipitation_sum"])), 1),
                "dias_lluvia": sum(1 for x in ok(d["precipitation_sum"]) if x >= 1)}
