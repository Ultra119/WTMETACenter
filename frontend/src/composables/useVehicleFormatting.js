import { useI18n } from 'vue-i18n'

export const NATION_FLAG = {
  usa:         '🇺🇸', germany:    '🇩🇪', ussr:        '🇷🇺',
  britain:     '🇬🇧', japan:      '🇯🇵', italy:       '🇮🇹',
  france:      '🇫🇷', sweden:     '🇸🇪', israel:      '🇮🇱',
  china:       '🇨🇳',
}

export const CLASS_PREFIX = {
  Premium:    'mdi-star',
  Pack:       'mdi-package-variant',
  Squadron:   'mdi-star-four-points',
  Marketplace:'mdi-store',
  Gift:       'mdi-gift',
  Event:      'mdi-ticket',
  Standard:   '',
}

const CLASS_ICON_COLOR = {
  Premium:     '#fbbf24',
  Pack:        '#60a5fa',
  Squadron:    '#34d399',
  Marketplace: '#a78bfa',
  Gift:        '#f472b6',
  Event:       '#fb923c',
}

export function vehicleClassMdiIcon(v) {
  return CLASS_PREFIX[v?.VehicleClass ?? 'Standard'] ?? ''
}

export function vehicleClassMdiColor(v) {
  return CLASS_ICON_COLOR[v?.VehicleClass] ?? null
}

export function useFmtType() {
  const { t } = useI18n()
  return (type) => {
    if (!type) return '—'
    const key = `vehicle_types.${type}`
    const translated = t(key)
    return translated === key ? type : translated
  }
}

export const TYPE_LABELS_EN = {
  medium_tank:         'Medium Tank',   light_tank:          'Light Tank',
  heavy_tank:          'Heavy Tank',    tank_destroyer:       'Tank Destroyer',
  spaa:                'SPAA',          fighter:              'Fighter',
  bomber:              'Bomber',        assault:              'Assault',
  utility_helicopter:  'Utility Heli',  attack_helicopter:   'Attack Heli',
  destroyer:           'Destroyer',     heavy_cruiser:        'Heavy Cruiser',
  light_cruiser:       'Light Cruiser', battleship:           'Battleship',
  battlecruiser:       'Battlecruiser', boat:                 'Boat',
  heavy_boat:          'Heavy Boat',    frigate:              'Frigate',
  barge:               'Barge',
}

export function fmtType(t) {
  return TYPE_LABELS_EN[t] ?? t ?? '—'
}

const NATION_DISPLAY = {
  usa:         'USA',
  germany:     'Germany',
  ussr:        'USSR',
  britain:     'Britain',
  japan:       'Japan',
  italy:       'Italy',
  france:      'France',
  sweden:      'Sweden',
  israel:      'Israel',
  china:       'China'
}

export function fmtNation(n) {
  if (!n) return '—'
  const key  = n.toLowerCase()
  const flag = NATION_FLAG[key] ?? '🏴'
  const name = NATION_DISPLAY[key] ?? (n.charAt(0).toUpperCase() + n.slice(1))
  return `${flag} ${name}`
}

export function fmtBR(v) {
  const n = parseFloat(v)
  return isNaN(n) ? '—' : n.toFixed(1)
}

export function fmtSL(v) {
  if (v == null) return '—'
  const n = Math.round(v)
  return n.toLocaleString() + ' SL'
}

const _META_STOPS = [
  [0,   [120, 15,  15]],
  [30,  [251, 36,  42]],
  [45,  [251, 191, 36]],
  [75,  [52,  211, 74]],
  [100, [5,   120, 15]],
]

const _FARM_STOPS = [
  [0,   [250, 250, 250]],
  [100, [109, 40,  217]],
]

const _WR_STOPS = [
  [35, [251, 36,  42 ]],
  [50, [250, 250, 250]],
  [60, [52,  211, 74]],
]

function _lerpChannel(a, b, t) { return Math.round(a + (b - a) * t) }

function _interpolate(stops, score) {
  const s = Math.max(0, Math.min(100, score ?? 0))
  if (s <= stops[0][0])                       return stops[0][1]
  if (s >= stops[stops.length - 1][0])        return stops[stops.length - 1][1]
  for (let i = 0; i < stops.length - 1; i++) {
    const [s0, c0] = stops[i]
    const [s1, c1] = stops[i + 1]
    if (s >= s0 && s <= s1) {
      const t = (s - s0) / (s1 - s0)
      return [
        _lerpChannel(c0[0], c1[0], t),
        _lerpChannel(c0[1], c1[1], t),
        _lerpChannel(c0[2], c1[2], t),
      ]
    }
  }
  return stops[stops.length - 1][1]
}

function _toHex([r, g, b]) {
  return '#' + [r, g, b].map(x => x.toString(16).padStart(2, '0')).join('')
}

export function metaColor(score) {
  if (score == null || isNaN(score)) return '#334155'
  return _toHex(_interpolate(_META_STOPS, score))
}

export function farmColor(score) {
  if (score == null || isNaN(score)) return '#334155'
  return _toHex(_interpolate(_FARM_STOPS, score))
}

export function wrColor(score) {
  if (score == null || isNaN(score)) return '#334155'
  return _toHex(_interpolate(_WR_STOPS, score))
}

export function vehicleDisplayName(v) {
  return v?.Name ?? ''
}

export const SAFE_KEYS = {
  'Сыграно игр':    'battles',
  'Net SL за игру': 'net_sl',
  'SL за игру':     'sl',
  'RP за игру':     'rp',
}

export function normRow(v) {
  const row = { ...v }
  for (const [orig, safe] of Object.entries(SAFE_KEYS)) {
    if (orig in row) row[safe] = row[orig]
  }
  return row
}
