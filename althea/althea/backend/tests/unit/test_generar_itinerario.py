from decimal import Decimal

import pytest

from app.application.ports.servicio_ia import ItemPropuesto, PropuestaIA
from app.application.use_cases.generar_itinerario_inteligente import GenerarItinerarioInteligente
from app.domain.entities.enums import TipoRecurso, TipoViajero
from app.domain.entities.perfil_viaje import PerfilViaje
from app.domain.entities.recursos import Actividad, Alojamiento, Destino, Transporte
from app.domain.exceptions.errores import PropuestaIAInvalidaError, RecursosInsuficientesError
from uuid import uuid4

DEST = uuid4()
HOTEL, ACT = Alojamiento(DEST, "Hotel Sol", 4, Decimal("100000")), Actividad(DEST, "Buceo", "Aventura", Decimal("80000"))
DESTINO = Destino("Cartagena", "Cartagena, Colombia", "", DEST)


class FakeRecursos:
    def buscar_destinos(self, id_destino): return [DESTINO] if id_destino == DEST else []
    def buscar_alojamientos(self, id_destino, *a): return [HOTEL] if id_destino == DEST else []
    def buscar_actividades(self, id_destino, *a): return [ACT] if id_destino == DEST else []
    def buscar_transportes(self, *a): return []


class FakePlanes:
    def guardar(self, plan): return plan


class FakeIA:
    def __init__(self, items): self.items = items
    def generar_itinerario(self, perfil, cat): return PropuestaIA("Plan", self.items)


PERFIL = PerfilViaje(Decimal("5000000"), 3, 2, TipoViajero.FAMILIA, ("Buceo",), DEST)


def test_calcula_costo_y_arma_items():
    ia = FakeIA([ItemPropuesto(1, TipoRecurso.ALOJAMIENTO, HOTEL.id), ItemPropuesto(2, TipoRecurso.ACTIVIDAD, ACT.id)])
    plan = GenerarItinerarioInteligente(FakeRecursos(), FakePlanes(), ia).ejecutar(PERFIL)
    assert plan.costo_estimado == Decimal("360000.00")   # 100k × 2 noches × 1 hab + 80k × 2 viajeros
    assert len(plan.items) == 2 and plan.cantidad_viajeros == 2
    assert plan.duracion_dias == PERFIL.duracion_dias


def test_allows_free_days_without_inventing_a_free_activity():
    ia = FakeIA([ItemPropuesto(1, TipoRecurso.ALOJAMIENTO, HOTEL.id)])

    plan = GenerarItinerarioInteligente(FakeRecursos(), FakePlanes(), ia).ejecutar(PERFIL)

    assert len(plan.items) == 1
    assert plan.duracion_dias == 3


def test_does_not_require_accommodation_for_a_one_day_trip():
    perfil = PerfilViaje(
        Decimal("5000000"), 1, 2, TipoViajero.FAMILIA, ("Buceo",), DEST,
    )
    ia = FakeIA([ItemPropuesto(1, TipoRecurso.ACTIVIDAD, ACT.id)])

    plan = GenerarItinerarioInteligente(FakeRecursos(), FakePlanes(), ia).ejecutar(perfil)

    assert len(plan.items) == 1
    assert plan.costo_estimado == Decimal("160000.00")


def test_accepts_ordered_multi_destination_trip_with_a_linked_transfer():
    second_id = uuid4()
    hotel_second = Alojamiento(second_id, "Hotel Norte", 3, Decimal("120000"))
    activity_second = Actividad(second_id, "Museo", "Cultura", Decimal("30000"))
    second_destination = Destino("Medellín", "Medellín, Colombia", "", second_id)
    bus = Transporte("Bus intermunicipal", Decimal("50000"), ids_destinos=(DEST, second_id))

    class MultiDestinationResources(FakeRecursos):
        def buscar_destinos(self, id_destino):
            return [DESTINO] if id_destino == DEST else [second_destination] if id_destino == second_id else []

        def buscar_alojamientos(self, id_destino, *args):
            return [HOTEL] if id_destino == DEST else [hotel_second] if id_destino == second_id else []

        def buscar_actividades(self, id_destino, *args):
            return [ACT] if id_destino == DEST else [activity_second] if id_destino == second_id else []

        def buscar_transportes(self, *args):
            return [bus]

    perfil = PerfilViaje(
        Decimal("5000000"), 4, 2, TipoViajero.FAMILIA, (),
        DEST, (DEST, second_id),
    )
    propuesta = FakeIA([
        ItemPropuesto(1, TipoRecurso.ALOJAMIENTO, HOTEL.id),
        ItemPropuesto(1, TipoRecurso.ACTIVIDAD, ACT.id),
        ItemPropuesto(1, TipoRecurso.TRANSPORTE, bus.id),
        ItemPropuesto(2, TipoRecurso.ALOJAMIENTO, hotel_second.id),
        ItemPropuesto(2, TipoRecurso.ACTIVIDAD, activity_second.id),
    ])

    plan = GenerarItinerarioInteligente(
        MultiDestinationResources(), FakePlanes(), propuesta,
    ).ejecutar(perfil)

    assert plan.id_destino == DEST
    assert plan.id_destinos == (DEST, second_id)
    assert plan.duracion_dias == 4
    assert [item.numero_dia for item in plan.items] == [1, 1, 1, 2, 2]
    assert plan.costo_estimado == Decimal("610000.00")


def test_rejects_moving_to_another_destination_without_a_matching_transfer():
    second_id = uuid4()
    hotel_second = Alojamiento(second_id, "Hotel Norte", 3, Decimal("120000"))
    second_destination = Destino("Medellín", "Medellín, Colombia", "", second_id)

    class MultiDestinationResources(FakeRecursos):
        def buscar_destinos(self, id_destino):
            return [DESTINO] if id_destino == DEST else [second_destination] if id_destino == second_id else []

        def buscar_alojamientos(self, id_destino, *args):
            return [HOTEL] if id_destino == DEST else [hotel_second] if id_destino == second_id else []

        def buscar_actividades(self, *args): return []

        def buscar_transportes(self, *args): return []

    perfil = PerfilViaje(
        Decimal("5000000"), 4, 2, TipoViajero.FAMILIA, (),
        DEST, (DEST, second_id),
    )
    propuesta = FakeIA([
        ItemPropuesto(1, TipoRecurso.ALOJAMIENTO, HOTEL.id),
        ItemPropuesto(2, TipoRecurso.ALOJAMIENTO, hotel_second.id),
    ])

    with pytest.raises(PropuestaIAInvalidaError, match="transporte asociado"):
        GenerarItinerarioInteligente(
            MultiDestinationResources(), FakePlanes(), propuesta,
        ).ejecutar(perfil)


def test_rejects_activity_from_unselected_destination():
    second_id = uuid4()
    outside_activity = Actividad(second_id, "Fuera del itinerario", "Cultura", Decimal("10000"))
    ia = FakeIA([
        ItemPropuesto(1, TipoRecurso.ALOJAMIENTO, HOTEL.id),
        ItemPropuesto(2, TipoRecurso.ACTIVIDAD, outside_activity.id),
    ])

    with pytest.raises(PropuestaIAInvalidaError, match="recurso inexistente"):
        GenerarItinerarioInteligente(FakeRecursos(), FakePlanes(), ia).ejecutar(PERFIL)


def test_rechaza_recurso_inventado_por_la_ia():
    ia = FakeIA([ItemPropuesto(1, TipoRecurso.ALOJAMIENTO, uuid4())])
    with pytest.raises(PropuestaIAInvalidaError):
        GenerarItinerarioInteligente(FakeRecursos(), FakePlanes(), ia).ejecutar(PERFIL)


def test_explains_when_budget_filters_out_available_resources():
    class SinRecursosDentroDelPresupuesto(FakeRecursos):
        def buscar_alojamientos(self, *a): return []

    ia = FakeIA([])
    caso = GenerarItinerarioInteligente(SinRecursosDentroDelPresupuesto(), FakePlanes(), ia)

    with pytest.raises(RecursosInsuficientesError, match="Aumenta el presupuesto"):
        caso.ejecutar(PERFIL)
