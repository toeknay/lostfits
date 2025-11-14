<script setup lang="ts">
import { useStats, usePopularShips, usePopularFits } from '../composables/useApi'
import { useEveImages } from '../composables/useEveImages'

const { data: stats, isLoading: statsLoading } = useStats()
const { data: topShips, isLoading: shipsLoading } = usePopularShips(7, 5)
const { data: topFits, isLoading: fitsLoading } = usePopularFits(7, 10)

const { getShipRender } = useEveImages()

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString()
}

const formatNumber = (num: number) => {
  return num.toLocaleString()
}
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div>
      <h1 class="text-4xl font-bold text-white mb-2">Dashboard</h1>
      <p class="text-gray-400">
        Analyzing EVE Online killmails to find the most common ship fittings
      </p>
    </div>

    <!-- Stats Overview -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div class="text-sm font-medium text-gray-400 mb-1">Total Killmails</div>
        <div v-if="statsLoading" class="text-2xl font-bold text-white">Loading...</div>
        <div v-else class="text-2xl font-bold text-white">
          {{ stats ? formatNumber(stats.total_killmails) : '0' }}
        </div>
      </div>

      <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div class="text-sm font-medium text-gray-400 mb-1">Ships & Items</div>
        <div v-if="statsLoading" class="text-2xl font-bold text-white">Loading...</div>
        <div v-else class="text-2xl font-bold text-white">
          {{ stats ? formatNumber(stats.total_item_types) : '0' }}
        </div>
      </div>

      <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div class="text-sm font-medium text-gray-400 mb-1">First Ingested</div>
        <div v-if="statsLoading" class="text-lg font-semibold text-white">Loading...</div>
        <div v-else class="text-lg font-semibold text-white">
          {{ stats ? formatDate(stats.first_ingested) : 'N/A' }}
        </div>
      </div>

      <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div class="text-sm font-medium text-gray-400 mb-1">Last Updated</div>
        <div v-if="statsLoading" class="text-lg font-semibold text-white">Loading...</div>
        <div v-else class="text-lg font-semibold text-white">
          {{ stats ? formatDate(stats.last_ingested) : 'N/A' }}
        </div>
      </div>
    </div>

    <!-- Top Ships -->
    <div class="bg-gray-800 rounded-lg border border-gray-700">
      <div class="px-6 py-4 border-b border-gray-700">
        <h2 class="text-2xl font-bold text-white">Top 5 Ships Lost (7 days)</h2>
        <p class="text-sm text-gray-400 mt-1">Most commonly destroyed ships this week</p>
      </div>
      <div class="p-6">
        <div v-if="shipsLoading" class="text-center text-gray-400 py-8">
          Loading ship data...
        </div>
        <div v-else-if="topShips && topShips.ships.length > 0" class="space-y-4">
          <div
            v-for="(ship, index) in topShips.ships"
            :key="ship.ship_type_id"
            class="flex items-center space-x-4 bg-gray-900 rounded-lg p-4 hover:bg-gray-750 transition"
          >
            <div class="flex-shrink-0 w-12 h-12 flex items-center justify-center bg-gray-800 rounded-full text-xl font-bold text-blue-400">
              {{ index + 1 }}
            </div>
            <div class="flex-shrink-0 w-16 h-16">
              <img
                :src="getShipRender(ship.ship_type_id, 128)"
                :alt="ship.ship_name"
                class="w-full h-full object-contain"
              />
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-lg font-semibold text-white truncate">
                {{ ship.ship_name }}
              </div>
              <div class="text-sm text-gray-400">
                Ship Type ID: {{ ship.ship_type_id }}
              </div>
            </div>
            <div class="flex-shrink-0 text-right">
              <div class="text-2xl font-bold text-red-400">
                {{ formatNumber(ship.total_losses) }}
              </div>
              <div class="text-xs text-gray-400">losses</div>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-gray-400 py-8">
          No ship data available yet
        </div>
      </div>
    </div>

    <!-- Top Fits -->
    <div class="bg-gray-800 rounded-lg border border-gray-700">
      <div class="px-6 py-4 border-b border-gray-700">
        <h2 class="text-2xl font-bold text-white">Top 10 Fits Lost (7 days)</h2>
        <p class="text-sm text-gray-400 mt-1">Most common ship fittings this week</p>
      </div>
      <div class="p-6">
        <div v-if="fitsLoading" class="text-center text-gray-400 py-8">
          Loading fit data...
        </div>
        <div v-else-if="topFits && topFits.fits.length > 0" class="space-y-3">
          <div
            v-for="(fit, index) in topFits.fits"
            :key="fit.fit_signature"
            class="flex items-center space-x-4 bg-gray-900 rounded-lg p-4 hover:bg-gray-750 transition cursor-pointer"
          >
            <div class="flex-shrink-0 w-10 h-10 flex items-center justify-center bg-gray-800 rounded-full text-sm font-bold text-blue-400">
              {{ index + 1 }}
            </div>
            <div class="flex-shrink-0 w-12 h-12">
              <img
                :src="getShipRender(fit.ship_type_id, 64)"
                :alt="fit.ship_name"
                class="w-full h-full object-contain"
              />
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-base font-semibold text-white">
                {{ fit.ship_name }}
              </div>
              <div class="text-xs text-gray-500 font-mono truncate">
                {{ fit.fit_signature }}
              </div>
            </div>
            <div class="flex-shrink-0 text-right">
              <div class="text-xl font-bold text-red-400">
                {{ formatNumber(fit.total_losses) }}
              </div>
              <div class="text-xs text-gray-400">losses</div>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-gray-400 py-8">
          No fit data available yet
        </div>
      </div>
    </div>
  </div>
</template>
