"""scip-java for Java and Kotlin through the container operation, against the fake Docker-compatible command line
of `test_codebase_map_container.py`.

The fake never runs a command. For the two bash phases it plays what a test scripted (files written into the
container, a log, an exit code), so each test checks what `indexers.java.index` and `indexers.kotlin.index` send,
keep and return: the build only in the container, the networks of the two phases, the project unchanged, the
outputs and the contract, a gap as `unavailable`, a build failure as `failed`, and the committed fixture indexes
read back through the contract into the graphs their `expected.json` describes. Downloads are served from memory:
scip-java's classpath and the default build tools are replaced by small files with their own checksums.

The smoke test at the end runs the Java fixture in a real container and only with DAODAN_JVM_SMOKE=1:

    DAODAN_JVM_SMOKE=1 python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_jvm.py -k Smoke
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
for path in (str(SCRIPTS), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import container  # noqa: E402
import preparation  # noqa: E402
import resolve_edges  # noqa: E402
import engine_tools  # noqa: E402
import test_codebase_map_code_graph as graph_tests  # noqa: E402
from indexers import java, jvm, kotlin  # noqa: E402
from test_codebase_map_container import FAKE_CLI, tree_digest  # noqa: E402

FIXTURES = HERE / "fixtures/code-graph"
OWN = {"index.scip", "expected.json"}  # the fixture's own files, never part of the project given to the indexer

# Before the shared fake: `start -a` of a bash phase plays `play/<phase>/` (files under `fs/` copied into the
# container, `log` printed, `code` the exit code) and keeps the script it was given in `scripts/<phase>.sh`.
PLAY = r'''
import json as _json, shutil as _shutil, sys as _sys
from pathlib import Path as _Path
_state, _args = _Path(_sys.argv[1]), _sys.argv[2:]
if _args[:2] == ["start", "-a"]:
    _box = _state / "containers" / _args[-1]
    _command = _json.loads((_box / "command.json").read_text())
    if _command[:2] == ["bash", "-c"]:
        with (_state / "calls.jsonl").open("a", encoding="utf-8") as _log:
            _log.write(_json.dumps(_args) + "\n")
        _phase = _command[2].split("\n", 1)[0].split()[-1]
        (_state / "scripts").mkdir(exist_ok=True)
        (_state / "scripts" / (_phase + ".sh")).write_text(_command[2], encoding="utf-8")
        _play = _state / "play" / _phase
        if (_play / "fs").is_dir():
            _shutil.copytree(_play / "fs", _box / "fs", dirs_exist_ok=True)
        if (_play / "log").is_file():
            _sys.stdout.write((_play / "log").read_text(encoding="utf-8"))
        _sys.exit(int((_play / "code").read_text()) if (_play / "code").is_file() else 0)
'''

JAVAP = """Classfile /work/target/classes/fx/Shapes.class
  this_class: #8                          // fx/Shapes
{
  public fx.Shapes();
    descriptor: ()V
    flags: (0x0001) ACC_PUBLIC
}
"""


def log(*steps: tuple[str, int, str], peak: int | None = 2**30) -> str:
    """A phase log as the scripts print it: each step's markers around its output, then the memory peak."""
    lines, clock = [], 100.0
    for name, code, output in steps:
        lines += [f"DAODAN_STEP begin {name} {clock:.3f}", output, f"DAODAN_STEP end {name} {code} {clock + 2.5:.3f}"]
        clock += 3
    lines.append(f"DAODAN_PEAK {peak if peak is not None else '-'}")
    return "\n".join(lines) + "\n"


class Recorder(subprocess.Popen):
    """Every host process, by its argv."""
    calls: list[list[str]] = []

    def __init__(self, args, *rest, **options):
        Recorder.calls.append([str(item) for item in ([args] if isinstance(args, (str, Path)) else args)])
        super().__init__(args, *rest, **options)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


JAR, MAVEN_ZIP, GRADLE_ZIP = b"the scip-java jar", b"the maven distribution", b"the gradle distribution"
MAVEN_URL = f"{jvm.MAVEN_SITE}0.test/apache-maven-0.test-bin.zip"
GRADLE_URL = f"{jvm.GRADLE_SITE}gradle-0.test-bin.zip"


BUILD_FILES = ("pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts")


def pre_map(project: Path, folder: Path) -> dict:
    """The project's pre-map, as an analysis derives it first: a snapshot outside the project, then the record."""
    import premap
    import snapshot
    manifest = folder / "manifest.sqlite"
    snapshot.write_snapshot(project, manifest)
    return premap.ensure(manifest)


class FakeEngineTest(unittest.TestCase):
    language = "java"

    def setUp(self):
        self.scratch = Path(tempfile.mkdtemp(prefix="daodan-jvm-test-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.state = self.scratch / "state"
        for name in ("containers", "images", "play"):
            (self.state / name).mkdir(parents=True)
        fake = self.scratch / "fake_docker.py"
        fake.write_text(PLAY + FAKE_CLI, encoding="utf-8")
        self.engine = container.Engine("fake", (sys.executable, str(fake), str(self.state)))
        self.fixture = FIXTURES / self.language
        self.project = self.scratch / "project" / self.language
        shutil.copytree(self.fixture, self.project, ignore=lambda folder, names: [
            name for name in names if name in OWN or name == "kotlin-configs"])
        self.work = self.scratch / "work"
        Recorder.calls = []
        self.asked: list[str] = []
        self.served = {f"{resolve_edges.MAVEN_CENTRAL}/fx/test/tool/1.0/tool-1.0.jar": JAR, MAVEN_URL: MAVEN_ZIP,
                       GRADLE_URL: GRADLE_ZIP}
        cache = self.scratch / "cache"
        for patcher in (mock.patch.dict(os.environ, {"LOCALAPPDATA": str(cache), "XDG_CACHE_HOME": str(cache)}),
                        mock.patch.object(jvm, "CLASSPATH", (("fx.test:tool:1.0", digest(JAR)),)),
                        mock.patch.object(jvm, "MAVEN", ("0.test", digest(MAVEN_ZIP))),
                        mock.patch.object(jvm, "GRADLE", ("0.test", digest(GRADLE_ZIP))),
                        mock.patch.object(resolve_edges, "open_url", self.open_url),
                        mock.patch.object(engine_tools, "open_url", self.open_url),
                        mock.patch("time.sleep")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def open_url(self, url: str, timeout: float):
        self.asked.append(url)
        if url not in self.served:
            raise OSError(f"not served: {url}")
        return io.BytesIO(self.served[url])

    def wrapper(self, relative: str, url: str, sha256: str | None = None):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"distributionUrl={url}\n" + (f"distributionSha256Sum={sha256}\n" if sha256 else ""),
                        encoding="utf-8")

    def arrived(self, phase: int = 1) -> Path:
        """The files system of a created container (0 is the proxy, 1 the preparation)."""
        call = self.created()[phase]
        return self.state / "containers" / call[call.index("--name") + 1] / "fs"

    def play(self, phase: str, *, files: dict[str, Path | str] | None = None, text: str = "", code: int = 0):
        folder = self.state / "play" / phase
        for rel, source in (files or {}).items():
            target = folder / "fs" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(source, Path) and source.is_dir():
                shutil.copytree(source, target)
            elif isinstance(source, Path):
                shutil.copyfile(source, target)
            else:
                target.write_text(source, encoding="utf-8")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "log").write_text(text, encoding="utf-8")
        (folder / "code").write_text(str(code))

    def play_success(self):
        """What a good build leaves: the fixture's committed index, and for Kotlin its compile tasks."""
        out, kept = jvm.OUT.lstrip("/"), jvm.KEPT.lstrip("/")
        self.play("prepare", files={f"{kept}/index.scip": self.fixture / "index.scip"},
                  text=log(("index", 0, "[INFO] BUILD SUCCESS")))
        if self.language == "java":
            self.play("execute", files={f"{out}/index.scip": self.fixture / "index.scip",  # as the script copies it
                                        f"{out}/index-forward.scip": self.fixture / "index.scip",
                                        f"{out}/javap/project.txt": JAVAP},
                      text=log(("aggregate", 0, "done"), ("javap-project", 0, ""), peak=2**28))
        else:
            self.play("execute", files={f"{out}/index.scip": self.fixture / "index.scip",
                                        f"{out}/kotlin-configs": self.fixture / "kotlin-configs"},
                      text=log(("configs", 0, ""), peak=2**28))

    def index(self, **options) -> dict:
        module = java if self.language == "java" else kotlin
        options.setdefault("engine", self.engine)
        options.setdefault("roots", {""})
        with mock.patch.object(container, "free_memory", return_value=64 * 2**30), \
                mock.patch("subprocess.Popen", Recorder):
            return module.index(self.project, self.work, **options)

    def calls(self) -> list[list[str]]:
        path = self.state / "calls.jsonl"
        return [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def created(self) -> list[list[str]]:
        return [call for call in self.calls() if call[0] == "create"]


class EachBuildTests:
    """One run per build folder of the pre-map, for Java and for Kotlin alike."""

    def test_each_build_the_pre_map_names_runs_in_a_container_of_its_own(self):
        """A project with its build in a subfolder, beside another: one run per build folder, over that folder
        only, its index named from the checkout by the folder."""
        shutil.copytree(self.project, self.scratch / "second")
        shutil.move(str(self.scratch / "second"), str(self.project / "services/shop"))
        self.play_success()
        result = self.index(roots={"", "services/shop"})
        self.assertNotIn("state", result)
        self.assertEqual([prefix for _path, prefix in result["indexes"]], ["", "services/shop"])
        self.assertEqual(result["builds"], [{"root": "", "state": "done"}, {"root": "services/shop", "state": "done"}])
        self.assertEqual(sorted({run["build"] for run in result["runs"]}), ["", "services/shop"])
        copied = [self.state / "containers" / call[call.index("--name") + 1] / "fs" for call in self.created()]
        roots = sorted({path.parent.relative_to(fs).as_posix() for fs in copied for name in BUILD_FILES
                        for path in fs.rglob(name) if "tools" not in path.parts} - {"."}, key=len)
        self.assertNotIn("services/shop", roots)  # the second run holds only its own folder

    def test_what_the_copy_of_the_project_left_out_is_a_gap_of_the_build(self):
        """A link Git tracks to outside the project stays out of the copy (`container.copy_perimeter`): a gap of
        the build beside the preparation's own."""
        left = {"kind": "link_outside", "path": "x.java", "target": "../y.java", "detail": "x.java links outside"}
        copied = container.copy_perimeter
        self.play_success()
        self.play("prepare", files={f"{jvm.KEPT.lstrip('/')}/index.scip": self.fixture / "index.scip"},
                  text=log(("index", 0, "[INFO] BUILD SUCCESS")) + "DAODAN-MISSING gradle@1.0\n")
        with mock.patch.object(container, "copy_perimeter", lambda *given: {**copied(*given), "gaps": [left]}):
            gaps = self.index().get("gaps", [])
        self.assertIn(left, gaps)
        self.assertIn("toolchain_unavailable", [gap["kind"] for gap in gaps])

    def test_a_build_s_container_holds_the_checkout_and_its_steps_run_in_its_folder(self):
        """A build reads what lies outside its folder as it does in a checkout (opentelemetry-demo's services read
        the protos at `../../pb`): its container holds the checkout, and its steps run in the build's folder."""
        shutil.copytree(self.project, self.scratch / "second")
        shutil.move(str(self.scratch / "second"), str(self.project / "services/shop"))
        (self.project / "pb").mkdir()
        (self.project / "pb/demo.proto").write_text('syntax = "proto3";\n', encoding="utf-8")
        self.play_success()
        self.index(roots={"services/shop"})
        fs = self.arrived(1) / "work"
        self.assertTrue((fs / "pb/demo.proto").is_file())
        self.assertTrue(any((fs / "services/shop" / name).is_file() for name in BUILD_FILES))
        for phase in ("prepare", "execute"):
            self.assertIn("\nDAODAN_ROOT=services/shop\n",
                          (self.state / f"scripts/{phase}.sh").read_text(encoding="utf-8"))

    def test_a_build_runs_on_the_jdks_its_own_files_state_not_another_build_s(self):
        """opentelemetry-demo's fraud-detection states Kotlin's JVM target 17 and no JDK; its ad service states
        Java 21: fraud-detection runs on the image's 17, as its CI's image does (on 21 its compileJava would target
        21 against compileKotlin's 17), and the ad service on 21. A file above the build states for it too."""
        self.serve_mise()
        shutil.copytree(self.project, self.scratch / "second")
        shutil.move(str(self.scratch / "second"), str(self.project / "src/fraud"))
        self.play_success()
        other = {"tool": "java", "version": "21", "declared_in": "src/ad/build.gradle#sourceCompatibility"}
        self.index(roots={"src/fraud"}, toolchains=[other])
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertIn("\nDAODAN_JDK=17\n", script)
        self.assertNotIn("install java@21", script)
        for declared_in in ("src/fraud/build.gradle#sourceCompatibility", ".tool-versions"):
            self.index(roots={"src/fraud"}, toolchains=[other, {**other, "declared_in": declared_in}])
            script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
            self.assertIn("\nDAODAN_JDK=21\n", script, declared_in)

    def test_an_android_build_that_stops_on_a_missing_google_services_json_names_the_file_and_its_plugin(self):
        missing = ("* What went wrong:\nExecution failed for task ':app:processDebugGoogleServices'.\n"
                   "> File google-services.json is missing. The Google Services Plugin cannot function without it.")
        self.play("prepare", text=log(("index", 1, missing)), code=1)
        result = self.index(tools={"": ["gradle"]})
        gap = next(gap for gap in result.get("gaps", ()) if gap["kind"] == "build_input_missing")
        self.assertEqual(gap["path"], ".")
        for said in ("google-services.json", "com.google.gms.google-services"):
            self.assertIn(said, gap["detail"])

    def test_a_build_that_fails_keeps_the_others_and_says_which_failed(self):
        shutil.copytree(self.project, self.scratch / "second")
        shutil.move(str(self.scratch / "second"), str(self.project / "services/shop"))
        self.play_success()
        real = jvm.run
        calls = []

        def one_fails(project_dir, *args, **options):
            calls.append(Path(project_dir))
            if Path(project_dir).name == "shop":
                return {"state": "failed", "cause": "the build failed"}, [], Path(args[0]) / "nothing"
            return real(project_dir, *args, **options)

        with mock.patch.object(jvm, "run", one_fails):
            result = self.index(roots={"", "services/shop"})
        self.assertNotIn("state", result)
        self.assertEqual([prefix for _path, prefix in result["indexes"]], [""])
        self.assertEqual(result["builds"][1]["root"], "services/shop")
        self.assertEqual(result["builds"][1]["state"], "failed")

    def test_without_a_build_in_the_pre_map_nothing_runs_and_the_cause_is_said(self):
        result = self.index(roots=set())
        self.assertEqual(result["state"], "unavailable")
        self.assertIn("no Gradle or Maven build", result["reason"])
        self.assertEqual(self.created(), [])

    def test_the_builds_are_the_outermost_gradle_and_maven_units_of_the_pre_map(self):
        record = {"units": [{"kind": "gradle-project", "root": "."}, {"kind": "gradle-project", "root": "app"},
                            {"kind": "maven-module", "root": "svc"}, {"kind": "maven-module", "root": "svc/core"},
                            {"kind": "gradle-project", "root": "tools/plugin"}, {"kind": "npm-package", "root": "web"}]}
        both = {"units": [{"kind": "gradle-project", "root": "."}, {"kind": "maven-module", "root": "."},
                          {"kind": "maven-module", "root": "core"}]}  # one folder, two builds
        for module in (java, kotlin):
            self.assertEqual(module.structure(record)["roots"], {"", "svc"})
            self.assertEqual(module.structure(record)["tools"], {"": ["gradle"], "svc": ["maven"]})
            self.assertEqual(module.structure(both)["tools"], {"": ["gradle", "maven"]})

    def test_a_folder_two_build_tools_build_is_built_by_the_next_only_when_one_gives_no_index(self):
        """A folder with a Gradle build and a Maven one: scip-java is told which (`--build-tool`), Gradle first;
        both compile the same files, so Maven builds only when Gradle gave no index, and Gradle's cause stays."""
        self.play_success()
        real, tools = jvm.run, []

        def gradle_fails(project_dir, work_dir, prepare, *args, **options):
            tools.append(re.search(r"^DAODAN_TOOL=(\w*)$", prepare, re.M).group(1))
            if tools[-1] == "gradle":
                return {"state": "failed", "cause": "no toolchain"}, [], Path(work_dir) / "nothing"
            return real(project_dir, work_dir, prepare, *args, **options)

        with mock.patch.object(jvm, "run", gradle_fails):
            result = self.index(roots={""}, tools={"": ["gradle", "maven"]})
        self.assertEqual(tools, ["gradle", "maven"])
        self.assertEqual([prefix for _path, prefix in result["indexes"]], [""])
        self.assertEqual([(build["tool"], build["state"]) for build in result["builds"]],
                         [("gradle", "failed"), ("maven", "done")])
        tools.clear()
        with mock.patch.object(jvm, "run", gradle_fails):
            result = self.index(roots={""}, tools={"": ["maven", "gradle"]})
        self.assertEqual(tools, ["maven"])  # the first gave an index: the second does not build
        self.assertEqual([build["tool"] for build in result["builds"]], ["maven"])

    def test_scip_java_is_told_the_build_tool_of_the_folder(self):
        self.play_success()
        self.index(roots={""}, tools={"": ["maven"]})
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertIn("\nDAODAN_TOOL=maven\n", script)
        self.assertIn('"$SCIP_JAVA" index --output "$OUT/index.scip" ${DAODAN_TOOL:+--build-tool=$DAODAN_TOOL}',
                      script)


class PreparationTests:
    """A JVM build takes the preparation's steps (`preparation`): its proxy for the JVM, the restore of the
    dependencies before scip-java, a JDK the pre-map states above the image's from mise; what they could not do is
    a gap of the stage, and the build goes on."""

    def manager(self) -> str:
        return "maven" if self.language == "java" else "gradle"

    def serve_mise(self):
        tool = b"mise"
        self.served[preparation.MISE[0]] = tool
        patcher = mock.patch.object(preparation, "MISE", (preparation.MISE[0], digest(tool), "mise"))
        patcher.start()
        self.addCleanup(patcher.stop)
        return tool

    def test_the_build_restores_its_dependencies_with_the_preparation_before_scip_java(self):
        self.play_success()
        self.index()
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        line = preparation.restore(self.manager(), ["."])
        self.assertIn(preparation.JAVA_PROXY, script)
        self.assertNotIn("address=${HTTPS_PROXY", jvm.PREPARE)  # one proxy setup for the JVM: the preparation's
        self.assertIn(line, script)
        called = re.compile(r"\bscip_index\b(?! *\(\))")  # scip-java's index, defined above the restore
        self.assertIsNone(called.search(script[:script.index(line)]))
        self.assertIsNotNone(called.search(script[script.index(line):]))

    def test_a_restore_that_fails_is_a_gap_and_the_build_goes_on(self):
        self.play_success()
        failed = (f"DAODAN-RESTORE-FAILED {self.manager()} .\n[ERROR] Could not resolve com.example:gone:1.0\n"
                  "DAODAN-RESTORE-END\n")
        self.play("prepare", text=failed + log(("index", 0, "[INFO] BUILD SUCCESS")))
        result = self.index()
        self.assertTrue(result["indexes"])
        self.assertEqual(result["gaps"], preparation.restore_gaps(failed))

    def test_a_jdk_the_pre_map_states_above_the_images_is_installed_by_the_preparation(self):
        tool = self.serve_mise()
        self.play_success()
        self.index(toolchains=[{"tool": "java", "version": "21", "declared_in": "pom.xml#maven.compiler.release"}])
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertIn("install java@21", script)
        self.assertIn("mise/installs/java", script)  # JAVA_HOME follows the JDK installed
        self.assertIn("api.adoptium.net", self.created()[0])
        self.assertEqual((self.arrived(1) / preparation.IN.lstrip("/") / "mise").read_bytes(), tool)

    def test_each_jdk_a_gradle_toolchain_asks_for_is_installed_and_the_build_runs_on_the_newest(self):
        """A composite build's toolchains (an included build on 17, its projects on 21): the image holds 17, the
        preparation installs the others, and the build runs on the newest stated above the image's."""
        self.serve_mise()
        self.play_success()
        field = "#java.toolchain.languageVersion"
        self.index(toolchains=[
            {"tool": "java", "version": "17", "declared_in": f"libs/money/build.gradle.kts{field}"},
            {"tool": "java", "version": "21", "declared_in": f"api/build.gradle.kts{field}"},
            {"tool": "java", "version": "11", "declared_in": f"legacy/build.gradle{field}"},
            {"tool": "java", "version": "1.8", "declared_in": "pom.xml#maven-compiler-plugin.source"}])
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertIn("install java@21", script)
        self.assertIn("install java@11", script)
        self.assertNotIn("install java@17", script)  # the image's
        self.assertNotIn("install java@1.8", script)  # a pom's level is no toolchain of Gradle's
        self.assertIn("\nDAODAN_JDK=21\n", script)

    def test_a_jdk_the_image_holds_is_not_installed(self):
        self.play_success()
        self.index(toolchains=[{"tool": "java", "version": "1.8", "declared_in": "pom.xml#x"},
                               {"tool": "java", "version": "17", "declared_in": "pom.xml#y"}])
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertNotIn("install java@", script)
        self.assertNotIn("api.adoptium.net", self.created()[0])

    def test_a_jdk_the_preparation_could_not_install_is_a_gap_and_the_build_still_needs_it(self):
        self.serve_mise()
        self.play("prepare", text="DAODAN-MISSING java@21\n" + log(
            ("index", 1, "> No matching toolchains found for requested specification: {languageVersion=21}")), code=1)
        result = self.index(toolchains=[{"tool": "java", "version": "21", "declared_in": "build.gradle#x"}])
        self.assertEqual(result["state"], "unavailable")
        self.assertIn("JDK 21", result["reason"])
        self.assertEqual([gap["kind"] for gap in result["gaps"]], ["toolchain_unavailable"])

    def test_the_stage_is_handed_the_jdk_the_pre_map_states(self):
        module = java if self.language == "java" else kotlin
        record = {"units": [], "workspace": [], "toolchains": [
            {"tool": "java", "version": "21", "declared_in": "a#x"},
            {"tool": "node", "version": "24", "declared_in": "b"}]}
        self.assertEqual(module.structure(record)["toolchains"],
                         [{"tool": "java", "version": "21", "declared_in": "a#x"}])

    ANDROID = [{"tool": "android-sdk", "version": "35", "declared_in": "app/build.gradle.kts#android.compileSdk"},
               {"tool": "android-build-tools", "version": "34.0.0",
                "declared_in": "app/build.gradle.kts#android.buildToolsVersion"}]

    def serve_cmdline_tools(self) -> bytes:
        tool = b"cmdline-tools"
        url, _digest, name = preparation.NEEDS["cmdline-tools"]["files"][0]
        self.served[url] = tool
        patcher = mock.patch.dict(preparation.NEEDS, {"cmdline-tools": {
            **preparation.NEEDS["cmdline-tools"], "files": [(url, digest(tool), name)]}})
        patcher.start()
        self.addCleanup(patcher.stop)
        return tool

    def test_the_stage_is_handed_the_android_packages_the_pre_map_states(self):
        module = java if self.language == "java" else kotlin
        record = {"units": [], "workspace": [], "toolchains": [*self.ANDROID, {"tool": "node", "version": "24"}]}
        self.assertEqual(module.structure(record)["toolchains"], self.ANDROID)

    def test_an_android_build_has_the_sdk_packages_it_states_installed_before_the_restore(self):
        """As a CI prepares one: Google's command-line tools, verified, carried in; the licences accepted; then
        sdkmanager installs exactly the stated packages from Google's repository, and ANDROID_HOME names the SDK
        in both phases (the dynamic step runs the tests in the second)."""
        tool = self.serve_cmdline_tools()
        self.play_success()
        self.index(toolchains=self.ANDROID)
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertLess(script.index("--licenses"), script.index("'platforms;android-35'"))
        self.assertLess(script.index("'build-tools;34.0.0'"), script.index(preparation.restore(self.manager(), ["."])))
        self.assertNotIn("install java@", script)  # an API level is no JDK
        self.assertIn("dl.google.com", self.created()[0])
        self.assertEqual((self.arrived(1) / preparation.IN.lstrip("/") / "cmdline-tools.zip").read_bytes(), tool)
        for phase in ("prepare", "execute"):
            self.assertIn(f"export ANDROID_HOME={preparation.ANDROID_HOME}",
                          (self.state / f"scripts/{phase}.sh").read_text(encoding="utf-8"))

    def test_an_sdk_package_sdkmanager_could_not_install_is_a_gap_naming_it_and_why(self):
        self.serve_cmdline_tools()
        self.play_success()
        failed = ("DAODAN-MISSING android-sdk@35 platforms;android-35: Warning: Failed to find package"
                  " 'platforms;android-35'\n")
        self.play("prepare", files={f"{jvm.KEPT.lstrip('/')}/index.scip": self.fixture / "index.scip"},
                  text=failed + log(("index", 0, "BUILD SUCCESSFUL")))
        result = self.index(toolchains=self.ANDROID)
        self.assertTrue(result["indexes"])
        self.assertEqual(result["gaps"], preparation.missing(failed))
        self.assertIn("platforms;android-35: Warning: Failed to find package", result["gaps"][0]["detail"])

    def test_the_hosts_the_project_declares_are_reached_by_the_preparation(self):
        self.play_success()
        self.index(declared={"hosts": ("jitpack.io",), "where": {"jitpack.io": ["pom.xml"]}})
        self.assertIn("jitpack.io", self.created()[0])

    def test_a_build_that_states_no_android_package_carries_no_sdk(self):
        self.play_success()
        self.index(toolchains=[{"tool": "java", "version": "17", "declared_in": "pom.xml#x"}])
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertNotIn("sdkmanager", script)
        self.assertFalse((self.arrived(1) / preparation.IN.lstrip("/") / "cmdline-tools.zip").exists())


class JavaContainerTests(PreparationTests, EachBuildTests, FakeEngineTest):
    def test_the_build_runs_only_in_the_container(self):
        self.play_success()
        result = self.index()
        self.assertTrue(result["indexes"], result)
        for argv in Recorder.calls:  # git answers what the copy leaves out
            self.assertTrue(argv[:2] == [sys.executable, self.engine.argv[1]] or Path(argv[0]).stem.lower() == "git",
                            f"a host process other than the engine CLI and git: {argv}")
        self.assertTrue(any(argv[:2] == [sys.executable, self.engine.argv[1]] for argv in Recorder.calls))
        prepare = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        execute = (self.state / "scripts/execute.sh").read_text(encoding="utf-8")
        self.assertIn('step index "$SCIP_JAVA" index --output "$OUT/index.scip"', prepare)
        self.assertIn("--no-emit-inverse-relationships", execute)
        self.assertNotIn("scip-java\" index", execute)

    @unittest.skipUnless(os.name == "nt", "the shell fallback of Python's version query exists only on Windows")
    def test_the_index_starts_no_version_query_even_when_windows_does_not_answer(self):
        """With the cache empty and WMI failing, Python's `platform` would run `ver` through the shell; the index
        takes the platform from the process (`resolve_edges._platform`), so no such process starts."""
        self.play_success()
        with mock.patch.object(platform, "_uname_cache", None), \
                mock.patch.object(platform, "_wmi_query", side_effect=OSError("WMI did not answer")):
            self.index()
        self.assertNotIn(["ver"], Recorder.calls)

    def test_preparation_reaches_only_the_registries_and_execution_no_network(self):
        self.play_success()
        self.index()
        proxy, prepare, execute = self.created()
        self.assertEqual(proxy[proxy.index(str(container.PROXY_PORT)) + 1:], list(jvm.registries(self.project)))
        for host in ("repo1.maven.org", "repo.maven.apache.org"):
            self.assertIn(host, proxy)
        portal = ("plugins.gradle.org", "plugins-artifacts.gradle.org")
        for host in portal:  # the Plugin Portal only for Gradle: it also takes plugin uploads
            (self.assertIn if self.language == "kotlin" else self.assertNotIn)(host, proxy)
        for host in ("registry.npmjs.org", "registry.yarnpkg.com", "rubygems.org", "pypi.org", "files.pythonhosted.org",
                     "index.crates.io", "static.crates.io", "api.nuget.org", "proxy.golang.org", "sum.golang.org"):
            self.assertNotIn(host, proxy)  # registries that accept publishing: a build here runs project code
        for host in ("services.gradle.org", "github.com", "objects.githubusercontent.com",
                     "release-assets.githubusercontent.com"):
            self.assertNotIn(host, proxy)
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"https?://", script), "the preparation names a host")
        self.assertTrue(prepare[prepare.index("--network") + 1].startswith("daodan-net-"))
        self.assertIn(jvm.IMAGE, prepare)
        self.assertIn("HTTPS_PROXY=http://proxy:3128", prepare)
        self.assertEqual(execute[execute.index("--network") + 1], "none")
        self.assertIn("HTTPS_PROXY=", execute)
        self.assertIn(jvm.IMAGE, execute)
        self.assertEqual([call for call in self.calls() if call[0] in ("commit", "rmi")], [])

    def test_the_preparation_keeps_its_state_in_the_volume_execution_mounts(self):
        self.play_success()
        self.index()
        proxy, prepare, execute = self.created()
        mounts = [[call[index + 1] for index, token in enumerate(call) if token == "-v"] for call in (prepare, execute)]
        self.assertEqual(mounts[0], mounts[1])
        self.assertEqual([mount.split(":", 1)[1] for mount in mounts[0]], ["/work", container.STATE])
        for path in (jvm.LIB, jvm.TOOLS, jvm.KEPT):
            self.assertTrue(container.kept(path), path)
        self.assertEqual((self.arrived(2) / jvm.KEPT.lstrip("/") / "index.scip").read_bytes(),
                         (self.fixture / "index.scip").read_bytes())
        self.assertIn(f"HOME={container.HOME}", prepare)
        script = (self.state / "scripts/execute.sh").read_text(encoding="utf-8")
        self.assertIn(f'cp -a {jvm.KEPT}/. "$OUT"/', script)
        self.assertIn("-Duser.home=$HOME", script)

    def test_each_build_tool_has_its_own_registries(self):
        maven = jvm.registries(self.project)
        gradle_project = self.scratch / "gradle-project"
        gradle_project.mkdir()
        (gradle_project / "settings.gradle").write_text("rootProject.name = 'x'\n", encoding="utf-8")
        gradle = jvm.registries(gradle_project)
        self.assertEqual(set(maven), set(jvm.READ_ONLY))
        self.assertEqual(set(gradle), {*jvm.READ_ONLY, *jvm.PLUGIN_PORTAL})
        self.assertEqual(set(jvm.registries(self.scratch / "no-build")), set(jvm.READ_ONLY))

    def test_the_project_is_not_changed(self):
        before = tree_digest(self.project)
        self.play_success()
        self.index()
        self.assertEqual(tree_digest(self.project), before)

    def test_outputs_come_back_and_the_contract_is_returned(self):
        self.play_success()
        result = self.index()
        self.assertNotIn("state", result)
        build = self.work.resolve() / "build-0"
        self.assertEqual(result["indexes"], [[str(build / "index-forward.scip"), ""]])
        self.assertEqual((build / "index-forward.scip").read_bytes(), (self.fixture / "index.scip").read_bytes())
        self.assertEqual(result["builds"], [{"root": "", "state": "done"}])
        self.assertEqual(result["indexer"], {"name": "scip-java", "version": jvm.VERSION, "seconds": 7.5,
                                             "peak_mb": 1024})
        self.assertEqual([(run["phase"], run["step"], run["returncode"]) for run in result["runs"]],
                         [("prepare", "index", 0), ("execute", "aggregate", 0), ("execute", "javap-project", 0)])
        self.assertTrue(result["runs"][1]["same_occurrences"])
        members = json.loads((self.work / "javap.json").read_text(encoding="utf-8"))
        self.assertEqual(members["fx/Shapes"][0]["flags"], ["ACC_PUBLIC"])
        records = [json.loads(row) for row in (build / "container" / container.RECORD_NAME).read_text(
            encoding="utf-8").splitlines()]
        self.assertEqual([record["phase"] for record in records], ["prepare", "execute"])

    def test_a_container_gap_is_unavailable_and_nothing_runs(self):
        for cause, remedy in (("no container engine answers: neither docker nor podman", "start Docker or Podman"),
                              ("300 MB free on the disk of D:\\daodan; Daodan's engine needs 1 GB",
                               "free space on D:\\"),
                              ("another Kiri engine runs in WSL (kiri); Daodan's would reset its network rules",
                               "open that Kiri so that `docker` answers, or stop it with wsl --terminate kiri")):
            with self.subTest(cause=cause):
                Recorder.calls = []
                with mock.patch.object(container, "find_engine", side_effect=container.Gap(cause, remedy)):
                    result = self.index(engine=None)
                self.assertEqual(result["state"], "unavailable")
                self.assertEqual(result["reason"], cause)
                self.assertEqual(result["install"], remedy)
                self.assertEqual((result["indexes"], Recorder.calls, self.asked), ([], [], []))

    def test_memory_below_the_container_limit_is_unavailable(self):
        with mock.patch.object(container, "free_memory", return_value=2**30), mock.patch("subprocess.Popen", Recorder):
            result = java.index(self.project, self.work, roots={""}, engine=self.engine)
        self.assertEqual(result["state"], "unavailable")
        self.assertIn("1.0 GB of memory free", result["reason"])
        self.assertEqual(Recorder.calls, [])

    def test_a_build_failure_is_failed_with_the_output_tail(self):
        tail = "[ERROR] COMPILATION ERROR : fx/Use.java:[3,1] cannot find symbol\n12:00 ERROR scip-java: no index"
        self.play("prepare", text=log(("index", 1, tail)), code=1)
        result = self.index()
        self.assertEqual(result["state"], "failed")
        self.assertIn("preparation exited with code 1", result["reason"])
        self.assertIn("cannot find symbol", result["reason"])
        self.assertEqual(result["errors"], 2)  # lines holding " ERROR ", as `code_graph.measured` counts them
        self.assertEqual(result["indexes"], [])
        self.assertEqual(len(self.created()), 2)  # the proxy and the preparation: no execution

    def test_the_contract_feeds_the_graph_and_its_expected_ends_hold(self):
        self.play_success()
        check_fixture(self, self.language, self.index())

    def test_scip_java_and_the_default_maven_arrive_from_the_shared_directory_once(self):
        self.play_success()
        self.index()
        fs = self.arrived()
        self.assertEqual((fs / jvm.LIB.lstrip("/") / "tool-1.0.jar").read_bytes(), JAR)
        self.assertEqual((fs / jvm.TOOLS.lstrip("/") / "apache-maven-0.test-bin.zip").read_bytes(), MAVEN_ZIP)
        self.assertEqual(sorted(self.asked), sorted([MAVEN_URL, f"{resolve_edges.MAVEN_CENTRAL}/fx/test/tool/1.0/"
                                                                "tool-1.0.jar"]))
        self.index()
        self.assertEqual(len(self.asked), 2)

    def test_the_wrapper_distribution_is_brought_and_the_wrapper_only_calls_it(self):
        url = f"{jvm.MAVEN_SITE}3.9.test/apache-maven-3.9.test-bin.zip"
        self.served[url] = b"the wrapper's maven"
        self.wrapper(".mvn/wrapper/maven-wrapper.properties", url, digest(b"the wrapper's maven"))
        (self.project / "mvnw").write_text("#!/bin/sh\ncurl https://example.com/maven.zip\n", encoding="utf-8")
        self.play_success()
        self.index()
        self.assertEqual((self.arrived() / jvm.TOOLS.lstrip("/") / "apache-maven-3.9.test-bin.zip").read_bytes(),
                         b"the wrapper's maven")
        self.assertNotIn(MAVEN_URL, self.asked)
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertIn("wrapper=mvnw", script)
        self.assertIn("printf '#!/bin/sh\\nexec %s \"$@\"\\n' \"$tool\" > \"$wrapper\"", script)

    def test_a_checksum_mismatch_is_refused_before_any_container(self):
        url = f"{jvm.MAVEN_SITE}3.9.test/apache-maven-3.9.test-bin.zip"
        self.served[url] = b"a changed distribution"
        self.wrapper(".mvn/wrapper/maven-wrapper.properties", url, "0" * 64)
        result = self.index()
        self.assertEqual(result["state"], "unavailable")
        self.assertIn("checksum mismatch", result["reason"])
        self.assertEqual(self.created(), [])
        self.assertEqual(list((self.scratch / "cache").rglob("apache-maven-3.9.test-bin.zip*")), [])

    def test_a_wrapper_naming_another_site_is_unavailable_and_nothing_is_fetched_from_it(self):
        self.wrapper(".mvn/wrapper/maven-wrapper.properties", "https://mirror.example.com/apache-maven-3.9.6-bin.zip")
        result = self.index()
        self.assertEqual(result["state"], "unavailable")
        self.assertIn("mirror.example.com", result["reason"])
        self.assertIn(".mvn/wrapper/maven-wrapper.properties", result["install"])
        self.assertFalse(any("example.com" in url for url in self.asked))
        self.assertEqual(self.created(), [])

    def test_a_build_asking_for_a_newer_jdk_is_unavailable(self):
        self.play("prepare", text=log(("index", 1, "> No matching toolchains found for requested specification: "
                                                   "{languageVersion=21, vendor=any, implementation=vendor-specific}")),
                  code=1)
        result = self.index()
        self.assertEqual(result["state"], "unavailable")
        self.assertIn("JDK 21", result["reason"])
        self.assertIn("JDK 17 only", result["reason"])

    def test_a_maven_build_on_a_jdk_scip_java_does_not_run_on_is_indexed_on_the_image_s_and_says_so(self):
        """javapoet's pom states Java 8; scip-java's compiler plugin runs on javac 17 or newer only: the build is
        indexed on the image's JDK, none is installed for it, and the result says why. A pom that states its
        `release` states no JDK: the image's compiles it for that release."""
        self.play_success()
        stated = [{"tool": "java", "version": "1.8", "declared_in": "pom.xml#properties.java.version"}]
        result = self.index(tools={"": ["maven"]}, toolchains=stated)
        self.assertNotIn("install java@", (self.state / "scripts/prepare.sh").read_text(encoding="utf-8"))
        self.assertTrue(result["indexes"])
        gap = next(gap for gap in result.get("gaps", ()) if gap["kind"] == "jdk_unsupported")
        self.assertEqual(gap["path"], ".")
        for said in ("Java 8", "pom.xml#properties.java.version", "JDK 17", "scip-java"):
            self.assertIn(said, gap["detail"])
        release = [{"tool": "java", "version": "8", "declared_in": "pom.xml#maven-compiler-plugin.release"}]
        self.assertNotIn("gaps", self.index(tools={"": ["maven"]}, toolchains=release))

    def test_a_gradle_toolchain_scip_java_does_not_run_on_is_compiled_on_and_the_gap_says_why_no_index(self):
        """Gradle runs on the image's JDK and compiles on the toolchain its scripts ask for, which the preparation
        installs and hands it: on 11, where scip-java's plugin, of Java 17's class files, does not load, the
        failure says why. A toolchain of 17 or newer has no such gap."""
        self.serve_mise()
        field = "#java.toolchain.languageVersion"
        stated = [{"tool": "java", "version": "11", "declared_in": f"lib/build.gradle.kts{field}"}]
        self.play("prepare", text=log(("index", 1, "> Task :lib:compileJava FAILED")), code=1)
        result = self.index(tools={"": ["gradle"]}, toolchains=stated)
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertIn("install java@11", script)
        self.assertIn("\nDAODAN_JDK=17\n", script)  # Gradle itself runs on the image's
        self.assertEqual(result["state"], "failed")
        gap = next(gap for gap in result.get("gaps", ()) if gap["kind"] == "jdk_unsupported")
        self.assertEqual(gap["path"], ".")
        for said in ("Java 11", f"lib/build.gradle.kts{field}", "scip-java", "17", "Gradle"):
            self.assertIn(said, gap["detail"])
        self.play_success()
        newer = [{"tool": "java", "version": "21", "declared_in": f"lib/build.gradle.kts{field}"}]
        self.assertNotIn("gaps", self.index(tools={"": ["gradle"]}, toolchains=newer))

    def test_an_index_of_the_edited_pom_is_a_declared_second_attempt(self):
        """The build as declared gives no index (javapoet's Error Prone 2.3.1 on JDK 17); the second build, with
        the root pom's compiler plugin edited, gives one: the result names what was removed and why the build as
        declared gave none."""
        removed = ["<compilerId>javac-with-errorprone</compilerId>",
                   "<forceJavacCompilerUse>true</forceJavacCompilerUse>"]
        failure = ("[INFO] BUILD FAILURE\n[ERROR] /work/src/main/java/fx/Shapes.java:[18,15] cannot access "
                   "java.io.IOException\n[ERROR]   bad class file: /modules/java.base/java/io/IOException.class\n"
                   "[ERROR]     class file has wrong version 61.0, should be 53.0")
        self.play_success()
        self.play("prepare", files={f"{jvm.KEPT.lstrip('/')}/index.scip": self.fixture / "index.scip"},
                  text=log(("index", 1, failure), ("plain-javac", 0, "DAODAN_PATCHED " + json.dumps(removed)),
                           ("index", 0, "[INFO] BUILD SUCCESS")))
        result = self.index(tools={"": ["maven"]})
        self.assertTrue(result["indexes"])
        gap = next(gap for gap in result.get("gaps", ()) if gap["kind"] == "build_edited")
        self.assertEqual(gap["path"], ".")
        for said in (*removed, "class file has wrong version 61.0, should be 53.0"):
            self.assertIn(said, gap["detail"])

    def test_a_pom_level_the_image_s_javac_does_not_compile_is_raised_in_the_second_attempt(self):
        """javac 17 compiles no level under 7: a pom that states Java 5 or 6 gives no index as declared; the
        second build, of the poms with those levels raised to 8, gives one, and the result names each level
        raised and the level the build states, not the JDK the observer runs it on."""
        raised = ["pom.xml: <source>1.6</source> -> 8",
                  "core/pom.xml: <maven.compiler.target>1.5</maven.compiler.target> -> 8"]
        failure = "[ERROR] Source option 6 is no longer supported. Use 7 or later."
        self.play_success()
        self.play("prepare", files={f"{jvm.KEPT.lstrip('/')}/index.scip": self.fixture / "index.scip"},
                  text=log(("index", 1, failure),
                           ("plain-javac", 0, "\n".join("DAODAN_RAISED " + json.dumps(item) for item in raised)),
                           ("index", 0, "[INFO] BUILD SUCCESS")))
        stated = [{"tool": "java", "version": "1.6", "declared_in": "pom.xml#maven-compiler-plugin.source"}]
        result = self.index(tools={"": ["maven"]}, toolchains=stated)
        self.assertTrue(result["indexes"])
        gaps = {gap["kind"]: gap["detail"] for gap in result["gaps"]}
        for said in (*raised, "Source option 6 is no longer supported"):
            self.assertIn(said, gaps["build_edited"])
        self.assertNotIn("compiler plugin's", gaps["build_edited"])  # nothing was removed from it
        self.assertIn("the build states Java 6 ", gaps["jdk_unsupported"])
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertNotIn("export DAODAN_RAISE=", script)  # Maven's second attempt edits the poms it reads

    def test_a_gradle_toolchain_scip_java_does_not_load_on_is_replaced_in_the_second_attempt(self):
        """scip-java's compiler plugin loads on no javac under 17: a Gradle build whose scripts state an older
        Java gets a second build with an init script, which replaces the toolchain by the JDK the build runs
        on and says so in Gradle's own output; a build that states none gets no second build."""
        said = 'DAODAN_RAISED "project :app: Java toolchain 8 -> 17"'
        self.serve_mise()  # the preparation installs JDK 8 for Gradle to find, as the build asks
        self.play_success()
        self.play("prepare", files={f"{jvm.KEPT.lstrip('/')}/index.scip": self.fixture / "index.scip"},
                  text=log(("index", 1, "> Compilation failed; see the compiler output below."),
                           ("index", 0, f"> Configure project :app\n{said}\n{said}\nBUILD SUCCESSFUL")))
        field = "build.gradle#java."
        stated = [{"tool": "java", "version": "8", "declared_in": f"app/{field}toolchain.languageVersion"},
                  {"tool": "java", "version": "1.6", "declared_in": f"lib/{field}sourceCompatibility"}]
        result = self.index(tools={"": ["gradle"]}, toolchains=stated)
        script = (self.state / "scripts/prepare.sh").read_text(encoding="utf-8")
        self.assertIn("export DAODAN_RAISE=all\n", script)
        self.assertIn("install java@8", script)
        self.assertNotIn("install java@6", script)  # a level names no JDK to find, and none that old is built
        self.assertTrue(result["indexes"])
        gap = next(gap for gap in result["gaps"] if gap["kind"] == "build_edited")
        self.assertEqual(gap["detail"].count("project :app: Java toolchain 8 -> 17"), 1)
        self.assertIn("Compilation failed", gap["detail"])
        self.play_success()
        newer = [{"tool": "java", "version": "21", "declared_in": "build.gradle#java.toolchain.languageVersion"}]
        self.index(tools={"": ["gradle"]}, toolchains=newer)
        self.assertNotIn("export DAODAN_RAISE=", (self.state / "scripts/prepare.sh").read_text(encoding="utf-8"))


class KotlinContainerTests(PreparationTests, EachBuildTests, FakeEngineTest):
    language = "kotlin"

    def test_a_gradle_build_whose_java_task_does_not_load_the_plugin_is_built_once_more(self):
        """A Kotlin build with Java beside it on a toolchain under 17: the Java compile task fails as declared and
        no index is written; the second build, with the toolchain replaced, writes it, and the result says the
        edit, not a failed build."""
        said = 'DAODAN_RAISED "the root project: Java toolchain 8 -> 17"'
        self.serve_mise()
        self.play_success()
        self.play("prepare", files={f"{jvm.KEPT.lstrip('/')}/index.scip": self.fixture / "index.scip"},
                  text=log(("index", 1, "> Compilation failed; see the compiler output below."), ("index", 0, said)))
        stated = [{"tool": "java", "version": "8", "declared_in": "build.gradle.kts#kotlin.jvmToolchain"}]
        result = self.index(toolchains=stated)
        self.assertTrue(result["indexes"])
        self.assertEqual([gap["kind"] for gap in result["gaps"]], ["build_edited"])
        self.assertIn("the root project: Java toolchain 8 -> 17", result["gaps"][0]["detail"])
        self.assertIn("export DAODAN_RAISE=all\n", (self.state / "scripts/prepare.sh").read_text(encoding="utf-8"))

    def test_kotlin_only_in_the_build_s_own_scripts_starts_no_build(self):
        """Gradle scripts and buildSrc are the build's definition, which the pre-map reads through Gradle: no
        Kotlin compile task compiles them, so with no other Kotlin file nothing is built, and the state says why."""
        self.assertEqual(kotlin.READS, (".kt", ".kts"))
        result = self.index(files=["build.gradle.kts", "settings.gradle.kts", "libs/money/build.gradle.kts",
                                   "buildSrc/src/main/kotlin/inventory.java-conventions.gradle.kts",
                                   "tools/buildSrc/src/main/kotlin/Versions.kt"])
        self.assertEqual(result["state"], "unavailable")
        self.assertIn("build's own Kotlin", result["reason"])
        self.assertEqual(self.created(), [])
        self.play_success()
        self.assertTrue(self.index(files=["build.gradle.kts", "src/main/kotlin/fx/A.kt"])["indexes"])

    def test_gradle_reaches_only_the_jvm_registries(self):
        JavaContainerTests.test_preparation_reaches_only_the_registries_and_execution_no_network(self)

    def test_outputs_come_back_and_the_contract_is_returned(self):
        self.play_success()
        before = tree_digest(self.project)
        result = self.index()
        self.assertEqual(tree_digest(self.project), before)
        forward = self.work.resolve() / "build-0" / "index-forward.scip"
        self.assertEqual(result["indexes"], [[str(forward), ""]])
        self.assertEqual(result["written"], [[str(self.work.resolve() / "build-0" / "scip-java-0.scip"), ""]])
        (configs, prefix), = result["configs"]
        self.assertEqual(prefix, "")
        self.assertEqual(sorted(path.name for path in Path(configs).iterdir()),
                         sorted(path.name for path in (self.fixture / "kotlin-configs").iterdir()))
        index_run = result["runs"][0]
        self.assertEqual((index_run["step"], index_run["reverse_relationships_dropped"], index_run["index"]),
                         ("index", 0, str(forward)))
        self.assertEqual(self.created()[0].count("dl.google.com"), 1)
        execute = (self.state / "scripts/execute.sh").read_text(encoding="utf-8")
        self.assertIn("kotlin-configs", execute)

    def test_the_gradle_wrapper_distribution_comes_with_the_checksum_gradle_publishes(self):
        url = f"{jvm.GRADLE_SITE}gradle-7.test-bin.zip"
        self.served.update({url: b"the wrapper's gradle", url + ".sha256": digest(b"the wrapper's gradle").encode()})
        self.wrapper("gradle/wrapper/gradle-wrapper.properties", url.replace(":", "\\:"))
        self.play_success()
        result = self.index()
        self.assertTrue(result["indexes"], result)
        self.assertEqual((self.arrived() / jvm.TOOLS.lstrip("/") / "gradle-7.test-bin.zip").read_bytes(),
                         b"the wrapper's gradle")
        self.assertNotIn(GRADLE_URL, self.asked)

    def test_a_build_without_an_index_is_failed(self):
        self.play("prepare", text=log(("index", 1, "FAILURE: Build failed with an exception.")), code=1)
        result = self.index()
        self.assertEqual(result["state"], "failed")
        self.assertIn("Build failed with an exception", result["reason"])


    def test_the_contract_feeds_the_graph_and_its_expected_ends_hold(self):
        self.play_success()
        check_fixture(self, self.language, self.index())


def check_fixture(test: unittest.TestCase, name: str, result: dict) -> None:
    """The fixture rebuilt from the contract's index (and compile tasks): every case of its `expected.json`."""
    scratch = Path(tempfile.mkdtemp(prefix="daodan-jvm-graph-"))
    test.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
    source = scratch / name
    shutil.copytree(FIXTURES / name, source)
    (path, prefix), = result["indexes"]
    test.assertEqual(prefix, "")
    shutil.copyfile(path, source / "index.scip")
    if name == "kotlin":
        shutil.rmtree(source / "kotlin-configs")
        (configs, _prefix), = result["configs"]
        shutil.copytree(configs, source / "kotlin-configs")
    manifest = scratch / "manifest.sqlite"
    done = subprocess.run([sys.executable, "-I", "snapshot.py", "write", str(source), "--out", str(manifest),
                           "--no-engine", "--no-index", "--no-modules"], cwd=SCRIPTS, capture_output=True, text=True,
                          timeout=300)
    test.assertEqual(done.returncode, 0, done.stderr)
    built = {name: graph_tests._built(name, source, manifest)}
    for case in sorted(graph_tests.CASES[name]):
        if (name, case) in graph_tests.KNOWN:
            continue
        with test.subTest(case=case):
            graph_tests.test_fixture_case(built, name, case)


SMOKE = os.environ.get("DAODAN_JVM_SMOKE") == "1"
HOST_MEMORY = 2 * 2**30  # free memory the host keeps beside a container at its limit
HOST_DISK = 3 * 2**30  # free on the system disk after the run
ADDED_AT_MOST = 2 * 2**30  # the image (0.4 GB), the proxy image, the tools, the layer the engine keeps
MEMORY = {"java": 2 * 2**30, "kotlin": 4 * 2**30}  # the container's limit for each fixture


def free_commit() -> int | None:
    """Bytes the system can still commit (Windows), or None."""
    if os.name != "nt":
        return None
    import ctypes

    class Status(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                    ("available", ctypes.c_ulonglong), ("page_total", ctypes.c_ulonglong),
                    ("page_free", ctypes.c_ulonglong), ("virtual_total", ctypes.c_ulonglong),
                    ("virtual_free", ctypes.c_ulonglong), ("extended", ctypes.c_ulonglong)]

    status = Status()
    status.length = ctypes.sizeof(Status)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return status.page_free


def engine_state(engine) -> dict:
    """What the engine holds, for the report: its images, its containers and its disk use."""
    def listed(*args: str) -> list[str]:
        return [line for line in container.cli(engine, *args).stdout.decode("utf-8", "replace").split("\n") if line]
    return {"images": listed("image", "ls", "--format", "{{.Repository}}@{{.ID}} {{.Size}}"),
            "containers": listed("ps", "-a", "--format", "{{.Names}}"),
            "df": listed("system", "df", "--format", "{{.Type}} {{.Size}} {{.Reclaimable}}")}


@unittest.skipUnless(SMOKE, "set DAODAN_JVM_SMOKE=1 to index the fixtures in a real container")
class RealContainerSmokeTest(unittest.TestCase):
    def test_java_fixture_in_one_container(self):
        self.index_fixture("java")

    def test_java_fixture_with_a_maven_wrapper_made_on_windows(self):
        """The wrapper as a Windows checkout leaves it: CRLF and no executable bit on disk, `.mvn/` tracked by Git.
        Run as written it would fail; the build passes only if the container calls the Maven Daodan brought."""
        self.index_fixture("java", wrapper=True)

    def test_kotlin_fixture_in_one_container(self):
        """No wrapper: the Gradle Daodan pins, downloaded and checked on the host, builds the fixture."""
        self.index_fixture("kotlin")

    def test_a_wrapper_naming_another_site_starts_no_container(self):
        engine = self.engine()
        held = engine_state(engine)
        scratch = Path(tempfile.mkdtemp(prefix="daodan-jvm-smoke-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        project = self.fixture(scratch, "kotlin")
        (project / "gradle/wrapper").mkdir(parents=True)
        (project / "gradle/wrapper/gradle-wrapper.properties").write_text(
            "distributionUrl=https\\://downloads.example.com/gradle-9.9.1-bin.zip\n", encoding="utf-8")
        asked = []
        real_open = resolve_edges.open_url

        def spy(url, timeout):
            asked.append(url)
            return real_open(url, timeout)

        with mock.patch.object(resolve_edges, "open_url", spy), mock.patch.object(engine_tools, "open_url", spy):
            result = kotlin.index(project, scratch / "work", roots={""}, engine=engine, memory=MEMORY["kotlin"])
        print(json.dumps({"state": result.get("state"), "reason": result.get("reason"), "asked": asked}, indent=1))
        self.assertEqual(result["state"], "unavailable")
        self.assertIn("downloads.example.com", result["reason"])
        self.assertFalse(any("example.com" in url for url in asked))
        self.assertEqual(engine_state(engine)["containers"], held["containers"])

    def engine(self):
        try:
            return container.find_engine()
        except container.Gap as gap:
            self.skipTest(f"no engine: {gap.cause}")

    @staticmethod
    def fixture(scratch: Path, language: str) -> Path:
        project = scratch / "project" / language
        shutil.copytree(FIXTURES / language, project, ignore=lambda folder, names: [
            name for name in names if name in OWN or name == "kotlin-configs"])
        return project

    def index_fixture(self, language: str, *, wrapper: bool = False):
        from test_codebase_map_container import user_settings
        memory = MEMORY[language]
        free, commit = container.free_memory(), free_commit()
        if free is not None and free < memory + HOST_MEMORY or commit is not None and commit < memory + HOST_MEMORY:
            self.skipTest(f"{(free or 0) / 2**30:.1f} GB physical and {(commit or 0) / 2**30:.1f} GB commit free, "
                          f"under the container's {memory / 2**30:.0f} GB plus {HOST_MEMORY / 2**30:.0f} GB")
        system = Path(os.environ.get("SystemDrive", "C:") + "\\") if os.name == "nt" else Path("/")
        disk = shutil.disk_usage(system).free
        if disk - ADDED_AT_MOST < HOST_DISK:
            self.skipTest(f"{disk / 2**30:.1f} GB free on {system}: the run could leave under 3 GB")
        before = user_settings()
        engine = self.engine()
        held = engine_state(engine)
        scratch = Path(tempfile.mkdtemp(prefix="daodan-jvm-smoke-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        project = self.fixture(scratch, language)
        if wrapper:
            url = f"{jvm.MAVEN_SITE}{jvm.MAVEN[0]}/apache-maven-{jvm.MAVEN[0]}-bin.zip"
            (project / ".mvn/wrapper").mkdir(parents=True)
            (project / ".mvn/wrapper/maven-wrapper.properties").write_bytes(
                f"distributionUrl={url}\r\ndistributionSha256Sum={jvm.MAVEN[1]}\r\n".encode())
            (project / "mvnw").write_bytes(b"#!/bin/sh\r\necho 'the project wrapper ran' >&2\r\nexit 3\r\n")
            git = shutil.which("git")
            if not git:
                self.skipTest("git is needed for a tracked `.mvn/`")
            for args in (["init", "-q"], ["add", "."]):
                subprocess.run([git, "-C", str(project), *args], check=True, capture_output=True)
        module = java if language == "java" else kotlin
        given = module.structure(pre_map(project, scratch / "snapshot"))  # what the stage hands the indexer
        self.assertEqual(given["roots"], {""})  # with the toolchains the pre-map states, for the preparation
        before_project = tree_digest(project)
        started = time.monotonic()
        result = module.index(project, scratch / "work", engine=engine, memory=memory, **given)
        after, engine_after = user_settings(), engine_state(engine)
        build = scratch / "work" / "build-0"
        records = [json.loads(row) for row in (build / "container" / container.RECORD_NAME).read_text(
            encoding="utf-8").splitlines()]
        tools = {name: str(path) for name, path in jvm.tools(project).items() if name.startswith(jvm.TOOLS)}
        print(json.dumps({"engine": engine.name, "language": language, "wrapper": wrapper,
                          "seconds": round(time.monotonic() - started, 1), "indexer": result["indexer"],
                          "state": result.get("state"), "reason": result.get("reason"),
                          "runs": [{key: run.get(key) for key in ("phase", "step", "returncode", "seconds", "peak_mb")}
                                   for run in result["runs"]],
                          "copies": [record.get("copy") for record in records],
                          "tools": {name: [path, jvm.sha256(Path(path))] for name, path in tools.items()},
                          "engine before": held, "engine after": engine_after,
                          "system disk free GB": [round(disk / 2**30, 2),
                                                  round(shutil.disk_usage(system).free / 2**30, 2)],
                          "settings unchanged": after == before}, indent=1))
        prepared = ""
        for phase in ("prepare", "execute"):
            log = build / "container" / f"{phase}.log"
            if log.is_file():
                text = log.read_text(encoding="utf-8", errors="replace")
                prepared = text if phase == "prepare" else prepared
                print(f"--- {phase}.log tail\n" + "\n".join(text.splitlines()[-40:]))
        self.assertTrue(result["indexes"], result.get("reason"))
        self.assertEqual(tree_digest(project), before_project)
        self.assertEqual(after, before)
        self.assertEqual(engine_after, held)  # no image, layer, volume or container left by the run
        self.assertEqual([(record["phase"], record["network"] == "none") for record in records],
                         [("prepare", False), ("execute", True)])
        self.assertNotRegex(prepared, r"Downloading https://services\.gradle\.org|apache-maven/[\d.]+/apache-maven")
        if wrapper:
            self.assertNotIn("the project wrapper ran", prepared)
            files = [path for path in project.rglob("*") if path.is_file() and ".git" not in path.parts]
            self.assertEqual(records[0]["copy"]["files"], len(files))  # `.mvn/` included: Git tracks it
        check_fixture(self, language, result)


if __name__ == "__main__":
    unittest.main()


def test_a_maven_build_gets_its_kotlin_from_the_analysis_indexer():
    """scip-java indexes Kotlin only under Gradle (its getting-started table: Maven, Kotlin no). Under Maven the
    preparation runs the Kotlin Analysis API indexer scip-java ships on each module's Kotlin files, with the
    module's classpath, into the build's targetroot, writes the compile task `tasks` reads, and aggregates."""
    maven, gradle = kotlin.PREPARE.split("\nelse\n")
    condition = maven.split("; then\n", 1)[0]
    assert "pom.xml" in condition and "build.gradle" in condition and "DAODAN_TOOL" in condition
    assert 'maven_kotlin "$OUT/kotlin-configs"' in maven and 'aggregate --output "$OUT/index.scip"' in maven
    for needed in ("dependency:build-classpath", "org.scip_code.scip_java.kotlin_analysis.MainKt",
                   '--targetroot "$targetroot"', '"$configs/maven-$name.txt"'):
        assert needed in jvm.MAVEN_KOTLIN, needed
    assert "maven_kotlin" not in gradle and "scip_index" in gradle


BASH = shutil.which("bash") if os.name != "nt" else None


def _phase(tmp_path: Path, body: str, tool: str, index_code: int, files=("pom.xml", "build.gradle.kts")):
    """`body` run by bash in a folder holding `files`, with the head's names stubbed: what it hands scip-java,
    `java` and `maven_kotlin` is recorded; scip-java exits `index_code`, writing an index when it succeeds."""
    work, out, calls = tmp_path / "work", tmp_path / "out", tmp_path / "calls"
    work.mkdir(parents=True)
    out.mkdir()
    for name in files:
        (work / name).write_text("", encoding="utf-8")
    scip = tmp_path / "scip-java"
    scip.write_text(f'#!/bin/sh\necho "scip-java $*" >> {calls}\n'
                    + (f'echo index > "{out}/index.scip"\n' if not index_code else "") + f"exit {index_code}\n",
                    encoding="utf-8")
    scip.chmod(0o755)
    head = (f"DAODAN_TOOL={tool}\nOUT={out}\nWORK={work}\nSCIP_JAVA={scip}\nstep() {{ shift; \"$@\"; }}\n{jvm.SCIP_INDEX}"
            f"java() {{ echo java >> {calls}; return 1; }}\nmaven_kotlin() {{ echo maven_kotlin >> {calls}; }}\n")
    code = subprocess.run([BASH, "-c", head + body], cwd=work).returncode
    return code, calls.read_text(encoding="utf-8").replace(str(out), "$OUT").splitlines() if calls.is_file() else []


@unittest.skipUnless(BASH, "the phase scripts are bash, run in the Linux container")
def test_each_build_tool_of_a_folder_runs_only_its_own_steps(tmp_path):
    """In a folder Gradle and Maven both build, scip-java runs the build it is told; only Maven's patches the
    root pom's compiler plugin when it gives no index, and only Maven's indexes the modules' Kotlin itself."""
    flag = "--build-tool={}"
    assert _phase(tmp_path / "1", java.PREPARE, "gradle", 1) == (
        1, [f"scip-java index --output $OUT/index.scip {flag.format('gradle')}"])
    assert _phase(tmp_path / "2", java.PREPARE, "maven", 1) == (
        1, [f"scip-java index --output $OUT/index.scip {flag.format('maven')}", "java"])
    assert _phase(tmp_path / "3", java.PREPARE, "gradle", 0)[1] == [
        f"scip-java index --output $OUT/index.scip {flag.format('gradle')}"]
    assert "maven_kotlin" in _phase(tmp_path / "4", java.PREPARE, "maven", 0)[1]
    assert _phase(tmp_path / "5", kotlin.PREPARE, "gradle", 0)[1] == [
        f"scip-java index --output $OUT/index.scip {flag.format('gradle')}"]
    assert "maven_kotlin" in _phase(tmp_path / "6", kotlin.PREPARE, "maven", 0)[1]
    assert "maven_kotlin" in _phase(tmp_path / "7", kotlin.PREPARE, "", 0, files=("pom.xml",))[1]  # as before


@unittest.skipUnless(BASH, "the phase scripts are bash, run in the Linux container")
def test_an_android_gradle_build_also_compiles_its_debug_variants(tmp_path):
    """scip-java's Gradle plugin puts no Android task in scipCompileAll (it attaches its javac plugin to every
    JavaCompile task of an Android project and dumps every KotlinCompile's configuration): with the Android SDK
    of the preparation, the build also runs each project's debug variant compiles, main and unit tests."""
    android = (f"scip-java index --output $OUT/index.scip --build-tool=gradle -- clean scipPrintDependencies "
               f"scipCompileAll --init-script {jvm.ANDROID_INIT} daodanAndroidCompile")
    for module in (java, kotlin):
        assert _phase(tmp_path / module.__name__ / "android", "ANDROID_HOME=/sdk\n" + module.PREPARE, "gradle", 0,
                      files=("build.gradle.kts",))[1] == [android]
        assert _phase(tmp_path / module.__name__ / "plain", module.PREPARE, "gradle", 0,
                      files=("build.gradle.kts",))[1] == [
            "scip-java index --output $OUT/index.scip --build-tool=gradle"]
    script = Path(jvm.ANDROID_INIT).read_text(encoding="utf-8")
    assert "daodanAndroidCompile" in script and r"compile\w*Debug(UnitTest)?Sources" in script


@unittest.skipUnless(BASH, "the phase scripts are bash, run in the Linux container")
def test_the_head_works_in_the_build_s_folder_of_the_checkout(tmp_path):
    work = tmp_path / "checkout"
    (work / "src/fraud").mkdir(parents=True)
    head = jvm.HEAD[jvm.HEAD.index("WORK="):jvm.HEAD.index("step() {")]
    ran = subprocess.run([BASH, "-c", f"PHASE_OUT={tmp_path / 'out'}\nHOME={tmp_path}\nDAODAN_WORK={work}\n"
                          f"DAODAN_ROOT=src/fraud\n{head.replace('/app/scip-java/bin', str(tmp_path / 'bin'))}"
                          'echo "$WORK $PWD"\n'], capture_output=True, text=True)
    assert ran.stdout.split() == [str(work / "src/fraud")] * 2, ran.stderr


@unittest.skipUnless(BASH, "the phase scripts are bash, run in the Linux container")
def test_the_head_takes_the_jdk_it_picked_as_that_jdk_names_itself(tmp_path):
    """JDK 8 says `1.8.0_N` where a later one says `N`: the head's check takes both for the JDK it picked."""
    check = jvm.HEAD[jvm.HEAD.index('if ! "$JAVA_HOME/bin/java"'):]
    check = check[:check.index("\nfi\n") + 4]
    java = tmp_path / "bin" / "java"
    java.parent.mkdir()
    for said, jdk, code in (('openjdk version "1.8.0_472"', 8, 0), ('openjdk version "17.0.21" 2026-10-21', 17, 0),
                            ('openjdk version "1.8.0_472"', 17, 70), ('openjdk version "11.0.2"', 1, 70)):
        java.write_text(f"#!/bin/sh\necho '{said}' >&2\n", encoding="utf-8")
        java.chmod(0o755)
        ran = subprocess.run([BASH, "-c", f'JAVA_HOME={tmp_path}\nJDK={jdk}\nstep() {{ shift; "$@"; }}\n{check}'],
                             capture_output=True)
        assert ran.returncode == code, (said, jdk, ran.stdout)


@unittest.skipUnless(BASH, "the phase scripts are bash, run in the Linux container")
def test_the_head_runs_on_the_jdk_it_was_given_and_hands_gradle_every_jdk_there(tmp_path):
    """Of the JDKs the preparation installed, the build runs on the one it was given (`DAODAN_JDK`); Gradle finds
    a toolchain among all of them and the image's (`org.gradle.java.installations.paths`) and downloads none."""
    tools, home = tmp_path / "tools", tmp_path / "home"
    for name, said in (("11.0.29+7", "11.0.29"), ("21.0.9+10", "21.0.9"), ("8.0.512+9", "1.8.0_512")):
        java = tools / "mise/installs/java" / name / "bin/java"
        java.parent.mkdir(parents=True)
        java.write_text(f"#!/bin/sh\necho 'openjdk version \"{said}\"' >&2\n", encoding="utf-8")
        java.chmod(0o755)
    head = jvm.HEAD[jvm.HEAD.index("JDK=17\n"):jvm.HEAD.index("# The options scip-java")]
    gradle = jvm.HEAD[jvm.HEAD.index('export GRADLE_USER_HOME'):]
    script = (f"DAODAN_JDK=21\nHOME={home}\nstep() {{ shift; \"$@\"; }}\n{head}{gradle}"
              'echo "$JAVA_HOME $JDK"\n').replace("/daodan/state/tools", str(tools))
    ran = subprocess.run([BASH, "-c", script], capture_output=True, text=True, env={"PATH": os.environ["PATH"],
                                                                                     "JAVA_HOME": str(tools / "x")})
    installs = tools / "mise/installs/java"
    assert ran.stdout.split()[-2:] == [str(installs / "21.0.9+10"), "21"], ran.stdout + ran.stderr
    written = jvm.properties(home / ".gradle/gradle.properties")
    assert written["org.gradle.java.installations.paths"].split(",") == [
        "/opt/java/openjdk", *(str(installs / name) for name in ("11.0.29+7", "21.0.9+10", "8.0.512+9"))]
    assert written["org.gradle.java.installations.auto-download"] == "false"


@unittest.skipUnless(BASH, "the phase scripts are bash, run in the Linux container")
def test_a_root_only_settings_gradle_kts_declares_gets_the_wrapper_scip_java_looks_for(tmp_path):
    """scip-java finds a Gradle build by settings.gradle, gradlew, build.gradle or build.gradle.kts, never by
    settings.gradle.kts alone (a composite build's root): there the preparation writes the wrapper, which only
    calls the Gradle Daodan brought."""
    tools, work = tmp_path / "tools", tmp_path / "work"
    gradle = tools / "gradle-0.test" / "gradle-0.test" / "bin" / "gradle"
    gradle.parent.mkdir(parents=True)
    gradle.write_text("#!/bin/sh\n", encoding="utf-8")
    work.mkdir()
    (work / "settings.gradle.kts").write_text('rootProject.name = "x"\n', encoding="utf-8")
    loop = jvm.PREPARE[jvm.PREPARE.index("for tool in"):jvm.PREPARE.index("export PATH")]
    subprocess.run([BASH, "-c", loop.replace("/daodan/state/tools", str(tools))], cwd=work, check=True)
    assert f'exec {gradle} "$@"' in (work / "gradlew").read_text(encoding="utf-8")
    assert os.access(work / "gradlew", os.X_OK)


def test_a_kotlin_file_no_compile_task_lists_says_so_for_any_build():
    reasons = kotlin.missing(None, ["src/main/kotlin/a/A.kt", "build.gradle.kts", "buildSrc/src/main/kotlin/B.kt"])
    assert reasons["src/main/kotlin/a/A.kt"] == "no Kotlin compile task of the build lists it"
    assert "Gradle script" in reasons["build.gradle.kts"] and "buildSrc" in reasons["buildSrc/src/main/kotlin/B.kt"]


def test_under_maven_the_kotlin_files_are_those_in_the_source_folders_the_pre_map_states():
    """What Maven compiles comes from Maven's own model, through the pre-map: the analyzer looks for no folder."""
    record = {"units": [
        {"kind": "maven-module", "root": ".", "name": "g:shop", "source_roots": []},
        {"kind": "maven-module", "root": "core", "name": "g:core", "source_roots": ["core/src/main/kotlin", "core/src/main/java"]},
        {"kind": "gradle-project", "root": "tools/gen", "name": "gen", "source_roots": ["tools/gen/src"]}], "workspace": []}
    given = kotlin.structure(record)
    assert given["modules"] == [["", []], ["core", ["core/src/main/kotlin", "core/src/main/java"]]]
    script = jvm.modules_line(given["modules"], "") + jvm.MAVEN_KOTLIN
    assert "DAODAN_MODULES='.\t\ncore\tcore/src/main/kotlin:core/src/main/java'\n" in script
    assert "find \"$WORK\" -name pom.xml" not in script and '"$WORK/$root"' in script
    nested = jvm.modules_line([["svc/api", ["svc/api/src/main/kotlin"]], ["other", ["other/src"]]], "svc")
    assert "DAODAN_MODULES='api\tapi/src/main/kotlin'\n" in nested  # relative to the build's folder, its own modules


def test_java_execution_reads_the_targetroot_and_the_classes_of_the_build_that_ran():
    """Maven writes under `target/`, Gradle under `build/`: the forward aggregation and `javap` read whichever
    the build made, in every module."""
    assert "target/scip-targetroot" in java.EXECUTE and "build/scip-targetroot" in java.EXECUTE
    assert "*/target/*classes/*" in java.EXECUTE and "*/build/classes/*" in java.EXECUTE


def test_without_an_equal_forward_index_the_contract_declares_the_inverse_implementations(tmp_path):
    """The default index writes each implementation both ways: read without its forward copy, a call on a
    method also reaches its parent and siblings. That is a gap of the contract, never silent."""
    out, work = tmp_path / "out", tmp_path / "work"
    out.mkdir()
    work.mkdir()
    (out / "index.scip").write_bytes(b"x")
    part = java.finish(tmp_path, work, {"state": "done"}, [{"step": "aggregate", "returncode": 1, "seconds": 1.0}], out)
    assert part["indexes"] == [[str(work / "index.scip"), ""]]
    [gap] = part["gaps"]
    assert gap["kind"] == "implementations_both_ways" and "aggregate" in gap["detail"]


def test_under_maven_the_java_index_also_holds_the_kotlin_of_its_modules():
    """A Java call to a Kotlin member ends where the same index defines it: Java's build indexes the modules'
    Kotlin as Kotlin's does (`jvm.MAVEN_KOTLIN`), from the same source folders of the pre-map."""
    record = {"units": [{"kind": "maven-module", "root": ".", "name": "g:a", "source_roots": ["src/main/kotlin"]}],
              "workspace": []}
    assert java.structure(record)["modules"] == kotlin.structure(record)["modules"] == [["", ["src/main/kotlin"]]]
    assert "maven_kotlin() {" in jvm.PREPARE and "kotlin_analysis.MainKt" in jvm.MAVEN_KOTLIN
    assert "maven_kotlin " in java.PREPARE and "maven_kotlin " in kotlin.PREPARE
    assert jvm.modules_line([["svc/api", ["svc/api/src/main/kotlin"]], ["other", ["other/src"]]], "svc") == (
        "DAODAN_MODULES='api\tapi/src/main/kotlin'\n")


def test_a_jvm_build_daodan_does_not_run_is_named_in_the_reason():
    record = {"units": [{"kind": "sbt-project", "root": ".", "name": "app"},
                        {"kind": "bazel-target", "root": "tools", "name": "//tools:gen"}], "workspace": []}
    given = java.structure(record)
    assert given["other_builds"] == ["bazel-target", "sbt-project"]
    result = java.index(Path("."), Path(tempfile.mkdtemp(prefix="daodan-jvm-none-")), **given)
    assert result["state"] == "unavailable"
    assert "sbt" in result["reason"] and "bazel" in result["reason"] and "Gradle and Maven" in result["reason"]


def test_a_kotlin_index_from_a_build_that_ended_in_error_says_so(tmp_path):
    out, work = tmp_path / "out", tmp_path / "work"
    out.mkdir()
    work.mkdir()
    (out / "index.scip").write_bytes(b"")
    runs = [{"step": "index", "returncode": 1, "seconds": 1.0, "stderr_tail": "FAILURE: Build failed with an exception."}]
    part = kotlin.finish(work, {"state": "done"}, runs, out)
    [gap] = part["gaps"]
    assert gap["kind"] == "build_failed" and "Build failed" in gap["detail"]
