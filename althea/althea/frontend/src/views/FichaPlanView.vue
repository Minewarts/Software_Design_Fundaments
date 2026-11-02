<script setup>
// Detalle de plan, edición del itinerario, clima, valoraciones y traducción.
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { planes, clima, traduccion, recursos } from '../services/api'
import { cop, porDia, IDIOMAS } from '../utils/format'
import StarRating from '../components/StarRating.vue'
import AgregarItem from '../components/AgregarItem.vue'
import SearchableSelect from '../components/SearchableSelect.vue'
import { mostrarToast } from '../utils/toast'
const props = defineProps({ id: String })
const router = useRouter()
const plan = ref(null), vals = ref([]), error = ref(''), avisoEdicion = ref('')
const editando = ref(false), guardandoEdicion = ref(false)
const borrador = ref(null), estadoInicialEdicion = ref(null)
const catalogo = ref({ destinos: [], alojamientos: [], actividades: [], transportes: [] })
const nueva = ref({ autor: '', puntuacion: 0, comentario: '' })
const tr = ref(null), idioma = ref(IDIOMAS[0]), meteo = ref(null)
const t = (k, fallback) => tr.value?.[k] ?? fallback
async function cargar() {
  try {
    error.value = ''
    const [planData, ratings] = await Promise.all([planes.obtener(props.id), planes.valoraciones(props.id)])
    plan.value = planData
    vals.value = ratings
    meteo.value = plan.value.id_destino ? await clima.actual(plan.value.id_destino) : null
  } catch (e) { error.value = e.message }
}
async function run(fn) { try { error.value = ''; await fn(); await cargar() } catch (e) { error.value = e.message } }
const cambiarEstado = (e) => run(() => planes.estado(props.id, e))
const calificar = () => run(async () => { await planes.calificar(props.id, nueva.value); nueva.value = { autor: '', puntuacion: 0, comentario: '' } })
async function duplicar() { try { const n = await planes.duplicar(props.id); router.push(`/plan/${n.id}`) } catch (e) { error.value = e.message } }
async function traducir() {
  try {
    error.value = ''
    tr.value = await traduccion.traducir(idioma.value, { titulo: plan.value.titulo, estado: plan.value.estado, dia: 'Día',
      costo: 'Costo estimado', viajeros: 'Viajeros', valoraciones: 'Valoraciones', ALOJAMIENTO: 'Alojamiento', ACTIVIDAD: 'Actividad', TRANSPORTE: 'Transporte' })
  } catch (e) { error.value = e.message }
}
const promedio = () => (vals.value.reduce((s, v) => s + v.puntuacion, 0) / (vals.value.length || 1)).toFixed(1)
function diasPlan(planData) {
  const dias = new Map(porDia(planData.items ?? []))
  const diasLibres = new Set((planData.dias_libres ?? []).map(Number))
  const duracion = Math.max(Number(planData.duracion) || 0, ...[...dias.keys()].map(Number), 0)
  return Array.from({ length: duracion }, (_, index) => {
    const dia = String(index + 1)
    return [dia, dias.get(dia) ?? [], diasLibres.has(index + 1)]
  })
}
const climaIcono = (datos) => {
  const code = datos?.codigo_tiempo ?? 0
  if (code === 0) return '☀️'
  if ([1, 2, 3].includes(code)) return '🌤️'
  if ([45, 48].includes(code)) return '🌫️'
  if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return '🌧️'
  if ([71, 73, 75, 77, 85, 86].includes(code)) return '❄️'
  if ([95, 96, 99].includes(code)) return '⛈️'
  return '🌦️'
}
const formatearHora = (valor) => {
  if (!valor) return 'ahora'
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return valor
  return fecha.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
const formatearFechaPronostico = (valor) => {
  const [anio, mes, dia] = valor.split('-').map(Number)
  return new Date(anio, mes - 1, dia).toLocaleDateString('es-CO', { weekday: 'short', day: 'numeric' })
}
const tiposRecurso = ['ALOJAMIENTO', 'ACTIVIDAD', 'TRANSPORTE']
const listaPorTipo = { ALOJAMIENTO: 'alojamientos', ACTIVIDAD: 'actividades', TRANSPORTE: 'transportes' }
function recursosDelTipo(tipo) {
  const lista = catalogo.value[listaPorTipo[tipo]] ?? []
  const destinosSeleccionados = borrador.value?.id_destinos ?? []
  return lista.filter((recurso) => {
    if (tipo === 'TRANSPORTE') {
      return (recurso.ids_destinos ?? []).some((idDestino) => destinosSeleccionados.includes(idDestino))
    }
    return destinosSeleccionados.includes(recurso.id_destino)
  })
}
function opcionesDeRecurso(tipo) {
  return recursosDelTipo(tipo).map((recurso) => ({
    value: recurso.id, label: recurso.nombre ?? recurso.tipo_vehiculo,
  }))
}
function nombreDeRecurso(item) {
  const recurso = (catalogo.value[listaPorTipo[item.tipo_recurso]] ?? [])
    .find((opcion) => opcion.id === item.id_recurso)
  return recurso?.nombre ?? recurso?.tipo_vehiculo ?? item.nombre ?? 'Recurso no disponible'
}
function recursoEsCompatible(item) {
  const destinosOriginales = (plan.value?.destinos ?? [])
    .map((destino) => destino.id)
  if (!destinosOriginales.length && plan.value?.id_destino) destinosOriginales.push(plan.value.id_destino)
  const destinosSinCambios = JSON.stringify(borrador.value?.id_destinos ?? []) === JSON.stringify(destinosOriginales)
  const recursoYaExistia = destinosSinCambios && plan.value?.items.some((original) =>
    original.id === item.id
      && original.tipo_recurso === item.tipo_recurso
      && original.id_recurso === item.id_recurso)
  return recursoYaExistia || recursosDelTipo(item.tipo_recurso).some((recurso) => recurso.id === item.id_recurso)
}
function datosParaGuardar() {
  return {
    titulo: borrador.value.titulo.trim(),
    cantidad_viajeros: Number(borrador.value.cantidad_viajeros),
    id_destinos: [...borrador.value.id_destinos],
    items: borrador.value.items.map(({ id, numero_dia, tipo_recurso, id_recurso }) => ({
      id: id ?? null,
      numero_dia: Number(numero_dia),
      tipo_recurso,
      id_recurso,
    })),
  }
}
async function iniciarEdicion() {
  try {
    error.value = ''
    avisoEdicion.value = ''
    const [destinos, alojamientos, actividades, transportes] = await Promise.all([
      recursos.listar('destinos'),
      recursos.listar('alojamientos'),
      recursos.listar('actividades'),
      recursos.listar('transportes'),
    ])
    catalogo.value = { destinos, alojamientos, actividades, transportes }
    borrador.value = {
      titulo: plan.value.titulo,
      cantidad_viajeros: plan.value.cantidad_viajeros,
      id_destinos: (plan.value.destinos ?? [])
        .map((destino) => destino.id)
        .concat(
          plan.value.id_destino && !(plan.value.destinos ?? []).length
            ? [plan.value.id_destino]
            : [],
        ),
      items: plan.value.items.map((item) => ({
        ...item,
        id_recurso: item.id_recurso,
      })),
    }
    estadoInicialEdicion.value = JSON.stringify(datosParaGuardar())
    editando.value = true
  } catch (e) { error.value = e.message }
}
function agregarItemEdicion(item) {
  borrador.value.items.push({
    ...item,
    nombre: opcionesDeRecurso(item.tipo_recurso).find((opcion) => opcion.value === item.id_recurso)?.label,
  })
  mostrarToast('Recurso añadido al borrador del itinerario.')
}
function quitarItemEdicion(item) {
  borrador.value.items.splice(borrador.value.items.indexOf(item), 1)
  mostrarToast('Recurso eliminado del borrador del itinerario.')
}
async function guardarEdicion() {
  try {
    error.value = ''
    avisoEdicion.value = ''
    const datos = datosParaGuardar()
    if (JSON.stringify(datos) === estadoInicialEdicion.value) {
      cancelarEdicion('No se detectaron cambios; se cerró la edición.')
      return
    }
    guardandoEdicion.value = true
    await planes.actualizarCompleto(props.id, datos)
    editando.value = false
    borrador.value = null
    estadoInicialEdicion.value = null
    await cargar()
  } catch (e) { error.value = e.message } finally { guardandoEdicion.value = false }
}
function cancelarEdicion(mensaje = '') {
  editando.value = false
  borrador.value = null
  estadoInicialEdicion.value = null
  error.value = ''
  avisoEdicion.value = mensaje
}
watch(() => props.id, () => { tr.value = meteo.value = null; plan.value = null; editando.value = false; borrador.value = null; estadoInicialEdicion.value = null; avisoEdicion.value = ''; cargar() })
onMounted(cargar)
</script>
<template>
  <template v-if="plan">
    <section class="card plan-card">
      <router-link to="/directorio" class="card-close" aria-label="Volver al directorio" title="Volver al directorio">×</router-link>
      <h2>{{ t('titulo', plan.titulo) }} <span class="pill" :class="plan.estado">{{ t('estado', plan.estado) }}</span></h2>
      <p v-if="!editando" class="mut">{{ t('costo', 'Costo estimado') }}: <b>{{ cop(plan.costo_estimado) }}</b> · {{ t('viajeros', 'Viajeros') }}: {{ plan.cantidad_viajeros }}<span v-if="plan.destino"> · {{ plan.destino }}</span></p>
      <div class="row" style="margin:10px 0">
        <a class="btn" :href="planes.pdfUrl(id)" target="_blank">Exportar a PDF</a>
        <button v-if="!editando" class="sec" @click="iniciarEdicion">Modificar itinerario</button>
        <button v-else :disabled="guardandoEdicion || !borrador?.titulo.trim() || borrador.items.some((item) => !recursoEsCompatible(item))" @click="guardarEdicion">
          {{ guardandoEdicion ? 'Guardando…' : 'Guardar cambios' }}
        </button>
        <button v-if="editando" class="sec" :disabled="guardandoEdicion" @click="cancelarEdicion('Edición cancelada.')">Cancelar</button>
        <button class="sec" @click="duplicar">Duplicar como plantilla</button>
        <button v-if="plan.estado === 'BORRADOR'" @click="cambiarEstado('APROBADO')">Aprobar</button>
        <button v-if="plan.estado === 'ARCHIVADO'" @click="cambiarEstado('BORRADOR')">Restaurar</button>
        <button v-else class="sec" @click="cambiarEstado('ARCHIVADO')">Archivar</button>
      </div>
      <div class="row" style="margin-bottom:10px">
        <label>Idioma
          <SearchableSelect
            v-model="idioma"
            :options="IDIOMAS.map((i) => ({ value: i, label: i }))"
            empty-label=""
            placeholder="Buscar idioma…"
          />
        </label>
        <button class="sec" @click="traducir">Traducir ficha</button><button v-if="tr" class="sec" @click="tr = null">Ver original</button>
      </div>
      <p class="err">{{ error }}</p>
      <p v-if="avisoEdicion" class="notice" role="status">{{ avisoEdicion }}</p>
      <template v-if="editando">
        <div class="itinerary-editor">
          <div class="form-grid editor-fields">
            <label class="editor-title">Título del plan<input v-model.trim="borrador.titulo" maxlength="200" required /></label>
            <label>Viajeros<input v-model.number="borrador.cantidad_viajeros" type="number" min="1" required /></label>
            <label>Destinos en orden de visita
              <SearchableSelect
                v-model="borrador.id_destinos"
                :options="catalogo.destinos.map((destino) => ({ value: destino.id, label: destino.nombre }))"
                :multiple="true"
                empty-label=""
                placeholder="Añade destinos en el orden de la ruta…"
              />
            </label>
          </div>
          <p v-if="borrador.items.some((item) => !recursoEsCompatible(item))" class="err">
            Hay recursos que no pertenecen al destino seleccionado. Reemplázalos o elimínalos antes de guardar.
          </p>
          <AgregarItem :id-destinos="borrador.id_destinos" @agregar="agregarItemEdicion" />
        </div>
        <div v-for="[dia, its] in porDia(borrador.items)" :key="dia" class="day">
          <b>Día {{ dia }}</b>
          <div class="items">
            <div v-for="(item, index) in its" :key="item.id ?? `nuevo-${index}`" class="item editor-item">
              <label>Tipo
                <SearchableSelect
                  v-model="item.tipo_recurso"
                  :options="tiposRecurso.map((tipo) => ({ value: tipo, label: tipo }))"
                  empty-label=""
                  placeholder="Tipo de recurso…"
                />
              </label>
              <label>Recurso
                <SearchableSelect
                  v-model="item.id_recurso"
                  :options="opcionesDeRecurso(item.tipo_recurso)"
                  empty-label=""
                  placeholder="Buscar recurso…"
                />
              </label>
              <label>Día<input v-model.number="item.numero_dia" type="number" min="1" /></label>
              <small v-if="item.id_recurso && !recursoEsCompatible(item)" class="err">Recurso incompatible con el destino.</small>
              <button class="sec" @click="quitarItemEdicion(item)">Quitar recurso</button>
            </div>
          </div>
        </div>
        <p v-if="!borrador.items.length" class="mut">El itinerario está vacío. Agrega recursos antes de guardar.</p>
      </template>
      <template v-else>
        <div v-for="[dia, its, libre] in diasPlan(plan)" :key="dia" class="day"><b>{{ t('dia', 'Día') }} {{ dia }}</b>
          <div v-if="its.length" class="items"><div v-for="i in its" :key="i.id" class="item">
            <small>{{ t(i.tipo_recurso, i.tipo_recurso) }}<span v-if="i.destino"> · {{ i.destino }}</span></small><br />{{ i.nombre }}
          </div></div>
          <p v-else-if="libre" class="mut">Día libre · sin recursos programados</p>
        </div>
      </template>
    </section>
    <section v-if="plan.id_destino" class="card weather-card">
      <div class="weather-header">
        <div>
          <div class="weather-kicker">Clima actual</div>
          <h2>{{ meteo?.lugar ?? plan.destino }}</h2>
        </div>
        <div class="weather-icon" aria-label="Estado del clima">{{ climaIcono(meteo) }}</div>
      </div>
      <div v-if="meteo" class="weather-body">
        <div class="weather-temp">
          <span class="temp-number">{{ Number(meteo.temperatura).toFixed(1) }}</span>
          <span class="temp-unit">°C</span>
        </div>
        <div class="weather-summary">
          <strong>{{ meteo.estado }}</strong>
          <span>Sensación térmica {{ Number(meteo.sensacion_termica).toFixed(1) }}°C</span>
          <small>Actualizado a las {{ formatearHora(meteo.actualizado) }} · Open-Meteo</small>
        </div>
      </div>
      <div v-if="meteo" class="weather-metrics">
        <div class="metric">
          <span>Humedad</span>
          <strong>{{ meteo.humedad }}%</strong>
        </div>
        <div class="metric">
          <span>Precip.</span>
          <strong>{{ meteo.precipitacion }} mm</strong>
        </div>
        <div class="metric">
          <span>Viento</span>
          <strong>{{ meteo.viento }} km/h</strong>
        </div>
      </div>
      <div v-if="meteo?.pronostico?.length" class="forecast">
        <div class="forecast-heading">
          <h3>Pronóstico</h3>
          <span>Próximos 6 días</span>
        </div>
        <div class="forecast-grid">
          <article v-for="dia in meteo.pronostico" :key="dia.fecha" class="forecast-day">
            <strong class="forecast-date">{{ formatearFechaPronostico(dia.fecha) }}</strong>
            <span class="forecast-icon" aria-hidden="true">{{ climaIcono(dia) }}</span>
            <span class="forecast-state">{{ dia.estado }}</span>
            <div class="forecast-temperatures">
              <strong>{{ Math.round(dia.temperatura_max) }}°</strong>
              <span>{{ Math.round(dia.temperatura_min) }}°</span>
            </div>
            <small>☂ {{ dia.probabilidad_precipitacion ?? '—' }}%</small>
          </article>
        </div>
      </div>
    </section>
    <section class="card">
      <h2>{{ t('valoraciones', 'Valoraciones') }} <span class="mut">· {{ promedio() }} ★ ({{ vals.length }})</span></h2>
      <div v-for="v in vals" :key="v.id" style="margin-bottom:10px"><b>{{ v.autor }}</b> <StarRating :model-value="v.puntuacion" readonly /><br />{{ v.comentario }}</div>
      <form class="row" @submit.prevent="calificar">
        <label>Nombre<input v-model="nueva.autor" required /></label>
        <label>Puntuación<StarRating v-model="nueva.puntuacion" /></label>
        <label>Comentario<input v-model="nueva.comentario" /></label>
        <button :disabled="!nueva.puntuacion">Calificar plan</button>
      </form>
    </section>
  </template>
</template>
