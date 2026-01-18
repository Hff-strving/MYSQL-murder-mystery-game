<template>
  <div class="auth-container">
    <div class="auth-box">
      <h1 class="auth-title">🎭 剧本杀店务管理系统</h1>
      <h2 class="auth-subtitle">用户登录</h2>

      <!-- 角色切换按钮 -->
      <div class="role-switch">
        <button
          type="button"
          class="role-btn"
          :class="{ active: selectedRole === 'player' }"
          @click="selectedRole = 'player'"
        >
          <span class="role-icon">👤</span>
          <span class="role-text">玩家登录</span>
        </button>
        <button
          type="button"
          class="role-btn"
          :class="{ active: selectedRole === 'staff' }"
          @click="selectedRole = 'staff'"
        >
          <span class="role-icon">👔</span>
          <span class="role-text">员工/老板登录</span>
        </button>
      </div>

      <!-- 角色提示框 -->
      <div class="role-hint" :class="roleHintClass">
        <span class="hint-icon">{{ selectedRole === 'player' ? '👤' : '👔' }}</span>
        <span class="hint-text">
          您正在以<strong>{{ selectedRole === 'player' ? '玩家' : '员工/老板' }}</strong>身份登录
        </span>
      </div>

      <!-- 登录表单 -->
      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label>用户名/手机号</label>
          <input
            v-model="formData.username"
            type="text"
            required
            placeholder="请输入用户名或手机号"
          >
        </div>

        <div class="form-group">
          <label>密码</label>
          <input
            v-model="formData.password"
            type="password"
            required
            placeholder="请输入密码"
          >
        </div>

        <button type="submit" class="btn-primary btn-block" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>

      <div class="auth-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
        <span class="footer-note">（仅限玩家注册，员工账号请联系管理员）</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { AuthAPI } from '@/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const authStore = useAuthStore()
const { showToast } = useToast()

const selectedRole = ref('player')
const loading = ref(false)
const formData = ref({
  username: '',
  password: ''
})

const roleHintClass = computed(() => {
  return selectedRole.value === 'player' ? 'role-hint-player' : 'role-hint-staff'
})

const handleLogin = async () => {
  loading.value = true
  try {
    const result = await AuthAPI.login(formData.value.username, formData.value.password)

    const isPlayerLogin = selectedRole.value === 'player'
    const roleOk = isPlayerLogin
      ? result.role === 'player'
      : (result.role === 'staff' || result.role === 'boss')

    if (!roleOk) {
      showToast(`当前账号角色为「${result.role}」，与选择的登录身份不匹配`, true)
      return
    }

    authStore.login(result)
    showToast('登录成功！')
    setTimeout(() => {
      router.push(result.role === 'player' ? '/' : '/admin')
    }, 1000)
  } catch (error) {
    showToast(error.message || '登录失败', true)
  } finally {
    loading.value = false
  }
}
</script>
