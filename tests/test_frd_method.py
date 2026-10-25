"""Behavioral tests of evidence-bound FRD lifecycle, spans, merge and conflicts."""

import contextlib
import copy
import hashlib
import io
import json
import os
import runpy
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/project-delivery/skills/frd-method/scripts/frd_tool.py"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


class FrdToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        self.project.mkdir()
        self.frd = self.project / "docs/frd"
        self.runtime = runpy.run_path(str(SCRIPT))
        self.counter = 0
        self.source_text = (
            "😀 Prefazione unicode.\n"
            "Alice works for Acme in Milan.\n"
            "A consultant can reopen a paused task.\n"
            "A consultant can reopen an assigned task.\n"
            "Alice Rossi works for Acme in Milan.\n"
        )
        write(self.project / "docs/source.md", self.source_text)
        write(self.project / "docs/alternate.md", self.source_text)

    def run_tool(self, *argv, ok=True):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.runtime["main"](list(argv))
        if ok:
            self.assertEqual(code, 0, stderr.getvalue())
            return json.loads(stdout.getvalue())
        self.assertEqual(code, 1, stdout.getvalue())
        return stderr.getvalue()

    def tool(self, command, *argv, ok=True):
        return self.run_tool(command, "--project", str(self.project), *argv, ok=ok)

    def evidence(self, excerpt, path="docs/source.md", occurrence=0):
        raw = (self.project / path).read_bytes()
        text = raw.decode("utf-8")
        start = -1
        for _ in range(occurrence + 1):
            start = text.index(excerpt, start + 1)
        return {
            "path": path,
            "document_sha256": hashlib.sha256(raw).hexdigest(),
            "start": start,
            "end": start + len(excerpt),
            "excerpt": excerpt,
        }

    def data(self):
        requirement = "A consultant can reopen a paused task."
        return {
            "requirements": [
                {"id": "REQ-001", "text": requirement, "evidence": [self.evidence(requirement)]},
            ],
            "entities": [
                {"id": "ENT-001", "entity_type": "PERSON", "name": "Alice",
                 "evidence": [self.evidence("Alice")]},
                {"id": "ENT-002", "entity_type": "ORGANIZATION", "name": "Acme",
                 "evidence": [self.evidence("Acme")]},
                {"id": "ENT-003", "entity_type": "LOCATION", "name": "Milan",
                 "evidence": [self.evidence("Milan")]},
            ],
            "relationships": [
                {"id": "REL-001", "source": "ENT-001", "target": "ENT-002", "type": "WORKS_FOR",
                 "evidence": [self.evidence("Alice works for Acme")]},
            ],
        }

    def data_file(self, data):
        self.counter += 1
        path = Path(self.temp.name) / f"data-{self.counter}.json"
        write(path, json.dumps(data, ensure_ascii=False))
        return str(path)

    def item_file(self, item):
        return self.data_file(item)

    def propose(self, data=None, ok=True):
        return self.tool("propose", "--title", "Task recovery", "--slug", "task-recovery", "--task", "change-1",
                         "--sha", "9c4e1b0a2d3f", "--data", self.data_file(data or self.data()), ok=ok)

    def record(self, version=1):
        name = "FRD-0001-task-recovery.json" if version == 1 else f"FRD-0001-v{version}-task-recovery.json"
        return json.loads((self.frd / name).read_text(encoding="utf-8"))

    def digest(self, which="proposed", identity="FRD-0001"):
        return self.tool("validate", "--frd", identity)[which]["digest"]

    def item(self, identity, version=1):
        data = self.record(version)
        return next(item for key in ("requirements", "entities", "relationships")
                    for item in data[key] if item["id"] == identity)

    def resolve(self, identity, status, data=None, conflict=None, digest=None, ok=True):
        argv = ["--frd", "FRD-0001", "--item", identity, "--status", status,
                "--expect-digest", digest or self.digest()]
        if data is not None:
            argv += ["--data", self.item_file(data)]
        if conflict:
            argv += ["--conflict", conflict]
        return self.tool("resolve", *argv, ok=ok)

    def promote(self, sha="aaaaaaa", ok=True):
        return self.tool("promote", "--frd", "FRD-0001", "--sha", sha,
                         "--expect-digest", self.digest(), ok=ok)

    def snapshot(self):
        return {path.name: path.read_bytes() for path in sorted(self.frd.glob("*"))} if self.frd.is_dir() else {}

    def test_propose_validates_entities_relationships_and_unicode_spans(self):
        source = self.data()
        result = self.propose(source)
        self.assertEqual((result["frd_id"], result["version"], result["status"]),
                         ("FRD-0001", 1, "Proposed"))
        record = self.record()
        self.assertEqual([item["entity_type"] for item in record["entities"]],
                         ["PERSON", "ORGANIZATION", "LOCATION"])
        self.assertEqual((record["relationships"][0]["source"], record["relationships"][0]["target"],
                          record["relationships"][0]["type"]), ("ENT-001", "ENT-002", "WORKS_FOR"))
        evidence = record["requirements"][0]["evidence"][0]
        text = (self.project / evidence["path"]).read_bytes().decode("utf-8")
        self.assertEqual(text[evidence["start"]:evidence["end"]], evidence["excerpt"])
        self.assertGreater(evidence["start"], len("😀 Prefazione unicode.\n".encode("utf-8")) - 2)
        self.assertEqual(record["requirements"][0]["status"], "extracted")
        self.assertEqual(result["digest"], hashlib.sha256(
            (self.frd / "FRD-0001-task-recovery.json").read_bytes()).hexdigest())
        index = (self.frd / "README.md").read_text(encoding="utf-8")
        self.assertIn("<!-- frd-index:start -->", index)
        self.assertIn("| [FRD-0001](<FRD-0001-task-recovery.json>) | 1 | Task recovery | Proposed | 1 | 0 |", index)
        self.assertTrue(self.tool("validate")["valid"])

    def test_bad_excerpt_offsets_and_stale_document_digest_are_refused(self):
        for change, expected in (
            (lambda e: e.update(excerpt="wrong"), "excerpt does not match"),
            (lambda e: e.update(start=e["start"] + 1), "excerpt does not match"),
            (lambda e: e.update(end=100000), "end exceeds the Unicode length"),
            (lambda e: e.update(document_sha256="0" * 64), "stale document_sha256"),
        ):
            data = self.data()
            change(data["requirements"][0]["evidence"][0])
            before = self.snapshot()
            refusal = self.propose(data, ok=False)
            self.assertIn(expected, refusal)
            self.assertEqual(self.snapshot(), before)
        data = self.data()
        self.propose(data)
        write(self.project / "docs/source.md", self.source_text + "changed\n")
        self.assertIn("stale document_sha256", self.tool("validate", ok=False))

    def test_evidence_paths_cannot_traverse_or_escape_the_project(self):
        for path in ("../outside.md", "/absolute.md", "docs/../source.md", "docs\\source.md"):
            data = self.data()
            evidence = data["requirements"][0]["evidence"][0]
            evidence["path"] = path
            self.assertIn("path", self.propose(data, ok=False))
        self.assertIn("without traversal", self.tool("index", "--dir", "../outside", ok=False))

    def test_resolve_applies_manual_verification_correction_and_rejection(self):
        self.propose()
        verified = self.resolve("REQ-001", "verified")
        self.assertEqual(verified["item_status"], "verified")
        self.assertEqual(self.item("REQ-001")["status"], "verified")
        corrected = copy.deepcopy(self.item("ENT-001"))
        corrected["name"] = "Alice Rossi"
        corrected["evidence"] = [self.evidence("Alice Rossi")]
        corrected.pop("status")
        self.resolve("ENT-001", "corrected", corrected)
        self.assertEqual((self.item("ENT-001")["name"], self.item("ENT-001")["status"]),
                         ("Alice Rossi", "corrected"))
        self.resolve("ENT-003", "rejected")
        self.assertEqual(self.item("ENT-003")["status"], "rejected")
        self.assertTrue(self.tool("validate")["valid"])

    def test_merge_unions_evidence_and_preserves_manual_review_states(self):
        self.propose()
        corrected = copy.deepcopy(self.item("ENT-001"))
        corrected["name"] = "Alice Rossi"
        corrected["evidence"] = [self.evidence("Alice Rossi")]
        self.resolve("ENT-001", "corrected", corrected)
        self.resolve("ENT-003", "rejected")
        self.resolve("REQ-001", "verified")
        incoming = self.data()
        incoming["requirements"][0]["evidence"] = [self.evidence(
            incoming["requirements"][0]["text"], path="docs/alternate.md")]
        incoming["entities"][0]["name"] = "Alice Rossi"
        incoming["entities"][0]["evidence"] = [self.evidence("Alice Rossi", path="docs/alternate.md")]
        incoming["entities"][2]["evidence"] = [self.evidence("Milan", path="docs/alternate.md")]
        result = self.tool("merge", "--frd", "FRD-0001", "--data", self.data_file(incoming),
                           "--expect-digest", self.digest())
        self.assertEqual((result["added"], result["evidence_merged"], result["conflicts_opened"]), (0, 3, 0))
        self.assertEqual(self.item("REQ-001")["status"], "verified")
        self.assertEqual(len(self.item("REQ-001")["evidence"]), 2)
        self.assertEqual((self.item("ENT-001")["name"], self.item("ENT-001")["status"]),
                         ("Alice Rossi", "corrected"))
        self.assertEqual(len(self.item("ENT-001")["evidence"]), 2)
        self.assertEqual(self.item("ENT-003")["status"], "rejected")
        self.assertEqual(len(self.item("ENT-003")["evidence"]), 2)
        repeated = self.tool("merge", "--frd", "FRD-0001", "--data", self.data_file(incoming),
                             "--expect-digest", self.digest())
        self.assertEqual(repeated["evidence_merged"], 0)
        self.assertEqual(len(self.item("REQ-001")["evidence"]), 2)

    def test_merge_preserves_corrected_item_and_records_disagreement(self):
        self.propose()
        corrected = copy.deepcopy(self.item("ENT-001"))
        corrected["name"] = "Alice Rossi"
        corrected["evidence"] = [self.evidence("Alice Rossi")]
        self.resolve("ENT-001", "corrected", corrected)
        result = self.tool("merge", "--frd", "FRD-0001", "--data", self.data_file(self.data()),
                           "--expect-digest", self.digest())
        self.assertEqual(result["conflicts_opened"], 1)
        self.assertEqual((self.item("ENT-001")["name"], self.item("ENT-001")["status"]),
                         ("Alice Rossi", "corrected"))
        conflict = self.record()["conflicts"][0]
        self.assertEqual((conflict["item_id"], conflict["existing"]["name"], conflict["incoming"]["name"],
                          conflict["status"]), ("ENT-001", "Alice Rossi", "Alice", "open"))
        before = self.snapshot()
        self.assertIn("unresolved conflicts block promote", self.promote(ok=False))
        self.assertEqual(self.snapshot(), before)
        resolved = self.resolve("ENT-001", "corrected", conflict=conflict["id"])
        self.assertEqual(resolved["open_conflicts"], 0)
        self.assertEqual(self.item("ENT-001")["name"], "Alice")
        self.assertEqual(self.item("ENT-001")["status"], "corrected")
        self.assertEqual(len(self.item("ENT-001")["evidence"]), 2)
        self.promote()

    def test_merge_adds_new_items_without_deleting_missing_items(self):
        self.propose()
        incoming = self.data()
        extra = "A consultant can reopen an assigned task."
        incoming["requirements"] = [{"id": "REQ-002", "text": extra, "evidence": [self.evidence(extra)]}]
        incoming["entities"] = []
        incoming["relationships"] = []
        result = self.tool("merge", "--frd", "FRD-0001", "--data", self.data_file(incoming),
                           "--expect-digest", self.digest())
        self.assertEqual(result["added"], 1)
        self.assertEqual(len(self.record()["requirements"]), 2)
        self.assertEqual(len(self.record()["entities"]), 3)
        self.assertEqual(self.item("REQ-002")["status"], "extracted")

    def test_versioning_promotion_supersession_and_verification(self):
        self.propose()
        accepted = self.promote("aaaaaaa")
        self.assertEqual(accepted["status"], "Accepted")
        self.assertEqual(self.record()["accepted_at_sha"], "aaaaaaa")
        self.assertIn("FRD-9999 does not exist", self.tool(
            "propose", "--revise", "FRD-9999", "--task", "t", "--sha", "bbbbbbb",
            "--data", self.data_file(self.data()), "--expect-digest", "0" * 64, ok=False))
        revised = self.tool("propose", "--revise", "FRD-0001", "--task", "change-2", "--sha", "bbbbbbb",
                            "--data", self.data_file(self.data()), "--expect-digest", accepted["digest"])
        self.assertEqual((revised["version"], revised["status"]), (2, "Proposed"))
        self.assertIn("already has a Proposed version", self.tool(
            "propose", "--revise", "FRD-0001", "--task", "change-3", "--sha", "bbbbbbb",
            "--data", self.data_file(self.data()), "--expect-digest", accepted["digest"], ok=False))
        promoted = self.promote("ccccccc")
        self.assertEqual((promoted["version"], promoted["superseded"]), (2, ["FRD-0001 v1"]))
        self.assertEqual(self.record(1)["status"], "Superseded")
        self.assertEqual(self.record(1)["superseded_by"], "FRD-0001 v2")
        self.assertEqual(self.record(2)["last_verified_sha"], None)
        verified = self.tool("verify", "--frd", "FRD-0001", "--sha", "ddddddd",
                             "--expect-digest", promoted["digest"])
        self.assertEqual(verified["last_verified_sha"], "ddddddd")
        self.assertEqual(self.record(2)["last_verified_sha"], "ddddddd")
        verified_again = self.tool("verify", "--frd", "FRD-0001", "--sha", "eeeeeee",
                                   "--expect-digest", verified["digest"])
        self.assertEqual(verified_again["last_verified_sha"], "eeeeeee")
        self.assertTrue(self.tool("validate")["valid"])

    def test_stale_accepted_sources_allow_revision_and_preserve_history(self):
        self.propose()
        self.promote("aaaaaaa")
        write(self.project / "docs/source.md", self.source_text + "Source evolved.\n")
        revised = self.tool("propose", "--revise", "FRD-0001", "--task", "change-2", "--sha", "bbbbbbb",
                            "--data", self.data_file(self.data()), "--expect-digest", self.digest("accepted"))
        self.assertEqual((revised["version"], revised["status"]), (2, "Proposed"))
        promoted = self.promote("ccccccc")
        self.assertEqual(promoted["version"], 2)
        self.assertEqual(self.record(1)["status"], "Superseded")
        self.assertTrue(self.tool("validate")["valid"])

    def test_stale_optimistic_digest_and_held_lock_write_nothing(self):
        proposed = self.propose()
        path = self.frd / "FRD-0001-task-recovery.json"
        stale = proposed["digest"]
        data = json.loads(path.read_text(encoding="utf-8"))
        data["title"] = "Changed independently"
        write(path, json.dumps(data, ensure_ascii=False))
        before = self.snapshot()
        refusal = self.tool("merge", "--frd", "FRD-0001", "--data", self.data_file(self.data()),
                            "--expect-digest", stale, ok=False)
        self.assertIn("changed since it was read", refusal)
        self.assertEqual(self.snapshot(), before)
        lock = self.frd / ".frd-lock"
        write(lock, "pid 42 since test\n")
        before = self.snapshot()
        self.assertIn("held by pid 42 since test", self.tool(
            "merge", "--frd", "FRD-0001", "--data", self.data_file(self.data()),
            "--expect-digest", hashlib.sha256(path.read_bytes()).hexdigest(), ok=False))
        self.assertEqual(self.snapshot(), before)

    def test_invalid_relationship_duplicate_identity_and_nonextracted_input_fail(self):
        data = self.data()
        data["relationships"][0]["target"] = "REQ-001"
        self.assertIn("must name an entity", self.propose(data, ok=False))
        data = self.data()
        data["entities"][0]["id"] = "REQ-001"
        self.assertIn("duplicated", self.propose(data, ok=False))
        data = self.data()
        data["requirements"][0]["status"] = "verified"
        self.assertIn("must be extracted", self.propose(data, ok=False))

    def test_stale_index_is_detected_and_regenerated_without_losing_prose(self):
        self.propose()
        path = self.frd / "README.md"
        write(path, "# Custom FRD guide\n\n" + path.read_text(encoding="utf-8") + "\nFooter retained.\n")
        write(path, path.read_text(encoding="utf-8").replace("Task recovery", "Wrong title"))
        self.assertIn("index is stale", self.tool("validate", ok=False))
        self.tool("index")
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Custom FRD guide"))
        self.assertIn("Task recovery", text)
        self.assertTrue(text.rstrip().endswith("Footer retained."))
        self.assertTrue(self.tool("validate")["valid"])


if __name__ == "__main__":
    unittest.main()
