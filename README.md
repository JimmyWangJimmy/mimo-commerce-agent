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

The model call uses Xiaomi MiMo Token Plan when `MIMO_API_KEY` and `MIMO_BASE_URL` are set. The repo keeps secrets out of disk and falls back to a deterministic local planner when credentials are missing.

## Quick Start

```bash
python3 -m revenue_agent.cli \
  --product examples/product.json \
  --reviews examples/reviews.csv \
  --out output/demo
```

With MiMo Token Plan:

```bash
export MIMO_API_KEY="tp-..."
export MIMO_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"

python3 -m revenue_agent.cli \
  --product examples/product.json \
  --reviews examples/reviews.csv \
  --out output/mimo-demo \
  --use-mimo
```

Open `output/demo/index.html` or `output/mimo-demo/index.html` after running.

## Product Thesis

Most AI content tools stop at copy. Commerce operators need actions tied to revenue:

```text
reviews -> pain points -> offer angles -> creative tests -> DM/support scripts -> next experiments
```

This repo is the first slice of a larger agentic commerce OS.

## Environment

- Python 3.11+
- No required third-party packages
- Optional MiMo API:
  - `MIMO_API_KEY`
  - `MIMO_BASE_URL`

