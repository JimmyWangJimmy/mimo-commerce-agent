from __future__ import annotations

import json
import re
from datetime import UTC, datetime
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


def build_playbook_patch(plan: dict) -> dict:
    playbook = plan.get("playbook") or {}
    loop = plan.get("learning_loop") or {}
    update = loop.get("playbook_update") or playbook.get("learned_rule")
    if not update:
        return {}
    winner = loop.get("winner") or {}
    loser = loop.get("loser") or {}
    return {
        "category": playbook.get("category") or "unknown",
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": plan.get("source", "unknown"),
        "learned_rule": update,
        "winning_pattern": winner.get("hook") or winner.get("experiment") or "",
        "bad_pattern": loser.get("hook") or loser.get("experiment") or "",
        "metrics": loop.get("totals", {}),
        "next_experiments": loop.get("next_bets", []),
    }
