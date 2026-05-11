from __future__ import annotations

import json


def campaign_prompt(
    product: dict,
    reviews: list[dict],
    local_analysis: dict,
    playbook: dict | None = None,
    results_summary: dict | None = None,
) -> str:
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
        "category_playbook": playbook or {},
        "experiment_results": results_summary or {},
    }
    return f"""
你是一个每天要对 GMV 负责的电商增长负责人，不是咨询顾问，也不是文案工具。
你的读者是一个很忙的品牌老板。他不想看“方法论”，只想知道今天该发什么、该测什么、该怎么回用户。

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
  "objection_queue": [
    {{
      "objection": "阻碍下单的顾虑",
      "priority": "high/medium",
      "why_it_blocks_order": "为什么会挡住成交",
      "evidence": "用户原话",
      "reply": "客服或私域运营今天就能发的回复",
      "owner": "负责人"
    }}
  ],
  "seven_day_plan": ["Day 1...", "Day 2..."],
  "decision_board": {{
    "ship_today": ["今天必须上线的动作"],
    "kill_if": ["什么情况说明这个方向该停"],
    "double_down_if": ["什么情况说明该加码"]
  }},
  "playbook": {{
    "category": "类目",
    "learned_rule": "这次样本沉淀出的打法"
  }},
  "learning_loop": {{
    "learning": "如果有实验结果，这轮学到了什么",
    "rows": [],
    "winner": {{}},
    "loser": {{}},
    "totals": {{}},
    "commercial_signal": {{
      "action": "加码/小额复测/暂停扩量",
      "recommended_budget": 0,
      "expected_revenue": 0,
      "expected_orders": 0,
      "aov": 0,
      "blended_cac": 0,
      "winner_cac": 0,
      "reason": "为什么这么分配预算",
      "budget_rule": "什么情况继续加，什么情况立刻停"
    }},
    "next_bets": ["下一轮怎么加码"],
    "playbook_update": "应该沉淀进类目手册的话"
  }},
  "voice_of_customer": ["高价值原声评论"],
  "keyword_cloud": [{{"term": "词", "count": 1}}]
}}

要求:
- 不要使用这些词：核心增长假设、定位角度、赋能、闭环、抓手、提升品牌认知、用户心智、场景化、差异化、价值主张。
- 不要写成三段式咨询报告。
- 每个 creative_tests 都必须像今天下午就能发出去的内容。
- 话术要像真实电商运营在飞书群里写给老板看的，不要像 AI 总结。
- 能短就短。允许有判断、有取舍、有“不建议这么做”。
- 明确指出买家为什么现在不下单，以及用什么证据推动下单。
- objection_queue 要像销售跟进清单，不要像抽象洞察；每条必须能直接复制给客服或私域运营。
- 保留评论里的真实语言，不要过度美化。
- 脚本要有人味，别每句都像广告语。可以用“先别买”“这个坑挺常见”“我会先测这个”这种表达。
- decision_board 必须具体。老板看完要知道今天做什么、什么数据不好就停、什么信号出现就加码。
- 如果输入里有 category_playbook，要利用它，但不要照抄。
- 如果输入里有 experiment_results，必须利用真实表现修正建议，不要还像没投放过一样从零判断。
- 如果输入里有 experiment_results，learning_loop.commercial_signal 必须给出下一轮预算动作和预估订单，不要只说“继续观察”。

输入数据:
{json.dumps(payload, ensure_ascii=False)}
""".strip()
