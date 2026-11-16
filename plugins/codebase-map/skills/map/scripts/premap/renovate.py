"""Source: Renovate's local extraction, a separate program Daodan starts and reads (AGPL-3.0: no code of it here).

`commands` describes, for Daodan's container, one `renovate --platform=local --dry-run=extract` at the
project's root with the report written to stdout and the log silenced: every manager reports the files it
understands, and looks nothing up. `read` keeps, per package file, the toolchains only: the version-file
managers, the engine fields of manifests, the `go` and `requires-python` directives, the runtime a Dockerfile,
compose file or devcontainer starts from (the version its tag holds, `_image_version`), the constraints a file
writes (Poetry's `python`, Composer's `php`, pub's `dart`), and the packages that are the language or its build
tool (`PACKAGE_TOOLS`: TypeScript in a manifest, Scala and sbt in an sbt build, the Kotlin Gradle plugins, the Bun
a workflow sets up). A
constraint is kept only when the file writes its value (Renovate derives `npm` from a lockfile's format and repeats
a root's `packageManager` on each member), a package only with a version (a pnpm `catalog:` reference has none: the
catalog states it). A wrapper's entry for itself is not a toolchain: the Maven wrapper gives Maven's version, not
its own. The other packages a file declares are not the pre-map's: each analyzer's build tool resolves them.

Of a service container a GitHub Actions job declares, Renovate's github-actions manager keeps the image alone
(`lib/modules/manager/github-actions/schema.ts`). Where a workflow of `.github/workflows` names `services` or runs
Docker Compose, or a `.sh` script of the checkout runs it, a second command reads each workflow in the container's
copy (Git tracks it; the snapshot leaves dot folders out) with Renovate's own YAML library (`YAML`, the `yaml`
package Renovate pins, beside the Renovate that runs): `services`, each service a job declares (`jobs.<id>.services`)
as the file writes it, with `host`, where the job's steps reach it (GitHub's rule: localhost on the runner, its name
from a job that runs in a container), and `job_env`, the variables the workflow and the job give the steps;
`compose`, each `docker compose up` a step runs (`_steps`) or an npm test script does (`compose.scripts`), itself or
in the shell scripts it runs (`compose.started`), which `premap/compose.py` reads with Compose itself. A service whose image is empty does not start, and is none.

Where `.gitlab-ci.yml` names `services` or includes files, the same command reads it: each service a job runs with
(its own, its templates' through `extends`, else `default:`'s unless it inherits none) is a `services` fact as
GitLab's runner gives it (docs.gitlab.com/ci/services, /ci/yaml): `host` and `aliases`, the names the job reaches
it by (its aliases, then its image without tag and registry port, `/` as `__` and as `-`); `env`, the job's
variables and its own; `job_env`, the job's (the global ones it inherits, its templates', its own), each expanded
once as the runner expands it, `computed` naming those that reference a variable the file does not define;
`entrypoint` and `command` as written; `wait` `ports`, the runner's wait for the ports its image exposes. A file
the pipeline includes is not read: an `include_not_read` gap names it; a job that runs Docker Compose, on the Docker
the job starts, is a `compose_not_read` one.
"""
from __future__ import annotations

import json
from pathlib import PurePosixPath
import posixpath
import re
import shlex

from premap import compose, npm_tests

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
    ("github-actions", "bun", "uses-with", "bun"),  # oven-sh/setup-bun's bun-version (known-actions/npm.ts)
    ("sbt", "scala", None, "scala"), ("sbt", "sbt/sbt", None, "sbt"),
    ("gradle", "org.jetbrains.kotlin.", "plugin", "kotlin"))  # a prefix ends with `.`: every Kotlin Gradle plugin
CANON = {"nodejs": "node", "golang": "go", "rustc": "rust", "cpython": "python", "jdk": "java", "jre": "java",
         "temurin": "java", "openjdk": "java", "node.js": "node", "gradle-wrapper": "gradle",
         "hashicorp/terraform": "terraform", "dotnet-sdk": "dotnet"}
WORKFLOWS = ".github/workflows"  # where GitHub reads a repository's workflows
GITLAB = ".gitlab-ci.yml"  # where GitLab reads a project's pipeline, unless the project's settings name another
SERVICES = re.compile(r"""["']?\bservices["']?\s*:""")  # a workflow that may declare a service container
INCLUDE = re.compile(r"""(?m)^["']?include["']?\s*:""")  # a pipeline that includes files, which may declare one
# Renovate's YAML library, beside the Renovate on the path: yaml 2.9.1, the version Renovate 44.239.1 pins
YAML = '"$(dirname "$(readlink -f "$(command -v renovate)")")/../node_modules/yaml/bin.mjs"'
# Each workflow of the copy, then its document as JSON, or `null` and the library's message on stderr.
EACH = (f'for f in {WORKFLOWS}/*.yml {WORKFLOWS}/*.yaml {GITLAB}; do [ -f "$f" ] || continue; echo "$f"; '
        f'node {YAML} --json --single --strict --merge < "$f" 2> /tmp/daodan-yaml.err'
        ' || { echo null; sed "s|^|$f: |" /tmp/daodan-yaml.err >&2; }; done')
CHECKOUT = "actions/checkout"  # the checkout of a job: Daodan's copy of the project
SETUP = re.compile(r"(?:^|[-_])setup(?:$|[-_])")  # a toolchain's setup action (`setup-node`, `action-setup`)
PACKAGE_MANAGERS = ("npm", "yarn", "pnpm", "bun", "npx")  # programs that run a package's scripts, not tests
COMPOSE_KEPT = ("up", "down", "pull", "build", "ps", "logs", "config", "stop", "rm")  # what `compose` reads, or none
EXPRESSION = re.compile(r"\$\{\{.*?\}\}")  # an expression of GitHub Actions
SERVICE_KEYS = ("env", "ports", "options", "command", "entrypoint", "volumes")  # what a service's job writes for it
# GitLab's global keywords (docs.gitlab.com/ci/yaml): every other top-level key not starting with `.` is a job
GITLAB_KEYWORDS = {"default", "include", "stages", "variables", "workflow", "image", "services", "cache",
                   "before_script", "after_script", "spec"}
NAME_PORT = re.compile(r"^(.*?)(|:[0-9]+)(|/.*)$")  # gitlab-runner's `referenceRegexpNoPort`: a registry's port
SPECIAL = set("*#$@!?-0123456789")  # the parameters Go's `os.Expand` names with one character
ALNUM = re.compile(r"[A-Za-z0-9_]*")  # a name after `$`, as `os.Expand` scans it


# Renovate's docker versioning (lib/modules/versioning/docker): a tag is a version, past a `v`, up to its first
# hyphen, and after it a compatibility suffix, the image's variant (`22-alpine`: Node 22 on Alpine).
TAG_VERSION = re.compile(r"\d+(?:\.\d+)*\w*", re.ASCII)
TAG_HASH = re.compile(r"[a-f0-9]{7,40}")  # a tag like a commit hash has no version


# The Dev Container images' tags: `<image version>-<language version>[-<OS>]` or `<language version>[-<OS>]`
# (devcontainers/images, src/java/README.md: `3.1.9-11-bookworm` is the image 3.1.9 with Java 11, `25-trixie`).
DEV_CONTAINERS = {"mcr.microsoft.com/devcontainers/java": "java"}
NUMBER = re.compile(r"\d+(?:\.\d+)*", re.ASCII)


def _image_version(tag: str, name: str = "") -> str:
    """The version an image tag holds, else the tag as written (`alpine`, `lts`): no version, which the
    preparation names as one it cannot install. A Dev Container image's is its language's (`DEV_CONTAINERS`)."""
    numbers = [part for part in tag.split("-") if NUMBER.fullmatch(part)]
    if name in DEV_CONTAINERS and 0 < len(numbers) <= 2:
        return numbers[-1]
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
    read = compose.reader(context)
    named = folder.is_dir() and not folder.is_symlink() and (any(
        pattern.search(path.read_text(encoding="utf-8", errors="replace")) for pattern in (SERVICES, compose.MENTION)
        for path in sorted(folder.glob("*.y*ml")) if path.is_file() and not path.is_symlink()) or any(
        rel.endswith(".sh") and compose.MENTION.search(read(rel) or "") for rel in context.inventory.files))
    pipeline = context.root / GITLAB
    named = named or pipeline.is_file() and not pipeline.is_symlink() and any(
        pattern.search(pipeline.read_text(encoding="utf-8", errors="replace")) for pattern in (SERVICES, INCLUDE))
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


def _env(item) -> dict:
    return item["env"] if isinstance(item, dict) and isinstance(item.get("env"), dict) else {}


def _directory(item) -> str | None:
    """The `working-directory` a workflow's or a job's `defaults.run` gives its steps."""
    run = item["defaults"].get("run") if isinstance(item.get("defaults"), dict) else None
    return run.get("working-directory") if isinstance(run, dict) else None


def _steps(rel: str, doc, read) -> tuple[list[dict], list[dict]]:
    """Each `docker compose up` a step of the workflow `doc` runs, itself or in the shell scripts of the checkout it
    runs (`compose.started`; `read(rel)` a file's text), as the `compose` facet states it: where GitHub runs the step
    (its `working-directory`, else the job's or the workflow's default), the variables the workflow writes for it
    (`env`; an expression is the CI's, and stays out), the job's (`job_env`, for the tests); a gap for one that runs
    Compose in a way its words do not say."""
    if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
        return [], []
    found, gaps, top, where = [], [], _env(doc), _directory(doc)
    for job_id, job in doc["jobs"].items():
        if not isinstance(job, dict) or not isinstance(job.get("steps"), list):
            continue
        job_env, folder = {**top, **_env(job)}, _directory(job) or where
        for index, step in enumerate(job["steps"]):
            script = step.get("run") if isinstance(step, dict) else None
            if not isinstance(script, str):
                continue
            path = f"{rel}#jobs.{job_id}.steps.{index}"
            cwd = posixpath.normpath(str(step.get("working-directory") or folder or "."))
            if "${{" in cwd or cwd.startswith(("/", "..")):  # computed, or outside the checkout
                words, unread = compose.invocations(script)
                gaps += [compose.not_read(path, line) for line in [*unread, *map(shlex.join, words)]]
                continue
            started, said = compose.started(path, script, cwd, read)
            env = {key: _text(value) for key, value in {**job_env, **_env(step)}.items() if "${{" not in _text(value)}
            found, gaps = found + compose.facts(started, cwd, env=env, job_env=job_env), gaps + said
    return found, gaps


def _shell(item) -> str | None:
    """The `shell` a workflow's or a job's `defaults.run` gives its steps."""
    run = item["defaults"].get("run") if isinstance(item.get("defaults"), dict) else None
    return run.get("shell") if isinstance(run, dict) else None


def _npm_script(words: list[str], scripts: dict) -> str | None:
    """The package script a command's `words` run: `npm test`, `npm run <name>`, `yarn|pnpm [run] <name>`, `bun run
    <name>`."""
    tool, rest = words[0].rsplit("/", 1)[-1], [word for word in words[1:] if not word.startswith("-")]
    if tool in ("npm", "yarn", "pnpm") and rest[:1] in (["test"], ["t"], ["tst"]):
        return "test"
    if tool in PACKAGE_MANAGERS and rest[:1] in (["run"], ["run-script"]) and len(rest) > 1:
        return rest[1]
    return rest[0] if tool in ("yarn", "pnpm") and rest and rest[0] in scripts else None


def _inside(path: str, folder: str) -> bool:
    return folder == "." or path == folder or path.startswith(folder + "/")


def _tests_of(script: str, cwd: str, tests: list[dict], read) -> list[dict]:
    """The `tests` entries a step's shell `script` run from `cwd` runs: a package script that starts what an
    entry's script starts (`npm_tests._starts`), or an entry's runner as a program, there or in the shell scripts
    of the checkout it runs (`compose.followed`), from a folder inside the entry's or holding it."""
    commands = [command for text in (script, *map(read, compose.followed(script, cwd, read)))
                for command in compose.simple_commands(text or "")]
    programs = {word.rsplit("/", 1)[-1] for command in commands for word in command}
    package = posixpath.normpath(posixpath.join(cwd, "package.json"))
    try:
        scripts = json.loads(read(package) or "{}").get("scripts") or {}
    except (ValueError, AttributeError):
        scripts = {}

    def starts(name: str) -> set:
        text = scripts.get(name) if isinstance(scripts, dict) else None
        return {(where, runner) for where, runner, _, _ in npm_tests._starts(text, scripts)} if isinstance(text, str) \
            else set()

    found = []
    for entry in tests:
        rel, _, name = str(entry.get("declared_in") or "").partition("#scripts.")
        if name and rel == package and any(run == name or starts(name) & starts(run) for run in (
                _npm_script(command, scripts) for command in commands) if run):
            found.append(entry)
        elif entry.get("runner") not in (None, *PACKAGE_MANAGERS) and entry["runner"] in programs and (
                _inside(cwd, entry.get("root") or ".") or _inside(entry.get("root") or ".", cwd)):
            found.append(entry)
    return found


def _step_fact(path: str, step: dict, cwd: str, env: dict, shell: str | None) -> dict | None:
    """A step before a job's tests as the `ci_steps` facet states it: `{declared_in, name, cwd, run, env, shell}`
    as GitHub's runner runs it, or `{declared_in, name, cause}` for one Daodan does not run; None for one that is
    not a step of Daodan's: the checkout (its copy), a toolchain's setup action (a toolchain the pre-map reads) and
    Docker Compose's `up`, `down` and the like (its services are the `compose` facet's)."""
    base = {"declared_in": path, **({"name": str(step["name"])} if step.get("name") else {})}
    uses, script = step.get("uses"), step.get("run")
    if isinstance(uses, str):
        action = uses.split("@")[0]
        if action == CHECKOUT or SETUP.search(action.rsplit("/", 1)[-1]):
            return None
        return {**base, "cause": f"it uses {uses}: Daodan runs no action but the checkout and a toolchain's setup"}
    if not isinstance(script, str):
        return None
    commands = compose.simple_commands(script)
    composed = [command for command in commands if command[:2] == ["docker", "compose"]
                or command[:1] == ["docker-compose"]]
    other = [command for command in composed if compose._split(command)[2] not in COMPOSE_KEPT]
    if other:
        return {**base, "cause": f"it runs `{shlex.join(other[0])}`, Docker Compose on the services it starts, which "
                                 "needs an engine beside the tests"}
    if commands and len(composed) == len(commands):
        return None
    shell = step.get("shell") or shell
    env = {key: _text(value) for key, value in env.items()}
    expression = next((found.group() for text in (script, cwd, *env.values())
                       for found in [EXPRESSION.search(text)] if found), None)
    cause = (f"it runs only if `{step['if']}`, which Daodan does not evaluate" if step.get("if") is not None else
             f"it reads `{expression}`, an expression of the CI (its secrets among them), which Daodan does not "
             "evaluate" if expression else
             f"it runs in {shell}, a shell Daodan does not run" if shell not in (None, "bash", "sh") else
             f"its folder {cwd} lies outside the checkout" if cwd.startswith(("/", "..")) else None)
    return {**base, "cause": cause} if cause else {**base, "cwd": cwd, "run": script, **({"env": env} if env else {}),
                                                   **({"shell": shell} if shell else {})}


def _ci_steps(rel: str, doc, tests: list[dict], read, claimed: set) -> list[dict]:
    """The steps a job of the workflow `doc` runs before its tests, as the `ci_steps` facet states them: for each
    `tests` entry not in `claimed`, the first job step that runs it (`_tests_of`) is its test step, and each step
    before it that runs no entry is a fact (`_step_fact`) with `tests` the entry's `declared_in`."""
    if not tests or not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
        return []
    facts, top, where, default = [], _env(doc), _directory(doc), _shell(doc)
    for job_id, job in doc["jobs"].items():
        if not isinstance(job, dict) or not isinstance(job.get("steps"), list):
            continue
        steps = [step if isinstance(step, dict) else {} for step in job["steps"]]
        folder, shell = _directory(job) or where, _shell(job) or default
        cwds = [posixpath.normpath(str(step.get("working-directory") or folder or ".")) for step in steps]
        tested = [_tests_of(step["run"], cwd, tests, read) if isinstance(step.get("run"), str) else []
                  for step, cwd in zip(steps, cwds)]
        for index, entries in enumerate(tested):
            for entry in entries:
                if entry["declared_in"] in claimed:
                    continue
                claimed.add(entry["declared_in"])
                for number in range(index):
                    fact = None if tested[number] else _step_fact(
                        f"{rel}#jobs.{job_id}.steps.{number}", steps[number], cwds[number],
                        {**top, **_env(job), **_env(steps[number])}, shell)
                    facts += [{**fact, "tests": entry["declared_in"]}] if fact else []
    return facts


def _shell_name(text: str) -> tuple[str, int]:
    """The name after a `$` and the characters it takes, as Go's `os.Expand` reads them (`getShellName`)."""
    if text[0] == "{":
        if len(text) > 2 and text[1] in SPECIAL and text[2] == "}":
            return text[1], 3
        end = text.find("}", 1)
        return ("", 1) if end < 0 else ("", 2) if end == 1 else (text[1:end], end + 1)
    if text[0] in SPECIAL:
        return text[0], 1
    name = ALNUM.match(text).group()
    return name, len(name)


def _text(value) -> str:
    return json.dumps(value) if isinstance(value, bool) else "" if value is None else str(value)


def _expand(text: str, variables: dict) -> tuple[str, list[str]]:
    """`text` as gitlab-runner expands a variable's value (`ExpandValue`: Go's `os.Expand` over the job's
    variables as written; `$$` is a dollar, another one-character parameter nothing), and the names it references
    that `variables` does not hold: the CI's own (its predefined variables, the project's settings)."""
    out, unknown, i, j = [], [], 0, 0
    while j < len(text):
        if text[j] == "$" and j + 1 < len(text):
            out.append(text[i:j])
            name, width = _shell_name(text[j + 1:])
            if not name and not width:  # no name: the dollar stays
                out.append("$")
            elif name == "$":
                out.append("$")
            elif name and name not in SPECIAL:
                if name in variables:
                    out.append(_text(variables[name]))
                else:
                    unknown.append(name)
            j += width
            i = j + 1
        j += 1
    return "".join(out) + text[i:], unknown


def _merged(base: dict, over: dict) -> dict:
    out = dict(base)
    for key, value in over.items():
        out[key] = _merged(out[key], value) if isinstance(out.get(key), dict) and isinstance(value, dict) else value
    return out


def _extended(doc: dict, job: dict, depth: int = 0) -> dict:
    """`job` over the jobs it `extends`, as GitLab merges them: hashes key by key, every other value replaced, the
    later template and then the job itself winning; at most 11 levels."""
    parents, merged = job.get("extends"), {}
    for name in [parents] if isinstance(parents, str) else parents if isinstance(parents, list) else []:
        if isinstance(doc.get(name), dict) and depth < 11:
            merged = _merged(merged, _extended(doc, doc[name], depth + 1))
    return _merged(merged, {key: value for key, value in job.items() if key != "extends"})


def _inherits(job: dict, kind: str, key: str) -> bool:
    """Whether `job` takes `key` of the pipeline's `default:` (`kind` default) or global `variables` (`inherit`)."""
    said = job["inherit"].get(kind, True) if isinstance(job.get("inherit"), dict) else True
    return key in said if isinstance(said, list) else said is not False


def _hosts(image: str, alias) -> list[str]:
    """The names gitlab-runner gives a service: its aliases (spaces or commas between them), then its image
    without tag, digest and registry port, with `/` as `__`, then as `-` (`services.SplitNameAndVersion`)."""
    name = image.split("@", 1)[0]
    head, colon, tag = name.rpartition(":")
    match = NAME_PORT.match(head if colon and "/" not in tag else name)
    service = match.group(1) + match.group(3)
    return list(dict.fromkeys([*(part for part in re.split(r"[\s,]+", str(alias or "")) if part),
                               service.replace("/", "__"), service.replace("/", "-")]))


def _gitlab(rel: str, doc) -> tuple[list[dict], list[dict]]:
    """Each service a job of GitLab's pipeline `doc` runs with, as GitLab gives it (the module's docstring), and a
    gap for each file the pipeline includes."""
    if not isinstance(doc, dict):
        return [], []
    include = doc.get("include")
    gaps = [{"kind": "include_not_read", "path": rel, "include": item,
             "detail": f"{rel} includes {json.dumps(item)}: Daodan does not read it, and the services its jobs "
                       "declare do not start"}
            for item in ([include] if isinstance(include, (str, dict)) else include if isinstance(include, list) else [])]
    default = doc["default"] if isinstance(doc.get("default"), dict) else {}
    top = doc["variables"] if isinstance(doc.get("variables"), dict) else {}
    found = []
    for job_id, job in doc.items():
        if job_id in GITLAB_KEYWORDS or str(job_id).startswith(".") or not isinstance(job, dict):
            continue
        job = _extended(doc, job)
        scripts = [job.get("before_script", default.get("before_script") if _inherits(job, "default",
                                                                                        "before_script") else None),
                   job.get("script")]
        gaps += [{"kind": "compose_not_read", "path": f"{rel}#{job_id}",
                  "detail": f"{rel}#{job_id} runs `{line}`: Daodan reads Docker Compose where a GitHub Actions step "
                            "starts it, not in a GitLab job, whose Compose runs on the Docker the job starts"}
                 for lines in scripts
                 for line in ([lines] if isinstance(lines, str) else lines if isinstance(lines, list) else [])
                 if isinstance(line, str) and compose.MENTION.search(line)]
        declared = job["services"] if "services" in job else (
            default.get("services", doc.get("services")) if _inherits(job, "default", "services") else None)
        if "script" not in job or not isinstance(declared, list):
            continue
        written = {**{key: value for key, value in top.items() if _inherits(job, "variables", key)},
                   **(job["variables"] if isinstance(job.get("variables"), dict) else {})}
        given = {key: value.get("value") if isinstance(value, dict) else value for key, value in written.items()}
        variables, computed = {}, []
        for key, value in given.items():  # `expand: false` keeps a value as written
            text, unknown = _expand(value, given) if isinstance(value, str) and not (
                isinstance(written[key], dict) and written[key].get("expand") is False) else (value, [])
            variables[key] = value if unknown else text
            computed += [key] if unknown else []
        for index, service in enumerate(declared):
            service = {"name": service} if isinstance(service, str) else service
            if not isinstance(service, dict) or not service.get("name"):
                continue
            image, unknown = _expand(str(service["name"]), given)
            image = str(service["name"]) if unknown else image
            hosts = _hosts(image, service.get("alias"))
            own = service["variables"] if isinstance(service.get("variables"), dict) else {}
            found.append({"name": hosts[0], "image": image, "declared_in": f"{rel}#{job_id}.services.{index}",
                          "host": hosts[0], **({"aliases": hosts[1:]} if hosts[1:] else {}),
                          **({"env": {**variables, **own}} if variables or own else {}),
                          **{key: service[key] for key in ("entrypoint", "command") if service.get(key)},
                          **({"job_env": variables} if variables else {}),
                          **({"computed": computed} if computed else {}), "wait": "ports"})
    return found, gaps


def _workflows(answer: dict, read, tests: list[dict] = ()) -> tuple[dict, list[dict]]:
    """The services the workflows' jobs declare and the steps that start Docker Compose, as facets, and a gap for a
    workflow the library could not read."""
    if answer["returncode"] != 0:
        return {}, [{"kind": "model_failed", "path": WORKFLOWS, "detail": f"yaml: {answer['stderr'].strip()[-400:]}"}]
    lines, errors = answer["stdout"].splitlines(), answer["stderr"].splitlines()
    services, steps, gaps, before, claimed = [], [], [], [], set()
    for rel, text in zip(lines[::2], lines[1::2]):
        doc = json.loads(text)
        if doc is None:  # the library's message is the line that names the error, above Node's stack
            said = [line.removeprefix(f"{rel}: ") for line in errors if line.startswith(f"{rel}: ")]
            said = next((line for line in said if re.match(r"\w+Error: ", line)), said[-1] if said else "")
            gaps.append({"kind": "model_failed", "path": rel,
                         "detail": f"{rel}: Renovate's YAML library does not read it: {said[:400]}"})
        elif rel == GITLAB:
            found, said = _gitlab(rel, doc)
            services, gaps = services + found, gaps + said
        else:
            found, said = _steps(rel, doc, read)
            services, steps, gaps = services + _services(rel, doc), steps + found, gaps + said
            before += _ci_steps(rel, doc, list(tests), read, claimed)
    return {name: facts for name, facts in (("services", services), ("compose", steps), ("ci_steps", before))
            if facts}, gaps


def read(context, commands, results):
    result, *rest = results
    tests = (getattr(context, "stated", None) or {}).get("tests") or []
    declared, gaps = _workflows(rest[0], compose.reader(context), tests) if rest else ({}, [])
    started, unread = compose.scripts(context)  # and the test scripts that start Docker Compose
    declared = {**declared, "compose": [*declared.get("compose", ()), *started]} if started else declared
    gaps += unread
    if result["returncode"] != 0:
        return {"facts": declared, "gaps": [*gaps, {
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
                    DOCKER_RUNTIMES.get(name, DEV_CONTAINERS.get(name)) if manager in IMAGE_MANAGERS
                    else _package_tool(manager, name, dep))
                if tool:
                    item = {"tool": tool, "declared_in": path}
                    if current is not None:
                        item["version"] = _image_version(current, name) if manager in IMAGE_MANAGERS else current
                    if item not in toolchains:  # the Kotlin plugins of one file share one version
                        toolchains.append(item)
            known = {(t["tool"], t["declared_in"]) for t in toolchains}
            written = text(path)
            for key, value in (package_file.get("extractedConstraints") or {}).items():
                if not key.startswith("%") and (_tool(key), path) not in known and isinstance(value, str) and (
                        value in written):  # a value no file writes is Renovate's deduction
                    toolchains.append({"tool": _tool(key), "version": value, "declared_in": path})
    return {"facts": {"toolchains": toolchains, **declared}, **({"gaps": gaps} if gaps else {})}
