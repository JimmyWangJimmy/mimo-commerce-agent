from __future__ import annotations

import html
import json
from pathlib import Path


def write_outputs(plan: dict, out_dir: str | Path) -> None:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "campaign.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (target / "index.html").write_text(render_html(plan), "utf-8")
    (target / "brief.md").write_text(render_markdown(plan), "utf-8")


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
    return "\n".join(lines) + "\n"


def _card(title: str, body: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2>{body}</section>"


def render_html(plan: dict) -> str:
    board = plan.get("decision_board") or {}
    playbook = plan.get("playbook") or {}
    source_label = "MiMo 生成" if plan.get("source") == "mimo" else "本地兜底"
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
    <div class="decision">
      <div class="ship"><h3>今天上线</h3><ul>{ship}</ul></div>
      <div class="kill"><h3>这些情况就停</h3><ul>{kill}</ul></div>
      <div class="double"><h3>这些信号就加码</h3><ul>{double}</ul></div>
    </div>
  </header>
  <main>
    {_card("用户到底卡在哪", f"<table><thead><tr><th>问题</th><th>提到几次</th><th>占比</th><th>原话</th></tr></thead><tbody>{pains}</tbody></table>")}
    {_card("类目手册里已经知道的事", f"<ul class='grid'>{playbook_rules}</ul>" if playbook_rules else "<p>这个类目还没有沉淀规则，先用本次评论跑第一轮。</p>")}
    {_card("别怎么卖，要这么说", f"<ul class='grid'>{angles}</ul>")}
    {_card("今天能发的内容", f"<div class='tests'>{tests}</div>")}
    {_card("评论和私信怎么回", f"<ul class='grid'>{dm}</ul>")}
    {_card("这一周怎么跑", f"<ol>{days}</ol>")}
  </main>
</body>
</html>
"""
