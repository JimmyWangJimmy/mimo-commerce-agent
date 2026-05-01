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
        "# Revenue Action Pack",
        "",
        f"Source: `{plan.get('source', 'unknown')}`",
        "",
        "## Executive Summary",
        "",
        plan.get("executive_summary", ""),
        "",
        "## Creative Tests",
    ]
    for test in plan.get("creative_tests", []):
        lines.extend(
            [
                "",
                f"### {test.get('name', 'Untitled')}",
                "",
                f"- Hypothesis: {test.get('hypothesis', '')}",
                f"- Hook: {test.get('hook', '')}",
                f"- Success metric: {test.get('success_metric', '')}",
                "",
                "Script:",
            ]
        )
        for line in test.get("script", []):
            lines.append(f"- {line}")
    lines.extend(["", "## Seven Day Plan"])
    for item in plan.get("seven_day_plan", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _card(title: str, body: str) -> str:
    return f"<section><h2>{html.escape(title)}</h2>{body}</section>"


def render_html(plan: dict) -> str:
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
          <p><b>Hypothesis:</b> {html.escape(test.get('hypothesis', ''))}</p>
          <p class="hook">{html.escape(test.get('hook', ''))}</p>
          <ol>{''.join(f'<li>{html.escape(str(line))}</li>' for line in test.get('script', []))}</ol>
          <p><b>Metric:</b> {html.escape(test.get('success_metric', ''))}</p>
        </article>
        """
        for test in plan.get("creative_tests", [])
    )
    dm = "".join(
        f"<li><b>{html.escape(item.get('trigger', ''))}</b><br>{html.escape(item.get('reply', ''))}</li>"
        for item in plan.get("dm_scripts", [])
    )
    days = "".join(f"<li>{html.escape(str(day))}</li>" for day in plan.get("seven_day_plan", []))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Revenue Action Pack</title>
  <style>
    :root {{ color-scheme: light; --ink:#18201c; --muted:#65706b; --line:#d9dfdc; --green:#0f7b5f; --amber:#f3ba4d; --paper:#fbfcfa; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--paper); }}
    header {{ padding: 48px 6vw 32px; background: #eaf3ee; border-bottom: 1px solid var(--line); }}
    main {{ padding: 28px 6vw 60px; max-width: 1180px; margin: auto; }}
    h1 {{ margin: 0 0 12px; font-size: clamp(32px, 5vw, 64px); line-height: 1.02; letter-spacing: 0; }}
    h2 {{ margin: 0 0 16px; font-size: 24px; }}
    h3 {{ margin: 0 0 10px; font-size: 20px; }}
    section {{ padding: 28px 0; border-bottom: 1px solid var(--line); }}
    .summary {{ max-width: 780px; font-size: 20px; color: #26332d; }}
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
    <div class="source">Source: {html.escape(plan.get('source', 'unknown'))}</div>
    <h1>Revenue Action Pack</h1>
    <p class="summary">{html.escape(plan.get('executive_summary', ''))}</p>
  </header>
  <main>
    {_card("Pain Map", f"<table><thead><tr><th>Pain</th><th>Mentions</th><th>Share</th><th>Evidence</th></tr></thead><tbody>{pains}</tbody></table>")}
    {_card("Positioning Angles", f"<ul class='grid'>{angles}</ul>")}
    {_card("Creative Tests", f"<div class='tests'>{tests}</div>")}
    {_card("DM Scripts", f"<ul class='grid'>{dm}</ul>")}
    {_card("Seven Day Plan", f"<ol>{days}</ol>")}
  </main>
</body>
</html>
"""

