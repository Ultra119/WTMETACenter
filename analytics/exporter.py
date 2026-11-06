from __future__ import annotations

import json
import os

MODES: tuple[str, ...] = ("Realistic", "Arcade", "Simulator")

_SHARED_STAT_COLS: tuple[str, ...] = ("Nation", "Type", "VehicleClass")


def _dump(path: str, payload) -> int:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    return os.path.getsize(path)


def shared_columns(records: list[dict]) -> list[str]:
    return [c for c in records[0] if c.startswith("vdb_")] + list(_SHARED_STAT_COLS)


def row_columns(records: list[dict]) -> list[str]:
    shared = set(shared_columns(records))
    return [c for c in records[0] if c not in shared]


def build_vehicles(period_records: dict[str, list[dict]]) -> dict[str, dict]:
    columns = shared_columns(next(iter(period_records.values())))
    vehicles: dict[str, dict] = {}
    for records in period_records.values():
        for r in records:
            identifier = r.get("vdb_identifier")
            if identifier and identifier not in vehicles:
                vehicles[identifier] = {
                    c: r.get(c) for c in columns if r.get(c) is not None
                }
    return vehicles


def build_stats(records: list[dict], columns: list[str]) -> dict:
    return {
        "columns": columns,
        "identifier": [r.get("vdb_identifier") for r in records],
        "rows": [[r.get(c) for c in columns] for r in records],
    }


def _clear_previous(data_dir: str) -> None:
    if os.path.isdir(data_dir):
        for name in os.listdir(data_dir):
            if name.startswith("mega_db_"):
                os.remove(os.path.join(data_dir, name))


def _clear_stats(stats_dir: str) -> None:
    if not os.path.isdir(stats_dir):
        return
    for root, _dirs, files in os.walk(stats_dir, topdown=False):
        for fname in files:
            if fname.endswith(".json"):
                os.remove(os.path.join(root, fname))
        if root != stats_dir and not os.listdir(root):
            os.rmdir(root)


def write_dataset(data_dir: str, period_records: dict[str, list[dict]]) -> dict:
    stats_dir = os.path.join(data_dir, "stats")

    _clear_previous(data_dir)
    _clear_stats(stats_dir)

    vehicles = build_vehicles(period_records)
    written = _dump(os.path.join(data_dir, "vehicles.json"), vehicles)

    columns = row_columns(next(iter(period_records.values())))
    index_periods: dict[str, dict] = {}

    for period, records in period_records.items():
        by_mode: dict[str, list[dict]] = {m: [] for m in MODES}
        for r in records:
            by_mode.setdefault(r.get("Mode"), []).append(r)

        modes: dict[str, int] = {}
        for mode, subset in by_mode.items():
            if not subset:
                continue
            path = os.path.join(stats_dir, period, f"{mode}.json")
            written += _dump(path, build_stats(subset, columns))
            modes[mode] = len(subset)

        index_periods[period] = {
            "modes": modes,
            "vehicles": sum(modes.values()),
        }

    index = {
        "row_columns": columns,
        "shared_columns": shared_columns(next(iter(period_records.values()))),
        "vehicles": len(vehicles),
        "periods": index_periods,
    }
    written += _dump(os.path.join(data_dir, "index.json"), index)

    return {
        "vehicles": len(vehicles),
        "periods": index_periods,
        "bytes": written,
    }
