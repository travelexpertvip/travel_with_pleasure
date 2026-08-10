<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { data as tours } from '../data/tours.data'
import { data as destinations } from '../data/destinations.data'
import { months } from '../data/destinations'

const current = ref(new Date().getMonth())

const localToday = () => {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

const isExpiredSpecialOffer = (tour: typeof tours[number]) =>
  tour.offer_type === 'special' &&
  Boolean(tour.special_offer_valid_until) &&
  tour.special_offer_valid_until! < localToday()

const activeTours = computed(() =>
  tours
    .filter(
      tour =>
        tour.status === 'active' &&
        !isExpiredSpecialOffer(tour)
    )
    .sort((a, b) => a.price - b.price)
)

const tourMonth = (value: unknown) => {
  if (!value) return null

  const raw =
    value instanceof Date
      ? value.toISOString().slice(0, 10)
      : String(value)

  const isoMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (isoMatch) return Number(isoMatch[2]) - 1

  return null
}

const currentMonthTours = computed(() =>
  activeTours.value.filter(
    tour => tourMonth(tour.departure_date) === current.value
  )
)
const selectedTourIds = ref<string[]>([])
const showSelection = ref(false)
const showArchive = ref(false)
const archiveDestination = ref('all')
const shareStatus = ref('')

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

watch(
  selectedTourIds,
  value => {
    localStorage.setItem('my-tour-selection', JSON.stringify(value))
  },
  { deep: true }
)

const isTourSelected = (tourId: string) =>
  selectedTourIds.value.includes(tourId)

const toggleTour = (tourId: string) => {
  selectedTourIds.value = isTourSelected(tourId)
    ? selectedTourIds.value.filter(id => id !== tourId)
    : [...selectedTourIds.value, tourId]
}

const myTours = computed(() =>
  activeTours.value.filter(tour =>
    selectedTourIds.value.includes(tour.id)
  )
)

const archivedTours = computed(() =>
  tours
    .filter(
      tour =>
        tour.status === 'archived' ||
        isExpiredSpecialOffer(tour)
    )
    .sort((a, b) => a.price - b.price)
)

const filteredArchivedTours = computed(() =>
  archivedTours.value.filter(
    tour =>
      archiveDestination.value === 'all' ||
      tour.destination_id === archiveDestination.value
  )
)

const selectionText = computed(() => {
  const items = myTours.value.map((tour, index) =>
    [
      `${index + 1}. ${tour.hotel} · ${tour.stars}★`,
      `${tour.nights} ночей · ${tour.meal_plan}`,
      `${tour.departure_city} · ${tour.departure_date} — ${tour.return_date}`,
      tour.flight,
      `от ${tour.price.toLocaleString('ru-RU')} ${tour.currency}`,
      tour.hotel_url || ''
    ]
      .filter(Boolean)
      .join('\n')
  )

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
const formatTourDate = (value: unknown) => {
  if (!value) return 'Дата уточняется'

  const raw =
    value instanceof Date
      ? value.toISOString().slice(0, 10)
      : String(value).slice(0, 10)

  const [year, month, day] = raw.split('-')

  if (!year || !month || !day) return 'Дата уточняется'

  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC'
  }).format(new Date(`${year}-${month}-${day}T00:00:00Z`))
}
</script>

<template>
  <main class="travel">
    <section class="hero">
      <span class="eyebrow">Готовые предложения</span>
      <h1>Туры<br><em>по месяцам</em></h1>
      <p>Выберите месяц, чтобы посмотреть актуальные предложения с перелётом.</p>
    </section>

    <section class="months">
      <button
        v-for="(month, index) in months"
        :key="month"
        :class="{ active: index === current }"
        @click="current = index"
      >
        <b>{{ month }}</b>
        <small>
          {{ activeTours.filter(tour => tourMonth(tour.departure_date) === index).length }} туров
        </small>
      </button>
    </section>

    <section class="tour-showcase">
      <div class="showcase-heading">
        <div>
          <span class="region">Активные предложения</span>
          <h2>Туры в {{ months[current] }}</h2>
        </div>

        <b>{{ currentMonthTours.length }} туров</b>
      </div>

      <div v-if="currentMonthTours.length" class="tour-showcase-grid">
        <article
          v-for="tour in currentMonthTours"
          :key="tour.id"
          class="tour-card"
        >
          <span class="region">
            {{ destinations.find(x => x.id === tour.destination_id)?.name || tour.destination_id }}
          </span>

          <strong>{{ tour.hotel }} · {{ tour.stars }}★</strong>

          <p>{{ tour.nights }} ночей · {{ tour.meal_plan }}</p>

          <p>
            ✈ {{ tour.departure_city }} ·
            {{ formatTourDate(tour.departure_date) }} —
            {{ formatTourDate(tour.return_date) }}
          </p>

          <p>{{ tour.flight }}</p>

          <p class="price">
            от {{ tour.price.toLocaleString('ru-RU') }} {{ tour.currency }}
          </p>

          <small>{{ tour.price_note }}</small>
<button
  type="button"
  class="tour-select"
  :class="{ selected: isTourSelected(tour.id) }"
  @click="toggleTour(tour.id)"
>
  {{ isTourSelected(tour.id) ? '✓ В моей подборке' : '+ В мою подборку' }}
</button>

          <p v-if="tour.hotel_url">
            <a
              :href="tour.hotel_url"
              target="_blank"
              rel="noreferrer"
            >
              Об отеле ↗
            </a>
          </p>
        </article>
      </div>

      <p v-else class="empty">
        В {{ months[current] }} пока нет активных туров.
      </p>
    </section>
  </main>
  <button
  v-if="selectedTourIds.length"
  type="button"
  class="selection-button"
  @click="showSelection = true"
>
  Моя подборка ({{ selectedTourIds.length }})
</button>

<button
  type="button"
  class="archive-button"
  @click="showArchive = true"
>
  Архив туров ({{ archivedTours.length }})
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
      <span class="region">
        {{ destinations.find(x => x.id === tour.destination_id)?.name || tour.destination_id }}
      </span>

      <strong>{{ tour.hotel }} · {{ tour.stars }}★</strong>
      <p>{{ tour.nights }} ночей · {{ tour.meal_plan }}</p>

      <p>
        ✈ {{ tour.departure_city }} ·
        {{ formatTourDate(tour.departure_date) }} —
        {{ formatTourDate(tour.return_date) }}
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

<div
  v-if="showArchive"
  class="back"
  @click.self="showArchive = false"
>
  <article class="modal">
    <button class="close" @click="showArchive = false">×</button>

    <span class="region">Неактуальные предложения</span>
    <h2>Архив туров</h2>

    <select v-model="archiveDestination">
      <option value="all">Все страны</option>

      <option
        v-for="destination in destinations"
        :key="destination.id"
        :value="destination.id"
      >
        {{ destination.name }}
      </option>
    </select>

    <article
      v-for="tour in filteredArchivedTours"
      :key="tour.id"
      class="tour-card"
    >
      <span class="region">
        {{ destinations.find(x => x.id === tour.destination_id)?.name || tour.destination_id }}
      </span>

      <strong>{{ tour.hotel }} · {{ tour.stars }}★</strong>

      <p v-if="tour.offer_type === 'special'" class="tour-special">
        СПО завершилось: {{ tour.special_offer_valid_until }}
      </p>

      <p>{{ tour.nights }} ночей · {{ tour.meal_plan }}</p>

      <p>
        ✈ {{ tour.departure_city }} ·
        {{ formatTourDate(tour.departure_date) }} —
        {{ formatTourDate(tour.return_date) }}
      </p>

      <p>{{ tour.flight }}</p>

      <p class="price">
        от {{ tour.price.toLocaleString('ru-RU') }} {{ tour.currency }}
      </p>
    </article>

    <p v-if="!filteredArchivedTours.length" class="note">
      В архиве нет туров по выбранной стране.
    </p>
  </article>
</div>
</template>