"""pip: what `pip install --dry-run --report` says about a project or a requirements file, installing nothing.

For each directory with a pyproject.toml, setup.py or setup.cfg (a walk by file name), `pip install --dry-run
--no-deps --ignore-installed --report` on the directory: pip asks the project's build backend for its metadata
(name, version, Requires-Dist, Requires-Python), which runs the backend and, for setuptools, setup.py. For each
requirements.txt, the same with `-r`: pip resolves the whole set against the index and marks the requested
(direct) ones.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import native_common as common

try:
    from packaging.requirements import Requirement
except ImportError:  # pip's own copy
    from pip._vendor.packaging.requirements import Requirement

VERSION = "pip 23.3.2 of the image's Python 3.12.1"
VERSION_COMMAND = [sys.executable, "-m", "pip", "--version"]
TRIGGERS = ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")
COMMAND = "pip install --dry-run --no-deps --ignore-installed --report R <dir>; pip install --dry-run --report R -r requirements.txt"
BASE = [sys.executable, "-m", "pip", "install", "--dry-run", "--ignore-installed", "--quiet",
        "--disable-pip-version-check", "--no-input"]


def run(fixture_dir, work_dir) -> dict:
    root, work = Path(fixture_dir), Path(work_dir)
    found = common.find(root, set(TRIGGERS))
    projects = sorted({common.parent(p) for p in found if not p.endswith("requirements.txt")})
    requirements = [p for p in found if p.endswith("requirements.txt")]
    units, toolchains, dependencies, errors = [], [], [], []
    for n, directory in enumerate(projects):
        report = work / f"pip-report-{n}.json"
        done = common.run([*BASE, "--no-deps", "--report", str(report), str(root / directory)], work,
                          name="pip install --dry-run --report <dir>")
        data = common.json_or_none(report.read_text(encoding="utf-8")) if report.is_file() else None
        if done.returncode != 0 or not data or not data.get("install"):
            errors.append(f"{directory}: {common.error_of(done)}")
            continue
        meta = data["install"][0]["metadata"]
        manifest = next((common.join(directory, m) for m in ("pyproject.toml", "setup.py", "setup.cfg")
                         if (root / directory / m).is_file()), None)
        units.append({"name": meta.get("name"), "kind": "python-project", "root": directory, "manifest": manifest})
        if meta.get("requires_python"):
            toolchains.append({"tool": "python", "version": meta["requires_python"], "declared_in": manifest})
        for text in meta.get("requires_dist") or []:
            try:
                req = Requirement(text)
            except Exception:  # noqa: BLE001 - kept as written
                errors.append(f"{directory}: unparsed requirement {text}")
                continue
            dependencies.append({"unit": meta.get("name"), "name": req.name, "declared": str(req.specifier) or None,
                                 "scope": "optional" if req.marker and "extra" in str(req.marker) else "runtime",
                                 "declared_in": manifest})
    for n, path in enumerate(requirements):
        report = work / f"pip-req-{n}.json"
        done = common.run([*BASE, "--report", str(report), "-r", str(root / path)], root / common.parent(path),
                          name="pip install --dry-run --report -r requirements.txt")
        data = common.json_or_none(report.read_text(encoding="utf-8")) if report.is_file() else None
        if done.returncode != 0 or not data:
            errors.append(f"{path}: {common.error_of(done)}")
            continue
        for item in data.get("install") or []:
            if item.get("requested"):
                dependencies.append({"name": item["metadata"]["name"], "resolved": item["metadata"].get("version"),
                                     "scope": "runtime", "declared_in": path})
    common.NOTES.update(errors=errors, raw={})
    out = {"units": units, "toolchains": toolchains, "dependencies": dependencies}
    return out if projects else {"dependencies": dependencies}


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1], sys.argv[2]), indent=1))
