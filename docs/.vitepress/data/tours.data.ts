import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import type { DataLoader } from 'vitepress'

export type TourStatus = 'draft' | 'active' | 'archived'
export type OfferType = 'standard' | 'special'
export type MealPlan = 'AI' | 'UAI' | 'HB' | 'BB' | 'FB' | 'RO' | 'UNKNOWN'
export type PriceFor = 'per_person' | 'per_two' | 'per_room' | 'unknown'

export type Tour = {
  id: string
  offer_group_id: string
  destination_id: string
  status: TourStatus
  offer_type?: OfferType
  special_offer_valid_until?: string
  hotel: string
  hotel_url?: string
  stars: number
  meal_plan: MealPlan
  nights: number
  departure_city: string
  departure_date: string
  return_date: string
  flight: string
  price: number
  currency: string
  price_for: PriceFor
  price_note: string
  published_at: string
  tour_source_url?: string
  price_checked_at?: string
}

const toursFile = fileURLToPath(new URL('../../data/tours.json', import.meta.url))

export default {
  watch: ['../../data/tours.json'],
  async load(): Promise<Tour[]> {
    const source = await readFile(toursFile, 'utf-8')
    const tours: unknown = JSON.parse(source)

    if (!Array.isArray(tours)) {
      throw new Error('docs/data/tours.json must contain an array of tours')
    }

    return tours as Tour[]
  },
} satisfies DataLoader
