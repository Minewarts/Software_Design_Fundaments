"""Adaptadores de generación de itinerarios y traducción sobre Gemini."""
from __future__ import annotations

import json
from uuid import UUID

from app.application.ports.servicio_ia import CatalogoCandidato, ItemPropuesto, PropuestaIA, ServicioIA
from app.application.ports.traductor import Traductor
from app.domain.entities.enums import TipoRecurso
from app.domain.entities.perfil_viaje import PerfilViaje
from app.domain.exceptions.errores import PropuestaIAInvalidaError
from app.infrastructure.ai.gemini_client import GeminiClient

SYSTEM = """Eres un diseñador de itinerarios turísticos para una agencia de viajes.
Recibes un perfil de viaje y un catálogo cerrado de recursos. Responde SOLO con JSON:
{"titulo": str, "items": [{"numero_dia": int, "tipo_recurso": "ALOJAMIENTO"|"ACTIVIDAD"|"TRANSPORTE", "id_recurso": uuid}]}
Reglas: usa únicamente id del catálogo; incluye al menos un ALOJAMIENTO (día 1); días entre 1 y duracion_dias;
reparte las actividades según los intereses y el tipo de viajero; 1-3 ítems por día; no inventes recursos."""


class LLMServicioIA(ServicioIA):
    def __init__(self, cliente: GeminiClient) -> None:
        self._c = cliente

    def generar_itinerario(self, perfil: PerfilViaje, cat: CatalogoCandidato) -> PropuestaIA:
        entrada = {
            "perfil": {"duracion_dias": perfil.duracion_dias, "viajeros": perfil.cantidad_viajeros,
                       "tipo_viajero": perfil.tipo_viajero.value, "intereses": list(perfil.intereses)},
            "catalogo": {
                "alojamientos": [{"id": str(a.id), "nombre": a.nombre, "estrellas": a.categoria_estrellas,
                                  "tarifa_noche": float(a.tarifa_noche)} for a in cat.alojamientos],
                "actividades": [{"id": str(a.id), "nombre": a.nombre, "tipo": a.tipo_actividad,
                                 "costo_persona": float(a.costo_persona)} for a in cat.actividades],
                "transportes": [{"id": str(t.id), "tipo": t.tipo_vehiculo,
                                 "tarifa": float(t.tarifa_estimada)} for t in cat.transportes]}}
        data = self._c.json(SYSTEM, json.dumps(entrada, ensure_ascii=False))
        try:
            items = [ItemPropuesto(int(i["numero_dia"]), TipoRecurso(i["tipo_recurso"]), UUID(i["id_recurso"]))
                     for i in data["items"]]
            return PropuestaIA(str(data["titulo"]), items)
        except (KeyError, ValueError, TypeError) as e:
            raise PropuestaIAInvalidaError(f"Propuesta de IA mal formada: {e}") from e


class GeminiTraductor(Traductor):
    def __init__(self, cliente: GeminiClient) -> None:
        self._c = cliente

    def traducir(self, textos: dict[str, str], idioma: str) -> dict[str, str]:
        data = self._c.json(f"Traduce al idioma «{idioma}» los VALORES del JSON recibido. Conserva las claves exactas "
                            "y no traduzcas nombres propios. Responde SOLO con el JSON.",
                            json.dumps(textos, ensure_ascii=False))
        return {k: str(data.get(k, v)) for k, v in textos.items()}
