-- Operaciones y vistas necesarias para consumir los repositorios por PostgREST.
BEGIN;

CREATE OR REPLACE VIEW public.plan_items_detalle
WITH (security_invoker = true) AS
SELECT i.id,
       i.id_plan,
       i.numero_dia,
       i.orden,
       i.tipo_recurso::text AS tipo_recurso,
       i.id_recurso_asociado AS id_recurso,
       COALESCE(a.nombre, ac.nombre, t.tipo_vehiculo) AS nombre
FROM public.item_itinerario i
LEFT JOIN public.alojamiento a ON a.id = i.id_alojamiento
LEFT JOIN public.actividad ac ON ac.id = i.id_actividad
LEFT JOIN public.transporte t ON t.id = i.id_transporte;

CREATE OR REPLACE VIEW public.plan_directorio
WITH (security_invoker = true) AS
SELECT p.id,
       p.titulo,
       p.estado::text AS estado,
       p.costo_estimado,
       p.cantidad_viajeros,
       duracion.duracion,
       destino.id AS id_destino,
       destino.nombre AS destino,
       valoracion.calificacion
FROM public.plan_turistico p
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
    ORDER BY i.numero_dia, i.orden
    LIMIT 1
) destino ON true
LEFT JOIN LATERAL (
    SELECT ROUND(AVG(v.puntuacion), 1) AS calificacion
    FROM public.valoracion v
    WHERE v.id_plan = p.id
) valoracion ON true;

CREATE OR REPLACE VIEW public.notificaciones_detalle
WITH (security_invoker = true) AS
SELECT n.id, n.id_plan, p.titulo, n.mensaje, n.leida, n.created_at
FROM public.notificacion n
JOIN public.plan_turistico p ON p.id = n.id_plan;

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
        (id, titulo, estado, costo_estimado, cantidad_viajeros)
    VALUES
        (v_plan_id, p_plan->>'titulo', (p_plan->>'estado')::estado_plan,
         (p_plan->>'costo_estimado')::numeric, (p_plan->>'cantidad_viajeros')::smallint);

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
        (titulo, estado, costo_estimado, cantidad_viajeros)
    SELECT 'Copia de ' || titulo, 'BORRADOR', costo_estimado, cantidad_viajeros
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

CREATE OR REPLACE FUNCTION public.agregar_item_plan(
    p_id_plan uuid,
    p_numero_dia smallint,
    p_tipo_recurso tipo_recurso,
    p_id_recurso uuid
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_orden smallint;
    v_item_id uuid := gen_random_uuid();
BEGIN
    PERFORM 1 FROM public.plan_turistico WHERE id = p_id_plan FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Plan no encontrado';
    END IF;

    SELECT COALESCE(MAX(orden), 0) + 1
    INTO v_orden
    FROM public.item_itinerario
    WHERE id_plan = p_id_plan AND numero_dia = p_numero_dia;

    INSERT INTO public.item_itinerario
        (id, id_plan, numero_dia, orden, tipo_recurso,
         id_alojamiento, id_actividad, id_transporte)
    VALUES
        (v_item_id, p_id_plan, p_numero_dia, v_orden, p_tipo_recurso,
         CASE WHEN p_tipo_recurso = 'ALOJAMIENTO' THEN p_id_recurso END,
         CASE WHEN p_tipo_recurso = 'ACTIVIDAD' THEN p_id_recurso END,
         CASE WHEN p_tipo_recurso = 'TRANSPORTE' THEN p_id_recurso END);

    RETURN v_item_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.mover_item_plan(
    p_id_plan uuid,
    p_id_item uuid,
    p_numero_dia smallint
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_orden smallint;
BEGIN
    PERFORM 1 FROM public.plan_turistico WHERE id = p_id_plan FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Plan no encontrado';
    END IF;

    SELECT COALESCE(MAX(orden), 0) + 1
    INTO v_orden
    FROM public.item_itinerario
    WHERE id_plan = p_id_plan AND numero_dia = p_numero_dia;

    UPDATE public.item_itinerario
    SET numero_dia = p_numero_dia, orden = v_orden
    WHERE id = p_id_item AND id_plan = p_id_plan;
END;
$$;

CREATE OR REPLACE FUNCTION public.recalcular_costo_plan(p_id_plan uuid)
RETURNS void
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    UPDATE public.plan_turistico p
    SET costo_estimado =
        COALESCE((
            SELECT SUM(a.tarifa_noche)
            FROM public.alojamiento a
            WHERE a.id IN (
                SELECT i.id_alojamiento FROM public.item_itinerario i
                WHERE i.id_plan = p_id_plan AND i.id_alojamiento IS NOT NULL
            )
        ), 0)
        * GREATEST(COALESCE((
            SELECT MAX(i.numero_dia) - 1 FROM public.item_itinerario i
            WHERE i.id_plan = p_id_plan
        ), 1), 1)
        * CEIL(p.cantidad_viajeros / 2.0)
        + COALESCE((
            SELECT SUM(a.costo_persona)
            FROM public.item_itinerario i
            JOIN public.actividad a ON a.id = i.id_actividad
            WHERE i.id_plan = p_id_plan
        ), 0) * p.cantidad_viajeros
        + COALESCE((
            SELECT SUM(t.tarifa_estimada)
            FROM public.item_itinerario i
            JOIN public.transporte t ON t.id = i.id_transporte
            WHERE i.id_plan = p_id_plan
        ), 0)
    WHERE p.id = p_id_plan;
$$;

CREATE OR REPLACE FUNCTION public.sincronizar_transporte_destinos(
    p_id_transporte uuid,
    p_ids_destinos uuid[]
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    DELETE FROM public.destino_transporte WHERE id_transporte = p_id_transporte;
    INSERT INTO public.destino_transporte (id_transporte, id_destino)
    SELECT p_id_transporte, destino_id
    FROM unnest(COALESCE(p_ids_destinos, ARRAY[]::uuid[])) AS destinos(destino_id);
END;
$$;

GRANT USAGE ON SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON
    public.destino, public.alojamiento, public.actividad, public.transporte,
    public.plan_turistico, public.item_itinerario, public.destino_transporte,
    public.valoracion, public.notificacion
TO service_role;
GRANT SELECT ON
    public.plan_items_detalle, public.plan_directorio, public.notificaciones_detalle
TO service_role;
GRANT EXECUTE ON FUNCTION public.crear_plan_con_items(jsonb, jsonb),
    public.duplicar_plan(uuid),
    public.agregar_item_plan(uuid, smallint, tipo_recurso, uuid),
    public.mover_item_plan(uuid, uuid, smallint),
    public.recalcular_costo_plan(uuid),
    public.sincronizar_transporte_destinos(uuid, uuid[])
TO service_role;

REVOKE ALL ON FUNCTION public.crear_plan_con_items(jsonb, jsonb),
    public.duplicar_plan(uuid),
    public.agregar_item_plan(uuid, smallint, tipo_recurso, uuid),
    public.mover_item_plan(uuid, uuid, smallint),
    public.recalcular_costo_plan(uuid),
    public.sincronizar_transporte_destinos(uuid, uuid[])
FROM PUBLIC, anon, authenticated;

NOTIFY pgrst, 'reload schema';

COMMIT;
