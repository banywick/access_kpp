// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import WelcomeView from '../views/WelcomeView.vue'
import ContractorView from '../views/ContractorView.vue'
import GuardView from '../views/GuardView.vue'
import AdminView from '../views/AdminView.vue'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: WelcomeView,
    meta: { title: 'Электронный пропуск' }
  },
  {
    path: '/dashboard',
    name: 'Contractor',
    component: ContractorView,
    meta: { title: 'Личный кабинет | Электронный пропуск' }
  },
  {
    path: '/guard',
    name: 'Guard',
    component: GuardView,
    meta: { title: 'Охрана | Электронный пропуск' }
  },
  {
    path: '/dashboard-admin',
    name: 'Admin',
    component: AdminView,
    meta: { title: 'Администрирование | Электронный пропуск' }
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
  document.title = to.meta.title || 'Электронный пропуск'
  next()
})

export default router