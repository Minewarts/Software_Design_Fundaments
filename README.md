# Althea

Aplicación web para consultar un catálogo de recursos turísticos, diseñar planes y ver sus fichas. Incluye un frontend Vue 3/Vite y una API FastAPI conectada a Supabase.

## Requisitos

- Node.js 20 o posterior y npm.
- Python 3.11 o posterior para el backend.
- Un proyecto Supabase con las migraciones del proyecto aplicadas.
- Git, para clonar el repositorio.

## Abrir el frontend

Desde la raíz del repositorio:

```bash
cd althea/althea/frontend
npm install
cp .env.example .env
npm run dev -- --host 0.0.0.0
```

Abre la dirección que Vite muestre en la terminal (normalmente `http://localhost:5173`). Para detener el servidor, pulsa `Ctrl+C` en esa terminal.

En desarrollo, el frontend usa `/api` y Vite reenvía esas solicitudes a `http://127.0.0.1:8000`, evitando problemas de `localhost` en Codespaces. Para otra API, configura `VITE_API_URL` en `althea/althea/frontend/.env` y reinicia Vite.

## Preparar Supabase y el backend

En el panel de Supabase, abre **SQL Editor** y ejecuta, en este orden, los scripts:

1. `althea/althea/backend/sql/001_schema_turismo.sql`
2. `althea/althea/backend/sql/002_release1_extras.sql`

La API usa `SUPABASE_URL` y `SUPABASE_SECRET_KEY` desde `althea/althea/backend/.env`. El archivo está excluido de Git. No pongas la clave secreta en variables `VITE_*` ni en el frontend. Si aún no tienes el archivo local, copia `.env.example` y completa los valores.

Desde la raíz del repositorio, instala y arranca el backend:

```bash
cd althea/althea/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La comprobación de la API está disponible en `http://localhost:8000/api/health`.

Mantén el backend ejecutándose en una terminal. En otra terminal, inicia el frontend con los comandos de la sección anterior; estará en `http://localhost:5173` y llamará a `http://localhost:8000/api` por defecto.

## Compilar el frontend

```bash
cd althea/althea/frontend
npm run build
```
