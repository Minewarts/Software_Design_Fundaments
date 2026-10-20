-- HU-09/14: viajeros por plan (recalcular costo y duplicar).  HU-16: notificaciones in-app.
BEGIN;
ALTER TABLE plan_turistico ADD COLUMN cantidad_viajeros SMALLINT NOT NULL DEFAULT 1 CHECK (cantidad_viajeros >= 1);
CREATE TABLE notificacion (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_plan    UUID NOT NULL REFERENCES plan_turistico(id) ON DELETE CASCADE,
    mensaje    TEXT NOT NULL,
    leida      BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_notificacion_leida ON notificacion (leida, created_at DESC);
COMMIT;
