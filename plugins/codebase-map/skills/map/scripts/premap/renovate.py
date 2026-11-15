"""Source: Renovate's local extraction, a separate program Daodan starts and reads (AGPL-3.0: no code of it here).

`commands` describes, for Daodan's container, one `renovate --platform=local --dry-run=extract` at the
project's root with the report written to stdout and the log silenced: every manager reports the files it
understands with their dependencies, and looks nothing up. `read` keeps, per package file, the toolchains (the
version-file managers, the engine fields of manifests, the `go` and `requires-python` directives, the runtime a
Dockerfile, compose file or devcontainer starts from) and the dependencies of the package managers (`MANAGERS`)
with the range as written and the version the lockfile fixes, each on the unit whose manifest the file is.
A file no unit owns (a version catalog, a central versions file) names no unit: the nearest one would be a
guess. Not dependencies of a unit: container images, CI actions,
transitive pins (`indirect`) and overrides; a git dependency's value is its ref, so it gives no `declared`.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath

NAME, VERSION, RANK = "renovate", "44.239.1", "reader"  # it reads declared files and runs no project code
NODE = "24.22.3"  # the Node release Renovate runs on (it needs `RegExp.escape`), installed with `--ignore-scripts`
# The report goes to stdout, the log to stderr: nothing else is printed on stdout.
ENV = {"LOG_LEVEL": "fatal", "LOG_FILE": "/dev/stderr", "LOG_FILE_LEVEL": "warn", "NO_COLOR": "1",
       "RENOVATE_ONBOARDING": "false", "RENOVATE_REQUIRE_CONFIG": "ignored", "RENOVATE_BASE_DIR": "/tmp/daodan-renovate"}
VERSION_MANAGERS = {"asdf", "mise", "proto", "nvm", "nodenv", "pyenv", "rust-toolchain", "gradle-wrapper",
                    "maven-wrapper", "bazelisk", "ruby-version", "bun-version"}
TOOL_DEPTYPES = {"engines", "packageManager", "volta", "golang", "toolchain", "requires-python"}
MANAGERS = frozenset({  # Renovate's managers whose dependencies are packages a project declares
    "npm", "pep621", "pip_requirements", "pip-compile", "pipenv", "poetry", "setup-cfg", "pip_setup", "gomod",
    "cargo", "maven", "maven-wrapper", "gradle", "gradle-wrapper", "composer", "bundler", "nuget", "pub", "mix",
    "swift", "sbt"})
IMAGE_MANAGERS = {"dockerfile", "docker-compose", "devcontainer"}
DOCKER_RUNTIMES = {"node": "node", "python": "python", "golang": "go", "rust": "rust", "ruby": "ruby",
                   "openjdk": "java", "eclipse-temurin": "java", "amazoncorretto": "java", "maven": "maven",
                   "gradle": "gradle"}
NOT_DECLARED = {"indirect", "overrides", "resolutions", "pnpm.overrides", "packageManager", "volta", "engines"}
CANON = {"nodejs": "node", "golang": "go", "rustc": "rust", "cpython": "python", "jdk": "java", "jre": "java",
         "temurin": "java", "openjdk": "java", "node.js": "node", "gradle-wrapper": "gradle"}
SCOPE = {"dependencies": "runtime", "devDependencies": "dev", "peerDependencies": "peer",
         "optionalDependencies": "optional", "compile": "runtime", "runtime": "runtime", "test": "test",
         "provided": "provided", "dev-dependencies": "dev", "build-dependencies": "build",
         "project.dependencies": "runtime"}


def _tool(name) -> str:
    value = str(name or "").strip().lower()
    return CANON.get(value, value)


def commands(context):
    if not context.inventory.files:
        return None
    return [{"tool": "renovate", "argv": ["renovate", "--platform=local", "--dry-run=extract", "--report-type=file",
                                          "--report-path=/dev/stdout"], "cwd": ".", "env": ENV, "network": "none"}]


def _owners(context) -> dict:
    """Manifest -> how its unit is referred to."""
    from premap.module_graph import references
    ref = references(context.graph)
    return {manifest: ref[module["id"]] for module in context.graph["modules"] if module["provenance"] == "build"
            for manifest in module["manifests"]}


def read(context, commands, results):
    [result] = results
    if result["returncode"] != 0:
        return {"facts": {}, "gaps": [{"kind": "model_failed", "path": ".",
                                       "detail": f"renovate: {(result['stderr'] or result['stdout']).strip()[-400:]}"}]}
    report = json.loads(result["stdout"])
    repository = (report.get("repositories") or {}).get("local") or {}
    by_manifest = _owners(context)

    toolchains, dependencies = [], []
    for manager, files in (repository.get("packageFiles") or {}).items():
        for package_file in files:
            path = package_file.get("packageFile")
            if not path:
                continue
            path = PurePosixPath(path).as_posix()
            unit = by_manifest.get(path)
            for dep in package_file.get("deps") or []:
                name, current = dep.get("depName") or dep.get("packageName"), dep.get("currentValue")
                if not name:
                    continue
                tool = _tool(name) if manager in VERSION_MANAGERS or dep.get("depType") in TOOL_DEPTYPES else \
                    DOCKER_RUNTIMES.get(name) if manager in IMAGE_MANAGERS else None
                if tool:
                    item = {"tool": tool, "declared_in": path}
                    if current is not None:
                        item["version"] = current
                    toolchains.append(item)
                    continue
                if manager not in MANAGERS or dep.get("depType") in NOT_DECLARED:
                    continue  # an image, an action, a transitive pin or an override: no package a unit declares
                item = {"name": name, "declared_in": path}
                if current and not str(dep.get("datasource", "")).startswith("git"):
                    item["declared"] = current  # a git dependency's value is its ref, not the range as written
                if unit:
                    item["unit"] = unit
                if dep.get("lockedVersion") is not None:
                    item["resolved"] = str(dep["lockedVersion"])
                if SCOPE.get(dep.get("depType")):
                    item["scope"] = SCOPE[dep["depType"]]
                dependencies.append(item)
            known = {(t["tool"], t["declared_in"]) for t in toolchains}
            for key, value in (package_file.get("extractedConstraints") or {}).items():
                if not key.startswith("%") and (_tool(key), path) not in known and isinstance(value, str):
                    toolchains.append({"tool": _tool(key), "version": value, "declared_in": path})
    return {"facts": {"toolchains": toolchains, "dependencies": dependencies}}
