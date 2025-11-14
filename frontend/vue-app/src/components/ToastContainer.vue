<template>
  <div class="fixed top-4 right-4 z-50 space-y-2 max-w-md">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="p-4 rounded-lg shadow-lg flex items-center justify-between animate-slide-in"
      :class="{
        'bg-red-100 text-red-900 border border-red-300': toast.type === 'error',
        'bg-green-100 text-green-900 border border-green-300': toast.type === 'success',
        'bg-blue-100 text-blue-900 border border-blue-300': toast.type === 'info',
      }"
    >
      <div class="flex items-center space-x-3">
        <span v-if="toast.type === 'error'" class="text-2xl">⚠️</span>
        <span v-if="toast.type === 'success'" class="text-2xl">✅</span>
        <span v-if="toast.type === 'info'" class="text-2xl">ℹ️</span>
        <span class="font-medium">{{ toast.message }}</span>
      </div>
      <button
        @click="removeToast(toast.id)"
        class="ml-4 text-gray-500 hover:text-gray-700"
      >
        ✕
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from '../composables/useToast'

const { toasts, removeToast } = useToast()
</script>

<style scoped>
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}
</style>
