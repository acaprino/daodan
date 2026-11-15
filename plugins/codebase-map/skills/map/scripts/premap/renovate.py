"""Source: Renovate's local extraction, a separate program Daodan starts and reads (AGPL-3.0: no code of it here).

`commands` describes, for Daodan's container, one `renovate --platform=local --dry-run=extract` at the
project's root with the report written to stdout and the log silenced: every manager reports the files it
understands, and looks nothing up. `read` keeps, per package file, the toolchains only: the version-file
managers, the engine fields of manifests, the `go` and `requires-python` directives, the runtime a Dockerfile,
compose file or devcontainer starts from, the constraints a file writes (Poetry's `python`, Composer's
`php`, pub's `dart`), and the packages that are the language or its build tool (`PACKAGE_TOOLS`: TypeScript in a
manifest, Scala and sbt in an sbt build, the Kotlin Gradle plugins). A constraint is kept only when the file writes
its value (Renovate derives `npm` from a lockfile's format and repeats a root's `packageManager` on each member), a
package only with a version (a pnpm `catalog:` reference has none: the catalog states it). A wrapper's entry for
itself is not a toolchain: the Maven wrapper gives Maven's version, not its own. The other packages a file declares
are not the pre-map's: each analyzer's build tool resolves them.
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
IMAGE_MANAGERS = {"dockerfile", "docker-compose", "devcontainer"}
DOCKER_RUNTIMES = {"node": "node", "python": "python", "golang": "go", "rust": "rust", "ruby": "ruby",
                   "openjdk": "java", "eclipse-temurin": "java", "amazoncorretto": "java", "maven": "maven",
                   "gradle": "gradle"}
PACKAGE_TOOLS = (  # (manager, package, depType or None, tool): a package that is the language or its build tool
    ("npm", "typescript", None, "typescript"), ("bun", "typescript", None, "typescript"),
    ("sbt", "scala", None, "scala"), ("sbt", "sbt/sbt", None, "sbt"),
    ("gradle", "org.jetbrains.kotlin.", "plugin", "kotlin"))  # a prefix ends with `.`: every Kotlin Gradle plugin
CANON = {"nodejs": "node", "golang": "go", "rustc": "rust", "cpython": "python", "jdk": "java", "jre": "java",
         "temurin": "java", "openjdk": "java", "node.js": "node", "gradle-wrapper": "gradle",
         "hashicorp/terraform": "terraform"}


def _tool(name) -> str:
    value = str(name or "").strip().lower()
    return CANON.get(value, value)


def _package_tool(manager: str, name: str, dep: dict) -> str | None:
    if dep.get("skipReason") == "unspecified-version":
        return None
    return next((tool for m, package, dep_type, tool in PACKAGE_TOOLS if m == manager
                 and (name == package or package.endswith(".") and name.startswith(package))
                 and dep_type in (None, dep.get("depType"))), None)


def commands(context):
    if not context.inventory.files:
        return None
    return [{"tool": "renovate", "argv": ["renovate", "--platform=local", "--dry-run=extract", "--report-type=file",
                                          "--report-path=/dev/stdout"], "cwd": ".", "env": ENV, "network": "none"}]


def read(context, commands, results):
    [result] = results
    if result["returncode"] != 0:
        return {"facts": {}, "gaps": [{"kind": "model_failed", "path": ".",
                                       "detail": f"renovate: {(result['stderr'] or result['stdout']).strip()[-400:]}"}]}
    report = json.loads(result["stdout"])
    repository = (report.get("repositories") or {}).get("local") or {}

    def text(rel: str) -> str:
        try:
            return context.inventory.text(rel)
        except (KeyError, OSError, ValueError):
            return ""

    toolchains = []
    for manager, files in (repository.get("packageFiles") or {}).items():
        for package_file in files:
            path = package_file.get("packageFile")
            if not path:
                continue
            path = PurePosixPath(path).as_posix().removeprefix("./")
            for dep in package_file.get("deps") or []:
                name, current = dep.get("depName") or dep.get("packageName"), dep.get("currentValue")
                if not name or (manager in WRAPPER_SELF and name in WRAPPER_SELF):
                    continue
                tool = _tool(name) if manager in VERSION_MANAGERS or dep.get("depType") in TOOL_DEPTYPES else (
                    DOCKER_RUNTIMES.get(name) if manager in IMAGE_MANAGERS else _package_tool(manager, name, dep))
                if tool:
                    item = {"tool": tool, "declared_in": path}
                    if current is not None:
                        item["version"] = current
                    if item not in toolchains:  # the Kotlin plugins of one file share one version
                        toolchains.append(item)
            known = {(t["tool"], t["declared_in"]) for t in toolchains}
            written = text(path)
            for key, value in (package_file.get("extractedConstraints") or {}).items():
                if not key.startswith("%") and (_tool(key), path) not in known and isinstance(value, str) and (
                        value in written):  # a value no file writes is Renovate's deduction
                    toolchains.append({"tool": _tool(key), "version": value, "declared_in": path})
    return {"facts": {"toolchains": toolchains}}
