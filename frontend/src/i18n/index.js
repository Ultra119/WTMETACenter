import { createI18n } from 'vue-i18n'
import ru from '../locales/ru.json'
import en from '../locales/en.json'

function detectLocale() {
  const saved = localStorage.getItem('wt-locale')
  if (saved && ['ru', 'en'].includes(saved)) return saved
  const browser = navigator.language?.slice(0, 2)
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
  localStorage.setItem('wt-locale', lang)
}

export const SUPPORTED_LOCALES = [
  { code: 'ru', label: 'RU', flag: '🇷🇺' },
  { code: 'en', label: 'EN', flag: '🇬🇧' },
]
