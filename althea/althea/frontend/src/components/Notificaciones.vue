<script setup>
// HU-16: notificaciones de cambios en el plan (dentro de la app, con sondeo cada 30 s).
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { notificaciones } from '../services/api'
const lista = ref([]), abierto = ref(false)
let timer
const sinLeer = computed(() => lista.value.filter((n) => !n.leida).length)
const cargar = async () => { try { lista.value = await notificaciones.listar() } catch { /* backend no disponible */ } }
async function alternar() {
  abierto.value = !abierto.value
  if (!abierto.value && sinLeer.value) { await notificaciones.leerTodas(); await cargar() }
}
onMounted(() => { cargar(); timer = setInterval(cargar, 30000) })
onUnmounted(() => clearInterval(timer))
</script>
<template>
  <div class="bell">
    <button @click="alternar" aria-label="Notificaciones">🔔</button><b v-if="sinLeer">{{ sinLeer }}</b>
    <div v-if="abierto" class="drop">
      <p v-if="!lista.length" class="mut" style="padding:8px">Sin notificaciones.</p>
      <router-link v-for="n in lista" :key="n.id" :to="`/plan/${n.id_plan}`" :class="{ nuevo: !n.leida }" @click="abierto = false">
        <b style="position:static;background:none;color:inherit;padding:0;font-size:13px">{{ n.titulo }}</b><br />{{ n.mensaje }}
      </router-link>
    </div>
  </div>
</template>
