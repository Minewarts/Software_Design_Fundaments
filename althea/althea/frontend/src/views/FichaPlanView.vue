<script setup>
// HU-12 ficha descriptiva · HU-17 valoraciones.
import { ref, onMounted } from 'vue'
import { planes } from '../services/api'
import { cop, porDia } from '../utils/format'
import StarRating from '../components/StarRating.vue'
const props = defineProps({ id: String })
const plan = ref(null), vals = ref([]), nueva = ref({ autor: '', puntuacion: 0, comentario: '' }), error = ref('')
async function cargar() { [plan.value, vals.value] = await Promise.all([planes.obtener(props.id), planes.valoraciones(props.id)]) }
async function calificar() {
  try { await planes.calificar(props.id, nueva.value); nueva.value = { autor: '', puntuacion: 0, comentario: '' }; await cargar() }
  catch (e) { error.value = e.message }
}
const promedio = () => (vals.value.reduce((s, v) => s + v.puntuacion, 0) / (vals.value.length || 1)).toFixed(1)
onMounted(cargar)
</script>
<template>
  <template v-if="plan">
    <section class="card">
      <router-link to="/directorio" class="mut">← Volver al directorio</router-link>
      <h2>{{ plan.titulo }} <span class="pill" :class="plan.estado">{{ plan.estado }}</span></h2>
      <p class="mut">Costo estimado: <b>{{ cop(plan.costo_estimado) }}</b></p>
      <div v-for="[dia, its] in porDia(plan.items)" :key="dia" class="day"><b>Día {{ dia }}</b>
        <div class="items"><div v-for="i in its" :key="i.id" class="item"><small>{{ i.tipo_recurso }}</small><br />{{ i.nombre }}</div></div></div>
    </section>
    <section class="card">
      <h2>Valoraciones <span class="mut">· {{ promedio() }} ★ ({{ vals.length }})</span></h2>
      <div v-for="v in vals" :key="v.id" style="margin-bottom:10px"><b>{{ v.autor }}</b> <StarRating :model-value="v.puntuacion" readonly /><br />{{ v.comentario }}</div>
      <form class="row" @submit.prevent="calificar">
        <label>Nombre<input v-model="nueva.autor" required /></label>
        <label>Puntuación<StarRating v-model="nueva.puntuacion" /></label>
        <label>Comentario<input v-model="nueva.comentario" /></label>
        <button :disabled="!nueva.puntuacion">Calificar plan</button>
      </form>
      <p class="err">{{ error }}</p>
    </section>
  </template>
</template>
