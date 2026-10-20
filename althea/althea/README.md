# Althea – Planes Turísticos

## Requisitos
- Python 3.10 o posterior
- Node.js y npm
- Un proyecto de Supabase

## Configurar Supabase
FastAPI usa la API REST de Supabase con `SUPABASE_URL` y una
clave secreta almacenada únicamente en `backend/.env`. No configures esa clave
en el frontend ni la compartas en el repositorio. Si una clave secreta se
expuso, revócala y crea otra antes de iniciar el servidor.

Desde el **SQL Editor** del proyecto, ejecuta en este orden:
1. `backend/sql/001_schema_turismo.sql`
2. `backend/sql/002_release1_extras.sql`
3. `backend/sql/003_release2.sql`
4. `backend/sql/004_supabase_rest_api.sql`

## Backend (FastAPI)
En PowerShell, desde `althea/althea`:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `backend/.env` y pega una clave secreta vigente en `SUPABASE_SECRET_KEY`.
`SUPABASE_URL` ya está configurada en el ejemplo. `ANTHROPIC_API_KEY` es
opcional para iniciar la app, pero se necesita para generar itinerarios y
traducir fichas.

Inicia el backend desde `backend/`:

```powershell
uvicorn app.main:app --reload
```

Documentación de la API: http://localhost:8000/docs

## Frontend (Vue 3 + Vite)
En otra terminal PowerShell, desde `althea/althea`:

```powershell
cd frontend
npm install
npm run dev
```

Abre http://localhost:5173. El frontend usa `http://localhost:8000/api` por
defecto; si cambias el backend, define `VITE_API_URL` en `frontend/.env`.

## Tests
Desde `backend/`:

```powershell
$env:PYTHONPATH = "."
python -m pytest tests/unit
```
