from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.domain.entities.enums import TipoViajero
from app.presentation import dependencies
from app.presentation.routes.planes import generar_plan
from app.presentation.schemas.schemas import PerfilIn


def test_generator_route_preserves_the_selected_destination_order(monkeypatch):
    destination_ids = [uuid4(), uuid4(), uuid4()]
    captured = {}

    class FakeGenerator:
        def ejecutar(self, perfil):
            captured["profile"] = perfil
            return SimpleNamespace(id=uuid4(), titulo="Ruta", costo_estimado=Decimal("100"))

    monkeypatch.setattr(dependencies, "generar", FakeGenerator())
    request = PerfilIn(
        id_destinos=destination_ids,
        duracion_dias=5,
        presupuesto_max=Decimal("1000000"),
        cantidad_viajeros=2,
        tipo_viajero=TipoViajero.FAMILIA,
    )

    generar_plan(request)

    perfil = captured["profile"]
    assert perfil.id_destino == destination_ids[0]
    assert perfil.destinos_seleccionados == tuple(destination_ids)
