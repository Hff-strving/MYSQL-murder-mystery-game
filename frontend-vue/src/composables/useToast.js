import { ref } from 'vue'

const toastMessage = ref('')
const toastVisible = ref(false)
const toastType = ref('success') // 'success' | 'error'

export function useToast() {
  const showToast = (message, isError = false) => {
    toastMessage.value = message
    toastType.value = isError ? 'error' : 'success'
    toastVisible.value = true

    setTimeout(() => {
      toastVisible.value = false
    }, 3000)
  }

  return {
    toastMessage,
    toastVisible,
    toastType,
    showToast
  }
}
