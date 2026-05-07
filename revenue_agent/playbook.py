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


def playbook_path(category: str, explicit_path: str | None = None) -> Path:
    if explicit_path:
        return Path(explicit_path)
    return PLAYBOOK_DIR / f"{slugify(category)}.json"


def _append_unique(items: list, value: str) -> list:
    value = (value or "").strip()
    if value and value not in items:
        items.append(value)
    return items


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


def apply_playbook_patch(patch: dict, explicit_path: str | None = None) -> tuple[Path, dict]:
    category = patch.get("category") or "default"
    path = playbook_path(category, explicit_path)
    current = load_playbook(category, str(path)) if path.exists() else load_playbook(category)
    current.setdefault("category", category)
    current.setdefault("known_objections", [])
    current.setdefault("winning_patterns", [])
    current.setdefault("bad_patterns", [])
    current.setdefault("metrics", [])
    current.setdefault("next_experiments", [])
    current.setdefault("learning_log", [])

    _append_unique(current["winning_patterns"], patch.get("learned_rule", ""))
    _append_unique(current["winning_patterns"], patch.get("winning_pattern", ""))
    _append_unique(current["bad_patterns"], patch.get("bad_pattern", ""))
    for experiment in patch.get("next_experiments", []):
        _append_unique(current["next_experiments"], str(experiment))
    metrics = patch.get("metrics") or {}
    for metric in metrics:
        _append_unique(current["metrics"], str(metric))
    current["learning_log"].append(
        {
            "created_at": patch.get("created_at"),
            "source": patch.get("source"),
            "learned_rule": patch.get("learned_rule"),
            "metrics": metrics,
        }
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return path, current
