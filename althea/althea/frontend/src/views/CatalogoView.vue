<script setup>
import { ref, onMounted } from 'vue'
import RecursoCrud from '../components/RecursoCrud.vue'
import { recursos } from '../services/api'
const CONFIG = {
  destinos: [{ key: 'nombre', label: 'Nombre', type: 'text' }, { key: 'ubicacion', label: 'Ubicación', type: 'text' },
             { key: 'clima_promedio', label: 'Clima promedio', type: 'text' }],
  alojamientos: [{ key: 'id_destino', label: 'Destino', type: 'destino' }, { key: 'nombre', label: 'Nombre', type: 'text' },
             { key: 'categoria_estrellas', label: 'Estrellas', type: 'number' }, { key: 'tarifa_noche', label: 'Tarifa/noche', type: 'number' }],
  actividades: [{ key: 'id_destino', label: 'Destino', type: 'destino' }, { key: 'nombre', label: 'Nombre', type: 'text' },
             { key: 'tipo_actividad', label: 'Tipo', type: 'text' }, { key: 'costo_persona', label: 'Costo/persona', type: 'number' }],
  transportes: [{ key: 'tipo_vehiculo', label: 'Tipo de vehículo', type: 'text' }, { key: 'tarifa_estimada', label: 'Tarifa estimada', type: 'number' },
             { key: 'ids_destinos', label: 'Destinos que sirve', type: 'destinos' }],
}
const tipo = ref('destinos'), relaciones = ref([])
const lista = (xs) => (xs ?? []).map((x) => x.nombre ?? x.tipo_vehiculo).join(', ') || '—'
onMounted(async () => { relaciones.value = await recursos.relaciones() })
</script>
<template>
  <section class="card">
    <h2>1. Gestión de Recursos Turísticos</h2>
    <div class="row" style="margin-bottom:14px">
      <button v-for="t in Object.keys(CONFIG)" :key="t" :class="{ sec: t !== tipo }" @click="tipo = t">{{ t }}</button>
    </div>
    <RecursoCrud :key="tipo" :tipo="tipo" :campos="CONFIG[tipo]" />
  </section>
  <section class="card">
    <h2>2. Interrelación de Recursos</h2>
    <p class="mut">Catálogo único: cada destino con sus alojamientos, actividades y transportes.</p>
    <table>
      <tr><th>Destino</th><th>Alojamientos</th><th>Actividades</th><th>Transporte</th></tr>
      <tr v-for="r in relaciones" :key="r.destino"><td><b>{{ r.destino }}</b></td>
        <td>{{ lista(r.alojamientos) }}</td><td>{{ lista(r.actividades) }}</td><td>{{ lista(r.transportes) }}</td></tr>
    </table>
  </section>
</template>
