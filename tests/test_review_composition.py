"""Composition preserves obligations, ownership and independent worker modes."""
import tempfile
import hashlib
import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path

from scripts.daodan.load import load_plugin
from scripts.daodan.model import ModelError
from test_work_record import ProtocolCase

ROOT = Path(__file__).resolve().parents[1]


class RoleBodiesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def plugin(self, name, roles, compositions="", dependencies=()):
        root = self.root / name
        (root / "roles").mkdir(parents=True, exist_ok=True)
        names = list(roles)
        for role, body in roles.items():
            if body is not None:
                (root / "roles" / f"{role}.md").write_text(body, encoding="utf-8")
        (root / "plugin.toml").write_text(
            f'schema="daodan/v1"\nname="{name}"\nversion="1.0.0"\n'
            'description="Fixture"\nlicense="MIT"\n[capabilities]\nrequired=[]\n'
            f'[dependencies]\nrequired={list(dependencies)!r}\n[components]\nroles={names!r}\n'
            + compositions, encoding="utf-8")
        return load_plugin(root)

    def test_nested_diamond_deduplicates_same_leaf_preserving_order_and_owner(self):
        from scripts.daodan.role_bodies import resolve_role, role_text
        a = self.plugin("alpha", {"leaf": "# Alpha\nCheck alpha.\n", "wide": None},
                        '[reviewers.compositions.wide]\nmembers=["alpha:leaf","beta:pair"]\n', ("beta",))
        b = self.plugin("beta", {"leaf": "# Beta\nRead `${CLAUDE_PLUGIN_ROOT}/skills/ref.md`.\n", "pair": None},
                        '[reviewers.compositions.pair]\nmembers=["beta:leaf","alpha:leaf"]\n', ("alpha",))
        result = resolve_role({"alpha": a, "beta": b}, "alpha", "wide")
        self.assertEqual(result["members"], ["alpha:leaf", "beta:leaf"])
        self.assertEqual([p["owner"] for p in result["parts"]], ["alpha", "beta"])
        body = role_text(result)
        self.assertEqual(body.count("Check alpha."), 1)
        self.assertIn("<beta-plugin-root>/skills/ref.md", body)
        self.assertEqual(result["metadata"]["model"], "inherit")

    def test_invalid_compositions_fail_before_reading_or_rendering(self):
        from scripts.daodan.role_bodies import resolve_role, RoleBodyError
        for members in (["alpha:leaf", "alpha:leaf"], ["alpha:wide"],
                        ["beta:leaf"], ["alpha:missing"], ["alpha:../secret"]):
            with self.subTest(members=members):
                a = self.plugin("alpha", {"leaf": "# Leaf", "wide": None},
                                f'[reviewers.compositions.wide]\nmembers={members!r}\n')
                with self.assertRaises(RoleBodyError):
                    resolve_role({"alpha": a}, "alpha", "wide")

    def test_prompt_metadata_is_rejected_and_leaf_bytes_unchanged(self):
        with self.assertRaises(ModelError):
            self.plugin("alpha", {"wide": None},
                        '[reviewers.compositions.wide]\nmembers=[]\nprompt="No"\n')
        from scripts.daodan.role_bodies import resolve_role, role_text
        text = "---\nname: leaf\nmodel: inherit\ntools: Read, Write\n---\n\n# Leaf\nBody.\n"
        a = self.plugin("alpha", {"leaf": text})
        self.assertEqual(role_text(resolve_role({"alpha": a}, "alpha", "leaf")), text)

    def test_independent_process_role_cannot_be_folded(self):
        from scripts.daodan.role_bodies import resolve_role, RoleBodyError
        a = self.plugin("senior-review", {"premise-auditor": "# Blind", "wide": None},
                        '[reviewers.compositions.wide]\nmembers=["senior-review:premise-auditor"]\n')
        with self.assertRaisesRegex(RoleBodyError, "independent"):
            resolve_role({"senior-review": a}, "senior-review", "wide")

    def test_composed_roles_render_with_same_members_on_every_host(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.render import render_plugin
        a = self.plugin("alpha", {"leaf": "---\nname: leaf\nmodel: inherit\ntools: Read, Write, Bash\n---\n# Check\nCheck sentinel.\n", "wide": None},
                        '[reviewers.compositions.wide]\nmembers=["alpha:leaf"]\n')
        from scripts.daodan.templates import render_path
        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ROOT / "adapters", host)
                destination = self.root / f"out-{host}"
                render_plugin(a, adapter, destination, adapters_root=ROOT / "adapters", plugin_registry={"alpha": a})
                rendered = destination / render_path(adapter.layout["roles"], {"role": "wide", "plugin": "alpha"})
                text = rendered.read_text(encoding="utf-8")
                self.assertEqual(text.count("Check sentinel."), 1)
                self.assertIn("alpha:leaf", text)
                self.assertIn("common review conventions", text)

    def test_cross_provider_roots_and_permissions_survive_all_hosts(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.render import publish_plugin
        from scripts.daodan.templates import render_path
        b = self.plugin("beta", {"leaf": "---\nname: leaf\nmodel: inherit\ntools: Read, Write, Bash\n---\n# Beta\nRead `${CLAUDE_PLUGIN_ROOT}/skills/beta.md`.\n"})
        a = self.plugin("alpha", {"leaf": "---\nname: leaf\nmodel: inherit\n---\n# Alpha\nUnrestricted leaf.\n", "wide": None},
            '[reviewers.compositions.wide]\nmembers=["alpha:leaf","beta:leaf"]\n', ("beta",))
        for host in HOSTS:
            with self.subTest(host=host):
                adapter = load_adapter(ROOT / "adapters", host)
                live = self.root / f"foreign-{host}"
                publish_plugin(a, adapter, live, adapters_root=ROOT / "adapters", plugin_registry={"alpha": a, "beta": b})
                path = live / render_path(adapter.layout["roles"], {"plugin": "alpha", "role": "wide"})
                text = path.read_text(encoding="utf-8")
                self.assertIn("<beta-plugin-root>/skills/beta.md", text)
                self.assertIn("Unrestricted leaf.", text)
                self.assertIn("create or overwrite files", text)
                self.assertIn("Do not use operations omitted from this list.", text)
                if host in {"codex", "pi"}:
                    self.assertIn("no additional tool restriction", text)
                if host == "opencode":
                    self.assertNotIn('action: "*"', text)

    def test_invalid_composition_preserves_published_output(self):
        from scripts.daodan.adapter import load_adapter
        from scripts.daodan.render import publish_plugin
        a = self.plugin("alpha", {"wide": None},
                        '[reviewers.compositions.wide]\nmembers=["alpha:missing"]\n')
        live = self.root / "live"
        live.mkdir()
        (live / "sentinel").write_text("published", encoding="utf-8")
        with self.assertRaises(ValueError):
            publish_plugin(a, load_adapter(ROOT / "adapters", "claude"), live, plugin_registry={"alpha": a})
        self.assertEqual(list(p.name for p in live.iterdir()), ["sentinel"])
        self.assertEqual((live / "sentinel").read_text(), "published")


class RuntimeCompositionTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {"host": "codex", "entries": []}
        self.bindings = {"host": "codex", "candidate": {"digest": "current"},
                         "common": [{"body": "Shared review conventions."}],
                         "knowledge_selection": "sha256:knowledge", "roles": {},
                         "scopes": {name: {"input_mode": "discovery", "permissions": "read-only",
                                           "output_dir": f"reports/{name}"} for name in ("one", "two")}}
        self.roster = {"shape": "branch", "grounding": {"candidate": {"digest": "current"}},
                       "required_specialists": [self.obligation("alpha:a", "one"),
                                                self.obligation("alpha:b", "one")]}
        for role in ("a", "b"):
            identity = f"alpha:{role}"
            body = f"# {role}\nCheck {role} with evidence.\n"
            digest = "sha256:" + hashlib.sha256(body.encode()).hexdigest()
            self.catalog["entries"].append({"id": identity, "kind": "role", "provider": "alpha",
                "provider_version": "1", "host_binding": {"host": "codex", "file": f"agents/{role}.md", "sha256": digest},
                "source_hashes": {identity: digest}})
            self.bindings["roles"][identity] = {"text": body, "provider": "alpha", "provider_version": "1",
                "file": f"agents/{role}.md", "root": "installed/alpha", "source_hashes": {identity: digest}}
        self.catalog["entries"].append({"id": "alpha:wide", "kind": "role", "members": ["alpha:a", "alpha:b"]})

    @staticmethod
    def obligation(identity, scope):
        return {"specialist_id": identity, "scope_id": scope, "evidence": ["required contract"]}

    def test_preset_and_adhoc_share_canonical_members(self):
        from scripts.daodan.composition import compose_jobs, validate_composition
        jobs = compose_jobs(self.roster, self.catalog, self.bindings)
        self.roster["required_specialists"] = [self.obligation("alpha:wide", "one")]
        self.assertEqual(jobs, compose_jobs(self.roster, self.catalog, self.bindings))
        self.assertEqual(validate_composition(self.roster, jobs, self.catalog), [])
        self.assertTrue(validate_composition(self.roster, [], self.catalog))

    def test_incomplete_catalog_projection_cannot_hide_roster_obligations(self):
        import runpy
        from scripts.daodan.composition import compose_jobs
        compute = runpy.run_path(str(ROOT / "plugins/senior-review/skills/review-preparation/scripts/review_roster.py"))["compute"]
        for entries in ([], self.catalog["entries"]):
            for kind, path in (("changeset", "src/leaf.c"), ("changeset", "src/leaf.py"),
                               ("changeset", "src/leaf.ts"), ("doc", "docs/claim.md")):
                with self.subTest(catalog_empty=not entries, kind=kind, path=path):
                    diff = f"--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n-old\n+new\n"
                    roster = compute("branch", diff, None, None, False, kind, context={
                        "catalog": {"entries": entries}, "scope_id": "one",
                        "candidate": self.bindings["candidate"],
                        "applicability": [{"specialist_id": "testing:test-suite-auditor",
                            "scope_id": "one", "candidate": self.bindings["candidate"],
                            "status": "not-applicable", "evidence": [{
                                "path": path, "reason": "No test change in this file."}]}],
                        "required_specialists": [self.obligation("alpha:a", "one")]})
                    with self.assertRaisesRegex(ValueError, "unknown"):
                        compose_jobs(roster, self.catalog, self.bindings)

    def test_duplicate_is_scoped(self):
        from scripts.daodan.composition import compose_jobs
        self.roster["required_specialists"] += [self.obligation("alpha:a", "one"), self.obligation("alpha:a", "two")]
        jobs = compose_jobs(self.roster, self.catalog, self.bindings)
        pairs = [(m, j["scope_id"]) for j in jobs for m in j["specialist_ids"]]
        self.assertCountEqual(pairs, [("alpha:a", "one"), ("alpha:b", "one"), ("alpha:a", "two")])

    def test_method_binding_retains_its_method_and_specialist_obligations(self):
        from scripts.daodan.composition import compose_jobs
        method = copy.deepcopy(self.catalog["entries"][0])
        method.update(id="alpha:method", kind="method-binding", skills=["alpha:audit-method"],
                      members=["alpha:a", "alpha:b"])
        self.catalog["entries"].append(method)
        self.bindings["roles"]["alpha:method"] = {**self.bindings["roles"]["alpha:a"],
                                                "skills": method["skills"]}
        self.roster["required_specialists"] = [self.obligation("alpha:method", "one")]
        jobs = compose_jobs(self.roster, self.catalog, self.bindings)
        self.assertEqual(jobs[0]["specialist_ids"], ["alpha:a", "alpha:b", "alpha:method"])

    def test_assembly_preserves_each_member_operation_scope(self):
        from scripts.daodan.composition import compose_jobs
        for entry in self.catalog["entries"][:2]:
            entry["operation_scope"] = f"Only operations permitted for {entry['id']}."
        body = compose_jobs(self.roster, self.catalog, self.bindings)[0]["body"]
        for identity in ("alpha:a", "alpha:b"):
            self.assertIn(f"Only operations permitted for {identity}.", body)

    def test_prepared_cli_reads_installed_bodies_and_preserves_output_on_mismatch(self):
        from scripts.daodan.composition import main
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bindings = copy.deepcopy(self.bindings)
            for bound in bindings["roles"].values():
                path = root / bound["file"]
                path.parent.mkdir(exist_ok=True)
                path.write_text(bound.pop("text"), encoding="utf-8", newline="\n")
                bound["root"] = str(root)
            for name, value in (("roster", self.roster), ("catalog", self.catalog), ("bindings", bindings)):
                (root / (name + ".json")).write_text(json.dumps(value), encoding="utf-8")
            output = root / "prepared.json"
            args = [value for name in ("roster", "catalog", "bindings")
                    for value in ("--" + name, str(root / (name + ".json")))] + ["--out", str(output)]
            self.assertEqual(main(args), 0)
            prepared = output.read_bytes()
            self.assertEqual(json.loads(prepared)["jobs"][0]["specialist_ids"], ["alpha:a", "alpha:b"])
            (root / "agents/a.md").write_text("Changed after preparation", encoding="utf-8")
            with self.assertRaises(SystemExit) as failure:
                main(args)
            self.assertEqual(failure.exception.code, 1)
            self.assertEqual(output.read_bytes(), prepared)

    def test_changed_member_invalidates_body_digest(self):
        from scripts.daodan.composition import compose_jobs
        for field, value in (("text", "altered"), ("provider_version", "2"), ("source_hashes", {})):
            with self.subTest(field=field):
                bindings = copy.deepcopy(self.bindings)
                bindings["roles"]["alpha:a"][field] = value
                with self.assertRaises(ValueError):
                    compose_jobs(self.roster, self.catalog, bindings)
        self.bindings["candidate"] = {"digest": "old"}
        with self.assertRaises(ValueError):
            compose_jobs(self.roster, self.catalog, self.bindings)

    def test_host_specific_override_requires_a_reviewed_composition_binding(self):
        from scripts.daodan.composition import compose_jobs
        self.catalog["entries"][0]["source_hashes"]["alpha/override:a"] = "sha256:override"
        self.bindings["roles"]["alpha:a"]["source_hashes"] = self.catalog["entries"][0]["source_hashes"]
        with self.assertRaisesRegex(ValueError, "override.*composition binding"):
            compose_jobs(self.roster, self.catalog, self.bindings)

    def test_output_and_permission_bindings_cannot_escape_the_assignment(self):
        from scripts.daodan.composition import compose_jobs
        for output in ("../escape", "C:/outside", "/outside"):
            with self.subTest(output=output):
                binding = copy.deepcopy(self.bindings)
                binding["scopes"]["one"]["output_dir"] = output
                with self.assertRaises(ValueError):
                    compose_jobs(self.roster, self.catalog, binding)
        self.bindings["roles"]["alpha:a"]["permissions"] = "write product"
        with self.assertRaises(ValueError):
            compose_jobs(self.roster, self.catalog, self.bindings)

    def test_blind_or_verifier_input_cannot_merge(self):
        from scripts.daodan.composition import compose_jobs
        self.bindings["roles"]["alpha:b"]["input_mode"] = "blind"
        jobs = compose_jobs(self.roster, self.catalog, self.bindings)
        self.assertEqual(len(jobs), 2)
        self.assertEqual({j["input_mode"] for j in jobs}, {"blind", "discovery"})

    def test_budget_omits_no_required_member(self):
        from scripts.daodan.composition import compose_jobs, validate_composition
        self.roster["required_specialists"].append(self.obligation("alpha:a", "two"))
        self.bindings["max_body_chars"] = 1
        with self.assertRaises(ValueError):
            compose_jobs(self.roster, self.catalog, self.bindings)
        del self.bindings["max_body_chars"]
        jobs = compose_jobs(self.roster, self.catalog, self.bindings)
        self.assertEqual(validate_composition(self.roster, jobs, self.catalog), [])
        self.roster["shape"] = "light"
        with self.assertRaises(ValueError):
            compose_jobs(self.roster, self.catalog, self.bindings)

    def test_light_floor_keeps_a_signalled_resource_obligation_in_one_discovery(self):
        import runpy
        roster_module = runpy.run_path(str(ROOT / "plugins/senior-review/skills/review-preparation/scripts/review_roster.py"))
        catalog = {"entries": [
            {"id": "senior-review:code-auditor", "members": ["senior-review:local-correctness-auditor", "senior-review:local-concurrency-auditor"]},
            *({"id": f"senior-review:{role}"} for role in ("local-correctness-auditor", "local-concurrency-auditor", "resource-lifecycle-auditor"))]}
        diff = "diff --git a/handler.py b/handler.py\n--- a/handler.py\n+++ b/handler.py\n@@ -1 +1,2 @@\n+conn = pool.acquire()\n+raise ValueError()\n"
        roster = roster_module["compute"]("light", diff, None, None, False,
                                         context={"catalog": catalog, "candidate": {"digest": "current"}})
        self.assertEqual(roster["roster"], ["senior-review:code-auditor"])
        self.assertIn("senior-review:resource-lifecycle-auditor",
                      [row["specialist_id"] for row in roster["required_specialists"]])


class MemberDeliveryTests(ProtocolCase):
    def setUp(self):
        super().setUp()
        self.review = {"id": "R1", "stage": "branch", "schema": "daodan/review-roster/v1",
            "shape": "branch", "kind": "changeset", "tier": "small",
            "roster": ["alpha:wide"], "support": ["work-controller:isolated-worker"],
            "reasons": ["required"], "verification": "high-and-above",
            "required_specialists": [{"specialist_id": "alpha:a", "scope_id": "one", "evidence": ["contract"]},
                                     {"specialist_id": "alpha:b", "scope_id": "one", "evidence": ["contract"]}],
            "grounding": {"candidate": {"digest": "current"}},
            "jobs": [{"id": "J1", "role": "work-controller:isolated-worker", "specialist_ids": ["alpha:a", "alpha:b"],
                      "scope_id": "one", "input_mode": "discovery", "body_sha256": "sha256:body",
                      "candidate": {"digest": "current"}, "output_path": "audit.md"}]}
        self.payload["reviews"] = [self.review]
        self.payload["deliveries"] = {"J1": {"status": "pending", "review": "R1", "role": "work-controller:isolated-worker", "job_id": "J1"}}

    def completion(self):
        return {"status": "complete", "phases": {"audit": {"status": "complete"}},
            "deliveries": {"J1": {"status": "delivered", "review": "R1", "role": "work-controller:isolated-worker",
            "job_id": "J1", "output": self.report(), "scope_id": "one", "body_sha256": "sha256:body",
            "candidate": {"digest": "current"}, "specialist_ids": ["alpha:a", "alpha:b"],
            "findings": [],
            "member_results": [{"specialist_id": member, "status": "delivered", "coverage": "complete",
                                "findings": [], "gaps": []} for member in ("alpha:a", "alpha:b")]}}}

    def update(self, payload, ok=True):
        revision = json.loads((self.project / ".daodan/runs/test-run/work.json").read_text())["revision"]
        return self.invoke("update", payload, extra=("--expected-revision", str(revision)), ok=ok)

    def check_delivery(self, kind, *, lens=None, output=None):
        mode = "blind" if kind == "blind-derivation" else "critic" if kind == "critic" else "full-context" if lens == 0 else "verification"
        role = "senior-review:premise-auditor" if kind == "blind-derivation" or lens == 0 else "work-controller:isolated-worker"
        check = {"kind": kind, "input_mode": mode, "independent": True,
                 "evidence": ["assigned source checked"]}
        if lens is not None:
            check.update(lens=lens, verdict="HOLDS" if lens == 0 else "REAL",
                         targets=[{"job_id": "J1", "finding_id": "F1"}])
        return {"review": "R1", "role": role, "status": "delivered",
                "output": self.report(output or f"{kind}-{lens}.md"),
                "candidate": {"digest": "current"}, "coverage": "complete", "gaps": [], "check": check}

    def finding_completion(self):
        payload = self.completion()
        payload["deliveries"]["J1"]["findings"] = [{"id": "F1", "severity": "High", "confidence": 90,
            "premise": "the direct caller reaches the wrong object", "premise_provenance": "independent",
            "introduced_by_candidate": True}]
        payload["deliveries"]["J1"]["member_results"][0]["findings"] = ["F1"]
        for lens in (1, 2, 3):
            payload["deliveries"][f"lens-{lens}"] = self.check_delivery("verification", lens=lens)
        return payload

    def legacy_completion(self):
        legacy_role = "project-protocol:isolated-worker"
        self.review.update(critic=True, support=[legacy_role])
        self.review["jobs"][0]["role"] = legacy_role
        self.payload["deliveries"]["J1"]["role"] = legacy_role
        self.init()
        payload = self.finding_completion()
        payload["deliveries"]["critic"] = self.check_delivery("critic")
        for delivery in payload["deliveries"].values():
            delivery["role"] = legacy_role
        return payload

    def test_legacy_completed_checks_preserve_recorded_roles_and_hashes(self):
        payload = self.legacy_completion()
        original_review, original_deliveries = copy.deepcopy((self.review, payload["deliveries"]))
        rules = self.runtime["contract"]()["loop"]["reviews"]
        self.runtime["validate_reviews"]([self.review], rules, payload["deliveries"], complete=True)
        self.assertEqual(self.review, original_review)
        self.assertEqual(payload["deliveries"], original_deliveries)

    def test_legacy_in_progress_review_completes_without_rebinding_evidence(self):
        payload = self.legacy_completion()
        historical = self.update({**payload, "status": "in_progress"})
        completed = self.update({"status": "complete"})
        self.assertEqual(completed["status"], "complete")
        for field in ("reviews", "deliveries"):
            self.assertEqual(completed[field], historical[field])

    def test_legacy_completed_record_can_show_resume_and_validate_without_writes(self):
        payload = self.legacy_completion()
        historical = self.update({**payload, "status": "in_progress"})
        historical["status"] = "complete"
        path = self.project / ".daodan/runs/test-run/work.json"
        path.write_text(json.dumps(historical), encoding="utf-8")
        original = path.read_bytes()
        for command in ("show", "resume", "validate"):
            with self.subTest(command=command):
                resume = {"authorizations": self.payload["authorizations"]} if command == "resume" else None
                self.invoke(command, resume, extra=("--current",) if command == "validate" else ())
                self.assertEqual(path.read_bytes(), original)

    def test_historical_alias_does_not_accept_wrong_or_unbound_check_roles(self):
        self.init()
        rules = self.runtime["contract"]()["loop"]["reviews"]
        for role, bound in (("project-protocol:isolated-worker", False), ("alpha:other-worker", True)):
            with self.subTest(role=role, bound=bound):
                review = copy.deepcopy(self.review)
                review["critic"] = True
                if bound:
                    review["support"].append(role)
                deliveries = self.completion()["deliveries"]
                deliveries["critic"] = self.check_delivery("critic")
                deliveries["critic"]["role"] = role
                with self.assertRaises(self.runtime["ProtocolError"]):
                    self.runtime["validate_reviews"]([review], rules, deliveries, complete=True)

    def test_historical_alias_cannot_replace_the_premise_auditor(self):
        payload = self.legacy_completion()
        rules = self.runtime["contract"]()["loop"]["reviews"]
        for kind, lens in (("blind-derivation", None), ("verification", 0)):
            with self.subTest(kind=kind, lens=lens):
                review = copy.deepcopy(self.review)
                review["blind_derivation"] = kind == "blind-derivation"
                deliveries = copy.deepcopy(payload["deliveries"])
                deliveries["premise"] = self.check_delivery(kind, lens=lens)
                deliveries["premise"]["role"] = "project-protocol:isolated-worker"
                if lens == 0:
                    deliveries["J1"]["findings"][0]["premise_provenance"] = "shared-context"
                with self.assertRaisesRegex(self.runtime["ProtocolError"], "incomplete"):
                    self.runtime["validate_reviews"]([review], rules, deliveries, complete=True)

    def test_explicit_empty_plan_is_preparation_not_completed_coverage(self):
        review = copy.deepcopy(self.review)
        review.update(required_specialists=[], jobs=[], blind_derivation=True, critic=True)
        rules = self.runtime["contract"]()["loop"]["reviews"]
        self.runtime["validate_reviews"]([review], rules, {}, complete=False)
        with self.assertRaisesRegex(self.runtime["ProtocolError"], "plan"):
            self.runtime["validate_reviews"]([review], rules, {}, complete=True)

    def test_legacy_review_without_composition_fields_remains_readable(self):
        review = {key: value for key, value in self.review.items() if key not in {"required_specialists", "jobs"}}
        review.update(blind_derivation=True, critic=True)
        rules = self.runtime["contract"]()["loop"]["reviews"]
        self.runtime["validate_reviews"]([review], rules, {}, complete=True)

    def test_active_pass_rejects_legacy_review_without_composition(self):
        candidate = {"digest": "a" * 64, "head": "base"}
        review = {key: value for key, value in self.review.items() if key not in {"required_specialists", "jobs"}}
        review.update(shape="light", tier="light", stage="pre-commit-a",
                      grounding={"candidate": candidate}, blind_derivation=True, critic=True)
        receipt = {"id": review["id"], "verdict": "PASS",
                   "snapshot": candidate["digest"], "head": candidate["head"]}
        rules = self.runtime["contract"]()["loop"]["reviews"]
        with self.assertRaisesRegex(self.runtime["ProtocolError"], "composition"):
            self.runtime["validate_pass_review"](review, candidate, receipt, rules, {})

    def test_composition_fields_must_be_present_together(self):
        rules = self.runtime["contract"]()["loop"]["reviews"]
        for missing in ("required_specialists", "jobs"):
            with self.subTest(missing=missing):
                review = copy.deepcopy(self.review)
                review.update(required_specialists=[], jobs=[])
                del review[missing]
                with self.assertRaisesRegex(self.runtime["ProtocolError"], "both"):
                    self.runtime["validate_reviews"]([review], rules, {}, complete=False)

    def test_discovery_delivery_cannot_satisfy_its_own_critic(self):
        self.review["critic"] = True
        self.init()
        payload = self.completion()
        payload["deliveries"]["J1"].update(self.check_delivery("critic", output="audit.md"))
        self.assertIn("independent", self.update(payload, ok=False).stderr.lower())

    def test_discovery_delivery_cannot_satisfy_its_own_verification_lens(self):
        self.init()
        payload = self.finding_completion()
        payload["deliveries"]["J1"].update(payload["deliveries"].pop("lens-1"))
        payload["deliveries"]["J1"]["output"] = "audit.md"
        self.assertIn("independent", self.update(payload, ok=False).stderr.lower())

    def test_independent_check_cannot_reuse_discovery_output(self):
        self.review["critic"] = True
        self.init()
        for output in ("audit.md", "./audit.md"):
            with self.subTest(output=output):
                payload = self.completion()
                payload["deliveries"]["critic"] = self.check_delivery("critic", output=output)
                self.assertIn("output", self.update(payload, ok=False).stderr.lower())

    def test_independent_checks_cannot_share_one_report(self):
        self.review.update(blind_derivation=True, critic=True)
        self.review["support"].append("senior-review:premise-auditor")
        self.init()
        payload = self.completion()
        for kind in ("blind-derivation", "critic"):
            payload["deliveries"][kind] = self.check_delivery(kind, output="checks.md")
        self.assertIn("output", self.update(payload, ok=False).stderr.lower())

    def test_independent_check_fields_reject_malformed_present_values(self):
        self.init()
        rules = self.runtime["contract"]()["loop"]["reviews"]
        valid = self.check_delivery("verification", lens=1)
        for field, value in (("kind", []), ("input_mode", []), ("independent", "true"),
                             ("evidence", "checked"), ("lens", True), ("targets", "F1"),
                             ("targets", [{"job_id": [], "finding_id": "F1"}]),
                             ("counterexample", ["caller.py:1"]), ("target", []), ("severity_vote", [])):
            with self.subTest(field=field, value=value):
                delivery = copy.deepcopy(valid)
                delivery["check"][field] = value
                with self.assertRaises(self.runtime["ProtocolError"]):
                    self.runtime["validate_reviews"]([self.review], rules, {"lens-1": delivery}, complete=False)

    def test_composition_plan_rejects_malformed_present_bindings(self):
        rules = self.runtime["contract"]()["loop"]["reviews"]
        for target, field, value in (("review", "grounding", []), ("job", "candidate", ["current"]),
                                     ("job", "knowledge_selection", []), ("job", "source_bindings", []),
                                     ("member", "evidence", [False])):
            with self.subTest(target=target, field=field):
                review = copy.deepcopy(self.review)
                row = review if target == "review" else review["jobs"][0] if target == "job" else review["required_specialists"][0]
                row[field] = value
                with self.assertRaises(self.runtime["ProtocolError"]):
                    self.runtime["validate_reviews"]([review], rules, {}, complete=False)

    def test_independent_check_cannot_hardlink_its_discovery_report(self):
        self.review["critic"] = True
        self.init()
        payload = self.completion()
        payload["deliveries"]["critic"] = self.check_delivery("critic", output="critic.md")
        directory = self.project / ".daodan/runs/test-run"
        report = directory / "critic.md"
        report.unlink()
        try:
            report.hardlink_to(directory / "audit.md")
        except OSError as error:
            self.skipTest(f"hardlink unavailable: {error}")
        self.assertIn("output", self.update(payload, ok=False).stderr.lower())

    def test_distinct_independent_lenses_allow_completed_finding(self):
        self.init()
        self.update(self.finding_completion())

    def test_missing_member_blocks_completion(self):
        self.init()
        payload = self.completion()
        payload["deliveries"]["J1"]["member_results"].pop()
        self.assertIn("member", self.update(payload, ok=False).stderr)

    def test_failed_member_is_accounted_not_passed(self):
        self.init()
        payload = self.completion()
        payload["status"] = "in_progress"
        payload["deliveries"]["J1"]["member_results"][1].update(status="failed", coverage="incomplete", gaps=["missing required input"])
        self.update(payload)
        self.assertIn("member", self.update({"status": "complete"}, ok=False).stderr)

    def test_duplicate_job_cannot_hide_missing_scope(self):
        self.review["required_specialists"][1]["scope_id"] = "two"
        self.assertIn("obligation", self.invoke("init", self.payload, ok=False).stderr)

    def test_auxiliary_worker_cannot_satisfy_discovery(self):
        self.init()
        payload = self.completion()
        payload["deliveries"]["J1"]["job_id"] = "AUX"
        self.assertIn("job", self.update(payload, ok=False).stderr)

    def test_complete_members_allow_clean_result(self):
        self.init()
        self.update(self.completion())

    def test_unassigned_runtime_limitation_does_not_claim_or_block_static_checks(self):
        self.init()
        payload = self.completion()
        payload["deliveries"]["J1"]["member_results"][0]["gaps"] = [
            {"required": False, "reason": "runtime exercise is outside the assigned static audit"}]
        self.update(payload)

    def test_member_cannot_reference_a_missing_canonical_finding(self):
        self.init()
        payload = self.completion()
        payload["deliveries"]["J1"]["member_results"][0]["findings"] = ["missing"]
        self.assertIn("finding", self.update(payload, ok=False).stderr)

    def test_required_blind_and_critic_checks_cannot_be_waived(self):
        self.init()
        for check in ("blind_derivation", "critic"):
            with self.subTest(check=check):
                review = copy.deepcopy(self.review)
                review[check] = True
                rules = self.runtime["contract"]()["loop"]["reviews"]
                delivered = self.completion()["deliveries"]
                with self.assertRaisesRegex(self.runtime["ProtocolError"], "check"):
                    self.runtime["validate_reviews"]([review], rules, delivered, complete=True)

    def test_required_finding_lenses_cannot_be_satisfied_by_an_auxiliary_worker(self):
        self.review["verification"] = "high-and-above"
        self.init()
        payload = self.completion()
        delivery = payload["deliveries"]["J1"]
        delivery["findings"] = [{"id": "F1", "severity": "High", "confidence": 90,
            "premise": "the direct caller reaches the wrong object", "premise_provenance": "independent",
            "introduced_by_candidate": True}]
        delivery["member_results"][0]["findings"] = ["F1"]
        payload["deliveries"]["aux"] = {"review": "R1", "role": "work-controller:isolated-worker",
            "status": "delivered", "output": self.report("aux.md")}
        self.assertIn("lens", self.update(payload, ok=False).stderr)

    def test_independent_clean_checks_can_close_a_complete_review(self):
        self.review.update(blind_derivation=True, critic=True)
        self.review["support"].append("senior-review:premise-auditor")
        self.init()
        payload = self.completion()
        for kind, role in (("blind-derivation", "senior-review:premise-auditor"),
                           ("critic", "work-controller:isolated-worker")):
            payload["deliveries"][kind] = {"review": "R1", "role": role, "status": "delivered",
                "output": self.report(kind + ".md"), "candidate": {"digest": "current"},
                "coverage": "complete", "gaps": [],
                "check": {"kind": kind, "input_mode": "blind" if kind == "blind-derivation" else "critic",
                          "independent": True, "evidence": ["assigned source checked"]}}
        self.update(payload)


if __name__ == "__main__":
    unittest.main()
