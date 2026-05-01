import json
import tempfile
import unittest
from pathlib import Path

from revenue_agent.analyze import fallback_plan, load_product, load_reviews
from revenue_agent.render import write_outputs


class AgentTest(unittest.TestCase):
    def test_fallback_plan_has_revenue_actions(self):
        product = load_product("examples/product.json")
        reviews = load_reviews("examples/reviews.csv")
        plan = fallback_plan(product, reviews)
        self.assertGreaterEqual(len(plan["pain_map"]), 2)
        self.assertGreaterEqual(len(plan["creative_tests"]), 2)
        self.assertIn("landing_page_copy", plan)
        self.assertIn("dm_scripts", plan)

    def test_render_outputs(self):
        product = load_product("examples/product.json")
        reviews = load_reviews("examples/reviews.csv")
        plan = fallback_plan(product, reviews)
        with tempfile.TemporaryDirectory() as tmp:
            write_outputs(plan, tmp)
            campaign = Path(tmp) / "campaign.json"
            page = Path(tmp) / "index.html"
            self.assertTrue(campaign.exists())
            self.assertTrue(page.exists())
            self.assertEqual(json.loads(campaign.read_text("utf-8"))["source"], "local-fallback")


if __name__ == "__main__":
    unittest.main()

