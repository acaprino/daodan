"""Ownership contracts for the harness and its unified correctness review."""
import json
from pathlib import Path
import re
import tempfile
import tomllib
import unittest

from host_binding_assertions import without_host_binding


ROOT = Path(__file__).resolve().parents[1]
STACK_ROLES = {"react-development/react-performance-optimizer", "typescript-development/type-safety-auditor", "platform-engineering/platform-reviewer"}
CORE_ROLES = {
    "code-review": {f"senior-review/{name}" for name in ("code-auditor", "security-auditor", "ui-race-auditor", "temporal-resilience-auditor", "data-integrity-auditor", "resource-lifecycle-auditor", "premise-auditor")} | {"testing/test-suite-auditor", "abstraction-architect/abstraction-architect-agent"},
    "team-review": {f"senior-review/{name}" for name in ("accessibility-auditor", "api-contract-auditor", "chicken-egg-detector", "cleanup-auditor", "code-auditor", "data-integrity-auditor", "distributed-flow-auditor", "logic-integrity-auditor", "operability-auditor", "performance-auditor", "premise-auditor", "resource-lifecycle-auditor", "security-auditor", "temporal-resilience-auditor", "ui-race-auditor")} | {"repo-hygiene/workspace-auditor", "testing/test-suite-auditor", "abstraction-architect/abstraction-architect-agent", "codebase-map/map-analyst", "codebase-map/semantic-interconnect-mapper"},
    "pr-review": {f"senior-review/{name}" for name in ("code-auditor", "security-auditor", "premise-auditor")},
}
# Since 38.0.0 every command is a workflow of the `daodan` entry plugin. The light
# review of review-changes binds one reviewer chosen by the roster helper and runs
# Lens 1 through the inline isolated worker. review-branch runs the team-review and
# pr-review variants; its roster covers every dimension the retired code-review
# entry bound, and the lifecycle's stage D runs the same branch shape.
ENTRY = "daodan"
LIGHT_ROLES = {"senior-review/code-auditor", "senior-review/premise-auditor"}
BRANCH_ROLES = CORE_ROLES["code-review"] | CORE_ROLES["team-review"] | CORE_ROLES["pr-review"] | STACK_ROLES
REVIEW_ENTRIES = {"review-changes": LIGHT_ROLES, "review-branch": BRANCH_ROLES}


def manifest(name):
    return tomllib.loads((ROOT / "plugins" / name / "plugin.toml").read_text(encoding="utf-8"))


def wrapper_path(host, plugin, entry):
    return {
        "claude": f"commands/{entry}.md",
        "copilot": f"agents/{entry}-coordinator.agent.md",
        "codex": f"skills/{entry}-workflow/SKILL.md",
        "pi": f"prompts/{plugin}-{entry}.md",
        "opencode": f"commands/{entry}.md",
    }[host]


def role_path(host, plugin, role):
    return {
        "claude": f"agents/{role}.md",
        "copilot": f"agents/{role}.agent.md",
        "codex": f"roles/{role}.md",
        "pi": f"skills/{plugin}-{role}/SKILL.md",
        "opencode": f"agents/{role}.md",
    }[host]


def working_paragraphs(case, text):
    """Select each operative paragraph, so unrelated mentions cannot satisfy it."""
    found = {}
    for label in ("assumptions", "simplicity", "scope", "verification", "redesign"):
        paragraphs = re.findall(rf"(?m)^Working {label}: ([^\n]+)$", text)
        case.assertEqual(len(paragraphs), 1, f"One working {label} rule is required")
        found[label] = paragraphs[0]
    return found


def assert_working_discipline(case, text):
    """Independent approved requirements, applied to the rule owning each action."""
    paragraphs = working_paragraphs(case, text)
    requirements = {
        "assumptions": (
            r"(?i)state\b[^.]*material assumptions",
            r"(?i)unresolved alternatives|unresolved choices",
            r"(?i)essential decision",
            r"(?i)instructions or authorization cannot resolve",
            r"(?i)ask|clarif",
        ),
        "simplicity": (
            r"^Choose the simplest design that satisfies approved requirements and existing contracts\.",
            r"(?:^|(?<=\. ))Prefer, in order, suitable project code and conventions, platform or standard-library facilities, dependencies already available, then the least new code\.",
            r"(?:^|(?<=\. ))Explain an exception when an earlier option cannot meet the requirement or is more complex overall\.",
            r"(?:^|(?<=\. ))Reuse existing owners; add no speculative features, abstractions or configuration\.",
            r"(?:^|(?<=\. ))Preserve boundary validation, data-loss prevention, security and accessibility\.",
            r"(?:^|(?<=\. ))Before recommending or adopting a dependency, verify maintenance and support status, fit, compatibility, license, security and total integration cost using current official sources\.",
            r"(?:^|(?<=\. ))Disclose unverified status; do not recommend discontinued or unverified libraries by default\.",
        ),
        "scope": (
            r"(?i)limit edits[^.]*task[^.]*owned files",
            r"(?i)remove code made unused by your changes",
            r"(?i)preexisting code only when its removal is explicitly authorized",
            r"(?i)required checks or approvals are satisfied",
        ),
        "verification": (
            r"(?i)observable success criteria",
            r"(?i)meaningful checks[^.]*actual candidate",
            r"(?i)preserve independent protection",
            r"(?i)unavailable checks",
            r"(?i)missing required checks or deliveries keep the task open",
            r"(?i)finish when the criteria are met",
        ),
        "redesign": (
            r"(?i)fix the cause, never the symptom",
            r"(?i)redesign that unit from the ground up",
            r"(?i)instead of patching the case at hand",
            r"(?i)debt, not a fix",
        ),
    }
    for label, patterns in requirements.items():
        for pattern in patterns:
            case.assertRegex(paragraphs[label], pattern, f"Working {label} loses {pattern}")
    return paragraphs


def markdown_section(case, text, title):
    match = re.search(rf"(?ms)^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text)
    case.assertIsNotNone(match, f"Required operative section missing: {title}")
    return " ".join(match.group(1).split())


def assert_brief_inputs(case, text):
    for pattern in (r"(?i)success criteria|observable delivery criteria",
                    r"(?i)approved requirement source", r"(?i)applicable[^.]*instruction[^.]*rules",
                    r"(?i)working discipline|four[^.]*rules"):
        case.assertRegex(text, pattern)


def assert_review_input_boundary(case, text, worker=False):
    case.assertRegex(text, r"(?i)independent discovery")
    case.assertRegex(text, r"(?i)omit peer findings|excludes peer results before your own delivery")
    case.assertRegex(text, r"(?i)verification or criticism")
    case.assertRegex(text, r"(?i)findings explicitly assigned by the domain method")
    if worker:
        case.assertIn("Do not read undeclared peer or private artifacts", text)
        case.assertIn("do not dispatch further workers", text)
    else:
        case.assertIn("unverified coordinator conclusions", text)


def assert_discipline_authority(case, protocol):
    discipline = markdown_section(case, protocol, "Working discipline")
    case.assertRegex(discipline, r"(?i)existing task authorization covers removal necessary to the approved change")
    case.assertRegex(discipline, r"(?i)grants no additional mutation or runtime authority")
    case.assertRegex(discipline, r"(?i)read-only worker[^.]*success[^.]*assigned evidence and report[^.]*permitted method")


def assert_delegated_writer(case, role):
    delegated = markdown_section(case, role, "Delegated execution")
    for pattern in (r"(?i)owned test files|assigned test files", r"(?i)select generation mode",
                    r"(?i)return[^.]*tests[^.]*observed evidence[^.]*coordinator",
                    r"(?i)correctly classified intended red|correctly classified expected red",
                    r"(?i)only[^.]*user[^.]*explicitly[^.]*implement the production code themselves",
                    r"(?i)new feature[^.]*automated tdd[^.]*does not select the human-wait branch",
                    r"(?i)coordinator owns[^.]*implementation step[^.]*final green gate"):
        case.assertRegex(delegated, pattern)
    case.assertNotIn('Use this when the user explicitly requests "TDD", "red-green-refactor", or is building a new feature from scratch.', role)
    generation = role[role.index("# MODE 1:"):role.index("# MODE 2:")]
    case.assertRegex(generation, r"(?i)run the test suite")
    interactive = role[role.index("# MODE 2:"):role.index("# ANTI-PATTERNS")]
    case.assertRegex(interactive, r"(?i)only[^.]*user[^.]*explicitly[^.]*interactive tdd teaching[^.]*implement the production code themselves")
    return delegated


class HarnessDomainOwnershipTests(unittest.TestCase):
    def test_weakened_simplicity_rules_cannot_satisfy_working_discipline(self):
        protocol = (ROOT / "plugins/work-controller/skills/work-record/SKILL.md").read_text(encoding="utf-8")
        # Mutate operative obligations independently; retaining the other terms
        # must not excuse a reversed preference, lost safeguard or weaker gate.
        mutations = (
            (" and existing contracts", ""),
            ("Prefer, in order, suitable project code and conventions, platform or standard-library facilities, dependencies already available, then the least new code.",
             "Prefer, in order, the least new code, dependencies already available, platform or standard-library facilities, then suitable project code and conventions."),
            ("Explain an exception when an earlier option cannot meet the requirement or is more complex overall.", "Exceptions need no explanation."),
            ("Reuse existing owners", "Replace existing owners"),
            ("add no speculative features", "add speculative features"),
            ("abstractions or configuration", "abstractions"),
            ("Preserve boundary validation", "Do not preserve boundary validation"),
            ("data-loss prevention, ", ""),
            ("security and accessibility", "security"),
            ("Before recommending or adopting a dependency, verify", "After recommending or adopting a dependency, verify"),
            ("maintenance and support status, ", ""),
            ("current official sources", "any available sources"),
            ("Disclose unverified status", "Hide unverified status"),
            ("do not recommend discontinued or unverified libraries", "recommend discontinued or unverified libraries"),
        )
        for original, replacement in mutations:
            with self.subTest(obligation=original):
                self.assertIn(original, working_paragraphs(self, protocol)["simplicity"])
                mutation = protocol.replace(original, replacement, 1)
                self.assertNotEqual(mutation, protocol)
                with self.assertRaises(AssertionError):
                    assert_working_discipline(self, mutation)

    def test_unrelated_mentions_cannot_replace_simplicity_obligations(self):
        protocol = (ROOT / "plugins/work-controller/skills/work-record/SKILL.md").read_text(encoding="utf-8")
        obligation = "Preserve boundary validation, data-loss prevention, security and accessibility."
        self.assertIn(obligation, working_paragraphs(self, protocol)["simplicity"])
        mutation = protocol.replace(obligation, "", 1) + "\n## Historical note\n\n" + obligation + "\n"

        with self.assertRaises(AssertionError):
            assert_working_discipline(self, mutation)

    def test_shared_execution_rules_reach_authoritative_and_downstream_instructions(self):
        protocol = (ROOT / "plugins/work-controller/skills/work-record/SKILL.md").read_text(encoding="utf-8")
        expected = assert_working_discipline(self, protocol)
        assert_discipline_authority(self, protocol)
        copies = (
            "CLAUDE.md", "AGENTS.md",
            "plugins/project-knowledge/skills/instructions-method/references/working-principles.md",
            "plugins/project-knowledge/skills/instructions-method/references/instruction-example.md",
        )

        for relative in copies:
            with self.subTest(copy=relative):
                actual = (ROOT / relative).read_text(encoding="utf-8")
                self.assertEqual(assert_working_discipline(self, actual), expected)
        working = (ROOT / copies[2]).read_text(encoding="utf-8")
        self.assertRegex(working, r"(?i)preserve equivalent project-specific guidance")
        self.assertNotIn("Delete code when it stops paying rent", working)
        self.assertIn("work-controller", manifest("project-knowledge")["dependencies"]["required"])
        self.assertEqual(manifest("work-controller")["dependencies"]["required"], [])

    def test_protocol_briefs_carry_execution_inputs_without_cross_reading_reviews(self):
        protocol = (ROOT / "plugins/work-controller/skills/work-record/SKILL.md").read_text(encoding="utf-8")
        brief = markdown_section(self, protocol, "Isolated worker briefs")
        worker = (ROOT / "plugins/work-controller/roles/isolated-worker.md").read_text(encoding="utf-8")
        worker_contract = markdown_section(self, worker, "Contract")

        for text in (brief, worker_contract):
            assert_brief_inputs(self, text)
        assert_review_input_boundary(self, brief)
        assert_review_input_boundary(self, worker_contract, worker=True)
        self.assertIn("working discipline the brief supplies", worker_contract)
        self.assertIn("coordinator-declared inputs", worker_contract)

    def test_delegated_test_writer_returns_evidence_and_reserves_human_wait_for_teaching(self):
        role = (ROOT / "plugins/testing/roles/test-writer.md").read_text(encoding="utf-8")

        assert_delegated_writer(self, role)

    def test_execution_discipline_survives_all_five_host_bodies_and_inline_resources(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.load import load_plugin
        from scripts.daodan.render import render_plugin

        registry = {p.parent.name: load_plugin(p.parent) for p in (ROOT / "plugins").glob("*/plugin.toml")}
        self.assertEqual(set(HOSTS), {"claude", "copilot", "codex", "pi", "opencode"})
        source_protocol = (ROOT / "plugins/work-controller/skills/work-record/SKILL.md").read_text(encoding="utf-8")
        expected_rules = dict(re.findall(r"(?m)^Working (assumptions|simplicity|scope|verification|redesign): ([^\n]+)$", source_protocol))
        brief = re.search(r"(?ms)^## Isolated worker briefs\n(.*?)(?=^## |\Z)", source_protocol)
        expected_brief = " ".join(brief.group(1).split()) if brief else ""
        source_worker = (ROOT / "plugins/work-controller/roles/isolated-worker.md").read_text(encoding="utf-8")
        expected_worker = markdown_section(self, source_worker, "Contract")
        source_writer = (ROOT / "plugins/testing/roles/test-writer.md").read_text(encoding="utf-8")
        writer = re.search(r"(?ms)^## Delegated execution\n(.*?)(?=^## |\Z)", source_writer)
        expected_writer = " ".join(writer.group(1).split()) if writer else ""

        with tempfile.TemporaryDirectory() as temporary:
            for host in HOSTS:
                roots = {}
                for plugin in ("work-controller", "project-knowledge", "testing", ENTRY):
                    roots[plugin] = Path(temporary) / host / plugin
                    render_plugin(registry[plugin], load_adapter(ROOT / "adapters", host), roots[plugin],
                                  adapters_root=ROOT / "adapters", plugin_registry=registry)
                protocol = without_host_binding(self, (roots["work-controller"] / "skills/work-record/SKILL.md").read_text(encoding="utf-8"), host)
                with self.subTest(host=host, component="protocol"):
                    self.assertEqual(assert_working_discipline(self, protocol), expected_rules)
                    assert_discipline_authority(self, protocol)
                    self.assertEqual(markdown_section(self, protocol, "Isolated worker briefs"), expected_brief)
                    rendered_brief = markdown_section(self, protocol, "Isolated worker briefs")
                    assert_brief_inputs(self, rendered_brief)
                    assert_review_input_boundary(self, rendered_brief)
                with self.subTest(host=host, component="instruction-destination"):
                    path = roots["project-knowledge"] / "skills/instructions-method/SKILL.md"
                    method = without_host_binding(self, path.read_text(encoding="utf-8"), host)
                    instructions = " ".join(method.split())
                    self.assertIn("Use explicit user destinations first", instructions)
                    self.assertIn("existing authoritative instruction file and documented synchronization rule", instructions)
                    self.assertIn("AGENTS.md for Codex", instructions)
                    self.assertIn("CLAUDE.md for Claude", instructions)
                    self.assertIn("do not invent a universal filename", instructions)
                    self.assertIn("do not rewrite a generated instruction copy directly", instructions)
                for reference in ("working-principles", "instruction-example"):
                    with self.subTest(host=host, component=reference):
                        path = roots["project-knowledge"] / f"skills/instructions-method/references/{reference}.md"
                        self.assertEqual(assert_working_discipline(self, path.read_text(encoding="utf-8")), expected_rules)
                for plugin, role, title, expected in (
                        ("work-controller", "isolated-worker", "Contract", expected_worker),
                        ("testing", "test-writer", "Delegated execution", expected_writer)):
                    with self.subTest(host=host, component=role):
                        text = without_host_binding(self, (roots[plugin] / role_path(host, plugin, role)).read_text(encoding="utf-8"), host)
                        self.assertEqual(markdown_section(self, text, title), expected)
                        if role == "isolated-worker":
                            contract = markdown_section(self, text, title)
                            assert_brief_inputs(self, contract)
                            assert_review_input_boundary(self, contract, worker=True)
                        else:
                            assert_delegated_writer(self, text)
                if host in {"codex", "pi"}:
                    # Since 38.0.0 the lifecycle and review entries are daodan's,
                    # so the inline role bodies ship in its package.
                    resources = (
                        (ENTRY, "work-controller", "isolated-worker", "Contract", expected_worker),
                        (ENTRY, "testing", "test-writer", "Delegated execution", expected_writer),
                    )
                    for consumer, owner, role, title, expected in resources:
                        with self.subTest(host=host, consumer=consumer, resource=role):
                            path = roots[consumer] / f"contracts/dispatch/{owner}/{role}.md"
                            text = without_host_binding(self, path.read_text(encoding="utf-8"), host)
                            self.assertEqual(markdown_section(self, text, title), expected)
                            if role == "isolated-worker":
                                contract = markdown_section(self, text, title)
                                assert_brief_inputs(self, contract)
                                assert_review_input_boundary(self, contract, worker=True)
                            else:
                                assert_delegated_writer(self, text)

    def test_review_wrapper_bindings_and_owner_resources_ship_on_every_host(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.load import load_plugin
        from scripts.daodan.render import render_plugin

        registry = {p.parent.name: load_plugin(p.parent) for p in (ROOT / "plugins").glob("*/plugin.toml")}
        with tempfile.TemporaryDirectory() as temporary:
            for host in HOSTS:
                # Since 38.0.0 the review wrappers are daodan's review entries.
                plugin = ENTRY
                with self.subTest(host=host):
                    root = Path(temporary) / host / plugin
                    render_plugin(registry[plugin], load_adapter(ROOT / "adapters", host), root,
                                  adapters_root=ROOT / "adapters", plugin_registry=registry)
                    for entry, roles in REVIEW_ENTRIES.items():
                        exported = (root / wrapper_path(host, plugin, entry)).read_text(encoding="utf-8")
                        body = without_host_binding(self, exported, host)
                        for binding in roles:
                            owner, role = binding.split("/")
                            identity = role if owner == plugin else f"{owner}:{role}"
                            self.assertIn(f"`{identity}`", body)
                        self.assertIn("work-controller:isolated-worker", body)
                        self.assertIn("senior-review:review-method", body)
                        # Rejection examples live in the separately verified
                        # binding; the actual method and harness stay neutral.
                        self.assertNotIn("subagent_type", body)
                    if host in {"codex", "pi"}:
                        for binding in BRANCH_ROLES | {"work-controller/isolated-worker"}:
                            owner, role = binding.split("/")
                            if owner == plugin:
                                continue
                            resource = root / "contracts/dispatch" / owner / f"{role}.md"
                            text = without_host_binding(self, resource.read_text(encoding="utf-8"), host)
                            self.assertIn(f"Owner: {owner}:{role}", text)
                            self.assertIn(f"<{owner}-plugin-root>", text)
                            for skill in registry[owner].components.skills:
                                self.assertIn(f"{owner}:{skill}", text)
                            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)

    def test_lifecycle_and_guide_wrappers_bind_their_composed_methods_on_every_host(self):
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.load import load_plugin
        from scripts.daodan.render import render_plugin

        registry = {p.parent.name: load_plugin(p.parent) for p in (ROOT / "plugins").glob("*/plugin.toml")}
        # Since 38.0.0 lifecycle change, repair and verify are daodan new-feature,
        # fix-bug and stage D of finish-task, each reviewing waves with the light
        # shape and the candidate with the branch shape; assess is check-health;
        # the knowledge guide and maintain entries are both write-docs.
        cases = {
            (ENTRY, "continue-task"): BRANCH_ROLES,
            (ENTRY, "refactor-code"): BRANCH_ROLES,
            (ENTRY, "run-maintenance"): BRANCH_ROLES,
            (ENTRY, "new-feature"): BRANCH_ROLES | {"testing/test-writer", "project-knowledge/instructions-auditor", "clean-code/clean-code-agent"},
            (ENTRY, "fix-bug"): BRANCH_ROLES | {"clean-code/clean-code-agent"},
            (ENTRY, "finish-task"): BRANCH_ROLES,
            (ENTRY, "check-health"): {"project-knowledge/documentation-engineer", "project-knowledge/guide-reviewer"},
            (ENTRY, "write-docs"): {"codebase-map/semantic-interconnect-mapper", "text-humanizer/text-humanizer"} | {f"project-knowledge/{role}" for role in ("codebase-explorer", "overview-writer", "tech-writer", "flow-writer", "ops-writer", "onboarding-writer", "documentation-engineer", "guide-reviewer", "instructions-auditor")},
        }
        with tempfile.TemporaryDirectory() as temporary:
            for host in HOSTS:
                for plugin in {plugin for plugin, _ in cases}:
                    root = Path(temporary) / host / plugin
                    render_plugin(registry[plugin], load_adapter(ROOT / "adapters", host), root,
                                  adapters_root=ROOT / "adapters", plugin_registry=registry)
                    for (case_plugin, entry), roles in cases.items():
                        if plugin != case_plugin:
                            continue
                        with self.subTest(host=host, plugin=plugin, entry=entry):
                            body = without_host_binding(self, (root / wrapper_path(host, plugin, entry)).read_text(encoding="utf-8"), host)
                            dispatch_rule = next(line for line in body.splitlines() if line.startswith("- Dispatch only roles from this set,"))
                            for binding in roles:
                                owner, role = binding.split("/")
                                identity = role if owner == plugin else f"{owner}:{role}"
                                self.assertIn(f"`{identity}`", body)
                                self.assertIn(f"`{identity}`", dispatch_rule)
                                if host in {"codex", "pi"} and owner != plugin:
                                    resource = root / "contracts/dispatch" / owner / f"{role}.md"
                                    text = without_host_binding(self, resource.read_text(encoding="utf-8"), host)
                                    self.assertIn(f"Owner: {owner}:{role}", text)
                                    self.assertIn(f"<{owner}-plugin-root>", text)
                                    for skill in registry[owner].components.skills:
                                        self.assertIn(f"{owner}:{skill}", text)

    def test_wrappers_keep_the_writes_a_worker_is_assigned_on_every_host(self):
        """A wrapper must not forbid the edits a mutating worker was authorized to make.

        project-lifecycle dispatches testing:test-writer and the inline isolated-worker,
        both of which write files. The wrappers used to allow workers only intermediate
        reports, which contradicted those roles on all five hosts. Since 38.0.0 the
        lifecycle change and repair wrappers are daodan new-feature and fix-bug.
        """
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.load import load_plugin
        from scripts.daodan.render import render_plugin

        def flat(text):
            return " ".join(text.split())

        rule = ("A worker writes only what the coordinator assigned to it: its intermediate report and, "
                "when its task authorizes edits, its assigned files. "
                "It never reverts preexisting or foreign changes.")
        owner = "The final report artifact has one exclusive owner in its declaring phase."
        templates = {
            "claude": "team-workflow.md.tmpl",
            "codex": "subagent-workflow.SKILL.md.tmpl",
            "copilot": "coordinator.agent.md.tmpl",
            "pi": "team-prompt.md.tmpl",
            "opencode": "team-command.md.tmpl",
        }
        self.assertEqual(set(templates), set(HOSTS))
        registry = {p.parent.name: load_plugin(p.parent) for p in (ROOT / "plugins").glob("*/plugin.toml")}
        with tempfile.TemporaryDirectory() as temporary:
            for host in HOSTS:
                template = flat((ROOT / "adapters" / host / "templates" / templates[host]).read_text(encoding="utf-8"))
                root = Path(temporary) / host / ENTRY
                render_plugin(registry[ENTRY], load_adapter(ROOT / "adapters", host), root,
                              adapters_root=ROOT / "adapters", plugin_registry=registry)
                rendered = {entry: flat(without_host_binding(
                    self, (root / wrapper_path(host, ENTRY, entry)).read_text(encoding="utf-8"), host))
                    for entry in ("new-feature", "fix-bug")}
                for name, text in {"template": template, **rendered}.items():
                    with self.subTest(host=host, wrapper=name):
                        self.assertNotIn("may write only intermediate reports", text)
                        self.assertIn(rule, text)
                        self.assertIn(owner, text)

    def test_clean_code_worker_executes_its_prepared_task_without_redispatch(self):
        """The readability worker must not restart the method that delegated it.

        readability-method dispatches clean-code-agent; the role used to load that
        same method, dispatch nested workers, ask the user to proceed and commit.
        """
        from scripts.daodan.adapter import HOSTS, load_adapter
        from scripts.daodan.load import load_plugin
        from scripts.daodan.render import render_plugin

        kernel = ROOT / "plugins/clean-code"
        role = (kernel / "roles/clean-code-agent.md").read_text(encoding="utf-8")
        frontmatter, _, body = role.partition("\n---\n")
        tools = next(line for line in frontmatter.splitlines() if line.startswith("tools:"))
        for nested in ("Task", "Agent"):
            self.assertNotIn(nested, tools)
        for restart in ("Load the `clean-code:readability-method`", "## Parallelism", "Proceed?"):
            self.assertNotIn(restart, body)
        self.assertIn("Never commit", body)
        method = (kernel / "skills/readability-method/SKILL.md").read_text(encoding="utf-8")
        step = method[method.index("## Step 4"):method.index("## Step 5")]
        self.assertIn("does not reload this method", step)
        for field in ("Owned files:", "Approved changes:", "Baseline:", "Authorization:", "Report path:"):
            self.assertIn(field, step)

        rendered_role = {
            "claude": "agents/clean-code-agent.md",
            "codex": "roles/clean-code-agent.md",
            "copilot": "agents/clean-code-agent.agent.md",
            "pi": "skills/clean-code-clean-code-agent/SKILL.md",
            "opencode": "agents/clean-code-agent.md",
        }
        self.assertEqual(set(rendered_role), set(HOSTS))
        with tempfile.TemporaryDirectory() as temporary:
            for host in HOSTS:
                with self.subTest(host=host):
                    root = Path(temporary) / host
                    render_plugin(load_plugin(kernel), load_adapter(ROOT / "adapters", host), root,
                                  adapters_root=ROOT / "adapters")
                    text = (root / rendered_role[host]).read_text(encoding="utf-8")
                    self.assertNotIn("Load the `clean-code:readability-method`", text)
                    if host == "copilot":
                        self.assertNotIn("'agent'", text.split("\n---\n", 1)[0])
                    if host == "opencode":
                        self.assertNotIn('action: "subagent"', text.split("\n---\n", 1)[0])

    def test_composed_inventory_binds_methods_without_copying_their_schedule(self):
        from scripts.daodan.reviewer_catalog import REVIEWER_ROLES
        self.assertFalse(manifest("senior-review")["components"].get("workflows"))
        self.assertIn("work-controller", manifest("senior-review")["dependencies"]["required"])
        for entry, roles in REVIEW_ENTRIES.items():
            with self.subTest(entry=entry):
                sidecar = tomllib.loads((ROOT / "plugins" / ENTRY / "workflows" / f"{entry}.toml").read_text(encoding="utf-8"))
                dispatch = sidecar["dispatch"]
                # Branch preparation may select any registered focused reviewer;
                # the light entry still declares only its two native defaults.
                expected = roles | {f"{owner}/{role}" for owner, role in REVIEWER_ROLES} if entry == "review-branch" else roles
                self.assertEqual(set(dispatch["roles"]), expected)
                self.assertTrue(dispatch["isolated"])
                self.assertIs(dispatch["inline_workers"], True)
                for provider in ("work-controller", "senior-review"):
                    self.assertIn(provider, manifest(ENTRY)["dependencies"]["required"])
                # Bind method workers without a duplicated outer phase graph.
                self.assertEqual([p["id"] for p in sidecar["phases"]], ["prepare", "execute"])
                for phase in sidecar["phases"]:
                    self.assertEqual(phase["isolation"], "shared")
                    for key in ("role", "fanout", "fanout_from"):
                        self.assertNotIn(key, phase)
        # Since 38.0.0 no kernel declares the team-review phase graph. Its delivery
        # barrier and single report owner are stated by the review method and stay
        # declared as outcomes of the review-branch contract.
        outcomes = tomllib.loads((ROOT / "plugins" / ENTRY / "workflows/review-branch.toml").read_text(encoding="utf-8"))["contract"]["outcomes"]
        for outcome in ("every-expected-reviewer-is-delivered-or-failed",
                        "consolidation-runs-only-after-the-delivery-barrier",
                        "only-the-consolidator-writes-the-final-report"):
            self.assertIn(outcome, outcomes)
        method = ROOT / "plugins/senior-review/skills/review-method"
        skill = " ".join((method / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertRegex(skill, r"(?i)one review preparation and final report owner")
        team = " ".join((method / "references/team-review.md").read_text(encoding="utf-8").split())
        self.assertRegex(team, r"(?i)hold the delivery barrier: wait until every dispatched reviewer is recorded `delivered` or `failed`")
        self.assertRegex(team, r"(?i)consolidation does not start until every spawned reviewer has either delivered")

    def test_one_review_owner_has_mandatory_specialists_on_every_host(self):
        from scripts.daodan.adapter import HOSTS

        core = manifest("senior-review")
        extras = {"react-development", "typescript-development", "platform-engineering"}
        self.assertTrue(extras.issubset(core["dependencies"]["required"]))
        self.assertTrue(extras.issubset(manifest("project-lifecycle")["dependencies"]["required"]))
        self.assertFalse((ROOT / "plugins/review-plus").exists())
        for host in HOSTS:
            with self.subTest(host=host):
                packages = ROOT / "exports" / host / "plugins"
                self.assertFalse((packages / "review-plus").exists())
                installed = json.loads((packages / "senior-review/.daodan-provenance.json").read_text())
                self.assertEqual(installed["version"], core["version"])
                for binding in STACK_ROLES:
                    owner, role = binding.split("/")
                    self.assertIn(role, manifest(owner)["components"]["roles"])

    def test_native_review_contracts_survive_the_envelope_migration(self):
        contracts = ROOT / "plugins/senior-review/contracts"
        self.assertEqual({p.stem for p in contracts.glob("*.toml")}, {"review-brief", "reviewer-binding", "reviewer-selection", "evidenced-finding", "reviewer-result", "delivery-ledger", "final-report"})
        for method in ("review-method", "review-preparation", "review-consolidation", "application-cleanup-method"):
            self.assertIn(method, manifest("senior-review")["components"]["skills"])
            self.assertTrue((ROOT / "plugins/senior-review/skills" / method / "SKILL.md").is_file())

    def test_python_uses_the_canonical_test_writer_without_a_cycle(self):
        python = manifest("python-development")
        self.assertIn("testing", python["dependencies"]["required"])
        self.assertIn("pytest-patterns", python["components"]["skills"])
        self.assertNotIn("python-tdd", python["components"]["skills"])
        self.assertNotIn("python-test-engineer", python["components"]["roles"])
        self.assertFalse((ROOT / "plugins/python-development/roles/python-test-engineer.md").exists())
        self.assertNotIn("python-development", manifest("testing")["dependencies"]["required"])
        for body in (ROOT / "plugins/testing").rglob("*.md"):
            self.assertNotIn("python-development:python-tdd", body.read_text(encoding="utf-8"))

    def test_mutation_owners_have_the_operational_protocol(self):
        for owner, method in (("senior-review", "application-cleanup-method"), ("testing", "test-remediation-method"), ("clean-code", "readability-method"), ("python-development", "python-refactor-method")):
            with self.subTest(owner=owner):
                self.assertIn("work-controller", manifest(owner)["dependencies"]["required"])
                body = (ROOT / "plugins" / owner / "skills" / method / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("work-controller:work-record", body)


if __name__ == "__main__":
    unittest.main()
