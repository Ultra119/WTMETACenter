<template>
  <v-navigation-drawer
    :model-value="open"
    :scrim="false"
    :width="272"
    color="surface"
    style="border-right: 1px solid var(--hairline); top: var(--topbar-h); height: calc(100% - var(--topbar-h));"
  >
    <div class="pa-3">
      <Transition name="hint-fade">
        <div v-if="hiddenCount > 0" class="filters-hint">
          <span class="mdi mdi-filter-off-outline hint-icon" />
          {{ t('sidebar.filters_hidden', { n: hiddenCount }) }}
        </div>
      </Transition>

      <div v-if="cfg.period && store.periods.length > 1" class="sidebar-section">
        <div class="sidebar-label">{{ t('sidebar.period') }}</div>
        <div class="seg-ctrl w-100 period-ctrl">
          <template v-if="store.periods.length <= 5">
            <button
              v-for="p in store.periods"
              :key="p"
              class="seg-btn period-btn"
              :class="{ 'seg-btn--active': store.currentPeriod === p }"
              :title="formatPeriodLabel(p)"
              @click="store.currentPeriod = p"
            >{{ periodShort(p) }}</button>
          </template>

          <template v-else>
            <v-select
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
          </template>
        </div>
      </div>

      <Transition name="section-fade">
        <div v-if="cfg.mode" class="sidebar-section">
          <div class="sidebar-label">{{ t('sidebar.mode') }}</div>
          <div class="seg-ctrl w-100">
            <button
              v-for="m in MODES"
              :key="m.value"
              class="seg-btn"
              :class="{ 'seg-btn--active': store.mode === m.value }"
              @click="store.mode = m.value"
            >{{ t(`modes.${m.value}`) }}</button>
          </div>
        </div>
      </Transition>

      <Transition name="section-fade">
        <div v-if="cfg.brRange" class="sidebar-section">
          <div class="sidebar-label">
            {{ t('sidebar.br_range') }}
            <span class="sidebar-value">{{ store.brRange[0].toFixed(1) }} – {{ store.brRange[1].toFixed(1) }}</span>
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
          <div class="sidebar-label">{{ t('sidebar.min_battles') }}</div>
          <div class="num-input-wrap mt-1">
            <button class="num-btn" @click="store.minBattles = Math.max(0, store.minBattles - 100)">
              <span class="mdi mdi-minus" />
            </button>
            <input
              v-model.number="store.minBattles"
              type="number"
              min="0"
              step="100"
              class="num-input"
            />
            <button class="num-btn" @click="store.minBattles += 100">
              <span class="mdi mdi-plus" />
            </button>
          </div>
        </div>
      </Transition>

      <Transition name="section-fade">
        <div v-if="cfg.classes" class="sidebar-section">
          <div class="sidebar-label">
            {{ t('sidebar.vehicle_class') }}
          </div>
          <div class="chip-grid">
            <button
              v-for="cls in ALL_CLASSES"
              :key="cls"
              class="chip-btn"
              :class="{ 'chip-btn--active': store.classes.includes(cls) }"
              @click="toggleClass(cls)"
            >
              <span
                v-if="CLASS_ICONS[cls]"
                class="mdi chip-icon"
                :class="CLASS_ICONS[cls]"
                :style="store.classes.includes(cls) && CLASS_COLORS[cls] ? `color: ${CLASS_COLORS[cls]}` : ''"
              />
              <span class="chip-label">{{ t(`vehicle_classes.${cls}`) }}</span>
            </button>
          </div>
          <div v-if="!store.classes.length" class="mix-warn mt-2">
            <span class="mdi mdi-alert-outline" style="font-size:12px;margin-right:4px;flex-shrink:0;" />
            {{ t('sidebar.warn_no_classes') }}
          </div>
        </div>
      </Transition>

      <Transition name="section-fade">
        <div v-if="cfg.types" class="sidebar-section">
          <div class="sidebar-label">{{ t('sidebar.vehicle_type') }}</div>
          <div class="type-chip-grid">
            <button
              v-for="tp in TYPE_ENTRIES"
              :key="tp.key"
              class="type-chip"
              :class="{ 'type-chip--active': store[tp.key] }"
              @click="store[tp.key] = !store[tp.key]"
            >
              <span class="mdi type-chip-icon" :class="tp.icon" />
              <span>{{ t(tp.label) }}</span>
            </button>
          </div>
          <div v-if="mixWarning" class="mix-warn mt-2">
            <span class="mdi mdi-alert-outline" style="font-size:12px;margin-right:4px;flex-shrink:0;" />
            {{ mixWarning }}
          </div>
        </div>
      </Transition>

      <div v-if="store.metaInfo" class="sidebar-section">
        <div class="sidebar-label">{{ t('common.dataset') }}</div>
        <div class="sidebar-info">
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
.sidebar-section {
  margin-bottom: 20px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--hairline);
}
.sidebar-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }

.sidebar-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--ink-faint);
}
.sidebar-value { color: var(--primary); letter-spacing: 0.04em; }

/* .seg-ctrl / .seg-btn base styles live in global.css */
.seg-btn     { flex: 1; text-align: center; }
.period-ctrl { flex-wrap: wrap; }
.period-btn  { flex: 0 1 auto; padding: 5px 8px; font-size: 10px; }

.period-select { font-size: 12px; }
.period-select :deep(.v-field__input) {
  min-height: unset;
  padding-top: 4px;
  padding-bottom: 4px;
  font-size: 12px;
  font-weight: 500;
}

.num-input-wrap {
  display: flex;
  align-items: center;
  height: 34px;
  border: 1px solid var(--hairline-strong);
  overflow: hidden;
  transition: border-color 0.15s;
}
.num-input-wrap:focus-within { border-color: var(--primary); }
.num-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 100%;
  background: transparent;
  border: none;
  color: var(--ink-faint);
  font-size: 14px;
  cursor: pointer;
  transition: color 0.15s, background 0.15s;
}
.num-btn:hover { color: var(--primary); background: var(--primary-soft); }
.num-input {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  outline: none;
  text-align: center;
  font-size: 13px;
  color: var(--ink);
  caret-color: var(--primary);
  -moz-appearance: textfield;
}
.num-input::-webkit-outer-spin-button,
.num-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }

.chip-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}
.type-chip-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.chip-btn,
.type-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid var(--hairline);
  border-radius: 0;
  background: transparent;
  color: var(--ink-muted);
  font-family: var(--font-display);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  cursor: pointer;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  transition: color 0.15s, background 0.15s, border-color 0.15s;
}
.chip-btn:hover:not(.chip-btn--active),
.type-chip:hover:not(.type-chip--active) {
  color: var(--ink);
  background: rgba(231, 233, 238, 0.04);
  border-color: var(--hairline-strong);
}
.chip-btn--active,
.type-chip--active {
  background: var(--primary-soft);
  border-color: var(--primary-line);
  color: var(--primary);
}
.chip-icon      { font-size: 13px; flex-shrink: 0; }
.chip-label     { overflow: hidden; text-overflow: ellipsis; }
.type-chip-icon { font-size: 14px; flex-shrink: 0; opacity: 0.85; }
.type-chip--active .type-chip-icon { opacity: 1; }

.mix-warn {
  display: flex;
  align-items: flex-start;
  padding: 6px 8px;
  background: rgba(245, 166, 35, 0.07);
  border: 1px solid rgba(245, 166, 35, 0.3);
  font-size: 11px;
  line-height: 1.5;
  color: var(--amber);
}

.sidebar-info {
  font-family: var(--font-display);
  font-size: 11px;
  line-height: 1.7;
  color: var(--ink-faint);
}

.filters-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 14px;
  padding: 6px 10px;
  border: 1px dashed var(--hairline-strong);
  font-size: 11px;
  color: var(--ink-muted);
}
.hint-icon { font-size: 13px; flex-shrink: 0; }

.section-fade-enter-active,
.section-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease, max-height 0.25s ease;
  max-height: 300px;
  overflow: hidden;
}
.section-fade-enter-from,
.section-fade-leave-to { opacity: 0; transform: translateY(-4px); max-height: 0; }

.hint-fade-enter-active,
.hint-fade-leave-active { transition: opacity 0.2s ease; }
.hint-fade-enter-from,
.hint-fade-leave-to     { opacity: 0; }
</style>
