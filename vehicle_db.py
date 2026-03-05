from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Optional

import pandas as pd

try:
    from analytics.units_csv import UnitsCsvTranslator as _UnitsCsvTranslator
except ImportError:
    _UnitsCsvTranslator = None

NATION_TO_COUNTRY: dict[str, str] = {
    "usa":         "usa",
    "germany":     "germany",
    "ussr":        "ussr",
    "britain":     "britain",
    "japan":       "japan",
    "italy":       "italy",
    "france":      "france",
    "sweden":      "sweden",
    "israel":      "israel",
    "china":       "china",
    "finland":     "finland",
    "netherlands": "netherlands",
    "hungary":     "hungary",
    "benelux":     "netherlands",
}

_ID_PREFIXES: tuple[str, ...] = (
    "us_", "uk_", "germ_", "ussr_", "jp_",
    "it_", "fr_", "sw_", "cn_", "il_",
    "fi_", "nl_", "hu_",
)

_ROMAN_PAIRS: list[tuple[str, str]] = [
    ("viii", "8"), ("vii",  "7"), ("vi",  "6"),
    ("iv",   "4"), ("ix",   "9"), ("iii", "3"),
    ("ii",   "2"), ("v",    "5"), ("xl",  "40"),
    ("xc",  "90"), ("x",   "10"), ("i",    "1"),
]

FUZZY_THRESHOLD: float = 0.65
FUZZY_WARN_THRESHOLD: float = 0.82

def _roman_to_arabic(s: str) -> str:
    parts = re.split(r"(\d+)", s)
    result = []
    for part in parts:
        if part.isdigit():
            result.append(part)
            continue
        tokens = re.findall(r"[a-z]+|[^a-z]+", part)
        converted = []
        for tok in tokens:
            replaced = tok
            for roman, arabic in _ROMAN_PAIRS:
                if replaced == roman:
                    replaced = arabic
                    break
            converted.append(replaced)
        result.append("".join(converted))
    return "".join(result)


@lru_cache(maxsize=8192)
def normalize_name(raw: str) -> str:
    s = str(raw).lower().strip()

    for pfx in _ID_PREFIXES:
        if s.startswith(pfx):
            s = s[len(pfx):]
            break

    s = re.sub(r"[\-_./()+,]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    s = _roman_to_arabic(s)
    s = re.sub(r"[^a-z0-9]", "", s)

    return s

def _parse_json_field(raw, default):
    if isinstance(raw, (dict, list)):
        return raw
    if not raw or raw in ("{}", "[]", "null", None):
        return default
    try:
        return json.loads(str(raw))
    except Exception:
        return default


def _extract_engine_stats(raw) -> dict:
    eng = _parse_json_field(raw, {})
    return {
        "vdb_engine_hp_ab":        float(eng.get("horse_power_ab",          0) or 0),
        "vdb_engine_hp_rb":        float(eng.get("horse_power_rb_sb",       0) or 0),
        "vdb_engine_max_speed_ab": float(eng.get("max_speed_ab",            0) or 0),
        "vdb_engine_max_speed_rb": float(eng.get("max_speed_rb_sb",         0) or 0),
        "vdb_engine_reverse_ab":   float(eng.get("max_reverse_speed_ab",    0) or 0),
        "vdb_engine_reverse_rb":   float(eng.get("max_reverse_speed_rb_sb", 0) or 0),
        "vdb_engine_max_rpm":      float(eng.get("max_rpm",                 0) or 0),
    }


def _extract_armor(raw) -> tuple[float, float, float]:
    lst = _parse_json_field(raw, [])
    if isinstance(lst, list) and len(lst) >= 3:
        try:
            return float(lst[0]), float(lst[1]), float(lst[2])
        except (ValueError, TypeError):
            pass
    return 0.0, 0.0, 0.0


def _extract_weapon_summary(raw) -> dict:
    weapons = _parse_json_field(raw, [])
    if not isinstance(weapons, list) or not weapons:
        return {
            "vdb_main_caliber_mm": 0.0,
            "vdb_main_gun_speed":  0.0,
            "vdb_ammo_types":      [],
            "vdb_has_atgm":        False,
            "vdb_has_heat":        False,
            "vdb_has_aphe":        False,
        }

    max_caliber = 0.0
    max_speed   = 0.0
    ammo_types: set[str] = set()

    for w in weapons:
        if not isinstance(w, dict):
            continue
        for ammo in w.get("ammos", []):
            if not isinstance(ammo, dict):
                continue
            cal   = float(ammo.get("caliber", 0) or 0) * 1000
            spd   = float(ammo.get("speed",   0) or 0)
            atype = str(ammo.get("type",      "") or "")
            if cal > max_caliber:
                max_caliber = cal
            if spd > max_speed:
                max_speed = spd
            if atype:
                ammo_types.add(atype)

    return {
        "vdb_main_caliber_mm": round(max_caliber, 1),
        "vdb_main_gun_speed":  round(max_speed,   1),
        "vdb_ammo_types":      sorted(ammo_types),
        "vdb_has_atgm":        any("atgm" in t or "guided" in t for t in ammo_types),
        "vdb_has_heat":        any("heat" in t for t in ammo_types),
        "vdb_has_aphe":        any("aphe" in t for t in ammo_types),
    }


def _extract_modifications_summary(raw) -> dict:
    mods = _parse_json_field(raw, [])
    if not isinstance(mods, list):
        return {"vdb_mod_count": 0, "vdb_mod_max_tier": 0, "vdb_mod_classes": []}

    classes: set[str] = set()
    max_tier = 0
    for m in mods:
        if not isinstance(m, dict):
            continue
        cls  = m.get("mod_class", "")
        tier = int(m.get("tier", 0) or 0)
        if cls:
            classes.add(cls)
        if tier > max_tier:
            max_tier = tier

    return {
        "vdb_mod_count":    len(mods),
        "vdb_mod_max_tier": max_tier,
        "vdb_mod_classes":  sorted(classes),
    }


def _build_vdb_row(v: dict) -> dict:
    row: dict = {}

    row.update(_extract_engine_stats(v.get("engine")))

    hf, hs, hr = _extract_armor(v.get("hull_armor",   "[]"))
    tf, ts, tr = _extract_armor(v.get("turret_armor", "[]"))
    row.update({
        "vdb_hull_front":   hf, "vdb_hull_side":   hs, "vdb_hull_rear":   hr,
        "vdb_turret_front": tf, "vdb_turret_side": ts, "vdb_turret_rear": tr,
    })

    row.update(_extract_weapon_summary(v.get("weapons")))
    row.update(_extract_modifications_summary(v.get("modifications")))

    thermal = _parse_json_field(v.get("thermal_devices"), {})
    row["vdb_has_thermal"] = isinstance(thermal, dict) and len(thermal) > 0

    _NUM_FIELDS: list[tuple[str, type, object]] = [
        ("arcade_br",                           float, 0.0),
        ("realistic_br",                        float, 0.0),
        ("simulator_br",                        float, 0.0),
        ("realistic_ground_br",                 float, 0.0),
        ("simulator_ground_br",                 float, 0.0),
        ("era",                                 int,   0  ),
        ("exp_mul",                             float, 1.0),
        ("ge_cost",                             int,   0  ),
        ("is_premium",                          int,   0  ),
        ("is_pack",                             int,   0  ),
        ("squadron_vehicle",                    int,   0  ),
        ("on_marketplace",                      int,   0  ),
        ("has_customizable_weapons",            int,   0  ),
        ("mass",                                float, 0.0),
        ("crew_total_count",                    int,   0  ),
        ("visibility",                          float, 0.0),
        ("req_exp",                             int,   0  ),
        ("value",                               int,   0  ),
        ("train1_cost",                         int,   0  ),
        ("train2_cost",                         int,   0  ),
        ("train3_cost_exp",                     int,   0  ),
        ("train3_cost_gold",                    int,   0  ),
        ("repair_cost_arcade",                  int,   0  ),
        ("repair_cost_realistic",               int,   0  ),
        ("repair_cost_simulator",               int,   0  ),
        ("repair_cost_full_upgraded_arcade",    int,   0  ),
        ("repair_cost_full_upgraded_realistic", int,   0  ),
        ("repair_cost_full_upgraded_simulator", int,   0  ),
        ("repair_cost_per_min_arcade",          int,   0  ),
        ("repair_cost_per_min_realistic",       int,   0  ),
        ("repair_cost_per_min_simulator",       int,   0  ),
        ("repair_time_arcade",                  float, 0.0),
        ("repair_time_realistic",               float, 0.0),
        ("repair_time_simulator",               float, 0.0),
        ("repair_time_no_crew_arcade",          float, 0.0),
        ("repair_time_no_crew_realistic",       float, 0.0),
        ("repair_time_no_crew_simulator",       float, 0.0),
        ("sl_mul_arcade",                       float, 1.0),
        ("sl_mul_realistic",                    float, 1.0),
        ("sl_mul_simulator",                    float, 1.0),
    ]
    for field, cast, default in _NUM_FIELDS:
        raw_val = v.get(field, default)
        try:
            row[f"vdb_{field}"] = cast(raw_val) if raw_val is not None else default
        except (ValueError, TypeError):
            row[f"vdb_{field}"] = default

    row["vdb_identifier"]       = str(v.get("identifier",       "") or "")
    row["vdb_country"]          = str(v.get("country",          "") or "")
    row["vdb_vehicle_type"]     = str(v.get("vehicle_type",     "") or "")
    row["vdb_release_date"]     = str(v.get("release_date",     "") or "")
    row["vdb_required_vehicle"] = str(v.get("required_vehicle", "") or "")
    row["vdb_version"]          = str(v.get("version",          "") or "")

    return row

class VehicleDB:
    def __init__(self, vehicles_json_path: str) -> None:
        self._index:        dict[tuple[str, str], dict]              = {}
        self._by_country:   dict[str, list[tuple[str, str]]]         = {}
        self._by_country_br: dict[tuple[str, float], list[tuple[str, str]]] = {}
        self._units = None

        self._load(vehicles_json_path)

    _FUZZY_LOG_FILE: str = "fuzzy_matches.log"

    def _load(self, path: str) -> None:
        dataset_dir = os.path.dirname(os.path.abspath(path)) if path else ""
        if _UnitsCsvTranslator is not None:
            self._units = _UnitsCsvTranslator(dataset_dir)
        else:
            self._units = None

        aliases_path = os.path.join(os.path.dirname(path), "aliases.json")
        self._aliases: dict[tuple[str, str], str] = {}
        if os.path.exists(aliases_path):
            try:
                with open(aliases_path, "r", encoding="utf-8") as _af:
                    raw_aliases: dict = json.load(_af)
                for akey, identifier in raw_aliases.items():
                    parts   = akey.split("/", 1)
                    acountry = parts[0].strip().lower() if len(parts) == 2 else ""
                    aname    = parts[-1].strip()
                    self._aliases[(normalize_name(aname), acountry)] = identifier
                print(f"[VehicleDB] 📖 Загружено {len(self._aliases)} алиасов из aliases.json")
            except Exception as _ae:
                print(f"[VehicleDB] ⚠️  Ошибка чтения aliases.json: {_ae}")

        if not os.path.exists(path):
            print(f"[VehicleDB] ⚠️  vehicles.json не найден: {path}")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[VehicleDB] ❌ Ошибка чтения vehicles.json: {e}")
            return

        if isinstance(data, dict):
            data = list(data.values())

        if not isinstance(data, list):
            print("[VehicleDB] ❌ Неожиданный формат vehicles.json (не list/dict)")
            return

        for v in data:
            if not isinstance(v, dict):
                continue
            country    = str(v.get("country", "") or "").lower().strip()
            identifier = str(v.get("identifier", "") or "")
            norm       = normalize_name(identifier)

            vdb_row = _build_vdb_row(v)

            key = (norm, country)
            if key not in self._index:
                self._index[key] = vdb_row
                self._by_country.setdefault(country, []).append(key)
                _br_fields = (
                    "arcade_br", "realistic_br", "simulator_br",
                    "realistic_ground_br", "simulator_ground_br",
                )
                _seen_brs: set[float] = set()
                for _bf in _br_fields:
                    _raw_br = v.get(_bf)
                    if _raw_br and float(_raw_br) > 0:
                        _br_key = round(float(_raw_br), 1)
                        if _br_key not in _seen_brs:
                            _seen_brs.add(_br_key)
                            _cbr = (country, _br_key)
                            self._by_country_br.setdefault(_cbr, []).append(key)

        print(f"[VehicleDB] ✅ Загружено {len(self._index)} записей из vehicles.json")

    @staticmethod
    def _nation_to_country(nation: str) -> str:
        return NATION_TO_COUNTRY.get(nation.lower().strip(), nation.lower().strip())

    @staticmethod
    def _score(a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def find_match(
        self,
        name:   str,
        nation: str,
        br:     float = 0.0,
        mode:   str   = "",
    ) -> tuple[Optional[dict], float]:
        if not self._index:
            return None, 0.0

        norm    = normalize_name(name)
        country = self._nation_to_country(nation)

        alias_id = self._aliases.get((norm, country))
        if alias_id:
            alias_norm = normalize_name(alias_id)
            alias_row  = self._index.get((alias_norm, country))
            if alias_row:
                return alias_row, 1.0

        if self._units is not None and self._units.loaded:
            units_id = self._units.find_id(name)
            if units_id:
                units_norm = normalize_name(units_id)
                row_exact = self._index.get((units_norm, country))
                if row_exact is not None:
                    return row_exact, 1.0
                for (n, c), candidate_row in self._index.items():
                    if n == units_norm:
                        return candidate_row, 0.97

        exact = self._index.get((norm, country))
        if exact is not None:
            return exact, 1.0

        _MODE_BR_FIELDS: dict[str, list[str]] = {
            "Arcade":    ["arcade_br"],
            "Realistic": ["realistic_br", "realistic_ground_br", "arcade_br"],
            "Simulator": ["simulator_br", "simulator_ground_br", "realistic_br"],
            "Mixed":     ["realistic_br", "arcade_br", "simulator_br"],
            "":          ["realistic_br", "arcade_br", "simulator_br"],
        }
        _br_fields_for_mode = _MODE_BR_FIELDS.get(
            mode, _MODE_BR_FIELDS[""]
        )
        _BR_WINDOWS: list[float] = [0.0, 0.3, 0.7]

        if br > 0.0:
            br_r = round(br, 1)
            for window in _BR_WINDOWS:
                candidate_keys: set[tuple[str, str]] = set()
                _step = 0.1
                _cur  = br_r - window
                while _cur <= br_r + window + 0.01:
                    _k = round(_cur, 1)
                    candidate_keys.update(self._by_country_br.get((country, _k), []))
                    _cur = round(_cur + _step, 1)

                if not candidate_keys:
                    continue

                br_best_row:   Optional[dict] = None
                br_best_score: float          = 0.0
                for ckey in candidate_keys:
                    s = self._score(norm, ckey[0])
                    row_cand = self._index[ckey]
                    for _bf in _br_fields_for_mode:
                        _cand_br = float(row_cand.get(_bf) or 0)
                        if _cand_br > 0 and abs(_cand_br - br) <= 0.15:
                            s = min(1.0, s + 0.08)
                            break
                    if s > br_best_score:
                        br_best_score = s
                        br_best_row   = row_cand

                br_threshold = max(FUZZY_THRESHOLD - 0.25 + window * 0.35, 0.38)
                if br_best_score >= br_threshold:
                    return br_best_row, br_best_score

        best_row:   Optional[dict] = None
        best_score: float          = 0.0

        for key in self._by_country.get(country, []):
            s = self._score(norm, key[0])
            if s > best_score:
                best_score = s
                best_row   = self._index[key]

        if best_score >= FUZZY_THRESHOLD:
            return best_row, best_score

        g_best_row:   Optional[dict] = None
        g_best_score: float          = 0.0

        for (cand_norm, cand_country), row in self._index.items():
            s = self._score(norm, cand_norm)
            if cand_country != country:
                s *= 0.85
            if s > g_best_score:
                g_best_score = s
                g_best_row   = row

        if g_best_score >= FUZZY_THRESHOLD:
            return g_best_row, g_best_score

        return None, 0.0

    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "Name" not in df.columns:
            return df

        df = df.copy()

        _pair_cols = [c for c in ["Name", "Nation", "BR", "Mode"] if c in df.columns]
        pairs = df[_pair_cols].drop_duplicates()
        if "Nation" not in pairs.columns:
            pairs = pairs.assign(Nation="")
        if "BR" not in pairs.columns:
            pairs = pairs.assign(BR=0.0)
        if "Mode" not in pairs.columns:
            pairs = pairs.assign(Mode="")

        cache: dict[tuple[str, str], tuple[Optional[dict], float]] = {}
        fuzzy_log_lines: list[str] = []

        for _, row in pairs.iterrows():
            k     = (str(row["Name"]), str(row.get("Nation", "")))
            k_br  = float(row.get("BR", 0.0) or 0.0)
            k_mode = str(row.get("Mode", "") or "")
            if k in cache:
                continue
            vdb_row, match_score = self.find_match(k[0], k[1], br=k_br, mode=k_mode)
            cache[k] = (vdb_row, match_score)

            if vdb_row is not None and match_score < FUZZY_WARN_THRESHOLD:
                matched_id = vdb_row.get("vdb_identifier", "?")
                line = f"score={match_score:.3f} | {k[1]}/{k[0]} -> {matched_id}"
                fuzzy_log_lines.append(line)
                if len(fuzzy_log_lines) <= 10:
                    print(f"[VehicleDB] ⚡ {line}")

        if fuzzy_log_lines:
            try:
                with open(self._FUZZY_LOG_FILE, "w", encoding="utf-8") as _fl:
                    _fl.write("# VehicleDB fuzzy match log\n")
                    _fl.write("# Формат: score | нация/имя_в_статистике -> identifier_в_vehicles.json\n")
                    _fl.write("# Чтобы исправить: добавьте запись в dataset/aliases.json:\n")
                    _fl.write('#   { "нация/имя_в_статистике": "правильный_identifier" }\n\n')
                    _fl.write("\n".join(fuzzy_log_lines))
                print(f"[VehicleDB] 📝 {len(fuzzy_log_lines)} нечётких матчей -> {self._FUZZY_LOG_FILE}")
            except Exception as _le:
                print(f"[VehicleDB] ⚠️  Не удалось записать fuzzy лог: {_le}")

        sample = next((r for r, _ in cache.values() if r is not None), None)
        if sample is None:
            df["vdb_match_score"] = 0.0
            return df

        vdb_keys = list(sample.keys())

        for k in vdb_keys:
            val = sample[k]
            if isinstance(val, bool):
                df[k] = False
            elif isinstance(val, int):
                df[k] = 0
            elif isinstance(val, float):
                df[k] = 0.0
            elif isinstance(val, list):
                df[k] = [[] for _ in range(len(df))]
            else:
                df[k] = None

        df["vdb_match_score"] = 0.0

        def _fill(row: pd.Series) -> pd.Series:
            key = (str(row["Name"]), str(row.get("Nation", "")))
            vdb_row, score = cache.get(key, (None, 0.0))
            row["vdb_match_score"] = round(score, 3)
            if vdb_row:
                for vdb_k in vdb_keys:
                    row[vdb_k] = vdb_row.get(vdb_k)
            return row

        df = df.apply(_fill, axis=1)

        matched = int((df["vdb_match_score"] > 0).sum())
        avg     = df.loc[df["vdb_match_score"] > 0, "vdb_match_score"].mean()
        print(
            f"[VehicleDB] 🔗 Сопоставлено {matched}/{len(df)} "
            f"(avg confidence: {avg:.2f})"
        )
        return df

    @property
    def loaded(self) -> bool:
        return len(self._index) > 0

    def get_by_identifier(self, identifier: str) -> Optional[dict]:
        norm = normalize_name(identifier)
        for (n, _c), row in self._index.items():
            if n == norm:
                return row
        return None

    def stats(self) -> dict:
        countries = {}
        for (_n, c) in self._index:
            countries[c] = countries.get(c, 0) + 1
        return {"total": len(self._index), "by_country": countries}

    def __len__(self) -> int:
        return len(self._index)

    def __repr__(self) -> str:
        return f"VehicleDB({len(self)} vehicles)"
