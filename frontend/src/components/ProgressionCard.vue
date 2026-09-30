<template>
  <div
    class="panel prog-card"
    :class="{
      'prog-card--grouped':  grouped,
      'prog-card--excluded': vehicle._excludedFromLineup,
    }"
    :style="cardStyle"
    @click="$emit('click')"
  >
    <div class="pc-header">
      <v-icon class="pc-type-icon" size="13" :title="vehicle._branch">{{ typeIcon }}</v-icon>
      <v-icon v-if="classIcon" class="pc-class-icon" size="11" :style="{ color: brColor }">{{ classIcon }}</v-icon>
      <span class="mono pc-name" :style="{ color: nameColor }">{{ vehicleName }}</span>
      <span class="mono pc-br"   :style="{ color: brColor   }">{{ brStr }}</span>
      <v-icon class="pc-verdict" size="12" :style="{ color: vc.border }">{{ vc.icon }}</v-icon>
    </div>

    <div class="mono pc-stats">
      <span class="pc-stat"><span class="eyebrow eyebrow--xs pc-stat-label">WR</span>{{ wrStr }}%</span>
      <span class="pc-stat"><span class="eyebrow eyebrow--xs pc-stat-label">K/D</span>{{ kdStr }}</span>
      <span class="pc-stat"><span class="eyebrow eyebrow--xs pc-stat-label">META</span>{{ metaStr }}</span>
    </div>

    <div v-if="vehicle.Cross_Hint" class="pc-hint pc-hint--cross">
      {{ vehicle.Cross_Hint }}
    </div>

    <div
      v-if="vehicle.Verdict === 'SKIP' && vehicle.Skip_Reason"
      class="pc-hint pc-hint--skip"
    >
      {{ vehicle.Skip_Reason }}
    </div>

    <div
      v-if="vehicle._excludedFromLineup"
      class="pc-hint pc-hint--excluded"
    >
      <v-icon size="11" class="pc-hint-icon">mdi-cancel</v-icon>{{ vehicle._excluded_hint }}
    </div>

    <template v-if="vehicle.Verdict === 'PREM'">
      <div v-if="vehicle.Prem_Pain_Fix" class="pc-hint pc-hint--prem">
        <v-icon size="11" class="pc-hint-icon">mdi-crown</v-icon>{{ (vehicle.Prem_Boost ?? 0) >= 1.05
          ? t('progression_tab.prem_pain_fix_boost')
          : t('progression_tab.prem_pain_fix_only') }}
      </div>
      <div
        v-if="boostLabel"
        class="pc-hint pc-hint--boost"
        :style="{ color: boostLabel.color }"
      >
        {{ boostLabel.text }}
      </div>
      <div v-if="!vehicle.Prem_Pain_Fix && !boostLabel" class="pc-hint pc-hint--prem">
        {{ t('progression_tab.prem_fallback') }}
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  VERDICT_COLORS,
  TYPE_ICON,
  CLASS_PREFIX,
  CLASS_BR_COLOR,
} from '../composables/constants.js'

const { t } = useI18n()

const props = defineProps({
  vehicle: { type: Object,  required: true },
  grouped: { type: Boolean, default: false },
})
defineEmits(['click'])

const vc = computed(() => VERDICT_COLORS[props.vehicle.Verdict] ?? VERDICT_COLORS.PASS)

const vehicleName = computed(() => props.vehicle.Name ?? '')
const classIcon   = computed(() => CLASS_PREFIX[props.vehicle.VehicleClass] || null)
const brStr   = computed(() => parseFloat(props.vehicle.BR           || 0).toFixed(1))
const wrStr   = computed(() => parseFloat(props.vehicle.WR           || 0).toFixed(1))
const kdStr   = computed(() => parseFloat(props.vehicle.KD           || 0).toFixed(1))
const metaStr = computed(() => parseFloat(props.vehicle._localScore  || 0).toFixed(0))

const typeIcon  = computed(() => TYPE_ICON[props.vehicle._branch] || 'mdi-wrench')
const classColor = computed(() => CLASS_BR_COLOR[props.vehicle.VehicleClass] || null)
const brColor    = computed(() => classColor.value || 'var(--ink-faint)')
const nameColor  = computed(() => classColor.value || 'var(--ink)')

const boostLabel = computed(() => {
  const b = props.vehicle.Prem_Boost
  if (!b || b < 0.01) return null
  const val = b.toFixed(1)
  if (b >= 1.05) return { text: t('progression_tab.prem_boost_grind',  { val }), color: 'var(--primary)' }
  if (b >= 0.95) return { text: t('progression_tab.prem_boost_parity', { val }), color: 'var(--ink-muted)' }
  return               { text: t('progression_tab.prem_boost_weaker', { val }), color: 'var(--danger)' }
})

const cardStyle = computed(() => ({
  borderLeft:      `3px solid ${vc.value.border}`,
  backgroundColor: vc.value.bg,
  '--glow':        vc.value.border,
}))
</script>

<style scoped>
.prog-card {                       /* border + bg come from .panel / inline verdict colours */
  position: relative;
  min-width: 0;
  margin-bottom: 4px;
  padding: 7px 10px;
  box-sizing: border-box;
  cursor: pointer;
  transition: box-shadow 0.15s, filter 0.12s;
}
.prog-card:hover           { box-shadow: inset 0 0 0 1px var(--glow, var(--primary-line)); filter: brightness(1.1); }
.prog-card--grouped        { margin-bottom: 0; }
.prog-card--excluded       { opacity: 0.5; filter: grayscale(0.4); }
.prog-card--excluded:hover { opacity: 0.85; filter: grayscale(0.15); }

.pc-header     { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; }
.pc-type-icon  { flex-shrink: 0; opacity: 0.7; }
.pc-class-icon { flex-shrink: 0; opacity: 0.9; }
.pc-name       { flex: 1; min-width: 0; font-size: 12px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pc-br         { flex-shrink: 0; font-size: 11px; font-weight: 600; }
.pc-verdict    { flex-shrink: 0; }

.pc-stats      { display: flex; gap: 10px; font-size: 11px; color: var(--ink-muted); }
.pc-stat-label { margin-right: 3px; color: var(--ink-dim); }

/* hint strip: one --c drives text + divider */
.pc-hint {
  --c: var(--ink-faint);
  margin-top: 5px;
  padding-top: 5px;
  font-size: 10px;
  line-height: 1.4;
  color: color-mix(in srgb, var(--c) 75%, white);
  border-top: 1px solid color-mix(in srgb, var(--c) 25%, transparent);
}
.pc-hint--cross { --c: var(--c-info); }
.pc-hint--skip  { --c: var(--c-bad); }
.pc-hint--prem  { --c: var(--c-violet); }
.pc-hint--boost { --c: var(--c-violet); margin-top: 3px; padding-top: 3px; font-family: var(--font-display); font-weight: 500; }
.pc-hint-icon   { margin-right: 4px; vertical-align: -1px; }
</style>
