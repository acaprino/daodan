"""Renovate in local extraction: `renovate --platform=local --dry-run=extract`, report read from a file.

Every manager reports the files it understands with their dependencies. Toolchain versions are the dependencies
of the version-file managers, the engine fields of package manifests and the directives of go.mod and
pyproject.toml, plus the base image of a Dockerfile when it names a runtime. The rest are dependencies. Renovate
reads the files, not the tracked set, only when the directory is not a git repository. Standard library only."""
from __future__ import annotations

import json
from pathlib import Path

from _versions import canon, sh

VERSION = "44.239.1"
VERSION_MANAGERS = {"asdf", "mise", "proto", "nvm", "nodenv", "pyenv", "rust-toolchain", "gradle-wrapper",
                    "maven-wrapper", "bazelisk", "ruby-version", "bun-version"}
TOOL_DEPTYPES = {"engines", "packageManager", "volta", "golang", "toolchain", "requires-python"}
DOCKER_RUNTIMES = {"node": "node", "python": "python", "golang": "go", "rust": "rust", "ruby": "ruby",
                   "openjdk": "java", "eclipse-temurin": "java", "amazoncorretto": "java", "maven": "maven",
                   "gradle": "gradle"}
SCOPE = {"dependencies": "runtime", "devDependencies": "dev", "peerDependencies": "peer",
         "optionalDependencies": "optional", "compile": "runtime", "runtime": "runtime", "test": "test",
         "provided": "build", "dev-dependencies": "dev", "build-dependencies": "build", "project.dependencies": "runtime"}


def run(fixture_dir, work_dir) -> dict:
    work = Path(work_dir)
    report = work / "renovate-report.json"
    env = {"RENOVATE_BASE_DIR": str(work / "renovate"), "LOG_LEVEL": "warn", "NO_COLOR": "1",
           "RENOVATE_ONBOARDING": "false", "RENOVATE_REQUIRE_CONFIG": "ignored"}
    r = sh(["renovate", "--platform=local", "--dry-run=extract", "--report-type=file", f"--report-path={report}"],
           fixture_dir, env, timeout=600)
    if r["rc"] != 0 or not report.exists():
        raise RuntimeError(f"renovate exit {r['rc']}: {r['err'].strip()[-400:] or r['out'].strip()[-400:]}")
    repo = json.loads(report.read_text(encoding="utf-8"))["repositories"]["local"]
    toolchains, dependencies = [], []
    for manager, files in (repo.get("packageFiles") or {}).items():
        for f in files:
            path = f.get("packageFile")
            for d in f.get("deps") or []:
                name, current = d.get("depName") or d.get("packageName"), d.get("currentValue")
                if not name:
                    continue
                tool = None
                if manager in VERSION_MANAGERS or d.get("depType") in TOOL_DEPTYPES:
                    tool = canon(name)
                elif manager in ("dockerfile", "docker-compose", "devcontainer") and name in DOCKER_RUNTIMES:
                    tool = DOCKER_RUNTIMES[name]
                if tool:
                    item = {"tool": tool, "declared_in": path, "via": d.get("depType") or manager}
                    if current is not None:
                        item["version"] = current
                    toolchains.append(item)
                    continue
                item = {"name": name, "declared": current, "declared_in": path}
                if d.get("lockedVersion") is not None:
                    item["resolved"] = str(d["lockedVersion"])
                if SCOPE.get(d.get("depType")):
                    item["scope"] = SCOPE[d["depType"]]
                dependencies.append(item)
    # Constraints a manager extracted from a manifest without listing them as dependencies (requires-python of a
    # project that has dependencies, for one): its own `extractedConstraints`, keys starting with % are internal.
    for manager, files in (repo.get("packageFiles") or {}).items():
        for f in files:
            path = f.get("packageFile")
            known = {(t["tool"], t["declared_in"]) for t in toolchains}
            for key, value in (f.get("extractedConstraints") or {}).items():
                tool = canon(key)
                if not key.startswith("%") and (tool, path) not in known and isinstance(value, str):
                    toolchains.append({"tool": tool, "version": value, "declared_in": path, "via": "extractedConstraints"})
    return {"toolchains": toolchains, "dependencies": dependencies}
