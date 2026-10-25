"""Static humanizer contracts and shipped reference parity, not LLM quality tests."""

from pathlib import Path
import re
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/text-humanizer"
SKILL = PLUGIN / "skills/anti-ai-writing-patterns"
HOSTS = ("claude", "copilot", "codex", "pi", "opencode")


class TextHumanizerContractTests(unittest.TestCase):
    def test_local_pattern_numbers_are_unique_and_complete(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        numbers = [int(n) for n in re.findall(r"^\| (\d+) \|", text, re.MULTILINE)]
        self.assertEqual(numbers, list(range(1, 26)))
        for path in (SKILL / "SKILL.md", PLUGIN / "roles/text-humanizer.md",
                     SKILL / "references/humanize.md"):
            with self.subTest(path=path):
                self.assertNotRegex(path.read_text(encoding="utf-8"),
                                    r"\b24 (?:AI writing|catalogued|patterns)")

    def test_reply_rule_keeps_context_and_fidelity_guards(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        row = next(line for line in text.splitlines() if line.startswith("| 25 |"))
        for guard in ("visible conversation", "preserving facts, evidence",
                      "requested detail", "uncertain context"):
            with self.subTest(guard=guard):
                self.assertIn(guard, row)
        self.assertIn("does not authorize dropping facts", text)
        self.assertIn("Never elide a passage", text)

    def test_italian_profile_is_mandatory_and_protects_native_voice(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        role = (PLUGIN / "roles/text-humanizer.md").read_text(encoding="utf-8")
        profile = (SKILL / "references/italiano.md").read_text(encoding="utf-8")
        self.assertIn("mandatory whenever the text is Italian", skill)
        self.assertIn("When the text is Italian, also read", role)
        for guard in ("non sono parole vietate", "non rendere ogni frase",
                      "Non tradurli per principio", "Con il contesto visibile",
                      "senza contesto non supporre", "Non aggiungere",
                      "Lei", "Synonym variation", "Long periods"):
            with self.subTest(guard=guard):
                self.assertIn(guard, profile)

    def test_every_host_ships_italian_examples_catalog_and_license(self):
        for host in HOSTS:
            exported = ROOT / f"exports/{host}/plugins/text-humanizer/skills/anti-ai-writing-patterns"
            for name in ("italiano.md", "pattern-catalog.md", "humanize.md", "upstream-license.txt"):
                with self.subTest(host=host, reference=name):
                    source = (SKILL / "references" / name).read_text(encoding="utf-8")
                    rendered = (exported / "references" / name).read_text(encoding="utf-8")
                    # Executable Markdown has a host binding wrapper; legal text does not.
                    if name.endswith(".md"):
                        rendered = re.sub(r"<daodan_host_binding\b[^>]*>.*?</daodan_host_binding>\s*",
                                          "", rendered, flags=re.DOTALL)
                    self.assertEqual(source, rendered)

    def test_worker_brief_forwards_conversation_as_separate_input(self):
        method = (SKILL / "references/humanize.md").read_text(encoding="utf-8")
        brief = re.search(r"```\n(Humanize the text below.*?)\n```", method, re.DOTALL)
        self.assertIsNotNone(brief)
        self.assertIn("Conversation context (not part of the final text):", brief.group(1))
        self.assertIn("relevant supplied messages, or none", brief.group(1))
        self.assertIn("do not write or edit any file", brief.group(1))

    def test_missing_file_is_not_inline_prose_and_write_consent_is_explicit(self):
        method = (SKILL / "references/humanize.md").read_text(encoding="utf-8")
        self.assertIn("missing or unreadable file is a blocker, not prose to rewrite", method)
        self.assertIn("wait for an explicit answer", method)
        self.assertIn("never infer consent or write while waiting", method)
        self.assertIn("Write only after the user picks 1 or 2", method)

    def test_dash_pass_respects_quoted_and_legal_content(self):
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        role = (PLUGIN / "roles/text-humanizer.md").read_text(encoding="utf-8")
        skill_pass = next(line for line in skill.splitlines() if line.startswith("6. Dash pass:"))
        role_pass = next(line for line in role.splitlines() if line.startswith("5. Dash pass:"))
        for text in (skill_pass, role_pass):
            self.assertIn("outside protected content", text)
            self.assertIn("Direct quotations, legal text, code", text)

    def test_examples_do_not_delete_obligations_or_promote_unnamed_sources(self):
        catalog = (SKILL / "references/pattern-catalog.md").read_text(encoding="utf-8")
        final = re.search(r"````text\n(.*?)\n````", catalog, re.DOTALL).group(1)
        self.assertIn("Teams must follow best practices.", final)
        self.assertNotIn("adoption has spread", final)
        synonym_example = catalog.split("### 11.", 1)[1].split("### 12.", 1)[0]
        after = synonym_example.split("**After:**", 1)[1]
        self.assertIn("must overcome obstacles", after)

    def test_leaf_contract_and_attribution_survive_update(self):
        manifest = tomllib.loads((PLUGIN / "plugin.toml").read_text(encoding="utf-8"))
        self.assertEqual(manifest["dependencies"]["required"], [])
        self.assertEqual(manifest["components"]["workflows"], ["humanize-text"])
        self.assertEqual(manifest["components"]["roles"], ["text-humanizer"])
        license_text = (SKILL / "references/upstream-license.txt").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2025 Siqi Chen", license_text)
        self.assertIn("THE SOFTWARE IS PROVIDED", license_text)
        self.assertIn("blader/humanizer", (ROOT / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
