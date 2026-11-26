import { fileURLToPath } from 'node:url'

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  telemetry: false,
  devtools: { enabled: false },
  hooks: {
    'pages:extend'(pages) {
      pages.push({ name: 'from-hook', path: '/from-hook', file: fileURLToPath(new URL('./app/pages/about.vue', import.meta.url)) })
    },
  },
  nitro: {
    handlers: [{ route: '/api/from-config', method: 'post', handler: fileURLToPath(new URL('./server/custom/config-handler.ts', import.meta.url)) }],
  },
})
