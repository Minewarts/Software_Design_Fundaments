BEGIN;

ALTER TABLE public.plan_turistico
    ADD COLUMN IF NOT EXISTS duracion_dias SMALLINT;

UPDATE public.plan_turistico p
SET duracion_dias = GREATEST(
    COALESCE((
        SELECT MAX(i.numero_dia)
        FROM public.item_itinerario i
        WHERE i.id_plan = p.id
    ), 1),
    1
)
WHERE p.duracion_dias IS NULL;

ALTER TABLE public.plan_turistico
    ALTER COLUMN duracion_dias SET DEFAULT 1,
    ALTER COLUMN duracion_dias SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_plan_duracion_dias_positive'
          AND conrelid = 'public.plan_turistico'::regclass
    ) THEN
        ALTER TABLE public.plan_turistico
            ADD CONSTRAINT ck_plan_duracion_dias_positive
            CHECK (duracion_dias >= 1);
    END IF;
END;
$$;

CREATE OR REPLACE VIEW public.plan_items_detalle
WITH (security_invoker = true) AS
SELECT i.id,
       i.id_plan,
       i.numero_dia,
       i.orden,
       i.tipo_recurso::text AS tipo_recurso,
       i.id_recurso_asociado AS id_recurso,
       COALESCE(a.nombre, ac.nombre, t.tipo_vehiculo) AS nombre,
       COALESCE(d.nombre, destinos_transporte.nombres) AS destino
FROM public.item_itinerario i
LEFT JOIN public.alojamiento a ON a.id = i.id_alojamiento
LEFT JOIN public.actividad ac ON ac.id = i.id_actividad
LEFT JOIN public.transporte t ON t.id = i.id_transporte
LEFT JOIN public.destino d ON d.id = COALESCE(a.id_destino, ac.id_destino)
LEFT JOIN LATERAL (
    SELECT string_agg(destino.nombre, ' / ' ORDER BY destino.nombre) AS nombres
    FROM public.destino_transporte dt
    JOIN public.destino destino ON destino.id = dt.id_destino
    WHERE dt.id_transporte = i.id_transporte
) destinos_transporte ON true;

CREATE OR REPLACE VIEW public.plan_directorio
WITH (security_invoker = true) AS
SELECT p.id,
       p.titulo,
       p.estado::text AS estado,
       p.costo_estimado,
       p.cantidad_viajeros,
       GREATEST(p.duracion_dias, COALESCE(duracion.duracion, 1))::smallint AS duracion,
       COALESCE(p.id_destino, destino_recurso.id) AS id_destino,
       COALESCE(destino_directo.nombre, destino_recurso.nombre) AS destino,
       valoracion.calificacion,
       ARRAY(
           SELECT libre.numero_dia::smallint
           FROM generate_series(
               1,
               GREATEST(p.duracion_dias, COALESCE(duracion.duracion, 1))
           ) AS libre(numero_dia)
           WHERE NOT EXISTS (
               SELECT 1
               FROM public.item_itinerario i
               WHERE i.id_plan = p.id
                 AND i.numero_dia = libre.numero_dia
           )
       ) AS dias_libres
FROM public.plan_turistico p
LEFT JOIN public.destino destino_directo ON destino_directo.id = p.id_destino
LEFT JOIN LATERAL (
    SELECT MAX(i.numero_dia) AS duracion
    FROM public.item_itinerario i
    WHERE i.id_plan = p.id
) duracion ON true
LEFT JOIN LATERAL (
    SELECT d.id, d.nombre
    FROM public.item_itinerario i
    LEFT JOIN public.alojamiento a ON a.id = i.id_alojamiento
    LEFT JOIN public.actividad ac ON ac.id = i.id_actividad
    LEFT JOIN public.destino d ON d.id = COALESCE(a.id_destino, ac.id_destino)
    WHERE i.id_plan = p.id
      AND d.id IS NOT NULL
    ORDER BY i.numero_dia, i.orden
    LIMIT 1
) destino_recurso ON true
LEFT JOIN LATERAL (
    SELECT ROUND(AVG(v.puntuacion), 1) AS calificacion
    FROM public.valoracion v
    WHERE v.id_plan = p.id
) valoracion ON true;

CREATE OR REPLACE FUNCTION public.crear_plan_con_items(p_plan jsonb, p_items jsonb)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_plan_id uuid := (p_plan->>'id')::uuid;
    v_item jsonb;
    v_tipo tipo_recurso;
    v_recurso_id uuid;
BEGIN
    INSERT INTO public.plan_turistico
        (id, titulo, estado, costo_estimado, cantidad_viajeros, id_destino, duracion_dias)
    VALUES
        (v_plan_id, p_plan->>'titulo', (p_plan->>'estado')::estado_plan,
         (p_plan->>'costo_estimado')::numeric,
         (p_plan->>'cantidad_viajeros')::smallint,
         NULLIF(p_plan->>'id_destino', '')::uuid,
         COALESCE(NULLIF(p_plan->>'duracion_dias', '')::smallint, 1));

    FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(p_items, '[]'::jsonb))
    LOOP
        v_tipo := (v_item->>'tipo_recurso')::tipo_recurso;
        v_recurso_id := (v_item->>'id_recurso')::uuid;
        INSERT INTO public.item_itinerario
            (id, id_plan, numero_dia, orden, tipo_recurso,
             id_alojamiento, id_actividad, id_transporte)
        VALUES
            ((v_item->>'id')::uuid, v_plan_id,
             (v_item->>'numero_dia')::smallint, (v_item->>'orden')::smallint, v_tipo,
             CASE WHEN v_tipo = 'ALOJAMIENTO' THEN v_recurso_id END,
             CASE WHEN v_tipo = 'ACTIVIDAD' THEN v_recurso_id END,
             CASE WHEN v_tipo = 'TRANSPORTE' THEN v_recurso_id END);
    END LOOP;

    RETURN v_plan_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.duplicar_plan(p_id_plan uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_nuevo_id uuid;
BEGIN
    INSERT INTO public.plan_turistico
        (titulo, estado, costo_estimado, cantidad_viajeros, id_destino, duracion_dias)
    SELECT 'Copia de ' || titulo, 'BORRADOR', costo_estimado,
           cantidad_viajeros, id_destino, duracion_dias
    FROM public.plan_turistico
    WHERE id = p_id_plan
    RETURNING id INTO v_nuevo_id;

    IF v_nuevo_id IS NULL THEN
        RAISE EXCEPTION 'Plan no encontrado';
    END IF;

    INSERT INTO public.item_itinerario
        (id_plan, numero_dia, orden, tipo_recurso,
         id_alojamiento, id_actividad, id_transporte)
    SELECT v_nuevo_id, numero_dia, orden, tipo_recurso,
           id_alojamiento, id_actividad, id_transporte
    FROM public.item_itinerario
    WHERE id_plan = p_id_plan;

    RETURN v_nuevo_id;
END;
$$;

NOTIFY pgrst, 'reload schema';

COMMIT;
