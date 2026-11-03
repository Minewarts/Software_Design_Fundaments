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

SYSTEM = """Eres un agente de viajes senior y diseñador de experiencias turísticas de lujo y aventura. Crea itinerarios lógicos, atractivos y equilibrados, desde escapadas cortas hasta circuitos de varios destinos.
FORMATO DE SALIDA ESTRICTO:
Responde únicamente con un objeto JSON válido, sin Markdown, saludos ni texto adicional. Usa exactamente esta estructura y estas claves:
{"titulo_plan":"Nombre comercial del plan","descripcion_corta":"Breve descripción de la experiencia","costo_total_estimado":0,"itinerario":[{"dia":1,"destino_del_dia":"Nombre del destino","titulo_dia":"Título breve del día","recursos":[{"id_recurso":"UUID exacto del catálogo","tipo":"TRANSPORTE","nombre":"Nombre exacto del catálogo"}]}]}
Cada día debe usar un número entre 1 y duracion_dias. Incluye los días libres con recursos vacío. tipo debe ser exactamente ALOJAMIENTO, ACTIVIDAD o TRANSPORTE. No agregues claves a ningún objeto.
Reglas obligatorias:
- Cada id_recurso debe existir en la lista correspondiente de [CATÁLOGO DE RECURSOS]. No inventes ni sustituyas recursos.
- Usa exclusivamente los destinos y recursos seleccionados. Respeta destinos_en_orden y crea una ruta secuencial; nunca retrocedas ni saltes destinos.
- Al cambiar de destino, incluye un TRANSPORTE enlazado tanto al origen como al destino cuando exista en el catálogo. Si no existe esa conexión, no inventes un transporte: asume que el viajero gestiona ese traslado por su cuenta y continúa con el siguiente destino.
- Los elementos de items deben estar en orden cronológico. Ordena el alojamiento, las actividades y los traslados según ocurrirían. No incluyas actividades de una ciudad después de salir de ella.
- Programa como máximo 3 actividades por día. En un día de cambio de destino, reduce las actividades y prioriza el traslado y el check-in.
- En viajes de más de 7 días, intercala días ligeros de descanso o tiempo libre. La duración define los días posibles (1 a duracion_dias), no una cuota de actividades. Un día libre puede tener cero actividades; no inventes un recurso llamado «Libre».
- Incluye alojamiento el día de llegada en cada destino donde se pernocte. No fuerces alojamiento en una ciudad visitada solo de paso ni en un viaje de un día. Evita más de un check-in por día.
- La suma de alojamientos, actividades y transportes no debe superar el presupuesto máximo indicado. Calcula alojamiento por noche y habitación, actividades por persona y transporte por tarifa estimada. Prioriza opciones asequibles.
- costo_total_estimado debe ser un número, pero es solo informativo: el sistema recalcula el costo con los precios del catálogo y no confía en el costo generado por la IA.
- En cada recurso, tipo e id_recurso deben corresponder al mismo elemento del catálogo y nombre debe copiarse exactamente. No uses el texto del nombre como identificador.
- Mantén un ritmo adecuado al tipo de viajero y sus intereses, evita repetir actividades y no afirmes horarios, duraciones ni servicios que no estén en el catálogo.
- Si faltan recursos adecuados, deja el día sin elementos en vez de inventar recursos. Si no hay enlace de transporte entre dos destinos, el traslado queda a cargo del viajero como se indicó arriba.
- El itinerario y los recursos son la fuente de verdad; destino_del_dia y titulo_dia son etiquetas descriptivas. No añadas claves, comentarios ni texto fuera del JSON."""


class LLMServicioIA(ServicioIA):
    def __init__(self, cliente: GeminiClient) -> None:
        self._c = cliente

    def generar_itinerario(self, perfil: PerfilViaje, cat: CatalogoCandidato) -> PropuestaIA:
        entrada = {
            "perfil": {"presupuesto_max": float(perfil.presupuesto_max), "moneda": "COP",
                       "duracion_dias": perfil.duracion_dias, "viajeros": perfil.cantidad_viajeros,
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
            if not isinstance(data, dict) or set(data) != {
                "titulo_plan", "descripcion_corta", "costo_total_estimado", "itinerario",
            }:
                raise ValueError("la respuesta no coincide con la estructura JSON requerida")
            if not isinstance(data["titulo_plan"], str) or not isinstance(data["descripcion_corta"], str):
                raise TypeError("titulo_plan y descripcion_corta deben ser texto")
            if (
                isinstance(data["costo_total_estimado"], bool)
                or not isinstance(data["costo_total_estimado"], (int, float))
            ):
                raise TypeError("costo_total_estimado debe ser numérico")
            dias = data["itinerario"]
            if not isinstance(dias, list):
                raise TypeError("itinerario debe ser una lista")
            items = []
            for dia in dias:
                if not isinstance(dia, dict) or set(dia) != {
                    "dia", "destino_del_dia", "titulo_dia", "recursos",
                }:
                    raise ValueError("cada día debe tener exactamente las claves solicitadas")
                if (
                    type(dia["dia"]) is not int
                    or not isinstance(dia["destino_del_dia"], str)
                    or not isinstance(dia["titulo_dia"], str)
                    or not isinstance(dia["recursos"], list)
                ):
                    raise TypeError("los datos del día tienen un tipo inválido")
                for recurso in dia["recursos"]:
                    if not isinstance(recurso, dict) or set(recurso) != {
                        "id_recurso", "tipo", "nombre",
                    }:
                        raise ValueError("cada recurso debe tener exactamente las claves solicitadas")
                    if not isinstance(recurso["nombre"], str):
                        raise TypeError("el nombre del recurso debe ser texto")
                    items.append(ItemPropuesto(
                        dia["dia"],
                        TipoRecurso(recurso["tipo"]),
                        UUID(recurso["id_recurso"]),
                    ))
            return PropuestaIA(str(data["titulo_plan"]), items)
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
