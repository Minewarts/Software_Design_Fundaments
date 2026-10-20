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
async def _supabase_error(_: Request, e: httpx.HTTPStatusError):
    if e.response.status_code == 409:
        return _err(409, "Supabase rechazó el cambio por una restricción de datos")
    return _err(502, f"Supabase rechazó la solicitud (HTTP {e.response.status_code})")
@app.exception_handler(httpx.HTTPError)
async def _502(_: Request, e): return _err(502, "No se pudo conectar con Supabase o con otro servicio externo")
