import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/chat' },
    { path: '/login', name: 'login', component: () => import('../views/LoginView.vue') },
    { path: '/chat', name: 'chat', component: () => import('../views/ChatView.vue'), meta: { requiresAuth: true } },
    { path: '/documents', name: 'documents', component: () => import('../views/DocumentsView.vue'), meta: { requiresAuth: true } },
    { path: '/knowledge', name: 'knowledge', component: () => import('../views/KnowledgeView.vue'), meta: { requiresAuth: true } },
    { path: '/resume', name: 'resume', component: () => import('../views/ResumeView.vue'), meta: { requiresAuth: true } },
  ],
})

// 登录守卫：未登录跳 /login，已登录访问 /login 跳回 /chat
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'login' && auth.isLoggedIn) {
    return { name: 'chat' }
  }
  return true
})

export default router
