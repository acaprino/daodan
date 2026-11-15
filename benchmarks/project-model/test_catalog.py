"""Tests for catalog.py. Run: python -m unittest test_catalog.py"""

import unittest

import catalog

DOMAIN = {"groups": [{"id": "structure", "title": "Struttura"}],
          "cases": [{"id": "no-build-file", "group": "structure", "definition": "Codice senza file di build."},
                    {"id": "nested-module", "group": "structure", "definition": "Modulo annidato.", "measured": "chi"}]}
DOC = {"languages": [{"path": "a.go", "language": "Go"}], "excluded": [],
       "units": [{"name": "x", "kind": "go-module", "root": ".", "manifest": "go.mod"},
                 {"name": "y", "kind": "go-module", "root": "sub", "manifest": "sub/go.mod"}],
       "toolchains": [{"tool": "go", "version": "1.22", "declared_in": "go.mod"},
                      {"tool": "go", "version": "1.23", "declared_in": "sub/go.mod"}],
       "dependencies": [], "frameworks": [], "services": [], "needs": {"container": False, "reason": ""},
       "traps": ["t"], "cases": ["nested-module"]}


class Render(unittest.TestCase):
    def test_entry_and_coverage(self):
        text = catalog.render(DOMAIN, {"sys-go-two": DOC},
                              {"sys-go-two": {"repo": "https://github.com/o/r.git", "commit": "a" * 40, "licence": "MIT"}})
        for line in ("- Origine: [github.com/o/r](https://github.com/o/r.git) al commit `" + "a" * 40 + "`, licenza MIT.",
                     "- Unità: go-module (2).",
                     "  - go: 1.22 (`go.mod`); 1.23 (`sub/go.mod`)",
                     "  - `nested-module`: Modulo annidato.",
                     "| Struttura | `nested-module` | Modulo annidato. | 1 | letto | chi |",
                     "| Struttura | `no-build-file` | Codice senza file di build. | 0 | dai dati |  |",
                     "- `no-build-file`: nessun progetto"):
            self.assertIn(line, text.splitlines())

    def test_committed_file_is_the_generator_output(self):
        self.assertEqual(catalog.OUT.read_text(encoding="utf-8"), catalog.render(*catalog.load()))


if __name__ == "__main__":
    unittest.main()
