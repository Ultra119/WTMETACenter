from __future__ import annotations

import os
import time
import urllib.error
import urllib.request

DATAMINE_OWNER  = "gszabi99"
DATAMINE_REPO   = "War-Thunder-Datamine"
DATAMINE_REF    = "refs/tags/2.59.0.9"
DATAMINE_BRANCH = DATAMINE_REF.split("/")[-1]

BASE_URL   = f"https://github.com/{DATAMINE_OWNER}/{DATAMINE_REPO}/raw/{DATAMINE_REF}"
_TIMEOUT   = 30
_ATTEMPTS  = 3
_BACKOFF   = 2.0


def fetch(dest: str, relative_path: str, label: str) -> bool:
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True

    url = f"{BASE_URL}/{relative_path}"
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)

    for attempt in range(1, _ATTEMPTS + 1):
        try:
            print(f"[{label}] 📥 {DATAMINE_BRANCH}/{relative_path} (attempt {attempt})")
            req = urllib.request.Request(url, headers={"User-Agent": "WTMetaCenter/1.0"})
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                payload = resp.read()
            if not payload:
                raise ValueError("empty response")
            with open(dest, "wb") as out_f:
                out_f.write(payload)
            print(f"[{label}] ✅ saved → {dest}")
            return True
        except (urllib.error.URLError, OSError, ValueError) as e:
            if attempt == _ATTEMPTS:
                print(f"[{label}] ❌ giving up after {_ATTEMPTS} attempts: {e}")
                break
            time.sleep(_BACKOFF ** attempt)

    print(f"[{label}] ⚠️  {os.path.basename(dest)} missing — upload it to dataset/ manually")
    print(f"[{label}]    URL: {url}")
    return False
