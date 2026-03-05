import pandas as pd


def get_farm_set(
    display_df: pd.DataFrame,
    target_br: float,
    nation: str = "All",
    vehicle_type: str = "All",
) -> dict:
    empty = pd.DataFrame()

    if display_df.empty or "FARM_SCORE" not in display_df.columns:
        return {
            "anchor": empty, "main_set": empty,
            "gems": empty,   "by_type": empty,
            "target_br": target_br,
        }

    df = display_df.copy()

    if nation != "All":
        df = df[df["Nation"] == nation]
    if vehicle_type != "All":
        df = df[df["Type"] == vehicle_type]

    anchor_df = df[
        (df["BR"] >= target_br - 0.15) &
        (df["BR"] <= target_br + 0.15)
    ].sort_values("FARM_SCORE", ascending=False)

    anchor_row  = anchor_df.head(1)
    anchor_farm = float(anchor_row["FARM_SCORE"].iloc[0]) if not anchor_row.empty else 0.0

    main_pool = df[
        (df["BR"] >= target_br - 1.0) &
        (df["BR"] <= target_br + 0.15)
    ].sort_values("FARM_SCORE", ascending=False)

    main_set = main_pool.head(7).copy()

    def assign_role(row: pd.Series) -> str:
        if abs(row["BR"] - target_br) <= 0.15:
            return "⚓ Якорь"
        elif row["FARM_SCORE"] >= anchor_farm * 0.9:
            return "💰 Топ-фармер"
        return "🔄 Резерв"

    if not main_set.empty:
        main_set["Роль"] = main_set.apply(assign_role, axis=1)

    gems_pool = df[
        (df["BR"] >= target_br - 2.0) &
        (df["BR"] <  target_br - 1.0 + 0.15)
    ]
    gems = (
        gems_pool[gems_pool["FARM_SCORE"] > anchor_farm]
        .sort_values("FARM_SCORE", ascending=False)
        .head(5)
    )

    if not main_pool.empty and "Type" in main_pool.columns:
        by_type = (
            main_pool
            .sort_values("FARM_SCORE", ascending=False)
            .groupby("Type", sort=False)
            .first()
            .reset_index()
        )
    else:
        by_type = empty

    return {
        "anchor":    anchor_row,
        "main_set":  main_set,
        "gems":      gems,
        "by_type":   by_type,
        "target_br": target_br,
    }
