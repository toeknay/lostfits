<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'

const router = useRouter()
const { showError } = useToast()

async function fetchStats() {
  const res = await fetch('/api/stats')
  if (!res.ok) {
    throw new Error(res.status === 503 ? 'Service temporarily unavailable' : 'Failed to load statistics')
  }
  return await res.json()
}

async function fetchPopularShips() {
  const res = await fetch('/api/fits/ships/popular?limit=5&days=7')
  if (!res.ok) {
    throw new Error(res.status === 503 ? 'Service temporarily unavailable' : 'Failed to load popular ships')
  }
  return await res.json()
}

async function fetchLocationStats() {
  const res = await fetch('/api/locations/popular?limit=5&days=7')
  if (!res.ok) {
    throw new Error(res.status === 503 ? 'Service temporarily unavailable' : 'Failed to load location statistics')
  }
  return await res.json()
}

const { data: stats, isLoading: loadingStats, isError: statsError } = useQuery({
  queryKey: ['stats'],
  queryFn: fetchStats,
  retry: 2,
  onError: (error: Error) => {
    showError(error.message)
  },
})

const { data: popularShips, isLoading: loadingShips, isError: shipsError } = useQuery({
  queryKey: ['popular-ships'],
  queryFn: fetchPopularShips,
  retry: 2,
  onError: (error: Error) => {
    showError(error.message)
  },
})

const { data: locationStats, isLoading: loadingLocations, isError: locationsError } = useQuery({
  queryKey: ['location-stats'],
  queryFn: fetchLocationStats,
  retry: 2,
  onError: (error: Error) => {
    showError(error.message)
  },
})
</script>

<template>
  <div class="space-y-8">
    <!-- Hero Section -->
    <div class="text-center space-y-4">
      <h1 class="text-4xl font-bold text-slate-900">Welcome to LostFits</h1>
      <p class="text-xl text-slate-600">
        Track and analyze the most common ship fittings lost in EVE Online
      </p>
      <router-link
        to="/fits"
        class="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3 rounded-lg transition"
      >
        Browse Popular Fits
      </router-link>
    </div>

    <!-- Stats Cards -->
    <div v-if="loadingStats" class="text-center py-8">
      <div class="text-slate-500">Loading statistics...</div>
    </div>
    <div v-else-if="statsError" class="text-center py-8">
      <div class="text-red-600">Unable to load statistics. Please try again later.</div>
    </div>
    <div v-else-if="stats" class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm font-medium text-slate-500 uppercase">Total Killmails</div>
        <div class="text-3xl font-bold text-slate-900 mt-2">
          {{ stats.total_killmails?.toLocaleString() }}
        </div>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm font-medium text-slate-500 uppercase">Ships & Modules Tracked</div>
        <div class="text-3xl font-bold text-slate-900 mt-2">
          {{ stats.total_item_types?.toLocaleString() }}
        </div>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <div class="text-sm font-medium text-slate-500 uppercase">Data Collection</div>
        <div class="text-sm text-slate-700 mt-2">
          <div>Started: {{ new Date(stats.first_ingested).toLocaleDateString() }}</div>
          <div>Latest: {{ new Date(stats.last_ingested).toLocaleString() }}</div>
        </div>
      </div>
    </div>

    <!-- Popular Ships (Last 7 Days) -->
    <div class="bg-white rounded-lg shadow">
      <div class="px-6 py-4 border-b border-slate-200">
        <h2 class="text-xl font-bold text-slate-900">Most Destroyed Ships (Last 7 Days)</h2>
      </div>
      <div v-if="loadingShips" class="p-6 text-center text-slate-500">
        Loading popular ships...
      </div>
      <div v-else-if="shipsError" class="p-6 text-center text-red-600">
        Unable to load popular ships data.
      </div>
      <div v-else-if="popularShips" class="p-6">
        <div class="space-y-3">
          <div
            v-for="ship in popularShips.ships"
            :key="ship.ship_type_id"
            class="flex items-center justify-between p-3 rounded hover:bg-slate-50"
          >
            <div>
              <div class="font-medium text-slate-900">{{ ship.ship_name }}</div>
              <div class="text-sm text-slate-500">Type ID: {{ ship.ship_type_id }}</div>
            </div>
            <div class="text-right">
              <div class="text-2xl font-bold text-red-600">{{ ship.total_losses }}</div>
              <div class="text-xs text-slate-500">losses</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Location Breakdown (Last 7 Days) -->
    <div class="bg-white rounded-lg shadow">
      <div class="px-6 py-4 border-b border-slate-200">
        <h2 class="text-xl font-bold text-slate-900">Kills by Security Zone (Last 7 Days)</h2>
      </div>
      <div v-if="loadingLocations" class="p-6 text-center text-slate-500">
        Loading location stats...
      </div>
      <div v-else-if="locationsError" class="p-6 text-center text-red-600">
        Unable to load location statistics.
      </div>
      <div v-else-if="locationStats" class="p-6">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div
            v-for="zone in locationStats.security_breakdown"
            :key="zone.security_type"
            class="p-4 rounded-lg border-2"
            :class="{
              'border-red-500 bg-red-50': zone.security_type === 'nullsec',
              'border-yellow-500 bg-yellow-50': zone.security_type === 'lowsec',
              'border-green-500 bg-green-50': zone.security_type === 'highsec',
              'border-purple-500 bg-purple-50': zone.security_type === 'w-space',
              'border-blue-500 bg-blue-50': zone.security_type === 'abyssal',
              'border-slate-300 bg-slate-50': zone.security_type === 'unknown'
            }"
          >
            <div class="text-sm font-medium uppercase text-slate-600">
              {{ zone.security_type }}
            </div>
            <div class="text-2xl font-bold text-slate-900 mt-1">
              {{ zone.kill_count }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
