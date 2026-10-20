<script setup>
// HU-10 consultar planes · HU-11 filtros avanzados · HU-14 duplicar como plantilla.
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { planes } from '../services/api'
import { cop } from '../utils/format'
import StarRating from '../components/StarRating.vue'
const router = useRouter()
const VACIO = { destino: '', estado: '', precio_min: '', precio_max: '', dias_max: '' }
const lista = ref([]), f = ref({ ...VACIO }), origen = ref(''), error = ref('')
const cuenta = (e) => lista.value.filter((p) => p.estado === e).length
async function buscar() { try { error.value = ''; lista.value = await planes.listar(f.value) } catch (e) { error.value = e.message } }
function limpiar() { f.value = { ...VACIO }; buscar() }
async function duplicar() { try { const n = await planes.duplicar(origen.value); router.push(`/plan/${n.id}`) } catch (e) { error.value = e.message } }
onMounted(buscar)
</script>
<template>
  <section class="card">
    <h2>1. Directorio de Planes Turísticos</h2>
    <form class="row" style="margin-bottom:14px" @submit.prevent="buscar">
      <label>Destino<input v-model="f.destino" placeholder="San Andrés" /></label>
      <label>Estado<select v-model="f.estado"><option value="">Todos</option><option v-for="e in ['BORRADOR','APROBADO','ARCHIVADO']" :key="e">{{ e }}</option></select></label>
      <label>Precio mín.<input type="number" min="0" v-model="f.precio_min" style="width:130px" /></label>
      <label>Precio máx.<input type="number" min="0" v-model="f.precio_max" style="width:130px" /></label>
      <label>Duración máx. (días)<input type="number" min="1" v-model="f.dias_max" style="width:120px" /></label>
      <button>Buscar</button><button type="button" class="sec" @click="limpiar">Limpiar</button>
    </form>
    <p class="err">{{ error }}</p>
    <table>
      <tr><th>Plan</th><th>Destino</th><th>Duración</th><th>Precio</th><th>Estado</th><th>Calificación</th><th></th></tr>
      <tr v-for="p in lista" :key="p.id"><td><b>{{ p.titulo }}</b></td><td>{{ p.destino ?? '—' }}</td>
        <td>{{ p.duracion ?? '—' }} días</td><td>{{ cop(p.costo_estimado) }}</td>
        <td><span class="pill" :class="p.estado">{{ p.estado }}</span></td>
        <td><StarRating :model-value="Math.round(p.calificacion ?? 0)" readonly /></td>
        <td><router-link class="btn" :to="`/plan/${p.id}`">Ver ficha</router-link></td></tr>
    </table>
    <p v-if="!lista.length" class="mut">No hay planes para mostrar.</p>
  </section>
  <section class="card">
    <h2>2. Resumen y plantillas</h2>
    <div class="stats"><div>Total<b>{{ lista.length }}</b></div><div>Aprobados<b>{{ cuenta('APROBADO') }}</b></div>
      <div>Borradores<b>{{ cuenta('BORRADOR') }}</b></div><div>Archivados<b>{{ cuenta('ARCHIVADO') }}</b></div></div>
    <div class="row"><label>Duplicar plan como plantilla
      <select v-model="origen"><option v-for="p in lista" :key="p.id" :value="p.id">{{ p.titulo }}</option></select></label>
      <button :disabled="!origen" @click="duplicar">Duplicar plan</button></div>
  </section>
</template>
