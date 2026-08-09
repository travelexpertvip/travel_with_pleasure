<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useData } from 'vitepress'
import { data as tours } from '../data/tours.data'
import { data as destinations } from '../data/destinations.data'
import {
  months,
  ui,
  visaLabel,
  type Destination,
  type DivingLevel,
  type VisaCode
} from '../data/destinations'

const { frontmatter } = useData<{
  eyebrow: string
  title: string
  accent: string
  description: string
}>()

const labels = ui.calendar
const current = ref(new Date().getMonth())
const q = ref('')
const region = ref('all')
const visa = ref<'all' | VisaCode>('all')
const diving = ref<'all' | DivingLevel>('all')
const selected = ref<Destination | null>(null)
const activeTours = computed(() =>
  tours.filter(tour => tour.status === 'active')
)

const tourCount = (destinationId: string) =>
  activeTours.value.filter(tour => tour.destination_id === destinationId).length

const selectedTours = computed(() =>
  selected.value
    ? activeTours.value.filter(tour => tour.destination_id === selected.value?.id)
    : []
)

const selectedTourIds = ref<string[]>([])

onMounted(() => {
  const saved = localStorage.getItem('my-tour-selection')

  if (saved) {
    try {
      selectedTourIds.value = JSON.parse(saved)
    } catch {
      selectedTourIds.value = []
    }
  }
})

watch(selectedTourIds, value => {
  localStorage.setItem('my-tour-selection', JSON.stringify(value))
}, { deep: true })

const isTourSelected = (tourId: string) =>
  selectedTourIds.value.includes(tourId)

const toggleTour = (tourId: string) => {
  selectedTourIds.value = isTourSelected(tourId)
    ? selectedTourIds.value.filter(id => id !== tourId)
    : [...selectedTourIds.value, tourId]
}
const showSelection = ref(false)

const myTours = computed(() =>
  activeTours.value.filter(tour =>
    selectedTourIds.value.includes(tour.id)
  )
)

const openSelection = () => {
  selected.value = null
  showSelection.value = true
}
const shareStatus = ref('')

const selectionText = computed(() => {
  const items = myTours.value.map((tour, index) => [
    `${index + 1}. ${tour.hotel} · ${tour.stars}★`,
    `${tour.nights} ночей · ${tour.meal_plan}`,
    `${tour.departure_city} · ${tour.departure_date} — ${tour.return_date}`,
    tour.flight,
    `от ${tour.price.toLocaleString('ru-RU')} ${tour.currency}`,
    tour.hotel_url || ''
  ].filter(Boolean).join('\n'))

  return ['Моя подборка туров', '', ...items].join('\n\n')
})

const shareSelection = async () => {
  shareStatus.value = ''

  try {
    if (navigator.share) {
      await navigator.share({
        text: selectionText.value
      })
    } else {
      await navigator.clipboard.writeText(selectionText.value)
      shareStatus.value = 'Подборка скопирована'
    }
  } catch {
    shareStatus.value = 'Отправка отменена'
  }
}
const regions = computed(() =>
  [...new Set(destinations.map(x => x.region))].sort()
)
const rows = computed(() =>
  destinations.filter(
    x =>
      x.season.includes(current.value) &&
      JSON.stringify(x).toLowerCase().includes(q.value.toLowerCase()) &&
      (region.value === 'all' || x.region === region.value) &&
      (visa.value === 'all' || x.visa === visa.value) &&
      (diving.value === 'all' || x.diving === diving.value)
  )
)
</script>

<template>
  <main class="travel">
    <section class="hero">
      <span class="eyebrow">{{ frontmatter.eyebrow }}</span>
      <h1>{{ frontmatter.title }}<br><em>{{ frontmatter.accent }}</em></h1>
      <p>{{ frontmatter.description }}</p>
      <p class="note">{{ labels.visaDisclaimer }}</p>
    </section>

    <section class="filters">
      <input v-model="q" :placeholder="labels.searchPlaceholder">
      <select v-model="region">
        <option value="all">{{ labels.regionAll }}</option>
        <option v-for="x in regions" :key="x" :value="x">{{ x }}</option>
      </select>
      <select v-model="visa">
        <option value="all">{{ labels.visaAll }}</option>
        <option value="Б">{{ labels.visaNo }}</option>
        <option value="П">{{ labels.visaOnArrival }}</option>
      </select>
      <select v-model="diving">
        <option value="all">{{ labels.divingAll }}</option>
        <option value="Развитая">{{ labels.divingDeveloped }}</option>
        <option value="Есть">{{ labels.divingAvailable }}</option>
        <option value="Ограниченная">{{ labels.divingLimited }}</option>
      </select>
    </section>

    <section class="months">
      <button
        v-for="(x, i) in months"
        :key="x"
        :class="{ active: i === current }"
        @click="current = i"
      >
        <b>{{ x }}</b>
        <small>{{ destinations.filter(y => y.season.includes(i)).length }} {{ labels.monthCountSuffix }}</small>
      </button>
    </section>

    <section class="summary">
      <div>
        <h2>{{ months[current] }} {{ labels.summaryTitle }}</h2>
        <p>{{ labels.summarySubtitle }}</p>
      </div>
      <b>{{ rows.length }} {{ labels.summaryCount }} {{ destinations.length }} {{ labels.summaryCountSuffix }}</b>
    </section>

    <section class="cards">
      <button v-for="x in rows" :key="x.id" class="card" @click="selected = x">
      <span
  v-if="tourCount(x.id)"
  class="tour-corner"
  title="Есть готовые туры"
  aria-label="Есть готовые туры"
>
  ✈
</span>
        <span class="region">{{ x.region }}</span>
        <h3>{{ x.name }}</h3>
        <p class="airport">{{ labels.airportPrefix }} {{ x.airport }}</p>
        <div class="badges">
          <span class="badge visa">{{ labels.badgeVisaPrefix }} {{ visaLabel(x.visa) }}</span>
          <span class="badge dive">{{ labels.badgeDivingPrefix }} {{ x.diving }}</span>
          <span class="badge budget">{{ x.budget }}</span>
        </div>
        <p class="desc">{{ x.description }}</p>
      </button>
      <div v-if="!rows.length" class="empty">{{ labels.emptyState }}</div>
    </section>
  </main>
<button
  v-if="selectedTourIds.length"
  type="button"
  class="selection-button"
  @click="openSelection"
>
  Моя подборка ({{ selectedTourIds.length }})
</button>
<div
  v-if="showSelection"
  class="back"
  @click.self="showSelection = false"
>
  <article class="modal">
    <button class="close" @click="showSelection = false">×</button>

    <span class="region">Выбранные предложения</span>
    <h2>Моя подборка</h2>

    <article
      v-for="tour in myTours"
      :key="tour.id"
      class="tour-card"
    >
      <strong>{{ tour.hotel }} · {{ tour.stars }}★</strong>
      <p>{{ tour.nights }} ночей · {{ tour.meal_plan }}</p>

      <p>
        ✈ {{ tour.departure_city }} ·
        {{ tour.departure_date }} — {{ tour.return_date }}
      </p>

      <p>{{ tour.flight }}</p>

      <p class="price">
        от {{ tour.price.toLocaleString('ru-RU') }} {{ tour.currency }}
      </p>

      <button
        type="button"
        class="selection-remove"
        @click="toggleTour(tour.id)"
      >
        Удалить из подборки
      </button>
    </article>
<button
  v-if="myTours.length"
  type="button"
  class="selection-share"
  @click="shareSelection"
>
  Поделиться подборкой
</button>

<p v-if="shareStatus" class="note">
  {{ shareStatus }}
</p>
  </article>
</div>
  <div v-if="selected" class="back" @click.self="selected = null">
    <article class="modal">
      <button class="close" @click="selected = null">×</button>
      <span class="region">{{ selected.region }}</span>
      <h2>{{ selected.name }}</h2>
      <p class="airport">{{ labels.airportPrefix }} {{ selected.airport }}</p>
      <p v-if="selected.temperature" class="airport">
  Температура: {{ selected.temperature }}
</p>
      <div class="badges">
        <span class="badge visa">{{ labels.badgeVisaPrefix }} {{ visaLabel(selected.visa) }}</span>
        <span class="badge dive">{{ labels.badgeDivingPrefix }} {{ selected.diving }}</span>
      </div>
      <p class="price">{{ selected.budget }} · {{ selected.priceFrom }}</p>
      <p v-if="selected.visa_note" class="note">
  <span
    v-if="selected.verification_status === 'unverified'"
    title="Требуется проверка условий въезда"
    aria-label="Требуется проверка условий въезда"
    style="color: #f4b63a; margin-right: 6px;"
  >
    ⚠
  </span>
  {{ selected.visa_note }}
</p>
<p v-if="selected.visa_checked_at" class="note">
  Проверено: {{ selected.visa_checked_at }}
</p>

<a
  v-if="selected.visa_source_url"
  :href="selected.visa_source_url"
  target="_blank"
  rel="noreferrer"
  class="note"
>
  Официальный источник условий въезда ↗
</a>
      <h4>{{ labels.modalFlightsTitle }}</h4>
<ul>
  <li v-for="f in selected.flights" :key="f">{{ f }}</li>
</ul>
<section v-if="selectedTours.length">
  <h4>Туры с перелётом</h4>

  <article
    v-for="tour in selectedTours"
    :key="tour.id"
    class="tour-card"
  >
    <strong>{{ tour.hotel }} · {{ tour.stars }}★</strong>

    <p>{{ tour.nights }} ночей · {{ tour.meal_plan }}</p>

    <p>
      ✈ {{ tour.departure_city }} ·
      {{ tour.departure_date }} — {{ tour.return_date }}
    </p>

    <p>{{ tour.flight }}</p>

    <p class="price">
      от {{ tour.price.toLocaleString('ru-RU') }} {{ tour.currency }}
    </p>

    <small>{{ tour.price_note }}</small>

    <p v-if="tour.hotel_url">
      <a
        :href="tour.hotel_url"
        target="_blank"
        rel="noreferrer"
      >
        Об отеле ↗
      </a>
    </p>
<button
  type="button"
  class="tour-select"
  :class="{ selected: isTourSelected(tour.id) }"
  @click="toggleTour(tour.id)"
>
  {{ isTourSelected(tour.id) ? '✓ В моей подборке' : '+ В мою подборку' }}
</button>
<p v-if="shareStatus" class="note">
  {{ shareStatus }}
</p>
  </article>
</section>
<h4>{{ labels.modalFeaturesTitle }}</h4>
<p class="desc noborder">{{ selected.description }}</p>
<p class="note">{{ labels.modalNote }}</p>
</article>
</div>
</template>
