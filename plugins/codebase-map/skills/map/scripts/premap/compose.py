"""Source: Docker Compose's own reading of the compose files a CI step starts (`docker compose config`).

Where the pre-map's `compose` facet names a step that runs `docker compose up` (`premap/renovate.py` reads it from
the workflows, and from the npm test scripts with `scripts`; `started` follows the shell scripts they run),
`commands` describes one
`docker-compose <the step's options> config --format json <its services>`
where the step runs it, in Daodan's container with no network and no engine: Compose itself finds the files that
step's `up` finds, merges them, interpolates the variables the step sets and the project's `.env`, and keeps the
services `up` starts with those they depend on. `read` states each of them as a `services` fact: `declared_in`
`<step>.services.<name>`, `host` localhost (the job's later steps reach what they publish on its runner),
`environment` as `env`, `ports` as `published:target`, `healthcheck`, `command` and `entrypoint` as Compose gives
them, `depends_on` as `after` (each name with the condition `up` waits for), the bind mounts as `binds` (relative
to the project where they lie inside it), `build` where Compose builds the image, `ignored` the keys it sets that no
option here applies, and the job's `job_env`. A Compose that does not read the files is a
`model_failed` gap naming the step, a variable it does not find a `model_partial` one.

`invocations` and `options` read a step's script as the shell splits its words (`shlex`): a `docker compose` or
`docker-compose` command whose subcommand is `up`, from the variables it sets on, past `sudo` and the shell's
keywords. `started` reads them in a script and in the shell scripts of the checkout it runs (a word that names one:
`.sh`, or a shell's `#!`), three levels deep, each from its caller's folder: one that changes folder and runs
Compose is a `compose_not_read` gap.
"""
from __future__ import annotations

import json
from pathlib import Path
import posixpath
import re
import shlex

import confinement

NAME, VERSION, RANK = "compose", "5.6.1", "model"  # Compose's own command reads its files
# Docker Compose's static binary (Apache-2.0), checked by the sha256 its release publishes
DOWNLOAD = ("https://github.com/docker/compose/releases/download/v5.6.1/docker-compose-linux-x86_64",
            "47737f4236e6d3ccea7291995203f8f018058783b4c3a9469119811a0b5db8c0")
MENTION = re.compile(r"\bdocker[ \t]+compose\b|\bdocker-compose\b")  # a line that may run Docker Compose
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
PUNCTUATION = ";&|()<>"  # what ends a simple command
LEADERS = {"then", "do", "else", "elif", "if", "while", "until", "!", "{", "sudo", "exec", "time", "command", "nohup"}
VALUED = {"-f", "--file", "-p", "--project-name", "--project-directory", "--env-file", "--profile", "--parallel",
          "--ansi", "--progress"}  # Compose's global options that take a value
UP_VALUED = {"--attach", "--exit-code-from", "--no-attach", "--pull", "--scale", "-t", "--timeout", "--wait-timeout"}
USED = {"image", "environment", "ports", "healthcheck", "command", "entrypoint", "volumes", "build", "depends_on"}
INERT = {"networks", "restart", "container_name", "labels", "logging", "profiles", "pull_policy",
         "deploy", "expose", "stop_grace_period", "stop_signal", "hostname", "domainname"}  # nothing the tests reach
UNSET = re.compile(r"variable is not set", re.I)  # Compose's warning for a variable it interpolates blank
SHELL = re.compile(r"#!\s*\S*/(?:env\s+)?(?:ba|da|a|k|z)?sh\b")  # a shell script's first line
MOVES = re.compile(r"(?:^|[;&|({]|\bthen|\bdo|\belse)\s*(?:cd|pushd)(?:\s|$)", re.M)  # a command that changes folder
DEPTH = 3  # the shell scripts a script runs, followed this deep


def _split(argv: list[str]) -> tuple[dict, list[str], str | None, list[str]]:
    """The variables a Compose command sets, its global options, its subcommand and what follows it."""
    env, i = {}, 0
    while i < len(argv) and ASSIGNMENT.match(argv[i]):
        key, _, value = argv[i].partition("=")
        env[key], i = value, i + 1
    i += 2 if argv[i:i + 1] == ["docker"] else 1
    options = []
    while i < len(argv) and argv[i].startswith("-"):
        options += argv[i:i + 2] if argv[i] in VALUED else argv[i:i + 1]
        i += 2 if argv[i] in VALUED else 1
    return env, options, argv[i] if i < len(argv) else None, argv[i + 1:]


def simple_commands(script: str) -> list[list[str]]:
    """Each simple command of a shell `script` as its words, from the program on (past the shell's keywords and the
    variables it sets); a line the shell's words do not split is none."""
    found = []
    for line in script.replace("\\\n", " ").splitlines():
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=PUNCTUATION)
            lexer.whitespace_split, lexer.commenters = True, "#"
            words = list(lexer)
        except ValueError:
            continue
        command: list[str] = []
        for word in [*words, ";"]:
            if not set(word) <= set(PUNCTUATION):
                command.append(word)
                continue
            start = next((n for n, w in enumerate(command) if w not in LEADERS and not ASSIGNMENT.match(w)),
                         len(command))
            found += [command[start:]] if command[start:] else []
            command = []
    return found


def followed(text: str, cwd: str, read, depth: int = 0) -> list[str]:
    """The shell scripts of the checkout a shell `text` run from `cwd` runs (`_runs`), and those they run, `DEPTH`
    deep, each once."""
    found: list[str] = []
    for rel in _runs(text, cwd, read) if depth < DEPTH else ():
        found += [item for item in (rel, *followed(read(rel), cwd, read, depth + 1)) if item not in found]
    return found


def invocations(script: str) -> tuple[list[list[str]], list[str]]:
    """The `up` commands of Docker Compose in a shell `script`, each as its words from the variables it sets on,
    and the lines that run one in a way its words do not say (a variable, a substitution, an open quote)."""
    found, unread = [], []
    for line in script.replace("\\\n", " ").splitlines():
        if not MENTION.search(line):
            continue
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=PUNCTUATION)
            lexer.whitespace_split, lexer.commenters = True, "#"
            words = list(lexer)
        except ValueError:
            unread.append(line.strip())
            continue
        command, unclear = [], False
        for word in [*words, ";"]:
            if not set(word) <= set(PUNCTUATION):
                command.append(word)
                continue
            start = next((n for n, w in enumerate(command) if w not in LEADERS), len(command))
            at = next((n for n in range(start, len(command)) if not ASSIGNMENT.match(command[n])), len(command))
            if command[at:at + 2] == ["docker", "compose"] or command[at:at + 1] == ["docker-compose"]:
                argv, computed = command[start:], lambda word: "$" in word or "`" in word
                subcommand = _split(argv)[2]
                if any(map(computed, argv)) and (subcommand in (None, "up") or computed(subcommand)):
                    unclear = True
                elif subcommand == "up":
                    found.append(argv)
            command = []
        if unclear:
            unread.append(line.strip())
    return found, unread


def options(argv: list[str]) -> tuple[list[str], list[str], bool, dict]:
    """A `docker compose up` command's words (`invocations`) as Compose reads them: its global options, the
    services `up` names, whether it starts them without those they depend on (`--no-deps`), the variables it
    sets."""
    env, given, _, rest = _split(argv)
    services, no_deps, i = [], False, 0
    while i < len(rest):
        no_deps = no_deps or rest[i] == "--no-deps"
        if not rest[i].startswith("-"):
            services.append(rest[i])
        i += 2 if rest[i] in UP_VALUED else 1
    return given, services, no_deps, env


def not_read(path: str, line: str) -> dict:
    return {"kind": "compose_not_read", "path": path,
            "detail": f"{path} runs `{line}`, which Daodan does not read: the services it starts do not start beside "
                      "the tests"}


def _runs(text: str, cwd: str, read) -> list[str]:
    """The shell scripts of the checkout a shell `text` run from `cwd` names (a word with a `/` or `.sh` that is
    such a file: `.sh`, or a shell's `#!`), each relative to the project."""
    try:
        lexer = shlex.shlex(text.replace("\\\n", " "), posix=True, punctuation_chars=PUNCTUATION)
        lexer.whitespace_split, lexer.commenters = True, "#"
        words = list(lexer)
    except ValueError:
        return []
    found = []
    for word in words:
        if ("/" not in word and not word.endswith(".sh")) or set("$`=*") & set(word) or word.startswith("-"):
            continue
        rel = posixpath.normpath(posixpath.join(cwd, word))
        body = read(rel) if rel not in found and not rel.startswith(("/", "..")) else None
        if body is not None and (rel.endswith(".sh") or SHELL.match(body)):
            found.append(rel)
    return found


def started(path: str, text: str, cwd: str, read, depth: int = 0) -> tuple[list[tuple[str, list[str]]], list[dict]]:
    """The `docker compose up` commands (`invocations`) a shell `text` written at `path` runs from `cwd`, each with
    the path it is written at: `text`'s, and the shell scripts' of the checkout it runs (`_runs`), which run from
    the same folder; `read(rel)` is a file's text or None. A gap for a line Daodan does not read, and for a script
    that changes folder and runs Compose."""
    words, unread = invocations(text)
    found, gaps = [(path, argv) for argv in words], [not_read(path, line) for line in unread]
    for rel in _runs(text, cwd, read) if depth < DEPTH else ():
        body = read(rel)
        more, said = started(rel, body, cwd, read, depth + 1)
        if (more or said) and MOVES.search(body):
            more, said = [], [{"kind": "compose_not_read", "path": rel,
                               "detail": f"{rel} changes folder and runs Docker Compose, or a script that does, in "
                                         "a folder Daodan does not follow: the services it starts do not start beside "
                                         "the tests"}]
        found, gaps = found + more, gaps + said
    return found, gaps


def facts(found: list[tuple[str, list[str]]], cwd: str, **more) -> list[dict]:
    """The `compose` entries of the commands `started` finds: `declared_in` the path each is written at, numbered
    after the first of a path."""
    counted: dict[str, int] = {}
    entries = []
    for path, argv in found:
        number = counted[path] = counted.get(path, -1) + 1
        entries.append({"declared_in": path if number == 0 else f"{path}.{number}", "cwd": cwd, "argv": argv,
                        **{key: value for key, value in more.items() if value}})
    return entries


def reader(context):
    """A checkout file's text by its path: the snapshot's, else the file on disk the snapshot leaves out (a script
    with no suffix), links not followed; None for no file."""
    def read(rel: str) -> str | None:
        try:
            if rel in context.inventory.headers:
                return context.inventory.text(rel)
            path = Path(context.root) / rel
            confinement.reject_link_chain(path)
            return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None
        except (OSError, ValueError):
            return None
    return read


def scripts(context) -> tuple[list[dict], list[dict]]:
    """The npm test scripts that run `docker compose up` (`invocations`), as the `compose` facet states them: the
    script each `tests` entry names (`<package.json>#scripts.<name>`) and its `pre` script, which npm runs first,
    in the package's folder; a gap for one that runs Compose in a way its words do not say."""
    found, gaps, seen = [], [], set()
    for entry in (getattr(context, "stated", None) or {}).get("tests") or ():
        rel, _, name = str(entry.get("declared_in") or "").partition("#scripts.")
        if not name or posixpath.basename(rel) != "package.json" or (rel, name) in seen:
            continue
        seen.add((rel, name))
        try:
            declared = json.loads(context.inventory.text(rel)).get("scripts") or {}
        except (KeyError, OSError, ValueError, AttributeError):
            continue  # an unreadable manifest is the module graph's gap
        for script in (f"pre{name}", name):
            text = declared.get(script)
            if isinstance(text, str):
                more, said = started(f"{rel}#scripts.{script}", text, entry["root"], reader(context))
                found, gaps = found + facts(more, entry["root"]), gaps + said
    return found, gaps


def commands(context):
    steps = (getattr(context, "stated", None) or {}).get("compose") or []
    return [{"tool": NAME, "argv": ["docker-compose", *given, "config", "--format", "json", *services],
             "cwd": step["cwd"], "env": {**{key: str(value) for key, value in (step.get("env") or {}).items()}, **env},
             "network": "none"}
            for step in steps for given, services, _, env in [options(step["argv"])]] or None


def _relative(path: str, root: str) -> str:
    """`path` relative to the project's copy at `root` where it lies inside it, else as Compose gives it."""
    inside = root and (path == root or path.startswith(root.rstrip("/") + "/"))
    return posixpath.relpath(path, root) if inside else path


def _service(path: str, name: str, service: dict, root: str, job_env) -> dict:
    ports = [(f"{port['published']}:{port['target']}" if port.get("published") else str(port["target"]))
             + ("" if port.get("protocol", "tcp") == "tcp" else f"/{port['protocol']}")
             for port in service.get("ports") or ()]
    binds = [f"{_relative(item['source'], root)}:{item['target']}" + (":ro" if item.get("read_only") else "")
             for item in service.get("volumes") or () if item.get("type") == "bind"]
    env = {key: value for key, value in (service.get("environment") or {}).items() if value is not None}
    ignored = sorted(key for key, value in service.items() if key not in USED | INERT and value not in (None, [], {}))
    build = service.get("build")
    after = {other: (how or {}).get("condition", "service_started") for other, how in
             (service.get("depends_on") or {}).items()}
    return {"name": name, "image": service.get("image") or "", "declared_in": f"{path}.services.{name}",
            "host": "localhost", **({"env": env} if env else {}), **({"ports": ports} if ports else {}),
            **{key: service[key] for key in ("healthcheck", "command", "entrypoint") if service.get(key)},
            **({"binds": binds} if binds else {}), **({"after": after} if after else {}),
            **({"build": _relative(build.get("context") or ".", root)} if isinstance(build, dict) else {}),
            **({"ignored": ignored} if ignored else {}), **({"job_env": job_env} if job_env else {})}


def read(context, commands, results):
    facts, gaps = [], []
    for step, result in zip(context.stated["compose"], results):
        path, said = step["declared_in"], (result.get("stderr") or "").strip()
        if result["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": path,
                         "detail": f"{path}: docker compose config in {step['cwd']}: {said[-400:]}"})
            continue
        unset = [line for line in said.splitlines() if UNSET.search(line)]
        if unset:
            gaps.append({"kind": "model_partial", "path": path,
                         "detail": f"{path}: docker compose config: {' | '.join(unset)[-400:]}"})
        _, named, no_deps, _ = options(step["argv"])
        for name, service in sorted(((json.loads(result["stdout"]) or {}).get("services") or {}).items()):
            if not (no_deps and named and name not in named):
                facts.append(_service(path, name, service, result.get("root") or "", step.get("job_env")))
    return {"facts": {"services": facts} if facts else {}, **({"gaps": gaps} if gaps else {})}
