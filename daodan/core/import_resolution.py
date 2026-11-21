"""Import specifiers resolved to files of the snapshot: module configuration
(tsconfig, jsconfig, workspaces), candidate paths per language, C and C++ include
contexts, and the reverse import index a change set's blast radius reads."""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath

from snapshot_store import file_headers, header_metadata
from source_files import MAX_PARSE_BYTES, is_forbidden
from tree_scope import Perimeter


# Extensions an import specifier may resolve to, in preference order.
_MODULE_EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".java", ".kt", ".kts", ".cs", ".rs")
# Directory imports: `orders` resolving to the package's entry file.
_PACKAGE_FILES = ("__init__.py", "index.ts", "index.tsx", "index.js", "index.jsx", "mod.rs")
# A stylesheet resolves stylesheets only, and only these ways: a TypeScript
# `import "./theme"` never means `theme.css`, and a Python `import app` never
# means `app/static/app.css`, so none of this is tried for any other importer.
_STYLESHEET_SUFFIXES = (".css", ".scss", ".sass", ".less", ".pcss", ".postcss")
_C_FAMILY_SUFFIXES = (".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".hxx")


def c_family_contexts(sources: dict[str, bytes]) -> dict[str, dict]:
    """Each C or C++ file's include context: the macros of the snapshot's files it shares a translation unit with,
    its includes resolved as the snapshot resolves them (see `languages.cfamily.include_contexts`)."""
    if not sources:
        return {}
    from languages import cfamily

    texts = {rel: data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
             for rel, data in sources.items()}
    known = _by_basename(texts)
    return cfamily.include_contexts(texts, lambda module, importer: resolve_module(module, importer, known))


def context_key(macros: dict) -> str:
    """The identity of an include context, part of a C or C++ file's reuse key."""
    return hashlib.sha256(json.dumps(macros, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]


def _by_basename(paths) -> dict[str, list[str]]:
    """
    Group paths by their final segment, each group sorted.

    Sorted rather than insertion order because the caller usually passes a
    set, whose iteration order depends on Python's per-process hash
    randomization: left unsorted, an ambiguous bare-basename citation with
    several candidates could resolve to a different one on every run of the
    identical tree. The ambiguity itself is not resolved here, only made to
    pick the same candidate consistently.
    """
    index: dict[str, list[str]] = {}
    for path in paths:
        index.setdefault(path.rsplit("/", 1)[-1], []).append(path)
    for candidates in index.values():
        candidates.sort()
    return index


def _lookup(candidate: str, known: dict[str, list[str]], importer: str) -> str | None:
    """
    Resolve one candidate path against the known set.

    A candidate matches a known path when it equals it or is a suffix of it at a
    segment boundary, because an import specifier names a module, not a path
    from the repository root. When several match, the one in the importer's own
    directory wins; a tie with no local winner resolves to nothing, since
    inflating the radius on a guess costs a re-read of the wrong file.
    """
    while candidate.startswith("./"):
        candidate = candidate[2:]
    if not candidate:
        return None
    hits = [p for p in known.get(candidate.rsplit("/", 1)[-1], [])
            if p == candidate or p.endswith("/" + candidate)]
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    home = importer.rsplit("/", 1)[0] if "/" in importer else ""
    local = [p for p in hits if p.rsplit("/", 1)[0] == home]
    return local[0] if len(local) == 1 else None


def _resolve_stylesheet(module: str, importer: str, known: dict[str, list[str]]) -> str | None:
    """
    A stylesheet import is a URL relative to the importing file, and each tool
    tries its own forms in its own order. Sass tries `.sass` and `.scss`, plain
    or partial, then `.css`, then the directory's index files; LESS appends
    `.less`; a plain CSS `@import` loads exactly what it names, or that name
    plus `.css`. A candidate must match a known path exactly: the specifier is
    already joined to the importer's directory, and a suffix match would bind
    it to a same-named file somewhere else.
    """
    if not module.startswith("."):
        return None
    base = importer.rsplit("/", 1)[0] if "/" in importer else ""
    joined = os.path.normpath(os.path.join(base, module)).replace(os.sep, "/")
    head, _, tail = joined.rpartition("/")
    partial = f"{head}/_{tail}" if head else f"_{tail}"
    lowered = importer.lower()
    candidates = [joined]
    if lowered.endswith((".scss", ".sass")):
        for ext in (".sass", ".scss", ".css"):
            candidates += [joined + ext, partial + ext]
        candidates += [f"{joined}/{name}" for name in
                       ("_index.sass", "index.sass", "_index.scss", "index.scss", "_index.css", "index.css")]
    elif lowered.endswith(".less"):
        candidates.append(joined + ".less")
    else:
        candidates.append(joined + ".css")
    for candidate in candidates:
        if candidate in known.get(candidate.rsplit("/", 1)[-1], []):
            return candidate
    return None


def _strip_jsonc_comments(raw: str) -> str:
    """Strip // and /* */ comments and trailing commas from tsconfig-style JSONC."""
    out: list[str] = []
    i = 0
    n = len(raw)
    in_string = False
    while i < n:
        ch = raw[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(raw[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and raw[i + 1] == "/":
            i += 2
            while i < n and raw[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and raw[i + 1] == "*":
            i += 2
            while i + 1 < n and not (raw[i] == "*" and raw[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(ch)
        i += 1
    cleaned = "".join(out)
    return re.sub(r'("(?:\\.|[^"\\])*")|,\s*(?=[}\]])',
                  lambda match: match.group(1) or "", cleaned)


class _ConfigReader:
    """JSON configuration files inside one perimeter, each read once, with `extends` followed."""

    def __init__(self, root: Path, perimeter: Perimeter, source_observations: dict[Path, bytes] | None):
        self.root = root
        self.perimeter = perimeter
        self.source_observations = source_observations
        self.documents: dict[Path, dict] = {}
        self.loaded: dict[Path, dict] = {}

    def allowed(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.root)
        except ValueError:
            return False
        return self.perimeter.covers(path) and not is_forbidden(path.name, path)

    def read(self, path: Path) -> dict:
        path = path.resolve()
        if path in self.documents:
            return self.documents[path]
        data = {}
        if self.allowed(path):
            try:
                if self.source_observations is None:
                    text = path.read_text(encoding="utf-8") if path.stat().st_size <= MAX_PARSE_BYTES else None
                else:
                    captured = self.source_observations.get(path)
                    text = (captured.decode("utf-8") if isinstance(captured, bytes) and len(captured) <= MAX_PARSE_BYTES
                            else None)
                if text is not None:
                    value = json.loads(_strip_jsonc_comments(text))
                    if isinstance(value, dict):
                        data = value
            except (OSError, UnicodeError, ValueError, RecursionError):
                pass
        self.documents[path] = data
        return data

    def _parent(self, path: Path, name: str) -> Path:
        """A relative `extends` target, with `.json` added when the bare name is not a file."""
        candidate = path.parent / name
        if self.allowed(candidate) and candidate.suffix != ".json":
            is_file = (candidate.resolve() in self.source_observations if self.source_observations is not None
                       else candidate.is_file())
            if not is_file:
                candidate = Path(str(candidate) + ".json")
        return candidate

    def options(self, path: Path, visiting: set[Path]) -> dict:
        path = path.resolve()
        # A cycle guard alone does not bound a long, acyclic inheritance chain.
        if path in visiting or len(visiting) >= 32:
            return {}
        if path in self.loaded:
            return self.loaded[path]
        document = self.read(path)
        merged = {}
        parent = document.get("extends")
        parents = parent if isinstance(parent, list) else [parent]
        for name in parents:
            if isinstance(name, str) and name.startswith("."):
                candidate = self._parent(path, name)
                if self.allowed(candidate):
                    merged.update(self.options(candidate, visiting | {path}))
        own = document.get("compilerOptions", {})
        if isinstance(own, dict):
            base = own.get("baseUrl")
            if isinstance(base, str):
                merged["baseUrl"] = (path.parent / base).resolve().as_posix()
            paths = own.get("paths")
            if isinstance(paths, dict):
                base_path = Path(merged.get("baseUrl", path.parent))
                merged["paths"] = {
                    pattern: [(base_path / target).as_posix() for target in targets
                              if isinstance(target, str)]
                    for pattern, targets in paths.items()
                    if isinstance(pattern, str) and isinstance(targets, list)
                }
        self.loaded[path] = merged
        return merged

    def directories(self):
        """The directories to look for configuration in: the walk, or the observed files' folders."""
        if self.source_observations is None:
            return self.perimeter.walk()
        observed_directories: dict[Path, set[str]] = {}
        for path in self.source_observations:
            if not isinstance(path, Path) or not path.is_absolute():
                raise ValueError("configuration observations require absolute Path keys")
            if self.allowed(path):
                observed_directories.setdefault(path.parent, set()).add(path.name)
        return sorted(observed_directories.items())


def _workspace_packages(reader: _ConfigReader, root: Path, package_paths: list[Path]) -> dict:
    """The packages of the root's workspaces by name; a name two packages share maps to None."""
    packages: dict = {}
    project = reader.read(root / "package.json")
    workspaces = project.get("workspaces", [])
    if isinstance(workspaces, dict):
        workspaces = workspaces.get("packages", [])
    patterns = [item for item in workspaces if isinstance(item, str)] if isinstance(workspaces, list) else []
    for path in package_paths:
        directory = path.parent.relative_to(root).as_posix()
        if directory != "." and not any(fnmatch.fnmatchcase(directory, pattern.rstrip("/")) for pattern in patterns):
            continue
        package = reader.read(path)
        name = package.get("name")
        if isinstance(name, str) and name:
            # Duplicate package identities are ambiguous, so neither wins.
            if name in packages:
                packages[name] = None
            else:
                packages[name] = {**package, "directory": path.parent.as_posix()}
    return packages


def ts_path_config(root: Path, *, source_observations: dict[Path, bytes] | None = None) -> dict:
    """Read project module configuration only inside the target's perimeter.

    Each option retains the directory in which it was declared, including an
    inherited baseUrl or paths map. Package configs apply to their descendants.
    Relative extends are supported; package-manager config lookup is outside
    the analyzed tree's dependency perimeter and is deliberately not guessed.
    Supplied observations use absolute Path keys and replace live discovery and
    content reads, so snapshot consumers cannot acquire unrecorded configuration.
    """
    root = Path(root).resolve()
    config = {"root": root.as_posix(), "configs": {}, "packages": {}}
    if not root.is_dir():
        return config
    reader = _ConfigReader(root, Perimeter(root), source_observations)
    package_paths = []
    for directory, names in reader.directories():
        if "tsconfig.json" in names:
            path = directory / "tsconfig.json"
            config["configs"][directory.as_posix()] = reader.options(path, set())
        elif "jsconfig.json" in names:
            path = directory / "jsconfig.json"
            config["configs"][directory.as_posix()] = reader.options(path, set())
        if "package.json" in names:
            package_paths.append(directory / "package.json")
    config["packages"] = _workspace_packages(reader, root, package_paths)
    return config


def _expand_alias(module: str, aliases: dict[str, list[str]] | None) -> list[str]:
    """Expand the most specific configured path pattern, without inventing aliases."""
    expanded: list[str] = []
    if aliases:
        if module in aliases:
            return list(aliases[module])
        for pat, targets in sorted(aliases.items(), key=lambda item: (-len(item[0].split("*")[0]), -len(item[0]))):
            if pat.count("*") == 1:
                prefix, suffix = pat.split("*", 1)
                if module.startswith(prefix) and module.endswith(suffix):
                    mid = module[len(prefix): len(module) - len(suffix) if suffix else len(module)]
                    for t in targets:
                        expanded.append(t.replace("*", mid))
                    break
    return expanded


def _module_candidates(candidate: str, importer: str) -> list[str]:
    """Ordered file forms for this importer's language."""
    suffix = Path(importer).suffix.lower()
    if suffix == ".py":
        return [candidate + ".py", candidate + "/__init__.py"]
    if suffix in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte", ".astro"}:
        extensions = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte")
        paths = [candidate]
        # TS source commonly imports the JavaScript path emitted by its build.
        if suffix in {".ts", ".tsx", ".vue", ".svelte", ".astro"}:
            for emitted, source in ((".js", ".ts"), (".jsx", ".tsx"), (".mjs", ".mts"), (".cjs", ".cts")):
                if candidate.endswith(emitted):
                    paths.insert(0, candidate[:-len(emitted)] + source)
        if Path(candidate).suffix.lower() not in extensions:
            paths += [candidate + ext for ext in extensions]
            paths += [candidate + "/index" + ext for ext in extensions]
        return paths
    return [candidate] + [candidate + ext for ext in _MODULE_EXTENSIONS] + [candidate + "/" + name for name in _PACKAGE_FILES]


def _package_candidates(module: str, packages: dict) -> list[str]:
    for name in sorted(packages, key=len, reverse=True):
        if module != name and not module.startswith(name + "/"):
            continue
        package = packages[name]
        if not isinstance(package, dict):
            return []
        subpath = "." if module == name else "./" + module[len(name) + 1:]

        def targets(value) -> list[str]:
            if isinstance(value, str):
                return [value]
            if isinstance(value, list):
                return [target for item in value for target in targets(item)]
            if isinstance(value, dict):
                for condition in ("types", "import", "require", "default"):
                    if condition in value:
                        return targets(value[condition])
            return []

        exports = package.get("exports")
        if "exports" in package:
            if isinstance(exports, dict) and any(key.startswith(".") for key in exports):
                matches = _expand_alias(subpath, {key: targets(value) for key, value in exports.items()})
            else:
                matches = targets(exports) if subpath == "." else []
        elif subpath == ".":
            matches = [package[key] for key in ("types", "module", "main") if isinstance(package.get(key), str)] or ["./index"]
        else:
            matches = [subpath]
        directory = Path(package["directory"])
        return [(directory / value).as_posix() for value in matches
                if value.startswith("./") or (exports is None and not Path(value).is_absolute())]
    return []


def _python_module_candidates(module: str, home: Path, target: Path) -> list[str]:
    """Module bases shared by graph resolution and imported-module bindings."""
    if module.startswith("."):
        level = len(module) - len(module.lstrip("."))
        base = home
        for _ in range(level - 1):
            base = base.parent
        return [(base / module[level:].replace(".", "/")).as_posix()]
    base = target if target.is_dir() else target.parent
    # The importer's directory comes first: it is sys.path[0] when the file
    # runs as a script, and flat script directories import siblings by bare name.
    return [(directory / module.replace(".", "/")).as_posix()
            for directory in dict.fromkeys((home, base, base / "src"))]


def resolved_imports(manifest: dict, config: dict | None = None, *,
                     include_self: bool = False) -> dict[str, dict[str, list[str]]]:
    return dict(iter_resolved_imports(manifest, config, include_self=include_self))


_SCRIPT_SUFFIXES = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte", ".astro"}


class _ImportResolver:
    """The files of one manifest an import may resolve to, and the resolution of one importer's specifiers."""

    def __init__(self, manifest, config: dict | None, include_self: bool, perimeter: Perimeter | None):
        root = Path(manifest.get("root") or ".").resolve()
        target = (root / (manifest.get("target") or ".")).resolve()
        self.root, self.target = root, target
        self.config = ts_path_config(target) if config is None else config
        self.files = file_headers(manifest)
        self.header = getattr(manifest, "get_file_header", self.files.get)
        self.include_self = include_self
        perimeter = Perimeter(target) if perimeter is None else perimeter
        self.by_absolute: dict[Path, str] = {}
        self.by_norm: dict[str, str] = {}
        self.allowed: set[str] = set()
        for rel in self.files:
            if is_forbidden(Path(rel).name, root / rel):
                continue
            full_path = root / rel
            resolved_rel = full_path.resolve()
            if (resolved_rel.is_relative_to(target) or resolved_rel == target) and perimeter.covers(resolved_rel):
                self.by_absolute[resolved_rel] = rel
                self.allowed.add(rel)
                norm_rel = os.path.normcase(os.path.abspath(str(full_path)))
                if os.path.normcase(str(resolved_rel)) == norm_rel:
                    self.by_norm[norm_rel] = rel
        self.known = _by_basename(self.by_absolute.values())
        self.tauri_apps = None

    def keeps(self, hit: str | None, importer: str) -> bool:
        return bool(hit) and (self.include_self or hit != importer)

    def lookup(self, candidate: str, importer: str) -> str | None:
        for path in _module_candidates(candidate, importer):
            norm_path = os.path.normcase(os.path.abspath(path))
            hit = self.by_norm.get(norm_path)
            if hit is not None and not os.path.islink(path):
                return hit
            if os.path.exists(path):
                match = self.by_absolute.get(Path(path).resolve())
                if match:
                    return match
        return None

    def settings(self, home: Path) -> dict:
        """The module configuration of the nearest directory above the importer that declares one."""
        applicable = [(Path(directory), value) for directory, value in self.config.get("configs", {}).items()
                      if home.is_relative_to(Path(directory))]
        return max(applicable, key=lambda item: len(item[0].parts))[1] if applicable else {}

    def declaring(self, name: str, importer: str, suffixes: tuple[str, ...]) -> list[str]:
        """Files of these languages that export or define `name`."""
        return [rel for rel in self.allowed
                if rel.lower().endswith(suffixes) and (self.include_self or rel != importer)
                and (name in ((self.files.get(rel) or {}).get("exports") or ())
                     or name in ((self.files.get(rel) or {}).get("symbols") or {}))]

    def tauri_command(self, importer: str, name: str) -> list[str]:
        """An attributed Rust function registered at a literal handler path in this frontend's src-tauri crate."""
        if self.tauri_apps is None:
            apps, records = {}, {}
            for rel in self.allowed:
                file = PurePosixPath(rel)
                if file.suffix != ".rs":
                    continue
                crate = next((p for p in file.parents if p.name == "src" and p.parent.name == "src-tauri"), None)
                if crate is None:
                    continue
                apps.setdefault(crate.parent.parent, {})
                header = self.header(rel) or {}
                if header.get("tauri"):
                    records[file] = (crate, header)
            for file, (crate, header) in records.items():
                for handler in header["tauri"]["handlers"]:
                    parts = handler.split("::")
                    command = parts.pop()
                    if not parts:
                        imports = {entry["module"] if not entry.get("from") else f"{entry['module']}::{command}"
                                   for entry in header.get("import_bindings", ()) if command in entry["names"]}
                        if len(imports) == 1:
                            parts = imports.pop().split("::")[:-1]
                        elif imports:
                            continue
                    paths = [file]
                    if parts:
                        base = file.parent if file.name in ("main.rs", "lib.rs", "mod.rs") else file.with_suffix("")
                        if parts[0] == "crate":
                            parts.pop(0)
                            base = crate
                        while parts and parts[0] in ("self", "super"):
                            if parts.pop(0) == "super":
                                base = base.parent
                        base = base.joinpath(*parts)
                        if base != crate:
                            paths = [base.with_suffix(".rs"), base / "mod.rs"]
                        else:
                            paths = [file] if file in (crate / "main.rs", crate / "lib.rs") else [crate / "main.rs", crate / "lib.rs"]
                    for candidate in paths:
                        if (candidate in records and records[candidate][0] == crate
                                and command in records[candidate][1]["tauri"]["commands"]):
                            apps[crate.parent.parent].setdefault(command, set()).add(str(candidate))
            self.tauri_apps = apps
        for parent in PurePosixPath(importer).parents:
            if parent in self.tauri_apps:
                return sorted(self.tauri_apps[parent].get(name, ()))
        return []

    def script_candidates(self, module: str, home: Path, settings: dict) -> list[str]:
        if module.startswith("."):
            return [(home / module).as_posix()]
        candidates = _expand_alias(module, settings.get("paths"))
        if "baseUrl" in settings:
            candidates.append((Path(settings["baseUrl"]) / module).as_posix())
        return candidates + _package_candidates(module, self.config.get("packages", {}))

    def by_module_name(self, module: str, importer: str, suffix: str, bindings: list[dict],
                       modules: dict, resolved: set[str]) -> None:
        """Languages that import by module or package name: the module, then each imported member."""
        hit = resolve_module(module, importer, self.known)
        if self.keeps(hit, importer):
            resolved.add(hit)
        if suffix in {".java", ".rs", ".kt", ".kts", ".cs"}:
            sep = "::" if suffix == ".rs" else "."
            for binding in bindings:
                if binding.get("module") == module and binding.get("from"):
                    for name in binding.get("names", []):
                        if name == "*":
                            continue
                        member = name.split(" as ", 1)[0].strip()
                        qualified = f"{module}{sep}{member}"
                        mhit = resolve_module(qualified, importer, self.known)
                        if self.keeps(mhit, importer):
                            resolved.add(mhit)
                            modules[qualified] = [mhit]
                        elif self.keeps(hit, importer):
                            modules[qualified] = [hit]
        if not resolved and suffix in {".kt", ".kts", ".cs"}:
            same_lang_exts = (".kt", ".kts") if suffix in {".kt", ".kts"} else (".cs",)
            matches = self.declaring(module.rsplit(".", 1)[-1], importer, same_lang_exts)
            if len(matches) == 1:
                resolved.add(matches[0])

    def python_names(self, module: str, importer: str, bindings: list[dict], candidates: list[str],
                     resolved: set[str]) -> None:
        """`from package import name`: a name that is itself a module of the package."""
        for binding in bindings:
            if binding.get("module") == module and binding.get("from"):
                for name in binding.get("names", []):
                    if name == "*":
                        continue
                    for candidate in candidates:
                        hit = self.lookup(candidate.rstrip("/") + "/" + name, importer)
                        if self.keeps(hit, importer):
                            resolved.add(hit)
                            break

    def resolve(self, importer: str, entry: dict) -> dict[str, list[str]]:
        bindings = entry.get("import_bindings", [])
        home = (self.root / importer).parent
        suffix = Path(importer).suffix.lower()
        settings = self.settings(home)
        modules = {}
        for module in entry.get("imports", []):
            resolved = set()
            candidates = []
            if module.startswith("tauri::command::"):
                command = module.removeprefix("tauri::command::")
                modules[module] = self.tauri_command(importer, command)
                continue
            if suffix == ".py":
                candidates = _python_module_candidates(module, home, self.target)
            elif suffix in _SCRIPT_SUFFIXES:
                candidates = self.script_candidates(module, home, settings)
            else:
                self.by_module_name(module, importer, suffix, bindings, modules, resolved)
            if suffix == ".rs" and " as " in module:
                clean_mod = module.split(" as ", 1)[0].strip()
                if clean_mod and resolved:
                    modules[clean_mod] = sorted(resolved)
            for candidate in candidates:
                hit = self.lookup(candidate, importer)
                if self.keeps(hit, importer):
                    resolved.add(hit)
                    # Paths entries are ordered fallbacks, not multiple edges.
                    break
            if suffix == ".py":
                self.python_names(module, importer, bindings, candidates, resolved)
            modules[module] = sorted(resolved)
        return modules


def iter_resolved_imports(manifest: dict, config: dict | None = None, *,
                     include_self: bool = False,
                     only_importers: set[str] | None = None,
                     perimeter: Perimeter | None = None) -> dict[str, dict[str, list[str]]]:
    """Resolve each manifest specifier once, keeping its binding provenance.

    JS/TS paths match only explicit relative, configured or workspace targets.
    Python absolute modules use the importer's directory, then the analyzed
    root and its conventional src directory; relative Python modules start at
    the importing package.
    """
    resolver = _ImportResolver(manifest, config, include_self, perimeter)
    header_iter = (
        manifest.iter_file_headers_only()
        if hasattr(manifest, "iter_file_headers_only")
        else resolver.files.items()
    )
    for importer, entry in header_iter:
        if only_importers is not None and importer not in only_importers:
            continue
        if importer not in resolver.allowed:
            yield importer, {}
            continue
        yield importer, resolver.resolve(importer, entry)


def module_targets(manifest: dict, config: dict | None = None, *,
                   include_self: bool = False) -> dict[str, list[str]]:
    """The distinct internal targets of every importer, in a stable order."""
    return {importer: sorted({target for targets in modules.values() for target in targets})
            for importer, modules in resolved_imports(manifest, config, include_self=include_self).items()}


def _known(candidate: str, known: dict[str, list[str]]) -> bool:
    return candidate in known.get(candidate.rsplit("/", 1)[-1], [])


def _include_target(module: str, importer: str, known: dict[str, list[str]]) -> str | None:
    # `#include <x.h>` names a system or search-path header: external. `#include "x.h"` is
    # looked up next to the including file first; the search paths are the build's, unknown
    # here, so otherwise only a single project file ending in that path matches.
    if module.startswith("<"):
        return None
    base = importer.rsplit("/", 1)[0] if "/" in importer else ""
    joined = os.path.normpath(os.path.join(base, module)).replace(os.sep, "/")
    if _known(joined, known):
        return joined
    return _lookup(module, known, importer)


def _super_prefixes(raw: str, base: str, stem: str) -> list[str]:
    """`super::` paths climbed from the module's own directory, and from its parent's."""
    prefixes: list[str] = []
    for start_dir in [base] if stem in {"mod", "lib", "main"} else [f"{base}/{stem}" if base else stem, base]:
        parent = start_dir
        rest = raw
        underflow = False
        while rest.startswith("super::"):
            rest = rest[len("super::"):]
            if not parent:
                underflow = True
                break
            parent = parent.rsplit("/", 1)[0] if "/" in parent else ""
        if not underflow:
            rel_mod = rest.replace("::", "/")
            cand = f"{parent}/{rel_mod}" if parent else rel_mod
            if cand not in prefixes:
                prefixes.append(cand)
    return prefixes


def _rust_target(module: str, importer: str, known: dict[str, list[str]]) -> str | None:
    """A `crate::`, `self::` or `super::` path to its `.rs` or `mod.rs` file; any other path is external."""
    raw = module.split(" as ", 1)[0].strip()
    if not raw.startswith(("crate::", "self::", "super::")):
        return None
    base = importer.rsplit("/", 1)[0] if "/" in importer else ""
    stem = importer.rsplit("/", 1)[-1][:-3]
    if raw.startswith("crate::"):
        rel_mod = raw[len("crate::"):].replace("::", "/")
        parts = importer.split("/")
        src_idx = max((idx for idx, seg in enumerate(parts[:-1]) if seg == "src"), default=-1)
        crate_root = "/".join(parts[:src_idx + 1]) if src_idx >= 0 else base
        prefixes = [f"{crate_root}/{rel_mod}" if crate_root else rel_mod]
        if crate_root:
            prefixes.append(rel_mod)
    elif raw.startswith("self::"):
        rel_mod = raw[len("self::"):].replace("::", "/")
        mod_dir = base if stem in {"mod", "lib", "main"} else (f"{base}/{stem}" if base else stem)
        prefixes = [f"{mod_dir}/{rel_mod}" if mod_dir else rel_mod]
    else:
        prefixes = _super_prefixes(raw, base, stem)
    candidates: list[str] = []
    for pref in prefixes:
        candidates += [pref + ".rs", f"{pref}/mod.rs"]
        if "/" in pref:
            mod_parent = pref.rsplit("/", 1)[0]
            candidates += [mod_parent + ".rs", f"{mod_parent}/mod.rs"]
    return next((candidate for candidate in candidates if _known(candidate, known)), None)


def _path_candidates(module: str, importer: str, aliases: dict[str, list[str]] | None) -> list[str]:
    """A relative specifier joined to the importer's folder; any other as a path and as a dotted name."""
    candidates: list[str] = []
    if module.startswith("."):
        base = importer.rsplit("/", 1)[0] if "/" in importer else ""
        joined = os.path.normpath(os.path.join(base, module)).replace(os.sep, "/")
        candidates.append(joined)
        candidates += [joined + ext for ext in _MODULE_EXTENSIONS]
        candidates += [f"{joined}/{name}" for name in _PACKAGE_FILES]
        return candidates
    for spec in _expand_alias(module, aliases) + [module]:
        if "/" in spec:
            candidates += [spec] + [spec + ext for ext in _MODULE_EXTENSIONS]
            candidates += [f"{spec}/{name}" for name in _PACKAGE_FILES]
        dotted = spec.replace(".", "/")
        candidates += [dotted + ext for ext in _MODULE_EXTENSIONS]
        candidates += [f"{dotted}/{name}" for name in _PACKAGE_FILES]
    return candidates


def resolve_module(
    module: str,
    importer: str,
    known: dict[str, list[str]],
    aliases: dict[str, list[str]] | None = None,
) -> str | None:
    """Map an import specifier to a path in the snapshot, or None."""
    if not module:
        return None
    if importer.lower().endswith(_STYLESHEET_SUFFIXES):
        return _resolve_stylesheet(module, importer, known)
    if importer.lower().endswith(_C_FAMILY_SUFFIXES):
        return _include_target(module, importer, known)
    if not module.startswith(".") and importer.lower().endswith(".rs"):
        return _rust_target(module, importer, known)
    for candidate in _path_candidates(module, importer, aliases):
        hit = (candidate if _known(candidate, known) else None)
        if not module.startswith(".") and not importer.lower().endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
            hit = _lookup(candidate, known, importer)
        if hit:
            return hit
    return None


def build_import_index(manifest: dict, comparison: dict, symbols: dict) -> dict[str, list[str]]:
    """
    Reverse import edges over the CURRENT view of the tree: the manifest's
    imports for unchanged files, the fresh parse for added and modified ones.
    Removed files contribute no outgoing edges of their own, since a deleted
    file no longer imports anything.

    They still have to be resolvable AS TARGETS, though: a surviving,
    unchanged importer's own import list still names the module that used to
    point at the removed file, and that edge is exactly what a removed file's
    blast radius depends on. So the known set for resolution is the current
    tree plus every removed file's last-known path, while the set actually
    walked for outgoing edges stays the current tree only.
    """
    old_files = file_headers(manifest)
    fresh = symbols.get("fresh", {})
    current_imports: dict[str, list[str]] = {}
    for rel in comparison["unchanged"]:
        current_imports[rel] = list(old_files.get(rel, {}).get("imports", []))
    for rel, entry in fresh.items():
        current_imports[rel] = list(entry.get("imports", []))

    resolvable = list(current_imports) + [rel for rel in comparison["removed"] if rel not in current_imports]
    graph_manifest = {**header_metadata(manifest), "root": comparison.get("root") or manifest.get("root"),
                      "target": comparison.get("target") or manifest.get("target") or ".", "files": {
        rel: {**old_files.get(rel, {}), **fresh.get(rel, {}), "imports": current_imports.get(rel, [])}
        for rel in resolvable
    }}
    graph = module_targets(graph_manifest, include_self=True)
    index: dict[str, list[str]] = {}
    for importer in current_imports:
        for imported in graph[importer]:
            index.setdefault(imported, []).append(importer)
    return {key: sorted(value) for key, value in index.items()}


def blast_radius(index: dict[str, list[str]], comparison: dict, symbols: dict) -> list[dict]:
    """
    Files importing something that changed. One hop, never the transitive
    closure: on most codebases the closure is the whole tree, which is a full
    run wearing a different name.

    A modified file whose symbols all survived unchanged (lines shifted, a
    comment rewritten) puts nobody in the radius: an importer depends on what a
    module offers, not on where its lines sit. A removed file, and a modified
    file with no symbols at all, always do.
    """
    moved: set[str] = set()
    for state in ("added", "removed", "changed"):
        moved.update(item["file"] for item in symbols[state])
    structureless = {
        rel for rel in comparison["modified"]
        if not symbols.get("fresh", {}).get(rel, {}).get("symbols")
    }
    touched = (set(comparison["modified"]) & (moved | structureless)) | set(comparison["removed"])
    reverse: dict[str, list[str]] = {}
    for imported in touched:
        for importer in index.get(imported, []):
            if importer in touched:
                continue
            reverse.setdefault(importer, []).append(imported)
    return [{"file": key, "imports": sorted(value)} for key, value in sorted(reverse.items())]
