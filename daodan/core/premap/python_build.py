"""Source: the package folders a Python build configuration declares, read from the file, never run.

`pyproject.toml`: `tool.setuptools.package-dir` and `tool.setuptools.packages.find.where`, hatch's wheel
`packages`, poetry's `packages[].from`, `tool.pdm.build.package-dir`, `tool.uv.build-backend.module-root`;
`setup.cfg`: `options.package_dir`; `setup.py`: a literal `package_dir={'': 'x'}`. Each becomes the unit's
`source_roots`. A configuration that declares none states nothing: the build backend's default (`src` when it
holds the package, else the root) is the backend's rule, and Pyright's, not a fact of the file. The unit's
`registries` are the origins of what the configuration says its dependencies come from: the URLs its requirements
name (`project.dependencies`, its extras, `dependency-groups`, setup.cfg's `install_requires` and extras), uv's
indexes (`tool.uv.index`, `index-url`, `extra-index-url`, `find-links`) and Poetry's (`tool.poetry.source`), the git
and URL sources of either.
"""
from __future__ import annotations

import configparser
from pathlib import PurePosixPath
import re
import tomllib

from premap.origins import origin, requirement

NAME, VERSION, RANK = "python-build", "daodan/premap/v1", "reader"
SETUP_PY = re.compile(r"""package_dir\s*=\s*\{\s*['"]['"]\s*:\s*['"]([^'"]+)['"]""")


def _join(root: str, folder: str) -> str:
    folder = folder.strip().strip("/").removeprefix("./") or "."
    return folder if root == "." else root if folder == "." else f"{root}/{folder}"


def _pyproject(data: dict) -> list[str]:
    tool = data.get("tool") if isinstance(data.get("tool"), dict) else {}
    found = []
    setuptools = tool.get("setuptools") if isinstance(tool.get("setuptools"), dict) else {}
    if isinstance(setuptools.get("package-dir"), dict) and isinstance(setuptools["package-dir"].get(""), str):
        found.append(setuptools["package-dir"][""])
    find = (setuptools.get("packages") or {}).get("find") if isinstance(setuptools.get("packages"), dict) else None
    if isinstance(find, dict) and isinstance(find.get("where"), list):
        found += [w for w in find["where"] if isinstance(w, str)]
    wheel = (((tool.get("hatch") or {}).get("build") or {}).get("targets") or {}).get("wheel") or {}
    if isinstance(wheel, dict) and isinstance(wheel.get("packages"), list):
        found += [PurePosixPath(p).parent.as_posix() for p in wheel["packages"] if isinstance(p, str)]
    poetry = tool.get("poetry") if isinstance(tool.get("poetry"), dict) else {}
    found += [p.get("from", ".") for p in poetry.get("packages") or [] if isinstance(p, dict)]
    pdm = ((tool.get("pdm") or {}).get("build") or {}) if isinstance(tool.get("pdm"), dict) else {}
    if isinstance(pdm.get("package-dir"), str):
        found.append(pdm["package-dir"])
    backend = ((tool.get("uv") or {}).get("build-backend") or {}) if isinstance(tool.get("uv"), dict) else {}
    if isinstance(backend.get("module-root"), str):
        found.append(backend["module-root"])
    return found


def _strings(value) -> list[str]:
    """The strings of a TOML value: itself, a list's, or those of a table's values."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)]
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _tables(value) -> list[dict]:
    return [t for t in (value if isinstance(value, list) else [value]) if isinstance(t, dict)]


def _origins(data: dict) -> set:
    project = data.get("project") if isinstance(data.get("project"), dict) else {}
    tool = data.get("tool") if isinstance(data.get("tool"), dict) else {}
    uv = tool.get("uv") if isinstance(tool.get("uv"), dict) else {}
    poetry = tool.get("poetry") if isinstance(tool.get("poetry"), dict) else {}
    found = {requirement(s) for s in [*_strings(project.get("dependencies")),
                                      *_strings(project.get("optional-dependencies")),
                                      *_strings(data.get("dependency-groups"))]}
    found |= {origin(url) for key in ("index-url", "extra-index-url", "find-links") for url in _strings(uv.get(key))}
    found |= {origin(t.get("url")) for t in [*_tables(uv.get("index")), *_tables(poetry.get("source"))]}
    groups = [g.get("dependencies") for g in (poetry["group"].values() if isinstance(poetry.get("group"), dict)
                                              else ()) if isinstance(g, dict)]
    found |= {origin(t.get("git") or t.get("url")) for tables in (uv.get("sources"), poetry.get("dependencies"),
                                                                  poetry.get("dev-dependencies"), *groups)
              if isinstance(tables, dict) for value in tables.values() for t in _tables(value)}
    return found - {None}


def run(context):
    inventory, roots, registries = context.inventory, {}, {}
    for rel in inventory.files:
        name = PurePosixPath(rel).name
        if name not in ("pyproject.toml", "setup.cfg", "setup.py"):
            continue
        root = PurePosixPath(rel).parent.as_posix() if "/" in rel else "."
        try:
            text = inventory.text(rel)
            if name == "pyproject.toml":
                data = tomllib.loads(text)
                found, origins = _pyproject(data), _origins(data)
            elif name == "setup.cfg":
                parser = configparser.ConfigParser(interpolation=None)
                parser.read_string(text)
                value = parser.get("options", "package_dir", fallback="")
                found = [line.split("=", 1)[1] for line in value.splitlines() if line.strip().startswith("=")]
                extras = parser.items("options.extras_require") if parser.has_section("options.extras_require") else []
                origins = {requirement(line) for requires in [parser.get("options", "install_requires", fallback=""),
                                                              *(v for _key, v in extras)]
                           for line in requires.splitlines()} - {None}
            else:
                origins = set()
                found = SETUP_PY.findall(text)
        except (ValueError, configparser.Error):
            continue  # an unreadable manifest is the module graph's gap
        roots.setdefault(root, set()).update(_join(root, f) for f in found)
        registries.setdefault(root, set()).update(origins)
    units = [{"root": root, "kind": "python-project", **({"source_roots": sorted(found)} if found else {}),
              **({"registries": sorted(registries[root])} if registries[root] else {})}
             for root, found in sorted(roots.items()) if found or registries[root]]
    return {"facts": {"units": units}} if units else None
