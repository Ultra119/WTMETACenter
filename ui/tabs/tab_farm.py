import streamlit as st
import pandas as pd

_CLASS_PREFIX: dict = {
    "Premium":    "★ ",
    "Pack":       "📦 ",
    "Squadron":   "✦ ",
    "Marketplace": "🏪 ",
    "Standard":   "",
}


def _add_name_display(df: pd.DataFrame) -> pd.DataFrame:
    """Добавляет колонку Name_Display = префикс_класса + Name."""
    if df.empty:
        return df
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
    farm_type_opts:      list,
    ui_type_cats:        dict,
) -> None:
    st.markdown("### ⚙️ Конструктор Сетапа")

    c1, c2, c3, c4 = st.columns(4)
    fs_br   = c1.select_slider("Целевой БР", options=wt_br_steps, value=7.0, key="fs_br")
    fs_nat  = c2.selectbox("Нация", all_nations, key="fs_nat")
    fs_type = c3.selectbox("Тип техники", farm_type_opts, key="fs_type")
    fs_mode = c4.selectbox(
        "Цель",
        ["SL", "RP"],
        format_func=lambda x: "💰 SL (Фарм)" if x == "SL" else "📚 RP (Грайнд)",
    )

    br_min = float(min(wt_br_steps))
    br_max = float(max(wt_br_steps))

    _filter_fingerprint = (
        base_filters.get("mode"),
        base_filters.get("min_battles"),
        tuple(sorted(base_filters.get("vehicle_classes", []))),
        tuple(sorted(selected_types_list)),
    )
    if st.session_state.get("_farm_filter_fp") != _filter_fingerprint:
        st.session_state.pop("farm_result", None)
        st.session_state["_farm_filter_fp"] = _filter_fingerprint

    if st.button("🚀 Подобрать сетап"):
        farm_filters = base_filters.copy()
        farm_filters["nation"] = "All"
        farm_filters["min_br"] = max(br_min, float(fs_br) - 2.0)
        farm_filters["max_br"] = min(br_max, float(fs_br) + 1.0)

        df_farm_src = core.calculate_meta(farm_filters)

        farm_types = ui_type_cats.get(fs_type, None)  # None = All
        if farm_types:
            df_farm_src = df_farm_src[df_farm_src["Type"].isin(farm_types)]

        core.display_df = df_farm_src
        res = core.get_farm_set(float(fs_br), fs_nat, "All")
        st.session_state["farm_result"] = res
        st.session_state["_farm_filter_fp"] = _filter_fingerprint

    if "farm_result" not in st.session_state:
        st.info("Настройте параметры выше и нажмите **🚀 Подобрать сетап**.")
        return

    res = st.session_state["farm_result"]

    if res["anchor"].empty:
        st.error("Не найдена якорная техника на этом БР.")
        return

    anchor = res["anchor"].iloc[0]
    anchor_name = _CLASS_PREFIX.get(anchor.get("VehicleClass", "Standard"), "") + anchor['Name']
    st.success(
        f"⚓ ЯКОРЬ: {anchor_name} ({anchor['BR']:.1f}) | Score: {anchor['FARM_SCORE']:.2f}"
    )

    main_set = _add_name_display(res["main_set"])
    gems     = _add_name_display(res["gems"])

    _sl_col = "Net SL за игру" if "Net SL за игру" in main_set.columns else "SL за игру"
    _sl_lbl = "Net SL/игру" if _sl_col == "Net SL за игру" else "SL/игру"

    _farm_cols = [c for c in [
        "Роль", "Name_Display", "Nation", "BR", "Type",
        "Сыграно игр", "WR", "KD", "FARM_SCORE", _sl_col,
    ] if c in main_set.columns]

    _gem_cols = [c for c in [
        "Name_Display", "Nation", "BR", "Type",
        "Сыграно игр", "WR", "KD", "FARM_SCORE", _sl_col,
    ] if c in gems.columns]

    _farm_cfg = {
        "Name_Display": "Техника",
        "Nation":      "Нация",
        "BR":          st.column_config.NumberColumn("БР", format="%.1f"),
        "Сыграно игр": st.column_config.NumberColumn("Бои", format="%d"),
        "WR":          st.column_config.ProgressColumn("WR%", format="%.1f", min_value=0, max_value=100),
        "KD":          st.column_config.NumberColumn("K/D", format="%.2f"),
        "FARM_SCORE":  st.column_config.ProgressColumn("Farm", format="%.1f", min_value=0, max_value=100),
        _sl_col:       st.column_config.NumberColumn(_sl_lbl, format="%d"),
    }

    st.write("#### 🛠️ Основной состав")
    st.dataframe(
        main_set[_farm_cols],
        column_config=_farm_cfg,
        hide_index=True,
        width="stretch",
    )

    st.write("#### 💎 Жемчужины (Low Rank / High Efficiency)")
    if gems.empty:
        st.caption("Нет жемчужин в диапазоне -2.0 BR с Farm Score выше якоря.")
    else:
        st.dataframe(
            gems[_gem_cols],
            column_config=_farm_cfg,
            hide_index=True,
            width="stretch",
        )
