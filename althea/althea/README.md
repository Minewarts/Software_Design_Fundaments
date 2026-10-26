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
5. `backend/sql/005_remove_notifications.sql`

Para poblar el catálogo con destinos, alojamientos, actividades y transportes
de demostración, ejecuta también `backend/sql/006_datos_ejemplo.sql`. Sus
registros se pueden insertar más de una vez sin duplicar los mismos ejemplos;
los precios son ilustrativos y están expresados en pesos colombianos.

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
Confirma que `SUPABASE_URL` apunte a tu proyecto. `GEMINI_API_KEY` es opcional
para iniciar la app, pero se necesita para generar itinerarios y traducir
fichas. El modelo predeterminado es `gemini-3.5-flash`; puedes cambiarlo con
`GEMINI_MODEL` si tu clave tiene acceso a otro modelo.

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

La navegación permite consultar actividades por destino, nombre y tipo. El
clima actual del destino se consulta automáticamente desde Open-Meteo al abrir
la ficha de un plan; no es necesario introducir un mes ni un clima promedio.
Al crear o cambiar la ubicación de un destino, el catálogo también obtiene
automáticamente la temperatura actual para completar el campo heredado de clima.

## Tests
Desde `backend/`:

```powershell
$env:PYTHONPATH = "."
python -m pytest tests/unit
```
