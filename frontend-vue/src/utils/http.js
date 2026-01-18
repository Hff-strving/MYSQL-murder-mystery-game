import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 创建axios实例
const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动添加token
http.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误
http.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code === 200) {
      return res.data
    } else {
      return Promise.reject(new Error(res.message || '请求失败'))
    }
  },
  (error) => {
    const authStore = useAuthStore()

    if (error.response) {
      switch (error.response.status) {
        case 401:
          authStore.logout()
          router.push('/login')
          return Promise.reject(new Error('登录已过期，请重新登录'))
        case 403:
          return Promise.reject(new Error('无权限访问'))
        case 404:
          return Promise.reject(new Error('请求的资源不存在'))
        default:
          return Promise.reject(new Error(error.response.data?.message || '请求失败'))
      }
    }
    return Promise.reject(error)
  }
)

export default http
