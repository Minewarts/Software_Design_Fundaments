# Althea

Aplicación web para consultar un catálogo de recursos turísticos, diseñar planes y ver sus fichas. El frontend está hecho con Vue 3 y Vite; la estructura del backend está preparada para FastAPI y PostgreSQL.

## Requisitos

- Node.js 20 o posterior y npm.
- Python 3.11 o posterior, solo para instalar las dependencias previstas del backend.
- PostgreSQL o un proyecto Supabase, solo cuando se implemente y conecte el backend.
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

El frontend usa `VITE_API_URL` para encontrar la API. El valor de ejemplo es `http://localhost:8000/api`; cambia esa variable en `althea/althea/frontend/.env` si tu API está en otra dirección. Vite lee las variables al iniciar, por lo que hay que reiniciar el servidor después de modificarlas.

## Estado del backend y la base de datos

El backend aún no se puede iniciar: `althea/althea/backend/app/main.py` está vacío y todavía no define la aplicación FastAPI ni sus endpoints. Por eso, las vistas que consultan datos de la API no tendrán funcionalidad de datos hasta implementar y ejecutar ese servicio. Las dependencias previstas están listadas en `althea/althea/backend/requirements.txt`.

Cuando se implemente el backend, se necesitará Python 3.11 o posterior. Desde la raíz del repositorio, las dependencias se instalan con:

```bash
cd althea/althea/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

La base de datos requiere PostgreSQL compatible con las migraciones del proyecto. Ejecuta los scripts SQL en orden sobre la base de datos:

1. `althea/althea/backend/sql/001_schema_turismo.sql`
2. `althea/althea/backend/sql/002_release1_extras.sql`

Configura las credenciales de base de datos en el backend cuando se incorpore su configuración; actualmente no hay archivo `.env` ni variables de conexión implementadas. Tampoco hay todavía un comando funcional para arrancar la API.

## Compilar el frontend

```bash
cd althea/althea/frontend
npm run build
```
