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
SCRIPTS = REPO_ROOT / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import review_roster  # noqa: E402


def diff_of(path):
    return (f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n"
            "@@ -1,2 +1,2 @@\n-x = 1\n+x = 2\n")


# Go has no specialist of its own: the roster of these is the rigor's alone.
PLAIN = diff_of("app/orders/pricing.go")
SENSITIVE = diff_of("app/payments/gateway.go")


SNAPSHOT = {"root": "/project", "target": "."}
BOUND = {"candidate": dict(SNAPSHOT)}


def compute(diff=PLAIN, shape="branch", kind="changeset", **extra):
    deeper = extra.pop("deeper", False)
    return review_roster.compute(shape, diff, None, None, deeper, kind, "r1", "standalone", **extra)


MAPPED = {"root": "/project", "target": ".", "created_at": "2026-11-20T00:00:00Z", "parser_fingerprint": "p1",
          "repo_revision": None}
MANIFEST = "/project/.map/snapshot.sqlite"


def mapped(changed, imports, neighbour=None, *, language="python", manifest=MANIFEST, bound=True):
    """A branch roster of one changed file of a unit that declares Stripe, with a bound map whose changed symbol
    calls into `neighbour`. `imports` maps a path to its imports in `snapshot.py files`; None as a value is a file
    without a parser, None as the whole is no inventory at all."""
    before = {"body_hash": "b1", "interface_hash": "i1", "effects_hash": "e1"}
    after = {**before, "body_hash": "b2"}
    symbol = f"{changed}::run"
    impact = {"schema": "daodan/edit-impact/v2", "root": "/project", "target": ".", "targets": [{
        "symbol_id": symbol, "file": changed, "start": 1, "end": 2, **after, "callers": {"total": 0, "listed": []},
        "callees": {"total": 1 if neighbour else 0, "listed": [{"file": neighbour}] if neighbour else []}}]}
    delta = {"schema": "daodan/stale-callers/v1", "base": MAPPED, "candidate": MAPPED, "changed": [
        {"symbol_id": symbol, "file": changed, "change_kind": "body_only", "old": before, "new": after}]}
    context = {"candidate": MAPPED, "base": MAPPED, "stale_callers": delta}
    technologies = {**SNAPSHOT, "manifest": MANIFEST, "units": [{"paths": ["."], "technologies": ["stripe"]}]}
    files = None if imports is None else {"schema": "codebase-map/files/v1", "manifest": manifest, "files": [
        {"path": path, "language": None if found is None else language,
         "status": "file-level" if found is None else "parsed", "imports": found or []}
        for path, found in imports.items()]}
    return review_roster.compute("branch", diff_of(changed), None, impact if bound else None, False, "changeset",
                                 "r1", "standalone", context=context, technologies=technologies, files=files)


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

    def test_a_technology_of_the_files_build_unit_adds_its_specialist(self):
        technologies = {**SNAPSHOT, "units": [{"paths": ["."], "technologies": ["react"]},
                                  {"paths": ["desktop"], "technologies": ["tauri"]},
                                  {"paths": ["api"], "technologies": ["fastapi"]}]}
        shell = compute(diff_of("desktop/ui/state.ts"), technologies=technologies, context=BOUND)
        self.assertEqual(shell["signals"]["technologies"], ["tauri"])
        self.assertIn("senior-review:tauri-auditor", shell["roster"])
        self.assertNotIn("senior-review:react-auditor", shell["roster"])
        self.assertIn("senior-review:react-auditor", compute(diff_of("web/hooks.ts"), technologies=technologies, context=BOUND)["roster"])
        api = compute(diff_of("api/routes.go"), technologies=technologies, context=BOUND)
        self.assertEqual((api["signals"]["technologies"], api["roster"]), (["fastapi"], review_roster.STANDARD_ROSTER))
        self.assertEqual(compute(diff_of("web/hooks.ts"))["signals"]["technologies"], [])
        other = compute(diff_of("desktop/ui/state.ts"), technologies={**technologies, "root": "/elsewhere"}, context=BOUND)
        self.assertEqual(other["signals"]["technologies"], [])
        self.assertIn("technologies record is not of the candidate snapshot", " ".join(other["gaps"]))

    def test_python_and_stripe_add_their_specialists(self):
        python = compute(diff_of("app/orders/pricing.py"))
        self.assertEqual(python["roster"], review_roster.STANDARD_ROSTER + ["senior-review:python-auditor"])
        hook = compute(diff_of("api/hooks.go").replace("+x = 2", "+event = stripe.Webhook.construct_event(body, sig, key)"))
        self.assertIn("senior-review:stripe-auditor", hook["roster"])
        units = {**SNAPSHOT, "units": [{"paths": ["."], "technologies": ["stripe"]}]}
        self.assertIn("senior-review:stripe-auditor", compute(technologies=units, context=BOUND)["roster"])
        for text in ("+.row.stripe { background: #eee }", "+// zebra stripe rows", "+Add a Stripe section to the page"):
            plain = compute(diff_of("web/table.go").replace("+x = 2", text))
            self.assertNotIn("senior-review:stripe-auditor", plain["roster"], text)

    def test_a_declared_library_needs_a_file_of_the_change_that_imports_it(self):
        def run(imports, neighbour=None, **kwargs):
            return mapped("app/billing.py", imports, neighbour, **kwargs)

        unused = run({"app/billing.py": ["app.integrations.stripe.service", "decimal"]})
        self.assertNotIn("senior-review:stripe-auditor", unused["roster"])
        self.assertEqual(unused["signals"]["technologies"], ["stripe"])
        self.assertEqual(unused["signals"]["suppressed"], [{
            "technology": "stripe", "role": "senior-review:stripe-auditor", "checked": ["app/billing.py"],
            "reason": "no changed file nor one-hop neighbour of the bound map imports it"}])
        self.assertIn("senior-review:stripe-auditor", run({"app/billing.py": ["stripe"]})["roster"])
        helper = run({"app/billing.py": ["app.payments"], "app/payments.py": ["stripe.error"]}, "app/payments.py")
        self.assertIn("senior-review:stripe-auditor", helper["roster"])
        self.assertEqual(helper["signals"]["suppressed"], [])
        script = mapped("web/pay.tsx", {"web/pay.tsx": ["@stripe/stripe-js"]}, language="typescript")
        self.assertIn("senior-review:stripe-auditor", script["roster"])

    def test_a_declared_library_keeps_its_specialist_when_its_use_is_unknown(self):
        unknown = {
            "no inventory": mapped("app/billing.py", None),
            "another snapshot": mapped("app/billing.py", {"app/billing.py": []}, manifest="/elsewhere.sqlite"),
            "no bound map": mapped("app/billing.py", {"app/billing.py": []}, bound=False),
            "a neighbour without imports": mapped("app/billing.py", {"app/billing.py": [], "app/hooks.rb": None},
                                                  "app/hooks.rb"),
        }
        for name, roster in unknown.items():
            self.assertIn("senior-review:stripe-auditor", roster["roster"], name)
            self.assertEqual(roster["signals"]["suppressed"], [], name)
            self.assertTrue(any(gap.startswith("stripe:") for gap in roster["gaps"]), name)

    def test_a_tauri_test_or_workspace_path_adds_its_specialist(self):
        tauri = compute(diff_of("src-tauri/src/commands.rs"))
        self.assertIn("senior-review:tauri-auditor", tauri["roster"])
        self.assertTrue(tauri["signals"]["content"]["tauri"])
        self.assertIn("senior-review:tauri-auditor", compute(diff_of("src/App.tsx").replace("+x = 2", "+import { invoke } from '@tauri-apps/api/core'"))["roster"])
        testing = compute(diff_of("tests/test_pricing.py"))
        self.assertIn("senior-review:testing-auditor", testing["roster"])
        self.assertNotIn("senior-review:tauri-auditor", testing["roster"])
        self.assertIn("senior-review:workspace-hygiene-auditor", compute(diff_of(".gitignore"))["roster"])
        self.assertIn("senior-review:workspace-hygiene-auditor", compute(diff_of("dist/app.js"))["roster"])
        self.assertIn("senior-review:workspace-hygiene-auditor",
                      compute(PLAIN.replace("+x = 2", "+<<<<<<< HEAD"))["roster"])
        self.assertEqual(compute()["roster"], review_roster.STANDARD_ROSTER)

    def test_deep_adds_testing_and_prior_art(self):
        deep = compute(rigor="deep")["roster"]
        self.assertIn("senior-review:testing-auditor", deep)
        self.assertIn("senior-review:prior-art-auditor", deep)
        self.assertNotIn("senior-review:testing-auditor", compute()["roster"])

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
