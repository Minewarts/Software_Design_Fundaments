import { createRouter, createWebHistory } from 'vue-router'
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/catalogo' },
    { path: '/catalogo', component: () => import('../views/CatalogoView.vue') },       // HU-01..05
    { path: '/disenio', component: () => import('../views/DisenoPlanView.vue') },      // HU-06, HU-08
    { path: '/directorio', component: () => import('../views/DirectorioView.vue') },   // HU-10
    { path: '/plan/:id', component: () => import('../views/FichaPlanView.vue'), props: true }, // HU-12, HU-17
  ],
})
