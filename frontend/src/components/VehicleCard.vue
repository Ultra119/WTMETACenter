<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="1100" scrollable>
    <div class="card-shell">
      <v-card v-if="vehicle" class="main-card" color="surface" variant="flat" border>

      <v-card-title class="card-header">
        <span class="vehicle-name">{{ displayName }}</span>
        <span v-if="vehicle.VehicleClass !== 'Standard'" class="class-chip ml-2" :style="classChipStyle(vehicle.VehicleClass)">
          <span v-if="CLASS_PREFIX[vehicle.VehicleClass]" class="mdi" :class="CLASS_PREFIX[vehicle.VehicleClass]" style="font-size:9px; margin-right:2px;" />
          {{ t(`vehicle_classes.${vehicle.VehicleClass}`) }}
        </span>
        <span v-if="vehicle.vdb_shop_rank" class="tag eyebrow ml-1">
          <span class="mdi mdi-medal-outline" style="font-size:10px; margin-right:3px;" />
          {{ t('vehicle_card.era') }} {{ vehicle.vdb_shop_rank }}
        </span>
        <v-spacer />

        <button
          type="button"
          class="ui-btn ui-btn--icon mr-1"
          :class="{ 'is-active': showStatsPanel }"
          :title="t('vehicle_card.stats')"
          @click="showStatsPanel = !showStatsPanel"
        >
          <span class="mdi mdi-chart-line" style="font-size:13px;" />
        </button>

        <div class="ui-group">
          <button
            v-for="m in BR_MODES"
            :key="m.key"
            type="button"
            class="ui-btn"
            :class="{ 'is-active': m.key === activeMode }"
            :title="t(`vehicle_card.${m.titleKey}`)"
            @click="activeMode = m.key"
          >
            <span class="eyebrow eyebrow--xs">{{ m.short }}</span>
            <span>{{ brByMode[m.key] ?? '—' }}</span>
          </button>
        </div>

        <v-btn icon="mdi-close" variant="text" size="small" :title="t('common.close')" @click="$emit('update:modelValue', false)" />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-0">

        <div class="info-band">
          <div class="img-pane">
            <VehicleImage :name="displayName" :identifier="vehicle.vdb_identifier" :type="vehicle.Type" aspect="2/1" fit="cover" />
          </div>
          <div class="meta-pane">
            <div class="kv kv--ruled kv--eyebrow">
              <span class="kv__k">{{ t('vehicle_card.nation') }}</span>
              <span class="kv__v">{{ fmtNation(vehicle.Nation) }}</span>
            </div>
            <div class="kv kv--ruled kv--eyebrow">
              <span class="kv__k">{{ t('vehicle_card.type') }}</span>
              <span class="kv__v">{{ fmtType(vehicle.Type) }}</span>
            </div>
            <div class="kv kv--ruled kv--eyebrow">
              <span class="kv__k">{{ t('vehicle_card.battles') }}</span>
              <span class="kv__v">{{ (modeVehicle['Сыграно игр'] ?? 0).toLocaleString() }}</span>
            </div>
            <div class="kv kv--ruled kv--eyebrow">
              <span class="kv__k">{{ t('vehicle_card.wr') }}</span>
              <span class="kv__v" :style="{ color: wrColor(modeVehicle.WR) }">{{ modeVehicle.WR?.toFixed(1) }}%</span>
            </div>
            <div v-for="row in kdBreakdown" :key="row.key" class="kv kv--ruled kv--eyebrow">
              <span class="kv__k">{{ t(row.labelKey) }}</span>
              <span class="kv__v">{{ row.value.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <div class="card-grid">

          <div class="card-section">
            <div class="eyebrow section-title">
              <v-icon size="12" style="margin-right:4px;opacity:.7">mdi-trophy</v-icon>
              {{ t('vehicle_card.scores') }}
              <span class="eyebrow eyebrow--xs eyebrow--primary scores-mode">{{ activeModePill }}</span>
            </div>

            <div class="score-row">
              <span class="kv__k score-label">{{ t('vehicle_card.meta_score') }}</span>
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
              <span class="kv__k score-label">{{ t('vehicle_card.farm_score') }}</span>
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
            <div class="kv mt-2">
              <span class="kv__k">{{ t('vehicle_card.net_sl') }}</span>
              <span class="kv__v" style="color: var(--primary);">{{ fmtSL(modeVehicle['Net SL за игру']) }}</span>
            </div>
          </div>

          <div class="card-section">
            <template v-if="hasVdb">
              <div class="eyebrow section-title"><v-icon size="12" style="margin-right:4px;opacity:.7">mdi-cog</v-icon>{{ t('vehicle_card.mobility') }}</div>
              <div class="kv">
                <span class="kv__k">{{ t('vehicle_card.speed_rb') }}</span>
                <span class="kv__v">{{ v('vdb_engine_max_speed_rb') }} {{ t('vehicle_card.speed_unit') }}</span>
              </div>
              <div v-if="showReverseSpeed" class="kv">
                <span class="kv__k">{{ t('vehicle_card.reverse_rb') }}</span>
                <span class="kv__v">{{ v('vdb_engine_reverse_rb') }} {{ t('vehicle_card.speed_unit') }}</span>
              </div>
              <div v-if="showHp" class="kv">
                <span class="kv__k">{{ t('vehicle_card.hp_rb') }}</span>
                <span class="kv__v">
                  {{ v('vdb_engine_hp_rb') }} {{ t('vehicle_card.hp_unit') }}
                  <span v-if="powerToWeight != null" class="t-muted" :title="powerToWeightHint">
                    ({{ powerToWeight.toFixed(1) }} {{ t('vehicle_card.power_to_weight_unit', 'hp/t') }})
                  </span>
                </span>
              </div>
              <div class="eyebrow section-title" style="margin-top:10px"><v-icon size="12" style="margin-right:4px;opacity:.7">mdi-cash</v-icon>{{ t('vehicle_card.economy') }}</div>
              <div class="kv">
                <span class="kv__k">{{ t('vehicle_card.repair_rb') }}</span>
                <span class="kv__v">{{ fmtSL(vehicle.vdb_repair_cost_realistic) }}</span>
              </div>
              <div class="kv">
                <span class="kv__k">{{ t('vehicle_card.sl_per_game') }}</span>
                <span class="kv__v" style="color: var(--primary);">{{ fmtSL(modeVehicle['SL за игру']) }}</span>
              </div>
            </template>
          </div>

          <template v-if="hasVdb">
            <div v-if="showArmor" class="card-section">
              <div class="eyebrow section-title"><v-icon size="12" style="margin-right:4px;opacity:.7">mdi-shield</v-icon>{{ t('vehicle_card.armor') }}</div>
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
              <div class="eyebrow section-title"><v-icon size="12" style="margin-right:4px;opacity:.7">mdi-bullet</v-icon>{{ t('vehicle_card.weapons') }}</div>
              <div class="kv">
                <span class="kv__k">{{ t('vehicle_card.caliber')      }}</span>
                <span class="kv__v">{{ v('vdb_main_caliber_mm') > 0 ? v('vdb_main_caliber_mm') + ' ' + t('vehicle_card.caliber_unit') : t('vehicle_card.no_vdb') }}</span>
              </div>
              <div class="kv">
                <span class="kv__k">{{ t('vehicle_card.shell_speed')  }}</span>
                <span class="kv__v">{{ v('vdb_main_gun_speed') > 0 ? v('vdb_main_gun_speed') + ' ' + t('vehicle_card.speed_unit_ms') : t('vehicle_card.no_vdb') }}</span>
              </div>
              <div class="chips-row">
                <v-chip v-if="showThermal && vehicle.vdb_has_thermal" color="info" size="x-small">{{ t('vehicle_card.thermal') }}</v-chip>
                <v-chip
                  v-for="cat in ammoCategories"
                  :key="cat"
                  :color="AMMO_CATEGORY_META[cat]?.color"
                  size="x-small"
                >
                  <span v-if="AMMO_CATEGORY_META[cat]?.icon" class="mdi" :class="AMMO_CATEGORY_META[cat].icon" style="font-size:11px; margin-right:3px;" />
                  {{ ammoCategoryLabel(cat) }}
                </v-chip>
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
import {
  getVehicleAmmoCategories, AMMO_CATEGORY_META, useAmmoCategoryLabel,
} from '../composables/useAmmoTypes.js'
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
const showHp           = computed(() => !isAir.value || !!veh.value?.vdb_engine_hp_rb)

const massTons = computed(() => {
  const kg = Number(veh.value?.vdb_mass)
  return kg > 0 ? kg / 1000 : null
})

const powerToWeight = computed(() => {
  const hp = Number(veh.value?.vdb_engine_hp_rb)
  return hp > 0 && massTons.value ? hp / massTons.value : null
})

const powerToWeightHint = computed(() =>
  powerToWeight.value == null
    ? ''
    : `${Math.round(Number(veh.value.vdb_engine_hp_rb))} ${t('vehicle_card.hp_unit')} ÷ ${massTons.value.toFixed(1)} t`
)

const ammoCategories  = computed(() => getVehicleAmmoCategories(veh.value))
const ammoCategoryLabel = useAmmoCategoryLabel()

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
.card-shell  { display: flex; align-items: flex-start; justify-content: center; gap: 12px; }
.main-card   { width: 760px; max-width: 100%; flex-shrink: 0; }
.stats-panel { width: 340px; flex-shrink: 0; }
.panel-slide-enter-active,
.panel-slide-leave-active { transition: opacity 0.22s ease, transform 0.26s ease; }
.panel-slide-enter-from,
.panel-slide-leave-to     { opacity: 0; transform: translateX(-18px); }

.card-header  { display: flex; align-items: center; gap: 8px; padding: 12px 16px; }
.vehicle-name { font: 600 18px var(--font-display); letter-spacing: 0.02em; color: var(--primary); }
.scores-mode  { margin-left: 6px; }

.info-band { display: grid; grid-template-columns: 1fr 1fr; border-bottom: 1px solid var(--hairline); }
.img-pane  { min-height: 90px; overflow: hidden; border-right: 1px solid var(--hairline); background: rgba(231, 233, 238, 0.03); }
.meta-pane { display: flex; flex-direction: column; justify-content: center; }
.meta-pane .kv { padding: 5px 14px; }

.card-grid    { display: grid; grid-template-columns: 1fr 1fr; }
.card-section { padding: 14px 16px; border-right: 1px solid var(--hairline); border-bottom: 1px solid var(--hairline); }
.card-section:nth-child(even)      { border-right: none; }
.card-section:nth-last-child(-n+2) { border-bottom: none; }
.section-title { display: flex; align-items: center; margin-bottom: 10px; }

.score-row   { margin-bottom: 8px; }
.score-label { display: block; margin-bottom: 3px; font-size: 11px; }
.score-bar-wrap { display: flex; align-items: center; gap: 8px; height: 20px; padding: 0 8px; background: var(--bg); border: 1px solid var(--hairline); }
.score-val   { flex-shrink: 0; min-width: 26px; font: 600 11px var(--font-display); }
.score-track { flex: 1; height: 3px; background: rgba(231, 233, 238, 0.08); overflow: hidden; }
.score-bar   { height: 100%; transition: width 0.3s, background 0.3s; }

.armor-table { width: 100%; border-collapse: collapse; font: 11px var(--font-display); }
.armor-table th { padding: 2px 6px 6px; text-align: center; font: 500 10px var(--font-display); letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-faint); }
.armor-table td { padding: 4px 6px; text-align: center; color: var(--ink); }
.armor-table tbody tr + tr td { border-top: 1px solid var(--hairline); }
.armor-label { color: var(--ink-muted) !important; text-align: left !important; }
.chips-row   { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
</style>
