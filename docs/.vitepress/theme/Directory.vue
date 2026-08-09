<script setup lang="ts">
import { computed, ref } from 'vue'
import { useData } from 'vitepress'
import { data as destinations } from '../data/destinations.data'
import { months, ui, visaLabel } from '../data/destinations'

const { frontmatter } = useData<{
  eyebrow: string
  title: string
}>()

const labels = ui.directory
const q = ref('')

const rows = computed(() =>
  destinations.filter(x => JSON.stringify(x).toLowerCase().includes(q.value.toLowerCase()))
)
</script>

<template>
  <main class="travel">
    <section class="hero short">
      <span class="eyebrow">{{ frontmatter.eyebrow }}</span>
      <h1>{{ frontmatter.title }}</h1>
    </section>

    <section class="filters one">
      <input v-model="q" :placeholder="labels.searchPlaceholder">
    </section>

    <p class="note">{{ labels.visaDisclaimer }}</p>
    <div class="table">
      <table>
        <thead>
          <tr>
            <th>{{ labels.tableHeaders.destination }}</th>
            <th>{{ labels.tableHeaders.region }}</th>
            <th>{{ labels.tableHeaders.visa }}</th>
            <th>{{ labels.tableHeaders.airport }}</th>
            <th>{{ labels.tableHeaders.diving }}</th>
            <th>{{ labels.tableHeaders.season }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="x in rows" :key="x.id">
            <td><b>{{ x.name }}</b></td>
            <td>{{ x.region }}</td>
            <td>
  {{ visaLabel(x.visa, 'long') }}
  <span
    v-if="x.verification_status === 'unverified'"
    title="Требуется проверка условий въезда"
    aria-label="Требуется проверка условий въезда"
    style="color: #f4b63a; margin-left: 6px; cursor: help;"
  >
    ⚠
  </span>
</td>
            <td>{{ x.airport }}</td>
            <td>{{ x.diving }}</td>
            <td>{{ x.season.map(i => months[i].slice(0, 3)).join(', ') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>
