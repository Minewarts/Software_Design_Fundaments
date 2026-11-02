BEGIN;

CREATE TABLE IF NOT EXISTS public.plan_destino (
    id_plan UUID NOT NULL REFERENCES public.plan_turistico(id) ON DELETE CASCADE,
    id_destino UUID NOT NULL REFERENCES public.destino(id) ON DELETE RESTRICT,
    orden SMALLINT NOT NULL CHECK (orden >= 1),
    PRIMARY KEY (id_plan, id_destino),
    UNIQUE (id_plan, orden)
);

INSERT INTO public.plan_destino (id_plan, id_destino, orden)
SELECT id, id_destino, 1
FROM public.plan_turistico
WHERE id_destino IS NOT NULL
ON CONFLICT (id_plan, id_destino) DO NOTHING;

WITH destinos_recursos AS (
    SELECT i.id_plan,
           COALESCE(a.id_destino, ac.id_destino) AS id_destino,
           MIN(i.numero_dia * 32768 + i.orden) AS primera_posicion
    FROM public.item_itinerario i
    LEFT JOIN public.alojamiento a ON a.id = i.id_alojamiento
    LEFT JOIN public.actividad ac ON ac.id = i.id_actividad
    WHERE COALESCE(a.id_destino, ac.id_destino) IS NOT NULL
    GROUP BY i.id_plan, COALESCE(a.id_destino, ac.id_destino)
), maximo_orden AS (
    SELECT id_plan, MAX(orden) AS orden
    FROM public.plan_destino
    GROUP BY id_plan
), destinos_pendientes AS (
    SELECT dr.id_plan, dr.id_destino, dr.primera_posicion,
           COALESCE(mo.orden, 0) AS orden_actual
    FROM destinos_recursos dr
    LEFT JOIN public.plan_destino pd
      ON pd.id_plan = dr.id_plan AND pd.id_destino = dr.id_destino
    LEFT JOIN maximo_orden mo ON mo.id_plan = dr.id_plan
    WHERE pd.id_destino IS NULL
), destinos_ordenados AS (
    SELECT id_plan, id_destino, orden_actual,
           ROW_NUMBER() OVER (
               PARTITION BY id_plan ORDER BY primera_posicion, id_destino
           ) AS siguiente_orden
    FROM destinos_pendientes
)
INSERT INTO public.plan_destino (id_plan, id_destino, orden)
SELECT id_plan, id_destino, (orden_actual + siguiente_orden)::smallint
FROM destinos_ordenados;

DROP FUNCTION IF EXISTS public.actualizar_plan_completo(uuid, text, smallint, uuid, jsonb);

CREATE OR REPLACE FUNCTION public.actualizar_plan_completo(
    p_id_plan uuid,
    p_titulo text,
    p_cantidad_viajeros smallint,
    p_id_destinos uuid[],
    p_items jsonb
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_item jsonb;
    v_tipo tipo_recurso;
    v_recurso_id uuid;
    v_recurso_destino uuid;
    v_destinos uuid[] := COALESCE(p_id_destinos, ARRAY[]::uuid[]);
    v_destinos_actuales uuid[];
    v_transporte_destinos uuid[];
    v_orden smallint;
    v_destino_sin_cambios boolean;
BEGIN
    PERFORM 1 FROM public.plan_turistico
    WHERE id = p_id_plan
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Plan no encontrado';
    END IF;
    IF btrim(p_titulo) = '' THEN
        RAISE EXCEPTION 'El título del plan es obligatorio';
    END IF;
    IF cardinality(v_destinos) <> (
        SELECT COUNT(DISTINCT id_destino)
        FROM unnest(v_destinos) AS selected(id_destino)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = 'P0001',
            MESSAGE = 'No repitas destinos en la ruta.';
    END IF;

    SELECT COALESCE(array_agg(id_destino ORDER BY orden), ARRAY[]::uuid[])
    INTO v_destinos_actuales
    FROM public.plan_destino
    WHERE id_plan = p_id_plan;
    v_destino_sin_cambios := v_destinos IS NOT DISTINCT FROM v_destinos_actuales;

    FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(p_items, '[]'::jsonb))
    LOOP
        v_tipo := (v_item->>'tipo_recurso')::tipo_recurso;
        v_recurso_id := (v_item->>'id_recurso')::uuid;

        IF v_tipo = 'ALOJAMIENTO' THEN
            SELECT id_destino INTO v_recurso_destino
            FROM public.alojamiento WHERE id = v_recurso_id;
        ELSIF v_tipo = 'ACTIVIDAD' THEN
            SELECT id_destino INTO v_recurso_destino
            FROM public.actividad WHERE id = v_recurso_id;
        ELSE
            SELECT COALESCE(array_agg(id_destino), ARRAY[]::uuid[])
            INTO v_transporte_destinos
            FROM public.destino_transporte
            WHERE id_transporte = v_recurso_id;

            IF NOT (v_transporte_destinos && v_destinos)
               AND NOT (
                   v_destino_sin_cambios
                   AND EXISTS (
                       SELECT 1 FROM public.item_itinerario
                       WHERE id = NULLIF(v_item->>'id', '')::uuid
                         AND id_plan = p_id_plan
                         AND tipo_recurso = v_tipo
                         AND id_transporte = v_recurso_id
                   )
               ) THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001',
                    MESSAGE = 'El transporte debe estar asociado a uno de los destinos seleccionados.';
            END IF;
            CONTINUE;
        END IF;

        IF v_recurso_destino IS NULL THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001',
                MESSAGE = 'No se encontró el recurso seleccionado.';
        END IF;

        IF NOT v_recurso_destino = ANY(v_destinos)
           AND NOT (
               v_destino_sin_cambios
               AND EXISTS (
                   SELECT 1 FROM public.item_itinerario
                   WHERE id = NULLIF(v_item->>'id', '')::uuid
                     AND id_plan = p_id_plan
                     AND tipo_recurso = v_tipo
                     AND id_recurso_asociado = v_recurso_id
               )
           ) THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001',
                MESSAGE = 'El recurso debe pertenecer a uno de los destinos seleccionados.';
        END IF;
    END LOOP;

    UPDATE public.plan_turistico
    SET titulo = btrim(p_titulo),
        cantidad_viajeros = p_cantidad_viajeros,
        id_destino = v_destinos[1]
    WHERE id = p_id_plan;

    DELETE FROM public.plan_destino WHERE id_plan = p_id_plan;
    INSERT INTO public.plan_destino (id_plan, id_destino, orden)
    SELECT p_id_plan, destino.id_destino, destino.orden::smallint
    FROM unnest(v_destinos) WITH ORDINALITY AS destino(id_destino, orden);

    DELETE FROM public.item_itinerario WHERE id_plan = p_id_plan;

    FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(p_items, '[]'::jsonb))
    LOOP
        v_tipo := (v_item->>'tipo_recurso')::tipo_recurso;
        v_recurso_id := (v_item->>'id_recurso')::uuid;

        SELECT COALESCE(MAX(i.orden), 0) + 1
        INTO v_orden
        FROM public.item_itinerario i
        WHERE i.id_plan = p_id_plan
          AND i.numero_dia = (v_item->>'numero_dia')::smallint;

        INSERT INTO public.item_itinerario
            (id_plan, numero_dia, orden, tipo_recurso,
             id_alojamiento, id_actividad, id_transporte)
        VALUES
            (p_id_plan, (v_item->>'numero_dia')::smallint, v_orden, v_tipo,
             CASE WHEN v_tipo = 'ALOJAMIENTO' THEN v_recurso_id END,
             CASE WHEN v_tipo = 'ACTIVIDAD' THEN v_recurso_id END,
             CASE WHEN v_tipo = 'TRANSPORTE' THEN v_recurso_id END);
    END LOOP;

    PERFORM public.recalcular_costo_plan(p_id_plan);
END;
$$;

GRANT EXECUTE ON FUNCTION public.actualizar_plan_completo(uuid, text, smallint, uuid[], jsonb)
TO service_role;

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
    v_destinos jsonb := COALESCE(p_plan->'id_destinos', '[]'::jsonb);
BEGIN
    IF jsonb_array_length(v_destinos) = 0 AND p_plan->>'id_destino' IS NOT NULL THEN
        v_destinos := jsonb_build_array(p_plan->>'id_destino');
    END IF;

    INSERT INTO public.plan_turistico
        (id, titulo, estado, costo_estimado, cantidad_viajeros, id_destino, duracion_dias)
    VALUES
        (v_plan_id, p_plan->>'titulo', (p_plan->>'estado')::estado_plan,
         (p_plan->>'costo_estimado')::numeric,
         (p_plan->>'cantidad_viajeros')::smallint,
         NULLIF(p_plan->>'id_destino', '')::uuid,
         COALESCE(NULLIF(p_plan->>'duracion_dias', '')::smallint, 1));

    INSERT INTO public.plan_destino (id_plan, id_destino, orden)
    SELECT v_plan_id, selected.id_destino::uuid, selected.orden::smallint
    FROM jsonb_array_elements_text(v_destinos) WITH ORDINALITY
         AS selected(id_destino, orden);

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

    INSERT INTO public.plan_destino (id_plan, id_destino, orden)
    SELECT v_nuevo_id, id_destino, orden
    FROM public.plan_destino
    WHERE id_plan = p_id_plan;

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
       ) AS dias_libres,
       COALESCE((
           SELECT jsonb_agg(
               jsonb_build_object('id', destino.id, 'nombre', destino.nombre)
               ORDER BY pd.orden
           )
           FROM public.plan_destino pd
           JOIN public.destino destino ON destino.id = pd.id_destino
           WHERE pd.id_plan = p.id
       ), '[]'::jsonb) AS destinos
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

NOTIFY pgrst, 'reload schema';

COMMIT;
