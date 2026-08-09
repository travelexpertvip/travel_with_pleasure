import raw from '../../data/destinations.json'

export type VisaCode = 'Б' | 'П'
export type DivingLevel = 'Развитая' | 'Есть' | 'Ограниченная'

export type Destination = {
  id: string
  name: string
  region: string
  airport: string
  visa: VisaCode
  verification_status: 'verified' | 'unverified'
  visa_note?: string
  visa_checked_at?: string
  visa_source_url?: string
  diving: DivingLevel
  season: number[]
  temperature: string | null
  description: string
  flights: string[]
  budget: string
  priceFrom: string
}

export type VisaLabel = { short: string; long: string }

export type DestinationsData = {
  months: string[]
  visaLabels: Record<VisaCode, VisaLabel>
  divingOptions: DivingLevel[]
  ui: {
    calendar: Record<string, string>
    directory: {
      searchPlaceholder: string
      tableHeaders: Record<string, string>
    }
    flights: { priceDisclaimer: string }
  }
  destinations: Destination[]
}

export const data = raw as DestinationsData
export const months = data.months
export const destinations = data.destinations
export const visaLabels = data.visaLabels
export const divingOptions = data.divingOptions
export const ui = data.ui

export function visaLabel(code: VisaCode, form: 'short' | 'long' = 'short'): string {
  return visaLabels[code][form]
}
