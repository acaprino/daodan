"""Source: Docker Compose's own reading of the compose files a CI step starts (`docker compose config`).

Where the pre-map's `compose` facet names a step that runs `docker compose up` (`premap/renovate.py` reads it from
the workflows, and from the npm test scripts with `scripts`), `commands` describes one
`docker-compose <the step's options> config --format json <its services>`
where the step runs it, in Daodan's container with no network and no engine: Compose itself finds the files that
step's `up` finds, merges them, interpolates the variables the step sets and the project's `.env`, and keeps the
services `up` starts with those they depend on. `read` states each of them as a `services` fact: `declared_in`
`<step>.services.<name>`, `host` localhost (the job's later steps reach what they publish on its runner),
`environment` as `env`, `ports` as `published:target`, `healthcheck`, `command` and `entrypoint` as Compose gives
them, the bind mounts as `volumes` relative to the project, `build` where Compose builds the image, `ignored` the
keys it sets that no option here applies, and the job's `job_env`. A Compose that does not read the files is a
`model_failed` gap naming the step, a variable it does not find a `model_partial` one.

`invocations` and `options` read a step's script as the shell splits its words (`shlex`): a `docker compose` or
`docker-compose` command whose subcommand is `up`, from the variables it sets on, past `sudo` and the shell's
keywords.
"""
from __future__ import annotations

import json
import posixpath
import re
import shlex

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
USED = {"image", "environment", "ports", "healthcheck", "command", "entrypoint", "volumes", "build"}
INERT = {"networks", "depends_on", "restart", "container_name", "labels", "logging", "profiles", "pull_policy",
         "deploy", "expose", "stop_grace_period", "stop_signal", "hostname", "domainname"}  # nothing the tests reach
UNSET = re.compile(r"variable is not set", re.I)  # Compose's warning for a variable it interpolates blank


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
            text, path = declared.get(script), f"{rel}#scripts.{script}"
            if isinstance(text, str) and MENTION.search(text):
                words, unread = invocations(text)
                gaps += [not_read(path, line) for line in unread]
                found += [{"declared_in": path if number == 0 else f"{path}.{number}", "cwd": entry["root"],
                           "argv": argv} for number, argv in enumerate(words)]
    return found, gaps


def commands(context):
    steps = (getattr(context, "stated", None) or {}).get("compose") or []
    return [{"tool": NAME, "argv": ["docker-compose", *given, "config", "--format", "json", *services],
             "cwd": step["cwd"], "env": {**{key: str(value) for key, value in (step.get("env") or {}).items()}, **env},
             "network": "none"}
            for step in steps for given, services, _, env in [options(step["argv"])]] or None


def _relative(path: str, root: str) -> str:
    return posixpath.relpath(path, root) if root and posixpath.isabs(path) else path


def _service(path: str, name: str, service: dict, root: str, job_env) -> dict:
    ports = [(f"{port['published']}:{port['target']}" if port.get("published") else str(port["target"]))
             + ("" if port.get("protocol", "tcp") == "tcp" else f"/{port['protocol']}")
             for port in service.get("ports") or ()]
    binds = [f"{_relative(item['source'], root)}:{item['target']}" + (":ro" if item.get("read_only") else "")
             for item in service.get("volumes") or () if item.get("type") == "bind"]
    env = {key: value for key, value in (service.get("environment") or {}).items() if value is not None}
    ignored = sorted(key for key, value in service.items() if key not in USED | INERT and value not in (None, [], {}))
    build = service.get("build")
    return {"name": name, "image": service.get("image") or "", "declared_in": f"{path}.services.{name}",
            "host": "localhost", **({"env": env} if env else {}), **({"ports": ports} if ports else {}),
            **{key: service[key] for key in ("healthcheck", "command", "entrypoint") if service.get(key)},
            **({"volumes": binds} if binds else {}),
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
