from app.application.use_cases.servicios_externos import ConsultarClimaHistorico
from app.infrastructure.weather_open_meteo import OpenMeteoClima


class FakeDestino:
    def __init__(self, nombre, ubicacion):
        self.nombre = nombre
        self.ubicacion = ubicacion


class FakeRepositorio:
    def __init__(self, destino):
        self._destino = destino

    def buscar_destinos(self, _id):
        return [self._destino]


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
        return Response({
            "current": {
                "time": "2026-10-25T15:00",
                "temperature_2m": 22.4,
                "apparent_temperature": 23.1,
                "relative_humidity_2m": 61,
                "precipitation": 0.0,
                "weather_code": 1,
                "wind_speed_10m": 7.2,
            },
            "daily": {
                "time": [
                    "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28",
                    "2026-10-29", "2026-10-30", "2026-10-31",
                ],
                "temperature_2m_max": [22, 23, 24, 25, 26, 27, 28],
                "temperature_2m_min": [12, 13, 14, 15, 16, 17, 18],
                "weather_code": [0, 1, 2, 3, 45, 61, 95],
                "precipitation_probability_max": [0, 10, 20, 30, 40, 50, 60],
            },
        })

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
        "pronostico": [
            {
                "fecha": "2026-10-26",
                "estado": "Mayormente despejado o nublado",
                "temperatura_max": 23,
                "temperatura_min": 13,
                "probabilidad_precipitacion": 10,
                "codigo_tiempo": 1,
            },
            {
                "fecha": "2026-10-27",
                "estado": "Mayormente despejado o nublado",
                "temperatura_max": 24,
                "temperatura_min": 14,
                "probabilidad_precipitacion": 20,
                "codigo_tiempo": 2,
            },
            {
                "fecha": "2026-10-28",
                "estado": "Mayormente despejado o nublado",
                "temperatura_max": 25,
                "temperatura_min": 15,
                "probabilidad_precipitacion": 30,
                "codigo_tiempo": 3,
            },
            {
                "fecha": "2026-10-29",
                "estado": "Niebla",
                "temperatura_max": 26,
                "temperatura_min": 16,
                "probabilidad_precipitacion": 40,
                "codigo_tiempo": 45,
            },
            {
                "fecha": "2026-10-30",
                "estado": "Lluvia",
                "temperatura_max": 27,
                "temperatura_min": 17,
                "probabilidad_precipitacion": 50,
                "codigo_tiempo": 61,
            },
            {
                "fecha": "2026-10-31",
                "estado": "Tormenta",
                "temperatura_max": 28,
                "temperatura_min": 18,
                "probabilidad_precipitacion": 60,
                "codigo_tiempo": 95,
            },
        ],
    }
    assert calls[0][2]["name"] == "Medellín, Colombia"
    assert calls[1][0] == "https://api.open-meteo.com/v1/forecast"
    assert calls[1][2]["latitude"] == 6.24
    assert calls[1][2]["forecast_days"] == 7


def test_actual_uses_ubicacion_without_repeating_destination_name(monkeypatch):
    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self.payload

    llamadas = []

    def get(url, *, timeout, params):
        llamadas.append((url, params))
        if "geocoding-api" in url:
            return Response({"results": [{"name": "Cartagena", "latitude": 10.4, "longitude": -75.5}]})
        return Response({
            "current": {
                "time": "2026-10-25T15:00",
                "temperature_2m": 30.0,
                "apparent_temperature": 31.0,
                "relative_humidity_2m": 75,
                "precipitation": 0.2,
                "weather_code": 0,
                "wind_speed_10m": 12.3,
            },
            "daily": {
                "time": ["2026-10-25"],
                "temperature_2m_max": [30.0],
                "temperature_2m_min": [24.0],
                "weather_code": [0],
                "precipitation_probability_max": [0],
            },
        })

    monkeypatch.setattr("app.infrastructure.weather_open_meteo.httpx.get", get)

    result = ConsultarClimaHistorico(FakeRepositorio(FakeDestino("Cartagena", "Cartagena, Bolívar, Colombia")), OpenMeteoClima()).actual("fake-id")

    assert result["lugar"] == "Cartagena"
    assert llamadas[0][1]["name"] == "Cartagena, Bolívar, Colombia"
