import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
import Analysis from '../views/Analysis.vue'
import Reports from '../views/Reports.vue'
import Database from '../views/Database.vue'
import Login from '../views/Login.vue'
import { isAuthenticated } from '../services/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { guest: true },
  },
  {
    path: '/',
    redirect: () => (isAuthenticated() ? '/analysis' : '/login'),
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: Analysis,
    meta: { requiresAuth: true },
  },
  {
    path: '/database',
    name: 'Database',
    component: Database,
    meta: { requiresAuth: true },
  },
  {
    path: '/reports',
    name: 'Reports',
    component: Reports,
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: import.meta.env.BASE_URL === '/'
    ? createWebHistory()
    : createWebHashHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to) => {
  const authed = isAuthenticated()

  if (to.meta.guest) {
    return authed ? '/analysis' : true
  }

  if (to.meta.requiresAuth && !authed) {
    return '/login'
  }

  return true
})

export default router
