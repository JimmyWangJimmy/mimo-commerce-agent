from __future__ import annotations

import argparse
import json
import sys

from revenue_agent.analyze import fallback_plan, load_product, load_reviews
from revenue_agent.mimo import MiMoError, call_mimo_json
from revenue_agent.playbook import load_playbook
from revenue_agent.prompts import campaign_prompt
from revenue_agent.render import write_outputs
from revenue_agent.results import load_results, summarize_results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a commerce revenue action pack.")
    parser.add_argument("--product", required=True, help="Product JSON path.")
    parser.add_argument("--reviews", required=True, help="Review CSV path.")
    parser.add_argument("--out", default="output/demo", help="Output directory.")
    parser.add_argument("--use-mimo", action="store_true", help="Call Xiaomi MiMo instead of local fallback.")
    parser.add_argument("--playbook", help="Optional category playbook JSON path.")
    parser.add_argument("--results", help="Optional experiment results CSV path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    product = load_product(args.product)
    reviews = load_reviews(args.reviews)
    results_summary = summarize_results(load_results(args.results))
    playbook = load_playbook(product.get("category", "default"), args.playbook)
    local = fallback_plan(product, reviews, playbook, results_summary)
    plan = local
    if args.use_mimo:
        try:
            prompt = campaign_prompt(product, reviews, local, playbook, results_summary)
            plan = call_mimo_json(prompt)
            plan.setdefault("source", "mimo")
            plan.setdefault("playbook", playbook)
            if results_summary:
                merged_loop = dict(results_summary)
                merged_loop.update(plan.get("learning_loop") or {})
                merged_loop.setdefault("rows", results_summary.get("rows", []))
                merged_loop.setdefault("totals", results_summary.get("totals", {}))
                plan["learning_loop"] = merged_loop
        except (MiMoError, json.JSONDecodeError, KeyError) as exc:
            print(f"MiMo unavailable; using local fallback: {exc}", file=sys.stderr)
            plan = local
    write_outputs(plan, args.out)
    print(json.dumps({"out": args.out, "source": plan.get("source"), "tests": len(plan.get("creative_tests", []))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
