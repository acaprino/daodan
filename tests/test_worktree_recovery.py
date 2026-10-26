"""Public record transitions for squash completion and interrupted handoffs."""

from __future__ import annotations

import copy
import shutil
import subprocess
import unittest

import test_work_record as records


@unittest.skipUnless(shutil.which("git"), "Git is required for integration recovery")
class IntegrationRecoveryTests(unittest.TestCase):
    def prepare(self, content=b"reviewed\n", dirty=None, attributes=None, mixed=False):
        # Reuse the real persisted plan/commit/review fixture without inheriting
        # or rerunning its unrelated test methods. Reports are synthetic gates.
        fixture = records.LoopRecordTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        invoke = fixture.invoke
        fixture.invoke = lambda command, payload=None, extra=(), ok=True: invoke(
            command, payload, ["--session", "owner", *extra], ok)
        project = fixture.project
        fixture.git("init", "-b", "main")
        for key, value in (("user.name", "Recovery test"), ("user.email", "recovery@example.invalid"),
                           ("core.autocrlf", "false"), ("commit.gpgsign", "false"),
                           ("core.hooksPath", str(project / ".no-hooks"))):
            fixture.git("config", key, value)
        (project / ".gitignore").write_bytes(b".daodan/\n")
        if mixed:
            (project / "legacy.txt").write_bytes(b"legacy\r\n")
            fixture.payload["scope"] = {"paths": ["."]}
        if attributes:
            (project / ".gitattributes").write_bytes(attributes)
        fixture.git("add", ".")
        fixture.git("commit", "-m", "Target")
        self.target = fixture.git("rev-parse", "HEAD")
        fixture.git("checkout", "-b", "task")
        fixture.git("config", "core.autocrlf", "true")
        fixture.payload["authorizations"] = {"mode": "write", "commit": True}
        fixture.payload["workspace"] = {"mode": "BRANCH", "branch": "task", "base_sha": self.target}
        fixture.payload["required_gates"] = ["final"]
        (project / "app.py").write_bytes(content)
        binding = self.binding()
        candidate = {"digest": binding["snapshot"]["digest"], "head": binding["head"]}
        fixture.use_review(candidate)
        fixture.payload["waves"] = [fixture.wave("w1", fixture.task("a", "app.py"))]
        record = fixture.init()
        fixture.git("add", "app.py")
        fixture.git("commit", "-m", "Reviewed change", "-m", "Daodan-Task: test-run wave 1/1")
        self.reviewed = fixture.git("rev-parse", "HEAD")
        committed = fixture.committed_task(candidate, self.reviewed)
        record = self.update(record, {"waves": [fixture.wave("w1", committed)]})
        wave_candidate = {"head": self.reviewed, "digest": candidate["digest"]}
        wave_review = fixture.review(wave_candidate, "R2", "wave-w1")
        sealed = fixture.wave("w1", committed, status="sealed", candidate=wave_candidate,
                              wave_review={"id": "R2", "verdict": "PASS",
                                           "snapshot": candidate["digest"], "head": self.reviewed})
        record = self.update(record, {"waves": [sealed], "reviews": [*record["reviews"], wave_review],
                                      "deliveries": fixture.review_delivery(wave_review, "test-run")})
        if dirty is not None:
            (project / "app.py").write_bytes(dirty)
        binding = self.binding()
        final_candidate = {"head": self.reviewed, "digest": binding["snapshot"]["digest"]}
        review = fixture.review(final_candidate, "R3", "candidate")
        review["shape"] = "branch"
        self.receipt = {"id": "R3", "verdict": "PASS", "head": self.reviewed,
                        "snapshot": final_candidate["digest"]}
        return self.update(record, {"reviews": [*record["reviews"], review],
                                   "deliveries": fixture.review_delivery(review, "test-run"),
                                   "gates": {"final": self.gate(binding)}})

    def binding(self):
        f = self.fixture
        return f.runtime["project_binding"](f.project, f.payload["scope"], f.project / ".daodan")

    def gate(self, binding):
        return {"status": "passed", "head": binding["head"], "snapshot": binding["snapshot"]["digest"],
                "evidence": {"command": "fixture final verification"}}

    def update(self, record, patch, ok=True):
        return self.fixture.invoke("update", patch, ["--expected-revision", str(record["revision"])], ok=ok)

    def integration(self, remote=False):
        f = self.fixture
        tree = f.git("rev-parse", self.reviewed + "^{tree}")
        location = f.project
        if remote:
            location = f.temp / "remote.git"
            subprocess.run(["git", "init", "--bare", str(location)], check=True, capture_output=True)
            for key, value in (("user.name", "Squash server"), ("user.email", "server@example.invalid")):
                subprocess.run(["git", "-C", str(location), "config", key, value], check=True)
            f.git("remote", "add", "origin", str(location))
            pushed = subprocess.run(["git", "-C", str(f.project), "-c", "protocol.file.allow=always",
                                     "push", "origin", "main", "task"], capture_output=True, text=True)
            self.assertEqual(pushed.returncode, 0, pushed.stderr)
        merged = subprocess.run(["git", "-C", str(location), "commit-tree", tree, "-p", self.target],
                                input="Server squash\n", text=True, capture_output=True, check=True).stdout.strip()
        if remote:
            subprocess.run(["git", "-C", str(location), "update-ref", "refs/heads/main", merged, self.target],
                           check=True)
            missing = subprocess.run(["git", "-C", str(f.project), "cat-file", "-e", merged], capture_output=True)
            self.assertNotEqual(missing.returncode, 0)
            f.git("-c", "protocol.file.allow=always", "fetch", "origin", "main")
            self.assertEqual(f.git("rev-parse", "origin/main"), merged)
        return {"strategy": "squash", "target_sha": self.target, "merged_sha": merged,
                "realigned": False, "candidate_review": copy.deepcopy(self.receipt)}

    def resume(self, ok=True, extra=(), payload=None):
        return self.fixture.invoke("resume", payload or {"authorizations": self.fixture.payload["authorizations"]},
                                   extra=extra, ok=ok)

    def completion(self, integration):
        return {"status": "complete", "integration": {**integration, "realigned": True},
                "interruption": None, "phases": {"audit": {"status": "complete"}},
                "deliveries": {"audit": {"status": "delivered", "output": self.fixture.report()}},
                "gates": {"final": self.gate(self.binding())}}

    def test_git_binary_dirty_inputs_are_rejected_by_actual_completion(self):
        for content in (b"lone\rreturn\n", b"\x01\x02\x03hello\n"):
            with self.subTest(content=content):
                record = self.prepare(content, dirty=content.replace(b"\n", b"\r\n"))
                integration = self.integration()
                self.fixture.git("checkout", "--detach", integration["merged_sha"])
                self.assertIn("M app.py", self.fixture.git("status", "--porcelain"))
                failure = self.update(record, self.completion(integration), ok=False)
                self.assertIn("clean integrated content", failure.stderr)
                self.assertEqual(self.fixture.invoke("show")["status"], "in_progress")
                self.assertEqual(self.fixture.invoke("show")["waves"], record["waves"])

    def test_clean_mixed_and_forced_text_complete_without_rewriting_receipts(self):
        for options in ({"content": b"reviewed\r\n", "mixed": True},
                        {"content": b"forced\0text\r\n", "attributes": b"app.py text\n"}):
            with self.subTest(options=options):
                record = self.prepare(**options)
                integration = self.integration()
                self.fixture.git("checkout", "--detach", integration["merged_sha"])
                self.assertEqual(self.fixture.git("status", "--porcelain"), "")
                complete = self.update(record, self.completion(integration))
                self.assertEqual(complete["status"], "complete")
                self.assertEqual(complete["waves"], record["waves"])
                self.assertEqual(complete["reviews"], record["reviews"])
                self.assertEqual(complete["integration"]["candidate_review"], self.receipt)

    def test_fetched_squash_detach_resume_and_closure_preserve_owned_evidence(self):
        record = self.prepare()
        integration = self.integration(remote=True)
        record = self.update(record, {"integration": integration,
                                      "grants": [{"id": "merge-result", "kind": "merge", "scope": ["app.py"],
                                                  "source": {"kind": "user", "reference": "Integrate this candidate"},
                                                  "granted_at": "2026-10-26T12:00:00Z"}],
                                      "interruption": {"reason": "handoff interrupted"}})
        self.fixture.git("checkout", "--detach", integration["merged_sha"])
        self.assertEqual(self.fixture.git("status", "--porcelain"), "")
        rows = self.fixture.invoke("agenda", extra=["--worktree", str(self.fixture.project)])["tasks"]
        self.assertEqual([row["run_id"] for row in rows], ["test-run"])
        self.assertEqual(rows[0]["branch"], "task")
        self.assertEqual(self.fixture.invoke("agenda", extra=["--run-id", "other"])["tasks"], [])
        resumed = self.resume()
        self.assertEqual(resumed["revision"], record["revision"] + 1)
        self.assertEqual(resumed["candidate"]["head"], integration["merged_sha"])
        for key in ("project", "authorizations", "grants", "scope", "integration", "waves", "reviews", "gates", "interruption"):
            self.assertEqual(resumed[key], record[key])
        self.assertEqual(self.fixture.git("rev-parse", "task"), self.reviewed)
        self.assertEqual(self.resume()["revision"], resumed["revision"])
        stale = self.completion(integration)
        del stale["gates"]
        self.assertIn("Stale candidate gate", self.update(resumed, stale, ok=False).stderr)
        complete = self.update(resumed, self.completion(integration))
        self.assertEqual(complete["status"], "complete")
        self.assertEqual(complete["waves"], record["waves"])
        self.assertEqual(self.fixture.git("rev-parse", "task"), self.reviewed)
        self.assertIsNone(self.fixture.invoke("agenda")["tasks"][0]["holder"])

    def test_recovery_rejects_unrelated_head_content_target_and_unreviewed_record(self):
        record = self.prepare()
        integration = self.integration()
        record = self.update(record, {"integration": integration})
        f = self.fixture
        path = f.project / ".daodan/runs/test-run/work.json"
        original = path.read_bytes()
        for change in ("head", "content", "target", "review", "source-branch"):
            with self.subTest(change=change):
                f.git("checkout", "--detach", integration["merged_sha"])
                (f.project / "app.py").write_bytes(b"reviewed\n")
                if change == "head":
                    f.git("checkout", "--detach", self.target)
                elif change == "content":
                    (f.project / "app.py").write_bytes(b"unreviewed\n")
                elif change in {"target", "review"}:
                    altered = copy.deepcopy(record)
                    if change == "target":
                        altered["integration"]["target_sha"] = self.reviewed
                    else:
                        altered["integration"]["candidate_review"]["id"] = "missing"
                    f.runtime["atomic_write"](path, altered, f.project / ".daodan")
                else:
                    f.git("update-ref", "refs/heads/task", self.target, self.reviewed)
                state_before = path.read_bytes()
                self.assertIn("no matching interrupted", self.resume(ok=False).stderr)
                self.assertEqual(path.read_bytes(), state_before)
                path.write_bytes(original)
                if change == "content":
                    (f.project / "app.py").write_bytes(b"reviewed\n")
                if change == "source-branch":
                    f.git("update-ref", "refs/heads/task", self.reviewed, self.target)

    def test_recovery_preserves_holder_and_identical_authorization_requirements(self):
        record = self.prepare()
        integration = self.integration()
        record = self.update(record, {"integration": integration})
        self.fixture.git("checkout", "--detach", integration["merged_sha"])
        self.assertIn("identical current authorizations", self.resume(ok=False, payload={"authorizations": {}}).stderr)
        self.assertIn("held by session owner", self.resume(ok=False, extra=["--session", "other"]).stderr)
        self.assertEqual(self.fixture.invoke("show")["revision"], record["revision"])
        self.assertEqual(self.resume()["integration"], integration)

    def test_copied_record_in_another_repository_cannot_resume(self):
        record = self.prepare()
        integration = self.integration()
        self.update(record, {"integration": integration})
        f = self.fixture
        other = f.temp / "other"
        cloned = subprocess.run(["git", "-c", "protocol.file.allow=always", "clone", "--no-hardlinks",
                                 str(f.project), str(other)], capture_output=True, text=True)
        self.assertEqual(cloned.returncode, 0, cloned.stderr)
        shutil.copytree(f.project / ".daodan", other / ".daodan")
        self.assertIn("Project identity", self.resume(ok=False, extra=["--project", str(other)]).stderr)


if __name__ == "__main__":
    unittest.main()
