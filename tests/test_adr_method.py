"""Behavioral tests of the ADR helper: lifecycle, index, resolution and atomicity."""

import contextlib
import io
import json
import runpy
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/project-knowledge/skills/adr-method/scripts/adr_tool.py"

BODY = """## Context and Problem Statement

`validate_order()` in `src/orders/validator.py:42` rejects `qty <= 0`, while drafts need it.

## Decision Drivers

- Drafts are saved incomplete; executable orders are not.

## Decision

Separate `validate_draft()` from `validate_order()`.

## Verified Interview Examples

- **EX-001** (nominal): Input: `validate_order(qty=10)` -> Expected: `ValidatedOrder(qty=10)`
- **EX-002** (boundary): Input: `validate_order(qty=0)` -> Expected: raises `InvalidQuantityError`
- **EX-003** (draft): Input: `validate_draft(qty=0)` -> Expected: `DraftValidationResult(executable=False)`

## Rejected Alternatives

- **RA-001**: a boolean `allow_zero_qty` on `validate_order()`; weakens the execution invariant.

## Enforceable Invariants

- **INV-001**: `validate_order()` never accepts `qty <= 0`.
- **INV-002**: no `executable == False` order reaches `OrderRouter.submit()`.

## Consequences

- One new module, two tests.

## Confirmation

- `tests/orders/test_validator.py`
"""


class AdrToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        self.project.mkdir()
        self.adr = self.project / "docs/adr"
        self.runtime = runpy.run_path(str(SCRIPT))
        self.counter = 0

    def run_tool(self, *argv, ok=True):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.runtime["main"](list(argv))
        if ok:
            self.assertEqual(code, 0, stderr.getvalue())
            return json.loads(stdout.getvalue()) if stdout.getvalue().startswith("{") else stdout.getvalue()
        self.assertEqual(code, 1, stdout.getvalue())
        return stderr.getvalue()

    def body_file(self, text=BODY):
        self.counter += 1
        path = Path(self.temp.name) / f"body-{self.counter}.md"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def propose(self, title, slug, body=BODY, paths=("src/orders/**",), extra=(), ok=True):
        return self.run_tool("propose", "--project", str(self.project), "--title", title, "--slug", slug,
                             "--task", "change-1", "--sha", "9c4e1b0a2d3f", "--body", self.body_file(body),
                             "--paths", *paths, *extra, ok=ok)

    def snapshot(self):
        return {path.name: path.read_bytes() for path in sorted(self.adr.glob("*"))} if self.adr.is_dir() else {}

    def test_template_lists_the_three_machine_checked_sections(self):
        text = self.run_tool("template")
        for item in ("EX-001", "RA-001", "INV-001", "## Verified Interview Examples", "## Rejected Alternatives", "## Enforceable Invariants"):
            self.assertIn(item, text)

    def test_propose_allocates_identity_writes_front_matter_and_index(self):
        result = self.propose("Separate draft validation: order path", "draft-validation",
                              extra=("--modules", "orders.validation", "--symbols", "py:src/orders/validator.py#validate_order"))
        self.assertEqual(result["adr_id"], "ADR-0001")
        record = (self.adr / "ADR-0001-draft-validation.md").read_text(encoding="utf-8")
        self.assertTrue(record.startswith("---\nadr_id: ADR-0001\n"))
        self.assertIn('title: "Separate draft validation: order path"', record)
        self.assertIn("status: Proposed\n", record)
        self.assertIn('  - "py:src/orders/validator.py#validate_order"', record)
        self.assertIn("# ADR-0001: Separate draft validation: order path\n", record)
        index = (self.adr / "README.md").read_text(encoding="utf-8")
        self.assertIn("<!-- adr-index:start -->", index)
        self.assertIn("[ADR-0001](<ADR-0001-draft-validation.md>)", index)
        self.assertEqual(self.run_tool("validate", "--project", str(self.project))["records"], 1)
        self.assertEqual(self.propose("Second", "second")["adr_id"], "ADR-0002")

    def test_propose_refuses_placeholders_and_missing_sections_without_writing(self):
        skeleton = self.run_tool("template")
        before = self.snapshot()
        refusal = self.propose("Draft", "draft", body=skeleton, ok=False)
        self.assertIn("template placeholders", refusal)
        self.assertEqual(self.snapshot(), before)
        without = BODY.replace("## Enforceable Invariants", "## Invariants")
        refusal = self.run_tool("propose", "--project", str(self.project), "--title", "Draft", "--slug", "draft",
                                "--task", "t", "--sha", "9c4e1b0a2d3f", "--body", self.body_file(without),
                                "--paths", "src/**", ok=False)
        self.assertIn("Enforceable Invariants", refusal)
        self.assertEqual(self.snapshot(), before)
        refusal = self.run_tool("propose", "--project", str(self.project), "--title", "Draft", "--slug", "draft",
                                "--task", "t", "--sha", "9c4e1b0a2d3f", "--body", self.body_file(), ok=False)
        self.assertIn("at least one path, module or domain", refusal)

    def test_resolve_returns_only_accepted_unsuperseded_records_for_the_scope(self):
        self.propose("Orders", "orders", paths=("src/orders/**",), extra=("--domains", "order-lifecycle"))
        self.propose("Billing", "billing", paths=("src/billing/invoice.py",), extra=("--modules", "billing"))
        self.propose("Pending", "pending", paths=("src/orders/**",))
        self.run_tool("promote", "--project", str(self.project), "--adr", "ADR-0001", "--sha", "aaaaaaa")
        self.run_tool("promote", "--project", str(self.project), "--adr", "ADR-0002", "--sha", "bbbbbbb")
        active = self.run_tool("resolve", "--project", str(self.project), "--paths", "src/orders/validator.py", "src/other.py")["active"]
        self.assertEqual([item["adr_id"] for item in active], ["ADR-0001"])
        self.assertIn("path src/orders/validator.py matches src/orders/**", active[0]["reasons"])
        by_module = self.run_tool("resolve", "--project", str(self.project), "--modules", "billing")["active"]
        self.assertEqual([item["adr_id"] for item in by_module], ["ADR-0002"])
        self.assertEqual(self.run_tool("resolve", "--project", str(self.project), "--paths", "docs/x.md")["active"], [])
        self.propose("Successor", "successor", paths=("src/orders/**",), extra=("--supersedes", "ADR-0001"))
        self.run_tool("promote", "--project", str(self.project), "--adr", "ADR-0004", "--sha", "ccccccc")
        active = self.run_tool("resolve", "--project", str(self.project), "--paths", "src/orders/x.py", "--domains", "order-lifecycle")["active"]
        self.assertEqual([item["adr_id"] for item in active], ["ADR-0004"])

    def test_promote_is_one_transaction_with_bidirectional_supersession(self):
        self.propose("Old", "old")
        self.run_tool("promote", "--project", str(self.project), "--adr", "ADR-0001", "--sha", "aaaaaaa")
        self.propose("New", "new", extra=("--supersedes", "ADR-0001"))
        result = self.run_tool("promote", "--project", str(self.project), "--adr", "ADR-0002", "--sha", "bbbbbbb")
        self.assertEqual(result["superseded"], ["ADR-0001"])
        new = (self.adr / "ADR-0002-new.md").read_text(encoding="utf-8")
        old = (self.adr / "ADR-0001-old.md").read_text(encoding="utf-8")
        self.assertIn("status: Accepted\n", new)
        self.assertIn("accepted_at_sha: bbbbbbb\n", new)
        self.assertIn("last_verified_sha: bbbbbbb\n", new)
        self.assertIn("status: Superseded\n", old)
        self.assertIn("superseded_by: ADR-0002\n", old)
        self.assertIn("## Enforceable Invariants", old)
        index = (self.adr / "README.md").read_text(encoding="utf-8")
        self.assertIn("| [ADR-0001](<ADR-0001-old.md>) | Old | ADR-0002 |", index)
        self.assertTrue(self.run_tool("validate", "--project", str(self.project))["valid"])
        refusal = self.run_tool("promote", "--project", str(self.project), "--adr", "ADR-0002", "--sha", "ddddddd", ok=False)
        self.assertIn("only a Proposed record is promoted", refusal)

    def test_promote_writes_nothing_when_the_future_state_is_invalid(self):
        self.propose("Old", "old")
        self.run_tool("promote", "--project", str(self.project), "--adr", "ADR-0001", "--sha", "aaaaaaa")
        self.propose("New", "new", extra=("--supersedes", "ADR-0001"))
        self.propose("Rival", "rival", extra=("--supersedes", "ADR-0001"))
        self.run_tool("promote", "--project", str(self.project), "--adr", "ADR-0002", "--sha", "bbbbbbb")
        before = self.snapshot()
        refusal = self.run_tool("promote", "--project", str(self.project), "--adr", "ADR-0003", "--sha", "ccccccc", ok=False)
        self.assertIn("ADR-0001 is Superseded", refusal)
        self.assertEqual(self.snapshot(), before)

    def test_a_record_cannot_supersede_a_proposed_record_or_itself(self):
        self.propose("Old", "old")
        refusal = self.propose("New", "new", extra=("--supersedes", "ADR-0001"), ok=False)
        self.assertIn("not Accepted", refusal)
        self.assertFalse((self.adr / "ADR-0002-new.md").exists())

    def test_hand_edits_that_break_the_invariants_are_caught_by_validate(self):
        self.propose("Old", "old")
        path = self.adr / "ADR-0001-old.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("status: Proposed", "status: Superseded"), encoding="utf-8")
        self.assertIn("names superseded_by", self.run_tool("validate", "--project", str(self.project), ok=False))
        path.write_text(text.replace("status: Proposed", "status: Accepted"), encoding="utf-8")
        self.assertIn("carries accepted_at_sha", self.run_tool("validate", "--project", str(self.project), ok=False))
        path.write_text(text, encoding="utf-8")
        index = self.adr / "README.md"
        index.write_text(index.read_text(encoding="utf-8").replace("| Old |", "| Renamed |"), encoding="utf-8")
        self.assertIn("stale", self.run_tool("validate", "--project", str(self.project), ok=False))
        self.run_tool("index", "--project", str(self.project))
        self.assertTrue(self.run_tool("validate", "--project", str(self.project))["valid"])

    def test_index_keeps_prose_outside_its_markers(self):
        self.run_tool("init-index", "--project", str(self.project))
        index = self.adr / "README.md"
        index.write_text("# Decisions of this project\n\nRead the active table first.\n\n" + index.read_text(encoding="utf-8").split("<!-- adr-index:start -->", 1)[0].join(("", "")) + "<!-- adr-index:start -->\nstale\n<!-- adr-index:end -->\n\nFooter kept.\n", encoding="utf-8")
        self.propose("Orders", "orders")
        text = index.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Decisions of this project\n\nRead the active table first.\n"))
        self.assertTrue(text.rstrip().endswith("Footer kept."))
        self.assertIn("[ADR-0001](<ADR-0001-orders.md>)", text)
        self.assertNotIn("\nstale\n", text)

    def test_adr_directory_stays_inside_the_project(self):
        refusal = self.run_tool("init-index", "--project", str(self.project), "--dir", "../outside", ok=False)
        self.assertIn("without traversal", refusal)
        self.assertFalse((Path(self.temp.name) / "outside").exists())


if __name__ == "__main__":
    unittest.main()
