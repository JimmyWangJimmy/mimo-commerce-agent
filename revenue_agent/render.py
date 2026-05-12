from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from revenue_agent.playbook import build_playbook_patch


def write_outputs(plan: dict, out_dir: str | Path) -> None:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "campaign.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (target / "index.html").write_text(render_html(plan), "utf-8")
    (target / "brief.md").write_text(render_markdown(plan), "utf-8")
    (target / "operator_onepager.html").write_text(render_operator_onepager(plan), "utf-8")
    (target / "investor_onepager.md").write_text(render_investor_onepager(plan), "utf-8")
    (target / "category_memory.html").write_text(render_category_memory(plan), "utf-8")
    (target / "demo_room.html").write_text(render_demo_room(plan), "utf-8")
    write_objection_csv(plan, target / "objection_queue.csv")
    patch = build_playbook_patch(plan)
    if patch:
        (target / "playbook_patch.json").write_text(json.dumps(patch, ensure_ascii=False, indent=2) + "\n", "utf-8")


def write_objection_csv(plan: dict, path: Path) -> None:
    fields = ["objection", "priority", "why_it_blocks_order", "evidence", "reply", "owner"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in plan.get("objection_queue", []):
            writer.writerow(item)


def render_markdown(plan: dict) -> str:
    lines = [
        "# 今天先测这几件事",
        "",
        f"Source: `{plan.get('source', 'unknown')}`",
        "",
        "## 先说结论",
        "",
        plan.get("executive_summary", ""),
        "",
        "## 今天能发的内容",
    ]
    for test in plan.get("creative_tests", []):
        lines.extend(
            [
                "",
                f"### {test.get('name', 'Untitled')}",
                "",
                f"- 为什么测：{test.get('hypothesis', '')}",
                f"- 开头第一句：{test.get('hook', '')}",
                f"- 看什么数据：{test.get('success_metric', '')}",
                "",
                "口播脚本：",
            ]
        )
        for line in test.get("script", []):
            lines.append(f"- {line}")
    lines.extend(["", "## 这一周怎么跑"])
    for item in plan.get("seven_day_plan", []):
        lines.append(f"- {item}")
    board = plan.get("decision_board") or {}
    if board:
        lines.extend(["", "## 今天的判断板"])
        for key, label in (("ship_today", "今天上线"), ("kill_if", "这些情况就停"), ("double_down_if", "这些情况就加码")):
            lines.extend(["", f"### {label}"])
            for item in board.get(key, []):
                lines.append(f"- {item}")
    loop = plan.get("learning_loop") or {}
    if loop:
        lines.extend(["", "## 跑完之后学到了什么", "", loop.get("learning", "")])
        for item in loop.get("next_bets", []):
            lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _card(title: str, body: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2>{body}</section>"


def _top_test(plan: dict) -> dict:
    loop = plan.get("learning_loop") or {}
    winner = loop.get("winner") or {}
    if winner:
        return winner
    tests = plan.get("creative_tests") or []
    return tests[0] if tests else {}


def _list_items(items: list, limit: int = 6) -> str:
    return "".join(f"<li>{html.escape(str(item))}</li>" for item in items[:limit])


def render_category_memory(plan: dict) -> str:
    playbook = plan.get("playbook") or {}
    patch = build_playbook_patch(plan)
    loop = plan.get("learning_loop") or {}
    existing_rules = []
    existing_rules.extend(playbook.get("winning_patterns") or [])
    existing_rules.extend(playbook.get("known_objections") or [])
    next_experiments = patch.get("next_experiments") or loop.get("next_bets") or playbook.get("next_experiments") or []
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Category Memory</title>
  <style>
    body {{ margin: 0; font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17221d; background: #fbfcfa; }}
    main {{ max-width: 1060px; margin: auto; padding: 44px 6vw 68px; }}
    h1 {{ margin: 0 0 12px; font-size: 44px; line-height: 1.05; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 22px; }}
    .summary {{ max-width: 780px; font-size: 20px; color: #33413b; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-top: 24px; }}
    section {{ background: white; border: 1px solid #d6ded9; border-radius: 8px; padding: 18px; }}
    ul, ol {{ margin: 0; padding-left: 20px; }}
    li + li {{ margin-top: 7px; }}
    pre {{ white-space: pre-wrap; background: #101c17; color: #eaf3ee; border-radius: 8px; padding: 14px; overflow-x: auto; }}
    .new {{ border-color: #88b9a6; background: #f2faf6; }}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(str(playbook.get('category') or patch.get('category') or 'Category'))} Memory</h1>
    <p class="summary">Data Flywheel: 每次把评论、投放结果和预算判断合并成一条类目记忆，下次生成不再从空白提示开始。</p>
    <div class="grid">
      <section>
        <h2>已有可复用规则</h2>
        <ul>{_list_items(existing_rules)}</ul>
      </section>
      <section class="new">
        <h2>这轮新增记忆</h2>
        <p>{html.escape(str(patch.get('learned_rule') or '这轮还没有可写入的新增规则。'))}</p>
        <p><b>胜出表达：</b>{html.escape(str(patch.get('winning_pattern') or ''))}</p>
        <p><b>该停表达：</b>{html.escape(str(patch.get('bad_pattern') or ''))}</p>
      </section>
      <section>
        <h2>下一轮实验</h2>
        <ol>{_list_items(next_experiments)}</ol>
      </section>
    </div>
    <section style="margin-top:14px">
      <h2>Memory Patch JSON</h2>
      <pre>{html.escape(json.dumps(patch, ensure_ascii=False, indent=2))}</pre>
    </section>
  </main>
</body>
</html>
"""


def render_demo_room(plan: dict) -> str:
    loop = plan.get("learning_loop") or {}
    totals = loop.get("totals") or {}
    commercial = loop.get("commercial_signal") or {}
    source_label = "MiMo 生成" if plan.get("source") == "mimo" else "本地兜底"
    links = [
        ("index.html", "运营看板", "今天上线什么、停什么、加码什么"),
        ("operator_onepager.html", "老板一页纸", "收入、订单、预算和第一条内容"),
        ("category_memory.html", "类目记忆", "已有规则、本轮新增记忆和下一轮实验"),
        ("objection_queue.csv", "销售跟进 CSV", "给客服和私域团队直接分派"),
        ("investor_onepager.md", "投资人一页纸", "产品楔子、数据飞轮和当前 demo 信号"),
        ("campaign.json", "结构化输出", "给 API、自动化和二次处理使用"),
    ]
    link_cards = "".join(
        f"<a class='card' href='{html.escape(href)}'><b>{html.escape(title)}</b><span>{html.escape(desc)}</span><code>{html.escape(href)}</code></a>"
        for href, title, desc in links
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MiMo Commerce Agent Demo Room</title>
  <style>
    body {{ margin: 0; font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17221d; background: #fbfcfa; }}
    header {{ padding: 46px 6vw 28px; background: #eaf3ee; border-bottom: 1px solid #d6ded9; }}
    main {{ max-width: 1120px; margin: auto; padding: 28px 6vw 68px; }}
    h1 {{ margin: 0 0 12px; font-size: 54px; line-height: 1.03; letter-spacing: 0; }}
    .summary {{ max-width: 820px; font-size: 20px; color: #26332d; }}
    .pills {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }}
    .pill {{ border: 1px solid #d6ded9; border-radius: 999px; background: white; padding: 5px 9px; font-size: 13px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 24px 0; }}
    .metric, .card {{ background: white; border: 1px solid #d6ded9; border-radius: 8px; padding: 16px; }}
    .metric b {{ display: block; color: #66736e; font-size: 13px; }}
    .metric strong {{ display: block; margin-top: 4px; font-size: 28px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }}
    .card {{ display: flex; min-height: 150px; flex-direction: column; gap: 10px; color: inherit; text-decoration: none; }}
    .card b {{ font-size: 20px; }}
    .card span {{ color: #33413b; }}
    .card code {{ margin-top: auto; color: #116b55; }}
  </style>
</head>
<body>
  <header>
    <div class="pills">
      <span class="pill">{html.escape(source_label)}</span>
      <span class="pill">Demo Room</span>
      <span class="pill">可分享入口</span>
    </div>
    <h1>MiMo Commerce Agent Demo Room</h1>
    <p class="summary">{html.escape(plan.get('executive_summary', ''))}</p>
  </header>
  <main>
    <div class="metrics">
      <div class="metric"><b>ROAS</b><strong>{totals.get('roas', 0)}</strong></div>
      <div class="metric"><b>订单</b><strong>{totals.get('orders', 0)}</strong></div>
      <div class="metric"><b>建议预算</b><strong>{commercial.get('recommended_budget', 0)}</strong></div>
      <div class="metric"><b>预算动作</b><strong>{html.escape(str(commercial.get('action', '')))}</strong></div>
    </div>
    <div class="grid">{link_cards}</div>
  </main>
</body>
</html>
"""


def render_investor_onepager(plan: dict) -> str:
    loop = plan.get("learning_loop") or {}
    totals = loop.get("totals") or {}
    commercial = loop.get("commercial_signal") or {}
    patch = build_playbook_patch(plan)
    top = _top_test(plan)
    lines = [
        "# MiMo Commerce Agent One-Pager",
        "",
        "## What It Does",
        "",
        "Turns customer reviews and campaign results into the next revenue actions for commerce teams.",
        "",
        "## Why It Matters",
        "",
        "Most AI content tools stop at copy. This product closes the loop from buyer feedback to creative tests to performance learning.",
        "",
        "## Current Demo Signal",
        "",
        f"- Summary: {plan.get('executive_summary', '')}",
        f"- Winning action: {top.get('experiment') or top.get('name') or top.get('hook') or ''}",
        f"- ROAS: {totals.get('roas', 'n/a')}",
        f"- Orders: {totals.get('orders', 'n/a')}",
        f"- Next budget action: {commercial.get('action', 'n/a')}",
        f"- Recommended next spend: {commercial.get('recommended_budget', 'n/a')}",
        f"- Expected next revenue: {commercial.get('expected_revenue', 'n/a')}",
        "",
        "## Data Flywheel",
        "",
        "1. Ingest reviews and campaign results.",
        "2. Generate what to ship, kill, and double down on.",
        "3. Export a playbook patch.",
        "4. Apply the patch back into the category playbook.",
        "5. The next run starts with learned category memory.",
        "",
        "## Playbook Patch",
        "",
        "```json",
        json.dumps(patch, ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines) + "\n"


def render_operator_onepager(plan: dict) -> str:
    loop = plan.get("learning_loop") or {}
    totals = loop.get("totals") or {}
    commercial = loop.get("commercial_signal") or {}
    board = plan.get("decision_board") or {}
    top = _top_test(plan)
    ship = "".join(f"<li>{html.escape(str(item))}</li>" for item in board.get("ship_today", [])[:4])
    kill = "".join(f"<li>{html.escape(str(item))}</li>" for item in board.get("kill_if", [])[:4])
    next_bets = "".join(f"<li>{html.escape(str(item))}</li>" for item in loop.get("next_bets", [])[:4])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>增长执行一页纸</title>
  <style>
    body {{ margin: 0; font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17221d; background: #fbfcfa; }}
    main {{ max-width: 980px; margin: auto; padding: 46px 6vw 70px; }}
    h1 {{ font-size: 48px; line-height: 1.05; margin: 0 0 16px; letter-spacing: 0; }}
    h2 {{ font-size: 20px; margin: 0 0 12px; }}
    .summary {{ font-size: 21px; color: #26332d; max-width: 820px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 26px 0; }}
    .metric, section {{ background: white; border: 1px solid #d6ded9; border-radius: 8px; padding: 18px; }}
    .metric b {{ display: block; color: #66736e; font-size: 13px; }}
    .metric strong {{ display: block; margin-top: 4px; font-size: 30px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; }}
    ul {{ padding-left: 20px; margin: 0; }}
    li + li {{ margin-top: 6px; }}
    .hook {{ display: inline-block; margin-top: 10px; padding: 8px 10px; background: #116b55; color: white; border-radius: 6px; font-weight: 800; }}
  </style>
</head>
<body>
  <main>
    <h1>这轮增长怎么打</h1>
    <p class="summary">{html.escape(plan.get('executive_summary', ''))}</p>
    <div class="metrics">
      <div class="metric"><b>总收入</b><strong>{totals.get('revenue', 0)}</strong></div>
      <div class="metric"><b>订单</b><strong>{totals.get('orders', 0)}</strong></div>
      <div class="metric"><b>ROAS</b><strong>{totals.get('roas', 0)}</strong></div>
      <div class="metric"><b>下一轮预算</b><strong>{commercial.get('recommended_budget', 0)}</strong></div>
      <div class="metric"><b>胜出实验</b><strong>{html.escape(str(top.get('experiment') or top.get('name') or ''))}</strong></div>
    </div>
    <div class="grid">
      <section><h2>今天上线</h2><ul>{ship}</ul></section>
      <section><h2>这些情况就停</h2><ul>{kill}</ul></section>
      <section><h2>下一轮只押这些</h2><ul>{next_bets}</ul></section>
    </div>
    <section style="margin-top:14px">
      <h2>预算判断</h2>
      <p><b>{html.escape(str(commercial.get('action', '先小额复测')))}</b>：{html.escape(str(commercial.get('reason', '等真实结果回来后再加预算。')))}</p>
      <p>{html.escape(str(commercial.get('budget_rule', '先看购买意图，不用预算硬救。')))}</p>
    </section>
    <section style="margin-top:14px">
      <h2>第一条内容怎么开头</h2>
      <div class="hook">{html.escape(str(top.get('hook') or ''))}</div>
    </section>
  </main>
</body>
</html>
"""


def render_html(plan: dict) -> str:
    board = plan.get("decision_board") or {}
    playbook = plan.get("playbook") or {}
    loop = plan.get("learning_loop") or {}
    commercial = loop.get("commercial_signal") or {}
    source_label = "MiMo 生成" if plan.get("source") == "mimo" else "本地兜底"
    patch = build_playbook_patch(plan)
    patch_json = json.dumps(patch, ensure_ascii=False, indent=2) if patch else ""
    warnings = "".join(f"<p>{html.escape(str(item))}</p>" for item in plan.get("warnings", []))
    warning_section = f"<div class='warning'>{warnings}</div>" if warnings else ""
    pains = "".join(
        f"<tr><td>{html.escape(str(p.get('pain')))}</td><td>{p.get('mentions')}</td><td>{p.get('share')}</td><td>{html.escape(' / '.join(p.get('evidence', [])[:2]))}</td></tr>"
        for p in plan.get("pain_map", [])
    )
    angles = "".join(
        f"<li><strong>{html.escape(a.get('angle', ''))}</strong><br>{html.escape(a.get('message', ''))}<small>{html.escape(a.get('why_it_matters', ''))}</small></li>"
        for a in plan.get("positioning_angles", [])
    )
    tests = "".join(
        f"""
        <article>
          <h3>{html.escape(test.get('name', 'Untitled'))}</h3>
          <p><b>为什么测：</b>{html.escape(test.get('hypothesis', ''))}</p>
          <p class="hook">{html.escape(test.get('hook', ''))}</p>
          <ol>{''.join(f'<li>{html.escape(str(line))}</li>' for line in test.get('script', []))}</ol>
          <p><b>看什么：</b>{html.escape(test.get('success_metric', ''))}</p>
        </article>
        """
        for test in plan.get("creative_tests", [])
    )
    dm = "".join(
        f"<li><b>{html.escape(item.get('trigger', ''))}</b><br>{html.escape(item.get('reply', ''))}</li>"
        for item in plan.get("dm_scripts", [])
    )
    objection_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(item.get('priority', '')))}</td>"
        f"<td>{html.escape(str(item.get('objection', '')))}</td>"
        f"<td>{html.escape(str(item.get('evidence', '')))}</td>"
        f"<td>{html.escape(str(item.get('reply', '')))}</td>"
        f"<td>{html.escape(str(item.get('owner', '')))}</td>"
        "</tr>"
        for item in plan.get("objection_queue", [])
    )
    days = "".join(f"<li>{html.escape(str(day))}</li>" for day in plan.get("seven_day_plan", []))
    ship = "".join(f"<li>{html.escape(str(item))}</li>" for item in board.get("ship_today", []))
    kill = "".join(f"<li>{html.escape(str(item))}</li>" for item in board.get("kill_if", []))
    double = "".join(f"<li>{html.escape(str(item))}</li>" for item in board.get("double_down_if", []))
    playbook_items = []
    if playbook.get("learned_rule"):
        playbook_items.append(playbook["learned_rule"])
    playbook_items.extend(playbook.get("winning_patterns") or [])
    playbook_items.extend(playbook.get("known_objections") or [])
    playbook_rules = "".join(f"<li>{html.escape(str(item))}</li>" for item in playbook_items[:6])
    result_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(row.get('experiment', '')))}</td>"
        f"<td>{html.escape(str(row.get('channel', '')))}</td>"
        f"<td>{html.escape(str(row.get('hook', '')))}</td>"
        f"<td>{row.get('save_rate', 0):.1%}</td>"
        f"<td>{row.get('click_rate', 0):.1%}</td>"
        f"<td>{int(row.get('orders') or 0)}</td>"
        f"<td>{row.get('roas', 0)}</td>"
        "</tr>"
        for row in loop.get("rows", [])
    )
    next_bets = "".join(f"<li>{html.escape(str(item))}</li>" for item in loop.get("next_bets", []))
    learning_section = ""
    if loop:
        commercial_body = ""
        if commercial:
            commercial_body = f"""
            <h3>下一轮预算怎么打</h3>
            <div class="metric-row">
              <div><b>动作</b><strong>{html.escape(str(commercial.get('action', '')))}</strong></div>
              <div><b>建议预算</b><strong>{commercial.get('recommended_budget', 0)}</strong></div>
              <div><b>预估订单</b><strong>{commercial.get('expected_orders', 0)}</strong></div>
              <div><b>预估收入</b><strong>{commercial.get('expected_revenue', 0)}</strong></div>
            </div>
            <p><b>判断：</b>{html.escape(str(commercial.get('reason', '')))}</p>
            <p><b>预算线：</b>{html.escape(str(commercial.get('budget_rule', '')))}</p>
            """
        learning_section = _card(
            "跑完之后学到了什么",
            f"""
            <p class="summary-small">{html.escape(loop.get('learning', ''))}</p>
            <div class="metric-row">
              <div><b>总花费</b><strong>{loop.get('totals', {}).get('spend', 0)}</strong></div>
              <div><b>总收入</b><strong>{loop.get('totals', {}).get('revenue', 0)}</strong></div>
              <div><b>订单</b><strong>{loop.get('totals', {}).get('orders', 0)}</strong></div>
              <div><b>ROAS</b><strong>{loop.get('totals', {}).get('roas', 0)}</strong></div>
            </div>
            <table><thead><tr><th>实验</th><th>渠道</th><th>开头</th><th>收藏率</th><th>点击率</th><th>订单</th><th>ROAS</th></tr></thead><tbody>{result_rows}</tbody></table>
            <h3>下一轮只做这些</h3><ul>{next_bets}</ul>
            {commercial_body}
            <p><b>沉淀进手册：</b>{html.escape(loop.get('playbook_update', ''))}</p>
            {f'<h3>手册补丁</h3><pre>{html.escape(patch_json)}</pre>' if patch_json else ''}
            """,
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>今天先测这几件事</title>
  <style>
    :root {{ color-scheme: light; --ink:#17221d; --muted:#66736e; --line:#d6ded9; --green:#116b55; --amber:#d99621; --red:#a84337; --paper:#fbfcfa; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--paper); }}
    header {{ padding: 42px 6vw 28px; background: #eaf3ee; border-bottom: 1px solid var(--line); }}
    main {{ padding: 28px 6vw 60px; max-width: 1180px; margin: auto; }}
    h1 {{ margin: 0 0 12px; font-size: clamp(32px, 5vw, 64px); line-height: 1.02; letter-spacing: 0; }}
    h2 {{ margin: 0 0 16px; font-size: 24px; }}
    h3 {{ margin: 0 0 10px; font-size: 20px; }}
    section {{ padding: 28px 0; border-bottom: 1px solid var(--line); }}
    .summary {{ max-width: 780px; font-size: 20px; color: #26332d; }}
    .summary-small {{ max-width: 820px; font-size: 18px; color: #26332d; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }}
    .pill {{ display: inline-flex; align-items: center; padding: 5px 9px; border: 1px solid var(--line); border-radius: 999px; background: #fff; color: #33413b; font-size: 13px; }}
    .decision {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; margin-top: 20px; }}
    .decision > div {{ background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 16px; }}
    .decision h3 {{ font-size: 16px; margin-bottom: 8px; }}
    .decision ul {{ margin: 0; padding-left: 20px; }}
    .ship h3 {{ color: var(--green); }}
    .kill h3 {{ color: var(--red); }}
    .double h3 {{ color: var(--amber); }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ padding: 12px; border: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ background: #f0f5f2; }}
    ul.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; padding: 0; list-style: none; }}
    ul.grid li, article {{ background: white; border: 1px solid var(--line); border-radius: 8px; padding: 18px; }}
    small {{ display: block; margin-top: 8px; color: var(--muted); }}
    .tests {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
    .hook {{ display: inline-block; margin: 8px 0 12px; padding: 8px 10px; color: white; background: var(--green); border-radius: 6px; font-weight: 700; }}
    .source {{ color: var(--muted); font-size: 14px; }}
    .warning {{ margin: 18px 0 0; max-width: 820px; border: 1px solid #f0c9c2; background: #fff2ef; color: #8a3128; border-radius: 8px; padding: 12px 14px; }}
    .warning p {{ margin: 0; }}
    .metric-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 18px 0; }}
    .metric-row div {{ background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    .metric-row b {{ display: block; color: var(--muted); font-size: 13px; font-weight: 500; }}
    .metric-row strong {{ display: block; margin-top: 4px; font-size: 26px; }}
    pre {{ white-space: pre-wrap; background: #101c17; color: #eaf3ee; border-radius: 8px; padding: 14px; overflow-x: auto; }}
  </style>
</head>
<body>
  <header>
    <div class="meta">
      <span class="pill">{html.escape(source_label)}</span>
      <span class="pill">{html.escape(str(playbook.get('category') or '未指定类目'))}</span>
      <span class="pill">{len(plan.get('creative_tests', []))} 个素材实验</span>
    </div>
    <h1>今天先测这几件事</h1>
    <p class="summary">{html.escape(plan.get('executive_summary', ''))}</p>
    {warning_section}
    <div class="decision">
      <div class="ship"><h3>今天上线</h3><ul>{ship}</ul></div>
      <div class="kill"><h3>这些情况就停</h3><ul>{kill}</ul></div>
      <div class="double"><h3>这些信号就加码</h3><ul>{double}</ul></div>
    </div>
  </header>
  <main>
    {learning_section}
    {_card("用户到底卡在哪", f"<table><thead><tr><th>问题</th><th>提到几次</th><th>占比</th><th>原话</th></tr></thead><tbody>{pains}</tbody></table>")}
    {_card("类目手册里已经知道的事", f"<ul class='grid'>{playbook_rules}</ul>" if playbook_rules else "<p>这个类目还没有沉淀规则，先用本次评论跑第一轮。</p>")}
    {_card("别怎么卖，要这么说", f"<ul class='grid'>{angles}</ul>")}
    {_card("今天能发的内容", f"<div class='tests'>{tests}</div>")}
    {_card("销售跟进队列", f"<table><thead><tr><th>优先级</th><th>顾虑</th><th>原话</th><th>怎么回</th><th>负责人</th></tr></thead><tbody>{objection_rows}</tbody></table>" if objection_rows else "<p>没有检测到需要人工跟进的购买顾虑。</p>")}
    {_card("评论和私信怎么回", f"<ul class='grid'>{dm}</ul>")}
    {_card("这一周怎么跑", f"<ol>{days}</ol>")}
  </main>
</body>
</html>
"""
