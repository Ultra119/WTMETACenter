<template>
  <div>
    <div class="controls-bar mb-3">
      <div class="controls-row">
        <SegControl v-model="heatMode" :options="heatModeOptions" />
        <div class="ctrl-divider" />

        <v-select
          v-model="stepsPerBracket"
          :items="stepOptions"
          item-title="title"
          item-value="value"
          :label="t('brackets_tab.br_step')"
          style="width:130px"
        />
        <v-select
          v-if="heatMode === 'strength'"
          v-model="topN"
          :items="topNOptions"
          item-title="label"
          item-value="value"
          :label="t('brackets_tab.top_n')"
          style="width:150px"
        />
        <v-select
          v-model="excludeTypes"
          :items="availableTypeOptions"
          item-title="label"
          item-value="value"
          :label="t('brackets_tab.excl_types')"
          multiple
          style="min-width:180px; max-width:300px"
        >
          <template #item="{ item, props }">
            <v-list-item v-bind="props">
              <template #prepend>
                <v-icon size="16" class="mr-2">{{ (item.raw ?? item).icon }}</v-icon>
              </template>
            </v-list-item>
          </template>

          <template #selection="{ index }">
            <div v-if="index === 0" class="excl-row">
              <span
                v-for="type in excludeTypes.slice(0, 3)"
                :key="type"
                class="tag tint excl-chip"
                @click.stop="removeExcludeType(type)"
              >
                <v-icon size="11">{{ getTypeIcon(type) }}</v-icon>
                {{ getShortLabel(type) }}
                <span class="excl-x">×</span>
              </span>
              <span v-if="excludeTypes.length > 3" class="tag excl-more">
                +{{ excludeTypes.length - 3 }}
              </span>
            </div>
          </template>
        </v-select>

        <div class="heat-legend ml-auto" :title="legendTitle">
          <span class="eyebrow eyebrow--xs">{{ legendLow }}</span>
          <span class="heat-bar" :style="{ background: legendGradient }" />
          <span class="eyebrow eyebrow--xs">{{ legendHigh }}</span>
        </div>

        <InfoTip align="right">
          <p><b>{{ t(heatMode === 'popularity' ? 'brackets_tab.description_popularity' : 'brackets_tab.description_strength') }}</b></p>
          <p>{{ t(heatMode === 'popularity' ? 'brackets_tab.tip_desc_popularity' : 'brackets_tab.tip_desc_strength') }}</p>
          <p style="margin-top:8px">
            <span class="heat-bar heat-bar--tip" :style="{ background: legendGradient }" />
            &nbsp;
            <template v-if="heatMode === 'popularity'">
              <span style="color:var(--ink-faint)">{{ t('brackets_tab.tip_rare') }}</span> →
              <span style="color:var(--c-info)">{{ t('brackets_tab.tip_avg_pop') }}</span> →
              <span style="color:var(--c-warn)">{{ t('brackets_tab.tip_dominant') }}</span>
            </template>
            <template v-else>
              <span style="color:var(--c-bad)">{{ t('brackets_tab.tip_weak') }}</span> →
              <span style="color:var(--c-warn)">{{ t('brackets_tab.tip_average') }}</span> →
              <span style="color:var(--c-ok)">{{ t('brackets_tab.tip_strong') }}</span>
            </template>
          </p>
        </InfoTip>
      </div>
    </div>

    <div v-if="pivot.rows.length" class="table-wrap pivot-wrap">
      <table class="pivot-table">
        <thead>
          <tr>
            <th class="br-col">{{ t('common.br') }}</th>
            <th v-for="nat in pivot.nations" :key="nat">{{ fmtNation(nat) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in pivot.rows" :key="row.bracket">
            <td class="br-cell">{{ row.bracket }}</td>
            <td
              v-for="nat in pivot.nations"
              :key="nat"
              class="score-cell"
              :class="{ 'is-empty': !row[nat] }"
              :style="{ '--c': scoreColor(row[nat], pivot.mode) }"
            >{{ formatCell(row[nat]) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="panel no-data">
      {{ t('brackets_tab.no_data') }}
    </div>
  </div>
</template>

<script setup>
import { ref, shallowRef, computed, watch, watchEffect, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTabFilters } from '../composables/useTabFilters.js'
import { useDataStore, WT_BR_STEPS } from '../stores/useDataStore.js'
import { metaColor, fmtNation } from '../composables/useVehicleFormatting.js'
import { BRANCH_TYPES, TYPE_LABELS, TYPE_ICON, LARGE_FLEET_TYPES, SMALL_FLEET_TYPES } from '../composables/constants.js'
import InfoTip from '../components/InfoTip.vue'
import SegControl from '../components/ui/SegControl.vue'

const { t }  = useI18n()
const store = useDataStore()
useTabFilters()

const stepsPerBracket = ref(3)
const topN            = ref(5)
const excludeTypes    = ref([])
const heatMode        = ref('strength')

const heatModeOptions = computed(() => [
  { value: 'strength',   icon: 'mdi-trophy-outline', label: t('brackets_tab.mode_strength')   },
  { value: 'popularity', icon: 'mdi-fire',           label: t('brackets_tab.mode_popularity') },
])

const stepOptions = computed(() =>
  [1, 2, 3, 4, 6].map(n => ({
    value: n,
    title: `${(WT_BR_STEPS[n] - WT_BR_STEPS[0]).toFixed(1)} BR`,
  }))
)

const topNOptions = computed(() => [
  { label: t('common.top_all'), value: 0 },
  { label: 'Top-3',  value: 3 },
  { label: 'Top-5',  value: 5 },
  { label: 'Top-7',  value: 7 },
  { label: 'Top-10', value: 10 },
])

const availableTypeOptions = computed(() => {
  const active = []
  if (store.showGround) {
    active.push(...BRANCH_TYPES.Ground)
  }
  if (store.showAviation) {
    active.push(...BRANCH_TYPES.Aviation)
  }
  if (store.showHelicopters) {
    active.push(...BRANCH_TYPES.Helicopters)
  }
  if (store.showLargeFleet) {
    active.push(...[...LARGE_FLEET_TYPES])
  }
  if (store.showSmallFleet) {
    active.push(...[...SMALL_FLEET_TYPES])
  }
  return active.map(type => ({
    value:      type,
    icon:       TYPE_ICON[type] ?? 'mdi-help',
    label:      t(`vehicle_types.${type}`, TYPE_LABELS[type] ?? type),
    shortLabel: TYPE_LABELS[type] ?? type,
  }))
})

watch(availableTypeOptions, (opts) => {
  const available = new Set(opts.map(o => o.value))
  excludeTypes.value = excludeTypes.value.filter(type => available.has(type))
})

const typeOptionMap = computed(() => new Map(availableTypeOptions.value.map(o => [o.value, o])))
const getShortLabel = type => typeOptionMap.value.get(type)?.shortLabel ?? type
const getTypeIcon   = type => typeOptionMap.value.get(type)?.icon ?? 'mdi-help'
const removeExcludeType = type => {
  excludeTypes.value = excludeTypes.value.filter(x => x !== type)
}

function buildWtBrackets(stepsN) {
  const step = Math.max(1, stepsN)
  const n    = WT_BR_STEPS.length
  const boundaryIndices = []
  for (let i = 0; i < n; i += step) boundaryIndices.push(i)
  if (boundaryIndices[boundaryIndices.length - 1] !== n - 1) boundaryIndices.push(n - 1)

  return boundaryIndices.slice(0, -1).map((startIdx, i) => {
    const endIdx = boundaryIndices[i + 1]
    const minBr  = WT_BR_STEPS[startIdx]
    const maxBr  = WT_BR_STEPS[endIdx]
    const isLast = i === boundaryIndices.length - 2
    const lastIncludedBr = isLast ? maxBr : WT_BR_STEPS[endIdx - 1]

    return {
      label: step === 1
        ? minBr.toFixed(1)
        : `${minBr.toFixed(1)}–${lastIncludedBr.toFixed(1)}`,
      min:       minBr,
      max:       maxBr,
      inclusive: isLast,
    }
  })
}

const battlesOf = v => v['Сыграно игр'] ?? 0

function weightedMeta(pool) {
  if (!pool.length) return 0
  let total = 0, weighted = 0, plain = 0
  for (const v of pool) {
    const b = battlesOf(v)
    total    += b
    weighted += v.META_SCORE * b
    plain    += v.META_SCORE
  }
  return total < 1 ? plain / pool.length : weighted / total
}

const pivot = shallowRef({ rows: [], nations: [], mode: 'strength' })
watchEffect(() => {
  const excluded      = new Set(excludeTypes.value)
  const allFiltered   = store.filteredVehicles
  const steps         = stepsPerBracket.value
  const n             = topN.value || null
  const mode          = heatMode.value

  nextTick(() => {
    const vehicles = excluded.size
      ? allFiltered.filter(v => !excluded.has(v.Type))
      : allFiltered
    if (!vehicles.length) { pivot.value = { rows: [], nations: [], mode }; return }

    const brackets = buildWtBrackets(steps)
    const nations  = [...new Set(vehicles.map(v => v.Nation))].sort()

    const buckets = brackets.map(() => new Map())
    for (const v of vehicles) {
      const bi = brackets.findIndex(b => v.BR >= b.min && (b.inclusive ? v.BR <= b.max : v.BR < b.max))
      if (bi === -1) continue
      const m = buckets[bi]
      const list = m.get(v.Nation)
      if (list) list.push(v); else m.set(v.Nation, [v])
    }

    const rows = brackets.map((b, bi) => {
      const byNation = buckets[bi]
      const row = { bracket: b.label }

      if (mode === 'popularity') {
        let total = 0
        const sums = new Map()
        for (const [nat, list] of byNation) {
          const s = list.reduce((acc, v) => acc + battlesOf(v), 0)
          sums.set(nat, s)
          total += s
        }
        for (const nat of nations) {
          row[nat] = total > 0 ? Math.round(((sums.get(nat) ?? 0) / total) * 1000) / 10 : 0
        }
        return row
      }

      for (const nat of nations) {
        let pool = byNation.get(nat) ?? []
        if (n && pool.length > n) pool = [...pool].sort((a, c) => c.META_SCORE - a.META_SCORE).slice(0, n)
        row[nat] = Math.round(weightedMeta(pool) * 10) / 10
      }
      return row
    })

    pivot.value = { rows: rows.filter(r => nations.some(nat => r[nat] > 0)), nations, mode }
  })
})

const POP_STOPS = [
  { t: 0,    c: [120, 128, 145] },
  { t: 0.45, c: [127, 178, 229] },
  { t: 1,    c: [245, 166, 35]  },
]

const popHotThreshold = computed(() => {
  const nCount = pivot.value.nations.length || 1
  return Math.min(80, Math.max(20, 300 / nCount))
})

function popularityColor(pct) {
  const x = Math.min(1, Math.max(0, pct / popHotThreshold.value))
  for (let i = 0; i < POP_STOPS.length - 1; i++) {
    const a = POP_STOPS[i], b = POP_STOPS[i + 1]
    if (x >= a.t && x <= b.t) {
      const k = (x - a.t) / (b.t - a.t || 1)
      const mix = j => Math.round(a.c[j] + (b.c[j] - a.c[j]) * k)
      return `rgb(${mix(0)},${mix(1)},${mix(2)})`
    }
  }
  const [r, g, b] = POP_STOPS[POP_STOPS.length - 1].c
  return `rgb(${r},${g},${b})`
}

function scoreColor(score, mode) {
  if (!score) return 'var(--ink-dim)'
  return mode === 'popularity' ? popularityColor(score) : metaColor(score)
}

const legendGradient = computed(() => heatMode.value === 'popularity'
  ? 'linear-gradient(to right, rgb(120,128,145) 0%, var(--c-info) 45%, var(--c-warn) 100%)'
  : 'linear-gradient(to right, var(--c-bad) 0%, var(--c-warn) 50%, var(--c-ok) 100%)'
)
const legendLow  = computed(() => t(heatMode.value === 'popularity' ? 'brackets_tab.tip_rare'     : 'brackets_tab.tip_weak'))
const legendHigh = computed(() => t(heatMode.value === 'popularity' ? 'brackets_tab.tip_dominant' : 'brackets_tab.tip_strong'))
const legendTitle = computed(() => `${legendLow.value} → ${legendHigh.value}`)

function formatCell(val) {
  if (!val) return '—'
  return pivot.value.mode === 'popularity' ? `${val.toFixed(1)}%` : val.toFixed(1)
}
</script>

<style scoped>
.excl-row   { display: flex; align-items: center; gap: 4px; max-width: 100%; overflow: hidden; }
.excl-chip  { padding: 1px 6px; font-size: 10px; cursor: pointer; transition: color 0.12s, border-color 0.12s, background 0.12s; }
.excl-chip:hover {
  --c: var(--c-bad);
}
.excl-x     { font-size: 11px; opacity: 0.6; }
.excl-more  { flex-shrink: 0; padding: 1px 6px; font-size: 10px; color: var(--ink-faint); }

.heat-legend { display: inline-flex; align-items: center; gap: 8px; }
.heat-bar    { display: inline-block; width: 120px; height: 6px; }
.heat-bar--tip { width: 140px; height: 8px; vertical-align: middle; }
@media (max-width: 960px) { .heat-legend { display: none; } }

.pivot-wrap {
  max-height: calc(100vh - 254px);
  overflow: auto;
}
.pivot-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: var(--surface);
  font: 12px var(--font-display);
  font-variant-numeric: tabular-nums;
}
.pivot-table th,
.pivot-table td {
  padding: 6px 12px;
  text-align: center;
  white-space: nowrap;
  border-bottom: 1px solid var(--hairline);
}
.pivot-table thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--surface);
  color: var(--ink-faint);
  font: 500 11px var(--font-display);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.pivot-table tbody tr:last-child td { border-bottom: none; }

.br-col,
.br-cell {
  position: sticky;
  left: 0;
  min-width: 100px;
  padding-left: 14px !important;
  text-align: left !important;
  background: var(--surface);
  border-right: 1px solid var(--hairline);
}
.br-col  { z-index: 3; }
.br-cell { z-index: 1; color: var(--ink-muted); font-weight: 600; }

.score-cell {
  color: var(--c);
  font-weight: 600;
  background: color-mix(in srgb, var(--c) 9%, transparent);
  transition: background 0.12s;
}
.score-cell.is-empty { font-weight: 400; background: transparent; }
.pivot-table tbody tr:hover .score-cell:not(.is-empty) { background: color-mix(in srgb, var(--c) 20%, transparent); }
.pivot-table tbody tr:hover .br-cell { color: var(--primary); background: var(--surface-2); }
</style>
