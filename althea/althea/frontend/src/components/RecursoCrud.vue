<script setup>
// CRUD genérico de recursos del catálogo.
import { ref, watch, onMounted } from 'vue'
import { recursos } from '../services/api'
import SearchableSelect from './SearchableSelect.vue'
const props = defineProps({ tipo: String, campos: Array })
const items = ref([]), destinos = ref([]), form = ref({}), editId = ref(null), error = ref(''), cargando = ref(false)
async function cargar() {
  try {
    cargando.value = true
    error.value = ''
    items.value = await recursos.listar(props.tipo)
    if (props.campos.some((c) => c.type.startsWith('destino'))) destinos.value = await recursos.listar('destinos')
  } catch (e) {
    items.value = []
    error.value = e.message
  } finally {
    cargando.value = false
  }
}
async function guardar() {
  try {
    error.value = ''
    editId.value ? await recursos.editar(props.tipo, editId.value, form.value) : await recursos.crear(props.tipo, form.value)
    form.value = {}; editId.value = null; await cargar()
  } catch (e) { error.value = e.message }
}
async function eliminar(i) {
  if (!confirm('¿Eliminar este registro?')) return
  try { await recursos.eliminar(props.tipo, i.id); await cargar() } catch (e) { error.value = e.message }
}
const nombres = (ids) => [].concat(ids ?? []).map((id) => destinos.value.find((d) => d.id === id)?.nombre ?? '—').join(', ')
const opcionesDestino = () => destinos.value.map((d) => ({ value: d.id, label: d.nombre }))
watch(() => props.tipo, () => { form.value = {}; editId.value = null; cargar() })
onMounted(cargar)
</script>
<template>
  <form class="form-grid resource-form" @submit.prevent="guardar">
    <label v-for="c in campos" :key="c.key">{{ c.label }}
      <SearchableSelect
        v-if="c.type === 'destino'"
        v-model="form[c.key]"
        :options="opcionesDestino()"
        empty-label=""
        placeholder="Buscar o pegar un destino…"
      />
      <SearchableSelect
        v-else-if="c.type === 'destinos'"
        v-model="form[c.key]"
        :options="opcionesDestino()"
        multiple
        placeholder="Buscar o pegar destinos…"
      />
      <input v-else v-model="form[c.key]" :type="c.type" :min="c.type === 'number' ? 0 : null" required />
    </label>
    <button>{{ editId ? 'Actualizar' : 'Agregar' }}</button>
    <button v-if="editId" type="button" class="sec" @click="form = {}; editId = null">Cancelar</button>
  </form>
  <p v-if="error" class="err">{{ error }}</p>
  <p v-else-if="cargando" class="mut">Cargando recursos…</p>
  <table>
    <tr><th v-for="c in campos" :key="c.key">{{ c.label }}</th><th></th></tr>
    <tr v-for="i in items" :key="i.id">
      <td v-for="c in campos" :key="c.key">{{ c.type.startsWith('destino') ? nombres(i[c.key]) : i[c.key] }}</td>
      <td><button class="sec" @click="form = { ...i }; editId = i.id">Editar</button>
          <button class="sec" @click="eliminar(i)">Eliminar</button></td>
    </tr>
  </table>
</template>
