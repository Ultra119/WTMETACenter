from typing import NamedTuple

TYPE_CATEGORIES: dict = {
    "Ground": [
        "medium_tank", "light_tank", "heavy_tank",
        "tank_destroyer", "spaa",
    ],
    "Aviation": [
        "fighter", "bomber", "assault",
        "utility_helicopter", "attack_helicopter",
    ],
    "LargeFleet": [
        "destroyer", "heavy_cruiser", "light_cruiser",
        "battleship", "battlecruiser",
    ],
    "SmallFleet": [
        "boat", "heavy_boat", "frigate", "barge",
    ],
}

_FOLDER_KEYWORDS: list = [

    ("tank",       "Ground"),
    ("ground",     "Ground"),
    ("spaa",       "Ground"),
    ("armored",    "Ground"),
    ("nazemka",    "Ground"),

    ("aviation",   "Aviation"),
    ("air",        "Aviation"),
    ("plane",      "Aviation"),
    ("heli",       "Aviation"),
    ("fighter",    "Aviation"),
    ("bomber",     "Aviation"),
    ("aviacia",    "Aviation"),

    ("large",      "LargeFleet"),
    ("cruiser",    "LargeFleet"),
    ("destroyer",  "LargeFleet"),
    ("battleship", "LargeFleet"),
    ("naval",      "LargeFleet"),
    ("fleet",      "LargeFleet"),

    ("small",      "SmallFleet"),
    ("boat",       "SmallFleet"),
    ("barge",      "SmallFleet"),
    ("frigate",    "SmallFleet"),
]


def folder_to_category(folder: str) -> str | None:
    low = folder.lower()
    for kw, cat in _FOLDER_KEYWORDS:
        if kw in low:
            return cat
    return None


class TypeFilterData(NamedTuple):
    type_to_cat:   dict
    ui_type_cats:  dict
    farm_type_opts: list 


def build_type_filter_data(all_types: list) -> TypeFilterData:
    type_to_cat: dict = {
        t: cat
        for cat, types in TYPE_CATEGORIES.items()
        for t in types
    }

    ui_cats = {
        "Ground": [
            t for t in all_types
            if type_to_cat.get(t) == "Ground" or folder_to_category(t) == "Ground"
        ],
        "Aviation": [
            t for t in all_types
            if type_to_cat.get(t) == "Aviation" or folder_to_category(t) == "Aviation"
        ],
        "Small Fleet": [
            t for t in all_types
            if type_to_cat.get(t) == "SmallFleet" or folder_to_category(t) == "SmallFleet"
        ],
        "Large Fleet": [
            t for t in all_types
            if type_to_cat.get(t) == "LargeFleet" or folder_to_category(t) == "LargeFleet"
        ],
    }
    ui_cats["_unknown"] = [
        t for t in all_types
        if not type_to_cat.get(t) and not folder_to_category(t)
    ]

    ui_type_cats   = {k: v for k, v in ui_cats.items() if v}
    farm_type_opts = ["All"] + [k for k in ui_type_cats if not k.startswith("_")]

    return TypeFilterData(
        type_to_cat=type_to_cat,
        ui_type_cats=ui_type_cats,
        farm_type_opts=farm_type_opts,
    )


def get_types_from_checkboxes(
    ground:      bool,
    aviation:    bool,
    large_fleet: bool,
    small_fleet: bool,
    all_types:   list,
    type_to_cat: dict,
) -> list:
    wanted: set = set()
    if ground:      wanted.add("Ground")
    if aviation:    wanted.add("Aviation")
    if large_fleet: wanted.add("LargeFleet")
    if small_fleet: wanted.add("SmallFleet")

    if not wanted:
        return []

    result: set = set()
    for t in all_types:
        cat = type_to_cat.get(t)
        if cat and cat in wanted:
            result.add(t)
            continue
        cat_fuzzy = folder_to_category(t)
        if cat_fuzzy and cat_fuzzy in wanted:
            result.add(t)
            continue
        if not cat and not cat_fuzzy:
            result.add(t)

    return list(result)
