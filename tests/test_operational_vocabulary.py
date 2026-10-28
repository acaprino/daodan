"""Operational vocabulary regression checks with domain examples preserved."""
from pathlib import Path
import unittest
from scripts.lint_host_vocabulary import scan_text
from scripts.sync_codex_instructions import adapt_claude_instructions_for_codex


class OperationalVocabularyTests(unittest.TestCase):
    def test_frontmatter_tools_are_neutral_metadata(self):
        text = "---\ntools: Bash, WebSearch, Agent\n---\nUse the host bindings.\n"
        self.assertEqual([], list(scan_text(Path("role.md"), text)))

    def test_nested_instruction_primitives_are_rejected(self):
        text = "Run actual checks via Bash.\nAskUserQuestion for scope.\nsubagent_type: x\nUse `Agent`.\n"
        hits = list(scan_text(Path("references/prompt.md"), text))
        self.assertEqual([1, 2, 3, 4], [hit[1] for hit in hits])

    def test_invented_tool_names_are_rejected(self):
        text = ("Search with host web search binding.\n"
                "Ask with the active host question mechanism.\n"
                "- **Host network search**: discovery.\n"
                "Collect through the host shell.\n"
                "Use network search, then network fetch; ask a user question.\n"
                "Stop when the host binding leaves network search unavailable.\n")
        hits = list(scan_text(Path("roles/researcher.md"), text))
        self.assertEqual([1, 2, 3, 4], [hit[1] for hit in hits])

    def test_codex_provisioning_uses_the_available_cli_commands(self):
        text = "claude plugin install testing@daodan\nclaude plugin marketplace update daodan\n"
        self.assertEqual("codex plugin add testing@daodan\ncodex plugin marketplace upgrade daodan\n",
                         adapt_claude_instructions_for_codex(text))

    def test_domain_shells_and_classes_are_not_dispatch(self):
        text = "```python\nclass Task:\n    pass\n```\nGit Bash needs Perl.\n# Bash\n"
        self.assertEqual([], list(scan_text(Path("example.md"), text)))


if __name__ == "__main__":
    unittest.main()
