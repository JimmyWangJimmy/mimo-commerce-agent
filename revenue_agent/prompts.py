from __future__ import annotations

import json


def campaign_prompt(product: dict, reviews: list[dict], local_analysis: dict) -> str:
    compact_reviews = [
        {
            "rating": row.get("rating"),
            "title": row.get("title"),
            "body": row.get("body"),
        }
        for row in reviews[:80]
    ]
    payload = {
        "product": product,
        "reviews": compact_reviews,
        "local_analysis": local_analysis,
    }
    return f"""
你是一个面向电商和跨境卖家的增长负责人，不是文案工具。
你的任务是把商品评论和产品信息转成一套可以直接执行的 revenue actions。

只输出 JSON，不要 Markdown，不要解释。JSON schema:
{{
  "source": "mimo",
  "executive_summary": "一句话说明应该押注什么增长假设",
  "pain_map": [
    {{"pain": "痛点名", "share": 0.0, "mentions": 0, "evidence": ["评论证据"]}}
  ],
  "positioning_angles": [
    {{"angle": "定位角度", "why_it_matters": "为什么影响转化", "message": "可直接用于广告的核心表达"}}
  ],
  "creative_tests": [
    {{
      "name": "实验名",
      "hypothesis": "如果...那么...",
      "hook": "短视频前三秒",
      "script": ["5-7 句中文口播"],
      "success_metric": "一个可量化指标"
    }}
  ],
  "creator_brief": {{
    "target_creator": "达人类型",
    "deliverables": ["交付物"],
    "must_show": ["必须展示"],
    "avoid": ["避免事项"]
  }},
  "landing_page_copy": {{
    "headline": "落地页标题",
    "subhead": "副标题",
    "bullets": ["利益点"],
    "cta": "行动按钮"
  }},
  "dm_scripts": [
    {{"trigger": "触发场景", "reply": "私信/评论回复话术"}}
  ],
  "seven_day_plan": ["Day 1...", "Day 2..."],
  "voice_of_customer": ["高价值原声评论"],
  "keyword_cloud": [{{"term": "词", "count": 1}}]
}}

要求:
- 不要泛泛写“提升品牌认知”。
- 每个 creative_tests 都必须能在 24 小时内上线测试。
- 话术要像真实电商运营，不要像咨询报告。
- 明确指出买家为什么现在不下单，以及用什么证据推动下单。
- 保留评论里的真实语言，不要过度美化。

输入数据:
{json.dumps(payload, ensure_ascii=False)}
""".strip()

