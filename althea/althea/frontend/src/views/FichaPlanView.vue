<script setup>
// Detalle de plan, edición del itinerario, clima, valoraciones y traducción.
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { planes, clima, traduccion } from '../services/api'
import { cop, porDia, IDIOMAS } from '../utils/format'
import StarRating from '../components/StarRating.vue'
import AgregarItem from '../components/AgregarItem.vue'
import SearchableSelect from '../components/SearchableSelect.vue'
const props = defineProps({ id: String })
const router = useRouter()
const plan = ref(null), vals = ref([]), error = ref(''), editando = ref(false)
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
const promedio = () => (vals.value.reduce((s, v) => s + v.puntuacion, 0) / (vals.value.length || 1)).toFixed(1)
watch(() => props.id, () => { tr.value = meteo.value = null; plan.value = null; editando.value = false; cargar() })
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
      <AgregarItem v-if="editando" @agregar="agregar" />
      <div v-for="[dia, its] in porDia(plan.items)" :key="dia" class="day"><b>{{ t('dia', 'Día') }} {{ dia }}</b>
        <div class="items"><div v-for="i in its" :key="i.id" class="item"><small>{{ t(i.tipo_recurso, i.tipo_recurso) }}</small><br />{{ i.nombre }}
          <template v-if="editando"><br /><input type="number" min="1" :value="i.numero_dia" style="width:60px" @change="mover(i, $event.target.value)" />
            <button class="sec" @click="quitar(i)">Quitar</button></template></div></div></div>
    </section>
    <section v-if="plan.id_destino" class="card">
      <h2>Clima actual · {{ meteo?.lugar ?? plan.destino }}</h2>
      <p v-if="meteo" style="margin-top:12px">
        <b>{{ meteo.estado }}</b> · Temperatura <b>{{ meteo.temperatura }}°C</b> · Sensación térmica <b>{{ meteo.sensacion_termica }}°C</b> ·
        Humedad <b>{{ meteo.humedad }}%</b> · Precipitación <b>{{ meteo.precipitacion }} mm</b> · Viento <b>{{ meteo.viento }} km/h</b>
        <span class="mut">(actualizado {{ meteo.actualizado }}, vía Open-Meteo)</span>
      </p>
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
