<template>
  <v-app-bar flat color="background" height="56" class="hairline-b" style="z-index: 1000;">
    <button
      v-if="!isHomePage"
      class="sidebar-toggle"
      :title="sidebarOpen ? 'Hide sidebar' : 'Show sidebar'"
      @click="toggleSidebar()"
    >
      <span class="mdi" :class="sidebarOpen ? 'mdi-backburger' : 'mdi-menu'" />
    </button>

    <v-app-bar-title>
      <div class="logo-group">
        <router-link to="/" class="logo-title-link">
          <span class="logo-title">{{ t('topbar.title') }}</span>
        </router-link>
        <a
          href="https://github.com/Ultra119/wt_meta_center/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="report-link"
          :title="t('topbar.report_title')"
        >
          <span class="mdi mdi-bug-outline" />
          <span class="report-text">{{ t('topbar.report') }}</span>
        </a>
      </div>
    </v-app-bar-title>

    <v-spacer />

    <div class="search-wrapper" ref="wrapperRef">

      <div class="search-field" :class="{ 'search-field--active': isOpen || (tabOwnsSearch && query.trim().length >= 2) }">
        <span class="mdi mdi-magnify search-icon" />
        <input
          ref="inputRef"
          v-model="query"
          class="search-input"
          :placeholder="t('topbar.search_hint')"
          autocomplete="off"
          spellcheck="false"
          @input="onInput"
          @focus="onFocus"
          @keydown.escape="closeSearch"
          @keydown.down.prevent="moveDown"
          @keydown.up.prevent="moveUp"
          @keydown.enter.prevent="selectActive"
        />
        <button v-if="query" class="search-clear" tabindex="-1" @mousedown.prevent="clearQuery">
          <span class="mdi mdi-close" />
        </button>
      </div>

      <Teleport to="body">
        <Transition name="dropdown">
          <div
            v-if="isOpen && !tabOwnsSearch"
            class="search-dropdown"
            :style="dropdownStyle"
          >
            <div class="search-header">
              {{ t('topbar.search_header') }}
              <span v-if="hits.length" class="search-count">{{ hits.length }}</span>
            </div>

            <div v-if="hits.length" class="search-list">
              <div
                v-for="(v, i) in hits"
                :key="v.Name + v.Nation"
                class="search-item"
                :class="{ 'search-item--active': i === activeIdx }"
                @mousedown.prevent="pick(v)"
                @mousemove="activeIdx = i"
              >
                <div class="item-left">
                  <v-icon class="item-type-icon" size="13">{{ typeIcon(v.Type) }}</v-icon>
                  <span class="item-name">{{ vehicleDisplayName(v) }}</span>
                </div>
                <div class="item-right">
                  <span class="item-flag" :title="v.Nation">{{ nationFlag(v.Nation) }}</span>
                  <span class="item-br">{{ fmtBR(v.BR) }}</span>
                </div>
              </div>
            </div>

            <div v-else class="search-empty">
              <span class="mdi mdi-magnify-remove-outline" style="font-size:20px; opacity:0.3" />
              {{ t('topbar.search_empty') }}
            </div>
          </div>
        </Transition>
      </Teleport>
    </div>

    <v-btn-toggle
      :model-value="locale"
      mandatory
      density="compact"
      color="primary"
      class="lang-switcher ml-3"
      @update:model-value="setLocale"
    >
      <v-btn v-for="loc in SUPPORTED_LOCALES" :key="loc.code" :value="loc.code" size="small">
        {{ loc.label }}
      </v-btn>
    </v-btn-toggle>

    <button
      class="about-toggle ml-2"
      :title="t('about.btn_title')"
      @click="aboutOpen = true"
    >
      <span class="mdi mdi-information-outline" />
    </button>

    <div class="px-2" />
  </v-app-bar>

  <AboutDialog v-model="aboutOpen" />
</template>

<script setup>
import { ref, shallowRef, watchEffect, nextTick, inject, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import { setLocale, SUPPORTED_LOCALES } from '../i18n/index.js'
import { vehicleDisplayName, fmtBR, NATION_FLAG } from '../composables/useVehicleFormatting.js'
import { TYPE_ICON } from '../composables/constants.js'
import AboutDialog from './AboutDialog.vue'

const { t, locale } = useI18n()
const store         = useDataStore()
const route         = useRoute()
const openVehicle   = inject('openVehicle')
const toggleSidebar = inject('toggleSidebar', null)
const sidebarOpen   = inject('sidebarOpen', null)

const isHomePage = computed(() => route.path === '/')

const tabOwnsSearch = computed(() => store.metaTabActive || store.historyTabActive)

const query      = ref('')
const isOpen     = ref(false)
const activeIdx  = ref(-1)
const inputRef   = ref(null)
const wrapperRef = ref(null)
const aboutOpen  = ref(false)

const dropdownStyle = ref({})
watch(query, q => { store.searchQuery = q.trim() })

function updateDropdownPos() {
  if (!wrapperRef.value) return
  const rect = wrapperRef.value.getBoundingClientRect()
  dropdownStyle.value = {
    position: 'fixed',
    top:      rect.bottom + 6 + 'px',
    right:    window.innerWidth - rect.right + 'px',
    width:    '380px',
    zIndex:   9999,
  }
}

function onDocClick(e) {
  if (!wrapperRef.value?.contains(e.target)) closeSearch()
}

onMounted(()        => document.addEventListener('mousedown', onDocClick))
onBeforeUnmount(()  => document.removeEventListener('mousedown', onDocClick))

const MAX_HITS = 12
const hits = shallowRef([])

watchEffect(() => {
  const q        = query.value.trim()
  const vehicles = store.allVehicles

  nextTick(() => {
    if (q.length < 2) { hits.value = []; return }
    const lower  = q.toLowerCase()
    const seen   = new Set()
    const result = []
    for (const v of (vehicles ?? [])) {
      if (!v.Name?.toLowerCase().includes(lower)) continue
      const key = `${v.Name}||${v.Nation}`
      if (seen.has(key)) continue
      seen.add(key)
      result.push(v)
      if (result.length >= MAX_HITS) break
    }
    hits.value = result
  })
})

function typeIcon(type)     { return TYPE_ICON[type] ?? 'mdi-car' }
function nationFlag(nation) { return NATION_FLAG[nation?.toLowerCase()] ?? '🏴' }

function onInput() {
  activeIdx.value = -1
  const show = query.value.trim().length >= 2 && !tabOwnsSearch.value
  if (show) updateDropdownPos()
  isOpen.value = show
}

function onFocus() {
  if (query.value.trim().length >= 2 && !tabOwnsSearch.value) {
    updateDropdownPos()
    isOpen.value = true
  }
}

function closeSearch() { isOpen.value = false; activeIdx.value = -1 }

function clearQuery() {
  query.value     = ''
  isOpen.value    = false
  activeIdx.value = -1
  inputRef.value?.focus()
}

function pick(v) { openVehicle?.(v); closeSearch(); query.value = '' }

function moveDown() {
  if (!hits.value.length) return
  activeIdx.value = (activeIdx.value + 1) % hits.value.length
}
function moveUp() {
  if (!hits.value.length) return
  activeIdx.value = activeIdx.value <= 0 ? hits.value.length - 1 : activeIdx.value - 1
}
function selectActive() { const v = hits.value[activeIdx.value]; if (v) pick(v) }
</script>

<style scoped>
.sidebar-toggle,
.about-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0;
  color: var(--ink-muted);
  font-size: 18px;
  cursor: pointer;
  flex-shrink: 0;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}
.sidebar-toggle { margin-left: 12px; }
.sidebar-toggle:hover,
.about-toggle:hover {
  color: var(--primary);
  border-color: var(--hairline);
  background: var(--primary-soft);
}

.logo-group {
  display: inline-flex;
  align-items: baseline;
  gap: 14px;
}
.logo-title-link { text-decoration: none; color: inherit; }
.logo-title {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--ink);
  transition: color 0.15s;
}
.logo-title-link:hover .logo-title { color: var(--primary); }

.report-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ink-dim);
  text-decoration: none;
  font-family: var(--font-display);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  white-space: nowrap;
  flex-shrink: 0;
  transition: color 0.15s;
}
.report-link:hover { color: var(--primary); }
.report-link .mdi  { font-size: 13px; }
.report-text       { line-height: 1; }

.search-wrapper { position: relative; }

.search-field {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 380px;
  max-width: 100%;
  height: 36px;
  padding: 0 10px;
  background: transparent;
  border: 1px solid var(--hairline-strong);
  border-radius: 0;
  transition: border-color 0.15s, background 0.15s;
}
.search-field--active,
.search-field:focus-within {
  border-color: var(--primary);
  background: var(--primary-soft);
}

.search-icon { font-size: 16px; color: var(--ink-faint); flex-shrink: 0; }

.search-input {
  flex: 1;
  min-width: 0;
  background: none;
  border: none;
  outline: none;
  color: var(--ink);
  font-size: 12px;
  caret-color: var(--primary);
}
.search-input::placeholder { color: var(--ink-dim); }

.search-clear {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  padding: 0;
  background: none;
  border: none;
  color: var(--ink-faint);
  cursor: pointer;
  transition: color 0.12s;
}
.search-clear:hover { color: var(--ink); }
.search-clear .mdi  { font-size: 15px; }

.lang-switcher :deep(.v-btn) {
  font-family: var(--font-display);
  letter-spacing: 0.1em;
}

.dropdown-enter-active { transition: opacity 0.12s ease, transform 0.12s ease; }
.dropdown-leave-active { transition: opacity 0.08s ease; }
.dropdown-enter-from   { opacity: 0; transform: translateY(-4px); }
.dropdown-leave-to     { opacity: 0; }

@media (max-width: 900px) {
  .search-field { width: 220px; }
  .report-text  { display: none; }
}
@media (max-width: 640px) {
  .search-field { width: 150px; }
}
</style>

<style>
.search-dropdown {
  background: var(--surface);
  border: 1px solid var(--hairline-strong);
  border-radius: 0;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55);
  overflow: hidden;
}

.search-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-bottom: 1px solid var(--hairline);
  font-family: var(--font-display);
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--ink-faint);
  text-transform: uppercase;
  user-select: none;
}

.search-count {
  padding: 0 6px;
  border: 1px solid var(--hairline);
  font-family: var(--font-display);
  font-size: 11px;
  line-height: 18px;
  color: var(--ink-muted);
}

.search-list { max-height: 360px; overflow-y: auto; }

.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--hairline);
  cursor: pointer;
  transition: background 0.08s;
}
.search-item:last-child { border-bottom: none; }
.search-item:hover,
.search-item--active { background: rgba(94, 234, 212, 0.06); }

.item-left  { display: flex; align-items: center; gap: 8px; min-width: 0; }
.item-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.item-type-icon { font-size: 13px; flex-shrink: 0; line-height: 1; color: var(--ink-faint); }

.item-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-flag { font-size: 15px; line-height: 1; flex-shrink: 0; }

.item-br {
  padding: 0 6px;
  border: 1px solid var(--hairline);
  font-size: 11px;
  font-weight: 500;
  line-height: 18px;
  color: var(--primary);
  white-space: nowrap;
}

.search-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 28px 14px;
  font-family: var(--font-display);
  font-size: 12px;
  color: var(--ink-faint);
}
</style>
