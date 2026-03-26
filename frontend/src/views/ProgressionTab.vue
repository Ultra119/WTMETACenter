<template>
  <div>
    <!-- Controls -->
    <v-row dense class="mb-3" align="center">
      <v-col cols="12" sm="4">
        <v-select
          v-model="nation"
          :items="nationOptions"
          label="Нация"
          prepend-inner-icon="mdi-flag"
          density="compact"
          variant="outlined"
          hide-details
        />
      </v-col>
      <v-col cols="12" sm="3">
        <v-select
          v-model="colorBy"
          :items="colorByOptions"
          label="Цвет по"
          prepend-inner-icon="mdi-palette"
          density="compact"
          variant="outlined"
          hide-details
        />
      </v-col>
      <v-col>
        <div class="tab-info">
          {{ treeVehicles.length }} машин в дереве · по строкам прокачки
        </div>
      </v-col>
    </v-row>

    <!-- Legend -->
    <div class="legend-row mb-3">
      <v-chip v-for="cls in CLASS_LIST" :key="cls.label" size="x-small" :color="cls.color" class="mr-1">
        {{ cls.label }}
      </v-chip>
    </div>

    <!-- Tree grid -->
    <div v-if="ranks.length" class="tree-scroll">
      <div v-for="rank in ranks" :key="rank" class="rank-row">
        <div class="rank-label">R{{ rank }}</div>
        <div class="rank-vehicles">
          <div
            v-for="v in vehiclesByRank[rank]"
            :key="v.vdb_identifier || v.Name"
            class="tree-card"
            :style="{ borderColor: cardBorderColor(v), '--glow': cardBorderColor(v) }"
            @click="openVehicle(v)"
            :title="vehicleDisplayName(v) + ' · BR ' + fmtBR(v.BR)"
          >
            <div class="tc-name" :style="{ color: nameColor(v) }">{{ v.Name }}</div>
            <div class="tc-meta">
              <span class="tc-br">{{ fmtBR(v.BR) }}</span>
              <span class="tc-score" :style="{ color: scoreColorFn(v) }">
                {{ scoreVal(v)?.toFixed(0) }}
              </span>
            </div>
            <!-- класс-бейдж -->
            <div v-if="v.VehicleClass !== 'Standard'" class="tc-badge">
              {{ CLASS_PREFIX[v.VehicleClass] }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <v-alert v-else type="info" variant="tonal" density="compact">
      Нет данных дерева прокачки для выбранной нации. Убедитесь, что build_data.py сохраняет поле vdb_shop_rank.
    </v-alert>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { useDataStore } from '../stores/useDataStore.js'
import {
  vehicleDisplayName, fmtBR, metaColor, farmColor, CLASS_PREFIX,
} from '../composables/useVehicleFormatting.js'

const store       = useDataStore()
const openVehicle = inject('openVehicle')

const nation  = ref('USSR')
const colorBy = ref('META_SCORE')

const colorByOptions = [
  { title: 'META Score',  value: 'META_SCORE'  },
  { title: 'FARM Score',  value: 'FARM_SCORE'  },
  { title: 'Win Rate',    value: 'WR'          },
]

const nationOptions = computed(() => store.nations.filter(n => n !== 'All'))

const CLASS_LIST = [
  { label: 'Standard',    color: 'surface' },
  { label: 'Premium',     color: 'warning' },
  { label: 'Pack',        color: 'success' },
  { label: 'Squadron',    color: 'info'    },
  { label: 'Marketplace', color: 'purple'  },
  { label: 'Gift',        color: 'pink'    },
  { label: 'Event',       color: 'error'   },
]

const CLASS_COLORS = {
  Standard: '#1e293b', Premium: '#92400e', Pack: '#065f46',
  Squadron: '#1e3a5f', Marketplace: '#4c1d95',
  Gift: '#831843', Event: '#7f1d1d',
}

// Все техники выбранной нации, у которых есть позиция в магазине
const treeVehicles = computed(() => {
  const allForNation = store.allVehicles.filter(v =>
    v.Nation === nation.value &&
    v.Mode   === store.mode &&
    (v.vdb_shop_rank ?? 0) > 0
  )

  // Дедупликация по Name — берём только одну запись (лучшую по META)
  const seen = new Map()
  for (const v of allForNation) {
    const key = v.vdb_identifier || v.Name
    if (!seen.has(key) || v.META_SCORE > seen.get(key).META_SCORE)
      seen.set(key, v)
  }
  return [...seen.values()]
})

const ranks = computed(() => {
  const rs = [...new Set(treeVehicles.value.map(v => v.vdb_shop_rank ?? 0))]
    .filter(r => r > 0)
    .sort((a, b) => a - b)
  return rs
})

const vehiclesByRank = computed(() => {
  const byRank = {}
  for (const v of treeVehicles.value) {
    const r = v.vdb_shop_rank ?? 0
    if (!r) continue
    if (!byRank[r]) byRank[r] = []
    byRank[r].push(v)
  }
  // Сортируем по колонке внутри каждого ранга
  for (const r of Object.keys(byRank))
    byRank[r].sort((a, b) => (a.vdb_shop_order ?? 0) - (b.vdb_shop_order ?? 0))
  return byRank
})

function scoreVal(v) {
  return colorBy.value === 'META_SCORE'
    ? v.META_SCORE
    : colorBy.value === 'FARM_SCORE'
      ? v.FARM_SCORE
      : v.WR
}

function scoreColorFn(v) {
  const val = scoreVal(v)
  if (colorBy.value === 'WR') {
    if (val >= 55) return '#34d399'
    if (val <  48) return '#f87171'
    return '#e2e8f0'
  }
  return colorBy.value === 'FARM_SCORE' ? farmColor(val) : metaColor(val)
}

function cardBorderColor(v) {
  return scoreColorFn(v)
}

function nameColor(v) {
  if (v.VehicleClass === 'Premium')     return '#fbbf24'
  if (v.VehicleClass === 'Pack')        return '#34d399'
  if (v.VehicleClass === 'Squadron')    return '#60a5fa'
  if (v.VehicleClass === 'Marketplace') return '#a78bfa'
  if (v.VehicleClass === 'Event')       return '#f87171'
  return '#e2e8f0'
}
</script>

<style scoped>
.tab-info {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #64748b;
}
.legend-row { display: flex; flex-wrap: wrap; gap: 4px; }

.tree-scroll {
  overflow-x: auto;
  overflow-y: auto;
  max-height: calc(100vh - 240px);
}

.rank-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
  min-height: 72px;
}

.rank-label {
  font-family: 'Rajdhani', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #475569;
  width: 36px;
  flex-shrink: 0;
  padding-top: 8px;
  text-align: center;
}

.rank-vehicles {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.tree-card {
  position: relative;
  background: #0f172a;
  border: 1px solid var(--glow, #1e3a5f);
  border-radius: 6px;
  padding: 6px 10px;
  min-width: 120px;
  max-width: 150px;
  cursor: pointer;
  transition: box-shadow .15s, transform .1s;
  flex-shrink: 0;
}
.tree-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 0 10px var(--glow, #1e3a5f);
}

.tc-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.tc-meta {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
}
.tc-br    { color: #94a3b8; }
.tc-score { font-weight: 700; }

.tc-badge {
  position: absolute;
  top: 3px;
  right: 4px;
  font-size: 10px;
}
</style>
