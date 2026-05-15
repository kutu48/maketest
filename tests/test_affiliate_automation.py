import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

import affiliate_automation as aa


class TestAffiliateAutomation(unittest.TestCase):
    def test_trending_keywords(self):
        trends = aa.get_trending_keywords_id(5)
        self.assertEqual(len(trends), 5)

    def test_auto_generate_backsound(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "audio"
            picks = aa.choose_backsounds(d, 4, auto_generate=True)
            self.assertEqual(len(picks), 4)
            self.assertTrue(all(p.exists() for p in picks))

    def test_content_and_queue(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            hooks = ["hook1", "hook2"]
            caps = ["cap1", "cap2"]
            trends = ["trend1"]
            aa.build_content_plan(out / "content_plan.csv", hooks, caps, trends)
            self.assertTrue((out / "content_plan.csv").exists())

            queue = aa.build_autopost_queue(
                out / "q.json",
                [datetime(2026, 5, 15, 0, 0, tzinfo=UTC)],
                [Path("videos/1.mp4")],
                ["caption"],
                ["facebook_page", "facebook_group", "tiktok", "instagram"],
            )
            self.assertIn("posts", queue)
            payload = json.loads((out / "q.json").read_text(encoding="utf-8"))
            self.assertTrue(payload["posts"][0]["targets"]["facebook_group"])


if __name__ == "__main__":
    unittest.main()
