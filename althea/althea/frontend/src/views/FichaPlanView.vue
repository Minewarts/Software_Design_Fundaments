<script setup>
// HU-12 ficha · HU-09 personalizar · HU-13 PDF · HU-14 duplicar · HU-15 clima · HU-17 valoraciones · HU-18 traducir
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { planes, clima, traduccion } from '../services/api'
import { cop, porDia, MESES, IDIOMAS } from '../utils/format'
import StarRating from '../components/StarRating.vue'
import AgregarItem from '../components/AgregarItem.vue'
const props = defineProps({ id: String })
const router = useRouter()
const plan = ref(null), vals = ref([]), error = ref(''), editando = ref(false)
const nueva = ref({ autor: '', puntuacion: 0, comentario: '' })
const tr = ref(null), idioma = ref(IDIOMAS[0]), mes = ref(new Date().getMonth() + 1), meteo = ref(null)
const t = (k, fallback) => tr.value?.[k] ?? fallback
async function cargar() { [plan.value, vals.value] = await Promise.all([planes.obtener(props.id), planes.valoraciones(props.id)]) }
async function run(fn) { try { error.value = ''; await fn(); await cargar() } catch (e) { error.value = e.message } }
const cambiarEstado = (e) => run(() => planes.estado(props.id, e))
const agregar = (it) => run(() => planes.agregarItem(props.id, it))
const quitar = (i) => run(() => planes.quitarItem(props.id, i.id))
const mover = (i, dia) => run(() => planes.moverItem(props.id, i.id, +dia))
const calificar = () => run(async () => { await planes.calificar(props.id, nueva.value); nueva.value = { autor: '', puntuacion: 0, comentario: '' } })
async function duplicar() { try { const n = await planes.duplicar(props.id); router.push(`/plan/${n.id}`) } catch (e) { error.value = e.message } }
async function traducir() {
  try {
    error.value = ''
    tr.value = await traduccion.traducir(idioma.value, { titulo: plan.value.titulo, estado: plan.value.estado, dia: 'Día',
      costo: 'Costo estimado', viajeros: 'Viajeros', valoraciones: 'Valoraciones', ALOJAMIENTO: 'Alojamiento', ACTIVIDAD: 'Actividad', TRANSPORTE: 'Transporte' })
  } catch (e) { error.value = e.message }
}
async function verClima() { try { error.value = ''; meteo.value = await clima.historico(plan.value.id_destino, mes.value) } catch (e) { error.value = e.message } }
const promedio = () => (vals.value.reduce((s, v) => s + v.puntuacion, 0) / (vals.value.length || 1)).toFixed(1)
watch(() => props.id, () => { tr.value = meteo.value = null; editando.value = false; cargar() })
onMounted(cargar)
</script>
<template>
  <template v-if="plan">
    <section class="card">
      <router-link to="/directorio" class="mut">← Volver al directorio</router-link>
      <h2>{{ t('titulo', plan.titulo) }} <span class="pill" :class="plan.estado">{{ t('estado', plan.estado) }}</span></h2>
      <p class="mut">{{ t('costo', 'Costo estimado') }}: <b>{{ cop(plan.costo_estimado) }}</b> · {{ t('viajeros', 'Viajeros') }}: {{ plan.cantidad_viajeros }}<span v-if="plan.destino"> · {{ plan.destino }}</span></p>
      <div class="row" style="margin:10px 0">
        <a class="btn" :href="planes.pdfUrl(id)" target="_blank">Exportar a PDF</a>
        <button class="sec" :disabled="plan.estado === 'ARCHIVADO'" @click="editando = !editando">{{ editando ? 'Terminar edición' : 'Personalizar itinerario' }}</button>
        <button class="sec" @click="duplicar">Duplicar como plantilla</button>
        <button v-if="plan.estado === 'BORRADOR'" @click="cambiarEstado('APROBADO')">Aprobar</button>
        <button v-if="plan.estado === 'ARCHIVADO'" @click="cambiarEstado('BORRADOR')">Restaurar</button>
        <button v-else class="sec" @click="cambiarEstado('ARCHIVADO')">Archivar</button>
      </div>
      <div class="row" style="margin-bottom:10px">
        <label>Idioma<select v-model="idioma"><option v-for="i in IDIOMAS" :key="i">{{ i }}</option></select></label>
        <button class="sec" @click="traducir">Traducir ficha</button><button v-if="tr" class="sec" @click="tr = null">Ver original</button>
      </div>
      <p class="err">{{ error }}</p>
      <AgregarItem v-if="editando" @agregar="agregar" />
      <div v-for="[dia, its] in porDia(plan.items)" :key="dia" class="day"><b>{{ t('dia', 'Día') }} {{ dia }}</b>
        <div class="items"><div v-for="i in its" :key="i.id" class="item"><small>{{ t(i.tipo_recurso, i.tipo_recurso) }}</small><br />{{ i.nombre }}
          <template v-if="editando"><br /><input type="number" min="1" :value="i.numero_dia" style="width:60px" @change="mover(i, $event.target.value)" />
            <button class="sec" @click="quitar(i)">Quitar</button></template></div></div></div>
    </section>
    <section v-if="plan.id_destino" class="card">
      <h2>Clima histórico · {{ plan.destino }}</h2>
      <div class="row"><label>Mes<select v-model.number="mes"><option v-for="(m, k) in MESES" :key="m" :value="k + 1">{{ m }}</option></select></label>
        <button class="sec" @click="verClima">Consultar</button></div>
      <p v-if="meteo" style="margin-top:12px">☀ Máx. promedio <b>{{ meteo.temp_max }}°C</b> · Mín. <b>{{ meteo.temp_min }}°C</b> ·
        🌧 {{ meteo.lluvia_mm }} mm en {{ meteo.dias_lluvia }} días <span class="mut">(datos de {{ MESES[meteo.mes - 1] }} {{ meteo.anio }})</span></p>
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
