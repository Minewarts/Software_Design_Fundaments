<script setup>
// HU-08 perfil + IA, HU-06 plan manual.
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { recursos, planes } from '../services/api'
import { cop, porDia } from '../utils/format'
const router = useRouter()
const destinos = ref([]), error = ref(''), cargando = ref(false)
const perfil = ref({ id_destino: '', duracion_dias: 5, presupuesto_max: 2500000, cantidad_viajeros: 3, tipo_viajero: 'FAMILIA', intereses: '' })
const manual = ref({ titulo: '', items: [] }), sel = ref({ tipo: 'ALOJAMIENTO', id: '', dia: 1 }), opciones = ref([])
const ENDPOINT = { ALOJAMIENTO: 'alojamientos', ACTIVIDAD: 'actividades', TRANSPORTE: 'transportes' }
onMounted(async () => { destinos.value = await recursos.listar('destinos'); await cargarOpciones() })
async function cargarOpciones() { opciones.value = await recursos.listar(ENDPOINT[sel.value.tipo]); sel.value.id = '' }
async function generar() {
  try {
    error.value = ''; cargando.value = true
    const p = { ...perfil.value, intereses: perfil.value.intereses.split(',').map((s) => s.trim()).filter(Boolean) }
    const plan = await planes.generar(p)
    router.push(`/plan/${plan.id}`)
  } catch (e) { error.value = e.message } finally { cargando.value = false }
}
function agregar() {
  const o = opciones.value.find((x) => x.id === sel.value.id); if (!o) return
  manual.value.items.push({ numero_dia: +sel.value.dia, tipo_recurso: sel.value.tipo, id_recurso: o.id, nombre: o.nombre ?? o.tipo_vehiculo })
}
async function guardar() {
  try { const plan = await planes.crear(manual.value); router.push(`/plan/${plan.id}`) } catch (e) { error.value = e.message }
}
</script>
<template>
  <section class="card">
    <h2>1. Perfil del Viajero</h2>
    <form class="row" @submit.prevent="generar">
      <label>Destino<select v-model="perfil.id_destino"><option value="">Cualquiera</option>
        <option v-for="d in destinos" :key="d.id" :value="d.id">{{ d.nombre }}</option></select></label>
      <label>Duración (días)<input type="number" min="1" v-model.number="perfil.duracion_dias" /></label>
      <label>Presupuesto (COP)<input type="number" min="1" v-model.number="perfil.presupuesto_max" /></label>
      <label>Viajeros<input type="number" min="1" v-model.number="perfil.cantidad_viajeros" /></label>
      <label>Tipo de viajero<select v-model="perfil.tipo_viajero">
        <option v-for="t in ['SOLO','PAREJA','FAMILIA','AMIGOS','CORPORATIVO']" :key="t">{{ t }}</option></select></label>
      <label>Intereses (separados por coma)<input v-model="perfil.intereses" placeholder="Buceo, Gastronomía" /></label>
      <button class="big">{{ cargando ? 'Generando…' : '⚡ Generar Plan con IA' }}</button>
    </form>
    <p class="err">{{ error }}</p>
  </section>
  <section class="card">
    <h2>2. Crear plan manualmente</h2>
    <div class="row">
      <label>Título<input v-model="manual.titulo" /></label>
      <label>Tipo<select v-model="sel.tipo" @change="cargarOpciones"><option v-for="t in Object.keys(ENDPOINT)" :key="t">{{ t }}</option></select></label>
      <label>Recurso<select v-model="sel.id"><option v-for="o in opciones" :key="o.id" :value="o.id">{{ o.nombre ?? o.tipo_vehiculo }}</option></select></label>
      <label>Día<input type="number" min="1" v-model.number="sel.dia" style="width:70px" /></label>
      <button class="sec" @click="agregar">Agregar</button>
    </div>
    <div v-for="[dia, its] in porDia(manual.items)" :key="dia" class="day"><b>Día {{ dia }}</b>
      <div class="items"><div v-for="(i, k) in its" :key="k" class="item"><small>{{ i.tipo_recurso }}</small><br />{{ i.nombre }}
        <br /><button class="sec" @click="manual.items.splice(manual.items.indexOf(i), 1)">Quitar</button></div></div></div>
    <button class="big" :disabled="!manual.titulo || !manual.items.length" @click="guardar">Guardar plan</button>
  </section>
</template>
