<template>
  <div id="app">
    <AppHeader v-if="!isLoginPage" />
    <router-view />
    <footer class="footer">
      <p>&copy; 2025 剧本杀店务管理系统 | 数据库设计课程大作业</p>
    </footer>
    <Toast />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import Toast from '@/components/Toast.vue'

const route = useRoute()
const isLoginPage = computed(() => {
  return route.path === '/login' || route.path === '/register'
})
</script>

<style>
@import '@/assets/styles/main.css';
</style>
