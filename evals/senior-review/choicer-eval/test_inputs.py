"""Offline regressions for evidence extraction, prompt fidelity and confinement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset
import run_eval


BASE = Path(__file__).resolve().parent
REPO = BASE.parents[2]


def fixture() -> tuple[dict, dict, dict]:
    cases = {
        "cases": [{
            "id": "C01",
            "source_case": "SECRET_CASE_TITLE_SENTINEL",
            "label_status": "labeled",
            "expected_roles": ["SECRET_EXPECTED_ROLE_SENTINEL"],
            "provenance": {"SECRET_REVISION_SENTINEL": "SECRET_SCORING_NOTE_SENTINEL"},
            "hunks": [{
                "id": "H1", "path": "src/example.py", "start_line": 17,
                "text": "def transfer(value):\n    return value + 1\n",
                "symbol_cards": [],
            }, {
                "id": "H2", "path": "src/example.py", "start_line": 25,
                "text": "def persist(db):\n    return db.commit()\n",
                "symbol_cards": [],
            }],
        }],
    }
    catalog = {
        "roles": [{
            "id": "example:first", "is_reviewer": True,
            "trigger_when": "The exact first criterion; keep $tokens and `code`.",
            "do_not_trigger_when": "The exact negative: no paraphrase.",
        }, {
            "id": "example:second", "is_reviewer": True,
            "trigger_when": "The exact second criterion.",
            "do_not_trigger_when": None,
        }, {
            "id": "example:writer", "is_reviewer": False,
            "trigger_when": "SECRET_NON_REVIEWER_SENTINEL",
            "do_not_trigger_when": None,
        }],
    }
    return cases, catalog, dataset.extract_prompts(REPO)


class PromptInputTests(unittest.TestCase):
    def test_repo_root_is_the_repository_not_evals(self):
        self.assertEqual(run_eval.REPO, REPO)
        self.assertTrue((run_eval.REPO / "plugins").is_dir())
        self.assertTrue((run_eval.REPO / dataset.SPEC).is_file())

    def test_all_three_templates_are_exact_source_slices(self):
        source = (REPO / dataset.SPEC).read_bytes().decode("utf-8")
        extracted = dataset.extract_prompts(REPO)
        self.assertEqual(set(extracted), {
            "TASK_TIER_CHOICER", "REVIEWER_CHOICER", "RETRY_TRIAGER",
        })
        lines = source.splitlines(keepends=True)
        for name, prompt in extracted.items():
            direct = "".join(lines[prompt["start_line"] - 1 : prompt["end_line"]])
            self.assertEqual(prompt["text"], direct, name)
            self.assertEqual(prompt["sha256"], hashlib.sha256(direct.encode()).hexdigest())
            self.assertEqual(lines[prompt["start_line"] - 2].strip(), "```text")
            self.assertEqual(lines[prompt["end_line"]].strip(), "```")

    def test_llm_substitution_preserves_every_other_template_character(self):
        cases, catalog, prompts = fixture()
        request = run_eval.build_requests(cases, catalog, prompts, "llm", "noul")[0]
        substitutions = {
            "mode": "full",
            "intent_and_docs": "Not supplied.",
            # The 2026-10-20 spec rewrite renamed $graph_facts to $code_graph_facts.
            # Both keys stay accepted so frozen historical templates still rebuild.
            "code_graph_facts": "[]\n",
            "graph_facts": "[]\n",
            "tool_results": "No deterministic checks were supplied.",
            "reviewers_catalog": (
                "example:first\n"
                "TRIGGER WHEN: The exact first criterion; keep $tokens and `code`.\n"
                "DO NOT TRIGGER WHEN: The exact negative: no paraphrase.\n\n"
                "example:second\n"
                "TRIGGER WHEN: The exact second criterion.\n"
                "DO NOT TRIGGER WHEN: "
            ),
            "diff_content": (
                "[H1]\nsrc/example.py:17 def transfer(value):\n"
                "src/example.py:18     return value + 1\n\n"
                "[H2]\nsrc/example.py:25 def persist(db):\n"
                "src/example.py:26     return db.commit()"
            ),
        }
        # Independent one-pass replacement ensures inserted dollars are data.
        expected = re.sub(
            r"\$([a-z_]+)",
            lambda match: substitutions[match.group(1)],
            prompts["REVIEWER_CHOICER"]["text"],
        )
        self.assertEqual(request["prompt"], expected)
        self.assertIn("$tokens", request["prompt"])
        self.assertEqual(request["template_sha256"], prompts["REVIEWER_CHOICER"]["sha256"])

    def test_only_opaque_case_and_hunk_ids_cross_the_boundary(self):
        cases, catalog, prompts = fixture()
        for impl, variant in (("llm", "noul"), ("julia", "noul"), ("julia", "choice")):
            requests = run_eval.build_requests(cases, catalog, prompts, impl, variant)
            serialized = json.dumps(requests)
            self.assertNotIn("SECRET_", serialized)
            self.assertNotIn("expected_roles", serialized)
            self.assertNotIn("provenance", serialized)
            self.assertTrue(all(request["case_id"] == "C01" for request in requests))
            self.assertEqual(
                [request["hunk_id"] for request in requests],
                [None] if impl == "llm" else ["H1", "H2"],
            )

    def test_noul_asks_every_reviewer_for_every_hunk_without_inventing_negatives(self):
        cases, catalog, prompts = fixture()
        requests = run_eval.build_requests(cases, catalog, prompts, "julia", "noul")
        for request in requests:
            self.assertEqual(set(request["questions"]), {"example:first", "example:second"})
            first = request["questions"]["example:first"]
            second = request["questions"]["example:second"]
            self.assertEqual(first["criteria"]["true"], catalog["roles"][0]["trigger_when"])
            self.assertEqual(first["criteria"]["false"], catalog["roles"][0]["do_not_trigger_when"])
            self.assertEqual(second["criteria"]["false"], "")
            self.assertEqual(first["instructions"], "Does this hunk satisfy the reviewer's TRIGGER WHEN?")

    def test_choice_uses_the_model_criteria_contract(self):
        cases, catalog, prompts = fixture()
        request = run_eval.build_requests(cases, catalog, prompts, "julia", "choice")[0]
        question = request["questions"]["reviewer"]
        self.assertNotIn("options", question)
        self.assertEqual(set(question["criteria"]), {"example:first", "example:second"})

    def test_llm_and_local_receive_identical_numbered_hunk_text(self):
        cases, catalog, prompts = fixture()
        llm = run_eval.build_requests(cases, catalog, prompts, "llm", "noul")[0]
        local = run_eval.build_requests(cases, catalog, prompts, "julia", "noul")
        for request in local:
            self.assertIn(request["state"], llm["prompt"])
        self.assertIn("src/example.py:17 def transfer(value):", local[0]["state"])

    def test_forbidden_oracle_text_in_source_is_rejected(self):
        cases, catalog, prompts = fixture()
        cases["cases"][0]["hunks"][0]["text"] += "# Scoring notes: gold\n"
        with self.assertRaisesRegex(ValueError, "prohibited"):
            run_eval.build_requests(cases, catalog, prompts, "julia", "noul")

    def test_llm_choice_cannot_silently_change_the_verbatim_prompt(self):
        cases, catalog, prompts = fixture()
        with self.assertRaisesRegex(ValueError, "protocol"):
            run_eval.build_requests(cases, catalog, prompts, "llm", "choice")


class ExtractionTests(unittest.TestCase):
    def test_catalog_is_deterministic_and_parses_all_source_roles(self):
        first = dataset.extract_catalog(REPO)
        second = dataset.extract_catalog(REPO)
        self.assertEqual(first, second)
        source_roles = list((REPO / "plugins").glob("*/roles/*.md"))
        self.assertEqual(first["role_count"], len(source_roles))
        self.assertEqual(first["reviewer_count"], len(first["reviewer_ids"]))
        self.assertNotIn("codebase-map:map-analyst", first["reviewer_ids"])
        self.assertNotIn("codebase-map:semantic-interconnect-mapper", first["reviewer_ids"])
        for role in first["roles"]:
            source = (REPO / role["source"]).read_bytes()
            self.assertEqual(role["source_sha256"], hashlib.sha256(source).hexdigest())
            self.assertIn(role["description_raw"], source.decode("utf-8"))
            for value in (role["trigger_when"], role["do_not_trigger_when"]):
                if value is not None:
                    self.assertIn(value, role["description"])

    def test_absent_negative_is_null_and_not_guessed(self):
        catalog = dataset.extract_catalog(REPO)
        roles = {role["id"]: role for role in catalog["roles"]}
        for name in (
            "platform-engineering:platform-reviewer",
            "senior-review:distributed-flow-auditor",
            "senior-review:ui-race-auditor",
        ):
            self.assertIsNone(roles[name]["do_not_trigger_when"])

    def test_unlabeled_precision_case_is_not_a_negative_example(self):
        text = (REPO / "evals/senior-review/cases/jupiter-credential-refill/case.md").read_text(encoding="utf-8")
        status, expected, dimensions = dataset._labels(text)
        self.assertEqual(status, "unlabeled")
        self.assertEqual((expected, dimensions), ([], []))

    def test_diff_old_side_never_includes_fixed_source(self):
        patch_text = (
            "diff --git a/example.py b/example.py\n"
            "--- a/example.py\n+++ b/example.py\n"
            "@@ -8,3 +8,3 @@\n"
            " def read():\n"
            "-    return False\n"
            "+    return None\n"
            " \n"
        )
        self.assertEqual(dataset._diff_blocks(patch_text, "old"), [
            (8, "def read():\n    return False\n\n"),
        ])
        self.assertEqual(dataset._diff_blocks(patch_text, "new"), [
            (8, "def read():\n    return None\n\n"),
        ])

    def test_whole_module_partition_preserves_all_source_and_complete_functions(self):
        source = (
            "import functools\n\n"
            "# preceding class\n"
            "class Example:\n"
            "    @functools.cache\n"
            "    def first(self):\n"
            "        def nested():\n"
            "            return 1\n"
            "        return nested()\n\n"
            "    async def second(self):\n"
            "        return await self.ready()\n\n"
            "# trailing source\n"
        )
        hunks = dataset._python_blocks("example.py", source)
        self.assertEqual(len(hunks), 2)
        self.assertEqual("".join(h["text"] for h in hunks), source)
        self.assertIn("@functools.cache\n    def first", hunks[0]["text"])
        self.assertIn("def nested()", hunks[0]["text"])
        self.assertTrue(hunks[-1]["text"].endswith("# trailing source\n"))
        for hunk in hunks:
            lines = source.splitlines(keepends=True)
            expected = "".join(lines[hunk["start_line"] - 1 : hunk["end_line"]])
            self.assertEqual(hunk["text"], expected)


class ConfinementTests(unittest.TestCase):
    def test_relative_and_absolute_traversal_are_rejected(self):
        for path in ("../outside.json", "../choicer-eval-other/file.json", REPO / "outside.json"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "escapes"):
                run_eval.confined(path)
        self.assertEqual(run_eval.confined("runs/probe/../example.json"), BASE / "runs/example.json")

    def test_write_and_freeze_only_touch_the_confined_test_directory(self):
        with tempfile.TemporaryDirectory(prefix="test-inputs-", dir=BASE) as temporary:
            target = Path(temporary).resolve()
            self.assertTrue(target.is_relative_to(BASE))
            with patch.object(run_eval, "BASE", target):
                run_eval.write_text("result.json", '{"measured": true}\n', freeze=True)
                self.assertEqual((target / "result.json").read_text(), '{"measured": true}\n')
                run_eval.write_text("result.json", '{"measured": true}\n', freeze=True)
                with self.assertRaisesRegex(ValueError, "Frozen evidence"):
                    run_eval.write_text("result.json", '{"measured": false}\n', freeze=True)
                with self.assertRaisesRegex(ValueError, "escapes"):
                    run_eval.write_text("../escaped.json", "must not exist")
                self.assertEqual(sorted(p.name for p in target.iterdir()), ["result.json"])

    def test_resolution_rejects_a_symlink_escape(self):
        with tempfile.TemporaryDirectory(prefix="test-inputs-", dir=BASE) as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.is_relative_to(BASE))
            inner = root / "inner"
            sibling = root / "sibling"
            inner.mkdir()
            sibling.mkdir()
            link = inner / "escape"
            try:
                link.symlink_to(sibling, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"Host does not permit creating test symlinks: {exc}")
            with patch.object(run_eval, "BASE", inner):
                with self.assertRaisesRegex(ValueError, "escapes"):
                    run_eval.write_text("escape/leaked.json", "must not exist")
            self.assertEqual(list(sibling.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
