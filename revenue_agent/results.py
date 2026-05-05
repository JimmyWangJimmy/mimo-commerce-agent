from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path


NUMERIC_FIELDS = ("impressions", "views", "saves", "clicks", "dms", "orders", "spend", "revenue")


def load_results(path: str | Path | None) -> list[dict]:
    if not path:
        return []
    return parse_results(Path(path).read_text("utf-8-sig"))


def parse_results(text: str) -> list[dict]:
    rows: list[dict] = []
    with StringIO(text) as handle:
        for row in csv.DictReader(handle):
            parsed = dict(row)
            for field in NUMERIC_FIELDS:
                parsed[field] = float(parsed.get(field) or 0)
            rows.append(parsed)
    return rows


def enrich_result(row: dict) -> dict:
    impressions = max(float(row.get("impressions") or 0), 1)
    views = max(float(row.get("views") or 0), 1)
    clicks = max(float(row.get("clicks") or 0), 1)
    spend = float(row.get("spend") or 0)
    revenue = float(row.get("revenue") or 0)
    enriched = dict(row)
    enriched["save_rate"] = round(float(row.get("saves") or 0) / views, 4)
    enriched["click_rate"] = round(float(row.get("clicks") or 0) / impressions, 4)
    enriched["dm_rate"] = round(float(row.get("dms") or 0) / impressions, 4)
    enriched["order_rate"] = round(float(row.get("orders") or 0) / clicks, 4)
    enriched["roas"] = round(revenue / spend, 2) if spend > 0 else 0
    return enriched


def summarize_results(results: list[dict]) -> dict:
    if not results:
        return {}
    enriched = [enrich_result(row) for row in results]
    ranked = sorted(enriched, key=lambda row: (row["roas"], row.get("orders", 0), row["save_rate"]), reverse=True)
    winner = ranked[0]
    loser = sorted(enriched, key=lambda row: (row.get("orders", 0), row["save_rate"]))[0]
    total_spend = sum(float(row.get("spend") or 0) for row in enriched)
    total_revenue = sum(float(row.get("revenue") or 0) for row in enriched)
    total_orders = sum(float(row.get("orders") or 0) for row in enriched)
    next_bets = [
        f"把「{winner.get('hook')}」改 3 个前三秒版本继续测",
        f"保留 {winner.get('channel')}，先别扩太多渠道",
        "把评论区问题整理进下一版私信自动回复",
    ]
    return {
        "rows": enriched,
        "winner": winner,
        "loser": loser,
        "totals": {
            "spend": round(total_spend, 2),
            "revenue": round(total_revenue, 2),
            "orders": int(total_orders),
            "roas": round(total_revenue / total_spend, 2) if total_spend > 0 else 0,
        },
        "learning": (
            f"这轮不是所有内容都值得继续。胜出的是「{winner.get('experiment')}」，"
            f"主要信号是 ROAS {winner.get('roas')}、订单 {int(winner.get('orders') or 0)}。"
            f"表现最弱的是「{loser.get('experiment')}」，先停，不要靠加预算硬救。"
        ),
        "next_bets": next_bets,
        "playbook_update": (
            f"在这个类目里，{winner.get('channel')} 上「{winner.get('hook')}」这种表达值得保留；"
            f"低订单且低收藏的内容不要继续扩量。"
        ),
    }
