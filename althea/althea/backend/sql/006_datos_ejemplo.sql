-- Add idempotent sample catalog data for local demonstrations.
-- Prices are illustrative values in Colombian pesos.
BEGIN;

DO $$
DECLARE
    cartagena_id UUID;
    medellin_id UUID;
    san_andres_id UUID;
BEGIN
    INSERT INTO destino (nombre, ubicacion, clima_promedio)
    VALUES
        ('Cartagena', 'Cartagena, Bolívar, Colombia', 'Consulta el clima actual en la ficha del plan'),
        ('Medellín', 'Medellín, Antioquia, Colombia', 'Consulta el clima actual en la ficha del plan'),
        ('San Andrés', 'San Andrés, Colombia', 'Consulta el clima actual en la ficha del plan')
    ON CONFLICT (nombre, ubicacion) DO NOTHING;

    SELECT id INTO cartagena_id
    FROM destino WHERE nombre = 'Cartagena' AND ubicacion = 'Cartagena, Bolívar, Colombia';
    SELECT id INTO medellin_id
    FROM destino WHERE nombre = 'Medellín' AND ubicacion = 'Medellín, Antioquia, Colombia';
    SELECT id INTO san_andres_id
    FROM destino WHERE nombre = 'San Andrés' AND ubicacion = 'San Andrés, Colombia';

    INSERT INTO alojamiento (id_destino, nombre, categoria_estrellas, tarifa_noche)
    SELECT sample.id_destino, sample.nombre, sample.estrellas, sample.tarifa
    FROM (VALUES
        (cartagena_id, 'Hospedaje Centro Histórico (demo)', 3, 180000::numeric),
        (cartagena_id, 'Hospedaje Bocagrande (demo)', 4, 320000::numeric),
        (medellin_id, 'Hospedaje Laureles (demo)', 3, 150000::numeric),
        (medellin_id, 'Hospedaje El Poblado (demo)', 4, 290000::numeric),
        (san_andres_id, 'Hospedaje Spratt Bight (demo)', 3, 210000::numeric),
        (san_andres_id, 'Hospedaje San Luis (demo)', 4, 280000::numeric)
    ) AS sample(id_destino, nombre, estrellas, tarifa)
    WHERE NOT EXISTS (
        SELECT 1 FROM alojamiento existing
        WHERE existing.id_destino = sample.id_destino AND existing.nombre = sample.nombre
    );

    INSERT INTO actividad (id_destino, nombre, tipo_actividad, costo_persona)
    SELECT sample.id_destino, sample.nombre, sample.tipo, sample.costo
    FROM (VALUES
        (cartagena_id, 'Recorrido por el centro histórico (demo)', 'Cultura', 65000::numeric),
        (cartagena_id, 'Paseo en kayak por la bahía (demo)', 'Aventura', 95000::numeric),
        (medellin_id, 'Recorrido guiado por la Comuna 13 (demo)', 'Cultura', 55000::numeric),
        (medellin_id, 'Caminata ecológica en Arví (demo)', 'Naturaleza', 70000::numeric),
        (san_andres_id, 'Snorkel en Johnny Cay (demo)', 'Acuática', 120000::numeric),
        (san_andres_id, 'Vuelta a la isla (demo)', 'Aventura', 85000::numeric)
    ) AS sample(id_destino, nombre, tipo, costo)
    WHERE NOT EXISTS (
        SELECT 1 FROM actividad existing
        WHERE existing.id_destino = sample.id_destino AND existing.nombre = sample.nombre
    );

    INSERT INTO transporte (tipo_vehiculo, tarifa_estimada)
    SELECT sample.tipo, sample.tarifa
    FROM (VALUES
        ('Van turística (demo)', 240000::numeric),
        ('Bus turístico (demo)', 90000::numeric),
        ('Lancha turística (demo)', 160000::numeric)
    ) AS sample(tipo, tarifa)
    WHERE NOT EXISTS (
        SELECT 1 FROM transporte existing
        WHERE existing.tipo_vehiculo = sample.tipo
    );

    INSERT INTO destino_transporte (id_destino, id_transporte)
    SELECT links.id_destino, transporte.id
    FROM (VALUES
        (cartagena_id, 'Van turística (demo)'),
        (cartagena_id, 'Bus turístico (demo)'),
        (medellin_id, 'Van turística (demo)'),
        (medellin_id, 'Bus turístico (demo)'),
        (san_andres_id, 'Van turística (demo)'),
        (san_andres_id, 'Lancha turística (demo)')
    ) AS links(id_destino, tipo_vehiculo)
    JOIN transporte ON transporte.tipo_vehiculo = links.tipo_vehiculo
    ON CONFLICT (id_destino, id_transporte) DO NOTHING;
END;
$$;

COMMIT;
