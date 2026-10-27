"""Vendored open-slide conversion gear: hash guard, bridge transport, contract records.

The real browser conversion runs only where Node, the Playwright module and a
Chromium-family browser are actually available; elsewhere it skips with the
reason instead of passing silently.
"""

import importlib.util
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest import mock


ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "plugins/office/skills").is_dir())
SCRIPTS = ROOT / "plugins/office/skills/pptx/scripts"
LIB = ROOT / "plugins/office/skills/pptx/lib/open-slide-pptx"
REFERENCE = ROOT / "plugins/office/skills/pptx/references/html-to-pptx.md"
SKILL = ROOT / "plugins/office/skills/pptx/SKILL.md"
DESIGNER = ROOT / "plugins/office/roles/presentation-designer.md"
FIXTURE = ROOT / "tests/fixtures/office/pptx-convert/design.html"

VENDORED = {
    "src/lib/sdk.ts",
    "src/lib/pptx/color.ts",
    "src/lib/pptx/css.ts",
    "src/lib/pptx/fonts.ts",
    "src/lib/pptx/images.ts",
    "src/lib/pptx/measure.ts",
    "src/lib/pptx/ooxml.ts",
    "src/lib/pptx/raster.ts",
    "src/lib/pptx/scene.ts",
    "src/lib/pptx/text-lines.ts",
    "src/lib/pptx/units.ts",
}
PIN = json.loads((LIB / "build.deps.json").read_text(encoding="utf-8"))["upstream"]
UPSTREAM_PIN = PIN["git_ref"]
BUNDLE_NAME = "bundle/open-slide-pptx.js"


def load(name):
    spec = importlib.util.spec_from_file_location("office_test_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bridge = load("pptx_convert_bridge")


def manifest():
    return json.loads((LIB / "manifest.json").read_text(encoding="utf-8"))


class VendorIntegrityTests(unittest.TestCase):
    def test_vendored_subset_is_exactly_the_pinned_eleven_files(self):
        actual = {str(path.relative_to(LIB)).replace("\\", "/")
                  for path in (LIB / "src").rglob("*.ts")}
        self.assertEqual(VENDORED, actual)

    def test_manifest_hashes_match_every_vendored_and_generated_file(self):
        recorded = manifest()["files"]
        self.assertIn(BUNDLE_NAME, recorded)
        for name, digest in recorded.items():
            target = LIB / name
            self.assertTrue(target.is_file(), f"manifest records a missing file: {name}")
            self.assertEqual(bridge.sha256(target), digest, f"hash drift in {name}")

    def test_manifest_records_the_pin_licenses_and_exclusions(self):
        upstream = manifest()["upstream"]
        self.assertEqual("@open-slide/core", upstream["package"])
        self.assertEqual(PIN, upstream, "manifest.json must carry the build.deps.json pin")
        self.assertEqual(UPSTREAM_PIN, upstream["git_ref"])
        self.assertEqual("MIT", upstream["license"])
        self.assertEqual(sorted(VENDORED), sorted(
            "src/lib/" + path.split("app/lib/", 1)[1] for path in upstream["copied_paths"]))
        self.assertTrue(any("render.ts" in item for item in upstream["excluded"]))
        third = {item["package"]: item for item in manifest()["third_party"]}
        self.assertEqual("0.8.3", third["fflate"]["version"])
        self.assertEqual("1.11.13", third["html-to-image"]["version"])
        for item in manifest()["third_party"]:
            notice = LIB / item["notice"]
            self.assertTrue(notice.is_file(), f"missing notice: {item['notice']}")
            self.assertIn("MIT", notice.read_text(encoding="utf-8"))

    def test_bundle_carries_the_attribution_and_the_office_entry(self):
        text = (LIB / "bundle" / "open-slide-pptx.js").read_text(encoding="utf-8")
        head = text[:1200]
        self.assertIn("open-slide", head)
        self.assertIn("MIT", head)
        self.assertIn("fflate", head)
        self.assertIn("html-to-image", head)
        self.assertIn("officeHtmlToPptx", text)
        self.assertIn("data-office-slide", text)

    def test_plugin_directory_ships_no_dependency_tree(self):
        for forbidden in ("node_modules", "dist", "package-lock.json"):
            self.assertFalse((LIB / forbidden).exists(), f"{forbidden} must stay out of the plugin")

    def test_upstream_note_names_the_pin_and_the_refresh_protocol(self):
        text = (LIB / "UPSTREAM.md").read_text(encoding="utf-8")
        self.assertIn(UPSTREAM_PIN, text)
        self.assertIn("Yiwei Ho", text)
        for name in sorted(VENDORED):
            self.assertIn(name.split("/", 2)[2], text)
        self.assertIn("rebuild.mjs", text)
        self.assertIn("Refresh protocol", text)

    def test_an_edited_vendored_file_fails_the_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "open-slide-pptx"
            shutil.copytree(LIB, copy)
            target = copy / "src/lib/pptx/units.ts"
            target.write_text(target.read_text(encoding="utf-8") + "\n// local edit\n", encoding="utf-8")
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.verify_manifest(copy)
            self.assertIn("units.ts", str(caught.exception))
            self.assertIn("read-only", str(caught.exception))

    def test_a_stale_bundle_fails_the_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "open-slide-pptx"
            shutil.copytree(LIB, copy)
            bundle = copy / "bundle/open-slide-pptx.js"
            bundle.write_text(bundle.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaises(bridge.BridgeError):
                bridge.verify_manifest(copy)

    def test_a_checkout_that_converted_line_endings_is_diagnosed_as_such(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "open-slide-pptx"
            shutil.copytree(LIB, copy)
            target = copy / "src/lib/pptx/units.ts"
            target.write_bytes(target.read_bytes().replace(b"\n", b"\r\n"))
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.verify_manifest(copy)
            self.assertIn("line endings", str(caught.exception))
            self.assertNotIn("read-only", str(caught.exception))

    def test_git_never_converts_the_line_endings_of_the_guarded_files(self):
        guarded = [str((LIB / name).relative_to(ROOT)).replace("\\", "/") for name in manifest()["files"]]
        completed = subprocess.run(["git", "check-attr", "text", "--", *guarded], cwd=ROOT,
                                   capture_output=True, text=True, check=True)
        lines = completed.stdout.strip().splitlines()
        self.assertEqual(len(guarded), len(lines))
        for line in lines:
            self.assertTrue(line.endswith(": text: unset"), line)

    def test_the_rebuild_takes_the_pin_from_build_inputs(self):
        source = (LIB / "rebuild.mjs").read_text(encoding="utf-8")
        self.assertNotIn(UPSTREAM_PIN, source, "the pin is data in build.deps.json, not code")
        self.assertIn("build.deps.json", source)


class NodeVersionTests(unittest.TestCase):
    def test_supported_and_unsupported_releases(self):
        for version, expected in (((20, 19), True), ((20, 18), False), ((21, 7), False),
                                  ((22, 12), True), ((22, 11), False), ((24, 14), True),
                                  ((18, 20), False)):
            self.assertEqual(expected, bridge.node_supported(version), version)

    def test_version_parsing(self):
        self.assertEqual((24, 14), bridge.parse_node_version("v24.14.1"))
        self.assertIsNone(bridge.parse_node_version("unknown"))


class DiscoveryTests(unittest.TestCase):
    def executable(self, directory):
        path = Path(directory) / "node.exe"
        path.write_text("stub", encoding="utf-8")
        return path

    def probe_node(self, version="v24.14.1"):
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=version, stderr="")

    def test_missing_node_reports_the_recovery_variable(self):
        with mock.patch.object(shutil, "which", return_value=None):
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.discover(environ={"PATH": ""})
        message = str(caught.exception)
        self.assertIn("OFFICE_PPTX_NODE", message)
        self.assertIn("html-to-pptx.md", message)

    def test_unsupported_node_is_rejected_before_any_conversion(self):
        with tempfile.TemporaryDirectory() as temporary:
            node = self.executable(temporary)
            with mock.patch.object(subprocess, "run", return_value=self.probe_node("v18.20.4")):
                with self.assertRaises(bridge.BridgeError) as caught:
                    bridge.discover(environ={"OFFICE_PPTX_NODE": str(node), "PATH": ""})
        self.assertIn("unsupported", str(caught.exception))

    def test_discovery_probes_with_an_argument_list_and_no_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            node = self.executable(temporary)
            with mock.patch.object(subprocess, "run", return_value=self.probe_node()) as runner:
                runtime = bridge.discover(environ={"OFFICE_PPTX_NODE": str(node), "PATH": ""})
        call = runner.call_args
        self.assertEqual([str(node), "--version"], call.args[0])
        self.assertNotIn("shell", call.kwargs)
        self.assertTrue(call.kwargs["capture_output"])
        self.assertEqual("24.14", runtime["node_version"])
        self.assertEqual(manifest()["bundle"]["sha256"], runtime["bundle_sha256"])
        self.assertEqual(PIN["version"], runtime["engine"]["version"])

    def test_a_missing_bundle_points_at_the_rebuild(self):
        with tempfile.TemporaryDirectory() as temporary:
            node = self.executable(temporary)
            with mock.patch.object(subprocess, "run", return_value=self.probe_node()):
                with mock.patch.object(bridge, "BUNDLE", LIB / "bundle" / "absent.js"):
                    with self.assertRaises(bridge.BridgeError) as caught:
                        bridge.discover(environ={"OFFICE_PPTX_NODE": str(node), "PATH": ""})
        self.assertIn("rebuild.mjs", str(caught.exception))

    def test_a_missing_driver_is_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            node = self.executable(temporary)
            with mock.patch.object(subprocess, "run", return_value=self.probe_node()):
                with mock.patch.object(bridge, "DRIVER", LIB / "absent.mjs"):
                    with self.assertRaises(bridge.BridgeError) as caught:
                        bridge.discover(environ={"OFFICE_PPTX_NODE": str(node), "PATH": ""})
        self.assertIn("driver is missing", str(caught.exception))


class ConversionTransportTests(unittest.TestCase):
    RUNTIME = {"node": "node", "node_version": "24.14", "lib": str(LIB),
               "bundle": str(LIB / "bundle" / "open-slide-pptx.js"),
               "bundle_sha256": "0" * 64,
               "engine": {"package": "@open-slide/core", "version": PIN["version"],
                          "git_ref": UPSTREAM_PIN, "license": "MIT"}}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.html = self.directory / "design.html"
        self.html.write_text("<!DOCTYPE html><title>t</title>", encoding="utf-8")
        self.addCleanup(self.temporary.cleanup)

    def run_bridge(self, **kwargs):
        with mock.patch.object(subprocess, "run") as runner:
            runner.side_effect = AssertionError("the bridge must validate the job before running anything")
            job = dict(runtime=self.RUNTIME, html=kwargs.pop("html", self.html),
                       output=kwargs.pop("output", self.directory / "deck.pptx"), **kwargs)
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.convert_html(**job)
        return str(caught.exception)

    def test_a_non_html_source_is_refused(self):
        text = self.html.with_suffix(".txt")
        text.write_text("not html", encoding="utf-8")
        self.assertIn("must be an .html file", self.run_bridge(html=text))

    def test_a_non_pptx_output_is_refused(self):
        message = self.run_bridge(output=self.directory / "deck.pdf")
        self.assertIn(".pptx", message)

    def test_a_missing_source_is_refused(self):
        message = self.run_bridge(html=self.directory / "absent.html")
        self.assertIn("does not exist", message)

    def test_a_missing_output_directory_is_refused(self):
        message = self.run_bridge(output=self.directory / "absent" / "deck.pptx")
        self.assertIn("output directory does not exist", message)

    def test_a_missing_asset_root_is_refused(self):
        message = self.run_bridge(assets_root=self.directory / "absent-assets")
        self.assertIn("asset root does not exist", message)

    def test_an_out_of_range_timeout_is_refused(self):
        self.assertIn("timeout_ms", self.run_bridge(timeout_ms=10))

    def test_an_existing_candidate_is_never_overwritten(self):
        output = self.directory / "deck.pptx"
        output.write_bytes(b"earlier candidate")
        self.assertIn("Refusing to overwrite", self.run_bridge(output=output))
        self.assertEqual(b"earlier candidate", output.read_bytes())

    def test_an_existing_evidence_record_is_never_overwritten(self):
        record = self.directory / "deck.conversion.json"
        record.write_text("{}", encoding="utf-8")
        self.assertIn("Refusing to overwrite", self.run_bridge(evidence=record))

    def test_the_html_must_sit_inside_the_asset_root(self):
        assets = self.directory / "assets"
        assets.mkdir()
        self.assertIn("inside the asset root", self.run_bridge(assets_root=assets))

    def test_the_probe_stops_without_a_usable_browser(self):
        payload = {"status": "probe", "bundle": {"present": True},
                   "playwright": {"available": True, "version": "1.62.1"},
                   "browser": {"available": False, "recovery": "Set OFFICE_PPTX_BROWSER to an existing browser"}}
        with mock.patch.object(subprocess, "run",
                               return_value=subprocess.CompletedProcess(args=[], returncode=3,
                                                                        stdout=json.dumps(payload), stderr="")):
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.probe(self.RUNTIME)
        self.assertIn("OFFICE_PPTX_BROWSER", str(caught.exception))

    def test_the_driver_runs_from_an_argument_list_with_a_temporary_job_file(self):
        output = self.directory / "deck.pptx"
        record = self.directory / "deck.conversion.json"
        payload = {"status": "error", "code": 3, "message": "The playwright Node module is unavailable."}
        with mock.patch.object(subprocess, "run",
                               return_value=subprocess.CompletedProcess(args=[], returncode=3,
                                                                        stdout=json.dumps(payload), stderr="")) as runner:
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.convert_html(self.RUNTIME, html=self.html, output=output, evidence=record)
        call = runner.call_args
        argv = call.args[0]
        self.assertNotIn("shell", call.kwargs)
        self.assertEqual([self.RUNTIME["node"], str(bridge.DRIVER), "--job"], argv[:3])
        self.assertTrue(Path(argv[3]).is_absolute())
        self.assertFalse(Path(argv[3]).exists(), "the job file must not survive the run")
        self.assertIn("playwright", str(caught.exception).lower())

    def test_a_driver_timeout_is_reported_as_a_bridge_error(self):
        with mock.patch.object(subprocess, "run",
                               side_effect=subprocess.TimeoutExpired(cmd=["node"], timeout=5)):
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.convert_html(self.RUNTIME, html=self.html, output=self.directory / "deck.pptx",
                                    timeout=5)
        self.assertIn("did not finish", str(caught.exception))

    def test_a_reported_success_without_a_saved_package_is_refused(self):
        output = self.directory / "deck.pptx"
        payload = {"status": "ok", "output_sha256": "0" * 64, "panels": 1, "parts": 1,
                   "conversion_ms": 1, "console_warnings": [], "page_errors": [],
                   "blocked_requests": [], "missing_local_requests": []}
        with mock.patch.object(subprocess, "run",
                               return_value=subprocess.CompletedProcess(args=[], returncode=0,
                                                                        stdout=json.dumps(payload), stderr="")):
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.convert_html(self.RUNTIME, html=self.html, output=output)
        self.assertIn("wrote no package", str(caught.exception))


class ContractRecordTests(unittest.TestCase):
    def read(self, path):
        return Path(path).read_text(encoding="utf-8")

    def test_reference_states_the_contract_runtime_and_limits(self):
        text = " ".join(self.read(REFERENCE).split())
        for required in ("data-office-slide", "1920x1080", "data-office-notes",
                         "OFFICE_PPTX_NODE", "OFFICE_PPTX_PLAYWRIGHT", "OFFICE_PPTX_BROWSER",
                         "pptx_convert_bridge.py", "office/pptx-html-conversion/v1",
                         "no native PPTX table", "UPSTREAM.md", "not a silent fallback"):
            self.assertIn(required, text, required)
        self.assertIn("never replaced silently", self.read(SKILL))

    def test_skill_and_role_route_construction_through_the_reference(self):
        self.assertIn("references/html-to-pptx.md", self.read(SKILL))
        self.assertIn("pptx_convert_bridge.py", self.read(SKILL))
        self.assertIn("html-to-pptx.md", self.read(DESIGNER))
        self.assertIn("data-office-slide", self.read(DESIGNER))

    def test_policy_records_stay_consistent_about_the_scoped_copy(self):
        readme = self.read(ROOT / "plugins/office/README.md")
        self.assertIn("open-slide/open-slide", readme)
        self.assertIn(UPSTREAM_PIN, readme)
        instructions = self.read(ROOT / "CLAUDE.md")
        self.assertIn("One scoped exception is in force", instructions)
        self.assertIn("open-slide PPTX exporter subset", instructions)
        sync = self.read(ROOT / ".claude/skills/upstream-sync/SKILL.md")
        self.assertIn("open-slide PPTX exporter, MIT", sync)
        self.assertIn(UPSTREAM_PIN, sync)
        intake = self.read(ROOT / ".claude/skills/external-repo-intake/SKILL.md")
        self.assertIn("open-slide PPTX exporter for Office", intake)
        licenses = self.read(ROOT / "docs/plugins/office/licenses.md")
        self.assertIn("Motore di conversione open-slide", licenses)
        updates = self.read(ROOT / "docs/plugins/office/upstream-updates.md")
        self.assertIn("Motore di conversione open-slide", updates)
        dependencies = self.read(ROOT / "docs/plugins/office/dependencies.md")
        self.assertIn("html-to-pptx.md", dependencies)

    def test_the_fixture_exercises_the_contract(self):
        text = self.read(FIXTURE)
        self.assertEqual(2, text.count("data-office-slide"))
        self.assertEqual(2, text.count("data-office-notes"))
        self.assertIn("width: 1920px", text)
        self.assertIn("height: 1080px", text)
        self.assertIn("position: relative", text)


def runtime_available():
    """Return (runtime, probe) or a skip reason; a missing runtime is not a failure."""
    try:
        runtime = bridge.discover()
        probe = bridge.probe(runtime)
    except bridge.BridgeError as error:
        return None, str(error)
    except (OSError, subprocess.SubprocessError) as error:
        return None, str(error)
    return (runtime, probe), None


def tiny_png():
    """A valid 2x2 opaque PNG, built rather than pasted so its checksums hold."""
    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))
    rows = b"".join(b"\x00" + b"\xe8\x5d\x04" * 2 for _ in range(2))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


class RealConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        available, reason = runtime_available()
        if available is None:
            raise unittest.SkipTest(f"conversion runtime unavailable: {reason}")
        cls.runtime, cls.probe = available

    def test_the_fixture_converts_to_a_native_package_with_notes_and_media(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output = directory / "fixture.pptx"
            record = directory / "fixture.conversion.json"
            try:
                result = bridge.convert_html(self.runtime, html=FIXTURE, output=output, evidence=record)
            except bridge.BridgeError as error:
                if "The browser did not start" in str(error):
                    self.skipTest(f"no usable browser: {error}")
                raise
            self.assertEqual(2, result["panels"])
            self.assertTrue(output.is_file())
            self.assertEqual(bridge.sha256(output), result["output_sha256"])
            self.assertEqual(result["output_bytes"], output.stat().st_size)

            evidence = json.loads(record.read_text(encoding="utf-8"))
            self.assertEqual("office/pptx-html-conversion/v1", evidence["schema"])
            self.assertEqual(bridge.sha256(FIXTURE), evidence["html"]["sha256"])
            self.assertEqual(self.runtime["bundle_sha256"], evidence["bundle"]["sha256"])
            self.assertEqual(UPSTREAM_PIN, evidence["engine"]["git_ref"])
            self.assertEqual({"width": 1920, "height": 1080, "device_scale_factor": 1}, evidence["viewport"])
            self.assertEqual([], evidence["blocked_requests"])
            self.assertEqual([], evidence["page_errors"])
            self.assertTrue(evidence["limits"])
            self.assertEqual([{"nodes": 4, "background": True, "notes": True},
                              {"nodes": 11, "background": True, "notes": True}],
                             [{key: slide[key] for key in ("nodes", "background", "notes")}
                              for slide in evidence["scene"]])

            with zipfile.ZipFile(output) as package:
                self.assertEqual([], package.testzip() or [])
                names = set(package.namelist())
                for required in ("[Content_Types].xml", "ppt/presentation.xml",
                                 "ppt/slides/slide1.xml", "ppt/slides/slide2.xml",
                                 "ppt/notesSlides/notesSlide1.xml", "ppt/notesSlides/notesSlide2.xml"):
                    self.assertIn(required, names, required)
                first = package.read("ppt/slides/slide1.xml").decode("utf-8")
                second = package.read("ppt/slides/slide2.xml").decode("utf-8")
                notes = package.read("ppt/notesSlides/notesSlide1.xml").decode("utf-8")
                presentation = package.read("ppt/presentation.xml").decode("utf-8")
                self.assertIn("Conversione nativa", first)
                self.assertIn("OFFICE FIXTURE | 2026-10-27", first)
                self.assertIn("Limite noto", second)
                self.assertIn("Aprire con la decisione", notes)
                self.assertIn('cx="12192000"', presentation)
                self.assertIn('cy="6858000"', presentation)
                self.assertIn("<p:pic>", second)
                self.assertNotIn("graphicFrame", second)
                self.assertTrue(any(name.startswith("ppt/media/") for name in names))
                for relationship in ("ppt/slides/_rels/slide1.xml.rels", "ppt/slides/_rels/slide2.xml.rels"):
                    self.assertNotIn('TargetMode="External"', package.read(relationship).decode("utf-8"))

    def test_a_panel_outside_the_contract_is_refused_by_the_engine(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "broken.html"
            source.write_text(
                "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
                ".slide{position:relative;width:1280px;height:720px;box-sizing:border-box;}"
                "</style></head><body><section class='slide' data-office-slide>"
                "<h1>Wrong canvas</h1></section></body></html>", encoding="utf-8")
            with self.assertRaises(bridge.BridgeError) as caught:
                bridge.convert_html(self.runtime, html=source, output=directory / "broken.pptx",
                                    evidence=directory / "broken.conversion.json")
            message = str(caught.exception)
            self.assertIn("contract violated", message)
            self.assertIn("1920x1080", message)
            self.assertIn("code 2", message)
            self.assertFalse((directory / "broken.pptx").exists())

    def write_design(self, directory, body, head="", name="design.html"):
        source = Path(directory) / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(
            "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
            "body{margin:0}.slide{position:relative;width:1920px;height:1080px;box-sizing:border-box;"
            "overflow:hidden;background:#f4f1ea;font-family:Arial,sans-serif}"
            f"</style>{head}</head><body><section class='slide' data-office-slide>{body}</section>"
            "</body></html>", encoding="utf-8")
        return source

    def convert(self, source, directory, name="deck", **options):
        directory = Path(directory)
        return bridge.convert_html(self.runtime, html=source, output=directory / f"{name}.pptx",
                                   evidence=directory / f"{name}.conversion.json", **options)

    def refused(self, source, directory, **options):
        with self.assertRaises(bridge.BridgeError) as caught:
            self.convert(source, directory, **options)
        self.assertFalse((Path(directory) / "deck.pptx").exists(), "a refused design leaves no package")
        return str(caught.exception)

    def test_entrance_animations_are_measured_at_their_end_frame(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = self.write_design(
                temporary,
                "<h1 class='rise' style='position:absolute;left:120px;top:200px;font-size:96px'>Animated title</h1>"
                "<div class='rise' style='position:absolute;left:120px;top:500px;width:600px;height:200px;"
                "background:#e85d04'></div>",
                head="<style>@keyframes rise{from{opacity:0;transform:translateY(40px)}to{opacity:1}}"
                     ".rise{animation:rise 1.2s both .3s}</style>")
            result = self.convert(source, temporary)
            evidence = json.loads(Path(result["evidence"]).read_text(encoding="utf-8"))
            self.assertGreaterEqual(evidence["scene"][0]["nodes"], 2)
            with zipfile.ZipFile(result["output"]) as package:
                self.assertIn("Animated title", package.read("ppt/slides/slide1.xml").decode("utf-8"))

    def test_a_panel_without_visible_content_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "empty.html"
            source.write_text(
                "<!DOCTYPE html><html><head><style>body{margin:0}.slide{position:relative;width:1920px;"
                "height:1080px;box-sizing:border-box}</style></head><body>"
                "<section class='slide' data-office-slide><p style='opacity:0'>hidden</p></section>"
                "</body></html>", encoding="utf-8")
            self.assertIn("measured no visible content", self.refused(source, temporary))

    def test_remote_requests_and_sockets_are_blocked_and_refuse_the_design(self):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(0.5)
        port = listener.getsockname()[1]
        connections = []

        def accept():
            try:
                connection, _ = listener.accept()
                connections.append(connection)
            except OSError:
                pass

        watcher = threading.Thread(target=accept)
        watcher.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                source = self.write_design(
                    temporary,
                    "<h1 style='position:absolute;left:120px;top:200px'>Egress</h1>"
                    f"<script>new WebSocket('ws://127.0.0.1:{port}/egress');"
                    "fetch('https://example.invalid/beacon').catch(()=>{});</script>")
                message = self.refused(source, temporary)
        finally:
            watcher.join()
            listener.close()
            for connection in connections:
                connection.close()
        self.assertEqual([], connections, "a WebSocket reached a listener outside the conversion origin")
        self.assertIn("contract violated", message)
        self.assertIn(f"ws://127.0.0.1:{port}/egress", message)
        self.assertIn("https://example.invalid/beacon", message)

    def test_relative_assets_resolve_from_the_html_directory_under_an_asset_root(self):
        png = tiny_png()
        with tempfile.TemporaryDirectory() as temporary:
            site = Path(temporary) / "site"
            (site / "deck" / "img").mkdir(parents=True)
            (site / "brand").mkdir()
            (site / "deck" / "img" / "a.png").write_bytes(png)
            (site / "brand" / "logo.png").write_bytes(png)
            source = self.write_design(
                site / "deck",
                "<img src='img/a.png' style='position:absolute;left:100px;top:100px;width:300px;height:300px'>"
                "<div style=\"position:absolute;left:600px;top:100px;width:300px;height:300px;"
                "background:url('/brand/logo.png') center/cover\"></div>"
                "<h1 style='position:absolute;left:100px;top:600px'>Assets</h1>")
            result = self.convert(source, temporary, assets_root=site)
            self.assertEqual([], result["missing_local_requests"])
            evidence = json.loads(Path(result["evidence"]).read_text(encoding="utf-8"))
            self.assertGreaterEqual(evidence["scene"][0]["kinds"].get("picture", 0), 1)

    def test_a_missing_local_asset_or_a_dotfile_refuses_the_design(self):
        with tempfile.TemporaryDirectory() as temporary:
            (Path(temporary) / ".env").write_text("SECRET=1", encoding="utf-8")
            source = self.write_design(
                temporary,
                "<h1 style='position:absolute;left:120px;top:200px'>Assets</h1>"
                "<div style=\"position:absolute;left:0;top:0;width:10px;height:10px;"
                "background:url('img/absent.png')\"></div>"
                "<script>fetch('.env').catch(()=>{});</script>")
            message = self.refused(source, temporary)
        self.assertIn("/img/absent.png", message)
        self.assertIn("/.env", message)

    def test_a_named_browser_that_does_not_exist_stops_the_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = self.write_design(temporary, "<h1>Browser</h1>")
            absent = str(Path(temporary) / "absent-chrome.exe")
            with mock.patch.dict(os.environ, {"OFFICE_PPTX_BROWSER": absent}):
                message = self.refused(source, temporary)
        self.assertIn("OFFICE_PPTX_BROWSER does not exist", message)
        self.assertIn("code 3", message)

    def test_the_same_design_produces_the_same_package_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = self.convert(FIXTURE, temporary, name="first")
            second = self.convert(FIXTURE, temporary, name="second")
        self.assertEqual(first["output_sha256"], second["output_sha256"])


if __name__ == "__main__":
    unittest.main()
