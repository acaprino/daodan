"""The type packages the TypeScript index needs beside the project's own, as the Java index has the JDK's classes
and the C one the system headers. It runs in the container after the project's restore; standard library only:
the image's python3 runs it.

    python3 typescript_types.py WORK NODE_MAJOR TYPES ROOT...

TypeScript knows Node's own API and an untyped package only through `@types` packages: `@types/node` at NODE_MAJOR
unless the copy's root has its own, and `@types/<package>` for each package a ROOT's manifest declares that is
installed with no types of its own and no `@types` package within its reach. Each is installed alone into TYPES,
so npm never touches the project's tree, and linked into WORK/node_modules/@types, the last folder TypeScript's
lookup reaches from any file of the copy: a package the project resolves itself is never shadowed, and no tsconfig
changes. Each added package is printed on stderr `DAODAN-TYPES-ADDED name@version`; one the registry does not have,
`DAODAN-TYPES-ABSENT name`, is not an error; one npm could not install otherwise, `DAODAN-MISSING name@range`.

TypeScript 6, the one scip-typescript runs, loads no `@types` package a program does not name (`types` defaults to
[]), so Node's own API is named in TYPES/references.d.ts, which the generated tsconfig includes: a file of the
program beside the project's `types`, never in their place. The other packages are reached by their imports.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

FIELDS = ("dependencies", "devDependencies", "optionalDependencies")
LOCAL = ("workspace:", "file:", "link:", "portal:")  # a package of the project, not of a registry


def _json(path: str):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _found(work: str, folder: str, name: str) -> str | None:
    """The folder of package `name` Node's lookup from `folder` reaches first, up to `work`; None when none."""
    here, top = os.path.normpath(os.path.join(work, folder)), os.path.normpath(work)
    while True:
        candidate = os.path.join(here, "node_modules", name)
        if os.path.isfile(os.path.join(candidate, "package.json")):
            return candidate
        if here == top or os.path.dirname(here) == here:
            return None
        here = os.path.dirname(here)


def _typed(package: str) -> bool:
    """Whether an installed package ships its own types."""
    manifest = _json(os.path.join(package, "package.json"))
    manifest = manifest if isinstance(manifest, dict) else {}
    main = os.path.splitext(str(manifest.get("main") or "index.js"))[0]
    return bool(manifest.get("types") or manifest.get("typings")
                or '"types"' in json.dumps(manifest.get("exports") or {})
                or os.path.isfile(os.path.join(package, "index.d.ts"))
                or os.path.isfile(os.path.join(package, main + ".d.ts")))


def types_package(name: str) -> str:
    """The DefinitelyTyped package of a library: `pg` is `@types/pg`, `@scope/name` is `@types/scope__name`."""
    return f"@types/{name[1:].replace('/', '__')}" if name.startswith("@") else f"@types/{name}"


def wanted(work: str, major: str, roots: list[str]) -> list[str]:
    """The type packages to add, `@types/node@<major>` first: see the module's docstring."""
    out = [] if os.path.isdir(os.path.join(work, "node_modules", "@types", "node")) else [f"@types/node@{major}"]
    for root in roots:
        manifest = _json(os.path.join(work, root, "package.json"))
        manifest = manifest if isinstance(manifest, dict) else {}
        for field in FIELDS:
            declared = manifest.get(field) if isinstance(manifest.get(field), dict) else {}
            for name, spec in sorted(declared.items()):
                if name.startswith("@types/") or str(spec).startswith(LOCAL):
                    continue
                types = types_package(name)
                package = _found(work, root, name)
                # A workspace member is a link out of every node_modules: the project's own code.
                local = package is not None and f"{os.sep}node_modules{os.sep}" not in os.path.realpath(package)
                if package is None or local or _typed(package) or _found(work, root, types) or types in out:
                    continue
                out.append(types)
    return out


def main(argv: list[str]) -> int:
    work, major, types, roots = argv[1], argv[2], argv[3], argv[4:]
    os.makedirs(types, exist_ok=True)
    for package in wanted(work, major, roots):
        name = package if package.count("@") == 1 else package.rsplit("@", 1)[0]
        done = subprocess.run(["npm", "install", "--prefix", types, "--ignore-scripts", "--no-audit", "--no-fund",
                               "--loglevel=error", package], capture_output=True, text=True)
        installed = _json(os.path.join(types, "node_modules", name, "package.json"))
        if done.returncode or not isinstance(installed, dict):
            said = done.stdout + done.stderr
            print(f"DAODAN-TYPES-ABSENT {name}" if "E404" in said else
                  f"{said.strip()[-600:]}\nDAODAN-MISSING {package if '@' in package[1:] else package + '@latest'}",
                  file=sys.stderr, flush=True)
            continue
        link = os.path.join(work, "node_modules", name)
        if not os.path.lexists(link):
            os.makedirs(os.path.dirname(link), exist_ok=True)
            os.symlink(os.path.join(types, "node_modules", name), link)
        print(f"DAODAN-TYPES-ADDED {name}@{installed.get('version')}", file=sys.stderr, flush=True)
    if os.path.isdir(os.path.join(work, "node_modules", "@types", "node")):
        with open(os.path.join(types, "references.d.ts"), "w", encoding="utf-8") as handle:
            handle.write('/// <reference types="node" />\n')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
