"""Tests for pipeline_report.py on a hand-made round. Run: python -m unittest test_pipeline_report.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pipeline_report


def facet(expected, found, extra=(), wrong=()):
    return {"given": True, "expected": expected, "found": found, "found_normalised": found, "missed": [],
            "extra": list(extra), "wrong": list(wrong)}


def coverage(sites, answered, holes, snapshot, missing=()):
    return {"sites": sites, "answered": answered,
            "holes": {name: {"count": count, "examples": [f"a.x:1 {name}"]} for name, count in holes.items()},
            "uncertain": 0, "externals": {},
            "files": {"snapshot": snapshot, "indexed": snapshot - len(missing),
                      "missing": [{"path": path, "reason": reason} for path, reason in missing]},
            "state": "lower-bound" if holes or missing else "complete"}


def run(phase, image, outcome, code, seconds, cause=None):
    return {"phase": phase, "image": image, "outcome": outcome, "exit_code": code, "duration_seconds": seconds,
            "cause": cause}


NODE_RANGE = {"kind": "toolchain_unavailable", "detail": "node >=20: a range, not a version to install",
              "path": "package.json", "source": "tsc@6.0.3"}
NO_SOURCE_SET = "in no Gradle source set: no KotlinCompile task lists it"
ROUND = {
    "js-one": {
        "premap": {"languages": facet(2, 2, extra=["JSON"]), "units": facet(3, 2, wrong=[{"item": "web"}]),
                   "dependencies": {"given": False, "expected": 4}},
        "gaps": [NODE_RANGE],
        "steps": {
            "analyze": {"engines": {"scip-typescript": {"gaps": [
                {"kind": "restore_failed", "detail": "npm wrote no node_modules", "manager": "npm", "path": "."}]}}},
            "union": {"languages": {"typescript": {
                "state": "fresh", "engine": "scip-typescript@0.5.2",
                "coverage": coverage(10, {"external": 4, "project-callable": 2},
                                     {"dangling-local": 3, "no-occurrence": 1}, 3)}}}},
        "containers": [run("prepare", "node:22@sha256:abc", "exited", 0, 8.5),
                       run("execute", "node:22@sha256:abc", "exited", 0, 1.5)],
        "seconds": 100.0},
    "jvm-two": {
        "premap": {"languages": facet(2, 1), "units": facet(1, 1)},
        "gaps": [NODE_RANGE, {"kind": "superseded", "detail": "pom.xml: read by the build tool", "path": "pom.xml"}],
        "steps": {"union": {
            "languages": {
                "java": {"state": "failed", "engine": "scip-java",
                         "reason": "the scip-java stage exited with code 1 without a report"},
                "kotlin": {"state": "fresh", "engine": "scip-kotlin@0.14.2",
                           "coverage": coverage(10, {}, {"no-document": 10}, 2,
                                                missing=[("a.kt", NO_SOURCE_SET), ("b.kt", NO_SOURCE_SET)])}},
            "no_analyzer": {"scala": 1200}}},
        "containers": [run("prepare", "gradle:8@sha256:def", "timeout", None, 30.0),
                       run("execute", "gradle:8@sha256:def", "exited", 1, 1500.0)],
        "seconds": 1300.5},
    "py-three": {"error": "KeyError: 'units'", "trace": "Traceback ...", "seconds": 2.0},
}
LATER = {"jvm-two": {
    "premap": {"languages": facet(2, 2), "units": facet(1, 1)},
    "gaps": [],
    "steps": {"union": {"languages": {
        "java": {"state": "fresh", "engine": "scip-java@0.14.2", "coverage": coverage(4, {"project-value": 4}, {}, 1)},
        "kotlin": {"state": "fresh", "engine": "scip-kotlin@0.14.2",
                   "coverage": coverage(10, {"project-callable": 7}, {"no-document": 3}, 2)}}}},
    "containers": [],
    "seconds": 200.0}}


class Build(unittest.TestCase):
    def setUp(self):
        self.report = pipeline_report.build(ROUND)

    def test_cases_and_seconds(self):
        self.assertEqual(self.report["cases"], {
            "run": 3, "failed": {"py-three": "KeyError: 'units'"},
            "seconds": {"total": 1402.5, "median": 100.0,
                        "slowest": [["jvm-two", 1300.5], ["js-one", 100.0], ["py-three", 2.0]]}})

    def test_a_failed_step_is_a_failed_case(self):
        report = pipeline_report.build({"x": {"steps": {"scan": {"failed": "no build tool", "remedy": "r"}},
                                              "seconds": 1.0}})
        self.assertEqual(report["cases"]["failed"], {"x": "scan: no build tool"})

    def test_languages_across_cases(self):
        self.assertEqual(self.report["languages"]["typescript"], {
            "cases": 1, "states": {"fresh": 1}, "reasons": {}, "files": {"snapshot": 3, "indexed": 3}, "sites": 10,
            "answered": {"external": 4, "project-callable": 2}, "holes": {"dangling-local": 3, "no-occurrence": 1},
            "share": 0.6})
        java = self.report["languages"]["java"]
        self.assertEqual((java["states"], java["sites"], java["share"]), ({"failed": 1}, 0, None))
        self.assertEqual(java["reasons"], {"failed": [["the scip-java stage exited with code 1 without a report", 1]]})

    def test_fresh_with_files_missing_and_no_analyzer(self):
        self.assertEqual(self.report["missing"], [{"case": "jvm-two", "language": "kotlin", "missing": 2,
                                                   "snapshot": 2, "reasons": {NO_SOURCE_SET: 2}}])
        self.assertEqual(self.report["no_analyzer"], {"scala": {"cases": 1, "files": 1200}})

    def test_premap_facets_summed_over_the_cases_that_give_them(self):
        self.assertEqual(self.report["premap"], {
            "languages": {"given": 2, "not_given": 0, "found": 3, "expected": 4, "extra": 1, "wrong": 0},
            "units": {"given": 2, "not_given": 0, "found": 3, "expected": 4, "extra": 0, "wrong": 1},
            "dependencies": {"given": 0, "not_given": 1, "found": 0, "expected": 0, "extra": 0, "wrong": 0}})

    def test_gaps_by_step_and_kind(self):
        self.assertEqual(self.report["gaps"], [
            {"step": "scan", "kind": "toolchain_unavailable", "count": 2,
             "examples": ["js-one: package.json: node >=20: a range, not a version to install",
                          "jvm-two: package.json: node >=20: a range, not a version to install"]},
            {"step": "scan", "kind": "superseded", "count": 1,
             "examples": ["jvm-two: pom.xml: pom.xml: read by the build tool"]},
            {"step": "analyze", "kind": "restore_failed", "count": 1,
             "examples": ["js-one: .: npm wrote no node_modules"]}])

    def test_containers(self):
        self.assertEqual(self.report["containers"], {
            "runs": 4, "seconds": 1540.0,
            "phases": {"execute": {"runs": 2, "seconds": 1501.5}, "prepare": {"runs": 2, "seconds": 38.5}},
            "not_zero": [
                {"phase": "execute", "image": "gradle:8", "outcome": "exited", "exit_code": 1, "cause": None,
                 "count": 1, "cases": ["jvm-two"]},
                {"phase": "prepare", "image": "gradle:8", "outcome": "timeout", "exit_code": None, "cause": None,
                 "count": 1, "cases": ["jvm-two"]}]})

    def test_by_case_holds_what_a_comparison_needs(self):
        self.assertEqual(self.report["by_case"]["jvm-two"], {"seconds": 1300.5, "languages": {
            "java": {"state": "failed", "holes": 0}, "kotlin": {"state": "fresh", "holes": 10}}})
        self.assertEqual(self.report["by_case"]["py-three"], {"seconds": 2.0, "error": "KeyError: 'units'",
                                                              "languages": {}})

    def test_the_report_is_plain_json(self):
        self.assertEqual(json.loads(json.dumps(self.report)), self.report)


class Render(unittest.TestCase):
    def test_tables_with_italian_numbers(self):
        lines = pipeline_report.render(pipeline_report.build(ROUND), ["a.json"]).splitlines()
        for line in ("- Eseguiti: 3; falliti: 1.",
                     "- Secondi: 1.402,5 in totale; mediana 100,0.",
                     "| jvm-two | 1.300,5 |",
                     "| py-three | KeyError: 'units' |",
                     "| Linguaggio | Casi | fresh | failed | unavailable | File indicizzati / nello snapshot | Siti |"
                     " Risposti | Buchi | Quota risposta |",
                     "| typescript | 1 | 1 | 0 | 0 | 3 / 3 | 10 | 6 | 4 | 60,0 % |",
                     "| java | 1 | 0 | 1 | 0 | 0 / 0 | 0 | 0 | 0 | — |",
                     "| typescript | external 4, project-callable 2 | dangling-local 3, no-occurrence 1 |",
                     "| java | failed | 1 | the scip-java stage exited with code 1 without a report |",
                     f"| jvm-two | kotlin | 2 / 2 | {NO_SOURCE_SET} (2) |",
                     "| scala | 1 | 1.200 |",
                     "| units | 2 | 0 | 3 | 4 | 0 | 1 |",
                     "| scan | toolchain_unavailable | 2 | js-one: package.json: node >=20: a range, not a version to"
                     " install<br>jvm-two: package.json: node >=20: a range, not a version to install |",
                     "- Corse: 4; secondi: 1.540,0.",
                     "| execute | gradle:8 | exited | 1 | — | 1 | jvm-two |",
                     "| prepare | gradle:8 | timeout | — | — | 1 | jvm-two |"):
            self.assertIn(line, lines)

    def test_a_pipe_in_a_cell_does_not_break_the_table(self):
        report = pipeline_report.build({"x": {"error": "a | b\nc", "seconds": 1.0}})
        self.assertIn("| x | a \\| b c |", pipeline_report.render(report, ["a.json"]).splitlines())


CODE = {"commit": "c" * 40, "tree": "a" * 40, "differs": []}
EDITED = {"commit": "c" * 40, "tree": "b" * 40, "differs": ["x/1.py", "x/2.py", "x/3.py", "x/4.py"]}
UNKNOWN = "Codice non registrato in un giro: non registrato → non registrato."


class Compare(unittest.TestCase):
    def test_state_changes_and_holes_per_language_and_case(self):
        old = pipeline_report.build(ROUND)
        new = pipeline_report.build({**{name: case for name, case in ROUND.items() if name != "py-three"},
                                     **LATER, "sys-new": {"seconds": 1.0, "steps": {}}})
        self.assertEqual(pipeline_report.compare(old, new), [
            UNKNOWN,
            "Per linguaggio:",
            "- java: fresh 0 → 1, failed 1 → 0",
            "- kotlin: buchi 10 → 3 (-7)",
            "Per caso:",
            "- jvm-two: java failed → fresh; kotlin buchi 10 → 3 (-7)",
            "- py-three: non più nel giro",
            "- sys-new: nuovo"])

    def test_no_difference(self):
        report = pipeline_report.build(ROUND)
        self.assertEqual(pipeline_report.compare(report, report), [UNKNOWN, "Nessuna differenza."])

    def test_a_comparison_says_first_whether_the_two_rounds_ran_the_same_code(self):
        """The tree of the copy each round uploaded decides: a commit alone does not, the copy may differ from it."""
        report = pipeline_report.build(ROUND)
        same, edited = {**report, "code": {"a.json": CODE}}, {**report, "code": {"b.json": EDITED}}
        self.assertEqual(pipeline_report.compare(same, {**report, "code": {"c.json": CODE}}),
                         ["Stesso codice: commit `cccccccccccc`, albero `aaaaaaaaaaaa`, uguale al commit.",
                          "Nessuna differenza."])
        self.assertEqual(pipeline_report.compare(same, edited)[0],
                         "Codice diverso: commit `cccccccccccc`, albero `aaaaaaaaaaaa`, uguale al commit → commit "
                         "`cccccccccccc`, albero `bbbbbbbbbbbb`, diverso dal commit in 4 percorsi (`x/1.py`, "
                         "`x/2.py`, `x/3.py`, …).")
        self.assertEqual(pipeline_report.compare(same, {**report, "code": {"b.json": None}})[0],
                         "Codice non registrato in un giro: commit `cccccccccccc`, albero `aaaaaaaaaaaa`, uguale al "
                         "commit → non registrato.")
        mixed = {**report, "code": {"a.json": CODE, "b.json": EDITED}}  # a round made of files of two codes
        self.assertTrue(pipeline_report.compare(same, mixed)[0].startswith("Codice diverso: "))


class Main(unittest.TestCase):
    def test_later_files_replace_cases_and_the_numbers_are_written_beside_the_markdown(self):
        with tempfile.TemporaryDirectory() as folder:
            first, second, out = Path(folder) / "a.json", Path(folder) / "b.json", Path(folder) / "round.md"
            first.write_text(json.dumps({"code": EDITED, **ROUND}), encoding="utf-8")  # the driver's code beside
            second.write_text(json.dumps(LATER), encoding="utf-8")  # a round from before the driver wrote it
            pipeline_report.main([str(first), str(second), "--out", str(out)])
            report = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(report["by_case"]["jvm-two"]["languages"]["java"], {"state": "fresh", "holes": 0})
            self.assertEqual(report["cases"]["run"], 3)
            self.assertEqual(report["code"], {"a.json": EDITED, "b.json": None})
            text = out.read_text(encoding="utf-8")
            self.assertEqual(text, pipeline_report.render(report, ["a.json", "b.json"]))
            self.assertIn("Codice di `a.json`: commit `cccccccccccc`, albero `bbbbbbbbbbbb`, diverso dal commit in 4 "
                          "percorsi (`x/1.py`, `x/2.py`, `x/3.py`, …).", text.splitlines())
            self.assertIn("Codice di `b.json`: non registrato.", text.splitlines())

    def test_the_comparison_prints_on_a_console_that_is_not_utf8(self):
        with tempfile.TemporaryDirectory() as folder:
            first, second = Path(folder) / "a.json", Path(folder) / "b.json"
            first.write_text(json.dumps({"code": CODE, **ROUND}), encoding="utf-8")
            second.write_text(json.dumps({"code": EDITED, **ROUND, **LATER}), encoding="utf-8")
            done = subprocess.run([sys.executable, pipeline_report.__file__, str(second), "--compare", str(first)],
                                  capture_output=True, env={**os.environ, "PYTHONIOENCODING": "cp1252"})
            self.assertEqual(done.returncode, 0, done.stderr.decode(errors="replace"))
            said = done.stdout.decode("utf-8").splitlines()
            self.assertIn("- jvm-two: java failed → fresh; kotlin buchi 10 → 3 (-7)", said)
            self.assertTrue(said[1].startswith("Codice diverso: commit `cccccccccccc`, albero `aaaaaaaaaaaa`"), said)


if __name__ == "__main__":
    unittest.main()
