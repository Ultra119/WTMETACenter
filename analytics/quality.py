from __future__ import annotations

from analytics.units_csv import _BADGE_CHARS


class Checks:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


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

    missing_br = sum(1 for r in records if r.get("BR") is None)
    if missing_br:
        checks.fail(f"{period}: {missing_br} rows without BR")

    below_gate = sum(1 for r in records if (r.get("Сыграно игр") or 0) < 1)
    if below_gate:
        checks.fail(f"{period}: {below_gate} rows with no battles")

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
) -> Checks:
    checks = Checks()

    check_vehicles(checks, vehicles)

    for period, records in period_records.items():
        check_records(checks, period, records)

    if "All" in period_records:
        check_tree(checks, period_records["All"], shop_loaded)

    return checks


def report(checks: Checks) -> None:
    for message in checks.warnings:
        print(f"   ⚠️   DQ: {message}")
    for message in checks.failures:
        print(f"   ❌  DQ: {message}")
