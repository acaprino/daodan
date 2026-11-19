"""The scip-go adapter's own rules: the names of Go's universe scope, which scip-go writes no occurrence of
(`prepare`), the files the indexer's build leaves out, indexed by further runs under a configuration the go tool
says builds them (`configuration`, `index`), and its run, in Daodan's container only: none of it on the host. The
container is `sh` playing the execution's script with a fake `go` and a fake `scip-go` (`boxed`).

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_go.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "daodan/core"
for path in (str(SCRIPTS), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import code_graph  # noqa: E402
import container  # noqa: E402
import engine_tools  # noqa: E402
import preparation  # noqa: E402
from indexers import go  # noqa: E402
from test_codebase_map_code_graph import document, occurrence  # noqa: E402
from test_codebase_map_indexers import FIXTURES, _graphs  # noqa: E402

STDLIB = "scip-go gomod github.com/golang/go/src "
TARGET = ("linux", "amd64")
# The scripts are the container's: a test plays them where `sh` and the container's programs are.
played = pytest.mark.skipif(os.name == "nt" or not all(map(shutil.which, ("sh", "timeout", "grep", "env"))),
                            reason="sh plays the container's script")


# ------------------------------------------------------------------ the universe scope

A = '''package m

import "fmt"

func F(b []byte, err error) int {
\tfmt.Println(string(b), err.Error())
\treturn len(b) + Missing(b)
}
'''
B = '''package sub

func G(xs []int) []int {
\treturn append(xs, cap(xs))
}
'''


class References:
    """What `prepare` asks of a snapshot: the Go references, each `(file, line, byte column of its last name,
    name parts)`."""

    def __init__(self, rows):
        self.rows, self.checkout = rows, {}

    def references(self, language):
        assert language == "go"
        for number, (rel, line, column, parts) in enumerate(self.rows):
            yield f"r{number}", rel, "call", "unresolved", None, (line, column, line, column + len(parts[-1])), \
                parts, "-"

    def callee(self, rel, span, parts):
        return span[0], span[1]


def test_a_name_of_the_universe_scope_gets_the_symbol_of_gos_builtin_package(tmp_path):
    """The version is the one the document links its standard library to, else its module's go directive."""
    for rel, text in {"go.mod": "module example.com/m\n\ngo 1.24\n", "a.go": A, "c.go": "package m\n\nvar n = len(A)\n",
                      "sub/go.mod": "module example.com/sub\n\ngo 1.16\n", "sub/b.go": B}.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8", newline="\n")
    (tmp_path / "index.scip").write_bytes(
        document("a.go", [occurrence(6, 1, 4, f"{STDLIB}go1.22 fmt/"),
                          occurrence(6, 5, 12, f"{STDLIB}go1.22 fmt/Println()."),
                          occurrence(6, 24, 27, "local 1")])
        + document("sub/b.go", [occurrence(3, 5, 6, "scip-go gomod example.com/sub v1 `example.com/sub`/G().", True)]))
    index = code_graph.Index(tmp_path)
    index.load(tmp_path / "index.scip")
    snapshot = References([("a.go", 6, 13, ["string"]), ("a.go", 6, 28, ["err", "Error"]), ("a.go", 7, 8, ["len"]),
                           ("a.go", 7, 17, ["Missing"]), ("a.go", 6, 5, ["fmt", "Println"]),
                           ("sub/b.go", 4, 8, ["append"]), ("sub/b.go", 4, 19, ["cap"]), ("c.go", 3, 8, ["len"])])
    assert go.prepare(index, snapshot) == {"builtins": 5}
    keys = {place: [o.key for o in found] for place, found in index.at.items()}
    assert keys[("a.go", 6, 13)] == [f"{STDLIB}go1.22 builtin/string#"]  # a conversion
    assert keys[("a.go", 6, 28)] == [f"{STDLIB}go1.22 builtin/error#Error()."]  # the predeclared error's method
    assert keys[("a.go", 7, 8)] == [f"{STDLIB}go1.22 builtin/len()."]
    assert keys[("sub/b.go", 4, 8)] == [f"{STDLIB}go1.16 builtin/append()."]  # its module's go directive
    assert keys[("sub/b.go", 4, 19)] == [f"{STDLIB}go1.16 builtin/cap()."]
    assert ("a.go", 7, 17) not in keys  # not predeclared: still nothing there
    assert keys[("a.go", 6, 5)] == [f"{STDLIB}go1.22 fmt/Println()."]  # the index's own occurrence stays alone
    assert "c.go" not in index.documents  # a file the index has no document of gets none
    assert [o.key for o in index.documents["a.go"]][-3:] == [keys[("a.go", 6, 13)][0], keys[("a.go", 6, 28)][0],
                                                            keys[("a.go", 7, 8)][0]]


# ------------------------------------------------------------------ the configuration of a file

def gated(expression: str, package: str = "store") -> str:
    return f"//go:build {expression}\n\npackage {package}\n"


def built(goos: str = "linux", goarch: str = "amd64", cgo: str = "1", tags=()) -> dict:
    return {"GOOS": goos, "GOARCH": goarch, "CGO_ENABLED": cgo, "tags": list(tags)}


@pytest.mark.parametrize("rel, text, cgo, want", [
    ("store/backend_other.go", gated("!linux && !windows"), True, built("darwin")),
    ("store/backend_windows.go", "package store\n", True, built("windows")),  # its name
    ("store/x_arm64.go", "package store\n", True, built(goarch="arm64")),
    ("store/integration_test.go", gated("integration", "store_test"), True, built(tags=["integration"])),
    ("sum/sum_nocgo.go", gated("!cgo", "sum"), True, built(cgo="0")),
    ("sum/sum.go", gated("cgo", "sum"), False, built()),
    ("store/poll.go", gated("unix && !linux"), True, built("darwin")),  # windows is no unix
    ("store/either.go", gated("(linux && arm64) || (darwin && amd64)"), True, built(goarch="arm64")),
    ("store/both.go", gated("integration && (windows || !cgo)"), True, built(cgo="0", tags=["integration"])),
    ("store/gen.go", gated("ignore", "main"), True, {"program": "store/gen.go"}),  # a `go run` program
    ("store/never.go", gated("linux && windows"), True, None),
    ("store/future.go", gated("go1.99"), True, None),  # a release later than Daodan's Go
    ("store/broken.go", gated("linux &&"), True, None),
    ("store/plain.go", gated("go1.21 && amd64"), True, built()),  # the indexer's own build
])
def test_the_configuration_nearest_the_indexers_build_that_builds_a_file(rel, text, cgo, want):
    assert go.configuration(rel, text, TARGET, cgo) == want


# ------------------------------------------------------------------ the further runs

FILES = {
    "go.mod": "module example.com/tags\n\ngo 1.22\n",
    "main.go": 'package main\n\nimport "example.com/tags/store"\n\nfunc main() { println(store.Open()) }\n',
    "store/store.go": "package store\n\nfunc Open() string { return backend() }\n",
    "store/backend_linux.go": 'package store\n\nfunc backend() string { return "epoll" }\n',
    "store/backend_other.go": gated("!linux && !windows") + '\nfunc backend() string { return "poll" }\n',
    "store/backend_windows.go": 'package store\n\nfunc backend() string { return "iocp" }\n',
    "store/gen.go": gated("ignore", "main") + "\nfunc main() {}\n",
    "store/integration_test.go": gated("integration", "store_test")
    + '\nimport "testing"\n\nfunc TestX(t *testing.T) {}\n',
    "store/never.go": gated("linux && windows") + "\nfunc never() {}\n",
    "store/fast.go": gated("cgo") + '\n// #include <stdio.h>\nimport "C"\n\nfunc fast() {}\n',
}
# What each run of scip-go writes, by the configuration it runs under: its packages' documents, the store's
# own files among them, which a further run must not add twice.
WRITTEN = {"": ["main.go", "store/store.go", "store/backend_linux.go"],
           "GOOS=darwin": ["store/store.go", "store/backend_other.go"],
           "GOOS=windows": ["store/store.go", "store/backend_windows.go"],
           "-tags=integration": ["store/store.go", "store/backend_linux.go", "store/integration_test.go"],
           "./store/gen.go": ["store/gen.go"]}
# What `go list` says each further run builds, as paths from the module's folder.
LISTED = {"GOOS=darwin": ["store/backend_other.go", "store/store.go"],
          "GOOS=windows": ["store/backend_windows.go", "store/store.go"],
          "-tags=integration": ["store/backend_linux.go", "store/store.go", "store/integration_test.go"],
          "./store/gen.go": ["store/gen.go"]}


# ------------------------------------------------------------------ the container

# The container's `go` and `scip-go`: which run each is (the program it names, its tags, a GOOS other than the
# indexer's, else the folder it runs in, '' for the project's), what `go list` prints for it and what scip-go
# writes.
FAKE = '''#!{python}
import json, os, shutil, sys
spec = json.load(open({spec!r}, encoding="utf-8"))
argv, env = sys.argv[1:], os.environ
folder = os.path.relpath(os.getcwd(), spec["project"]).replace(os.sep, "/")
named = next((part for part in argv if part.endswith(".go")), None)
tags = next((flag for flag in env.get("GOFLAGS", "").split() if flag.startswith("-tags=")), None)
which = named or tags or ("GOOS=" + env["GOOS"] if env.get("GOOS", "linux") != "linux" else
                          "" if folder == "." else folder)
if os.path.basename(sys.argv[0]) == "go":
    if argv[:3] != ["list", "-e", "-f"] or which not in spec["listed"]:
        sys.exit("go: unsupported GOOS/GOARCH pair")
    print("\\n".join(os.getcwd() + "/" + path for path in spec["listed"][which]))
    sys.exit(0)
output = next(part.split("=", 1)[1] for part in argv if part.startswith("--output="))
with open(spec["log"], "a", encoding="utf-8") as log:
    log.write(json.dumps({{"which": which, "patterns": [part for part in argv if not part.startswith("--output=")],
                          "env": {{name: env.get(name) for name in ("GOOS", "GOARCH", "GOFLAGS", "CGO_ENABLED",
                                                                    "GOPROXY", "GOTOOLCHAIN")}}}}) + "\\n")
code = spec["codes"].get(which, 0)
if code == 0 and which in spec["written"]:
    shutil.copyfile(spec["written"][which], output)
sys.exit(code)
'''


def program(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path


def written(root: Path, files: dict) -> Path:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8", newline="\n")
    return root


def modules(root: Path) -> Path:
    """The Go fixture's sources with a nested module and a directory Go ignores."""
    shutil.copytree(FIXTURES / "go", root, ignore=shutil.ignore_patterns("index.scip", "expected.json"))
    return written(root, {"tools/go.mod": "module example.com/tools\n\ngo 1.21\n",
                          "tools/tool.go": "package tools\n\nfunc Tool() {}\n",
                          "_examples/demo/main.go": "package main\n\nfunc main() {}\n"})


def boxed(tmp_path, monkeypatch, project, indexes, listed=None, codes=None, outcome=None, prepared="", **given):
    """`go.index` with the pass's engine and a container that is `sh` playing the execution's script over the
    project: `go list` prints `listed` by run (an error without one), scip-go writes `indexes` by run and ends with
    `codes`; with `outcome`, a container that ends so and plays nothing. The result, what the container was asked,
    scip-go's runs."""
    state, data, log = tmp_path / "state", tmp_path / "data", tmp_path / "runs.jsonl"
    data.mkdir(parents=True)
    paths = {}
    for number, (which, content) in enumerate(indexes.items()):
        (data / f"{number}.scip").write_bytes(content)
        paths[which] = str(data / f"{number}.scip")
    spec = data / "spec.json"
    spec.write_text(json.dumps({"project": str(project), "listed": listed or {}, "written": paths,
                                "codes": codes or {}, "log": str(log)}), encoding="utf-8")
    tools = state / Path(preparation.T).relative_to(preparation.STATE)
    for path in (tools / "bin/scip-go", tools / "go/bin/go"):
        program(path, FAKE.format(python=sys.executable, spec=str(spec)))
    asked = {}

    def run_in_container(project_dir, command, **options):
        asked.update(options, command=command)
        out = Path(options["out_dir"])
        out.mkdir(parents=True, exist_ok=True)
        (out / "prepare.log").write_text(prepared, encoding="utf-8")
        if outcome is not None:
            return outcome
        # The container's folders as this machine's: the outputs, Daodan's tools, the copy of the project.
        script = command[-1].replace(f"OUT={go.OUT}\n", f"OUT={out / Path(go.OUT).name}\n")
        script = script.replace(preparation.STATE, str(state))
        script = re.sub(rf"(?<= ){container.WORKDIR}(?=[/ ])", str(project_dir), script)
        env = {name: value.replace(preparation.STATE, str(state)) for name, value in options["env"].items()}
        env["PATH"] += os.pathsep + os.environ["PATH"]
        done = subprocess.run(["sh", "-c", script], env=env, capture_output=True, text=True, timeout=120)
        assert done.returncode == 0, done.stderr
        return {"state": "done", "exit_code": 0}

    monkeypatch.setattr(container, "run_in_container", run_in_container)
    monkeypatch.setattr(preparation, "fetched", lambda url, digest, name: tmp_path / name)
    monkeypatch.setattr(go, "_target", lambda: TARGET)
    result = go.index(project, tmp_path / "work", engine="the pass's engine", **given)
    runs = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []
    return result, asked, runs


def test_nothing_of_go_starts_on_the_host(tmp_path, monkeypatch):
    """What a Go project makes the go command start: git, for a module no proxy serves; the C compiler, for a file
    that imports "C"; another Go, the one its `toolchain` line names, from the PATH or downloaded. So the go
    command and scip-go run only in Daodan's container, never on the host (AGENTS.md): each of those programs,
    and Daodan's own Go and scip-go where a host run found them, leaves a mark here if it starts, and none does.
    Without a container Go is unavailable, with the cause."""
    marks, tools, cache = tmp_path / "marks", tmp_path / "bin", tmp_path / "cache"
    marks.mkdir()
    mark = f'#!/bin/sh\necho "$0 $*" >> "{marks}/$(basename "$0")"\n'
    for name in ("go", "go1.99.0", "git", "gcc", "cc", "clang", "scip-go"):
        program(tools / name, mark)
    monkeypatch.setenv("PATH", f"{tools}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(engine_tools, "shared_cache_dir", lambda: cache)
    program(engine_tools.shared_engine_dir("go") / engine_tools.GO_VERSION / "go/bin"
            / engine_tools.executable_name("go"), mark)
    home = engine_tools.shared_engine_dir("scip-go") / go.VERSION
    program(home / engine_tools.executable_name("scip-go"), mark)
    (home / ".installed").write_text("test", encoding="utf-8")
    project = written(tmp_path / "project", {
        "go.mod": "module example.com/guard\n\ngo 1.22\n\ntoolchain go1.99.0\n\n"
                  "require git.example.invalid/outside/every-proxy v0.0.1\n",
        "main.go": 'package main\n\n/*\n#cgo CFLAGS: -DGUARD=1\nint one(void) { return 1; }\n*/\nimport "C"\n\n'
                   "func main() { _ = C.one() }\n"})
    started, run, popen = [], subprocess.run, subprocess.Popen
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: started.append(args) or run(*args, **kwargs))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: started.append(args) or popen(*args, **kwargs))
    monkeypatch.setattr(container, "run_in_container",
                        lambda *args, **kwargs: {"state": "gap", "cause": "no engine", "remedy": "start one"})
    result = go.index(project, tmp_path / "work", **go.structure({"units": [{"kind": "go-module", "root": "."}]}))
    assert (started, sorted(path.name for path in marks.iterdir())) == ([], [])
    assert go.NEEDS_CONTAINER
    assert (result["state"], result["indexes"], result["install"]) == ("unavailable", [], "start one")
    assert result["reason"] == "scip-go runs only in Daodan's container: no engine"


def test_the_structure_names_the_modules_scip_go_runs_in():
    """The folders of the modules. A `go.work`'s folder is none: `./...` there names no module's packages."""
    record = {"units": [{"kind": "go-module", "root": "."}, {"kind": "go-module", "root": "tools"},
                        {"kind": "go-module", "root": "ws/a"}, {"kind": "go-module", "root": "ws/b"}],
              "workspace": [{"tool": "go", "root": "ws", "members": ["ws/a", "ws/b"]}],
              "docker_builds": [{"dockerfile": "Dockerfile"}]}
    assert go.structure(record) == {"roots": {"", "tools", "ws/a", "ws/b"},
                                    "docker": record["docker_builds"]}  # `declared` and the engine are the pass's


@pytest.mark.parametrize(("cpus", "jobs"), [(22, "4"), (2, "2"), (None, "1")])
def test_the_container_builds_scip_go_and_fetches_the_modules_then_indexes_with_no_network(monkeypatch, cpus, jobs):
    monkeypatch.setattr(os, "cpu_count", lambda: cpus)
    prepare, execute, needs = go.scripts(
        [(".", ["./...", "./_examples/demo"]), ("tools", ["./..."])],
        [(".", {"GOOS": "darwin", "GOARCH": "amd64", "CGO_ENABLED": "1"}, ["./store"], ["store/backend_other.go"])])
    assert [name for _url, _digest, name in needs["files"]] == ["go.tar.gz"]
    assert go._target() == TARGET  # the build of the Go the container runs, whatever this machine is
    assert preparation.setup(["go"])["lines"][0] in prepare and "mise" not in prepare
    # scip-go's build is no build of the project: Daodan's Go alone, at most four compilers at once.
    assert (f"GOFLAGS= GOTOOLCHAIN=local {preparation.T}/go/bin/go install -p {jobs} "
            f"github.com/scip-code/scip-go/cmd/scip-go@{go.VERSION}") in prepare
    assert f"echo 'DAODAN-MISSING scip-go@{go.VERSION}'" in prepare
    # A `toolchain` line brings no other Go, in the preparation or after it; no module is fetched after it.
    assert prepare.index("export GOFLAGS=-mod=readonly GOTOOLCHAIN=local") < prepare.index(
        preparation.restore("go", [".", "tools"]))
    assert "export CGO_ENABLED=1 GOFLAGS=-mod=readonly GOPROXY=off GOTOOLCHAIN=local" in execute
    assert f"run 0 {container.WORKDIR} {go.SCIP_GO} --output=$OUT/index-0.scip ./... ./_examples/demo" in execute
    assert f"run 1 {container.WORKDIR}/tools {go.SCIP_GO} --output=$OUT/index-1.scip ./..." in execute
    # A further run: `go list` under its configuration, and scip-go only where it lists a file to index.
    assert f"( cd {container.WORKDIR} && env GOOS=darwin GOARCH=amd64 CGO_ENABLED=1 go list -e -f " in execute
    assert execute.index("grep -qxF -e store/backend_other.go $OUT/list-2.txt") < execute.index("run 2 ")
    if shutil.which("sh"):
        for script in (prepare, execute):
            assert subprocess.run(["sh", "-n", "-c", script], capture_output=True).returncode == 0


@played
def test_scip_go_runs_in_each_folder_and_names_the_directories_go_ignores(tmp_path, monkeypatch):
    project = modules(tmp_path / "project")
    fixture = (FIXTURES / "go/index.scip").read_bytes()
    result, asked, runs = boxed(tmp_path, monkeypatch, project, {"": fixture, "tools": b""}, roots={"", "tools"},
                                declared={"hosts": ("git.example.com",), "where": {}})
    assert "state" not in result, result.get("reason")
    assert [(run["which"], run["patterns"]) for run in runs] == [("", ["./...", "./_examples/demo"]),
                                                                 ("tools", ["./..."])]
    assert [run["prefix"] for run in result["runs"]] == ["", "tools"]
    assert (asked["image"], asked["memory"], asked["engine"]) == (go.IMAGE, go.MEMORY, "the pass's engine")
    assert asked["outputs"] == [go.OUT] and list(asked["inputs"]()) == [f"{preparation.IN}/go.tar.gz"]
    # The preparation reaches Go's proxy and the hosts the project declares; `go mod download` runs in each folder.
    assert {"proxy.golang.org", "sum.golang.org", "git.example.com"} <= set(asked["registries"])
    assert preparation.restore("go", [".", "tools"]) in asked["prepare"][-1]
    built = _graphs(project, result["indexes"], ("go",), result["indexer"])
    expected = _graphs(project, [(FIXTURES / "go/index.scip", "")], ("go",), result["indexer"])
    assert built["go"]["edges"] == expected["go"]["edges"] and built["go"]["edges"]
    assert built["go"]["files"] == expected["go"]["files"] and built["go"]["indexer"]["name"] == "scip-go"


@played
def test_a_run_without_an_index_is_the_reason_its_module_s_files_have_no_document(tmp_path, monkeypatch):
    """`configs` is what the stage hands `tasks`, then `missing`: the folders of the modules, and those whose run
    wrote no index."""
    project = modules(tmp_path / "project")
    result, _asked, _runs = boxed(tmp_path, monkeypatch, project, {"": (FIXTURES / "go/index.scip").read_bytes()},
                                  codes={"tools": 2}, roots={"", "tools"})
    assert result["configs"] == {"roots": ["", "tools"], "failed": {"tools": "exit code 2"}}
    index = code_graph.Index(project)
    for path, prefix in result["indexes"]:
        index.load(Path(path), prefix)
    assert go.missing(index, ["tools/tool.go"], go.tasks(result["configs"])) == {
        "tools/tool.go": "the scip-go run of its module tools wrote no index (exit code 2)"}


@played
def test_scip_go_runs_in_no_folder_but_a_module_that_holds_a_go_file(tmp_path, monkeypatch):
    """A `go.work`'s folder is no module, and a module without a Go file has nothing to index: no run there, so
    none that fails; a Go file outside every module says so."""
    project = written(tmp_path / "project", {
        "go.work": "go 1.22\n\nuse (\n\t./a\n\t./b\n)\n", "a/go.mod": "module example.com/a\n",
        "a/a.go": "package a\n", "b/go.mod": "module example.com/b\n", "x.go": "package x\n"})
    record = {"units": [{"kind": "go-module", "root": "a"}, {"kind": "go-module", "root": "b"}],
              "workspace": [{"tool": "go", "root": ".", "members": ["a", "b"]}]}
    result, asked, runs = boxed(tmp_path, monkeypatch, project, {"a": document("a.go", [])}, **go.structure(record))
    assert [run["which"] for run in runs] == ["a"] and preparation.restore("go", ["a"]) in asked["prepare"][-1]
    assert result["configs"] == {"roots": ["a", "b"], "failed": {}}
    index = code_graph.Index(project)
    for path, prefix in result["indexes"]:
        index.load(Path(path), prefix)
    assert sorted(index.documents) == ["a/a.go"]
    assert go.missing(index, ["x.go"], go.tasks(result["configs"])) == {"x.go": go.NO_MODULE}


def test_a_container_that_does_not_run_is_the_cause_and_what_its_preparation_could_not_do_is_a_gap(tmp_path,
                                                                                                    monkeypatch):
    """No step falls back to a host run (AGENTS.md): the language is failed, with the cause."""
    project = modules(tmp_path / "project")
    result, _asked, _runs = boxed(tmp_path, monkeypatch, project, {}, outcome={"state": "timeout"}, roots={""})
    assert result["state"] == "failed" and result["indexes"] == []
    assert result["reason"].startswith("the container run of scip-go ended timeout")
    said = (f"DAODAN-MISSING scip-go@{go.VERSION}\nDAODAN-RESTORE-FAILED go tools\ngo: example.com/x@v1.0.0: "
            "reading https://proxy.golang.org/example.com/x/@v/v1.0.0.mod: 404 Not Found\nDAODAN-RESTORE-END\n")
    result, _asked, _runs = boxed(tmp_path / "b", monkeypatch, project, {}, prepared=said, roots={"", "tools"},
                                  outcome={"state": "done", "exit_code": 0})
    assert result["state"] == "failed" and result["reason"].startswith("scip-go wrote no index")
    assert [(gap["kind"], gap.get("tool") or gap.get("path")) for gap in result["gaps"]] == [
        ("toolchain_unavailable", "scip-go"), ("restore_failed", "tools")]



@played
def test_a_file_the_indexers_build_leaves_out_is_indexed_under_a_configuration_that_builds_it(tmp_path, monkeypatch):
    project = written(tmp_path / "project", FILES)
    indexes = {which: b"".join(document(rel, []) for rel in rels) for which, rels in WRITTEN.items()}
    result, _asked, runs = boxed(tmp_path, monkeypatch, project, indexes, LISTED, roots={""})
    assert [run["which"] for run in runs] == ["", "GOOS=darwin", "GOOS=windows", "./store/gen.go",
                                              "-tags=integration"]  # in the files' order
    by = {run["which"]: run for run in runs}
    assert by["GOOS=darwin"]["patterns"] == ["./store"] and by["GOOS=darwin"]["env"]["GOARCH"] == "amd64"
    assert by["-tags=integration"]["env"]["GOFLAGS"] == "-mod=readonly -tags=integration"  # beside the indexer's own
    assert by["./store/gen.go"]["patterns"] == ["./store/gen.go"] and by["./store/gen.go"]["env"]["GOOS"] is None
    # Every run is the indexer's build but for its configuration: Daodan's Go alone, cgo on, no module fetched.
    assert {(run["env"]["GOTOOLCHAIN"], run["env"]["CGO_ENABLED"], run["env"]["GOPROXY"]) for run in runs} == {
        ("local", "1", "off")}
    index = code_graph.Index(project)
    for path, prefix in result["indexes"]:
        index.load(Path(path), prefix)
    assert sorted(index.documents) == sorted({rel for rels in WRITTEN.values() for rel in rels})
    assert index.repeated["store/store.go"] == 1  # only the files left out come from the further runs
    assert [run["configuration"] for run in result["runs"][1:]] == ["GOOS=darwin", "GOOS=windows",
                                                                    "go run store/gen.go", "-tags=integration"]
    reasons = {
        "store/never.go": "build constraint `//go:build linux && windows`: no GOOS, GOARCH, cgo and tags build it",
        "store/fast.go": 'a cgo file (`import "C"`): scip-go indexes the copy cgo writes into the build cache, '
                         "not the file"}
    assert result["configs"]["constraints"] == reasons
    assert go.missing(index, sorted(reasons), go.tasks(result["configs"])) == reasons


@played
def test_a_configuration_the_go_tool_does_not_list_the_file_under_is_said_and_runs_nothing(tmp_path, monkeypatch):
    project = written(tmp_path / "project", {rel: FILES[rel] for rel in (
        "go.mod", "main.go", "store/store.go", "store/backend_linux.go", "store/backend_windows.go")})
    indexes = {"": b"".join(document(rel, []) for rel in WRITTEN[""])}
    result, _asked, runs = boxed(tmp_path, monkeypatch, project, indexes, roots={""})  # `go list` fails
    assert [run["which"] for run in runs] == [""] and len(result["runs"]) == 1
    assert result["configs"]["constraints"] == {
        "store/backend_windows.go": "file name constraint `windows`: `go list` under GOOS=windows does not list it"}


@played
def test_a_further_run_of_a_nested_module_runs_in_it_and_names_its_files_from_it(tmp_path, monkeypatch):
    project = written(tmp_path / "project", {
        "go.mod": FILES["go.mod"], "main.go": "package main\n\nfunc main() {}\n",
        "tools/go.mod": "module example.com/tools\n", "tools/x.go": "package tools\n",
        "tools/win/y_windows.go": "package win\n"})
    indexes = {"": document("main.go", []), "tools": document("x.go", []),
               "GOOS=windows": document("win/y_windows.go", []) + document("x.go", [])}
    result, _asked, runs = boxed(tmp_path, monkeypatch, project, indexes, {"GOOS=windows": ["win/y_windows.go"]},
                                 roots={"", "tools"})
    assert [(run["which"], run["patterns"]) for run in runs] == [("", ["./..."]), ("tools", ["./..."]),
                                                                 ("GOOS=windows", ["./win"])]
    assert [(run["prefix"], run.get("configuration")) for run in result["runs"]] == [
        ("", None), ("tools", None), ("tools", "GOOS=windows")]
    index = code_graph.Index(project)
    for path, prefix in result["indexes"]:
        index.load(Path(path), prefix)
    assert sorted(index.documents) == ["main.go", "tools/win/y_windows.go", "tools/x.go"]
    assert index.repeated["tools/x.go"] == 1 and "constraints" not in result["configs"]


@played
def test_the_further_runs_of_one_index_stop_at_a_number(tmp_path, monkeypatch):
    names = [f"gate{number}" for number in range(go.PASSES + 1)]
    project = written(tmp_path / "project", {"go.mod": FILES["go.mod"], "main.go": "package main\n\nfunc main() {}\n",
                                             **{f"{name}/x.go": gated(name, name) for name in names}})
    indexes = {"": document("main.go", []), **{f"-tags={name}": document(f"{name}/x.go", []) for name in names}}
    listed = {f"-tags={name}": [f"{name}/x.go"] for name in names}
    result, _asked, runs = boxed(tmp_path, monkeypatch, project, indexes, listed, roots={""})
    assert len(runs) == 1 + go.PASSES and len(result["runs"]) == 1 + go.PASSES
    assert result["configs"]["constraints"][f"{names[-1]}/x.go"] == (
        f"build constraint `//go:build {names[-1]}`: not indexed, the further runs of one index stop at {go.PASSES}")
