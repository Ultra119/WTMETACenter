<template>
  <v-navigation-drawer
    :model-value="open"
    :scrim="false"
    :width="272"
    color="surface"
    style="border-right: 1px solid var(--hairline); top: var(--topbar-h); height: calc(100% - var(--topbar-h));"
  >
    <div class="pa-3">
      <Transition name="fade">
        <div v-if="hiddenCount > 0" class="note note--dashed mb-3">
          <span class="mdi mdi-filter-off-outline" />
          {{ t('sidebar.filters_hidden', { n: hiddenCount }) }}
        </div>
      </Transition>

      <div v-if="cfg.period && store.periods.length > 1" class="sidebar-section">
        <div class="eyebrow sidebar-label">{{ t('sidebar.period') }}</div>
        <SegControl
          v-if="store.periods.length <= 5"
          v-model="store.currentPeriod"
          :options="periodOptions"
          fill
          gap
        />
        <v-select
          v-else
          :model-value="store.currentPeriod"
          :items="periodItems"
          item-title="label"
          item-value="value"
          density="compact"
          variant="outlined"
          hide-details
          class="period-select"
          @update:model-value="v => store.currentPeriod = v"
        />
      </div>

      <Transition name="section-fade">
        <div v-if="cfg.mode" class="sidebar-section">
          <div class="eyebrow sidebar-label">{{ t('sidebar.mode') }}</div>
          <SegControl v-model="store.mode" :options="modeOptions" fill />
        </div>
      </Transition>

      <Transition name="section-fade">
        <div v-if="cfg.brRange" class="sidebar-section">
          <div class="eyebrow sidebar-label">
            {{ t('sidebar.br_range') }}
            <span class="mono text-primary">{{ store.brRange[0].toFixed(1) }} – {{ store.brRange[1].toFixed(1) }}</span>
          </div>
          <v-range-slider
            :model-value="store.brRange"
            :min="store.BR_MIN"
            :max="store.BR_MAX"
            :step="0.1"
            color="primary"
            track-color="surface-variant"
            density="compact"
            class="mt-1 br-slider"
            @update:model-value="v => store.brRange = v.map(snapBR)"
          />
        </div>
      </Transition>

      <Transition name="section-fade">
        <div v-if="cfg.minBattles" class="sidebar-section">
          <div class="eyebrow sidebar-label">{{ t('sidebar.min_battles') }}</div>
          <div class="ui-field ui-field--flush mt-1">
            <button class="ui-btn ui-btn--icon ui-btn--ghost" @click="store.minBattles = Math.max(0, store.minBattles - 100)">
              <span class="mdi mdi-minus" />
            </button>
            <input
              v-model.number="store.minBattles"
              type="number"
              min="0"
              step="100"
            />
            <button class="ui-btn ui-btn--icon ui-btn--ghost" @click="store.minBattles += 100">
              <span class="mdi mdi-plus" />
            </button>
          </div>
        </div>
      </Transition>

      <Transition name="section-fade">
        <div v-if="cfg.classes" class="sidebar-section">
          <div class="eyebrow sidebar-label">
            {{ t('sidebar.vehicle_class') }}
          </div>
          <div class="chip-grid">
            <button
              v-for="cls in ALL_CLASSES"
              :key="cls"
              class="ui-btn ui-btn--left"
              :class="{ 'is-active': store.classes.includes(cls) }"
              @click="toggleClass(cls)"
            >
              <span
                v-if="CLASS_ICONS[cls]"
                class="mdi"
                :class="CLASS_ICONS[cls]"
                :style="store.classes.includes(cls) && CLASS_COLORS[cls] ? `color: ${CLASS_COLORS[cls]}` : ''"
              />
              <span class="chip-label">{{ t(`vehicle_classes.${cls}`) }}</span>
            </button>
          </div>
          <div v-if="!store.classes.length" class="note tint tint--warn mt-2">
            <span class="mdi mdi-alert-outline" />
            {{ t('sidebar.warn_no_classes') }}
          </div>
        </div>
      </Transition>

      <Transition name="section-fade">
        <div v-if="cfg.types" class="sidebar-section">
          <div class="eyebrow sidebar-label">{{ t('sidebar.vehicle_type') }}</div>
          <div class="chip-grid chip-grid--col">
            <button
              v-for="tp in TYPE_ENTRIES"
              :key="tp.key"
              class="ui-btn ui-btn--left"
              :class="{ 'is-active': store[tp.key] }"
              @click="store[tp.key] = !store[tp.key]"
            >
              <span class="mdi" :class="tp.icon" />
              <span>{{ t(tp.label) }}</span>
            </button>
          </div>
          <div v-if="mixWarning" class="note tint tint--warn mt-2">
            <span class="mdi mdi-alert-outline" />
            {{ mixWarning }}
          </div>
        </div>
      </Transition>

      <div v-if="store.metaInfo" class="sidebar-section">
        <div class="eyebrow sidebar-label">{{ t('common.dataset') }}</div>
        <div class="sidebar-info mono t-faint">
          <div>
            <v-icon size="11" style="opacity:.6;margin-right:3px">mdi-database</v-icon>
            {{ t('common.records', { n: store.metaInfo.total_records?.toLocaleString() }) }}
          </div>
          <div>
            <v-icon size="11" style="opacity:.6;margin-right:3px">mdi-clock-outline</v-icon>
            {{ t('sidebar.dataset_date', { date: generatedDate }) }}
          </div>
        </div>
      </div>

    </div>
  </v-navigation-drawer>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n }  from 'vue-i18n'

const props = defineProps({
  open: { type: Boolean, default: true },
})
import { useDataStore }     from '../stores/useDataStore.js'
import { formatPeriodLabel } from '../stores/useDataStore.js'
import { CLASS_PREFIX, CLASS_BR_COLOR } from '../composables/constants.js'
import SegControl from './ui/SegControl.vue'

const { t }  = useI18n()
const store  = useDataStore()

const ALL_FILTER_KEYS = ['period', 'mode', 'brRange', 'minBattles', 'classes', 'types']

const cfg = computed(() => {
  const base = Object.fromEntries(ALL_FILTER_KEYS.map(k => [k, true]))
  return store.tabFilterConfig ? { ...base, ...store.tabFilterConfig } : base
})

const hiddenCount = computed(() =>
  ALL_FILTER_KEYS.filter(k => !cfg.value[k]).length
)

const ALL_CLASSES = ['Standard','Premium','Pack','Squadron','Marketplace','Gift','Event']

const CLASS_ICONS  = CLASS_PREFIX
const CLASS_COLORS = CLASS_BR_COLOR

const TYPE_ENTRIES = [
  { key: 'showGround',      icon: 'mdi-tank',        label: 'sidebar.ground'      },
  { key: 'showAviation',    icon: 'mdi-airplane',    label: 'sidebar.aviation'    },
  { key: 'showHelicopters', icon: 'mdi-helicopter',  label: 'sidebar.helicopters' },
  { key: 'showLargeFleet',  icon: 'mdi-ferry',       label: 'sidebar.large_fleet' },
  { key: 'showSmallFleet',  icon: 'mdi-sail-boat',   label: 'sidebar.small_fleet' },
]

const MODES = [
  { value: 'Realistic' },
  { value: 'Arcade'    },
  { value: 'Simulator' },
]

function toggleClass(cls) {
  const idx = store.classes.indexOf(cls)
  if (idx === -1) store.classes.push(cls)
  else store.classes.splice(idx, 1)
}

function periodShort(p) {
  if (!p || p === 'All') return 'All'
  const parts = p.split('-')
  if (parts.length !== 2) return p
  try {
    const d = new Date(parseInt(parts[1], 10), parseInt(parts[0], 10) - 1, 1)
    const mon = d.toLocaleDateString(undefined, { month: 'short' })
    const yr  = String(d.getFullYear()).slice(2)
    return `${mon}'${yr}`
  } catch {
    return p
  }
}

const periodItems = computed(() =>
  store.periods.map(p => ({ value: p, label: formatPeriodLabel(p) }))
)
const periodOptions = computed(() =>
  store.periods.map(p => ({ value: p, label: periodShort(p), title: formatPeriodLabel(p) }))
)
const modeOptions = computed(() =>
  MODES.map(m => ({ value: m.value, label: t(`modes.${m.value}`) }))
)

function snapBR(val) {
  const base = Math.floor(val)
  const frac = val - base
  const snapped = [0, 0.3, 0.7].reduce((best, f) =>
    Math.abs(frac - f) < Math.abs(frac - best) ? f : best
  , 0)
  return parseFloat((base + snapped).toFixed(1))
}

const mixWarning = computed(() => {
  const fleet  = store.showLargeFleet || store.showSmallFleet
  const ground = store.showGround || store.showAviation || store.showHelicopters
  const none   = !store.showGround && !store.showAviation && !store.showHelicopters && !store.showLargeFleet && !store.showSmallFleet
  if (none)            return t('sidebar.warn_none')
  if (fleet && ground) return t('sidebar.warn_mix')
  return null
})

const generatedDate = computed(() => {
  const d = store.metaInfo?.generated_at
  if (!d) return '—'
  return new Date(d).toLocaleDateString(undefined, { day: '2-digit', month: '2-digit', year: 'numeric' })
})
</script>

<style scoped>
.sidebar-section { margin-bottom: 20px; padding-bottom: 18px; border-bottom: 1px solid var(--hairline); }
.sidebar-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.sidebar-label   { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }

.period-select :deep(.v-field__input) { min-height: unset; padding-block: 4px; font-size: 12px; }

.chip-grid       { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
.chip-grid--col  { grid-template-columns: 1fr; }
.chip-label      { overflow: hidden; text-overflow: ellipsis; }
.sidebar-info    { font-size: 11px; line-height: 1.7; }

.section-fade-enter-active,
.section-fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease, max-height 0.25s ease; max-height: 300px; overflow: hidden; }
.section-fade-enter-from,
.section-fade-leave-to     { opacity: 0; transform: translateY(-4px); max-height: 0; }
</style>
