<template>
  <div class="month" :class="{ 'month--launch': launch }">
    <div class="month-hdr">
      <span class="month-date" :class="{ 'month-date--launch': launch }">
        {{ launch ? group.label : group.monthLabel }}
      </span>
      <span v-if="group.subtitle" class="month-sub">{{ group.subtitle }}</span>

      <span class="month-types">
        <span v-for="item in typeSummary" :key="item.cat" class="month-type">
          <v-icon size="12" :style="{ color: CATEGORY_COLOR[item.cat] }">{{ CATEGORY_ICON[item.cat] }}</v-icon>
          {{ item.count }}
        </span>
      </span>

      <span class="month-line" />
      <span class="month-count">{{ group.vehicles.length }}</span>
    </div>

    <div class="grid-outer" :class="{ 'grid-outer--collapsed': collapsed }">
      <div class="grid-inner" :inert="collapsed ? '' : undefined">
        <div class="grid">
          <div
            v-for="v in group.vehicles"
            :key="v._dedup_key"
            class="veh-row"
            :class="{ 'veh-row--limited': isLimited(v) }"
            tabindex="0"
            role="button"
            @click="emit('open', v)"
            @keydown.enter="emit('open', v)"
          >
            <span class="veh-flag" :title="v.Nation">{{ NATION_FLAG[v.Nation?.toLowerCase()] ?? '🏴' }}</span>
            <v-icon
              size="13"
              class="veh-type-icon"
              :style="{ color: TYPE_BRANCH_COLOR[v.Type] ?? 'var(--ink-dim)' }"
              :title="fmtType(v.Type)"
            >{{ TYPE_ICON[v.Type] ?? 'mdi-help-circle-outline' }}</v-icon>
            <span class="veh-name" v-html="highlightName(v.Name)" />
            <span class="veh-right">
              <span
                v-if="v.VehicleClass !== 'Standard'"
                class="class-chip"
                :style="classChipStyle(v.VehicleClass)"
              >
                <v-icon v-if="CLASS_PREFIX[v.VehicleClass]" size="9" class="mr-1">{{ CLASS_PREFIX[v.VehicleClass] }}</v-icon>{{ t(`vehicle_classes.${v.VehicleClass}`) }}
              </span>
              <span class="veh-br">{{ fmtBR(v.vdb_realistic_br ?? v.BR) }}</span>
            </span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="collapsible" class="more-row">
      <button type="button" class="ui-btn ui-btn--sm" @click="emit('toggle')">
        <v-icon size="14">{{ expanded ? 'mdi-chevron-double-up' : 'mdi-chevron-double-down' }}</v-icon>
        {{ expanded ? t('history_tab.collapse') : t('history_tab.show_all', { n: group.vehicles.length }) }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NATION_FLAG, fmtType, fmtBR, CLASS_PREFIX, classChipStyle } from '../composables/useVehicleFormatting.js'
import { TYPE_ICON, TYPE_BRANCH_COLOR } from '../composables/constants.js'

const props = defineProps({
  group:    { type: Object,  required: true },
  expanded: Boolean,
  launch:   Boolean,
  query:    { type: String, default: '' },
  preview:  { type: Number, default: 6 },
})
const emit = defineEmits(['toggle', 'open'])
const { t } = useI18n()

const collapsible = computed(() => props.launch || props.group.vehicles.length > props.preview)
const collapsed   = computed(() => collapsible.value && !props.expanded)

const CATEGORY_ICON  = { Ground: 'mdi-tank', Aviation: 'mdi-airplane', Helicopters: 'mdi-helicopter', Fleet: 'mdi-ferry' }
const CATEGORY_COLOR = { Ground: 'var(--primary)', Aviation: 'var(--c-info)', Helicopters: 'var(--c-violet)', Fleet: 'var(--c-warn)' }
const CAT_ORDER = ['Ground', 'Aviation', 'Helicopters', 'Fleet']
const TYPE_TO_CAT = {
  medium_tank: 'Ground', light_tank: 'Ground', heavy_tank: 'Ground',
  tank_destroyer: 'Ground', spaa: 'Ground',
  fighter: 'Aviation', bomber: 'Aviation', assault: 'Aviation',
  attack_helicopter: 'Helicopters', utility_helicopter: 'Helicopters',
  destroyer: 'Fleet', heavy_cruiser: 'Fleet', light_cruiser: 'Fleet',
  battleship: 'Fleet', battlecruiser: 'Fleet',
  boat: 'Fleet', heavy_boat: 'Fleet', frigate: 'Fleet', barge: 'Fleet',
}

const typeSummary = computed(() => {
  const counts = {}
  for (const v of props.group.vehicles) {
    const cat = TYPE_TO_CAT[v.Type]
    if (cat) counts[cat] = (counts[cat] ?? 0) + 1
  }
  return CAT_ORDER.filter(c => counts[c]).map(c => ({ cat: c, count: counts[c] }))
})

const isLimited = v => v.vdb_shop_is_event || v.vdb_shop_is_gift

const hlRe = computed(() => {
  const q = props.query.trim()
  return q ? new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi') : null
})
const escapeHtml = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

function highlightName(name) {
  const safe = escapeHtml(name ?? '')
  return hlRe.value ? safe.replace(hlRe.value, '<mark class="hl">$1</mark>') : safe
}
</script>

<style scoped>
.month { display: flex; flex-direction: column; padding: 2px 0 8px; }
.month--launch { margin-top: 8px; padding-top: 6px; border-top: 1px solid var(--hairline); }

.month-hdr { display: flex; align-items: center; gap: 10px; padding: 4px 2px; user-select: none; }
.month-date {
  flex-shrink: 0;
  font: 600 11px var(--font-display);
  letter-spacing: 0.08em;
  color: var(--ink-muted);
}
.month-date--launch { color: var(--c-warn); }
.month-sub   { font-size: 11px; font-style: italic; color: var(--ink-faint); }
.month-types { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.month-type  { display: flex; align-items: center; gap: 3px; font: 600 10px/1 var(--font-display); color: var(--ink-faint); }
.month-line  { flex: 1; height: 1px; background: var(--hairline); }
.month-count { flex-shrink: 0; font: 600 10px var(--font-display); color: var(--ink-faint); font-variant-numeric: tabular-nums; }

.grid-outer { display: grid; grid-template-rows: 1fr; transition: grid-template-rows 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.grid-outer--collapsed { grid-template-rows: 0fr; }
.grid-inner { min-height: 0; overflow: hidden; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 4px;
  padding-bottom: 2px;
}

.veh-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 5px 8px;
  border: 1px solid var(--hairline);
  cursor: pointer;
  contain: layout style;
  transition: background 0.12s, border-color 0.12s;
}
.veh-row:hover { background: var(--primary-soft); border-color: var(--primary-line); }
.veh-row:focus-visible { outline: 2px solid var(--primary); outline-offset: 1px; }

.veh-row--limited { border-left: 2px solid var(--c-warn); }
.veh-row--limited:hover {
  background: color-mix(in srgb, var(--c-warn) 8%, transparent);
  border-color: color-mix(in srgb, var(--c-warn) 45%, transparent);
}

.veh-flag      { flex-shrink: 0; font-size: 14px; line-height: 1; }
.veh-type-icon { flex-shrink: 0; opacity: 0.9; }
.veh-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font: 500 12px var(--font-display);
  color: var(--ink-muted);
}
.veh-row:hover .veh-name { color: var(--ink); }
.veh-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.veh-br {
  min-width: 28px;
  text-align: right;
  font: 600 11px var(--font-display);
  font-variant-numeric: tabular-nums;
  color: var(--ink-faint);
}

.more-row { padding: 4px 0 2px; }

:deep(.hl) {
  padding: 0 1px;
  background: color-mix(in srgb, var(--c-warn) 28%, transparent);
  color: var(--ink);
}
</style>
