import json
from uuid import uuid4

import pytest

from app.application.ports.servicio_ia import CatalogoCandidato
from app.domain.entities.enums import TipoViajero
from app.domain.exceptions.errores import PropuestaIAInvalidaError
from app.domain.entities.perfil_viaje import PerfilViaje
from app.domain.entities.recursos import Actividad, Alojamiento, Destino, Transporte
from app.infrastructure.ai.llm_servicio_ia import LLMServicioIA, SYSTEM


class FakeGeminiClient:
    def __init__(self):
        self.system = None
        self.user = None
        self.response = {
            "titulo_plan": "Ruta",
            "descripcion_corta": "Una experiencia memorable.",
            "costo_total_estimado": 1000,
            "itinerario": [],
        }

    def json(self, system, user):
        self.system = system
        self.user = user
        return self.response


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
    client.response["itinerario"] = [
        {
            "dia": 1,
            "destino_del_dia": "Ciudad A",
            "titulo_dia": "Llegada",
            "recursos": [
                {"id_recurso": str(hotel.id), "tipo": "ALOJAMIENTO", "nombre": "Hotel A"},
            ],
        },
        {
            "dia": 2,
            "destino_del_dia": "Ciudad B",
            "titulo_dia": "Traslado y cultura",
            "recursos": [
                {"id_recurso": str(transport.id), "tipo": "TRANSPORTE", "nombre": "Bus"},
                {"id_recurso": str(activity.id), "tipo": "ACTIVIDAD", "nombre": "Museo B"},
            ],
        },
    ]

    proposal = LLMServicioIA(client).generar_itinerario(
        profile,
        CatalogoCandidato([hotel], [activity], [transport], destinations),
    )

    payload = json.loads(client.user)
    assert payload["perfil"]["presupuesto_max"] == 5000.0
    assert payload["perfil"]["moneda"] == "COP"
    assert [destination["id"] for destination in payload["destinos_en_orden"]] == [
        str(destination_a), str(destination_b),
    ]
    assert payload["catalogo"]["actividades"][0]["id_destino"] == str(destination_b)
    assert payload["catalogo"]["transportes"][0]["ids_destinos"] == [
        str(destination_a), str(destination_b),
    ]
    assert proposal.titulo == "Ruta"
    assert [(item.numero_dia, item.tipo_recurso, item.id_recurso) for item in proposal.items] == [
        (1, "ALOJAMIENTO", hotel.id),
        (2, "TRANSPORTE", transport.id),
        (2, "ACTIVIDAD", activity.id),
    ]
    assert "cero actividades" in client.system
    assert "nunca retrocedas" in client.system
    assert "transporte" in client.system
    assert "máximo 3 actividades por día" in client.system
    assert "presupuesto máximo indicado" in client.system
    assert "gestiona ese traslado por su cuenta" in client.system
    assert "FORMATO DE SALIDA ESTRICTO" in client.system
    assert "titulo_plan" in client.system
    assert "costo_total_estimado" in client.system
    assert "No agregues claves" in client.system


def test_rejects_response_with_unexpected_output_keys():
    client = FakeGeminiClient()
    client.response["items"] = []

    with pytest.raises(PropuestaIAInvalidaError, match="estructura JSON requerida"):
        LLMServicioIA(client).generar_itinerario(
            PerfilViaje(5000, 3, 2, TipoViajero.FAMILIA, (), uuid4()),
            CatalogoCandidato([], [], []),
        )
