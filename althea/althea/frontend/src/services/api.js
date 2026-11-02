import { mostrarToast } from '../utils/toast'

// Contrato REST que debe exponer el backend (FastAPI). tipo: destinos|alojamientos|actividades|transportes
const BASE = import.meta.env.VITE_API_URL || '/api'

function mensajeDeMutacion(path, method) {
  if (method === 'POST') {
    if (path === '/planes/generar') return 'Itinerario generado correctamente.'
    if (path === '/planes') return 'Plan creado correctamente.'
    if (/^\/planes\/[^/]+\/duplicar$/.test(path)) return 'Plan duplicado correctamente.'
    if (/^\/planes\/[^/]+\/items$/.test(path)) return 'Recurso añadido al itinerario.'
    if (/^\/planes\/[^/]+\/valoraciones$/.test(path)) return 'Valoración registrada correctamente.'
    if (/^\/recursos\/[^/]+$/.test(path)) return 'Recurso creado correctamente.'
  }
  if (method === 'PUT') {
    if (/^\/planes\/[^/]+\/estado$/.test(path)) return 'Estado del plan actualizado.'
    if (/^\/planes\/[^/]+\/items\/[^/]+$/.test(path)) return 'Día del recurso actualizado.'
    if (/^\/planes\/[^/]+$/.test(path)) return 'Itinerario actualizado correctamente.'
    if (/^\/recursos\/[^/]+\/[^/]+$/.test(path)) return 'Recurso actualizado correctamente.'
  }
  if (method === 'DELETE') {
    if (/^\/planes\/[^/]+\/items\/[^/]+$/.test(path)) return 'Recurso eliminado del itinerario.'
    if (/^\/recursos\/[^/]+\/[^/]+$/.test(path)) return 'Recurso eliminado correctamente.'
  }
  return null
}

async function req(path, { method = 'GET', body } = {}) {
  const mensajeOk = mensajeDeMutacion(path, method)
  try {
    const r = await fetch(BASE + path, {
      method, headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined })
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail ?? `Error ${r.status}`)
    const resultado = r.status === 204 ? null : await r.json()
    if (mensajeOk) mostrarToast(mensajeOk)
    return resultado
  } catch (error) {
    if (mensajeOk) mostrarToast(error.message || 'No se pudo completar el cambio.', 'error')
    throw error
  }
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
  generar: (perfil) => req('/planes/generar', { method: 'POST', body: perfil }),
  crear: (plan) => req('/planes', { method: 'POST', body: plan }),
  listar: (filtros = {}) => req('/planes' + qs(filtros)),
  obtener: (id) => req(`/planes/${id}`),
  actualizarCompleto: (id, plan) => req(`/planes/${id}`, { method: 'PUT', body: plan }),
  valoraciones: (id) => req(`/planes/${id}/valoraciones`),
  calificar: (id, v) => req(`/planes/${id}/valoraciones`, { method: 'POST', body: v }),
  duplicar: (id) => req(`/planes/${id}/duplicar`, { method: 'POST' }),
  estado: (id, estado) => req(`/planes/${id}/estado`, { method: 'PUT', body: { estado } }),
  agregarItem: (id, it) => req(`/planes/${id}/items`, { method: 'POST', body: it }),
  quitarItem: (id, item) => req(`/planes/${id}/items/${item}`, { method: 'DELETE' }),
  moverItem: (id, item, dia) => req(`/planes/${id}/items/${item}`, { method: 'PUT', body: { numero_dia: dia } }),
  pdfUrl: (id) => `${BASE}/planes/${id}/pdf`,
}
export const clima = {
  actual: (idDestino) => req(`/clima/actual/${idDestino}`),
  historico: (idDestino, mes) => req(`/clima/${idDestino}?mes=${mes}`),
}
export const traduccion = { traducir: (idioma, textos) => req('/traducir', { method: 'POST', body: { idioma, textos } }) }
