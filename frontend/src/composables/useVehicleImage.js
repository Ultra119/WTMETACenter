import { ref, watch } from 'vue'

const DATAMINE_OWNER = 'gszabi99'
const DATAMINE_REPO  = 'War-Thunder-Datamine'
const DATAMINE_REF   = 'refs/tags/2.57.0.42'
const DATAMINE_ROOT  = 'tex.vromfs.bin_u'

const CDN_BASE =
  `https://rawcdn.githack.com/${DATAMINE_OWNER}/${DATAMINE_REPO}/${DATAMINE_REF}/${DATAMINE_ROOT}`

const GROUND_TYPES = new Set([
  'medium_tank', 'light_tank', 'heavy_tank', 'tank_destroyer', 'spaa',
])
const AIR_TYPES = new Set([
  'fighter', 'bomber', 'assault',
  'attack_helicopter', 'utility_helicopter',
])
const SHIP_TYPES = new Set([
  'destroyer', 'heavy_cruiser', 'light_cruiser', 'battleship', 'battlecruiser',
  'boat', 'heavy_boat', 'frigate', 'barge',
])

function typeToFolder(vehicleType) {
  if (!vehicleType) return null
  const t = vehicleType.toLowerCase()
  if (GROUND_TYPES.has(t)) return 'tanks'
  if (AIR_TYPES.has(t))    return 'aircrafts'
  if (SHIP_TYPES.has(t))   return 'ships'
  return null
}


export function vehicleImageUrl(identifier, vehicleType) {
  if (!identifier || !vehicleType) return null
  const folder = typeToFolder(vehicleType)
  if (!folder) return null
  const id = identifier.trim().toLowerCase()
  return `${CDN_BASE}/${folder}/${id}.png`
}

const _cache = new Map()

export function useVehicleImage(identifierRef, typeRef) {
  const src    = ref(null)
  const loaded = ref(false)
  const error  = ref(false)

  function probe() {
    const identifier = identifierRef.value?.trim().toLowerCase() ?? ''
    const type = typeRef.value

    src.value    = null
    loaded.value = false
    error.value  = false

    if (!identifier || !type) return

    const url = vehicleImageUrl(identifier, type)
    if (!url) return
    src.value = url

    const cached = _cache.get(identifier)
    if (cached === 'ok')    { loaded.value = true;  return }
    if (cached === 'error') { error.value  = true; src.value = null; return }

    const img  = new Image()
    img.onload = () => {
      _cache.set(identifier, 'ok')
      if (src.value === url) loaded.value = true
    }
    img.onerror = () => {
      _cache.set(identifier, 'error')
      if (src.value === url) { error.value = true; src.value = null }
    }
    img.src = url
  }

  watch([identifierRef, typeRef], probe, { immediate: true })

  return { src, loaded, error }
}

export function vehicleImageCached(identifier) {
  return identifier ? _cache.get(identifier.trim().toLowerCase()) === 'ok' : false
}
