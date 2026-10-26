from datetime import date
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation import dependencies as D
from app.presentation.schemas.schemas import TraducirIn

router = APIRouter()


@router.get("/clima/{id_destino}")
def clima(id_destino: UUID, mes: int = Query(date.today().month, ge=1, le=12)):
    return D.clima.ejecutar(id_destino, mes)


@router.get("/clima/actual/{id_destino}")
def clima_actual(id_destino: UUID):
    return D.clima.actual(id_destino)


@router.post("/traducir")
def traducir(b: TraducirIn):
    return D.traducir.ejecutar(b.textos, b.idioma)
