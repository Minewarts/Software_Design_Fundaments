"""Configuración desde variables de entorno (.env). Ejecutar uvicorn desde backend/."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_secret_key: str = os.getenv("SUPABASE_SECRET_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.5-flash"
    cors_origins: tuple = tuple(os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","))


settings = Settings()
