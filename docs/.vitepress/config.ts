import { defineConfig } from 'vitepress'

export default defineConfig({
  lang: 'ru-RU',
  title: 'Travel Expert Calendar',
  base: '/travel_with_pleasure/',

  themeConfig: {
    nav: [
      { text: 'Календарь', link: '/' },
      { text: 'Направления', link: '/destinations' },
      { text: 'Авиабилеты', link: '/flights' }
    ]
  }
})