-- Add the traveler count used for plan cost calculations and duplication.
BEGIN;
ALTER TABLE plan_turistico ADD COLUMN cantidad_viajeros SMALLINT NOT NULL DEFAULT 1 CHECK (cantidad_viajeros >= 1);
COMMIT;
