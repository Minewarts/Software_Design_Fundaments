<script setup>
import { computed, onMounted, ref } from 'vue'
import { recursos } from '../services/api'
import { cop } from '../utils/format'
import SearchableSelect from '../components/SearchableSelect.vue'

const actividades = ref([])
const destinos = ref([])
const destino = ref('')
const busqueda = ref('')
const cargando = ref(true)
const error = ref('')
const opcionesDestino = computed(() => destinos.value.map((d) => ({ value: d.id, label: d.nombre })))

const filtradas = computed(() => actividades.value.filter((actividad) => {
  const texto = `${actividad.nombre} ${actividad.tipo_actividad}`.toLocaleLowerCase()
  return (!destino.value || actividad.id_destino === destino.value) &&
    texto.includes(busqueda.value.trim().toLocaleLowerCase())
}))

onMounted(async () => {
  try {
    ;[actividades.value, destinos.value] = await Promise.all([
      recursos.listar('actividades'),
      recursos.listar('destinos'),
    ])
  } catch (e) {
    error.value = e.message
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <section class="card">
    <h2>Consultar actividades</h2>
    <p class="mut">Explora las actividades disponibles por destino, nombre o tipo.</p>
    <div class="row" style="margin:14px 0">
      <label>Destino
        <SearchableSelect v-model="destino" :options="opcionesDestino" empty-label="Todos los destinos" placeholder="Buscar o pegar destino…" />
      </label>
      <label>Actividad o tipo
        <input v-model="busqueda" type="search" placeholder="Ej. buceo, aventura" />
      </label>
    </div>
    <p v-if="error" class="err">{{ error }}</p>
    <p v-else-if="cargando" class="mut">Cargando actividades…</p>
    <template v-else>
      <p v-if="!filtradas.length" class="mut">No hay actividades que coincidan con la búsqueda.</p>
      <table v-else>
        <thead><tr><th>Actividad</th><th>Tipo</th><th>Destino</th><th>Costo por persona</th></tr></thead>
        <tbody>
          <tr v-for="actividad in filtradas" :key="actividad.id">
            <td><b>{{ actividad.nombre }}</b></td>
            <td>{{ actividad.tipo_actividad }}</td>
            <td>{{ destinos.find((d) => d.id === actividad.id_destino)?.nombre ?? '—' }}</td>
            <td>{{ cop(actividad.costo_persona) }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </section>
</template>
