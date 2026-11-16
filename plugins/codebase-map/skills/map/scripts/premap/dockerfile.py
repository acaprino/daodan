"""Source: BuildKit's own reading of each Dockerfile, for a build that only its Dockerfile declares.

`commands` describes, in Daodan's container with no network, `daodan-dockerfile`: `dockerfile_stages.go` beside
this file, built with BuildKit's Dockerfile frontend at `VERSION` (its parser, `instructions.Parse` and the shell
lexer BuildKit expands words with), which prints each stage with its base and each instruction with its lines,
its words expanded with the Dockerfile's ARG and ENV values and its flags. A build is declared where Compose
declares it: per Compose file of a folder (the first of `COMPOSE_FILES`, as Compose picks it), Compose itself
(`docker-compose config --format json`, the static binary `compose` pins) resolves each service's `build`, its
context, Dockerfile and arguments with the `.env` interpolated, and the helper reads that Dockerfile with them.
Any other Dockerfile is read as `docker build <its folder>` reads it: that folder the context, no argument.
`read` states each as a `docker_builds` fact: `dockerfile`, `context`, `args`, BuildKit's `stages`, and for
Compose's `declared_in` and `target`; a Dockerfile BuildKit does not read, or a Compose file Compose does not, is
a `model_failed` gap naming it. What a stage's steps need and leave is the analyzers' (`docker_build.py`): the
pre-map runs none of them.
"""
from __future__ import annotations

import json
import posixpath
import shlex

NAME, VERSION, RANK = "buildkit", "v0.34.2", "model"  # github.com/moby/buildkit, released 2026-11-03
TOOL = "daodan-dockerfile"
COMPOSE_FILES = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")  # Compose's order
MODEL = "/tmp/daodan-compose.json"


def commands(context):
    files = context.inventory.files
    chosen = {}
    for rel in files:
        folder, name = posixpath.dirname(rel), posixpath.basename(rel)
        if name in COMPOSE_FILES and (folder not in chosen or COMPOSE_FILES.index(name)
                                      < COMPOSE_FILES.index(posixpath.basename(chosen[folder]))):
            chosen[folder] = rel
    composed = [{"tool": TOOL, "argv": ["sh", "-c", f"cd {shlex.quote(posixpath.dirname(rel) or '.')}"
                                        f" && docker-compose -f {shlex.quote(posixpath.basename(rel))} config"
                                        f" --format json > {MODEL} && exec {TOOL} --compose {MODEL}", rel],
                 "cwd": ".", "env": {}, "network": "none"} for rel in sorted(chosen.values())]
    alone = [{"tool": TOOL, "argv": [TOOL, rel, "{}"], "cwd": ".", "env": {}, "network": "none"}
             for rel in sorted(files) if posixpath.basename(rel) == "Dockerfile"]
    return [*composed, *alone] or None


def _under(folder: str, rel: str) -> str:
    return posixpath.normpath(posixpath.join(folder, rel)) if folder else posixpath.normpath(rel)


def read(context, commands, results):
    facts, gaps, built = [], [], set()
    for command, result in zip(commands, results):
        if command["argv"][0] == "sh":  # a Compose file
            rel = command["argv"][3]
            folder = posixpath.dirname(rel)
            if result["returncode"] != 0:
                gaps.append({"kind": "model_failed", "path": rel,
                             "detail": f"{NAME}: {(result['stderr'] or '').strip()[-400:]}"})
                continue
            answer = json.loads(result["stdout"])
            for build in answer["builds"]:
                dockerfile = _under(folder, build["dockerfile"])
                built.add(dockerfile)
                facts.append({"dockerfile": dockerfile, "context": _under(folder, build["context"]),
                              "args": build["args"], "stages": build["stages"],
                              "declared_in": f"{rel}#services.{build['service']}.build",
                              **({"target": build["target"]} if build.get("target") else {})})
            for error in answer.get("errors") or ():
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
        facts.append({"dockerfile": rel, "context": posixpath.dirname(rel) or ".", "args": json.loads(command["argv"][2]),
                      "stages": json.loads(result["stdout"])["stages"]})
    return {"facts": {"docker_builds": facts} if facts else {}, **({"gaps": gaps} if gaps else {})}
