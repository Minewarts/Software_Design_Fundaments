<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { TOAST_EVENT } from '../utils/toast'

const notificaciones = ref([])
const temporizadores = new Map()
let siguienteId = 0

function mostrar(evento) {
  const id = ++siguienteId
  const notificacion = { id, ...evento.detail }
  notificaciones.value.push(notificacion)
  temporizadores.set(id, window.setTimeout(() => quitar(id), evento.detail.tipo === 'error' ? 7000 : 4500))
}

function quitar(id) {
  window.clearTimeout(temporizadores.get(id))
  temporizadores.delete(id)
  notificaciones.value = notificaciones.value.filter((notificacion) => notificacion.id !== id)
}

onMounted(() => window.addEventListener(TOAST_EVENT, mostrar))
onUnmounted(() => {
  window.removeEventListener(TOAST_EVENT, mostrar)
  temporizadores.forEach((temporizador) => window.clearTimeout(temporizador))
  temporizadores.clear()
})
</script>

<template>
  <div class="toast-stack" aria-live="polite" aria-relevant="additions">
    <TransitionGroup name="toast">
      <div
        v-for="notificacion in notificaciones"
        :key="notificacion.id"
        class="toast"
        :class="`toast--${notificacion.tipo}`"
        :role="notificacion.tipo === 'error' ? 'alert' : 'status'"
      >
        <span class="toast__icon" aria-hidden="true">{{ notificacion.tipo === 'error' ? '!' : '✓' }}</span>
        <span class="toast__message">{{ notificacion.mensaje }}</span>
        <button
          type="button"
          class="toast__close"
          aria-label="Cerrar notificación"
          @click="quitar(notificacion.id)"
        >×</button>
      </div>
    </TransitionGroup>
  </div>
</template>
