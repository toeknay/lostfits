<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '../composables/useToast'

const route = useRoute()
const router = useRouter()
const { showError } = useToast()

const fitSignature = computed(() => route.params.signature as string)

async function fetchFitDetails() {
  const res = await fetch(`/api/fits/${fitSignature.value}`)
  if (!res.ok) {
    throw new Error(res.status === 404 ? 'Fit not found' : 'Failed to load fit details')
  }
  return await res.json()
}

async function fetchFitLocationData() {
  const res = await fetch(`/api/fits/${fitSignature.value}/by-location`)
  if (!res.ok) {
    throw new Error('Failed to load location data')
  }
  return await res.json()
}

const { data: fitData, isLoading: loadingFit, isError: fitError } = useQuery({
  queryKey: ['fit-details', fitSignature],
  queryFn: fetchFitDetails,
  retry: 1,
  onError: (error: Error) => {
    showError(error.message)
  },
})

const { data: locationData, isLoading: loadingLocation, isError: locationError } = useQuery({
  queryKey: ['fit-location', fitSignature],
  queryFn: fetchFitLocationData,
  retry: 2,
  onError: (error: Error) => {
    showError(error.message)
  },
})

// Group items by slot type based on flag
function groupItemsBySlot(items: any[]) {
  const groups: Record<string, any[]> = {
    high: [],
    mid: [],
    low: [],
    rig: [],
    subsystem: [],
    drone: [],
    cargo: [],
    other: [],
  }

  items.forEach((item) => {
    const flag = item.flag
    // EVE flag mappings (approximate)
    if (flag >= 27 && flag <= 34) groups.high.push(item)
    else if (flag >= 19 && flag <= 26) groups.mid.push(item)
    else if (flag >= 11 && flag <= 18) groups.low.push(item)
    else if (flag >= 92 && flag <= 94) groups.rig.push(item)
    else if (flag >= 125 && flag <= 132) groups.subsystem.push(item)
    else if (flag === 87) groups.drone.push(item)
    else if (flag === 5) groups.cargo.push(item)
    else groups.other.push(item)
  })

  return groups
}

const groupedItems = computed(() => {
  if (!fitData.value?.fitted_items) return null
  return groupItemsBySlot(fitData.value.fitted_items)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Back Button -->
    <button
      @click="router.push('/fits')"
      class="text-blue-600 hover:text-blue-700 font-medium"
    >
      ← Back to Fits Browser
    </button>

    <!-- Loading State -->
    <div v-if="loadingFit" class="bg-white rounded-lg shadow p-8 text-center">
      <div class="text-slate-500">Loading fit details...</div>
    </div>

    <!-- Error State -->
    <div v-else-if="fitError" class="bg-white rounded-lg shadow p-8 text-center">
      <div class="text-red-600 mb-4">
        <svg class="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="font-medium">Unable to load fit details</p>
        <p class="text-sm text-slate-600 mt-2">This fit may not exist or there was an error loading the data</p>
      </div>
    </div>

    <!-- Fit Not Found -->
    <div
      v-else-if="fitData && !fitData.found"
      class="bg-white rounded-lg shadow p-8 text-center"
    >
      <div class="text-red-600 font-medium">{{ fitData.message }}</div>
    </div>

    <!-- Fit Details -->
    <div v-else-if="fitData" class="space-y-6">
      <!-- Header Card -->
      <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <h1 class="text-3xl font-bold text-slate-900">{{ fitData.ship_name }}</h1>
            <div class="text-sm text-slate-500 mt-2">
              Ship Type ID: {{ fitData.ship_type_id }}
            </div>
            <div class="text-xs text-slate-400 mt-1 font-mono">
              Fit Signature: {{ fitData.fit_signature }}
            </div>
          </div>
          <div class="text-right">
            <div class="text-4xl font-bold text-red-600">
              {{ fitData.total_occurrences }}
            </div>
            <div class="text-sm text-slate-500">total losses</div>
          </div>
        </div>

        <!-- Slot Counts -->
        <div class="mt-6 pt-6 border-t border-slate-200">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="text-center">
              <div class="text-2xl font-bold text-slate-900">
                {{ fitData.slot_counts.high_slots }}
              </div>
              <div class="text-sm text-slate-600">High Slots</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-slate-900">
                {{ fitData.slot_counts.mid_slots }}
              </div>
              <div class="text-sm text-slate-600">Mid Slots</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-slate-900">
                {{ fitData.slot_counts.low_slots }}
              </div>
              <div class="text-sm text-slate-600">Low Slots</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-slate-900">
                {{ fitData.slot_counts.rig_slots }}
              </div>
              <div class="text-sm text-slate-600">Rig Slots</div>
            </div>
          </div>
        </div>

        <!-- Location Summary -->
        <div v-if="fitData.location_summary?.length" class="mt-6 pt-6 border-t border-slate-200">
          <div class="text-sm font-medium text-slate-700 mb-3">Most Common Locations:</div>
          <div class="flex gap-3">
            <div
              v-for="loc in fitData.location_summary"
              :key="loc.security_type"
              class="px-4 py-2 rounded-lg text-sm font-medium"
              :class="{
                'bg-red-100 text-red-700': loc.security_type === 'nullsec',
                'bg-yellow-100 text-yellow-700': loc.security_type === 'lowsec',
                'bg-green-100 text-green-700': loc.security_type === 'highsec',
                'bg-purple-100 text-purple-700': loc.security_type === 'w-space',
                'bg-blue-100 text-blue-700': loc.security_type === 'abyssal',
              }"
            >
              {{ loc.security_type }}: {{ loc.count }}
            </div>
          </div>
        </div>
      </div>

      <!-- Fitted Items -->
      <div v-if="groupedItems" class="bg-white rounded-lg shadow">
        <div class="px-6 py-4 border-b border-slate-200">
          <h2 class="text-xl font-bold text-slate-900">Fitted Modules & Items</h2>
        </div>
        <div class="p-6 space-y-6">
          <!-- High Slots -->
          <div v-if="groupedItems.high.length">
            <h3 class="font-semibold text-slate-900 mb-3">High Slots</h3>
            <div class="space-y-2">
              <div
                v-for="(item, idx) in groupedItems.high"
                :key="idx"
                class="flex items-center justify-between p-3 bg-slate-50 rounded"
              >
                <span class="text-slate-900">{{ item.name }}</span>
                <span class="text-sm text-slate-500">x{{ item.quantity }}</span>
              </div>
            </div>
          </div>

          <!-- Mid Slots -->
          <div v-if="groupedItems.mid.length">
            <h3 class="font-semibold text-slate-900 mb-3">Mid Slots</h3>
            <div class="space-y-2">
              <div
                v-for="(item, idx) in groupedItems.mid"
                :key="idx"
                class="flex items-center justify-between p-3 bg-slate-50 rounded"
              >
                <span class="text-slate-900">{{ item.name }}</span>
                <span class="text-sm text-slate-500">x{{ item.quantity }}</span>
              </div>
            </div>
          </div>

          <!-- Low Slots -->
          <div v-if="groupedItems.low.length">
            <h3 class="font-semibold text-slate-900 mb-3">Low Slots</h3>
            <div class="space-y-2">
              <div
                v-for="(item, idx) in groupedItems.low"
                :key="idx"
                class="flex items-center justify-between p-3 bg-slate-50 rounded"
              >
                <span class="text-slate-900">{{ item.name }}</span>
                <span class="text-sm text-slate-500">x{{ item.quantity }}</span>
              </div>
            </div>
          </div>

          <!-- Rigs -->
          <div v-if="groupedItems.rig.length">
            <h3 class="font-semibold text-slate-900 mb-3">Rigs</h3>
            <div class="space-y-2">
              <div
                v-for="(item, idx) in groupedItems.rig"
                :key="idx"
                class="flex items-center justify-between p-3 bg-slate-50 rounded"
              >
                <span class="text-slate-900">{{ item.name }}</span>
                <span class="text-sm text-slate-500">x{{ item.quantity }}</span>
              </div>
            </div>
          </div>

          <!-- Drones -->
          <div v-if="groupedItems.drone.length">
            <h3 class="font-semibold text-slate-900 mb-3">Drones</h3>
            <div class="space-y-2">
              <div
                v-for="(item, idx) in groupedItems.drone"
                :key="idx"
                class="flex items-center justify-between p-3 bg-slate-50 rounded"
              >
                <span class="text-slate-900">{{ item.name }}</span>
                <span class="text-sm text-slate-500">x{{ item.quantity }}</span>
              </div>
            </div>
          </div>

          <!-- Other Items -->
          <div v-if="groupedItems.other.length">
            <h3 class="font-semibold text-slate-900 mb-3">Cargo & Other</h3>
            <div class="space-y-2">
              <div
                v-for="(item, idx) in groupedItems.other"
                :key="idx"
                class="flex items-center justify-between p-3 bg-slate-50 rounded"
              >
                <span class="text-slate-900">{{ item.name }}</span>
                <span class="text-sm text-slate-500">x{{ item.quantity }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Location Breakdown -->
      <div v-if="locationData && locationData.found" class="bg-white rounded-lg shadow">
        <div class="px-6 py-4 border-b border-slate-200">
          <h2 class="text-xl font-bold text-slate-900">Where This Fit Dies</h2>
          <p class="text-sm text-slate-600 mt-1">
            Last {{ locationData.days }} days
            ({{ locationData.total_losses }} losses)
          </p>
        </div>
        <div class="p-6 space-y-6">
          <!-- Security Status Breakdown -->
          <div>
            <h3 class="font-semibold text-slate-900 mb-3">Security Zone Distribution</h3>
            <div class="space-y-3">
              <div
                v-for="zone in locationData.security_breakdown"
                :key="zone.security_type"
                class="flex items-center gap-4"
              >
                <div class="w-32 text-sm font-medium text-slate-700 capitalize">
                  {{ zone.security_type }}
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-3">
                    <div class="flex-1 bg-slate-200 rounded-full h-6 overflow-hidden">
                      <div
                        class="h-full rounded-full transition-all"
                        :class="{
                          'bg-red-500': zone.security_type === 'nullsec',
                          'bg-yellow-500': zone.security_type === 'lowsec',
                          'bg-green-500': zone.security_type === 'highsec',
                          'bg-purple-500': zone.security_type === 'w-space',
                          'bg-blue-500': zone.security_type === 'abyssal',
                          'bg-slate-400': zone.security_type === 'unknown',
                        }"
                        :style="{ width: zone.percentage + '%' }"
                      ></div>
                    </div>
                    <div class="w-16 text-right">
                      <span class="text-sm font-bold">{{ zone.percentage }}%</span>
                    </div>
                    <div class="w-16 text-right text-sm text-slate-600">
                      {{ zone.loss_count }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Top Regions -->
          <div>
            <h3 class="font-semibold text-slate-900 mb-3">Top Regions</h3>
            <div class="space-y-2">
              <div
                v-for="region in locationData.top_regions"
                :key="region.region_id"
                class="flex items-center justify-between p-3 bg-slate-50 rounded hover:bg-slate-100"
              >
                <div class="flex-1">
                  <div class="font-medium text-slate-900">
                    {{ region.name }}
                  </div>
                  <div class="text-sm text-slate-600">
                    {{ region.percentage }}% of all losses
                  </div>
                </div>
                <div class="text-lg font-bold text-slate-900">
                  {{ region.loss_count }}
                </div>
              </div>
            </div>
          </div>

          <!-- Top Constellations -->
          <div>
            <h3 class="font-semibold text-slate-900 mb-3">Top Constellations</h3>
            <div class="space-y-2">
              <div
                v-for="constellation in locationData.top_constellations"
                :key="constellation.constellation_id"
                class="flex items-center justify-between p-3 bg-slate-50 rounded hover:bg-slate-100"
              >
                <div class="flex-1">
                  <div class="font-medium text-slate-900">
                    {{ constellation.name }}
                  </div>
                  <div class="text-sm text-slate-600">
                    {{ constellation.region_name }} • {{ constellation.percentage }}% of all losses
                  </div>
                </div>
                <div class="text-lg font-bold text-slate-900">
                  {{ constellation.loss_count }}
                </div>
              </div>
            </div>
          </div>

          <!-- Top Solar Systems -->
          <div>
            <h3 class="font-semibold text-slate-900 mb-3">Top Solar Systems</h3>
            <div class="space-y-2">
              <div
                v-for="system in locationData.top_solar_systems"
                :key="system.system_id"
                class="flex items-center justify-between p-3 bg-slate-50 rounded hover:bg-slate-100"
              >
                <div class="flex-1">
                  <div class="font-medium text-slate-900">
                    {{ system.name }}
                  </div>
                  <div class="text-sm text-slate-600">
                    {{ system.constellation_name }}, {{ system.region_name }} • {{ system.percentage }}% of all losses
                  </div>
                </div>
                <div class="text-lg font-bold text-slate-900">
                  {{ system.loss_count }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Example Killmails -->
      <div v-if="fitData.example_killmails?.length" class="bg-white rounded-lg shadow">
        <div class="px-6 py-4 border-b border-slate-200">
          <h2 class="text-xl font-bold text-slate-900">Example Killmails</h2>
        </div>
        <div class="p-6">
          <div class="space-y-2">
            <div
              v-for="km in fitData.example_killmails"
              :key="km.killmail_id"
              class="flex items-center justify-between p-3 bg-slate-50 rounded hover:bg-slate-100"
            >
              <div>
                <div class="font-medium text-slate-900">
                  Killmail {{ km.killmail_id }}
                </div>
                <div class="text-sm text-slate-600">
                  {{ new Date(km.kill_time).toLocaleString() }}
                </div>
              </div>
              <a
                :href="`https://zkillboard.com/kill/${km.killmail_id}/`"
                target="_blank"
                class="text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                View on zKill →
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
