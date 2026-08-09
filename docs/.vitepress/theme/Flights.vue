<script setup lang="ts">
import { useData } from 'vitepress'
import { destinations, ui } from '../data/destinations'

const { frontmatter } = useData<{
  eyebrow: string
  title: string
  description: string
}>()

const labels = ui.flights
</script>

<template>
  <main class="travel">
    <section class="hero short">
      <span class="eyebrow">{{ frontmatter.eyebrow }}</span>
      <h1>{{ frontmatter.title }}</h1>
      <p>{{ frontmatter.description }}</p>
    </section>

    <section class="cards">
      <article v-for="x in destinations" :key="x.id" class="card flight">
        <span class="region">{{ x.region }}</span>
        <h3>{{ x.name }}</h3>
        <p class="price">{{ x.priceFrom }}</p>
        <p class="airlines">{{ x.flights.join(' · ') }}</p>
        <p class="desc">{{ x.budget }}. {{ labels.priceDisclaimer }}</p>
      </article>
    </section>
  </main>
</template>
