"""Adaptador de clima con Open-Meteo: pronóstico actual e histórico (sin API key)."""
from __future__ import annotations

from datetime import date, timedelta
from statistics import mean

import httpx

from app.application.ports.servicio_clima import ServicioClima
from app.domain.exceptions.errores import DominioError


class OpenMeteoClima(ServicioClima):
    @staticmethod
    def _descripcion(codigo: int) -> str:
        if codigo == 0:
            return "Despejado"
        if codigo in (1, 2, 3):
            return "Mayormente despejado o nublado"
        if codigo in (45, 48):
            return "Niebla"
        if codigo in (51, 53, 55, 56, 57):
            return "Llovizna"
        if codigo in (61, 63, 65, 66, 67, 80, 81, 82):
            return "Lluvia"
        if codigo in (71, 73, 75, 77, 85, 86):
            return "Nieve"
        if codigo in (95, 96, 99):
            return "Tormenta"
        return "Condiciones variables"

    def _geocodificar(self, lugar: str) -> dict:
        response = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            timeout=20,
            params={"name": lugar, "count": 1, "language": "es"},
        )
        response.raise_for_status()
        results = response.json().get("results")
        if not results:
            raise DominioError(f"No se pudo ubicar «{lugar}» para consultar el clima")
        return results[0]

    def actual(self, lugar: str) -> dict:
        location = self._geocodificar(lugar)
        response = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            timeout=20,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
                "forecast_days": 7,
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        payload = response.json()
        current = payload["current"]
        code = current["weather_code"]
        daily = payload["daily"]
        today = current["time"][:10]
        forecast = [
            {
                "fecha": forecast_date,
                "estado": self._descripcion(daily["weather_code"][index]),
                "temperatura_max": daily["temperature_2m_max"][index],
                "temperatura_min": daily["temperature_2m_min"][index],
                "probabilidad_precipitacion": daily["precipitation_probability_max"][index],
                "codigo_tiempo": daily["weather_code"][index],
            }
            for index, forecast_date in enumerate(daily["time"])
            if forecast_date > today
        ][:6]
        return {
            "lugar": location["name"],
            "actualizado": current["time"],
            "estado": self._descripcion(code),
            "temperatura": current["temperature_2m"],
            "sensacion_termica": current["apparent_temperature"],
            "humedad": current["relative_humidity_2m"],
            "precipitacion": current["precipitation"],
            "viento": current["wind_speed_10m"],
            "codigo_tiempo": code,
            "pronostico": forecast,
        }

    def historico_mensual(self, lugar: str, mes: int) -> dict:
        g, anio = self._geocodificar(lugar), date.today().year - 1
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
