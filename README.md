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
3. `althea/althea/backend/sql/003_release2.sql`
4. `althea/althea/backend/sql/004_supabase_rest_api.sql`
5. `althea/althea/backend/sql/005_remove_notifications.sql`
6. Opcionalmente, `althea/althea/backend/sql/006_datos_ejemplo.sql` para insertar destinos y recursos de demostración.
7. `althea/althea/backend/sql/007_edicion_completa_planes.sql`
8. `althea/althea/backend/sql/008_conservar_recursos_existentes_plan.sql` para poder editar planes con recursos históricos que no corresponden al destino actual sin impedir cambios en sus otros campos.
9. `althea/althea/backend/sql/009_duracion_dias_libres.sql` para conservar la duración del viaje aunque la IA deje días sin recursos programados.
10. `althea/althea/backend/sql/010_edicion_multidestino.sql` para guardar el orden de destinos y poder añadir destinos al modificar un itinerario.

En el generador de IA, selecciona los destinos en el orden de visita. El sistema
filtra los recursos por esos destinos, valida los traslados al cambiar de ciudad
y conserva los días libres sin crear actividades ficticias.

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
