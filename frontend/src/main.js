import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import router from './router/index.js'
import i18n   from './i18n/index.js'
import App    from './App.vue'

const vuetify = createVuetify({
  icons: { defaultSet: 'mdi', aliases, sets: { mdi } },
  theme: {
    defaultTheme: 'wt',
    themes: {
      wt: {
        dark: true,
        colors: {
          background:   '#020c1a',
          surface:      '#0f172a',
          'surface-2':  '#1e293b',
          primary:      '#a7f3d0',
          secondary:    '#a78bfa',
          accent:       '#34d399',
          warning:      '#fbbf24',
          error:        '#f87171',
          info:         '#60a5fa',
          'on-surface': '#e2e8f0',
          border:       '#1e3a5f',
        },
      },
    },
  },
  defaults: {
    VBtn:         { variant: 'tonal', rounded: 'lg' },
    VCard:        { rounded: 'lg' },
    VChip:        { rounded: 'sm' },
    VTextField:   { variant: 'outlined', density: 'compact', hideDetails: 'auto' },
    VSelect:      { variant: 'outlined', density: 'compact', hideDetails: 'auto' },
    VRangeSlider: { hideDetails: 'auto' },
  },
})

const app = createApp(App)
app.use(createPinia())
app.use(vuetify)
app.use(router)
app.use(i18n)
app.mount('#app')
