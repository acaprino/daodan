"""Source: pip's requirements files, read as pip reads them, never run.

A requirements file is a `.txt` or `.in` whose name holds `requirements`, or one in a `requirements/` folder
(it belongs to the folder above). A folder whose only Python manifest is a requirements file is a
`python-project` unit, without a name, its manifest `requirements.in`, else `requirements.txt`, else the first
by name; a requirements file beside a `pyproject.toml` or below a Python unit adds to that unit and makes no
other. `-r` includes belong to the including file's unit, `-c` constraints are no dependencies, `-e` and bare
local paths (from the unit's folder, where pip runs) are edges to the unit at that path, `--index-url` and `--extra-index-url` are registries. A file
pip-compile wrote (its header names the `.in` it compiled) is the lock of that `.in`: its pins are the
`resolved` versions of the `.in`'s requirements, and it declares nothing itself. Every requirements file of a
unit is in its `config.requirements`.
"""
from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
import re
from urllib.parse import urlsplit

NAME, VERSION, RANK = "requirements", "daodan/premap/v1", "reader"
INCLUDE = re.compile(r"^(-r|--requirement|-c|--constraint)(?:\s+|=)(\S+)$")
INDEX = re.compile(r"^(?:-i|--index-url|--extra-index-url)(?:\s+|=)(\S+)$")
EDITABLE = re.compile(r"^(?:-e|--editable)(?:\s+|=)(\S+)$")
REQUIREMENT = re.compile(r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)\s*(?:\[[^\]]*\])?\s*(.*)$")
COMPILED = re.compile(r"^#\s+pip-compile\b.*?\s(\S+\.in)\s*$", re.M)
PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==([^\s;#]+)", re.M)
PREFERRED = ("requirements.in", "requirements.txt")


def _parent(rel: str) -> str:
    return PurePosixPath(rel).parent.as_posix() if "/" in rel else "."


def _join(folder: str, name: str) -> str:
    value = posixpath.normpath(name if folder == "." else f"{folder}/{name}")
    return "." if value in ("", ".") else value


def _inside(rel: str, root: str) -> bool:
    return root == "." or rel == root or rel.startswith(root + "/")


def is_requirements(rel: str) -> bool:
    path = PurePosixPath(rel)
    return path.suffix in (".txt", ".in") and ("requirements" in path.name or path.parent.name == "requirements")


def _home(rel: str) -> str:
    """The folder a requirements file speaks for: its own, or the one above a `requirements/` folder."""
    folder = _parent(rel)
    return _parent(folder) if PurePosixPath(folder).name == "requirements" else folder


def _lines(text: str) -> list[str]:
    joined = re.sub(r"\\\n", " ", text)
    return [re.split(r"(?:^|\s)#", line, maxsplit=1)[0].strip() for line in joined.splitlines()]


def _parse(text: str) -> dict:
    out = {"includes": [], "constraints": [], "indexes": [], "paths": [], "requirements": []}
    for line in _lines(text):
        if not line:
            continue
        include = INCLUDE.match(line)
        if include:
            out["includes" if include.group(1) in ("-r", "--requirement") else "constraints"].append(include.group(2))
            continue
        index = INDEX.match(line)
        if index:
            out["indexes"].append(index.group(1))
            continue
        editable = EDITABLE.match(line)
        target = editable.group(1) if editable else line if line.startswith((".", "/")) else None
        if target is not None:
            if not re.match(r"^[a-z+]+://", target):
                out["paths"].append(target)
            continue
        if line.startswith("-"):
            continue  # another pip option: it declares no package
        requirement = REQUIREMENT.match(line)
        if requirement:
            spec = requirement.group(2).split(";", 1)[0].strip()
            declared = spec[1:].strip() if spec.startswith("@") else spec or None
            out["requirements"].append((requirement.group(1), declared))
    return out


def _in_files(context) -> dict[str, str]:
    """The `.in` requirements files of the folders the snapshot holds: the snapshot does not inventory `.in`, so
    they are read from disk, in those folders only (the map's perimeter)."""
    import confinement
    found = {}
    for folder in sorted(context.inventory.directories):
        base = context.root / folder if folder != "." else context.root
        try:
            names = sorted(p.name for p in base.iterdir() if p.is_file())
        except OSError:
            continue
        for name in names:
            rel = name if folder == "." else f"{folder}/{name}"
            if rel.endswith(".in") and is_requirements(rel):
                confinement.reject_link_chain(base / name)
                found[rel] = (base / name).read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    return found


def run(context):
    inventory = context.inventory
    disk = _in_files(context)
    files = sorted({rel for rel in inventory.files if is_requirements(rel)} | set(disk))
    if not files:
        return None
    text = lambda rel: disk[rel] if rel in disk else inventory.text(rel)  # noqa: E731
    from premap.module_graph import references
    ref = references(context.graph)
    python = sorted(((m["members"][0]["path"], ref[m["id"]]) for m in context.graph["modules"]
                     if m["provenance"] == "build" and "python" in m["ecosystems"]), key=lambda r: -len(r[0]))
    roots = {m["members"][0]["path"]: ref[m["id"]] for m in context.graph["modules"] if m["provenance"] == "build"}
    parsed = {rel: _parse(text(rel)) for rel in files}
    compiled = {rel: _join(_parent(rel), match.group(1)) for rel in files
                for match in [COMPILED.search(text(rel))] if match}
    included = {_join(_parent(rel), name) for rel in files for name in parsed[rel]["includes"]}
    constraints = {_join(_parent(rel), name) for rel in files for name in parsed[rel]["constraints"]}
    # Each file's unit folder: a file no other includes speaks for its own folder; an included one goes with
    # the first file that includes it.
    home, queue = {}, [rel for rel in files if rel not in included and rel not in constraints]
    for rel in queue:
        home.setdefault(rel, _home(rel))
    while queue:
        rel = queue.pop(0)
        for name in parsed[rel]["includes"]:
            target = _join(_parent(rel), name)
            if target in parsed and target not in home:
                home[target] = home[rel]
                queue.append(target)
    for rel in files:
        if rel not in home and rel not in constraints:
            home[rel] = _home(rel)
    for rel, source in compiled.items():  # a lock goes with the `.in` it compiles, even when used as a constraint
        if source in home:
            home[rel] = home[source]
    pins = {compiled[rel]: {name.lower(): version for name, version in PIN.findall(text(rel))} for rel in compiled}
    units, dependencies, gaps, by_folder = [], [], [], {}
    for rel, folder in sorted(home.items()):
        by_folder.setdefault(folder, []).append(rel)
    for folder, members in sorted(by_folder.items()):
        owner = next(((root, name) for root, name in python if _inside(folder, root)), None)
        unit_name = owner[1] if owner else None
        unit = {"root": owner[0] if owner else folder, "kind": "python-project",
                "config": {"requirements": sorted(members)}}
        if owner is None:
            names = [m for m in members if m not in compiled]
            unit["manifest"] = next((_join(folder, p) for p in PREFERRED if _join(folder, p) in names), sorted(names)[0]
                                    if names else sorted(members)[0])
            unit["name"] = None
        origins, depends = set(), set()
        for rel in members:
            if rel in compiled:
                continue
            facts = parsed[rel]
            origins |= {f"{u.scheme}://{u.netloc}" for u in map(urlsplit, facts["indexes"]) if u.scheme in ("http", "https")}
            for path in facts["paths"]:  # pip reads a local path from where it runs: the unit's folder
                target = _join(folder, path)
                if target in roots:
                    depends.add(roots[target])
                else:
                    gaps.append({"kind": "dependency_unresolved", "path": rel,
                                 "detail": f"{path}: no build unit at {target}"})
            for name, declared in facts["requirements"]:
                item = {"unit": unit_name, "name": name, "declared": declared, "declared_in": rel}
                if pins.get(rel, {}).get(name.lower()):
                    item["resolved"] = pins[rel][name.lower()]
                dependencies.append(item)
        if origins:
            unit["registries"] = sorted(origins)
        if depends:
            unit["depends_on"] = sorted(depends)
        units.append(unit)
    return {"facts": {"units": units, "dependencies": dependencies}, "gaps": gaps}
