"""review_roster.py computes a rigor: quick, standard or deep.

The model reads the request and passes the rigor; the helper matches no words. Pinned:
the default is standard; size alone never raises it; a risk signal forces deep and
nothing lowers it; deeper raises one level; quick, standard and deep set the
verification level; only a deep branch review has the critic; light caps at standard.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "plugins/senior-review/skills/review-preparation/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import review_roster  # noqa: E402


def diff_of(path):
    return (f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
            "@@ -1,2 +1,2 @@\n-x = 1\n+x = 2\n")


PLAIN = diff_of("app/orders/pricing.py")
SENSITIVE = diff_of("app/payments/gateway.py")


def compute(diff=PLAIN, shape="branch", kind="changeset", **extra):
    deeper = extra.pop("deeper", False)
    return review_roster.compute(shape, diff, None, None, deeper, kind, "r1", "standalone", **extra)


class RigorTest(unittest.TestCase):
    def test_default_is_standard_and_the_field_is_rigor(self):
        roster = compute()
        self.assertEqual(roster["rigor"], "standard")
        self.assertNotIn("tier", roster)
        self.assertEqual(roster["verification"], "critical-high")
        self.assertFalse(roster["critic"])
        self.assertEqual(roster["roster"], review_roster.STANDARD_ROSTER)

    def test_size_alone_does_not_raise_it(self):
        paths = [f"{top}/mod{i}.py" for top in ("alpha", "beta", "gamma") for i in range(3)]
        roster = compute(shape="branch", context={"review_basis": "content", "conclusion_paths": paths})
        self.assertEqual(len(roster["signals"]["modules"]), 3)
        self.assertEqual(roster["signals"]["production_files"], 9)
        self.assertEqual(roster["rigor"], "standard")

    def test_the_three_rigors_set_verification_and_critic(self):
        quick, standard, deep = (compute(rigor=r) for r in ("quick", "standard", "deep"))
        self.assertEqual([quick["verification"], standard["verification"], deep["verification"]],
                         ["critical", "critical-high", "all-above-floor"])
        self.assertEqual([quick["critic"], standard["critic"], deep["critic"]], [False, False, True])
        self.assertEqual(deep["roster"][:len(review_roster.DEEP_ROSTER)], review_roster.DEEP_ROSTER)
        self.assertEqual(quick["roster"], review_roster.STANDARD_ROSTER)

    def test_a_risk_signal_forces_deep_even_when_quick_was_asked(self):
        roster = compute(SENSITIVE, rigor="quick")
        self.assertEqual(roster["rigor"], "deep")
        self.assertTrue(roster["critic"])
        self.assertTrue(any("override the requested quick" in reason for reason in roster["reasons"]))
        self.assertTrue(any("sensitive paths" in reason for reason in roster["reasons"]))

    def test_deeper_raises_one_level(self):
        self.assertEqual(compute(deeper=True)["rigor"], "deep")
        self.assertEqual(compute(rigor="quick", deeper=True)["rigor"], "standard")
        self.assertEqual(compute(rigor="deep", deeper=True)["rigor"], "deep")

    def test_an_unknown_rigor_is_an_error(self):
        with self.assertRaises(ValueError):
            compute(rigor="medium")

    def test_light_has_one_reviewer_and_caps_at_standard(self):
        roster = compute(shape="light", rigor="deep")
        self.assertEqual(roster["rigor"], "standard")
        self.assertFalse(roster["critic"])
        self.assertEqual(roster["roster"], ["senior-review:code-auditor"])
        self.assertTrue(any("review-branch" in line for line in roster["advice"]))
        self.assertEqual(compute(shape="light", rigor="quick")["verification"], "critical")

    def test_a_document_keeps_its_fixed_set_at_any_rigor(self):
        deep = compute(kind="spec", rigor="deep", context={"review_basis": "claims"})
        standard = compute(kind="spec", context={"review_basis": "claims"})
        self.assertEqual(deep["roster"], standard["roster"])
        self.assertEqual(deep["verification"], "all-above-floor")

    def test_check_refuses_a_critic_outside_a_deep_review(self):
        roster = compute()
        self.assertTrue(review_roster.check(roster, {"roles": [], "critic": True}))
        self.assertEqual(review_roster.check(compute(rigor="deep"), {"roles": [], "critic": True}), [])

    def test_cli_takes_the_rigor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "d.patch").write_text(PLAIN, encoding="utf-8")
            code = review_roster.main(["compute", "--shape", "branch", "--diff", str(root / "d.patch"),
                                       "--rigor", "deep", "--out", str(root / "r.json")])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads((root / "r.json").read_text(encoding="utf-8"))["rigor"], "deep")


if __name__ == "__main__":
    unittest.main()
