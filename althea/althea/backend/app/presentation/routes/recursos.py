from uuid import UUID

from fastapi import APIRouter

from app.presentation import dependencies as D

router = APIRouter()


@router.get("/recursos/{tipo}")
def listar(tipo: str):
    return D.admin.listar(tipo)


@router.post("/recursos/{tipo}", status_code=201)
def crear(tipo: str, datos: dict):
    ids = datos.get("ids_destinos")
    r = D.crear_recurso.ejecutar(tipo, datos)
    if tipo == "transportes" and "ids_destinos" in datos:
        D.admin.sincronizar_destinos(r.id, ids)
    return {"id": r.id}


@router.put("/recursos/{tipo}/{id_}")
def editar(tipo: str, id_: UUID, datos: dict):
    D.admin.actualizar(tipo, id_, datos)
    return {"id": id_}


@router.delete("/recursos/{tipo}/{id_}", status_code=204)
def eliminar(tipo: str, id_: UUID):
    D.admin.eliminar(tipo, id_)


@router.get("/catalogo/relaciones")
def relaciones():
    return D.admin.relaciones()
