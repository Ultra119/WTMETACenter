import numpy as np
import pandas as pd

from analytics.constants import ROLE_WEIGHTS


_MODE_PRIORITY: list[str] = ["Realistic", "Simulator", "Arcade"]


def aggregate_modes(x: pd.DataFrame) -> pd.Series:
    if len(x) == 1:
        return x.iloc[0].copy()

    total_battles = x["Сыграно игр"].sum()

    if "Mode" in x.columns:
        for preferred in _MODE_PRIORITY:
            subset = x[x["Mode"] == preferred]
            if not subset.empty:
                res = subset.iloc[0].copy()
                res["Сыграно игр"] = total_battles
                res["Mode"] = "Mixed"
                return res

    res = x.iloc[0].copy()
    res["Сыграно игр"] = total_battles
    res["Mode"] = "Mixed"
    return res

def score(df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    df = df.copy()

    mm_window = float(settings.get("mm_window", 1.0))
    sig_scale = float(settings.get("sigmoid_scale", 1.5))
    z_clip    = float(settings.get("z_clip", 3.0))

    spawns = df["Возрождения"].clip(lower=1)
    df["_ks_g_raw"] = df["Наземные убийства"]  / spawns
    df["_ks_a_raw"] = df["Воздушные убийства"] / spawns
    df["_ks_n_raw"] = df["Морские убийства"]   / spawns
    df["_kd_raw"]   = df["KD"]
    df["_wr_raw"]   = df["WR"] / 100.0
    df["_surv_raw"] = (1.0 - (df["Смерти"] / spawns)).clip(0.0, 1.0)

    unique_brs  = df["BR"].unique()
    metric_keys = ["_wr", "_kd", "_ks_g", "_ks_a", "_ks_n", "_surv"]

    for k in metric_keys:
        df[k]          = 0.0
        df[f"z{k}"]    = 0.0

    C_battles = 200.0
    C_spawns  = 300.0

    for br in unique_brs:
        mask_peer = (df["BR"] >= br - mm_window) & (df["BR"] <= br + mm_window)
        peers     = df.loc[mask_peer]

        if peers.empty:
            continue

        total_games   = max(peers["Сыграно игр"].sum(), 1)
        total_spawns  = max(peers["Возрождения"].sum(),  1)

        avg_wr   = (peers["WR"]  * peers["Сыграно игр"]).sum() / total_games / 100.0
        avg_kd   = (peers["KD"]  * peers["Сыграно игр"]).sum() / total_games
        avg_ks_g = (peers["_ks_g_raw"] * peers["Возрождения"]).sum() / total_spawns
        avg_ks_a = (peers["_ks_a_raw"] * peers["Возрождения"]).sum() / total_spawns

        mask_self = df["BR"] == br
        row_slice = df.loc[mask_self]
        n_games   = row_slice["Сыграно игр"]
        n_spawns  = row_slice["Возрождения"]

        df.loc[mask_self, "_wr"] = (
            (row_slice["_wr_raw"] * n_games + avg_wr * C_battles)
            / (n_games + C_battles)
        ) * 100.0

        df.loc[mask_self, "_kd"] = (
            (row_slice["_kd_raw"] * n_games + avg_kd * C_battles)
            / (n_games + C_battles)
        )

        df.loc[mask_self, "_ks_g"] = (
            (row_slice["_ks_g_raw"] * n_spawns + avg_ks_g * C_spawns)
            / (n_spawns + C_spawns)
        )
        df.loc[mask_self, "_ks_a"] = (
            (row_slice["_ks_a_raw"] * n_spawns + avg_ks_a * C_spawns)
            / (n_spawns + C_spawns)
        )

        df.loc[mask_self, "_ks_n"] = row_slice["_ks_n_raw"]
        df.loc[mask_self, "_surv"] = row_slice["_surv_raw"]

        for m_col in metric_keys:
            z_col   = f"z{m_col}"
            raw_col = m_col + "_raw"   # "_wr_raw", "_ks_n_raw", "_surv_raw", …

            if raw_col in peers.columns:
                p_vals = peers[raw_col] * (100.0 if m_col == "_wr" else 1.0)
            else:
                p_vals = peers[m_col]

            mu    = p_vals.mean()
            sigma = p_vals.std()
            if pd.isna(sigma) or sigma < 1e-9:
                sigma = 1.0

            df.loc[mask_self, z_col] = (
                (df.loc[mask_self, m_col] - mu) / sigma
            ).clip(-z_clip, z_clip)

    def _sigmoid(z_col: str) -> pd.Series:
        return 100.0 / (1.0 + np.exp(-sig_scale * df[z_col]))

    s_wr   = _sigmoid("z_wr")
    s_kd   = _sigmoid("z_kd")
    s_ks_g = _sigmoid("z_ks_g")
    s_ks_a = _sigmoid("z_ks_a")
    s_ks_n = _sigmoid("z_ks_n")
    s_surv = _sigmoid("z_surv")

    df["META_SCORE"] = 0.0

    for idx, row in df.iterrows():
        vtype   = row["Type"]
        weights = ROLE_WEIGHTS.get(vtype, ROLE_WEIGHTS["_default"]).copy()

        if vtype == "spaa" and row["_ks_g"] > row["_ks_a"] * 1.5:
            weights = ROLE_WEIGHTS["tank_destroyer"].copy()

        if vtype == "light_tank" and row["_kd"] > 2.0 and row["_wr"] < 50:
            weights["wr"] *= 0.7
            weights["kd"] *= 1.3

        w_sum = sum(weights.values())
        for k in weights:
            weights[k] /= w_sum

        base_score = (
            weights.get("wr",   0) * s_wr[idx]   +
            weights.get("kd",   0) * s_kd[idx]   +
            weights.get("ks_g", 0) * s_ks_g[idx] +
            weights.get("ks_a", 0) * s_ks_a[idx] +
            weights.get("ks_n", 0) * s_ks_n[idx] +
            weights.get("surv", 0) * s_surv[idx]
        )

        diff              = abs(s_wr[idx] - s_kd[idx])
        consistency_factor = 1.0 - (diff / 200.0)
        final_score        = base_score * consistency_factor

        battles = row["Сыграно игр"]
        if battles > 100:
            final_score += np.log10(battles) * 0.5

        df.at[idx, "META_SCORE"] = final_score

    df["META_SCORE"] = df["META_SCORE"].clip(0.0, 100.0)

    if "vdb_repair_cost_realistic" in df.columns:
        repair = df["vdb_repair_cost_realistic"].fillna(0).astype(float)
        has_vdb = df.get("vdb_match_score", pd.Series(0.0, index=df.index)) > 0
        net_sl  = df["SL за игру"].where(~has_vdb, df["SL за игру"] - repair)
    else:
        net_sl = df["SL за игру"]

    df["_sl_eff"] = net_sl.clip(lower=0) * (df["_wr"] / 50.0).clip(lower=0.5)
    df["Net SL за игру"] = net_sl.round(0).astype(int)
    df["_z_sl"]   = 0.0

    for br in unique_brs:
        mask_peer = (df["BR"] >= br - mm_window) & (df["BR"] <= br + mm_window)
        mu    = df.loc[mask_peer, "_sl_eff"].mean()
        sigma = df.loc[mask_peer, "_sl_eff"].std()
        if pd.isna(sigma) or sigma < 1e-9:
            sigma = 1.0
        df.loc[df["BR"] == br, "_z_sl"] = (
            (df.loc[df["BR"] == br, "_sl_eff"] - mu) / sigma
        ).clip(-z_clip, z_clip)

    df["FARM_SCORE"] = (
        100.0 / (1.0 + np.exp(-sig_scale * df["_z_sl"]))
    ).clip(0, 100)

    drop_cols = [c for c in df.columns if (c.startswith("_") or c.startswith("z_")) and c != "Net SL за игру"]
    df.drop(columns=drop_cols, inplace=True, errors="ignore")

    return df
