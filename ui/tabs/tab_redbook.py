import pandas as pd
import streamlit as st

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
) -> None:
    br_min = float(min(wt_br_steps))
    br_max = float(max(wt_br_steps))

    c1, c2 = st.columns([1, 2])
    rb_nation = c1.selectbox("Нация", all_nations, key="rb_nation")
    with c2:
        rb_br = st.select_slider(
            "БР", options=wt_br_steps, value=(br_min, br_max), key="rb_br"
        )

    rb_filters = base_filters.copy()
    rb_filters.update({
        "search": "",
        "nation": rb_nation,
        "min_br": float(rb_br[0]),
        "max_br": float(rb_br[1]),
    })

    df_rb = core.calculate_meta(rb_filters)
    if not selected_types_list:
        df_rb = pd.DataFrame()
    elif not df_rb.empty:
        df_rb = df_rb[df_rb["Type"].isin(selected_types_list)]

    if df_rb.empty:
        st.info("В Красной Книге пусто.")
        return

    df_rb = (
        df_rb[df_rb["Сыграно игр"] > 0]
        .sort_values("Сыграно игр", ascending=True)
        .head(100)
    )
    df_rb = _add_name_display(df_rb)
    st.dataframe(
        df_rb[["Name_Display", "Nation", "BR", "Сыграно игр", "WR"]],
        column_config={
            "Name_Display": "Техника",
            "Nation":      "Нация",
            "BR":          st.column_config.NumberColumn("БР", format="%.1f"),
            "Сыграно игр": st.column_config.NumberColumn("Бои", format="%d"),
            "WR":          st.column_config.NumberColumn("WR%", format="%.1f"),
        },
        hide_index=True,
        width="stretch",
    )
