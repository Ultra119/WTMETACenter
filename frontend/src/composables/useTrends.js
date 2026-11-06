import { shallowRef } from 'vue'

const TREND_METRICS = ['META_SCORE', 'WR', 'BR']

function _key(name, nation, type, mode) {
  return `${name}||${nation}||${type}||${mode}`
}

export function diffPoints(points) {
  if (!points || points.length < 2) return null

  const first = points[0]
  const last  = points[points.length - 1]

  const out = {}
  let any = false
  for (const metric of TREND_METRICS) {
    const a = first[metric]
    const b = last[metric]
    if (a == null || b == null || !Number.isFinite(a) || !Number.isFinite(b)) {
      out[metric] = null
      continue
    }
    out[metric] = Number((b - a).toFixed(2))
    if (out[metric] !== 0) any = true
  }

  if (!any) return null
  out.from = first.period
  out.to   = last.period
  return out
}

function _periodDate(p) {
  const parts = String(p).split('-')
  if (parts.length !== 2) return 0
  return Number(parts[1]) * 12 + Number(parts[0])
}

export function useTrends() {
  const trends = shallowRef(new Map())
  let _token = 0

  async function build(store) {
    const token = ++_token
    const periods = [...(store.metaInfo?.periods ?? [])]
      .filter(p => p !== 'All')
      .sort((a, b) => _periodDate(a) - _periodDate(b))
    if (!periods.length) return

    const map = new Map()

    for (const period of periods) {
      let rows
      try {
        rows = await store.getPeriodRows(period)
      } catch {
        continue
      }
      if (token !== _token) return

      for (const r of rows) {
        const key = _key(r.Name, r.Nation, r.Type, r.Mode)
        let entry = map.get(key)
        if (!entry) { entry = []; map.set(key, entry) }
        entry.push({
          period,
          META_SCORE: r.META_SCORE,
          WR: r.WR,
          BR: r.BR,
        })
      }
    }

    const out = new Map()
    for (const [key, points] of map) {
      const d = diffPoints(points)
      if (d) out.set(key, d)
    }

    if (token === _token) trends.value = out
  }

  function trendFor(vehicle) {
    if (!vehicle) return null
    return trends.value.get(_key(vehicle.Name, vehicle.Nation, vehicle.Type, vehicle.Mode)) ?? null
  }

  return { trends, build, trendFor }
}
