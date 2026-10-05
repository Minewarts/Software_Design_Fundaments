"""
app/application/use_cases/generar_itinerario_inteligente.py

Caso de uso: PerfilViaje -> catálogo filtrado -> IA -> validación -> PlanTuristico.
La IA nunca es fuente de verdad: sus IDs se validan contra el catálogo y el costo
se recalcula en el dominio (evita alucinaciones y desvíos de presupuesto).
"""
from __future__ import annotations

from decimal import Decimal

from app.application.ports.exportador_plan import Recurso  # noqa: F401  (re-export tipo)
from app.application.ports.plan_repository import PlanRepository
from app.application.ports.recurso_repository import RecursoRepository
from app.application.ports.servicio_ia import CatalogoCandidato, PropuestaIA, ServicioIA
from app.domain.entities.enums import TipoRecurso
from app.domain.entities.perfil_viaje import PerfilViaje
from app.domain.entities.plan_turistico import PlanTuristico
from app.domain.exceptions.errores import (
    PropuestaIAInvalidaError,
    RecursosInsuficientesError,
)

# Reparto del presupuesto por rubro (regla de negocio ajustable).
PCT_ALOJAMIENTO = Decimal("0.45")
PCT_ACTIVIDADES = Decimal("0.35")
PCT_TRANSPORTE = Decimal("0.20")


class GenerarItinerarioInteligente:
    def __init__(self, recursos: RecursoRepository, planes: PlanRepository,
                 ia: ServicioIA) -> None:
        self._recursos = recursos
        self._planes = planes
        self._ia = ia

    def ejecutar(self, perfil: PerfilViaje) -> PlanTuristico:
        catalogo = self._construir_catalogo(perfil)
        propuesta = self._ia.generar_itinerario(perfil, catalogo)
        plan = self._construir_plan(perfil, catalogo, propuesta)
        plan.validar_presupuesto(perfil.presupuesto_max)
        return self._planes.guardar(plan)

    # ── 1. Catálogo que encaja con el presupuesto ──
    def _construir_catalogo(self, perfil: PerfilViaje) -> CatalogoCandidato:
        p = perfil.presupuesto_max
        tarifa_max = p * PCT_ALOJAMIENTO / (perfil.noches * perfil.habitaciones)
        costo_act_max = p * PCT_ACTIVIDADES / (perfil.duracion_dias * perfil.cantidad_viajeros)

        alojamientos = self._recursos.buscar_alojamientos(perfil.id_destino, tarifa_max)
        actividades = self._recursos.buscar_actividades(
            perfil.id_destino, costo_act_max, perfil.intereses)
        transportes = self._recursos.buscar_transportes(p * PCT_TRANSPORTE)

        if not alojamientos or not actividades:
            raise RecursosInsuficientesError(
                "No hay alojamientos/actividades que encajen con el perfil")
        return CatalogoCandidato(alojamientos, actividades, transportes)

    # ── 2. Validar propuesta de la IA y armar el plan ──
    def _construir_plan(self, perfil: PerfilViaje, cat: CatalogoCandidato,
                        propuesta: PropuestaIA) -> PlanTuristico:
        indice = {
            TipoRecurso.ALOJAMIENTO: {a.id: a for a in cat.alojamientos},
            TipoRecurso.ACTIVIDAD: {a.id: a for a in cat.actividades},
            TipoRecurso.TRANSPORTE: {t.id: t for t in cat.transportes},
        }
        plan = PlanTuristico(titulo=propuesta.titulo)
        costo = Decimal("0")
        alojamientos_usados: set = set()

        for it in propuesta.items:
            if not 1 <= it.numero_dia <= perfil.duracion_dias:
                raise PropuestaIAInvalidaError(f"Día fuera de rango: {it.numero_dia}")
            recurso = indice[it.tipo_recurso].get(it.id_recurso)
            if recurso is None:
                raise PropuestaIAInvalidaError(
                    f"La IA refirió un recurso inexistente: {it.id_recurso}")

            plan.agregar_item(it.numero_dia, it.id_recurso, it.tipo_recurso)

            if it.tipo_recurso is TipoRecurso.ACTIVIDAD:
                costo += recurso.costo_persona * perfil.cantidad_viajeros
            elif it.tipo_recurso is TipoRecurso.TRANSPORTE:
                costo += recurso.tarifa_estimada
            elif it.tipo_recurso is TipoRecurso.ALOJAMIENTO:
                # El alojamiento se cobra por noche/habitación una sola vez por hotel.
                if recurso.id not in alojamientos_usados:
                    alojamientos_usados.add(recurso.id)
                    costo += recurso.tarifa_noche * perfil.noches * perfil.habitaciones

        if not alojamientos_usados:
            raise PropuestaIAInvalidaError("La propuesta no incluye alojamiento")

        plan.costo_estimado = costo.quantize(Decimal("0.01"))
        return plan
