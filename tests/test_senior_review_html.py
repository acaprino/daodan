"""review_html.py renders findings as one standalone page.

Pinned: every finding has an index entry and an anchored article, ordered by
severity; each finding opens with its plain example; a missing field reads `unknown`; an unplaced field is kept; text from a
record is escaped; `--root` adds the cited source line and never reads outside
the root; an input without a findings list fails.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/senior-review/skills/review-consolidation/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import review_html  # noqa: E402

FIXTURE = REPO_ROOT / "benchmarks/flow-model/app"
LOW = {"file": "server/jobs.py", "line": 8, "severity": "Low", "confidence": 60, "premise": "low premise",
       "premise_provenance": "independent", "evidence": "db.find(...)"}
HIGH = {"file": "server/orders.py", "line": 6, "severity": "High", "confidence": 90,
        "premise": "<img src=x onerror=1>", "premise_provenance": "independent", "evidence": "db.get(...)",
        "trigger": "any paid order", "example": "Anna pays order 42 and still sees it unpaid.", "counterevidence_checked": ["no second writer"], "fix": "read by field",
        "lens_votes": {"1": "REAL"}}


class RenderTests(unittest.TestCase):
    def test_index_and_articles_follow_severity(self):
        page = review_html.render([LOW, HIGH], ["web/debug.ts::probe: dynamic route path"])
        self.assertLess(page.index('id="f-01"'), page.index('id="f-02"'))
        self.assertIn('href="#f-01"', page)
        self.assertIn("F-01 · High", page)
        self.assertIn("F-02 · Low", page)
        self.assertIn("dynamic route path", page)
        self.assertIn("2 findings (1 High, 1 Low) · 1 gaps", page)

    def test_record_text_is_escaped(self):
        page = review_html.render([HIGH], [])
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;img src=x onerror=1&gt;", page)

    def test_missing_field_is_unknown_and_unplaced_field_is_kept(self):
        page = review_html.render([LOW, HIGH], [])
        low = page[page.index('id="f-02"'):]
        self.assertIn("<h3>Trigger</h3><p>unknown</p>", low)
        high = page[page.index('id="f-01"'):page.index('id="f-02"')]
        self.assertLess(high.index("Anna pays order 42"), high.index("<h3>Premise</h3>"))
        self.assertIn("<code>lens_votes</code>", page)

    def test_root_adds_the_cited_line_only_inside_the_root(self):
        page = review_html.render([HIGH], [], root=FIXTURE)
        self.assertIn("<mark>   6      document = db.get(&quot;payments&quot;, order_id)</mark>", page)
        outside = review_html.render([{**HIGH, "file": "../expected.json", "line": 1}], [], root=FIXTURE)
        self.assertNotIn("<h3>Source</h3>", outside)


class CommandTests(unittest.TestCase):
    def test_render_reads_both_record_shapes(self):
        with tempfile.TemporaryDirectory() as folder:
            final = Path(folder, "final.json")
            final.write_text(json.dumps({"retained_findings": [HIGH]}), encoding="utf-8")
            result = Path(folder, "result.json")
            result.write_text(json.dumps({"reviewer": "recovery-auditor", "findings": [LOW], "gaps": ["g"]}), encoding="utf-8")
            out = Path(folder, "report.html")
            self.assertEqual(review_html.main(["render", str(final), str(result), "--out", str(out)]), 0)
            page = out.read_text(encoding="utf-8")
            self.assertIn("recovery-auditor", page)
            self.assertIn('id="f-02"', page)

    def test_input_without_findings_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder, "bad.json")
            bad.write_text("{}", encoding="utf-8")
            self.assertEqual(review_html.main(["render", str(bad), "--out", str(Path(folder, "o.html"))]), 1)
            self.assertFalse(Path(folder, "o.html").exists())


if __name__ == "__main__":
    unittest.main()
