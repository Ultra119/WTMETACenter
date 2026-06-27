import { defineStore } from 'pinia'
import { ref, shallowRef, computed, watch, watchEffect } from 'vue'

export const WT_BR_STEPS = [
  1.0,1.3,1.7, 2.0,2.3,2.7, 3.0,3.3,3.7, 4.0,4.3,4.7,
  5.0,5.3,5.7, 6.0,6.3,6.7, 7.0,7.3,7.7, 8.0,8.3,8.7,
  9.0,9.3,9.7, 10.0,10.3,10.7, 11.0,11.3,11.7, 12.0,12.3,12.7, 13.0,
]

const BR_MIN = Math.min(...WT_BR_STEPS)
const BR_MAX = Math.max(...WT_BR_STEPS)

const TYPE_CATEGORIES = {
  Ground:      ['medium_tank','light_tank','heavy_tank','tank_destroyer','spaa'],
  Aviation:    ['fighter','bomber','assault'],
  Helicopters: ['attack_helicopter','utility_helicopter'],
  LargeFleet:  ['destroyer','heavy_cruiser','light_cruiser','battleship','battlecruiser'],
  SmallFleet:  ['boat','heavy_boat','frigate','barge'],
}

function typeToCategory(t) {
  for (const [cat, types] of Object.entries(TYPE_CATEGORIES))
    if (types.includes(t)) return cat
  return null
}

function debounce(fn, delay) {
  let timer = null
  return (...args) => {
    if (timer !== null) clearTimeout(timer)
    timer = setTimeout(() => { timer = null; fn(...args) }, delay)
  }
}

export function formatPeriodLabel(p) {
  if (!p || p === 'All') return 'All Periods'
  const parts = p.split('-')
  if (parts.length !== 2) return p
  try {
    const d = new Date(parseInt(parts[1], 10), parseInt(parts[0], 10) - 1, 1)
    return d.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
  } catch {
    return p
  }
}

export const useDataStore = defineStore('data', () => {

  const allVehicles = ref([])
  const metaInfo    = ref(null)
  const loading     = ref(false)
  const loadError   = ref(null)

  const _basePath = ref('')

  const tabFilterConfig = ref(null)

  function setTabFilters(cfg) { tabFilterConfig.value = cfg  }
  function clearTabFilters()  { tabFilterConfig.value = null }

  const currentPeriod = ref('All')

  const periods = computed(() => metaInfo.value?.periods ?? ['All'])

  const mode       = ref('Realistic')
  const minBattles = ref(50)
  const brRange    = ref([BR_MIN, BR_MAX])
  const classes    = ref(['Standard','Premium','Pack','Squadron','Marketplace','Gift','Event'])

  const showGround      = ref(true)
  const showAviation    = ref(true)
  const showHelicopters = ref(false)
  const showLargeFleet  = ref(false)
  const showSmallFleet  = ref(false)

  const _minBattles = ref(50)
  const _brRange    = ref([BR_MIN, BR_MAX])

  const commitRange   = debounce(v => { _brRange.value    = v }, 220)
  const commitBattles = debounce(v => { _minBattles.value = v }, 220)
  watch(brRange,    v => commitRange([...v]))
  watch(minBattles, v => commitBattles(v))

  const searchQuery = ref('')
  const metaTabActive = ref(false)

  let _vehicleAC = null

  async function _loadVehicles() {
    if (_vehicleAC) _vehicleAC.abort()
    _vehicleAC = new AbortController()
    const { signal } = _vehicleAC

    const hash = metaInfo.value?.dataset_hash ?? ''
    const qs   = hash ? `?v=${hash.slice(0, 8)}` : ''
    const url  = `${_basePath.value}/data/mega_db_${currentPeriod.value}.json${qs}`

    const res = await fetch(url, { signal })
    if (!res.ok) throw new Error(`mega_db_${currentPeriod.value}.json: ${res.status}`)
    allVehicles.value = await res.json()
  }

  let _periodInitialized = false

  async function loadData(basePath = '') {
    _basePath.value  = basePath
    loading.value    = true
    loadError.value  = null
    try {
      const metaRes = await fetch(`${basePath}/meta_info.json`)
      if (!metaRes.ok) throw new Error(`meta_info.json: ${metaRes.status}`)
      metaInfo.value = await metaRes.json()

      const available = metaInfo.value?.periods ?? ['All']

      if (!_periodInitialized) {
        _periodInitialized = true
        const latestMonth = available.find(p => p !== 'All')
        currentPeriod.value = latestMonth ?? available[0] ?? 'All'
      } else if (!available.includes(currentPeriod.value)) {
        currentPeriod.value = available[0] ?? 'All'
      }

      await _loadVehicles()
    } catch (e) {
      if (e.name === 'AbortError') return
      loadError.value = e.message
      console.error('[DataStore]', e)
    } finally {
      loading.value = false
    }
  }

  const _periodCache = new Map()

  function _periodToDate(p) {
    const parts = String(p).split('-')
    if (parts.length !== 2) return 0
    const t = new Date(parseInt(parts[1], 10), parseInt(parts[0], 10) - 1, 1).getTime()
    return isNaN(t) ? 0 : t
  }

  async function _getPeriodVehicles(period) {
    if (period === currentPeriod.value) return allVehicles.value
    if (_periodCache.has(period)) return _periodCache.get(period)

    const hash = metaInfo.value?.dataset_hash ?? ''
    const qs   = hash ? `?v=${hash.slice(0, 8)}` : ''
    const url  = `${_basePath.value}/data/mega_db_${period}.json${qs}`

    const res = await fetch(url)
    if (!res.ok) throw new Error(`mega_db_${period}.json: ${res.status}`)
    const data = await res.json()
    _periodCache.set(period, data)
    return data
  }

  async function fetchVehicleHistory({ name, nation, type, mode }) {
    const allPeriods = (metaInfo.value?.periods ?? []).filter(p => p !== 'All')
    const points = []

    for (const period of allPeriods) {
      try {
        const vehicles = await _getPeriodVehicles(period)
        const entry = vehicles.find(e =>
          e.Name === name && e.Nation === nation && e.Type === type && e.Mode === mode
        )
        if (entry) {
          points.push({
            period,
            label:   formatPeriodLabel(period),
            br:      entry.BR ?? null,
            wr:      entry.WR ?? null,
            kd:      entry.KD ?? null,
            meta:    entry.META_SCORE ?? null,
            farm:    entry.FARM_SCORE ?? null,
            battles: entry['Сыграно игр'] ?? null,
            netSl:   entry['Net SL за игру'] ?? null,
          })
        }
      } catch (e) {
        console.error('[DataStore] history fetch error:', period, e)
      }
    }

    points.sort((a, b) => _periodToDate(a.period) - _periodToDate(b.period))
    return points
  }

  watch(currentPeriod, async () => {
    if (!metaInfo.value) return
    filtering.value = true
    loadError.value = null
    try {
      await _loadVehicles()
    } catch (e) {
      if (e.name === 'AbortError') return
      loadError.value = e.message
      filtering.value = false
      console.error('[DataStore] period switch error:', e)
    }
  })

  const activeTypes = computed(() => {
    const wanted = new Set()
    if (showGround.value)      wanted.add('Ground')
    if (showAviation.value)    wanted.add('Aviation')
    if (showHelicopters.value) wanted.add('Helicopters')
    if (showLargeFleet.value)  wanted.add('LargeFleet')
    if (showSmallFleet.value)  wanted.add('SmallFleet')
    if (wanted.size === 0) return []

    const all = metaInfo.value?.types ?? []
    return all.filter(t => {
      const cat = typeToCategory(t)
      return cat ? wanted.has(cat) : true
    })
  })

  const filteredVehicles = shallowRef([])
  const filtering = ref(false)

  let _filterVersion = 0

  watchEffect(() => {
    const vehicles    = allVehicles.value
    const currentMode = mode.value
    const brMin       = _brRange.value[0]
    const brMax       = _brRange.value[1]
    const minB        = _minBattles.value
    const cls         = [...classes.value]
    const types       = activeTypes.value

    const version = ++_filterVersion

    filtering.value = true

    setTimeout(() => {
      if (version !== _filterVersion) return
      filteredVehicles.value = !vehicles.length ? [] : vehicles.filter(v =>
        v.Mode === currentMode &&
        v.BR   >= brMin &&
        v.BR   <= brMax &&
        (v['Сыграно игр'] ?? 0) >= minB &&
        cls.includes(v.VehicleClass ?? 'Standard') &&
        types.includes(v.Type)
      )
      filtering.value = false
    }, 0)
  })

  const nations = computed(() => {
    const raw = metaInfo.value?.nations ?? []
    return ['All', ...raw]
  })

  return {
    allVehicles, metaInfo, loading, loadError,
    currentPeriod, periods,
    mode, minBattles, brRange, classes,
    showGround, showAviation, showHelicopters, showLargeFleet, showSmallFleet,
    filteredVehicles, activeTypes, nations, filtering,
    loadData,
    fetchVehicleHistory,
    tabFilterConfig, setTabFilters, clearTabFilters,
    BR_MIN, BR_MAX, WT_BR_STEPS,
    searchQuery,
    metaTabActive,
  }
})
