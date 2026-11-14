"""The indexer runs of `indexers/{go,rust,typescript,python}.py`, with a fake indexer and fake downloads: no
network, no toolchain, no project code. Every program an `index()` starts is the stand-in `Fake`; every URL is
the stand-in `Web`. The committed indexes of `fixtures/code-graph/` are what the fake indexer writes.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers.py
"""
from __future__ import annotations

import collections
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import zipfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import code_graph  # noqa: E402
import resolve_edges as rx  # noqa: E402
from indexers import go, python, runtime, rust, typescript  # noqa: E402

FIXTURES = HERE / "fixtures/code-graph"
GB = 2**30
MODULES = {"go": go, "rust": rust, "ts": typescript, "python": python}
LANGUAGES = {"go": ("go",), "rust": ("rust",), "ts": ("javascript", "typescript"), "python": ("python",)}
NPM = {"ts": "@sourcegraph/scip-typescript", "python": "@sourcegraph/scip-python"}
MANIFESTS = ("go.mod", "go.sum", "Cargo.toml", "Cargo.lock", "package.json", "tsconfig.json", "pyproject.toml")


class Fake:
    """Every program an `index()` starts. An indexer run (`--output`) writes `index` there (the first run; an
    empty index after) and exits with `code` and `stderr`; each run and `go mod download` also writes where a real tool writes, beside the manifests of
    its working directory; `go install` and `npm install` leave their tool where the install expects it."""

    def __init__(self, index: Path | None = None, code: int = 0, stderr: str = ""):
        self.index, self.code, self.stderr = index, code, stderr
        self.calls: list[tuple[list[str], str | None]] = []
        self.envs: list[dict] = []  # each call's environment, in the order of `calls`

    def __call__(self, command, *args, **kwargs):
        command = [str(part) for part in command]
        if len(command) > 3 and command[0] == sys.executable and command[1] == "-c":
            command = command[3:]  # code_graph.measured's memory probe
        cwd, env = kwargs.get("cwd"), kwargs.get("env") or {}
        self.calls.append((command, str(cwd) if cwd else None))
        self.envs.append(kwargs.get("env"))
        done = subprocess.CompletedProcess(command, 0, "", "")
        if "--version" in command:
            done.stdout = "tool 0.0.0-test\n"
        elif "install" in command and "--prefix" in command:
            package = command[-1].rsplit("@", 1)[0]
            root = Path(command[command.index("--prefix") + 1]) / "node_modules" / package
            root.mkdir(parents=True)
            (root / "package.json").write_text(json.dumps({"bin": {package.rsplit("/", 1)[-1]: "main.js"}}),
                                               encoding="utf-8")
        elif command[1:2] == ["install"] and env.get("GOBIN"):
            Path(env["GOBIN"], rx.executable_name("scip-go")).write_text("fake", encoding="utf-8")
        elif any(part == "--output" or part.startswith("--output=") for part in command):
            at = next(i for i, part in enumerate(command) if part.startswith("--output"))
            output = Path(command[at].split("=", 1)[1] if "=" in command[at] else command[at + 1])
            self._write(cwd)
            if self.code == 0 and self.index is not None:
                # The fixture's index from the first run, an empty one from a nested module's or crate's.
                output.write_bytes(b"" if len(self.runs()) > 1 else self.index.read_bytes())
            done.returncode, done.stderr = self.code, self.stderr
        elif command[1:3] == ["mod", "download"]:
            self._write(cwd)
        return done

    @staticmethod
    def _write(cwd) -> None:
        if cwd is None:
            return
        here = Path(cwd)
        (here / "written-by-the-indexer").write_text("x", encoding="utf-8")
        for name in MANIFESTS:
            if (here / name).is_file():
                with (here / name).open("a", encoding="utf-8") as handle:
                    handle.write("\n")

    def runs(self) -> list[tuple[list[str], str | None]]:
        return [(command, cwd) for command, cwd in self.calls
                if any(part.startswith("--output") for part in command)]


class Web:
    """Every URL: what `pages` holds, a refused connection otherwise; `asked` lists what was opened."""

    def __init__(self, pages: dict[str, bytes] | None = None):
        self.pages, self.asked = dict(pages or {}), []

    def __call__(self, url: str, timeout: float):
        self.asked.append(url)
        if url not in self.pages:
            raise urllib.error.URLError("no network in this test")
        return io.BytesIO(self.pages[url])


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """The shared directory, temporary directories, memory and disk of a test; programs and URLs are fakes."""
    cache = tmp_path / "cache"
    temp = tmp_path / "temp"
    temp.mkdir()
    monkeypatch.setattr(rx, "shared_cache_dir", lambda: cache)
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    monkeypatch.setattr(rx, "free_memory", lambda: 64 * GB)
    usage = collections.namedtuple("usage", "total used free")
    monkeypatch.setattr(shutil, "disk_usage", lambda path: usage(500 * GB, 400 * GB, 100 * GB))
    monkeypatch.setattr("time.sleep", lambda seconds: None)
    fake, web = Fake(), Web()
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: fake(*args, **kwargs))
    monkeypatch.setattr(rx, "open_url", lambda url, timeout: web(url, timeout))
    monkeypatch.setattr(python, "RUNS_HERE", True)  # the fakes run on every platform
    return {"root": tmp_path, "cache": cache, "temp": temp, "fake": fake, "web": web, "monkeypatch": monkeypatch}


def _installed(home: Path, files: dict[str, str] = ()) -> None:
    home.mkdir(parents=True, exist_ok=True)
    for rel, text in dict(files).items():
        (home / rel).parent.mkdir(parents=True, exist_ok=True)
        (home / rel).write_text(text, encoding="utf-8")
    (home / ".installed").write_text("test", encoding="utf-8")


def _tools(project: Path, which: str) -> None:
    """Everything `which` needs already in the shared directory, so nothing is downloaded."""
    if which == "go":
        go_bin = rx.shared_engine_dir("go") / rx.GO_VERSION / "go" / "bin" / rx.executable_name("go")
        go_bin.parent.mkdir(parents=True)
        go_bin.write_text("fake", encoding="utf-8")
        _installed(rx.shared_engine_dir("scip-go") / go.VERSION, {rx.executable_name("scip-go"): "fake"})
    elif which == "rust":
        _installed(rx.shared_engine_dir("rust") / rx.RUST_VERSION)
        _installed(rx.shared_engine_dir("rust-analyzer") / rx.RUST_ANALYZER_RELEASE,
                   {rx.executable_name("rust-analyzer"): "fake"})
    else:
        home = rx.shared_engine_dir("node") / runtime.NODE_VERSION
        _installed(home)
        directory = runtime.node_directory(home)  # npm too, which `npm_modules` looks for on the PATH
        directory.mkdir(parents=True, exist_ok=True)
        for name in (rx.executable_name("node"), "npm.cmd" if os.name == "nt" else "npm"):
            (directory / name).write_text("fake", encoding="utf-8")
            (directory / name).chmod(0o755)
        package, module = NPM[which], MODULES[which]
        bin_name = package.rsplit("/", 1)[-1]
        _installed(rx.shared_engine_dir(bin_name) / module.VERSION,
                   {f"node_modules/{package}/package.json": json.dumps({"bin": {bin_name: "main.js"}}),
                    f"node_modules/{package}/main.js": "// the indexer"})
        key = rx.npm_key(project)
        if key:
            _installed(rx.shared_cache_dir() / "npm" / key, {"daodan-modules.json": "{}", "node_modules/.keep": ""})


def _project(sandbox, which: str) -> Path:
    """A copy of the fixture's sources, without its index; Go and Rust get a nested module or crate too."""
    project = sandbox["root"] / "project" / which
    shutil.copytree(FIXTURES / which, project, ignore=shutil.ignore_patterns("index.scip", "expected.json"))
    if which == "go":
        (project / "tools").mkdir()
        (project / "tools/go.mod").write_text("module example.com/tools\n\ngo 1.21\n", encoding="utf-8")
        (project / "tools/tool.go").write_text("package tools\n\nfunc Tool() {}\n", encoding="utf-8")
        (project / "_examples/demo").mkdir(parents=True)
        (project / "_examples/demo/main.go").write_text("package main\n\nfunc main() {}\n", encoding="utf-8")
    if which == "rust":
        (project / "fuzz/src").mkdir(parents=True)
        (project / "fuzz/Cargo.toml").write_text('[package]\nname = "fuzz"\nversion = "0.1.0"\n', encoding="utf-8")
        (project / "fuzz/src/main.rs").write_text("fn main() {}\n", encoding="utf-8")
    return project


def _hashes(root: Path) -> dict[str, str]:
    """Every path under `root`, links never entered, with its content's digest."""
    out = {}
    for current, directories, files in os.walk(root):
        for name in directories:
            out[Path(current, name).relative_to(root).as_posix() + "/"] = "directory"
        for name in files:
            path = Path(current, name)
            out[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


class Stub:
    """What `code_graph.build` asks of a snapshot, for an index's own documents: no reference, no declaration."""

    def __init__(self, index: code_graph.Index, language: str):
        documents = sorted(index.documents)
        self.languages = {rel: language for rel in documents}
        self.rel, self.checkout, self.inventory = {}, {rel: rel for rel in documents}, documents

    def references(self, language):
        return iter(())

    def grade(self, rel, line, column):
        return "value", "variable"

    def function_at(self, rel, line, column):
        return None


def _graphs(root: Path, indexes: list, languages: tuple, indexer: dict) -> dict:
    index = code_graph.Index(root)
    for path, prefix in indexes:
        index.load(Path(path), prefix)
    return {language: code_graph.build(index, Stub(index, language), language, {}, indexer)[0]
            for language in languages}


@pytest.mark.parametrize("which", sorted(MODULES))
def test_a_run_writes_nothing_in_the_project_removes_its_mirror_and_feeds_the_graph(sandbox, which):
    project = _project(sandbox, which)
    _tools(project, which)
    sandbox["fake"].index = FIXTURES / which / "index.scip"
    before = _hashes(project)
    result = MODULES[which].index(project, sandbox["root"] / "work")
    assert "state" not in result, result.get("reason")
    assert _hashes(project) == before
    runs = sandbox["fake"].runs()
    assert runs
    for _command, cwd in runs:
        assert Path(project).resolve() not in Path(cwd).resolve().parents and Path(cwd).resolve() != project
        assert not Path(cwd).exists()
    assert list(sandbox["temp"].iterdir()) == []  # the mirror's own temporary directory is gone too
    assert [prefix for _path, prefix in result["indexes"]][0] == ""
    built = _graphs(project, result["indexes"], LANGUAGES[which], result["indexer"])
    expected = _graphs(project, [(FIXTURES / which / "index.scip", "")], LANGUAGES[which], result["indexer"])
    for language in LANGUAGES[which]:
        assert built[language]["edges"] == expected[language]["edges"]
        assert built[language]["files"] == expected[language]["files"]
        assert built[language]["indexer"]["name"] == {"go": "scip-go", "rust": "rust-analyzer",
                                                      "ts": "scip-typescript", "python": "scip-python"}[which]
    assert any(built[language]["edges"] for language in LANGUAGES[which])
    if which == "ts":
        assert result["node_modules"] == {"": str(rx.shared_cache_dir() / "npm" / rx.npm_key(project) / "node_modules")}


def test_go_runs_every_module_and_names_the_directories_go_ignores(sandbox):
    project = _project(sandbox, "go")
    _tools(project, "go")
    sandbox["fake"].index = FIXTURES / "go/index.scip"
    result = go.index(project, sandbox["root"] / "work")
    roots = [run["prefix"] for run in result["runs"]]
    assert roots == ["", "tools"]
    first = result["runs"][0]["command"]
    assert "./..." in first and "./_examples/demo" in first


def test_without_a_root_package_json_each_outermost_package_gets_its_install(sandbox):
    project = sandbox["root"] / "project" / "app-only"
    shutil.copytree(FIXTURES / "ts", project / "app", ignore=shutil.ignore_patterns("index.scip"))
    (project / "app/tsconfig.json").rename(project / "app/tsconfig.app.json")
    _tools(project / "app", "ts")
    sandbox["fake"].index = FIXTURES / "ts/index.scip"
    seen = {}
    real_tsconfig = typescript._tsconfig

    def spy(mirror, files, base=None):  # what the mirror holds when the run starts
        seen["linked"] = os.path.isjunction(mirror / "app/node_modules") or (mirror / "app/node_modules").is_symlink()
        return real_tsconfig(mirror, files, base)

    sandbox["monkeypatch"].setattr(typescript, "_tsconfig", spy)
    result = typescript.index(project, sandbox["root"] / "work", tsconfig="app/tsconfig.app.json")
    assert "state" not in result, result.get("reason")
    assert list(result["node_modules"]) == ["app"] and seen["linked"]
    assert result["tsconfig_extends"] == "./app/tsconfig.app.json"


def test_the_first_use_installs_with_one_log_line(sandbox, capsys):
    project = _project(sandbox, "go")
    _tools(project, "go")
    shutil.rmtree(rx.shared_engine_dir("scip-go"))
    sandbox["fake"].index = FIXTURES / "go/index.scip"
    result = go.index(project, sandbox["root"] / "work")
    assert "state" not in result
    lines = [line for line in capsys.readouterr().out.splitlines() if line.startswith("installing ")]
    assert lines == [f"installing scip-go {go.VERSION} into {rx.shared_engine_dir('scip-go') / go.VERSION} "
                     "(first use)"]
    assert (rx.shared_engine_dir("scip-go") / go.VERSION / ".installed").is_file()


def _node_release(digest: str | None = None, platform: str | None = None) -> dict[str, bytes]:
    """Node's archive for this platform (or `platform`) and its SHASUMS256, which names `digest` instead when
    given."""
    windows = platform is None and os.name == "nt"
    platform = runtime.NODE_PLATFORMS[platform or rx._platform()]
    top = f"node-{runtime.NODE_VERSION}-{platform}"
    buffer = io.BytesIO()
    if windows:
        asset = f"{top}.zip"
        with zipfile.ZipFile(buffer, "w") as bundle:
            bundle.writestr(f"{top}/node.exe", "fake")
    else:
        asset = f"{top}.tar.gz"
        with tarfile.open(fileobj=buffer, mode="w:gz") as bundle:
            data = b"fake"
            member = tarfile.TarInfo(f"{top}/bin/node")
            member.size = len(data)
            bundle.addfile(member, io.BytesIO(data))
    archive = buffer.getvalue()
    base = f"https://nodejs.org/dist/{runtime.NODE_VERSION}/"
    sums = f"{digest or hashlib.sha256(archive).hexdigest()}  {asset}\n{'0' * 64}  other.tar.gz\n"
    return {base + asset: archive, base + "SHASUMS256.txt": sums.encode("ascii")}


def test_node_installs_from_its_release_checked_against_shasums256(sandbox, capsys):
    project = _project(sandbox, "python")
    sandbox["web"].pages.update(_node_release())
    sandbox["fake"].index = FIXTURES / "python/index.scip"
    result = python.index(project, sandbox["root"] / "work")
    assert "state" not in result, result.get("reason")
    out = capsys.readouterr().out
    assert f"installing node {runtime.NODE_VERSION} into" in out
    assert f"installing scip-python {python.VERSION} into" in out


def test_a_wrong_checksum_is_refused(sandbox):
    project = _project(sandbox, "ts")
    sandbox["web"].pages.update(_node_release(digest="f" * 64))
    result = typescript.index(project, sandbox["root"] / "work")
    assert result["state"] == "unavailable"
    assert "checksum mismatch" in result["reason"] and "nodejs.org" in result["install"]
    assert not (rx.shared_engine_dir("node") / runtime.NODE_VERSION / ".installed").exists()
    assert sandbox["fake"].runs() == []


def test_a_download_that_cannot_happen_is_unavailable_with_its_cause(sandbox):
    project = _project(sandbox, "go")
    result = go.index(project, sandbox["root"] / "work")
    assert result["state"] == "unavailable"
    assert result["reason"].startswith(f"Go {rx.GO_VERSION} and scip-go {go.VERSION} could not be downloaded")
    assert "no network in this test" in result["reason"]
    assert result["install"].startswith("check the network")
    assert result["indexes"] == [] and sandbox["fake"].runs() == []


def test_rust_analyzer_leaves_its_temporary_directories_in_a_folder_removed_after_the_run(sandbox):
    project = _project(sandbox, "rust")
    shutil.rmtree(project / "fuzz")
    _tools(project, "rust")
    sandbox["fake"].index = FIXTURES / "rust/index.scip"
    work, fake, seen = sandbox["root"] / "work", sandbox["fake"], []

    def leaving(command, *args, **kwargs):
        if "scip" in [str(part) for part in command]:
            env = kwargs["env"]
            seen.append({name: env.get(name) for name in ("TEMP", "TMP", "TMPDIR")})
            Path(env["TEMP"], "proc-macro-srv4dc0-0").mkdir()  # what rust-analyzer leaves on Windows
        return fake(command, *args, **kwargs)

    sandbox["monkeypatch"].setattr(subprocess, "run", leaving)
    result = rust.index(project, work)
    assert "state" not in result and len(seen) == 1
    temp = Path(seen[0]["TEMP"])
    assert set(seen[0].values()) == {str(temp)} and temp.is_relative_to(work)
    assert not temp.exists()


def test_rust_analyzer_is_named_by_its_pinned_release_and_keeps_the_build_it_states(sandbox):
    project = _project(sandbox, "rust")
    shutil.rmtree(project / "fuzz")
    _tools(project, "rust")
    sandbox["fake"].index = FIXTURES / "rust/index.scip"
    result = rust.index(project, sandbox["root"] / "work")
    assert (result["indexer"]["version"], result["build"]) == (rx.RUST_ANALYZER_RELEASE, "tool 0.0.0-test")


def test_an_install_that_crashes_states_the_first_line_of_its_error(sandbox):
    project = _project(sandbox, "go")
    _tools(project, "go")
    shutil.rmtree(rx.shared_engine_dir("scip-go"))
    trace = "fatal error: out of memory\n" + "runtime.frame()\n\truntime/malloc.go:2141\n" * 60 + "runtime.rt0_go()\n"
    fake = sandbox["fake"]

    def crashing(command, *args, **kwargs):
        if [str(part) for part in command][1:2] == ["install"]:
            raise subprocess.CalledProcessError(2, command, "", trace)
        return fake(command, *args, **kwargs)

    sandbox["monkeypatch"].setattr(subprocess, "run", crashing)
    result = go.index(project, sandbox["root"] / "work")
    assert result["state"] == "unavailable" and "(exit code 2)" in result["reason"]
    assert "fatal error: out of memory" in result["reason"] and result["reason"].endswith("runtime.rt0_go()")
    assert len(result["reason"]) < 1200


def test_a_failed_run_is_failed_with_the_stderr_tail_and_the_error_count(sandbox):
    project = _project(sandbox, "rust")
    shutil.rmtree(project / "fuzz")
    _tools(project, "rust")
    sandbox["fake"].code = 101
    sandbox["fake"].stderr = "start\n2026-11-14 ERROR one thing\n2026-11-14 ERROR another\nthe last words\n"
    result = rust.index(project, sandbox["root"] / "work")
    assert result["state"] == "failed" and result["indexes"] == []
    assert "the last words" in result["reason"] and "101" in result["reason"]
    assert result["errors"] == 2 and len(result["runs"]) == 1  # the fallback run replaces the first one


def test_a_long_failure_keeps_the_cause_it_states_first(sandbox):
    project = _project(sandbox, "python")
    _tools(project, "python")
    sandbox["fake"].code = 1
    sandbox["fake"].stderr = ("SyntaxError: Invalid regular expression: /\\/g: \\ at end of pattern\n"
                              + "    at r (dist/webpack/bootstrap:19:32)\n" * 50 + "Node.js v22.23.4\n")
    result = python.index(project, sandbox["root"] / "work")
    assert result["state"] == "failed"
    assert "SyntaxError: Invalid regular expression" in result["reason"] and result["reason"].endswith("Node.js v22.23.4")
    assert len(result["reason"]) < 1200


def test_python_names_its_project_by_a_constant_version_and_runs_no_git(sandbox):
    project = _project(sandbox, "python")
    _tools(project, "python")
    sandbox["fake"].index = FIXTURES / "python/index.scip"
    result = python.index(project, sandbox["root"] / "work")
    assert "state" not in result, result.get("reason")
    command = sandbox["fake"].runs()[0][0]
    assert command[command.index("--project-version") + 1] == "_" and result["project"][1] == "_"
    assert not [command for command, _cwd in sandbox["fake"].calls if Path(command[0]).stem == "git"]


class Box:
    """`container.run_in_container`: with `gap`, no engine answers; else it asks for the inputs, as a run does
    once an engine answers, and brings back `index` with an execution log."""

    def __init__(self, index: Path | None = None, gap: tuple[str, str] | None = None, peak: int = 400 * 2**20):
        self.index, self.gap, self.peak, self.asked = index, gap, peak, []

    def __call__(self, project, command, **options):
        self.asked.append({"project": Path(project), "command": command, **options})
        if self.gap:
            return {"state": "gap", "cause": self.gap[0], "remedy": self.gap[1], "outputs": []}
        inputs = options["inputs"]() if callable(options["inputs"]) else options["inputs"]
        self.asked[-1]["inputs"] = inputs
        out = Path(options["out_dir"])
        (out / "out").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.index, out / "out/index.scip")
        (out / "execute.log").write_text(f"indexing\nDAODAN_PEAK {self.peak}\n", encoding="utf-8")
        (out / "container-runs.jsonl").write_text(json.dumps({"phase": "execute", "duration_seconds": 12.5}) + "\n",
                                                   encoding="utf-8")
        return {"state": "done", "exit_code": 0, "outputs": ["out/index.scip"], "engine": "test"}


def _environment(root: Path) -> Path:
    """A Windows virtual environment with one package, `pkg` 1.0."""
    site = root / "env/Lib/site-packages"
    (site / "pkg").mkdir(parents=True)
    (site / "pkg/__init__.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (site / "pkg/__pycache__").mkdir()
    (site / "pkg/__pycache__/__init__.cpython-313.pyc").write_bytes(b"\0")
    info = site / "pkg-1.0.dist-info"
    info.mkdir()
    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\n", encoding="utf-8")
    (info / "RECORD").write_text("pkg/__init__.py,,\npkg-1.0.dist-info/METADATA,,\n", encoding="utf-8")
    return root / "env"


def test_where_scip_python_cannot_start_it_runs_in_a_container_over_the_host_environment(sandbox):
    import container
    project = _project(sandbox, "python")
    _tools(project, "python")
    platform = f"linux-{container.architecture()}"
    sandbox["web"].pages.update(_node_release(platform=platform))
    box = Box(FIXTURES / "python/index.scip")
    sandbox["monkeypatch"].setattr(python, "RUNS_HERE", False)
    sandbox["monkeypatch"].setattr(container, "run_in_container", box)
    before = _hashes(project)
    work = sandbox["root"] / "work"
    result = python.index(project, work, environment=_environment(sandbox["root"]))
    assert "state" not in result, result.get("reason")
    assert _hashes(project) == before and sandbox["fake"].runs() == []  # nothing ran on the host
    asked = box.asked[0]
    assert asked["project"] == project and asked["image"] == python.IMAGE and asked["outputs"] == ["/daodan/out"]
    assert asked["command"][:2] == ["bash", "-c"] and asked["command"][-2:] == [result["project"][0], "_"]
    inputs = asked["inputs"]
    archive = f"node-{runtime.NODE_VERSION}-{runtime.NODE_PLATFORMS[platform]}.tar.gz"
    assert Path(inputs["/daodan/tools/node.tar.gz"]).name == archive  # Node for Linux, checked like the host's
    assert json.loads(Path(inputs["/daodan/tools/environment.json"]).read_text(encoding="utf-8")) == [
        {"name": "pkg", "version": "1.0", "files": ["pkg/__init__.py", "pkg-1.0.dist-info/METADATA"]}]
    assert "/daodan/env/pkg/__init__.py" in inputs and not [key for key in inputs if "__pycache__" in key]
    assert "/daodan/scip-python/node_modules/@sourcegraph/scip-python/main.js" in inputs
    assert Path(inputs["/daodan/tools/scip-python.path"]).read_text(encoding="utf-8") == \
        "/daodan/scip-python/node_modules/@sourcegraph/scip-python/main.js"
    assert result["runs"][0]["peak_mb"] == 400 and result["runs"][0]["seconds"] == 12.5
    built = _graphs(project, result["indexes"], ("python",), result["indexer"])
    expected = _graphs(project, [(FIXTURES / "python/index.scip", "")], ("python",), result["indexer"])
    assert built["python"]["edges"] == expected["python"]["edges"] and built["python"]["edges"]


def test_where_scip_python_cannot_start_and_no_container_engine_answers_it_is_unavailable(sandbox):
    import container
    project = _project(sandbox, "python")
    box = Box(gap=("no container engine answers: neither docker nor podman", "start Docker or Podman"))
    sandbox["monkeypatch"].setattr(python, "RUNS_HERE", False)
    sandbox["monkeypatch"].setattr(container, "run_in_container", box)
    result = python.index(project, sandbox["root"] / "work")
    assert result["state"] == "unavailable" and f"scip-python {python.VERSION}" in result["reason"]
    assert "path separator" in result["reason"] and "no container engine answers" in result["reason"]
    assert result["install"] == "start Docker or Podman"
    assert sandbox["web"].asked == [] and sandbox["fake"].calls == []  # nothing downloaded without an engine


def test_less_memory_than_the_indexer_needs_starts_nothing(sandbox):
    project = _project(sandbox, "ts")
    _tools(project, "ts")
    sandbox["monkeypatch"].setattr(rx, "free_memory", lambda: typescript.MIN_FREE - 1)
    result = typescript.index(project, sandbox["root"] / "work")
    assert result["state"] == "unavailable" and "memory" in result["reason"]
    assert sandbox["fake"].calls == [] and sandbox["web"].asked == []


def test_under_one_gigabyte_of_disk_nothing_is_downloaded(sandbox):
    project = _project(sandbox, "python")
    usage = collections.namedtuple("usage", "total used free")
    sandbox["monkeypatch"].setattr(shutil, "disk_usage", lambda path: usage(500 * GB, 499.5 * GB, GB // 2))
    result = python.index(project, sandbox["root"] / "work")
    assert result["state"] == "unavailable"
    assert "0.5 GB free on the drive of" in result["reason"] and "free at least 1 GB" in result["install"]
    assert sandbox["web"].asked == [] and sandbox["fake"].calls == []


@pytest.mark.parametrize(("cpus", "jobs"), [(22, "4"), (2, "2"), (None, "1")])
def test_scip_go_is_built_with_at_most_four_compilers_at_once(sandbox, cpus, jobs):
    project = _project(sandbox, "go")
    _tools(project, "go")
    shutil.rmtree(rx.shared_engine_dir("scip-go"))
    sandbox["monkeypatch"].setattr(os, "cpu_count", lambda: cpus)
    sandbox["fake"].index = FIXTURES / "go/index.scip"
    assert "state" not in go.index(project, sandbox["root"] / "work")
    build = next(command for command, _cwd in sandbox["fake"].calls if command[1:2] == ["install"])
    assert build[1:4] == ["install", "-p", jobs]


def test_go_keeps_its_configuration_and_telemetry_in_the_shared_directory_and_turns_telemetry_off(sandbox):
    project = _project(sandbox, "go")
    _tools(project, "go")
    shutil.rmtree(rx.shared_engine_dir("scip-go"))
    sandbox["fake"].index = FIXTURES / "go/index.scip"
    for _ in range(2):
        assert "state" not in go.index(project, sandbox["root"] / "work")
    # The variable Go's os.UserConfigDir reads on this platform.
    variable = "APPDATA" if os.name == "nt" else "HOME" if sys.platform == "darwin" else "XDG_CONFIG_HOME"
    fake = sandbox["fake"]
    started = [(command, env) for (command, _cwd), env in zip(fake.calls, fake.envs)
               if Path(command[0]).name in (rx.executable_name("go"), rx.executable_name("scip-go"))]
    assert started
    for command, env in started:
        assert Path(env[variable]).is_relative_to(sandbox["cache"]), (command, env[variable])
    assert [command[1:] for command, _env in started if command[1:2] == ["telemetry"]] == [["telemetry", "off"]]


def test_node_and_npm_keep_their_caches_in_the_shared_directory(sandbox):
    project = _project(sandbox, "ts")
    _tools(project, "ts")
    shutil.rmtree(rx.shared_engine_dir("scip-typescript"))
    shutil.rmtree(rx.shared_cache_dir() / "npm")
    sandbox["fake"].index = FIXTURES / "ts/index.scip"
    typescript.index(project, sandbox["root"] / "work")
    fake = sandbox["fake"]
    started = [(command, env) for (command, _cwd), env in zip(fake.calls, fake.envs)
               if Path(command[0]).stem in ("node", "npm")]
    assert {Path(command[0]).stem for command, _env in started} == {"node", "npm"}  # npm_package, npm_modules
    for command, env in started:
        assert env is not None, command
        assert Path(env["npm_config_cache"]).is_relative_to(sandbox["cache"])
        assert Path(env["NODE_COMPILE_CACHE"]).is_relative_to(sandbox["cache"])


def _rooted(index: Path, root: str) -> bytes:
    """`index` with `root` as its metadata's project root (SCIP: `Index.metadata` 1, `Metadata.project_root` 3)."""
    def varint(number: int) -> bytes:
        out = bytearray()
        while True:
            byte, number = number & 0x7F, number >> 7
            out.append(byte | (0x80 if number else 0))
            if not number:
                return bytes(out)

    def field(number: int, payload: bytes) -> bytes:
        return varint(number << 3 | 2) + varint(len(payload)) + payload

    out = b""
    for number, wire, value in code_graph._fields(index.read_bytes()):
        assert wire == 2  # the metadata, a document, an external symbol
        if number == 1:
            value = b"".join(field(part, item) if kind == 2 else varint(part << 3) + varint(item)
                             for part, kind, item in code_graph._fields(value) if part != 3) + field(3, root.encode())
        out += field(number, value)
    return out


@pytest.mark.parametrize("which", ["go", "rust"])
def test_two_mirrors_of_one_project_give_the_same_project_nodes(tmp_path, which):
    """A run's index names its mirror, a new temporary directory each time, as its root: the graph never reads it."""
    graphs = []
    for name, root in (("one", "file:///tmp/daodan-scip-go-1a2b"), ("two", "file://D:%5CTemp%5Cdaodan-scip-go-9z8y")):
        path = tmp_path / f"{name}.scip"
        path.write_bytes(_rooted(FIXTURES / which / "index.scip", root))
        graphs.append(_graphs(FIXTURES / which, [(path, "")], LANGUAGES[which], {"name": "x", "version": "1"}))
    assert (tmp_path / "one.scip").read_bytes() != (tmp_path / "two.scip").read_bytes()
    for language in LANGUAGES[which]:
        ids = [sorted(node["id"] for node in graph[language]["nodes"] if node["file"]) for graph in graphs]
        assert ids[0] and ids[0] == ids[1]
        assert graphs[0][language]["edges"] == graphs[1][language]["edges"]


def test_the_peak_is_none_when_no_run_measured_it():
    assert code_graph.indexer("tool", "1", [{"seconds": 1.0, "peak_mb": None}])["peak_mb"] is None
    assert code_graph.indexer("tool", "1", [{"seconds": 1.0, "peak_mb": None},
                                            {"seconds": 2.0, "peak_mb": 300}])["peak_mb"] == 300
    assert code_graph.indexer("tool", "1", [])["peak_mb"] is None


def test_every_indexer_declares_the_memory_it_needs():
    assert [MODULES[name].MIN_FREE // 2**20 for name in ("go", "rust", "ts", "python")] == [512, 1280, 2304, 512]
