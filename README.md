# MiMo Commerce Agent

MiMo Commerce Agent turns customer feedback into revenue actions.

It is a narrow wedge for commerce teams: ingest product context, reviews, and competitor notes, then generate a campaign experiment pack:

- customer pain map
- positioning angles
- short-video hooks and scripts
- creator brief
- landing-page copy
- DM and support conversion scripts
- seven-day growth experiment plan
- decision board for what to ship, kill, or double down on
- commercial signal for next budget, expected orders, AOV, and CAC
- category playbook memory for reusable channel/category rules

The model call uses Xiaomi MiMo Token Plan when `MIMO_API_KEY` and `MIMO_BASE_URL` are set. The repo keeps secrets out of disk and falls back to a deterministic local planner when credentials are missing.

## Quick Start

```bash
python3 -m revenue_agent.cli \
  --product examples/product.json \
  --reviews examples/reviews.csv \
  --results examples/results.csv \
  --out output/demo
```

With MiMo Token Plan:

```bash
export MIMO_API_KEY="tp-..."
export MIMO_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"

python3 -m revenue_agent.cli \
  --product examples/product.json \
  --reviews examples/reviews.csv \
  --results examples/results.csv \
  --out output/mimo-demo \
  --use-mimo
```

Open `output/demo/index.html` or `output/mimo-demo/index.html` after running.

Each run writes:

- `index.html`: full operator dashboard
- `operator_onepager.html`: compact shareable execution memo
- `investor_onepager.md`: product/VC one-pager
- `playbook_patch.json`: category memory patch

Or serve the generated report locally:

```bash
python3 -m http.server 8787 --directory output/mimo-demo
```

Then open `http://127.0.0.1:8787/index.html`.

## Interactive Local Demo

Run the zero-dependency local web app:

```bash
python3 -m revenue_agent.server
```

Then open `http://127.0.0.1:8788`.

The app lets you paste product JSON, review CSV, and campaign result CSV, then generates the dashboard in the browser. Checking "使用 MiMo 生成文案" uses `MIMO_API_KEY` and `MIMO_BASE_URL` from the current shell only; secrets are not written to disk.

## Applying Learning Back To A Playbook

Generated reports include `playbook_patch.json` when experiment results are present. Apply that patch back into the category playbook:

```bash
python3 -m revenue_agent.playbook_cli output/demo/playbook_patch.json
```

This appends learned rules, winning hooks, bad patterns, next experiments, and a timestamped learning log.

## Product Thesis

Most AI content tools stop at copy. Commerce operators need actions tied to revenue:

```text
reviews -> pain points -> offer angles -> creative tests -> DM/support scripts -> next experiments
```

With experiment results attached, the loop becomes:

```text
campaign results -> winner/loser -> budget action -> next bet -> category playbook update
```

This repo is the first slice of a larger agentic commerce OS.

## Category Playbooks

Playbooks live under `playbooks/`. The CLI automatically loads a playbook whose filename matches the product category slug. For example:

```text
category: ready-to-drink tea
playbook: playbooks/ready-to-drink-tea.json
```

The point is to avoid starting from a blank prompt every time. Each category can remember common objections, winning content patterns, bad patterns, and the metrics that matter.

## Environment

- Python 3.11+
- No required third-party packages
- Optional MiMo API:
  - `MIMO_API_KEY`
  - `MIMO_BASE_URL`
