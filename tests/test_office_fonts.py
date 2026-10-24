"""Font fetching, verification, installation and embedding helpers of office:design."""

import importlib.util
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "plugins").is_dir() and (parent / "scripts").is_dir())
SCRIPTS = ROOT / "plugins/office/skills/design/scripts"
OFFL = "This Font Software is licensed under the SIL Open Font License, Version 1.1."


def _load(name):
    spec = importlib.util.spec_from_file_location("office_test_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fetch = _load("font_fetch")
embed = _load("font_embed")


def build_font(family, weight=400, italic=False, fs_type=0, license_text=OFFL,
               typographic_family=None, full_name=None):
    """A minimal sfnt with the name and OS/2 fields the helper reads."""
    names = {1: family, 2: "Italic" if italic else "Regular", 4: full_name or family, 13: license_text}
    if typographic_family:
        names[16] = typographic_family
    strings, records, offset = b"", b"", 0
    for name_id, text in sorted(names.items()):
        raw = text.encode("utf-16-be")
        records += struct.pack(">6H", 3, 1, 0x409, name_id, len(raw), offset)
        strings += raw
        offset += len(raw)
    name_table = struct.pack(">HHH", 0, len(names), 6 + len(records)) + records + strings
    os2 = bytearray(78)
    struct.pack_into(">H", os2, 4, weight)
    struct.pack_into(">H", os2, 8, fs_type)
    struct.pack_into(">H", os2, 62, 1 if italic else 0x40)
    tables = [(b"OS/2", bytes(os2)), (b"name", name_table)]
    start = 12 + 16 * len(tables)
    directory, body = b"", b""
    for tag, data in tables:
        directory += struct.pack(">4sIII", tag, 0, start + len(body), len(data))
        body += data + b"\0" * (-len(data) % 4)
    return struct.pack(">IHHHH", 0x00010000, len(tables), 32, 1, 0) + directory + body


CSS = """
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 400;
  src: url(https://fonts.gstatic.com/s/inter/a.ttf) format('truetype');
}
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-weight: 700;
  src: url(https://fonts.gstatic.com/s/inter/b.ttf) format('truetype');
}
"""


class SpecAndApiTests(unittest.TestCase):
    def test_spec_lists_explicit_faces(self):
        self.assertEqual(fetch.parse_spec("Inter"), ("Inter", [("normal", 400)]))
        self.assertEqual(fetch.parse_spec("Inter:wght@400;700")[1], [("normal", 400), ("normal", 700)])
        self.assertEqual(fetch.parse_spec("Source Sans 3:ital,wght@0,400;1,400")[1],
                         [("normal", 400), ("italic", 400)])

    def test_spec_rejects_ranges_unknown_axes_and_odd_names(self):
        for spec in ("Inter:wght@100..900", "Inter:opsz,wght@14,400", "Inter;rm -rf", "Inter:wght@400;400"):
            with self.subTest(spec=spec), self.assertRaises(fetch.FontError):
                fetch.parse_spec(spec)

    def test_css_maps_faces_and_refuses_subsets_and_foreign_hosts(self):
        faces = fetch.parse_css(CSS)
        self.assertEqual(faces[("normal", 700)], "https://fonts.gstatic.com/s/inter/b.ttf")
        with self.assertRaises(fetch.FontError):
            fetch.parse_css(CSS.replace("font-weight: 700;", "font-weight: 700;\n  unicode-range: U+0000-00FF;"))
        with self.assertRaises(fetch.FontError):
            fetch.parse_css(CSS.replace("fonts.gstatic.com", "example.com"))

    def test_request_url_uses_css2_family_syntax(self):
        self.assertEqual(fetch.css_url("Source Sans 3:ital,wght@0,400;1,400"),
                         "https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,400;1,400")


class VerificationTests(unittest.TestCase):
    def test_open_licensed_matching_face_is_accepted(self):
        meta = fetch.verify(build_font("Inter", 700), "Inter", "normal", 700)
        self.assertEqual((meta["license"], meta["embedding"]), ("OFL-1.1", "installable"))

    def test_legacy_family_name_carrying_the_weight_matches(self):
        data = build_font("Barlow Medium", 500)
        self.assertEqual(fetch.verify(data, "Barlow", "normal", 500)["license"], "OFL-1.1")

    def test_mismatch_unknown_license_and_restricted_embedding_are_rejected(self):
        cases = (
            (build_font("Lato", 400), "Inter", "normal", 400),
            (build_font("Inter", 400), "Inter", "normal", 700),
            (build_font("Inter", 400, italic=True), "Inter", "normal", 400),
            (build_font("Inter", license_text="All rights reserved."), "Inter", "normal", 400),
            (build_font("Inter", fs_type=0x0002), "Inter", "normal", 400),
            (b"not a font at all", "Inter", "normal", 400),
        )
        for data, family, style, weight in cases:
            with self.subTest(family=family, weight=weight), self.assertRaises(fetch.FontError):
                fetch.verify(data, family, style, weight)

    def test_embedding_permissions_follow_fs_type(self):
        self.assertEqual(fetch.embedding_of(0), "installable")
        self.assertEqual(fetch.embedding_of(0x0008), "editable")
        self.assertEqual(fetch.embedding_of(0x0004), "preview-print")
        self.assertEqual(fetch.embedding_of(0x0002), "restricted")


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        files = {"https://fonts.gstatic.com/s/inter/a.ttf": build_font("Inter", 400),
                 "https://fonts.gstatic.com/s/inter/b.ttf": build_font("Inter", 700)}

        def fake_get(url, limit):
            return CSS.encode() if url.startswith(fetch.CSS_ENDPOINT) else files[url]

        patcher = mock.patch.object(fetch, "_get", side_effect=fake_get)
        self.get = patcher.start()
        self.addCleanup(patcher.stop)

    def test_fetch_writes_verified_files_once(self):
        report = fetch.run("fetch", ["Inter:wght@400;700"], self.root / "out")
        self.assertTrue(report["ok"])
        self.assertTrue((self.root / "out/Inter-700.ttf").is_file())
        self.assertEqual({face["license"] for face in report["faces"]}, {"OFL-1.1"})
        again = fetch.run("fetch", ["Inter:wght@400"], self.root / "out")
        self.assertEqual(again["faces"][0]["file"], "exists")

    def test_missing_face_fails_the_report(self):
        report = fetch.run("fetch", ["Inter:wght@400;900"], self.root / "out")
        self.assertFalse(report["ok"])
        self.assertEqual(report["faces"][1]["status"], "failed")

    def test_install_registers_missing_faces_and_skips_installed_ones(self):
        system = self.root / "system"
        system.mkdir()
        (system / "inter.ttf").write_bytes(build_font("Inter", 400))
        user = self.root / "user"
        with mock.patch.object(fetch, "font_dirs", return_value=[system, user]), \
                mock.patch.object(fetch, "user_font_dir", return_value=user), \
                mock.patch.object(fetch, "register") as register:
            report = fetch.run("install", ["Inter:wght@400;700"])
            status = fetch.run("status", ["Inter:wght@400;700"])
        self.assertTrue(report["ok"])
        self.assertEqual([face["status"] for face in report["faces"]], ["already-installed", "installed"])
        register.assert_called_once()
        self.assertTrue((user / "Inter-700.ttf").is_file())
        self.assertEqual([face["status"] for face in status["faces"]], ["already-installed"] * 2)

    def test_cli_reports_invalid_specs_as_usage_errors(self):
        with mock.patch("sys.stdout"):
            self.assertEqual(fetch.main(["status", "Inter:wght@1..9"]), 2)


def _zip(path, parts):
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in parts.items():
            archive.writestr(name, data)


A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
P = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
RELS = 'xmlns="http://schemas.openxmlformats.org/package/2006/relationships"'


class EmbedTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_pptx_inspection_reports_embedded_subset_and_missing_fonts(self):
        deck = self.root / "deck.pptx"
        _zip(deck, {
            "ppt/slides/slide1.xml": f'<p:sld {P} {A}><a:latin typeface="Inter"/><a:latin typeface="Lato"/>'
                                     '<a:latin typeface="+mj-lt"/></p:sld>',
            "ppt/presentation.xml": f'<p:presentation {P} {R}><p:embeddedFontLst><p:embeddedFont>'
                                    '<p:font typeface="Inter"/><p:regular r:id="rId9"/></p:embeddedFont>'
                                    '</p:embeddedFontLst></p:presentation>',
            "ppt/_rels/presentation.xml.rels": f'<Relationships {RELS}><Relationship Id="rId9" '
                                               'Target="fonts/font1.fntdata"/></Relationships>',
            "ppt/fonts/font1.fntdata": struct.pack("<IIII", 16, 0, 0x20002, 0x5),
        })
        report = embed.inspect(deck)
        self.assertEqual(report["used"], ["Inter", "Lato"])
        self.assertEqual(report["embedded"]["Inter"], {"styles": ["regular"], "subset": True})
        self.assertEqual(report["not_embedded"], ["Lato"])

    def test_docx_inspection_reports_complete_embedding(self):
        document = self.root / "report.docx"
        _zip(document, {
            "word/fontTable.xml": f'<w:fonts {W} {R}><w:font w:name="Inter"><w:embedRegular r:id="rId1"/>'
                                  '<w:embedBold r:id="rId2"/></w:font><w:font w:name="Cambria"/></w:fonts>',
            "word/_rels/fontTable.xml.rels": f'<Relationships {RELS}><Relationship Id="rId1" Target="fonts/font1.odttf"/>'
                                             '<Relationship Id="rId2" Target="fonts/font2.odttf"/></Relationships>',
            "word/fonts/font1.odttf": b"x", "word/fonts/font2.odttf": b"x",
            "word/settings.xml": f'<w:settings {W}><w:embedTrueTypeFonts/></w:settings>',
        })
        report = embed.inspect(document)
        self.assertEqual(report["embedded"]["Inter"], {"styles": ["regular", "bold"], "subset": False})
        self.assertEqual(report["not_embedded"], ["Cambria"])

    def test_embed_never_overwrites_or_changes_format(self):
        source = self.root / "deck.pptx"
        source.write_bytes(b"x")
        existing = self.root / "done.pptx"
        existing.write_bytes(b"x")
        for target in (source, existing, self.root / "deck.docx"):
            with self.subTest(target=target.name), self.assertRaises(embed.EmbedError):
                embed.embed(source, target)

    def test_embed_reports_hosts_without_an_office_engine(self):
        source = self.root / "deck.pptx"
        source.write_bytes(b"x")
        with mock.patch.object(embed.sys, "platform", "linux"), self.assertRaises(embed.EmbedError) as caught:
            embed.embed(source, self.root / "out.pptx")
        self.assertIn("no supported embedding engine", str(caught.exception))

    def test_paths_travel_in_the_environment_not_the_script(self):
        source = self.root / "deck.pptx"
        _zip(source, {"ppt/presentation.xml": f"<p:presentation {P} {R}/>"})
        target = self.root / "out.pptx"

        def fake_run(command, env, **kwargs):
            target.write_bytes(source.read_bytes())
            return mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(embed.sys, "platform", "win32"), \
                mock.patch.object(embed.subprocess, "run", side_effect=fake_run) as run:
            report = embed.embed(source, target)
        command, environment = run.call_args.args[0], run.call_args.kwargs["env"]
        self.assertNotIn(str(source.resolve()), " ".join(command))
        self.assertEqual(environment["FONT_EMBED_OUTPUT"], str(target.resolve()))
        self.assertEqual((environment["FONT_EMBED_APP"], environment["FONT_EMBED_FORMAT"]), ("PowerPoint", "24"))
        self.assertEqual(report["engine"], "Microsoft PowerPoint (COM)")


HOSTS = ("claude", "codex", "copilot", "opencode", "pi")
SKILLS = "plugins/office/skills"


def _text(path):
    return " ".join(path.read_text(encoding="utf-8").split())


class FontContractTests(unittest.TestCase):
    def test_catalog_lists_twelve_open_pairings_with_fetchable_specs(self):
        catalog = (SCRIPTS.parent / "references/font-pairings.md").read_text(encoding="utf-8")
        rows = [line for line in catalog.splitlines() if line.startswith("| ") and line[2].isdigit()]
        self.assertEqual(len(rows), 12)
        for row in rows:
            specs = [cell.strip("`") for cell in row.split("|")[6].split("` `")]
            for spec in (cell.strip(" `") for cell in specs):
                with self.subTest(spec=spec):
                    fetch.parse_spec(spec)
        self.assertIn("Every face is OFL-1.1", catalog)

    def test_font_helpers_and_catalog_ship_and_are_cited_on_every_host(self):
        for host in HOSTS:
            root = ROOT / "exports" / host / SKILLS
            with self.subTest(host=host):
                for relative in ("design/scripts/font_fetch.py",
                                 "design/scripts/font_embed.py"):
                    self.assertEqual((root / relative).read_bytes(), (ROOT / SKILLS / relative).read_bytes())
                catalog = "design/references/font-pairings.md"
                self.assertIn(_text(ROOT / SKILLS / catalog), _text(root / catalog))
                typography = _text(root / "design/SKILL.md")
                self.assertIn("design/scripts/font_fetch.py\" install", typography)
                self.assertIn("design/scripts/font_embed.py\" embed", typography)
                self.assertIn("claim embedding without the inspection result", typography.replace("do not ", ""))
                directions = _text(root / "design/references/directions.md")
                self.assertRegex(directions, r"\| \*\*A Executive Boardroom\*\* \|.*\| 1: Inter / Inter \|")
                for method in ("presentation-design/SKILL.md", "docx/SKILL.md"):
                    self.assertIn("font_embed.py", _text(root / method))
                    self.assertIn("font pairing", _text(root / method))

if __name__ == "__main__":
    unittest.main()
