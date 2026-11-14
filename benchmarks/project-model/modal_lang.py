"""Facet `lang` of the project-model benchmark on Modal: which language each file is, which files to leave out.

Seven tools read every fixture of `fixtures/` (and two synthetic probe fixtures built here): Linguist (CLI and
gem classes), Linguist's data files through a standard-library reader, go-enry, scc, tokei, Magika and Daodan's
own detection. No model. Each tool runs on a fresh copy of each fixture (a Git repository with everything
committed, `expected.json` and `source.json` removed), three ways, all through `tools/<tool>.py`:

  net      one container, network on: traced by strace (execve, connect) for the child processes and the network
           attempts, then timed alone for seconds and peak memory; the folder is hashed before and after
  offline  one container with the network blocked: the same adapter; its answer is compared with `net`'s

The volume keeps `project-model/lang/<tool>-net.json` and `-offline.json`; `fetch` scores them with `score.py`
into `results/<tool>.json`. The adapters' hash is printed at container start and compared with the local one.

    modal deploy benchmarks/project-model/modal_lang.py
    python benchmarks/project-model/modal_lang.py spawn [--tools linguist,scc] [--fixtures js-bun,...]
    python benchmarks/project-model/modal_lang.py fetch [--tools ...]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import modal

HERE = Path(__file__).resolve().parent
LOCAL = modal.is_local()
ROOT = HERE if LOCAL else Path("/pm")
REPO = HERE.parents[1] if LOCAL else Path("/")
APP = "daodan-pm-lang"
TOOLS = ("linguist", "linguist_data", "enry", "scc", "tokei", "magika", "daodan")
GROUP = "lang"
STORE = "project-model/lang"
SRC = "project-model/lang-src"  # clones of the descriptor fixtures, one tar each, made with the network on
DATA = "/opt/linguist-data"
GO = "1.27.4"
VERSIONS = {"linguist": "9.7.0", "enry": "v2.9.6", "scc": "v4.1.0", "tokei": "15.0.0", "magika": "1.0.3"}
COMMANDS = {
    "linguist": "github-linguist --breakdown --json (+ tools/linguist_facts.rb over the same repository)",
    "linguist_data": "tools/linguist_data.py over languages/heuristics/vendor/documentation.yml and .gitattributes",
    "enry": "enry -json -all . (+ enry_facts, go-enry's IsVendor/IsDocumentation/IsGenerated/IsBinary)",
    "scc": "scc --by-file -f json --gen .",
    "tokei": "tokei -o json -f .",
    "magika": "magika.Magika().identify_paths(files)",
    "daodan": "languages.detect_language + tree_scope.Perimeter (plugin working tree)",
}
# Where each tool's release page says a Windows build exists, checked 2026-11-14 (README of this benchmark).
WINDOWS = {
    "linguist": "gem github-linguist 9.7.0, platform ruby only (rubygems.org lists no other platform for it, for rugged "
                "or for charlock_holmes): no Windows binary or wheel; the install compiles rugged (libgit2, cmake) and "
                "charlock_holmes (ICU) from source",
    "linguist_data": "tools/linguist_data.py over languages/heuristics/vendor/documentation.yml and .gitattributes",
    "enry": "enry -json -all . (+ enry_facts, go-enry's IsVendor/IsDocumentation/IsGenerated/IsBinary)",
    "scc": "scc --by-file -f json --gen .",
    "tokei": "tokei -o json -f .",
    "magika": "magika.Magika().identify_paths(files)",
    "daodan": "languages.detect_language + tree_scope.Perimeter (plugin working tree)",
}
# Where each tool's release page says a Windows build exists, checked 2026-11-14 (README of this benchmark).
WINDOWS = {
    "linguist": "gem github-linguist 9.7.0 (platform ruby: native extensions rugged and charlock_holmes built on "
                "install; no Windows binary or wheel)",
    "linguist_data": "no install: four MIT data files (languages.yml about 0.6 MB) read by Python",
    "enry": "v2.9.6 release has no assets; `go install` builds the CLI, cgo only with the oniguruma tag",
    "scc": "v4.1.0: scc_Windows_x86_64.zip 7,244,303 bytes (also i386 and arm64)",
    "tokei": "v15.0.0 release has no assets, nor do v14.0.0 and v13.0.0 (the last with binaries is v12.1.2); "
             "`cargo install tokei` builds it",
    "magika": "wheel magika-1.0.3-py3-none-win_amd64.whl 13,057,718 bytes (pure wheel 2,969,548 bytes); "
              "CLI magika-cli-x86_64-pc-windows-msvc.zip 10,076,032 bytes (cli/v1.1.0)",
    "daodan": "Python, in the plugin",
}

BUILD = [
    "apt-get update",
    "apt-get install -y --no-install-recommends ruby ruby-dev build-essential cmake pkg-config libicu-dev "
    "libssl-dev zlib1g-dev git curl ca-certificates xz-utils strace file",
    f"gem install github-linguist -v {VERSIONS['linguist']} --no-document",
    f"curl -fsSL https://go.dev/dl/go{GO}.linux-amd64.tar.gz | tar -C /usr/local -xz",
    f"GOBIN=/usr/local/bin /usr/local/go/bin/go install github.com/go-enry/go-enry/v2/cmd/enry@{VERSIONS['enry']}",
    f"curl -fsSL https://github.com/boyter/scc/releases/download/{VERSIONS['scc']}/scc_Linux_x86_64.tar.gz "
    "| tar -C /usr/local/bin -xz scc",
    "curl -fsSL https://sh.rustup.rs | sh -s -- -y --profile minimal",
    f"/root/.cargo/bin/cargo install tokei --version {VERSIONS['tokei']} --locked --root /usr/local",
]
GO_FACTS = (f"cd /opt/enryfacts && /usr/local/go/bin/go mod init enryfacts && /usr/local/go/bin/go get "
            f"github.com/go-enry/go-enry/v2@{VERSIONS['enry']} && "
            "/usr/local/go/bin/go build -o /usr/local/bin/enry_facts .")


def _convert() -> None:
    """Build step: the four Linguist data files of the installed gem as JSON."""
    import glob

    import yaml

    gem = glob.glob("/var/lib/gems/*/gems/github-linguist-*/lib/linguist")[0]
    out = Path(DATA)
    out.mkdir(parents=True, exist_ok=True)
    for name in ("languages", "heuristics", "vendor", "documentation"):
        with open(f"{gem}/{name}.yml", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        (out / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


def _image():
    image = (
        modal.Image.debian_slim(python_version="3.13")
        .run_commands(*BUILD)
        .pip_install(f"magika=={VERSIONS['magika']}", "pyyaml")
        .run_function(_convert)
        .add_local_file(ROOT / "tools/enry_facts.go", "/opt/enryfacts/main.go", copy=True)
        .run_commands(GO_FACTS)
        .env({"DAODAN_SCRIPTS": "/daodan/map/scripts", "LINGUIST_DATA": DATA})
    )
    return (
        image.add_local_dir(REPO / "plugins/codebase-map/skills/map" if LOCAL else Path("/daodan/map"), "/daodan/map",
                            ignore=["**/__pycache__/**", "**/tests/**"])
        .add_local_dir(ROOT / "tools", "/pm/tools", ignore=["**/__pycache__/**"])
        .add_local_dir(ROOT / "fixtures", "/pm/fixtures")
    )


app = modal.App(APP, image=_image())
volume = modal.Volume.from_name("daodan-flow-results", create_if_missing=True)

ADAPTER_FILES = [*(f"{t}.py" for t in TOOLS), "_lang.py", "linguist_facts.rb", "enry_facts.go"]


def code_sha256(folder: Path) -> str:
    """One hash over the adapters and their helpers, compared with the local one before trusting a run."""
    digest = hashlib.sha256()
    for name in sorted(ADAPTER_FILES):
        digest.update(name.encode() + b"\0" + (folder / name).read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


def plugin_sha256(scripts: Path) -> str:
    digest = hashlib.sha256()
    for name in ("languages/__init__.py", "tree_scope.py"):
        digest.update(name.encode() + b"\0" + (scripts / name).read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()


# --------------------------------------------------------------------------- probe fixtures

_MIN = "!function(){var a=1,b=2;" + "console.log(a+b);" * 60 + "}();\n"
PROBES = {
    "probe-mixed": {
        "files": {
            "src/main.c": "#include <stdio.h>\nint main(void) { return 0; }\n",
            "include/api.h": "#ifndef API_H\n#define API_H\nint api_call(int x);\n#endif\n",
            "include/vec.h": "#pragma once\n#include <vector>\nnamespace geo {\nclass Vec { public: std::vector<double> v; };\n}\n",
            "include/Cell.h": "#import <Foundation/Foundation.h>\n@interface Cell : NSObject\n@end\n",
            "tools/run": "#!/usr/bin/env python3\nprint(1)\n",
            "tools/deploy": "#!/bin/sh\necho hi\n",
            "tools/serve": "#!/usr/bin/env node\nconsole.log(1)\n",
            "db/schema.sql": "CREATE TABLE users (id integer PRIMARY KEY, name text);\n",
            "db/fn.sql": "CREATE OR REPLACE FUNCTION f() RETURNS integer AS $$\nBEGIN\n  RETURN 1;\nEND;\n$$ LANGUAGE plpgsql;\n",
            "db/pkg.pks": "CREATE OR REPLACE PACKAGE pkg AS\n  PROCEDURE p;\nEND pkg;\n/\n",
            "db/proc.sql": "CREATE PROCEDURE [dbo].[p]\nAS\nBEGIN\n  SET NOCOUNT ON;\n  SELECT 1;\nEND\nGO\n",
            "web/App.vue": "<template><p>hi</p></template>\n<script>export default { name: 'App' }</script>\n",
            "web/Card.svelte": "<script>let n = 0;</script>\n<button on:click={() => n++}>{n}</button>\n",
            "web/Page.astro": "---\nconst title = 'x';\n---\n<h1>{title}</h1>\n",
            "web/Box.tsx": "export const Box = (p: { n: number }) => <div>{p.n}</div>;\n",
            "web/legacy.jsx": "export const L = () => <p>hi</p>;\n",
            "web/styles.scss": "$c: red;\n.a { .b { color: $c; } }\n",
            "types/index.d.ts": "export declare function f(x: number): string;\n",
            "nb/analysis.ipynb": '{"cells":[],"metadata":{"kernelspec":{"language":"python","name":"python3"}},"nbformat":4,"nbformat_minor":5}\n',
            "Dockerfile": "FROM python:3.12\nRUN pip install x\n",
            "ci/build.dockerfile": "FROM alpine\nRUN echo hi\n",
            "Makefile": "all:\n\techo hi\n",
            "CMakeLists.txt": "cmake_minimum_required(VERSION 3.20)\nproject(p C)\n",
            "Gemfile": "source 'https://rubygems.org'\ngem 'rake'\n",
            "gen/api.pb.go": "// Code generated by protoc-gen-go. DO NOT EDIT.\n\npackage api\n",
            "src/schema_pb2.py": "# Generated by the protocol buffer compiler.  DO NOT EDIT!\n# source: schema.proto\nimport sys\n",
            "src/Parser.java": "// Generated from Calc.g4 by ANTLR 4.13.1\npackage calc;\npublic class Parser {}\n",
            "dist/app.min.js": _MIN,
            "node_modules/left-pad/index.js": "module.exports = function (s, n) { return s; };\n",
            "vendor/lib/util.c": "int util(void) { return 1; }\n",
            "docs/guide.md": "# Guide\n\nSome words.\n",
            "assets/logo.png": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + bytes(range(256)) * 3,
        },
        "languages": {
            "src/main.c": "C", "include/api.h": "C", "include/vec.h": "C++", "include/Cell.h": "Objective-C",
            "tools/run": "Python", "tools/deploy": "Shell", "tools/serve": "JavaScript", "db/schema.sql": "SQL",
            "db/fn.sql": "PLpgSQL", "db/pkg.pks": "PLSQL", "db/proc.sql": "TSQL", "web/App.vue": "Vue",
            "web/Card.svelte": "Svelte", "web/Page.astro": "Astro", "web/Box.tsx": "TSX",
            "web/legacy.jsx": "JavaScript", "web/styles.scss": "SCSS", "types/index.d.ts": "TypeScript",
            "nb/analysis.ipynb": "Jupyter Notebook", "Dockerfile": "Dockerfile", "ci/build.dockerfile": "Dockerfile",
            "Makefile": "Makefile", "CMakeLists.txt": "CMake", "Gemfile": "Ruby",
        },
        "excluded": [("gen/api.pb.go", "generated"), ("src/schema_pb2.py", "generated"),
                     ("src/Parser.java", "generated"), ("dist/app.min.js", "vendored"),
                     ("node_modules/", "vendored"), ("vendor/", "vendored"), ("docs/guide.md", "documentation"),
                     ("assets/logo.png", "binary")],
    },
    "probe-attrs": {
        "files": {
            ".gitattributes": ("legacy/*.txt linguist-language=Python\nvendor/ours/** linguist-vendored=false\n"
                               "src/big.js linguist-generated\ndocs/spec.py linguist-documentation=false\n"
                               "build/** linguist-vendored\n*.inc linguist-language=C++\n"),
            "legacy/code.txt": "def f():\n    return 1\n",
            "vendor/ours/a.js": "var a = 1;\n",
            "vendor/theirs/b.js": "var b = 2;\n",
            "src/big.js": "var big = 1;\n",
            "docs/spec.py": "def spec():\n    pass\n",
            "docs/other.md": "# other\n",
            "build/out.js": "var out = 1;\n",
            "lib/x.inc": "int x;\n",
        },
        "languages": {"legacy/code.txt": "Python", "vendor/ours/a.js": "JavaScript", "docs/spec.py": "Python",
                      "lib/x.inc": "C++"},
        "excluded": [("vendor/theirs/b.js", "vendored"), ("src/big.js", "generated"),
                     ("docs/other.md", "documentation"), ("build/out.js", "vendored")],
    },
}


def probe_expected(name: str) -> dict:
    probe = PROBES[name]
    return {"languages": [{"path": p, "language": lang} for p, lang in probe["languages"].items()],
            "excluded": [{"path": p, "why": why} for p, why in probe["excluded"]]}


# --------------------------------------------------------------------------- container side

RUN_ONE = '''
import importlib.util, json, sys, time, traceback
tool, fixture, work, out = sys.argv[1:5]
sys.path.append("/pm/tools")
spec = importlib.util.spec_from_file_location("adapter_" + tool, f"/pm/tools/{tool}.py")
module = importlib.util.module_from_spec(spec)
started = time.time()
try:
    spec.loader.exec_module(module)
    result = {"output": module.run(fixture, work), "version": module.VERSION}
except BaseException:
    result = {"error": traceback.format_exc()[-3000:]}
result["seconds"] = round(time.time() - started, 3)
open(out, "w", encoding="utf-8").write(json.dumps(result))
'''
PROJECT_TOOLS = {"npm", "npx", "node", "yarn", "pnpm", "bun", "deno", "go", "cargo", "rustc", "pip", "pip3", "uv",
                 "poetry", "pdm", "pipenv", "hatch", "conda", "mvn", "mvnw", "gradle", "gradlew", "sbt", "java",
                 "javac", "kotlinc", "dotnet", "nuget", "composer", "php", "bundle", "mix", "elixir", "swift", "dart",
                 "flutter", "cmake", "make", "conan", "vcpkg", "bazel", "meson", "ninja", "gcc", "cc", "g++", "clang"}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _snapshot(root: Path) -> tuple[dict, dict]:
    """Hash of every file: (outside .git, inside .git)."""
    import os
    outside, inside = {}, {}
    for folder, dirs, names in os.walk(root):
        for name in names:
            path = Path(folder) / name
            rel = path.relative_to(root).as_posix()
            try:
                value = "link:" + os.readlink(path) if path.is_symlink() else _sha(path.read_bytes())
            except OSError:
                value = "unreadable"
            (inside if rel.startswith(".git/") else outside)[rel] = value
    return outside, inside


def _cases(only: list[str]) -> list[str]:
    folder = Path("/pm/fixtures")
    names = sorted(d.name for d in folder.iterdir()
                   if d.is_dir() and not d.name.startswith("_") and (d / "expected.json").exists())
    names += sorted(PROBES)
    return [n for n in names if not only or n in only]


def _prepare(name: str, destination: Path) -> bool:
    """A fresh Git repository holding the fixture's files, everything committed; False if it has no files."""
    import shutil
    import subprocess
    shutil.rmtree(destination, ignore_errors=True)
    if (Path("/pm/fixtures") / name / "source.json").exists():
        import tarfile
        archive = Path("/results") / SRC / f"{name}.tar"
        if not archive.exists():
            return False
        destination.mkdir(parents=True)
        with tarfile.open(archive) as tar:
            tar.extractall(destination, filter="tar")
        return True  # a clone at its pinned commit: already a repository, nothing to commit
    if name in PROBES:
        for rel, content in PROBES[name]["files"].items():
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
    else:
        shutil.copytree(Path("/pm/fixtures") / name, destination, symlinks=True)
        for dropped in ("expected.json", "source.json"):
            (destination / dropped).unlink(missing_ok=True)
    if not any(p.is_file() or p.is_symlink() for p in destination.rglob("*")):
        return False
    git = ["git", "-c", "user.name=pm", "-c", "user.email=pm@local", "-c", "commit.gpgsign=false",
           "-c", "core.autocrlf=false"]
    for command in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "fixture"]):
        subprocess.run(git + command, cwd=destination, capture_output=True, check=True)
    return True


def _parse_strace(log: str, fixture: Path) -> dict:
    import re
    executed, destinations, lines = [], set(), []
    for line in log.splitlines():
        match = re.search(r'execve\("([^"]+)".*\)\s+=\s+0\s*$', line)
        if match:
            executed.append(match.group(1))
            continue
        if "connect(" not in line and "sendto(" not in line:
            continue
        v4 = re.search(r'sin_port=htons\((\d+)\), sin_addr=inet_addr\("([^"]+)"\)', line)
        v6 = re.search(r'sin6_port=htons\((\d+)\).*inet_pton\(AF_INET6, "([^"]+)"', line)
        found = v4 or v6
        if found:
            port, address = found.group(1), found.group(2)
            if address.startswith("127.") or address in ("::1", "0.0.0.0", "::"):
                continue
            destinations.add(f"{address}:{port}")
            lines.append(line[:240])
    names = sorted({Path(p).name for p in executed})
    inside = sorted({p for p in executed if str(fixture) in p})
    tools = sorted(n for n in names if n in PROJECT_TOOLS)
    return {"executed": names, "project_exe": inside, "build_tools": tools, "network": sorted(destinations), "network_lines": lines[:6]}


EXEC_TIMEOUT = 150  # seconds for one tool execution on one fixture; a longer one is killed and recorded as an error


def _timed(command: list[str], cwd: str | None = None) -> tuple[float, float, int]:
    """Seconds, peak memory in MB (the child and what it waited for) and exit code of a command."""
    import os
    import resource
    import subprocess
    import time
    started = time.time()
    process = subprocess.Popen(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    import signal
    import threading
    timer = threading.Timer(EXEC_TIMEOUT, lambda: os.killpg(process.pid, signal.SIGKILL))
    timer.start()
    try:
        _, status, usage = os.wait4(process.pid, 0)
    finally:
        timer.cancel()
    process.returncode = os.waitstatus_to_exitcode(status)
    return round(time.time() - started, 3), round(usage.ru_maxrss / 1024, 1), process.returncode


def _tag_types(output: dict) -> dict:
    """Add Linguist's type to each language entry, so the scoring side needs no Linguist data."""
    sys.path.append("/pm/tools")
    from _lang import type_of
    for entry in output.get("languages") or []:
        entry["type"] = type_of(entry["language"])
    return output


def _norm(output: dict) -> dict:
    out = {k: v for k, v in output.items() if k != "_raw"}
    for key in ("languages", "excluded"):
        if key in out:
            out[key] = sorted(out[key], key=lambda e: (e.get("path", ""), e.get("language", ""), e.get("why", "")))
    return out


def _serve(tool: str, mode: str, only: list[str]) -> dict:
    import subprocess
    import tempfile
    import time
    started = time.time()
    local = code_sha256(Path("/pm/tools"))
    print("adapters", local, "plugin", plugin_sha256(Path("/daodan/map/scripts")), flush=True)
    runner = Path("/tmp/run_one.py")
    runner.write_text(RUN_ONE, encoding="utf-8")
    python = [sys.executable, "-I", str(runner)]
    base_seconds, base_mb, _ = _timed([sys.executable, "-I", "-c", "pass"])
    meta = {"tool": tool, "mode": mode, "adapters_sha256": local, "plugin_sha256": plugin_sha256(Path("/daodan/map/scripts")),
            "baseline": {"seconds": base_seconds, "peak_mb": base_mb}, "strace": None}
    if mode == "net":
        control = Path("/tmp/control.log")
        snippet = ("import socket, subprocess\nsubprocess.run(['/bin/true'])\ns = socket.socket()\ns.settimeout(1)\n"
                   "try:\n    s.connect(('192.0.2.1', 9))\nexcept OSError:\n    pass\n")
        subprocess.run(["strace", "-f", "-qq", "-e", "trace=execve,connect,sendto", "-o", str(control), sys.executable,
                        "-I", "-c", snippet], capture_output=True)
        meta["control"] = _parse_strace(control.read_text(errors="replace"), Path("/nonexistent")) if control.exists() else None
    out: dict = {"meta": meta, "fixtures": {}}
    target = Path("/results") / STORE / f"{tool}-{mode}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    kept = {}
    if only and target.exists():  # a rerun of some fixtures keeps the others
        kept = json.loads(target.read_text(encoding="utf-8")).get("fixtures", {})

    def save(data: dict, commit: bool = True) -> None:
        target.write_text(json.dumps({**data, "fixtures": {**kept, **data["fixtures"]}}), encoding="utf-8")
        if commit:  # a volume commit takes about 12 s: every fifth fixture, and at the end
            volume.commit()

    work = Path("/work") / tool
    for name in _cases(only):
        fixture = work / name
        record: dict = {}
        out["fixtures"][name] = record
        if not _prepare(name, fixture):
            record["skipped"] = "no files (a descriptor fixture whose clone is not on the volume, or an empty folder)"
            continue
        scratch = Path(tempfile.mkdtemp(prefix="scratch-"))
        result_file = scratch / "result.json"
        before, before_git = _snapshot(fixture)
        if mode == "net":
            log = scratch / "strace.log"
            try:
                traced = subprocess.run(["strace", "-f", "-qq", "-e", "trace=execve,connect,sendto", "-s", "300",
                                         "-o", str(log)] + python + [tool, str(fixture), str(scratch), str(result_file)],
                                        capture_output=True, text=True, timeout=EXEC_TIMEOUT)
            except subprocess.TimeoutExpired:
                traced = subprocess.CompletedProcess([], 124, "", f"traced run over {EXEC_TIMEOUT}s")
            if log.exists() and log.stat().st_size:
                record["trace"] = _parse_strace(log.read_text(errors="replace"), fixture)
                meta["strace"] = True
            else:
                meta["strace"] = meta["strace"] or False
                record["trace_error"] = (traced.stderr or "no strace log")[-300:]
            first = json.loads(result_file.read_text()) if result_file.exists() else {"error": "no result file"}
            after, after_git = _snapshot(fixture)
            record["wrote"] = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))[:10]
            record["wrote_git"] = before_git != after_git
            result_file.unlink(missing_ok=True)
        seconds, peak, code = _timed(python + [tool, str(fixture), str(scratch), str(result_file)])
        second = json.loads(result_file.read_text()) if result_file.exists() else {"error": f"no result file ({code})"}
        if mode == "net":
            after2, after2_git = _snapshot(fixture)
            record["wrote"] = sorted(set(record["wrote"]) | {k for k in set(before) | set(after2) if before.get(k) != after2.get(k)})[:10]
            record["wrote_git"] = record["wrote_git"] or before_git != after2_git
        if mode == "net":
            record["output_traced_equals_timed"] = _norm(first.get("output") or {}) == _norm(second.get("output") or {})
        record.update({"seconds": seconds, "adapter_seconds": second.get("seconds"), "peak_mb": peak,
                       "version": second.get("version")})
        if "error" in second:
            record["error"] = second["error"]
        else:
            output = second["output"]
            record["raw"] = output.get("_raw")
            record["output"] = _norm(_tag_types(output))
        subprocess.run(["rm", "-rf", str(scratch)])
        meta["seconds"] = round(time.time() - started, 1)
        save(out, commit=len(out["fixtures"]) % 5 == 0)  # a stopped run keeps what it did, five fixtures at most lost
    meta["seconds"] = round(time.time() - started, 1)
    save(out)
    return {"tool": tool, "mode": mode, "fixtures": len(out["fixtures"]), "seconds": meta["seconds"], "strace": meta["strace"]}


@app.function(cpu=1, memory=2048, timeout=1800, volumes={"/results": volume})
def clone(only: list[str] | None = None) -> dict:
    """Clone every descriptor fixture (source.json: repo, commit) at its commit into a tar on the volume."""
    import subprocess
    import tarfile
    import tempfile
    done = {}
    for name in sorted(d.name for d in Path("/pm/fixtures").iterdir() if (d / "source.json").exists()):
        if only and name not in only:
            continue
        archive = Path("/results") / SRC / f"{name}.tar"
        if archive.exists():
            done[name] = "cached"
            continue
        info = json.loads((Path("/pm/fixtures") / name / "source.json").read_text(encoding="utf-8"))
        folder = Path(tempfile.mkdtemp(prefix="clone-"))
        try:
            for command in (["init", "-q"], ["remote", "add", "origin", info["repo"]],
                            ["fetch", "-q", "--depth", "1", "origin", info["commit"]], ["checkout", "-q", "FETCH_HEAD"]):
                subprocess.run(["git"] + command, cwd=folder, capture_output=True, check=True, timeout=900)
        except subprocess.SubprocessError as exc:
            done[name] = f"failed: {str(exc)[-200:]}"
            continue
        archive.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, "w") as tar:
            tar.add(folder, arcname=".")
        done[name] = archive.stat().st_size
        subprocess.run(["rm", "-rf", str(folder)])
        volume.commit()
    return done


@app.function(cpu=1, memory=4096, timeout=2700, volumes={"/results": volume})
def net(tool: str, only: list[str] | None = None) -> dict:
    return _serve(tool, "net", only or [])


@app.function(cpu=1, memory=4096, timeout=2700, volumes={"/results": volume}, block_network=True)
def offline(tool: str, only: list[str] | None = None) -> dict:
    return _serve(tool, "offline", only or [])


@app.function(cpu=1, memory=4096, timeout=600, volumes={"/results": volume})
def magika_net(name: str) -> str:
    """Where Magika's connection on a large repository comes from: a Python audit hook on socket.connect and
    getaddrinfo while it identifies the files, and the thread that makes each call."""
    import sys
    import tarfile
    import threading
    import traceback
    folder = Path("/work/net-check")
    folder.mkdir(parents=True, exist_ok=True)
    with tarfile.open(Path("/results") / SRC / f"{name}.tar") as tar:
        tar.extractall(folder, filter="tar")
    sys.path.append("/pm/tools")
    events = []

    def hook(event, args):
        if event in ("socket.connect", "socket.getaddrinfo", "socket.__new__"):
            events.append(f"{event} {str(args)[:120]} thread={threading.current_thread().name}"
                          + chr(10) + "".join(traceback.format_stack(limit=6)))

    sys.addaudithook(hook)
    import importlib.util
    spec = importlib.util.spec_from_file_location("adapter_magika", "/pm/tools/magika.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.run(str(folder), "/tmp")
    return f"python-level network events: {len(events)}" + chr(10) + chr(10).join(events[:4])


@app.function(cpu=1, memory=2048, timeout=600)
def probe(commands: list[str]) -> str:
    import subprocess
    out = []
    for command in commands:
        done = subprocess.run(["bash", "-c", command], capture_output=True, text=True, timeout=300)
        out.append(f"$ {command}\n[{done.returncode}]\n{done.stdout[-5000:]}\n{done.stderr[-2000:]}")
    return "\n".join(out)


# --------------------------------------------------------------------------- local side

def _read(path: str) -> dict | None:
    try:
        return json.loads(b"".join(volume.read_file(path)))
    except Exception:
        return None


def _filtered(output: dict) -> dict:
    """The same answer with data and prose languages left out: Linguist's default for what counts as code."""
    keep = {"programming", "markup"}
    return {**output, "languages": [e for e in output.get("languages", []) if e.get("type") in keep]}


def fetch(tools: list[str]) -> None:
    sys.path.insert(0, str(HERE))
    import score as scoring

    local = code_sha256(HERE / "tools")
    for tool in tools:
        net_data, off_data = _read(f"{STORE}/{tool}-net.json"), _read(f"{STORE}/{tool}-offline.json")
        if not net_data:
            print(tool, "no net result on the volume")
            continue
        if net_data["meta"]["adapters_sha256"] != local:
            print(tool, "WARNING: adapters on the volume differ from the local ones")
        offline = (off_data or {}).get("fixtures", {})
        results, version = {}, None
        for name, record in net_data["fixtures"].items():
            expected_file = HERE / "fixtures" / name / "expected.json"
            if name in PROBES:
                expected = probe_expected(name)
            elif expected_file.exists():
                expected = json.loads(expected_file.read_text(encoding="utf-8"))
            else:
                continue
            entry = {k: record[k] for k in ("seconds", "peak_mb", "raw", "wrote", "wrote_git", "skipped") if k in record}
            if name in PROBES:
                entry["probe"] = True
            version = version or record.get("version")
            trace = record.get("trace")
            if trace is not None:
                entry["network_attempts"] = len(trace["network"])
                if trace["network"]:
                    entry["network_destinations"] = trace["network"]
                    entry["network_lines"] = trace.get("network_lines")
                entry["children"] = trace["executed"]
                entry["executed_project_code"] = "yes" if (trace["project_exe"] or trace["build_tools"]) else "no"
            else:
                entry["executed_project_code"] = "unknown"
            if "error" in record:
                entry["error"] = record["error"]
            elif "output" in record:
                output = record["output"]
                entry["output"] = output
                entry["score"] = scoring.score(expected, output)
                entry["score_code"] = scoring.score(expected, _filtered(output))
                other = offline.get(name)
                entry["offline_second_run"] = bool(other and "output" in other and other["output"] == output)
                if other and "error" in other:
                    entry["offline_error"] = other["error"][-200:]
            results[name] = entry
        document = {"tool": tool, "version": version or VERSIONS.get(tool), "group": GROUP,
                    "command": COMMANDS[tool], "windows": WINDOWS[tool],
                    "run": {"adapters_sha256": net_data["meta"]["adapters_sha256"],
                            "plugin_sha256": net_data["meta"]["plugin_sha256"], "strace": net_data["meta"]["strace"],
                            "baseline_python_run": net_data["meta"]["baseline"], "network_control": net_data["meta"].get("control"), "seconds": net_data["meta"]["seconds"]},
                    "fixtures": results}
        target = HERE / "results" / f"{tool}.json"
        target.parent.mkdir(exist_ok=True)
        # One line per fixture, `output` without Linguist's type tag: small file, diffs by fixture.
        for entry in results.values():
            for item in (entry.get("output") or {}).get("languages", []):
                item.pop("type", None)
        head = json.dumps({k: v for k, v in document.items() if k != "fixtures"}, ensure_ascii=False)[:-1]
        body = ",\n".join(f" {json.dumps(n)}: {json.dumps(r, ensure_ascii=False, separators=(',', ':'))}"
                          for n, r in sorted(results.items()))
        target.write_text(f'{head}, "fixtures": {{\n{body}\n}}}}\n', encoding="utf-8", newline="\n")
        print(tool, len(results), "fixtures,", sum(1 for r in results.values() if "error" in r), "errors ->", target)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("probe", "clone", "spawn", "fetch", "magika-net"))
    parser.add_argument("--tools", default=",".join(TOOLS))
    parser.add_argument("--fixtures", default="")
    parser.add_argument("--modes", default="net,offline")
    parser.add_argument("--file", help="with probe: a file holding one shell command per line")
    args = parser.parse_args()
    chosen = [t.strip() for t in args.tools.split(",") if t.strip()]
    only = [f.strip() for f in args.fixtures.split(",") if f.strip()]
    if args.command == "probe":
        lines = [line for line in Path(args.file).read_text(encoding="utf-8").splitlines() if line.strip()]
        print(modal.Function.from_name(APP, "probe").remote(lines))
    elif args.command == "magika-net":
        print(modal.Function.from_name(APP, "magika_net").remote(only[0]))
    elif args.command == "clone":
        print(modal.Function.from_name(APP, "clone").remote(only))
    elif args.command == "spawn":
        print("local adapters", code_sha256(HERE / "tools"))
        print("local plugin", plugin_sha256(REPO / "plugins/codebase-map/skills/map/scripts"))
        for mode in args.modes.split(","):
            function = modal.Function.from_name(APP, mode)
            for tool in chosen:
                print(mode, tool, function.spawn(tool, only).object_id)
    else:
        fetch(chosen)
