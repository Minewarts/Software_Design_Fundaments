from decimal import Decimal

import pytest

from app.application.ports.servicio_ia import ItemPropuesto, PropuestaIA
from app.application.use_cases.generar_itinerario_inteligente import GenerarItinerarioInteligente
from app.domain.entities.enums import TipoRecurso, TipoViajero
from app.domain.entities.perfil_viaje import PerfilViaje
from app.domain.entities.recursos import Actividad, Alojamiento
from app.domain.exceptions.errores import PropuestaIAInvalidaError, RecursosInsuficientesError
from uuid import uuid4

DEST = uuid4()
HOTEL, ACT = Alojamiento(DEST, "Hotel Sol", 4, Decimal("100000")), Actividad(DEST, "Buceo", "Aventura", Decimal("80000"))


class FakeRecursos:
    def buscar_alojamientos(self, *a): return [HOTEL]
    def buscar_actividades(self, *a): return [ACT]
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
