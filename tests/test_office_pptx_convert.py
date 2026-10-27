"""Vendored open-slide conversion gear: hash guard, bridge transport, contract records.

The real browser conversion runs only where Node, the Playwright module and a
Chromium-family browser are actually available; elsewhere it skips with the
reason instead of passing silently.
"""

import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
import zipfile
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
UPSTREAM_PIN = "82349cf2d07d37b75975170503a82fcaacae9298"
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
        self.assertEqual("2.3.1", upstream["version"])
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
        self.assertEqual("2.3.1", runtime["engine"]["version"])

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
               "engine": {"package": "@open-slide/core", "version": "2.3.1",
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
                if "Chromium did not start" in str(error):
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
            self.assertFalse((directory / "broken.pptx").exists())


if __name__ == "__main__":
    unittest.main()
