<template>
  <v-app-bar flat color="background" height="56" class="hairline-b" style="z-index: 1000;">
    <button
      v-if="!isHomePage"
      class="ui-btn ui-btn--icon ui-btn--ghost ui-btn--lg ml-3"
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
          class="eyebrow report-link"
          :title="t('topbar.report_title')"
        >
          <span class="mdi mdi-bug-outline" />
          <span class="report-text">{{ t('topbar.report') }}</span>
        </a>
      </div>
    </v-app-bar-title>

    <v-spacer />

    <div class="search-wrapper" ref="wrapperRef">

      <div class="ui-field search-field" :class="{ 'is-active': isOpen || (tabOwnsSearch && query.trim().length >= 2) }">
        <span class="mdi mdi-magnify t-faint" />
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
        <button v-if="query" class="ui-btn ui-btn--icon ui-btn--ghost ui-btn--xs" tabindex="-1" @mousedown.prevent="clearQuery">
          <span class="mdi mdi-close" />
        </button>
      </div>

      <Teleport to="body">
        <Transition name="pop">
          <div
            v-if="isOpen && !tabOwnsSearch"
            class="popover search-dropdown"
            :style="dropdownStyle"
          >
            <div class="eyebrow search-header">
              {{ t('topbar.search_header') }}
              <span v-if="hits.length" class="tag">{{ hits.length }}</span>
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
                  <v-icon class="t-faint" size="13">{{ typeIcon(v.Type) }}</v-icon>
                  <span class="item-name">{{ vehicleDisplayName(v) }}</span>
                </div>
                <div class="item-right">
                  <span class="item-flag" :title="v.Nation">{{ nationFlag(v.Nation) }}</span>
                  <span class="tag text-primary">{{ fmtBR(v.BR) }}</span>
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
      class="ui-btn ui-btn--icon ui-btn--ghost ui-btn--lg ml-2"
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
.logo-group      { display: inline-flex; align-items: baseline; gap: 14px; }
.logo-title-link { color: inherit; text-decoration: none; }
.logo-title {
  font: 600 15px var(--font-display);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--ink);
  transition: color 0.15s;
}
.logo-title-link:hover .logo-title { color: var(--primary); }
.report-link       { display: inline-flex; align-items: center; gap: 5px; flex-shrink: 0; color: var(--ink-dim); text-decoration: none; white-space: nowrap; transition: color 0.15s; }
.report-link:hover { color: var(--primary); }

.search-wrapper { position: relative; }
.search-field   { width: 380px; max-width: 100%; }

.search-dropdown { overflow: hidden; }
.search-header   { display: flex; align-items: center; justify-content: space-between; padding: 8px 14px; border-bottom: 1px solid var(--hairline); user-select: none; }
.search-list     { max-height: 360px; overflow-y: auto; }
.search-item {
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--hairline);
  cursor: pointer;
  transition: background 0.08s;
}
.search-item:last-child { border-bottom: none; }
.search-item:hover,
.search-item--active    { background: var(--primary-soft); }
.item-left  { display: flex; align-items: center; gap: 8px; min-width: 0; }
.item-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.item-name  { font-size: 12px; font-weight: 500; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-flag  { font-size: 15px; line-height: 1; }
.search-empty {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 28px 14px;
  font: 12px var(--font-display);
  color: var(--ink-faint);
}

.lang-switcher :deep(.v-btn) { font-family: var(--font-display); letter-spacing: 0.1em; }

@media (max-width: 900px) { .search-field { width: 220px; } .report-text { display: none; } }
@media (max-width: 640px) { .search-field { width: 150px; } }
</style>
