import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/products', name: 'Products', component: () => import('../views/Products.vue') },
  { path: '/reviews', name: 'Reviews', component: () => import('../views/Reviews.vue') },
  { path: '/reports', name: 'Reports', component: () => import('../views/Reports.vue') },
  { path: '/report', name: 'Report', component: () => import('../views/Report.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
