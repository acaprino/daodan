"""composition.py binds a computed roster into jobs made of focused role files.

Pinned behaviours: the catalog is derived from plugin.toml and readable by
review_roster.py; a composition expands to leaf roles without copying prose;
digests are stable and change with a role file; uncovered required specialists
get their own job except in light, which folds them into its single job; an
identity absent from the catalog leaves the job unbound and the exit non-zero;
a cycle, a foreign candidate or a second light job is an error. A branch bind
states its selection: the reviewers Phase 1 chose replace the automatic roster and
its floor, source obligations stay, and a dispatch validates against that result.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins/senior-review"
SCRIPTS = PLUGIN_ROOT / "skills/review-preparation/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import composition  # noqa: E402
import review_roster  # noqa: E402

CANDIDATE = {"ref": "abc123", "snapshot": "snap-1"}


def roster(roles, shape="branch", required=(), scope_id="candidate"):
    return {
        "schema": composition.ROSTER_SCHEMA, "shape": shape, "roster": list(roles),
        "support": ["senior-review:premise-auditor"], "required_specialists": list(required),
        "jobs": [], "grounding": {"scope_id": scope_id, "candidate": CANDIDATE}, "gaps": [],
    }


BINDINGS = {"candidate": CANDIDATE, "knowledge_selection": "", "output_dir": ".team-review/jobs", "selection": "automatic"}


class CatalogTest(unittest.TestCase):
    def test_catalog_matches_plugin_toml_and_feeds_review_roster(self):
        catalog = composition.load_catalog(PLUGIN_ROOT)
        entries = {row["id"]: row for row in catalog["entries"]}
        self.assertEqual(len(entries), 62)
        self.assertEqual(entries["senior-review:accessibility-auditor"]["members"],
                         ["senior-review:accessible-navigation-auditor", "senior-review:accessible-perception-auditor"])
        self.assertEqual(entries["senior-review:authorization-auditor"]["file"], "roles/authorization-auditor.md")
        for row in entries.values():
            if row["kind"] == "role":
                self.assertTrue((PLUGIN_ROOT / row["file"]).is_file(), row["id"])
        obligations = review_roster.specialist_obligations(
            ["senior-review:accessibility-auditor"], {"catalog": catalog, "candidate": CANDIDATE}, "s", 
            {"changed": []}, [])
        self.assertEqual([o["specialist_id"] for o in obligations],
                         ["senior-review:accessible-navigation-auditor", "senior-review:accessible-perception-auditor"])


class BindTest(unittest.TestCase):
    def test_composition_expands_to_leaf_roles_with_hashes_only(self):
        prepared = composition.bind(roster(["senior-review:code-auditor"]), BINDINGS, PLUGIN_ROOT)
        self.assertEqual(len(prepared["jobs"]), 1)
        job = prepared["jobs"][0]
        self.assertEqual(job["status"], "bound")
        self.assertEqual(len(job["specialist_ids"]), 27)
        self.assertNotIn("senior-review:security-auditor", job["specialist_ids"])
        self.assertIn("senior-review:authorization-auditor", job["specialist_ids"])
        self.assertEqual(set(job["source_bindings"]), set(job["specialist_ids"]))
        self.assertEqual(job["output_path"], ".team-review/jobs/job-01.md")
        self.assertEqual(prepared["common"]["path"], composition.COMMON.as_posix())
        text = json.dumps(prepared)
        self.assertNotIn("Causal checks", text)
        self.assertNotIn("Mandate", text)

    def test_digest_is_stable_and_tracks_role_content(self):
        first = composition.bind(roster(["senior-review:accessibility-auditor"]), BINDINGS, PLUGIN_ROOT)
        second = composition.bind(roster(["senior-review:accessibility-auditor"]), BINDINGS, PLUGIN_ROOT)
        self.assertEqual(first["jobs"][0]["body_sha256"], second["jobs"][0]["body_sha256"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "roles").mkdir()
            (root / composition.COMMON).parent.mkdir(parents=True)
            (root / composition.COMMON).write_text("common\n", encoding="utf-8")
            (root / "plugin.toml").write_text(
                'name = "senior-review"\n[components]\nroles = ["a", "b", "pair"]\n'
                '[reviewers.compositions.pair]\nmembers = ["senior-review:a", "senior-review:b"]\n', encoding="utf-8")
            (root / "roles/a.md").write_text("A\n", encoding="utf-8")
            (root / "roles/b.md").write_text("B\n", encoding="utf-8")
            before = composition.bind(roster(["senior-review:pair"]), BINDINGS, root)["jobs"][0]["body_sha256"]
            (root / "roles/b.md").write_text("B changed\n", encoding="utf-8")
            after = composition.bind(roster(["senior-review:pair"]), BINDINGS, root)["jobs"][0]["body_sha256"]
        self.assertNotEqual(before, after)

    def test_required_specialists_uncovered_get_their_own_job(self):
        required = [{"specialist_id": "senior-review:accessibility-auditor", "scope_id": "candidate", "evidence": ["x"]},
                    {"specialist_id": "senior-review:authorization-auditor", "scope_id": "candidate", "evidence": ["x"]}]
        prepared = composition.bind(roster(["senior-review:security-auditor"], required=required), BINDINGS, PLUGIN_ROOT)
        roles = [job["role"] for job in prepared["jobs"]]
        self.assertEqual(roles, ["senior-review:security-auditor", "senior-review:accessibility-auditor"])
        self.assertEqual([job["job_id"] for job in prepared["jobs"]], ["job-01", "job-02"])

    def test_light_folds_required_specialists_into_its_single_job(self):
        required = [{"specialist_id": "senior-review:ui-race-auditor", "scope_id": "candidate", "evidence": ["x"]}]
        prepared = composition.bind(roster(["senior-review:code-auditor"], shape="light", required=required), BINDINGS, PLUGIN_ROOT)
        self.assertEqual(len(prepared["jobs"]), 1)
        self.assertIn("senior-review:ui-race-auditor", prepared["jobs"][0]["specialist_ids"])

    def test_light_with_two_roster_roles_is_an_error(self):
        with self.assertRaises(ValueError):
            composition.bind(roster(["senior-review:code-auditor", "senior-review:ui-race-auditor"], shape="light"),
                             BINDINGS, PLUGIN_ROOT)

    def test_unknown_identity_leaves_job_unbound_with_gap(self):
        prepared = composition.bind(roster(["senior-review:security-auditor", "nobody:test-auditor"]), BINDINGS, PLUGIN_ROOT)
        statuses = {job["role"]: job["status"] for job in prepared["jobs"]}
        self.assertEqual(statuses["nobody:test-auditor"], "unbound")
        self.assertEqual(statuses["senior-review:security-auditor"], "bound")
        self.assertTrue(any("nobody:test-auditor" in gap for gap in prepared["gaps"]))

    def test_candidate_mismatch_and_cycle_are_errors(self):
        with self.assertRaises(ValueError):
            composition.bind(roster(["senior-review:code-auditor"]), {**BINDINGS, "candidate": {"ref": "other"}}, PLUGIN_ROOT)
        entries = {"senior-review:x": {"id": "senior-review:x", "kind": "composition", "members": ["senior-review:y"]},
                   "senior-review:y": {"id": "senior-review:y", "kind": "composition", "members": ["senior-review:x"]}}
        with self.assertRaises(ValueError):
            composition.leaf_roles("senior-review:x", entries)


class SelectionTest(unittest.TestCase):
    AUTOMATIC = [
        {"specialist_id": "senior-review:authorization-auditor", "scope_id": "candidate",
         "evidence": [{"source": "computed-roster", "role": "senior-review:code-auditor"},
                      {"source": "code-review-floor", "reason": "no evidenced candidate/scope exclusion"}]},
    ]
    FROM_SOURCE = [
        {"specialist_id": "senior-review:ui-race-auditor", "scope_id": "candidate",
         "evidence": [{"source": "computed-roster", "role": "senior-review:code-auditor"},
                      {"source": "requirements", "id": "R1"}]},
    ]

    def bind_selected(self, selection, required=()):
        return composition.bind(roster(["senior-review:code-auditor"], required=required),
                                {**BINDINGS, "selection": selection}, PLUGIN_ROOT)

    def test_selection_replaces_the_automatic_roster_and_its_floor(self):
        chosen = ["senior-review:local-correctness-auditor", "senior-review:logic-integrity-auditor"]
        prepared = self.bind_selected(chosen, self.AUTOMATIC)
        self.assertEqual(prepared["roster"], chosen)
        self.assertEqual(prepared["required_specialists"], [])
        self.assertEqual([job["specialist_ids"] for job in prepared["jobs"]], [[c] for c in chosen])
        self.assertEqual(prepared["selection"], {"reviewers": chosen, "superseded": ["senior-review:code-auditor"]})

    def test_selection_keeps_an_obligation_with_its_own_source(self):
        prepared = self.bind_selected(["senior-review:local-correctness-auditor"], self.FROM_SOURCE)
        self.assertEqual([job["role"] for job in prepared["jobs"]],
                         ["senior-review:local-correctness-auditor", "senior-review:ui-race-auditor"])

    def test_branch_without_a_stated_selection_is_an_error(self):
        bindings = {key: value for key, value in BINDINGS.items() if key != "selection"}
        with self.assertRaises(ValueError):
            composition.bind(roster(["senior-review:code-auditor"]), bindings, PLUGIN_ROOT)

    def test_automatic_keeps_the_computed_roster(self):
        prepared = composition.bind(roster(["senior-review:code-auditor"]), BINDINGS, PLUGIN_ROOT)
        self.assertEqual(prepared["roster"], ["senior-review:code-auditor"])
        self.assertEqual(len(prepared["jobs"][0]["specialist_ids"]), 27)
        self.assertNotIn("selection", prepared)

    def test_empty_or_malformed_selection_is_an_error(self):
        for bad in ([], [""], "local-correctness", [1]):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.bind_selected(bad)

    def test_light_needs_no_selection_and_refuses_one(self):
        light = roster(["senior-review:code-auditor"], shape="light")
        bindings = {key: value for key, value in BINDINGS.items() if key != "selection"}
        self.assertEqual(len(composition.bind(light, bindings, PLUGIN_ROOT)["jobs"]), 1)
        with self.assertRaises(ValueError):
            composition.bind(light, {**BINDINGS, "selection": ["senior-review:ui-race-auditor"]}, PLUGIN_ROOT)

    def test_dispatch_validates_against_the_prepared_review(self):
        prepared = self.bind_selected(["senior-review:local-correctness-auditor"], self.FROM_SOURCE)
        roles = [job["role"] for job in prepared["jobs"]] + ["senior-review:premise-auditor"]
        self.assertEqual(review_roster.check(prepared, {"roles": roles, "critic": False}), [])
        self.assertTrue(review_roster.check(prepared, {"roles": ["senior-review:code-auditor"], "critic": False}))


class CliTest(unittest.TestCase):
    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "roster.json").write_text(json.dumps(roster(["senior-review:accessibility-auditor"])), encoding="utf-8")
            (root / "bad.json").write_text(json.dumps(roster(["nobody:auditor"])), encoding="utf-8")
            (root / "bindings.json").write_text(json.dumps(BINDINGS), encoding="utf-8")
            ok = subprocess.run([sys.executable, str(SCRIPTS / "composition.py"), "bind", "--roster", str(root / "roster.json"),
                                 "--bindings", str(root / "bindings.json"), "--out", str(root / "ok.json")],
                                capture_output=True, text=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(json.loads(ok.stdout)["jobs"], 1)
            bad = subprocess.run([sys.executable, str(SCRIPTS / "composition.py"), "bind", "--roster", str(root / "bad.json"),
                                  "--bindings", str(root / "bindings.json"), "--out", str(root / "bad-out.json")],
                                 capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)
            self.assertEqual(json.loads(bad.stdout)["unbound"], ["job-01"])
            cat = subprocess.run([sys.executable, str(SCRIPTS / "composition.py"), "catalog", "--out", str(root / "catalog.json")],
                                 capture_output=True, text=True)
            self.assertEqual(cat.returncode, 0, cat.stderr)
            self.assertEqual(json.loads(cat.stdout)["entries"], 62)


if __name__ == "__main__":
    unittest.main()
