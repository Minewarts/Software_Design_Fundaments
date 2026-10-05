<script setup>
// CRUD genérico de recursos del catálogo (HU-01, 02, 03, 04, 05).
import { ref, watch, onMounted } from 'vue'
import { recursos } from '../services/api'
const props = defineProps({ tipo: String, campos: Array })
const items = ref([]), destinos = ref([]), form = ref({}), editId = ref(null), error = ref('')
async function cargar() {
  items.value = await recursos.listar(props.tipo)
  if (props.campos.some((c) => c.type.startsWith('destino'))) destinos.value = await recursos.listar('destinos')
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
watch(() => props.tipo, () => { form.value = {}; editId.value = null; cargar() })
onMounted(cargar)
</script>
<template>
  <form class="row" @submit.prevent="guardar">
    <label v-for="c in campos" :key="c.key">{{ c.label }}
      <select v-if="c.type === 'destino'" v-model="form[c.key]" required>
        <option v-for="d in destinos" :key="d.id" :value="d.id">{{ d.nombre }}</option></select>
      <select v-else-if="c.type === 'destinos'" v-model="form[c.key]" multiple>
        <option v-for="d in destinos" :key="d.id" :value="d.id">{{ d.nombre }}</option></select>
      <input v-else v-model="form[c.key]" :type="c.type" :min="c.type === 'number' ? 0 : null" required />
    </label>
    <button>{{ editId ? 'Actualizar' : 'Agregar' }}</button>
    <button v-if="editId" type="button" class="sec" @click="form = {}; editId = null">Cancelar</button>
  </form>
  <p class="err">{{ error }}</p>
  <table>
    <tr><th v-for="c in campos" :key="c.key">{{ c.label }}</th><th></th></tr>
    <tr v-for="i in items" :key="i.id">
      <td v-for="c in campos" :key="c.key">{{ c.type.startsWith('destino') ? nombres(i[c.key]) : i[c.key] }}</td>
      <td><button class="sec" @click="form = { ...i }; editId = i.id">Editar</button>
          <button class="sec" @click="eliminar(i)">Eliminar</button></td>
    </tr>
  </table>
</template>
