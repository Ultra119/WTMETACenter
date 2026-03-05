import pandas as pd


def calculate_nation_dominance(display_df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    if display_df.empty:
        return pd.DataFrame()

    df  = display_df.copy()
    top = settings.get("top_nations_vehicles", 5)

    def nation_power(g: pd.DataFrame) -> pd.Series:
        top_vehicles = g.nlargest(top, "META_SCORE")
        return pd.Series({
            "Power_Score":    top_vehicles["META_SCORE"].mean(),
            "Vehicles_Count": len(g),
            "Best_Vehicle":   top_vehicles.iloc[0]["Name"] if not top_vehicles.empty else "N/A",
        })

    nat_stats = (
        df.groupby("Nation")
          .apply(nation_power, include_groups=False)
          .reset_index()
    )
    return nat_stats.sort_values(by="Power_Score", ascending=False)
