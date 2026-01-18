<template>
  <div class="auth-container">
    <div class="auth-box">
      <h1 class="auth-title">🎭 剧本杀店务管理系统</h1>
      <h2 class="auth-subtitle">玩家注册</h2>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label>用户名</label>
          <input
            v-model="formData.username"
            type="text"
            required
            placeholder="请输入用户名（3-50字符）"
          >
        </div>

        <div class="form-group">
          <label>手机号</label>
          <input
            v-model="formData.phone"
            type="tel"
            required
            placeholder="请输入手机号"
          >
        </div>

        <div class="form-group">
          <label>密码</label>
          <input
            v-model="formData.password"
            type="password"
            required
            placeholder="请输入密码（至少6位）"
          >
        </div>

        <div class="form-group">
          <label>确认密码</label>
          <input
            v-model="formData.confirmPassword"
            type="password"
            required
            placeholder="请再次输入密码"
          >
        </div>

        <button type="submit" class="btn-primary btn-block" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>

      <div class="auth-footer">
        已有账号？<router-link to="/login">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { AuthAPI } from '@/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { showToast } = useToast()

const loading = ref(false)
const formData = ref({
  username: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const handleRegister = async () => {
  if (formData.value.password !== formData.value.confirmPassword) {
    showToast('两次输入的密码不一致', true)
    return
  }

  loading.value = true
  try {
    await AuthAPI.register(
      formData.value.username,
      formData.value.phone,
      formData.value.password
    )
    showToast('注册成功！请登录')
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (error) {
    showToast(error.message || '注册失败', true)
  } finally {
    loading.value = false
  }
}
</script>
