import { createRouter, createWebHistory } from 'vue-router'
import { currentUserRole, routeRoles } from '../rolePolicy'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('../views/LoginView.vue') },
    {
      path: '/',
      component: () => import('../views/ShellView.vue'),
      children: [
        { path: '', component: () => import('../views/DashboardView.vue'), meta: { roles: routeRoles.dashboard } },
        { path: 'patients', component: () => import('../views/PatientsView.vue'), meta: { roles: routeRoles.patients } },
        { path: 'imaging', component: () => import('../views/ImagingView.vue'), meta: { roles: routeRoles.imaging } },
        { path: 'analysis', component: () => import('../views/AnalysisView.vue'), meta: { roles: routeRoles.analysis } },
        { path: 'audit', component: () => import('../views/AuditView.vue'), meta: { roles: routeRoles.audit } },
        { path: 'users', component: () => import('../views/UsersView.vue'), meta: { roles: routeRoles.users } },
        { path: '403', component: () => import('../views/ForbiddenView.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('pcr_token')
  if (to.path !== '/login' && !token) return '/login'
  if (to.path === '/login' && token) return '/'
  const allowedRoles = to.meta.roles as string[] | undefined
  if (allowedRoles?.length) {
    const role = currentUserRole()
    if (!role || !allowedRoles.includes(role)) return '/403'
  }
  return true
})
