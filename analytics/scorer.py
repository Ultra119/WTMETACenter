from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.constants import (
    ROLE_WEIGHTS, VEHICLE_TYPE_CATEGORY,
    SCORING_PEER_GROUP, FARM_SCORING_PEER_GROUP,
    ROLE_SHIFT_RAW_THRESHOLDS,
)


_SHIFT_MIN_BATTLES = 1000.0
_SIG_CALIBRATION = 2.0

_REPAIR_COL_BY_MODE: dict[str, str] = {
    "Realistic":  "vdb_repair_cost_realistic",
    "Arcade":     "vdb_repair_cost_arcade",
    "Simulator":  "vdb_repair_cost_simulator",
}

_SL_MUL_COL_BY_MODE: dict[str, str] = {
    "Realistic":  "vdb_sl_mul_realistic",
    "Arcade":     "vdb_sl_mul_arcade",
    "Simulator":  "vdb_sl_mul_simulator",
}

_MIN_SL_MUL           = 0.3
_DEFAULT_MUL_EXPONENT = 1.35
_MIN_EXPONENT_ROWS    = 80

_EXPONENT_CACHE: dict = {}


def _sl_multiplier(df: pd.DataFrame) -> pd.Series:
    mul = pd.Series(np.nan, index=df.index)

    if "Mode" in df.columns:
        for mode_name, col_name in _SL_MUL_COL_BY_MODE.items():
            if col_name in df.columns:
                mask = df["Mode"] == mode_name
                mul = mul.where(~mask, df[col_name].astype(float))

    for col_name in _SL_MUL_COL_BY_MODE.values():
        if col_name in df.columns:
            mul = mul.fillna(df[col_name].astype(float))

    return mul.fillna(1.0).clip(lower=_MIN_SL_MUL)


def _premium_residual(values, df) -> float:
    y = np.log(values.values if hasattr(values, 'values') else values)
    X = np.column_stack([
        np.ones(len(y)),
        df["WR"].astype(float).values,
        df["_kills_raw"].astype(float).values,
        df["_deaths_raw"].astype(float).values,
        (df["VehicleClass"] != "Standard").astype(float).values,
    ])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return float(coef[4])


def _fit_mul_exponent(sub: pd.DataFrame, mul: pd.Series) -> float:
    best_abs, best_a = None, _DEFAULT_MUL_EXPONENT

    for a in np.arange(0.6, 2.01, 0.05):
        values = sub["SL за игру"].astype(float) / mul.loc[sub.index] ** a
        if not np.isfinite(values).all() or (values <= 0).any():
            continue
        residual = _premium_residual(values, sub)
        if best_abs is None or abs(residual) < best_abs:
            best_abs, best_a = abs(residual), round(float(a), 2)

    return best_a


def _compute_net_sl(df: pd.DataFrame) -> np.ndarray:
    has_vdb = df.get("vdb_match_score", pd.Series(0.0, index=df.index)).values > 0

    repair = np.zeros(len(df), dtype=float)

    if "Mode" in df.columns:
        mode_arr = df["Mode"].values
        for mode_name, col_name in _REPAIR_COL_BY_MODE.items():
            if col_name in df.columns:
                mask = (mode_arr == mode_name)
                repair[mask] = df[col_name].fillna(0).astype(float).values[mask]

    repair[~has_vdb] = 0.0

    games = df["Сыграно игр"].values.astype(float)
    deaths = df["Смерти"].values.astype(float)
    sl_game = df["SL за игру"].values.astype(float)

    deaths_per_game = deaths / np.maximum(games, 1.0)
    repair_per_game = repair * deaths_per_game

    result = sl_game.copy()
    result[has_vdb] = sl_game[has_vdb] - repair_per_game[has_vdb]
    return result


def _compute_activity(df: pd.DataFrame) -> np.ndarray:
    mul = _sl_multiplier(df)
    exponent = pd.Series(_DEFAULT_MUL_EXPONENT, index=df.index)

    if "Type" in df.columns and "VehicleClass" in df.columns:
        usable = df[(df["SL за игру"] > 0) & mul.notna()]
        for vtype, sub in usable.groupby("Type"):
            if len(sub) < _MIN_EXPONENT_ROWS:
                continue
            if vtype not in _EXPONENT_CACHE:
                _EXPONENT_CACHE[vtype] = _fit_mul_exponent(sub, mul)
            exponent.loc[df["Type"] == vtype] = _EXPONENT_CACHE[vtype]

    games = df["Сыграно игр"].values.astype(float)
    return df["SL за игру"].astype(float).values / np.maximum(mul.values.astype(float), 1e-9) ** exponent.values


def _weighted_avg_np(values: np.ndarray, weights: np.ndarray) -> float:
    w = np.clip(weights, 0, None)
    total = w.sum()
    if total < 1e-9:
        return float(np.mean(values))
    return float(np.dot(values, w) / total)


def score(df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    df = df.copy()

    mm_window = float(settings.get("mm_window",     1.0))
    sig_scale = float(settings.get("sigmoid_scale", 1.5))
    z_clip    = float(settings.get("z_clip",         3.0))
    C_battles = float(settings.get("c_battles", 5000.0))
    C_spawns  = float(settings.get("c_spawns",  7500.0))

    if not np.isfinite(sig_scale) or sig_scale <= 0.0:
        sig_scale = 1.5
    if not np.isfinite(z_clip) or z_clip <= 0.0:
        z_clip = 3.0
    if not np.isfinite(mm_window) or mm_window < 0.0:
        mm_window = 1.0
    if not np.isfinite(C_battles) or C_battles < 0.0:
        C_battles = 5000.0
    if not np.isfinite(C_spawns) or C_spawns < 0.0:
        C_spawns = 7500.0

    n = len(df)
    
    # Pre-extract numpy arrays
    games = df["Сыграно игр"].values.astype(float)
    spawns = np.clip(df["Возрождения"].values.astype(float), 1, None)
    
    g_kills = df["Наземные убийства"].values.astype(float)
    a_kills = df["Воздушные убийства"].values.astype(float)
    n_kills = df["Морские убийства"].values.astype(float)
    deaths = df["Смерти"].values.astype(float)
    
    wr_raw = (df["WR"].values.astype(float) / 100.0).clip(0.0, 1.0)
    ks_g_raw = g_kills / spawns
    ks_a_raw = a_kills / spawns
    ks_n_raw = n_kills / spawns
    
    deaths_for_kd = np.clip(deaths, 1, None)
    kd_ground = g_kills / deaths_for_kd
    kd_air = a_kills / deaths_for_kd
    kd_naval = n_kills / deaths_for_kd
    
    kills_raw = (g_kills + a_kills + n_kills) / np.maximum(games, 1.0)
    deaths_raw = deaths / np.maximum(games, 1.0)
    
    # These columns are needed by _premium_residual via _compute_activity
    df["_kills_raw"] = kills_raw
    df["_deaths_raw"] = deaths_raw
    
    sl_eff = _compute_net_sl(df)
    act_raw = _compute_activity(df)
    
    # Pre-extract categorical arrays
    mode_arr = df["Mode"].values if "Mode" in df.columns else np.array([None] * n)
    br_arr = df["BR"].values.astype(float)
    type_arr = df["Type"].values
    pg_arr = df["Type"].values  # Will map to SCORING_PEER_GROUP
    pg_arr = np.array([SCORING_PEER_GROUP.get(t, t) for t in type_arr])
    farm_pg_arr = np.array([FARM_SCORING_PEER_GROUP.get(t, t) for t in type_arr])
    
    # Get unique values
    unique_modes = np.unique(mode_arr) if "Mode" in df.columns else np.array([None])
    unique_brs = np.unique(br_arr)
    type_groups = np.unique(pg_arr)
    
    # Precompute masks
    mode_masks = {m: (mode_arr == m) for m in unique_modes}
    br_window_masks = {}
    br_exact_masks = {}
    for br in unique_brs:
        br_window_masks[br] = (br_arr >= br - mm_window) & (br_arr <= br + mm_window)
        br_exact_masks[br] = (br_arr == br)
    pg_masks = {tg: (pg_arr == tg) for tg in type_groups}
    
    # Global averages for fallback
    _global_avg: dict[tuple, dict[str, float]] = {}
    for _mode in unique_modes:
        _mask_mode = mode_masks[_mode] if _mode is not None else np.ones(n, dtype=bool)
        for _tg in type_groups:
            _g_mask = pg_masks[_tg] & _mask_mode
            _g_idx = np.where(_g_mask)[0]
            if len(_g_idx) == 0:
                continue
            _global_avg[(_tg, _mode)] = {
                "avg_wr":   _weighted_avg_np(wr_raw[_g_idx],   games[_g_idx]),
                "avg_ks_g": _weighted_avg_np(ks_g_raw[_g_idx], spawns[_g_idx]),
                "avg_ks_a": _weighted_avg_np(ks_a_raw[_g_idx], spawns[_g_idx]),
                "avg_ks_n": _weighted_avg_np(ks_n_raw[_g_idx], spawns[_g_idx]),
                "avg_act":  _weighted_avg_np(act_raw[_g_idx],  games[_g_idx]),
            }
    
    # Output arrays for shrunk metrics
    out_wr = np.zeros(n)
    out_ks_g = np.zeros(n)
    out_ks_a = np.zeros(n)
    out_ks_n = np.zeros(n)
    out_act = np.zeros(n)
    
    # PASS 1: Compute shrunk metrics using numpy
    for mode in unique_modes:
        m_mask = mode_masks[mode] if mode is not None else np.ones(n, dtype=bool)
        for br in unique_brs:
            br_win = br_window_masks[br]
            br_ex = br_exact_masks[br]
            for tg in type_groups:
                tg_m = pg_masks[tg]
                
                peer_mask = m_mask & br_win & tg_m
                self_mask = m_mask & br_ex & tg_m
                
                self_idx = np.where(self_mask)[0]
                if len(self_idx) == 0:
                    continue
                
                ext_mask = peer_mask & ~self_mask
                ext_idx = np.where(ext_mask)[0]
                
                if len(ext_idx) == 0:
                    g_avg = _global_avg.get((tg, mode), {})
                    avg_wr = g_avg.get("avg_wr", 0.5)
                    avg_ks_g = g_avg.get("avg_ks_g", 0.5)
                    avg_ks_a = g_avg.get("avg_ks_a", 0.1)
                    avg_ks_n = g_avg.get("avg_ks_n", 0.0)
                    avg_act = g_avg.get("avg_act", 0.0)
                else:
                    w_b = np.clip(games[ext_idx], 0, None)
                    w_s = np.clip(spawns[ext_idx], 0, None)
                    total_b = w_b.sum()
                    total_s = w_s.sum()
                    
                    if total_b < 1e-9:
                        avg_wr = wr_raw[ext_idx].mean()
                        avg_act = act_raw[ext_idx].mean()
                    else:
                        avg_wr = np.dot(wr_raw[ext_idx], w_b) / total_b
                        avg_act = np.dot(act_raw[ext_idx], w_b) / total_b
                    
                    if total_s < 1e-9:
                        avg_ks_g = ks_g_raw[ext_idx].mean()
                        avg_ks_a = ks_a_raw[ext_idx].mean()
                        avg_ks_n = ks_n_raw[ext_idx].mean()
                    else:
                        avg_ks_g = np.dot(ks_g_raw[ext_idx], w_s) / total_s
                        avg_ks_a = np.dot(ks_a_raw[ext_idx], w_s) / total_s
                        avg_ks_n = np.dot(ks_n_raw[ext_idx], w_s) / total_s
                
                # Apply shrinkage to self rows
                n_g_self = games[self_idx]
                n_s_self = spawns[self_idx]
                d_g = np.maximum(n_g_self + C_battles, 1e-9)
                d_s = np.maximum(n_s_self + C_spawns, 1e-9)
                
                out_wr[self_idx] = (wr_raw[self_idx] * n_g_self + avg_wr * C_battles) / d_g
                out_ks_g[self_idx] = (g_kills[self_idx] + avg_ks_g * C_spawns) / d_s
                out_ks_a[self_idx] = (a_kills[self_idx] + avg_ks_a * C_spawns) / d_s
                out_ks_n[self_idx] = (n_kills[self_idx] + avg_ks_n * C_spawns) / d_s
                out_act[self_idx] = (act_raw[self_idx] * n_g_self + avg_act * C_battles) / d_g
    
    # PASS 2: Compute z-scores using numpy
    # First compute global sigma (median/MAD per type_group+mode)
    _global_sigma: dict[tuple, dict[str, float]] = {}
    for mode in unique_modes:
        m_mask = mode_masks[mode] if mode is not None else np.ones(n, dtype=bool)
        for tg in type_groups:
            g_mask = pg_masks[tg] & m_mask
            g_idx = np.where(g_mask)[0]
            if len(g_idx) == 0:
                continue
            
            sigs = {}
            for arr_name, arr in [("_wr", out_wr), ("_ks_g", out_ks_g), 
                                   ("_ks_a", out_ks_a), ("_ks_n", out_ks_n), 
                                   ("_act", out_act)]:
                vals = arr[g_idx]
                mu = np.median(vals)
                mad = np.median(np.abs(vals - mu))
                sigma = mad * 1.4826
                sigs[arr_name] = float(sigma) if (not np.isnan(sigma) and sigma > 1e-9) else 0.0
            _global_sigma[(tg, mode)] = sigs
    
    out_z_wr = np.zeros(n)
    out_z_ks_g = np.zeros(n)
    out_z_ks_a = np.zeros(n)
    out_z_ks_n = np.zeros(n)
    out_z_act = np.zeros(n)
    
    for mode in unique_modes:
        m_mask = mode_masks[mode] if mode is not None else np.ones(n, dtype=bool)
        for br in unique_brs:
            br_win = br_window_masks[br]
            br_ex = br_exact_masks[br]
            for tg in type_groups:
                tg_m = pg_masks[tg]
                
                peer_mask = m_mask & br_win & tg_m
                self_mask = m_mask & br_ex & tg_m
                
                self_idx = np.where(self_mask)[0]
                if len(self_idx) == 0:
                    continue
                
                ext_mask = peer_mask & ~self_mask
                ext_idx = np.where(ext_mask)[0]
                
                if len(ext_idx) == 0:
                    ext_idx = np.where(peer_mask)[0]
                
                g_sigs = _global_sigma.get((tg, mode), {})
                
                # Compute z-scores for each metric
                for arr_name, out_z, g_sig_default in [
                    ("_wr", out_z_wr, g_sigs.get("_wr", 0.0)),
                    ("_ks_g", out_z_ks_g, g_sigs.get("_ks_g", 0.0)),
                    ("_ks_a", out_z_ks_a, g_sigs.get("_ks_a", 0.0)),
                    ("_ks_n", out_z_ks_n, g_sigs.get("_ks_n", 0.0)),
                    ("_act", out_z_act, g_sigs.get("_act", 0.0)),
                ]:
                    arr = {"_wr": out_wr, "_ks_g": out_ks_g, "_ks_a": out_ks_a, 
                           "_ks_n": out_ks_n, "_act": out_act}[arr_name]
                    
                    p_vals = arr[ext_idx]
                    mu = np.median(p_vals)
                    mad = np.median(np.abs(p_vals - mu))
                    sigma = mad * 1.4826
                    
                    if np.isnan(sigma) or sigma < 1e-9:
                        sigma = g_sig_default
                    
                    if sigma < 1e-9:
                        continue
                    
                    z_vals = (arr[self_idx] - mu) / sigma
                    out_z[self_idx] = np.clip(z_vals, -z_clip, z_clip)
    
    # Compute sigmoid scores
    z_cal = z_clip * _SIG_CALIBRATION
    lo = 100.0 / (1.0 + np.exp(sig_scale * z_cal))
    hi = 100.0 / (1.0 + np.exp(-sig_scale * z_cal))
    
    def _sigmoid_arr(z_arr):
        raw = 100.0 / (1.0 + np.exp(-sig_scale * z_arr))
        return ((raw - lo) / (hi - lo) * 100.0).clip(0.0, 100.0)
    
    s_wr = _sigmoid_arr(out_z_wr)
    s_ks_g = _sigmoid_arr(out_z_ks_g)
    s_ks_a = _sigmoid_arr(out_z_ks_a)
    s_ks_n = _sigmoid_arr(out_z_ks_n)
    s_act = _sigmoid_arr(out_z_act)
    
    # Compute META_SCORE vectorized
    meta_score = np.zeros(n)
    
    # Pre-build weight arrays per type
    w_wr = np.zeros(n)
    w_ks_g = np.zeros(n)
    w_ks_a = np.zeros(n)
    w_ks_n = np.zeros(n)
    w_act = np.zeros(n)
    
    for vtype, w in ROLE_WEIGHTS.items():
        if vtype == "_default":
            continue
        mask = (type_arr == vtype)
        w_wr[mask] = w.get("wr", 0)
        w_ks_g[mask] = w.get("ks_g", 0)
        w_ks_a[mask] = w.get("ks_a", 0)
        w_ks_n[mask] = w.get("ks_n", 0)
        w_act[mask] = w.get("act", 0)
    
    # Apply default weights to unmatched types
    default_mask = ~np.isin(type_arr, [k for k in ROLE_WEIGHTS.keys() if k != "_default"])
    if default_mask.any():
        w_wr[default_mask] = ROLE_WEIGHTS["_default"]["wr"]
        w_ks_g[default_mask] = ROLE_WEIGHTS["_default"]["ks_g"]
        w_ks_a[default_mask] = ROLE_WEIGHTS["_default"]["ks_a"]
        w_ks_n[default_mask] = ROLE_WEIGHTS["_default"]["ks_n"]
        w_act[default_mask] = ROLE_WEIGHTS["_default"]["act"]
    
    # Apply role shifts
    min_batt_mask = games >= _SHIFT_MIN_BATTLES
    
    # spaa shift
    spaa_mask = (type_arr == "spaa") & min_batt_mask
    if spaa_mask.any():
        thr = ROLE_SHIFT_RAW_THRESHOLDS.get(("spaa", "_ks_g_raw"), 0.70)
        if thr > 0:
            t = np.clip((ks_g_raw[spaa_mask] - thr) / thr, 0, 1)
            w_alt = ROLE_WEIGHTS["tank_destroyer"]
            w_wr[spaa_mask] = w_wr[spaa_mask] * (1 - t) + w_alt["wr"] * t
            w_ks_g[spaa_mask] = w_ks_g[spaa_mask] * (1 - t) + w_alt["ks_g"] * t
            w_ks_a[spaa_mask] = w_ks_a[spaa_mask] * (1 - t) + w_alt["ks_a"] * t
            w_ks_n[spaa_mask] = w_ks_n[spaa_mask] * (1 - t) + w_alt["ks_n"] * t
            w_act[spaa_mask] = w_act[spaa_mask] * (1 - t) + w_alt["act"] * t
    
    # tank_destroyer, light_tank, medium_tank shift
    for vtype in ["tank_destroyer", "light_tank", "medium_tank"]:
        vt_mask = (type_arr == vtype) & min_batt_mask
        if vt_mask.any():
            thr = ROLE_SHIFT_RAW_THRESHOLDS.get((vtype, "_ks_a_raw"), 0.12)
            if thr > 0:
                t = np.clip((ks_a_raw[vt_mask] - thr) / thr, 0, 1)
                w_alt = ROLE_WEIGHTS["spaa"]
                w_wr[vt_mask] = w_wr[vt_mask] * (1 - t) + w_alt["wr"] * t
                w_ks_g[vt_mask] = w_ks_g[vt_mask] * (1 - t) + w_alt["ks_g"] * t
                w_ks_a[vt_mask] = w_ks_a[vt_mask] * (1 - t) + w_alt["ks_a"] * t
                w_ks_n[vt_mask] = w_ks_n[vt_mask] * (1 - t) + w_alt["ks_n"] * t
                w_act[vt_mask] = w_act[vt_mask] * (1 - t) + w_alt["act"] * t
    
    # fighter shift
    fighter_mask = (type_arr == "fighter") & min_batt_mask
    if fighter_mask.any():
        thr = ROLE_SHIFT_RAW_THRESHOLDS.get(("fighter", "_ks_g_raw"), 0.85)
        if thr > 0:
            t = np.clip((ks_g_raw[fighter_mask] - thr) / thr, 0, 1)
            w_alt = ROLE_WEIGHTS["assault"]
            w_wr[fighter_mask] = w_wr[fighter_mask] * (1 - t) + w_alt["wr"] * t
            w_ks_g[fighter_mask] = w_ks_g[fighter_mask] * (1 - t) + w_alt["ks_g"] * t
            w_ks_a[fighter_mask] = w_ks_a[fighter_mask] * (1 - t) + w_alt["ks_a"] * t
            w_ks_n[fighter_mask] = w_ks_n[fighter_mask] * (1 - t) + w_alt["ks_n"] * t
            w_act[fighter_mask] = w_act[fighter_mask] * (1 - t) + w_alt["act"] * t
    
    # assault, bomber shift
    for vtype in ["assault", "bomber"]:
        vt_mask = (type_arr == vtype) & min_batt_mask
        if vt_mask.any():
            thr = ROLE_SHIFT_RAW_THRESHOLDS.get((vtype, "_ks_a_raw"), 0.65)
            if thr > 0:
                t = np.clip((ks_a_raw[vt_mask] - thr) / thr, 0, 1)
                w_alt = ROLE_WEIGHTS["fighter"]
                w_wr[vt_mask] = w_wr[vt_mask] * (1 - t) + w_alt["wr"] * t
                w_ks_g[vt_mask] = w_ks_g[vt_mask] * (1 - t) + w_alt["ks_g"] * t
                w_ks_a[vt_mask] = w_ks_a[vt_mask] * (1 - t) + w_alt["ks_a"] * t
                w_ks_n[vt_mask] = w_ks_n[vt_mask] * (1 - t) + w_alt["ks_n"] * t
                w_act[vt_mask] = w_act[vt_mask] * (1 - t) + w_alt["act"] * t
    
    # Normalize weights
    w_sum = w_wr + w_ks_g + w_ks_a + w_ks_n + w_act
    w_sum = np.maximum(w_sum, 1e-9)
    w_wr /= w_sum
    w_ks_g /= w_sum
    w_ks_a /= w_sum
    w_ks_n /= w_sum
    w_act /= w_sum
    
    # Compute final META_SCORE
    meta_score = (w_wr * s_wr + w_ks_g * s_ks_g + w_ks_a * s_ks_a + 
                  w_ks_n * s_ks_n + w_act * s_act)
    meta_score = meta_score.clip(0.0, 100.0)
    
    # Write results to df
    df["_wr"] = out_wr
    df["_ks_g"] = out_ks_g
    df["_ks_a"] = out_ks_a
    df["_ks_n"] = out_ks_n
    df["_act"] = out_act
    df["z_wr"] = out_z_wr
    df["z_ks_g"] = out_z_ks_g
    df["z_ks_a"] = out_z_ks_a
    df["z_ks_n"] = out_z_ks_n
    df["z_ks_act"] = out_z_act
    df["META_SCORE"] = meta_score
    df["KD_GROUND"] = kd_ground
    df["KD_AIR"] = kd_air
    df["KD_NAVAL"] = kd_naval
    df["Net SL за игру"] = np.round(sl_eff).astype(int)
    
    # FARM_SCORE (already vectorized in original)
    farm_type_groups = np.unique(farm_pg_arr)
    farm_pct = np.zeros(n)
    
    for mode in unique_modes:
        m_mask = mode_masks[mode] if mode is not None else np.ones(n, dtype=bool)
        for tg in farm_type_groups:
            tg_mask = (farm_pg_arr == tg) & m_mask
            tg_idx = np.where(tg_mask)[0]
            if len(tg_idx) == 0:
                continue
            sl_vals = sl_eff[tg_idx]
            ranks = pd.Series(sl_vals).rank(method="average", pct=True).values * 100.0
            farm_pct[tg_idx] = ranks
    
    fp = farm_pct / 100.0
    fp = fp.clip(1e-6, 1.0 - 1e-6)
    logit = np.log(fp / (1.0 - fp))
    scale = 0.6
    sig = 1.0 / (1.0 + np.exp(-scale * logit))
    df["FARM_SCORE"] = (sig * 100.0).clip(0.0, 100.0)
    
    # Drop temporary columns
    drop_cols = [
        c for c in df.columns
        if (c.startswith("_") or c.startswith("z_")) and c != "Net SL за игру"
    ]
    df = df.drop(columns=drop_cols, errors="ignore")
    
    return df
