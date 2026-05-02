from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK_DIR = ROOT / "playbooks"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "default"


def load_playbook(category: str, explicit_path: str | None = None) -> dict:
    if explicit_path:
        path = Path(explicit_path)
    else:
        path = PLAYBOOK_DIR / f"{slugify(category)}.json"
    if not path.exists():
        return {
            "category": category,
            "known_objections": [],
            "winning_patterns": [],
            "bad_patterns": [],
            "metrics": ["收藏率", "评论区购买意图", "私信领取人数"],
            "next_experiments": [],
        }
    return json.loads(path.read_text("utf-8"))

