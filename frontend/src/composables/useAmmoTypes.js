import { useI18n } from 'vue-i18n'

export const AMMO_TYPE_MAP = {
  ap: 'AP', ap_ball: 'AP', ap_ball_m2: 'AP', ap_i: 'AP', ap_i_ball: 'AP',
  ap_i_ball_m8: 'AP', ap_i_belt: 'AP', ap_i_t: 'AP', ap_i_t_ball: 'AP',
  ap_i_t_ball_m20: 'AP', ap_large_caliber_tank: 'AP', ap_t: 'AP', ap_t_ball: 'AP',
  ap_tank: 'AP', apt_ball: 'AP',
  ball: 'AP', ball_ap_hc: 'AP', ball_m2: 'AP', ball_shell: 'AP', ball_steel_core: 'AP',
  ball_steel_core_ep: 'AP', ball_t_shell: 'AP', cannon_ball: 'AP',
  i: 'AP', i_ball: 'AP', i_ball_m1: 'AP', i_ball_m23: 'AP', i_t: 'AP', i_t_ball: 'AP',
  t_ball: 'AP', t_ball_m1: 'AP', t_ball_m48a2: 'AP', t_shell: 'AP',
  frag_i: 'AP', frag_i_t: 'AP', fap: 'AP', pele_t: 'AP',
  sapi: 'AP', sapi_belt: 'AP', ac_shell_tank: 'AP',

  apc_solid_medium_caliber_tank: 'APC', apc_t: 'APC', apc_tank: 'APC',
  apbc_tank: 'APBC', apbc_tank_belt: 'APBC', apbc_usa_tank: 'APBC',
  sapbc_flat_nose_tank: 'APBC', sapbc_tank: 'APBC',

  apcbc_solid_medium_caliber_tank: 'APCBC', apcbc_tank: 'APCBC',
  apcbc_tank_belt: 'APCBC', apcbc_tank_shell: 'APCBC', sapcbc_tank: 'APCBC',

  apcr: 'APCR', apcr_i_ball: 'APCR', apcr_i_ball_bs41: 'APCR', apcr_t: 'APCR',
  apcr_tank: 'APCR', hvap_tank: 'APCR', slap: 'APCR', slap_t: 'APCR',

  apds_autocannon: 'APDS', apds_ball: 'APDS', apds_early_tank: 'APDS',
  apds_fs_full_body_steel_tank: 'APDS', apds_fs_ld_30_east_tank: 'APDS',
  apds_fs_ld_30_tank: 'APDS', apds_fs_long_tank: 'APDS', apds_fs_long_tank_belt: 'APDS',
  apds_fs_long_tank_telescoped: 'APDS', apds_fs_tank: 'APDS',
  apds_fs_tungsten_l10_l15_tank: 'APDS', apds_fs_tungsten_small_core_tank: 'APDS',
  apds_he_i_ball: 'APDS', apds_l15_tank: 'APDS', apds_tank: 'APDS',

  aphe: 'APHE', aphe_i_sd: 'APHE', aphe_t: 'APHE', aphe_tank: 'APHE', aphebc_tank: 'APHE',
  sap_he: 'APHE', sap_hei: 'APHE', sap_hei_t: 'APHE', sap_hei_tank: 'APHE',
  sap_hei_tank_shell_belt: 'APHE', sap_tank: 'APHE',

  heat_bomb: 'HEAT', heat_fs_rocket: 'HEAT', heat_fs_tank: 'HEAT',
  heat_fs_west_tank: 'HEAT', heat_grenade_tank: 'HEAT', heat_mp_vt_tank: 'HEAT',
  heat_tank: 'HEAT', he_at: 'HEAT', he_at_grenade: 'HEAT',

  hesh_tank: 'HESH', hesh_tank_rr: 'HESH',

  he_ball: 'HE', he_bomb: 'HE', he_dp: 'HE', he_frag: 'HE', he_frag_ball: 'HE',
  he_frag_base_fuse_tank: 'HE', he_frag_dist_fuse: 'HE', he_frag_dist_fuse_auto_cannon: 'HE',
  he_frag_dist_fuse_telescoped: 'HE', he_frag_fs_dist_fuse: 'HE', he_frag_fs_radio_fuse_shell: 'HE',
  he_frag_fs_tank: 'HE', he_frag_i: 'HE', he_frag_i_belt: 'HE', he_frag_i_t: 'HE',
  he_frag_i_t_belt: 'HE', he_frag_i_tank: 'HE', he_frag_radio_fuse: 'HE',
  he_frag_radio_fuse_shell: 'HE', he_frag_t: 'HE', he_frag_t_ball: 'HE', he_frag_t_belt: 'HE',
  he_frag_tank: 'HE', he_frag_tank_belt: 'HE', he_frag_tank_modern: 'HE',
  he_frag_tank_shell: 'HE', he_frag_tank_telescoped: 'HE', he_frag_vog: 'HE',
  he_grenade_tank: 'HE', he_i: 'HE', he_i_ball: 'HE', he_i_belt: 'HE', he_i_fuse_ball: 'HE',
  he_i_mine: 'HE', he_i_t: 'HE', he_i_t_ball: 'HE', he_i_t_belt: 'HE', he_i_t_mine: 'HE',
  he_i_t_n_mine: 'HE', he_or_tank: 'HE', he_tf: 'HE', he_vt: 'HE',
  shrapnel_tank: 'HE', ke_bomb: 'HE', common_tank: 'HE', special_common_tank: 'HE',

  atgm_he_tank: 'ATGM', atgm_ke_tank: 'ATGM', atgm_tandem_tank: 'ATGM',
  atgm_tank: 'ATGM', atgm_vt_fuze_tank: 'ATGM', sam_tank: 'ATGM', aam: 'ATGM',

  rocket_aircraft: 'ROCKET', rocket_ap_tank: 'ROCKET', rocket_aphe_aircraft: 'ROCKET',
  rocket_tank: 'ROCKET',

  smoke_grenade_tank: 'SMOKE', smoke_tank: 'SMOKE',

  ahead: 'AIRBURST', ahead_tank: 'AIRBURST', ahead_tank_telescoped: 'AIRBURST',

  practice_tank: 'PRACTICE', tp_tank: 'PRACTICE', tphv_tank: 'PRACTICE',
  flare: 'OTHER', mp: 'OTHER', default: 'OTHER', football_kick: 'OTHER',
}

const FALLBACK_PATTERNS = [
  [/^atgm|^sam_|^aam\b/, 'ATGM'],
  [/heat/, 'HEAT'],
  [/hesh/, 'HESH'],
  [/apds/, 'APDS'],
  [/apcr|hvap|slap/, 'APCR'],
  [/apcbc/, 'APCBC'],
  [/apbc/, 'APBC'],
  [/aphe|^sap_he|^sap_tank/, 'APHE'],
  [/^apc/, 'APC'],
  [/smoke/, 'SMOKE'],
  [/rocket/, 'ROCKET'],
  [/ahead/, 'AIRBURST'],
  [/practice|^tp_|tphv/, 'PRACTICE'],
  [/he_frag|^he_|shrapnel|common_tank/, 'HE'],
  [/^ap|^ball|^i_|^i$|^t_ball|^t_shell|^frag_i|sapi/, 'AP'],
]

export function classifyAmmoType(raw) {
  if (!raw) return null
  const key = String(raw).toLowerCase()
  if (key in AMMO_TYPE_MAP) return AMMO_TYPE_MAP[key]

  for (const [re, cat] of FALLBACK_PATTERNS) {
    if (re.test(key)) {
      if (typeof console !== 'undefined') {
        console.warn(`[useAmmoTypes] unmapped ammo type "${raw}" — guessed "${cat}". Add it to AMMO_TYPE_MAP.`)
      }
      return cat
    }
  }
  if (typeof console !== 'undefined') {
    console.warn(`[useAmmoTypes] unknown ammo type "${raw}", falling back to OTHER.`)
  }
  return 'OTHER'
}

export const AMMO_CATEGORY_META = {
  ATGM:     { color: 'error',      icon: 'mdi-rocket-launch' },
  HEAT:     { color: 'warning',    icon: 'mdi-fire' },
  HESH:     { color: 'deep-orange',icon: 'mdi-fire-circle' },
  APHE:     { color: 'secondary',  icon: 'mdi-circle-slice-8' },
  APDS:     { color: 'cyan',       icon: 'mdi-arrow-up-bold' },
  APCR:     { color: 'teal',       icon: 'mdi-arrow-up-bold-outline' },
  APCBC:    { color: 'blue-grey',  icon: 'mdi-shield-half-full' },
  APBC:     { color: 'blue-grey',  icon: 'mdi-shield-half-full' },
  APC:      { color: 'blue-grey',  icon: 'mdi-shield-outline' },
  AP:       { color: 'grey',       icon: 'mdi-circle-outline' },
  HE:       { color: 'orange',     icon: 'mdi-flare' },
  ROCKET:   { color: 'red-darken-1', icon: 'mdi-rocket' },
  AIRBURST: { color: 'purple',     icon: 'mdi-chart-bubble' },
  SMOKE:    { color: 'blue-grey',  icon: 'mdi-weather-fog' },
  PRACTICE: { color: 'grey',       icon: 'mdi-target' },
  OTHER:    { color: 'grey',       icon: 'mdi-help-circle-outline' },
}

export const AMMO_CATEGORY_ORDER = [
  'ATGM', 'HEAT', 'HESH', 'APDS', 'APCR', 'APHE', 'APCBC', 'APBC', 'APC', 'AP',
  'HE', 'AIRBURST', 'ROCKET', 'SMOKE', 'PRACTICE', 'OTHER',
]

export function getVehicleAmmoCategories(vehicle) {
  const raw = vehicle?.vdb_ammo_types
  if (!Array.isArray(raw) || raw.length === 0) return []
  const present = new Set(raw.map(classifyAmmoType).filter(Boolean))
  return AMMO_CATEGORY_ORDER.filter(cat => present.has(cat))
}

export function useAmmoCategoryLabel() {
  const { t } = useI18n()
  return (cat) => {
    const key = `vehicle_card.ammo_types.${cat.toLowerCase()}`
    const translated = t(key)
    return translated === key ? cat : translated
  }
}