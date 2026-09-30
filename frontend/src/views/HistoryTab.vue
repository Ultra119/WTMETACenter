<template>
  <div class="history-root">

    <div class="controls-bar mb-4">
      <div class="controls-row">

        <v-select
          v-model="nation"
          :items="nationOptions"
          item-title="label"
          item-value="value"
          :label="t('common.nation')"
          prepend-inner-icon="mdi-flag"
          style="max-width:220px"
        />

        <div class="stats-row ml-auto">
          <span class="tag stat">
            <v-icon size="13" class="stat-icon">mdi-rocket-launch-outline</v-icon>
            <b class="stat-val">{{ filteredTotal.toLocaleString() }}</b>
            <span class="eyebrow eyebrow--xs">{{ t('history_tab.vehicles') }}</span>
          </span>
          <span class="tag stat">
            <v-icon size="13" class="stat-icon">mdi-calendar-multiple</v-icon>
            <b class="stat-val">{{ datedGroupCount }}</b>
            <span class="eyebrow eyebrow--xs">{{ t('history_tab.patches') }}</span>
          </span>
          <span class="tag stat stat--muted">
            <v-icon size="13" class="stat-icon">mdi-calendar-question</v-icon>
            <b class="stat-val">{{ launchCount.toLocaleString() }}</b>
            <span class="eyebrow eyebrow--xs">{{ t('history_tab.founding') }}</span>
          </span>
        </div>

        <InfoTip align="right">
          <b>{{ t('history_tab.info', { n: filteredTotal, groups: datedGroupCount, launch: launchCount }) }}</b>
          <p>{{ t('history_tab.tip_sort') }}</p>
          <div class="tip-row" style="margin-top:8px">
            <v-icon class="tip-icon" style="color:var(--c-warn)">mdi-circle</v-icon>
            <span>{{ t('history_tab.tip_limited') }}</span>
          </div>
        </InfoTip>

      </div>
    </div>

    <div v-if="!groups.length" class="panel no-data">
      {{ t('history_tab.search_empty') }}
    </div>

    <div v-else class="timeline">
      <section v-for="yw in yearGroups" :key="yw.year" class="tl-year-wrap">
        <button
          type="button"
          class="tl-year"
          :class="{ 'tl-year--open': isOpen(yw.year) }"
          :aria-expanded="isOpen(yw.year)"
          @click="toggleYear(yw.year)"
        >
          <span class="tl-year__text">{{ yw.year }}</span>
          <span class="tl-year__meta">
            {{ yw.groups.length }}&thinsp;{{ t('history_tab.patches').toLowerCase() }}
            &nbsp;·&nbsp;
            {{ yw.totalVehicles.toLocaleString() }}&thinsp;{{ t('history_tab.vehicles').toLowerCase() }}
          </span>
          <v-icon size="16" class="tl-year__chevron">mdi-chevron-right</v-icon>
        </button>

        <div class="tl-body-outer" :class="{ 'tl-body-outer--open': isOpen(yw.year) }">
          <div v-if="everOpenedYears.has(yw.year)" class="tl-body">
            <HistoryGroup
              v-for="group in yw.groups"
              :key="group.key"
              :group="group"
              :expanded="monthExpanded.has(group.key)"
              :query="store.searchQuery"
              :preview="MONTH_PREVIEW"
              @toggle="toggleMonth(group.key)"
              @open="open"
            />
          </div>
        </div>
      </section>

      <HistoryGroup
        v-if="launchGroup"
        launch
        :group="launchGroup"
        :expanded="monthExpanded.has(launchGroup.key)"
        :query="store.searchQuery"
        @toggle="toggleMonth(launchGroup.key)"
        @open="open"
      />
    </div>

  </div>
</template>

<script setup>
import { ref, computed, inject, watch, onMounted, onBeforeUnmount, onActivated, onDeactivated } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import { useTabFilters } from '../composables/useTabFilters.js'
import { NATION_FLAG } from '../composables/useVehicleFormatting.js'
import InfoTip from '../components/InfoTip.vue'
import HistoryGroup from '../components/HistoryGroup.vue'

const { t }       = useI18n()
const store       = useDataStore()
const openVehicle = inject('openVehicle')

useTabFilters({ period: false, mode: false, brRange: false, minBattles: false, classes: true, types: true })

onMounted(()     => { store.historyTabActive = true  })
onBeforeUnmount(()  => { store.historyTabActive = false })
onActivated(()   => { store.historyTabActive = true  })
onDeactivated(() => { store.historyTabActive = false })

const MONTH_PREVIEW = 6

const nation = ref('All')

const nationOptions = computed(() => [
  { value: 'All', label: t('common.all') },
  ...(store.metaInfo?.nations ?? []).map(n => ({
    value: n,
    label: `${NATION_FLAG[n.toLowerCase()] ?? '🏴'} ${n.charAt(0).toUpperCase() + n.slice(1)}`,
  })),
])


const uniqueVehicles = computed(() => {
  const all = store.allVehicles
  const map = new Map()
  for (const v of all) {
    const key = v.vdb_identifier || `${v.Name}|${v.Nation}|${v.Type}`
    const existing = map.get(key)
    if (!existing || v.Mode === 'Realistic') {
      map.set(key, { ...v, _dedup_key: key })
    }
  }
  return [...map.values()]
})


const filtered = computed(() => {
  let list = uniqueVehicles.value

  list = list.filter(v => store.classes.includes(v.VehicleClass ?? 'Standard'))

  const activeTypes = store.activeTypes
  list = list.filter(v => activeTypes.includes(v.Type))

  if (nation.value !== 'All') {
    list = list.filter(v => v.Nation === nation.value)
  }

  const q = store.searchQuery.trim().toLowerCase()
  if (q) {
    list = list.filter(v => (v.Name ?? '').toLowerCase().includes(q))
  }

  return list
})


function parseReleaseDate(raw) {
  if (!raw) return null
  const s = String(raw).replace(/[./]/g, '-').trim()
  const parts = s.split('-')
  if (parts.length !== 3) return null

  let year, month, day
  if (parts[0].length === 4) {
    ;[year, month, day] = parts.map(Number)
  } else {
    ;[day, month, year] = parts.map(Number)
  }

  if (
    !Number.isInteger(year)  || year  < 2013 || year  > 2100 ||
    !Number.isInteger(month) || month < 1    || month > 12   ||
    !Number.isInteger(day)   || day   < 1    || day   > 31
  ) return null

  const d = new Date(year, month - 1, day)
  if (d.getFullYear() !== year || d.getMonth() !== month - 1 || d.getDate() !== day) return null
  return d
}

function formatGroupDate(isoKey) {
  try {
    const [y, m, d] = isoKey.split('-').map(Number)
    return new Date(y, m - 1, d).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
  } catch { return isoKey }
}

function formatGroupMonth(isoKey) {
  try {
    const [y, m, d] = isoKey.split('-').map(Number)
    return new Date(y, m - 1, d).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
  } catch { return isoKey }
}

const LAUNCH_KEY = '__launch__'

const groups = computed(() => {
  const map = new Map()

  for (const v of filtered.value) {
    const d   = parseReleaseDate(v.vdb_release_date)
    const key = d ? d.toISOString().slice(0, 10) : LAUNCH_KEY

    if (!map.has(key)) {
      map.set(key, {
        key,
        vehicles:   [],
        isLaunch:   key === LAUNCH_KEY,
        label:      key === LAUNCH_KEY ? t('history_tab.game_launch') : formatGroupDate(key),
        monthLabel: key === LAUNCH_KEY ? t('history_tab.game_launch') : formatGroupMonth(key),
        subtitle:   key === LAUNCH_KEY ? t('history_tab.launch_subtitle') : null,
      })
    }
    map.get(key).vehicles.push(v)
  }

  return [...map.values()].sort((a, b) => {
    if (a.isLaunch) return  1
    if (b.isLaunch) return -1
    return b.key.localeCompare(a.key)
  }).map(g => ({
    ...g,
    vehicles: g.vehicles.slice().sort((a, b) => {
      const nc = (a.Nation ?? '').localeCompare(b.Nation ?? '')
      if (nc !== 0) return nc
      return (a.BR ?? 0) - (b.BR ?? 0)
    }),
  }))
})

const yearGroups = computed(() => {
  const yearMap = new Map()
  for (const g of groups.value) {
    if (g.isLaunch) continue
    const year = g.key.slice(0, 4)
    if (!yearMap.has(year)) yearMap.set(year, { year, groups: [], totalVehicles: 0 })
    const yw = yearMap.get(year)
    yw.groups.push(g)
    yw.totalVehicles += g.vehicles.length
  }
  return [...yearMap.values()].sort((a, b) => b.year.localeCompare(a.year))
})

const launchGroup = computed(() => groups.value.find(g => g.isLaunch) ?? null)

const filteredTotal   = computed(() => filtered.value.length)
const datedGroupCount = computed(() => groups.value.filter(g => !g.isLaunch).length)
const launchCount     = computed(() => launchGroup.value?.vehicles.length ?? 0)

const collapsedYears  = ref(new Set())
const everOpenedYears = ref(new Set())

watch(yearGroups, (ywList) => {
  const next = new Set(collapsedYears.value)
  for (const yw of ywList) next.add(yw.year)
  collapsedYears.value = next
}, { immediate: true })

function toggleYear(year) {
  const nextCollapsed = new Set(collapsedYears.value)
  const nextOpened    = new Set(everOpenedYears.value)

  if (nextCollapsed.has(year)) {
    nextCollapsed.delete(year)
    nextOpened.add(year)
  } else {
    nextCollapsed.add(year)
  }

  collapsedYears.value  = nextCollapsed
  everOpenedYears.value = nextOpened
}

const monthExpanded = ref(new Set())

function toggleMonth(key) {
  const next = new Set(monthExpanded.value)
  next.has(key) ? next.delete(key) : next.add(key)
  monthExpanded.value = next
}

watch(() => store.searchQuery, q => {
  if (q.trim()) {
    const nextCollapsed = new Set()
    const nextOpened    = new Set(yearGroups.value.map(yw => yw.year))
    collapsedYears.value  = nextCollapsed
    everOpenedYears.value = nextOpened
    monthExpanded.value   = new Set(groups.value.map(g => g.key))
  } else {
    collapsedYears.value = new Set(yearGroups.value.map(yw => yw.year))
    monthExpanded.value  = new Set()
  }
})

const isOpen = year => !collapsedYears.value.has(year)

function open(v) {
  openVehicle?.(v)
}
</script>

<style scoped>
.history-root { width: 100%; }

.stats-row { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.stat      { gap: 6px; padding: 4px 10px; }
.stat-icon { color: var(--primary); }
.stat-val  { font: 600 13px var(--font-display); font-variant-numeric: tabular-nums; color: var(--ink); }
.stat .eyebrow { font-size: 9px; letter-spacing: 0.1em; }
.stat--muted   { opacity: 0.7; }

.timeline { display: flex; flex-direction: column; gap: 6px; }

.tl-year-wrap {
  display: flex;
  flex-direction: column;
  content-visibility: auto;
  contain-intrinsic-size: 0 44px;
}

.tl-year {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 9px 14px;
  border: 1px solid var(--hairline);
  background: var(--surface);
  color: inherit;
  text-align: left;
  cursor: pointer;
  user-select: none;
  transition: border-color 0.15s, background 0.15s;
}
.tl-year:hover       { border-color: var(--hairline-strong); }
.tl-year--open       { border-color: var(--primary-line); background: var(--primary-soft); }
.tl-year__text {
  flex-shrink: 0;
  font: 600 14px var(--font-display);
  letter-spacing: 0.08em;
  color: var(--ink);
}
.tl-year--open .tl-year__text { color: var(--primary); }
.tl-year__meta    { font-size: 11px; color: var(--ink-faint); }
.tl-year__chevron { margin-left: auto; flex-shrink: 0; color: var(--ink-dim); transition: transform 0.26s cubic-bezier(0.4, 0, 0.2, 1), color 0.15s; }
.tl-year:hover .tl-year__chevron { color: var(--ink-muted); }
.tl-year--open .tl-year__chevron { transform: rotate(90deg); color: var(--primary); }

.tl-body-outer { display: grid; grid-template-rows: 0fr; transition: grid-template-rows 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.tl-body-outer--open { grid-template-rows: 1fr; }
.tl-body {
  min-height: 0;
  margin-left: 8px;
  padding: 6px 0 0 16px;
  overflow: hidden;
  border-left: 1px solid var(--hairline);
}

@media (max-width: 720px) {
  .stats-row { display: none; }
}
</style>
