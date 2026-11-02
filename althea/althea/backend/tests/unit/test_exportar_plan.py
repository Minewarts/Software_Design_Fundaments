from uuid import uuid4

from app.application.use_cases.exportar_plan_ficha import ExportarPlanFicha
from app.infrastructure.export.pdf_exportador import PdfExportador


def test_pdf_export_includes_current_weather_and_forecast():
    id_destino = uuid4()
    id_plan = uuid4()
    ficha = {
        "id": str(id_plan),
        "id_destino": str(id_destino),
        "titulo": "Escapada Cartagena",
        "estado": "BORRADOR",
        "costo_estimado": 1500000,
        "cantidad_viajeros": 2,
        "duracion": 3,
        "destino": "Cartagena",
        "items": [{
            "numero_dia": 1,
            "tipo_recurso": "ACTIVIDAD",
            "nombre": "Paseo por el centro",
            "destino": "Cartagena",
        }],
    }

    class Planes:
        def ficha(self, _id):
            return ficha

    class Clima:
        def __init__(self):
            self.consultados = []

        def actual(self, destino):
            self.consultados.append(destino)
            return {
                "lugar": "Cartagena de Indias",
                "actualizado": "2026-11-01T16:45",
                "estado": "Mayormente despejado",
                "temperatura": 28.1,
                "sensacion_termica": 34.2,
                "humedad": 85,
                "precipitacion": 0.0,
                "viento": 5.2,
                "pronostico": [{
                    "fecha": "2026-11-02",
                    "estado": "Lluvia",
                    "temperatura_max": 29.0,
                    "temperatura_min": 24.0,
                    "probabilidad_precipitacion": 70,
                }],
            }

    servicio_clima = Clima()
    pdf = ExportarPlanFicha(Planes(), PdfExportador(), servicio_clima.actual).ejecutar(id_plan)

    assert servicio_clima.consultados == [id_destino]
    assert pdf.startswith(b"%PDF")
    assert b"/Type /Page" in pdf
