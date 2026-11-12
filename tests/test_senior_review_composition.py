"""composition.py binds a computed roster into jobs made of focused role files.

Pinned behaviours: the catalog is derived from plugin.toml and readable by
review_roster.py; a composition expands to leaf roles without copying prose;
digests are stable and change with a role file; uncovered required specialists
get their own job except in light, which folds them into its single job; an
identity absent from the catalog leaves the job unbound and the exit non-zero;
a cycle, a foreign candidate or a second light job is an error. A branch bind
states its selection: the reviewers Phase 1 chose replace the automatic roster and
its floor, source obligations stay, and a dispatch validates against that result.
A branch bind on content basis with `coverage` gives every perimeter file one cell
per planned reviewer and splits each default-scope job into groups under a byte budget.
"""

import hashlib
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
        self.assertEqual(len(entries), 66)
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
            self.assertEqual(json.loads(cat.stdout)["entries"], 66)


CODE = "senior-review:code-auditor"
TYPESCRIPT = "senior-review:typescript-auditor"
TAURI = "senior-review:tauri-auditor"
TESTING = "senior-review:testing-auditor"
FIXTURE = [("app/a.py", "python", 50000), ("app/b.py", "python", 50000),
           ("docs/d.md", None, 1000), ("web/c.ts", "typescript", 30000)]


class CoverageCase(unittest.TestCase):
    """A temporary root holding the inventoried files at their sizes, and their FILES.json."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="review-coverage-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.files = self.root / "FILES.json"
        self.inventory(FIXTURE)

    def inventory(self, specs, contents=None):
        rows = []
        for path, language, size in specs:
            data = (contents or {}).get(path, b"x" * size)
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            rows.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
                         "lines": 1, "language": language})
        self.paths = [row["path"] for row in rows]
        self.files.write_text(json.dumps({"schema": "codebase-map/files/v1", "manifest": "manifest.sqlite",
                                          "files": rows}), encoding="utf-8")

    def bind(self, roles, paths=None, required=(), shape="branch", basis="content", **coverage):
        review = roster(roles, shape=shape, required=required)
        review["review_basis"] = basis
        review["grounding"]["conclusion_paths"] = self.paths if paths is None else paths
        coverage = {"files": str(self.files), "root": str(self.root), **coverage}
        return composition.bind(review, {**BINDINGS, "coverage": coverage}, PLUGIN_ROOT)

    @staticmethod
    def cells(prepared, reviewer):
        return {cell["path"]: cell for cell in prepared["coverage"]["cells"] if cell["reviewer"] == reviewer}

    @staticmethod
    def groups(prepared, role):
        return [job["paths"] for job in prepared["jobs"] if job["role"] == role]


class CoverageBindTest(CoverageCase):
    def test_every_file_has_one_cell_per_reviewer(self):
        prepared = self.bind([CODE, TYPESCRIPT])
        pairs = [(cell["path"], cell["reviewer"]) for cell in prepared["coverage"]["cells"]]
        self.assertEqual(len(pairs), 8)
        self.assertEqual(len(set(pairs)), 8)
        self.assertEqual(set(prepared["coverage"]["reviewers"]), {CODE, TYPESCRIPT})
        for job in prepared["jobs"]:
            self.assertEqual(prepared["coverage"]["reviewers"][job["role"]], job["body_sha256"])

    def test_open_cells_belong_to_exactly_one_job(self):
        required = [{"specialist_id": TESTING, "scope_id": "candidate",
                     "evidence": [{"source": "requirements", "path": "app/a.py", "reason": "tests are in scope"}]}]
        prepared = self.bind([CODE], paths=[*self.paths, "app/missing.py"], required=required, budget=60000)
        self.assertEqual(prepared["required_specialists"], required)
        jobs = {job["job_id"]: job for job in prepared["jobs"]}
        self.assertEqual({job["scope_id"] for job in jobs.values()}, {"candidate"})
        self.assertEqual({cell["reviewer"] for cell in prepared["coverage"]["cells"]}, {CODE, TESTING})
        for cell in prepared["coverage"]["cells"]:
            if cell["sha256"] is None:
                self.assertEqual((cell["path"], cell["status"], cell["job_id"], cell["note"]),
                                 ("app/missing.py", "open", None, "missing from map inventory"))
                continue
            holders = [job_id for job_id, job in jobs.items()
                       if job["role"] == cell["reviewer"] and cell["path"] in job["paths"]]
            self.assertEqual(holders, [cell["job_id"]], cell)

    def test_groups_respect_budget(self):
        prepared = self.bind([CODE], budget=60000)
        self.assertEqual(self.groups(prepared, CODE), [["app/a.py"], ["app/b.py", "docs/d.md"], ["web/c.ts"]])
        self.assertEqual([job["bytes"] for job in prepared["jobs"]], [50000, 51000, 30000])
        prepared = self.bind([CODE], budget=40000)
        self.assertEqual((prepared["jobs"][0]["paths"], prepared["jobs"][0]["bytes"]), (["app/a.py"], 50000))
        for job in prepared["jobs"]:
            self.assertTrue(job["bytes"] <= 40000 or len(job["paths"]) == 1, job)

    def test_given_units_replace_the_groups_by_path(self):
        prepared = self.bind([CODE], budget=60000, units=[["web/c.ts", "app/a.py"], ["app/a.py", "docs/d.md"]])
        # The first unit keeps its files; a file already grouped stays there; the rest is packed by path.
        self.assertEqual(self.groups(prepared, CODE), [["web/c.ts", "app/a.py"], ["docs/d.md"], ["app/b.py"]])
        with self.assertRaisesRegex(ValueError, "coverage.units"):
            self.bind([CODE], units=["app/a.py"])

    def test_typescript_reviewer_skips_known_other_languages(self):
        cells = self.cells(self.bind([TYPESCRIPT]), TYPESCRIPT)
        self.assertEqual({path: cell["status"] for path, cell in cells.items()},
                         {"app/a.py": "not-applicable", "app/b.py": "not-applicable",
                          "docs/d.md": "open", "web/c.ts": "open"})
        self.assertIsNone(cells["app/a.py"]["job_id"])
        self.assertIn("typescript", cells["app/a.py"]["note"])

    def test_configuration_and_explicit_obligations_stay_open(self):
        self.inventory([("app/a.py", "python", 10), ("package.json", "json", 10), ("scripts/settings.py", "python", 10),
                        ("tools/gen.py", "python", 10), ("tsconfig.json", "json", 10)])
        required = [
            {"specialist_id": "senior-review:input-validation-auditor", "scope_id": "candidate",
             "evidence": [{"source": "configurations", "path": "scripts/settings.py"}]},
            {"specialist_id": TYPESCRIPT, "scope_id": "candidate",
             "evidence": [{"source": "caller", "path": "tools/gen.py", "reason": "generates the typed client"}]},
        ]
        cells = self.cells(self.bind([CODE, TYPESCRIPT], required=required), TYPESCRIPT)
        self.assertEqual({path for path, cell in cells.items() if cell["status"] == "open"},
                         {"package.json", "scripts/settings.py", "tools/gen.py", "tsconfig.json"})
        self.assertEqual(cells["app/a.py"]["status"], "not-applicable")

    def test_directory_scope_and_missing_map_paths(self):
        prepared = self.bind([CODE], paths=["app/", "web/c.ts", "lib/gone.py"])
        cells = self.cells(prepared, CODE)
        self.assertEqual(sorted(cells), ["app/a.py", "app/b.py", "lib/gone.py", "web/c.ts"])
        self.assertEqual((cells["lib/gone.py"]["status"], cells["lib/gone.py"]["job_id"], cells["lib/gone.py"]["note"]),
                         ("open", None, "missing from map inventory"))
        self.assertEqual(sorted(path for job in prepared["jobs"] for path in job["paths"]),
                         ["app/a.py", "app/b.py", "web/c.ts"])
        empty = self.bind([CODE], paths=[])
        self.assertEqual((empty["coverage"]["cells"], empty["jobs"]), ([], []))
        review = roster([CODE])
        review["review_basis"] = "content"
        with self.assertRaises(ValueError):
            composition.bind(review, {**BINDINGS, "coverage": {"files": str(self.files), "root": str(self.root)}},
                             PLUGIN_ROOT)

    def test_tauri_needs_path_or_api(self):
        self.inventory([("src-tauri/src/main.rs", "rust", 0), ("web/api.ts", "typescript", 0),
                        ("web/view.ts", "typescript", 0)],
                       contents={"src-tauri/src/main.rs": b"fn main() {}\n",
                                 "web/api.ts": b'import { invoke } from "@tauri-apps/api/core";\n',
                                 "web/view.ts": b"export const view = 1;\n"})
        cells = self.cells(self.bind([TAURI]), TAURI)
        self.assertEqual({path: cell["status"] for path, cell in cells.items()},
                         {"src-tauri/src/main.rs": "open", "web/api.ts": "open", "web/view.ts": "not-applicable"})

    def test_reviewer_with_no_open_cell_has_no_job(self):
        self.inventory([("app/a.py", "python", 100), ("app/b.py", "python", 100)])
        prepared = self.bind([CODE, TYPESCRIPT])
        self.assertEqual({job["role"] for job in prepared["jobs"]}, {CODE})
        self.assertEqual({cell["status"] for cell in self.cells(prepared, TYPESCRIPT).values()}, {"not-applicable"})
        self.assertIn(TYPESCRIPT, prepared["coverage"]["reviewers"])

    def test_missing_inventory_file_fails(self):
        (self.root / "app/b.py").unlink()
        with self.assertRaisesRegex(ValueError, "refresh the map"):
            self.bind([CODE])

    def test_invalid_basis_or_shape_rejects_coverage(self):
        for shape, basis in (("light", "content"), ("branch", "changeset"), ("branch", "claims")):
            with self.assertRaises(ValueError, msg=(shape, basis)):
                self.bind([CODE], shape=shape, basis=basis)

    def test_group_output_is_single_json_result(self):
        prepared = self.bind([CODE, TYPESCRIPT], budget=60000)
        outputs = [job["output_path"] for job in prepared["jobs"]]
        self.assertTrue(outputs and all(path.endswith(".json") for path in outputs))
        self.assertEqual(len(set(outputs)), len(outputs))
        plain = composition.bind(roster([CODE, TYPESCRIPT]), BINDINGS, PLUGIN_ROOT)
        self.assertNotIn("coverage", plain)
        self.assertEqual([job["output_path"] for job in plain["jobs"]],
                         [".team-review/jobs/job-01.md", ".team-review/jobs/job-02.md"])
        self.assertTrue(all("paths" not in job for job in plain["jobs"]))
        for budget in (0, -1, True, "60000"):
            with self.assertRaises(ValueError, msg=repr(budget)):
                self.bind([CODE], budget=budget)


def result(job, read=(), partial=None, status="delivered", member_status="delivered", member_coverage="complete"):
    """A group job's single reviewer-result, bound to its job."""
    return {"dimension": "correctness", "reviewer": job["role"], "status": status, "findings": [], "gaps": [],
            "output_path": job["output_path"], "knowledge_usage": [], "job_id": job["job_id"],
            "specialist_ids": job["specialist_ids"], "scope_id": job["scope_id"], "candidate": job["candidate"],
            "body_sha256": job["body_sha256"], "read": list(read), "partial": {} if partial is None else partial,
            "member_results": [{"specialist_id": member, "status": member_status, "coverage": member_coverage,
                                "findings": [], "gaps": []} for member in job["specialist_ids"]]}


class CoverageAccountTest(CoverageCase):
    def account(self, prepared, deliveries):
        report = composition.account(prepared, deliveries, self.root)
        return {(cell["path"], cell["reviewer"]): cell for cell in report["cells"]}, report

    def test_read_files_with_completed_checks_are_covered(self):
        prepared = self.bind([CODE], budget=60000)
        first, second, _ = prepared["jobs"]
        cells, _ = self.account(prepared, {first["job_id"]: result(first, read=["app/a.py"]),
                                           second["job_id"]: result(second, read=["app/b.py", "docs/d.md"])})
        self.assertEqual({path: cell["status"] for (path, _), cell in cells.items()},
                         {"app/a.py": "covered", "app/b.py": "covered", "docs/d.md": "covered", "web/c.ts": "open"})

    def test_read_but_failed_or_incomplete_result_stays_open(self):
        prepared = self.bind([CODE], budget=60000)
        job = prepared["jobs"][1]
        read = ["app/b.py", "docs/d.md"]
        missing_member = result(job, read=read)
        missing_member["member_results"] = missing_member["member_results"][1:]
        for delivery in (result(job, read=read, status="failed"), missing_member,
                         result(job, read=read, member_status="failed"),
                         result(job, read=read, member_coverage="incomplete")):
            cells, _ = self.account(prepared, {job["job_id"]: delivery})
            for path in read:
                self.assertEqual(cells[(path, CODE)]["status"], "open")
                self.assertTrue(cells[(path, CODE)]["note"])

    def test_foreign_or_malformed_result_stays_open(self):
        prepared = self.bind([CODE], budget=60000)
        job = prepared["jobs"][0]
        variants = [{"job_id": "job-99"}, {"candidate": {"ref": "other"}}, {"reviewer": TYPESCRIPT},
                    {"specialist_ids": job["specialist_ids"][:1]}, {"scope_id": "elsewhere"}, {"body_sha256": "0" * 64},
                    {"read": "app/a.py"}, {"read": [1]}, {"partial": ["app/a.py"]}, {"partial": {"app/a.py": 3}}]
        for change in variants:
            cells, _ = self.account(prepared, {job["job_id"]: {**result(job, read=["app/a.py"]), **change}})
            self.assertEqual(cells[("app/a.py", CODE)]["status"], "open", change)
            self.assertIn("invalid result", cells[("app/a.py", CODE)]["note"], change)
        cells, _ = self.account(prepared, {job["job_id"]: ["not", "an", "object"]})
        self.assertEqual(cells[("app/a.py", CODE)]["note"], "invalid result: not a JSON object")

    def test_partial_stays_open_with_reason(self):
        prepared = self.bind([CODE], budget=60000)
        job = prepared["jobs"][1]
        cells, _ = self.account(prepared, {job["job_id"]: result(
            job, read=["app/b.py", "docs/d.md"], partial={"docs/d.md": "checks after line 40 not done"})})
        self.assertEqual(cells[("app/b.py", CODE)]["status"], "covered")
        self.assertEqual(cells[("docs/d.md", CODE)]["status"], "open")
        self.assertIn("checks after line 40 not done", cells[("docs/d.md", CODE)]["note"])

    def test_missing_delivery_leaves_cells_open(self):
        prepared = self.bind([CODE], budget=60000)
        for deliveries in ({}, {job["job_id"]: None for job in prepared["jobs"]}):
            cells, _ = self.account(prepared, deliveries)
            self.assertEqual({(cell["status"], cell["note"]) for cell in cells.values()}, {("open", "no result file")})

    def test_unassigned_and_directory_paths_do_not_count(self):
        prepared = self.bind([CODE], budget=60000)
        job = prepared["jobs"][0]
        cells, _ = self.account(prepared, {job["job_id"]: result(job, read=["web/", "web/c.ts", "app/"])})
        self.assertEqual((cells[("app/a.py", CODE)]["status"], cells[("app/a.py", CODE)]["note"]), ("open", "not read"))
        self.assertEqual((cells[("web/c.ts", CODE)]["status"], cells[("web/c.ts", CODE)]["note"]),
                         ("open", "no result file"))

    def test_windows_and_absolute_paths_normalize(self):
        prepared = self.bind([CODE])
        job = prepared["jobs"][0]
        self.assertEqual(job["paths"], ["app/a.py", "app/b.py", "docs/d.md"])
        cells, _ = self.account(prepared, {job["job_id"]: result(
            job, read=["app\\a.py", str(self.root / "app/b.py"), "./docs/d.md"])})
        for path in job["paths"]:
            self.assertEqual(cells[(path, CODE)]["status"], "covered", path)

    def test_summary_counts(self):
        prepared = self.bind([CODE, TYPESCRIPT], paths=[*self.paths, "lib/gone.py"], budget=60000)
        deliveries = {job["job_id"]: result(job, read=job["paths"]) for job in prepared["jobs"] if job["role"] == CODE}
        _, report = self.account(prepared, deliveries)
        self.assertEqual(report["schema"], "daodan/review-coverage/v1")
        self.assertEqual(report["summary"], {CODE: {"covered": 4, "open": 1, "not-applicable": 0},
                                             TYPESCRIPT: {"covered": 0, "open": 3, "not-applicable": 2}})

    def test_account_cli_uses_prepared_root(self):
        prepared = self.bind([CODE], budget=60000)
        first, second, _ = prepared["jobs"]
        target = self.root / first["output_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result(first, read=["app/a.py"])), encoding="utf-8")
        (self.root / second["output_path"]).write_text("{not json", encoding="utf-8")
        prepared_path = self.root / "PREPARED-REVIEW.json"
        prepared_path.write_text(json.dumps(prepared), encoding="utf-8")
        outputs = []
        with tempfile.TemporaryDirectory() as elsewhere:
            for cwd in (self.root, Path(elsewhere)):
                out = Path(elsewhere) / f"coverage-{len(outputs)}.json"
                run = subprocess.run([sys.executable, str(SCRIPTS / "composition.py"), "account",
                                      "--prepared", str(prepared_path), "--out", str(out)],
                                     capture_output=True, text=True, cwd=cwd)
                self.assertEqual(run.returncode, 0, run.stderr)
                outputs.append(json.loads(run.stdout))
                self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["schema"], "daodan/review-coverage/v1")
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0]["summary"], {CODE: {"covered": 1, "open": 3, "not-applicable": 0}})
        self.assertEqual(outputs[0]["open_total"], 3)
        notes = {cell["path"]: cell["note"] for cell in outputs[0]["open"]}
        self.assertEqual(notes["web/c.ts"], "no result file")
        self.assertIn("invalid result", notes["app/b.py"])


if __name__ == "__main__":
    unittest.main()
