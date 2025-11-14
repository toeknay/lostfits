export interface Stats {
  total_killmails: number
  total_item_types: number
  first_ingested: string | null
  last_ingested: string | null
}

export interface PopularShip {
  ship_type_id: number
  ship_name: string
  total_losses: number
}

export interface PopularShipsResponse {
  days: number
  start_date: string
  end_date: string
  total_results: number
  ships: PopularShip[]
}

export interface PopularFit {
  ship_type_id: number
  ship_name: string
  fit_signature: string
  total_losses: number
}

export interface PopularFitsResponse {
  days: number
  start_date: string
  end_date: string
  ship_type_filter: number | null
  total_results: number
  fits: PopularFit[]
}
