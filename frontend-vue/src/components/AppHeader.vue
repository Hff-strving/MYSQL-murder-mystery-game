<template>
  <header class="header">
    <div class="container">
      <h1 class="logo">🎭 剧本杀店务管理系统</h1>
      <nav class="nav">
        <!-- 剧本大厅 -->
        <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
          剧本大厅
        </router-link>

        <!-- 玩家导航 -->
        <template v-if="authStore.isPlayer">
          <router-link to="/orders" class="nav-link" :class="{ active: $route.path === '/orders' }">
            我的订单
          </router-link>
          <router-link to="/my-locks" class="nav-link" :class="{ active: $route.path === '/my-locks' }">
            我的锁位
          </router-link>
        </template>

        <!-- 员工/老板导航 -->
        <template v-if="authStore.isStaff || authStore.isBoss">
          <router-link to="/admin" class="nav-link" :class="{ active: $route.path === '/admin' }">
            {{ authStore.isBoss ? '老板后台' : '管理后台' }}
          </router-link>
          <router-link to="/admin/schedules" class="nav-link" :class="{ active: $route.path === '/admin/schedules' }">
            场次管理
          </router-link>
          <router-link to="/admin/reports" class="nav-link" :class="{ active: $route.path === '/admin/reports' }">
            综合报表
          </router-link>
        </template>

        <!-- 已登录：用户下拉菜单 -->
        <div v-if="authStore.isLoggedIn" class="nav-user-dropdown">
          <div class="nav-user-info">
            <span class="user-icon">{{ authStore.isPlayer ? '👤' : '👔' }}</span>
            <span class="user-name">{{ authStore.username }}</span>
            <span class="user-role">{{ authStore.isPlayer ? '玩家' : (authStore.isBoss ? '老板' : '员工') }}</span>
            <span class="dropdown-arrow">▼</span>
          </div>
          <div class="dropdown-menu">
            <div class="dropdown-info">
              <div class="info-row">
                <span class="info-label">角色：</span>
                <span class="info-value">{{ authStore.role }}</span>
              </div>
              <div class="info-row" v-if="authStore.userInfo?.user_id">
                <span class="info-label">用户ID：</span>
                <span class="info-value">{{ authStore.userInfo.user_id }}</span>
              </div>
              <div class="info-row" v-if="authStore.refId">
                <span class="info-label">关联ID：</span>
                <span class="info-value">{{ authStore.refId }}</span>
              </div>
            </div>
            <div class="dropdown-divider"></div>
            <router-link to="/profile" class="dropdown-item">
              <span class="item-icon">📋</span>
              <span>个人中心</span>
            </router-link>
            <a href="#" class="dropdown-item logout" @click.prevent="handleLogout">
              <span class="item-icon">🚪</span>
              <span>退出登录</span>
            </a>
          </div>
        </div>

        <!-- 未登录 -->
        <template v-else>
          <router-link to="/login" class="nav-link">登录</router-link>
          <router-link to="/register" class="nav-link">注册</router-link>
        </template>
      </nav>
    </div>
  </header>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'

const authStore = useAuthStore()
const router = useRouter()
const { showToast } = useToast()

const handleLogout = () => {
  authStore.logout()
  showToast('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.dropdown-info {
  padding: 0.75rem 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
  font-size: 0.85rem;
}

.info-label {
  color: #666;
  font-weight: 500;
}

.info-value {
  color: #333;
  font-weight: 600;
}

.dropdown-divider {
  height: 1px;
  background: #e9ecef;
  margin: 0.5rem 0;
}
</style>
