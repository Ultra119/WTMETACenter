import pandas as pd
import streamlit as st


_STEP_MAP: dict = {
    "Каждый WT BR (0.3)": 1,
    "По 1 BR-пункту":     3,
    "Широкие (3 пункта)": 9,
}


def _filters(key_step: str | None, key_all: str, key_n: str):
    use_all = st.session_state.get(key_all, False)

    if key_step:
        col_step, col_n, col_all, col_pad = st.columns([3, 2, 1, 3])
        with col_step:
            step_label = st.selectbox(
                "Детализация кронштейнов",
                options=list(_STEP_MAP.keys()),
                index=0,
                key=key_step,
            )
        step_val = _STEP_MAP[step_label]
    else:
        col_n, col_all, col_pad = st.columns([2, 1, 6])
        step_val = None

    with col_n:
        top_n_val = st.number_input(
            "Топ-N машин  ↕  или →",
            min_value=1, max_value=50, value=5, step=1,
            key=key_n,
            disabled=use_all,
        )

    with col_all:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        st.checkbox("Все", key=key_all, help="Использовать все машины вместо топ-N")

    top_n = None if use_all else int(top_n_val)
    return step_val, top_n


def render(core, meta_filters: dict, selected_types_list: list) -> None:
    br_lo = meta_filters.get("min_br", "?")
    br_hi = meta_filters.get("max_br", "?")
    mode  = meta_filters.get("mode", "All/Mixed")
    st.caption(
        f"📡 Активный диапазон: **{br_lo} – {br_hi}** · режим **{mode}**. "
        f"Изменить — на вкладке **🏆 META Рейтинг**."
    )

    bracket_filters = meta_filters.copy()
    bracket_filters["nation"] = "All"
    bracket_filters["search"] = ""

    df_src = core.calculate_meta(bracket_filters)
    if not selected_types_list:
        df_src = pd.DataFrame()
    elif not df_src.empty:
        df_src = df_src[df_src["Type"].isin(selected_types_list)]
    core.display_df = df_src

    def highlight_brackets(row: pd.Series) -> list:
        row_max_val = row.replace(0, float("nan")).max()
        styles = []
        for val in row:
            if not isinstance(val, (int, float)) or val <= 0 or pd.isna(row_max_val):
                styles.append("color: #475569;")
            elif val == row_max_val:
                styles.append("background-color: #854d0e; color: #fef08a; font-weight: bold;")
            elif val >= row_max_val * 0.90:
                styles.append("color: #a7f3d0;")
            elif val >= row_max_val * 0.75:
                styles.append("color: #fcd34d;")
            else:
                styles.append("color: #f87171;")
        return styles

    sub_meta, sub_mm, sub_nations = st.tabs([
        "📊 META Score по кронштейнам",
        "⚔️ MM-контекст (боль/выгода)",
        "🌍 Топ Наций",
    ])

    with sub_meta:
        step_val, top_n = _filters("brackets_step_meta", "brackets_all_meta", "brackets_topn_meta")
        label = "всех машин" if top_n is None else f"топ-{top_n} машин"
        st.caption(f"Средний META_SCORE **{label}** нации в каждом кронштейне. Золото = лучшая нация в строке.")
        pivot = core.get_bracket_stats(step_val, top_n=top_n)
        if pivot.empty:
            st.warning("Нет данных.")
        else:
            st.dataframe(pivot.style.format("{:.1f}").apply(highlight_brackets, axis=1), width="stretch", height=500)

    with sub_mm:
        step_val_mm, top_n_mm = _filters("brackets_step_mm", "brackets_all_mm", "brackets_topn_mm")
        label_mm = "всех машин" if top_n_mm is None else f"топ-{top_n_mm} машин"
        st.caption(
            f"MM-контекст по **{label_mm}**: скор с учётом позиции в окне матчмейкинга (±1.0 BR). "
            "Высокий META при низком MM-скоре = нация сильна только когда в топе сессии."
        )
        pivot_mm = core.get_mm_context(step_val_mm, top_n=top_n_mm)
        if pivot_mm.empty:
            st.info("Нет данных для MM-анализа.")
        else:
            st.dataframe(pivot_mm.style.format("{:.1f}").apply(highlight_brackets, axis=1), width="stretch", height=500)

    with sub_nations:
        _, top_n_nat = _filters(None, "brackets_all_nat", "brackets_topn_nat")
        core.settings["top_nations_vehicles"] = 9999 if top_n_nat is None else top_n_nat
        core._calculate_nation_dominance()
        stats = core.nation_stats
        label_nat = "всех машин" if top_n_nat is None else f"топ-{top_n_nat} машин"
        st.caption(f"Рейтинг наций по Power Score — среднее META_SCORE **{label_nat}** в диапазоне БР **{br_lo} – {br_hi}**.")
        if stats.empty:
            st.info("Нет данных.")
        else:
            st.dataframe(
                stats,
                column_config={
                    "Nation":         "Нация",
                    "Vehicles_Count": "Машин в пуле",
                    "Best_Vehicle":   "Лидер нации",
                    "Power_Score":    st.column_config.ProgressColumn("Power Score", format="%.1f", min_value=0, max_value=100),
                },
                hide_index=True, width="stretch",
            )
