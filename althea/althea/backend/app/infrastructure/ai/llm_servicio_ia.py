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

SYSTEM = """Eres un planificador de viajes. Construye un itinerario realista y cronológico usando exclusivamente el perfil, los destinos ordenados y los recursos del catálogo recibido.
Devuelve solo JSON válido con esta forma exacta:
{"titulo":"texto","items":[{"numero_dia":1,"tipo_recurso":"ALOJAMIENTO","id_recurso":"UUID"}]}
tipo_recurso debe ser exactamente uno de: ALOJAMIENTO, ACTIVIDAD, TRANSPORTE.
Reglas obligatorias:
- Cada id_recurso debe existir en la lista correspondiente del catálogo. No inventes, sustituyas ni combines IDs.
- Usa solo recursos asociados a los destinos seleccionados. Respeta su orden como ruta: no retrocedas ni saltes a un destino posterior sin un transporte que esté asociado tanto al destino de salida como al de llegada.
- Los elementos del arreglo están en orden cronológico. Dentro de un día, ordena las actividades, el transporte y el alojamiento según ocurrirían. Para cambiar de ciudad en el mismo día, coloca el transporte entre los recursos de ambas ciudades.
- No mezcles actividades de ciudades distintas sin un traslado entre ellas. No planifiques una actividad en una ciudad después de que el grupo ya haya salido de ella.
- La duración define los días posibles (1 a duracion_dias), no una cuota de actividades. Puedes dejar cualquier día sin elementos si un día libre o de traslado sin actividad es lo más razonable; representa ese día con cero items. No inventes una actividad llamada «Libre».
- Incluye alojamiento el día de llegada en cada destino donde el grupo pernocte; no fuerces alojamiento en una ciudad visitada solo de paso ni en un viaje de un día. Evita asignar más de un check-in de alojamiento en un día.
- Usa transporte únicamente si corresponde a la ruta. No añadas actividades, alojamientos ni transportes por completar una cuota diaria.
- Mantén un ritmo razonable para el tipo de viajero e intereses, evita repetir actividades y prioriza recursos asequibles. No afirmes horarios, duraciones ni servicios que no estén en el catálogo.
- Si no hay recursos adecuados para una parte del viaje, deja el día sin elementos en lugar de inventar recursos.
- No añadas claves, comentarios ni texto fuera del JSON."""


class LLMServicioIA(ServicioIA):
    def __init__(self, cliente: GeminiClient) -> None:
        self._c = cliente

    def generar_itinerario(self, perfil: PerfilViaje, cat: CatalogoCandidato) -> PropuestaIA:
        entrada = {
            "perfil": {"duracion_dias": perfil.duracion_dias, "viajeros": perfil.cantidad_viajeros,
                       "tipo_viajero": perfil.tipo_viajero.value, "intereses": list(perfil.intereses)},
            "destinos_en_orden": [
                {"id": str(destino.id), "nombre": destino.nombre, "ubicacion": destino.ubicacion}
                for destino in cat.destinos
            ],
            "catalogo": {
                "alojamientos": [{"id": str(a.id), "nombre": a.nombre, "estrellas": a.categoria_estrellas,
                                  "id_destino": str(a.id_destino),
                                  "tarifa_noche": float(a.tarifa_noche)} for a in cat.alojamientos],
                "actividades": [{"id": str(a.id), "nombre": a.nombre, "tipo": a.tipo_actividad,
                                 "id_destino": str(a.id_destino),
                                 "costo_persona": float(a.costo_persona)} for a in cat.actividades],
                "transportes": [{"id": str(t.id), "tipo": t.tipo_vehiculo,
                                 "ids_destinos": [str(id_destino) for id_destino in t.ids_destinos],
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
