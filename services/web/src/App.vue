<script setup lang="ts">
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-gray-100">
    <nav class="bg-gray-800 border-b border-gray-700">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center">
            <router-link to="/" class="text-2xl font-bold text-blue-400">
              LostFits
            </router-link>
          </div>
          <div class="flex space-x-4">
            <router-link
              to="/"
              class="px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-700 transition"
            >
              Dashboard
            </router-link>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <router-view />
    </main>
  </div>
</template>
