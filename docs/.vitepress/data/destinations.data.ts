import { createContentLoader } from 'vitepress'
import type { Destination } from './destinations'

declare const data: Destination[]
export { data }

export default createContentLoader('.vitepress/content/destinations/*.md', {
  transform(rawData) {
    return rawData.map(page => page.frontmatter as Destination)
  }
})
