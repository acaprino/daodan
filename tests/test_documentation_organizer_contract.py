"""Documentation-organizer policy and five-host propagation contracts.

These checks prove declared instructions and shipped resources, not live agent
execution, correct human answers, document quality or filesystem confinement.
The behavioral cases under evals/project-knowledge/cases remain separate.
"""
from dataclasses import replace
from pathlib import Path
import re
import tomllib
import unittest

from host_binding_assertions import without_host_binding


ROOT = Path(__file__).resolve().parents[1]
OWNER = "project-knowledge"
ROLE = "documentation-organizer"
REFERENCE = "skills/project-knowledge/references/documentation-organization.md"
HOSTS = ("claude", "copilot", "codex", "pi", "opencode")
SECTIONS = ("Required plugin dossier", "Dependency and intake provenance",
            "Legacy decisions and forbidden output", "Execution and verification")


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def section(case, text, title):
    match = re.search(rf"(?ms)^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text)
    case.assertIsNotNone(match, f"Missing operative section: {title}")
    return " ".join(match.group(1).split())


def requirements(case, text, patterns):
    for pattern in patterns:
        case.assertRegex(text, pattern)


def assert_legacy_boundary(case, text):
    """Keep authorization tests inside the rule that governs legacy mutation."""
    legacy = section(case, text, "Legacy decisions and forbidden output")
    requirements(case, legacy, (
        r"(?i)(?:each|every)[^.]*\b(?:spec|specification)[^.]*plan[^.]*research",
        r"(?i)(?:human|user)[^.]*answer",
        r"(?i)retention[^.]*destination|destination[^.]*retention",
        r"(?i)(?:require|must)[^.]*explicit human answer[^.]*retention and destination[^.]*before dependent work",
        r"(?i)archive|archiving", r"(?i)retire|retirement",
        r"(?i)global[^.]*authoriz", r"(?i)silence", r"(?i)timeout",
        r"(?i)assumed[^.]*approval|assum[^.]*consent",
        r"(?i)global[^.]*authoriz[^.]*(?:not substitutes|cannot satisfy|do not satisfy|never count)",
        r"(?i)(?:changed|changes|digest)[^.]*decision|decision[^.]*changed",
        r"(?i)preserve[^.]*unanswered[^.]*bytes|unanswered[^.]*byte[^.]*preserv",
        r"(?i)continue[^.]*independent",
        r"(?i)(?:no|never|forbid|do not)[^.]*write[^.]*docs/superpowers",
        r"(?i)link[^.]*repair", r"(?i)index[^.]*generat",
    ))
    return legacy


def role_path(host):
    return {
        "claude": f"agents/{ROLE}.md", "copilot": f"agents/{ROLE}.agent.md",
        "codex": f"roles/{ROLE}.md", "pi": f"skills/{OWNER}-{ROLE}/SKILL.md",
        "opencode": f"agents/{ROLE}.md",
    }[host]


def wrapper_path(host):
    return {
        "claude": "commands/write-docs.md", "copilot": "agents/write-docs-coordinator.agent.md",
        "codex": "skills/write-docs-workflow/SKILL.md", "pi": "prompts/daodan-write-docs.md",
        "opencode": "commands/write-docs.md",
    }[host]


class DocumentationOrganizerContractTests(unittest.TestCase):
    def test_existing_owner_declares_mutating_isolated_role_without_new_entry(self):
        plugin = tomllib.loads(read("plugins/project-knowledge/plugin.toml"))
        self.assertIn(ROLE, plugin["components"]["roles"])
        self.assertNotIn(ROLE, plugin["components"]["skills"])
        self.assertEqual(plugin["components"]["workflows"], [])
        for capability in ("repository.read", "repository.write", "roles.dispatch", "contexts.isolate"):
            self.assertIn(capability, plugin["capabilities"]["required"])
        self.assertIn("work-controller", plugin["dependencies"]["required"])
        body = read(f"plugins/{OWNER}/roles/{ROLE}.md")
        frontmatter = body.split("---", 2)[1]
        self.assertRegex(frontmatter, r"(?m)^model: inherit$")
        tools = re.search(r"(?m)^tools: (.*)$", frontmatter)
        if tools is not None:
            self.assertRegex(tools.group(1), r"\bWrite\b")
            self.assertRegex(tools.group(1), r"\bEdit\b")
        requirements(self, body, (r"(?i)load[^\n]*project-knowledge",
                                 r"(?i)read[^.]*documentation-organization\.md"))
        # The role consumes the policy; it must not grow a second copy.
        self.assertNotIn("## Required plugin dossier", body)

    def test_write_docs_routes_and_declares_the_method_worker(self):
        workflow = tomllib.loads(read("plugins/daodan/workflows/write-docs.toml"))
        self.assertIn(f"{OWNER}/{ROLE}", workflow["dispatch"]["roles"])
        self.assertTrue(workflow["dispatch"]["isolated"])
        body = read("plugins/daodan/workflows/write-docs.md")
        requirements(self, body, (r"(?i)organiz[^\n]*project-knowledge",
                                 r"documentation-organization\.md"))
        method = read(f"plugins/{OWNER}/skills/project-knowledge/SKILL.md")
        self.assertIn(ROLE, method)
        self.assertIn("references/documentation-organization.md", method)

    def test_missing_write_or_isolation_capability_is_not_silently_supported(self):
        from scripts.daodan.adapter import load_adapter, resolve_support
        from scripts.daodan.load import load_plugin

        plugin = load_plugin(ROOT / "plugins" / OWNER)
        for host in HOSTS:
            adapter = load_adapter(ROOT / "adapters", host)
            for capability in ("repository.write", "contexts.isolate", "roles.dispatch"):
                with self.subTest(host=host, capability=capability):
                    bindings = dict(adapter.bindings)
                    bindings.pop(capability)
                    support = resolve_support(plugin, replace(adapter, bindings=bindings))
                    self.assertEqual(support.state, "unsupported")
                    self.assertIn(capability, support.missing_capabilities)

    def test_dossier_requires_semantic_use_cases_and_attributed_research(self):
        dossier = section(self, read(f"plugins/{OWNER}/{REFERENCE}"), SECTIONS[0])
        for filename in ("README.md", "functional-spec.md", "technical-spec.md", "use-cases.md",
                         "research/README.md", "validation.md", "dependencies.md", "intakes.md", "licenses.md"):
            self.assertIn(filename, dossier)
        requirements(self, dossier, (
            r"(?i)(?:one|single)[^.]*folder[^.]*plugin|plugin[^.]*one[^.]*folder",
            r"(?i)actor", r"(?i)precondition", r"(?i)trigger",
            r"(?i)(?:observable|expected)[^.]*result|expected[^.]*outcome",
            r"(?i)research[^.]*attribut|attribut[^.]*research",
            r"(?i)(?:do not|never)[^.]*invent",
        ))

    def test_intake_includes_delegated_dependencies_and_evidenced_versions(self):
        provenance = section(self, read(f"plugins/{OWNER}/{REFERENCE}"), SECTIONS[1])
        requirements(self, provenance, (
            r"(?i)copied[^.]*content", r"(?i)delegated[^.]*runtime",
            r"(?i)tools?[^.]*models?[^.]*parsers?",
            r"(?i)Craft", r"Worktrunk", r"EmbeddingGemma", r"tree-sitter",
            r"(?i)URL", r"(?i)credits?", r"(?i)licen[sc]e[^.]*evidence",
            r"(?i)adopted[^.]*excluded|excluded[^.]*adopted",
            r"(?i)local[^.]*paths?", r"(?i)reasons?",
            r"(?i)(?:actual|evidenced)[^.]*intake[^.]*date|intake[^.]*date[^.]*evidence",
            r"(?i)Daodan[^.]*marketplace[^.]*version",
            r"(?i)local[^.]*plugin[^.]*version", r"(?i)upstream[^.]*release[^.]*commit",
            r"(?i)unknown", r"(?i)(?:do not|never)[^.]*invent",
            r"(?i)supported", r"(?i)installed", r"(?i)discovered", r"(?i)currently? available|current[^.]*available",
        ))

    def test_legacy_decisions_are_individual_answered_and_bound_to_source(self):
        assert_legacy_boundary(self, read(f"plugins/{OWNER}/{REFERENCE}"))

    def test_unrelated_keyword_note_cannot_replace_legacy_gate(self):
        source = read(f"plugins/{OWNER}/{REFERENCE}")
        start = source.index("## Legacy decisions and forbidden output")
        end = source.index("## Execution and verification", start)
        mutation = (source[:start] + "## Legacy decisions and forbidden output\n\n"
                    "Organize legacy files when useful.\n\n" + source[end:]
                    + "\n## Detached note\n\n" + source[start:end])
        with self.assertRaises(AssertionError):
            assert_legacy_boundary(self, mutation)

    def test_weakened_human_answer_gate_is_rejected(self):
        source = read(f"plugins/{OWNER}/{REFERENCE}")
        gate = re.search(r"(?is)(?:require|must)[^.]*explicit human answer[^.]*retention and destination[^.]*before dependent work", source)
        self.assertIsNotNone(gate)
        mutation = source[:gate.start()] + "Assume a suitable answer for retention and destination" + source[gate.end():]
        with self.assertRaises(AssertionError):
            assert_legacy_boundary(self, mutation)

    def test_execution_does_not_turn_registration_into_behavioral_evidence(self):
        execution = section(self, read(f"plugins/{OWNER}/{REFERENCE}"), SECTIONS[3])
        requirements(self, execution, (
            r"(?i)snapshot|digest|source bytes|hashes", r"(?i)owned", r"(?i)links?|references?",
            r"(?i)unavailable|missing", r"(?i)structural|propagation|static checks",
            r"(?i)live|behavioral|installed.host",
        ))

    def test_all_five_hosts_ship_role_nested_policy_and_write_docs_binding(self):
        source = read(f"plugins/{OWNER}/{REFERENCE}")
        expected = {title: section(self, source, title) for title in SECTIONS}
        source_frontmatter = read(f"plugins/{OWNER}/roles/{ROLE}.md").split("---", 2)[1]
        restricted = re.search(r"(?m)^tools:", source_frontmatter) is not None
        for host in HOSTS:
            with self.subTest(host=host):
                base = ROOT / "exports" / host / "plugins"
                exported_role = (base / OWNER / role_path(host)).read_text(encoding="utf-8")
                role = without_host_binding(self, exported_role, host)
                self.assertIn("documentation-organization.md", role)
                frontmatter = exported_role.split("---", 2)[1]
                # An omitted source tool restriction inherits host defaults.
                # A declared restriction must preserve its mutating access.
                if host == "claude" and "tools:" in frontmatter:
                    self.assertRegex(frontmatter, r"(?m)^tools:.*\bWrite\b")
                elif host == "copilot" and "tools:" in frontmatter:
                    self.assertRegex(frontmatter, r"(?m)^tools:.*['\"]edit['\"]")
                elif host == "opencode" and "permissions:" in frontmatter:
                    rules = re.findall(r'(?m)^\s*- action: "([^"]+)"\s+resource: "([^"]+)"\s+effect: (allow|deny)$', frontmatter)
                    if restricted:
                        self.assertIn(("edit", "*", "allow"), rules)
                        self.assertNotIn(("edit", "*", "deny"), rules)
                    else:
                        # OpenCode's loader appends this package-only allowance
                        # to native defaults. A deny-first list replaces those
                        # defaults and would silently restrict this role.
                        self.assertEqual(rules, [("external_directory", "<package-root>/**", "allow")])
                model = re.search(r"(?m)^model: (.*)$", frontmatter)
                if model is not None:
                    self.assertEqual(model.group(1).strip(), "inherit")
                nested = without_host_binding(self, (base / OWNER / REFERENCE).read_text(encoding="utf-8"), host)
                for title in SECTIONS:
                    self.assertEqual(section(self, nested, title), expected[title])
                assert_legacy_boundary(self, nested)
                method = without_host_binding(self, (base / OWNER / "skills/project-knowledge/SKILL.md").read_text(encoding="utf-8"), host)
                self.assertIn(ROLE, method)
                self.assertIn("references/documentation-organization.md", method)
                wrapper = without_host_binding(self, (base / "daodan" / wrapper_path(host)).read_text(encoding="utf-8"), host)
                self.assertIn(f"{OWNER}:{ROLE}", wrapper)
                self.assertIn("documentation-organization.md", wrapper)
                if host in {"codex", "pi"}:
                    resource = f"contracts/dispatch/{OWNER}/{ROLE}.md"
                    self.assertIn(resource, wrapper)
                    dispatch = without_host_binding(self, (base / "daodan" / resource).read_text(encoding="utf-8"), host)
                    self.assertIn("documentation-organization.md", dispatch)
                    self.assertIn(OWNER, dispatch)
                else:
                    self.assertRegex(wrapper, rf"`{OWNER}:{ROLE}`: dispatch the installed")


if __name__ == "__main__":
    unittest.main()
