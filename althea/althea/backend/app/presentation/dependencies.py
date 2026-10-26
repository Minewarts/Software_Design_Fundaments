"""Composición de dependencias (inyección manual)."""
from app.application.use_cases.crear_recurso_turistico import CrearRecursoTuristico
from app.application.use_cases.exportar_plan_ficha import ExportarPlanFicha
from app.application.use_cases.generar_itinerario_inteligente import GenerarItinerarioInteligente
from app.application.use_cases.gestionar_planes import GestionarPlanes
from app.application.use_cases.servicios_externos import ConsultarClimaHistorico, TraducirTextos
from app.infrastructure.ai.gemini_client import GeminiClient
from app.infrastructure.ai.llm_servicio_ia import GeminiTraductor, LLMServicioIA
from app.infrastructure.config.settings import settings
from app.infrastructure.export.pdf_exportador import PdfExportador
from app.infrastructure.persistence.supabase_plan_repository import SupabasePlanRepository
from app.infrastructure.persistence.supabase_recurso_repository import CatalogoAdmin, SupabaseRecursoRepository
from app.infrastructure.weather_open_meteo import OpenMeteoClima

_recursos, _planes = SupabaseRecursoRepository(), SupabasePlanRepository()
_gemini = GeminiClient(settings.gemini_api_key, settings.gemini_model)

admin = CatalogoAdmin()
crear_recurso = CrearRecursoTuristico(_recursos)
generar = GenerarItinerarioInteligente(_recursos, _planes, LLMServicioIA(_gemini))
gestionar = GestionarPlanes(_planes)
exportar = ExportarPlanFicha(_planes, PdfExportador())
clima = ConsultarClimaHistorico(_recursos, OpenMeteoClima())
traducir = TraducirTextos(GeminiTraductor(_gemini))
