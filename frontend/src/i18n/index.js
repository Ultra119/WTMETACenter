import { createI18n } from 'vue-i18n'
import ru from '../locales/ru.json'
import en from '../locales/en.json'

// localStorage throws in blocked-storage browsers and does not exist during SSR
export function safeGet(key) {
  try { return localStorage.getItem(key) } catch { return null }
}

export function safeSet(key, value) {
  try { localStorage.setItem(key, value) } catch { /* storage unavailable */ }
}

function detectLocale() {
  const saved = safeGet('wt-locale')
  if (saved && ['ru', 'en'].includes(saved)) return saved
  const browser = (typeof navigator !== 'undefined' ? navigator.language : '')?.slice(0, 2)
  return browser === 'ru' ? 'ru' : 'en'
}

const i18n = createI18n({
  legacy:        false,
  locale:        detectLocale(),
  fallbackLocale: 'en',
  messages:      { ru, en },
})

export default i18n

export function setLocale(lang) {
  i18n.global.locale.value = lang
  safeSet('wt-locale', lang)
  // keep the document language in sync with the UI language
  if (typeof document !== 'undefined') document.documentElement.lang = lang
}

export const SUPPORTED_LOCALES = [
  { code: 'ru', label: 'RU', flag: '🇷🇺' },
  { code: 'en', label: 'EN', flag: '🇬🇧' },
]
