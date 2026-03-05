import streamlit as st

from ui.type_filter import TypeFilterData, get_types_from_checkboxes, folder_to_category


_WT_NATIONS: set = {
    "USA", "Germany", "USSR", "Britain", "Japan", "Italy",
    "France", "Sweden", "Israel", "China"
}


def get_valid_nations(core) -> list:
    if "Nation" not in core.full_df.columns:
        return ["All"]
    raw = set(core.full_df["Nation"].dropna().unique().tolist())
    valid = {n for n in raw if n.strip().title() in _WT_NATIONS or n in _WT_NATIONS}
    return ["All"] + sorted(valid)


def render_sidebar(
    core,
    all_nations: list,
    all_types:   list,
    tf_data:     TypeFilterData,
    br_min:      float,
    br_max:      float,
) -> tuple[dict, list]:
    st.sidebar.header("🎛️ Глобальные настройки")

    mode_select = st.sidebar.selectbox(
        "Режим игры:",
        ["All/Mixed", "Realistic", "Arcade", "Sim"],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.write("🏷️ **Классы техники:**")

    _fleet_active = (
        st.session_state.get("cb_large_fleet", False)
        or st.session_state.get("cb_small_fleet", False)
    )
    _ground_air_active = (
        st.session_state.get("cb_ground", True)
        or st.session_state.get("cb_air", False)
    )

    cb_ground = st.sidebar.checkbox(
        "🚜 Наземка", value=True, key="cb_ground",
        disabled=_fleet_active,
        help="Недоступно при выборе флота" if _fleet_active else None,
    )
    cb_air = st.sidebar.checkbox(
        "✈️ Авиация", value=False, key="cb_air",
        disabled=_fleet_active,
        help="Недоступно при выборе флота" if _fleet_active else None,
    )

    st.sidebar.markdown(
        "<small style='color:#64748b'>— флот —</small>",
        unsafe_allow_html=True,
    )

    cb_large_fleet = st.sidebar.checkbox(
        "🚢 Большой флот", value=False, key="cb_large_fleet",
        disabled=_ground_air_active,
        help="Недоступно при выборе наземки/авиации" if _ground_air_active else None,
    )
    cb_small_fleet = st.sidebar.checkbox(
        "⛵ Малый флот", value=False, key="cb_small_fleet",
        disabled=_ground_air_active,
        help="Недоступно при выборе наземки/авиации" if _ground_air_active else None,
    )

    selected_types_list = get_types_from_checkboxes(
        ground=cb_ground,
        aviation=cb_air,
        large_fleet=cb_large_fleet,
        small_fleet=cb_small_fleet,
        all_types=all_types,
        type_to_cat=tf_data.type_to_cat,
    )

    _no_type_selected = not any([cb_ground, cb_air, cb_large_fleet, cb_small_fleet])
    if _no_type_selected:
        st.sidebar.warning(
            "⚠️ Не выбран ни один класс техники.\n\n"
            "Все таблицы будут пустыми. Выберите хотя бы один класс выше.",
        )

    st.sidebar.markdown("---")
    battles_inp = st.sidebar.number_input(
        "Мин. боев:", value=50, step=10,
        help="Отсекает технику с малой статистикой",
    )

    st.sidebar.markdown("---")
    st.sidebar.write("💎 **Тип техники:**")

    _ALL_CLASSES = ["Standard", "Premium", "Pack", "Squadron", "Marketplace"]
    _CLASS_LABELS = {
        "Standard":    "🔓 Стандартная",
        "Premium":     "★ Премиум",
        "Pack":        "📦 Пак",
        "Squadron":    "✦ Эскадрилья",
        "Marketplace": "🏪 Маркетплейс",
    }

    selected_classes = st.sidebar.multiselect(
        "Показывать:",
        options=_ALL_CLASSES,
        default=_ALL_CLASSES,
        format_func=lambda x: _CLASS_LABELS.get(x, x),
        key="vehicle_classes_filter",
        help="Фильтрует технику по типу",
    )
    if not selected_classes:
        selected_classes = _ALL_CLASSES

    with st.sidebar.expander("🔍 Debug: типы в данных", expanded=False):
        st.caption("Значения Type загруженных JSON:")
        _debug = core.full_df["Type"].value_counts().reset_index()
        _debug.columns = ["Type (папка/vehicle_type)", "Записей"]
        _debug["→ категория"] = _debug["Type (папка/vehicle_type)"].apply(
            lambda t: (
                tf_data.type_to_cat.get(t)
                or folder_to_category(t)
                or "❓ неизвестно"
            )
        )
        st.dataframe(_debug, hide_index=True, width="stretch")
        st.caption(f"Активный фильтр: `{selected_types_list or '[] = нет данных'}`")

    st.sidebar.markdown("---")
    st.sidebar.markdown("🔍 **Карточка техники**")
    sb_search = st.sidebar.text_input(
        "Поиск по имени:",
        placeholder="Например: Tiger, T-34, F-16…",
        key="sidebar_search",
    )
    if sb_search and not core.full_df.empty:
        sb_df = core.full_df[
            core.full_df["Name"].str.contains(sb_search, case=False, na=False)
        ]
        if not sb_df.empty:
            _nation_col = "Nation" if "Nation" in sb_df.columns else None
            if _nation_col:
                sb_df = sb_df.drop_duplicates(subset=["Name", "Nation"])
                sb_options_raw = [
                    (f"{r['Name']} ({r['Nation']})", r["Name"], r["Nation"])
                    for _, r in sb_df.iterrows()
                ][:30]
            else:
                sb_df = sb_df.drop_duplicates(subset=["Name"])
                sb_options_raw = [
                    (r["Name"], r["Name"], "")
                    for _, r in sb_df.iterrows()
                ][:30]

            sb_labels  = [o[0] for o in sb_options_raw]
            sb_pick_lbl = st.sidebar.selectbox("Выбери технику:", sb_labels, key="sb_pick")
            if st.sidebar.button("📋 Показать карточку", key="sb_show"):
                _idx    = sb_labels.index(sb_pick_lbl)
                _name   = sb_options_raw[_idx][1]
                _nation = sb_options_raw[_idx][2]
                if _nation:
                    sb_row = sb_df[
                        (sb_df["Name"] == _name) & (sb_df["Nation"] == _nation)
                    ].iloc[0]
                else:
                    sb_row = sb_df[sb_df["Name"] == _name].iloc[0]

                row_data = sb_row.to_dict()
                if (
                    not core.display_df.empty
                    and "META_SCORE" in core.display_df.columns
                ):
                    scored = core.display_df[core.display_df["Name"] == _name]
                    if _nation and "Nation" in scored.columns:
                        scored_nat = scored[scored["Nation"] == _nation]
                        if not scored_nat.empty:
                            scored = scored_nat
                    if not scored.empty:
                        row_data = scored.iloc[0].to_dict()

                st.session_state["sidebar_card_row"] = row_data
        else:
            st.sidebar.caption("Ничего не найдено")

    base_filters = {
        "min_battles":     int(battles_inp),
        "mode":            mode_select,
        "search":          "",
        "min_br":          br_min,
        "max_br":          br_max,
        "nation":          "All",
        "type":            "All",
        "vehicle_classes": selected_classes,
    }

    return base_filters, selected_types_list
