from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation import dependencies as D
from app.presentation.schemas.schemas import TraducirIn

router = APIRouter()


@router.get("/clima/{id_destino}")                          # HU-15
def clima(id_destino: UUID, mes: int = Query(date.today().month, ge=1, le=12)):
    return D.clima.ejecutar(id_destino, mes)


@router.post("/traducir")                                   # HU-18
def traducir(b: TraducirIn):
    return D.traducir.ejecutar(b.textos, b.idioma)


@router.get("/notificaciones")                              # HU-16
def notificaciones():
    return D.gestionar.notificaciones()


@router.post("/notificaciones/leer")
def leer():
    D.gestionar.marcar_leidas()
    return {"ok": True}
