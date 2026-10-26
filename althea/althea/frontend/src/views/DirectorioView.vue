<script setup>
// Consulta de planes con filtros y opción para duplicar como plantilla.
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { planes, recursos } from '../services/api'
import { cop } from '../utils/format'
import StarRating from '../components/StarRating.vue'
import SearchableSelect from '../components/SearchableSelect.vue'
const router = useRouter()
const VACIO = { destino: '', estado: '', precio_min: '', precio_max: '', dias_max: '' }
const lista = ref([]), destinos = ref([]), f = ref({ ...VACIO }), origen = ref(''), error = ref('')
const cuenta = (e) => lista.value.filter((p) => p.estado === e).length
async function buscar() { try { error.value = ''; lista.value = await planes.listar(f.value) } catch (e) { error.value = e.message } }
function limpiar() { f.value = { ...VACIO }; buscar() }
async function duplicar() { try { const n = await planes.duplicar(origen.value); router.push(`/plan/${n.id}`) } catch (e) { error.value = e.message } }
onMounted(async () => {
  try {
    destinos.value = await recursos.listar('destinos')
    await buscar()
  } catch (e) { error.value = e.message }
})
</script>
<template>
  <section class="card">
    <h2>1. Directorio de Planes Turísticos</h2>
    <form class="row" style="margin-bottom:14px" @submit.prevent="buscar">
      <label>Destino
        <SearchableSelect
          v-model="f.destino"
          :options="destinos.map((d) => ({ value: d.nombre, label: d.nombre }))"
          empty-label="Todos los destinos"
          placeholder="Buscar o pegar destino…"
        />
      </label>
      <label>Estado
        <SearchableSelect
          v-model="f.estado"
          :options="['BORRADOR', 'APROBADO', 'ARCHIVADO'].map((e) => ({ value: e, label: e }))"
          empty-label="Todos"
          placeholder="Buscar estado…"
        />
      </label>
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
      <SearchableSelect
        v-model="origen"
        :options="lista.map((p) => ({ value: p.id, label: p.titulo }))"
        empty-label=""
        placeholder="Buscar o pegar el nombre del plan…"
      />
    </label>
      <button :disabled="!origen" @click="duplicar">Duplicar plan</button></div>
  </section>
</template>
