<script setup>
// HU-09: selector para agregar un recurso del catálogo a un día del itinerario.
import { ref, onMounted } from 'vue'
import { recursos } from '../services/api'
const emit = defineEmits(['agregar'])
const ENDPOINT = { ALOJAMIENTO: 'alojamientos', ACTIVIDAD: 'actividades', TRANSPORTE: 'transportes' }
const tipo = ref('ACTIVIDAD'), opciones = ref([]), id = ref(''), dia = ref(1)
async function cargar() { opciones.value = await recursos.listar(ENDPOINT[tipo.value]); id.value = '' }
onMounted(cargar)
</script>
<template>
  <div class="row" style="margin:10px 0">
    <label>Tipo<select v-model="tipo" @change="cargar"><option v-for="t in Object.keys(ENDPOINT)" :key="t">{{ t }}</option></select></label>
    <label>Recurso<select v-model="id"><option v-for="o in opciones" :key="o.id" :value="o.id">{{ o.nombre ?? o.tipo_vehiculo }}</option></select></label>
    <label>Día<input type="number" min="1" v-model.number="dia" style="width:70px" /></label>
    <button :disabled="!id" @click="emit('agregar', { numero_dia: dia, tipo_recurso: tipo, id_recurso: id })">Agregar al itinerario</button>
  </div>
</template>
