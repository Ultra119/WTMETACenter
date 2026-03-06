"""
Общие утилиты UI: форматирование, фабрики таблиц, генерация карточки техники.
"""
import math
import pandas as pd
from dash import dash_table, html
import dash_bootstrap_components as dbc

from analytics.constants import WT_BR_STEPS

BR_MIN = float(min(WT_BR_STEPS))
BR_MAX = float(max(WT_BR_STEPS))

# ── Prefixes ──────────────────────────────────────────────────────────────────
CLASS_PREFIX: dict[str, str] = {
    "Premium":     "★ ",
    "Pack":        "📦 ",
    "Squadron":    "✦ ",
    "Marketplace": "🏪 ",
    "Standard":    "",
}

# ── Formatting ────────────────────────────────────────────────────────────────
def fmt_num(n: int, suffix: str = "", signed: bool = False) -> str:
    try:
        n = int(n)
        s = f"{abs(n):,}".replace(",", "\u202f")
        sign = "-" if n < 0 else ("+" if signed and n > 0 else "")
        return f"{sign}{s}{suffix}"
    except Exception:
        return str(n)


def add_name_display(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if "VehicleClass" in df.columns:
        df["Name_Display"] = df.apply(
            lambda r: CLASS_PREFIX.get(r["VehicleClass"], "") + str(r["Name"]),
            axis=1,
        )
    else:
        df["Name_Display"] = df["Name"]
    return df


# ── Dark DataTable factory ────────────────────────────────────────────────────
_HEADER_STYLE = {
    "backgroundColor": "#1e293b",
    "color": "#a7f3d0",
    "fontWeight": "600",
    "fontSize": "11px",
    "letterSpacing": "0.1em",
    "textTransform": "uppercase",
    "border": "1px solid #1e3a5f",
}
_CELL_STYLE = {
    "backgroundColor": "#0f172a",
    "color": "#e2e8f0",
    "border": "1px solid #1e293b",
    "fontFamily": "'JetBrains Mono', monospace",
    "fontSize": "12px",
    "padding": "6px 10px",
}
_SEL_STYLE = [
    {"if": {"state": "selected"},
     "backgroundColor": "rgba(16,185,129,0.12)",
     "border": "1px solid #10b981"},
]


def dark_table(
    df: pd.DataFrame,
    columns: list[str],
    col_names: dict[str, str],
    *,
    sort_by: list | None = None,
    selectable: bool = False,
    extra_cond_styles: list | None = None,
    table_id: str | None = None,
    page_size: int = 100,
    max_height: str = "520px",
) -> dash_table.DataTable:
    cols_avail = [c for c in columns if c in df.columns]
    kwargs: dict = dict(
        data=df[cols_avail].round(2).to_dict("records"),
        columns=[
            {
                "name": col_names.get(c, c),
                "id": c,
                "type": "numeric" if c not in ("Name_Display", "Name", "Nation", "Type", "Роль") else "text",
            }
            for c in cols_avail
        ],
        style_table={"overflowX": "auto", "minWidth": "100%", "maxHeight": max_height, "overflowY": "auto"},
        style_header=_HEADER_STYLE,
        style_cell=_CELL_STYLE,
        style_data_conditional=_SEL_STYLE + (extra_cond_styles or []),
        fixed_rows={"headers": True},
        sort_action="native",
        sort_by=sort_by or [],
        filter_action="native",
        filter_options={"case": "insensitive"},
        page_size=page_size,
        style_as_list_view=False,
    )
    if selectable:
        kwargs["row_selectable"] = "single"
        kwargs["selected_rows"] = []
    if table_id:
        kwargs["id"] = table_id

    return dash_table.DataTable(**kwargs)


def pivot_table(pivot: pd.DataFrame) -> html.Div | dash_table.DataTable:
    """Pivot-таблица кронштейнов с подсветкой максимума по строке."""
    if pivot.empty:
        return html.Div("Нет данных", style={"color": "#475569", "padding": "12px"})

    pivot = pivot.reset_index()
    idx_col = pivot.columns[0]
    nation_cols = [c for c in pivot.columns if c != idx_col]
    records = pivot.to_dict("records")

    styles = [{"if": {"state": "selected"}, "backgroundColor": "rgba(16,185,129,0.1)"}]
    for row_i, row in enumerate(records):
        vals = {c: float(row.get(c, 0) or 0) for c in nation_cols}
        row_max = max(vals.values()) if vals else 0
        for col, val in vals.items():
            if row_max <= 0:
                continue
            if val == row_max:
                s = {"backgroundColor": "#854d0e", "color": "#fef08a", "fontWeight": "bold"}
            elif val >= row_max * 0.90:
                s = {"color": "#a7f3d0"}
            elif val >= row_max * 0.75:
                s = {"color": "#fcd34d"}
            elif val > 0:
                s = {"color": "#f87171"}
            else:
                s = {"color": "#475569"}
            styles.append({"if": {"row_index": row_i, "column_id": col}, **s})

    return dash_table.DataTable(
        data=records,
        columns=[{"name": c, "id": c} for c in pivot.columns],
        style_table={"overflowX": "auto", "minWidth": "100%", "maxHeight": "520px", "overflowY": "auto"},
        style_header=_HEADER_STYLE,
        style_cell={**_CELL_STYLE, "minWidth": "60px"},
        style_cell_conditional=[
            {"if": {"column_id": idx_col}, "color": "#94a3b8", "fontSize": "11px", "minWidth": "80px"}
        ],
        style_data_conditional=styles,
        fixed_rows={"headers": True},
        sort_action="native",
        page_size=200,
    )


# ── Vehicle Card — Dash Components ────────────────────────────────────────────
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


def _g(row: dict, col, default=None):
    """Безопасное извлечение значения из строки с заменой NaN/пустых строк."""
    v = row.get(col, default)
    if v is None:
        return default
    if isinstance(v, float) and math.isnan(v):
        return default
    if isinstance(v, str) and not v.strip():
        return default
    return v


def _score_col(v: float) -> str:
    if v >= 70:
        return "#34d399"
    if v >= 45:
        return "#fbbf24"
    return "#f87171"


# ── Card sub-components ───────────────────────────────────────────────────────

def _stat_row(label: str, value: str, cls: str = "vc-value") -> html.Div:
    return html.Div(className="vc-row", children=[
        html.Span(label, className="vc-label"),
        html.Span(value, className=cls),
    ])


def _armor_bar(label: str, value: float) -> html.Div:
    pct = min(100.0, (value / 500.0) * 100.0) if value > 0 else 0.0
    if value >= 300:    color = "#ef4444"
    elif value >= 150:  color = "#f97316"
    elif value >= 60:   color = "#fbbf24"
    elif value > 0:     color = "#34d399"
    else:               color = "#1e293b"
    num = "—" if value == 0 else f"{value:.0f} мм"
    return html.Div(className="vc-armor-bar", children=[
        html.Span(label, className="vc-armor-label"),
        html.Div(className="vc-armor-track", children=[
            html.Div(className="vc-armor-fill",
                     style={"width": f"{pct:.0f}%", "background": color}),
        ]),
        html.Span(num, className="vc-armor-num"),
    ])


def _ammo_chip(atype: str) -> html.Span:
    t = str(atype).lower()
    if "aphe" in t:
        cls, lbl = "chip-aphe", "APHE"
    elif "heat" in t or "hesh" in t:
        cls, lbl = "chip-heat", "HEAT/HESH"
    elif "atgm" in t or "guided" in t:
        cls, lbl = "chip-atgm", "ATGM"
    elif "apds" in t or "apfs" in t or "apcr" in t:
        cls, lbl = "chip-apds", t.upper()[:6]
    elif "he_frag" in t or t == "he":
        cls, lbl = "chip-he", "HE"
    elif "smoke" in t:
        cls, lbl = "chip-smoke", "Smoke"
    else:
        cls, lbl = "chip-other", t[:8].upper()
    return html.Span(lbl, className=f"vc-ammo-chip {cls}")


def _score_gauge(value: float, label: str, gradient: str) -> html.Div:
    color = _score_col(value)
    return html.Div(style={
        "display": "inline-flex", "flexDirection": "column",
        "alignItems": "center", "justifyContent": "center",
        "width": "66px", "height": "66px", "borderRadius": "50%",
        "border": f"3px solid {color}",
        "background": f"radial-gradient(circle,{gradient} 0%,#0f172a 100%)",
        "boxShadow": f"0 0 14px {color}44", "flexShrink": "0",
    }, children=[
        html.Span(f"{value:.0f}", style={
            "fontFamily": "Rajdhani,sans-serif", "fontSize": "1.3rem",
            "fontWeight": "700", "color": color, "lineHeight": "1",
        }),
        html.Span(label, style={
            "fontSize": ".5rem", "color": "#6ee7b7" if label == "META" else "#a78bfa",
            "letterSpacing": ".1em", "textTransform": "uppercase",
        }),
    ])


# ── Public API ────────────────────────────────────────────────────────────────

def generate_vehicle_card(row: dict) -> html.Div:
    """Карточка техники в виде дерева Dash-компонентов."""

    # ── Raw values ────────────────────────────────────────────────────────────
    name    = _g(row, "Name",    "—")
    nation  = str(_g(row, "Nation", "")).lower()
    br      = float(_g(row, "BR",  0))
    vtype   = str(_g(row, "Type", "—"))
    wr      = float(_g(row, "WR",  0))
    kd      = float(_g(row, "KD",  0))
    battles = int(_g(row, "Сыграно игр", 0))
    meta    = float(_g(row, "META_SCORE", 0))
    farm    = float(_g(row, "FARM_SCORE", 0))
    sl_pg   = int(_g(row, "SL за игру",  0))
    rp_pg   = int(_g(row, "RP за игру",  0))

    flag      = _NATION_FLAG.get(nation, "🏴")
    type_icon = _TYPE_ICON.get(vtype, "🔧")

    era       = int(_g(row, "vdb_era", 0))
    crew      = int(_g(row, "vdb_crew_total_count", 0))
    rep_rb    = int(_g(row, "vdb_repair_cost_realistic", 0))
    rep_fu    = int(_g(row, "vdb_repair_cost_full_upgraded_realistic", 0))
    sl_mul_rb = float(_g(row, "vdb_sl_mul_realistic", 0))
    sl_mul_ab = float(_g(row, "vdb_sl_mul_arcade", 0))
    req_exp   = int(_g(row, "vdb_req_exp", 0))
    val_sl    = int(_g(row, "vdb_value", 0))
    hull_f    = float(_g(row, "vdb_hull_front",   0))
    hull_s    = float(_g(row, "vdb_hull_side",    0))
    hull_r    = float(_g(row, "vdb_hull_rear",    0))
    turt_f    = float(_g(row, "vdb_turret_front", 0))
    turt_s    = float(_g(row, "vdb_turret_side",  0))
    turt_r    = float(_g(row, "vdb_turret_rear",  0))
    caliber   = float(_g(row, "vdb_main_caliber_mm", 0))
    gun_spd   = float(_g(row, "vdb_main_gun_speed",  0))
    ammo_types = _g(row, "vdb_ammo_types", []) or []
    has_atgm  = bool(_g(row, "vdb_has_atgm",    False))
    has_heat  = bool(_g(row, "vdb_has_heat",    False))
    has_aphe  = bool(_g(row, "vdb_has_aphe",    False))
    has_therm = bool(_g(row, "vdb_has_thermal", False))
    spd_rb    = int(_g(row, "vdb_engine_max_speed_rb", 0))
    hp_rb     = int(_g(row, "vdb_engine_hp_rb",        0))
    mass      = float(_g(row, "vdb_mass", 0))
    is_prem   = int(_g(row, "vdb_is_premium",       0))
    is_pack   = int(_g(row, "vdb_is_pack",          0))
    is_squad  = int(_g(row, "vdb_squadron_vehicle", 0))
    on_mkt    = int(_g(row, "vdb_on_marketplace",   0))
    identifier = str(_g(row, "vdb_identifier", ""))
    match_sc   = float(_g(row, "vdb_match_score", 0.0))
    rel_date   = str(_g(row, "vdb_release_date", ""))
    ver        = str(_g(row, "vdb_version", ""))

    _ERA_ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
    era_str = _ERA_ROMAN[era] if 0 < era < len(_ERA_ROMAN) else (str(era) if era else "—")

    wr_cls = "vc-value-green" if wr >= 55 else "vc-value-yellow" if wr >= 48 else "vc-value-red"

    # ── Header ────────────────────────────────────────────────────────────────
    badges = []
    if is_prem:  badges.append(html.Span("★ Premium",    className="vc-badge vc-badge-prem"))
    if is_pack:  badges.append(html.Span("📦 Pack",       className="vc-badge vc-badge-pack"))
    if is_squad: badges.append(html.Span("✦ Squadron",   className="vc-badge vc-badge-squad"))
    if on_mkt:   badges.append(html.Span("🏪 Marketplace", className="vc-badge vc-badge-mkt"))

    header = html.Div(className="vc-header", children=[
        html.Div(f"{flag} {name}", className="vc-title"),
        html.Div(className="vc-subtitle", children=[
            f"{type_icon} {vtype.replace('_', ' ').title()}",
            html.Span(" · ", style={"opacity": ".5"}),
            nation.title(),
            html.Span(" · ", style={"opacity": ".5"}),
            f"БР {br:.1f}",
            html.Span(" · ", style={"opacity": ".5"}),
            f"Ранг {era_str}",
        ]),
        html.Div(badges, style={"marginTop": "8px"}),
    ])

    # ── Score gauges + quick stats ────────────────────────────────────────────
    gauges_row = html.Div(style={
        "display": "flex", "alignItems": "center",
        "gap": "20px", "marginBottom": "12px",
    }, children=[
        _score_gauge(meta, "META", "#064e3b"),
        _score_gauge(farm, "FARM", "#1c1917"),
        html.Div(style={"display": "flex", "flexDirection": "column", "gap": "3px", "fontSize": ".78rem"},
                 children=[
                     _stat_row("WinRate", f"{wr:.1f}%", wr_cls),
                     _stat_row("K/D",     f"{kd:.2f}"),
                     _stat_row("Боёв",    fmt_num(battles)),
                 ]),
    ])

    # ── Economy ───────────────────────────────────────────────────────────────
    rep_cls    = "vc-value-red" if rep_rb > 5000 else "vc-value-yellow" if rep_rb > 2000 else "vc-value-green"
    sl_mul_cls = "vc-value-green" if sl_mul_rb >= 1.5 else "vc-value-yellow" if sl_mul_rb >= 1.0 else "vc-value-red"
    net_sl     = sl_pg - rep_rb if sl_pg > 0 and rep_rb > 0 else 0
    net_cls    = "vc-value-green" if net_sl > 0 else "vc-value-red"

    econ_rows = []
    if sl_pg > 0:     econ_rows.append(_stat_row("SL / игру",        fmt_num(sl_pg),              "vc-value-yellow"))
    if rp_pg > 0:     econ_rows.append(_stat_row("RP / игру",        fmt_num(rp_pg),              "vc-value-blue"))
    if net_sl != 0:   econ_rows.append(_stat_row("Чистый SL / игру", fmt_num(net_sl, signed=True), net_cls))
    if rep_rb > 0:    econ_rows.append(_stat_row("Ремонт RB",        fmt_num(rep_rb, " SL"),      rep_cls))
    if rep_fu > 0:    econ_rows.append(_stat_row("Полный ремонт",    fmt_num(rep_fu, " SL"),      "vc-value"))
    if sl_mul_rb > 0: econ_rows.append(_stat_row("SL-множитель RB",  f"×{sl_mul_rb:.2f}",         sl_mul_cls))
    if sl_mul_ab > 0: econ_rows.append(_stat_row("SL-множитель AB",  f"×{sl_mul_ab:.2f}",         "vc-value"))
    if req_exp > 0:   econ_rows.append(_stat_row("Нужно RP",         fmt_num(req_exp),            "vc-value-blue"))
    if val_sl > 0:    econ_rows.append(_stat_row("Стоимость",        fmt_num(val_sl, " SL"),      "vc-value"))

    econ_section = (
        [html.Div("💰 Экономика", className="vc-section-title")] + econ_rows
        if econ_rows else []
    )

    # ── Armour ────────────────────────────────────────────────────────────────
    armor_values = [hull_f, hull_s, hull_r, turt_f, turt_s, turt_r]
    armor_section = []
    if any(armor_values):
        armor_section = [
            html.Div("🛡️ Бронирование", className="vc-section-title"),
            _armor_bar("Корпус: перед", hull_f),
            _armor_bar("Корпус: борт",  hull_s),
            _armor_bar("Корпус: корма", hull_r),
            _armor_bar("Башня: перед",  turt_f),
            _armor_bar("Башня: борт",   turt_s),
            _armor_bar("Башня: корма",  turt_r),
        ]

    # ── Weapons ───────────────────────────────────────────────────────────────
    weapon_rows = []
    if caliber:  weapon_rows.append(_stat_row("Калибр",        f"{caliber:.0f} мм"))
    if gun_spd:  weapon_rows.append(_stat_row("Нач. скорость", f"{gun_spd:.0f} м/с"))

    perks = []
    if has_atgm:  perks.append("🚀 ATGM")
    if has_therm: perks.append("🌡️ Термооптика")
    if has_heat:  perks.append("🔥 HEAT/HESH")
    if has_aphe:  perks.append("💥 APHE")

    ammo_chips = (
        [_ammo_chip(t) for t in ammo_types[:12]]
        if ammo_types
        else [html.Span("нет данных", style={"color": "#475569", "fontSize": ".7rem"})]
    )

    weapon_section = []
    if weapon_rows or ammo_types or perks:
        weapon_section = [
            html.Div("🔫 Вооружение", className="vc-section-title"),
            *weapon_rows,
            html.Div(ammo_chips, style={"marginTop": "6px"}),
        ]
        if perks:
            weapon_section.append(
                html.Div(
                    " | ".join(perks),
                    style={"marginTop": "6px", "fontSize": ".72rem", "color": "#a7f3d0"},
                )
            )

    # ── Mobility ──────────────────────────────────────────────────────────────
    mobility_section = []
    if spd_rb > 0 or hp_rb > 0:
        pw = (hp_rb / (mass / 1000)) if mass > 0 and hp_rb > 0 else 0
        pw_cls = "vc-value-green" if pw >= 20 else "vc-value-yellow" if pw >= 12 else "vc-value-red"

        mob_parts = []
        if spd_rb:
            mob_parts.append(html.Span(f"Скорость {spd_rb} км/ч"))
        if pw:
            mob_parts.append(html.Span([
                "Уд. мощность ",
                html.Span(f"{pw:.1f} л.с./т", className=pw_cls),
            ]))
        if crew:
            mob_parts.append(html.Span(f"Экипаж {crew} чел."))

        mobility_section = [
            html.Div("⚡ Подвижность", className="vc-section-title"),
            html.Div(mob_parts, style={
                "fontSize": ".78rem", "color": "#e2e8f0",
                "display": "flex", "gap": "20px", "flexWrap": "wrap",
            }),
        ]

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_match = f"✅ match {match_sc:.0%}" if match_sc > 0 else "⚠️ vdb нет данных"

    footer_extra_parts: list = []
    if rel_date:
        footer_extra_parts.append(f"Добавлено: {rel_date}")
    if ver:
        footer_extra_parts.append(ver)
    footer_extra = " | ".join(footer_extra_parts)

    footer = html.Div(className="vc-footer", children=[
        html.Span(identifier or "—"),
        html.Span(footer_extra),
        html.Span(footer_match),
    ])

    # ── Assemble ──────────────────────────────────────────────────────────────
    return html.Div(className="vc-card", children=[
        header,
        html.Div(className="vc-body", children=[
            gauges_row,
            *econ_section,
            *armor_section,
            *weapon_section,
            *mobility_section,
        ]),
        footer,
    ])


# Backward-compatible alias (callers that imported the old name still work)
generate_card_html = generate_vehicle_card
