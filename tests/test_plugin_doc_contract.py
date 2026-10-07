"""Protection against lossy doc updates and hidden transitive requirements."""

from pathlib import Path
from types import SimpleNamespace
import unittest

from scripts.sync_plugin_docs import END, START, closure, replace_reference


class PluginDocContract(unittest.TestCase):
    def test_refresh_preserves_manual_content_on_both_sides_of_reference(self):
        original = f"# User guide\n\nA deliberate explanation.\n\n{START}\nold facts\n{END}\n\nA manual example.\n"
        replacement = f"{START}\ncurrent facts\n{END}"
        expected = original.replace(f"{START}\nold facts\n{END}", replacement)
        updated = replace_reference(original, replacement, Path("guide.md"))
        self.assertEqual(updated, expected)
        self.assertEqual(replace_reference(updated, replacement, Path("guide.md")), updated)
        for malformed in (original.replace(END, ""), original + START, f"{END}\n{START}"):
            with self.assertRaises(ValueError):
                replace_reference(malformed, replacement, Path("guide.md"))

    def test_shared_provider_requirements_remain_mandatory_and_are_counted_once(self):
        plugins = {
            "entry": SimpleNamespace(required_dependencies=("left", "right", "method@upstream")),
            "left": SimpleNamespace(required_dependencies=("leaf",)),
            "right": SimpleNamespace(required_dependencies=("leaf", "checks@vendor")),
            "leaf": SimpleNamespace(required_dependencies=("method@upstream",)),
        }
        self.assertEqual(closure("entry", plugins),
                         (["entry", "leaf", "left", "right"], ["checks@vendor", "method@upstream"]))
        plugins["leaf"].required_dependencies = ("misspelled-provider",)
        with self.assertRaises(ValueError):
            closure("entry", plugins)


if __name__ == "__main__":
    unittest.main()
