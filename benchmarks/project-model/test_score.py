"""Tests for score.py on two hand-made cases. Run: python -m unittest test_score.py"""

import unittest

import score

NPM_EXPECTED = {
    "languages": [
        {"path": "packages/a/index.ts", "language": "TypeScript"},
        {"path": "packages/b/index.js", "language": "JavaScript"},
        {"path": "scripts/build", "language": "Shell"},
    ],
    "excluded": [{"path": "vendor/", "why": "vendored"}],
    "units": [
        {"name": "root", "kind": "npm-package", "root": ".", "manifest": "package.json", "depends_on": []},
        {"name": "@acme/a", "kind": "npm-package", "root": "packages/a",
         "manifest": "packages/a/package.json", "depends_on": ["@acme/b"]},
        {"name": "@acme/b", "kind": "npm-package", "root": "packages/b",
         "manifest": "packages/b/package.json", "depends_on": []},
    ],
    "workspace": {"tool": "pnpm", "root": ".", "members": ["packages/a", "packages/b"]},
    "toolchains": [
        {"tool": "node", "version": "20.11.0", "declared_in": ".nvmrc"},
        {"tool": "pnpm", "version": "9.1.0", "declared_in": "package.json"},
    ],
    "dependencies": [
        {"unit": "@acme/a", "name": "react", "declared": "^18.2.0", "resolved": "18.2.0",
         "scope": "runtime", "declared_in": "packages/a/package.json"},
    ],
    "frameworks": [{"name": "Next.js", "unit": "@acme/a", "evidence": "packages/a/next.config.js"}],
    "services": [],
    "needs": {"container": False, "reason": ""},
    "traps": ["the root package is private and not a member"],
}

NPM_GOT = {
    "languages": [
        {"path": "packages/a/index.ts", "language": "TypeScript"},
        {"path": "packages/b/index.js", "language": "javascript"},
        {"path": "vendor/x.js", "language": "JavaScript"},
        {"path": "tools/gen.py", "language": "Python"},
    ],
    "excluded": [
        {"path": "vendor/x.js", "why": "vendored"},
        {"path": "vendor/y.js"},
        {"path": "docs/", "why": "documentation"},
    ],
    "units": [
        {"name": "root", "kind": "npm-package", "root": "", "depends_on": []},
        {"name": "@acme/a", "kind": "npm-package", "root": "packages/a", "depends_on": []},
        {"name": "@acme/b", "kind": "yarn-package", "root": "packages/b/"},
        {"name": "@acme/c", "kind": "npm-package", "root": "packages/c"},
    ],
    "toolchains": [
        {"tool": "node", "version": "v20.11.0", "declared_in": ".nvmrc"},
        {"tool": "python", "version": "3.12"},
    ],
    "frameworks": [{"name": "nextjs"}],
    "services": [],
    "needs": {"container": True},
}

PY_EXPECTED = {
    "languages": [{"path": "src/pkg/__init__.py", "language": "Python"}],
    "excluded": [{"path": "src/pkg/_gen.py", "why": "generated"}],
    "units": [{"name": "My_Pkg", "kind": "python-project", "root": ".", "manifest": "pyproject.toml",
               "source_roots": ["src"]}],
    "toolchains": [
        {"tool": "python", "version": ">=3.11", "declared_in": "pyproject.toml"},
        {"tool": "python", "version": "3.12.1", "declared_in": ".python-version"},
    ],
    "dependencies": [
        {"unit": "My_Pkg", "name": "Requests", "declared": ">=2.31", "resolved": "2.31.0",
         "scope": "runtime", "declared_in": "pyproject.toml"},
        {"unit": "My_Pkg", "name": "pytest", "declared": ">=8", "resolved": None,
         "scope": "test", "declared_in": "pyproject.toml"},
    ],
    "needs": {"container": False, "reason": ""},
    "traps": ["src layout: the import root is src, not the project root"],
}

PY_GOT = {
    "excluded": [{"path": "src\\pkg\\_gen.py"}],
    "units": [{"name": "my-pkg", "kind": "python-project", "root": "./", "source_roots": ["src/"]}],
    "toolchains": [{"tool": "python", "version": ">= 3.11", "declared_in": "pyproject.toml"}],
    "dependencies": [
        {"name": "requests", "declared": ">=2.31", "resolved": "2.31.0"},
        {"name": "pytest", "declared": ">=8.0", "scope": "dev"},
        {"name": "idna", "resolved": "3.6"},
    ],
}


def invariant(test, result):
    for facet, r in result.items():
        if r["given"]:
            test.assertEqual(r["expected"], r["found"] + len(r["wrong"]) + len(r["missed"]), facet)


class NpmWorkspace(unittest.TestCase):
    def setUp(self):
        self.r = score.score(NPM_EXPECTED, NPM_GOT)

    def test_invariant(self):
        invariant(self, self.r)

    def test_language_set_and_files(self):
        s = self.r["languages"]
        self.assertEqual((s["expected"], s["found"]), (3, 2))
        self.assertEqual(s["missed"], ["Shell"])
        self.assertEqual(s["extra"], ["Python"])
        f = self.r["languages.files"]
        self.assertEqual((f["expected"], f["found"], f["missed"], f["extra"]), (3, 2, ["scripts/build"], []))

    def test_excluded_directory_covered_by_files(self):
        e = self.r["excluded"]
        self.assertEqual((e["found"], e["missed"], e["extra"]), (1, [], ["docs/"]))

    def test_units_identity_and_wrong_kind(self):
        u = self.r["units"]
        self.assertEqual((u["expected"], u["found"]), (3, 2))
        self.assertEqual(u["extra"], ["npm-package@packages/c"])
        self.assertEqual(len(u["wrong"]), 1)
        self.assertEqual(u["wrong"][0]["item"], "npm-package@packages/b")
        self.assertIn("kind", u["wrong"][0]["fields"])

    def test_depends_on_scored_over_all_expected_units(self):
        d = self.r["units.depends_on"]
        self.assertTrue(d["given"])
        self.assertEqual((d["expected"], d["found"], d["missed"]), (1, 0, ["npm-package@packages/a > @acme/b"]))

    def test_absent_facets_are_not_given(self):
        for facet in ("workspace", "workspace.members", "dependencies", "units.source_roots", "units.config"):
            self.assertFalse(self.r[facet]["given"], facet)
        self.assertEqual(self.r["workspace"]["expected"], 1)
        self.assertEqual(self.r["dependencies"]["expected"], 1)

    def test_versions_as_written_with_normalisation_flag(self):
        t = self.r["toolchains"]
        self.assertEqual((t["found"], t["found_normalised"]), (0, 1))
        self.assertTrue(t["wrong"][0]["same_after_normalisation"])
        self.assertEqual(t["missed"], ["pnpm@package.json"])
        self.assertEqual(t["extra"], ["python"])

    def test_frameworks_names_and_empty_services(self):
        self.assertEqual(self.r["frameworks"]["found"], 1)
        self.assertEqual((self.r["services"]["given"], self.r["services"]["expected"]), (True, 0))

    def test_service_alias(self):
        r = score.score({"services": [{"name": "PostgreSQL", "kind": "database", "evidence": "x"}]},
                        {"services": [{"name": "Postgres"}]})
        self.assertEqual(r["services"]["found"], 1)

    def test_needs(self):
        n = self.r["needs"]
        self.assertEqual((n["found"], len(n["wrong"])), (0, 1))


class PythonSrcLayout(unittest.TestCase):
    def setUp(self):
        self.r = score.score(PY_EXPECTED, PY_GOT)

    def test_invariant(self):
        invariant(self, self.r)

    def test_pep503_names_and_paths(self):
        self.assertEqual(self.r["units"]["found"], 1)
        self.assertEqual(self.r["units.source_roots"]["found"], 1)
        self.assertEqual(self.r["excluded"]["found"], 1)

    def test_toolchain_relaxed_match(self):
        t = self.r["toolchains"]
        self.assertEqual((t["found"], t["found_normalised"]), (0, 1))
        self.assertEqual(t["missed"], ["python@.python-version"])

    def test_dependencies(self):
        d = self.r["dependencies"]
        self.assertEqual((d["expected"], d["found"], d["found_normalised"]), (2, 1, 1))
        self.assertEqual(d["extra"], ["idna"])
        w = d["wrong"][0]
        self.assertEqual(sorted(w["fields"]), ["declared", "scope"])
        self.assertFalse(w["same_after_normalisation"])

    def test_not_given(self):
        for facet in ("languages", "languages.files", "needs", "frameworks"):
            self.assertFalse(self.r[facet]["given"], facet)


class Targets(unittest.TestCase):
    def test_two_targets_in_one_directory(self):
        e = {"units": [{"name": "core", "kind": "cmake-target", "root": "."},
                       {"name": "app", "kind": "cmake-target", "root": ".", "depends_on": ["core"]}]}
        g = {"units": [{"name": "app", "kind": "cmake-target", "root": ".", "depends_on": ["core"]},
                       {"name": "core", "kind": "cmake-target", "root": "."}]}
        r = score.score(e, g)
        self.assertEqual((r["units"]["found"], r["units.depends_on"]["found"]), (2, 1))


class Fragments(unittest.TestCase):
    E = {"toolchains": [{"tool": "node", "version": ">=20", "declared_in": "package.json#engines"},
                        {"tool": "node", "version": "20.11.1", "declared_in": "package.json#volta"},
                        {"tool": "python", "version": "3.12", "declared_in": ".python-version"}]}

    def test_fragment_compared_only_when_both_name_one(self):
        g = {"toolchains": [{"tool": "node", "version": "20.11.1", "declared_in": "package.json"},
                            {"tool": "node", "version": ">=20", "declared_in": "package.json#engines"},
                            {"tool": "python", "version": "3.12", "declared_in": ".python-version#x"}]}
        t = score.score(self.E, g)["toolchains"]
        self.assertEqual((t["found"], t["wrong"], t["missed"], t["extra"]), (3, [], [], []))

    def test_matrix_versions_in_one_setting(self):
        f = ".github/workflows/ci.yml#jobs.test.strategy.matrix.node"
        e = {"toolchains": [{"tool": "node", "version": v, "declared_in": f} for v in ("18.x", "20.x", "22.x")]}
        g = {"toolchains": [{"tool": "node", "version": v, "declared_in": f} for v in ("22.x", "18.x")]}
        t = score.score(e, g)["toolchains"]
        self.assertEqual((t["found"], t["wrong"], t["missed"]), (2, [], [f"node@{f}"]))

    def test_different_fragments_are_wrong(self):
        g = {"toolchains": [{"tool": "node", "version": ">=20", "declared_in": "package.json#volta"}]}
        t = score.score({"toolchains": self.E["toolchains"][:1]}, g)["toolchains"]
        self.assertEqual(t["found"], 0)
        self.assertEqual(sorted(t["wrong"][0]["fields"]), ["declared_in"])


class Unknown(unittest.TestCase):
    def test_unknown_facets_are_left_out_and_null_names_not_compared(self):
        e = {"units": [{"name": None, "kind": "terraform-module", "root": "modules/vpc", "manifest": None}],
             "unknown": ["dependencies"]}
        g = {"units": [{"name": "vpc", "kind": "terraform-module", "root": "modules/vpc"}],
             "dependencies": [{"name": "x"}]}
        r = score.score(e, g)
        self.assertNotIn("dependencies", r)
        self.assertEqual(r["units"]["found"], 1)


class RealDescriptors(unittest.TestCase):
    DOC = {
        "units": [{"name": "web", "kind": "npm-package", "root": "web", "manifest": "web/package.json"},
                  {"name": "api", "kind": "go-module", "root": "api", "manifest": "api/go.mod"}],
        "dependencies": [{"unit": "web", "name": "react", "declared": "^18", "resolved": None,
                          "scope": "runtime", "declared_in": "web/package.json"}],
        "unknown": [{"facet": "dependencies", "known": ["web"]}],
        "connections": [{"kind": "http-route", "key": "GET /api/items", "provided_by": ["api"],
                         "used_by": ["web"], "evidence": ["api/routes.go", "web/src/items.ts"]}],
        "needs": {"container": False, "reason": ""}, "traps": ["t"],
    }

    def test_check_accepts_per_unit_unknown_and_connections(self):
        self.assertEqual(score.check_expected(self.DOC, None), [])

    def test_dependencies_scored_only_for_known_units(self):
        g = {"dependencies": [{"unit": "web", "name": "react", "declared": "^18"},
                              {"unit": "api", "name": "github.com/go-chi/chi/v5"},
                              {"name": "lodash"}, {"name": "react"}]}
        d = score.score(self.DOC, g)["dependencies"]
        self.assertEqual((d["expected"], d["found"], d["extra"]), (1, 1, ["react"]))

    def test_null_named_unit_referred_to_by_root(self):
        doc = {"units": [{"name": None, "kind": "source-tree", "root": "seed-data", "manifest": None},
                         {"name": "api", "kind": "go-module", "root": "api", "manifest": "api/go.mod"}],
               "dependencies": [], "unknown": [{"facet": "dependencies", "known": ["seed-data"]}],
               "connections": [{"kind": "http-route", "key": "POST /", "provided_by": ["api"],
                                "used_by": ["seed-data"], "evidence": ["seed-data/make-data.py"]}],
               "needs": {"container": False, "reason": ""}, "traps": ["t"]}
        self.assertEqual(score.check_expected(doc, None), [])
        dup = dict(doc, units=doc["units"] + [{"name": "api", "kind": "go-module", "root": "api2", "manifest": "api2/go.mod"}],
                   connections=[dict(doc["connections"][0], provided_by=["api2"])])
        self.assertEqual(score.check_expected(dup, None), [])
        bad = dict(doc, connections=[dict(doc["connections"][0], used_by=["ghost"])])
        self.assertTrue(any("ghost" in x for x in score.check_expected(bad, None)))

    def test_check_rejects_unit_outside_known(self):
        doc = dict(self.DOC, unknown=[{"facet": "dependencies", "known": ["api"]}])
        self.assertTrue(any("not in the known units" in x for x in score.check_expected(doc, None)))


class SameTargetTwoMakefiles(unittest.TestCase):
    def test_manifest_tells_them_apart(self):
        e = {"units": [{"name": "example.exe", "kind": "make-target", "root": "msdos", "manifest": f"msdos/{m}"}
                       for m in ("Makefile.bor", "Makefile.tc")],
             "needs": {"container": False, "reason": ""}, "traps": ["t"]}
        self.assertEqual(score.check_expected(e, None), [])
        g = {"units": [dict(u) for u in reversed(e["units"])]}
        self.assertEqual(score.score(e, g)["units"]["found"], 2)


class Config(unittest.TestCase):
    def test_config_values_ignore_order_and_dot_slash(self):
        e = {"units": [{"name": "w", "kind": "npm-package", "root": "w",
                        "config": {"entry_files": ["w/a.ts", "w/b.ts"], "tsconfig": ["w/tsconfig.json"]}}]}
        g = {"units": [{"name": "w", "kind": "npm-package", "root": "w",
                        "config": {"entry_files": ["./w/b.ts", "w/a.ts"], "tsconfig": ["w/tsconfig.app.json"]}}]}
        c = score.score(e, g)["units.config"]
        self.assertEqual((c["expected"], c["found"], len(c["wrong"])), (2, 1, 1))


class Check(unittest.TestCase):
    def test_check_flags_unknown_kind_and_config_key(self):
        doc = {"units": [{"name": "r", "kind": "workspace-root", "root": ".", "config": {"note": "x"}}],
               "needs": {"container": False, "reason": ""}, "traps": ["t"]}
        problems = score.check_expected(doc, None)
        self.assertTrue(any("workspace-root" in x and not x.startswith("warning:") for x in problems))
        self.assertTrue(any("note" in x and x.startswith("warning:") for x in problems))

    def test_toolchain_and_dependency_in_different_files(self):
        doc = {"toolchains": [{"tool": "cmake", "version": "3.24", "declared_in": "CMakeLists.txt"},
                              {"tool": "typescript", "version": "^5", "declared_in": "package.json"}],
               "dependencies": [{"unit": "a", "name": "cmake", "declared": "3.28.1", "resolved": None,
                                 "scope": "build", "declared_in": "conanfile.txt"},
                                {"unit": "a", "name": "typescript", "declared": "^5", "resolved": None,
                                 "scope": "dev", "declared_in": "package.json"}],
               "needs": {"container": False, "reason": ""}, "traps": ["t"]}
        problems = score.check_expected(doc, None)
        self.assertEqual(len(problems), 1)
        self.assertIn("typescript", problems[0])

    def test_internal_name_check_stays_in_one_ecosystem(self):
        doc = {"units": [{"name": "app", "kind": "python-project", "root": "backend", "manifest": "backend/pyproject.toml"},
                         {"name": "emails", "kind": "npm-package", "root": "packages/emails",
                          "manifest": "packages/emails/package.json"}],
               "dependencies": [{"unit": "app", "name": "emails", "declared": ">=1.1.2,<2.0", "resolved": "1.1.2",
                                 "scope": "runtime", "declared_in": "backend/pyproject.toml"}],
               "needs": {"container": False, "reason": ""}, "traps": ["t"]}
        self.assertEqual(score.check_expected(doc, None), [])
        doc["dependencies"][0].update(declared_in="packages/emails/package.json", unit="emails")
        self.assertTrue(any("depends_on" in x for x in score.check_expected(doc, None)))

    def test_check_manifest_null_and_fragments(self):
        doc = {"units": [{"name": "scripts", "kind": "python-project", "root": ".", "manifest": None}],
               "toolchains": [{"tool": "python", "version": "3.12",
                               "declared_in": "pyproject.toml#tool.pyright.pythonVersion"},
                              {"tool": "mypy", "version": "3.9", "declared_in": "pyproject.toml"}],
               "needs": {"container": False, "reason": ""}, "traps": ["t"]}
        problems = score.check_expected(doc, None)
        self.assertEqual(len(problems), 1)
        self.assertIn("mypy", problems[0])

    def test_check_reports_shape_problems(self):
        bad = {"units": [{"kind": "npm-package", "root": "nowhere", "depends_on": ["ghost"]}],
               "dependencies": [{"unit": "x", "name": "y", "scope": "sometimes"}], "colour": 1}
        problems = score.check_expected(bad, None)
        text = "\n".join(problems)
        for needle in ("colour", "ghost", "sometimes", "needs", "traps"):
            self.assertIn(needle, text)

    def test_check_accepts_the_hand_made_cases(self):
        self.assertEqual(score.check_expected(NPM_EXPECTED, None), [])
        self.assertEqual(score.check_expected(PY_EXPECTED, None), [])


if __name__ == "__main__":
    unittest.main()
