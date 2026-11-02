BEGIN;

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
    v_destino_actual uuid;
BEGIN
    SELECT id_destino INTO v_destino_actual
    FROM public.plan_turistico
    WHERE id = p_id_plan
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Plan no encontrado';
    END IF;
    IF btrim(p_titulo) = '' THEN
        RAISE EXCEPTION 'El título del plan es obligatorio';
    END IF;

    FOR v_item IN SELECT value FROM jsonb_array_elements(COALESCE(p_items, '[]'::jsonb))
    LOOP
        v_tipo := (v_item->>'tipo_recurso')::tipo_recurso;
        v_recurso_id := (v_item->>'id_recurso')::uuid;

        IF p_id_destino IS NOT NULL AND v_tipo = 'ALOJAMIENTO'
           AND NOT EXISTS (
               SELECT 1 FROM public.alojamiento
               WHERE id = v_recurso_id AND id_destino = p_id_destino
           )
           AND NOT (
               p_id_destino IS NOT DISTINCT FROM v_destino_actual
               AND EXISTS (
                   SELECT 1 FROM public.item_itinerario
                   WHERE id = NULLIF(v_item->>'id', '')::uuid
                     AND id_plan = p_id_plan
                     AND tipo_recurso = v_tipo
                     AND id_alojamiento = v_recurso_id
               )
           ) THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001',
                MESSAGE = 'El alojamiento seleccionado no pertenece al destino del plan.';
        END IF;
        IF p_id_destino IS NOT NULL AND v_tipo = 'ACTIVIDAD'
           AND NOT EXISTS (
               SELECT 1 FROM public.actividad
               WHERE id = v_recurso_id AND id_destino = p_id_destino
           )
           AND NOT (
               p_id_destino IS NOT DISTINCT FROM v_destino_actual
               AND EXISTS (
                   SELECT 1 FROM public.item_itinerario
                   WHERE id = NULLIF(v_item->>'id', '')::uuid
                     AND id_plan = p_id_plan
                     AND tipo_recurso = v_tipo
                     AND id_actividad = v_recurso_id
               )
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
           )
           AND NOT (
               p_id_destino IS NOT DISTINCT FROM v_destino_actual
               AND EXISTS (
                   SELECT 1 FROM public.item_itinerario
                   WHERE id = NULLIF(v_item->>'id', '')::uuid
                     AND id_plan = p_id_plan
                     AND tipo_recurso = v_tipo
                     AND id_transporte = v_recurso_id
               )
           ) THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001',
                MESSAGE = 'El transporte seleccionado no está asociado al destino del plan.';
        END IF;
    END LOOP;

    UPDATE public.plan_turistico
    SET titulo = btrim(p_titulo),
        cantidad_viajeros = p_cantidad_viajeros,
        id_destino = p_id_destino
    WHERE id = p_id_plan;

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

GRANT EXECUTE ON FUNCTION public.actualizar_plan_completo(uuid, text, smallint, uuid, jsonb)
TO service_role;

NOTIFY pgrst, 'reload schema';

COMMIT;
