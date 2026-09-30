import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import { wtVuetify } from './theme/theme.js'
import router from './router/index.js'
import i18n   from './i18n/index.js'
import App    from './app.vue'

import './styles/global.css'

const GA_ID = import.meta.env.VITE_GA_ID
if (GA_ID) {
  const s = document.createElement('script')
  s.async = true
  s.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`
  document.head.appendChild(s)
  window.dataLayer = window.dataLayer || []
  window.gtag = function () { window.dataLayer.push(arguments) }
  window.gtag('js', new Date())
  window.gtag('config', GA_ID, { send_page_view: false })
}

const vuetify = createVuetify({
  icons: { defaultSet: 'mdi', aliases, sets: { mdi } },
  ...wtVuetify,
})

const app = createApp(App)
app.use(createPinia())
app.use(vuetify)
app.use(router)
router.afterEach(to => {
  if (window.gtag) {
    window.gtag('event', 'page_view', {
      page_path:  to.fullPath,
      page_title: to.name ?? to.fullPath,
    })
  }
})
app.use(i18n)
app.mount('#app')
