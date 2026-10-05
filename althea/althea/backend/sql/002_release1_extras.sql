-- HU-05: transporte <-> destino (N:M).  HU-17: valoraciones del plan.
BEGIN;
CREATE TABLE destino_transporte (
    id_destino    UUID NOT NULL REFERENCES destino(id)    ON DELETE CASCADE,
    id_transporte UUID NOT NULL REFERENCES transporte(id) ON DELETE CASCADE,
    PRIMARY KEY (id_destino, id_transporte)
);
CREATE TABLE valoracion (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_plan     UUID NOT NULL REFERENCES plan_turistico(id) ON DELETE CASCADE,
    autor       VARCHAR(120) NOT NULL,
    puntuacion  SMALLINT NOT NULL CHECK (puntuacion BETWEEN 1 AND 5),
    comentario  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_valoracion_plan ON valoracion (id_plan);
COMMIT;
