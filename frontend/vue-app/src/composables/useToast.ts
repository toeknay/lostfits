import { ref } from 'vue'

export type ToastType = 'error' | 'success' | 'info'

export interface Toast {
  id: number
  message: string
  type: ToastType
}

const toasts = ref<Toast[]>([])
let nextId = 1

export function useToast() {
  const showToast = (message: string, type: ToastType = 'info', duration = 5000) => {
    const id = nextId++
    toasts.value.push({ id, message, type })

    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  const removeToast = (id: number) => {
    const index = toasts.value.findIndex((t) => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  const showError = (message: string, duration = 5000) => {
    showToast(message, 'error', duration)
  }

  const showSuccess = (message: string, duration = 3000) => {
    showToast(message, 'success', duration)
  }

  return {
    toasts,
    showToast,
    showError,
    showSuccess,
    removeToast,
  }
}
