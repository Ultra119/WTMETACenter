<template>
  <div class="prog-root">

    <!-- ── Controls ──────────────────────────────────────────────────────── -->
    <div class="controls-bar mb-3">
      <div class="controls-row">

        <!-- Nation -->
        <v-select
          v-model="nation"
          :items="nationOptions"
          :label="$t('progression_tab.nation')"
          prepend-inner-icon="mdi-flag"
          density="compact"
          variant="outlined"
          hide-details
          class="ctrl-nation"
        />

        <!-- Branch -->
        <div class="ctrl-group">
          <div class="ctrl-label">BRANCH</div>
          <v-btn-toggle
            v-model="branch"
            mandatory
            density="compact"
            variant="outlined"
            rounded="lg"
            class="branch-toggle"
          >
            <v-btn value="Ground"   size="small">⚙️ Ground</v-btn>
            <v-btn value="Aviation" size="small">✈️ Aviation</v-btn>
            <v-btn value="Fleet"    size="small">⚓ Fleet</v-btn>
          </v-btn-toggle>
        </div>

        <!-- Slots -->
        <div class="ctrl-group">
          <div class="ctrl-label">CREW SLOTS</div>
          <v-btn-toggle
            v-model="slots"
            mandatory
            density="compact"
            variant="outlined"
            rounded="lg"
          >
            <v-btn :value="3" size="small">3</v-btn>
            <v-btn :value="4" size="small">4</v-btn>
            <v-btn :value="5" size="small">5</v-btn>
          </v-btn-toggle>
        </div>

        <!-- Info badges -->
        <div class="stats-badges">
          <span v-if="progressionData.length" class="badge badge-total">
            📋 {{ progressionData.length }}
          </span>
          <span class="badge badge-must">🟢 {{ countByVerdict('MUST') }}</span>
          <span class="badge badge-fill">🔵 {{ countByVerdict('FILL') }}</span>
          <span class="badge badge-skip">🔴 {{ countByVerdict('SKIP') }}</span>
          <span class="badge badge-prem">👑 {{ countByVerdict('PREM') }}</span>
        </div>
      </div>

      <!-- Type checkboxes (dynamic per branch) -->
      <div class="type-toggles mt-2">
        <v-chip
          v-for="t in branchTypes"
          :key="t"
          size="small"
          :variant="activeTypes.has(t) ? 'elevated' : 'outlined'"
          :color="activeTypes.has(t) ? 'primary' : 'default'"
          class="mr-1 mb-1 type-chip"
          @click="toggleType(t)"
        >
          {{ TYPE_LABELS[t] || t }}
        </v-chip>
      </div>
    </div>

    <!-- ── Legend ─────────────────────────────────────────────────────────── -->
    <div class="legend-row mb-3">
      <span v-for="(vc, key) in VERDICT_COLORS" :key="key" class="legend-item">
        <span class="legend-icon">{{ vc.icon }}</span>
        <span class="legend-text">{{ vc.label }}</span>
      </span>
    </div>

    <!-- ── No-data state ──────────────────────────────────────────────────── -->
    <v-alert
      v-if="!gridData"
      type="info"
      variant="tonal"
      density="compact"
      class="mt-4"
    >
      {{ $t('progression_tab.no_data') }}
    </v-alert>

    <!-- ── Main Grid ──────────────────────────────────────────────────────── -->
    <div v-else class="prog-scroll">
      <div
        class="prog-grid"
        :style="{ gridTemplateColumns: `52px repeat(${gridData.numCols}, minmax(140px,1fr)) 180px` }"
      >
        <!-- Header row -->
        <div class="grid-header-rank">RANK</div>
        <div
          v-for="col in gridData.numCols"
          :key="`hdr-${col}`"
          class="grid-header-col"
        >
          <span v-if="gridData.typesInDf">
            {{ TYPE_LABELS[gridData.typesInDf[col - 1]] || gridData.typesInDf[col - 1] }}
          </span>
        </div>
        <div class="grid-header-prem">👑 PREMIUM</div>

        <!-- Data rows (one per era) -->
        <template v-for="era in gridData.eras" :key="`era-${era}`">

          <!-- Rank label -->
          <div class="rank-label-cell">
            <span class="rank-roman">{{ ROMAN[era] }}</span>
          </div>

          <!-- Standard columns -->
          <div
            v-for="col in gridData.numCols"
            :key="`cell-${era}-${col}`"
            class="prog-cell"
          >
            <template v-if="gridData.getCellVehicles(era, col - 1).length">
              <template v-for="item in groupedCells(gridData.getCellVehicles(era, col - 1))" :key="item.key">
                <!-- Group bracket -->
                <div v-if="item.isGroup" class="group-bracket">
                  <div class="group-label">📁 {{ item.groupLabel }}</div>
                  <VehicleCard
                    v-for="v in item.vehicles"
                    :key="v._idx"
                    :vehicle="v"
                    :grouped="true"
                    @click="openVehicle?.(v)"
                  />
                </div>
                <!-- Single card -->
                <VehicleCard
                  v-else
                  :vehicle="item.vehicle"
                  @click="openVehicle?.(item.vehicle)"
                />
              </template>
            </template>
            <div v-else class="empty-cell" />
          </div>

          <!-- Premium column -->
          <div class="prem-cell">
            <template v-if="gridData.getPremVehicles(era).length">
              <VehicleCard
                v-for="v in gridData.getPremVehicles(era)"
                :key="v._idx"
                :vehicle="v"
                @click="openVehicle?.(v)"
              />
            </template>
            <div v-else class="empty-cell" />
          </div>

        </template>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, computed, inject, watch, shallowRef, h } from 'vue'
import { useDataStore } from '../stores/useDataStore.js'

// Constants

const RANK_PENALTY = {
  '-4': 0.05, '-3': 0.10, '-2': 0.30, '-1': 0.90,
   0: 1.00,    1: 1.00,    2: 0.35,    3: 0.15,    4: 0.06,
}
const RANK_PENALTY_PREMIUM = {
  '-4': 1.00, '-3': 1.00, '-2': 1.00, '-1': 1.00,
   0: 1.00,    1: 1.00,    2: 0.35,    3: 0.15,    4: 0.06,
}

const MM_WINDOW        = 1.0
const BR_FILL_WINDOW   = 1.0
const JUNK_FLOOR       = 35.0
const YELLOW_FLOOR     = 35.0
const YELLOW_PCTILE    = 0.30
const STAY_PREV_THRESHOLD = 0.85 // kept for future use

const ROMAN = { 1:'I', 2:'II', 3:'III', 4:'IV', 5:'V', 6:'VI', 7:'VII', 8:'VIII' }

const VERDICT_MUST = 'MUST'
const VERDICT_PASS = 'PASS'
const VERDICT_SKIP = 'SKIP'
const VERDICT_PREM = 'PREM'
const VERDICT_FILL = 'FILL'

const VERDICT_COLORS = {
  MUST: { border: '#10b981', bg: 'rgba(16,185,129,0.08)',  icon: '🟢', label: 'Must Play'      },
  FILL: { border: '#38bdf8', bg: 'rgba(56,189,248,0.07)',  icon: '🔵', label: 'Lineup Filler'  },
  PASS: { border: '#fbbf24', bg: 'rgba(251,191,36,0.06)',  icon: '🟡', label: 'Passable'       },
  SKIP: { border: '#f87171', bg: 'rgba(248,113,113,0.08)', icon: '🔴', label: 'Hard Skip'      },
  PREM: { border: '#a78bfa', bg: 'rgba(167,139,250,0.09)', icon: '👑', label: 'Premium Fix'    },
}

const BRANCH_TYPES = {
  Ground:   ['medium_tank', 'light_tank', 'heavy_tank', 'tank_destroyer', 'spaa'],
  Aviation: ['fighter', 'bomber', 'assault', 'attack_helicopter', 'utility_helicopter'],
  Fleet:    ['destroyer', 'heavy_cruiser', 'light_cruiser', 'battleship', 'battlecruiser',
             'boat', 'heavy_boat', 'frigate', 'barge'],
}

const TYPE_LABELS = {
  medium_tank:        '🛡️ Medium',    light_tank:    '💨 Light',
  heavy_tank:         '⚔️ Heavy',      tank_destroyer:'🎯 Tank Dest.',
  spaa:               '🌀 SPAA',
  fighter:            '✈️ Fighter',   bomber:        '💣 Bomber',
  assault:            '🔥 Assault',   attack_helicopter: '🚁 Atk Heli',
  utility_helicopter: '🔧 Util Heli',
  destroyer:          '🚢 Destroyer', heavy_cruiser: '🛳️ H.Cruiser',
  light_cruiser:      '🛳️ L.Cruiser', battleship:    '⚓ Battleship',
  battlecruiser:      '⚓ B.Cruiser', boat:          '⛵ Boat',
  heavy_boat:         '🚤 H.Boat',    frigate:       '🛥️ Frigate',
  barge:              '🪝 Barge',
}

const TYPE_ICON = {
  medium_tank: '🛡️', heavy_tank: '⚔️', light_tank: '💨', tank_destroyer: '🎯',
  spaa: '🌀', fighter: '✈️', bomber: '💣', assault: '🔥',
  attack_helicopter: '🚁', utility_helicopter: '🔧',
  destroyer: '🚢', battleship: '⚓', light_cruiser: '🛳️',
  heavy_cruiser: '🛳️', battlecruiser: '⚓', boat: '⛵',
  heavy_boat: '🚤', frigate: '🛥️', barge: '🪝',
}

const CLASS_PREFIX = {
  Premium: '★ ', Pack: '📦 ', Squadron: '✦ ',
  Marketplace: '🏪 ', Gift: '🎁 ', Event: '🎪 ', Standard: '',
}

const CLASS_BR_COLOR = {
  Premium: '#fbbf24', Pack: '#60a5fa', Squadron: '#34d399',
  Marketplace: '#a78bfa', Gift: '#f472b6', Event: '#fb923c',
}

const STD_CLASS = 'Standard'

// Store & Inject

const store      = useDataStore()
const openVehicle = inject('openVehicle', null)

// Controls

const nation      = ref('')
const branch      = ref('Ground')
const slots       = ref(4)
const activeTypes = shallowRef(new Set(BRANCH_TYPES.Ground))

const nationOptions = computed(() =>
  (store.nations ?? []).filter(n => n !== 'All')
)

// Init nation once nations are loaded
watch(nationOptions, (opts) => {
  if (!nation.value && opts.length) nation.value = opts[0]
}, { immediate: true })

// When branch changes → reset activeTypes to all of that branch
watch(branch, (newBranch) => {
  activeTypes.value = new Set(BRANCH_TYPES[newBranch] ?? [])
})

const branchTypes = computed(() => BRANCH_TYPES[branch.value] ?? [])

function toggleType(t) {
  const next = new Set(activeTypes.value)
  if (next.has(t)) { if (next.size > 1) next.delete(t) }
  else              next.add(t)
  activeTypes.value = next
}

// Algorithm Helpers

function brToEra(br) {
  const thresholds = [2.3, 3.7, 5.3, 6.7, 8.3, 9.7, 11.3]
  for (let i = 0; i < thresholds.length; i++) {
    if (br <= thresholds[i]) return i + 1
  }
  return 8
}

function brDecay(researcherBr, targetBr) {
  const gap = targetBr - researcherBr
  if (gap <= MM_WINDOW) return 1.0
  return Math.max(0.02, Math.exp(-1.1 * (gap - MM_WINDOW)))
}

function rankPenaltyStd(resEra, tgtEra) {
  const diff = tgtEra - resEra
  return RANK_PENALTY[diff] ?? (diff < 0 ? 0.05 : 0.06)
}

function rankPenaltyPrem(resEra, tgtEra) {
  const diff = tgtEra - resEra
  return RANK_PENALTY_PREMIUM[diff] ?? (diff <= 1 ? 1.0 : 0.06)
}

function combinedPenalty(resEra, resBr, tgtEra, tgtBr, isPrem = false) {
  const pen = isPrem ? rankPenaltyPrem(resEra, tgtEra) : rankPenaltyStd(resEra, tgtEra)
  return pen * brDecay(resBr, tgtBr)
}

/** Approximate percentile of a numeric array */
function quantile(arr, q) {
  if (!arr.length) return 0
  const s = [...arr].sort((a, b) => a - b)
  const pos  = (s.length - 1) * q
  const low  = Math.floor(pos)
  const high = Math.ceil(pos)
  return low === high ? s[low] : s[low] * (high - pos) + s[high] * (pos - low)
}

/** Returns [junkThresh, yellowThresh, greenThresh] */
function computeDynamicThresholds(allMeta) {
  const valid = allMeta.filter(m => m > 1.0)
  if (!valid.length) return [JUNK_FLOOR, YELLOW_FLOOR, YELLOW_FLOOR + 30]
  const p30 = quantile(valid, YELLOW_PCTILE)
  const p70 = quantile(valid, 0.70)
  const yellow = Math.max(p30, YELLOW_FLOOR)
  const green  = Math.max(p70, 65.0)
  return [yellow, yellow, green]
}

function lineupScore(eraVehicles, anchorBr, junkThresh, minLineup) {
  const cands = eraVehicles.filter(v =>
    v._localScore >= junkThresh &&
    v.BR >= anchorBr - BR_FILL_WINDOW &&
    v.BR <= anchorBr
  )
  if (!cands.length) return 0
  const avg = cands.reduce((s, v) => s + v._localScore, 0) / cands.length
  return avg * Math.min(cands.length, minLineup) / Math.max(minLineup, 1)
}

function bestAnchorForEra(eraVehicles, junkThresh, yellowThresh, minLineup) {
  const candidates = eraVehicles.filter(v => v._localScore >= yellowThresh)
  if (!candidates.length) return { idx: null, br: 0, score: -1 }
  let bestIdx = null, bestBr = 0, bestScore = -1
  for (const v of candidates) {
    const ls = lineupScore(eraVehicles, v.BR, junkThresh, minLineup)
    if (ls > bestScore) { bestScore = ls; bestBr = v.BR; bestIdx = v._idx }
  }
  return { idx: bestIdx, br: bestBr, score: bestScore }
}

function superCat(branchName) {
  const GROUND   = new Set(['medium_tank', 'light_tank', 'heavy_tank', 'tank_destroyer'])
  const AVIATION = new Set(['fighter', 'bomber', 'assault', 'attack_helicopter', 'utility_helicopter'])
  if (branchName === 'spaa')  return 'AntiAir'
  if (GROUND.has(branchName)) return 'Ground'
  if (AVIATION.has(branchName)) return 'Aviation'
  return 'Fleet'
}

// Main Computation

const progressionData = computed(() => {
  const allVehicles = store.allVehicles ?? []
  if (!allVehicles.length || !nation.value) return []

  const selectedNation = nation.value
  const selectedMode   = store.mode
  const brTypes        = BRANCH_TYPES[branch.value] ?? []
  const active         = activeTypes.value
  const minLineup      = slots.value

  // 1. Filter & deduplicate
  const raw = allVehicles.filter(v =>
    v.Nation === selectedNation &&
    v.Mode   === selectedMode  &&
    (v.vdb_shop_rank ?? 0) > 0 &&
    brTypes.includes(v.Type) &&
    active.has(v.Type)
  )

  const seen = new Map()
  for (const v of raw) {
    const key = v.vdb_identifier || v.Name
    if (!seen.has(key) || (v.META_SCORE ?? 0) > (seen.get(key).META_SCORE ?? 0))
      seen.set(key, v)
  }

  if (!seen.size) return []

  // 2. Enrich
  const enriched = [...seen.values()].map((v, i) => {
    const br     = parseFloat(v.BR)  || 0
    const rawEra = v.vdb_era ? (parseInt(v.vdb_era) || 0) : 0
    const era    = Math.max(1, Math.min(8, rawEra > 0 ? rawEra : brToEra(br)))
    return {
      ...v,
      // Computed fields (own properties so we can mutate them below)
      _idx:        i,
      _era_int:    era,
      _branch:     v.Type || 'unknown',
      _localScore: parseFloat(v.META_SCORE) || 0,
      Verdict:     VERDICT_PASS,
      Skip_Reason: '',
      Alt_Vehicle: '',
      Cross_Hint:  '',
      Cross_Alt:   '',
      Prem_Boost:  0,
      Prem_Pain_Fix: false,
    }
  })

  const stdVehicles  = enriched.filter(v => v.VehicleClass === STD_CLASS)
  const premVehicles = enriched.filter(v => v.VehicleClass !== STD_CLASS)

  const shopSort = v => v.vdb_shop_order != null ? v.vdb_shop_order : v.BR * 10000
  stdVehicles.sort((a, b)  => shopSort(a) - shopSort(b))
  premVehicles.sort((a, b) => shopSort(a) - shopSort(b))

  // 3. Dynamic thresholds
  const allMeta = enriched.map(v => v._localScore)
  const [junkThresh, yellowThresh] = computeDynamicThresholds(allMeta)

  // Per-era junk thresholds (finer granularity)
  const eraJunk = {}
  {
    const byEra = {}
    for (const v of stdVehicles) {
      const e = v._era_int
      ;(byEra[e] ??= []).push(v._localScore)
    }
    for (const [e, scores] of Object.entries(byEra)) {
      eraJunk[+e] = computeDynamicThresholds(scores)[0]
    }
  }

  const mustMinMeta = yellowThresh
  const skipMaxMeta = junkThresh

  // Pass 1: MUST / PASS / SKIP per branch
  const byBranch = {}
  for (const v of stdVehicles) {
    ;(byBranch[v._branch] ??= []).push(v)
  }

  for (const grp of Object.values(byBranch)) {
    grp.sort((a, b) => a.BR !== b.BR ? a.BR - b.BR : b._localScore - a._localScore)
    const p60 = quantile(grp.map(v => v._localScore), 0.60)

    for (let pos = 0; pos < grp.length; pos++) {
      const v      = grp[pos]
      const era    = v._era_int
      const locS   = v._localScore
      const noData = locS < 1.0
      const ourGrp = v.vdb_shop_group || ''

      let shouldSkip = false, reason = '', altName = ''

      if (pos > 0 && !noData) {
        let bestEff = 0, bestName = ''
        for (const prev of grp.slice(0, pos)) {
          if (ourGrp && prev.vdb_shop_group === ourGrp) continue
          const eff = prev._localScore * combinedPenalty(prev._era_int, prev.BR, era, v.BR)
          if (eff > bestEff) { bestEff = eff; bestName = prev.Name }
        }
        if (bestEff > locS * 1.05) {
          shouldSkip = true
          reason  = `Effective grind on "${bestName}" (META ${bestEff.toFixed(0)} vs ${locS.toFixed(0)})`
          altName = bestName
        }
      }

      if (shouldSkip) {
        v.Verdict = VERDICT_SKIP; v.Skip_Reason = reason; v.Alt_Vehicle = altName
      } else if (!noData && locS < (eraJunk[era] ?? skipMaxMeta)) {
        v.Verdict     = VERDICT_SKIP
        v.Skip_Reason = `Weak vehicle (META ${locS.toFixed(0)} < ${(eraJunk[era] ?? skipMaxMeta).toFixed(0)})`
      } else {
        v.Verdict = (!noData && locS >= p60 && locS >= mustMinMeta) ? VERDICT_MUST : VERDICT_PASS
      }
    }
  }

  // Pass 2: Cross-branch hints
  const CROSS_THRESH      = 1.30
  const CROSS_SKIP_THRESH = 1.40
  const CROSS_BR_WINDOW   = 0.7
  const CROSS_BR_LOOKBACK = 1.0
  const NO_CROSS          = new Set(['spaa'])

  for (const v of stdVehicles) {
    if (v.Verdict !== VERDICT_MUST && v.Verdict !== VERDICT_PASS) continue
    if (v._localScore < 1e-3 || NO_CROSS.has(v._branch)) continue

    const ourCat = superCat(v._branch)
    let bestMeta = 0, bestName = '', bestBr = 0

    for (const other of stdVehicles) {
      if (other._branch === v._branch) continue
      if (superCat(other._branch) !== ourCat) continue
      if (other._era_int !== v._era_int) continue
      if (other.BR < v.BR - CROSS_BR_LOOKBACK || other.BR > v.BR + CROSS_BR_WINDOW) continue
      if (other.Verdict === VERDICT_SKIP) continue
      const eff = other._localScore * brDecay(other.BR, v.BR)
      if (eff > bestMeta) { bestMeta = eff; bestName = other.Name; bestBr = other.BR }
    }

    if (bestMeta > v._localScore * CROSS_THRESH) {
      v.Cross_Alt  = bestName
      v.Cross_Hint = `Better to use "${bestName}" (${bestBr.toFixed(1)}) — stronger in adjacent branch`
      if (v.Verdict === VERDICT_MUST) {
        v.Verdict = VERDICT_PASS
      } else if (bestMeta > v._localScore * CROSS_SKIP_THRESH && bestBr < v.BR) {
        v.Verdict = VERDICT_SKIP
        v.Skip_Reason = `Better to grind "${bestName}" (${bestBr.toFixed(1)}) from adjacent branch`
        v.Cross_Hint  = ''
      }
    }
  }

  // Pain eras (no MUST vehicle)
  const eraHasMust = {}
  for (const v of stdVehicles) {
    eraHasMust[v._era_int] ??= false
    if (v.Verdict === VERDICT_MUST) eraHasMust[v._era_int] = true
  }
  const painEras = new Set(
    Object.entries(eraHasMust).filter(([, has]) => !has).map(([e]) => +e)
  )

  // Pass 3: FILL
  const bySuperCatEra = {}
  for (const v of stdVehicles) {
    const key = `${superCat(v._branch)}_${v._era_int}`
    ;(bySuperCatEra[key] ??= { era: v._era_int, vehicles: [] }).vehicles.push(v)
  }

  for (const { era, vehicles: grp } of Object.values(bySuperCatEra)) {
    const mustCount = grp.filter(v => v.Verdict === VERDICT_MUST).length
    if (mustCount >= slots.value) continue

    const { br: bestAnchorBr } = bestAnchorForEra(grp, junkThresh, yellowThresh, slots.value)
    if (bestAnchorBr === 0) continue

    const need    = slots.value - mustCount
    const mustBrs = grp.filter(v => v.Verdict === VERDICT_MUST).map(v => v.BR)

    const candidates = grp
      .filter(v =>
        v._localScore >= junkThresh &&
        v.BR >= bestAnchorBr - BR_FILL_WINDOW &&
        v.BR <= bestAnchorBr &&
        v.Verdict !== VERDICT_MUST
      )
      .filter(cand => !mustBrs.some(mbr => Math.abs(cand.BR - mbr) <= BR_FILL_WINDOW))
      .sort((a, b) => b._localScore - a._localScore)

    let filled = 0
    for (const cand of candidates) {
      if (filled >= need) break
      cand.Verdict     = VERDICT_FILL
      cand.Skip_Reason = ''
      cand.Alt_Vehicle = ''
      filled++
    }
  }

  //Premium: PREM verdict + boost
  for (const v of premVehicles) {
    v.Verdict      = VERDICT_PREM
    v.Prem_Pain_Fix = painEras.has(v._era_int)

    const sameBranchStd = stdVehicles.filter(s => s._branch === v._branch)
    let bestFree = 0
    for (const s of sameBranchStd) {
      const eff = s._localScore * combinedPenalty(s._era_int, s.BR, v._era_int, v.BR)
      if (eff > bestFree) bestFree = eff
    }
    const premGrind = v._localScore * combinedPenalty(v._era_int, v.BR, v._era_int, v.BR, true)
    v.Prem_Boost = bestFree < 1e-3
      ? Math.round((premGrind / Math.max(v._localScore, 1e-3)) * 100) / 100
      : Math.round((premGrind / bestFree) * 100) / 100
  }

  // Clean dangling SKIP references
  const skipNames = new Set(stdVehicles.filter(v => v.Verdict === VERDICT_SKIP).map(v => v.Name))
  for (const v of stdVehicles) {
    if (skipNames.has(v.Alt_Vehicle)) {
      v.Skip_Reason = ''; v.Alt_Vehicle = ''; v.Verdict = VERDICT_PASS
    }
    if (skipNames.has(v.Cross_Alt)) { v.Cross_Alt = ''; v.Cross_Hint = '' }
  }

  return [...stdVehicles, ...premVehicles]
})

// Grid Data

const gridData = computed(() => {
  const vehicles = progressionData.value
  if (!vehicles.length) return null

  const std  = vehicles.filter(v => v.VehicleClass === STD_CLASS)
  const prem = vehicles.filter(v => v.VehicleClass !== STD_CLASS)

  // Collect eras
  const allEras = new Set()
  for (const v of vehicles) { const e = v._era_int; if (e >= 1 && e <= 8) allEras.add(e) }
  const eras = [...allEras].sort((a, b) => a - b)

  // Determine columns
  const hasShop = std.some(v => parseInt(v.vdb_shop_column ?? -1) >= 0)

  let colMap = null, numCols = 0, typesInDf = null

  if (hasShop) {
    const rawCols = [...new Set(
      std.map(v => parseInt(v.vdb_shop_column ?? -1)).filter(c => c >= 0)
    )].sort((a, b) => a - b)
    colMap  = Object.fromEntries(rawCols.map((old, i) => [old, i]))
    numCols = rawCols.length
  } else {
    typesInDf = [...new Set(std.map(v => v._branch))]
    numCols   = typesInDf.length
  }

  function getCellVehicles(era, colIdx) {
    let cell
    if (hasShop) {
      cell = std.filter(v => {
        const c = colMap[parseInt(v.vdb_shop_column ?? -1)]
        return v._era_int === era && c === colIdx
      })
    } else {
      const brName = typesInDf?.[colIdx]
      cell = std.filter(v => v._era_int === era && v._branch === brName)
    }
    return cell.sort((a, b) => {
      const ar = a.vdb_shop_row ?? 99999, br = b.vdb_shop_row ?? 99999
      if (ar !== br) return ar - br
      return (a.vdb_shop_order ?? 99999) - (b.vdb_shop_order ?? 99999)
    })
  }

  function getPremVehicles(era) {
    return prem
      .filter(v => v._era_int === era)
      .sort((a, b) => (a.vdb_shop_order ?? a.BR * 10000) - (b.vdb_shop_order ?? b.BR * 10000))
  }

  return { eras, numCols, typesInDf, getCellVehicles, getPremVehicles }
})

// Group bracketing

/**
 * Takes a flat list of vehicles for a cell and returns a list of items:
 *  { isGroup: false, vehicle, key } or
 *  { isGroup: true,  vehicles, groupLabel, key }
 */
function groupedCells(cellVehicles) {
  const result  = []
  const seenGrp = new Map()

  for (const v of cellVehicles) {
    const g = (v.vdb_shop_group || '').trim()
    if (g) {
      if (seenGrp.has(g)) {
        result[seenGrp.get(g)].vehicles.push(v)
      } else {
        seenGrp.set(g, result.length)
        result.push({
          isGroup:    true,
          groupLabel: v.Name.trim(),
          vehicles:   [v],
          key:        `grp-${g}`,
        })
      }
    } else {
      result.push({ isGroup: false, vehicle: v, key: `v-${v._idx}` })
    }
  }
  return result
}

// Stats

function countByVerdict(verdict) {
  return progressionData.value.filter(v => v.Verdict === verdict).length
}

// VehicleCard
const VehicleCard = {
  name: 'VehicleCard',
  props: {
    vehicle: { type: Object, required: true },
    grouped: { type: Boolean, default: false },
  },
  emits: ['click'],
  setup(props, { emit }) {
    return () => {
      const veh = props.vehicle
      const vc  = VERDICT_COLORS[veh.Verdict] ?? VERDICT_COLORS.PASS

      const nameStr  = (CLASS_PREFIX[veh.VehicleClass] || '') + (veh.Name ?? '')
      const brStr    = parseFloat(veh.BR || 0).toFixed(1)
      const wrStr    = parseFloat(veh.WR || 0).toFixed(1)
      const kdStr    = parseFloat(veh.KD || 0).toFixed(1)
      const metaStr  = parseFloat(veh._localScore || 0).toFixed(0)
      const typeIcon = TYPE_ICON[veh._branch] || '🔧'
      const brColor  = CLASS_BR_COLOR[veh.VehicleClass] || '#64748b'
      const nameColor = brColor === '#64748b' ? '#e2e8f0' : brColor

      const cardStyle = {
        borderLeft:      `4px solid ${vc.border}`,
        borderTop:       `1px solid ${vc.border}22`,
        borderRight:     `1px solid ${vc.border}22`,
        borderBottom:    `1px solid ${vc.border}22`,
        backgroundColor: vc.bg,
        '--glow':        vc.border,
      }

      // Boost label for premium vehicles
      const b = veh.Prem_Boost
      let boostLabel = null
      if (b && b >= 0.01) {
        if      (b >= 1.05) boostLabel = { text: `⚡ Grind ×${b.toFixed(1)} vs free`, color: '#34d399' }
        else if (b >= 0.95) boostLabel = { text: `≈ Parity ×${b.toFixed(1)}`,          color: '#94a3b8' }
        else                boostLabel = { text: `↓ Weaker ×${b.toFixed(1)}`,            color: '#f87171' }
      }

      // Hint nodes
      const hints = []
      if (veh.Cross_Hint)
        hints.push(h('div', { class: 'tc-hint tc-hint--cross' }, veh.Cross_Hint))
      if (veh.Verdict === 'SKIP' && veh.Skip_Reason)
        hints.push(h('div', { class: 'tc-hint tc-hint--skip' }, veh.Skip_Reason))
      if (veh.Verdict === 'PREM') {
        if (veh.Prem_Pain_Fix)
          hints.push(h('div', { class: 'tc-hint tc-hint--prem' }, '👑 Helps bypass painful rank'))
        if (boostLabel)
          hints.push(h('div', { class: 'tc-hint tc-hint--boost', style: { color: boostLabel.color } }, boostLabel.text))
        if (!veh.Prem_Pain_Fix && !boostLabel)
          hints.push(h('div', { class: 'tc-hint tc-hint--prem' }, '★ Premium'))
      }

      return h(
        'div',
        {
          class:   ['tree-card', { 'tree-card--grouped': props.grouped }],
          style:   cardStyle,
          onClick: () => emit('click'),
        },
        [
          // Header row
          h('div', { class: 'tc-header' }, [
            h('span', { class: 'tc-type-icon', title: veh._branch }, typeIcon),
            h('span', { class: 'tc-name', style: { color: nameColor } }, nameStr),
            h('span', { class: 'tc-br',   style: { color: brColor  } }, brStr),
            h('span', { class: 'tc-verdict' }, vc.icon),
          ]),
          // Stats row
          h('div', { class: 'tc-stats' }, [
            h('span', { class: 'tc-stat' }, [h('span', { class: 'tc-stat-label' }, 'WR'),   `${wrStr}%`]),
            h('span', { class: 'tc-stat' }, [h('span', { class: 'tc-stat-label' }, 'K/D'),  kdStr      ]),
            h('span', { class: 'tc-stat' }, [h('span', { class: 'tc-stat-label' }, 'META'), metaStr    ]),
          ]),
          // Hints
          ...hints,
        ]
      )
    }
  },
}
</script>

<style scoped>
/* Root */
.prog-root {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Controls bar */
.controls-bar {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  padding: 10px 14px;
}
.controls-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}
.ctrl-nation {
  max-width: 200px;
  flex-shrink: 0;
}
.ctrl-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.ctrl-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #475569;
  text-transform: uppercase;
}
.branch-toggle { flex-shrink: 0; }

/* Stats badges */
.stats-badges {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-left: auto;
}
.badge {
  display: inline-flex;
  align-items: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  border-radius: 5px;
  padding: 2px 8px;
  white-space: nowrap;
}
.badge-total { background: rgba(148,163,184,0.10); color: #94a3b8; }
.badge-must  { background: rgba(16,185,129,0.12);  color: #10b981; }
.badge-fill  { background: rgba(56,189,248,0.12);  color: #38bdf8; }
.badge-skip  { background: rgba(248,113,113,0.12); color: #f87171; }
.badge-prem  { background: rgba(167,139,250,0.12); color: #a78bfa; }

/* Type chips */
.type-toggles { display: flex; flex-wrap: wrap; }
.type-chip { cursor: pointer; font-size: 11px !important; transition: opacity 0.15s; }
.type-chip:hover { opacity: 0.8; }

/* Legend */
.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 4px 2px;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #64748b;
}
.legend-icon { font-size: 12px; }
.legend-text { white-space: nowrap; }

/* Scroll container */
.prog-scroll {
  overflow: auto;
  flex: 1;
  max-height: calc(100vh - 280px);
  padding-bottom: 12px;
}

/* CSS Grid */
.prog-grid {
  display: grid;
  gap: 4px;
  align-items: start;
  min-width: max-content;
}

/* Header row cells */
.grid-header-rank,
.grid-header-col,
.grid-header-prem {
  background: #1e293b;
  border-radius: 4px;
  padding: 6px 4px;
  text-align: center;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.grid-header-rank { color: #475569; }
.grid-header-col  { color: #475569; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.grid-header-prem { color: #a78bfa; }

/* Rank label */
.rank-label-cell {
  background: #162032;
  border-radius: 4px;
  padding: 8px 4px;
  text-align: center;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: 52px;
  padding-top: 10px;
}
.rank-roman {
  font-family: 'Rajdhani', 'Barlow Condensed', sans-serif;
  font-size: 24px;
  font-weight: 800;
  color: #a7f3d0;
  line-height: 1;
}

/* Standard cell */
.prog-cell {
  min-height: 52px;
  padding: 2px;
}

/* Premium cell */
.prem-cell {
  min-height: 52px;
  padding: 2px;
  background: rgba(167, 139, 250, 0.03);
  border-radius: 4px;
  border: 1px dashed rgba(167, 139, 250, 0.15);
}

/* Empty cell */
.empty-cell {
  background: rgba(15, 23, 42, 0.4);
  border: 1px dashed #1e293b;
  border-radius: 4px;
  min-height: 52px;
}

/* Group bracket */
.group-bracket {
  border-left:   2px solid #334155;
  border-bottom: 1px solid #1e293b;
  border-top:    1px solid #1e293b;
  border-right:  1px solid #1e293b;
  border-radius: 0 4px 4px 0;
  padding: 4px 0;
  margin-bottom: 4px;
  background: rgba(30, 41, 59, 0.35);
}
.group-label {
  font-size: 8px;
  color: #475569;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0 4px 2px 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
/* Cards inside a group lose their outer border-radius on connecting sides */
.group-bracket .tree-card:not(:last-child) {
  border-bottom-left-radius:  0;
  border-bottom-right-radius: 0;
  margin-bottom: 1px;
}
.group-bracket .tree-card:not(:first-child) {
  border-top-left-radius:  0;
  border-top-right-radius: 0;
}

/* Vehicle Card */
</style>

<!-- Global (non-scoped) styles for the VehicleCard sub-component -->
<style>
.tree-card {
  position: relative;
  border-radius: 0 5px 5px 0;
  padding: 5px 8px;
  margin-bottom: 4px;
  box-sizing: border-box;
  cursor: pointer;
  transition: box-shadow 0.15s, transform 0.12s, filter 0.12s;
  min-width: 130px;
}
.tree-card:hover {
  transform: translateY(-1px) translateX(1px);
  box-shadow: 3px 4px 16px var(--glow, #1e3a5f66);
  filter: brightness(1.08);
}
.tree-card--grouped {
  margin-bottom: 0;
}

/* Header */
.tc-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 3px;
}
.tc-type-icon {
  font-size: 10px;
  flex-shrink: 0;
  opacity: 0.7;
}
.tc-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tc-br {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}
.tc-verdict {
  font-size: 9px;
  flex-shrink: 0;
}

/* Stats */
.tc-stats {
  display: flex;
  gap: 8px;
}
.tc-stat {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #94a3b8;
}
.tc-stat-label {
  font-size: 9px;
  color: #475569;
  margin-right: 2px;
}

/* Hints */
.tc-hint {
  font-size: 9px;
  margin-top: 5px;
  padding-top: 5px;
  line-height: 1.4;
}
.tc-hint--cross {
  color: #7dd3fc;
  border-top: 1px solid rgba(125, 211, 252, 0.20);
}
.tc-hint--skip {
  color: #fecaca;
  border-top: 1px solid rgba(248, 113, 113, 0.25);
}
.tc-hint--prem {
  color: #c4b5fd;
  border-top: 1px solid rgba(167, 139, 250, 0.25);
}
.tc-hint--boost {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  border-top: 1px solid rgba(167, 139, 250, 0.15);
  padding-top: 3px;
  margin-top: 3px;
}
</style>
