"""Source: BuildKit's own reading of each Dockerfile, for a build that only its Dockerfile declares.

`commands` describes, in Daodan's container with no network, `daodan-dockerfile`: `dockerfile_stages.go` beside
this file, built with BuildKit's Dockerfile frontend at `VERSION` (its parser, `instructions.Parse` and the shell
lexer BuildKit expands words with), which prints each stage with its base and each instruction with its lines,
its words expanded with the Dockerfile's ARG and ENV values and its flags. A build is declared where Compose
declares it: per Compose file of a folder (the first of `COMPOSE_FILES`, as Compose picks it), Compose itself
(`docker-compose config --format json`, the static binary `compose` pins, which the helper runs) resolves each
service's `build`, its context, Dockerfile and arguments, and the helper reads that Dockerfile with them.
Any other Dockerfile is read as `docker build <its folder>` reads it: that folder the context, no argument.
`read` states each as a `docker_builds` fact: `dockerfile`, `context`, `args`, BuildKit's `stages`, for Compose's
`declared_in` and `target`, and where an ignore file is the `dockerignore` BuildKit reads (the Dockerfile's own
before the context's) with what it leaves out of the context (`excluded`, relative to it, a folder ending in /,
by BuildKit's own matcher); a Dockerfile BuildKit does not read, or a Compose file Compose does not, is
a `model_failed` gap naming it, with Compose's error and the variables it found unset. A value of a tracked
`.env` file never reaches a fact: Compose reads the values the pre-map's container keeps beside the copy
(`container.named`), and the helper writes, for an argument that names a variable of it, `${NAME}`, and for a
context or Dockerfile one names, the tracked path it gives (else a gap naming the variable); `dotenv` names the
file of each such variable. What a
stage's steps need and leave is the analyzers' (`docker_build.py`): the pre-map runs none of them.
"""
from __future__ import annotations

import json
import posixpath
import re
import shlex

from premap import compose

NAME, VERSION, RANK = "buildkit", "v0.34.2", "model"  # github.com/moby/buildkit, released 2026-11-03
TOOL = "daodan-dockerfile"
COMPOSE_FILES = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")  # Compose's order
WARNING = re.compile(r"level=warning")  # Compose's warnings, printed after its error
UNSET = re.compile(r'The \\?"(\w+)\\?" variable is not set')  # a variable Compose interpolates blank


def commands(context):
    files = context.inventory.files
    chosen = {}
    for rel in files:
        folder, name = posixpath.dirname(rel), posixpath.basename(rel)
        if name in COMPOSE_FILES and (folder not in chosen or COMPOSE_FILES.index(name)
                                      < COMPOSE_FILES.index(posixpath.basename(chosen[folder]))):
            chosen[folder] = rel
    composed = [{"tool": TOOL, "argv": ["sh", "-c", f"cd {shlex.quote(posixpath.dirname(rel) or '.')}"
                                        f" && exec {TOOL} --compose {shlex.quote(posixpath.basename(rel))}", rel],
                 "cwd": ".", "env": {}, "network": "none"} for rel in sorted(chosen.values())]
    alone = [{"tool": TOOL, "argv": [TOOL, rel, "{}"], "cwd": ".", "env": {}, "network": "none"}
             for rel in sorted(files) if posixpath.basename(rel) == "Dockerfile"]
    return [*composed, *alone] or None


def _under(folder: str, rel: str) -> str:
    return posixpath.normpath(posixpath.join(folder, rel)) if folder else posixpath.normpath(rel)


def _ignored(answer: dict, folder: str) -> dict:
    """The ignore file BuildKit reads for a build, from the checkout's root, and what it leaves out of the
    context, relative to it (a folder ending in /): none without an ignore file."""
    if not answer.get("dockerignore"):
        return {}
    return {"dockerignore": _under(folder, answer["dockerignore"]), "excluded": answer.get("excluded") or []}


def read(context, commands, results):
    facts, gaps, built = [], [], set()
    for command, result in zip(commands, results):
        if command["argv"][0] == "sh":  # a Compose file
            rel = command["argv"][3]
            folder = posixpath.dirname(rel)
            if result["returncode"] != 0:
                said = compose._named(result["stderr"] or "", {})  # a tracked .env's placeholder: its name
                errors = " ".join(line.strip() for line in said.splitlines() if line.strip() and not WARNING.search(line))
                unset = sorted(set(UNSET.findall(said)))
                gaps.append({"kind": "model_failed", "path": rel,
                             "detail": f"{NAME}: docker compose config: {errors[-400:]}" + (
                                 f"; not set, so blank: {', '.join(unset)} (Daodan reads no .env: it may hold "
                                 f"secrets)" if unset else "")})
                continue
            answer = json.loads(result["stdout"])
            for build in answer["builds"]:
                names = dict(build.get("dotenv") or {})  # the variables of tracked .env files it reads, by file
                build = compose._named(build, names)
                dockerfile = _under(folder, build["dockerfile"])
                built.add(dockerfile)
                facts.append({"dockerfile": dockerfile, "context": _under(folder, build["context"]),
                              "args": build["args"], "stages": build["stages"],
                              "declared_in": f"{rel}#services.{build['service']}.build",
                              **({"target": build["target"]} if build.get("target") else {}),
                              **_ignored(build, folder), **({"dotenv": names} if names else {})})
            for error in answer.get("errors") or ():
                error = compose._named(error, {})
                dockerfile = _under(folder, error["dockerfile"])
                built.add(dockerfile)
                gaps.append({"kind": "model_failed", "path": dockerfile,
                             "detail": f"{NAME}: {rel}#services.{error['service']}.build: {error['error'][-400:]}"})
            continue
        rel = command["argv"][1]
        if rel in built:
            continue
        if result["returncode"] != 0:
            gaps.append({"kind": "model_failed", "path": rel,
                         "detail": f"{NAME}: {(result['stderr'] or '').strip()[-400:]}"})
            continue
        answer = json.loads(result["stdout"])
        facts.append({"dockerfile": rel, "context": posixpath.dirname(rel) or ".", "args": json.loads(command["argv"][2]),
                      "stages": answer["stages"], **_ignored(answer, "")})
    return {"facts": {"docker_builds": facts} if facts else {}, **({"gaps": gaps} if gaps else {})}
