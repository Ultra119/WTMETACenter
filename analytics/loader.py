import json
import os
import re

import pandas as pd

from logger import log_debug
from analytics.constants import VEHICLE_TYPE_CATEGORY, snap_to_wt_br
from analytics.units_csv import _strip_badge_prefix

_PERIOD_RE = re.compile(r'^(0[1-9]|1[0-2])-\d{4}$')
_PERIOD_ALIASES = frozenset({"all"})

invalid_periods: list[str] = []


_NA_TOKENS = {"n/a", "none", "nan", "null", "-", ""}


def _to_number(series: pd.Series, scale: float = 1.0) -> pd.Series:
    # Fast path: convert to string vectorized
    s = series.astype(str)
    s = s.where(~series.isna(), "")
    s = s.str.strip().str.replace(",", "", regex=False).str.replace("%", "", regex=False)
    s = s.str.replace(" ", "", regex=False)
    s = s.where(~s.str.lower().isin(_NA_TOKENS), other=pd.NA)
    out = pd.to_numeric(s, errors="coerce").fillna(0).astype(float) * scale
    if (out == out.round()).all():
        return out.round().astype("int64")
    return out


def _period_from_dir(first_sub: str) -> str:
    if not first_sub:
        return "All"
    if _PERIOD_RE.match(first_sub):
        return first_sub
    if first_sub.lower() in _PERIOD_ALIASES:
        return "All"
    invalid_periods.append(first_sub)
    log_debug(f"Skipping directory with an unrecognised period name: {first_sub!r}")
    return ""


def load_json_files(script_dir: str) -> list:
    log_debug("=== STARTING WT META CENTER ===")

    all_data: list = []
    skip_files = {"settings.json", "vehicles.json"}
    invalid_periods.clear()

    for root, _dirs, files in os.walk(script_dir):
        for filename in files:
            if not filename.endswith(".json") or filename in skip_files:
                continue

            rel_path  = os.path.relpath(root, script_dir)
            first_sub = rel_path.split(os.sep)[0] if rel_path != "." else ""

            dir_category = first_sub if first_sub else "Uncategorized"

            period = _period_from_dir(first_sub)
            if not period:
                continue

            name_parts = filename.replace(".json", "").split("_")
            nation = name_parts[0] if name_parts else "Unknown"
            _raw_mode = name_parts[1] if len(name_parts) > 1 else "Unknown"
            _MODE_NORM = {
                "rb": "Realistic", "realistic": "Realistic",
                "ab": "Arcade",    "arcade":    "Arcade",
                "sim": "Simulator","sb":        "Simulator", "simulator": "Simulator",
            }
            mode = _MODE_NORM.get(_raw_mode.lower(), _raw_mode.capitalize())

            try:
                with open(os.path.join(root, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data:
                    entry["_dir_category"] = dir_category
                    entry["Nation"]        = nation
                    entry["Mode"]          = mode
                    entry["Period"]        = period
                all_data.extend(data)
            except Exception as e:
                log_debug(f"File error {filename}: {e}")

    return all_data


def extract_br(raw: str) -> float:
    s = str(raw)
    if "БР" in s:
        try:
            parts = s.split()
            idx   = parts.index("БР")
            if idx + 1 < len(parts):
                return float(parts[idx + 1])
        except Exception:
            pass
    match = re.search(r"\b(\d+\.\d+)\b", s)
    return float(match.group(1)) if match else float("nan")


def clean_dataframe(df: pd.DataFrame, vehicle_db) -> pd.DataFrame:
    if "vehicle_type" in df.columns:
        vt = df["vehicle_type"].astype(str).str.strip()
        vt = vt.replace({"nan": "", "None": "", "none": ""})
        fallback = df["_dir_category"] if "_dir_category" in df.columns else "Uncategorized"
        df["Type"] = vt.where(vt != "", fallback)
    else:
        df["Type"] = df["_dir_category"] if "_dir_category" in df.columns else "Uncategorized"

    if "Name" in df.columns:
        df["Name"] = df["Name"].astype(str)
    else:
        df["Name"] = ""

    if "vdb_display_name" in df.columns:
        display = df["vdb_display_name"].fillna("").astype(str)
        df["Name"] = display.where(display.str.len() > 0, df["Name"])

    df["Name"] = df["Name"].map(_strip_badge_prefix)

    df["Category"] = df["Type"].map(VEHICLE_TYPE_CATEGORY).fillna("Uncategorized")

    if "vehicle_sub_types" in df.columns:
        df["vehicle_sub_types"] = df["vehicle_sub_types"].apply(_parse_json_list)
    else:
        df["vehicle_sub_types"] = [[] for _ in range(len(df))]

    for col in ("value", "train1_cost", "train2_cost",
                "train3_cost_exp", "train3_cost_gold"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        else:
            df[col] = 0

    if "visibility" in df.columns:
        df["visibility"] = pd.to_numeric(df["visibility"], errors="coerce").fillna(0)
    else:
        df["visibility"] = 0

    if "version" not in df.columns:
        df["version"] = ""
    else:
        df["version"] = df["version"].fillna("").astype(str)

    if "thermal_devices" in df.columns:
        df["thermal_devices"] = df["thermal_devices"].apply(_parse_json_dict)
    else:
        df["thermal_devices"] = [{} for _ in range(len(df))]

    if "turret_armor" in df.columns:
        df["turret_armor"] = df["turret_armor"].apply(_parse_json_list)
    else:
        df["turret_armor"] = [[] for _ in range(len(df))]

    if "weapons" in df.columns:
        df["weapons"] = df["weapons"].apply(_parse_json_list)
        df["weapons_count"] = df["weapons"].apply(
            lambda ws: sum(w.get("count", 1) for w in ws)
        )
        df["weapon_types"] = df["weapons"].apply(
            lambda ws: list({w.get("weapon_type", "unknown") for w in ws})
        )
    else:
        df["weapons"]       = [[] for _ in range(len(df))]
        df["weapons_count"] = 0
        df["weapon_types"]  = [[] for _ in range(len(df))]

    int_cols = [
        "Сыграно игр", "Победы", "Возрождения", "Смерти",
        "Наземные убийства", "Воздушные убийства", "Морские убийства",
        "Убийств за возрождение",
    ]

    if "Морские убийства" not in df.columns:
        df["Морские убийства"] = 0
    for col in int_cols:
        if col in df.columns:
            df[col] = _to_number(df[col])

    for col in ("SL за игру", "RP за игру"):
        df[col] = _to_number(df[col]) if col in df.columns else 0.0

    df["KD"] = _to_number(df["Убийств за смерть"].str.replace(",", ".", regex=False)) \
        if "Убийств за смерть" in df.columns else 0.0

    df["WR"] = _to_number(df["Процент побед"]) if "Процент побед" in df.columns else 0.0

    raw_br = (
        df["Rank_Info"].apply(extract_br)
        if "Rank_Info" in df.columns
        else pd.Series(float("nan"), index=df.index)
    )

    # Vectorized BR snapping using numpy searchsorted
    import numpy as np
    from analytics.constants import WT_BR_STEPS
    _br_steps = np.array(WT_BR_STEPS, dtype=float)
    br_vals = raw_br.values.astype(float)
    valid = ~np.isnan(br_vals)
    result = np.full(len(br_vals), np.nan)
    if valid.any():
        v = br_vals[valid]
        idx = np.searchsorted(_br_steps, v, side='left')
        idx = np.clip(idx, 1, len(_br_steps) - 1)
        up = _br_steps[idx]
        down = _br_steps[idx - 1]
        snapped = np.where((up - v) <= (v - down), up, down)
        # Handle edge cases: below first step or above last step
        snapped = np.where(v <= _br_steps[0], _br_steps[0], snapped)
        snapped = np.where(v >= _br_steps[-1], _br_steps[-1], snapped)
        result[valid] = snapped
    df["BR"] = result

    invalid_br = df["BR"].isna()
    if invalid_br.any():
        log_debug(
            f"Skipped {int(invalid_br.sum())} records without valid br"
            f"(examples Name: {df.loc[invalid_br, 'Name'].head(5).tolist()})"
        )
        df = df[~invalid_br].reset_index(drop=True)

    df.drop(columns=["_dir_category"], errors="ignore", inplace=True)

    if vehicle_db is not None and vehicle_db.loaded:
        df = vehicle_db.enrich_dataframe(df)
        df = df.copy()

        matched = int((df.get("vdb_match_score", 0) > 0).sum())
        log_debug(
            f"[VehicleDB] vdb_ match completed. "
            f"Compared: {matched}/{len(df)}"
        )

        if "vdb_vehicle_type" in df.columns:
            good_match = df.get("vdb_match_score", pd.Series(0.0, index=df.index)) > 0
            vdb_vt = df["vdb_vehicle_type"].astype(str).str.strip()
            valid  = good_match & vdb_vt.isin(["", "nan"]).eq(False)
            df.loc[valid, "Type"] = df.loc[valid, "vdb_vehicle_type"]
            log_debug(
                f"[VehicleDB] Type updated by {int(valid.sum())} strings "
                f"from {len(df)} (через vdb_vehicle_type)"
            )

    _KNOWN_TYPES = set(VEHICLE_TYPE_CATEGORY.keys())
    invalid_type = ~df["Type"].isin(_KNOWN_TYPES)
    if invalid_type.any():
        bad_values = df.loc[invalid_type, "Type"].unique().tolist()
        log_debug(
            f"[loader] {int(invalid_type.sum())} records with unknown Type "
            f"(set to Uncategorized): {bad_values[:10]}"
        )
        df.loc[invalid_type, "Type"] = "Uncategorized"

    def _derive_class(row) -> str:
        if int(row.get("vdb_is_pack",          0) or 0): return "Pack"
        if int(row.get("vdb_on_marketplace",   0) or 0): return "Marketplace"
        if int(row.get("vdb_squadron_vehicle", 0) or 0): return "Squadron"
        if     row.get("vdb_shop_is_event", False):      return "Event"
        if     row.get("vdb_shop_is_gift",  False):      return "Gift"
        if int(row.get("vdb_is_premium",       0) or 0): return "Premium"
        return "Standard"

    _vdb_flag_cols = [
        "vdb_is_premium", "vdb_is_pack", "vdb_squadron_vehicle",
        "vdb_on_marketplace", "vdb_shop_is_gift", "vdb_shop_is_event",
    ]
    if all(c in df.columns for c in _vdb_flag_cols):
        # Vectorized VehicleClass derivation (replaces slow df.apply)
        import numpy as np
        n = len(df)
        vc = np.full(n, "Standard", dtype=object)
        
        is_prem = df["vdb_is_premium"].fillna(0).astype(int).values > 0
        is_gift = df["vdb_shop_is_gift"].fillna(False).astype(bool).values
        is_event = df["vdb_shop_is_event"].fillna(False).astype(bool).values
        is_sq = df["vdb_squadron_vehicle"].fillna(0).astype(int).values > 0
        is_mp = df["vdb_on_marketplace"].fillna(0).astype(int).values > 0
        is_pack = df["vdb_is_pack"].fillna(0).astype(int).values > 0
        
        # Apply in priority order (later assignments override earlier)
        vc[is_prem] = "Premium"
        vc[is_gift] = "Gift"
        vc[is_event] = "Event"
        vc[is_sq] = "Squadron"
        vc[is_mp] = "Marketplace"
        vc[is_pack] = "Pack"
        
        df["VehicleClass"] = vc
    else:
        df["VehicleClass"] = "Standard"

    return df


def _parse_json_list(raw) -> list:
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(str(raw)) if raw not in (None, "", "[]") else []
    except Exception:
        return []


def _parse_json_dict(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(str(raw)) if raw not in (None, "", "{}") else {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}
