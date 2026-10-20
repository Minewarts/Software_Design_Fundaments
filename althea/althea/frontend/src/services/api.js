// Contrato REST que debe exponer el backend (FastAPI). tipo: destinos|alojamientos|actividades|transportes
const BASE = import.meta.env.VITE_API_URL || '/api'
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
const qs = (o) => { const p = new URLSearchParams(Object.entries(o).filter(([, v]) => v !== '' && v != null)); return p.toString() ? `?${p}` : '' }
export const planes = {
  generar: (perfil) => req('/planes/generar', { method: 'POST', body: perfil }),     // HU-08
  crear: (plan) => req('/planes', { method: 'POST', body: plan }),                    // HU-06
  listar: (filtros = {}) => req('/planes' + qs(filtros)),                             // HU-10 / HU-11
  obtener: (id) => req(`/planes/${id}`),                                              // HU-12
  valoraciones: (id) => req(`/planes/${id}/valoraciones`),                            // HU-17
  calificar: (id, v) => req(`/planes/${id}/valoraciones`, { method: 'POST', body: v }),
  duplicar: (id) => req(`/planes/${id}/duplicar`, { method: 'POST' }),                // HU-14
  estado: (id, estado) => req(`/planes/${id}/estado`, { method: 'PUT', body: { estado } }),
  agregarItem: (id, it) => req(`/planes/${id}/items`, { method: 'POST', body: it }),  // HU-09
  quitarItem: (id, item) => req(`/planes/${id}/items/${item}`, { method: 'DELETE' }),
  moverItem: (id, item, dia) => req(`/planes/${id}/items/${item}`, { method: 'PUT', body: { numero_dia: dia } }),
  pdfUrl: (id) => `${BASE}/planes/${id}/pdf`,                                         // HU-13
}
export const clima = { historico: (idDestino, mes) => req(`/clima/${idDestino}?mes=${mes}`) }        // HU-15
export const traduccion = { traducir: (idioma, textos) => req('/traducir', { method: 'POST', body: { idioma, textos } }) } // HU-18
export const notificaciones = {                                                                       // HU-16
  listar: () => req('/notificaciones'),
  leerTodas: () => req('/notificaciones/leer', { method: 'POST' }),
}
