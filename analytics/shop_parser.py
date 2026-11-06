from __future__ import annotations

import json
import os

from analytics.datamine import fetch

SHOP_FILENAME: str = "shop.blkx"
SHOP_PATH: str     = "char.vromfs.bin_u/config/shop.blkx"

_META_KEYS = frozenset({
    "image", "reqAir", "futureReqAir", "slaveUnit",
    "marketplaceItemdefId", "isClanVehicle",
    "reqFeature", "showByPlatform",
    "beginPurchaseDate", "endPurchaseDate",
    "isCrossPromo", "crossPromoBanner", "hideFeature", "event",
})

_VAL_FLAGS = frozenset({"showOnlyWhenBought", "showOnlyWhenResearch"})

# wide enough that a column's row index can never spill into the next column
_ORDER_STRIDE = 1_000_000


def _try_download(dest: str) -> None:
    fetch(dest, SHOP_PATH, "ShopParser")


def _iter_column(col_dict: dict):
    row = 0
    for key, val in col_dict.items():
        if key in _META_KEYS or not isinstance(val, dict):
            continue

        if val.get("isClanVehicle", False):
            continue

        is_event    = bool(val.get("showOnlyWhenBought",   False))
        is_research = bool(val.get("showOnlyWhenResearch", False))
        is_gift     = bool(val.get("gift", ""))

        nested = [
            (k, v) for k, v in val.items()
            if k not in _META_KEYS and k not in _VAL_FLAGS and isinstance(v, dict) and "rank" in v
        ]

        if nested:
            for sub_key, sub_val in nested:
                # fold in the parent flags too, otherwise a gift that lives in a
                # nested slot loses the marker its parent carried
                sub_is_gift     = is_gift or bool(sub_val.get("gift", ""))
                sub_is_event    = is_event    or bool(sub_val.get("showOnlyWhenBought",   False))
                sub_is_research = is_research or bool(sub_val.get("showOnlyWhenResearch", False))
                yield sub_key, int(sub_val.get("rank", 0) or 0), key, row, sub_is_gift, sub_is_event, sub_is_research
                row += 1
        elif "rank" in val:
            yield key, int(val.get("rank", 0) or 0), "", row, is_gift, is_event, is_research
            row += 1


def parse_shop_file(path: str) -> dict[str, dict]:
    if not os.path.exists(path):
        _try_download(path)

    if not os.path.exists(path):
        print("[ShopParser] ⚠️  shop.blkx is unavailable — tree order is disabled")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ShopParser] ❌ Error reading shop.blkx: {e}")
        return {}

    result: dict[str, dict] = {}

    for nation_key, nation_data in data.items():
        if not isinstance(nation_data, dict):
            continue
        nation = nation_key.replace("country_", "")

        for branch, branch_data in nation_data.items():
            if not isinstance(branch_data, dict):
                continue
            columns = branch_data.get("range", [])
            if not isinstance(columns, list):
                continue

            for col_idx, col_dict in enumerate(columns):
                if not isinstance(col_dict, dict):
                    continue
                for vid, rank, group, row_idx, is_gift, is_event, is_research in _iter_column(col_dict):
                    result[vid] = {
                        "shop_column":          col_idx,
                        "shop_row":             row_idx,
                        "shop_rank":            rank,
                        "shop_group":           group,
                        "shop_nation":          nation,
                        "shop_branch":          branch,
                        "shop_order":           col_idx * _ORDER_STRIDE + row_idx,
                        "shop_is_gift":         is_gift,
                        "shop_is_event":        is_event,
                        "shop_is_research_only": is_research,
                    }

    print(f"[ShopParser] ✅ {len(result)} items from shop.blkx have been parsed")
    return result
