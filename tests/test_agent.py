import json
import tempfile
import unittest
from pathlib import Path

from revenue_agent.analyze import fallback_plan, load_product, load_reviews
from revenue_agent.playbook import apply_playbook_patch, build_playbook_patch, load_playbook
from revenue_agent.render import write_outputs
from revenue_agent.results import load_results, parse_results, summarize_results
from revenue_agent.server import build_plan
from revenue_agent.server import render_form


class AgentTest(unittest.TestCase):
    def test_fallback_plan_has_revenue_actions(self):
        product = load_product("examples/product.json")
        reviews = load_reviews("examples/reviews.csv")
        playbook = load_playbook(product["category"])
        plan = fallback_plan(product, reviews, playbook)
        self.assertGreaterEqual(len(plan["pain_map"]), 2)
        self.assertGreaterEqual(len(plan["creative_tests"]), 2)
        self.assertIn("landing_page_copy", plan)
        self.assertIn("dm_scripts", plan)
        self.assertIn("decision_board", plan)
        self.assertEqual(plan["playbook"]["category"], "ready-to-drink tea")

    def test_render_outputs(self):
        product = load_product("examples/product.json")
        reviews = load_reviews("examples/reviews.csv")
        results = summarize_results(load_results("examples/results.csv"))
        playbook = load_playbook(product["category"])
        plan = fallback_plan(product, reviews, playbook, results)
        with tempfile.TemporaryDirectory() as tmp:
            write_outputs(plan, tmp)
            campaign = Path(tmp) / "campaign.json"
            page = Path(tmp) / "index.html"
            patch = Path(tmp) / "playbook_patch.json"
            operator = Path(tmp) / "operator_onepager.html"
            investor = Path(tmp) / "investor_onepager.md"
            memory = Path(tmp) / "category_memory.html"
            self.assertTrue(campaign.exists())
            self.assertTrue(page.exists())
            self.assertTrue(patch.exists())
            self.assertTrue(operator.exists())
            self.assertTrue(investor.exists())
            self.assertTrue(memory.exists())
            self.assertIn("下一轮预算", operator.read_text("utf-8"))
            self.assertIn("Next budget action", investor.read_text("utf-8"))
            self.assertIn("这轮新增记忆", memory.read_text("utf-8"))
            self.assertIn("Data Flywheel", memory.read_text("utf-8"))
            self.assertEqual(json.loads(campaign.read_text("utf-8"))["source"], "local-fallback")

    def test_build_playbook_patch(self):
        product = load_product("examples/product.json")
        reviews = load_reviews("examples/reviews.csv")
        results = summarize_results(load_results("examples/results.csv"))
        plan = fallback_plan(product, reviews, load_playbook(product["category"]), results)
        patch = build_playbook_patch(plan)
        self.assertEqual(patch["category"], "ready-to-drink tea")
        self.assertIn("learned_rule", patch)

    def test_apply_playbook_patch(self):
        product = load_product("examples/product.json")
        reviews = load_reviews("examples/reviews.csv")
        results = summarize_results(load_results("examples/results.csv"))
        plan = fallback_plan(product, reviews, load_playbook(product["category"]), results)
        patch = build_playbook_patch(plan)
        with tempfile.TemporaryDirectory() as tmp:
            path, playbook = apply_playbook_patch(patch, str(Path(tmp) / "tea.json"))
            self.assertTrue(path.exists())
            self.assertTrue(playbook["learning_log"])
            self.assertIn(patch["learned_rule"], playbook["winning_patterns"])

    def test_results_summary_ranks_experiments(self):
        summary = summarize_results(load_results("examples/results.csv"))
        self.assertEqual(summary["winner"]["experiment"], "配料表翻瓶挑战")
        self.assertGreater(summary["totals"]["roas"], 1)
        self.assertEqual(summary["commercial_signal"]["action"], "加码")
        self.assertGreater(summary["commercial_signal"]["recommended_budget"], 0)
        self.assertIn("playbook_update", summary)

    def test_parse_results_from_text(self):
        text = "experiment,channel,hook,impressions,views,saves,clicks,dms,orders,spend,revenue\nA,抖音,h,100,80,8,4,2,1,10,30\n"
        rows = parse_results(text)
        self.assertEqual(rows[0]["orders"], 1)

    def test_server_build_plan_without_mimo(self):
        product = Path("examples/product.json").read_text("utf-8")
        reviews = Path("examples/reviews.csv").read_text("utf-8")
        results = Path("examples/results.csv").read_text("utf-8")
        plan = build_plan(product, reviews, results, use_mimo=False)
        self.assertEqual(plan["source"], "local-fallback")
        self.assertIn("learning_loop", plan)

    def test_server_form_renders_mimo_toggle(self):
        body = render_form().decode("utf-8")
        self.assertIn("使用 MiMo 生成文案", body)


if __name__ == "__main__":
    unittest.main()
