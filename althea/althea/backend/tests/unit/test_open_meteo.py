from app.infrastructure.weather_open_meteo import OpenMeteoClima


def test_current_weather_uses_geocoding_and_forecast_api(monkeypatch):
    calls = []

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    def get(url, *, timeout, params):
        calls.append((url, timeout, params))
        if "geocoding-api" in url:
            return Response({"results": [{"name": "Medellín", "latitude": 6.24, "longitude": -75.58}]})
        return Response({"current": {
            "time": "2026-10-25T15:00",
            "temperature_2m": 22.4,
            "apparent_temperature": 23.1,
            "relative_humidity_2m": 61,
            "precipitation": 0.0,
            "weather_code": 1,
            "wind_speed_10m": 7.2,
        }})

    monkeypatch.setattr("app.infrastructure.weather_open_meteo.httpx.get", get)

    weather = OpenMeteoClima().actual("Medellín, Colombia")

    assert weather == {
        "lugar": "Medellín",
        "actualizado": "2026-10-25T15:00",
        "estado": "Mayormente despejado o nublado",
        "temperatura": 22.4,
        "sensacion_termica": 23.1,
        "humedad": 61,
        "precipitacion": 0.0,
        "viento": 7.2,
        "codigo_tiempo": 1,
    }
    assert calls[0][2]["name"] == "Medellín, Colombia"
    assert calls[1][0] == "https://api.open-meteo.com/v1/forecast"
    assert calls[1][2]["latitude"] == 6.24
