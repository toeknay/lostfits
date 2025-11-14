<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'

const router = useRouter()

// Filter state
const days = ref(7)
const securityStatus = ref('')
const limit = ref(20)

// Multi-select filter state
const selectedShips = ref<number[]>([])
const shipMode = ref<'include' | 'exclude'>('include')
const selectedRegions = ref<number[]>([])
const regionMode = ref<'include' | 'exclude'>('include')
const selectedConstellations = ref<number[]>([])
const constellationMode = ref<'include' | 'exclude'>('include')
const selectedSystems = ref<number[]>([])
const systemMode = ref<'include' | 'exclude'>('include')

// Build query params
const queryParams = computed(() => {
  const params = new URLSearchParams()
  params.append('limit', limit.value.toString())
  params.append('days', days.value.toString())
  if (securityStatus.value) params.append('security_status', securityStatus.value)

  // Ship filters
  selectedShips.value.forEach(id => params.append('ship_type_ids', id.toString()))
  if (selectedShips.value.length > 0) params.append('ship_mode', shipMode.value)

  // Region filters
  selectedRegions.value.forEach(id => params.append('region_ids', id.toString()))
  if (selectedRegions.value.length > 0) params.append('region_mode', regionMode.value)

  // Constellation filters
  selectedConstellations.value.forEach(id => params.append('constellation_ids', id.toString()))
  if (selectedConstellations.value.length > 0) params.append('constellation_mode', constellationMode.value)

  // System filters
  selectedSystems.value.forEach(id => params.append('solar_system_ids', id.toString()))
  if (selectedSystems.value.length > 0) params.append('system_mode', systemMode.value)

  return params.toString()
})

// Fetch ships
async function fetchShips() {
  const res = await fetch('/api/ships')
  if (!res.ok) throw new Error('Failed to fetch ships')
  return await res.json()
}

const { data: shipsData } = useQuery({
  queryKey: ['ships'],
  queryFn: fetchShips,
})

// Fetch regions
async function fetchRegions() {
  const res = await fetch('/api/universe/regions')
  if (!res.ok) throw new Error('Failed to fetch regions')
  return await res.json()
}

const { data: regionsData } = useQuery({
  queryKey: ['regions'],
  queryFn: fetchRegions,
})

// Fetch all constellations
async function fetchAllConstellations() {
  const res = await fetch('/api/universe/constellations')
  if (!res.ok) throw new Error('Failed to fetch constellations')
  return await res.json()
}

const { data: allConstellationsData } = useQuery({
  queryKey: ['all-constellations'],
  queryFn: fetchAllConstellations,
})

// Fetch all systems
async function fetchAllSystems() {
  const res = await fetch('/api/universe/systems')
  if (!res.ok) throw new Error('Failed to fetch systems')
  return await res.json()
}

const { data: allSystemsData } = useQuery({
  queryKey: ['all-systems'],
  queryFn: fetchAllSystems,
})

// Filtered constellations based on selected regions
const filteredConstellations = computed(() => {
  if (!allConstellationsData.value?.constellations) return []

  const constellations = allConstellationsData.value.constellations

  // If no regions selected, show all
  if (selectedRegions.value.length === 0) return constellations

  // Filter based on mode
  if (regionMode.value === 'include') {
    // Show only constellations in selected regions
    return constellations.filter(c => selectedRegions.value.includes(c.region_id))
  } else {
    // Show all constellations EXCEPT those in excluded regions
    return constellations.filter(c => !selectedRegions.value.includes(c.region_id))
  }
})

// Filtered systems based on selected constellations
const filteredSystems = computed(() => {
  if (!allSystemsData.value?.systems) return []

  let systems = allSystemsData.value.systems

  // First filter by regions if any are selected
  if (selectedRegions.value.length > 0 && allConstellationsData.value?.constellations) {
    const validConstellationIds = filteredConstellations.value.map(c => c.constellation_id)
    systems = systems.filter(s => validConstellationIds.includes(s.constellation_id))
  }

  // Then filter by constellations if any are selected
  if (selectedConstellations.value.length > 0) {
    if (constellationMode.value === 'include') {
      systems = systems.filter(s => selectedConstellations.value.includes(s.constellation_id))
    } else {
      systems = systems.filter(s => !selectedConstellations.value.includes(s.constellation_id))
    }
  }

  return systems
})

// Clean up invalid constellation selections when region filter changes
const validConstellationIds = computed(() => {
  return new Set(filteredConstellations.value.map(c => c.constellation_id))
})

// Clean up invalid system selections when constellation/region filter changes
const validSystemIds = computed(() => {
  return new Set(filteredSystems.value.map(s => s.system_id))
})

// Watch for changes and clean up invalid selections
watch([selectedRegions, regionMode], () => {
  // Remove any selected constellations that are no longer in the filtered list
  selectedConstellations.value = selectedConstellations.value.filter(id =>
    validConstellationIds.value.has(id)
  )
})

watch([selectedConstellations, constellationMode, selectedRegions, regionMode], () => {
  // Remove any selected systems that are no longer in the filtered list
  selectedSystems.value = selectedSystems.value.filter(id =>
    validSystemIds.value.has(id)
  )
})

// Fetch popular fits
async function fetchPopularFits() {
  const res = await fetch(`/api/fits/popular?${queryParams.value}`)
  if (!res.ok) throw new Error('Failed to fetch popular fits')
  return await res.json()
}

const { data: fitsData, isLoading } = useQuery({
  queryKey: ['popular-fits', queryParams],
  queryFn: fetchPopularFits,
})

function viewFitDetails(fitSignature: string) {
  router.push(`/fits/${fitSignature}`)
}

function clearFilters() {
  days.value = 7
  securityStatus.value = ''
  selectedShips.value = []
  shipMode.value = 'include'
  selectedRegions.value = []
  regionMode.value = 'include'
  selectedConstellations.value = []
  constellationMode.value = 'include'
  selectedSystems.value = []
  systemMode.value = 'include'
  limit.value = 20
}
</script>

<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-3xl font-bold text-slate-900">Popular Fits Browser</h1>
      <p class="text-slate-600 mt-2">
        Explore the most common ship fittings being destroyed across New Eden
      </p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
      <!-- Filters Sidebar -->
      <div class="lg:col-span-1">
        <div class="bg-white rounded-lg shadow sticky top-6 max-h-[calc(100vh-3rem)] overflow-y-auto">
          <div class="p-6 pb-4">
            <h2 class="text-lg font-bold text-slate-900 mb-4">Filters</h2>

            <div class="space-y-4">
            <!-- Time Range -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">
                Time Range
              </label>
              <select
                v-model.number="days"
                class="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option :value="1">Last 24 Hours</option>
                <option :value="7">Last 7 Days</option>
                <option :value="30">Last 30 Days</option>
                <option :value="90">Last 90 Days</option>
              </select>
            </div>

            <!-- Security Status -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">
                Security Zone
              </label>
              <select
                v-model="securityStatus"
                class="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Zones</option>
                <option value="highsec">Highsec</option>
                <option value="lowsec">Lowsec</option>
                <option value="nullsec">Nullsec</option>
                <option value="w-space">Wormhole Space</option>
                <option value="abyssal">Abyssal</option>
              </select>
            </div>

            <!-- Ship Type Filter -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-slate-700">
                  Ship Types
                </label>
                <div class="flex gap-1">
                  <button
                    @click="shipMode = 'include'"
                    :class="[
                      'px-2 py-1 text-xs rounded',
                      shipMode === 'include'
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    ]"
                  >
                    Include
                  </button>
                  <button
                    @click="shipMode = 'exclude'"
                    :class="[
                      'px-2 py-1 text-xs rounded',
                      shipMode === 'exclude'
                        ? 'bg-red-600 text-white'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    ]"
                  >
                    Exclude
                  </button>
                </div>
              </div>
              <select
                v-model="selectedShips"
                multiple
                class="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                size="5"
              >
                <option
                  v-for="ship in shipsData?.ships"
                  :key="ship.ship_type_id"
                  :value="ship.ship_type_id"
                >
                  {{ ship.name }}
                </option>
              </select>
              <p class="text-xs text-slate-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
            </div>

            <!-- Region Filter -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-slate-700">
                  Regions
                </label>
                <div class="flex gap-1">
                  <button
                    @click="regionMode = 'include'"
                    :class="[
                      'px-2 py-1 text-xs rounded',
                      regionMode === 'include'
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    ]"
                  >
                    Include
                  </button>
                  <button
                    @click="regionMode = 'exclude'"
                    :class="[
                      'px-2 py-1 text-xs rounded',
                      regionMode === 'exclude'
                        ? 'bg-red-600 text-white'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    ]"
                  >
                    Exclude
                  </button>
                </div>
              </div>
              <select
                v-model="selectedRegions"
                multiple
                class="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                size="5"
              >
                <option
                  v-for="region in regionsData?.regions"
                  :key="region.region_id"
                  :value="region.region_id"
                >
                  {{ region.name }}
                </option>
              </select>
              <p class="text-xs text-slate-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
            </div>

            <!-- Constellation Filter -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-slate-700">
                  Constellations
                </label>
                <div class="flex gap-1">
                  <button
                    @click="constellationMode = 'include'"
                    :class="[
                      'px-2 py-1 text-xs rounded',
                      constellationMode === 'include'
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    ]"
                  >
                    Include
                  </button>
                  <button
                    @click="constellationMode = 'exclude'"
                    :class="[
                      'px-2 py-1 text-xs rounded',
                      constellationMode === 'exclude'
                        ? 'bg-red-600 text-white'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    ]"
                  >
                    Exclude
                  </button>
                </div>
              </div>
              <select
                v-model="selectedConstellations"
                multiple
                class="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                size="5"
              >
                <option
                  v-for="constellation in filteredConstellations"
                  :key="constellation.constellation_id"
                  :value="constellation.constellation_id"
                >
                  {{ constellation.name }}
                </option>
              </select>
              <p class="text-xs text-slate-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
            </div>

            <!-- Solar System Filter -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-slate-700">
                  Solar Systems
                </label>
                <div class="flex gap-1">
                  <button
                    @click="systemMode = 'include'"
                    :class="[
                      'px-2 py-1 text-xs rounded',
                      systemMode === 'include'
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    ]"
                  >
                    Include
                  </button>
                  <button
                    @click="systemMode = 'exclude'"
                    :class="[
                      'px-2 py-1 text-xs rounded',
                      systemMode === 'exclude'
                        ? 'bg-red-600 text-white'
                        : 'bg-slate-200 text-slate-600 hover:bg-slate-300'
                    ]"
                  >
                    Exclude
                  </button>
                </div>
              </div>
              <select
                v-model="selectedSystems"
                multiple
                class="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                size="5"
              >
                <option
                  v-for="system in filteredSystems"
                  :key="system.system_id"
                  :value="system.system_id"
                >
                  {{ system.name }}
                </option>
              </select>
              <p class="text-xs text-slate-500 mt-1">Hold Ctrl/Cmd to select multiple</p>
            </div>

            <!-- Results Limit -->
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-2">
                Results to Show
              </label>
              <select
                v-model.number="limit"
                class="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option :value="10">10 fits</option>
                <option :value="20">20 fits</option>
                <option :value="50">50 fits</option>
                <option :value="100">100 fits</option>
              </select>
            </div>

            <!-- Clear Filters -->
            <button
              @click="clearFilters"
              class="w-full px-4 py-2 text-sm font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md transition"
            >
              Clear Filters
            </button>
            </div>

            <!-- Active Filters Summary -->
            <div v-if="securityStatus || selectedShips.length || selectedRegions.length || selectedConstellations.length || selectedSystems.length" class="mt-6 pt-4 border-t border-slate-200">
              <div class="text-sm font-medium text-slate-700 mb-2">Active Filters:</div>
              <div class="space-y-1 text-sm text-slate-600">
                <div v-if="securityStatus">
                  Security: <span class="font-medium">{{ securityStatus }}</span>
                </div>
                <div v-if="selectedShips.length">
                  <span :class="shipMode === 'exclude' ? 'text-red-600' : 'text-green-600'">
                    {{ shipMode === 'exclude' ? 'Excluding' : 'Including' }}
                  </span>
                  {{ selectedShips.length }} ship type(s)
                </div>
                <div v-if="selectedRegions.length">
                  <span :class="regionMode === 'exclude' ? 'text-red-600' : 'text-green-600'">
                    {{ regionMode === 'exclude' ? 'Excluding' : 'Including' }}
                  </span>
                  {{ selectedRegions.length }} region(s)
                </div>
                <div v-if="selectedConstellations.length">
                  <span :class="constellationMode === 'exclude' ? 'text-red-600' : 'text-green-600'">
                    {{ constellationMode === 'exclude' ? 'Excluding' : 'Including' }}
                  </span>
                  {{ selectedConstellations.length }} constellation(s)
                </div>
                <div v-if="selectedSystems.length">
                  <span :class="systemMode === 'exclude' ? 'text-red-600' : 'text-green-600'">
                    {{ systemMode === 'exclude' ? 'Excluding' : 'Including' }}
                  </span>
                  {{ selectedSystems.length }} system(s)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Fits List -->
      <div class="lg:col-span-3">
        <!-- Loading State -->
        <div v-if="isLoading" class="bg-white rounded-lg shadow p-8 text-center">
          <div class="text-slate-500">Loading popular fits...</div>
        </div>

        <!-- Results -->
        <div v-else-if="fitsData" class="space-y-4">
          <!-- Results Header -->
          <div class="bg-white rounded-lg shadow px-6 py-4">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-xl font-bold text-slate-900">
                  {{ fitsData.total_results }} Popular Fits
                </h2>
                <p class="text-sm text-slate-600 mt-1">
                  From {{ new Date(fitsData.start_date).toLocaleDateString() }}
                  to {{ new Date(fitsData.end_date).toLocaleDateString() }}
                </p>
              </div>
            </div>
          </div>

          <!-- No Results -->
          <div
            v-if="fitsData.total_results === 0"
            class="bg-white rounded-lg shadow p-8 text-center"
          >
            <div class="text-slate-500">
              No fits found matching your filters. Try adjusting your search criteria.
            </div>
          </div>

          <!-- Fits Cards -->
          <div
            v-for="fit in fitsData.fits"
            :key="fit.fit_signature"
            class="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer"
            @click="viewFitDetails(fit.fit_signature)"
          >
            <div class="p-6">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h3 class="text-xl font-bold text-slate-900">
                    {{ fit.ship_name }}
                  </h3>
                  <div class="text-sm text-slate-500 mt-1">
                    Ship Type ID: {{ fit.ship_type_id }}
                  </div>
                  <div class="text-xs text-slate-400 mt-1 font-mono">
                    Fit Signature: {{ fit.fit_signature }}
                  </div>
                </div>
                <div class="text-right ml-4">
                  <div class="text-3xl font-bold text-red-600">
                    {{ fit.total_losses }}
                  </div>
                  <div class="text-sm text-slate-500">losses</div>
                </div>
              </div>

              <div class="mt-4 pt-4 border-t border-slate-200">
                <button
                  class="text-blue-600 hover:text-blue-700 font-medium text-sm"
                >
                  View Fit Details →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
