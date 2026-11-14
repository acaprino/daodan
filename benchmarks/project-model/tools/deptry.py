"""deptry: Python imports set against the declared dependencies; for projects that declare little or nothing.

deptry reads the declarations from pyproject.toml, or requirements.txt / requirements.in, in its working folder,
and stops with an error when it finds none (dependency_getter/builder.py, DependencySpecificationNotFoundError). So
it runs in the project folder, and when none of those three files is there the adapter hands it an empty
requirements file outside the project: "nothing is declared", which is the truth there. No switch is needed for
network or processes; that it reads imports without importing modules is what the canary measures. deptry maps a
module to a package through the environment it runs in (an installed PyYAML makes `yaml` a "transitive" DEP003
instead of a missing DEP001), so it runs from a virtual environment of its own, /opt/deptry, holding only deptry.

What the answer holds: no facet of the shared shape (deptry does not list the declared dependencies), so the
output is empty and every facet is "not given". `honesty()` gives its findings: DEP001 (imported, missing from the declarations) and DEP003 (imported, only a
transitive dependency), with file and line, as deptry writes them: a module name, never a package name.
"""
from __future__ import annotations

import json
from pathlib import Path

import _sbom  # the driver puts tools/ on sys.path

VERSION = "0.25.1"
COMMAND = "deptry . --json-output <out> --no-ansi, in the project folder; --requirements-files <empty> when no declaration file"
OK = (0, 1)  # 1: violations found
CWD = "project"  # deptry reads its configuration and declarations from the working folder
CANARY = True
DECLARATION_FILES = ("pyproject.toml", "requirements.txt", "requirements.in")  # what deptry looks for by itself


def command(fixture_dir, work_dir) -> tuple[list, dict, Path]:
    out = Path(work_dir) / "deptry.json"
    argv = ["/opt/deptry/bin/deptry", ".", "--json-output", str(out), "--no-ansi"]
    if not any((Path(fixture_dir) / name).is_file() for name in DECLARATION_FILES):
        empty = Path(work_dir) / "declared-nothing.txt"
        empty.write_text("", encoding="utf-8")
        argv += ["--requirements-files", str(empty)]
    return argv, {}, out


def parse(out: Path, fixture_dir) -> dict:
    json.loads(Path(out).read_text(encoding="utf-8"))  # an unreadable report is an error, not an empty answer
    return {}


def honesty(out: Path, fixture_dir) -> dict:
    """{undeclared: [module], packages: [package names the tool states], findings: [...]}"""
    report = json.loads(Path(out).read_text(encoding="utf-8"))
    findings = [{"code": v["error"]["code"], "module": v.get("module"),
                 "file": _sbom.rel((v.get("location") or {}).get("file"), fixture_dir),
                 "line": (v.get("location") or {}).get("line")} for v in report]
    return {"undeclared": sorted({f["module"] for f in findings if f["code"] in ("DEP001", "DEP003") and f["module"]}),
            "packages": [], "findings": findings}


def run(fixture_dir, work_dir) -> dict:
    argv, env, out = command(fixture_dir, work_dir)
    done = _sbom.sh(argv, fixture_dir, env)
    if done["rc"] not in OK or not out.is_file():
        raise RuntimeError(f"deptry rc={done['rc']}: {done['err'][-800:]}")
    return parse(out, fixture_dir)
