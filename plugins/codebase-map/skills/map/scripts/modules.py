"""Modules of a snapshot: build units read from manifests, modules declared by
the project, modules proposed by a model. All verified against the snapshot.

Three provenances, one record:

- `build`: what the build system declares. Workspaces, packages, crates,
  Maven and Gradle modules, Go modules, .NET projects, Composer, Gems,
  pubspec, Swift, Mix, Deno, Nx, Lerna, CMake, Cabal and Stack, sbt,
  Terraform, Zig, Julia and dune. Read programmatically, no heuristics,
  status `confirmed`.
- `declared`: `codebase-modules.json` at the project root, written by the
  project: name, responsibility and members (`path::Symbol`, files,
  directories). `confirmed` when every member resolves.
- `proposed`: the proposals ledger beside the manifest, written from a model's
  answer. Every member is verified; the module stays `inferred`.

Edges: declared dependencies between build units, resolved imports and calls
between members. Markdown is never interpreted here: a model reads it and
proposes. Deterministic for the same snapshot, ledger and declared file; no
model or network call.
"""
from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import tomllib
import xml.etree.ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import confinement  # noqa: E402
import snapshot  # noqa: E402
from snapshot_store import logical_digest, open_snapshot  # noqa: E402
from tree_scope import DEPENDENCY_DIRS, Perimeter  # noqa: E402

SCHEMA = "daodan/module-graph/v1"
DECLARED_SCHEMA = "daodan/declared-modules/v1"
LEDGER_SCHEMA = "daodan/module-proposals/v1"
GRAPH_FILE = "modules.json"
VIEW_FILE = "modules.md"
LEDGER_FILE = "proposals.json"
DECLARED_FILE = "codebase-modules.json"
PROVENANCES = ("build", "declared", "proposed")
STATUSES = ("confirmed", "inferred", "incomplete")
MODULE_KINDS = ("component", "feature")
LOCATIONS = ("internal", "external")
MAX_MEMBERS = 500
MAX_MODULES = 500
MAX_EDGE_EVIDENCE = 20
MAX_BRIEF_SYMBOLS = 2000


# ---------------------------------------------------------------- helpers

def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).casefold()).strip("-")


def _posix(value: str) -> str:
    return str(value).replace("\\", "/").strip().strip("/")


def _dirname(rel: str) -> str:
    return rel.rsplit("/", 1)[0] if "/" in rel else "."


def _inside(path: str, prefix: str) -> bool:
    return prefix == "." or path == prefix or path.startswith(prefix + "/")


def _join(base: str, relative: str) -> str:
    joined = os.path.normpath(os.path.join("" if base == "." else base, relative)).replace(os.sep, "/")
    return "." if joined in ("", ".") else joined.strip("/")


def _line_of(text: str, needle: str) -> int | None:
    for number, line in enumerate(text.split("\n"), 1):
        if needle and needle in line:
            return number
    return None


def _scalar(value: str):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [_scalar(item) for item in value[1:-1].split(",") if item.strip()]
    return value.strip("'\"")


def _yaml(text: str) -> dict:
    """The YAML subset workspace files use: nested maps, lists of scalars or of one-line maps."""
    root: dict = {}
    stack: list[tuple[int, object]] = [(-1, root)]
    for raw in text.split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = re.sub(r"\s+#.*$", "", raw.strip())
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()
        holder = stack[-1][1]
        if isinstance(holder, tuple):
            parent, key = holder
            holder = [] if line.startswith("- ") else {}
            parent[key] = holder
            stack[-1] = (stack[-1][0], holder)
        if line.startswith("- "):
            if not isinstance(holder, list):
                continue
            item = line[2:].strip()
            match = re.match(r"^([\w.\-/]+):\s*(.*)$", item)
            if match:
                entry = {match.group(1): _scalar(match.group(2))} if match.group(2) else {}
                holder.append(entry)
                stack.append((indent + 1, entry))
                if not match.group(2):
                    stack.append((indent + 1, (entry, match.group(1))))
            else:
                holder.append(_scalar(item))
            continue
        match = re.match(r"^([^:]+):\s*(.*)$", line)
        if not match or not isinstance(holder, dict):
            continue
        key, value = match.group(1).strip().strip("'\""), match.group(2).strip()
        if value:
            holder[key] = _scalar(value)
        else:
            stack.append((indent, (holder, key)))
    return root


def _names(values) -> list[str]:
    if isinstance(values, dict):
        return sorted(k for k in values if isinstance(k, str))
    if isinstance(values, list):
        found = []
        for item in values:
            if isinstance(item, str):
                match = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._@/-]*)", item)
                if match:
                    found.append(match.group(1))
        return sorted(set(found))
    return []


class StaleSource(ValueError):
    """A file on disk no longer matches the snapshot; nothing derived from it is evidence."""


class _Inventory:
    """Snapshot files and directories, with source text verified against the snapshot hash."""

    def __init__(self, store):
        self.store = store
        self.root = Path(store["root"])
        self.target = store.get("target") or "."
        self.headers = dict(store.iter_file_headers_only())
        self.files = sorted(self.headers)
        self.directories: set[str] = {"."}
        for rel in self.files:
            parts = rel.split("/")
            for depth in range(1, len(parts)):
                self.directories.add("/".join(parts[:depth]))
        self._text: dict[str, str] = {}
        self._perimeter = None

    def exists(self, path: str) -> bool:
        return path in self.headers or path in self.directories

    def hash(self, rel: str) -> str | None:
        header = self.headers.get(rel)
        return header.get("raw_hash") if header else None

    def text(self, rel: str) -> str:
        if rel not in self._text:
            path = self.root / rel
            confinement.reject_link_chain(path)
            try:
                data = path.read_bytes()
            except OSError as error:
                raise ValueError(f"cannot read {rel}; refresh the manifest") from error
            if hashlib.sha256(data).hexdigest() != self.hash(rel):
                raise StaleSource(f"source changed since the snapshot: {rel}; refresh the manifest")
            self._text[rel] = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
        return self._text[rel]

    def files_under(self, paths: list[str], excluded: list[str] = ()) -> list[str]:
        return [rel for rel in self.files if any(_inside(rel, p) for p in paths)
                and not any(_inside(rel, p) for p in excluded)]

    def glob_directories(self, base: str, pattern: str) -> list[str]:
        """Directories matching a workspace pattern: `*` stays inside one segment, `**` crosses segments."""
        relative = _join(base, pattern.rstrip("/"))
        regex = "".join("[^/]*" if part == "*" else ".*" if part == "**" else "[^/]" if part == "?" else re.escape(part)
                        for part in re.split(r"(\*\*|\*|\?)", relative) if part)
        return sorted(d for d in self.directories if d != "." and re.fullmatch(regex, d))

    def absence(self, rel: str) -> str:
        """Why a cited path is not in the snapshot."""
        rel = _posix(rel)
        parts = PurePosixPath(rel).parts
        if not parts or ".." in parts or PurePosixPath(rel).is_absolute() or ":" in parts[0]:
            return "not a project-relative path"
        if snapshot.is_forbidden(parts[-1], self.root / rel):
            return "credential or secret file, never inventoried"
        if any(part.startswith(".") for part in parts[:-1]):
            return "inside a dot directory, outside the map perimeter"
        if any(part in DEPENDENCY_DIRS for part in parts):
            return "inside a dependency or build directory, outside the map perimeter"
        path = self.root / rel
        try:
            exists, is_dir = path.exists(), path.is_dir()
        except OSError:
            exists, is_dir = False, False
        if not exists:
            return "absent from the tree"
        if is_dir and parts[-1].startswith("."):
            return "inside a dot directory, outside the map perimeter"
        if self._perimeter is None:
            target = (self.root / self.target).resolve()
            self._perimeter = Perimeter(target) if target.is_dir() else False
        probe = path / "probe" if is_dir else path
        if self._perimeter and self._perimeter.git_ignore == "applied" and not self._perimeter.covers(probe):
            return "ignored by Git, outside the map perimeter"
        if is_dir:
            return "directory holds no inventoried file"
        suffix = path.suffix.lower()
        if (suffix not in snapshot.SUPPORTED_EXTENSIONS and suffix not in snapshot.DOC_EXTENSIONS
                and suffix not in snapshot.PRESENTATION_EXTENSIONS and path.name not in snapshot.MANIFEST_FILES):
            return "file type the map does not inventory"
        return "present on disk but not in this snapshot; refresh the snapshot"


# ---------------------------------------------------------- build units

def _unit(rel: str, kind: str, name: str | None = None, **fields) -> dict:
    """One build unit as a manifest declares it; `directory` is the unit root."""
    record = {"path": rel, "directory": _dirname(rel), "kind": kind, "name": name, "aliases": [],
              "description": None, "dependencies": [], "path_dependencies": [], "members": [],
              "line": None}
    record.update(fields)
    return record


def _described(record: dict, table) -> None:
    value = table.get("description") if isinstance(table, dict) else None
    if isinstance(value, str) and value.strip():
        record["description"] = value.strip()[:200]


def _package_json(inv, rel, text):
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("not an object")
    unit = _unit(rel, "npm-package", data.get("name") if isinstance(data.get("name"), str) else None)
    _described(unit, data)
    deps = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps.update(_names(data.get(key)))
    unit["dependencies"] = sorted(deps)
    workspaces = data.get("workspaces")
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages")
    if isinstance(workspaces, list):
        unit["kind"] = "npm-workspace"
        unit["members"] = [w for w in workspaces if isinstance(w, str)]
    return [unit]


def _pnpm_workspace(inv, rel, text):
    data = _yaml(text)
    packages = [p for p in (data.get("packages") or []) if isinstance(p, str) and not p.startswith("!")]
    return [_unit(rel, "pnpm-workspace", None, members=packages)]


def _lerna(inv, rel, text):
    data = json.loads(text)
    packages = data.get("packages") if isinstance(data, dict) else None
    return [_unit(rel, "lerna-workspace", None, members=[p for p in packages or [] if isinstance(p, str)])]


def _deno(inv, rel, text):
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("not an object")
    unit = _unit(rel, "deno-package", data.get("name") if isinstance(data.get("name"), str) else None)
    workspace = data.get("workspace")
    if isinstance(workspace, dict):
        workspace = workspace.get("members")
    if isinstance(workspace, list):
        unit["kind"] = "deno-workspace"
        unit["members"] = [w for w in workspace if isinstance(w, str)]
    return [unit]


def _nx_project(inv, rel, text):
    data = json.loads(text)
    if not isinstance(data, dict) or not isinstance(data.get("name"), str):
        return []
    deps = data.get("implicitDependencies")
    return [_unit(rel, "nx-project", data["name"], dependencies=_names(deps) if isinstance(deps, list) else [])]


def _pyproject(inv, rel, text):
    data = tomllib.loads(text)
    project = data.get("project") if isinstance(data.get("project"), dict) else {}
    tool = data.get("tool") if isinstance(data.get("tool"), dict) else {}
    poetry = tool.get("poetry") if isinstance(tool.get("poetry"), dict) else {}
    uv = tool.get("uv") if isinstance(tool.get("uv"), dict) else {}
    name = project.get("name") or poetry.get("name")
    unit = _unit(rel, "python-package", name if isinstance(name, str) else None)
    _described(unit, project)
    if unit["description"] is None:
        _described(unit, poetry)
    deps = set(_names(project.get("dependencies")))
    for group in (project.get("optional-dependencies") or {}).values() if isinstance(project.get("optional-dependencies"), dict) else []:
        deps.update(_names(group))
    deps.update(d for d in _names(poetry.get("dependencies")) if d != "python")
    unit["dependencies"] = sorted(deps)
    workspace = uv.get("workspace") if isinstance(uv.get("workspace"), dict) else {}
    if isinstance(workspace.get("members"), list):
        unit["kind"] = "uv-workspace"
        unit["members"] = [m for m in workspace["members"] if isinstance(m, str)]
    for dep, spec in (uv.get("sources") or {}).items() if isinstance(uv.get("sources"), dict) else []:
        if isinstance(spec, dict) and isinstance(spec.get("path"), str):
            unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], spec["path"])})
    for dep, spec in poetry.get("dependencies", {}).items() if isinstance(poetry.get("dependencies"), dict) else []:
        if isinstance(spec, dict) and isinstance(spec.get("path"), str):
            unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], spec["path"])})
    return [unit]


def _setup_cfg(inv, rel, text):
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(text)
    name = parser.get("metadata", "name", fallback=None)
    return [_unit(rel, "python-package", name.strip() if name else None)]


def _setup_py(inv, rel, text):
    match = re.search(r"""\bname\s*=\s*['"]([^'"]+)['"]""", text)
    return [_unit(rel, "python-package", match.group(1) if match else None)]


def _cargo(inv, rel, text):
    data = tomllib.loads(text)
    package = data.get("package") if isinstance(data.get("package"), dict) else {}
    unit = _unit(rel, "cargo-crate", package.get("name") if isinstance(package.get("name"), str) else None)
    _described(unit, package)
    deps = set()
    for key in ("dependencies", "dev-dependencies", "build-dependencies"):
        table = data.get(key)
        if isinstance(table, dict):
            for dep, spec in table.items():
                deps.add(dep)
                if isinstance(spec, dict) and isinstance(spec.get("path"), str):
                    unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], spec["path"])})
    unit["dependencies"] = sorted(deps)
    workspace = data.get("workspace") if isinstance(data.get("workspace"), dict) else {}
    if isinstance(workspace.get("members"), list):
        unit["kind"] = "cargo-workspace"
        unit["members"] = [m for m in workspace["members"] if isinstance(m, str)]
    return [unit]


def _go_mod(inv, rel, text):
    match = re.search(r"^module\s+(\S+)", text, re.M)
    unit = _unit(rel, "go-module", match.group(1).strip('"') if match else None)
    deps = set(re.findall(r"^\s*([A-Za-z0-9][\w./-]*)\s+v[\w.+-]+", text, re.M))
    unit["dependencies"] = sorted(deps)
    for dep, target in re.findall(r"^\s*(?:replace\s+)?(\S+)(?:\s+\S+)?\s+=>\s+(\.{1,2}/\S+|/\S+)", text, re.M):
        unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], target)})
    return [unit]


def _go_work(inv, rel, text):
    members = re.findall(r"^\s*(?:use\s+)?(\.{1,2}/[^\s)]+|\./?)\s*$", text, re.M)
    return [_unit(rel, "go-workspace", None, members=[m for m in members if m != "./"])]


def _pom(inv, rel, text):
    root = ET.fromstring(text)
    ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""

    def child(node, name):
        found = node.find(ns + name)
        return found.text.strip() if found is not None and found.text else None

    artifact = child(root, "artifactId")
    group = child(root, "groupId")
    parent = root.find(ns + "parent")
    if group is None and parent is not None:
        group = child(parent, "groupId")
    unit = _unit(rel, "maven-module", artifact)
    _described(unit, {"description": child(root, "description")})
    if group and artifact:
        unit["aliases"] = [f"{group}:{artifact}"]
    deps = set()
    for dep in root.iter(ns + "dependency"):
        name = child(dep, "artifactId")
        if name:
            deps.add(name)
    unit["dependencies"] = sorted(deps)
    members = [m.text.strip() for m in root.iter(ns + "module") if m.text and m.text.strip()]
    if members:
        unit["kind"] = "maven-aggregator"
        unit["members"] = members
    return [unit]


def _gradle_settings(inv, rel, text):
    name = re.search(r"""rootProject\.name\s*=\s*['"]([^'"]+)['"]""", text)
    unit = _unit(rel, "gradle-build", name.group(1) if name else None)
    members = []
    for block in re.findall(r"\binclude\s*\(?([^)\n]+)\)?", text):
        for project in re.findall(r"""['"]:?([^'"]+)['"]""", block):
            members.append(project.replace(":", "/"))
    for build in re.findall(r"""includeBuild\s*\(?\s*['"]([^'"]+)['"]""", text):
        members.append(build)
    unit["members"] = members
    return [unit]


def _gradle_build(inv, rel, text):
    unit = _unit(rel, "gradle-project", None)
    for project in re.findall(r"""project\s*\(\s*(?:path\s*[:=]\s*)?['"]:?([^'"]+)['"]""", text):
        unit["path_dependencies"].append({"name": project, "path": project.replace(":", "/")})
    return [unit]


def _sln(inv, rel, text):
    units = []
    for name, path in re.findall(r"""Project\("\{[^}]+\}"\)\s*=\s*"([^"]+)",\s*"([^"]+)\""""
                                 , text):
        posix = _posix(path)
        if posix.lower().endswith((".csproj", ".fsproj", ".vbproj")):
            units.append(_unit(_join(_dirname(rel), posix), "dotnet-project", name,
                               directory=_dirname(_join(_dirname(rel), posix)), declared_by=rel))
    return [_unit(rel, "dotnet-solution", PurePosixPath(rel).stem, members=[u["directory"] for u in units])] + units


def _msbuild_project(inv, rel, text):
    root = ET.fromstring(text)
    name = None
    for node in root.iter():
        if node.tag.endswith("AssemblyName") and node.text and node.text.strip():
            name = node.text.strip()
            break
    unit = _unit(rel, "dotnet-project", name or PurePosixPath(rel).stem)
    for node in root.iter():
        if node.tag.endswith("ProjectReference") and node.get("Include"):
            target = _posix(node.get("Include"))
            unit["path_dependencies"].append({"name": PurePosixPath(target).stem,
                                              "path": _dirname(_join(unit["directory"], target))})
        elif node.tag.endswith("PackageReference") and node.get("Include"):
            unit["dependencies"].append(node.get("Include"))
    unit["dependencies"].sort()
    return [unit]


def _composer(inv, rel, text):
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("not an object")
    unit = _unit(rel, "composer-package", data.get("name") if isinstance(data.get("name"), str) else None)
    _described(unit, data)
    unit["dependencies"] = sorted(set(_names(data.get("require"))) | set(_names(data.get("require-dev"))))
    for repo in data.get("repositories", []) if isinstance(data.get("repositories"), list) else []:
        if isinstance(repo, dict) and repo.get("type") == "path" and isinstance(repo.get("url"), str):
            unit["members"].append(repo["url"])
    return [unit]


def _gemspec(inv, rel, text):
    match = re.search(r"""\.name\s*=\s*['"]([^'"]+)['"]""", text)
    unit = _unit(rel, "ruby-gem", match.group(1) if match else PurePosixPath(rel).stem)
    unit["dependencies"] = sorted(set(re.findall(r"""add(?:_runtime|_development)?_dependency\s*\(?\s*['"]([^'"]+)['"]""", text)))
    return [unit]


def _gemfile(inv, rel, text):
    unit = _unit(rel, "ruby-bundle", None)
    for gem, path in re.findall(r"""gem\s+['"]([^'"]+)['"][^\n]*?path:\s*['"]([^'"]+)['"]""", text):
        unit["path_dependencies"].append({"name": gem, "path": _join(unit["directory"], path)})
    unit["dependencies"] = sorted(set(re.findall(r"""^\s*gem\s+['"]([^'"]+)['"]""", text, re.M)))
    return [unit]


def _pubspec(inv, rel, text):
    data = _yaml(text)
    unit = _unit(rel, "dart-package", data.get("name") if isinstance(data.get("name"), str) else None)
    _described(unit, data)
    deps = set()
    for key in ("dependencies", "dev_dependencies"):
        table = data.get(key)
        if isinstance(table, dict):
            for dep, spec in table.items():
                deps.add(dep)
                if isinstance(spec, dict) and isinstance(spec.get("path"), str):
                    unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], spec["path"])})
    unit["dependencies"] = sorted(deps)
    workspace = data.get("workspace")
    if isinstance(workspace, list):
        unit["kind"] = "dart-workspace"
        unit["members"] = [w for w in workspace if isinstance(w, str)]
    return [unit]


def _melos(inv, rel, text):
    data = _yaml(text)
    packages = [p for p in (data.get("packages") or []) if isinstance(p, str)]
    return [_unit(rel, "melos-workspace", data.get("name") if isinstance(data.get("name"), str) else None,
                  members=packages)]


def _package_swift(inv, rel, text):
    name = re.search(r"""Package\s*\(\s*name\s*:\s*"([^"]+)\"""", text)
    unit = _unit(rel, "swift-package", name.group(1) if name else None)
    for path in re.findall(r"""\.package\s*\(\s*(?:name\s*:\s*"[^"]+"\s*,\s*)?path\s*:\s*"([^"]+)\"""", text):
        unit["path_dependencies"].append({"name": PurePosixPath(path).name, "path": _join(unit["directory"], path)})
    unit["dependencies"] = sorted(set(re.findall(r"""\.package\s*\([^)]*?url\s*:\s*"[^"]*/([^/"]+?)(?:\.git)?\"""", text)))
    return [unit]


def _mix(inv, rel, text):
    app = re.search(r"\bapp:\s*:(\w+)", text)
    unit = _unit(rel, "mix-project", app.group(1) if app else None)
    apps_path = re.search(r"""apps_path:\s*"([^"]+)\"""", text)
    if apps_path:
        unit["kind"] = "mix-umbrella"
        unit["members"] = [apps_path.group(1).rstrip("/") + "/*"]
    for dep, path in re.findall(r"""\{\s*:(\w+)\s*,[^}]*?path:\s*"([^"]+)\"""", text):
        unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], path)})
    unit["dependencies"] = sorted(set(re.findall(r"""\{\s*:(\w+)\s*,\s*"[~>=<\d]""", text)))
    return [unit]


def _cmake(inv, rel, text):
    name = re.search(r"\bproject\s*\(\s*([A-Za-z0-9_.-]+)", text)
    unit = _unit(rel, "cmake-project", name.group(1) if name else None)
    unit["members"] = re.findall(r"\badd_subdirectory\s*\(\s*([^\s)]+)", text)
    return [unit]


def _cabal(inv, rel, text):
    name = re.search(r"^name:\s*(\S+)", text, re.M | re.I)
    unit = _unit(rel, "cabal-package", name.group(1) if name else PurePosixPath(rel).stem)
    depends = " ".join(re.findall(r"^\s*build-depends:\s*([^\n]+)", text, re.M | re.I))
    unit["dependencies"] = sorted(set(re.findall(r"(?:^|,)\s*([A-Za-z][\w-]*)", depends)))
    return [unit]


def _stack(inv, rel, text):
    data = _yaml(text)
    members = []
    for item in data.get("packages") or []:
        if isinstance(item, str):
            members.append(item)
        elif isinstance(item, dict) and isinstance(item.get("location"), str):
            members.append(item["location"])
    return [_unit(rel, "stack-workspace", None, members=members)]


def _sbt(inv, rel, text):
    units = []
    for val, path in re.findall(r"""lazy\s+val\s+(\w+)\s*=\s*(?:\(\s*)?project(?:\s+in\s+file|\.in\s*\(\s*file)\s*\(\s*"([^"]+)"\s*\)""", text):
        unit = _unit(rel, "sbt-project", val, directory=_join(_dirname(rel), path))
        unit["path_dependencies"] = [{"name": dep, "path": None} for dep in re.findall(
            rf"""lazy\s+val\s+{val}\b[^\n]*?dependsOn\s*\(([^)]*)\)""", text) for dep in re.findall(r"\w+", dep)]
        units.append(unit)
    if not units:
        name = re.search(r"""\bname\s*:=\s*"([^"]+)\"""", text)
        units.append(_unit(rel, "sbt-project", name.group(1) if name else None))
    return units


def _terraform(inv, rel, text):
    """A root that calls local modules: each `module "x" { source = "./y" }` registers y as a member."""
    unit = _unit(rel, "terraform-root", None)
    for name, source in re.findall(r"""module\s+"([^"]+)"\s*\{[^}]*?source\s*=\s*"(\.{1,2}/[^"]+)\"""", text, re.S):
        unit["path_dependencies"].append({"name": name, "path": _join(unit["directory"], source)})
        unit["members"].append(source)
    return [unit] if unit["members"] else []


def _zig(inv, rel, text):
    name = re.search(r"""\.name\s*=\s*\.?"?([\w.-]+)"?""", text)
    unit = _unit(rel, "zig-package", name.group(1) if name else None)
    for dep, path in re.findall(r"""\.(\w+)\s*=\s*\.\{[^}]*?\.path\s*=\s*"([^"]+)\"""", text, re.S):
        unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], path)})
    return [unit]


def _julia(inv, rel, text):
    data = tomllib.loads(text)
    unit = _unit(rel, "julia-package", data.get("name") if isinstance(data.get("name"), str) else None)
    unit["dependencies"] = _names(data.get("deps"))
    return [unit]


def _dune(inv, rel, text):
    name = re.search(r"\(name\s+([^\s)]+)\)", text)
    return [_unit(rel, "dune-project", name.group(1) if name else None)]


def _daodan_plugin(inv, rel, text):
    data = tomllib.loads(text)
    if data.get("schema") != "daodan/v1":
        return []
    unit = _unit(rel, "daodan-plugin", data.get("name") if isinstance(data.get("name"), str) else None)
    _described(unit, data)
    dependencies = data.get("dependencies") if isinstance(data.get("dependencies"), dict) else {}
    unit["dependencies"] = sorted(set(_names(dependencies.get("required"))) | set(_names(dependencies.get("optional"))))
    return [unit]


READERS: dict[str, tuple[str, object]] = {
    "package.json": ("npm", _package_json), "pnpm-workspace.yaml": ("pnpm", _pnpm_workspace),
    "lerna.json": ("lerna", _lerna), "deno.json": ("deno", _deno), "deno.jsonc": ("deno", _deno),
    "project.json": ("nx", _nx_project), "pyproject.toml": ("python", _pyproject),
    "setup.cfg": ("python", _setup_cfg), "setup.py": ("python", _setup_py), "Cargo.toml": ("cargo", _cargo),
    "go.mod": ("go", _go_mod), "go.work": ("go", _go_work), "pom.xml": ("maven", _pom),
    "settings.gradle": ("gradle", _gradle_settings), "settings.gradle.kts": ("gradle", _gradle_settings),
    "build.gradle": ("gradle", _gradle_build), "build.gradle.kts": ("gradle", _gradle_build),
    "composer.json": ("composer", _composer), "Gemfile": ("bundler", _gemfile),
    "pubspec.yaml": ("pub", _pubspec), "melos.yaml": ("melos", _melos), "Package.swift": ("swiftpm", _package_swift),
    "mix.exs": ("mix", _mix), "CMakeLists.txt": ("cmake", _cmake), "stack.yaml": ("stack", _stack),
    "build.sbt": ("sbt", _sbt), "build.zig.zon": ("zig", _zig), "Project.toml": ("julia", _julia),
    "dune-project": ("dune", _dune), "plugin.toml": ("daodan", _daodan_plugin),
}
SUFFIX_READERS = {".sln": ("dotnet", _sln), ".csproj": ("dotnet", _msbuild_project),
                  ".fsproj": ("dotnet", _msbuild_project), ".vbproj": ("dotnet", _msbuild_project),
                  ".gemspec": ("rubygems", _gemspec), ".cabal": ("cabal", _cabal), ".tf": ("terraform", _terraform)}
ECOSYSTEMS = sorted({eco for eco, _ in [*READERS.values(), *SUFFIX_READERS.values()]})


def _read_units(inventory: _Inventory) -> tuple[list[dict], list[dict]]:
    units, gaps = [], []
    for rel in inventory.files:
        name = PurePosixPath(rel).name
        reader = READERS.get(name) or SUFFIX_READERS.get(PurePosixPath(rel).suffix.lower())
        if reader is None or (name == "project.json" and "node_modules" in rel):
            continue
        ecosystem, read = reader
        text = inventory.text(rel)
        try:
            found = read(inventory, rel, text)
        except (ValueError, TypeError, KeyError, configparser.Error, tomllib.TOMLDecodeError, ET.ParseError) as error:
            gaps.append({"kind": "manifest_unreadable", "path": rel, "detail": f"{type(error).__name__}: {error}"})
            continue
        for unit in found:
            if unit["directory"] != "." and unit["directory"] not in inventory.directories:
                gaps.append({"kind": "directory_missing", "path": rel,
                             "detail": f"{unit['name'] or unit['kind']} at {unit['directory']}: {inventory.absence(unit['directory'])}"})
                continue
            unit["ecosystem"] = ecosystem
            unit["line"] = _line_of(text, unit["name"]) if unit["name"] else None
            units.append(unit)
    return units, gaps


# ------------------------------------------------------------- modules

def validate_module(record: object) -> dict:
    if not isinstance(record, dict):
        raise ValueError("a module must be an object")
    unknown = set(record) - {"name", "kind", "location", "responsibility", "members", "evidence"}
    if unknown:
        raise ValueError("unknown module fields: " + ", ".join(sorted(unknown)))
    name = record.get("name")
    if not isinstance(name, str) or not name.strip() or len(name) > 100:
        raise ValueError("module name must be a short text")
    kind = record.get("kind")
    if kind not in MODULE_KINDS:
        raise ValueError(f"module {name}: kind is required, one of " + ", ".join(MODULE_KINDS))
    location = record.get("location", LOCATIONS[0])
    if location not in LOCATIONS:
        raise ValueError(f"module {name}: location must be one of " + ", ".join(LOCATIONS))
    if kind == "feature" and location == "external":
        raise ValueError(f"module {name}: a feature is a highlight over internal members, it has no external location")
    responsibility = record.get("responsibility", "")
    if not isinstance(responsibility, str) or len(responsibility) > 1000:
        raise ValueError(f"module {name}: responsibility must be text of at most 1000 characters")
    members = record.get("members") or []
    if location == "external":
        if members:
            raise ValueError(f"module {name}: an external module has no members; cite the files that bind to it as evidence")
    elif (not isinstance(members, list) or not members or len(members) > MAX_MEMBERS
            or any(not isinstance(m, str) or not m.strip() or len(m) > 1000 for m in members)):
        raise ValueError(f"module {name}: members must be 1 to {MAX_MEMBERS} entity ids or paths")
    evidence = record.get("evidence", [])
    if not isinstance(evidence, list) or any(not isinstance(e, str) or not e.strip() or len(e) > 1000 for e in evidence):
        raise ValueError(f"module {name}: evidence must be a list of path or path#heading references")
    return {"name": name.strip(), "kind": kind, "location": location, "responsibility": responsibility.strip(),
            "members": list(dict.fromkeys(m.strip() for m in members)),
            "evidence": list(dict.fromkeys(e.strip() for e in evidence))}


def validate_modules(value: object, *, source: str) -> list[dict]:
    if isinstance(value, dict) and "modules" in value:
        if value.get("schema") not in (None, DECLARED_SCHEMA, LEDGER_SCHEMA):
            raise ValueError(f"{source}: unsupported schema")
        value = value["modules"]
    if not isinstance(value, list) or len(value) > MAX_MODULES:
        raise ValueError(f"{source}: modules must be a list of at most {MAX_MODULES} records")
    records = [validate_module(item) for item in value]
    if len({slug(r["name"]) for r in records}) != len(records):
        raise ValueError(f"{source}: module names must be distinct")
    return records


def ledger_name(manifest: Path) -> Path:
    return Path(manifest).with_name(LEDGER_FILE)


def load_ledger(manifest: Path) -> list[dict]:
    path = ledger_name(manifest)
    _plain(path)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"not a readable proposals ledger: {error}") from error
    if not isinstance(value, dict) or value.get("schema") != LEDGER_SCHEMA:
        raise ValueError("not a proposals ledger of this schema")
    return validate_modules(value, source=LEDGER_FILE)


def write_ledger(manifest: Path, records: list[dict], *, replace: bool = False) -> list[dict]:
    """Record proposals beside the manifest; a same-named proposal replaces the earlier one."""
    manifest = Path(manifest).resolve()
    kept = [] if replace else [r for r in load_ledger(manifest) if slug(r["name"]) not in {slug(x["name"]) for x in records}]
    proposals = sorted([*kept, *records], key=lambda r: slug(r["name"]))
    path = ledger_name(manifest)
    descriptor, name = tempfile.mkstemp(prefix=".proposals-", dir=path.parent)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(_json({"schema": LEDGER_SCHEMA, "modules": proposals}).encode("utf-8"))
    os.replace(name, path)
    return proposals


def _member(inventory: _Inventory, store, text: str) -> dict:
    """One member as the snapshot knows it: a symbol, a file, a directory, or unresolved with the reason."""
    if "::" in text:
        path, symbol = text.split("::", 1)
        path = _posix(path)
        record = {"id": f"{path}::{symbol}", "kind": "symbol", "path": path, "symbol": symbol, "resolved": False}
        if path not in inventory.headers:
            record["reason"] = inventory.absence(path)
            return record
        spec = ((store.get_file(path, semantic=False) or {}).get("symbols") or {}).get(symbol)
        if spec is None:
            record["reason"] = "symbol is not in the snapshot of this file"
            return record
        record.update(resolved=True, start_line=spec.get("start"), end_line=spec.get("end"), hash=spec.get("hash"))
        return record
    path = _posix(text)
    if path in inventory.headers:
        return {"id": path, "kind": "file", "path": path, "resolved": True}
    if path in inventory.directories:
        return {"id": path, "kind": "directory", "path": path, "resolved": True}
    return {"id": path, "kind": "file", "path": path, "resolved": False, "reason": inventory.absence(path)}


def _evidence(inventory: _Inventory, text: str) -> dict:
    path, _, anchor = text.partition("#")
    path = _posix(path)
    if path not in inventory.headers:
        return {"path": path, "line": None, "resolved": False, "reason": inventory.absence(path)}
    record = {"path": path, "line": None, "resolved": True}
    if anchor:
        for number, line in enumerate(inventory.text(path).split("\n"), 1):
            match = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
            if match and slug(re.sub(r"[`*]", "", match.group(1))) == slug(anchor):
                record["line"] = number
                break
        else:
            record.update(resolved=False, reason=f"heading #{anchor} not found in {path}")
    return record


def resolve_members(manifest: Path, texts: list[str]) -> list[dict]:
    """Members as the snapshot knows them, each resolved or with the reason it is not."""
    with open_snapshot(manifest) as store:
        inventory = _Inventory(store)
        return [_member(inventory, store, text) for text in texts]


def resolve_evidence(manifest: Path, texts: list[str]) -> list[dict]:
    """`path` or `path#heading` references, each resolved or with the reason it is not."""
    with open_snapshot(manifest) as store:
        inventory = _Inventory(store)
        return [_evidence(inventory, text) for text in texts]


def _review_paths(inventory: _Inventory, files: set[str]) -> list[str]:
    """Member files, collapsed to a directory only when every inventoried file in it is a member."""
    paths: list[str] = []
    for directory in sorted({_dirname(f) for f in files if _dirname(f) != "."}, key=lambda d: (d.count("/"), d)):
        if not any(_inside(directory, p) for p in paths) and set(inventory.files_under([directory])) <= files:
            paths.append(directory)
    paths.extend(f for f in sorted(files) if not any(_inside(f, p) for p in paths))
    return paths


def _call_edges(store, symbol_owner: dict[str, dict[str, list[str]]], file_owner: dict[str, list[str]]) -> list[dict]:
    """Resolved calls between members of different modules, from the semantic store."""
    from semantic_store import _ImpactIndex, install_edge_view, semantic_reader

    def owners(row):
        file, name = row[1], row[2]
        found = set(file_owner.get(file, []))
        for module_id, names in symbol_owner.get(file, {}).items():
            if any(name == n or name.startswith(n + ".") for n in names):
                found.add(module_id)
        return sorted(found)

    calls = []
    with semantic_reader(store) as db:
        install_edge_view(db, store)
        index = _ImpactIndex(db)
        for file, line, target in db.execute(
                "SELECT file,l0,target_id FROM effective_references WHERE kind='call' AND resolution='resolved' "
                "ORDER BY file,l0,c0,l1,c1,id"):
            caller = index.enclosing(file, line)
            callee = index.symbol_for_declaration(target) if target else None
            if caller is None or callee is None:
                continue
            for source in owners(caller):
                for destination in owners(callee):
                    if source != destination:
                        calls.append({"source": source, "target": destination, "path": file, "line": line,
                                      "caller": caller[2], "callee": f"{callee[1]}::{callee[2]}"})
    return calls


def derive(store, *, ledger: list[dict] | None = None) -> dict:
    """Derive the module graph of a snapshot; deterministic for the same inputs."""
    inventory = _Inventory(store)
    gaps: list[dict] = []
    modules: list[dict] = []

    # 1. Build units, merged per directory, with workspace members resolved to directories.
    units, unit_gaps = _read_units(inventory)
    gaps.extend(unit_gaps)
    by_directory: dict[str, dict] = {}
    for unit in sorted(units, key=lambda u: (u["directory"].count("/"), u["directory"], u["path"])):
        merged = by_directory.get(unit["directory"])
        if merged is None:
            by_directory[unit["directory"]] = merged = {
                "directory": unit["directory"], "name": unit["name"], "aliases": list(unit["aliases"]),
                "kinds": [unit["kind"]], "ecosystems": [unit["ecosystem"]], "description": unit["description"],
                "manifests": [unit["path"]], "evidence": [{"path": unit["path"], "line": unit["line"]}],
                "dependencies": set(unit["dependencies"]), "path_dependencies": list(unit["path_dependencies"]),
                "patterns": list(unit["members"]), "registered_by": []}
            continue
        if merged["name"] is None:
            merged["name"] = unit["name"]
        elif unit["name"] and unit["name"] != merged["name"] and unit["name"] not in merged["aliases"]:
            merged["aliases"].append(unit["name"])
        merged["aliases"].extend(a for a in unit["aliases"] if a not in merged["aliases"])
        merged["kinds"].append(unit["kind"])
        merged["ecosystems"].append(unit["ecosystem"])
        merged["description"] = merged["description"] or unit["description"]
        merged["manifests"].append(unit["path"])
        merged["evidence"].append({"path": unit["path"], "line": unit["line"]})
        merged["dependencies"].update(unit["dependencies"])
        merged["path_dependencies"].extend(unit["path_dependencies"])
        merged["patterns"].extend(unit["members"])
    for directory, merged in list(by_directory.items()):
        for pattern in merged["patterns"]:
            found = inventory.glob_directories(directory, pattern)
            if not found and not any(ch in pattern for ch in "*?["):
                gaps.append({"kind": "member_missing", "path": merged["manifests"][0],
                             "detail": f"workspace member {pattern}: {inventory.absence(_join(directory, pattern))}"})
            for member in found:
                if member not in by_directory:
                    by_directory[member] = {
                        "directory": member, "name": PurePosixPath(member).name, "aliases": [], "kinds": ["workspace-member"],
                        "ecosystems": [merged["ecosystems"][0]], "description": None, "manifests": [],
                        "evidence": [], "dependencies": set(), "path_dependencies": [], "patterns": [], "registered_by": []}
                site = {"path": merged["manifests"][0], "line": _line_of(inventory.text(merged["manifests"][0]), pattern)}
                by_directory[member]["registered_by"].append((directory, site))
                by_directory[member]["evidence"].append(site)
    for merged in by_directory.values():
        name = merged["name"] or PurePosixPath(merged["directory"]).name or PurePosixPath(inventory.root).name
        basename = PurePosixPath(merged["directory"]).name
        if basename and basename != name and basename not in merged["aliases"]:
            merged["aliases"].append(basename)
        nested = sorted(d for d in by_directory if d != merged["directory"] and _inside(d, merged["directory"]))
        excluded = [d for d in nested if not any(_inside(d, other) for other in nested if other != d)]
        modules.append({
            "id": "", "name": name, "aliases": sorted(dict.fromkeys(merged["aliases"])), "provenance": "build",
            "kind": sorted(set(merged["kinds"]))[0] if len(set(merged["kinds"])) == 1 else "+".join(sorted(set(merged["kinds"]))),
            "location": "internal", "ecosystems": sorted(set(merged["ecosystems"])), "description": merged["description"],
            "responsibility": "", "members": [{"id": merged["directory"], "kind": "directory",
                                               "path": merged["directory"], "resolved": True}],
            "excluded": excluded, "manifests": sorted(merged["manifests"]),
            "registered_by": [d for d, _ in merged["registered_by"]], "registrations": merged["registered_by"],
            "evidence": merged["evidence"], "dependencies": sorted(merged["dependencies"]),
            "path_dependencies": merged["path_dependencies"], "conflicts": [], "gaps": [], "status": "confirmed",
        })

    # 2. Declared and proposed modules, every member verified.
    declared: list[dict] = []
    if DECLARED_FILE in inventory.headers:
        try:
            declared = validate_modules(json.loads(inventory.text(DECLARED_FILE)), source=DECLARED_FILE)
        except ValueError as error:
            gaps.append({"kind": "modules_unreadable", "path": DECLARED_FILE, "detail": str(error)})
    proposals = load_ledger(Path(store.path)) if ledger is None else ledger
    declared_names = {slug(r["name"]) for r in declared}
    for record in proposals:
        if slug(record["name"]) in declared_names:
            gaps.append({"kind": "proposal_superseded", "detail": f"proposal {record['name']} is now declared in {DECLARED_FILE}"})
    for provenance, records in (("declared", declared),
                                ("proposed", [r for r in proposals if slug(r["name"]) not in declared_names])):
        for record in records:
            members = [_member(inventory, store, text) for text in record["members"]]
            evidence = [_evidence(inventory, text) for text in record["evidence"]]
            module_gaps = [{"kind": "member_missing", "detail": f"{m['id']}: {m['reason']}"} for m in members if not m["resolved"]]
            module_gaps.extend({"kind": "evidence_missing", "detail": f"{e['path']}: {e['reason']}"} for e in evidence if not e["resolved"])
            if not evidence:
                module_gaps.append({"kind": "evidence_missing", "detail": "no evidence cited"})
            # What anchors the module to the snapshot: its members, or for an external one the files binding to it.
            anchors = evidence if record["location"] == "external" else members
            if not evidence or not any(a["resolved"] for a in anchors):
                status = "incomplete"
            elif provenance == "declared":
                status = "confirmed" if all(a["resolved"] for a in anchors) else "incomplete"
            else:
                status = "inferred"
            modules.append({
                "id": "", "name": record["name"], "aliases": [], "provenance": provenance, "kind": record["kind"],
                "location": record["location"], "ecosystems": [], "description": None, "responsibility": record["responsibility"],
                "members": members, "excluded": [], "manifests": [DECLARED_FILE] if provenance == "declared" else [],
                "registered_by": [], "evidence": evidence, "dependencies": [], "path_dependencies": [],
                "conflicts": [], "gaps": module_gaps, "status": status,
            })

    # 3. Identities, shared members, files and review paths.
    counts: dict[str, int] = {}
    for module in modules:
        counts[slug(module["name"])] = counts.get(slug(module["name"]), 0) + 1
    taken: set[str] = set()
    for module in modules:
        key = slug(module["name"]) or "unnamed"
        anchor = module["members"][0]["path"] if module["provenance"] == "build" else module["provenance"]
        identity = key if counts[slug(module["name"])] == 1 and key not in taken else f"{key}@{anchor}"
        while identity in taken:
            identity += "+"
        module["id"] = identity
        taken.add(identity)
    by_id = {m["id"]: m for m in modules}
    claims: dict[str, list[str]] = {}
    for module in modules:
        if module["provenance"] != "build":
            for member in module["members"]:
                if member["resolved"]:
                    claims.setdefault(member["id"], []).append(module["id"])
    for module in modules:
        for member in module["members"]:
            others = [o for o in claims.get(member["id"], []) if o != module["id"]]
            if others and member["resolved"]:
                module["conflicts"].append({"kind": "shared_member", "member": member["id"], "others": others})
        files = set()
        for member in module["members"]:
            if not member["resolved"]:
                continue
            files.update(inventory.files_under([member["path"]], module["excluded"]) if member["kind"] == "directory"
                         else [member["path"]])
        module["files"] = sorted(files)
        module["paths"] = (sorted(m["path"] for m in module["members"]) if module["provenance"] == "build"
                           else _review_paths(inventory, files))
        module["coverage"] = {"members": len(module["members"]),
                              "resolved": sum(1 for m in module["members"] if m["resolved"]),
                              "files": len(files),
                              "source_files": sum(1 for f in files if inventory.headers[f].get("language"))}
        module["members_digest"] = _digest([[m["id"], m.get("hash"), inventory.hash(m["path"])] for m in module["members"]]
                                           + [module["files"]])

    # 4. Ownership of files: the most specific directory or file member; symbols on their own.
    file_owner: dict[str, list[str]] = {}
    specific: dict[str, tuple[int, str]] = {}
    symbol_owner: dict[str, dict[str, list[str]]] = {}
    for module in modules:
        for member in module["members"]:
            if not member["resolved"]:
                continue
            if member["kind"] == "symbol":
                symbol_owner.setdefault(member["path"], {}).setdefault(module["id"], []).append(member["symbol"])
            elif member["kind"] == "file":
                file_owner.setdefault(member["path"], []).append(module["id"])
            else:
                for rel in inventory.files_under([member["path"]], module["excluded"]):
                    depth = -1 if member["path"] == "." else len(member["path"])
                    if module["provenance"] == "build":
                        if rel not in specific or depth > specific[rel][0]:
                            specific[rel] = (depth, module["id"])
                    else:
                        file_owner.setdefault(rel, []).append(module["id"])
    for rel, (_, module_id) in specific.items():
        file_owner.setdefault(rel, []).append(module_id)
    file_owner = {rel: sorted(set(ids)) for rel, ids in file_owner.items()}

    # 5. Edges.
    edges: dict[str, dict] = {}

    def edge(kind, source, target, status, evidence):
        # Build units and responsibility modules are two layers: a build unit
        # holds a module's files (`owned_by` in the query), it does not call it.
        # An external module sits outside both layers, so `uses` reaches it from either.
        if kind != "uses" and (by_id[source]["provenance"] == "build") != (by_id[target]["provenance"] == "build"):
            return
        key = f"{kind}:{source}->{target}"
        record = edges.setdefault(key, {"id": key, "kind": kind, "source": source, "target": target,
                                        "status": status, "evidence": [], "evidence_total": 0})
        record["evidence_total"] += 1
        if evidence not in record["evidence"] and len(record["evidence"]) < MAX_EDGE_EVIDENCE:
            record["evidence"].append(evidence)

    by_name: dict[str, list[str]] = {}
    build_by_dir = {m["members"][0]["path"]: m["id"] for m in modules if m["provenance"] == "build"}
    for module in modules:
        if module["provenance"] == "build":
            for name in [module["name"], *module["aliases"]]:
                by_name.setdefault(slug(name), []).append(module["id"])
    for module in modules:
        if module["provenance"] != "build":
            continue
        text = inventory.text(module["manifests"][0]) if module["manifests"] else ""
        external = []
        for item in module["path_dependencies"]:
            target = build_by_dir.get(item["path"]) if item["path"] else (by_name.get(slug(item["name"]), [None])[0])
            site = {"path": module["manifests"][0] if module["manifests"] else module["members"][0]["path"],
                    "line": _line_of(text, item["name"])}
            if target and target != module["id"]:
                edge("declares", module["id"], target, "confirmed", site)
            elif target is None:
                module["gaps"].append({"kind": "dependency_unresolved",
                                       "detail": f"{item['name']} -> {item['path'] or 'no path'}: no build unit there"})
        for name in module["dependencies"]:
            targets = [t for t in by_name.get(slug(name), []) if t != module["id"]]
            if len(targets) == 1:
                edge("declares", module["id"], targets[0], "confirmed",
                     {"path": module["manifests"][0], "line": _line_of(text, name)})
            elif not targets:
                external.append(name)
        module["external"] = external
        for parent, site in module.pop("registrations"):
            if parent in build_by_dir:
                edge("contains", build_by_dir[parent], module["id"], "confirmed", site)
    resolved_imports = snapshot.resolved_imports(store)
    for importer in sorted(resolved_imports):
        entry = None
        sources = file_owner.get(importer, [])
        if not sources:
            continue
        for specifier, targets in sorted(resolved_imports[importer].items()):
            for target in targets:
                if target == importer:
                    continue
                if entry is None:
                    entry = store.get_file(importer) or {}
                line = next((i["span"][0] for i in entry.get("semantic", {}).get("imports", [])
                             if i.get("module") == specifier and i.get("span")), None)
                named = {n.split(" as ", 1)[0].strip() for b in entry.get("import_bindings", [])
                         if b.get("from") and b.get("module") == specifier for n in b.get("names", [])}
                destinations = set(file_owner.get(target, []))
                destinations.update(mid for mid, names in symbol_owner.get(target, {}).items() if set(names) & named)
                for source in sources:
                    for destination in sorted(destinations):
                        if source != destination:
                            status = "confirmed" if by_id[source]["status"] == by_id[destination]["status"] == "confirmed" else "inferred"
                            edge("imports", source, destination, status, {"path": importer, "line": line, "imported": target})
    if symbol_owner or any(m["provenance"] != "build" for m in modules):
        try:
            for call in _call_edges(store, symbol_owner, file_owner):
                status = "confirmed" if by_id[call["source"]]["status"] == by_id[call["target"]]["status"] == "confirmed" else "inferred"
                edge("calls", call["source"], call["target"], status,
                     {"path": call["path"], "line": call["line"], "caller": call["caller"], "callee": call["callee"]})
        except ValueError as error:
            gaps.append({"kind": "calls_unavailable", "detail": str(error)})
    for module in modules:
        if module["location"] != "external":
            continue
        for site in module["evidence"]:
            if not site["resolved"]:
                continue
            for owner in modules:
                if owner["id"] != module["id"] and site["path"] in owner["files"]:
                    status = "confirmed" if owner["status"] == module["status"] == "confirmed" else "inferred"
                    edge("uses", owner["id"], module["id"], status, {"path": site["path"], "line": site["line"]})

    modules.sort(key=lambda m: m["id"])
    edge_list = [edges[k] for k in sorted(edges)]
    for module in modules:
        module.pop("path_dependencies", None)
    return {
        "schema": SCHEMA,
        "binding": {"manifest": str(Path(store.path).resolve()), "logical_digest": logical_digest(store),
                    "root": store["root"], "target": store["target"], "git": store.get("git")},
        "modules": modules,
        "edges": edge_list,
        "coverage": {"files": len(inventory.files), "ecosystems": ECOSYSTEMS,
                     "modules": {p: sum(1 for m in modules if m["provenance"] == p) for p in PROVENANCES},
                     "statuses": {s: sum(1 for m in modules if m["status"] == s) for s in STATUSES},
                     "edges": {k: sum(1 for e in edge_list if e["kind"] == k) for k in ("declares", "contains", "imports", "calls", "uses")}},
        "gaps": gaps,
        "notes": [
            "Build units come from manifests only; declared modules from codebase-modules.json; proposed modules from "
            "the ledger beside the snapshot and stay inferred until declared. No Markdown is interpreted here.",
            "Static edges prove no runtime behavior; a missing call edge proves no independence (lexical resolver).",
        ],
    }


# ----------------------------------------------------------- lifecycle

def graph_name(manifest: Path) -> Path:
    return Path(manifest).with_name(GRAPH_FILE)


def _plain(path: Path) -> None:
    confinement.reject_link_chain(path)
    if path.exists() and not path.is_file():
        raise ValueError(f"artifact must be a regular file: {path}")


def load_graph(path: Path) -> dict:
    _plain(path)
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"not a readable module graph: {error}") from error
    if not isinstance(graph, dict) or graph.get("schema") != SCHEMA or not isinstance(graph.get("modules"), list):
        raise ValueError("not a module graph of this schema")
    return graph


def _inputs_digest(manifest: Path, store) -> str:
    return _digest([logical_digest(store), store["root"], _digest(load_ledger(manifest))])


def graph_state(manifest: Path) -> dict:
    """fresh, stale, missing or corrupt, without touching the graph."""
    manifest = Path(manifest).resolve()
    graph_path = graph_name(manifest)
    _plain(manifest)
    if not manifest.is_file():
        raise ValueError(f"manifest does not exist: {manifest}")
    report = {"graph": str(graph_path), "manifest": str(manifest)}
    if not graph_path.exists():
        return {**report, "state": "missing", "reason": "no module graph beside the manifest"}
    try:
        graph = load_graph(graph_path)
    except ValueError as error:
        return {**report, "state": "corrupt", "reason": str(error)}
    with open_snapshot(manifest) as store:
        try:
            current = _inputs_digest(manifest, store)
        except ValueError as error:
            return {**report, "state": "stale", "reason": f"proposals ledger unreadable: {error}", "modules": len(graph["modules"])}
    if graph.get("inputs_digest") == current:
        return {**report, "state": "fresh", "modules": len(graph["modules"])}
    return {**report, "state": "stale", "reason": "snapshot or proposals changed since the graph was derived",
            "modules": len(graph["modules"])}


def _changes(graph: dict, previous: dict | None) -> dict:
    before = {m["id"]: m for m in (previous or {}).get("modules", [])} if isinstance(previous, dict) else {}
    now = {m["id"]: m for m in graph["modules"]}
    return {"added": sorted(set(now) - set(before)), "removed": sorted(set(before) - set(now)),
            "changed": sorted(i for i in now if i in before and before[i].get("members_digest") != now[i]["members_digest"]),
            "unchanged": sorted(i for i in now if i in before and before[i].get("members_digest") == now[i]["members_digest"])}


def write_graph(manifest: Path) -> dict:
    """Derive and publish `modules.json` and `modules.md` beside the manifest."""
    manifest = Path(manifest).resolve()
    graph_path, view_path = graph_name(manifest), Path(manifest).with_name(VIEW_FILE)
    _plain(graph_path)
    _plain(view_path)
    previous = None
    if graph_path.exists():
        try:
            previous = load_graph(graph_path)
        except ValueError:
            previous = None
    with open_snapshot(manifest) as store:
        before = _inputs_digest(manifest, store)
        graph = derive(store, ledger=load_ledger(manifest))
        graph["inputs_digest"] = before
        if _inputs_digest(manifest, store) != before:
            raise ValueError("snapshot or ledger changed during derivation; retry")
    graph["changes"] = _changes(graph, previous)
    view = render(graph)
    for path, data in ((graph_path, _json(graph).encode("utf-8")), (view_path, view.encode("utf-8"))):
        descriptor, name = tempfile.mkstemp(prefix=".modules-", dir=path.parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
        os.replace(name, path)
    return graph


def ensure_graph(manifest: Path, *, check: bool = False) -> dict:
    before = graph_state(manifest)
    if before["state"] == "fresh" or check:
        return {**before, "action": "none" if before["state"] == "fresh" else "reported"}
    try:
        graph = write_graph(manifest)
    except (OSError, ValueError) as error:
        return {**before, "state": "failed", "action": "none", "reason": str(error)}
    return {**graph_state(manifest), "action": "rebuilt" if before["state"] != "stale" else "refreshed",
            "changes": graph["changes"]}


# ---------------------------------------------------------------- query

def _match(module: dict, key: str) -> str | None:
    names = [module["name"], *module["aliases"]]
    if key == module["id"] or any(slug(n) == key for n in names):
        return "exact" if key == module["id"] or slug(module["name"]) == key else "alias"
    if any(key == slug(p) or slug(PurePosixPath(p).name) == key for p in module["paths"]):
        return "path"
    if any(key in slug(n) for n in names):
        return "partial"
    return None


def _owner_of(graph: dict, rel: str) -> str | None:
    """The most specific build unit whose directory holds a file."""
    best, depth = None, -2
    for module in graph["modules"]:
        if module["provenance"] != "build" or any(_inside(rel, p) for p in module["excluded"]):
            continue
        for path in module["paths"]:
            if _inside(rel, path) and (-1 if path == "." else len(path)) > depth:
                best, depth = module["id"], (-1 if path == "." else len(path))
    return best


def query(graph: dict, name: str, *, state: str = "unverified", limit: int = 10) -> dict:
    """Candidates for a name or alias with paths, files, members, relations as read scope, gaps."""
    if not isinstance(name, str) or not name.strip() or len(name) > 1000:
        raise ValueError("query name must be text of at most 1000 characters")
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer from 1 through 100")
    key = slug(name) or _posix(name)
    order = {"exact": 0, "alias": 1, "path": 2, "partial": 3}
    by_id = {m["id"]: m for m in graph["modules"]}
    matched = sorted(((order[kind], STATUSES.index(m["status"]), m["id"], kind, m)
                      for m in graph["modules"] if (kind := _match(m, key))), key=lambda i: i[:3])
    candidates = []
    for _, _, _, kind, module in matched[:limit]:
        relations, scope = [], []
        for item in graph["edges"]:
            if module["id"] not in (item["source"], item["target"]):
                continue
            outgoing = item["source"] == module["id"]
            other = item["target"] if outgoing else item["source"]
            relations.append({"kind": item["kind"], "direction": "outgoing" if outgoing else "incoming", "module": other,
                              "status": item["status"], "evidence": item["evidence"][:5], "evidence_total": item["evidence_total"]})
            if other in by_id:
                scope.append({"module": other, "name": by_id[other]["name"], "relation": item["kind"],
                              "direction": relations[-1]["direction"], "status": by_id[other]["status"],
                              "paths": by_id[other]["paths"], "excluded": by_id[other]["excluded"]})
        if module["provenance"] != "build":
            # The build units whose directories hold the member files: read scope, not target.
            for owner in sorted({_owner_of(graph, rel) for rel in module["files"]} - {None}):
                scope.append({"module": owner, "name": by_id[owner]["name"], "relation": "owned_by", "direction": "outgoing",
                              "status": by_id[owner]["status"], "paths": by_id[owner]["paths"], "excluded": by_id[owner]["excluded"]})
        candidates.append({**{k: module[k] for k in ("id", "name", "aliases", "provenance", "kind", "location", "description",
                                                      "responsibility", "status", "paths", "excluded", "files", "members",
                                                      "manifests", "evidence", "conflicts", "gaps", "coverage")},
                           "match": kind, "relations": relations,
                           "read_scope": sorted(scope, key=lambda r: (r["module"], r["relation"], r["direction"]))})
    direct = [c for c in candidates if c["match"] in ("exact", "alias")]
    if not candidates:
        status, reason = "unknown", "no module, alias or path matches the name"
    elif len(direct) == 1 and direct[0]["status"] == "confirmed" and not direct[0]["conflicts"] and state == "fresh":
        status, reason = "resolved", "one confirmed module matches the name"
    elif len(direct) == 1 and direct[0]["conflicts"]:
        status, reason = "needs_clarification", "the matching module shares members with another module"
    elif len(direct) == 1:
        status = "incomplete"
        reason = f"the matching module is {direct[0]['status']}" if state == "fresh" else f"the module graph is {state}"
    elif len(direct) > 1:
        status, reason = "needs_clarification", "several modules match the name"
    else:
        status, reason = "needs_clarification", "only partial or path matches exist"
    gaps = [] if state == "fresh" else [{"kind": f"graph_{state}", "detail": "rebuild the module graph",
                                         "repair": f"{Path(__file__).name} build <manifest>"}]
    if len(matched) > limit:
        gaps.append({"kind": "limit", "detail": f"{len(matched) - limit} further candidates omitted"})
    return {"schema": "daodan/module-query/v1", "query": name, "status": status, "reason": reason,
            "candidates": candidates, "total_matches": len(matched), "gaps": gaps, "graph_state": state,
            "binding": graph.get("binding")}


def query_manifest(manifest: Path, name: str, *, limit: int = 10) -> dict:
    state = graph_state(manifest)
    if state["state"] in ("missing", "corrupt"):
        return {"schema": "daodan/module-query/v1", "query": name, "status": "unknown", "reason": state["reason"],
                "candidates": [], "total_matches": 0, "graph_state": state["state"], "binding": None,
                "gaps": [{"kind": f"graph_{state['state']}", "detail": state["reason"],
                          "repair": f"{Path(__file__).name} build {manifest}"}]}
    return query(load_graph(Path(state["graph"])), name, state=state["state"], limit=limit)


# ------------------------------------------------------------ proposals

def propose(manifest: Path, value: object, *, replace: bool = False) -> dict:
    """Validate proposals, record them beside the manifest, rebuild; report each against the snapshot."""
    manifest = Path(manifest).resolve()
    records = validate_modules(value, source="proposals")
    write_ledger(manifest, records, replace=replace)
    graph = write_graph(manifest)
    names = {slug(r["name"]) for r in records}
    keys = ("id", "name", "kind", "location", "status", "provenance", "paths", "files", "coverage", "gaps", "conflicts")
    return {"schema": LEDGER_SCHEMA, "manifest": str(manifest), "accepted": len(records),
            "modules": [{k: m[k] for k in keys} for m in graph["modules"] if slug(m["name"]) in names],
            "graph": graph_state(manifest), "changes": graph["changes"]}


def brief(manifest: Path, *, symbol_limit: int = MAX_BRIEF_SYMBOLS) -> dict:
    """What a model needs before proposing: modules so far, symbols per file, member format, rule."""
    manifest = Path(manifest).resolve()
    if type(symbol_limit) is not int or not 0 <= symbol_limit <= 20_000:
        raise ValueError("symbol_limit must be an integer from 0 through 20000")
    state = graph_state(manifest)
    if state["state"] in ("missing", "corrupt"):
        return {"schema": "daodan/modules-brief/v1", "graph_state": state["state"], "reason": state["reason"],
                "repair": f"{Path(__file__).name} build {manifest}", "modules": [], "symbols": {}}
    graph = load_graph(Path(state["graph"]))
    by_file: dict[str, list[tuple[int, str]]] = {}
    with open_snapshot(manifest) as store:
        for record in store.iter_symbols():
            if record["name"].count(".") <= 1:
                by_file.setdefault(record["path"], []).append((record.get("start") or 0, record["name"]))
    symbols, kept = {}, 0
    total = sum(len(v) for v in by_file.values())
    for path in sorted(by_file):
        names = [n for _, n in sorted(by_file[path])]
        if kept + len(names) > symbol_limit:
            break
        symbols[path] = names
        kept += len(names)
    keys = ("id", "name", "provenance", "kind", "location", "responsibility", "status", "paths", "excluded", "coverage", "gaps")
    return {"schema": "daodan/modules-brief/v1", "graph_state": state["state"],
            "modules": [{k: m[k] for k in keys} | {"members": [x["id"] for x in m["members"]]} for m in graph["modules"]],
            "symbols": symbols, "symbols_omitted": total - kept,
            **({"symbols_hint": "files past the limit are omitted whole; list them with codebase_map_outline(path=...)"}
               if total > kept else {}),
            "member_format": "path::Symbol for a snapshot symbol, a file path, or a directory path; evidence as path or path#heading",
            "declared_file": DECLARED_FILE,
            "rule": (
                "Propose responsibility modules from an already inventoried snapshot: components, macro-features and "
                "other parts of the system, also when they cut across directories and build units. Do not recreate "
                "build units: manifests already define them. Group by responsibility, not by directory or folder name. "
                "For each candidate, identify the design decision, protocol, feature or domain state it hides and what "
                "could change independently. Include a member only when imports, calls, routes, naming or project "
                "documents connect it to the others, and cite the supporting paths in evidence: at least one, or the "
                "module stays incomplete. In responsibility, use one plain sentence, then "
                "name the incoming contract (symbols used from outside) and exclusions with reasons. When a member "
                "is shared by two modules, list it in the members of both instead of forcing one owner. Do not propose "
                "physical nodes from this brief: it contains no deployment evidence. Return records with exactly the fields "
                "name, kind, location, responsibility, members, evidence. kind is required: component (a part with its "
                "own boundary, a node of the map) or feature (a macro-feature across components, a highlight on the "
                "map, not a node). location is internal (default) or external (a service, database or device outside "
                "the repository: a component with no members, its evidence are the files that bind to it, each giving "
                "a uses edge from the module owning that file). List "
                "unassigned files and reasons separately from the proposal array. A proposal becomes an inferred module "
                f"after every member is verified; only the project's {DECLARED_FILE} confirms a module")}


# ----------------------------------------------------------------- view

def _text(value) -> str:
    return re.sub(r"([\\`*_{}\[\]|])", r"\\\1", str(value).replace("\n", " "))


def _code(value) -> str:
    return "`" + str(value).replace("`", "'") + "`"


def render(graph: dict) -> str:
    c = graph["coverage"]
    lines = ["# Modules", "", f"Snapshot digest {_code(graph['binding']['logical_digest'])}. Files: {c['files']}. "
             + "Modules: " + "; ".join(f"{p}: {c['modules'][p]}" for p in PROVENANCES) + ". "
             + "Statuses: " + "; ".join(f"{s}: {c['statuses'][s]}" for s in STATUSES) + ". "
             + "Edges: " + "; ".join(f"{k}: {v}" for k, v in c["edges"].items()) + ".", "",
             "| Id | Name | Provenance | Kind | Status | Paths | Files | Gaps |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for m in graph["modules"]:
        lines.append("| " + " | ".join([_code(m["id"]), _text(m["name"]), m["provenance"], m["kind"], m["status"],
                                        ", ".join(_code(p) for p in m["paths"]) or "none", str(m["coverage"]["files"]),
                                        str(len(m["gaps"]) + len(m["conflicts"]))]) + " |")
    for m in graph["modules"]:
        lines.extend(["", f"## {_code(m['id'])}", "", f"- Name: {_text(m['name'])}"
                      + (f"; aliases: {', '.join(_text(a) for a in m['aliases'])}" if m["aliases"] else "")
                      + f"; {m['provenance']}, {m['kind']}, {m['location']}, {m['status']}"])
        if m["description"] or m["responsibility"]:
            lines.append(f"- {_text(m['description'] or m['responsibility'])}")
        lines.append(f"- Paths: {', '.join(_code(p) for p in m['paths']) or 'none'}"
                     + (f"; excluded: {', '.join(_code(p) for p in m['excluded'])}" if m["excluded"] else "")
                     + f"; {m['coverage']['files']} files")
        if m["provenance"] != "build":
            lines.append("- Members: " + (", ".join(_code(x["id"]) + ("" if x["resolved"] else " (unresolved)") for x in m["members"]) or "none"))
        if m["evidence"]:
            lines.append("- Evidence: " + ", ".join(_code(e["path"] + (f":{e['line']}" if e.get("line") else "")) for e in m["evidence"]))
        for item in m["conflicts"]:
            lines.append(f"- Conflict: {_code(item['member'])} also in {', '.join(_code(o) for o in item['others'])}")
        for item in m["gaps"]:
            lines.append(f"- Gap {item['kind']}: {_text(item['detail'])}")
        related = [e for e in graph["edges"] if m["id"] in (e["source"], e["target"])]
        for e in related:
            lines.append(f"- {e['kind']} ({e['status']}): {_code(e['source'])} -> {_code(e['target'])}, evidence {e['evidence_total']}")
    lines.extend(["", "## Gaps", ""])
    lines.extend(f"- {g['kind']}: {_text(g.get('path', ''))} {_text(g['detail'])}" for g in graph["gaps"]) if graph["gaps"] else lines.append("- none")
    if "changes" in graph:
        lines.extend(["", "## Changes", ""] + [f"- {k}: {', '.join(_code(i) for i in v) or 'none'}" for k, v in graph["changes"].items()])
    lines.extend(["", "## Notes", ""] + [f"- {_text(n)}" for n in graph["notes"]])
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ CLI

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Modules of a Codebase Map snapshot: build units, declared and proposed modules.")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="derive modules.json and modules.md beside the manifest")
    build.add_argument("manifest", type=Path)
    build.add_argument("--check", action="store_true", help="report the graph state and write nothing")
    build.add_argument("--force", action="store_true", help="rebuild even when fresh")
    ask = sub.add_parser("query", help="candidates for a module name, alias or path")
    ask.add_argument("manifest", type=Path)
    ask.add_argument("name")
    ask.add_argument("--limit", type=int, default=10)
    info = sub.add_parser("brief", help="what a model needs before proposing modules")
    info.add_argument("manifest", type=Path)
    info.add_argument("--symbol-limit", type=int, default=MAX_BRIEF_SYMBOLS)
    prop = sub.add_parser("propose", help="validate and record a model's proposals, then rebuild")
    prop.add_argument("manifest", type=Path)
    prop.add_argument("proposals", help="JSON file (a list or {\"modules\": [...]}), or - for stdin")
    prop.add_argument("--replace", action="store_true", help="drop earlier proposals first")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            if args.force:
                graph = write_graph(args.manifest)
                result = {**graph_state(args.manifest), "action": "rebuilt", "changes": graph["changes"]}
            else:
                result = ensure_graph(args.manifest, check=args.check)
            code = 0 if result["state"] == "fresh" else 1
        elif args.command == "query":
            result, code = query_manifest(args.manifest, args.name, limit=args.limit), 0
        elif args.command == "brief":
            result, code = brief(args.manifest, symbol_limit=args.symbol_limit), 0
        else:
            text = sys.stdin.read() if args.proposals == "-" else Path(args.proposals).read_text(encoding="utf-8")
            result, code = propose(args.manifest, json.loads(text), replace=args.replace), 0
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return code
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
