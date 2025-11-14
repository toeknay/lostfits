<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <ToastContainer />
    <header class="bg-slate-900 text-white shadow-lg">
      <div class="container mx-auto px-4 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-8">
            <router-link to="/" class="text-2xl font-bold hover:text-blue-400 transition">
              LostFits
            </router-link>
            <nav class="hidden md:flex space-x-6">
              <router-link
                to="/"
                class="hover:text-blue-400 transition"
                :class="{ 'text-blue-400': $route.path === '/' }"
              >
                Dashboard
              </router-link>
              <router-link
                to="/fits"
                class="hover:text-blue-400 transition"
                :class="{ 'text-blue-400': $route.path.startsWith('/fits') }"
              >
                Fits Browser
              </router-link>
            </nav>
          </div>
          <div class="text-sm text-slate-400">
            EVE Online Killmail Tracker
          </div>
        </div>
      </div>
    </header>
    <main class="container mx-auto px-4 py-8">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import ToastContainer from './components/ToastContainer.vue'
</script>
