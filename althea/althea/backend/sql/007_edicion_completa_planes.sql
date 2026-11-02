-- Persist the plan destination and replace the entire itinerary atomically.
BEGIN;

ALTER TABLE public.plan_turistico
    ADD COLUMN IF NOT EXISTS id_destino UUID REFERENCES public.destino(id) ON DELETE SET NULL;

ALTER TABLE public.plan_turistico
    ADD COLUMN IF NOT EXISTS cantidad_viajeros SMALLINT NOT NULL DEFAULT 1
    CHECK (cantidad_viajeros >= 1);

UPDATE public.plan_turistico p
SET id_destino = (
    SELECT COALESCE(a.id_destino, ac.id_destino)
    FROM public.item_itinerario i
    LEFT JOIN public.alojamiento a ON a.id = i.id_alojamiento
    LEFT JOIN public.actividad ac ON ac.id = i.id_actividad
    WHERE i.id_plan = p.id
      AND COALESCE(a.id_destino, ac.id_destino) IS NOT NULL
    ORDER BY i.numero_dia, i.orden
    LIMIT 1
)
WHERE p.id_destino IS NULL;

CREATE OR REPLACE VIEW public.plan_directorio
WITH (security_invoker = true) AS
SELECT p.id,
       p.titulo,
       p.estado::text AS estado,
       p.costo_estimado,
       p.cantidad_viajeros,
       duracion.duracion,
       COALESCE(p.id_destino, destino_recurso.id) AS id_destino,
       COALESCE(destino_directo.nombre, destino_recurso.nombre) AS destino,
       valoracion.calificacion
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
        (id, titulo, estado, costo_estimado, cantidad_viajeros, id_destino)
    VALUES
        (v_plan_id, p_plan->>'titulo', (p_plan->>'estado')::estado_plan,
         (p_plan->>'costo_estimado')::numeric,
         (p_plan->>'cantidad_viajeros')::smallint,
         NULLIF(p_plan->>'id_destino', '')::uuid);

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
        (titulo, estado, costo_estimado, cantidad_viajeros, id_destino)
    SELECT 'Copia de ' || titulo, 'BORRADOR', costo_estimado, cantidad_viajeros, id_destino
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

CREATE OR REPLACE FUNCTION public.actualizar_plan_completo(
    p_id_plan uuid,
    p_titulo text,
    p_cantidad_viajeros smallint,
    p_id_destino uuid,
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
    v_orden smallint;
BEGIN
    UPDATE public.plan_turistico
    SET titulo = btrim(p_titulo),
        cantidad_viajeros = p_cantidad_viajeros,
        id_destino = p_id_destino
    WHERE id = p_id_plan;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Plan no encontrado';
    END IF;
    IF btrim(p_titulo) = '' THEN
        RAISE EXCEPTION 'El título del plan es obligatorio';
    END IF;

    DELETE FROM public.item_itinerario WHERE id_plan = p_id_plan;

    FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(p_items, '[]'::jsonb))
    LOOP
        v_tipo := (v_item->>'tipo_recurso')::tipo_recurso;
        v_recurso_id := (v_item->>'id_recurso')::uuid;

        IF p_id_destino IS NOT NULL AND v_tipo = 'ALOJAMIENTO'
           AND NOT EXISTS (
               SELECT 1 FROM public.alojamiento
               WHERE id = v_recurso_id AND id_destino = p_id_destino
           ) THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001',
                MESSAGE = 'El alojamiento seleccionado no pertenece al destino del plan.';
        END IF;
        IF p_id_destino IS NOT NULL AND v_tipo = 'ACTIVIDAD'
           AND NOT EXISTS (
               SELECT 1 FROM public.actividad
               WHERE id = v_recurso_id AND id_destino = p_id_destino
           ) THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001',
                MESSAGE = 'La actividad seleccionada no pertenece al destino del plan.';
        END IF;
        IF p_id_destino IS NOT NULL AND v_tipo = 'TRANSPORTE'
           AND EXISTS (
               SELECT 1 FROM public.destino_transporte
               WHERE id_transporte = v_recurso_id
           )
           AND NOT EXISTS (
               SELECT 1 FROM public.destino_transporte
               WHERE id_transporte = v_recurso_id AND id_destino = p_id_destino
           ) THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001',
                MESSAGE = 'El transporte seleccionado no está asociado al destino del plan.';
        END IF;

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

GRANT EXECUTE ON FUNCTION public.actualizar_plan_completo(uuid, text, smallint, uuid, jsonb)
TO service_role;

NOTIFY pgrst, 'reload schema';

COMMIT;
