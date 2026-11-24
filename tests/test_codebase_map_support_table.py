"""The support document is what `support_table.py` writes now, from the product and the committed results."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "daodan/core"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import support_table  # noqa: E402


class SupportTableTests(unittest.TestCase):
    def test_the_committed_document_is_the_one_the_script_writes(self):
        self.assertEqual(support_table.check(), [])

    def test_the_document_does_not_change_with_the_library_version_the_environment_installs(self):
        from premap import module_graph
        with mock.patch.object(module_graph, "VERSION", module_graph.DOCUMENTED.format("0.0.0")):
            self.assertEqual(support_table.check(), [])

    def test_a_document_that_differs_is_a_problem(self):
        with tempfile.TemporaryDirectory() as folder:
            stale = Path(folder) / "supporto.md"
            stale.write_text("# Supporto\n", encoding="utf-8")
            self.assertTrue(support_table.check(stale))

    def test_a_measure_names_its_file_and_a_missing_one_says_so(self):
        text = support_table.render()
        self.assertIn("2026-11-16-finale.report.json", text)
        self.assertIn("daodan_stack.json", text)
        self.assertIn("non misurato", text)


def _entry(ident, category, rule=True):
    return {"id": ident, "name": ident.capitalize(), "kind": "project", "type": "altro", "category": category,
            "from": ["stack-analyser"] if rule else ["additions"]}


class StackSectionTests(unittest.TestCase):
    REGISTRY = {"entries": [_entry("vue", "framework"), _entry("zod", "library"), _entry("twig", "library"),
                            _entry("asdf", "tool"), _entry("kafka", "service"), _entry("legacy", "tool", rule=False)]}

    def rows(self, registry):
        lines = support_table.stack_section(registry, {"fixtures": {}})
        return "\n".join(lines), {line.split(" | ")[1].strip("`"): line.split(" | ") for line in lines
                                  if line.startswith("| ") and line.count("`") >= 2}

    def test_the_classes_and_their_sentence_follow_the_registry(self):
        text, _ = self.rows(self.REGISTRY)
        self.assertIn("| library | 2 | 2 |", text)
        self.assertIn("| tool | 1 | 2 |", text)  # a rule of the fork for one, the category written for both
        self.assertIn("Ognuna delle 5 voci `project` con una regola del fork ha la sua `category` scritta", text)
        defaulted = {"entries": [*self.REGISTRY["entries"], _entry("numpy", None)]}
        text = self.rows(defaulted)[0]
        self.assertIn("| framework | 2 | 1 |", text)
        self.assertIn("Delle 6 voci `project` con una regola del fork, 1 è `framework` solo per il default", text)
        self.assertNotIn("Ognuna delle", text)

    def test_a_project_of_category_service_is_in_the_services_list(self):
        text = "\n".join(support_table.services_section(self.REGISTRY, {"fixtures": {}}))
        self.assertIn("Servizi con una regola del fork: 1 voci", text)
        self.assertIn("| Kafka | `kafka` | altro |", text)

    def test_a_row_says_whether_the_fork_has_a_rule_for_the_entry_and_no_column_lists_signs(self):
        text, rows = self.rows(self.REGISTRY)
        self.assertIn("Framework, librerie e strumenti: 5 voci", text)
        self.assertNotIn("kafka", rows)  # a service is in the services' list
        head = next(line for line in text.splitlines() if line.startswith("| Voce |"))
        column = head.split(" | ").index("Regola del fork")
        self.assertEqual((rows["zod"][column], rows["legacy"][column]), ("sì", "no"))
        for gone in ("Segni", "Codice analizzato"):
            self.assertNotIn(gone, head)
        self.assertFalse(hasattr(support_table, "PACKAGE_LANGUAGES"))

    def test_an_own_reading_is_what_its_readers_read_and_every_reader_is_tied_to_an_entry(self):
        from unittest import mock

        import languages
        from indexers import components, css, css_tailwind
        from languages import sfc
        text, rows = self.rows(self.REGISTRY)
        head = next(line for line in text.splitlines() if line.startswith("| Voce |"))
        column = head.split(" | ").index("Lettura propria")
        self.assertIn("indexers/components.py", rows["vue"][column])
        self.assertEqual(rows["zod"][column], "—")
        registry = {e["id"]: e for e in support_table._json(support_table.service_registry.REGISTRY)["entries"]}
        for ident, key in support_table.OWN_READINGS.items():
            self.assertIn(support_table.service_registry.entry_category(registry[ident]), ("framework", "library"))
            self.assertTrue(support_table.own_reading(key), ident)
        sfc_read = {suffix for suffix, language in languages.SUPPORTED_EXTENSIONS.items()
                    if isinstance(languages.get_adapter(language), type(sfc.vue_adapter))}
        self.assertEqual(set(support_table.OWN_READINGS.values()),
                         set(components.SUFFIXES) | set(css.COMPONENTS) | sfc_read | {css_tailwind.PACKAGE})
        self.assertIn("stack-analyser", registry["tailwind"]["from"])  # the package it asks for is the fork's rule's
        self.assertIn("del template solo gli eventi (`premap/astro.py`)", support_table.own_reading(".astro"))
        with mock.patch.dict(css.COMPONENTS, clear=True):  # a reading the code no longer has is not said
            self.assertNotIn("indexers/css_", support_table.own_reading(".vue"))
        self.assertEqual(support_table.own_reading(".nothing"), "")


if __name__ == "__main__":
    unittest.main()
