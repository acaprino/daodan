"""dependency-cruiser without configuration: JavaScript and TypeScript imports, for projects with little or nothing
declared.

Run with `--no-config`: a `.dependency-cruiser.js` or the webpack and babel configurations it may be pointed at are
JavaScript it would load, so none is read. Node is called by its absolute path, so the shims on PATH do not stand
in for it. No network feature.

What the answer holds: no facet of the shared shape (it resolves imports, it does not list declarations), so the
output is empty. `honesty()` gives the imports it could not resolve that are neither relative nor core modules, as
written in the source: dependency-cruiser does not turn an import into a package name.
"""
from __future__ import annotations

import json
from pathlib import Path

import _sbom  # the driver puts tools/ on sys.path

VERSION = "18.7.2"
NODE = "/opt/node/bin/node"
CLI = "/opt/node/lib/node_modules/dependency-cruiser/bin/dependency-cruiser.mjs"  # package.json "bin"
COMMAND = "node bin/dependency-cruiser.mjs --no-config --output-type json --output-to <out> . (in the project folder)"
CWD = "project"
CANARY = True


def command(fixture_dir, work_dir) -> tuple[list, dict, Path]:
    out = Path(work_dir) / "depcruise.json"
    return [NODE, CLI, "--no-config", "--output-type", "json", "--output-to", str(out), "."], {}, out


def parse(out: Path, fixture_dir) -> dict:
    json.loads(Path(out).read_text(encoding="utf-8"))
    return {}


def honesty(out: Path, fixture_dir) -> dict:
    report = json.loads(Path(out).read_text(encoding="utf-8"))
    findings = []
    for module in report.get("modules") or []:
        for dep in module.get("dependencies") or []:
            types = dep.get("dependencyTypes") or []
            if dep.get("couldNotResolve") and not dep["module"].startswith(".") and "core" not in types:
                findings.append({"module": dep["module"], "file": module.get("source"), "types": types})
    return {"undeclared": sorted({f["module"] for f in findings}), "packages": [], "findings": findings}


def run(fixture_dir, work_dir) -> dict:
    argv, env, out = command(fixture_dir, work_dir)
    done = _sbom.sh(argv, fixture_dir, env)
    if done["rc"] != 0 or not out.is_file():
        raise RuntimeError(f"dependency-cruiser rc={done['rc']}: {done['err'][-800:]}")
    return parse(out, fixture_dir)
