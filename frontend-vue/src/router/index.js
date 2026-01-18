import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/scripts/:id',
    name: 'ScriptDetail',
    component: () => import('@/views/ScriptDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('@/views/Orders.vue'),
    meta: { requiresAuth: true, requiresPlayer: true }
  },
  {
    path: '/my-locks',
    name: 'MyLocks',
    component: () => import('@/views/MyLocks.vue'),
    meta: { requiresAuth: true, requiresPlayer: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('@/views/AdminDashboard.vue'),
    meta: { requiresAuth: true, requiresStaff: true }
  },
  {
    path: '/admin/schedules',
    name: 'AdminSchedules',
    component: () => import('@/views/AdminSchedules.vue'),
    meta: { requiresAuth: true, requiresStaff: true }
  },
  {
    path: '/admin/reports',
    name: 'AdminReports',
    component: () => import('@/views/AdminReports.vue'),
    meta: { requiresAuth: true, requiresStaff: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 需要登录
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
    return
  }

  // 如果已登录且需要权限验证，先同步用户信息
  if (authStore.isLoggedIn && (to.meta.requiresPlayer || to.meta.requiresStaff)) {
    await authStore.syncUserInfo()
  }

  // 需要玩家权限
  if (to.meta.requiresPlayer && !authStore.isPlayer) {
    window.dispatchEvent(new CustomEvent('show-toast', {
      detail: { message: `此功能仅限玩家使用（当前角色：${authStore.role || '未知'}）`, type: 'error' }
    }))
    next('/')
    return
  }

  // 需要员工权限
  if (to.meta.requiresStaff && !(authStore.isStaff || authStore.isBoss)) {
    window.dispatchEvent(new CustomEvent('show-toast', {
      detail: { message: `此功能仅限员工/老板使用（当前角色：${authStore.role || '未知'}）`, type: 'error' }
    }))
    next('/')
    return
  }

  next()
})

export default router
