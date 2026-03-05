import pandas as pd
import streamlit as st

from analytics import AnalyticsCore, WT_BR_STEPS
from ui.styles     import inject_css
from ui.sidebar    import render_sidebar, get_valid_nations
from ui.type_filter import build_type_filter_data
from ui.components  import render_vehicle_card
from ui.tabs        import tab_meta, tab_redbook, tab_brackets, tab_farm

st.set_page_config(page_title="WT Meta Center", layout="wide", page_icon="🛡️")
inject_css()

@st.cache_resource
def get_core() -> AnalyticsCore:
    core = AnalyticsCore()
    core.load_data_recursive()
    return core


core = get_core()

if core.full_df.empty:
    st.error("❌ База данных пуста. Проверьте JSON файлы.")
    st.stop()

_br_min    = float(min(WT_BR_STEPS))
_br_max    = float(max(WT_BR_STEPS))

all_nations = get_valid_nations(core)
all_types   = (
    sorted(core.full_df["Type"].dropna().unique().tolist())
    if "Type" in core.full_df.columns else []
)
tf_data = build_type_filter_data(all_types)

base_filters, selected_types_list = render_sidebar(
    core        = core,
    all_nations = all_nations,
    all_types   = all_types,
    tf_data     = tf_data,
    br_min      = _br_min,
    br_max      = _br_max,
)

if "sidebar_card_row" in st.session_state:
    _sc_row = pd.Series(st.session_state["sidebar_card_row"])
    with st.expander(f"📋 Карточка: {_sc_row.get('Name', '')}", expanded=True):
        _cc1, _cc2 = st.columns([6, 1])
        with _cc1:
            render_vehicle_card(_sc_row)
        with _cc2:
            if st.button("✕ Закрыть", key="close_sb_card"):
                del st.session_state["sidebar_card_row"]
                st.rerun()
    st.markdown("---")

t_meta, t_redbook, t_brackets, t_farm = st.tabs([
    "🏆 META Рейтинг",
    "💀 Красная Книга",
    "📊 БР Кронштейны",
    "⚙️ Конструктор Сетапа",
])

with t_meta:
    meta_filters = tab_meta.render(
        core                = core,
        base_filters        = base_filters,
        selected_types_list = selected_types_list,
        all_nations         = all_nations,
        wt_br_steps         = WT_BR_STEPS,
        sidebar_card_open   = "sidebar_card_row" in st.session_state,
    )

with t_redbook:
    tab_redbook.render(
        core                = core,
        base_filters        = base_filters,
        selected_types_list = selected_types_list,
        all_nations         = all_nations,
        wt_br_steps         = WT_BR_STEPS,
    )

with t_brackets:
    tab_brackets.render(
        core                = core,
        meta_filters        = meta_filters,
        selected_types_list = selected_types_list,
    )

with t_farm:
    tab_farm.render(
        core                = core,
        base_filters        = base_filters,
        selected_types_list = selected_types_list,
        all_nations         = all_nations,
        wt_br_steps         = WT_BR_STEPS,
        farm_type_opts      = tf_data.farm_type_opts,
        ui_type_cats        = tf_data.ui_type_cats,
    )
