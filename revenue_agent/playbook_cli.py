from __future__ import annotations

import argparse
import json
from pathlib import Path

from revenue_agent.playbook import apply_playbook_patch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply a generated playbook patch.")
    parser.add_argument("patch", help="Path to playbook_patch.json.")
    parser.add_argument("--playbook", help="Optional target playbook path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    patch = json.loads(Path(args.patch).read_text("utf-8"))
    path, playbook = apply_playbook_patch(patch, args.playbook)
    print(json.dumps({"playbook": str(path), "learning_log": len(playbook.get("learning_log", []))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
