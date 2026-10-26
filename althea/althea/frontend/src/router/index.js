import { createRouter, createWebHistory } from 'vue-router'
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/catalogo' },
    { path: '/catalogo', component: () => import('../views/CatalogoView.vue') },
    { path: '/actividades', component: () => import('../views/ActividadesView.vue') },
    { path: '/disenio', component: () => import('../views/DisenoPlanView.vue') },
    { path: '/directorio', component: () => import('../views/DirectorioView.vue') },
    { path: '/plan/:id', component: () => import('../views/FichaPlanView.vue'), props: true },
  ],
})
