"""Report renderer behavior and its real filesystem CLI boundary.

No existing owner was found for render_report or report-rendering. This follows
the repository's flat unittest placement; host adaptation contracts extend their
existing owner in test_daodan_host_rendering.py. Browser interactions have a
separate runtime lane rather than an optional dependency in this suite.
"""

import base64
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/report-rendering/skills/report-renderer/scripts/render_report.py"


class Element:
    def __init__(self, tag, attrs=()):
        self.tag = tag
        self.attrs = dict(attrs)
        self.children = []

    def text(self):
        return "".join(child.text() if isinstance(child, Element) else child
                       for child in self.children)

    def descendants(self, tag=None):
        for child in self.children:
            if isinstance(child, Element):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.descendants(tag)


class Document(HTMLParser):
    """Observe HTML content and resources without executing scripts."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.stack = [self.root]
        self.feed(page)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def nodes(self, tag):
        return list(self.root.descendants(tag))

    def source(self):
        nodes = [node for node in self.nodes("script")
                 if node.attrs.get("id") == "report-source"]
        if len(nodes) != 1:
            raise AssertionError("The complete source must have one recoverable payload")
        node = nodes[0]
        if node.attrs.get("type") != "text/plain" or node.attrs.get("data-encoding") != "base64":
            raise AssertionError("The source payload must be inert UTF-8 bytes encoded as base64")
        return base64.b64decode(node.text(), validate=True)


def renderer():
    spec = importlib.util.spec_from_file_location("daodan_report_renderer_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.render_report


class ReportContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.render = staticmethod(renderer())

    def test_unicode_title_and_entire_source_survive_rendering(self):
        source = "# Città e qualità 🧭\r\n\r\nDecisione: café, 東京, naïve.\r\n"

        page = self.render(source, source_name="analisi qualità.md")
        document = Document(page)

        self.assertEqual(document.nodes("h1")[0].text(), "Città e qualità 🧭")
        self.assertIn("Decisione: café, 東京, naïve.", [node.text() for node in document.nodes("p")])
        self.assertEqual(document.source(), source.encode("utf-8"))

    def test_literal_heading_hash_survives_while_spaced_closing_markers_are_removed(self):
        for source, expected in (("# C#\n", "C#"), ("# C# ##\n", "C#"),
                                 ("# Heading ###\n", "Heading")):
            with self.subTest(source=source):
                document = Document(self.render(source))

                self.assertEqual(document.nodes("h1")[0].text(), expected)
                self.assertEqual(document.nodes("title")[0].text(), expected)
                self.assertTrue(any(link.text() == expected for nav in document.nodes("nav")
                                    for link in nav.descendants("a")))
                self.assertEqual(document.source(), source.encode("utf-8"))

    def test_setext_heading_keeps_literal_hashes_in_heading_title_and_navigation(self):
        for underline, tag in (("===", "h1"), ("---", "h2")):
            source = ("# Overview\n\n" if tag == "h2" else "") + f"Result ##\n{underline}\n"
            expected_title = "Overview" if tag == "h2" else "Result ##"
            with self.subTest(underline=underline):
                document = Document(self.render(source))

                self.assertEqual(document.nodes(tag)[0].text(), "Result ##")
                self.assertEqual(document.nodes("title")[0].text(), expected_title)
                self.assertTrue(any(link.text() == "Result ##" for nav in document.nodes("nav")
                                    for link in nav.descendants("a")))
                self.assertEqual(document.source(), source.encode("utf-8"))

    def test_native_statuses_evidence_and_unscored_qualifiers_remain_visible(self):
        source = """# Review

| Finding | Severity | Evidence | Disposition |
| --- | --- | --- | --- |
| Login blocks entry | P0 | src/login.py:17 | [blocked] |
| Retry requirement | P1 | NOT VERIFIED | [warn] |
| Candidate balance | not scored | NOT SCREENED: EUIPO | deferred |

Coverage: inventory 32, read in depth 9, exercised at runtime none.
"""

        document = Document(self.render(source, profile="review"))

        rows = [node.text() for node in document.nodes("tr")]
        for preserved in ("P0", "src/login.py:17", "[blocked]", "P1", "NOT VERIFIED",
                          "[warn]", "not scored", "NOT SCREENED: EUIPO", "deferred"):
            with self.subTest(value=preserved):
                self.assertTrue(any(preserved in row for row in rows), preserved)
        self.assertTrue(any("exercised at runtime none" in node.text()
                            for node in document.nodes("p")))
        self.assertEqual(document.source(), source.encode("utf-8"))

    def test_nested_lists_and_pipe_content_keep_their_semantics(self):
        source = r"""# Contract

- Parent requirement
  - Child requirement
    1. Ordered detail
- Sibling requirement

| Requirement | Value |
| --- | --- |
| Inline expression | `left|right` |
| Escaped separator | one\|two |
"""

        document = Document(self.render(source))

        parent = next(node for node in document.nodes("li")
                      if "Parent requirement" in node.text())
        self.assertTrue(any("Child requirement" in node.text()
                            for node in parent.descendants("li")))
        self.assertTrue(any("Ordered detail" in node.text()
                            for node in parent.descendants("ol")))
        rows = [[cell.text() for cell in node.children
                 if isinstance(cell, Element) and cell.tag == "td"]
                for node in document.nodes("tr")]
        self.assertIn(["Inline expression", "left|right"], rows)
        self.assertIn(["Escaped separator", "one|two"], rows)
        self.assertTrue(any(node.text() == "left|right" for node in document.nodes("code")))

    def test_unknown_markdown_and_mermaid_are_displayed_instead_of_removed(self):
        source = """# Architecture

```mermaid
flowchart LR
  Client --> API
```

```unrecognised-contract
unknown: preserve this requirement
```

[requirements][spec]

[spec]: ./evidence.md "Canonical requirements"
"""

        document = Document(self.render(source))

        code = [node.text() for node in document.nodes("pre")]
        self.assertTrue(any("flowchart LR" in text and "Client --> API" in text for text in code))
        self.assertTrue(any("unknown: preserve this requirement" in text for text in code))
        self.assertTrue(any("[spec]: ./evidence.md" in node.text() for node in document.nodes("p")))
        self.assertEqual(document.source(), source.encode("utf-8"))

    def test_raw_html_and_unsafe_uris_cannot_become_executable_page_content(self):
        source = """# Literal source

<script>globalThis.injectedBySource = 1</script>
<iframe src="https://untrusted.example/embed"></iframe>
<img src=x onerror="alert(1)">

[Unsafe](javascript:alert%281%29)
[Encoded](javascript&#58;alert%281%29)
[Data](data:text/html,script)
![SVG payload](data:image/svg+xml,unsafe)
[Safe web](https://example.com/evidence)
[Mail](mailto:owner@example.com)
[Relative](./evidence.md)
"""

        document = Document(self.render(source))

        scripts = [node for node in document.nodes("script")
                   if node.attrs.get("type") != "text/plain"]
        self.assertTrue(scripts, "The offline controls need an embedded script")
        self.assertFalse(any("injectedBySource" in node.text() for node in scripts))
        self.assertEqual(document.nodes("iframe"), [])
        for node in document.root.descendants():
            self.assertFalse(any(name.startswith("on") for name in node.attrs), node.attrs)
            for attribute in ("href", "src"):
                value = node.attrs.get(attribute, "") or ""
                self.assertFalse(value.lower().startswith("javascript:"), value)
                if value.lower().startswith("data:"):
                    self.assertTrue(value.startswith("data:text/plain;charset=utf-8;base64,"), value)
        hrefs = [node.attrs.get("href") for node in document.nodes("a")]
        self.assertIn("https://example.com/evidence", hrefs)
        self.assertIn("mailto:owner@example.com", hrefs)
        self.assertIn("./evidence.md", hrefs)
        self.assertTrue(any("<script>globalThis.injectedBySource = 1</script>" in node.text()
                            for node in document.nodes("p")))
        self.assertEqual(document.source(), source.encode("utf-8"))

    def test_offline_assets_are_embedded_and_profiles_do_not_change_evidence(self):
        source = "# Findings\n\nEvidence: unchanged, NOT VERIFIED.\n"

        for profile in ("report", "naming", "review"):
            with self.subTest(profile=profile):
                document = Document(self.render(source, profile=profile))

                self.assertTrue(any(node.text().strip() for node in document.nodes("style")))
                self.assertTrue(any(node.text().strip() for node in document.nodes("script")
                                    if node.attrs.get("type") != "text/plain"))
                self.assertFalse(any("src" in node.attrs for node in document.nodes("script")))
                self.assertFalse(any(node.attrs.get("rel") == "stylesheet"
                                     for node in document.nodes("link")))
                self.assertEqual(document.source(), source.encode("utf-8"))

    def test_localized_naming_scorecard_exposes_weights_and_keeps_original_qualifiers(self):
        source = """# Scelta del nome

## Valutazione

| Criterio | Peso | Alfa | Beta |
| --- | --- | --- | --- |
| Memorabilità | 60% | 4 (non verificato) | 3 |
| Disponibilità | 40% | non valutato | 2 (non esaminato) |
| Totale | 100% | 4.0 (non verificato) | 2.6 (non esaminato) |

Raccomandazione originale: Alfa, con verifiche ancora aperte.
"""

        document = Document(self.render(source, profile="naming"))

        weights = [node for node in document.nodes("input")
                   if node.attrs.get("type") == "number"]
        self.assertEqual([node.attrs.get("value") for node in weights], ["60", "40"])
        self.assertTrue(all(node.attrs.get("aria-label") for node in weights))
        cells = [node.text() for node in document.nodes("td")]
        for value in ("4 (non verificato)", "non valutato", "2 (non esaminato)",
                      "4.0 (non verificato)", "2.6 (non esaminato)"):
            with self.subTest(value=value):
                self.assertIn(value, cells)
        self.assertTrue(any("Raccomandazione originale: Alfa" in node.text()
                            for node in document.nodes("p")))
        self.assertEqual(document.source(), source.encode("utf-8"))

    def test_documented_polish_overall_label_enables_scorecard_weight_exploration(self):
        source = """# Wybór nazwy

| Kryterium | Waga | Alfa |
| --- | --- | --- |
| Zapamiętywalność | 100% | 5 |
| Ocena łączna | 100% | 5.0 |
"""

        document = Document(self.render(source, profile="naming"))

        weights = [node for node in document.nodes("input")
                   if node.attrs.get("type") == "number"]
        self.assertEqual([node.attrs.get("value") for node in weights], ["100"])
        self.assertIn("Ocena łączna", [node.text() for node in document.nodes("td")])
        self.assertEqual(document.source(), source.encode("utf-8"))

    def test_out_of_range_naming_scores_remain_an_ordinary_visible_table(self):
        source = """# Naming

| Criterion | Weight | Alpha |
| --- | --- | --- |
| Memorability | 100% | 7 |
| Overall | 100% | 7.0 |
"""

        document = Document(self.render(source, profile="naming"))

        self.assertFalse(any(node.attrs.get("type") == "number"
                             for node in document.nodes("input")))
        self.assertIn("7", [node.text() for node in document.nodes("td")])
        self.assertIn("7.0", [node.text() for node in document.nodes("td")])
        self.assertEqual(document.source(), source.encode("utf-8"))

    def test_invalid_profile_is_an_explicit_error(self):
        with self.assertRaises(ValueError):
            self.render("# Source", profile="invented")


class ReportCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="daodan-report-cli-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "owned"
        self.root.mkdir()
        self.source = self.root / "report.md"
        self.source_bytes = "# Qualità 🧭\r\n\r\nSource stays canonical.\r\n".encode("utf-8")
        self.source.write_bytes(self.source_bytes)
        self.output = self.root / "report.html"

    def cli(self, *extra, input_path=None, output_path=None, root=None, profile="report"):
        return subprocess.run([
            sys.executable, "-I", str(SCRIPT),
            "--input", str(input_path or self.source),
            "--output", str(output_path or self.output),
            "--profile", profile, "--root", str(root or self.root), *extra,
        ], cwd=self.root, capture_output=True, text=True, encoding="utf-8", timeout=20)

    def assert_untouched_failure(self, result, existing=b"existing human view"):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.source.read_bytes(), self.source_bytes)
        self.assertEqual(self.output.read_bytes(), existing)
        self.assertTrue(result.stderr.strip(), "Failure must have a diagnostic")

    def test_success_retains_source_bytes_and_outputs_a_complete_standalone_page(self):
        result = self.cli()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.source.read_bytes(), self.source_bytes)
        page = self.output.read_text(encoding="utf-8")
        self.assertTrue(page.lstrip().lower().startswith("<!doctype html>"))
        self.assertEqual(Document(page).source(), self.source_bytes)
        self.assertEqual({path.name for path in self.root.iterdir()}, {"report.md", "report.html"})

    def test_existing_view_requires_explicit_force_and_force_never_changes_source(self):
        self.output.write_bytes(b"existing human view")

        rejected = self.cli()

        self.assert_untouched_failure(rejected)

        accepted = self.cli("--force")

        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertEqual(self.source.read_bytes(), self.source_bytes)
        self.assertEqual(Document(self.output.read_text(encoding="utf-8")).source(), self.source_bytes)

    def test_missing_input_and_invalid_profile_leave_existing_artifacts_untouched(self):
        self.output.write_bytes(b"existing human view")

        for kwargs in ({"input_path": self.root / "missing.md"}, {"profile": "invented"}):
            with self.subTest(arguments=kwargs):
                result = self.cli("--force", **kwargs)

                self.assert_untouched_failure(result)

    def test_traversal_and_outside_outputs_are_rejected_even_with_force(self):
        outside = self.base / "outside.html"
        outside.write_bytes(b"outside must survive")
        candidates = (outside, self.root / ".." / "outside.html",
                      self.root / "nested" / ".." / "report.html")

        for output in candidates:
            with self.subTest(output=output):
                result = self.cli("--force", output_path=output)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(outside.read_bytes(), b"outside must survive")
                self.assertEqual(self.source.read_bytes(), self.source_bytes)
                self.assertFalse(self.output.exists())

    def test_force_cannot_overwrite_input_through_direct_or_hardlink_alias(self):
        alias = self.root / "source-alias.html"
        os.link(self.source, alias)

        for output in (self.source, alias):
            with self.subTest(output=output):
                result = self.cli("--force", output_path=output)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(self.source.read_bytes(), self.source_bytes)
                self.assertEqual(alias.read_bytes(), self.source_bytes)

    def test_links_in_root_parent_and_output_never_redirect_writes(self):
        target = self.base / "target"
        target.mkdir()
        sentinel = target / "report.html"
        sentinel.write_bytes(b"linked target must survive")
        root_link = self.base / "root-alias"
        root_link.symlink_to(self.root, target_is_directory=True)
        self.addCleanup(root_link.unlink)
        child_link = self.root / "child-alias"
        child_link.symlink_to(target, target_is_directory=True)
        self.addCleanup(child_link.unlink)
        output_link = self.root / "output-alias.html"
        output_link.symlink_to(sentinel)
        self.addCleanup(output_link.unlink)
        cases = (
            {"root": root_link, "output_path": root_link / "report.html"},
            {"output_path": child_link / "report.html"},
            {"output_path": output_link},
        )

        for kwargs in cases:
            with self.subTest(arguments=kwargs):
                result = self.cli("--force", **kwargs)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(sentinel.read_bytes(), b"linked target must survive")
                self.assertEqual(self.source.read_bytes(), self.source_bytes)
                self.assertFalse(self.output.exists())

    @unittest.skipUnless(os.name == "nt", "Windows junctions have no equivalent on this platform")
    def test_windows_junctions_are_rejected_for_root_and_child_paths(self):
        target = self.base / "junction-target"
        target.mkdir()
        sentinel = target / "report.html"
        sentinel.write_bytes(b"junction target must survive")
        links = (self.base / "junction-root", self.root / "junction-child")
        for link in links:
            self.assertTrue(link.absolute().is_relative_to(self.base.absolute()))
            environment = {**os.environ, "DAODAN_TEST_LINK": str(link),
                           "DAODAN_TEST_TARGET": str(target)}
            created = subprocess.run([
                "powershell", "-NoProfile", "-Command",
                "New-Item -ItemType Junction -Path $env:DAODAN_TEST_LINK "
                "-Target $env:DAODAN_TEST_TARGET | Out-Null",
            ], env=environment, capture_output=True, text=True, timeout=20)
            self.assertEqual(created.returncode, 0, created.stderr)
            self.addCleanup(link.rmdir)
            self.assertEqual(link.resolve(), target.resolve())

        for kwargs in ({"root": links[0], "output_path": links[0] / "report.html"},
                       {"output_path": links[1] / "report.html"}):
            with self.subTest(arguments=kwargs):
                result = self.cli("--force", **kwargs)

                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(sentinel.read_bytes(), b"junction target must survive")
                self.assertEqual(self.source.read_bytes(), self.source_bytes)
                self.assertFalse(self.output.exists())

    def test_linked_or_invalid_utf8_input_is_rejected_without_changing_existing_view(self):
        self.output.write_bytes(b"existing human view")
        linked_source = self.root / "source-alias.md"
        linked_source.symlink_to(self.source)
        self.addCleanup(linked_source.unlink)
        invalid = self.root / "invalid.md"
        invalid.write_bytes(b"invalid UTF-8: \xff\xfe")

        for source in (linked_source, invalid):
            with self.subTest(source=source):
                result = self.cli("--force", input_path=source)

                self.assert_untouched_failure(result)
        self.assertEqual(invalid.read_bytes(), b"invalid UTF-8: \xff\xfe")

    def test_relative_evidence_targets_survive_an_output_in_another_owned_folder(self):
        evidence = self.root / "evidence"
        evidence.mkdir()
        (evidence / "proof.md").write_text("canonical evidence", encoding="utf-8")
        (evidence / "chart.png").write_bytes(b"fixture image is not fetched")
        source = self.root / "reports" / "analysis.md"
        source.parent.mkdir()
        source.write_text("# Analysis\n\n[Proof](../evidence/proof.md#claim)\n\n"
                          "![Chart](../evidence/chart.png)\n", encoding="utf-8")
        output = self.root / "views" / "analysis.html"
        output.parent.mkdir()

        result = self.cli(input_path=source, output_path=output)

        self.assertEqual(result.returncode, 0, result.stderr)
        document = Document(output.read_text(encoding="utf-8"))
        proof = next(node.attrs["href"] for node in document.nodes("a") if node.text() == "Proof")
        chart = next(node.attrs["src"] for node in document.nodes("img")
                     if node.attrs.get("alt") == "Chart")
        self.assertEqual((output.parent / proof.split("#", 1)[0]).resolve(), evidence / "proof.md")
        self.assertTrue(proof.endswith("#claim"), proof)
        self.assertEqual((output.parent / chart).resolve(), evidence / "chart.png")

    def test_atomic_publication_failure_preserves_existing_view_and_cleans_temporary_file(self):
        self.output.write_bytes(b"existing human view")
        before = {path.name for path in self.root.iterdir()}
        code = ("import runpy, sys; from unittest.mock import patch; "
                "sys.argv = sys.argv[1:]; "
                "publication = patch('os.replace', side_effect=OSError('publication blocked')); "
                "publication.start(); runpy.run_path(sys.argv[0], run_name='__main__')")
        command = [sys.executable, "-I", "-c", code, str(SCRIPT), "--input", str(self.source),
                   "--output", str(self.output), "--root", str(self.root), "--force"]

        result = subprocess.run(command, cwd=self.root, capture_output=True,
                                text=True, encoding="utf-8", timeout=20)

        self.assert_untouched_failure(result)
        self.assertEqual({path.name for path in self.root.iterdir()}, before)


if __name__ == "__main__":
    unittest.main()
