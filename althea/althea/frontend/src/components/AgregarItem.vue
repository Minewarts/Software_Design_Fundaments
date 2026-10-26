<script setup>
// Selector para agregar un recurso del catálogo a un día del itinerario.
import { ref, onMounted } from 'vue'
import { recursos } from '../services/api'
import SearchableSelect from './SearchableSelect.vue'
const emit = defineEmits(['agregar'])
const ENDPOINT = { ALOJAMIENTO: 'alojamientos', ACTIVIDAD: 'actividades', TRANSPORTE: 'transportes' }
const tipo = ref('ACTIVIDAD'), opciones = ref([]), id = ref(''), dia = ref(1)
const error = ref('')
const opcionesRecurso = () => opciones.value.map((o) => ({ value: o.id, label: o.nombre ?? o.tipo_vehiculo }))
async function cargar() {
  try {
    error.value = ''
    opciones.value = await recursos.listar(ENDPOINT[tipo.value])
    id.value = ''
  } catch (e) { error.value = e.message }
}
async function cambiarTipo(value) {
  tipo.value = value
  await cargar()
}
onMounted(cargar)
</script>
<template>
  <div class="row" style="margin:10px 0">
    <label>Tipo
      <SearchableSelect
        v-model="tipo"
        :options="Object.keys(ENDPOINT).map((t) => ({ value: t, label: t }))"
        empty-label=""
        placeholder="Buscar tipo…"
        @update:model-value="cambiarTipo"
      />
    </label>
    <label>Recurso
      <SearchableSelect v-model="id" :options="opcionesRecurso()" empty-label="" placeholder="Buscar o pegar recurso…" />
    </label>
    <label>Día<input type="number" min="1" v-model.number="dia" style="width:70px" /></label>
    <button :disabled="!id" @click="emit('agregar', { numero_dia: dia, tipo_recurso: tipo, id_recurso: id })">Agregar al itinerario</button>
  </div>
  <p v-if="error" class="err">{{ error }}</p>
</template>
