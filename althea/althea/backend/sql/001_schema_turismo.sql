-- 001_schema_turismo.sql — PostgreSQL / Supabase
-- Módulo: Diseñador Inteligente de Planes Turísticos

BEGIN;

CREATE TYPE tipo_recurso   AS ENUM ('ALOJAMIENTO', 'ACTIVIDAD', 'TRANSPORTE');
CREATE TYPE estado_plan    AS ENUM ('BORRADOR', 'APROBADO', 'EXPORTADO', 'ARCHIVADO');

-- ───────────── Catálogo de recursos ─────────────
CREATE TABLE destino (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre          VARCHAR(150) NOT NULL,
    ubicacion       VARCHAR(255) NOT NULL,
    clima_promedio  VARCHAR(100) NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_destino_nombre_ubicacion UNIQUE (nombre, ubicacion)
);

CREATE TABLE alojamiento (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_destino           UUID         NOT NULL REFERENCES destino(id) ON DELETE RESTRICT,
    nombre               VARCHAR(150) NOT NULL,
    categoria_estrellas  SMALLINT     NOT NULL CHECK (categoria_estrellas BETWEEN 1 AND 5),
    tarifa_noche         NUMERIC(12,2) NOT NULL CHECK (tarifa_noche >= 0),
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE actividad (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_destino      UUID         NOT NULL REFERENCES destino(id) ON DELETE RESTRICT,
    nombre          VARCHAR(150) NOT NULL,
    tipo_actividad  VARCHAR(80)  NOT NULL,
    costo_persona   NUMERIC(12,2) NOT NULL CHECK (costo_persona >= 0),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE transporte (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo_vehiculo    VARCHAR(80)  NOT NULL,
    tarifa_estimada  NUMERIC(12,2) NOT NULL CHECK (tarifa_estimada >= 0),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ───────────── Plan e itinerario ─────────────
CREATE TABLE plan_turistico (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    titulo           VARCHAR(200)  NOT NULL,
    estado           estado_plan   NOT NULL DEFAULT 'BORRADOR',
    costo_estimado   NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (costo_estimado >= 0),
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- Referencia polimórfica con integridad real: una FK por tipo de recurso,
-- y un CHECK que obliga a que exista exactamente una, coherente con tipo_recurso.
CREATE TABLE item_itinerario (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_plan         UUID          NOT NULL REFERENCES plan_turistico(id) ON DELETE CASCADE,
    numero_dia      SMALLINT      NOT NULL CHECK (numero_dia >= 1),
    orden           SMALLINT      NOT NULL DEFAULT 1 CHECK (orden >= 1),
    tipo_recurso    tipo_recurso  NOT NULL,

    id_alojamiento  UUID REFERENCES alojamiento(id) ON DELETE RESTRICT,
    id_actividad    UUID REFERENCES actividad(id)   ON DELETE RESTRICT,
    id_transporte   UUID REFERENCES transporte(id)  ON DELETE RESTRICT,

    -- id_recurso_asociado: columna derivada, expone el ID genérico al dominio.
    id_recurso_asociado UUID GENERATED ALWAYS AS
        (COALESCE(id_alojamiento, id_actividad, id_transporte)) STORED,

    CONSTRAINT ck_item_un_solo_recurso CHECK (
        num_nonnulls(id_alojamiento, id_actividad, id_transporte) = 1
    ),
    CONSTRAINT ck_item_tipo_coherente CHECK (
        (tipo_recurso = 'ALOJAMIENTO' AND id_alojamiento IS NOT NULL) OR
        (tipo_recurso = 'ACTIVIDAD'   AND id_actividad   IS NOT NULL) OR
        (tipo_recurso = 'TRANSPORTE'  AND id_transporte  IS NOT NULL)
    ),
    CONSTRAINT uq_item_posicion UNIQUE (id_plan, numero_dia, orden)
);

-- ───────────── Índices ─────────────
CREATE INDEX ix_alojamiento_destino_tarifa ON alojamiento (id_destino, tarifa_noche);
CREATE INDEX ix_actividad_destino_costo    ON actividad   (id_destino, costo_persona);
CREATE INDEX ix_actividad_tipo             ON actividad   (tipo_actividad);
CREATE INDEX ix_item_plan_dia              ON item_itinerario (id_plan, numero_dia, orden);
CREATE INDEX ix_item_alojamiento           ON item_itinerario (id_alojamiento) WHERE id_alojamiento IS NOT NULL;
CREATE INDEX ix_item_actividad             ON item_itinerario (id_actividad)   WHERE id_actividad   IS NOT NULL;
CREATE INDEX ix_item_transporte            ON item_itinerario (id_transporte)  WHERE id_transporte  IS NOT NULL;

-- ───────────── updated_at automático ─────────────
CREATE OR REPLACE FUNCTION fn_set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_plan_updated_at
BEFORE UPDATE ON plan_turistico
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

COMMIT;
