import json
from uuid import uuid4

from app.application.ports.servicio_ia import CatalogoCandidato
from app.domain.entities.enums import TipoViajero
from app.domain.entities.perfil_viaje import PerfilViaje
from app.domain.entities.recursos import Actividad, Alojamiento, Destino, Transporte
from app.infrastructure.ai.llm_servicio_ia import LLMServicioIA, SYSTEM


class FakeGeminiClient:
    def __init__(self):
        self.system = None
        self.user = None

    def json(self, system, user):
        self.system = system
        self.user = user
        return {"titulo": "Ruta", "items": []}


def test_prompt_and_payload_include_ordered_destination_resource_scope():
    destination_a, destination_b = uuid4(), uuid4()
    hotel = Alojamiento(destination_a, "Hotel A", 3, 100)
    activity = Actividad(destination_b, "Museo B", "Cultura", 20)
    transport = Transporte("Bus", 40, ids_destinos=(destination_a, destination_b))
    destinations = [
        Destino("Ciudad A", "Ubicación A", "", destination_a),
        Destino("Ciudad B", "Ubicación B", "", destination_b),
    ]
    profile = PerfilViaje(
        5000, 3, 2, TipoViajero.FAMILIA, (), destination_a,
        (destination_a, destination_b),
    )
    client = FakeGeminiClient()

    LLMServicioIA(client).generar_itinerario(
        profile,
        CatalogoCandidato([hotel], [activity], [transport], destinations),
    )

    payload = json.loads(client.user)
    assert [destination["id"] for destination in payload["destinos_en_orden"]] == [
        str(destination_a), str(destination_b),
    ]
    assert payload["catalogo"]["actividades"][0]["id_destino"] == str(destination_b)
    assert payload["catalogo"]["transportes"][0]["ids_destinos"] == [
        str(destination_a), str(destination_b),
    ]
    assert "cero items" in client.system
    assert "no retrocedas" in client.system
    assert "transporte" in client.system
