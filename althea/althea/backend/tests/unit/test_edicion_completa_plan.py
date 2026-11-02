from uuid import uuid4

import pytest

from app.application.use_cases.gestionar_planes import GestionarPlanes
from app.domain.entities.enums import EstadoPlan, TipoRecurso
from app.domain.entities.plan_turistico import PlanTuristico
from app.domain.exceptions.errores import DominioError


class FakePlanes:
    def __init__(self, plan):
        self.plan = plan
        self.actualizacion = None

    def obtener_por_id(self, _id):
        return self.plan

    def actualizar_completo(self, *args):
        self.actualizacion = args


def test_actualiza_datos_y_reemplaza_itinerario_completo():
    id_plan, id_destino, id_recurso = uuid4(), uuid4(), uuid4()
    id_destinos = [id_destino, uuid4()]
    planes = FakePlanes(PlanTuristico("Anterior", id=id_plan))
    items = [{
        "numero_dia": 2,
        "tipo_recurso": TipoRecurso.ACTIVIDAD,
        "id_recurso": id_recurso,
    }]

    GestionarPlanes(planes).actualizar_completo(
        id_plan, "  Nuevo itinerario  ", 3, id_destinos, items,
    )

    assert planes.actualizacion == (id_plan, "Nuevo itinerario", 3, id_destinos, items)


def test_permite_editar_plan_archivado_sin_cambiar_su_estado():
    planes = FakePlanes(PlanTuristico("Archivado", estado=EstadoPlan.ARCHIVADO))

    GestionarPlanes(planes).actualizar_completo(uuid4(), "Plan editado", 2, [], [])

    assert planes.actualizacion[1] == "Plan editado"
    assert planes.plan.estado is EstadoPlan.ARCHIVADO


def test_no_permite_titulo_vacio():
    planes = FakePlanes(PlanTuristico("Anterior"))

    with pytest.raises(DominioError, match="título"):
        GestionarPlanes(planes).actualizar_completo(uuid4(), "  ", 2, [], [])

    assert planes.actualizacion is None
