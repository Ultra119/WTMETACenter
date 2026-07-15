<template>
  <v-card class="stats-card" color="#0f172a" style="border: 1px solid #1e3a5f;">
    <div class="stats-card__head">
      <div class="d-flex align-center">
        <v-icon icon="mdi-chart-line" size="14" style="opacity:.7" class="mr-2" />
        <span class="stats-card__title">{{ t('vehicle_card.stats') }}</span>
      </div>
      <span v-if="activePeriodLabel" class="stats-card__period">{{ activePeriodLabel }}</span>
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
        <div
          v-for="m in metrics"
          :key="m.key"
          class="metric-block"
          :style="{ borderLeft: `2px solid ${m.color}` }"
        >
          <div class="metric-block__head">
            <v-icon :icon="m.icon" size="13" style="opacity:.65" />
            <span class="metric-block__label">{{ m.label }}</span>
            <span
              class="metric-block__delta"
              :class="m.delta >= 0 ? 'is-up' : 'is-down'"
            >
              <v-icon size="9">{{ m.delta >= 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>{{ m.deltaFmt }}
            </span>
          </div>

          <div class="metric-block__row">
            <span class="metric-block__val" :style="{ color: m.color }">{{ m.valueFmt }}</span>

            <div
              class="spark-wrap"
              @mousemove="e => onChartHover(e, m)"
              @mouseleave="onHover(null)"
            >
              <span class="spark-label spark-label--max">{{ m.maxFmt }}</span>
              <span class="spark-label spark-label--min">{{ m.minFmt }}</span>

              <svg class="spark-svg" :viewBox="`0 0 ${SPARK_W} ${SPARK_H}`" preserveAspectRatio="none">
                <defs>
                  <linearGradient :id="`spark-grad-${m.key}`" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   :stop-color="m.color" stop-opacity="0.30" />
                    <stop offset="100%" :stop-color="m.color" stop-opacity="0.02" />
                  </linearGradient>
                </defs>
                <path :d="m.areaPath" :fill="`url(#spark-grad-${m.key})`" stroke="none" />
                <path :d="m.linePath" fill="none" :stroke="m.color" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke" />
                <line
                  :x1="m.markerX" y1="0" :x2="m.markerX" :y2="SPARK_H"
                  stroke="rgba(148,163,184,0.30)" stroke-width="1" stroke-dasharray="2,2" vector-effect="non-scaling-stroke"
                />
                <circle :cx="m.markerX" :cy="m.markerY" r="3.5" :fill="m.color" stroke="#0f172a" stroke-width="1.5" vector-effect="non-scaling-stroke" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  </v-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
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

const hoveredIdx = ref(null)

async function load() {
  if (!props.vehicle?.Name) { points.value = []; return }
  loading.value = true
  error.value = null
  hoveredIdx.value = null
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

function onHover(idx) { hoveredIdx.value = idx }

const SPARK_W = 300
const SPARK_H = 64
const PAD_X = 8
const PAD_Y = 8

function onChartHover(evt, m) {
  const rect = evt.currentTarget.getBoundingClientRect()
  const relX = (evt.clientX - rect.left) / rect.width
  const svgX = relX * SPARK_W
  const len  = m.values.length
  const stepX = (SPARK_W - 2 * PAD_X) / Math.max(len - 1, 1)
  let idx = Math.round((svgX - PAD_X) / stepX)
  idx = Math.max(0, Math.min(len - 1, idx))
  hoveredIdx.value = idx
}

function hexToRgba(hex, a) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r},${g},${b},${a})`
}

const METRIC_DEFS = [
  { key: 'meta',    labelKey: 'common.meta',    icon: 'mdi-trophy-outline', colorFn: metaColor, fmt: v => v.toFixed(1),                  unit: ''  },
  { key: 'wr',      labelKey: 'common.wr',      icon: 'mdi-target',        colorFn: wrColor,   fmt: v => v.toFixed(1),                  unit: '%' },
  { key: 'farm',    labelKey: 'common.farm',    icon: 'mdi-cash-multiple', colorFn: farmColor, fmt: v => v.toFixed(1),                  unit: ''  },
  { key: 'battles', labelKey: 'common.battles', icon: 'mdi-sword-cross',   colorFn: null,      fmt: v => Math.round(v).toLocaleString(), unit: ''  },
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

    const idx       = hoveredIdx.value
    const activeIdx = (idx != null && series[idx]) ? idx : series.length - 1
    const activeVal = series[activeIdx].value
    const activeLbl = series[activeIdx].label

    const color = def.colorFn ? def.colorFn(activeVal) : '#7dd3fc'

    const minV = Math.min(...values)
    const maxV = Math.max(...values)
    const range = (maxV - minV) || 1

    const stepX = (SPARK_W - 2 * PAD_X) / Math.max(values.length - 1, 1)
    const pts = values.map((v, i) => ({
      x: PAD_X + i * stepX,
      y: SPARK_H - PAD_Y - ((v - minV) / range) * (SPARK_H - 2 * PAD_Y),
    }))

    const linePath = 'M ' + pts.map(p => `${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' L ')
    const lastPt   = pts[pts.length - 1]
    const areaPath = `${linePath} L ${lastPt.x.toFixed(1)} ${SPARK_H} L ${pts[0].x.toFixed(1)} ${SPARK_H} Z`

    return {
      key:         def.key,
      label:       t(def.labelKey),
      icon:        def.icon,
      values,
      color,
      delta,
      deltaFmt:    def.fmt(Math.abs(delta)) + def.unit,
      valueFmt:    def.fmt(activeVal) + def.unit,
      minFmt:      def.fmt(minV) + def.unit,
      maxFmt:      def.fmt(maxV) + def.unit,
      periodLabel: activeLbl,
      linePath,
      areaPath,
      markerX:     pts[activeIdx].x,
      markerY:     pts[activeIdx].y,
    }
  }).filter(Boolean)
})

const activePeriodLabel = computed(() => metrics.value[0]?.periodLabel ?? null)
</script>

<style scoped>
.stats-card { padding: 14px 16px; height: 100%; display: flex; flex-direction: column; }

.stats-card__head { display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
.stats-card__title { font-size: 12px; font-weight: 700; letter-spacing: .1em; color: #a7f3d0; text-transform: uppercase; }
.stats-card__period { font-size: 10px; color: #7dd3fc; font-family: 'JetBrains Mono', monospace; letter-spacing: .04em; }
.stats-card__sub { font-size: 11px; color: #a8b3c4; font-family: 'JetBrains Mono', monospace; margin-top: 2px; flex-shrink: 0; }

.stats-card__body { flex: 1 1 auto; min-height: 0; overflow: hidden; }

.stats-state {
  display: flex; align-items: center; justify-content: center;
  padding: 28px 8px; font-size: 12px; color: #a8b3c4;
}
.stats-state--error { color: #f87171; }

.metric-block { height: 96px; padding-left: 12px; margin-bottom: 14px; }
.metric-block:last-child { margin-bottom: 0; }

.metric-block__head { display: flex; align-items: center; gap: 4px; height: 16px; }
.metric-block__label { font-size: 10px; font-weight: 700; letter-spacing: .1em; color: #94a3b8; text-transform: uppercase; }
.metric-block__delta { margin-left: 2px; font-size: 10px; font-weight: 600; display: inline-flex; align-items: center; gap: 1px; }
.metric-block__delta.is-up   { color: #34d399; }
.metric-block__delta.is-down { color: #f87171; }

.metric-block__row { display: flex; align-items: center; gap: 10px; height: 64px; margin-top: 6px; }
.metric-block__val {
  flex: 0 0 76px;
  width: 76px;
  font-size: 21px;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1;
  white-space: nowrap;
}

.spark-wrap { position: relative; flex: 1 1 auto; height: 64px; cursor: crosshair; }
.spark-svg  { width: 100%; height: 100%; display: block; }

.spark-label {
  position: absolute; right: 2px;
  font-size: 9px; color: #64748b;
  font-family: 'JetBrains Mono', monospace;
  pointer-events: none; z-index: 1;
}
.spark-label--max { top: 0; }
.spark-label--min { bottom: 0; }

@media (max-width: 420px) {
  .metric-block__val { font-size: 17px; flex-basis: 60px; width: 60px; }
}
</style>
