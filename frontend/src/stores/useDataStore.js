import { defineStore } from 'pinia'
import { ref, shallowRef, computed, watch } from 'vue'

export const FALLBACK_BR_STEPS = [
  1.0,1.3,1.7, 2.0,2.3,2.7, 3.0,3.3,3.7, 4.0,4.3,4.7,
  5.0,5.3,5.7, 6.0,6.3,6.7, 7.0,7.3,7.7, 8.0,8.3,8.7,
  9.0,9.3,9.7, 10.0,10.3,10.7, 11.0,11.3,11.7, 12.0,12.3,12.7, 13.0,
]

export function buildBrSteps(maxBr) {
  const steps = []
  for (let i = 0; i < 500; i++) {
    const br = (10 + 3 * i + Math.floor((i + 1) / 3)) / 10
    if (br > maxBr + 1e-9) break
    steps.push(br)
  }
  return steps
}

export function maxBrOf(rows) {
  let mx = 0
  for (const r of rows ?? []) {
    const b = Number(r?.BR)
    if (Number.isFinite(b) && b > mx) mx = b
  }
  return mx
}

export const WT_BR_STEPS = FALLBACK_BR_STEPS

const EMPTY_ROWS  = Object.freeze([])
const EMPTY_TYPES = new Set()

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
  const classes    = ref(['Standard','Premium','Pack','Squadron','Marketplace','Gift','Event'])

  const dataMaxBr = ref(0)
  const brCeiling = computed(() => {
    const fromData = dataMaxBr.value
    const fromMeta = Number(metaInfo.value?.max_br) || 0
    const fromRows = maxBrOf(allVehicles.value)
    return Math.max(fromData, fromMeta, fromRows, WT_BR_STEPS[WT_BR_STEPS.length - 1])
  })

  const brSteps = computed(() => buildBrSteps(brCeiling.value))
  const BR_MAX  = computed(() => brSteps.value[brSteps.value.length - 1])
  const BR_STEP_MIN = computed(() => brSteps.value[0])

  const brRange = ref([BR_STEP_MIN.value, BR_MAX.value])

  const showGround      = ref(true)
  const showAviation    = ref(true)
  const showHelicopters = ref(false)
  const showLargeFleet  = ref(false)
  const showSmallFleet  = ref(false)

  const _minBattles = ref(50)
  const _brRange    = ref([BR_STEP_MIN.value, BR_MAX.value])

  const commitRange   = debounce(v => { _brRange.value    = v }, 220)
  const commitBattles = debounce(v => { _minBattles.value = v }, 220)
  watch(brRange,    v => commitRange([...v]))
  watch(minBattles, v => commitBattles(v))

  const searchQuery = ref('')
  const metaTabActive = ref(false)
  const historyTabActive = ref(false)

  const _attrsAC  = new AbortController()
  let _vehiclesReady = null
  let _periodAC  = new AbortController()

  function _cacheBust() {
    const hash = metaInfo.value?.dataset_hash ?? ''
    return hash ? `?v=${hash.slice(0, 8)}` : ''
  }

  async function _loadVehicleAttrs() {
    if (_vehiclesReady) return _vehiclesReady
    _vehiclesReady = (async () => {
      const res = await fetch(`${_basePath.value}/data/vehicles.json${_cacheBust()}`, { signal: _attrsAC.signal })
      if (!res.ok) throw new Error(`vehicles.json: ${res.status}`)
      return res.json()
    })()
    try {
      return await _vehiclesReady
    } catch (e) {
      _vehiclesReady = null
      throw e
    }
  }

  function _decodeStats(mode, blob, attrs) {
    const columns = blob.columns ?? []
    const ids     = blob.identifier ?? []
    const rows    = blob.rows ?? []
    const out     = new Array(rows.length)

    for (let i = 0; i < rows.length; i++) {
      const values = rows[i]
      const id     = ids[i]
      const base   = attrs[id]
      const row    = base ? { ...base } : {}
      for (let c = 0; c < columns.length; c++) {
        const v = values[c]
        if (v !== null) row[columns[c]] = v
      }
      row.vdb_identifier = id
      row.Mode           = mode
      out[i] = row
    }
    return out
  }

  async function _loadPeriod(period, signal) {
    const index  = metaInfo.value?.index
    const entry  = index?.periods?.[period]
    if (!entry) throw new Error(`period ${period} is not in index.json`)

    const attrs  = await _loadVehicleAttrs()
    const modes  = Object.keys(entry.modes ?? {})
    const blobs  = await Promise.all(modes.map(async m => {
      const res = await fetch(`${_basePath.value}/data/stats/${period}/${m}.json${_cacheBust()}`, { signal })
      if (!res.ok) throw new Error(`stats/${period}/${m}.json: ${res.status}`)
      return [m, await res.json()]
    }))

    return blobs.flatMap(([m, blob]) => _decodeStats(m, blob, attrs))
  }

  async function _loadVehicles() {
    const period = currentPeriod.value
    const ac     = new AbortController()
    _periodAC.abort()
    _periodAC = ac
    const rows = await _loadPeriod(period, ac.signal)
    if (period !== currentPeriod.value) return
    allVehicles.value = rows
    dataMaxBr.value   = maxBrOf(rows)
    _followCeiling()
  }

  function _followCeiling() {
    const top = brCeiling.value
    const [lo, hi] = _brRange.value

    if (lo > top) return
    if (hi >= top - 1e-9) {
      if (hi !== top) {
        _brRange.value = [lo, top]
        brRange.value  = [lo, top]
      }
      return
    }
    if (hi === brSteps.value[brSteps.value.length - 2]) {
      _brRange.value = [lo, top]
      brRange.value  = [lo, top]
    }
  }

  let _periodInitialized = false
  let _seenPeriod = null

  async function loadData(basePath = '') {
    _basePath.value  = basePath
    loading.value    = true
    loadError.value  = null
    try {
      const metaRes = await fetch(`${basePath}/meta_info.json`)
      if (!metaRes.ok) throw new Error(`meta_info.json: ${metaRes.status}`)
      metaInfo.value = await metaRes.json()

      const indexRes = await fetch(`${basePath}/data/index.json${_cacheBust()}`)
      if (!indexRes.ok) throw new Error(`data/index.json: ${indexRes.status}`)
      metaInfo.value = { ...metaInfo.value, index: await indexRes.json() }

      const available = metaInfo.value?.periods ?? ['All']

      let next = currentPeriod.value

      if (!_periodInitialized) {
        _periodInitialized = true
        const latestMonth = available.find(p => p !== 'All')
        next = latestMonth ?? available[0] ?? 'All'
      } else if (!available.includes(currentPeriod.value)) {
        next = available[0] ?? 'All'
      }

      _seenPeriod = next
      currentPeriod.value = next

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

  async function _getPeriodVehicles(period, signal) {
    if (period === currentPeriod.value) return allVehicles.value
    if (_periodCache.has(period)) return _periodCache.get(period)

    const data = await _loadPeriod(period, signal)
    _periodCache.set(period, data)
    return data
  }

  async function fetchVehicleHistory({ name, nation, type, mode, signal }) {
    const allPeriods = (metaInfo.value?.periods ?? []).filter(p => p !== 'All')
    const points = []

    for (const period of allPeriods) {
      if (signal?.aborted) break
      try {
        const vehicles = await _getPeriodVehicles(period, signal)
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
        if (e.name === 'AbortError') break
        console.error('[DataStore] history fetch error:', period, e)
      }
    }

    if (signal?.aborted) throw new DOMException('aborted', 'AbortError')
    points.sort((a, b) => _periodToDate(a.period) - _periodToDate(b.period))
    return points
  }

  watch(currentPeriod, async () => {
    if (!metaInfo.value) return
    if (currentPeriod.value === _seenPeriod) return
    _seenPeriod = currentPeriod.value
    filtering.value = true
    loadError.value = null
    try {
      await _loadVehicles()
    } catch (e) {
      if (e.name !== 'AbortError') {
        loadError.value = e.message
        console.error('[DataStore] period switch error:', e)
      }
    } finally {
      filtering.value = false
    }
  })

  function clearLoadError() { loadError.value = null }

  const activeTypes = computed(() => {
    const wanted = new Set()
    if (showGround.value)      wanted.add('Ground')
    if (showAviation.value)    wanted.add('Aviation')
    if (showHelicopters.value) wanted.add('Helicopters')
    if (showLargeFleet.value)  wanted.add('LargeFleet')
    if (showSmallFleet.value)  wanted.add('SmallFleet')
    if (wanted.size === 0) return EMPTY_TYPES

    const all = metaInfo.value?.types ?? []
    return new Set(all.filter(t => {
      const cat = typeToCategory(t)
      return cat ? wanted.has(cat) : true
    }))
  })

  const filteredVehicles = computed(() => {
    const vehicles = allVehicles.value
    if (!vehicles.length) return EMPTY_ROWS

    const currentMode = mode.value
    const brMin       = _brRange.value[0]
    const brMax       = _brRange.value[1]
    const minB        = _minBattles.value
    const cls         = classes.value
    const typeSet     = activeTypes.value

    return vehicles.filter(v =>
      v.Mode === currentMode &&
      v.BR   >= brMin &&
      v.BR   <= brMax &&
      (v['Сыграно игр'] ?? 0) >= minB &&
      cls.includes(v.VehicleClass ?? 'Standard') &&
      typeSet.has(v.Type)
    )
  })

  const filtering = ref(false)

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
    loadData, clearLoadError,
    fetchVehicleHistory,
    tabFilterConfig, setTabFilters, clearTabFilters,
    BR_MIN: BR_STEP_MIN, BR_MAX, BR_STEP_MIN, brSteps, brCeiling, WT_BR_STEPS,
    searchQuery,
    metaTabActive,
    historyTabActive,
  }
})
