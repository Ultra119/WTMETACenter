from __future__ import annotations

import csv
import os
import re
import unicodedata
from typing import Optional

from analytics.datamine import fetch

_SHOP_SUFFIX_RE = re.compile(r"_shop$")

_BADGE_PREFIX_RE = re.compile(r"^[^\w(\[{\"']+", re.UNICODE)


def _strip_badge_prefix(name: str) -> str:
    stripped = name.strip()
    while stripped and unicodedata.category(stripped[0]) in ("So", "Sm", "Sk", "Co", "Cn"):
        stripped = stripped[1:].lstrip()
    return stripped.replace('""', '"') or name.strip()


UNITS_CSV_FILENAME: str = "units.csv"
UNITS_CSV_PATH: str     = "lang.vromfs.bin_u/lang/units.csv"


class UnitsCsvTranslator:
    def __init__(self, dataset_dir: str) -> None:
        self._en_to_id: dict[str, str] = {}
        self._id_to_en: dict[str, str] = {}
        self.loaded: bool = False

        local_path = os.path.join(dataset_dir, UNITS_CSV_FILENAME)
        self._load(local_path)


    def find_name(self, identifier: str) -> Optional[str]:
        if not identifier:
            return None
        return self._id_to_en.get(identifier)

    def __len__(self) -> int:
        return len(self._en_to_id)

    def __repr__(self) -> str:
        status = "loaded" if self.loaded else "not loaded"
        return f"UnitsCsvTranslator({len(self._en_to_id)} names, {status})"


    def _load(self, path: str) -> None:
        if not os.path.exists(path):
            self._try_download(path)
        if not os.path.exists(path):
            print(
                "[UnitsCsv] ⚠️  units.csv is unavailable — equipment names will be "
                "taken from the source data without normalization"
            )
            return
        self._parse(path)

    def _try_download(self, dest: str) -> None:
        fetch(dest, UNITS_CSV_PATH, "UnitsCsv")

    def _parse(self, path: str) -> None:
        count_parsed  = 0
        count_skipped = 0
        try:
            with open(path, encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.reader(f, delimiter=";", quotechar='"')
                for i, row in enumerate(reader):
                    if i == 0:
                        continue
                    if len(row) < 2:
                        count_skipped += 1
                        continue

                    raw_id  = row[0].strip().strip('"')
                    english = row[1].strip()

                    if len(english) >= 2 and english[0] == '"' and english[-1] == '"':
                        english = english[1:-1].replace('""', '"')

                    english = _strip_badge_prefix(english)

                    if not raw_id or not english:
                        count_skipped += 1
                        continue
                    if english.startswith("<") and english.endswith(">"):
                        count_skipped += 1
                        continue
                    if english in ("-", "—", " "):
                        count_skipped += 1
                        continue

                    identifier = raw_id.split("/", 1)[-1] if "/" in raw_id else raw_id
                    base_id    = _SHOP_SUFFIX_RE.sub("", identifier)
                    en_key     = english.lower()
                    is_shop    = identifier.endswith("_shop")

                    if en_key not in self._en_to_id or is_shop:
                        self._en_to_id[en_key] = base_id
                    if base_id not in self._id_to_en or is_shop:
                        self._id_to_en[base_id] = english

                    count_parsed += 1

        except Exception as e:
            print(f"[UnitsCsv] ❌ Error parsing units.csv: {e}")
            return

        self.loaded = True
        print(
            f"[UnitsCsv] ✅ {count_parsed} records loaded "
            f"({len(self._en_to_id)} (unique names) from units.csv"
        )
