<template>
  <v-card class="stats-card" color="#0f172a" style="border: 1px solid #1e3a5f;">
    <div class="stats-card__head">
      <v-icon icon="mdi-chart-line" size="14" style="opacity:.7" class="mr-2" />
      <span class="stats-card__title">{{ t('vehicle_card.stats') }}</span>
    </div>
    <div class="stats-card__sub">{{ vehicleName }}</div>

    <v-divider color="#1e293b" class="my-3" />

    <div class="stats-card__body">
      <div v-if="loading" class="stats-state">
        <v-progress-circular indeterminate size="20" width="2" color="#38bdf8" class="mr-2" />
        {{ t('common.loading') }}
      </div>

      <div v-else-if="error" class="stats-state stats-state--error">
        {{ t('common.error_load', { msg: error }) }}
      </div>

      <div v-else-if="metrics.length === 0" class="stats-state">
        {{ t('vehicle_card.history_empty') }}
      </div>

      <div v-else class="metrics-wrap">
        <div v-for="m in metrics" :key="m.key" class="metric-block">
          <div class="d-flex align-center ga-1 mb-1">
            <v-icon :icon="m.icon" size="13" style="opacity:.65" />
            <span class="metric-block__label">{{ m.label }}</span>
            <span
              v-if="m.delta != null"
              class="metric-block__delta"
              :class="m.delta >= 0 ? 'is-up' : 'is-down'"
            >
              <v-icon size="9">{{ m.delta >= 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>{{ m.deltaFmt }}
            </span>
            <v-spacer />
            <span class="metric-block__period">{{ m.periodLabel }}</span>
          </div>

          <div class="d-flex align-end ga-3">
            <span class="metric-block__val" :style="{ color: m.color }">{{ m.valueFmt }}</span>
            <v-sparkline
              :model-value="m.values"
              :gradient="m.gradient"
              :color="m.color"
              height="46"
              line-width="1.5"
              marker-size="7"
              marker-stroke="#0f172a"
              smooth="2"
              padding="6"
              style="flex:1"
              fill
              interactive
              @update:current-index="i => onHover(m.key, i)"
            />
          </div>
        </div>
      </div>
    </div>
  </v-card>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import {
  vehicleDisplayName, metaColor, farmColor, wrColor,
} from '../composables/useVehicleFormatting.js'

const { t } = useI18n()
const store = useDataStore()

const props = defineProps({
  vehicle: { type: Object, default: null },
  mode:    { type: String, default: 'Realistic' },
})

const vehicleName = computed(() => vehicleDisplayName(props.vehicle))

const points  = ref([])
const loading = ref(false)
const error   = ref(null)

const hoveredIdx = reactive({ meta: null, farm: null, wr: null, battles: null })

async function load() {
  if (!props.vehicle?.Name) { points.value = []; return }
  loading.value = true
  error.value = null
  Object.keys(hoveredIdx).forEach(k => { hoveredIdx[k] = null })
  try {
    points.value = await store.fetchVehicleHistory({
      name:   props.vehicle.Name,
      nation: props.vehicle.Nation,
      type:   props.vehicle.Type,
      mode:   props.mode,
    })
  } catch (e) {
    error.value = e.message
    points.value = []
  } finally {
    loading.value = false
  }
}

watch(() => [props.vehicle?.Name, props.vehicle?.Nation, props.vehicle?.Type, props.mode], load, { immediate: true })

function onHover(key, idx) { hoveredIdx[key] = idx }

function hexToRgba(hex, a) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${a})`
}

const METRIC_DEFS = [
  { key: 'meta',    labelKey: 'common.meta',    icon: 'mdi-trophy-outline',  colorFn: metaColor, fmt: v => v.toFixed(1),                 unit: ''  },
  { key: 'farm',    labelKey: 'common.farm',    icon: 'mdi-cash-multiple',   colorFn: farmColor, fmt: v => v.toFixed(1),                 unit: ''  },
  { key: 'wr',      labelKey: 'common.wr',      icon: 'mdi-target',          colorFn: wrColor,   fmt: v => v.toFixed(1),                 unit: '%' },
  { key: 'battles', labelKey: 'common.battles', icon: 'mdi-sword-cross',     colorFn: null,      fmt: v => Math.round(v).toLocaleString(), unit: ''  },
]

const metrics = computed(() => {
  if (points.value.length < 2) return []

  return METRIC_DEFS.map(def => {
    const series = points.value
      .map(p => ({ label: p.label, value: p[def.key] }))
      .filter(s => s.value != null && !isNaN(s.value))

    if (series.length < 2) return null

    const values = series.map(s => s.value)
    const first  = values[0]
    const last   = values[values.length - 1]
    const delta  = last - first

    const idx       = hoveredIdx[def.key]
    const activeIdx = (idx != null && series[idx]) ? idx : series.length - 1
    const activeVal = series[activeIdx].value
    const activeLbl = series[activeIdx].label

    const color = def.colorFn ? def.colorFn(activeVal) : '#7dd3fc'

    return {
      key:         def.key,
      label:       t(def.labelKey),
      icon:        def.icon,
      values,
      color,
      gradient:    [hexToRgba(color, 0.30), hexToRgba(color, 0.02)],
      delta,
      deltaFmt:    def.fmt(Math.abs(delta)) + def.unit,
      valueFmt:    def.fmt(activeVal) + def.unit,
      periodLabel: activeLbl,
    }
  }).filter(Boolean)
})
</script>

<style scoped>
.stats-card { padding: 14px 16px; }

.stats-card__head { display: flex; align-items: center; }
.stats-card__title { font-size: 12px; font-weight: 700; letter-spacing: .1em; color: #a7f3d0; text-transform: uppercase; }
.stats-card__sub { font-size: 11px; color: #a8b3c4; font-family: 'JetBrains Mono', monospace; margin-top: 2px; }

.stats-state {
  display: flex; align-items: center; justify-content: center;
  padding: 28px 8px; font-size: 12px; color: #a8b3c4;
}
.stats-state--error { color: #f87171; }

.metric-block { margin-bottom: 18px; }
.metric-block:last-child { margin-bottom: 0; }

.metric-block__label { font-size: 10px; font-weight: 700; letter-spacing: .1em; color: #94a3b8; text-transform: uppercase; }
.metric-block__delta { margin-left: 6px; font-size: 10px; font-weight: 600; display: inline-flex; align-items: center; gap: 1px; }
.metric-block__delta.is-up   { color: #34d399; }
.metric-block__delta.is-down { color: #f87171; }
.metric-block__period { font-size: 10px; color: #a8b3c4; font-family: 'JetBrains Mono', monospace; }

.metric-block__val {
  font-size: 18px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  min-width: 58px;
  line-height: 1.1;
}
</style>
