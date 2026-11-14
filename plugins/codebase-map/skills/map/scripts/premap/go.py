"""Source: the go command's model of every Go module, nested ones too.

`commands` describes, for Daodan's container: `go env -json GOPROXY`; in each folder holding a `go.work`, `go
work edit -json`; in each folder holding a `go.mod`, `go mod edit -json` (requirements as written), `go list -m
-json` (main modules), `go list -m -json all` (the build list) and `go list -e -json ./...` (packages), with
`GOWORK=off` and, for a module under a `go.work`, also in workspace mode. `-mod=readonly` and
`GOTOOLCHAIN=local`: nothing is written in the project, no project code runs. `read` keeps, for each module,
the answers of the mode Go applies to it (workspace mode when a `go.work` uses it). A command that fails is a
`model_failed` gap with its stderr.
"""
from __future__ import annotations

import json
import posixpath
from pathlib import PurePosixPath

NAME, VERSION, RANK = "go", "1.27.3", "model"  # the Go release Daodan pins (`resolve_edges.GO_VERSION`)
ENV = {"GOFLAGS": "-mod=readonly", "GOTOOLCHAIN": "local", "CGO_ENABLED": "1"}
OFF = {**ENV, "GOWORK": "off"}


def _parent(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _inside(rel: str, folder: str) -> bool:
    return folder == "." or rel == folder or rel.startswith(folder + "/")


def _stream(text: str) -> list:
    """The JSON values `go list -json` prints one after the other."""
    decoder, out, at, text = json.JSONDecoder(), [], 0, text.strip()
    while at < len(text):
        value, at = decoder.raw_decode(text, at)
        out.append(value)
        while at < len(text) and text[at].isspace():
            at += 1
    return out


def _command(argv: list[str], cwd: str, env: dict, network: str) -> dict:
    return {"tool": "go", "argv": argv, "cwd": cwd, "env": env, "network": network}


def commands(context):
    files = context.inventory.files
    works = [_parent(rel) for rel in files if PurePosixPath(rel).name == "go.work"]
    mods = [_parent(rel) for rel in files if PurePosixPath(rel).name == "go.mod"]
    if not mods:
        return None
    out = [_command(["go", "env", "-json", "GOPROXY"], ".", ENV, "none")]
    out += [_command(["go", "work", "edit", "-json"], work, ENV, "none") for work in works]
    for mod in mods:
        out.append(_command(["go", "mod", "edit", "-json"], mod, OFF, "none"))
        for env in [OFF] + ([ENV] if any(_inside(mod, work) for work in works) else []):
            out += [_command(["go", "list", "-m", "-json"], mod, env, "none"),
                    _command(["go", "list", "-m", "-json", "all"], mod, env, "registries"),
                    _command(["go", "list", "-e", "-json", "./..."], mod, env, "registries")]
    return out


def read(context, commands, results):
    answers = {(c["cwd"], " ".join(c["argv"]), c["env"].get("GOWORK")): r for c, r in zip(commands, results)}
    gaps, units, workspaces, toolchains, dependencies = [], [], [], [], []
    root = next((r["root"] for r in results if r.get("root")), "/")

    def rel(path: str) -> str:
        value = posixpath.relpath(path, root)
        return "." if value in ("", ".") else value

    def answer(cwd, argv, mode, *, report=True):
        result = answers.get((cwd, argv, mode))
        if result is None or result["returncode"] != 0:
            if report and result is not None:
                gaps.append({"kind": "model_failed", "path": cwd,
                             "detail": f"{argv}: {(result['stderr'] or result['stdout']).strip()[-400:]}"})
            return None
        return result["stdout"]

    proxy = json.loads(answer(".", "go env -json GOPROXY", None) or "{}").get("GOPROXY", "")
    registries = [entry for entry in proxy.replace("|", ",").split(",") if entry and entry != "off"]
    used = set()
    for cwd, argv, _mode in [k for k in answers if k[1] == "go work edit -json"]:
        text = answer(cwd, argv, None)
        if text is None:
            continue
        data = json.loads(text)
        members = [posixpath.normpath(posixpath.join(cwd, use["DiskPath"])) if cwd != "." else
                   posixpath.normpath(use["DiskPath"]) for use in data.get("Use") or []]
        used.update(members)
        workspaces.append({"tool": "go", "root": cwd, "members": members})
        work = "go.work" if cwd == "." else f"{cwd}/go.work"
        toolchains += [{"tool": "go", "version": data[key], "declared_in": work} for key in ("Go", "Toolchain") if data.get(key)]
    mods = sorted({cwd for cwd, argv, _ in answers if argv == "go mod edit -json"})
    mode_of = {mod: None if mod in used else "off" for mod in mods}
    mains = {}
    for mod in mods:
        for module in _stream(answer(mod, "go list -m -json", mode_of[mod]) or ""):
            if isinstance(module, dict) and module.get("Dir"):
                mains[module["Path"]] = rel(module["Dir"])
    for mod in mods:
        mode = mode_of[mod]
        module = next((m for m in _stream(answer(mod, "go list -m -json", mode, report=False) or "")
                       if isinstance(m, dict) and m.get("Dir") and rel(m["Dir"]) == mod), None)
        if module is None:
            gaps.append({"kind": "model_failed", "path": mod, "detail": "no go command named this module"})
            continue
        written = json.loads(answer(mod, "go mod edit -json", "off") or "{}")
        build = answer(mod, "go list -m -json all", mode)
        resolved = ({m["Path"]: m.get("Version") for m in _stream(build) if isinstance(m, dict) and not m.get("Main")}
                    if build is not None else None)
        packages = [p for p in _stream(answer(mod, "go list -e -json ./...", mode, report=False) or "")
                    if isinstance(p, dict)]
        manifest = rel(module.get("GoMod") or posixpath.join(root, mod, "go.mod"))
        config = {"packages": sorted(p["ImportPath"] for p in packages if p.get("ImportPath"))}
        ignored = sorted(rel(posixpath.join(p["Dir"], f)) for p in packages for f in p.get("IgnoredGoFiles") or [])
        if ignored:
            config["ignored_files"] = ignored
        cgo = [{"package": p["ImportPath"], "c_files": [rel(posixpath.join(p["Dir"], f)) for f in p.get("CFiles") or []]}
               for p in packages if p.get("CgoFiles")]
        if cgo:
            config["cgo"] = cgo
        if written.get("Replace"):
            config["replace"] = {r["Old"]["Path"]: r["New"]["Path"] + (f"@{r['New']['Version']}" if r["New"].get("Version") else "")
                                 for r in written["Replace"]}
        broken = [f"{p['ImportPath']}: {(p.get('Error') or {}).get('Err', '')[:160]}" for p in packages if p.get("Error")]
        if broken:
            gaps.append({"kind": "model_failed", "path": mod, "detail": "go list: " + "; ".join(broken[:5])})
        requires = written.get("Require") or []
        depends = sorted({r["Path"] for r in requires if r["Path"] in mains}
                         | {r["Old"]["Path"] for r in written.get("Replace") or [] if r["Old"]["Path"] in mains})
        for require in requires:
            if require["Path"] in mains or require.get("Indirect"):
                continue
            item = {"unit": module["Path"], "name": require["Path"], "declared": require.get("Version"),
                    "scope": "runtime", "declared_in": manifest}
            if resolved is not None and resolved.get(require["Path"]):
                item["resolved"] = resolved[require["Path"]]
            dependencies.append(item)
        dependencies += [{"unit": module["Path"], "name": tool["Path"], "scope": "dev", "declared_in": manifest}
                         for tool in written.get("Tool") or []]
        unit = {"name": module["Path"], "kind": "go-module", "root": mod, "manifest": manifest,
                "source_roots": [mod], "depends_on": depends, "config": config}
        if any(r["Path"] not in mains for r in requires):
            unit["registries"] = registries
        units.append(unit)
        toolchains += [{"tool": "go", "version": v, "declared_in": manifest}
                       for v in (module.get("GoVersion"), written.get("Toolchain")) if v]
    return {"facts": {"units": units, "workspace": workspaces, "toolchains": toolchains,
                      "dependencies": dependencies}, "gaps": gaps}
