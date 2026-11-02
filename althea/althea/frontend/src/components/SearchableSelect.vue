<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  modelValue: { type: [String, Number, Array], default: '' },
  options: { type: Array, default: () => [] },
  multiple: { type: Boolean, default: false },
  placeholder: { type: String, default: 'Escribe para buscar o pega un valor…' },
  emptyLabel: { type: String, default: 'Selecciona una opción' },
})
const emit = defineEmits(['update:modelValue'])
const query = ref('')
const abierto = ref(false)
const contenedor = ref(null)
const normalizar = (valor) => String(valor ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase()
const filtradas = computed(() => {
  const term = normalizar(query.value.trim())
  return term
    ? props.options.filter((option) => normalizar(option.label).includes(term))
    : props.options
})
const seleccionadas = computed(() => {
  const values = props.multiple
    ? (Array.isArray(props.modelValue) ? props.modelValue : [])
    : [props.modelValue]
  if (props.multiple) {
    const optionsByValue = new Map(props.options.map((option) => [option.value, option]))
    return values.map((value) => optionsByValue.get(value)).filter(Boolean)
  }
  return props.options.filter((option) => values.includes(option.value))
})
const estaSeleccionada = (value) =>
  Array.isArray(props.modelValue) && props.modelValue.includes(value)

function cerrarAlHacerClickFuera(evento) {
  if (!contenedor.value?.contains(evento.target)) abierto.value = false
}

function elegir(option) {
  if (props.multiple) {
    const current = Array.isArray(props.modelValue) ? props.modelValue : []
    const next = current.includes(option.value)
      ? current.filter((value) => value !== option.value)
      : [...current, option.value]
    emit('update:modelValue', next)
  } else {
    emit('update:modelValue', option.value)
    query.value = ''
    abierto.value = false
  }
}

function agregarCoincidencias() {
  const current = Array.isArray(props.modelValue) ? props.modelValue : []
  const matches = filtradas.value.map((option) => option.value)
  emit('update:modelValue', [...new Set([...current, ...matches])])
  query.value = ''
}

function quitar(value) {
  const current = Array.isArray(props.modelValue) ? props.modelValue : []
  emit('update:modelValue', current.filter((item) => item !== value))
}

onMounted(() => document.addEventListener('pointerdown', cerrarAlHacerClickFuera))
onUnmounted(() => document.removeEventListener('pointerdown', cerrarAlHacerClickFuera))
</script>

<template>
  <div ref="contenedor" class="search-select">
    <div v-if="multiple && seleccionadas.length" class="search-select__chips">
      <span v-for="option in seleccionadas" :key="option.value" class="search-select__chip">
        {{ option.label }}
        <button type="button" :aria-label="`Quitar ${option.label}`" @click="quitar(option.value)">×</button>
      </span>
    </div>
    <div v-else-if="!multiple && seleccionadas.length && !abierto" class="search-select__current">
      {{ seleccionadas[0].label }}
      <button v-if="modelValue !== ''" type="button" class="sec" @click="emit('update:modelValue', '')">Limpiar</button>
    </div>
    <input
      type="search"
      :value="query"
      :placeholder="placeholder"
      autocomplete="off"
      :aria-expanded="abierto"
      @focus="abierto = true"
      @input="query = $event.target.value; abierto = true"
      @keydown.esc="abierto = false"
    />
    <div v-if="abierto" class="search-select__menu">
      <button
        v-if="!multiple && emptyLabel"
        type="button"
        class="search-select__option"
        @click="emit('update:modelValue', ''); query = ''; abierto = false"
      >{{ emptyLabel }}</button>
      <button
        v-for="option in filtradas"
        :key="option.value"
        type="button"
        class="search-select__option"
        :class="{ selected: multiple && estaSeleccionada(option.value) }"
        @click="elegir(option)"
      >
        <span v-if="multiple" aria-hidden="true">{{ estaSeleccionada(option.value) ? '✓ ' : '' }}</span>
        {{ option.label }}
      </button>
      <p v-if="!filtradas.length" class="search-select__empty">No hay coincidencias.</p>
      <button
        v-if="multiple && filtradas.length"
        type="button"
        class="search-select__add"
        @click="agregarCoincidencias"
      >Agregar coincidencias ({{ filtradas.length }})</button>
    </div>
  </div>
</template>
