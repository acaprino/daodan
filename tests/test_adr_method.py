"""Behavioral tests of the ADR helper: lifecycle, versions, digests, drift, index and atomicity.

The examples and invariants are those of docs/adr/ADR-0004-adr-versions-and-drift.md.
"""

import contextlib
from datetime import date
import hashlib
import io
import json
import runpy
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/project-delivery/skills/adr-method/scripts/adr_tool.py"

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
CHANGED = BODY.replace("never accepts `qty <= 0`.", "never accepts `qty < 1`.")
FRONT_ORDER = ["adr_id", "version", "title", "status", "author", "scope", "governs_symbols", "depends_on",
               "created_from_task", "proposed_on", "proposed_at_sha", "accepted_on", "accepted_at_sha",
               "last_verified_sha", "retired_on", "retired_reason", "supersedes", "superseded_by", "changes"]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


class AdrToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        self.project.mkdir()
        self.adr = self.project / "docs/adr"
        self.runtime = runpy.run_path(str(SCRIPT))
        self.counter = 0
        self.today = date.today().isoformat()
        self.git("init", "-q")
        for key, value in (("user.name", "Test Author"), ("user.email", "adr@example.invalid"),
                           ("core.autocrlf", "false"), ("commit.gpgsign", "false")):
            self.git("config", key, value)

    def git(self, *arguments):
        return subprocess.run(["git", "-C", str(self.project), *arguments], capture_output=True,
                              text=True, encoding="utf-8", check=True).stdout.strip()

    def commit(self, files):
        for name, text in files.items():
            write(self.project / name, text)
        self.git("add", *files)
        self.git("commit", "-q", "-m", "change")
        return self.git("rev-parse", "HEAD")

    def run_tool(self, *argv, ok=True):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.runtime["main"](list(argv))
        if ok:
            self.assertEqual(code, 0, stderr.getvalue())
            return json.loads(stdout.getvalue()) if stdout.getvalue().startswith("{") else stdout.getvalue()
        self.assertEqual(code, 1, stdout.getvalue())
        return stderr.getvalue()

    def tool(self, command, *argv, ok=True):
        return self.run_tool(command, "--project", str(self.project), *argv, ok=ok)

    def body_file(self, text=BODY):
        self.counter += 1
        path = Path(self.temp.name) / f"body-{self.counter}.md"
        write(path, text)
        return str(path)

    def propose(self, title, slug, body=BODY, paths=("src/orders/**",), extra=(), ok=True):
        return self.tool("propose", "--title", title, "--slug", slug, "--task", "change-1", "--sha", "9c4e1b0a2d3f",
                         "--body", self.body_file(body), "--paths", *paths, *extra, ok=ok)

    def revise(self, adr, body=CHANGED, extra=(), ok=True):
        return self.tool("propose", "--revise", adr, "--task", "change-2", "--sha", "9c4e1b0a2d3f",
                         "--body", self.body_file(body), *extra, ok=ok)

    def digest(self, adr, which="proposed"):
        return self.tool("validate", "--adr", adr)[which]["digest"]

    def promote(self, adr, sha="aaaaaaa"):
        return self.tool("promote", "--adr", adr, "--sha", sha, "--expect-digest", self.digest(adr))

    def text(self, name):
        return (self.adr / name).read_text(encoding="utf-8")

    def snapshot(self):
        return {path.name: path.read_bytes() for path in sorted(self.adr.glob("*"))} if self.adr.is_dir() else {}

    def test_template_lists_the_three_machine_checked_sections(self):
        text = self.run_tool("template")
        for item in ("EX-001", "RA-001", "INV-001", "## Verified Interview Examples", "## Rejected Alternatives", "## Enforceable Invariants"):
            self.assertIn(item, text)

    def test_propose_allocates_identity_writes_front_matter_header_and_index(self):
        result = self.propose("Separate draft validation: order path", "draft-validation",
                              extra=("--modules", "orders.validation", "--symbols", "py:src/orders/validator.py#validate_order"))
        self.assertEqual((result["adr_id"], result["version"], result["changes"]), ("ADR-0001", 1, []))
        record = self.text("ADR-0001-draft-validation.md")
        self.assertEqual(result["digest"], hashlib.sha256(record.encode("utf-8")).hexdigest())
        front = record.split("\n---\n", 1)[0].split("\n")[1:]
        self.assertEqual([line.split(":", 1)[0] for line in front if line[:1].isalpha()], FRONT_ORDER)
        self.assertTrue(record.startswith("---\nadr_id: ADR-0001\nversion: 1\n"))
        self.assertIn('title: "Separate draft validation: order path"', record)
        self.assertIn("status: Proposed\nauthor: Test Author\n", record)
        self.assertIn('  - "py:src/orders/validator.py#validate_order"', record)
        self.assertIn(f"proposed_on: {self.today}\n", record)
        self.assertIn("retired_on: null\nretired_reason: null\n", record)
        self.assertIn("# ADR-0001: Separate draft validation: order path\n\n<!-- adr-header:start -->\n"
                      f"Version 1 · Proposed {self.today} by Test Author\n<!-- adr-header:end -->\n\n"
                      "## Context and Problem Statement\n", record)
        index = self.text("README.md")
        self.assertIn("<!-- adr-index:start -->", index)
        self.assertIn("[ADR-0001](<ADR-0001-draft-validation.md>)", index)
        self.assertEqual(self.tool("validate")["records"], 1)
        self.assertEqual(self.propose("Second", "second")["adr_id"], "ADR-0002")
        self.assertIn("slug must be", self.propose("Third", "v2-third", ok=False))

    def test_propose_refuses_placeholders_and_missing_sections_without_writing(self):
        skeleton = self.run_tool("template")
        before = self.snapshot()
        refusal = self.propose("Draft", "draft", body=skeleton, ok=False)
        self.assertIn("template placeholders", refusal)
        self.assertEqual(self.snapshot(), before)
        without = BODY.replace("## Enforceable Invariants", "## Invariants")
        refusal = self.tool("propose", "--title", "Draft", "--slug", "draft", "--task", "t", "--sha", "9c4e1b0a2d3f",
                            "--body", self.body_file(without), "--paths", "src/**", ok=False)
        self.assertIn("Enforceable Invariants", refusal)
        self.assertEqual(self.snapshot(), before)
        refusal = self.tool("propose", "--title", "Draft", "--slug", "draft", "--task", "t", "--sha", "9c4e1b0a2d3f",
                            "--body", self.body_file(), ok=False)
        self.assertIn("at least one path, module or domain", refusal)

    def test_resolve_returns_only_accepted_unsuperseded_records_for_the_scope(self):
        self.propose("Orders", "orders", paths=("src/orders/**",), extra=("--domains", "order-lifecycle"))
        self.propose("Billing", "billing", paths=("src/billing/invoice.py",), extra=("--modules", "billing"))
        self.propose("Pending", "pending", paths=("src/orders/**",))
        self.promote("ADR-0001", "aaaaaaa")
        self.promote("ADR-0002", "bbbbbbb")
        active = self.tool("resolve", "--paths", "src/orders/validator.py", "src/other.py")["active"]
        self.assertEqual([(item["adr_id"], item["version"]) for item in active], [("ADR-0001", 1)])
        self.assertIn("path src/orders/validator.py matches src/orders/**", active[0]["reasons"])
        self.assertEqual(active[0]["digest"], hashlib.sha256((self.adr / "ADR-0001-orders.md").read_bytes()).hexdigest())
        by_module = self.tool("resolve", "--modules", "billing")["active"]
        self.assertEqual([item["adr_id"] for item in by_module], ["ADR-0002"])
        self.assertEqual(self.tool("resolve", "--paths", "docs/x.md")["active"], [])
        self.propose("Successor", "successor", paths=("src/orders/**",), extra=("--supersedes", "ADR-0001"))
        self.promote("ADR-0004", "ccccccc")
        active = self.tool("resolve", "--paths", "src/orders/x.py", "--domains", "order-lifecycle")["active"]
        self.assertEqual([item["adr_id"] for item in active], ["ADR-0004"])

    def test_promote_is_one_transaction_with_bidirectional_supersession(self):
        self.propose("Old", "old")
        self.promote("ADR-0001", "aaaaaaa")
        self.propose("New", "new", extra=("--supersedes", "ADR-0001"))
        result = self.promote("ADR-0002", "bbbbbbb")
        self.assertEqual((result["superseded"], result["dependents_to_review"]), (["ADR-0001"], []))
        new, old = self.text("ADR-0002-new.md"), self.text("ADR-0001-old.md")
        self.assertIn("status: Accepted\n", new)
        self.assertIn(f"accepted_on: {self.today}\naccepted_at_sha: bbbbbbb\nlast_verified_sha: null\n", new)
        self.assertIn(f"\nVersion 1 · Accepted {self.today} at bbbbbbb · proposed {self.today} by Test Author\n", new)
        self.assertIn("status: Superseded\n", old)
        self.assertIn("superseded_by: ADR-0002\n", old)
        self.assertIn(f"\nVersion 1 · Superseded by ADR-0002 · proposed {self.today} by Test Author\n", old)
        self.assertEqual(old.count("<!-- adr-header:start -->"), 1)
        self.assertIn("## Enforceable Invariants", old)
        index = self.text("README.md")
        self.assertIn("| [ADR-0001](<ADR-0001-old.md>) | Old | ADR-0002 |", index)
        self.assertTrue(self.tool("validate")["valid"])
        refusal = self.tool("promote", "--adr", "ADR-0002", "--sha", "ddddddd", "--expect-digest", "0", ok=False)
        self.assertIn("ADR-0002 v1 is Accepted, only a Proposed record is promoted", refusal)

    def test_a_failed_promote_leaves_every_file_and_the_index_byte_identical(self):
        """INV-007: the future state is validated and the index rendered before any write."""
        self.propose("Old", "old")
        self.promote("ADR-0001", "aaaaaaa")
        self.propose("New", "new", extra=("--supersedes", "ADR-0001"))
        self.propose("Rival", "rival", extra=("--supersedes", "ADR-0001"))
        self.promote("ADR-0002", "bbbbbbb")
        before = self.snapshot()
        refusal = self.tool("promote", "--adr", "ADR-0003", "--sha", "ccccccc", "--expect-digest", self.digest("ADR-0003"), ok=False)
        self.assertIn("ADR-0001 is Superseded", refusal)
        self.assertEqual(self.snapshot(), before)
        self.revise("ADR-0002")
        self.propose("Successor", "successor", extra=("--supersedes", "ADR-0002"))
        self.promote("ADR-0004", "ddddddd")
        before = self.snapshot()
        refusal = self.tool("promote", "--adr", "ADR-0002", "--sha", "eeeeeee", "--expect-digest", self.digest("ADR-0002"), ok=False)
        self.assertIn("ADR-0002 v2 revises ADR-0002, which has no Accepted version left", refusal)
        self.assertEqual(self.snapshot(), before)

    def test_a_record_cannot_supersede_or_depend_on_a_proposed_record_or_itself(self):
        self.propose("Old", "old")
        refusal = self.propose("New", "new", extra=("--supersedes", "ADR-0001"), ok=False)
        self.assertIn("not Accepted", refusal)
        self.assertFalse((self.adr / "ADR-0002-new.md").exists())
        self.assertIn("ADR-0001 is not Accepted, so it cannot be a dependency",
                      self.propose("New", "new", extra=("--depends-on", "ADR-0001"), ok=False))
        self.assertIn("a version never supersedes its own decision",
                      self.propose("New", "new", extra=("--supersedes", "ADR-0002"), ok=False))
        self.assertIn("a record never depends on its own decision",
                      self.propose("New", "new", extra=("--depends-on", "ADR-0002"), ok=False))
        self.assertFalse((self.adr / "ADR-0002-new.md").exists())

    def test_hand_edits_that_break_the_invariants_are_caught_by_validate(self):
        self.propose("Old", "old")
        path = self.adr / "ADR-0001-old.md"
        text = path.read_text(encoding="utf-8")
        write(path, text.replace("status: Proposed", "status: Superseded"))
        self.assertIn("names superseded_by", self.tool("validate", ok=False))
        write(path, text.replace("status: Proposed", "status: Accepted"))
        self.assertIn("carries accepted_at_sha", self.tool("validate", ok=False))
        write(path, text.replace("version: 1\n", ""))
        self.assertIn("front matter is missing version", self.tool("validate", ok=False))
        write(path, text.replace("version: 1\n", "version: 2\n"))
        self.assertIn("version 2 is named ADR-0001-v2-<slug>.md", self.tool("validate", ok=False))
        write(path, text)
        index = self.adr / "README.md"
        write(index, index.read_text(encoding="utf-8").replace("| Old |", "| Renamed |"))
        self.assertIn("stale", self.tool("validate", ok=False))
        self.tool("index")
        self.assertTrue(self.tool("validate")["valid"])

    def test_index_keeps_prose_outside_its_markers(self):
        self.tool("init-index")
        index = self.adr / "README.md"
        write(index, "# Decisions of this project\n\nRead the active table first.\n\n"
                     "<!-- adr-index:start -->\nstale\n<!-- adr-index:end -->\n\nFooter kept.\n")
        self.propose("Orders", "orders")
        text = index.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Decisions of this project\n\nRead the active table first.\n"))
        self.assertTrue(text.rstrip().endswith("Footer kept."))
        self.assertIn("[ADR-0001](<ADR-0001-orders.md>)", text)
        self.assertNotIn("\nstale\n", text)
        write(index, "# Decisions without markers\n")
        before = self.snapshot()
        self.assertIn("lacks the adr-index markers", self.propose("Billing", "billing", ok=False))
        self.assertEqual(self.snapshot(), before)

    def test_adr_directory_stays_inside_the_project(self):
        refusal = self.tool("init-index", "--dir", "../outside", ok=False)
        self.assertIn("without traversal", refusal)
        self.assertFalse((Path(self.temp.name) / "outside").exists())

    def test_revise_writes_the_next_version_with_the_items_whose_text_changed(self):
        """EX-001, INV-002."""
        self.propose("Orders", "orders", extra=("--modules", "orders", "--symbols", "py:src/orders/validator.py#validate_order"))
        self.promote("ADR-0001")
        result = self.revise("ADR-0001")
        self.assertEqual((result["version"], result["changes"], result["path"], result["status"]),
                         (2, ["INV-001"], "docs/adr/ADR-0001-v2-orders.md", "Proposed"))
        record = self.text("ADR-0001-v2-orders.md")
        self.assertIn("adr_id: ADR-0001\nversion: 2\ntitle: Orders\nstatus: Proposed\n", record)
        self.assertIn("  paths:\n    - src/orders/**\n  modules:\n    - orders\n", record)
        self.assertIn('governs_symbols:\n  - "py:src/orders/validator.py#validate_order"\n', record)
        self.assertIn("changes:\n  - INV-001\n---\n", record)
        self.assertIn(f"# ADR-0001: Orders\n\n<!-- adr-header:start -->\nVersion 2 · Proposed {self.today} by Test Author\n", record)
        self.tool("retire", "--adr", "ADR-0001", "--reason", "wrong bound", "--expect-digest", result["digest"])
        reflowed = (BODY.replace("- **EX-003** (draft): Input: `validate_draft(qty=0)` -> Expected: "
                                 "`DraftValidationResult(executable=False)`\n", "")
                    .replace("invariant.\n", "invariant.\n- **RA-002**: a second validator class; two owners of one rule.\n")
                    .replace("order reaches `OrderRouter.submit()`.", "order reaches\n  `OrderRouter.submit()`."))
        result = self.revise("ADR-0001", reflowed, extra=("--title", "Orders, revised", "--paths", "src/orders/validator.py"))
        self.assertEqual((result["version"], result["changes"]), (3, ["EX-003", "RA-002"]))
        record = self.text("ADR-0001-v3-orders.md")
        self.assertIn("# ADR-0001: Orders, revised\n", record)
        self.assertIn("  paths:\n    - src/orders/validator.py\n  modules:\n    - orders\n", record)
        self.assertIn("keeps the slug of version 1", self.revise("ADR-0001", extra=("--slug", "other"), ok=False))

    def test_approval_accepts_a_revision_and_supersedes_the_previous_version(self):
        """EX-002, EX-010, INV-001, INV-003, INV-009."""
        head = self.commit({"src/orders/validator.py": "def validate_order(): pass\n"})
        self.propose("Orders", "orders")
        self.promote("ADR-0001", head)
        self.revise("ADR-0001")
        self.git("add", "docs/adr")
        self.git("commit", "-q", "-m", "merge the record")
        head = self.git("rev-parse", "HEAD")
        self.assertEqual(self.tool("validate", "--adr", "ADR-0001")["proposed"]["version"], 2)
        result = self.tool("promote", "--adr", "ADR-0001", "--sha", head, "--expect-digest", self.digest("ADR-0001"))
        self.assertEqual((result["version"], result["status"], result["superseded"], result["dependents_to_review"]),
                         (2, "Accepted", ["ADR-0001 v1"], []))
        current, previous = self.text("ADR-0001-v2-orders.md"), self.text("ADR-0001-orders.md")
        self.assertIn(f"accepted_on: {self.today}\naccepted_at_sha: {head}\nlast_verified_sha: null\n", current)
        self.assertIn(f"\nVersion 2 · Accepted {self.today} at {head[:7]} · proposed {self.today} by Test Author\n", current)
        self.assertIn("status: Superseded\n", previous)
        self.assertIn("superseded_by: ADR-0001 v2\n", previous)
        self.assertIn("\nVersion 1 · Superseded by ADR-0001 v2 · proposed", previous)
        active = self.tool("resolve", "--paths", "src/orders/validator.py")["active"]
        self.assertEqual([(item["adr_id"], item["version"], item["digest"]) for item in active],
                         [("ADR-0001", 2, result["digest"])])
        index = self.text("README.md")
        self.assertIn("| [ADR-0001 v2](<ADR-0001-v2-orders.md>) | Orders |", index)
        self.assertIn("| [ADR-0001](<ADR-0001-orders.md>) | Orders | ADR-0001 v2 |", index)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        touched = [line.split(maxsplit=1)[1] for line in self.git("status", "--porcelain", "--untracked-files=all").splitlines()]
        self.assertEqual(sorted(touched), ["docs/adr/ADR-0001-orders.md", "docs/adr/ADR-0001-v2-orders.md", "docs/adr/README.md"])

    def test_a_record_changed_since_it_was_read_or_a_held_lock_is_refused_without_writes(self):
        """EX-003, INV-004."""
        self.propose("Orders", "orders")
        self.promote("ADR-0001")
        self.revise("ADR-0001")
        read = self.digest("ADR-0001")
        path = self.adr / "ADR-0001-v2-orders.md"
        write(path, path.read_text(encoding="utf-8").replace("`qty < 1`", "`qty < 2`"))
        found = hashlib.sha256(path.read_bytes()).hexdigest()
        before = self.snapshot()
        refusal = self.tool("promote", "--adr", "ADR-0001", "--sha", "bbbbbbb", "--expect-digest", read, ok=False)
        self.assertIn(f"ADR-0001 v2 changed since it was read: expected {read}, found {found}", refusal)
        self.assertIn("ADR-0001 v2 changed since it was read",
                      self.tool("retire", "--adr", "ADR-0001", "--reason", "x", "--expect-digest", read, ok=False))
        self.assertIn("ADR-0001 v1 changed since it was read",
                      self.tool("verify", "--adr", "ADR-0001", "--sha", "bbbbbbb", "--expect-digest", read, ok=False))
        self.assertEqual(self.snapshot(), before)
        lock = self.adr / ".adr-lock"
        write(lock, "pid 4242 since 2026-10-25T10:00:00+00:00\n")
        before = self.snapshot()
        for argv in (("promote", "--adr", "ADR-0001", "--sha", "bbbbbbb", "--expect-digest", found),
                     ("verify", "--adr", "ADR-0001", "--sha", "bbbbbbb", "--expect-digest", self.digest("ADR-0001", "accepted")),
                     ("retire", "--adr", "ADR-0001", "--reason", "x", "--expect-digest", found),
                     ("index",)):
            self.assertIn(".adr-lock is held by pid 4242 since 2026-10-25T10:00:00+00:00", self.tool(*argv, ok=False))
        self.assertIn("held by pid 4242", self.propose("Billing", "billing", ok=False))
        self.assertEqual(self.snapshot(), before)
        lock.unlink()
        self.tool("promote", "--adr", "ADR-0001", "--sha", "bbbbbbb", "--expect-digest", found)
        self.assertFalse(lock.exists())

    def test_a_decision_has_one_open_version_and_one_accepted_version(self):
        """EX-004, INV-001."""
        self.propose("Orders", "orders")
        self.promote("ADR-0001")
        self.revise("ADR-0001")
        before = self.snapshot()
        refusal = self.revise("ADR-0001", BODY, ok=False)
        self.assertIn("ADR-0001 v2 is still Proposed: a decision has one open version at a time", refusal)
        self.assertEqual(self.snapshot(), before)
        self.propose("Billing", "billing")
        self.assertIn("ADR-0002 has no Accepted version to revise", self.revise("ADR-0002", ok=False))
        path = self.adr / "ADR-0001-v2-orders.md"
        write(path, path.read_text(encoding="utf-8").replace("status: Proposed", "status: Accepted")
              .replace("accepted_on: null", f"accepted_on: {self.today}").replace("accepted_at_sha: null", "accepted_at_sha: bbbbbbb"))
        self.assertIn("ADR-0001: a decision has at most one Accepted version", self.tool("validate", ok=False))
        self.assertIn("at most one Accepted version", self.tool("resolve", "--paths", "src/orders/x.py", ok=False))

    def test_drift_lists_governed_files_changed_since_the_last_verification(self):
        """EX-005, EX-006, INV-005."""
        start = self.commit({"src/orders/validator.py": "v0\n", "src/billing/invoice.py": "v0\n", "src/other.py": "v0\n"})
        self.propose("Orders", "orders", extra=("--symbols", "py:src/billing/invoice.py#total"))
        self.propose("Pending", "pending")
        self.promote("ADR-0001", start)
        self.assertEqual(self.tool("validate", "--sha", start)["drifted"], [{"adr_id": "ADR-0001", "version": 1, "files": None}])
        verified = self.tool("verify", "--adr", "ADR-0001", "--sha", start, "--expect-digest", self.digest("ADR-0001", "accepted"))
        self.assertEqual((verified["status"], verified["last_verified_sha"]), ("Accepted", start))
        self.assertEqual(self.tool("validate", "--sha", start)["drifted"], [])
        unrelated = self.commit({"src/other.py": "v1\n"})
        self.assertEqual(self.tool("validate", "--sha", unrelated)["drifted"], [])
        governed = self.commit({"src/orders/validator.py": "v2\n", "src/billing/invoice.py": "v2\n"})
        drift = [{"adr_id": "ADR-0001", "version": 1, "files": ["src/billing/invoice.py", "src/orders/validator.py"]}]
        self.assertEqual(self.tool("validate", "--sha", governed)["drifted"], drift)
        self.assertEqual(self.tool("validate", "--adr", "ADR-0001", "--sha", governed)["drifted"], drift)
        self.tool("verify", "--adr", "ADR-0001", "--sha", governed, "--expect-digest", verified["digest"])
        self.assertEqual(self.tool("validate", "--sha", governed)["drifted"], [])
        self.assertIn(f"last_verified_sha: {governed}\n", self.text("ADR-0001-orders.md"))
        self.assertIn("sha must be a commit sha", self.tool("validate", "--sha", "HEAD", ok=False))

    def test_promote_lists_dependents_to_review_and_never_rewrites_them(self):
        """EX-007, INV-008."""
        self.propose("Base", "base")
        self.promote("ADR-0001")
        self.propose("Dependent", "dependent", paths=("src/billing/**",), extra=("--depends-on", "ADR-0001"))
        self.promote("ADR-0002")
        dependent = (self.adr / "ADR-0002-dependent.md").read_bytes()
        self.assertIn(b"depends_on:\n  - ADR-0001\n", dependent)
        self.revise("ADR-0001")
        self.assertEqual(self.promote("ADR-0001")["dependents_to_review"], ["ADR-0002"])
        self.propose("Successor", "successor", extra=("--supersedes", "ADR-0001"))
        result = self.promote("ADR-0003")
        self.assertEqual((result["superseded"], result["dependents_to_review"]), (["ADR-0001"], ["ADR-0002"]))
        self.assertEqual((self.adr / "ADR-0002-dependent.md").read_bytes(), dependent)
        self.propose("Unrelated", "unrelated", paths=("src/other/**",))
        self.assertEqual(self.promote("ADR-0004")["dependents_to_review"], [])
        self.assertIn("ADR-0001 is not Accepted, so it cannot be a dependency", self.revise("ADR-0002", BODY, ok=False))
        self.assertIn("a record never depends on its own decision",
                      self.revise("ADR-0002", BODY, extra=("--depends-on", "ADR-0002"), ok=False))
        result = self.revise("ADR-0002", BODY, extra=("--depends-on", "ADR-0003"))
        self.assertIn("depends_on:\n  - ADR-0003\n", self.text("ADR-0002-v2-dependent.md"))

    def test_retire_abandons_only_a_proposed_record_for_good(self):
        """EX-008, INV-006."""
        self.propose("Map", "map")
        result = self.tool("retire", "--adr", "ADR-0001", "--reason", "replaced by the decision map",
                           "--expect-digest", self.digest("ADR-0001"))
        self.assertEqual((result["status"], result["version"], result["retired_on"]), ("Abandoned", 1, self.today))
        record = self.text("ADR-0001-map.md")
        self.assertIn(f"status: Abandoned\n", record)
        self.assertIn(f"retired_on: {self.today}\nretired_reason: replaced by the decision map\n", record)
        self.assertIn(f"\nVersion 1 · Abandoned {self.today}: replaced by the decision map · proposed {self.today} by Test Author\n", record)
        index = self.text("README.md")
        self.assertIn(f"## Abandoned\n\n| ADR | Title | Retired on | Reason |\n|---|---|---|---|\n"
                      f"| [ADR-0001](<ADR-0001-map.md>) | Map | {self.today} | replaced by the decision map |", index)
        self.assertEqual(self.tool("resolve", "--paths", "src/orders/x.py")["active"], [])
        self.assertEqual(self.tool("validate", "--adr", "ADR-0001")["proposed"], None)
        before = self.snapshot()
        digest = hashlib.sha256((self.adr / "ADR-0001-map.md").read_bytes()).hexdigest()
        self.assertIn("ADR-0001 v1 is Abandoned, only a Proposed record is promoted",
                      self.tool("promote", "--adr", "ADR-0001", "--sha", "aaaaaaa", "--expect-digest", digest, ok=False))
        self.assertIn("only a Proposed record is retired",
                      self.tool("retire", "--adr", "ADR-0001", "--reason", "again", "--expect-digest", digest, ok=False))
        self.assertIn("only an Accepted record is verified",
                      self.tool("verify", "--adr", "ADR-0001", "--sha", "aaaaaaa", "--expect-digest", digest, ok=False))
        self.assertEqual(self.snapshot(), before)
        self.propose("Kept", "kept")
        self.promote("ADR-0002")
        self.assertIn("ADR-0002 v1 is Accepted, only a Proposed record is retired",
                      self.tool("retire", "--adr", "ADR-0002", "--reason", "x", "--expect-digest", self.digest("ADR-0002", "accepted"), ok=False))
        self.assertIn("retire requires --reason", self.tool("retire", "--adr", "ADR-0002", "--expect-digest", "0", ok=False))
        self.assertIn("retire requires a reason", self.tool("retire", "--adr", "ADR-0002", "--reason", " ", "--expect-digest", "0", ok=False))

    def test_a_version_never_supersedes_its_own_decision(self):
        """EX-009, INV-008."""
        self.propose("Orders", "orders")
        self.promote("ADR-0001")
        before = self.snapshot()
        refusal = self.revise("ADR-0001", extra=("--supersedes", "ADR-0001"), ok=False)
        self.assertIn("a version never supersedes its own decision", refusal)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
