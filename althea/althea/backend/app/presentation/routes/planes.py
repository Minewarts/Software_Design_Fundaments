from uuid import UUID

from fastapi import APIRouter, Response

from app.domain.entities.perfil_viaje import PerfilViaje
from app.presentation import dependencies as D
from app.presentation.schemas.schemas import (EstadoIn, ItemIn, MoverIn, PerfilIn, PlanManualIn, ValoracionIn)

router = APIRouter()


@router.post("/planes/generar", status_code=201)            # HU-08
def generar_plan(p: PerfilIn):
    perfil = PerfilViaje(p.presupuesto_max, p.duracion_dias, p.cantidad_viajeros, p.tipo_viajero,
                         tuple(p.intereses), p.id_destino)
    plan = D.generar.ejecutar(perfil)
    return {"id": plan.id, "titulo": plan.titulo, "costo_estimado": plan.costo_estimado}


@router.post("/planes", status_code=201)                    # HU-06
def crear_plan(p: PlanManualIn):
    items = [(i.numero_dia, i.tipo_recurso, i.id_recurso) for i in p.items]
    return {"id": D.gestionar.crear_manual(p.titulo, p.cantidad_viajeros, items)}


@router.get("/planes")                                      # HU-10 / HU-11
def listar(destino: str | None = None, estado: str | None = None, precio_min: float | None = None,
           precio_max: float | None = None, dias_max: int | None = None):
    return D.gestionar.listar(dict(destino=destino, estado=estado, precio_min=precio_min,
                                   precio_max=precio_max, dias_max=dias_max))


@router.get("/planes/{id_plan}")                            # HU-12
def ficha(id_plan: UUID):
    return D.gestionar.ficha(id_plan)


@router.post("/planes/{id_plan}/duplicar", status_code=201)  # HU-14
def duplicar(id_plan: UUID):
    return {"id": D.gestionar.duplicar(id_plan)}


@router.put("/planes/{id_plan}/estado")
def estado(id_plan: UUID, b: EstadoIn):
    D.gestionar.cambiar_estado(id_plan, b.estado)
    return {"ok": True}


@router.post("/planes/{id_plan}/items", status_code=201)    # HU-09
def agregar_item(id_plan: UUID, b: ItemIn):
    D.gestionar.agregar_item(id_plan, b.numero_dia, b.tipo_recurso, b.id_recurso)
    return {"ok": True}


@router.put("/planes/{id_plan}/items/{id_item}")
def mover_item(id_plan: UUID, id_item: UUID, b: MoverIn):
    D.gestionar.mover_item(id_plan, id_item, b.numero_dia)
    return {"ok": True}


@router.delete("/planes/{id_plan}/items/{id_item}", status_code=204)
def quitar_item(id_plan: UUID, id_item: UUID):
    D.gestionar.quitar_item(id_plan, id_item)


@router.get("/planes/{id_plan}/pdf")                        # HU-13
def pdf(id_plan: UUID):
    return Response(D.exportar.ejecutar(id_plan), media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="plan-{id_plan}.pdf"'})


@router.get("/planes/{id_plan}/valoraciones")               # HU-17
def valoraciones(id_plan: UUID):
    return D.gestionar.valoraciones(id_plan)


@router.post("/planes/{id_plan}/valoraciones", status_code=201)
def calificar(id_plan: UUID, b: ValoracionIn):
    D.gestionar.calificar(id_plan, b.autor, b.puntuacion, b.comentario)
    return {"ok": True}
