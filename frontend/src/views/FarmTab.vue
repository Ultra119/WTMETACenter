<template>
  <div>

    <div class="controls-bar mb-4">
      <div class="controls-row">

        <div class="br-ctrl">
          <span class="ctrl-label">{{ t('farm_tab.target_br') }}</span>
          <div class="br-ctrl-inner">
            <v-slider
              v-model="brIndex"
              :min="0"
              :max="WT_BR_STEPS.length - 1"
              :step="1"
              hide-details
              color="primary"
              track-color="surface-variant"
              thumb-color="primary"
              class="br-slider"
            />
            <span class="br-badge">{{ fmtBR(targetBr) }}</span>
          </div>
        </div>

        <div class="ctrl-divider" />

        <v-select
          v-model="nation"
          :items="nationItems"
          item-title="title"
          item-value="value"
          :label="t('farm_tab.nation')"
          prepend-inner-icon="mdi-flag"
          style="max-width:220px"
        />

        <InfoTip align="right" class="ml-auto">
          <p><b>{{ t('tabs.farm') }}</b></p>
          <p>{{ t('farm_tab.tip_desc') }}</p>
          <div class="tip-row" style="margin-top:8px">
            <v-icon class="tip-icon" style="color:var(--primary)">mdi-check-circle</v-icon>
            <span><b>{{ t('farm_tab.role_primary') }}</b> — {{ t('farm_tab.tip_anchor') }}</span>
          </div>
          <div class="tip-row">
            <v-icon class="tip-icon" style="color:var(--c-violet)">mdi-diamond-stone</v-icon>
            <span><b>{{ t('farm_tab.gems_label') }}</b> — {{ t('farm_tab.tip_gems') }}</span>
          </div>
        </InfoTip>

      </div>
    </div>

    <div v-if="store.filtering" class="panel no-data">
      <v-icon size="14" class="mdi-spin mr-1">mdi-loading</v-icon>{{ t('common.loading') }}
    </div>

    <div v-else-if="noAnchor" class="panel no-data">
      {{ t('farm_tab.no_anchor') }}
    </div>

    <template v-else-if="result">

      <div class="panel anchor-strip mb-5">
        <div class="anchor-strip__main">
          <span class="eyebrow eyebrow--sm">{{ t('farm_tab.anchor_label') }}</span>
          <span class="anchor-strip__name">
            <v-icon
              v-if="anchorClassIcon"
              size="16"
              class="cell-class-icon"
              :style="anchorClassColor ? { color: anchorClassColor } : null"
            >{{ anchorClassIcon }}</v-icon>{{ vehicleDisplayName(result.anchor) }}
          </span>
          <span class="tag">BR {{ fmtBR(result.anchor.BR) }}</span>
        </div>
        <div class="anchor-strip__score">
          <span class="eyebrow eyebrow--sm">{{ t('farm_tab.anchor_farm') }}</span>
          <span class="anchor-strip__val" :style="{ color: farmColor(result.anchor.FARM_SCORE) }">
            {{ result.anchor.FARM_SCORE?.toFixed(1) }}
          </span>
        </div>
      </div>

      <div class="sub-head">
        <v-icon size="14" class="t-dim">mdi-view-list-outline</v-icon>
        <span class="eyebrow eyebrow--primary">{{ t('farm_tab.main_set') }}</span>
        <span class="t-faint sub-head__range">BR {{ fmtBR(targetBr - 1.0) }} – {{ fmtBR(targetBr) }}</span>
      </div>

      <div class="table-wrap mb-6">
        <v-data-table
          :headers="farmHeaders"
          :items="mainSetRows"
          :items-per-page="-1"
          hide-default-footer
          density="compact"
          class="wt-table"
          :row-props="rowProps"
          @click:row="(_, { item }) => openVehicle(item)"
        >
          <template #item.role="{ item }">
            <span class="tag tint" :style="{ '--c': roleColor(item._roleKey) }">{{ item.role }}</span>
          </template>
          <template #item.Name_Display="{ item }">
            <span class="cell-name">
              <v-icon v-if="item.classIcon" size="13" class="cell-class-icon" :style="item.classColor ? { color: item.classColor } : null">{{ item.classIcon }}</v-icon>{{ item.Name_Display }}
            </span>
          </template>
          <template #item.BR="{ item }">
            <span class="t-muted fw-600">{{ fmtBR(item.BR) }}</span>
          </template>
          <template #item.FARM_SCORE="{ item }">
            <div class="farm-cell">
              <span class="cell-score" :style="{ color: farmColor(item.FARM_SCORE) }">{{ item.FARM_SCORE?.toFixed(1) }}</span>
              <div class="farm-bar">
                <div class="farm-bar__fill" :style="{ width: Math.min(item.FARM_SCORE, 100) + '%', background: farmColor(item.FARM_SCORE) }" />
              </div>
            </div>
          </template>
          <template #item.net_sl="{ item }">
            <span class="fw-600" style="color:var(--c-ok)">{{ item.net_sl != null ? item.net_sl.toLocaleString() : '—' }}</span>
          </template>
        </v-data-table>
      </div>

      <div class="sub-head">
        <v-icon size="14" style="color:var(--c-violet)">mdi-diamond-stone</v-icon>
        <span class="eyebrow" style="color:var(--c-violet)">{{ t('farm_tab.gems') }}</span>
        <span class="t-faint sub-head__range">BR {{ fmtBR(targetBr - 2.0) }} – {{ fmtBR(targetBr - 1.0) }}</span>
      </div>

      <div v-if="gemRows.length" class="table-wrap">
        <v-data-table
          :headers="gemHeaders"
          :items="gemRows"
          :items-per-page="-1"
          hide-default-footer
          density="compact"
          class="wt-table"
          :row-props="rowProps"
          @click:row="(_, { item }) => openVehicle(item)"
        >
          <template #item.Name_Display="{ item }">
            <span class="cell-name">
              <v-icon v-if="item.classIcon" size="13" class="cell-class-icon" :style="item.classColor ? { color: item.classColor } : null">{{ item.classIcon }}</v-icon>{{ item.Name_Display }}
            </span>
          </template>
          <template #item.BR="{ item }">
            <span class="t-muted fw-600">{{ fmtBR(item.BR) }}</span>
          </template>
          <template #item.FARM_SCORE="{ item }">
            <div class="farm-cell">
              <span class="cell-score" :style="{ color: farmColor(item.FARM_SCORE) }">{{ item.FARM_SCORE?.toFixed(1) }}</span>
              <div class="farm-bar">
                <div class="farm-bar__fill" :style="{ width: Math.min(item.FARM_SCORE, 100) + '%', background: farmColor(item.FARM_SCORE) }" />
              </div>
            </div>
          </template>
          <template #item.delta="{ item }">
            <span class="fw-600" style="color:var(--c-violet)">+{{ item.delta }}%</span>
          </template>
        </v-data-table>
      </div>
      <div v-else class="panel no-data">{{ t('farm_tab.gems_empty') }}</div>

    </template>

  </div>
</template>

<script setup>
import { ref, shallowRef, computed, watchEffect, nextTick, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTabFilters }   from '../composables/useTabFilters.js'
import { useDataStore, WT_BR_STEPS } from '../stores/useDataStore.js'
import {
  vehicleDisplayName, vehicleClassMdiIcon, vehicleClassMdiColor,
  farmColor, fmtBR, fmtNation, normRow,
} from '../composables/useVehicleFormatting.js'
import InfoTip from '../components/InfoTip.vue'

const { t }       = useI18n()
const store       = useDataStore()
const openVehicle = inject('openVehicle')

useTabFilters()

const DEFAULT_BR = 7.0
const brIndex    = ref(Math.max(0, WT_BR_STEPS.indexOf(DEFAULT_BR)))
const targetBr   = computed(() => WT_BR_STEPS[brIndex.value])

const nation = ref('All')
const nationItems = computed(() =>
  (store.nations ?? []).map(n => ({
    title: n === 'All' ? t('common.all') : fmtNation(n),
    value: n,
  }))
)

const ROLE_PRIMARY   = 'primary'
const ROLE_CANDIDATE = 'candidate'
const ROLE_RESERVE   = 'reserve'

const farmOf = v => v.FARM_SCORE ?? 0
const byFarmDesc = (a, b) => farmOf(b) - farmOf(a)

function buildFarmSet(vehicles, tBr, nat) {
  const df = nat === 'All' ? vehicles : vehicles.filter(v => v.Nation === nat)

  let anchor = null
  for (const v of df) {
    if (Math.abs(v.BR - tBr) <= 0.15 && (!anchor || farmOf(v) > farmOf(anchor))) anchor = v
  }
  if (!anchor) return null

  const anchorFarm = farmOf(anchor)

  const mainSet = df
    .filter(v => v.BR >= tBr - 1.0 && v.BR <= tBr + 0.15)
    .sort(byFarmDesc)
    .slice(0, 7)
    .map(v => ({
      ...v,
      _roleKey: Math.abs(v.BR - tBr) <= 0.15
        ? ROLE_PRIMARY
        : farmOf(v) >= anchorFarm * 0.9
          ? ROLE_CANDIDATE
          : ROLE_RESERVE,
    }))

  const gems = df
    .filter(v => v.BR >= tBr - 2.0 && v.BR < tBr - 0.85 && farmOf(v) > anchorFarm)
    .sort(byFarmDesc)
    .slice(0, 5)
    .map(v => ({
      ...v,
      _delta: anchorFarm > 0
        ? Math.round(((v.FARM_SCORE - anchorFarm) / anchorFarm) * 100)
        : 0,
    }))

  return { anchor, mainSet, gems }
}

function roleLabel(key) {
  if (key === ROLE_PRIMARY)   return t('farm_tab.role_primary')
  if (key === ROLE_CANDIDATE) return t('farm_tab.role_candidate')
  return t('farm_tab.role_reserve')
}

function roleColor(key) {
  if (key === ROLE_PRIMARY)   return 'var(--primary)'
  if (key === ROLE_CANDIDATE) return 'var(--c-info)'
  return 'var(--ink-faint)'
}

function toRows(list) {
  return list.map(v => ({
    ...normRow(v),
    Name_Display: vehicleDisplayName(v),
    classIcon:    vehicleClassMdiIcon(v),
    classColor:   vehicleClassMdiColor(v),
    delta:        v._delta ?? 0,
    _roleKey:     v._roleKey ?? ROLE_RESERVE,
    role:         roleLabel(v._roleKey ?? ROLE_RESERVE),
  }))
}

const result      = shallowRef(null)
const noAnchor    = shallowRef(false)
const mainSetRows = shallowRef([])
const gemRows     = shallowRef([])

watchEffect(() => {
  const vehicles = store.filteredVehicles
  const tBr      = targetBr.value
  const nat      = nation.value
  nextTick(() => {
    const r           = buildFarmSet(vehicles, tBr, nat)
    result.value      = r
    noAnchor.value    = !r
    mainSetRows.value = toRows(r?.mainSet ?? [])
    gemRows.value     = toRows(r?.gems    ?? [])
  })
})

const anchorClassIcon  = computed(() => result.value ? vehicleClassMdiIcon(result.value.anchor)  : null)
const anchorClassColor = computed(() => result.value ? vehicleClassMdiColor(result.value.anchor) : null)

const rowProps = ({ index }) => ({ class: index % 2 === 0 ? 'row-even' : 'row-odd' })

const farmHeaders = computed(() => [
  { title: t('farm_tab.role'),        key: 'role',         width: 110, sortable: false },
  { title: t('farm_tab.col_vehicle'), key: 'Name_Display', sortable: false },
  { title: t('common.br'),            key: 'BR',           width: 65  },
  { title: t('common.battles'),       key: 'battles',      width: 80  },
  { title: t('common.wr'),            key: 'WR',           width: 65  },
  { title: t('farm_tab.col_farm'),    key: 'FARM_SCORE',   width: 130 },
  { title: t('farm_tab.col_net_sl'),  key: 'net_sl',       width: 110 },
])

const gemHeaders = computed(() => [
  { title: t('farm_tab.col_vehicle'), key: 'Name_Display', sortable: false },
  { title: t('common.br'),            key: 'BR',           width: 65  },
  { title: t('common.battles'),       key: 'battles',      width: 80  },
  { title: t('farm_tab.col_farm'),    key: 'FARM_SCORE',   width: 130 },
  { title: t('farm_tab.delta_vs'),    key: 'delta',        width: 90  },
])
</script>

<style scoped>
.fw-600 { font-weight: 600; }

.br-ctrl        { flex: 1; min-width: 180px; max-width: 300px; }
.br-ctrl-inner  { display: flex; align-items: center; gap: 10px; }
.br-badge {
  flex-shrink: 0;
  min-width: 44px;
  text-align: right;
  font: 600 22px/1 var(--font-display);
  font-variant-numeric: tabular-nums;
  color: var(--primary);
}
.br-slider :deep(.v-slider-thumb__label) { display: none; }
.br-slider :deep(.v-slider-track__fill)  { border-radius: 0; }
.br-slider :deep(.v-slider-track__background) { opacity: 1; }

.anchor-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
  border-left: 2px solid var(--primary);
}
.anchor-strip__main  { display: flex; align-items: baseline; flex-wrap: wrap; gap: 12px; }
.anchor-strip__name  { font: 600 16px var(--font-display); color: var(--ink); }
.anchor-strip__score { display: flex; align-items: baseline; gap: 10px; flex-shrink: 0; }
.anchor-strip__val   { font: 600 24px/1 var(--font-display); font-variant-numeric: tabular-nums; }

.sub-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.sub-head__range { margin-left: auto; font: 11px var(--font-display); }

.farm-cell { display: flex; flex-direction: column; gap: 3px; min-width: 80px; padding: 4px 0; }
.farm-bar  { height: 2px; background: var(--hairline); }
.farm-bar__fill { height: 100%; transition: width 0.2s; }
</style>
