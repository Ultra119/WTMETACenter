from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd

PROJECT_DIR  = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PUB = os.path.join(PROJECT_DIR, "frontend", "public")
DATA_DIR     = os.path.join(FRONTEND_PUB, "data")
OUT_META     = os.path.join(FRONTEND_PUB, "meta_info.json")

os.makedirs(DATA_DIR, exist_ok=True)

sys.path.insert(0, os.path.join(PROJECT_DIR, "analytics"))
sys.path.insert(0, PROJECT_DIR)

from analytics.core      import AnalyticsCore
from analytics.exporter  import write_dataset
from analytics.loader    import invalid_periods
from analytics.quality  import Checks, check_export, evaluate, report as report_quality
from analytics.constants import WT_BR_STEPS

_KEEP_COLS = [
    "Name", "Nation", "BR", "Type", "Mode", "VehicleClass",
    "Сыграно игр", "WR", "KD", "KD_GROUND", "KD_AIR", "KD_NAVAL",
    "SL за игру", "RP за игру", "Net SL за игру",
    "META_SCORE", "FARM_SCORE",
    "vdb_hull_front",  "vdb_hull_side",  "vdb_hull_rear",
    "vdb_turret_front","vdb_turret_side","vdb_turret_rear",
    "vdb_engine_hp_rb",     "vdb_engine_hp_ab",
    "vdb_engine_max_speed_rb","vdb_engine_max_speed_ab",
    "vdb_engine_reverse_rb",
    "vdb_main_caliber_mm","vdb_main_gun_speed",
    "vdb_has_thermal","vdb_has_atgm","vdb_has_heat","vdb_has_aphe",
    "vdb_ammo_types",
    "vdb_is_premium","vdb_is_pack","vdb_squadron_vehicle",
    "vdb_on_marketplace","vdb_shop_is_gift","vdb_shop_is_event","vdb_shop_is_research_only",
    "vdb_shop_rank","vdb_era","vdb_country","vdb_identifier",
    "vdb_arcade_br","vdb_realistic_br","vdb_simulator_br",
    "vdb_repair_cost_realistic","vdb_repair_cost_arcade","vdb_repair_cost_simulator",
    "vdb_ge_cost","vdb_exp_mul","vdb_sl_mul_realistic","vdb_sl_mul_arcade",
    "vdb_shop_column","vdb_shop_row","vdb_shop_nation","vdb_shop_branch",
    "vdb_shop_order","vdb_req_exp","vdb_value","vdb_required_vehicle",
    "BR_HISTORY",
    "vdb_shop_group",
    "vdb_crew_total_count","vdb_visibility","vdb_mass",
    "vdb_match_score",
    "vdb_release_date",
]

_ALL_VEHICLE_CLASSES = [
    "Standard","Premium","Pack","Squadron","Marketplace","Gift","Event",
]

_MODES = ["Realistic", "Arcade", "Simulator"]

_WT_NATIONS = {
    "USA","Germany","USSR","Britain","Japan","Italy",
    "France","Sweden","Israel","China",
}

_WT_NATIONS_LOWER = {n.lower() for n in _WT_NATIONS}

MIN_BATTLES = 1

def _load_vehicles_json() -> list[dict]:
    path = os.path.join(PROJECT_DIR, "dataset", "vehicles.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else list(data.values())


def _compute_dataset_hash(stats_dir: str) -> str:
    h = hashlib.sha256()
    for root, dirs, files in os.walk(stats_dir):
        dirs.sort()
        for fname in sorted(files):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, stats_dir).replace(os.sep, "/")
            h.update(rel.encode("utf-8"))
            h.update(b"\0")
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
    return h.hexdigest()


def _safe_val(v):
    import math
    import numpy as np
    if isinstance(v, (np.integer,)):     return int(v)
    if isinstance(v, (np.floating,)):    return None if math.isnan(v) else float(v)
    if isinstance(v, (np.bool_,)):       return bool(v)
    if isinstance(v, float) and math.isnan(v): return None
    return v


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    records = []
    cols = [c for c in _KEEP_COLS if c in df.columns]
    for row in df[cols].itertuples(index=False):
        rec = {}
        for c, v in zip(cols, row):
            if c == "BR_HISTORY":
                continue
            rec[c] = _safe_val(v)
        rec["BR_HISTORY"] = _br_history_of(row, cols)
        records.append(rec)
    return records


def _br_history_of(row, cols) -> dict | None:
    if "BR_HISTORY" not in cols:
        return None
    trail = row[cols.index("BR_HISTORY")]
    if not isinstance(trail, dict) or not trail:
        return None
    ordered = sorted(trail.items(), key=lambda kv: _period_sort_key(kv[0]))
    return {p: br for p, br in ordered}


def _period_sort_key(p: str) -> tuple:
    if p == "All":
        return (0, 0)
    try:
        month, year = p.split("-")
        return (int(year), int(month))
    except ValueError:
        return (0, 0)


def _process_period(
    core: AnalyticsCore,
    period_df: pd.DataFrame,
    period_label: str,
) -> list[dict]:
    original_df  = core.full_df
    core.full_df = period_df
    all_records: list[dict] = []

    try:
        for mode in _MODES:
            has_mode = (
                "Mode" in core.full_df.columns
                and mode in core.full_df["Mode"].values
            )
            if not has_mode:
                print(f"   ⚠️   {mode} not found in the '{period_label}' period — skipped")
                continue

            filters = {
                "type":            "All",
                "mode":            mode,
                "search":          "",
                "nation":          "All",
                "min_br":          float(min(WT_BR_STEPS)),
                "max_br":          float(max(WT_BR_STEPS)),
                "min_battles":     MIN_BATTLES,
                "vehicle_classes": _ALL_VEHICLE_CLASSES,
            }

            df_mode = core.calculate_meta(filters)
            if df_mode.empty:
                print(f"   ℹ️   No data available: {mode} / '{period_label}'")
                continue

            records = _df_to_records(df_mode)
            before = len(records)
            records = [r for r in records if r.get("Type") != "Uncategorized"]
            dropped = before - len(records)
            if dropped:
                print(f"   ⚠️   Dropped {dropped} records with Type=Uncategorized (no VDB match)")

            unmatched = [r for r in records if not r.get("vdb_match_score")]
            if unmatched:
                names = list({r.get("vdb_identifier") or r.get("Name", "?") for r in unmatched})
                print(f"   ⚠️   {len(unmatched)} records without a VDB match (statistics only): {names[:5]}")

            all_records.extend(records)
            print(f"   ✅  {mode}: {len(records)} records")

    finally:
        core.full_df = original_df

    return all_records


def main() -> None:
    t0 = time.perf_counter()
    print("=" * 60)
    print("  WT META Center — Data Pipeline")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    core = AnalyticsCore()
    ok   = core.load_data_recursive()
    if not ok or core.full_df.empty:
        print("❌  Data has not been loaded. Check the dataset/stats/ folder.")
        sys.exit(1)

    stats_dir    = os.path.join(PROJECT_DIR, "dataset", "stats")
    dataset_hash = _compute_dataset_hash(stats_dir)
    print(f"🔑  Dataset hash: {dataset_hash[:16]}…")

    old_generated_at: str | None = None
    if os.path.exists(OUT_META):
        try:
            with open(OUT_META, "r", encoding="utf-8") as f:
                old_meta = json.load(f)
            if old_meta.get("dataset_hash") == dataset_hash:
                old_generated_at = old_meta.get("generated_at")
                print(f"✅  Dataset unchanged — keeping generated_at: {old_generated_at}")
        except Exception:
            pass

    generated_at = old_generated_at or datetime.now(timezone.utc).isoformat()

    print(f"✅  full_df: {len(core.full_df)} strings")

    raw_periods: list[str] = []
    if "Period" in core.full_df.columns:
        raw_periods = [
            p for p in core.full_df["Period"].dropna().unique().tolist()
            if p and p != "All"
        ]

    raw_periods.sort(key=_period_sort_key, reverse=True)
    all_period_labels = ["All"] + raw_periods

    print(f"📅  Periods: {len(raw_periods)}  →  {raw_periods or '(none)'}")

    print("\n▶  Aggregate all periods → All")
    all_df = core.aggregate_all_periods(core.full_df)
    print(f"   ✅  {len(all_df)} unique records (identifier+Mode+Nation+Type+BR)")

    period_dfs: dict[str, pd.DataFrame] = {"All": all_df}
    for p in raw_periods:
        period_dfs[p] = core.full_df[core.full_df["Period"] == p].copy()

    period_record_counts: dict[str, int] = {}
    period_records:      dict[str, list[dict]] = {}

    for period_label in all_period_labels:
        print(f"\n▶  Period: {period_label}")
        period_df = period_dfs.get(period_label, pd.DataFrame())

        if period_df.empty:
            print("   ⚠️   No data — skip")
            continue

        records = _process_period(core, period_df, period_label)

        if not records:
            print("   ⚠️   The list of entries is empty—the file has not been saved")
            continue

        period_record_counts[period_label] = len(records)
        period_records[period_label] = records

    if not period_record_counts:
        print("\n❌  No data was found for any period — nothing was saved")
        sys.exit(1)

    print("\n▶  Data quality gate")
    checks = evaluate(
        vehicles=_load_vehicles_json(),
        period_records=period_records,
        shop_loaded=core.shop_loaded,
        invalid_periods=invalid_periods,
    )
    report_quality(checks)

    if checks.failures:
        print(f"\n❌  DQ gate failed with {len(checks.failures)} error(s) — output was not written")
        sys.exit(1)

    print("   ✅  gate passed")

    export = write_dataset(DATA_DIR, period_records)
    print(
        f"   💾  {export['vehicles']} vehicles · "
        f"{sum(export['periods'][p]['vehicles'] for p in export['periods'])} rows · "
        f"{export['bytes'] / 1_048_576:.2f} MB"
    )

    expected = {p: len(r) for p, r in period_records.items()}
    written_checks = Checks()
    check_export(written_checks, DATA_DIR, expected)
    report_quality(written_checks)
    if written_checks.failures:
        print(
            f"\n❌  Export check failed with {len(written_checks.failures)} error(s)"
        )
        sys.exit(1)

    all_nations_raw = (
        core.full_df["Nation"].dropna().unique().tolist()
        if "Nation" in core.full_df.columns else []
    )
    nations_list = sorted(
        n for n in all_nations_raw
        if n.strip().lower() in _WT_NATIONS_LOWER
    )
    all_types = (
        sorted(core.full_df["Type"].dropna().unique().tolist())
        if "Type" in core.full_df.columns else []
    )

    meta_info = {
        "generated_at":    generated_at,
        "dataset_hash":    dataset_hash,
        "periods":         all_period_labels,
        "nations":         nations_list,
        "types":           all_types,
        "br_steps":        WT_BR_STEPS,
        "modes":           _MODES,
        "vehicle_classes": _ALL_VEHICLE_CLASSES,
        "total_records":   period_record_counts.get("All", 0),
        "period_records":  period_record_counts,
    }

    print(f"\n💾  {OUT_META} …")
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(
        f"   ✅  {len(nations_list)} nations · {len(all_types)} types · "
        f"{len(all_period_labels)} periods"
    )

    elapsed = time.perf_counter() - t0
    print(f"\n✅  Done in {elapsed:.1f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    main()
