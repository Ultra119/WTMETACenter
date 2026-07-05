<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="1100" scrollable>
    <div class="card-shell">
      <v-card v-if="vehicle" class="main-card" color="#0f172a" style="border: 1px solid #1e3a5f;">

      <v-card-title class="card-header">
        <span class="vehicle-name">{{ displayName }}</span>
        <span v-if="vehicle.VehicleClass !== 'Standard'" class="class-chip ml-2" :style="classChipStyle(vehicle.VehicleClass)">
          <span v-if="CLASS_PREFIX[vehicle.VehicleClass]" class="mdi" :class="CLASS_PREFIX[vehicle.VehicleClass]" style="font-size:9px; margin-right:2px;" />
          {{ t(`vehicle_classes.${vehicle.VehicleClass}`) }}
        </span>
        <span v-if="vehicle.vdb_shop_rank" class="rank-badge ml-1">
          <span class="mdi mdi-medal-outline" style="font-size:10px; margin-right:3px;" />
          {{ t('vehicle_card.era') }} {{ vehicle.vdb_shop_rank }}
        </span>
        <v-spacer />

        <button
          type="button"
          class="stats-toggle"
          :class="{ 'stats-toggle--active': showStatsPanel }"
          :title="t('vehicle_card.stats')"
          @click="showStatsPanel = !showStatsPanel"
        >
          <span class="mdi mdi-chart-line" style="font-size:13px;" />
        </button>

        <div class="br-modes">
          <span
            v-for="m in BR_MODES"
            :key="m.key"
            class="br-pill"
            :class="{ 'br-pill--active': m.key === activeMode }"
            :title="t(`vehicle_card.${m.titleKey}`)"
            @click="activeMode = m.key"
          >
            <span class="br-pill__mode">{{ m.short }}</span>
            <span class="br-pill__val">{{ brByMode[m.key] ?? '—' }}</span>
          </span>
        </div>

        <v-btn icon="mdi-close" variant="text" size="small" :title="t('common.close')" @click="$emit('update:modelValue', false)" />
      </v-card-title>

      <v-divider color="#1e293b" />

      <v-card-text class="pa-0">

        <div class="info-band">
          <div class="img-pane">
            <VehicleImage :name="displayName" :identifier="vehicle.vdb_identifier" :type="vehicle.Type" aspect="2/1" fit="cover" />
          </div>
          <div class="meta-pane">
            <div class="meta-row">
              <span class="meta-lbl">{{ t('vehicle_card.nation') }}</span>
              <span class="meta-val">{{ fmtNation(vehicle.Nation) }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-lbl">{{ t('vehicle_card.type') }}</span>
              <span class="meta-val">{{ fmtType(vehicle.Type) }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-lbl">{{ t('vehicle_card.battles') }}</span>
              <span class="meta-val">{{ (modeVehicle['Сыграно игр'] ?? 0).toLocaleString() }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-lbl">{{ t('vehicle_card.wr') }}</span>
              <span class="meta-val" :style="{ color: wrColor(modeVehicle.WR) }">{{ modeVehicle.WR?.toFixed(1) }}%</span>
            </div>
            <div v-for="row in kdBreakdown" :key="row.key" class="meta-row">
              <span class="meta-lbl">{{ t(row.labelKey) }}</span>
              <span class="meta-val">{{ row.value.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <div class="card-grid">

          <div class="card-section">
            <div class="section-title">
              <v-icon size="12" style="margin-right:4px;opacity:.7">mdi-trophy</v-icon>
              {{ t('vehicle_card.scores') }}
              <span class="scores-mode">{{ activeModePill }}</span>
            </div>

            <div class="score-row">
              <span class="score-label">{{ t('vehicle_card.meta_score') }}</span>
              <div class="score-bar-wrap">
                <span class="score-val" :style="{ color: metaColor(activeScores.meta) }">
                  {{ activeScores.meta != null ? activeScores.meta.toFixed(1) : '—' }}
                </span>
                <div class="score-track">
                  <div
                    class="score-bar"
                    :style="{
                      width: (activeScores.meta ?? 0) + '%',
                      background: metaColor(activeScores.meta),
                    }"
                  />
                </div>
              </div>
            </div>
            <div class="score-row">
              <span class="score-label">{{ t('vehicle_card.farm_score') }}</span>
              <div class="score-bar-wrap">
                <span class="score-val" :style="{ color: farmColor(activeScores.farm) }">
                  {{ activeScores.farm != null ? activeScores.farm.toFixed(1) : '—' }}
                </span>
                <div class="score-track">
                  <div
                    class="score-bar"
                    :style="{
                      width: (activeScores.farm ?? 0) + '%',
                      background: farmColor(activeScores.farm),
                    }"
                  />
                </div>
              </div>
            </div>
            <div class="stat-row mt-2">
              <span class="stat-label">{{ t('vehicle_card.net_sl') }}</span>
              <span class="stat-value" style="color: #34d399;">{{ fmtSL(modeVehicle['Net SL за игру']) }}</span>
            </div>
          </div>

          <div class="card-section">
            <template v-if="hasVdb">
              <div class="section-title"><v-icon size="12" style="margin-right:4px;opacity:.7">mdi-cog</v-icon>{{ t('vehicle_card.mobility') }}</div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.speed_rb') }}</span>
                <span class="stat-value">{{ v('vdb_engine_max_speed_rb') }} {{ t('vehicle_card.speed_unit') }}</span>
              </div>
              <div v-if="showReverseSpeed" class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.reverse_rb') }}</span>
                <span class="stat-value">{{ v('vdb_engine_reverse_rb') }} {{ t('vehicle_card.speed_unit') }}</span>
              </div>
              <div v-if="showHp" class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.hp_rb') }}</span>
                <span class="stat-value">{{ v('vdb_engine_hp_rb') }} {{ t('vehicle_card.hp_unit') }}</span>
              </div>
              <div class="section-title" style="margin-top:10px"><v-icon size="12" style="margin-right:4px;opacity:.7">mdi-cash</v-icon>{{ t('vehicle_card.economy') }}</div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.repair_rb') }}</span>
                <span class="stat-value">{{ fmtSL(vehicle.vdb_repair_cost_realistic) }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.sl_per_game') }}</span>
                <span class="stat-value" style="color: #34d399;">{{ fmtSL(modeVehicle['SL за игру']) }}</span>
              </div>
            </template>
          </div>

          <template v-if="hasVdb">
            <div v-if="showArmor" class="card-section">
              <div class="section-title"><v-icon size="12" style="margin-right:4px;opacity:.7">mdi-shield</v-icon>{{ t('vehicle_card.armor') }}</div>
              <table class="armor-table">
                <thead>
                  <tr>
                    <th></th>
                    <th>{{ t('vehicle_card.armor_front') }}</th>
                    <th>{{ t('vehicle_card.armor_side')  }}</th>
                    <th>{{ t('vehicle_card.armor_rear')  }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="armor-label">{{ t('vehicle_card.armor_hull')   }}</td>
                    <td>{{ v('vdb_hull_front')  }}</td><td>{{ v('vdb_hull_side')  }}</td><td>{{ v('vdb_hull_rear')  }}</td>
                  </tr>
                  <tr>
                    <td class="armor-label">{{ t('vehicle_card.armor_turret') }}</td>
                    <td>{{ v('vdb_turret_front') }}</td><td>{{ v('vdb_turret_side') }}</td><td>{{ v('vdb_turret_rear') }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="card-section" :style="!showArmor ? { gridColumn: '1 / -1' } : {}">
              <div class="section-title"><v-icon size="12" style="margin-right:4px;opacity:.7">mdi-bullet</v-icon>{{ t('vehicle_card.weapons') }}</div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.caliber')      }}</span>
                <span class="stat-value">{{ v('vdb_main_caliber_mm') > 0 ? v('vdb_main_caliber_mm') + ' ' + t('vehicle_card.caliber_unit') : t('vehicle_card.no_vdb') }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('vehicle_card.shell_speed')  }}</span>
                <span class="stat-value">{{ v('vdb_main_gun_speed') > 0 ? v('vdb_main_gun_speed') + ' ' + t('vehicle_card.speed_unit_ms') : t('vehicle_card.no_vdb') }}</span>
              </div>
              <div class="chips-row">
                <v-chip v-if="showThermal && vehicle.vdb_has_thermal" color="info"      size="x-small">{{ t('vehicle_card.thermal') }}</v-chip>
                <v-chip v-if="showAtgm   && vehicle.vdb_has_atgm"    color="error"     size="x-small">{{ t('vehicle_card.atgm')    }}</v-chip>
                <v-chip v-if="showHeat   && vehicle.vdb_has_heat"    color="warning"   size="x-small">{{ t('vehicle_card.heat')    }}</v-chip>
                <v-chip v-if="showAphe   && vehicle.vdb_has_aphe"    color="secondary" size="x-small">{{ t('vehicle_card.aphe')    }}</v-chip>
              </div>
            </div>
          </template>

        </div>
      </v-card-text>
      </v-card>

      <Transition name="panel-slide">
        <VehicleStatsPanel
          v-if="showStatsPanel"
          :vehicle="veh"
          :mode="activeMode"
          class="stats-panel"
        />
      </Transition>
    </div>
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n }  from 'vue-i18n'
import { useDataStore } from '../stores/useDataStore.js'
import {
  vehicleDisplayName, fmtType, fmtNation, fmtBR, fmtSL,
  metaColor, farmColor, wrColor, CLASS_PREFIX, classChipStyle,
} from '../composables/useVehicleFormatting.js'
import VehicleImage from './VehicleImage.vue'
import VehicleStatsPanel from './VehicleStatsPanel.vue'

const { t } = useI18n()
const store  = useDataStore()

const props = defineProps({ modelValue: Boolean, vehicle: Object })
defineEmits(['update:modelValue'])

const showStatsPanel = ref(false)

const BR_MODES = [
  { key: 'Arcade',    short: 'AB', titleKey: 'br_arcade'    },
  { key: 'Realistic', short: 'RB', titleKey: 'br_realistic' },
  { key: 'Simulator', short: 'SB', titleKey: 'br_simulator' },
]

const veh      = computed(() => props.vehicle ?? {})
const hasVdb   = computed(() => (veh.value?.vdb_match_score ?? 0) > 0)
const displayName = computed(() => vehicleDisplayName(veh.value))

const _GROUND_SET = new Set(['medium_tank', 'light_tank', 'heavy_tank', 'tank_destroyer', 'spaa'])
const _AIR_SET    = new Set(['fighter', 'bomber', 'assault'])
const _HELI_SET   = new Set(['attack_helicopter', 'utility_helicopter'])

const vehType  = computed(() => veh.value?.Type ?? '')
const isGround = computed(() => _GROUND_SET.has(vehType.value))
const isAir    = computed(() => _AIR_SET.has(vehType.value))
const isHeli   = computed(() => _HELI_SET.has(vehType.value))
const isFlying = computed(() => isAir.value || isHeli.value)

const showReverseSpeed = computed(() => !isFlying.value)
const showArmor        = computed(() => isGround.value)
const showThermal      = computed(() => !isAir.value)
const showAtgm         = computed(() => true)
const showHeat         = computed(() => isGround.value)
const showAphe         = computed(() => isGround.value)
const showHp           = computed(() => !isAir.value || !!veh.value?.vdb_engine_hp_rb)

const activeMode = ref(props.vehicle?.Mode ?? 'Realistic')
watch(veh, v => { if (v?.Mode) activeMode.value = v.Mode }, { immediate: true })
watch(() => props.modelValue, v => { if (!v) showStatsPanel.value = false })

const vehicleByMode = computed(() => {
  const base = veh.value
  if (!base?.Name) return {}
  const { Name: name, Nation: nation, Type: type } = base
  const result  = {}
  const maxModes = BR_MODES.length
  for (const entry of store.allVehicles) {
    if (
      entry.Name   === name   &&
      entry.Nation === nation &&
      entry.Type   === type   &&
      entry.Mode   != null
    ) {
      if (!(entry.Mode in result)) {
        result[entry.Mode] = entry
        if (Object.keys(result).length === maxModes) break
      }
    }
  }
  return result
})

const modeVehicle = computed(() =>
  vehicleByMode.value[activeMode.value] ?? veh.value
)

const brByMode = computed(() =>
  Object.fromEntries(
    Object.entries(vehicleByMode.value)
      .filter(([, e]) => e.BR != null)
      .map(([mode, e]) => [mode, fmtBR(e.BR)])
  )
)

const scoresByMode = computed(() =>
  Object.fromEntries(
    Object.entries(vehicleByMode.value)
      .map(([mode, e]) => [mode, { meta: e.META_SCORE ?? null, farm: e.FARM_SCORE ?? null }])
  )
)

const KD_BREAKDOWN_DEFS = [
  { key: 'KD_GROUND', labelKey: 'vehicle_card.kd_ground' },
  { key: 'KD_AIR',     labelKey: 'vehicle_card.kd_air'    },
  { key: 'KD_NAVAL',   labelKey: 'vehicle_card.kd_naval'  },
]

const kdBreakdown = computed(() => {
  const v = modeVehicle.value
  if (!v) return []
  return KD_BREAKDOWN_DEFS
    .map(d => ({ ...d, value: v[d.key] }))
    .filter(d => d.value != null && d.value > 0)
})

const activeModePill = computed(() =>
  BR_MODES.find(m => m.key === activeMode.value)?.short ?? ''
)

const activeScores = computed(() => {
  const s = scoresByMode.value[activeMode.value]
  if (s) return s
  return {
    meta: veh.value?.META_SCORE ?? null,
    farm: veh.value?.FARM_SCORE ?? null,
  }
})

function v(key) {
  const val = veh.value?.[key]
  return val ?? t('vehicle_card.no_vdb')
}
</script>

<style scoped>
.card-shell {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 8px;
}
.main-card { width: 760px; max-width: 100%; flex-shrink: 0; }
.stats-panel { width: 340px; flex-shrink: 0; }

.panel-slide-enter-active,
.panel-slide-leave-active {
  transition: opacity .22s ease, transform .26s ease;
}
.panel-slide-enter-from,
.panel-slide-leave-to {
  opacity: 0;
  transform: translateX(-18px);
}

.stats-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 24px;
  margin-right: 4px;
  border: 1px solid #1e3a5f;
  border-radius: 5px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: border-color .15s, background .15s, color .15s;
}
.stats-toggle:hover {
  border-color: rgba(56, 189, 248, 0.25);
  background: rgba(56, 189, 248, 0.04);
  color: #7dd3fc;
}
.stats-toggle--active {
  border-color: rgba(56, 189, 248, 0.45);
  background: rgba(56, 189, 248, 0.08);
  color: #38bdf8;
}


.card-header { display: flex; align-items: center; padding: 12px 16px; gap: 8px; }
.vehicle-name { font-size: 18px; font-weight: 700; color: #a7f3d0; letter-spacing: .06em; }

.rank-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 7px;
  border: 1px solid rgba(45, 212, 191, 0.35);
  border-radius: 5px;
  background: rgba(45, 212, 191, 0.08);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .05em;
  color: #2dd4bf;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  white-space: nowrap;
}

.br-modes {
  display: flex;
  gap: 4px;
  align-items: center;
}
.br-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  padding: 2px 7px;
  border: 1px solid #1e3a5f;
  border-radius: 5px;
  background: transparent;
  cursor: pointer;
  transition: border-color .15s, background .15s;
}
.br-pill:hover:not(.br-pill--active) {
  border-color: rgba(56, 189, 248, 0.25);
  background: rgba(56, 189, 248, 0.04);
}
.br-pill--active {
  border-color: rgba(56, 189, 248, 0.45);
  background: rgba(56, 189, 248, 0.08);
}
.br-pill__mode {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: #94a3b8;
}
.br-pill--active .br-pill__mode { color: #7dd3fc; }
.br-pill__val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: #94a3b8;
}
.br-pill--active .br-pill__val { color: #38bdf8; }

.scores-mode {
  margin-left: 5px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: .1em;
  color: #38bdf8;
  opacity: 0.75;
}

.info-band {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-bottom: 1px solid #1e293b;
}
.img-pane {
  border-right: 1px solid #1e293b;
  background: rgba(30, 58, 95, 0.12);
  min-height: 90px;
  overflow: hidden;
}
.veh-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.img-placeholder { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
.meta-pane { display: flex; flex-direction: column; justify-content: center; }
.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 14px;
  border-bottom: 1px solid rgba(30, 41, 59, 0.7);
  font-size: 12px;
}
.meta-row:last-child { border-bottom: none; }
.meta-lbl { font-size: 9px; font-weight: 700; letter-spacing: .1em; color: #94a3b8; text-transform: uppercase; }
.meta-val { color: #e2e8f0; font-weight: 600; font-family: 'JetBrains Mono', monospace; }

.card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.card-section { padding: 14px 16px; border-right: 1px solid #1e293b; border-bottom: 1px solid #1e293b; }
.card-section:nth-child(even) { border-right: none; }
.card-section:nth-last-child(-n+2) { border-bottom: none; }
.section-title { font-size: 10px; font-weight: 700; letter-spacing: .12em; color: #94a3b8; text-transform: uppercase; margin-bottom: 10px; }
.stat-row { display: flex; justify-content: space-between; margin-bottom: 5px; font-size: 12px; }
.stat-label { color: #a8b3c4; }
.stat-value { color: #e2e8f0; font-weight: 600; }
.score-row { margin-bottom: 8px; }
.score-label { font-size: 10px; color: #a8b3c4; display: block; margin-bottom: 3px; letter-spacing: .06em; }
.score-bar-wrap { display: flex; align-items: center; gap: 8px; background: #1e293b; border-radius: 4px; height: 18px; padding: 0 8px; }
.score-val { font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace; flex-shrink: 0; min-width: 26px; }
.score-track { flex: 1; height: 4px; background: rgba(255,255,255,.06); border-radius: 2px; overflow: hidden; }
.score-bar { height: 100%; border-radius: 2px; transition: width .3s, background .3s; }
.armor-table { width: 100%; font-size: 11px; border-collapse: collapse; font-family: 'JetBrains Mono', monospace; }
.armor-table th { color: #94a3b8; font-weight: 600; text-align: center; padding: 2px 6px 5px; font-family: inherit; }
.armor-table td { text-align: center; color: #e2e8f0; padding: 4px 6px; }
.armor-table tbody tr + tr td { border-top: 1px solid #1e293b; }
.armor-label { color: #a8b3c4 !important; text-align: left !important; }
.chips-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
</style>
