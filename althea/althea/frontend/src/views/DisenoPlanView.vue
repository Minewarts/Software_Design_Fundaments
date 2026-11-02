<script setup>
// Diseño de planes con generación asistida o creación manual.
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { recursos, planes } from '../services/api'
import { cop, porDia } from '../utils/format'
import { mostrarToast } from '../utils/toast'
import SearchableSelect from '../components/SearchableSelect.vue'
const router = useRouter()
const destinos = ref([]), error = ref(''), cargando = ref(false)
const perfil = ref({ id_destinos: [], duracion_dias: 5, presupuesto_max: 5000000, cantidad_viajeros: 3, tipo_viajero: 'FAMILIA', intereses: '' })
const manual = ref({ titulo: '', cantidad_viajeros: 2, items: [] }), sel = ref({ tipo: 'ALOJAMIENTO', id: '', dia: 1 }), opciones = ref([])
const ENDPOINT = { ALOJAMIENTO: 'alojamientos', ACTIVIDAD: 'actividades', TRANSPORTE: 'transportes' }
const opcionesDestino = () => destinos.value.map((d) => ({ value: d.id, label: d.nombre }))
const opcionesRecurso = () => opciones.value.map((o) => ({ value: o.id, label: o.nombre ?? o.tipo_vehiculo }))
onMounted(async () => {
  try {
    destinos.value = await recursos.listar('destinos')
    await cargarOpciones()
  } catch (e) { error.value = e.message }
})
async function cargarOpciones() { opciones.value = await recursos.listar(ENDPOINT[sel.value.tipo]); sel.value.id = '' }
async function cambiarTipo(tipo) {
  sel.value.tipo = tipo
  try { await cargarOpciones() } catch (e) { error.value = e.message }
}
async function generar() {
  try {
    error.value = ''; cargando.value = true
    if (!perfil.value.id_destinos.length) throw new Error('Selecciona al menos un destino.')
    const p = { ...perfil.value, id_destino: perfil.value.id_destinos[0], intereses: perfil.value.intereses.split(',').map((s) => s.trim()).filter(Boolean) }
    const plan = await planes.generar(p)
    router.push(`/plan/${plan.id}`)
  } catch (e) { error.value = e.message } finally { cargando.value = false }
}
function agregar() {
  const o = opciones.value.find((x) => x.id === sel.value.id); if (!o) return
  manual.value.items.push({ numero_dia: +sel.value.dia, tipo_recurso: sel.value.tipo, id_recurso: o.id, nombre: o.nombre ?? o.tipo_vehiculo })
  mostrarToast('Recurso añadido al borrador del plan.')
}
function quitarItem(item) {
  manual.value.items.splice(manual.value.items.indexOf(item), 1)
  mostrarToast('Recurso eliminado del borrador del plan.')
}
async function guardar() {
  try { const plan = await planes.crear(manual.value); router.push(`/plan/${plan.id}`) } catch (e) { error.value = e.message }
}
</script>
<template>
  <section class="card">
    <h2>1. Perfil del Viajero</h2>
    <form class="form-grid profile-form" @submit.prevent="generar">
      <label class="profile-destinations">Destinos en orden de visita
        <SearchableSelect
          v-model="perfil.id_destinos"
          :options="opcionesDestino()"
          :multiple="true"
          empty-label=""
          placeholder="Busca y selecciona los destinos en orden…"
        />
        <small>Selecciona en el orden de la ruta. La IA solo usará recursos asociados a ellos.</small>
      </label>
      <label>Duración (días)<input type="number" min="1" v-model.number="perfil.duracion_dias" /></label>
      <label>Presupuesto (COP)<input type="number" min="1" v-model.number="perfil.presupuesto_max" /></label>
      <label>Viajeros<input type="number" min="1" v-model.number="perfil.cantidad_viajeros" /></label>
      <label>Tipo de viajero
        <SearchableSelect
          v-model="perfil.tipo_viajero"
          :options="['SOLO','PAREJA','FAMILIA','AMIGOS','CORPORATIVO'].map((t) => ({ value: t, label: t }))"
          empty-label=""
          placeholder="Buscar tipo de viajero…"
        />
      </label>
      <label class="profile-interests">Intereses (separados por coma)<input v-model="perfil.intereses" placeholder="Buceo, Gastronomía" /></label>
      <button class="big profile-submit">{{ cargando ? 'Generando…' : '⚡ Generar Plan con IA' }}</button>
    </form>
    <p class="err">{{ error }}</p>
  </section>
  <section class="card">
    <h2>2. Crear plan manualmente</h2>
    <div class="manual-entry">
      <div class="form-grid manual-plan-fields">
        <label>Título<input v-model="manual.titulo" /></label>
        <label>Viajeros<input type="number" min="1" v-model.number="manual.cantidad_viajeros" /></label>
      </div>
      <div class="form-grid manual-item-fields">
        <label>Tipo
          <SearchableSelect
            v-model="sel.tipo"
            :options="Object.keys(ENDPOINT).map((t) => ({ value: t, label: t }))"
            empty-label=""
            placeholder="Buscar tipo…"
            @update:model-value="cambiarTipo"
          />
        </label>
        <label>Recurso
          <SearchableSelect v-model="sel.id" :options="opcionesRecurso()" empty-label="" placeholder="Buscar o pegar recurso…" />
        </label>
        <label>Día<input type="number" min="1" v-model.number="sel.dia" /></label>
        <button class="sec" type="button" @click="agregar">Agregar recurso</button>
      </div>
    </div>
    <div v-for="[dia, its] in porDia(manual.items)" :key="dia" class="day"><b>Día {{ dia }}</b>
      <div class="items"><div v-for="(i, k) in its" :key="k" class="item"><small>{{ i.tipo_recurso }}</small><br />{{ i.nombre }}
        <br /><button class="sec" @click="quitarItem(i)">Quitar</button></div></div></div>
    <button class="big" :disabled="!manual.titulo || !manual.items.length" @click="guardar">Guardar plan</button>
  </section>
</template>
