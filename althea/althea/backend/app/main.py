"""Punto de entrada: `uvicorn app.main:app --reload` (desde backend/)."""
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.domain.exceptions.errores import DominioError, PlanNoEncontradoError
from app.infrastructure.config.settings import settings
from app.infrastructure.persistence.rest import SupabaseConfigError
from app.presentation.routes import extras, planes, recursos

app = FastAPI(title="Althea – Planes Turísticos")
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_methods=["*"], allow_headers=["*"])
for r in (recursos.router, planes.router, extras.router):
    app.include_router(r, prefix="/api")


def _err(status: int, msg: str) -> JSONResponse:
    return JSONResponse({"detail": msg}, status_code=status)


@app.exception_handler(PlanNoEncontradoError)
async def _404(_: Request, e: PlanNoEncontradoError): return _err(404, f"No encontrado: {e}")


@app.exception_handler(DominioError)
async def _422(_: Request, e: DominioError): return _err(422, str(e))


@app.exception_handler(SupabaseConfigError)
async def _503(_: Request, e: SupabaseConfigError): return _err(503, str(e))


@app.exception_handler(httpx.HTTPStatusError)
async def _external_service_error(_: Request, e: httpx.HTTPStatusError):
    status = e.response.status_code
    host = e.request.url.host
    if host == "generativelanguage.googleapis.com":
        if status in (401, 403):
            return _err(
                502,
                "Gemini rechazó la clave de API. Verifica GEMINI_API_KEY "
                "en backend/.env y reinicia el servidor.",
            )
        if status == 404:
            return _err(
                502,
                "Gemini no encontró el modelo configurado. Verifica GEMINI_MODEL "
                "en backend/.env.",
            )
        if status == 400:
            return _err(
                502,
                "Gemini rechazó la solicitud. Verifica que la clave tenga acceso a Gemini API "
                "y que GEMINI_MODEL sea un modelo disponible.",
            )
        return _err(502, f"Gemini rechazó la solicitud (HTTP {status})")
    if status in (401, 403):
        return _err(
            503,
            "Supabase rechazó la autenticación. Verifica que SUPABASE_SECRET_KEY sea "
            "una clave secreta vigente del mismo proyecto indicado en SUPABASE_URL.",
        )
    if status == 409:
        return _err(409, "Supabase rechazó el cambio por una restricción de datos")
    try:
        payload = e.response.json()
    except ValueError:
        payload = {}
    if (
        payload.get("code") == "PGRST202"
        and e.request.url.path.endswith("/rpc/actualizar_plan_completo")
    ):
        return _err(
            503,
            "Supabase aún no tiene habilitada la edición completa del itinerario. "
            "Ejecuta backend/sql/007_edicion_completa_planes.sql en el SQL Editor "
            "de Supabase y vuelve a intentar.",
        )
    if payload.get("code") == "42703":
        return _err(
            503,
            "La base de datos no tiene el esquema requerido para editar planes. "
            "Ejecuta backend/sql/007_edicion_completa_planes.sql en el SQL Editor "
            "de Supabase y vuelve a intentar.",
        )
    if payload.get("code") == "P0001":
        return _err(422, payload.get("message", "La base de datos rechazó los cambios del plan"))
    if payload.get("code") in {"PGRST202", "PGRST205"}:
        return _err(
            503,
            "La base de datos de Supabase no tiene el esquema de Althea. "
            "Ejecuta las migraciones SQL del proyecto en orden.",
        )
    return _err(502, f"Supabase rechazó la solicitud (HTTP {status})")


@app.exception_handler(httpx.HTTPError)
async def _502(_: Request, e): return _err(502, "No se pudo conectar con Supabase o con otro servicio externo")
