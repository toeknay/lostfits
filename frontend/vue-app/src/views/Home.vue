<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'

async function apiHello() {
  const res = await fetch('/api/hello')
  return await res.json()
}

const { data, isLoading, error } = useQuery({
  queryKey: ['hello'],
  queryFn: apiHello,
})
</script>

<template>
  <div class="space-y-4">
    <p class="text-lg">Welcome to <strong>LostFits</strong>.</p>
    <div v-if="isLoading">Loading API…</div>
    <div v-else-if="error">Failed to reach API.</div>
    <pre v-else class="p-3 bg-white rounded border">{{ data }}</pre>
  </div>
</template>
