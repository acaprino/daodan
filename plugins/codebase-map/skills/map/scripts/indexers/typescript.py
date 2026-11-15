"""scip-typescript, for JavaScript and TypeScript: how it runs, and the aliases its index states its own way.

`index` runs scip-typescript (npm, without install scripts, on Daodan's Node) in a mirror of the project with
the engine pass's package install linked as `node_modules` (`npm_modules`: `npm ci --ignore-scripts`; a
project without a root `package.json` gets it in each outermost directory holding one) and a generated
tsconfig that holds every JS/TS file of the snapshot (`allowJs`) and extends the project's own, or without a
root `tsconfig.json` the one the pre-map names. One program has one `paths`: the generated tsconfig carries
the aliases every unit's tsconfig states and the name of each package another reaches by name (a workspace's
member, a unit's dependency) on its folder, so neither needs a link in `node_modules`. What the run lacks is
a gap of its contract (`gaps`): an install that failed, a package no install serves, a local dependency left
out of the install that no alias reaches, an alias two units give different targets. No project code runs.

`hops` reads the statement that defines a name: `a = b`, `k: b.c`, `exports.f = g` and `{ k: name } = …` lead
to the symbol the index references at the value or the key (CommonJS `module.exports = { f }` needs none: the
index states it as a shared range); a function value leads to the function the snapshot declares there. A
library function whose documented contract returns its argument is a declared hop, tagged
`declared:<package>.<function>`.
"""
from __future__ import annotations

import collections
import json
import subprocess
from pathlib import Path, PurePosixPath

import code_graph

VERSION = "0.5.2"  # @sourcegraph/scip-typescript on npm
# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-typescript", ("typescript", "javascript"), frozenset({"npm-package"}), False
MIN_FREE = 2304 * 2**20  # 2,264 MB peak on tududi (benchmarks/inference-audit, 13 November 2026)
SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
WORKSPACES = {"npm", "pnpm", "yarn", "lerna"}  # the pre-map's workspace tools whose members are packages
GRAMMARS = {".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "tsx", ".js": "javascript",
            ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript"}
PATTERNS = {"object_pattern", "array_pattern", "pair_pattern", "shorthand_property_identifier_pattern",
            "assignment_pattern", "object_assignment_pattern", "rest_pattern"}
PARAMETERS = {"formal_parameters", "required_parameter", "optional_parameter", "catch_clause"}
WRAPPERS = {"parenthesized_expression", "as_expression", "satisfies_expression", "non_null_expression",
            "type_assertion"}
FUNCTIONS = {"arrow_function", "function_expression", "function", "generator_function", "class"}
# Library functions whose documented contract returns their argument (`argument`) or what their argument, a
# function without a block body, returns (`result`); matched by the package and descriptors of the index.
DECLARED = {("@types/react", "/React/useCallback()."): "argument",
            ("@types/react", "/React/useMemo()."): "result"}


def _unwrap(node):
    while node is not None and node.type in WRAPPERS:
        node = node.named_children[0] if node.named_children else None
    return node


def _defining_value(node) -> tuple[str, object]:
    """(form, node) of the statement that defines the name at `node`: `pattern-key` with the key, `value` or
    `field` with the value, `parameter`, `destructured` (another element of a pattern) or `none`."""
    child, parent = node, node.parent
    if parent is not None and parent.type == "assignment_pattern" and parent.child_by_field_name("left") == node:
        child, parent = parent, parent.parent
    if parent is not None and parent.type == "pair_pattern" and parent.child_by_field_name("value") == child:
        return "pattern-key", parent.child_by_field_name("key")
    child, parent, destructured = node, node.parent, False
    while parent is not None and parent.type in PATTERNS:
        child, parent, destructured = parent, parent.parent, True
    if parent is None:
        return "none", None
    kind, field = parent.type, parent.child_by_field_name
    if kind in PARAMETERS or (kind == "arrow_function" and field("parameter") == child):
        return "parameter", None
    if kind == "variable_declarator" and field("name") == child:
        return ("destructured" if destructured else "value"), field("value")
    if kind == "pair" and field("key") == child:
        return "value", field("value")
    if kind in ("public_field_definition", "field_definition"):
        return "field", field("value")
    if kind == "member_expression" and field("property") == child and parent.parent is not None \
            and parent.parent.type == "assignment_expression" and parent.parent.child_by_field_name("left") == parent:
        return "value", parent.parent.child_by_field_name("right")
    return "none", None


def _value(index, rel: str, value, tag: str, function_tag: str = "value") -> list:
    """Where a value leads: a function's start, or the symbols the index references at a name."""
    value = _unwrap(value)
    if value is None:
        return []
    if value.type in FUNCTIONS:
        return [((rel, value.start_point[0] + 1, value.start_point[1]), function_tag)]
    if value.type in ("identifier", "member_expression"):
        name = value if value.type == "identifier" else value.child_by_field_name("property")
        return [(key, tag) for key in index.stated(rel, name)] if name is not None else []
    if value.type == "call_expression":
        return _declared(index, rel, value)
    return []


def _declared(index, rel: str, call) -> list:
    callee = _unwrap(call.child_by_field_name("function"))
    if callee is None:
        return []
    name = callee if callee.type == "identifier" else callee.child_by_field_name("property") \
        if callee.type == "member_expression" else None
    arguments = call.child_by_field_name("arguments")
    first = arguments.named_children[0] if arguments is not None and arguments.named_children else None
    if name is None or first is None:
        return []
    for key in index.stated(rel, name):
        parts = code_graph.split_symbol(key)
        for (package, suffix), contract in DECLARED.items():
            if not parts or parts[2] != package or not parts[4].endswith(suffix):
                continue
            tag = f"declared:{package}.{suffix.rsplit('/', 1)[-1][:-3]}"
            if contract == "argument":
                return _value(index, rel, first, tag, tag)
            first = _unwrap(first)
            body = first.child_by_field_name("body") if first is not None and first.type == "arrow_function" else None
            return _value(index, rel, body, tag, tag) if body is not None and body.type != "statement_block" else []
    return []


def hops(index) -> dict:
    """Alias edges from the statements that define the names of JS/TS documents."""
    out = collections.defaultdict(list)
    for rel, occurrences in index.documents.items():
        grammar = GRAMMARS.get(Path(rel).suffix.lower())
        if grammar is None:
            continue
        for occurrence in occurrences:
            # Types, methods, modules and parameters are declarations, never aliases.
            if not occurrence.definition or occurrence.key.endswith(("#", ").", "/", ")")):
                continue
            node = index.node(rel, occurrence, grammar)
            if node is None:
                continue
            form, value = _defining_value(node)
            if form == "pattern-key" and value is not None:
                found = [(key, "pattern-key") for key in index.stated(rel, value)]
            elif form in ("value", "field") and value is not None:
                found = _value(index, rel, value, "initializer")
            else:
                found = []
            out[occurrence.key] += [item for item in found if item[0] != occurrence.key]
    return {key: list(dict.fromkeys(items)) for key, items in out.items() if items}


def _aliases(paths, members: dict | None) -> tuple[dict, list[dict]]:
    """One program's `paths`, targets from the project's root: each unit's aliases in the units' order, then
    each reachable package's name on its folder. An alias two units give different targets keeps them all (the
    compiler takes the first that holds the file) and is a gap."""
    merged, owners = {}, collections.defaultdict(list)
    for root, stated in paths or ():
        for key, targets in stated.items():
            known = merged.setdefault(key, [])
            if any(target not in known for target in targets):
                owners[key].append(root)
            known += [target for target in targets if target not in known]
    gaps = [{"kind": "alias_ambiguous", "alias": key, "paths": roots,
             "detail": f"`{key}` has other targets in {', '.join(roots)}: one program holds one mapping, so an "
                       "import through it resolves to the first target that holds the file"}
            for key, roots in owners.items() if len(roots) > 1]
    for name, folder in sorted((members or {}).items()):
        for key, target in ((name, folder), (f"{name}/*", f"{folder}/*")):
            if target not in merged.setdefault(key, []):
                merged[key].append(target)
    return merged, gaps


def _tsconfig(mirror: Path, files: list[str], base: str | None = None, aliases: dict | None = None) -> str | None:
    """Every JS/TS file of the snapshot in one program with `allowJs`; the project's own options kept;
    `aliases` as its `paths`, absolute in the mirror (an inherited `baseUrl` would move a relative target)."""
    options = {"allowJs": True, "checkJs": False, "noEmit": True, "incremental": False, "skipLibCheck": True}
    if aliases:
        options["paths"] = {key: [(mirror / target).as_posix() for target in targets]
                            for key, targets in aliases.items()}
    config = {"compilerOptions": options, "include": files, "exclude": []}
    own = mirror / "tsconfig.json"
    if own.is_file():
        own.rename(mirror / "tsconfig.project.json")
        config["extends"] = "./tsconfig.project.json"
    elif base and (mirror / base).is_file():
        config["extends"] = f"./{base}"
    else:
        options.update({"target": "es2022", "module": "esnext", "moduleResolution": "bundler", "jsx": "preserve",
                        "esModuleInterop": True, "allowSyntheticDefaultImports": True, "resolveJsonModule": True})
    own.write_text(json.dumps(config, indent=1), encoding="utf-8")
    return config.get("extends")


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: the folders it runs in (`roots`); the tsconfig a root without one
    extends (`tsconfig`: the root unit's first, else the only unit's that states one, since a program extends
    one); each unit's aliases (`paths`, with its folder, the root's first); and the folder of each package
    another reaches by name (`members`): a workspace's member, or one a unit depends on."""
    import premap
    units = sorted(record.get("units", []), key=lambda unit: (unit["root"] != ".", unit["root"]))
    stated = [unit for unit in units if (unit.get("config") or {}).get("tsconfig")]
    packages = [unit for unit in units if unit["kind"] in UNIT_KINDS and unit.get("name")]
    reached = {member for workspace in record.get("workspace", []) if workspace.get("tool") in WORKSPACES
               for member in workspace.get("members") or ()}
    named = {name for unit in packages for name in unit.get("depends_on") or ()}
    found = {"roots": premap.roots(record, UNIT_KINDS, WORKSPACES),
             "tsconfig": stated[0]["config"]["tsconfig"][0]
             if stated and (stated[0]["root"] == "." or len(stated) == 1) else None,
             "paths": [[unit["root"], unit["config"]["paths"]] for unit in units
                       if (unit.get("config") or {}).get("paths")],
             "members": {unit["name"]: unit["root"] for unit in packages
                         if unit["root"] in reached or unit["name"] in named}}
    return {key: value for key, value in found.items() if value or key == "roots"}


def _package_roots(roots: set[str]) -> list[str]:
    """'' when the project's root is a package, else each outermost folder that is one."""
    if "" in roots:
        return [""]
    return [root for root in sorted(roots) if not any(root.startswith(f"{other}/") for other in roots)]


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, tsconfig: str | None = None, *,
          roots: set[str], paths=(), members: dict | None = None) -> dict:
    """The scip-typescript index of `project_dir` for `files` (default: every JS/TS file outside
    `node_modules`), `tsconfig` the configuration a root without one extends, `roots` the folders of its packages,
    `paths` the aliases of its units and `members` the folders of the packages reached by name, all as the
    pre-map names them (`structure`); see the module's docstring."""
    import engine_tools
    import resolve_edges as rx
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    tool = runtime.Tool(project_dir, "scip-typescript", VERSION, skip=(".git", "node_modules"))
    try:
        runtime.memory("scip-typescript", MIN_FREE)
        directory = runtime.node(project_dir)
        script = runtime.npm_package(project_dir, directory, "@sourcegraph/scip-typescript", VERSION)
        packages, roots = set(roots), _package_roots(set(roots))
        for root in roots:
            key = rx.npm_key(project_dir / root)
            if key and not (rx.shared_cache_dir() / "npm" / key / "daodan-modules.json").is_file():
                runtime.room()
    except runtime.Unavailable as error:
        return runtime.refused("scip-typescript", VERSION, error)
    installs, links, served = {}, {}, set()
    aliases, gaps = _aliases(paths, members)
    for root in roots:
        failed = []
        try:
            with runtime.on_path(directory):
                modules = rx.npm_modules(project_dir / root, failed)  # the engine pass's own: npm ci --ignore-scripts
        except (OSError, subprocess.SubprocessError) as error:
            modules, failed = None, [str(error)]
        gaps += [{"kind": "restore_failed", "manager": "npm", "path": root or ".", "detail": reason[:600]}
                 for reason in failed]
        installs[root] = str(modules) if modules else None
        manifests = rx.npm_manifests(project_dir / root)
        served |= {manifest.parent.relative_to(project_dir).as_posix() for manifest in manifests}
        for manifest in manifests if modules is not None else ():
            installed = modules.parent / manifest.parent.relative_to(project_dir / root) / "node_modules"
            if installed.is_dir():
                relative = manifest.parent.relative_to(project_dir).as_posix()
                links[(PurePosixPath(relative) / "node_modules").as_posix()] = installed
        gaps += [{"kind": "dependency_not_installed", "manager": "npm",
                  "path": (PurePosixPath(root) / manifest).as_posix(),
                  "detail": f"{name} ({spec}): a local package, left out of the install, that no alias reaches"}
                 for manifest, name, spec in engine_tools.npm_local_packages(project_dir / root)
                 if name not in (members or {})]
    # A package under an install's root that its `workspaces` do not name: npm installs nothing for it.
    gaps += [{"kind": "restore_failed", "manager": "npm", "path": root,
              "detail": "its packages are not installed: the `workspaces` of no package.json above name this folder"}
             for root in sorted(packages - set(roots) - served) if (project_dir / root / "package.json").is_file()]
    if files is None:
        files = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*")
                       if path.suffix in SUFFIXES and "node_modules" not in path.relative_to(project_dir).parts)
    output = work_dir / "scip-typescript-0.scip"
    runtime.clear(work_dir, "scip-typescript")
    env = runtime.environment(directory, NODE_OPTIONS="--max-old-space-size=12288")
    with runtime.mirrored(tool, links) as mirror:
        extends = _tsconfig(mirror, [rel for rel in files if rel.endswith(SUFFIXES)], tsconfig, aliases)
        run = {"prefix": "", **code_graph.measured(
            [str(directory / rx.executable_name("node")), str(script), "index", "--cwd", str(mirror), "--output",
             str(output), "--no-progress-bar"], str(mirror), env, 3 * 3600)}
    run["index"] = str(output) if output.is_file() else None
    run["index_bytes"] = output.stat().st_size if output.is_file() else 0
    return {**runtime.outcome("scip-typescript", VERSION, [run]), "node_modules": installs,
            "tsconfig_extends": extends, **({"gaps": gaps} if gaps else {})}
