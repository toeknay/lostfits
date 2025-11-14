import { useQuery } from '@tanstack/vue-query'
import type { Stats, PopularShipsResponse, PopularFitsResponse } from '../types/api'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }
  return response.json()
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: () => fetchJson<Stats>('/api/stats')
  })
}

export function usePopularShips(days: number = 7, limit: number = 5) {
  return useQuery({
    queryKey: ['popular-ships', days, limit],
    queryFn: () => fetchJson<PopularShipsResponse>(`/api/fits/ships/popular?days=${days}&limit=${limit}`)
  })
}

export function usePopularFits(days: number = 7, limit: number = 10, shipTypeId?: number) {
  return useQuery({
    queryKey: ['popular-fits', days, limit, shipTypeId],
    queryFn: () => {
      const params = new URLSearchParams({
        days: days.toString(),
        limit: limit.toString()
      })
      if (shipTypeId) {
        params.append('ship_type_id', shipTypeId.toString())
      }
      return fetchJson<PopularFitsResponse>(`/api/fits/popular?${params}`)
    }
  })
}
