<template>
  <div>
    <div class="controls-bar mb-4">
      <div class="controls-row">

        <div class="seg-ctrl">
          <button
            v-for="m in METRICS"
            :key="m.key"
            :class="['seg-btn', metric === m.key && 'seg-btn--active']"
            @click="metric = m.key"
          >
            <span class="mdi seg-btn-icon" :class="m.icon" />
            {{ t(`cost_tab.metric_${m.key}`) }}
          </button>
        </div>

        <label class="folder-toggle">
          <input type="checkbox" v-model="skipFolderDupes" class="folder-toggle__input" />
          <span class="folder-toggle__box">
            <span class="mdi mdi-folder-multiple-outline folder-toggle__icon" />
          </span>
          <span class="folder-toggle__label">{{ t('cost_tab.skip_folder') }}</span>
        </label>

        <div class="era-legend ml-auto">
          <span v-for="e in 8" :key="e" class="era-pip">
            <span class="era-dot" :style="{ background: ERA_COLORS[e] }" />
            {{ ROMAN[e] }}
          </span>
        </div>

        <InfoTip align="right">
          <p><b>{{ t('cost_tab.tip_title') }}</b></p>
          <p>{{ t('cost_tab.tip_desc') }}</p>
          <div class="tip-row mt-2">
            <span class="mdi mdi-chart-bar tip-icon" />
            <span>{{ t('cost_tab.tip_bars') }}</span>
          </div>
          <div class="tip-row">
            <span class="mdi mdi-palette tip-icon" />
            <span>{{ t('cost_tab.tip_eras') }}</span>
          </div>
          <div v-if="isRpBasedMetric" class="tip-row mt-2" style="border-top: 1px solid #1e3a5f; padding-top: 8px;">
            <span class="mdi mdi-flask-outline tip-icon" style="color: #6ee7b7;" />
            <span>{{ t('cost_tab.tip_standard_only') }}</span>
          </div>
          <div v-if="metric === 'meta_eff'" class="tip-row mt-2" style="border-top: 1px solid #1e3a5f; padding-top: 8px;">
            <span class="mdi mdi-medal-outline tip-icon" style="color: #a78bfa;" />
            <span><b style="color: #a78bfa;">RP/META</b> — {{ t('cost_tab.tip_meta_eff_info') }}</span>
          </div>
        </InfoTip>

      </div>
    </div>

    <div class="branches-grid" :style="{ '--count-col-w': metric === 'meta_eff' ? '64px' : '36px' }">
      <div
        v-for="branch in BRANCHES"
        :key="branch.key"
        class="branch-card"
        :style="{ '--accent': branch.accent }"
      >

        <div class="branch-card__hdr">
          <span class="mdi branch-card__icon" :class="branch.icon" />
          <span class="branch-card__title">
            {{ t(`cost_tab.branch_${branch.key.toLowerCase()}`) }}
          </span>
          <span class="branch-card__count">
            {{ t('cost_tab.n_vehicles', { n: fmtFull(branchVehicleCount(branch.key)) }) }}
          </span>
          <template v-if="chartRows(branch.key).length >= 2">
            <div class="branch-card__summary ml-auto">
              <span class="card-stat card-stat--cheap">
                <span class="card-stat__dot" />
                {{ nationFlag(chartRows(branch.key).at(-1)?.nation) }}
                <b>{{ fmtNationName(chartRows(branch.key).at(-1)?.nation) }}</b>
                <span class="card-stat__val">{{ fmtRowVal(chartRows(branch.key).at(-1)) }}</span>
              </span>
              <span class="card-stat card-stat--exp">
                <span class="card-stat__dot" />
                {{ nationFlag(chartRows(branch.key)[0]?.nation) }}
                <b>{{ fmtNationName(chartRows(branch.key)[0]?.nation) }}</b>
                <span class="card-stat__val">{{ fmtRowVal(chartRows(branch.key)[0]) }}</span>
              </span>
            </div>
          </template>
        </div>

        <div class="branch-card__rows">
          <div
            v-for="row in chartRows(branch.key)"
            :key="row.nation"
            class="bar-row"
          >
            <div class="nation-col">
              <span class="nation-flag">{{ nationFlag(row.nation) }}</span>
              <span class="nation-name">{{ fmtNationName(row.nation) }}</span>
            </div>

            <div class="bar-col">
              <div class="bar-track">
                <template v-for="e in 8" :key="e">
                  <v-tooltip v-if="row.byEra[e]" location="top">
                    <template #activator="{ props }">
                      <div
                        v-bind="props"
                        class="bar-seg"
                        :style="{
                          width: segPctLocal(row.byEra[e], row, branch.key) + '%',
                          background: ERA_COLORS[e],
                        }"
                      >
                        <span class="bar-seg-label">{{ ROMAN[e] }}</span>
                      </div>
                    </template>
                    <span class="tooltip-content">
                      <b>{{ t('cost_tab.era') }} {{ e }}</b><br/>
                      <template v-if="metric === 'meta_eff'">
                        {{ t('cost_tab.tooltip_avg_rp_per_veh', { val: fmtFull(Math.round(row.byEra[e] / row.countByEra[e])) }) }}<br/>
                        {{ t('cost_tab.tooltip_avg_meta', { val: row.sumMetaByEra?.[e] && row.countByEra[e]
                          ? (row.sumMetaByEra[e] / row.countByEra[e]).toFixed(1)
                          : '—' }) }}<br/>
                      </template>
                      <template v-else>
                        {{ fmtFull(row.byEra[e]) }} {{ metricUnit }}<br/>
                      </template>
                      {{ fmtFull(row.countByEra[e]) }} {{ t('cost_tab.vehicles') }}
                    </span>
                  </v-tooltip>
                </template>
              </div>
            </div>

            <div class="count-col">
              <span
                class="count-chip"
                :class="{ 'count-chip--meta': metric === 'meta_eff' }"
                :title="metric === 'meta_eff'
                  ? `${t('cost_tab.count_veh_hint')} / ${t('cost_tab.count_meta_hint')}`
                  : t('cost_tab.count_veh_hint')"
              >
                <template v-if="metric === 'meta_eff'">{{ fmtFull(row.count) }} <span class="count-chip__sep">·</span>Ø{{ row.avgMeta }}</template>
                <template v-else>{{ fmtFull(row.count) }}</template>
              </span>
            </div>

            <div class="total-col">
              <span class="total-label" :style="{ color: totalColorLocal(row, branch.key) }">
                {{ fmtRowVal(row) }}
              </span>
            </div>
          </div>

          <div v-if="!chartRows(branch.key).length" class="no-data">
            {{ t('common.no_data') }}
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, shallowRef, computed, watchEffect, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTabFilters } from '../composables/useTabFilters.js'
import { useDataStore } from '../stores/useDataStore.js'
import InfoTip from '../components/InfoTip.vue'

const { t }   = useI18n()
const store = useDataStore()
useTabFilters({ period: false, mode: false, brRange: false, minBattles: false, classes: true, types: false })

const ERA_COLORS = {
  1: '#6ee7b7', 2: '#4ade80', 3: '#a3e635', 4: '#facc15',
  5: '#fb923c', 6: '#f87171', 7: '#c084fc', 8: '#818cf8',
}

const ROMAN = { 1:'I', 2:'II', 3:'III', 4:'IV', 5:'V', 6:'VI', 7:'VII', 8:'VIII' }

const NATION_FLAG = {
  usa:'🇺🇸', germany:'🇩🇪', ussr:'🇷🇺', britain:'🇬🇧', japan:'🇯🇵',
  italy:'🇮🇹', france:'🇫🇷', sweden:'🇸🇪', israel:'🇮🇱', china:'🇨🇳',
}

const NATION_DISPLAY = {
  usa:'USA', germany:'Germany', ussr:'USSR', britain:'Britain', japan:'Japan',
  italy:'Italy', france:'France', sweden:'Sweden', israel:'Israel', china:'China',
}

function fmtNationName(n) {
  if (!n) return '—'
  const key = n.toLowerCase()
  return NATION_DISPLAY[key] ?? (n.charAt(0).toUpperCase() + n.slice(1))
}

function nationFlag(n) {
  return NATION_FLAG[n?.toLowerCase()] ?? '🏳️'
}

const BRANCHES = [
  { key: 'Ground',      icon: 'mdi-tank',       accent: '#a7f3d0', types: ['medium_tank','light_tank','heavy_tank','tank_destroyer','spaa'] },
  { key: 'Aviation',    icon: 'mdi-airplane',    accent: '#38bdf8', types: ['fighter','bomber','assault'] },
  { key: 'Helicopters', icon: 'mdi-helicopter',  accent: '#a78bfa', types: ['attack_helicopter','utility_helicopter'] },
  { key: 'Fleet',       icon: 'mdi-anchor',      accent: '#60a5fa', types: ['destroyer','heavy_cruiser','light_cruiser','battleship','battlecruiser','boat','heavy_boat','frigate','barge'] },
]
const BRANCH_TYPE_SET = Object.fromEntries(
  BRANCHES.map(b => [b.key, new Set(b.types)])
)

const METRICS = [
  { key: 'rp',       icon: 'mdi-flask'         },
  { key: 'sl',       icon: 'mdi-cash'          },
  { key: 'meta_eff', icon: 'mdi-medal-outline' },
]

const metric          = ref('rp')
const skipFolderDupes = ref(true)
const isRpBasedMetric = computed(() => metric.value === 'rp' || metric.value === 'meta_eff')

const metricUnit = computed(() => metric.value === 'sl' ? 'SL' : 'RP')

const uniqueVehicles = shallowRef([])
watchEffect(() => {
  // Intentionally raw/unfiltered: this tab ignores the sidebar's mode/BR/min-battles
  // filters (see useTabFilters below) and applies its own era+type+class criteria
  // further down. NOTE: previously this read `store.allVehicles ?? store.filteredVehicles ?? []`,
  // but store.allVehicles is always an array (never null/undefined) so that fallback
  // was dead code and never actually ran — removed for clarity, behavior unchanged.
  const source = store.allVehicles
  nextTick(() => {
    const seen = new Set()
    const out  = []
    for (const v of source) {
      const key = v.vdb_identifier || `${v.Nation}__${v.Name}`
      if (!key || seen.has(key)) continue
      seen.add(key)
      out.push(v)
    }
    uniqueVehicles.value = out
  })
})

const metaScoreMap = computed(() => {
  const map  = new Map()
  const mode = store.mode
  for (const v of store.allVehicles) {
    if (v.Mode !== mode || !v.META_SCORE) continue
    map.set(`${v.Nation}__${v.Name}`, v.META_SCORE)
  }
  return map
})

const chartData = shallowRef({})
watchEffect(() => {
  const vehicles = uniqueVehicles.value
  const met      = metric.value
  const cls      = [...store.classes]
  const skipDup  = skipFolderDupes.value
  const metaMap  = metaScoreMap.value

  const isRpBased = met === 'rp' || met === 'meta_eff'
  const isMetaEff = met === 'meta_eff'

  nextTick(() => {
    let src = vehicles
    if (skipDup) {
      const groupMin = new Map()
      for (const v of vehicles) {
        const g = v.vdb_shop_group
        if (!g) continue
        // Eligibility here must mirror the main loop below exactly — otherwise
        // the "cheapest in folder" pick can be a vehicle that the main loop
        // would itself discard (wrong class / zero value), silently dropping
        // the whole group instead of falling back to the next eligible one.
        if (!cls.includes(v.VehicleClass ?? 'Standard')) continue
        if (isRpBased && (v.VehicleClass ?? 'Standard') !== 'Standard') continue
        const era = Number(v.vdb_era ?? 0)
        if (era < 1 || era > 8) continue
        let bKey = null
        for (const b of BRANCHES) {
          if (BRANCH_TYPE_SET[b.key].has(v.Type)) { bKey = b.key; break }
        }
        if (!bKey) continue
        const val = isRpBased ? Number(v.vdb_req_exp ?? 0) : Number(v.vdb_value ?? 0)
        if (!val) continue
        const key = `${v.Nation}__${bKey}__${g}`
        const cur = groupMin.get(key)
        if (!cur || val < cur.val) groupMin.set(key, { v, val })
      }
      const keep = new Set([...groupMin.values()].map(({ v }) => v))
      src = vehicles.filter(v => !v.vdb_shop_group || keep.has(v))
    }

    const byBranch = {}
    for (const b of BRANCHES) byBranch[b.key] = {}

    for (const v of src) {
      if (!cls.includes(v.VehicleClass ?? 'Standard')) continue
      if (isRpBased && v.VehicleClass !== 'Standard') continue

      const era = Number(v.vdb_era ?? 0)
      if (era < 1 || era > 8) continue

      const val = isRpBased ? Number(v.vdb_req_exp ?? 0) : Number(v.vdb_value ?? 0)
      if (!val) continue

      const vType = v.Type
      let bKey = null
      for (const b of BRANCHES) {
        if (BRANCH_TYPE_SET[b.key].has(vType)) { bKey = b.key; break }
      }
      if (!bKey) continue

      const nat = v.Nation
      if (!nat) continue

      if (!byBranch[bKey][nat]) {
        byBranch[bKey][nat] = { nation: nat, total: 0, byEra: {}, countByEra: {} }
      }
      const entry = byBranch[bKey][nat]
      entry.total          += val
      entry.byEra[era]      = (entry.byEra[era]     ?? 0) + val
      entry.countByEra[era] = (entry.countByEra[era] ?? 0) + 1

      if (isMetaEff) {
        const ms = metaMap.get(`${nat}__${v.Name}`) ?? 50
        entry.sumMeta              = (entry.sumMeta              ?? 0) + ms
        entry.sumMetaByEra         = entry.sumMetaByEra ?? {}
        entry.sumMetaByEra[era]    = (entry.sumMetaByEra[era]    ?? 0) + ms
      }
    }

    for (const bKey of Object.keys(byBranch)) {
      for (const row of Object.values(byBranch[bKey])) {
        row.count      = Object.values(row.countByEra).reduce((s, n) => s + n, 0)
        const sumW     = row.sumMeta ?? 0
        row.metaAdjVal = (isMetaEff && sumW > 0) ? Math.round(row.total / (sumW / 100)) : 0
        row.avgMeta    = row.count > 0 ? Math.round(sumW / row.count) : 0
      }
    }

    const result = {}
    for (const b of BRANCHES) {
      const rows = Object.values(byBranch[b.key]).sort((a, z) =>
        met === 'meta_eff' ? z.metaAdjVal - a.metaAdjVal : z.total - a.total
      )
      const vehicleCount = rows.reduce((sum, row) => sum + row.count, 0)
      result[b.key] = { rows, vehicleCount }
    }
    chartData.value = result
  })
})

function chartRows(branchKey) {
  return chartData.value[branchKey]?.rows ?? []
}

function branchVehicleCount(branchKey) {
  return chartData.value[branchKey]?.vehicleCount ?? 0
}

const branchMaxes = computed(() => {
  const out = {}
  for (const b of BRANCHES) {
    const rows = chartRows(b.key)
    if (!rows.length) { out[b.key] = 1; continue }
    out[b.key] = metric.value === 'meta_eff'
      ? Math.max(...rows.map(r => r.metaAdjVal ?? 0))
      : Math.max(...rows.map(r => r.total))
  }
  return out
})

function segPctLocal(eraVal, row, branchKey) {
  const max    = branchMaxes.value[branchKey] ?? 1
  const refVal = metric.value === 'meta_eff' ? row.metaAdjVal : row.total
  return Math.min((eraVal / (row.total || 1)) * (refVal / max) * 100, 100)
}

function totalColorLocal(row, branchKey) {
  const val = metric.value === 'meta_eff' ? (row.metaAdjVal ?? 0) : (row.total ?? 0)
  const p   = val / (branchMaxes.value[branchKey] ?? 1)
  if (p > 0.85) return '#f87171'
  if (p > 0.60) return '#fb923c'
  if (p < 0.25) return '#4ade80'
  return '#e2e8f0'
}

function fmtRowVal(row) {
  if (!row) return '—'
  return metric.value === 'meta_eff' ? fmtM(row.metaAdjVal) + '/META' : fmtM(row.total)
}

function fmtM(n) {
  if (!n) return '0'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return (n / 1_000).toFixed(0) + 'K'
  return String(n)
}

function fmtFull(n) {
  if (!n) return '0'
  return n.toLocaleString()
}
</script>

<style scoped>
.era-legend {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}
.era-pip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #64748b;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: .03em;
}
.era-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.branches-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.branch-card {
  background: rgba(12, 20, 38, 0.65);
  border: 1px solid #1e3a5f;
  border-left: 3px solid var(--accent, #a7f3d0);
  border-radius: 10px;
  overflow: hidden;
}

.branch-card__hdr {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 14px;
  background: rgba(7, 14, 28, 0.6);
  border-bottom: 1px solid #1e3a5f;
  flex-wrap: wrap;
}
.branch-card__icon {
  font-size: 18px;
  color: var(--accent, #a7f3d0);
  flex-shrink: 0;
}
.branch-card__title {
  font-size: 13px;
  font-weight: 700;
  color: var(--accent, #a7f3d0);
  text-transform: uppercase;
  letter-spacing: .1em;
}
.branch-card__count {
  font-size: 10px;
  color: #e2e8f0;
  background: rgba(30, 58, 95, 0.5);
  border: 1px solid rgba(30, 58, 95, 0.9);
  border-radius: 4px;
  padding: 1px 7px;
  font-family: 'JetBrains Mono', monospace;
}
.branch-card__summary {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.card-stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #64748b;
}
.card-stat__dot {
  width: 5px;
  height: 5px;
  border-radius: 1px;
  flex-shrink: 0;
}
.card-stat--cheap .card-stat__dot { background: #4ade80; }
.card-stat--exp   .card-stat__dot { background: #f87171; }
.card-stat--cheap b { color: #4ade80; }
.card-stat--exp   b { color: #f87171; }
.card-stat__val {
  color: #475569;
  font-family: 'JetBrains Mono', monospace;
}

.branch-card__rows { padding: 3px 0; }

.bar-row {
  display: grid;
  grid-template-columns: 110px 1fr var(--count-col-w, 36px) 80px;
  gap: 8px;
  align-items: center;
  padding: 5px 14px;
  border-top: 1px solid rgba(30, 58, 95, 0.35);
  transition: opacity .12s;
  cursor: default;
}
.bar-row:first-child { border-top: none; }

.branch-card__rows:has(.bar-row:hover) .bar-row:not(:hover) {
  opacity: 0.18;
}

.nation-col {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
.nation-flag { font-size: 14px; line-height: 1; flex-shrink: 0; }
.nation-name {
  font-size: 11px;
  font-weight: 700;
  color: #cbd5e1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: .04em;
}

.bar-col { min-width: 0; }

.bar-track {
  display: flex;
  height: 24px;
  border-radius: 3px;
  overflow: hidden;
  background: rgba(30, 58, 95, 0.3);
  width: 100%;
}
.bar-seg {
  height: 100%;
  min-width: 2px;
  margin-right: 1px;
  flex-shrink: 0;
  transition: filter .12s;
  container-type: inline-size;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.bar-seg-label {
  display: none;
  font-size: 10px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  color: rgba(15, 23, 42, 0.72);
  letter-spacing: -0.02em;
  white-space: nowrap;
  pointer-events: none;
  user-select: none;
}
@container (min-width: 24px) {
  .bar-seg-label { display: block; }
}
.bar-seg:last-child { margin-right: 0; }
.bar-seg:hover { filter: brightness(1.3); }

.total-col { text-align: right; }
.total-label {
  font-size: 12px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

.count-col { text-align: right; }
.count-chip {
  display: inline-block;
  font-size: 10px;
  font-family: 'JetBrains Mono', monospace;
  color: #e2e8f0;
  background: rgba(30, 58, 95, 0.4);
  border: 1px solid rgba(30, 58, 95, 0.75);
  border-radius: 4px;
  padding: 1px 5px;
  white-space: nowrap;
  line-height: 1.6;
}
.count-chip--meta {
  color: #a78bfa;
  background: rgba(167, 139, 250, 0.08);
  border-color: rgba(167, 139, 250, 0.3);
}
.count-chip__sep {
  color: #475569;
  margin: 0 2px;
}

.tooltip-content { font-size: 12px; line-height: 1.6; }
</style>
