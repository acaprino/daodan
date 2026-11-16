"""The scip-go adapter's own rules: the names of Go's universe scope, which scip-go writes no occurrence of
(`prepare`), and the files the indexer's build leaves out, indexed by further runs under a configuration the go
tool says builds them (`configuration`, `index`), against the fake programs of `test_codebase_map_indexers.py`.

    python -B -m pytest -q -p no:cacheprovider tests/test_codebase_map_indexers_go.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "plugins/codebase-map/skills/map/scripts"
for path in (str(SCRIPTS), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import code_graph  # noqa: E402
from indexers import go  # noqa: E402
from test_codebase_map_code_graph import document, occurrence  # noqa: E402
from test_codebase_map_indexers import _tools, sandbox  # noqa: E402,F401

STDLIB = "scip-go gomod github.com/golang/go/src "
TARGET = ("linux", "amd64")


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
LISTED = {"GOOS=darwin": {"GoFiles": ["backend_other.go", "store.go"]},
          "GOOS=windows": {"GoFiles": ["backend_windows.go", "store.go"]},
          "-tags=integration": {"GoFiles": ["backend_linux.go", "store.go"], "XTestGoFiles": ["integration_test.go"]},
          "./store/gen.go": {"GoFiles": ["gen.go"]}}


def configured(command: list[str], env: dict) -> str:
    """Which of `WRITTEN` a run is: its program, its tags, a GOOS other than the indexer's, or that build."""
    if "./store/gen.go" in command:
        return "./store/gen.go"
    if "-tags=integration" in env.get("GOFLAGS", ""):
        return "-tags=integration"
    return f"GOOS={env['GOOS']}" if env.get("GOOS", TARGET[0]) != TARGET[0] else ""


def test_a_file_the_indexers_build_leaves_out_is_indexed_under_a_configuration_that_builds_it(sandbox, monkeypatch):
    project = sandbox["root"] / "project"
    for rel, text in FILES.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8", newline="\n")
    _tools(project, "go")
    monkeypatch.setattr(go, "_target", lambda: TARGET)
    fake, runs = sandbox["fake"], []

    def run(command, *args, **kwargs):
        command, env = [str(part) for part in command], kwargs.get("env") or {}
        if len(command) > 3 and command[0] == sys.executable and command[1] == "-c":
            command = command[3:]  # code_graph.measured's memory probe
        if command[1:3] == ["env", "CGO_ENABLED"]:
            return subprocess.CompletedProcess(command, 0, "1\n", "")
        if command[1:2] == ["list"]:
            which = configured(command, env)
            folder = Path(kwargs["cwd"]) / "store"
            return subprocess.CompletedProcess(command, 0, json.dumps({"Dir": str(folder), **LISTED[which]}), "")
        output = next((part.split("=", 1)[1] for part in command if part.startswith("--output=")), None)
        if output is not None:
            which = configured(command, env)
            runs.append((which, command[2:], env))
            Path(output).write_bytes(b"".join(document(rel, []) for rel in WRITTEN[which]))
            return subprocess.CompletedProcess(command, 0, "", "")
        return fake(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    result = go.index(project, sandbox["root"] / "work", roots={""})
    assert [which for which, _patterns, _env in runs] == ["", "GOOS=darwin", "GOOS=windows", "./store/gen.go",
                                                          "-tags=integration"]  # in the files' order
    by = {which: (patterns, env) for which, patterns, env in runs}
    assert by["GOOS=darwin"][0] == ["./store"] and by["GOOS=darwin"][1]["GOARCH"] == "amd64"
    assert by["-tags=integration"][1]["GOFLAGS"].endswith(" -tags=integration")  # beside the indexer's own flags
    assert by["./store/gen.go"][0] == ["./store/gen.go"] and "GOOS" not in by["./store/gen.go"][1]
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


def test_a_configuration_the_go_tool_does_not_list_the_file_under_is_said_and_runs_nothing(sandbox, monkeypatch):
    project = sandbox["root"] / "project"
    for rel in ("go.mod", "main.go", "store/store.go", "store/backend_linux.go", "store/backend_windows.go"):
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(FILES[rel], encoding="utf-8", newline="\n")
    _tools(project, "go")
    monkeypatch.setattr(go, "_target", lambda: TARGET)
    fake, runs = sandbox["fake"], []

    def run(command, *args, **kwargs):
        command, env = [str(part) for part in command], kwargs.get("env") or {}
        if len(command) > 3 and command[0] == sys.executable and command[1] == "-c":
            command = command[3:]
        if command[1:3] == ["env", "CGO_ENABLED"]:
            return subprocess.CompletedProcess(command, 0, "0\n", "")
        if command[1:2] == ["list"]:  # an error of the go tool: no package listed
            return subprocess.CompletedProcess(command, 1, "", "go: unsupported GOOS/GOARCH pair windows/amd64\n")
        output = next((part.split("=", 1)[1] for part in command if part.startswith("--output=")), None)
        if output is not None:
            runs.append(command)
            Path(output).write_bytes(b"".join(document(rel, []) for rel in WRITTEN[""]))
            return subprocess.CompletedProcess(command, 0, "", "")
        return fake(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    result = go.index(project, sandbox["root"] / "work", roots={""})
    assert len(runs) == 1
    assert result["configs"]["constraints"] == {
        "store/backend_windows.go": "file name constraint `windows`: `go list` under GOOS=windows does not list it"}
