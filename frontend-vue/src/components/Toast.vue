<template>
  <Transition name="toast">
    <div v-if="toastVisible" class="toast" :class="{ error: toastType === 'error' }">
      {{ toastMessage }}
    </div>
  </Transition>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useToast } from '@/composables/useToast'

const { toastMessage, toastVisible, toastType, showToast } = useToast()

// 监听全局 toast 事件（用于路由守卫等场景）
const handleToastEvent = (event) => {
  const { message, type } = event.detail
  showToast(message, type === 'error')
}

onMounted(() => {
  window.addEventListener('show-toast', handleToastEvent)
})

onUnmounted(() => {
  window.removeEventListener('show-toast', handleToastEvent)
})
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}

.toast-leave-to {
  opacity: 0;
}
</style>
