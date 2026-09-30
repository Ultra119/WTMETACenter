export const VERDICT_MUST = 'MUST'
export const VERDICT_PASS = 'PASS'
export const VERDICT_SKIP = 'SKIP'
export const VERDICT_PREM = 'PREM'
export const VERDICT_FILL = 'FILL'

export const VERDICT_COLORS = {
  MUST: { border: '#5EEAD4', bg: 'rgba(94,234,212,0.08)',  icon: 'mdi-check-circle',  label: 'Must Play'      },
  FILL: { border: '#7FB2E5', bg: 'rgba(127,178,229,0.07)',  icon: 'mdi-plus-circle',   label: 'Lineup Filler'  },
  PASS: { border: '#F5A623', bg: 'rgba(245,166,35,0.06)',  icon: 'mdi-minus-circle',  label: 'Passable'       },
  SKIP: { border: '#E8607B', bg: 'rgba(232,96,123,0.08)', icon: 'mdi-close-circle',  label: 'Hard Skip'      },
  PREM: { border: '#A99BE0', bg: 'rgba(169,155,224,0.09)', icon: 'mdi-crown',         label: 'Premium Fix'    },
}

export const BRANCH_TYPES = {
  Ground:      ['medium_tank', 'light_tank', 'heavy_tank', 'tank_destroyer', 'spaa'],
  Aviation:    ['fighter', 'bomber', 'assault'],
  Helicopters: ['attack_helicopter', 'utility_helicopter'],
  LargeFleet:  ['destroyer', 'heavy_cruiser', 'light_cruiser', 'battleship', 'battlecruiser'],
  SmallFleet:  ['boat', 'heavy_boat', 'frigate', 'barge'],
}

export const TYPE_LABELS = {
  medium_tank:        'Medium',       light_tank:         'Light',
  heavy_tank:         'Heavy',        tank_destroyer:     'Tank Dest.',
  spaa:               'SPAA',
  fighter:            'Fighter',      bomber:             'Bomber',
  assault:            'Assault',      attack_helicopter:  'Atk Heli',
  utility_helicopter: 'Util Heli',
  destroyer:          'Destroyer',    heavy_cruiser:      'H.Cruiser',
  light_cruiser:      'L.Cruiser',    battleship:         'Battleship',
  battlecruiser:      'B.Cruiser',    boat:               'Boat',
  heavy_boat:         'H.Boat',       frigate:            'Frigate',
  barge:              'Barge',
}

export const TYPE_ICON = {
  medium_tank:        'mdi-tank',           heavy_tank:        'mdi-shield',
  light_tank:         'mdi-lightning-bolt', tank_destroyer:    'mdi-crosshairs-gps',
  spaa:               'mdi-radar',
  fighter:            'mdi-airplane',       bomber:            'mdi-bomb',
  assault:            'mdi-airplane-takeoff',
  attack_helicopter:  'mdi-helicopter',     utility_helicopter:'mdi-tools',
  destroyer:          'mdi-ferry',          battleship:        'mdi-anchor',
  light_cruiser:      'mdi-ferry',          heavy_cruiser:     'mdi-ferry',
  battlecruiser:      'mdi-anchor',         boat:              'mdi-sail-boat',
  heavy_boat:         'mdi-speedboat',      frigate:           'mdi-ship-wheel',
  barge:              'mdi-ferry',
}

export const CLASS_PREFIX = {
  Premium:     'mdi-star',
  Pack:        'mdi-package-variant',
  Squadron:    'mdi-star-four-points',
  Marketplace: 'mdi-store',
  Gift:        'mdi-gift',
  Event:       'mdi-ticket',
  Standard:    '',
}

export const CLASS_BR_COLOR = {
  Premium:     '#F5A623',
  Pack:        '#6FA0D8',
  Squadron:    '#5EEAD4',
  Marketplace: '#A99BE0',
  Gift:        '#E58BB4',
  Event:       '#E0855A',
}

export const ROMAN = { 1:'I', 2:'II', 3:'III', 4:'IV', 5:'V', 6:'VI', 7:'VII', 8:'VIII' }

export const STD_CLASS = 'Standard'

export const MM_WINDOW      = 1.0
export const BR_FILL_WINDOW = 1.0
export const JUNK_FLOOR     = 30.0
export const YELLOW_FLOOR   = 30.0
export const YELLOW_PCTILE  = 0.30

export const RANK_PENALTY = {
  '-4': 0.05, '-3': 0.10, '-2': 0.30, '-1': 0.90,
   0: 1.00,    1: 1.00,    2: 0.35,    3: 0.15,    4: 0.06,
}
export const RANK_PENALTY_PREMIUM = {
  '-4': 1.00, '-3': 1.00, '-2': 1.00, '-1': 1.00,
   0: 1.00,    1: 1.00,    2: 0.35,    3: 0.15,    4: 0.06,
}

export const TYPE_CATEGORIES = {
  Ground:      BRANCH_TYPES.Ground,
  Aviation:    BRANCH_TYPES.Aviation,
  Helicopters: BRANCH_TYPES.Helicopters,
  LargeFleet:  ['destroyer', 'heavy_cruiser', 'light_cruiser', 'battleship', 'battlecruiser'],
  SmallFleet:  ['boat', 'heavy_boat', 'frigate', 'barge'],
}

export const LARGE_FLEET_TYPES = new Set(TYPE_CATEGORIES.LargeFleet)
export const SMALL_FLEET_TYPES = new Set(TYPE_CATEGORIES.SmallFleet)

export const TANK_TYPES = new Set(['medium_tank', 'heavy_tank', 'light_tank'])

export const DEFAULT_LINEUP_SLOTS = 4

export const LINEUP_PRIORITY = {
  Ground:      ['tank', 'spaa', 'tank_destroyer'],
  Aviation:    ['fighter', 'assault', 'bomber'],
  Helicopters: ['attack_helicopter', 'utility_helicopter'],
  LargeFleet:  ['destroyer', 'light_cruiser', 'heavy_cruiser',
                'battleship', 'battlecruiser'],
  SmallFleet:  ['boat', 'heavy_boat', 'frigate', 'barge'],
}

export const BR_ERA_THRESHOLDS = [2.3, 3.7, 5.3, 6.7, 8.3, 9.7, 11.3]

export const CROSS_THRESH       = 1.30
export const CROSS_SKIP_THRESH  = 1.40
export const CROSS_BR_WINDOW    = 0.7
export const CROSS_BR_LOOKBACK  = 1.0
export const NO_CROSS_TYPES     = new Set(['spaa'])
export const FILL_MIN_SCORE     = 1.0

export const REDBOOK_LOW_BATTLES = 100

export const TYPE_BRANCH_COLOR = {
  medium_tank:        '#9AA0AD', light_tank:         '#9AA0AD',
  heavy_tank:         '#9AA0AD', tank_destroyer:     '#9AA0AD', spaa: '#A99BE0',
  fighter:            '#7FB2E5', bomber:             '#7FB2E5', assault: '#7FB2E5',
  attack_helicopter:  '#5EEAD4', utility_helicopter: '#5EEAD4',
  destroyer:          '#6FA0D8', heavy_cruiser:      '#6FA0D8', light_cruiser: '#6FA0D8',
  battleship:         '#6FA0D8', battlecruiser:      '#6FA0D8',
  boat:               '#9CC8EE', heavy_boat:         '#9CC8EE', frigate: '#9CC8EE', barge: '#9CC8EE',
}
