<template>
  <div class="history-root">

    <div class="controls-bar mb-4">
      <div class="controls-row">

        <div class="history-search-wrap">
          <span class="mdi mdi-magnify search-icon" />
          <input
            v-model="search"
            class="history-search"
            :placeholder="t('topbar.search_hint')"
          />
          <button v-if="search" class="search-clear" @click="search = ''">
            <span class="mdi mdi-close" />
          </button>
        </div>

        <div class="ctrl-divider" />

        <div>
          <div class="ctrl-label">{{ t('common.nation') }}</div>
          <v-select
            :model-value="nation"
            :items="nationOptions"
            item-title="label"
            item-value="value"
            density="compact"
            variant="outlined"
            hide-details
            style="min-width: 160px;"
            @update:model-value="v => nation = v"
          />
        </div>

        <div class="ml-auto stats-row" style="display:flex;align-items:center;gap:8px;">
          <div class="stat-pill">
            <span class="mdi mdi-rocket-launch-outline stat-icon" />
            <span class="stat-val">{{ filteredTotal.toLocaleString() }}</span>
            <span class="stat-lbl">{{ t('history_tab.vehicles') }}</span>
          </div>
          <div class="stat-pill">
            <span class="mdi mdi-calendar-multiple stat-icon" />
            <span class="stat-val">{{ datedGroupCount }}</span>
            <span class="stat-lbl">{{ t('history_tab.patches') }}</span>
          </div>
          <div class="stat-pill stat-pill--muted">
            <span class="mdi mdi-history stat-icon" />
            <span class="stat-val">{{ launchCount.toLocaleString() }}</span>
            <span class="stat-lbl">{{ t('history_tab.founding') }}</span>
          </div>

          <InfoTip align="right" class="ml-auto">
            <b>{{ t('history_tab.info', { n: filteredTotal, groups: datedGroupCount, launch: launchCount }) }}</b>
            <p>{{ t('history_tab.tip_sort') }}</p>
            <div class="tip-row" style="margin-top:8px">
              <span class="mdi mdi-circle tip-icon" style="color:#fb923c" />
              <span>{{ t('history_tab.tip_limited') }}</span>
            </div>
          </InfoTip>
        </div>

      </div>
    </div>

    <div v-if="!groups.length" class="no-data">
      {{ t('history_tab.search_empty') }}
    </div>

    <div v-else class="timeline">
      <div
        v-for="yw in yearGroups"
        :key="yw.year"
        class="tl-year-wrap"
      >
        <div
          class="tl-year-header"
          :class="{ 'tl-year-header--open': !collapsedYears.has(yw.year) }"
          @click="toggleYear(yw.year)"
        >
          <span class="tl-year-text">{{ yw.year }}</span>
          <span class="tl-year-meta">
            {{ yw.groups.length }}&thinsp;{{ t('history_tab.patches').toLowerCase() }}
            &nbsp;·&nbsp;
            {{ yw.totalVehicles.toLocaleString() }}&thinsp;{{ t('history_tab.vehicles').toLowerCase() }}
          </span>
          <span class="mdi mdi-chevron-right tl-year-chevron" />
        </div>

        <div
          class="tl-year-body-outer"
          :class="{ 'tl-year-body-outer--open': !collapsedYears.has(yw.year) }"
        >
          <div v-if="everOpenedYears.has(yw.year)" class="tl-year-body">

            <div
              v-for="group in yw.groups"
              :key="group.key"
              class="month-section"
            >
              <!-- Month label row: date | type pills | line | count -->
              <div class="month-header">
                <span class="month-header__date">{{ group.monthLabel }}</span>
                <div class="month-header__types">
                  <span
                    v-for="item in groupTypeSummary(group.vehicles)"
                    :key="item.cat"
                    class="tl-type-pill"
                  >
                    <span
                      class="mdi"
                      :class="CATEGORY_ICON[item.cat]"
                      :style="{ color: CATEGORY_COLOR[item.cat] }"
                    />
                    <span class="tl-type-count">{{ item.count }}</span>
                  </span>
                </div>
                <div class="month-header__line" />
                <span class="month-header__count">{{ group.vehicles.length }}</span>
              </div>

              <div
                class="veh-grid-outer"
                :class="{ 'veh-grid-outer--collapsed': needsPreview(group) && !monthExpanded.has(group.key) }"
              >
                <div class="veh-grid-inner">
                <div class="veh-grid">
                  <div
                    v-for="v in group.vehicles"
                    :key="v._dedup_key"
                    class="veh-row"
                    :class="{ 'veh-row--limited': isLimited(v) }"
                    @click="open(v)"
                  >
                    <span class="veh-flag" :title="v.Nation">
                      {{ NATION_FLAG[v.Nation?.toLowerCase()] ?? '🏴' }}
                    </span>
                    <span
                      class="mdi veh-type-icon"
                      :class="TYPE_ICON[v.Type] ?? 'mdi-help-circle-outline'"
                      :style="{ color: typeIconColor(v.Type) }"
                      :title="fmtType(v.Type)"
                    />
                    <span class="veh-name" v-html="highlightName(v.Name)" />
                    <div class="veh-right">
                      <span
                        v-if="v.VehicleClass !== 'Standard'"
                        class="class-chip"
                        :style="classChipStyle(v.VehicleClass)"
                      >
                        <span
                          v-if="CLASS_PREFIX[v.VehicleClass]"
                          class="mdi"
                          :class="CLASS_PREFIX[v.VehicleClass]"
                          style="font-size: 9px; margin-right: 2px;"
                        />{{ t(`vehicle_classes.${v.VehicleClass}`) }}
                      </span>
                      <span class="veh-br">{{ displayBR(v) }}</span>
                    </div>
                  </div>
                </div>
                </div>
              </div>

              <div v-if="needsPreview(group)" class="show-more-row">
                <button
                  v-if="!monthExpanded.has(group.key)"
                  class="show-more-btn"
                  @click="expandMonth(group.key)"
                >
                  <span class="mdi mdi-chevron-double-down" style="margin-right: 4px;" />
                  {{ t('history_tab.show_all', { n: group.vehicles.length }) }}
                </button>
                <button
                  v-else
                  class="show-more-btn show-more-btn--collapse"
                  @click="collapseMonth(group.key)"
                >
                  <span class="mdi mdi-chevron-double-up" style="margin-right: 4px;" />
                  {{ t('history_tab.collapse') }}
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>

      <div v-if="launchGroup" class="month-section month-section--launch">
        <div class="month-header">
          <span class="month-header__date month-header__date--launch">{{ launchGroup.label }}</span>
          <span class="tl-badge tl-badge--launch">{{ t('history_tab.all_time') }}</span>
          <span v-if="launchGroup.subtitle" class="tl-subtitle" style="margin-left:4px">
            {{ launchGroup.subtitle }}
          </span>
          <div class="month-header__types">
            <span
              v-for="item in groupTypeSummary(launchGroup.vehicles)"
              :key="item.cat"
              class="tl-type-pill"
            >
              <span
                class="mdi"
                :class="CATEGORY_ICON[item.cat]"
                :style="{ color: CATEGORY_COLOR[item.cat] }"
              />
              <span class="tl-type-count">{{ item.count }}</span>
            </span>
          </div>
          <div class="month-header__line month-header__line--launch" />
          <span class="month-header__count">{{ launchGroup.vehicles.length }}</span>
        </div>

        <div
          class="veh-grid-outer"
          :class="{ 'veh-grid-outer--collapsed': !monthExpanded.has(launchGroup.key) }"
        >
          <div class="veh-grid-inner">
          <div class="veh-grid">
            <div
              v-for="v in launchGroup.vehicles"
              :key="v._dedup_key"
              class="veh-row"
              :class="{ 'veh-row--limited': isLimited(v) }"
              @click="open(v)"
            >
              <span class="veh-flag" :title="v.Nation">
                {{ NATION_FLAG[v.Nation?.toLowerCase()] ?? '🏴' }}
              </span>
              <span
                class="mdi veh-type-icon"
                :class="TYPE_ICON[v.Type] ?? 'mdi-help-circle-outline'"
                :style="{ color: typeIconColor(v.Type) }"
                :title="fmtType(v.Type)"
              />
              <span class="veh-name" v-html="highlightName(v.Name)" />
              <div class="veh-right">
                <span
                  v-if="v.VehicleClass !== 'Standard'"
                  class="class-chip"
                  :style="classChipStyle(v.VehicleClass)"
                >
                  <span
                    v-if="CLASS_PREFIX[v.VehicleClass]"
                    class="mdi"
                    :class="CLASS_PREFIX[v.VehicleClass]"
                    style="font-size: 9px; margin-right: 2px;"
                  />{{ t(`vehicle_classes.${v.VehicleClass}`) }}
                </span>
                <span class="veh-br">{{ displayBR(v) }}</span>
              </div>
            </div>
          </div>
          </div>
        </div>

        <div class="show-more-row">
          <button
            v-if="!monthExpanded.has(launchGroup.key)"
            class="show-more-btn"
            @click="expandMonth(launchGroup.key)"
          >
            <span class="mdi mdi-chevron-double-down" style="margin-right: 4px;" />
            {{ t('history_tab.show_all', { n: launchGroup.vehicles.length }) }}
          </button>
          <button
            v-else
            class="show-more-btn show-more-btn--collapse"
            @click="collapseMonth(launchGroup.key)"
          >
            <span class="mdi mdi-chevron-double-up" style="margin-right: 4px;" />
            {{ t('history_tab.collapse') }}
          </button>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ref, computed, inject, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import { useTabFilters } from '../composables/useTabFilters.js'
import { NATION_FLAG, fmtType, fmtBR, CLASS_PREFIX, classChipStyle } from '../composables/useVehicleFormatting.js'
import { TYPE_ICON, TYPE_BRANCH_COLOR } from '../composables/constants.js'
import InfoTip from '../components/InfoTip.vue'

const { t }       = useI18n()
const store       = useDataStore()
const openVehicle = inject('openVehicle')

useTabFilters({ period: false, mode: false, brRange: false, minBattles: false, classes: true, types: true })

const MONTH_PREVIEW = 6

const search = ref('')
const nation = ref('All')

const CATEGORY_ICON = {
  Ground:     'mdi-tank',
  Aviation:   'mdi-airplane',
  Helicopters:'mdi-helicopter',
  Fleet:      'mdi-ferry',
}
const CATEGORY_COLOR = {
  Ground:     '#84cc16',
  Aviation:   '#38bdf8',
  Helicopters:'#a78bfa',
  Fleet:      '#2dd4bf',
}
const TYPE_TO_CAT = {
  medium_tank: 'Ground', light_tank: 'Ground', heavy_tank: 'Ground',
  tank_destroyer: 'Ground', spaa: 'Ground',
  fighter: 'Aviation', bomber: 'Aviation', assault: 'Aviation',
  attack_helicopter: 'Helicopters', utility_helicopter: 'Helicopters',
  destroyer: 'Fleet', heavy_cruiser: 'Fleet', light_cruiser: 'Fleet',
  battleship: 'Fleet', battlecruiser: 'Fleet',
  boat: 'Fleet', heavy_boat: 'Fleet', frigate: 'Fleet', barge: 'Fleet',
}
const CAT_ORDER = ['Ground', 'Aviation', 'Helicopters', 'Fleet']

function groupTypeSummary(vehicles) {
  const counts = {}
  for (const v of vehicles) {
    const cat = TYPE_TO_CAT[v.Type]
    if (cat) counts[cat] = (counts[cat] ?? 0) + 1
  }
  return CAT_ORDER.filter(c => counts[c]).map(c => ({ cat: c, count: counts[c] }))
}

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

  const q = search.value.trim().toLowerCase()
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

function needsPreview(group) {
  return group.vehicles.length > MONTH_PREVIEW
}
function expandMonth(key) {
  const next = new Set(monthExpanded.value)
  next.add(key)
  monthExpanded.value = next
}
function collapseMonth(key) {
  const next = new Set(monthExpanded.value)
  next.delete(key)
  monthExpanded.value = next
}

watch(search, q => {
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

function isLimited(v) {
  return v.vdb_shop_is_event || v.vdb_shop_is_gift
}

function displayBR(v) {
  return fmtBR(v.vdb_realistic_br ?? v.BR)
}

function typeIconColor(type) {
  return TYPE_BRANCH_COLOR[type] ?? '#475569'
}

function open(v) {
  openVehicle?.(v)
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function highlightName(name) {
  const q    = search.value.trim()
  const safe = escapeHtml(name ?? '')
  if (!q) return safe
  const esc = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return safe.replace(new RegExp(`(${esc})`, 'gi'), '<mark class="hl">$1</mark>')
}
</script>

<style scoped>
.history-root {
  width: 100%;
}


.history-search-wrap {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 180px;
  max-width: 300px;
}
.search-icon {
  position: absolute;
  left: 10px;
  color: #475569;
  font-size: 15px;
  pointer-events: none;
}
.history-search {
  width: 100%;
  height: 36px;
  padding: 0 32px 0 32px;
  background: rgba(10, 22, 40, 0.8);
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  outline: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #e2e8f0;
  transition: border-color 0.15s;
}
.history-search::placeholder { color: #475569; }
.history-search:focus { border-color: rgba(56, 189, 248, 0.5); }
.search-clear {
  position: absolute;
  right: 8px;
  background: transparent;
  border: none;
  color: #475569;
  cursor: pointer;
  font-size: 13px;
  padding: 0;
  display: flex;
  align-items: center;
}
.search-clear:hover { color: #94a3b8; }

.stats-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.stat-pill {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  background: rgba(10, 22, 40, 0.8);
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  white-space: nowrap;
}
.stat-pill--muted { opacity: 0.7; }
.stat-icon { font-size: 13px; color: #38bdf8; flex-shrink: 0; }
.stat-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  color: #a7f3d0;
}
.stat-lbl {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: #475569;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tl-year-wrap {
  display: flex;
  flex-direction: column;
  gap: 3px;
  content-visibility: auto;
  contain-intrinsic-size: 0 48px;
}

.tl-year-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 14px;
  background: rgba(10, 22, 40, 0.75);
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  transition: background 0.12s, border-color 0.15s;
}
.tl-year-header:hover {
  background: rgba(30, 58, 95, 0.22);
  border-color: rgba(56, 189, 248, 0.18);
}
.tl-year-header--open {
  background: linear-gradient(90deg, rgba(30, 58, 95, 0.30) 0%, rgba(15, 23, 42, 0.85) 100%);
  border-color: rgba(56, 189, 248, 0.22);
}

.tl-year-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  color: #7dd3fc;
  letter-spacing: 0.08em;
  flex-shrink: 0;
}
.tl-year-meta {
  font-size: 11px;
  color: #334155;
  letter-spacing: 0.03em;
}

.tl-year-chevron {
  font-size: 15px;
  color: #334155;
  margin-left: auto;
  flex-shrink: 0;
  transition: transform 0.26s cubic-bezier(0.4, 0, 0.2, 1), color 0.15s;
}
.tl-year-header:hover .tl-year-chevron { color: #475569; }
.tl-year-header--open .tl-year-chevron {
  transform: rotate(90deg);
  color: #38bdf8;
}

.tl-year-body-outer {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.30s cubic-bezier(0.4, 0, 0.2, 1);
}
.tl-year-body-outer--open {
  grid-template-rows: 1fr;
}

.tl-year-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-left: 18px;
  overflow: hidden;
  min-height: 0;
}

.month-section {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 2px 0 8px;
}
.month-section--launch {
  margin-top: 8px;
  padding-top: 4px;
  border-top: 1px solid rgba(251, 191, 36, 0.15);
}

.month-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 2px 4px;
  user-select: none;
}
.month-header__date {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  letter-spacing: 0.07em;
  flex-shrink: 0;
}
.month-header__date--launch { color: #fbbf24; }

.month-header__types {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.month-header__line {
  flex: 1;
  height: 1px;
  background: #1e293b;
  margin: 0 2px;
}
.month-header__line--launch {
  background: rgba(251, 191, 36, 0.12);
}
.month-header__count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: #334155;
  flex-shrink: 0;
}

.veh-grid-outer {
  display: grid;
  grid-template-rows: 1fr;
  transition: grid-template-rows 0.30s cubic-bezier(0.4, 0, 0.2, 1);
}
.veh-grid-outer--collapsed {
  grid-template-rows: 0fr;
}
.veh-grid-inner {
  overflow: hidden;
  min-height: 0;
}

.veh-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 3px;
  padding: 0 0 2px;
}

.tl-subtitle {
  font-size: 10px;
  color: #475569;
  font-style: italic;
  letter-spacing: 0.03em;
}
.tl-badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 4px;
}
.tl-badge--launch {
  border: 1px solid rgba(251, 191, 36, 0.35);
  background: rgba(251, 191, 36, 0.08);
  color: #fbbf24;
}

.tl-type-pill {
  display: flex;
  align-items: center;
  gap: 3px;
}
.tl-type-pill .mdi {
  font-size: 12px;
  opacity: 0.9;
}
.tl-type-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: #475569;
  line-height: 1;
}

.veh-row {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 8px;
  border-radius: 5px;
  border: 1px solid rgba(30, 58, 95, 0.6);
  cursor: pointer;
  transition: background 0.1s, border-color 0.1s;
  min-width: 0;
  background: transparent;
  contain: layout style;
}
.veh-row:hover {
  background: rgba(56, 189, 248, 0.06);
  border-color: rgba(56, 189, 248, 0.28);
}

.veh-row--limited {
  border-color: rgba(251, 146, 60, 0.28);
  background: transparent;
}
.veh-row--limited:hover {
  background: rgba(251, 146, 60, 0.07);
  border-color: rgba(251, 146, 60, 0.45);
}

.veh-flag {
  font-size: 14px;
  flex-shrink: 0;
  line-height: 1;
}
.veh-type-icon {
  font-size: 13px;
  flex-shrink: 0;
  opacity: 0.85;
}
.veh-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
}
.veh-row:hover .veh-name { color: #e2e8f0; }

.veh-right {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}
.veh-br {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  min-width: 28px;
  text-align: right;
}

.show-more-row {
  display: flex;
  justify-content: flex-start;
  padding: 4px 0 2px;
}
.show-more-btn {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  background: transparent;
  color: #475569;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}
.show-more-btn:hover {
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.06);
}
.show-more-btn--collapse { border-color: rgba(56, 189, 248, 0.2); color: #334155; }
.show-more-btn--collapse:hover { color: #94a3b8; border-color: #334155; background: transparent; }


:deep(.hl) {
  background: rgba(251, 191, 36, 0.25);
  color: #fde68a;
  border-radius: 2px;
  font-style: normal;
}
</style>
