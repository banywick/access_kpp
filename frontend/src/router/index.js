// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Contractor',
    component: () => import('../views/ContractorView.vue'),
    meta: { title: 'Подрядчик | Контроль доступа' }
  },
  {
    path: '/guard',
    name: 'Guard',
    component: () => import('../views/GuardView.vue'),
    meta: { title: 'Охрана | Контроль доступа' }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/AdminView.vue'),
    meta: { title: 'Админ | Контроль доступа' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || 'Контроль доступа'
  next()
})

export default router