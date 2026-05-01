from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


PAIN_KEYWORDS = {
    "taste": ["味", "难喝", "甜", "苦", "口感", "涩", "taste", "bitter", "sweet"],
    "trust": ["配料", "添加", "代糖", "糖", "成分", "ingredient", "additive"],
    "price": ["贵", "便宜", "价格", "price", "expensive"],
    "packaging": ["包装", "漏", "瓶", "盖", "package", "leak"],
    "delivery": ["物流", "快递", "shipping", "delivery"],
    "effect": ["没用", "效果", "健康", "睡", "fat", "energy", "healthy"],
}


def load_product(path: str | Path) -> dict:
    return json.loads(Path(path).read_text("utf-8"))


def load_reviews(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            row["rating"] = float(row.get("rating") or 0)
            rows.append(row)
    return rows


def detect_pains(reviews: list[dict]) -> list[dict]:
    buckets: Counter[str] = Counter()
    evidence: dict[str, list[str]] = {key: [] for key in PAIN_KEYWORDS}
    for row in reviews:
        text = " ".join(str(row.get(key, "")) for key in ("title", "body")).lower()
        for pain, keywords in PAIN_KEYWORDS.items():
            if any(keyword.lower() in text for keyword in keywords):
                buckets[pain] += 1
                if len(evidence[pain]) < 3:
                    evidence[pain].append(row.get("body") or row.get("title") or "")
    total = max(len(reviews), 1)
    return [
        {
            "pain": pain,
            "share": round(count / total, 3),
            "mentions": count,
            "evidence": evidence[pain],
        }
        for pain, count in buckets.most_common()
    ]


def extract_voice_of_customer(reviews: list[dict], limit: int = 8) -> list[str]:
    candidates = []
    for row in reviews:
        body = str(row.get("body") or "").strip()
        if len(body) >= 12:
            candidates.append((row.get("rating", 0), body))
    candidates.sort(key=lambda item: item[0])
    return [text for _, text in candidates[:limit]]


def keyword_cloud(reviews: list[dict], limit: int = 30) -> list[dict]:
    stop = {"the", "and", "but", "this", "that", "with", "very", "really", "一个", "没有", "感觉"}
    words: Counter[str] = Counter()
    for row in reviews:
        text = " ".join(str(row.get(key, "")) for key in ("title", "body")).lower()
        for token in re.findall(r"[\u4e00-\u9fff]{2,}|[a-z]{3,}", text):
            if token not in stop:
                words[token] += 1
    return [{"term": term, "count": count} for term, count in words.most_common(limit)]


def fallback_plan(product: dict, reviews: list[dict]) -> dict:
    pains = detect_pains(reviews)
    top_pain = pains[0]["pain"] if pains else "trust"
    name = product["name"]
    audience = product.get("target_audience", "high-intent shoppers")
    offer = product.get("offer", "try the product with a clear guarantee")
    return {
        "source": "local-fallback",
        "executive_summary": (
            f"Position {name} around the highest-friction buyer concern: {top_pain}. "
            "The first campaign should not sell features; it should turn review anxiety into a simple buying test."
        ),
        "pain_map": pains,
        "positioning_angles": [
            {
                "angle": "Proof before promise",
                "why_it_matters": "Skeptical buyers convert when the ad shows how to verify the claim.",
                "message": f"Do not trust {name}; check these three signals before buying.",
            },
            {
                "angle": "Hidden cost of the cheap alternative",
                "why_it_matters": "Competitor pain makes price objections easier to reframe.",
                "message": "Cheap substitutes cost more when taste, ingredients, or returns fail.",
            },
            {
                "angle": "One-minute buying checklist",
                "why_it_matters": "Checklist content earns saves and gives support teams a conversion script.",
                "message": f"Use this checklist before choosing {product.get('category', 'this product')}.",
            },
        ],
        "creative_tests": [
            {
                "name": "Review autopsy",
                "hypothesis": f"{audience} will respond to a teardown of common bad reviews.",
                "hook": f"买{name}前，先看这 3 条差评。",
                "script": [
                    "先别急着下单，差评里藏着真正的购买标准。",
                    "第一，看用户是不是在抱怨同一个问题。",
                    "第二，看商家有没有直接回应这个问题。",
                    f"第三，用这个标准判断{name}是不是值得试。",
                    offer,
                ],
                "success_metric": "save rate and product-page click-through",
            },
            {
                "name": "Ingredient / feature receipt",
                "hypothesis": "Specific proof beats broad lifestyle promises.",
                "hook": "真正该看的不是广告，是这张清单。",
                "script": [
                    "大多数产品都在讲感觉，少数产品敢给证据。",
                    "把配料、参数、适用人群逐条摊开。",
                    "你会发现坑通常藏在没写清楚的地方。",
                    f"{name} 的卖点要用可检查证据讲出来。",
                ],
                "success_metric": "comment questions and DM intent",
            },
        ],
        "creator_brief": {
            "target_creator": "Practical comparison creator with trusted shopping tone",
            "deliverables": ["30s short video", "3-frame image post", "comment reply script"],
            "must_show": product.get("proof_points", []),
            "avoid": ["generic lifestyle claims", "over-polished studio tone"],
        },
        "landing_page_copy": {
            "headline": f"Stop guessing. Use real buyer signals to choose {name}.",
            "subhead": "A simple proof-led offer built from customer feedback, not marketing adjectives.",
            "bullets": product.get("proof_points", [])[:5],
            "cta": offer,
        },
        "dm_scripts": [
            {
                "trigger": "comment asks whether it is worth buying",
                "reply": f"你可以先看这 3 个点：{', '.join(product.get('proof_points', [])[:3])}。需要的话我发你完整对比清单。",
            },
            {
                "trigger": "price objection",
                "reply": "如果只比价格确实不占便宜，但这类产品更该比踩坑成本。我发你一张判断表。",
            },
        ],
        "seven_day_plan": [
            "Day 1: publish review-autopsy creative and collect objections",
            "Day 2: turn top comments into FAQ image post",
            "Day 3: test checklist hook against proof hook",
            "Day 4: DM everyone asking price/ingredients/features",
            "Day 5: publish competitor comparison without naming competitor",
            "Day 6: compile saves/comments into second offer angle",
            "Day 7: keep the winning hook, rewrite the first three seconds, retest",
        ],
        "voice_of_customer": extract_voice_of_customer(reviews),
        "keyword_cloud": keyword_cloud(reviews),
    }

