"""Source: Renovate's local extraction, a separate program Daodan starts and reads (AGPL-3.0: no code of it here).

`commands` describes, for Daodan's container, one `renovate --platform=local --dry-run=extract` at the
project's root with the report written to stdout and the log silenced: every manager reports the files it
understands, and looks nothing up. `read` keeps, per package file, the toolchains only: the version-file
managers, the engine fields of manifests, the `go` and `requires-python` directives, the runtime a Dockerfile,
compose file or devcontainer starts from (the version its tag holds, `_image_version`), the constraints a file
writes (Poetry's `python`, Composer's `php`, pub's `dart`), and the packages that are the language or its build
tool (`PACKAGE_TOOLS`: TypeScript in a manifest, Scala and sbt in an sbt build, the Kotlin Gradle plugins). A
constraint is kept only when the file writes its value (Renovate derives `npm` from a lockfile's format and repeats
a root's `packageManager` on each member), a package only with a version (a pnpm `catalog:` reference has none: the
catalog states it). A wrapper's entry for itself is not a toolchain: the Maven wrapper gives Maven's version, not
its own. The other packages a file declares are not the pre-map's: each analyzer's build tool resolves them.

Of a service container a GitHub Actions job declares, Renovate's github-actions manager keeps the image alone
(`lib/modules/manager/github-actions/schema.ts`). Where a workflow of `.github/workflows` names `services`, a second
command reads each workflow in the container's copy (Git tracks it; the snapshot leaves dot folders out) with
Renovate's own YAML library (`YAML`, the `yaml` package Renovate pins, beside the Renovate that runs): `services`,
each service a job declares
(`jobs.<id>.services`) as the file writes it, with `host`, where the job's steps reach it (GitHub's rule: localhost
on the runner, its name from a job that runs in a container), and `job_env`, the variables the workflow and the
job give the steps. A service whose image is empty does not start, and is none.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath
import re

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
         "hashicorp/terraform": "terraform", "dotnet-sdk": "dotnet"}
WORKFLOWS = ".github/workflows"  # where GitHub reads a repository's workflows
SERVICES = re.compile(r"""["']?\bservices["']?\s*:""")  # a workflow that may declare a service container
# Renovate's YAML library, beside the Renovate on the path: yaml 2.9.1, the version Renovate 44.239.1 pins
YAML = '"$(dirname "$(readlink -f "$(command -v renovate)")")/../node_modules/yaml/bin.mjs"'
# Each workflow of the copy, then its document as JSON, or `null` and the library's message on stderr.
EACH = (f'for f in {WORKFLOWS}/*.yml {WORKFLOWS}/*.yaml; do [ -f "$f" ] || continue; echo "$f"; '
        f'node {YAML} --json --single --strict --merge < "$f" 2> /tmp/daodan-yaml.err'
        ' || { echo null; sed "s|^|$f: |" /tmp/daodan-yaml.err >&2; }; done')
SERVICE_KEYS = ("env", "ports", "options", "command", "entrypoint", "volumes")  # what a service's job writes for it


# Renovate's docker versioning (lib/modules/versioning/docker): a tag is a version, past a `v`, up to its first
# hyphen, and after it a compatibility suffix, the image's variant (`22-alpine`: Node 22 on Alpine).
TAG_VERSION = re.compile(r"\d+(?:\.\d+)*\w*", re.ASCII)
TAG_HASH = re.compile(r"[a-f0-9]{7,40}")  # a tag like a commit hash has no version


def _image_version(tag: str) -> str:
    """The version an image tag holds, else the tag as written (`alpine`, `lts`): no version, which the
    preparation names as one it cannot install."""
    if TAG_HASH.fullmatch(tag) and not tag.isdigit():
        return tag
    version = re.sub(r"^[vV]", "", tag).split("-")[0]
    return version if TAG_VERSION.fullmatch(version) else tag


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
    folder = context.root / WORKFLOWS  # outside the snapshot: read on disk, as `.gitmodules` is, links left out
    named = folder.is_dir() and not folder.is_symlink() and any(
        SERVICES.search(path.read_text(encoding="utf-8", errors="replace"))
        for path in sorted(folder.glob("*.y*ml")) if path.is_file() and not path.is_symlink())
    workflows = [{"tool": "renovate", "argv": ["sh", "-c", EACH], "cwd": ".", "env": {}, "network": "none"}] \
        if named else []
    return [{"tool": "renovate", "argv": ["renovate", "--platform=local", "--dry-run=extract", "--report-type=file",
                                          "--report-path=/dev/stdout"], "cwd": ".", "env": ENV, "network": "none"},
            *workflows]


def _services(rel: str, doc) -> list[dict]:
    """Each service container a job of the workflow `doc` declares, as `rel` writes it (the module's docstring)."""
    jobs = doc.get("jobs") if isinstance(doc, dict) else None
    top = doc.get("env") if isinstance(doc, dict) and isinstance(doc.get("env"), dict) else {}
    found = []
    for job_id, job in (jobs or {}).items() if isinstance(jobs, dict) else ():
        declared = job.get("services") if isinstance(job, dict) else None
        job_env = {**top, **(job["env"] if isinstance(job, dict) and isinstance(job.get("env"), dict) else {})}
        for name, service in declared.items() if isinstance(declared, dict) else ():
            service = {"image": service} if isinstance(service, str) else service
            if not isinstance(service, dict) or not service.get("image"):
                continue
            entry = {"name": str(name), "image": str(service["image"]),
                     "declared_in": f"{rel}#jobs.{job_id}.services.{name}",
                     "host": str(name) if job.get("container") else "localhost",
                     **{key: service[key] for key in SERVICE_KEYS if service.get(key) not in (None, "", [], {})}}
            found.append({**entry, "job_env": job_env} if job_env else entry)
    return found


def _workflows(answer: dict) -> tuple[list[dict], list[dict]]:
    """The services the workflows' jobs declare, and a gap for a workflow the library could not read."""
    if answer["returncode"] != 0:
        return [], [{"kind": "model_failed", "path": WORKFLOWS, "detail": f"yaml: {answer['stderr'].strip()[-400:]}"}]
    lines, errors = answer["stdout"].splitlines(), answer["stderr"].splitlines()
    services, gaps = [], []
    for rel, text in zip(lines[::2], lines[1::2]):
        doc = json.loads(text)
        if doc is None:
            said = " ".join(line.removeprefix(f"{rel}: ") for line in errors if line.startswith(f"{rel}: "))
            gaps.append({"kind": "model_failed", "path": rel,
                         "detail": f"{rel}: Renovate's YAML library does not read it: {said[-400:]}"})
        else:
            services += _services(rel, doc)
    return services, gaps


def read(context, commands, results):
    result, *rest = results
    services, gaps = _workflows(rest[0]) if rest else ([], [])
    if result["returncode"] != 0:
        return {"facts": {"services": services} if services else {}, "gaps": [*gaps, {
            "kind": "model_failed", "path": ".",
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
                        item["version"] = _image_version(current) if manager in IMAGE_MANAGERS else current
                    if item not in toolchains:  # the Kotlin plugins of one file share one version
                        toolchains.append(item)
            known = {(t["tool"], t["declared_in"]) for t in toolchains}
            written = text(path)
            for key, value in (package_file.get("extractedConstraints") or {}).items():
                if not key.startswith("%") and (_tool(key), path) not in known and isinstance(value, str) and (
                        value in written):  # a value no file writes is Renovate's deduction
                    toolchains.append({"tool": _tool(key), "version": value, "declared_in": path})
    return {"facts": {"toolchains": toolchains, **({"services": services} if services else {})},
            **({"gaps": gaps} if gaps else {})}
