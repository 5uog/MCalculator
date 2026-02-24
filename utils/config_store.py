# FILE: utils/config_store.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

def load_json(path: Path) -> Optional[dict[str, Any]]:
    try:
        txt = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        return None

    try:
        obj = json.loads(txt)
    except json.JSONDecodeError:
        return None

    return obj if isinstance(obj, dict) else None

def save_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")

    txt = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    tmp.write_text(txt, encoding="utf-8")

    # Atomic replace on Windows/macOS/Linux
    os.replace(str(tmp), str(path))