<template>
  <div>
    <div class="controls-bar mb-4">
      <div class="controls-row">

        <SegControl v-model="metric" :options="metricOptions" />

        <label class="folder-toggle">
          <input type="checkbox" v-model="skipFolderDupes" class="folder-toggle__input" />
          <span class="folder-toggle__box">
            <v-icon class="folder-toggle__icon">mdi-folder-multiple-outline</v-icon>
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
          <template v-if="metric !== 'meta_eff'">
            <p>{{ t('cost_tab.tip_desc') }}</p>
            <div class="tip-row mt-2">
              <v-icon class="tip-icon">mdi-chart-bar</v-icon>
              <span>{{ t('cost_tab.tip_bars') }}</span>
            </div>
            <div class="tip-row">
              <v-icon class="tip-icon">mdi-palette</v-icon>
              <span>{{ t('cost_tab.tip_eras') }}</span>
            </div>
          </template>
          <div v-if="isRpBasedMetric" class="tip-row hairline-t mt-2" style="padding-top:8px">
            <v-icon class="tip-icon" style="color:var(--primary)">mdi-flask-outline</v-icon>
            <span>{{ t('cost_tab.tip_standard_only') }}</span>
          </div>
          <div v-if="metric === 'meta_eff'" class="tip-row hairline-t mt-2" style="padding-top:8px">
            <v-icon class="tip-icon" style="color:var(--c-violet)">mdi-medal-outline</v-icon>
            <span><b style="color:var(--c-violet)">RP/META</b> — {{ t('cost_tab.tip_meta_eff_info') }}</span>
          </div>
        </InfoTip>

      </div>
    </div>

    <div class="branches-grid" :style="{ '--count-col-w': metric === 'meta_eff' ? '72px' : '40px' }">
      <section
        v-for="bv in branchViews"
        :key="bv.branch.key"
        class="panel branch-card"
        :style="{ '--accent': bv.branch.accent }"
      >

        <header class="branch-card__hdr">
          <v-icon class="branch-card__icon" size="18">{{ bv.branch.icon }}</v-icon>
          <span class="eyebrow branch-card__title">
            {{ t(`cost_tab.branch_${bv.branch.key.toLowerCase()}`) }}
          </span>
          <span class="tag">{{ t('cost_tab.n_vehicles', { n: fmtFull(bv.count) }) }}</span>

          <div v-if="bv.cheap && bv.exp" class="branch-card__summary ml-auto">
            <span class="card-stat" style="--c: var(--c-ok)">
              <span class="card-stat__dot" />
              {{ nationFlag(bv.cheap.nation) }}
              <b>{{ fmtNationName(bv.cheap.nation) }}</b>
              <span class="card-stat__val">{{ fmtRowVal(bv.cheap) }}</span>
            </span>
            <span class="card-stat" style="--c: var(--c-bad)">
              <span class="card-stat__dot" />
              {{ nationFlag(bv.exp.nation) }}
              <b>{{ fmtNationName(bv.exp.nation) }}</b>
              <span class="card-stat__val">{{ fmtRowVal(bv.exp) }}</span>
            </span>
          </div>
        </header>

        <div class="branch-card__rows">
          <div
            v-for="row in bv.rows"
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
                          width: segPctLocal(row.byEra[e], row, bv.branch.key) + '%',
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
                class="tag count-chip"
                :class="{ 'tint tint--violet': metric === 'meta_eff' }"
                :title="metric === 'meta_eff'
                  ? `${t('cost_tab.count_veh_hint')} / ${t('cost_tab.count_meta_hint')}`
                  : t('cost_tab.count_veh_hint')"
              >
                <template v-if="metric === 'meta_eff'">{{ fmtFull(row.count) }}<span class="count-chip__sep">·</span>Ø{{ row.avgMeta }}</template>
                <template v-else>{{ fmtFull(row.count) }}</template>
              </span>
            </div>

            <div class="total-col">
              <span class="total-label" :style="{ color: totalColorLocal(row, bv.branch.key) }">
                {{ fmtRowVal(row) }}
              </span>
            </div>
          </div>

          <div v-if="!bv.rows.length" class="no-data">
            {{ t('common.no_data') }}
          </div>
        </div>

      </section>
    </div>

  </div>
</template>

<script setup>
import { ref, shallowRef, computed, watchEffect, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTabFilters } from '../composables/useTabFilters.js'
import { useDataStore } from '../stores/useDataStore.js'
import InfoTip from '../components/InfoTip.vue'
import SegControl from '../components/ui/SegControl.vue'
import { BR_ERA_THRESHOLDS } from '../composables/constants.js'

const { t }   = useI18n()
const store = useDataStore()
useTabFilters({ period: false, mode: false, brRange: false, minBattles: false, classes: true, types: false })

const ERA_COLORS = {
  1: '#5EEAD4', 2: '#8BE0A0', 3: '#C2E37A', 4: '#F2D35C',
  5: '#F5A623', 6: '#EE8A5A', 7: '#E8607B', 8: '#A99BE0',
}

const ROMAN = { 1:'I', 2:'II', 3:'III', 4:'IV', 5:'V', 6:'VI', 7:'VII', 8:'VIII' }

function brToEra(br) {
  for (let i = 0; i < BR_ERA_THRESHOLDS.length; i++) {
    if (br <= BR_ERA_THRESHOLDS[i]) return i + 1
  }
  return 8
}

function vehicleEra(v) {
  const rawEra = Number(v.vdb_era ?? 0)
  return Math.max(1, Math.min(8, rawEra > 0 ? rawEra : brToEra(Number(v.BR) || 0)))
}

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
  { key: 'Ground',      icon: 'mdi-tank',       accent: 'var(--primary)', types: ['medium_tank','light_tank','heavy_tank','tank_destroyer','spaa'] },
  { key: 'Aviation',    icon: 'mdi-airplane',    accent: 'var(--c-info)', types: ['fighter','bomber','assault'] },
  { key: 'Helicopters', icon: 'mdi-helicopter',  accent: 'var(--c-violet)', types: ['attack_helicopter','utility_helicopter'] },
  { key: 'Fleet',       icon: 'mdi-anchor',      accent: 'var(--c-warn)', types: ['destroyer','heavy_cruiser','light_cruiser','battleship','battlecruiser','boat','heavy_boat','frigate','barge'] },
]
const TYPE_TO_BRANCH = {}
for (const b of BRANCHES) for (const ty of b.types) TYPE_TO_BRANCH[ty] ??= b.key

const METRICS = [
  { key: 'rp',       icon: 'mdi-flask'         },
  { key: 'sl',       icon: 'mdi-cash'          },
  { key: 'meta_eff', icon: 'mdi-medal-outline' },
]

const metricOptions = computed(() => METRICS.map(m => ({
  value: m.key,
  icon:  m.icon,
  label: t(`cost_tab.metric_${m.key}`),
})))

const metric          = ref('rp')
const skipFolderDupes = ref(true)
const isRpBasedMetric = computed(() => metric.value === 'rp' || metric.value === 'meta_eff')

const metricUnit = computed(() => metric.value === 'sl' ? 'SL' : 'RP')

const uniqueVehicles = shallowRef([])
watchEffect(() => {
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
        if (!cls.includes(v.VehicleClass ?? 'Standard')) continue
        if (isRpBased && (v.VehicleClass ?? 'Standard') !== 'Standard') continue
        const bKey = TYPE_TO_BRANCH[v.Type]
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

      const era = vehicleEra(v)

      const val = isRpBased ? Number(v.vdb_req_exp ?? 0) : Number(v.vdb_value ?? 0)
      if (!val) continue

      const bKey = TYPE_TO_BRANCH[v.Type]
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

const branchViews = computed(() => BRANCHES.map(branch => {
  const rows = chartRows(branch.key)
  return {
    branch,
    rows,
    count: branchVehicleCount(branch.key),
    cheap: rows.length >= 2 ? rows[rows.length - 1] : null,
    exp:   rows.length >= 2 ? rows[0] : null,
  }
}))

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
  if (p > 0.85) return 'var(--c-bad)'
  if (p > 0.60) return 'var(--c-warn)'
  if (p < 0.25) return 'var(--c-ok)'
  return 'var(--ink)'
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
.era-legend { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.era-pip {
  display: flex;
  align-items: center;
  gap: 4px;
  font: 500 10px var(--font-display);
  letter-spacing: 0.04em;
  color: var(--ink-faint);
}
.era-dot { width: 9px; height: 9px; flex-shrink: 0; }

.branches-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.branch-card {
  min-width: 0;
  border-left: 2px solid var(--accent, var(--primary));
}
.branch-card__hdr {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--hairline);
}
.branch-card__icon  { flex-shrink: 0; color: var(--accent, var(--primary)); }
.branch-card__title { font-size: 12px; color: var(--accent, var(--primary)); }
.branch-card__summary { display: flex; flex-wrap: wrap; gap: 12px; }

.card-stat {
  --c: var(--ink-muted);
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--ink-faint);
}
.card-stat__dot { width: 5px; height: 5px; flex-shrink: 0; background: var(--c); }
.card-stat b    { color: var(--c); font-weight: 600; }
.card-stat__val { font-family: var(--font-display); color: var(--ink-muted); }

.branch-card__rows { padding: 2px 0; overflow-x: auto; -webkit-overflow-scrolling: touch; }

.bar-row {
  display: grid;
  grid-template-columns: 110px 1fr var(--count-col-w, 40px) 84px;
  align-items: center;
  gap: 8px;
  min-width: 470px;
  padding: 5px 14px;
  border-top: 1px solid var(--hairline);
  transition: opacity 0.12s;
}
.bar-row:first-child { border-top: none; }
.branch-card__rows:has(.bar-row:hover) .bar-row:not(:hover) { opacity: 0.25; }

.nation-col  { display: flex; align-items: center; gap: 6px; min-width: 0; }
.nation-flag { flex-shrink: 0; font-size: 14px; line-height: 1; }
.nation-name {
  overflow: hidden;
  font: 500 11px var(--font-display);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--ink-muted);
}

.bar-col   { min-width: 0; }
.bar-track { display: flex; width: 100%; height: 22px; overflow: hidden; background: var(--surface-2); }
.bar-seg {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  min-width: 2px;
  height: 100%;
  margin-right: 1px;
  overflow: hidden;
  container-type: inline-size;
  transition: filter 0.12s;
}
.bar-seg:last-child { margin-right: 0; }
.bar-seg:hover      { filter: brightness(1.2); }
.bar-seg-label {
  display: none;
  font: 600 10px var(--font-display);
  letter-spacing: -0.02em;
  white-space: nowrap;
  color: var(--bg);
  opacity: 0.75;
  pointer-events: none;
  user-select: none;
}
@container (min-width: 24px) { .bar-seg-label { display: block; } }

.count-col  { text-align: right; }
.count-chip { padding: 1px 6px; font-size: 10px; font-weight: 500; color: var(--ink-muted); }
.count-chip.tint { color: var(--c); }
.count-chip__sep { margin: 0 3px; opacity: 0.5; }

.total-col   { text-align: right; }
.total-label { font: 600 12px var(--font-display); font-variant-numeric: tabular-nums; }

.tooltip-content { font-size: 12px; line-height: 1.6; }

@media (max-width: 760px) {
  .controls-row { flex-wrap: nowrap; overflow-x: auto; -webkit-overflow-scrolling: touch; padding-bottom: 2px; }
  .controls-row > * { flex-shrink: 0; }
  .controls-row .ml-auto { margin-left: 0; }
  .era-legend    { flex-wrap: nowrap; }
  .branches-grid { grid-template-columns: 1fr; }
}
</style>
