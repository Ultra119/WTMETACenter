import math

import pandas as pd
import streamlit as st


def _fmt(n: int, suffix: str = "", signed: bool = False) -> str:
    formatted = f"{abs(n):,}".replace(",", "\u202f")
    if n < 0:
        sign = "-"
    elif signed and n > 0:
        sign = "+"
    else:
        sign = ""
    return f"{sign}{formatted}{suffix}"

_NATION_FLAG: dict = {
    "usa": "🇺🇸", "germany": "🇩🇪", "ussr": "🇷🇺", "britain": "🇬🇧",
    "japan": "🇯🇵", "italy": "🇮🇹", "france": "🇫🇷", "sweden": "🇸🇪",
    "israel": "🇮🇱", "china": "🇨🇳", "finland": "🇫🇮",
    "netherlands": "🇳🇱", "hungary": "🇭🇺",
}

_TYPE_ICON: dict = {
    "medium_tank": "🛡️", "heavy_tank": "⚔️", "light_tank": "💨",
    "tank_destroyer": "🎯", "spaa": "🌀",
    "fighter": "✈️", "bomber": "💣", "assault": "🔥",
    "attack_helicopter": "🚁", "utility_helicopter": "🚁",
    "destroyer": "🚢", "battleship": "⚓", "light_cruiser": "🛳️",
    "heavy_cruiser": "🛳️", "battlecruiser": "⚓",
    "boat": "⛵", "heavy_boat": "🚤", "frigate": "🛥️",
}

_ARMOR_SCALE_MAX: float = 500.0


def _armor_bar(label: str, value: float) -> str:
    pct = min(100.0, (value / _ARMOR_SCALE_MAX) * 100.0) if value > 0 else 0.0
    if value >= 300:   color = "#ef4444"
    elif value >= 150: color = "#f97316"
    elif value >= 60:  color = "#fbbf24"
    elif value > 0:    color = "#34d399"
    else:              color = "#1e293b"
    return (
        f'<div class="vc-armor-bar">'
        f'  <span class="vc-armor-label">{label}</span>'
        f'  <div class="vc-armor-track">'
        f'    <div class="vc-armor-fill" style="width:{pct:.0f}%;background:{color}"></div>'
        f'  </div>'
        f'  <span class="vc-armor-num">{"—" if value == 0 else f"{value:.0f} мм"}</span>'
        f'</div>'
    )


def _ammo_chip(atype: str) -> str:
    t = str(atype).lower()
    if "aphe" in t:
        cls, label = "chip-aphe", "APHE"
    elif "heat" in t or "hesh" in t:
        cls, label = "chip-heat", "HEAT/HESH"
    elif "atgm" in t or "guided" in t:
        cls, label = "chip-atgm", "ATGM"
    elif "apds" in t or "apfs" in t or "apcr" in t:
        cls, label = "chip-apds", t.upper()[:6]
    elif "he_frag" in t or t == "he":
        cls, label = "chip-he", "HE"
    elif "smoke" in t:
        cls, label = "chip-smoke", "Smoke"
    else:
        cls, label = "chip-other", t[:8].upper()
    return f'<span class="vc-ammo-chip {cls}">{label}</span>'


def _score_color(v: float) -> str:
    if v >= 70: return "#34d399"
    if v >= 45: return "#fbbf24"
    return "#f87171"


def _wr_color(wr: float) -> str:
    if wr >= 55: return "vc-value-green"
    if wr >= 48: return "vc-value-yellow"
    return "vc-value-red"


def _stat_row(label: str, value: str, cls: str = "vc-value") -> str:
    return (
        f'<div class="vc-row">'
        f'<span class="vc-label">{label}</span>'
        f'<span class="{cls}">{value}</span>'
        f'</div>'
    )


def render_vehicle_card(row: "pd.Series") -> None:
    def g(col, default=None):
        v = row.get(col, default) if hasattr(row, "get") else getattr(row, col, default)
        if v is None:
            return default
        if isinstance(v, float) and math.isnan(v):
            return default
        if isinstance(v, str) and not v.strip():
            return default
        return v

    name    = g("Name",          "—")
    nation  = str(g("Nation",    "")).lower()
    br      = float(g("BR",      0))
    vtype   = str(g("Type",      "—"))
    wr      = float(g("WR",      0))
    kd      = float(g("KD",      0))
    battles = int(g("Сыграно игр", 0))
    meta    = float(g("META_SCORE", 0))
    farm    = float(g("FARM_SCORE", 0))
    sl_pg   = int(g("SL за игру",   0))
    rp_pg   = int(g("RP за игру",   0))

    flag      = _NATION_FLAG.get(nation, "🏴")
    type_icon = _TYPE_ICON.get(vtype, "🔧")

    era        = int(g("vdb_era", 0))
    crew       = int(g("vdb_crew_total_count", 0))

    rep_rb     = int(g("vdb_repair_cost_realistic", 0))
    rep_fu_rb  = int(g("vdb_repair_cost_full_upgraded_realistic", 0))
    sl_mul_rb  = float(g("vdb_sl_mul_realistic", 0))
    sl_mul_ab  = float(g("vdb_sl_mul_arcade", 0))
    req_exp    = int(g("vdb_req_exp", 0))
    val_sl     = int(g("vdb_value", 0))

    hull_f = float(g("vdb_hull_front",   0))
    hull_s = float(g("vdb_hull_side",    0))
    hull_r = float(g("vdb_hull_rear",    0))
    turt_f = float(g("vdb_turret_front", 0))
    turt_s = float(g("vdb_turret_side",  0))
    turt_r = float(g("vdb_turret_rear",  0))

    caliber    = float(g("vdb_main_caliber_mm", 0))
    gun_speed  = float(g("vdb_main_gun_speed",  0))
    ammo_types = g("vdb_ammo_types", []) or []
    has_atgm   = bool(g("vdb_has_atgm",    False))
    has_heat   = bool(g("vdb_has_heat",    False))
    has_aphe   = bool(g("vdb_has_aphe",    False))
    has_therm  = bool(g("vdb_has_thermal", False))

    spd_rb = int(g("vdb_engine_max_speed_rb", 0))
    hp_rb  = int(g("vdb_engine_hp_rb",        0))
    mass   = float(g("vdb_mass", 0))

    is_prem  = int(g("vdb_is_premium",       0))
    is_pack  = int(g("vdb_is_pack",          0))
    is_squad = int(g("vdb_squadron_vehicle", 0))
    on_mkt   = int(g("vdb_on_marketplace",   0))

    identifier = str(g("vdb_identifier", ""))
    match_sc   = float(g("vdb_match_score", 0.0))
    rel_date   = str(g("vdb_release_date", ""))
    ver        = str(g("vdb_version", ""))

    era_roman = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
    era_str   = era_roman[era] if 0 < era < len(era_roman) else (str(era) if era else "—")

    meta_col = _score_color(meta)
    farm_col = _score_color(farm)
    wr_cls   = _wr_color(wr)

    badges = ""
    if is_prem:  badges += '<span class="vc-badge vc-badge-prem">★ Premium</span>'
    if is_pack:  badges += '<span class="vc-badge vc-badge-pack">📦 Pack</span>'
    if is_squad: badges += '<span class="vc-badge vc-badge-squad">✦ Squadron</span>'
    if on_mkt:   badges += '<span class="vc-badge vc-badge-mkt">🏪 Marketplace</span>'

    rep_cls    = "vc-value-red"    if rep_rb > 5000 else "vc-value-yellow" if rep_rb > 2000 else "vc-value-green"
    sl_mul_cls = "vc-value-green"  if sl_mul_rb >= 1.5 else "vc-value-yellow" if sl_mul_rb >= 1.0 else "vc-value-red"

    net_sl = sl_pg - rep_rb if sl_pg > 0 and rep_rb > 0 else 0
    net_cls = "vc-value-green" if net_sl > 0 else "vc-value-red"

    econ_rows = ""
    if sl_pg > 0:
        econ_rows += _stat_row("SL / игру", _fmt(sl_pg), "vc-value-yellow")
    if rp_pg > 0:
        econ_rows += _stat_row("RP / игру", _fmt(rp_pg), "vc-value-blue")
    if net_sl != 0:
        econ_rows += _stat_row("Чистый SL / игру", _fmt(net_sl, signed=True), net_cls)
    if rep_rb > 0:
        econ_rows += _stat_row("Ремонт RB", _fmt(rep_rb, " SL"), rep_cls)
    if rep_fu_rb > 0:
        econ_rows += _stat_row("Полный ремонт", _fmt(rep_fu_rb, " SL"), "vc-value")
    if sl_mul_rb > 0:
        econ_rows += _stat_row("SL-множитель RB", f"×{sl_mul_rb:.2f}", sl_mul_cls)
    if sl_mul_ab > 0:
        econ_rows += _stat_row("SL-множитель AB", f"×{sl_mul_ab:.2f}", "vc-value")
    if req_exp > 0:
        econ_rows += _stat_row("Нужно RP", _fmt(req_exp), "vc-value-blue")
    if val_sl > 0:
        econ_rows += _stat_row("Стоимость", _fmt(val_sl, " SL"), "vc-value")

    econ_section = f'<div class="vc-section-title">💰 Экономика прокачки</div>{econ_rows}' if econ_rows else ""

    has_armor  = any([hull_f, hull_s, hull_r, turt_f, turt_s, turt_r])
    armor_html = ""
    if has_armor:
        armor_html = (
            '<div class="vc-section-title">🛡️ Бронирование</div>'
            + _armor_bar("Корпус: перед / борт / корма",  hull_f)
            + _armor_bar("",                               hull_s)
            + _armor_bar("",                               hull_r)
            + _armor_bar("Башня: перед / борт / корма",   turt_f)
            + _armor_bar("",                               turt_s)
            + _armor_bar("",                               turt_r)
        )

    weapon_rows = ""
    if caliber:
        weapon_rows += _stat_row("Калибр", f"{caliber:.0f} мм")
    if gun_speed:
        weapon_rows += _stat_row("Нач. скорость", f"{gun_speed:.0f} м/с")

    perks = []
    if has_atgm:  perks.append("🚀 ATGM")
    if has_therm: perks.append("🌡️ Термооптика")
    if has_heat:  perks.append("🔥 HEAT/HESH")
    if has_aphe:  perks.append("💥 APHE")

    ammo_chips = (
        "".join(_ammo_chip(t) for t in ammo_types[:12])
        if ammo_types
        else '<span style="color:#475569;font-size:0.7rem">нет данных</span>'
    )

    weapon_section = ""
    if weapon_rows or ammo_types or perks:
        perks_html = (
            f'<div style="margin-top:6px;font-size:0.72rem;color:#a7f3d0">'
            f'{" &nbsp;|&nbsp; ".join(perks)}</div>'
            if perks else ""
        )
        weapon_section = (
            f'<div class="vc-section-title">🔫 Вооружение</div>'
            f'{weapon_rows}'
            f'<div style="margin-top:6px">{ammo_chips}</div>'
            f'{perks_html}'
        )

    mobility_html = ""
    if spd_rb > 0 or hp_rb > 0:
        pw_ratio = (hp_rb / (mass / 1000)) if mass > 0 and hp_rb > 0 else 0
        pw_cls   = "vc-value-green" if pw_ratio >= 20 else "vc-value-yellow" if pw_ratio >= 12 else "vc-value-red"
        parts = []
        if spd_rb:   parts.append(f"Скорость {spd_rb} км/ч")
        if pw_ratio: parts.append(f"Уд. мощность <span class='{pw_cls}'>{pw_ratio:.1f} л.с./т</span>")
        if crew:     parts.append(f"Экипаж {crew} чел.")
        mobility_html = (
            f'<div class="vc-section-title">⚡ Подвижность</div>'
            f'<div style="font-size:0.78rem;color:#e2e8f0;display:flex;gap:20px;flex-wrap:wrap">'
            + "".join(f'<span>{p}</span>' for p in parts)
            + "</div>"
        )

    footer_match = f"✅ match {match_sc:.0%}" if match_sc > 0 else "⚠️ vdb нет данных"
    footer_extra = ""
    if rel_date: footer_extra += f"Добавлено: {rel_date}"
    if ver:      footer_extra += f"&nbsp;|&nbsp;{ver}"

    html = f"""
<div class="vc-card">
<div class="vc-header">
<div class="vc-title">{flag} {name}</div>
<div class="vc-subtitle">
{type_icon} {vtype.replace("_"," ").title()} &nbsp;·&nbsp;
{nation.title()} &nbsp;·&nbsp; БР {br:.1f} &nbsp;·&nbsp; Ранг {era_str}
</div>
<div style="margin-top:8px">{badges}</div>
</div>
<div class="vc-body">
<div style="display:flex;align-items:center;gap:20px;margin-bottom:12px">
<div style="display:inline-flex;flex-direction:column;align-items:center;
justify-content:center;width:66px;height:66px;border-radius:50%;
border:3px solid {meta_col};
background:radial-gradient(circle, #064e3b 0%, #0f172a 100%);
box-shadow:0 0 14px {meta_col}44;flex-shrink:0">
<span style="font-family:Rajdhani,sans-serif;font-size:1.3rem;font-weight:700;
color:{meta_col};line-height:1">{meta:.0f}</span>
<span style="font-size:0.5rem;color:#6ee7b7;letter-spacing:0.1em;
text-transform:uppercase">META</span>
</div>
<div style="display:inline-flex;flex-direction:column;align-items:center;
justify-content:center;width:66px;height:66px;border-radius:50%;
border:3px solid {farm_col};
background:radial-gradient(circle, #1c1917 0%, #0f172a 100%);
box-shadow:0 0 14px {farm_col}44;flex-shrink:0">
<span style="font-family:Rajdhani,sans-serif;font-size:1.3rem;font-weight:700;
color:{farm_col};line-height:1">{farm:.0f}</span>
<span style="font-size:0.5rem;color:#a78bfa;letter-spacing:0.1em;
text-transform:uppercase">FARM</span>
</div>
<div style="display:flex;flex-direction:column;gap:3px;font-size:0.78rem">
{_stat_row("WinRate", f"{wr:.1f}%", wr_cls)}
{_stat_row("K/D", f"{kd:.2f}")}
{_stat_row("Боёв в БД", _fmt(battles))}
</div>
</div>
{econ_section}
{armor_html}
{weapon_section}
{mobility_html}
</div>
<div class="vc-footer">
<span>{identifier or "—"}</span>
<span>{footer_extra}</span>
<span>{footer_match}</span>
</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)
