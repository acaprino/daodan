"""Consumers of the code-context receipt keep their owners, independence and limits.

The consumer matrix in docs/plugins/codebase-map.md is the single statement of
what each command reads from a context packet. These checks keep it tied to the
workflows that exist and to the instructions that actually carry each rule.
"""
import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
LIFECYCLE = PLUGINS / "project-lifecycle/skills/lifecycle-method/references"
PAGE = ROOT / "docs/plugins/codebase-map.md"
COLUMNS = ("Command", "Input used", "Output", "Freshness", "Recovery", "Limits")
COMMANDS = {"new-feature", "fix-bug", "refactor-code", "continue-task", "finish-task",
            "write-docs", "write-tests", "review-changes", "review-branch", "map-code"}


def read(path):
    return " ".join(Path(path).read_text(encoding="utf-8").split())


def matrix():
    page = PAGE.read_text(encoding="utf-8")
    section = page.split("### Context consumers\n", 1)[1].split("\n#", 1)[0]
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in section.splitlines() if line.startswith("|")]
    header, body = rows[0], [row for row in rows[2:] if row]
    return header, body


class ContextConsumerTests(unittest.TestCase):
    def test_matrix_names_every_consumer_with_all_five_facts(self):
        header, body = matrix()
        self.assertEqual(tuple(header), COLUMNS)
        found = {name for row in body for name in re.findall(r"/daodan:([a-z-]+)", row[0])}
        self.assertEqual(found, COMMANDS)
        for row in body:
            self.assertEqual(len(row), len(COLUMNS), row)
            self.assertTrue(all(cell for cell in row), row)

    def test_every_matrix_command_is_a_registered_workflow(self):
        workflows = {path.stem for path in (PLUGINS / "daodan/workflows").glob("*.toml")}
        self.assertLessEqual(COMMANDS, workflows)

    def test_lifecycle_entries_declare_the_context_contract_they_consume(self):
        for name in ("new-feature", "fix-bug", "refactor-code", "continue-task", "finish-task"):
            with self.subTest(command=name):
                workflow = tomllib.loads((PLUGINS / f"daodan/workflows/{name}.toml").read_text(encoding="utf-8"))
                self.assertIn("codebase-map/contracts/context.toml", workflow["contract"]["shared_schemas"])

    def test_knowledge_work_binds_a_packet_by_digest_and_limits_stale_cards(self):
        text = read(PLUGINS / "project-knowledge/skills/project-knowledge/references/preparation.md")
        for fragment in ("context packet binds by digest", "fresh cards", "verified source blocks",
                         "stale or unread cards are leads", "gaps are documented limits"):
            self.assertIn(fragment, text)

    def test_independent_derivation_never_receives_packets_slices_receipts_or_cards(self):
        text = (PLUGINS / "senior-review/roles/premise-auditor.md").read_text(encoding="utf-8")
        forbidden = text.split("**Forbidden inputs.**", 1)[1].split("**Mandate", 1)[0]
        for fragment in ("context packet", "map slice", "lifecycle receipt", "semantic card"):
            self.assertIn(fragment, forbidden)
        grounding = read(PLUGINS / "senior-review/skills/review-preparation/references/candidate-grounding.md")
        self.assertIn("a lifecycle packet leads and replaces no source reading", grounding)
        self.assertIn("Keep premise derivation blind to maps", grounding)

    def test_test_obligations_reach_their_owner_without_a_new_dependency(self):
        verify = read(LIFECYCLE / "verify.md")
        self.assertIn("Route packet `validation_obligations` to `testing:test-writer`", verify)
        self.assertIn("confirms each oracle", verify)
        testing = tomllib.loads((PLUGINS / "testing/plugin.toml").read_text(encoding="utf-8"))
        self.assertNotIn("codebase-map", testing["dependencies"]["required"])
        self.assertNotIn("project-lifecycle", testing["dependencies"]["required"])

    def test_workers_receive_the_verified_task_packet_and_nothing_wider(self):
        brief = read(LIFECYCLE / "worker-brief.md")
        self.assertIn("read context: <verified `task-packet`", brief)
        self.assertIn("write_set: <exact paths; nothing else may change>", brief)

    def test_finish_reports_residual_obligations_and_realign_invalidates_packets(self):
        self.assertIn("Report the last receipt's residual obligations", read(LIFECYCLE / "finish.md"))
        realign = read(LIFECYCLE / "realign.md")
        self.assertIn("Invalidate affected packets", realign)
        self.assertIn("retain obligations", realign)

    def test_matrix_limits_state_the_static_boundary(self):
        page = PAGE.read_text(encoding="utf-8")
        section = page.split("### Context consumers\n", 1)[1].split("\n#", 1)[0]
        for fragment in ("static", "no write authority", "runtime"):
            self.assertIn(fragment, section)


if __name__ == "__main__":
    unittest.main()
