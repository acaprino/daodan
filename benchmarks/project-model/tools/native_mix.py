"""Mix (Elixir): the project as Mix loads it, per mix.exs: `mix deps` (each dependency, its source and the
version mix.lock holds) and `mix run --no-compile --no-start --no-deps-check -e` printing Mix.Project.config's
app, version, Elixir requirement, declared deps and the umbrella's apps. Loading mix.exs runs it.
"""
from __future__ import annotations

import re
from pathlib import Path

import native_common as common

VERSION = "Elixir 1.17.3 on OTP 27.1.2"
VERSION_COMMAND = ["elixir", "--version"]
TRIGGERS = ("mix.exs",)
COMMAND = "mix deps; mix run --no-compile --no-start --no-deps-check -e <print Mix.Project.config>"
EXPR = ('c = Mix.Project.config(); IO.puts("APP\\t#{c[:app]}\\t#{c[:version]}\\t#{c[:elixir]}"); '
        'for {a, p} <- (Mix.Project.apps_paths() || %{}), do: IO.puts("MEMBER\\t#{a}\\t#{p}"); '
        'for d <- c[:deps] || [], do: IO.puts("DEP\\t#{elem(d, 0)}\\t#{inspect(Tuple.delete_at(d, 0))}")')
ENV = {"MIX_ENV": "dev", "HEX_OFFLINE": "0"}


def run(fixture_dir, work_dir) -> dict:
    root = Path(fixture_dir)
    units, workspaces, toolchains, dependencies, errors = [], [], [], [], []
    projects = {}
    for manifest in common.find(root, {"mix.exs"}, prune=common.PRUNE | {"deps", "_build"}):
        here, directory = root / common.parent(manifest), common.parent(manifest)
        done = common.run(["mix", "run", "--no-compile", "--no-start", "--no-deps-check", "-e", EXPR], here,
                          name="mix run -e Mix.Project.config", env=ENV)
        if done.returncode != 0:
            errors.append(f"{manifest}: mix run: {common.error_of(done)}")
            continue
        app, members, declared = None, [], []
        for line in done.stdout.splitlines():
            parts = line.split("\t")
            if parts[0] == "APP" and len(parts) >= 4:
                app = parts[1] or None
                if parts[3]:
                    toolchains.append({"tool": "elixir", "version": parts[3], "declared_in": manifest})
            elif parts[0] == "MEMBER" and len(parts) >= 3:
                members.append(common.rel(here / parts[2], root))
            elif parts[0] == "DEP" and len(parts) >= 3:
                declared.append((parts[1], parts[2]))
        listing = common.run(["mix", "deps"], here, name="mix deps", env=ENV)
        locked = {m.group(1): m.group(2) for m in re.finditer(r"^\* (\S+).*\n\s+locked at (\S+)", listing.stdout, re.M)}
        if listing.returncode != 0:
            errors.append(f"{manifest}: mix deps: {common.error_of(listing)}")
        projects[directory] = (app or Path(here).name, declared, locked)
        units.append({"name": app or Path(common.rel(here, root)).name or root.name, "kind": "mix-project",
                      "root": directory, "manifest": manifest})
        if members:
            workspaces.append({"tool": "mix", "root": directory, "members": sorted(members)})
    names = {u["name"] for u in units}
    for unit in units:
        app, declared, locked = projects[unit["root"]]
        depends = []
        for name, rest in declared:
            if name in names or "in_umbrella: true" in rest or "path:" in rest:
                depends.append(name)
                continue
            requirement = re.match(r'^\{"([^"]+)"', rest)
            dependencies.append({"unit": unit["name"], "name": name,
                                 "declared": requirement.group(1) if requirement else None,
                                 "resolved": locked.get(name), "scope": "runtime", "declared_in": unit["manifest"]})
        unit["depends_on"] = sorted(depends)
    common.NOTES.update(errors=errors, raw={})
    return {"units": units, "workspace": workspaces[0] if len(workspaces) == 1 else (workspaces or None),
            "toolchains": toolchains, "dependencies": dependencies}
