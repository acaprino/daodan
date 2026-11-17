"""Build units as the build system declares them: one reader per manifest kind,
read programmatically, no heuristics."""
from __future__ import annotations

import configparser
import json
import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import PurePosixPath

from module_inventory import EMPTY_DIRECTORY, _Inventory, _dirname, _join, _line_of, _posix


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


def _table(value) -> dict:
    return value if isinstance(value, dict) else {}


def _family(ecosystem: str) -> str:
    return {"pnpm": "npm", "lerna": "npm", "nx": "npm", "angular": "npm", "rubygems": "bundler",
            "melos": "pub", "stack": "cabal"}.get(ecosystem, ecosystem)


def _dependency_name(name: str, family: str) -> str:
    if family == "python":
        return re.sub(r"[-_.]+", "-", name).casefold()
    return name


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
        for dep, spec in _table(data.get(key)).items():
            if isinstance(spec, str) and spec.startswith(("file:", "link:")):
                unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], spec.split(":", 1)[1])})
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
    packages = [p for p in (data.get("packages") or []) if isinstance(p, str)]
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
    imports = dict(_table(data.get("imports")))
    import_map = _join(unit["directory"], data["importMap"]) if isinstance(data.get("importMap"), str) else None
    if import_map in inv.headers:
        imports.update(_table(_table(json.loads(inv.text(import_map))).get("imports")))
    unit["dependencies"] = sorted(k for k, v in imports.items() if isinstance(v, str) and not v.startswith((".", "/")))
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


def _angular(inv, rel, text):
    projects = {name: spec.get("root") or "." for name, spec in _table(_table(json.loads(text)).get("projects")).items()
                if isinstance(spec, dict)}
    return [_unit(rel, "angular-workspace", None, members=list(projects.values())),
            *(_unit(rel, "angular-project", name, directory=_join(_dirname(rel), root)) for name, root in projects.items())]


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
    build = data.get("build-system")
    if isinstance(build, dict):
        deps.update(_names(build.get("requires")))
    for group in (project.get("optional-dependencies") or {}).values() if isinstance(project.get("optional-dependencies"), dict) else []:
        deps.update(_names(group))
    deps.update(d for d in _names(poetry.get("dependencies")) if d != "python")
    for group in [*_table(data.get("dependency-groups")).values(),
                  *_table(_table(tool.get("pdm")).get("dev-dependencies")).values(),
                  *(_table(g).get("dependencies") for g in _table(poetry.get("group")).values()),
                  *(_table(e).get("dependencies") for e in _table(_table(tool.get("hatch")).get("envs")).values())]:
        deps.update(_names(group))
    unit["dependencies"] = sorted(deps)
    workspace = uv.get("workspace") if isinstance(uv.get("workspace"), dict) else {}
    if isinstance(workspace.get("members"), list):
        unit["kind"] = "uv-workspace"
        unit["members"] = [m for m in workspace["members"] if isinstance(m, str)]
        unit["members"].extend("!" + m for m in workspace.get("exclude", []) if isinstance(m, str))
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
    requirements = [parser.get("options", "install_requires", fallback="")]
    if parser.has_section("options.extras_require"):
        requirements += [value for _, value in parser.items("options.extras_require")]
    return [_unit(rel, "python-package", name.strip() if name else None,
                  dependencies=_names([line for value in requirements for line in value.splitlines()]))]


def _setup_py(inv, rel, text):
    match = re.search(r"""\bname\s*=\s*['"]([^'"]+)['"]""", text)
    return [_unit(rel, "python-package", match.group(1) if match else None)]


def _cargo(inv, rel, text):
    data = tomllib.loads(text)
    package = data.get("package") if isinstance(data.get("package"), dict) else {}
    unit = _unit(rel, "cargo-crate", package.get("name") if isinstance(package.get("name"), str) else None)
    _described(unit, package)
    deps = set()
    for holder in [data, *_table(data.get("target")).values()]:
        for key in ("dependencies", "dev-dependencies", "build-dependencies"):
            for dep, spec in _table(_table(holder).get(key)).items():
                spec = _table(spec)
                dep = spec["package"] if isinstance(spec.get("package"), str) else dep
                deps.add(dep)
                if isinstance(spec.get("path"), str):
                    unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], spec["path"])})
                elif isinstance(spec.get("git"), str):
                    unit["path_dependencies"].append({"name": dep, "path": "", "git": spec["git"]})
    unit["dependencies"] = sorted(deps)
    workspace = data.get("workspace") if isinstance(data.get("workspace"), dict) else {}
    if isinstance(workspace.get("members"), list):
        unit["kind"] = "cargo-workspace"
        unit["members"] = [m for m in workspace["members"] if isinstance(m, str)]
        unit["members"].extend("!" + m for m in workspace.get("exclude", []) if isinstance(m, str))
    return [unit]


def _go_mod(inv, rel, text):
    match = re.search(r"^module\s+(\S+)", text, re.M)
    unit = _unit(rel, "go-module", match.group(1).strip('"') if match else None)
    deps = set()
    requiring = False
    for raw in text.splitlines():
        line, _, comment = raw.partition("//")
        line = line.strip()
        require = re.match(r"require\s+(.+)", line)
        if require and require.group(1) == "(":
            requiring = True
            continue
        if line == ")":
            requiring = False
            continue
        declaration = require.group(1) if require else line if requiring else ""
        match = re.fullmatch(r'("[^"]+"|[^\s"]+)\s+v[^\s]+', declaration)
        if match and comment.strip() != "indirect":
            deps.add(match.group(1).strip('"'))
    unit["dependencies"] = sorted(deps)
    for dep, target in re.findall(r"^\s*(?:replace\s+)?(\S+)(?:\s+\S+)?\s+=>\s+(\.{1,2}/\S+|/\S+)", text, re.M):
        unit["path_dependencies"].append({"name": dep, "path": _join(unit["directory"], target)})
    return [unit]


def _go_work(inv, rel, text):
    members = re.findall(r"^\s*(?:use\s+)?(\.{1,2}/[^\s)]+|\./?)\s*$", text, re.M)
    return [_unit(rel, "go-workspace", None, members=members)]


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
    plugins = root.findall(f"{ns}build/{ns}plugins/{ns}plugin")
    used = [node for plugin in plugins for tag in ("dependency", "path") for node in plugin.iter(ns + tag)]
    for dep in [*root.findall(f"{ns}dependencies/{ns}dependency"), *plugins, *used]:
        name = child(dep, "artifactId")
        if name:
            dep_group = child(dep, "groupId") or ("org.apache.maven.plugins" if dep in plugins else None)
            if dep_group in ("${project.groupId}", "${pom.groupId}"):
                dep_group = group
            deps.add(f"{dep_group}:{name}" if dep_group else name)
    unit["dependencies"] = sorted(deps)
    members = [m.text.strip() for m in root.findall(f"{ns}modules/{ns}module") if m.text and m.text.strip()]
    if members:
        unit["kind"] = "maven-aggregator"
        unit["members"] = members
    if root.find(ns + "profiles") is not None:
        unit["gaps"] = [{"kind": "profiles_not_evaluated",
                         "detail": "Only unconditional Maven modules and dependencies are read; profiles are not evaluated"}]
    return [unit]


def _gradle_settings(inv, rel, text):
    name = re.search(r"""rootProject\.name\s*=\s*['"]([^'"]+)['"]""", text)
    unit = _unit(rel, "gradle-build", name.group(1) if name else None)
    members = []
    for block in re.findall(r"\binclude\b\s*\(?([^)\n]+)\)?", text):
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
    units, members = [], []
    for name, path in re.findall(r"""Project\("\{[^}]+\}"\)\s*=\s*"([^"]+)",\s*"([^"]+)\""""
                                 , text):
        posix = _posix(path)
        if posix.lower().endswith((".csproj", ".fsproj", ".vbproj")):
            members.append(_dirname(posix))
            units.append(_unit(_join(_dirname(rel), posix), "dotnet-project", name,
                               directory=_dirname(_join(_dirname(rel), posix)), declared_by=rel))
    return [_unit(rel, "dotnet-solution", PurePosixPath(rel).stem, members=members)] + units


def _slnx(inv, rel, text):
    projects = [_posix(node.get("Path", "")) for node in ET.fromstring(text).iter("Project")]
    return [_unit(rel, "dotnet-solution", PurePosixPath(rel).stem,
                  members=[_dirname(p) for p in projects if p.lower().endswith((".csproj", ".fsproj", ".vbproj"))])]


def _vcxproj(inv, rel, text):
    """One unit per project file: several share a folder, so the file is the unit's `slot`."""
    unit = _unit(rel, "msbuild-project", PurePosixPath(rel).stem, slot=rel)
    for node in ET.fromstring(text).iter():
        if node.tag.endswith("ProjectReference") and node.get("Include"):
            target = _join(unit["directory"], _posix(node.get("Include")))
            unit["path_dependencies"].append({"name": PurePosixPath(target).stem, "path": _dirname(target), "slot": target})
    return [unit]


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
    unit["dependencies"] = sorted(n for n in {*_names(data.get("require")), *_names(data.get("require-dev"))}
                                  if "/" in n)  # `php`, `ext-json`: the platform, not a package
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
                if isinstance(spec, dict) and "sdk" in spec:
                    continue  # `sdk: flutter` comes with the toolchain
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
    for dep in re.findall(r"\{\s*:(\w+)\s*,[^}]*?in_umbrella:\s*true", text):
        unit["path_dependencies"].append({"name": dep, "path": None})
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
            rf"""lazy\s+val\s+{val}\b(?:(?!lazy\s+val)[\s\S])*?dependsOn\s*\(([^)]*)\)""", text) for dep in re.findall(r"\w+", dep)]
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


def _buf(inv, rel, text):
    data = _yaml(text)
    modules = [m for m in data.get("modules") or [] if isinstance(m, dict) and isinstance(m.get("path"), str)]
    return [_unit(rel, "buf-module", m.get("name") if isinstance(m.get("name"), str) else None,
                  directory=_join(_dirname(rel), m["path"]), dependencies=_names(data.get("deps")))
            for m in modules or [{"path": ".", "name": data.get("name")}]]


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
    "project.json": ("nx", _nx_project), "angular.json": ("angular", _angular), "pyproject.toml": ("python", _pyproject),
    "setup.cfg": ("python", _setup_cfg), "setup.py": ("python", _setup_py), "Cargo.toml": ("cargo", _cargo),
    "go.mod": ("go", _go_mod), "go.work": ("go", _go_work), "pom.xml": ("maven", _pom),
    "settings.gradle": ("gradle", _gradle_settings), "settings.gradle.kts": ("gradle", _gradle_settings),
    "build.gradle": ("gradle", _gradle_build), "build.gradle.kts": ("gradle", _gradle_build),
    "composer.json": ("composer", _composer), "Gemfile": ("bundler", _gemfile),
    "pubspec.yaml": ("pub", _pubspec), "melos.yaml": ("melos", _melos), "Package.swift": ("swiftpm", _package_swift),
    "mix.exs": ("mix", _mix), "CMakeLists.txt": ("cmake", _cmake), "stack.yaml": ("stack", _stack),
    "build.sbt": ("sbt", _sbt), "build.zig.zon": ("zig", _zig), "Project.toml": ("julia", _julia),
    "dune-project": ("dune", _dune), "buf.yaml": ("buf", _buf), "plugin.toml": ("daodan", _daodan_plugin),
}


SUFFIX_READERS = {".sln": ("dotnet", _sln), ".slnx": ("dotnet", _slnx), ".csproj": ("dotnet", _msbuild_project),
                  ".vcxproj": ("msbuild", _vcxproj), ".vcproj": ("msbuild", _vcxproj),
                  ".fsproj": ("dotnet", _msbuild_project), ".vbproj": ("dotnet", _msbuild_project),
                  ".gemspec": ("rubygems", _gemspec), ".cabal": ("cabal", _cabal), ".tf": ("terraform", _terraform)}


ECOSYSTEMS = sorted({eco for eco, _ in [*READERS.values(), *SUFFIX_READERS.values()]})


def _read_units(inventory: _Inventory) -> tuple[list[dict], list[dict]]:
    units, gaps = [], []
    for rel in inventory.files:
        name = PurePosixPath(rel).name
        reader = READERS.get(name) or SUFFIX_READERS.get(PurePosixPath(rel).suffix.lower())
        if reader is None:
            continue
        ecosystem, read = reader
        text = inventory.text(rel)
        try:
            found = read(inventory, rel, text)
        except (ValueError, TypeError, KeyError, configparser.Error, tomllib.TOMLDecodeError, ET.ParseError) as error:
            gaps.append({"kind": "manifest_unreadable", "path": rel, "detail": f"{type(error).__name__}: {error}"})
            continue
        for unit in found:
            gaps.extend({"path": rel, **gap} for gap in unit.pop("gaps", []))
            absence = None if unit["directory"] in inventory.directories else inventory.absence(unit["directory"])
            if absence not in (None, EMPTY_DIRECTORY):  # a folder of files the snapshot does not inventory is still the unit's
                gaps.append({"kind": "directory_missing", "path": rel,
                             "detail": f"{unit['name'] or unit['kind']} at {unit['directory']}: {absence}"})
                continue
            unit["ecosystem"] = ecosystem
            unit["line"] = _line_of(text, unit["name"]) if unit["name"] else None
            units.append(unit)
    return units, gaps
