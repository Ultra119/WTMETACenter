import { ref, shallowRef } from 'vue'

const CACHE_SIZE = 12

export function decodeStats(mode, blob, attrs) {
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

export function useDataset() {
  const metaInfo = shallowRef(null)
  const loading  = ref(false)
  const error    = shallowRef(null)

  const _basePath   = ref('')
  const _attrsAC    = new AbortController()
  const _periodAC   = ref(new AbortController())
  const _attrs      = shallowRef(null)
  const _attrsReady = ref(null)
  const _cache      = new Map()

  function _bust() {
    const hash = metaInfo.value?.dataset_hash ?? ''
    return hash ? `?v=${hash.slice(0, 8)}` : ''
  }

  function _remember(key, rows) {
    if (_cache.has(key)) _cache.delete(key)
    _cache.set(key, rows)
    while (_cache.size > CACHE_SIZE) {
      _cache.delete(_cache.keys().next().value)
    }
  }

  async function _loadAttrs() {
    if (_attrs.value) return _attrs.value
    if (!_attrsReady.value) {
      _attrsReady.value = (async () => {
        const res = await fetch(`${_basePath.value}/data/vehicles.json${_bust()}`, {
          signal: _attrsAC.signal,
        })
        if (!res.ok) throw new Error(`vehicles.json: ${res.status}`)
        return res.json()
      })()
    }
    try {
      _attrs.value = await _attrsReady.value
      return _attrs.value
    } catch (e) {
      _attrsReady.value = null
      throw e
    }
  }

  async function loadPeriod(period, signal) {
    const entry = metaInfo.value?.index?.periods?.[period]
    if (!entry) throw new Error(`period ${period} is not in index.json`)

    const attrs = await _loadAttrs()
    const modes = Object.keys(entry.modes ?? {})
    const blobs = await Promise.all(modes.map(async m => {
      const res = await fetch(`${_basePath.value}/data/stats/${period}/${m}.json${_bust()}`, { signal })
      if (!res.ok) throw new Error(`stats/${period}/${m}.json: ${res.status}`)
      return [m, await res.json()]
    }))

    return blobs.flatMap(([m, blob]) => decodeStats(m, blob, attrs))
  }

  async function getPeriod(period, signal) {
    const hit = _cache.get(period)
    if (hit) {
      _cache.delete(period)
      _cache.set(period, hit)
      return hit
    }
    const rows = await loadPeriod(period, signal)
    _remember(period, rows)
    return rows
  }

  async function load(basePath = '') {
    _basePath.value = basePath
    loading.value   = true
    error.value     = null
    try {
      const metaRes = await fetch(`${basePath}/meta_info.json`)
      if (!metaRes.ok) throw new Error(`meta_info.json: ${metaRes.status}`)
      const meta = await metaRes.json()

      const indexRes = await fetch(`${basePath}/data/index.json${_bust()}`)
      if (!indexRes.ok) throw new Error(`data/index.json: ${indexRes.status}`)
      metaInfo.value = { ...meta, index: await indexRes.json() }

      return metaInfo.value
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  function abortPeriods() {
    _periodAC.value.abort()
    _periodAC.value = new AbortController()
    return _periodAC.value.signal
  }

  const periods = () => metaInfo.value?.periods ?? ['All']

  function clearError() { error.value = null }

  return {
    metaInfo, loading, error,
    periods, load, loadPeriod, getPeriod, abortPeriods, clearError,
  }
}
