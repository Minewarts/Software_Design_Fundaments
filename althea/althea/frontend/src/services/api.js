// Contrato REST que debe exponer el backend (FastAPI). tipo: destinos|alojamientos|actividades|transportes
const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'
async function req(path, { method = 'GET', body } = {}) {
  const r = await fetch(BASE + path, {
    method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined })
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? `Error ${r.status}`)
  return r.status === 204 ? null : r.json()
}
export const recursos = {
  listar: (t) => req(`/recursos/${t}`),
  crear: (t, d) => req(`/recursos/${t}`, { method: 'POST', body: d }),
  editar: (t, id, d) => req(`/recursos/${t}/${id}`, { method: 'PUT', body: d }),
  eliminar: (t, id) => req(`/recursos/${t}/${id}`, { method: 'DELETE' }),
  relaciones: () => req('/catalogo/relaciones'), // [{destino, alojamientos:[{nombre}], actividades:[], transportes:[]}]
}
export const planes = {
  generar: (perfil) => req('/planes/generar', { method: 'POST', body: perfil }), // GenerarItinerarioInteligente
  crear: (plan) => req('/planes', { method: 'POST', body: plan }),               // creación manual (HU-06)
  listar: () => req('/planes'),
  obtener: (id) => req(`/planes/${id}`), // {id,titulo,estado,costo_estimado,items:[{numero_dia,tipo_recurso,nombre}]}
  valoraciones: (id) => req(`/planes/${id}/valoraciones`),
  calificar: (id, v) => req(`/planes/${id}/valoraciones`, { method: 'POST', body: v }),
}
