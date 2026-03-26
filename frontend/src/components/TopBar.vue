<template>
  <v-app-bar
    elevation="0"
    height="48"
    style="background: #0a1628; border-bottom: 1px solid #1e3a5f; z-index: 1000;"
  >
    <v-app-bar-title class="logo-title flex-shrink-0">
      {{ t('topbar.title') }}
    </v-app-bar-title>

    <v-spacer />

    <!-- Global search -->
    <div class="search-wrapper" ref="searchRef">
      <v-text-field
        v-model="query"
        :placeholder="t('topbar.search_hint')"
        prepend-inner-icon="mdi-magnify"
        clearable
        variant="outlined"
        density="compact"
        hide-details
        style="width: 280px; font-size: 12px;"
        @focus="showResults = true"
        @blur="onBlur"
        @keydown.escape="closeSearch"
      />
      <Transition name="fade">
        <div v-if="showResults && (query?.length ?? 0) >= 2" class="search-dropdown">
          <div class="search-header">{{ t('topbar.search_header') }}</div>
          <template v-if="hits.length">
            <div
              v-for="(v, i) in hits"
              :key="i"
              class="search-item"
              @mousedown.prevent="selectVehicle(v)"
            >
              <span class="item-name">{{ displayName(v) }}</span>
              <span class="item-meta">{{ fmtNation(v.Nation) }} · BR {{ fmtBR(v.BR) }} · {{ fmtType(v.Type) }}</span>
            </div>
          </template>
          <div v-else class="search-empty">{{ t('topbar.search_empty') }}</div>
        </div>
      </Transition>
    </div>

    <!-- Language switcher -->
    <div class="lang-switcher ml-3">
      <v-btn
        v-for="loc in SUPPORTED_LOCALES"
        :key="loc.code"
        :variant="locale === loc.code ? 'tonal' : 'text'"
        size="x-small"
        class="lang-btn"
        @click="switchLocale(loc.code)"
      >
        {{ loc.flag }} {{ loc.label }}
      </v-btn>
    </div>

    <div class="px-2" />
  </v-app-bar>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import { setLocale, SUPPORTED_LOCALES } from '../i18n/index.js'
import { vehicleDisplayName, fmtNation, fmtBR, fmtType } from '../composables/useVehicleFormatting.js'

const { t, locale } = useI18n()
const store          = useDataStore()
const openVehicle    = inject('openVehicle')

const query       = ref('')
const showResults = ref(false)

function displayName(v) { return vehicleDisplayName(v) }

const hits = computed(() => {
  const q = query.value?.trim()
  if (!q || q.length < 2 || !store.allVehicles.length) return []
  const lower = q.toLowerCase()
  const seen  = new Set()
  const result = []
  for (const v of store.allVehicles) {
    if (!v.Name?.toLowerCase().includes(lower)) continue
    const key = `${v.Name}||${v.Nation}`
    if (seen.has(key)) continue
    seen.add(key)
    result.push(v)
    if (result.length >= 15) break
  }
  return result
})

function selectVehicle(v) {
  openVehicle(v)
  closeSearch()
}

function closeSearch() {
  showResults.value = false
  query.value = ''
}

function onBlur() {
  setTimeout(() => { showResults.value = false }, 200)
}

function switchLocale(code) {
  setLocale(code)
}
</script>

<style scoped>
.logo-title {
  font-family: 'Rajdhani', sans-serif !important;
  font-size: 18px !important;
  font-weight: 700 !important;
  color: #a7f3d0 !important;
  letter-spacing: 0.08em;
}
.search-wrapper { position: relative; }
.search-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  width: 360px;
  background: #0f172a;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,.7);
  z-index: 9999;
  max-height: 420px;
  overflow-y: auto;
}
.search-header {
  padding: 6px 14px;
  background: #0a1628;
  border-bottom: 1px solid #1e3a5f;
  color: #475569;
  font-size: 10px;
  letter-spacing: .1em;
  text-transform: uppercase;
  user-select: none;
}
.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  border-bottom: 1px solid #0f172a;
  cursor: pointer;
  transition: background .1s;
  gap: 8px;
}
.search-item:hover { background: #1e293b; }
.item-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-meta { font-size: 10px; color: #64748b; white-space: nowrap; flex-shrink: 0; }
.search-empty { padding: 12px 14px; color: #475569; font-size: 12px; font-style: italic; }
.lang-switcher { display: flex; gap: 2px; }
.lang-btn { font-family: 'Rajdhani', sans-serif !important; font-size: 11px !important; min-width: 44px !important; }
.fade-enter-active, .fade-leave-active { transition: opacity .12s; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
