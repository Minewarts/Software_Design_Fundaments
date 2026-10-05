<script setup>
import { ref, computed, onMounted } from 'vue'
import { planes } from '../services/api'
import { cop } from '../utils/format'
const lista = ref([]), estado = ref('')
const visibles = computed(() => lista.value.filter((p) => !estado.value || p.estado === estado.value))
onMounted(async () => { lista.value = await planes.listar() })
</script>
<template>
  <section class="card">
    <h2>Directorio de Planes Turísticos</h2>
    <div class="row" style="margin-bottom:12px"><label>Estado<select v-model="estado"><option value="">Todos</option>
      <option v-for="e in ['BORRADOR','APROBADO','ARCHIVADO']" :key="e">{{ e }}</option></select></label></div>
    <table>
      <tr><th>Plan</th><th>Estado</th><th>Costo estimado</th><th></th></tr>
      <tr v-for="p in visibles" :key="p.id"><td><b>{{ p.titulo }}</b></td>
        <td><span class="pill" :class="p.estado">{{ p.estado }}</span></td><td>{{ cop(p.costo_estimado) }}</td>
        <td><router-link class="btn" :to="`/plan/${p.id}`">Ver ficha</router-link></td></tr>
    </table>
    <p v-if="!visibles.length" class="mut">No hay planes para mostrar.</p>
  </section>
</template>
