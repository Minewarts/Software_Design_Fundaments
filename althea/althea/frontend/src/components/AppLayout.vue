<script setup>
const logo = Object.values(import.meta.glob('../assets/images/logo.*', { eager: true, import: 'default', query: '?url' }))[0]
const otros = ['Proveedores', 'Viajes', 'Cotizaciones', 'Ventas', 'Consultas', 'Configuración'] // fuera del release 1
</script>
<template>
  <div class="shell">
    <aside class="side">
      <img v-if="logo" :src="logo" alt="Althea Gestión Turística" />
      <span v-for="o in otros" :key="o">{{ o }}</span>
      <a class="on">Planes Inteligentes</a>
    </aside>
    <div>
      <nav class="tabs">
        <router-link to="/catalogo">Gestión de Catálogo</router-link>
        <router-link to="/disenio">Diseño de Planes</router-link>
        <router-link to="/directorio">Directorio de Planes</router-link>
      </nav>
      <main><router-view /></main>
    </div>
  </div>
</template>
