# Demo Report Snapshot

Generated from `examples/product.json` and `examples/reviews.csv`.

```text
Core hypothesis:
Use ingredient-list proof plus a low-risk trial offer to move sugar-conscious buyers from "afraid of being misled" to "worth trying."
```

Run locally to reproduce:

```bash
python3 -m revenue_agent.cli \
  --product examples/product.json \
  --reviews examples/reviews.csv \
  --out output/demo
```

Run with MiMo:

```bash
export MIMO_API_KEY="tp-..."
export MIMO_BASE_URL="https://token-plan-cn.xiaomimimo.com/v1"
python3 -m revenue_agent.cli \
  --product examples/product.json \
  --reviews examples/reviews.csv \
  --out output/mimo-demo \
  --use-mimo
```

