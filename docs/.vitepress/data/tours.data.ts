import { createContentLoader } from 'vitepress'

export type Tour = {
  id: string
  offer_group_id: string
  destination_id: string
  status: 'draft' | 'active' | 'archived'
  offer_type?: 'standard' | 'special'
  special_offer_valid_until?: string
  hotel: string
  hotel_url?: string
  stars: number
  meal_plan: string
  nights: number
  departure_city: string
  departure_date: string
  return_date: string
  flight: string
  price: number
  currency: string
  price_for?: 'per_person' | 'per_two' | 'per_room' | 'unknown'
  price_note: string
  published_at: string
  tour_source_url?: string
  price_checked_at?: string
}

declare const data: Tour[]
export { data }

export default createContentLoader('.vitepress/content/tours/*.md', {
  transform(rawData) {
    return rawData.map(page => page.frontmatter as Tour)
  },
})
