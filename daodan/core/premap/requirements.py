"""Source: pip's requirements files, read with pip's own parser (`pip-requirements-parser`), never run.

A requirements file is a `.txt` or `.in` whose name holds `requirements`, or one in a `requirements/` folder
(it belongs to the folder above). A folder whose only Python manifest is a requirements file is a
`python-project` unit, without a name, its manifest `requirements.in`, else `requirements.txt`, else the first
by name; a requirements file beside a `pyproject.toml` or below a Python unit adds to that unit and makes no
other. `-r` includes belong to the including file's unit, `-c` constraints to none; `-e` and bare local paths
(from the unit's folder, where pip runs) are edges to the unit at that path; the origins of `--index-url`,
`--extra-index-url`, `--find-links` and of the URL a requirement names (`name @ URL`, a VCS URL, `-e URL`) are
registries. A file pip-compile wrote (its header names the `.in` it compiled) goes with
that `.in`. Every requirements file of a unit is in its `config.requirements`; the packages they name are not
the pre-map's.
"""
from __future__ import annotations

import ast
import configparser
import posixpath
from pathlib import Path, PurePosixPath
import re
import tempfile
import tomllib

from build_units import normalize_pypi_name, requirement_version
from premap.origins import origin

NAME, VERSION, RANK = "requirements", "daodan/premap/v2", "reader"
# pip-compile's header names the `.in` it compiled: a comment, text without grammar.
COMPILED = re.compile(r"^#\s+pip-compile\b.*?\s(\S+\.in)\s*$", re.M)
PREFERRED = ("requirements.in", "requirements.txt")
INDEXES = ("index_url", "extra_index_urls", "find_links")  # pip's option names (`dest`) for where packages come from


def read(text: str):
    """A requirements file as pip reads it, with pip's own parser (`pip-requirements-parser`: pip's `req_file.py`
    and `constructors.py` as a library): its requirements, its option lines (`-r`, `-c`, the indexes), its invalid
    lines; nested files are not followed. The parser reads a path: the text goes to a temporary file with a UTF-8
    BOM, which pip decodes before any locale."""
    from pip_requirements_parser import RequirementsFile
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "requirements.txt"
        path.write_text(text, encoding="utf-8-sig")
        return RequirementsFile.from_file(str(path))


def local(link) -> bool:
    """Whether pip's `link` names a path (a folder, an archive) rather than a URL."""
    from pip_requirements_parser import is_url
    return link is not None and not is_url(link.url)


def vcs(text: str) -> tuple[str, str] | None:
    """`(name, URL)` of one requirement that names a VCS URL, as pip reads it: PEP 508 `name @ git+URL` (parsed by
    `packaging`) or pip's `git+URL#egg=name`; the URL without its `git+`; None for any other requirement."""
    from pip_requirements_parser import build_install_req
    try:
        req = build_install_req(str(text).strip())
    except Exception:  # pip's own refusal of a line that is no requirement: InstallationError, InvalidRequirement
        return None
    if req.link is None or not req.link.is_vcs:
        return None
    return req.name or "", req.link.url.split("+", 1)[1]


def _strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


def _table(value) -> dict:
    return value if isinstance(value, dict) else {}


def vcs_requirements(rel: str, text: str) -> list[tuple[str, str]]:
    """The VCS requirements a Python manifest declares, `(name, URL)`: a requirements file read by pip's parser;
    in `pyproject.toml` (`tomllib`) the PEP 508 lists (`[project]` dependencies and extras, `[dependency-groups]`,
    `[build-system]`, uv's `dev-dependencies`) and the `git` sources of `[tool.uv.sources]` and of Poetry's
    dependency tables; in `setup.cfg` (`configparser`) the requirement options of `[options]` and
    `[options.extras_require]`; in `setup.py` (`ast`, never run) every string literal pip reads as one; any other
    file is a requirements file."""
    name = PurePosixPath(rel).name
    found: list = []
    if name == "pyproject.toml":
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            return []
        project, tool = _table(data.get("project")), _table(data.get("tool"))
        uv, poetry = _table(tool.get("uv")), _table(tool.get("poetry"))
        lists = [project.get("dependencies"), _table(data.get("build-system")).get("requires"),
                 uv.get("dev-dependencies"), *_table(project.get("optional-dependencies")).values(),
                 *_table(data.get("dependency-groups")).values()]
        found += [vcs(item) for value in lists for item in _strings(value)]
        sources = [_table(uv.get("sources")), _table(poetry.get("dependencies")), _table(poetry.get("dev-dependencies")),
                   *(_table(_table(group).get("dependencies")) for group in _table(poetry.get("group")).values())]
        found += [(key, entry["git"]) for source in sources for key, value in source.items()
                  for entry in (value if isinstance(value, list) else [value])
                  if isinstance(entry, dict) and isinstance(entry.get("git"), str)]
    elif name == "setup.cfg":
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        try:
            parser.read_string(text)
        except configparser.Error:
            return []
        values = [parser.get("options", key, fallback="") for key in
                  ("install_requires", "setup_requires", "tests_require", "dependency_links")]
        if parser.has_section("options.extras_require"):
            values += [value for _key, value in parser.items("options.extras_require")]
        found += [vcs(line) for value in values for line in value.splitlines()
                  if line.strip() and not line.strip().startswith("#")]
    elif name == "setup.py":
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError):
            return []
        found += [vcs(node.value) for node in ast.walk(tree)
                  if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    else:  # a requirements file
        found += [(req.name or "", req.link.url.split("+", 1)[1]) for req in read(text).requirements
                  if req.link is not None and req.link.is_vcs]
    return [item for item in found if item]


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
    """The requirement lines of a requirements file, joined and without comments as pip reads them (`read`)."""
    return [req.line for req in read(text).requirements if req.line]


def _parse(text: str) -> dict:
    found = read(text)
    out = {"includes": [], "constraints": [], "origins": set(), "paths": [], "requirements": found.requirements}
    for line in found.options:
        out["includes"] += line.options.get("requirements") or []
        out["constraints"] += line.options.get("constraints") or []
        out["origins"] |= {origin(url) for key in INDEXES for url in _strings(line.options.get(key))}
    for req in found.requirements:
        if local(req.link):  # `-e PATH` or a bare path: an edge to the unit there
            out["paths"].append(req.link.url)
        elif req.link is not None:  # `name @ URL`, a VCS URL, `-e URL`, an archive's URL
            out["origins"].add(origin(req.link.url))
    out["origins"].discard(None)
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
    python = sorted((m["members"][0]["path"] for m in context.graph["modules"]
                     if m["provenance"] == "build" and "python" in m["ecosystems"]), key=lambda r: -len(r))
    roots = {m["members"][0]["path"]: ref[m["id"]] for m in context.graph["modules"] if m["provenance"] == "build"}
    parsed = {rel: _parse(text(rel)) for rel in files}
    compiled = {rel: _join(_parent(rel), match.group(1)) for rel in files
                for match in [COMPILED.search(text(rel))] if match}
    included = {_join(_parent(rel), name) for rel in files for name in parsed[rel]["includes"]}
    for target in sorted(included & set(inventory.files) - set(files)):
        files.append(target)
        parsed[target] = _parse(text(target))
    files.sort()
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
    units, gaps, by_folder = [], [], {}
    for rel, folder in sorted(home.items()):
        by_folder.setdefault(folder, []).append(rel)
    for folder, members in sorted(by_folder.items()):
        owner = next((root for root in python if _inside(folder, root)), None)
        unit = {"root": owner or folder, "kind": "python-project",
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
            origins |= facts["origins"]
            for path in facts["paths"]:  # pip reads a local path from where it runs: the unit's folder
                target = _join(folder, path)
                if target in roots:
                    depends.add(roots[target])
                else:
                    gaps.append({"kind": "dependency_unresolved", "path": rel,
                                 "detail": f"{path}: no build unit at {target}"})
        if origins:
            unit["registries"] = sorted(origins)
        if depends:
            unit["depends_on"] = sorted(depends)
        units.append(unit)
    packages: list[dict] = []
    seen_pkgs: set[tuple[str, str]] = set()
    from pip_requirements_parser import break_args_options
    for rel in files:
        if rel in constraints:
            continue
        for req in parsed[rel]["requirements"]:
            # a named requirement, bare or `name @ URL`; not an editable, a path, or a URL named by its `#egg=`
            if not req.name or req.is_editable or (req.link is not None and not req.req.url):
                continue
            norm = normalize_pypi_name(req.name)
            # the PEP 508 requirement before pip's own options (` --hash=...`), split as pip splits them
            version = requirement_version(break_args_options(req.line)[0])
            if (norm, rel) not in seen_pkgs:
                seen_pkgs.add((norm, rel))
                packages.append({"ecosystem": "pypi", "name": norm, "declared_in": f"{rel}#L{req.line_number}",
                                 **({"version": version} if version else {})})
    return {"facts": {"units": units, **({"packages": packages} if packages else {})}, "gaps": gaps}
