<template>
  <main class="main-content">
    <div class="container">
      <div class="page-header">
        <h2 class="page-title">个人中心</h2>
      </div>

      <div class="profile-container">
        <!-- 用户信息卡片 -->
        <div class="profile-card">
          <div class="profile-header">
            <div class="profile-avatar">
              {{ authStore.isPlayer ? '👤' : (authStore.isBoss ? '👑' : '👔') }}
            </div>
            <div class="profile-info">
              <h3 class="profile-name">{{ authStore.username }}</h3>
              <span class="profile-role" :class="authStore.isPlayer ? 'role-player' : 'role-staff'">
                {{ authStore.isPlayer ? '玩家' : (authStore.isBoss ? '老板' : '员工') }}
              </span>
            </div>
          </div>

          <div class="profile-details">
            <div class="detail-item">
              <span class="detail-label">用户ID</span>
              <span class="detail-value">{{ authStore.userInfo?.user_id }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">角色</span>
              <span class="detail-value">{{ authStore.role }}</span>
            </div>
            <div v-if="authStore.refId" class="detail-item">
              <span class="detail-label">关联ID</span>
              <span class="detail-value">{{ authStore.refId }}</span>
            </div>
          </div>

          <div class="profile-actions">
            <button class="btn-primary btn-block" @click="handleLogout">
              退出登录
            </button>
          </div>
        </div>

        <!-- 快捷入口 -->
        <div class="quick-links">
          <h3>快捷入口</h3>
          <div class="links-grid">
            <router-link v-if="authStore.isPlayer" to="/orders" class="link-card">
              <span class="link-icon">📋</span>
              <span class="link-text">我的订单</span>
            </router-link>
            <router-link v-if="authStore.isPlayer" to="/my-locks" class="link-card">
              <span class="link-icon">🔒</span>
              <span class="link-text">我的锁位</span>
            </router-link>
            <router-link v-if="authStore.isStaff || authStore.isBoss" to="/admin" class="link-card">
              <span class="link-icon">⚙️</span>
              <span class="link-text">管理后台</span>
            </router-link>
            <router-link to="/" class="link-card">
              <span class="link-icon">🎭</span>
              <span class="link-text">剧本大厅</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const authStore = useAuthStore()
const { showToast } = useToast()

const handleLogout = () => {
  authStore.logout()
  showToast('已退出登录')
  setTimeout(() => {
    router.push('/login')
  }, 1000)
}
</script>

<style scoped>
.main-content {
  padding: 2rem;
  min-height: 100vh;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 600;
  color: #d4af37;
}

.profile-container {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 2rem;
  align-items: start;
}

/* 用户信息卡片 - 暗黑主题 */
.profile-card {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);
}

.profile-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #d4af37 0%, #f4d03f 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  flex-shrink: 0;
  box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
}

.profile-info {
  flex: 1;
}

.profile-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e0e0e0;
  margin: 0 0 0.5rem 0;
}

.profile-role {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.role-player {
  background: rgba(33, 150, 243, 0.2);
  color: #64b5f6;
  border: 1px solid rgba(33, 150, 243, 0.3);
}

.role-staff {
  background: rgba(255, 152, 0, 0.2);
  color: #ffb74d;
  border: 1px solid rgba(255, 152, 0, 0.3);
}

.profile-details {
  margin-bottom: 2rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid rgba(212, 175, 55, 0.1);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 0.9rem;
  color: #999;
}

.detail-value {
  font-size: 0.95rem;
  font-weight: 500;
  color: #d4af37;
}

.profile-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid rgba(212, 175, 55, 0.2);
}

.btn-primary {
  padding: 0.6rem 1.5rem;
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.5);
}

/* 快捷入口 - 暗黑主题 */
.quick-links {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(212, 175, 55, 0.2);
}

.quick-links h3 {
  font-size: 1.3rem;
  font-weight: 600;
  color: #d4af37;
  margin: 0 0 1.5rem 0;
}

.links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 1rem;
}

.link-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1.5rem 1rem;
  background: rgba(212, 175, 55, 0.1);
  border-radius: 8px;
  text-decoration: none;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.link-card:hover {
  background: rgba(212, 175, 55, 0.2);
  border-color: #d4af37;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
}

.link-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.link-text {
  font-size: 0.95rem;
  font-weight: 500;
  color: #e0e0e0;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .profile-container {
    grid-template-columns: 1fr;
  }

  .profile-header {
    flex-direction: column;
    text-align: center;
  }

  .links-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .profile-actions {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .main-content {
    padding: 1rem;
  }

  .links-grid {
    grid-template-columns: 1fr;
  }
}
</style>
