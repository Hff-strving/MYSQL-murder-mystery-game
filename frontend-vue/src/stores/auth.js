import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { AuthAPI } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null'))

  function normalizeUserInfo(raw) {
    if (!raw || typeof raw !== 'object') return null

    const user_id = raw.user_id ?? raw.User_ID ?? raw.userId ?? null
    const username = raw.username ?? raw.Username ?? raw.user_name ?? raw.UserName ?? null
    const role = raw.role ?? raw.Role ?? null
    const ref_id = raw.ref_id ?? raw.Ref_ID ?? raw.refId ?? null

    if (!user_id || !username || !role) return null

    return { user_id, username, role, ref_id }
  }

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const isPlayer = computed(() => userInfo.value?.role === 'player')
  const isStaff = computed(() => userInfo.value?.role === 'staff')
  const isBoss = computed(() => userInfo.value?.role === 'boss')
  const username = computed(() => userInfo.value?.username || '')
  const role = computed(() => userInfo.value?.role || '')
  const refId = computed(() => userInfo.value?.ref_id || null)

  // 同步用户信息（从后端获取最新数据）
  async function syncUserInfo() {
    if (!token.value) return false

    try {
      const data = await AuthAPI.getCurrentUser()
      const normalized = normalizeUserInfo(data)
      if (!normalized) {
        console.warn('[Auth] /api/me 返回数据不符合预期，跳过覆盖本地登录态:', data)
        return false
      }

      userInfo.value = normalized
      localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
      console.log('[Auth] 用户信息已同步:', userInfo.value)
      return true
    } catch (error) {
      console.error('[Auth] 同步用户信息失败:', error)
      // 如果token失效，清除登录态
      if (error.message?.includes('401') || error.message?.includes('token')) {
        logout()
      }
      return false
    }
  }

  // 登录
  function login(loginData) {
    token.value = loginData.token
    const normalized = normalizeUserInfo(loginData)
    if (!normalized) {
      throw new Error('登录返回的用户信息缺失，无法保存登录态')
    }
    userInfo.value = normalized
    localStorage.setItem('token', token.value)
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
  }

  // 退出登录
  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isPlayer,
    isStaff,
    isBoss,
    username,
    role,
    refId,
    login,
    logout,
    syncUserInfo
  }
})
