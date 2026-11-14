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
import resolve_edges  # noqa: E402
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
                        mock.patch("resolve_edges.time.sleep")):
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
        out = jvm.OUT.lstrip("/")
        self.play("prepare", files={f"{out}/index.scip": self.fixture / "index.scip"},
                  text=log(("index", 0, "[INFO] BUILD SUCCESS")))
        if self.language == "java":
            self.play("execute", files={f"{out}/index-forward.scip": self.fixture / "index.scip",
                                        f"{out}/javap/project.txt": JAVAP},
                      text=log(("aggregate", 0, "done"), ("javap-project", 0, ""), peak=2**28))
        else:
            self.play("execute", files={f"{out}/kotlin-configs": self.fixture / "kotlin-configs"},
                      text=log(("configs", 0, ""), peak=2**28))

    def index(self, **options) -> dict:
        module = java if self.language == "java" else kotlin
        options.setdefault("engine", self.engine)
        with mock.patch.object(container, "free_memory", return_value=64 * 2**30), \
                mock.patch("subprocess.Popen", Recorder):
            return module.index(self.project, self.work, **options)

    def calls(self) -> list[list[str]]:
        path = self.state / "calls.jsonl"
        return [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def created(self) -> list[list[str]]:
        return [call for call in self.calls() if call[0] == "create"]


class JavaContainerTests(FakeEngineTest):
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

    def test_preparation_reaches_only_the_registries_and_execution_no_network(self):
        self.play_success()
        self.index()
        proxy, prepare, execute = self.created()
        self.assertEqual(proxy[proxy.index(str(container.PROXY_PORT)) + 1:], list(jvm.registries()))
        for host in ("repo.maven.apache.org", "plugins.gradle.org", "plugins-artifacts.gradle.org"):
            self.assertIn(host, proxy)
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
        committed = [call for call in self.calls() if call[0] == "commit"][0][2]
        self.assertIn(committed, execute)

    def test_the_project_is_not_changed(self):
        before = tree_digest(self.project)
        self.play_success()
        self.index()
        self.assertEqual(tree_digest(self.project), before)

    def test_outputs_come_back_and_the_contract_is_returned(self):
        self.play_success()
        result = self.index()
        self.assertNotIn("state", result)
        self.assertEqual(result["indexes"], [[str(self.work.resolve() / "index-forward.scip"), ""]])
        self.assertEqual((self.work / "index-forward.scip").read_bytes(), (self.fixture / "index.scip").read_bytes())
        self.assertEqual(result["indexer"], {"name": "scip-java", "version": jvm.VERSION, "seconds": 7.5,
                                             "peak_mb": 1024})
        self.assertEqual([(run["phase"], run["step"], run["returncode"]) for run in result["runs"]],
                         [("prepare", "index", 0), ("execute", "aggregate", 0), ("execute", "javap-project", 0)])
        self.assertTrue(result["runs"][1]["same_occurrences"])
        members = json.loads((self.work / "javap.json").read_text(encoding="utf-8"))
        self.assertEqual(members["fx/Shapes"][0]["flags"], ["ACC_PUBLIC"])
        records = [json.loads(row) for row in (self.work / "container" / container.RECORD_NAME).read_text(
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
            result = java.index(self.project, self.work, engine=self.engine)
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
        self.assertEqual((fs / "app/scip-java/lib/tool-1.0.jar").read_bytes(), JAR)
        self.assertEqual((fs / "daodan/tools/apache-maven-0.test-bin.zip").read_bytes(), MAVEN_ZIP)
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
        self.assertEqual((self.arrived() / "daodan/tools/apache-maven-3.9.test-bin.zip").read_bytes(),
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


class KotlinContainerTests(FakeEngineTest):
    language = "kotlin"

    def test_outputs_come_back_and_the_contract_is_returned(self):
        self.play_success()
        before = tree_digest(self.project)
        result = self.index()
        self.assertEqual(tree_digest(self.project), before)
        forward = self.work.resolve() / "index-forward.scip"
        self.assertEqual(result["indexes"], [[str(forward), ""]])
        self.assertEqual(result["written"], str(self.work.resolve() / "scip-java-0.scip"))
        self.assertEqual(sorted(path.name for path in Path(result["configs"]).iterdir()),
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
        self.assertEqual((self.arrived() / "daodan/tools/gradle-7.test-bin.zip").read_bytes(), b"the wrapper's gradle")
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
        shutil.copytree(result["configs"], source / "kotlin-configs")
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
MIN_PHYSICAL = MIN_COMMIT = 3 * 2**30  # free before the run starts, both
MIN_SYSTEM_DISK = 8 * 2**30  # free on the system disk after the run, whatever the engine and downloads add
ADDED_AT_MOST = 2 * 2**30  # the image (0.4 GB), the proxy image, scip-java, Maven, the prepared image


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
    """What the engine holds, for the report: its images and its disk use."""
    images = container.cli(engine, "image", "ls", "--format", "{{.Repository}}:{{.Tag}}@{{.ID}} {{.Size}}")
    usage = container.cli(engine, "system", "df", "--format", "{{.Type}} {{.Size}} {{.Reclaimable}}")
    return {"images": images.stdout.decode("utf-8", "replace").split("\n"),
            "df": usage.stdout.decode("utf-8", "replace").split("\n")}


@unittest.skipUnless(SMOKE, "set DAODAN_JVM_SMOKE=1 to index the Java fixture in a real container")
class RealContainerSmokeTest(unittest.TestCase):
    def test_java_fixture_in_one_container(self):
        self.index_fixture(wrapper=False)

    def test_java_fixture_with_a_maven_wrapper_made_on_windows(self):
        """The wrapper as a Windows checkout leaves it: CRLF and no executable bit on disk, `.mvn/` tracked by Git.
        Run as written it would fail; the build passes only if the container calls the Maven Daodan brought."""
        self.index_fixture(wrapper=True)

    def index_fixture(self, *, wrapper: bool):
        from test_codebase_map_container import user_settings
        memory = 2 * 2**30
        free, commit = container.free_memory(), free_commit()
        if free is not None and free < MIN_PHYSICAL or commit is not None and commit < MIN_COMMIT:
            self.skipTest(f"{(free or 0) / 2**30:.1f} GB physical and {(commit or 0) / 2**30:.1f} GB commit free, "
                          f"under {MIN_PHYSICAL / 2**30:.0f} GB")
        system = Path(os.environ.get("SystemDrive", "C:") + "\\") if os.name == "nt" else Path("/")
        disk = shutil.disk_usage(system).free
        if disk - ADDED_AT_MOST < MIN_SYSTEM_DISK:
            self.skipTest(f"{disk / 2**30:.1f} GB free on {system}: the run could leave under 8 GB")
        before = user_settings()
        try:
            engine = container.find_engine()
        except container.Gap as gap:
            self.skipTest(f"no engine: {gap.cause}")
        held = engine_state(engine)
        scratch = Path(tempfile.mkdtemp(prefix="daodan-jvm-smoke-"))
        self.addCleanup(shutil.rmtree, scratch, ignore_errors=True)
        project = scratch / "project" / "java"
        shutil.copytree(FIXTURES / "java", project, ignore=lambda folder, names: [n for n in names if n in OWN])
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
        before_project = tree_digest(project)
        started = time.monotonic()
        result = java.index(project, scratch / "work", engine=engine, memory=memory)
        after = user_settings()
        records = [json.loads(row) for row in (scratch / "work" / "container" / container.RECORD_NAME).read_text(
            encoding="utf-8").splitlines()]
        print(json.dumps({"engine": engine.name, "wrapper": wrapper, "seconds": round(time.monotonic() - started, 1),
                          "indexer": result["indexer"], "state": result.get("state"), "reason": result.get("reason"),
                          "runs": [{key: run.get(key) for key in ("phase", "step", "returncode", "seconds", "peak_mb")}
                                   for run in result["runs"]],
                          "copies": [record.get("copy") for record in records],
                          "engine before": held, "engine after": engine_state(engine),
                          "system disk free GB": [round(disk / 2**30, 2),
                                                  round(shutil.disk_usage(system).free / 2**30, 2)],
                          "settings unchanged": after == before}, indent=1))
        prepared = ""
        for phase in ("prepare", "execute"):
            log = scratch / "work" / "container" / f"{phase}.log"
            if log.is_file():
                text = log.read_text(encoding="utf-8", errors="replace")
                prepared = text if phase == "prepare" else prepared
                print(f"--- {phase}.log tail\n" + "\n".join(text.splitlines()[-25:]))
        self.assertTrue(result["indexes"], result.get("reason"))
        self.assertEqual(tree_digest(project), before_project)
        self.assertEqual(after, before)
        self.assertEqual([(record["phase"], record["network"] == "none") for record in records],
                         [("prepare", False), ("execute", True)])
        if wrapper:
            self.assertNotIn("the project wrapper ran", prepared)
            self.assertNotIn("apache-maven/", prepared)  # no build downloaded a distribution
            files = [path for path in project.rglob("*") if path.is_file() and ".git" not in path.parts]
            self.assertEqual(records[0]["copy"]["files"], len(files))  # `.mvn/` included: Git tracks it
        check_fixture(self, "java", result)


if __name__ == "__main__":
    unittest.main()
