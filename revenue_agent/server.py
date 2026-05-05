from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from revenue_agent.analyze import fallback_plan, load_product, parse_reviews
from revenue_agent.mimo import MiMoError, call_mimo_json
from revenue_agent.playbook import load_playbook
from revenue_agent.prompts import campaign_prompt
from revenue_agent.render import render_html
from revenue_agent.results import parse_results, summarize_results


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCT = (ROOT / "examples" / "product.json").read_text("utf-8")
DEFAULT_REVIEWS = (ROOT / "examples" / "reviews.csv").read_text("utf-8")
DEFAULT_RESULTS = (ROOT / "examples" / "results.csv").read_text("utf-8")


def build_plan(product_text: str, reviews_text: str, results_text: str, use_mimo: bool) -> dict:
    product = json.loads(product_text)
    reviews = parse_reviews(reviews_text)
    results_summary = summarize_results(parse_results(results_text)) if results_text.strip() else {}
    playbook = load_playbook(product.get("category", "default"))
    local = fallback_plan(product, reviews, playbook, results_summary)
    if not use_mimo:
        return local
    try:
        plan = call_mimo_json(campaign_prompt(product, reviews, local, playbook, results_summary))
        plan.setdefault("source", "mimo")
        plan.setdefault("playbook", playbook)
        if results_summary:
            merged_loop = dict(results_summary)
            merged_loop.update(plan.get("learning_loop") or {})
            merged_loop.setdefault("rows", results_summary.get("rows", []))
            merged_loop.setdefault("totals", results_summary.get("totals", {}))
            plan["learning_loop"] = merged_loop
        return plan
    except (MiMoError, json.JSONDecodeError, KeyError) as exc:
        local["source"] = "local-fallback"
        local.setdefault("warnings", []).append(f"MiMo 不可用，已用本地兜底：{exc}")
        return local


def render_form(error: str = "") -> bytes:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MiMo Commerce Agent</title>
  <style>
    body {{ margin: 0; font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17221d; background: #fbfcfa; }}
    header {{ padding: 36px 6vw 24px; background: #eaf3ee; border-bottom: 1px solid #d6ded9; }}
    main {{ max-width: 1160px; margin: auto; padding: 26px 6vw 60px; }}
    h1 {{ margin: 0 0 10px; font-size: 42px; letter-spacing: 0; }}
    p {{ max-width: 760px; color: #46534e; }}
    form {{ display: grid; grid-template-columns: 1fr; gap: 18px; }}
    label {{ font-weight: 700; }}
    textarea {{ width: 100%; min-height: 190px; padding: 12px; border: 1px solid #cfd8d3; border-radius: 8px; font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace; background: white; }}
    textarea.product {{ min-height: 260px; }}
    .row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 18px; }}
    .panel {{ background: white; border: 1px solid #d6ded9; border-radius: 8px; padding: 16px; }}
    .actions {{ display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }}
    button {{ appearance: none; border: 0; border-radius: 8px; padding: 12px 18px; background: #116b55; color: white; font-weight: 800; cursor: pointer; }}
    .error {{ color: #a84337; background: #fff2ef; border: 1px solid #f0c9c2; border-radius: 8px; padding: 12px; }}
    .hint {{ font-size: 13px; color: #66736e; }}
  </style>
</head>
<body>
  <header>
    <h1>MiMo Commerce Agent</h1>
    <p>把商品信息、评论和投放结果粘进去，生成一张今天能执行的增长面板。默认不调用 MiMo；勾选后会用环境变量里的 MiMo key，key 不会写入页面或文件。</p>
  </header>
  <main>
    {f'<div class="error">{html.escape(error)}</div>' if error else ''}
    <form method="post" action="/generate">
      <div class="panel">
        <label>商品 JSON</label>
        <textarea class="product" name="product">{html.escape(DEFAULT_PRODUCT)}</textarea>
      </div>
      <div class="row">
        <div class="panel">
          <label>评论 CSV</label>
          <textarea name="reviews">{html.escape(DEFAULT_REVIEWS)}</textarea>
        </div>
        <div class="panel">
          <label>实验结果 CSV</label>
          <textarea name="results">{html.escape(DEFAULT_RESULTS)}</textarea>
        </div>
      </div>
      <div class="actions">
        <button type="submit">生成增长面板</button>
        <label><input type="checkbox" name="use_mimo" value="1"> 使用 MiMo 生成文案</label>
        <span class="hint">没有 MiMo 环境变量时会自动 fallback。</span>
      </div>
    </form>
  </main>
</body>
</html>
""".encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self) -> None:
        if self.path in ("/", "/index.html"):
            body = render_form()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send(render_form())
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/generate":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        params = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        product = params.get("product", [""])[0]
        reviews = params.get("reviews", [""])[0]
        results = params.get("results", [""])[0]
        use_mimo = params.get("use_mimo", [""])[0] == "1"
        try:
            self._send(render_html(build_plan(product, reviews, results, use_mimo)).encode("utf-8"))
        except Exception as exc:  # Keep the local demo usable for malformed paste-in data.
            self._send(render_form(str(exc)), status=400)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8788), Handler)
    print("MiMo Commerce Agent running at http://127.0.0.1:8788")
    server.serve_forever()


if __name__ == "__main__":
    main()
