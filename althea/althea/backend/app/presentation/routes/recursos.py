from uuid import UUID

from fastapi import APIRouter

from app.presentation import dependencies as D

router = APIRouter()


@router.get("/recursos/{tipo}")
def listar(tipo: str):
    return D.admin.listar(tipo)


@router.post("/recursos/{tipo}", status_code=201)
def crear(tipo: str, datos: dict):
    if tipo == "destinos":
        temperatura = D.clima.actual_por_ubicacion(datos.get("ubicacion", ""))["temperatura"]
        datos = {**datos, "clima_promedio": f"{temperatura} °C"}
    ids = datos.get("ids_destinos")
    r = D.crear_recurso.ejecutar(tipo, datos)
    if tipo == "transportes" and "ids_destinos" in datos:
        D.admin.sincronizar_destinos(r.id, ids)
    return {"id": r.id}


@router.put("/recursos/{tipo}/{id_}")
def editar(tipo: str, id_: UUID, datos: dict):
    if tipo == "destinos" and "ubicacion" in datos:
        temperatura = D.clima.actual_por_ubicacion(datos["ubicacion"])["temperatura"]
        datos = {**datos, "clima_promedio": f"{temperatura} °C"}
    D.admin.actualizar(tipo, id_, datos)
    return {"id": id_}


@router.delete("/recursos/{tipo}/{id_}", status_code=204)
def eliminar(tipo: str, id_: UUID):
    D.admin.eliminar(tipo, id_)


@router.get("/catalogo/relaciones")
def relaciones():
    return D.admin.relaciones()
