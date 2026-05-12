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
        v-for="(group, gi) in groups"
        :key="group.key"
        class="tl-group"
      >
        <div
          class="tl-header"
          :class="{ 'tl-header--launch': group.isLaunch }"
          @click="toggleGroup(group.key)"
        >
          <div class="tl-rail">
            <div class="tl-rail-line tl-rail-line--top" :class="{ invisible: gi === 0 }" />
            <div class="tl-dot" :class="group.isLaunch ? 'tl-dot--launch' : 'tl-dot--patch'" />
            <div class="tl-rail-line tl-rail-line--bot" :class="{ invisible: gi === groups.length - 1 && collapsed.has(group.key) }" />
          </div>

          <div class="tl-date-area">
            <span class="tl-date-text" :class="{ 'tl-date-text--launch': group.isLaunch }">
              {{ group.label }}
            </span>
            <span v-if="group.isLaunch" class="tl-badge tl-badge--launch">
              {{ t('history_tab.all_time') }}
            </span>
            <span v-if="group.subtitle" class="tl-subtitle">{{ group.subtitle }}</span>
          </div>

          <div class="tl-dash" />
          <span class="tl-count">{{ group.vehicles.length }}</span>

          <span
            class="mdi tl-chevron"
            :class="collapsed.has(group.key) ? 'mdi-chevron-right' : 'mdi-chevron-down'"
          />
        </div>

        <Transition name="group-slide">
          <div v-if="!collapsed.has(group.key)" class="tl-body">
            <div class="tl-body-rail">
              <div class="tl-rail-line tl-rail-line--full" :class="{ invisible: gi === groups.length - 1 }" />
            </div>

            <div class="veh-grid">
              <div
                v-for="v in visibleVehicles(group)"
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

                <span class="veh-name">{{ v.Name }}</span>

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

            <div v-if="group.vehicles.length > PAGE_SIZE" class="show-more-row">
              <button
                v-if="!expanded.has(group.key)"
                class="show-more-btn"
                @click.stop="expanded.add(group.key); expanded = new Set(expanded)"
              >
                <span class="mdi mdi-chevron-double-down" style="margin-right: 4px;" />
                {{ t('history_tab.show_all', { n: group.vehicles.length }) }}
              </button>
              <button
                v-else
                class="show-more-btn show-more-btn--collapse"
                @click.stop="expanded.delete(group.key); expanded = new Set(expanded)"
              >
                <span class="mdi mdi-chevron-double-up" style="margin-right: 4px;" />
                {{ t('history_tab.collapse') }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import { useTabFilters } from '../composables/useTabFilters.js'
import { NATION_FLAG, fmtType, fmtBR, CLASS_PREFIX, classChipStyle } from '../composables/useVehicleFormatting.js'
import { TYPE_ICON, TYPE_BRANCH_COLOR } from '../composables/constants.js'
import InfoTip from '../components/InfoTip.vue'

const { t }    = useI18n()
const store    = useDataStore()
const openVehicle = inject('openVehicle')

useTabFilters({ period: false, mode: false, brRange: false, minBattles: false, classes: true, types: true })


const PAGE_SIZE = 30

const search  = ref('')
const nation  = ref('All')


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
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

function formatGroupDate(isoKey) {
  try {
    const [y, m, d] = isoKey.split('-').map(Number)
    const date = new Date(y, m - 1, d)
    return date.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
  } catch {
    return isoKey
  }
}

const LAUNCH_KEY = '__launch__'

const groups = computed(() => {
  const map = new Map()

  for (const v of filtered.value) {
    const rd  = v.vdb_release_date
    const d   = parseReleaseDate(rd)
    const key = d ? d.toISOString().slice(0, 10) : LAUNCH_KEY

    if (!map.has(key)) {
      map.set(key, {
        key,
        vehicles:  [],
        isLaunch:  key === LAUNCH_KEY,
        label:     key === LAUNCH_KEY ? t('history_tab.game_launch') : formatGroupDate(key),
        subtitle:  key === LAUNCH_KEY ? t('history_tab.launch_subtitle') : null,
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


const filteredTotal   = computed(() => filtered.value.length)
const datedGroupCount = computed(() => groups.value.filter(g => !g.isLaunch).length)
const launchCount     = computed(() => groups.value.find(g => g.isLaunch)?.vehicles.length ?? 0)

const collapsed = ref(new Set([LAUNCH_KEY]))
const expanded  = ref(new Set())

function toggleGroup(key) {
  const next = new Set(collapsed.value)
  if (next.has(key)) next.delete(key)
  else               next.add(key)
  collapsed.value = next
}


function visibleVehicles(group) {
  if (expanded.value.has(group.key)) return group.vehicles
  return group.vehicles.slice(0, PAGE_SIZE)
}


function isLimited(v) {
  return v.vdb_shop_is_event || v.vdb_shop_is_gift
}

function displayBR(v) {
  const br = v.vdb_realistic_br ?? v.BR
  return fmtBR(br)
}

function typeIconColor(type) {
  return TYPE_BRANCH_COLOR[type] ?? '#475569'
}

function open(v) {
  openVehicle?.(v)
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


.timeline { display: flex; flex-direction: column; }

.tl-group { display: flex; flex-direction: column; }

.tl-header {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  padding: 2px 0;
  border-radius: 6px;
  transition: background 0.12s;
}
.tl-header:hover { background: rgba(255, 255, 255, 0.02); }
.tl-header--launch .tl-date-text { color: #fbbf24; }

.tl-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 20px;
}
.tl-rail-line {
  width: 2px;
  flex: 1;
  min-height: 10px;
  background: #1e3a5f;
}
.tl-rail-line--top { min-height: 8px; }
.tl-rail-line--bot { min-height: 8px; }
.tl-rail-line--full { width: 2px; background: #1e3a5f; flex: 1; min-height: 100%; }
.invisible { visibility: hidden; }

.tl-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #1e3a5f;
  background: #0f172a;
  flex-shrink: 0;
  transition: border-color 0.15s, background 0.15s;
}
.tl-dot--patch {
  border-color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
}
.tl-dot--launch {
  border-color: #fbbf24;
  background: rgba(251, 191, 36, 0.15);
  width: 12px;
  height: 12px;
}
.tl-header:hover .tl-dot--patch  { background: rgba(56, 189, 248, 0.30); }
.tl-header:hover .tl-dot--launch { background: rgba(251, 191, 36, 0.30); }

.tl-date-area {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  min-width: 160px;
}
.tl-date-text {
  font-size: 13px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  color: #e2e8f0;
  letter-spacing: 0.04em;
}
.tl-date-text--launch { color: #fbbf24; }
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

.tl-dash {
  flex: 1;
  height: 1px;
  background: #1e293b;
  margin: 0 4px;
  min-width: 20px;
}

.tl-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #475569;
  min-width: 28px;
  text-align: right;
  flex-shrink: 0;
}

.tl-chevron {
  font-size: 14px;
  color: #334155;
  flex-shrink: 0;
  transition: color 0.15s;
}
.tl-header:hover .tl-chevron { color: #64748b; }

.tl-body {
  display: flex;
  gap: 0;
  padding-bottom: 6px;
  overflow: hidden;
}

.tl-body-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 20px;
  padding-top: 0;
}

.veh-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 2px;
  padding: 4px 0 4px 8px;
  min-width: 0;
}

.veh-row {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 8px;
  border-radius: 5px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: background 0.1s, border-color 0.1s;
  min-width: 0;
  background: transparent;
}
.veh-row:hover {
  background: rgba(56, 189, 248, 0.05);
  border-color: rgba(56, 189, 248, 0.15);
}
.veh-row--limited {
  border-color: rgba(251, 146, 60, 0.12);
  background: rgba(251, 146, 60, 0.03);
}
.veh-row--limited:hover {
  background: rgba(251, 146, 60, 0.07);
  border-color: rgba(251, 146, 60, 0.30);
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
  padding: 4px 8px 4px 8px;
  grid-column: 1 / -1;
  width: 100%;
}
.tl-body { flex-wrap: wrap; }
.show-more-row { flex-basis: 100%; }

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


.group-slide-enter-active,
.group-slide-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease;
  max-height: 2000px;
  overflow: hidden;
}
.group-slide-enter-from,
.group-slide-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
