"""Source: Renovate's local extraction, a separate program Daodan starts and reads (AGPL-3.0: no code of it here).

`commands` describes, for Daodan's container, one `renovate --platform=local --dry-run=extract` at the
project's root with the report written to stdout and the log silenced: every manager reports the files it
understands with their dependencies, and looks nothing up. `read` keeps, per package file, the toolchains (the
version-file managers, the engine fields of manifests, the `go` and `requires-python` directives, the runtime a
Dockerfile, compose file or devcontainer starts from) and the dependencies of the package managers (`MANAGERS`)
with the range as written and the version the lockfile fixes, each on the unit whose manifest the file is.
A file no unit owns (a version catalog, a central versions file) names no unit: the nearest one would be a
guess. Not dependencies of a unit: container images, CI actions, transitive pins (`indirect`), overrides,
scripts and tasks, a `replace` target, an import mapped to a path or a URL, and what the file also states as
a constraint (Poetry's `python`, Composer's `php`, pub's `dart`): that is a toolchain. A constraint is kept
only when the file writes its value (Renovate derives `npm` from a lockfile's format and repeats a root's
`packageManager` on each member). A Maven parent is scope `parent`, an imported BOM `bom`; a Gradle entry has no
scope, since the report names no configuration. A git dependency's value is its ref, so it gives no
`declared`; a Gemfile range comes without its quotes. A file pip-compile wrote is no declaration: the
requirements reader gives its pins as `resolved`.
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
                    "maven-wrapper", "bazelisk", "ruby-version", "bun-version", "terraform-version"}
TOOL_DEPTYPES = {"engines", "packageManager", "volta", "golang", "toolchain", "requires-python", "required_version"}
WRAPPER_SELF = {"maven-wrapper", "gradle-wrapper"}  # a wrapper manager's entry for the wrapper itself, not the tool
MANAGERS = frozenset({  # Renovate's managers whose dependencies are packages a project declares
    "npm", "pep621", "pip_requirements", "pip-compile", "pipenv", "poetry", "setup-cfg", "pip_setup", "gomod",
    "cargo", "maven", "maven-wrapper", "gradle", "gradle-wrapper", "composer", "bundler", "nuget", "pub", "mix",
    "swift", "sbt", "bazel-module", "helmv3", "terraform", "conan", "deno"})
IMAGE_MANAGERS = {"dockerfile", "docker-compose", "devcontainer"}
DOCKER_RUNTIMES = {"node": "node", "python": "python", "golang": "go", "rust": "rust", "ruby": "ruby",
                   "openjdk": "java", "eclipse-temurin": "java", "amazoncorretto": "java", "maven": "maven",
                   "gradle": "gradle"}
NOT_DECLARED = {"indirect", "overrides", "resolutions", "pnpm.overrides", "packageManager", "volta", "engines",
                "scripts", "tasks", "replace"}
NOT_PACKAGES = ("./", "../", "/", "http://", "https://", "file:")  # an import mapped to a path or a URL
CANON = {"nodejs": "node", "golang": "go", "rustc": "rust", "cpython": "python", "jdk": "java", "jre": "java",
         "temurin": "java", "openjdk": "java", "node.js": "node", "gradle-wrapper": "gradle",
         "hashicorp/terraform": "terraform"}
SCOPE = {"dependencies": "runtime", "devDependencies": "dev", "peerDependencies": "peer",
         "optionalDependencies": "optional", "compile": "runtime", "runtime": "runtime", "test": "test",
         "provided": "provided", "dev-dependencies": "dev", "build-dependencies": "build",
         "project.dependencies": "runtime", "parent": "parent", "parent-root": "parent", "import": "bom"}
NO_SCOPE = {"gradle"}  # managers whose report names no configuration
# A table of versions: its entries say which version a package takes where a unit names it, not that a unit
# uses it (`premap.versions_from_tables` joins them). By its depType, or a file of these managers no unit owns.
TABLE_DEPTYPES = ("pnpm.catalog", "workspace.dependencies")
TABLE_MANAGERS = {"nuget", "gradle"}
PLACEHOLDERS = ("catalog:", "workspace:")  # a reference to a table, not a range


def _tool(name) -> str:
    value = str(name or "").strip().lower()
    return CANON.get(value, value)


def _name(manager: str, dep: dict) -> str | None:
    """The package as its build tool names it: Cargo's `package =` (Renovate's packageName), SwiftPM's last part of
    the URL; else Renovate's depName."""
    name = dep.get("depName") or dep.get("packageName")
    if manager == "cargo" and dep.get("packageName"):
        return dep["packageName"]
    if manager == "swift" and name:
        return str(name).rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]
    return name


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
    from premap.requirements import COMPILED

    def text(rel: str) -> str:
        try:
            return context.inventory.text(rel)
        except (KeyError, OSError, ValueError):
            return ""

    toolchains, dependencies = [], []
    for manager, files in (repository.get("packageFiles") or {}).items():
        for package_file in files:
            path = package_file.get("packageFile")
            if not path:
                continue
            path = PurePosixPath(path).as_posix().removeprefix("./")
            if manager == "pip_requirements" and COMPILED.search(text(path)):
                continue  # pip-compile's pins: the requirements reader gives them as resolved
            unit = by_manifest.get(path)
            constraints = {_tool(key) for key in package_file.get("extractedConstraints") or {}}
            for dep in package_file.get("deps") or []:
                name, current = _name(manager, dep), dep.get("currentValue")
                if not name or (manager in WRAPPER_SELF and name in WRAPPER_SELF):
                    continue
                tool = _tool(name) if manager in VERSION_MANAGERS or dep.get("depType") in TOOL_DEPTYPES else \
                    DOCKER_RUNTIMES.get(name) if manager in IMAGE_MANAGERS else None
                if tool:
                    item = {"tool": tool, "declared_in": path}
                    if current is not None:
                        item["version"] = current
                    toolchains.append(item)
                    continue
                if manager not in MANAGERS or dep.get("depType") in NOT_DECLARED or _tool(name) in constraints \
                        or str(name).startswith(NOT_PACKAGES):
                    continue  # an image, an action, a pin, an override, a constraint, a path: no package declared
                item = {"name": name, "declared_in": path}
                if current and not str(dep.get("datasource", "")).startswith("git") \
                        and not str(current).startswith(PLACEHOLDERS):
                    item["declared"] = current.strip('"') if manager == "bundler" else current
                if str(dep.get("depType") or "").startswith(TABLE_DEPTYPES) or (unit is None and manager in TABLE_MANAGERS):
                    item["_table"] = True
                elif unit:
                    item["unit"] = unit
                if dep.get("lockedVersion") is not None:
                    item["resolved"] = str(dep["lockedVersion"])
                if SCOPE.get(dep.get("depType")) and manager not in NO_SCOPE:
                    item["scope"] = SCOPE[dep["depType"]]
                dependencies.append(item)
            known = {(t["tool"], t["declared_in"]) for t in toolchains}
            written = text(path)
            for key, value in (package_file.get("extractedConstraints") or {}).items():
                if not key.startswith("%") and (_tool(key), path) not in known and isinstance(value, str) \
                        and value in written:  # a value no file writes is Renovate's deduction
                    toolchains.append({"tool": _tool(key), "version": value, "declared_in": path})
    return {"facts": {"toolchains": toolchains, "dependencies": dependencies}}
