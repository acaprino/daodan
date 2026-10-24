"""A routing proposal becomes a per-request run binding only after confirmation."""

import copy
import contextlib
import hashlib
import io
import json
import unittest
from unittest.mock import patch

from test_task_router import RouterCase, SIGNALS_DEEP, SIGNALS_SIMPLE, tr
import run_state


class TaskBindingTests(RouterCase):
    def proposal(self):
        plan_path, _ = self.plan()
        code, doc = self.assign(SIGNALS_DEEP, plan_path)
        self.assertEqual(code, 0)
        self.assertIn("binding_proposal", doc)
        return doc

    def test_binding_identifies_the_request_and_exact_selection_inputs(self):
        doc = self.proposal()
        binding = doc["binding_proposal"]
        self.assertEqual(binding["request_sha256"], doc["request_sha256"])
        self.assertEqual(binding["models_sha256"], hashlib.sha256(
            (self.tmp / "models.json").read_bytes()).hexdigest())
        self.assertEqual(binding["catalog_sha256"], hashlib.sha256(
            (self.tmp / "catalog.json").read_bytes()).hexdigest())
        self.assertEqual(binding["model_id"], doc["selection"]["chosen"])
        self.assertEqual(binding["model_param"], doc["selection"]["model_param"])
        self.assertEqual(binding["tier"], "tier3")
        self.assertEqual(binding["work_type"], "coding")
        self.assertNotIn("confirmation", binding)

    def test_no_candidate_never_produces_a_binding(self):
        plan_path, _ = self.plan()
        code, doc = self.assign(SIGNALS_SIMPLE, plan_path,
                                extra=("--min-context", "100000000"))
        self.assertEqual(code, 1)
        self.assertIn("binding_proposal", doc)
        self.assertIsNone(doc["binding_proposal"])

    def test_input_digests_describe_consumed_bytes_when_files_change_during_selection(self):
        for filename, hook, field in (("models.json", "normalize_models", "models_sha256"),
                                      ("catalog.json", "catalog_tiers", "catalog_sha256")):
            with self.subTest(input=filename):
                plan_path, _ = self.plan()
                path = self.tmp / filename
                consumed_bytes = path.read_bytes()
                original_hook = getattr(tr, hook)

                def change_after_parsing(data):
                    changed = json.loads(consumed_bytes)
                    if filename == "models.json":
                        changed["provider"]["gw"]["models"]["frontier-dear"]["cost"]["input"] = 100
                    else:
                        changed["models"][-1]["tier_evidence"]["benchmark"]["score"] = 1
                    path.write_text(json.dumps(changed), encoding="utf-8")
                    return original_hook(data)

                reply = self.tmp / "reply.json"
                reply.write_text(json.dumps(SIGNALS_DEEP), encoding="utf-8")
                with patch.object(tr, hook, side_effect=change_after_parsing), \
                        contextlib.redirect_stdout(io.StringIO()):
                    code = tr.main(["assign", "--plan", str(plan_path), "--reply", str(reply),
                                    "--models", str(self.tmp / "models.json"), "--catalog",
                                    str(self.tmp / "catalog.json"), "--out", str(self.tmp / "bound.json")])
                self.assertEqual(code, 0)
                binding = json.loads((self.tmp / "bound.json").read_text(encoding="utf-8"))["binding_proposal"]
                self.assertNotEqual(consumed_bytes, path.read_bytes())
                self.assertEqual(binding[field], hashlib.sha256(consumed_bytes).hexdigest())
                path.write_bytes(consumed_bytes)

    def test_a_confirmed_assignment_survives_the_run_validation_path(self):
        binding = self.proposal()["binding_proposal"]
        binding["confirmation"] = {"confirmed": True, "source": "Use this model for this request",
                                   "host": "opencode", "model_override_supported": True,
                                   "effort_override_supported": True}
        environment = {"interpreter": "python", "models": {
            "host": "opencode", "model_override_supported": True,
            "effort_override_supported": True,
            "assignments": {binding["request_sha256"]: binding}}}
        run_state.validate_loop({"environment": environment})
        self.assertNotIn("tiers", environment["models"])

    def test_assignment_persists_through_revisioned_update_and_resume_on_another_host(self):
        binding = self.proposal()["binding_proposal"]
        binding["confirmation"] = {"confirmed": True, "source": "Use this model for this request",
                                   "host": "opencode", "model_override_supported": True,
                                   "effort_override_supported": True}
        authorizations = {"mode": "read-only"}

        def invoke(command, payload, *extra):
            path = self.tmp / f"{command}-input.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                code = run_state.main([command, "--project", str(self.tmp),
                                       "--run-id", "binding-run", "--payload", str(path), *extra])
            self.assertEqual(code, 0, errors.getvalue())
            return json.loads(output.getvalue())

        invoke("init", {"operation": "assess", "objective": "Route a request",
                        "scope": {"paths": ["request.txt"]}, "authorizations": authorizations,
                        "budget": {"max_workers": 1}})
        invoke("update", {"environment": {"interpreter": "python", "models": {
            "host": "opencode", "model_override_supported": True, "effort_override_supported": True,
            "assignments": {binding["request_sha256"]: binding}}}}, "--expected-revision", "0")
        invoke("update", {"environment": {"models": {"host": "copilot",
            "model_override_supported": False, "effort_override_supported": False}}},
               "--expected-revision", "1")
        resumed = invoke("resume", {"authorizations": authorizations})
        self.assertEqual(resumed["environment"]["models"]["assignments"][binding["request_sha256"]],
                         binding)


class RunBindingValidationTests(unittest.TestCase):
    def setUp(self):
        digest = "a" * 64
        self.binding = {
            "schema": "daodan/task-binding/v1", "request_sha256": digest,
            "models_sha256": "b" * 64, "catalog_sha256": "c" * 64,
            "catalog_revision": 3, "tier": "tier3", "work_type": "coding",
            "governing_board": "code", "model_id": "gw/frontier",
            "model_param": "gw/frontier#high", "effort": "high",
            "confirmation": {"confirmed": True, "source": "I confirm this exact proposal",
                             "host": "codex", "model_override_supported": True,
                             "effort_override_supported": True}}
        self.environment = {"interpreter": "python", "models": {
            "host": "codex", "model_override_supported": True,
            "effort_override_supported": True, "assignments": {digest: self.binding}}}

    def validate(self, environment=None):
        run_state.validate_loop({"environment": environment or self.environment})

    def test_environment_models_must_be_an_object(self):
        with self.assertRaises(run_state.ProtocolError):
            self.validate({"interpreter": "python", "models": "malformed"})

    def test_preflight_inventory_needs_no_confirmed_assignment(self):
        self.validate({"interpreter": "python", "models": {
            "host": "codex", "model_override_supported": False,
            "effort_override_supported": False, "assignments": {}}})

    def test_unconfirmed_proposals_and_empty_confirmation_sources_are_refused(self):
        for confirmation in (None, {}, {"confirmed": False, "source": "yes"},
                             {"confirmed": True, "source": " "}):
            with self.subTest(confirmation=confirmation):
                candidate = copy.deepcopy(self.environment)
                candidate["models"]["assignments"]["a" * 64]["confirmation"] = confirmation
                with self.assertRaises(run_state.ProtocolError):
                    self.validate(candidate)

    def test_assignment_key_and_input_fingerprints_are_checked(self):
        for key, value in (("request_sha256", "d" * 64), ("models_sha256", "bad"),
                           ("catalog_sha256", "bad"), ("schema", "unknown"),
                           ("model_param", "gw/other#high"), ("tier", "tier0")):
            with self.subTest(field=key):
                candidate = copy.deepcopy(self.environment)
                candidate["models"]["assignments"]["a" * 64][key] = value
                with self.assertRaises(run_state.ProtocolError):
                    self.validate(candidate)

    def test_assignments_require_the_host_to_support_the_selected_override(self):
        for field in ("model_override_supported", "effort_override_supported"):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.environment)
                candidate["models"]["assignments"]["a" * 64]["confirmation"][field] = False
                with self.assertRaises(run_state.ProtocolError):
                    self.validate(candidate)

    def test_resume_preserves_assignments_when_current_host_support_changes(self):
        candidate = copy.deepcopy(self.environment)
        candidate["models"].update(host="copilot", model_override_supported=False,
                                   effort_override_supported=False)
        self.validate(candidate)
        self.assertEqual(candidate["models"]["assignments"]["a" * 64]["confirmation"]["host"],
                         "codex")

    def test_confirmation_records_its_original_host(self):
        del self.binding["confirmation"]["host"]
        with self.assertRaises(run_state.ProtocolError):
            self.validate()


if __name__ == "__main__":
    unittest.main()
