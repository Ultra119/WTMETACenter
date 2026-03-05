import pandas as pd
import streamlit as st

from ui.components import render_vehicle_card

# Префиксы для колонки Name_Display
_CLASS_PREFIX: dict = {
    "Premium":    "★ ",
    "Pack":       "📦 ",
    "Squadron":   "✦ ",
    "Marketplace": "🏪 ",
    "Standard":   "",
}


def _add_name_display(df: pd.DataFrame) -> pd.DataFrame:
    """Добавляет колонку Name_Display = префикс_класса + Name."""
    if "VehicleClass" in df.columns:
        df = df.copy()
        df["Name_Display"] = df.apply(
            lambda r: _CLASS_PREFIX.get(r["VehicleClass"], "") + str(r["Name"]),
            axis=1,
        )
    else:
        df = df.copy()
        df["Name_Display"] = df["Name"]
    return df


def render(
    core,
    base_filters:        dict,
    selected_types_list: list,
    all_nations:         list,
    wt_br_steps:         list,
    sidebar_card_open:   bool = False,
) -> dict:
    br_min = float(min(wt_br_steps))
    br_max = float(max(wt_br_steps))

    with st.expander("🔎 Фильтры таблицы META", expanded=True):
        c1, c2 = st.columns([1, 2])
        meta_nation = c1.selectbox("Нация", all_nations, key="meta_nation")
        with c2:
            meta_br = st.select_slider(
                "Диапазон БР",
                options=wt_br_steps,
                value=(br_min, br_max),
                key="meta_br",
            )

    meta_filters = base_filters.copy()
    meta_filters.update({
        "search": "",
        "nation": meta_nation,
        "min_br": float(meta_br[0]),
        "max_br": float(meta_br[1]),
    })

    if meta_filters.get("mode") == "All/Mixed":
        st.info(
            "ℹ️ **Режим All/Mixed**: скоры считаются по данным **Realistic Battles** "
            "(приоритет RB → SB → AB). Для чистой статистики выберите конкретный "
            "режим в сайдбаре.",
            icon=None,
        )

    df_meta = core.calculate_meta(meta_filters)

    if not selected_types_list:
        df_meta = pd.DataFrame()
    elif not df_meta.empty:
        df_meta = df_meta[df_meta["Type"].isin(selected_types_list)]

    if df_meta.empty:
        st.warning("Нет данных по заданным критериям.")
        return meta_filters

    df_meta = _add_name_display(df_meta)

    _cols = ["Name_Display", "Nation", "BR", "Type", "Сыграно игр", "WR", "KD", "META_SCORE"]
    _cfg  = {
        "Name_Display": "Техника",
        "Nation":      "Нация",
        "BR":          st.column_config.NumberColumn("БР", format="%.1f"),
        "Type":        "Тип",
        "Сыграно игр": st.column_config.NumberColumn("Бои", format="%d"),
        "WR":          st.column_config.ProgressColumn("WR%", format="%.1f", min_value=0, max_value=100),
        "KD":          st.column_config.NumberColumn("K/D", format="%.2f"),
        "META_SCORE":  st.column_config.ProgressColumn("META", format="%.1f", min_value=0, max_value=100),
    }

    st.caption("💡 Кликни на строку, чтобы открыть карточку техники")

    _df_fingerprint = (len(df_meta), tuple(df_meta["Name"].iloc[:5].tolist()) if len(df_meta) >= 5 else tuple(df_meta["Name"].tolist()))
    if st.session_state.get("_meta_df_fp") != _df_fingerprint:
        st.session_state.pop("_meta_sel_data", None)
        st.session_state["_meta_df_fp"] = _df_fingerprint

    sel = st.dataframe(
        df_meta[_cols],
        column_config=_cfg,
        hide_index=True,
        width="stretch",
        height=520,
        on_select="rerun",
        selection_mode="single-row",
        key="meta_table_sel",
    )

    sel_rows = sel.selection.rows if hasattr(sel, "selection") else []

    if sel_rows:
        idx = sel_rows[0]
        if idx < len(df_meta):
            st.session_state["_meta_sel_data"] = df_meta.iloc[idx].to_dict()
    else:
        st.session_state.pop("_meta_sel_data", None)

    _card_data = st.session_state.get("_meta_sel_data")

    if _card_data is not None:
        if sidebar_card_open:
            st.session_state["sidebar_card_row"] = _card_data
            st.info("📋 Карточка обновлена выше — прокрутите страницу вверх.")
        else:
            st.markdown("---")
            _c_card, _ = st.columns([5, 1])
            with _c_card:
                render_vehicle_card(pd.Series(_card_data))
    elif st.session_state.get("meta_card_pinned") and not sidebar_card_open:
        st.markdown("---")
        render_vehicle_card(st.session_state["meta_card_pinned"])

    return meta_filters
