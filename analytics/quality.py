from __future__ import annotations

import json
import os

from analytics.units_csv import _BADGE_CHARS


class Checks:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def check_periods(checks: Checks, invalid: list[str]) -> None:
    for name in sorted(set(invalid)):
        checks.fail(f"unrecognised period directory: {name!r}")


def check_vehicles(checks: Checks, vehicles: list[dict]) -> None:
    if not vehicles:
        checks.fail("vehicles.json is empty")
        return

    without_id = sum(1 for v in vehicles if not v.get("identifier"))
    if without_id:
        checks.fail(f"{without_id} vehicles have no identifier")

    without_br = sum(
        1 for v in vehicles
        if not v.get("realistic_br") and not v.get("arcade_br") and not v.get("simulator_br")
    )
    if without_br > len(vehicles) * 0.10:
        checks.fail(f"{without_br} of {len(vehicles)} vehicles have no BR")


def check_records(checks: Checks, period: str, records: list[dict]) -> None:
    if not records:
        checks.fail(f"{period}: no records")
        return

    missing_meta = sum(1 for r in records if r.get("META_SCORE") is None)
    if missing_meta:
        checks.fail(f"{period}: {missing_meta} rows without META_SCORE")

    out_of_range = sum(
        1 for r in records
        if r.get("META_SCORE") is not None and not 0.0 <= r["META_SCORE"] <= 100.0
    )
    if out_of_range:
        checks.fail(f"{period}: {out_of_range} rows with META_SCORE outside 0-100")

    without_id = sum(1 for r in records if not r.get("vdb_identifier"))
    if without_id:
        checks.fail(f"{period}: {without_id} rows without vdb_identifier")

    missing_br = sum(1 for r in records if r.get("BR") is None)
    if missing_br:
        checks.fail(f"{period}: {missing_br} rows without BR")

    below_gate = sum(1 for r in records if (r.get("Сыграно игр") or 0) < 1)
    if below_gate:
        checks.fail(f"{period}: {below_gate} rows with no battles")

    bad_ci = 0
    for r in records:
        lo, hi, wr = r.get("WR_CI_LOW"), r.get("WR_CI_HIGH"), r.get("WR")
        if lo is None or hi is None or wr is None:
            bad_ci += 1
            continue
        if not (lo <= hi) or not (lo <= wr <= hi):
            bad_ci += 1
    if bad_ci:
        checks.fail(f"{period}: {bad_ci} rows with a WR interval that excludes WR")

    low_sample = sum(1 for r in records if (r.get("Сыграно игр") or 0) < 250)
    if low_sample and low_sample / len(records) > 0.75:
        checks.fail(
            f"{period}: {low_sample / len(records):.0%} of rows have under 250 battles"
        )

    glyphs = sum(
        1 for r in records
        if any(ch in _BADGE_CHARS for ch in (r.get("Name") or ""))
    )
    if glyphs:
        share = glyphs / len(records)
        message = f"{period}: {glyphs} names carry badge glyphs ({share:.1%})"
        if share > 0.01:
            checks.fail(message)
        else:
            checks.warn(message)

    seen: set[tuple] = set()
    duplicates = 0
    for r in records:
        key = (
            r.get("vdb_identifier") or r.get("Name"),
            r.get("Mode"),
            r.get("Nation"),
            r.get("Type"),
            r.get("BR"),
        )
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    if duplicates:
        checks.fail(f"{period}: {duplicates} duplicate vehicle rows")


def check_tree(checks: Checks, records: list[dict], shop_loaded: bool) -> None:
    standard = [r for r in records if (r.get("VehicleClass") or "Standard") == "Standard"]
    if not standard:
        checks.warn("no Standard rows in the dataset")
        return

    ranked = sum(1 for r in standard if (r.get("vdb_shop_rank") or 0) > 0)
    if ranked == 0:
        if shop_loaded:
            checks.fail("shop.blkx loaded but no Standard row has a shop rank")
        else:
            checks.warn("shop.blkx missing - tech tree order unavailable")
        return

    share = ranked / len(standard)
    if share < 0.80:
        checks.fail(f"only {share:.1%} of Standard rows have a shop rank")


def evaluate(
    vehicles: list[dict],
    period_records: dict[str, list[dict]],
    shop_loaded: bool,
    invalid_periods: list[str] | None = None,
) -> Checks:
    checks = Checks()

    check_periods(checks, invalid_periods or [])
    check_vehicles(checks, vehicles)

    for period, records in period_records.items():
        check_records(checks, period, records)

    if "All" in period_records:
        check_tree(checks, period_records["All"], shop_loaded)

    return checks


def check_export(checks: Checks, data_dir: str, expected: dict[str, int]) -> None:
    index_path = os.path.join(data_dir, "index.json")
    try:
        with open(index_path, encoding="utf-8") as f:
            index = json.load(f)
    except (OSError, ValueError) as e:
        checks.fail(f"index.json unreadable: {e}")
        return

    vehicles_path = os.path.join(data_dir, "vehicles.json")
    try:
        with open(vehicles_path, encoding="utf-8") as f:
            vehicles = json.load(f)
    except (OSError, ValueError) as e:
        checks.fail(f"vehicles.json unreadable: {e}")
        return

    if not vehicles:
        checks.fail("vehicles.json is empty")
        return

    if index.get("vehicles") != len(vehicles):
        checks.fail(
            f"index.json claims {index.get('vehicles')} vehicles, "
            f"vehicles.json holds {len(vehicles)}"
        )

    columns = index.get("row_columns") or []
    if "vdb_identifier" in columns:
        checks.fail("vdb_identifier must not be a row column")

    for period, expected_rows in expected.items():
        entry = (index.get("periods") or {}).get(period)
        if not entry:
            checks.fail(f"index.json is missing period {period}")
            continue

        seen = 0
        for mode, count in (entry.get("modes") or {}).items():
            path = os.path.join(data_dir, "stats", period, f"{mode}.json")
            try:
                with open(path, encoding="utf-8") as f:
                    blob = json.load(f)
            except (OSError, ValueError) as e:
                checks.fail(f"stats/{period}/{mode}.json unreadable: {e}")
                continue

            ids = blob.get("identifier") or []
            rows = blob.get("rows") or []
            if len(ids) != len(rows):
                checks.fail(
                    f"stats/{period}/{mode}.json: {len(ids)} identifiers "
                    f"for {len(rows)} rows"
                )
            if blob.get("columns") != columns:
                checks.fail(f"stats/{period}/{mode}.json: column list differs from index")
            for i, identifier in enumerate(ids):
                if not identifier:
                    checks.fail(f"stats/{period}/{mode}.json: row {i} has no identifier")
                    break
                if identifier not in vehicles:
                    checks.fail(
                        f"stats/{period}/{mode}.json: {identifier!r} is not in vehicles.json"
                    )
                    break
            seen += len(rows)

        if seen != entry.get("vehicles"):
            checks.fail(
                f"{period}: index claims {entry.get('vehicles')} vehicles, "
                f"files hold {seen}"
            )
        if seen != expected_rows:
            checks.fail(
                f"{period}: files hold {seen} rows, the build produced {expected_rows}"
            )


def report(checks: Checks) -> None:
    for message in checks.warnings:
        print(f"   ⚠️   DQ: {message}")
    for message in checks.failures:
        print(f"   ❌  DQ: {message}")
