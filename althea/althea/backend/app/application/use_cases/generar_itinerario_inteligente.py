"""
app/application/use_cases/generar_itinerario_inteligente.py

Caso de uso: PerfilViaje -> catálogo filtrado -> IA -> validación -> PlanTuristico.
La IA nunca es fuente de verdad: sus IDs se validan contra el catálogo y el costo
se recalcula en el dominio (evita alucinaciones y desvíos de presupuesto).
"""
from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from app.application.ports.exportador_plan import Recurso  # noqa: F401  (re-export tipo)
from app.application.ports.plan_repository import PlanRepository
from app.application.ports.recurso_repository import RecursoRepository
from app.application.ports.servicio_ia import (
    CatalogoCandidato, ItemPropuesto, PropuestaIA, ServicioIA,
)
from app.domain.entities.enums import TipoRecurso
from app.domain.entities.perfil_viaje import PerfilViaje
from app.domain.entities.plan_turistico import PlanTuristico
from app.domain.entities.recursos import Transporte
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
        ids_destinos = perfil.destinos_seleccionados
        if not ids_destinos:
            raise RecursosInsuficientesError("Selecciona al menos un destino para generar el itinerario.")

        destinos = []
        alojamientos = []
        actividades = []
        for id_destino in ids_destinos:
            destino = self._recursos.buscar_destinos(id_destino)
            if not destino:
                raise RecursosInsuficientesError(f"No se encontró el destino seleccionado: {id_destino}")
            destinos.extend(destino)
            alojamientos.extend(self._recursos.buscar_alojamientos(id_destino, tarifa_max))
            actividades.extend(
                self._recursos.buscar_actividades(id_destino, costo_act_max, perfil.intereses)
            )

        destinos_permitidos = set(ids_destinos)
        transportes = []
        for transporte in self._recursos.buscar_transportes(p * PCT_TRANSPORTE):
            ids_transporte = set(transporte.ids_destinos)
            destinos_coincidentes = ids_transporte & destinos_permitidos
            if destinos_coincidentes:
                transportes.append(replace(
                    transporte,
                    ids_destinos=tuple(
                        id_destino for id_destino in transporte.ids_destinos
                        if id_destino in destinos_permitidos
                    ),
                ))
            elif len(destinos_permitidos) == 1 and not ids_transporte:
                transportes.append(transporte)

        if not alojamientos and perfil.duracion_dias > 1:
            raise RecursosInsuficientesError(
                "No hay alojamientos dentro del presupuesto por noche para los destinos seleccionados. "
                "Aumenta el presupuesto o reduce la duración o la cantidad de viajeros.")
        return CatalogoCandidato(alojamientos, actividades, transportes, destinos)

    # ── 2. Validar propuesta de la IA y armar el plan ──
    def _construir_plan(self, perfil: PerfilViaje, cat: CatalogoCandidato,
                        propuesta: PropuestaIA) -> PlanTuristico:
        indice = {
            TipoRecurso.ALOJAMIENTO: {a.id: a for a in cat.alojamientos},
            TipoRecurso.ACTIVIDAD: {a.id: a for a in cat.actividades},
            TipoRecurso.TRANSPORTE: {t.id: t for t in cat.transportes},
        }
        plan = PlanTuristico(
            titulo=propuesta.titulo,
            cantidad_viajeros=perfil.cantidad_viajeros,
            id_destino=perfil.destinos_seleccionados[0],
            duracion_dias=perfil.duracion_dias,
            id_destinos=perfil.destinos_seleccionados,
        )
        ordenados = sorted(enumerate(propuesta.items), key=lambda entrada: (entrada[1].numero_dia, entrada[0]))
        self._validar_ruta(perfil, cat, ordenados)

        costo = Decimal("0")
        alojamientos = []
        for _, it in ordenados:
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
                alojamientos.append((it.numero_dia, recurso))

        for index, (dia_entrada, alojamiento) in enumerate(alojamientos):
            siguiente_entrada = (
                alojamientos[index + 1][0]
                if index + 1 < len(alojamientos)
                else perfil.duracion_dias
            )
            noches = max(0, siguiente_entrada - dia_entrada)
            if len(alojamientos) == 1 and perfil.duracion_dias > 1:
                noches = max(noches, 1)
            costo += alojamiento.tarifa_noche * noches * perfil.habitaciones

        plan.costo_estimado = costo.quantize(Decimal("0.01"))
        return plan

    @staticmethod
    def _validar_ruta(
        perfil: PerfilViaje,
        cat: CatalogoCandidato,
        ordenados: list[tuple[int, ItemPropuesto]],
    ) -> None:
        destinos = perfil.destinos_seleccionados
        posicion = {id_destino: index for index, id_destino in enumerate(destinos)}
        indice = {
            TipoRecurso.ALOJAMIENTO: {recurso.id: recurso for recurso in cat.alojamientos},
            TipoRecurso.ACTIVIDAD: {recurso.id: recurso for recurso in cat.actividades},
            TipoRecurso.TRANSPORTE: {recurso.id: recurso for recurso in cat.transportes},
        }
        destino_actual = None
        transportes_desde_ultimo_destino: list[Transporte] = []
        visitados = []
        dias_llegada: dict = {}
        alojamientos_por_dia: set[int] = set()

        for _, item in ordenados:
            if not 1 <= item.numero_dia <= perfil.duracion_dias:
                raise PropuestaIAInvalidaError(f"Día fuera de rango: {item.numero_dia}")
            recurso = indice[item.tipo_recurso].get(item.id_recurso)
            if recurso is None:
                raise PropuestaIAInvalidaError(
                    f"La IA refirió un recurso inexistente: {item.id_recurso}")

            if item.tipo_recurso is TipoRecurso.TRANSPORTE:
                asociados = set(recurso.ids_destinos)
                if asociados and destino_actual is not None and destino_actual not in asociados:
                    raise PropuestaIAInvalidaError(
                        "El transporte no está asociado al destino desde el que comienza el trayecto.")
                transportes_desde_ultimo_destino.append(recurso)
                continue

            id_destino = recurso.id_destino
            if id_destino not in posicion:
                raise PropuestaIAInvalidaError(
                    "La IA incluyó un recurso de un destino no seleccionado.")

            if item.tipo_recurso is TipoRecurso.ALOJAMIENTO:
                if item.numero_dia in alojamientos_por_dia:
                    raise PropuestaIAInvalidaError(
                        f"Hay más de un check-in de alojamiento en el día {item.numero_dia}.")
                alojamientos_por_dia.add(item.numero_dia)

            if destino_actual is None:
                if posicion[id_destino] != 0:
                    raise PropuestaIAInvalidaError(
                        "La ruta no comienza por el primer destino seleccionado.")
                destino_actual = id_destino
                visitados.append(id_destino)
                dias_llegada[id_destino] = item.numero_dia
                transportes_desde_ultimo_destino.clear()
                continue

            if id_destino != destino_actual:
                posicion_anterior = posicion[destino_actual]
                posicion_nueva = posicion[id_destino]
                if posicion_nueva < posicion_anterior:
                    raise PropuestaIAInvalidaError(
                        "La ruta retrocede a un destino visitado anteriormente.")
                if posicion_nueva != posicion_anterior + 1:
                    raise PropuestaIAInvalidaError(
                        "La ruta debe visitar los destinos seleccionados en el orden indicado.")
                transporte_disponible = any(
                    destino_actual in transporte.ids_destinos
                    and id_destino in transporte.ids_destinos
                    for transporte in cat.transportes
                )
                transporte_propuesto = any(
                    destino_actual in transporte.ids_destinos
                    and id_destino in transporte.ids_destinos
                    for transporte in transportes_desde_ultimo_destino
                )
                if transporte_disponible and not transporte_propuesto:
                    raise PropuestaIAInvalidaError(
                        "Cada cambio de destino con transporte disponible debe incluirlo en la ruta.")
                destino_actual = id_destino
                visitados.append(id_destino)
                dias_llegada[id_destino] = item.numero_dia
            transportes_desde_ultimo_destino.clear()

        if tuple(visitados) != destinos:
            raise PropuestaIAInvalidaError(
                "La propuesta debe incluir los destinos seleccionados en el orden indicado.")

        alojamientos = {
            (
                indice[TipoRecurso.ALOJAMIENTO][item.id_recurso].id_destino,
                item.numero_dia,
            )
            for _, item in ordenados
            if item.tipo_recurso is TipoRecurso.ALOJAMIENTO
        }
        for index, id_destino in enumerate(destinos):
            dia_salida = (
                dias_llegada[destinos[index + 1]]
                if index + 1 < len(destinos)
                else perfil.duracion_dias
            )
            if dia_salida > dias_llegada[id_destino] and (
                id_destino, dias_llegada[id_destino]
            ) not in alojamientos:
                raise PropuestaIAInvalidaError(
                    "Cada destino con noche de estadía necesita un alojamiento el día de llegada.")
