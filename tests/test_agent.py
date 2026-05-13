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
        self.assertIn("objection_queue", plan)
        self.assertGreaterEqual(len(plan["objection_queue"]), 2)
        self.assertIn("reply", plan["objection_queue"][0])
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
            room = Path(tmp) / "demo_room.html"
            objection_csv = Path(tmp) / "objection_queue.csv"
            backlog_csv = Path(tmp) / "experiment_backlog.csv"
            founder = Path(tmp) / "founder_update.md"
            boardroom = Path(tmp) / "boardroom.html"
            self.assertTrue(campaign.exists())
            self.assertTrue(page.exists())
            self.assertTrue(patch.exists())
            self.assertTrue(operator.exists())
            self.assertTrue(investor.exists())
            self.assertTrue(memory.exists())
            self.assertTrue(room.exists())
            self.assertTrue(objection_csv.exists())
            self.assertTrue(backlog_csv.exists())
            self.assertTrue(founder.exists())
            self.assertTrue(boardroom.exists())
            self.assertIn("销售跟进队列", page.read_text("utf-8"))
            csv_body = objection_csv.read_text("utf-8")
            self.assertIn("objection,priority,why_it_blocks_order,evidence,reply,owner", csv_body)
            self.assertIn("客服/私域运营", csv_body)
            backlog_body = backlog_csv.read_text("utf-8")
            self.assertIn("task_type,name,owner,hook,success_metric,next_step", backlog_body)
            self.assertIn("content_test", backlog_body)
            founder_body = founder.read_text("utf-8")
            self.assertIn("Founder Update", founder_body)
            self.assertIn("ROAS", founder_body)
            self.assertIn("Ask", founder_body)
            boardroom_body = boardroom.read_text("utf-8")
            self.assertIn("Boardroom", boardroom_body)
            self.assertIn("Revenue Loop", boardroom_body)
            self.assertIn("Data Moat", boardroom_body)
            self.assertIn("下一轮预算", operator.read_text("utf-8"))
            self.assertIn("Next budget action", investor.read_text("utf-8"))
            self.assertIn("这轮新增记忆", memory.read_text("utf-8"))
            self.assertIn("Data Flywheel", memory.read_text("utf-8"))
            room_body = room.read_text("utf-8")
            self.assertIn("Demo Room", room_body)
            self.assertIn("index.html", room_body)
            self.assertIn("operator_onepager.html", room_body)
            self.assertIn("category_memory.html", room_body)
            self.assertIn("objection_queue.csv", room_body)
            self.assertIn("experiment_backlog.csv", room_body)
            self.assertIn("founder_update.md", room_body)
            self.assertIn("boardroom.html", room_body)
            self.assertIn("建议预算", room_body)
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
