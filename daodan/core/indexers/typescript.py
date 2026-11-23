"""scip-typescript, for JavaScript and TypeScript: how it runs, and the aliases its index states its own way.

`index` is one container run over a copy of the project (`container.run_in_container`, spec
`docs/specs/2026-11-12-passo-dinamico.md`, sections 2-4), never on the host: without a container the languages
are `unavailable`, with the gap's cause and remedy.

- Preparation, on a network that reaches only npm's registry (`preparation.NODE_REGISTRIES`), the hosts a
  manager names and, for a Node the pre-map states at an exact version, mise's: Daodan's Node
  (`preparation.NEEDS`), scip-typescript from npm without its install scripts, the stated Node (`mise`,
  `preparation.toolchains`), then the project's own restore (`preparation.node_prepare`): in each package folder
  the pre-map names that no other holds, and in each with a lockfile of its own, with the manager the lockfile
  names, else the one its manifest names (`packageManager`, through corepack), else npm; a Yarn project on
  Plug'n'Play is laid out in node_modules, which TypeScript's resolver reads (`_prepared`, a `build_edited` gap
  says so). The install runs with
  its lifecycle scripts, as a CI's does: there a framework generates what the compiler reads (SvelteKit's
  `.svelte-kit/tsconfig.json`, Nuxt's `.nuxt`). They are project code, which may run in the preparation and
  stays in the container (spec, section 4); an install they break is done again without them. Last, the type
  packages the project lacks (`typescript_types.py`): `@types/node` at the major of the Node the project runs on,
  and `@types/<package>` for a declared package that ships no types, each installed apart and linked where
  TypeScript looks last, Node's named in a file the generated tsconfig includes (`REFERENCES`); the indexer's
  record lists those added (`types`). Where a tsconfig of the project extends a file a framework generates
  (`GENERATORS`: SvelteKit's `svelte-kit sync` writes `.svelte-kit/tsconfig.json` and the generated types,
  svelte.dev/docs/kit/cli), the project's installed command writes it (`generator`), after the restore, whatever
  its lifecycle scripts run; the record lists what it wrote with the version (`generated`). With Vue components,
  Daodan's pin of Vue's tool, which a project without its own needs (`components.PIN`).
- Execution, with no network: scip-typescript on Daodan's Node (0.6.2 needs Node 22.23.4 or later, whatever the
  project runs on), with a generated tsconfig in place of the project's: it holds every JS/TS file of the
  snapshot (`allowJs`) and extends the project's own, or without a root `tsconfig.json` the one the pre-map
  names. One program has one `paths`: the generated tsconfig carries the aliases every unit's tsconfig states
  and the name of each package another reaches by name (a workspace's member, a unit's dependency) on its
  folder. The program holds the Vue and Svelte components too (`indexers/components.py`): a Svelte one
  scip-typescript turns into TypeScript itself, a Vue one is first turned by Vue's own tool, in a generated file
  beside it whose index `components.rewrite` gives back to it; the record names each tool, its version and whose
  (`frameworks`), `missing` why a component has no document. Then the checker's pass over the same program
  (`typescript_unbound.js`): the members it binds no declaration to, where the index has no occurrence, and why
  (`unanswered`). Both come back as the run's output.

What the run lacks is a gap of its contract (`gaps`): a restore that failed (`preparation.restore_gaps`), an
install whose lifecycle scripts failed (`preparation.generation_gaps`), a Node the preparation could not install,
a package folder no restore serves, an alias two units give different targets, a tsconfig that extends a file no
install step generated (`_not_generated`).

`hops` reads the statement that defines a name: `a = b`, `k: b.c`, `exports.f = g` and `{ k: name } = …` lead
to the symbol the index references at the value or the key (CommonJS `module.exports = { f }` needs none: the
index states it as a shared range); a function value leads to the function the snapshot declares there. A
library function whose documented contract returns its argument is a declared hop, tagged
`declared:<package>.<function>`. scip-typescript names a member of an anonymous type, an object literal or an
index signature another file declares with a local of the file that reads it, defined nowhere: no hop or shared
range leads there (`same_range`), and the name bound to it ends at its own definition. A name an import binds to
a module's default export, which the index names so when the export is an expression (a Vue component's), leads to
the module where the index defines it (`_default_import`). `classify` names why such a local is a dead end: a
member (`MEMBER`), or a name an import of a module TypeScript does not read binds (a component it resolves to no
file, or to a module the index defines nowhere); it ends `module`, which the index names with such a local, on
Node's module object. `unanswered` names why a member's site has no occurrence: the checker's pass says it.
"""
from __future__ import annotations

import collections
import json
import os
import posixpath
import re
import shlex
import shutil
from pathlib import Path

import code_graph
import preparation
from indexers import components

# @sourcegraph/scip-typescript on npm. From 0.6.1 a package.json without a name no longer ends the search for a
# file's package (sourcegraph/scip-typescript#527): before, a package's files below one (`24/outline/` of
# @heroicons/react, a `dist/cjs/` of `{"type": "commonjs"}`) were the anonymous package's, defined nowhere.
VERSION = "0.6.2"
# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
NAME, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = ("scip-typescript", ("typescript", "javascript", "vue", "svelte"),
                                                 frozenset({"npm-package"}), True)
# The container's memory: on the host the run peaked at 2,264 MB on tududi (benchmarks/inference-audit, 13 November
# 2026)
MIN_FREE = 3 * 2**30
IMAGE = "buildpack-deps:noble@sha256:890e8b5c0040e1deff5cc7dc7b4414e67069f79e3301afc4ec5bd49d64ef13e5"  # git, for
# a package a manifest takes from a repository (`indexers/clang.py` IMAGE)
WORK, OUT = "/work", "/daodan/out"  # the copy (`container.WORKDIR`), and where the index is brought back from
CONFIG = f"{preparation.STATE}/scip-typescript/tsconfig.json"  # the generated tsconfig, carried with the copy
TYPES = f"{preparation.STATE}/scip-typescript/typescript_types.py"  # carried with the copy; installs into `TYPES_DIR`
UNBOUND = f"{preparation.STATE}/scip-typescript/typescript_unbound.js"  # carried with the copy; the checker's pass
TYPES_DIR = f"{preparation.STATE}/types"
REFERENCES = f"{TYPES_DIR}/references.d.ts"  # where it names the type packages the program loads (Node's)
# A folder a framework generates its tsconfig in -> the command that writes it; the scripts an install runs.
GENERATORS = {".svelte-kit": "svelte-kit sync"}
GENERATED = re.compile(r"DAODAN-GENERATED (\S+) (\S+) (.+)")  # what `generator` prints: folder, version, command
INDEXER = f"{preparation.T}/npm/lib/node_modules/@sourcegraph/scip-typescript"  # the package npm installs
LIFECYCLE = ("preinstall", "install", "postinstall", "prepare")
UNREAD = re.compile(r"error TS5083: Cannot read file '/work/([^']+)'")
NODE_TYPES = "scip-typescript npm @types/node "  # the symbols of the Node types, before their version
# A member name's nodes, and the cause of one the index names with a local it defines nowhere (`classify`).
MEMBERS = ("property_identifier", "private_property_identifier", "shorthand_property_identifier_pattern")
MEMBER = ("a member of an anonymous type, an object literal or an index signature another file declares: the index "
          "names it with a local of this file it defines nowhere")
# Why the checker binds no declaration to a member (`typescript_unbound.js`), by its kind, with the receiver's type.
UNBOUND_CAUSES = {"any": "a member of a value of type any: only execution knows it",
                  "index": "{}'s index signature: only execution knows the value",
                  "mapped": "{}'s member has no declaration, the checker made it: the index names nothing there",
                  "undeclared": "{} declares no such member: only execution knows it"}
T = preparation.T
MANAGERS = ("npm", "pnpm", "yarn")  # the Node managers of `preparation.RESTORES`
PEAK = "trap 'echo \"DAODAN_PEAK $(cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo -)\"' EXIT"
# The preparation: Daodan's Node, the indexer (before a stated Node is first on the path), `{chains}`, `{restores}`,
# the framework's `{generators}`, `{types}`, then the components' tools (`{frameworks}`).
PREPARE = f'''set -u
{PEAK}
mkdir -p {T}/bin "$HOME"
{{node}}
{{{{ npm install -g --prefix {T}/npm --ignore-scripts --no-audit --no-fund --loglevel=error\
 @sourcegraph/scip-typescript@{VERSION} ; }}}} >&2
[ -e {T}/npm/bin/scip-typescript ] || {{{{ echo 'DAODAN-MISSING scip-typescript@{VERSION}' >&2; exit 70; }}}}
{{chains}}
cd {WORK} || exit 70
{{restores}}
{{generators}}
{{types}}
{{frameworks}}
exit 0
'''
# The execution: the generated tsconfig in place of the project's, the Vue components' TypeScript
# (`{components}`), the indexer on Daodan's Node, `{heap}` MB.
EXECUTE = f'''set -u
{PEAK}
mkdir -p {OUT}
cd {WORK} || exit 70
if [ -f tsconfig.json ]; then mv tsconfig.json tsconfig.project.json || exit 70; fi
cp {CONFIG} tsconfig.json || exit 70
{{components}}
NODE_OPTIONS=--max-old-space-size={{heap}} {T}/node/bin/node "$(readlink -f {T}/npm/bin/scip-typescript)" index\
 --cwd {WORK} --output {OUT}/index.scip --no-progress-bar
indexed=$?
NODE_OPTIONS=--max-old-space-size={{heap}} {T}/node/bin/node {UNBOUND} {WORK}\
 "$(readlink -f {T}/npm/bin/scip-typescript)" > {OUT}/unbound.jsonl
exit "$indexed"
'''
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


def _unnamed(index, key) -> bool:
    """Whether a key is a local the index defines nowhere: a member of an anonymous type, an object literal or an
    index signature another file declares, which scip-typescript names with a local of the file that reads it."""
    return isinstance(key, str) and "#local " in key and not index.defs.get(key)


def _default_import(index, rel: str, occurrence, grammar: str) -> list:
    """The module an import binds a name to the default export of, when the index defines it and references the
    name with a local it defines nowhere: scip-typescript names so the import of an expression's export (Vue's
    generated `export default {} as typeof __VLS_export;`)."""
    node = index.node(rel, occurrence, grammar)
    clause = node.parent if node is not None and node.type == "identifier" else None
    statement = clause.parent if clause is not None and clause.type == "import_clause" else None
    source = statement.child_by_field_name("source") if statement is not None \
        and statement.type == "import_statement" else None
    return [] if source is None else [(key, "import") for key in index.stated(rel, source)
                                      if key.endswith("/") and index.defs.get(key)]


def hops(index) -> dict:
    """Alias edges from the statements that define the names of JS/TS documents; none to a local the index
    defines nowhere (`_unnamed`), where an alias leads nowhere: the name ends at its own definition. Such a local
    an import binds to a module's default export leads to the module (`_default_import`)."""
    out = collections.defaultdict(list)
    for rel, occurrences in index.documents.items():
        grammar = GRAMMARS.get(Path(rel).suffix.lower())
        if grammar is None:
            continue
        for occurrence in occurrences:
            if not occurrence.definition and _unnamed(index, occurrence.key):
                out[occurrence.key] += _default_import(index, rel, occurrence, grammar)
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
            out[occurrence.key] += [item for item in found if item[0] != occurrence.key
                                    and not _unnamed(index, item[0])]
    return {key: list(dict.fromkeys(items)) for key, items in out.items() if items}


def same_range(index) -> dict:
    """A definition that shares its range with a local the index defines nowhere (the key of `{ t } = …`, a member
    of the value's type) is no alias of it: the name ends at its own definition."""
    pairs = {}
    for items in index.at.values():
        for item in items:
            if not item.definition and _unnamed(index, item.key):
                pairs.update({(other.key, item.key): False for other in items if other.definition
                              and (other.end_line, other.end) == (item.end_line, item.end)})
    return pairs


def _imported(root, name: str):
    """The source (a string node) of the import statement of the document that binds `name`, None when none does."""
    for statement in root.named_children:
        source = statement.child_by_field_name("source") if statement.type == "import_statement" else None
        clause = next((child for child in statement.named_children if child.type == "import_clause"), None)
        if source is None or clause is None:
            continue
        stack = [clause]
        while stack:
            node = stack.pop()
            if node.type == "identifier" and node.text.decode("utf-8", errors="replace") == name and (
                    node.parent.type != "import_specifier" or node == node.parent.named_children[-1]):
                return source
            stack += node.named_children
    return None


def classify(index):
    """The cause of a local the index defines nowhere. A member, of an anonymous type, an object literal or an
    index signature another file declares, which the index names with such a local, ends on that (`MEMBER`).
    One bound by an import of a module whose extension TypeScript does not read (a `.vue` or `.svelte`
    component) ends on why, where no hop leads to the module (`_default_import`): TypeScript resolves the import
    to no file (no generated TypeScript of the component, no declaration of such modules), or to a module the
    index defines nowhere. `module`, which TypeScript reads in
    a JavaScript file as the file's own module (`module.exports = …`, `require.main === module`) and the index
    names with such a local, is Node's module object: external, of the Node types that declare it with
    `require`, at the version the index references (`NODE_TYPES`), else a dead end that says none is referenced.
    Any other key keeps the default rule."""
    causes, objects, versions = {}, set(), collections.Counter()
    for rel, occurrences in index.documents.items():
        grammar = GRAMMARS.get(Path(rel).suffix.lower())
        for occurrence in occurrences if grammar else ():
            if occurrence.key.startswith(NODE_TYPES):
                versions[occurrence.key.split(" ")[3]] += 1
            if not occurrence.key.startswith(f"{rel}#local ") or index.defs.get(occurrence.key) \
                    or occurrence.key in causes or occurrence.key in objects:
                continue
            node = index.node(rel, occurrence, grammar)
            if node is not None and node.type in MEMBERS:
                causes[occurrence.key] = MEMBER
                continue
            if node is None or node.type != "identifier":
                continue
            if node.text == b"module":
                objects.add(occurrence.key)
                continue
            root = node
            while root.parent is not None:
                root = root.parent
            source = _imported(root, node.text.decode("utf-8", errors="replace"))
            module = source.text.decode("utf-8", errors="replace").strip("'\"") if source is not None else ""
            suffix = posixpath.splitext(module)[1]
            if suffix and suffix not in (*SUFFIXES, ".json"):
                causes[occurrence.key] = (
                    "the import resolves to a module the index defines nowhere"
                    if any(key.endswith("/") for key in index.stated(rel, source)) else
                    f"TypeScript resolves the import to no file and finds no declaration of *{suffix} modules")
    declared = {"manager": "npm", "package": "@types/node", "version": versions.most_common(1)[0][0]} if versions \
        else "module.exports: the index names `module` with a local it defines nowhere, and references no Node " \
             "types that declare it"
    causes.update(dict.fromkeys(objects, declared))
    return causes.get


def unanswered(index):
    """Why the index has no occurrence at a member's site: the checker's pass in the container binds no
    declaration there, and says why (`UNBOUND_CAUSES`), in the file beside the index (`<index>.unbound.jsonl`)."""
    causes = {}
    for path, prefix in index.sources:
        side = path.with_suffix(".unbound.jsonl")
        for line in side.read_text(encoding="utf-8").splitlines() if side.is_file() else ():
            try:
                rel, row, column, kind, receiver = json.loads(line)
                causes[(posixpath.join(prefix, rel) if prefix else rel, row, column)] = \
                    UNBOUND_CAUSES[kind].format(receiver)
            except (ValueError, KeyError, TypeError):  # a line the pass cut short says nothing
                continue
    return causes.get


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


def _tsconfig(project: Path, target: Path, files: list[str], base: str | None = None,
              aliases: dict | None = None) -> str | None:
    """The tsconfig the run puts at the copy's root, written to `target`: every JS/TS file of the snapshot in one
    program with `allowJs`; the project's own options kept (its root `tsconfig.json`, which the run renames);
    `aliases` as its `paths`, absolute in the copy (an inherited `baseUrl` would move a relative target)."""
    options = {"allowJs": True, "checkJs": False, "noEmit": True, "incremental": False, "skipLibCheck": True}
    if aliases:
        options["paths"] = {key: [f"{WORK}/{name}" for name in targets] for key, targets in aliases.items()}
    config = {"compilerOptions": options, "include": [*files, REFERENCES], "exclude": []}
    if (project / "tsconfig.json").is_file():
        config["extends"] = "./tsconfig.project.json"
    elif base and (project / base).is_file():
        config["extends"] = f"./{base}"
    else:
        options.update({"target": "es2022", "module": "esnext", "moduleResolution": "bundler", "jsx": "preserve",
                        "esModuleInterop": True, "allowSyntheticDefaultImports": True, "resolveJsonModule": True})
    target.write_text(json.dumps(config, indent=1), encoding="utf-8")
    return config.get("extends")


def _extending(project_dir: Path):
    """Each tsconfig of the project outside `node_modules` with the file it extends: `(its path, the folder that
    holds it, the extended file from the project's root, the command that generates that one or None)`."""
    for config in sorted(project_dir.rglob("tsconfig*.json")):
        here = config.relative_to(project_dir).as_posix()
        if "node_modules" in here.split("/"):
            continue
        extended = re.search(r'"extends"\s*:\s*"([^"]+)"', config.read_text(encoding="utf-8", errors="replace"))
        if extended:
            folder = posixpath.dirname(here) or "."
            yield (here, folder, posixpath.normpath(posixpath.join(folder, extended.group(1))),
                   GENERATORS.get(posixpath.normpath(extended.group(1)).split("/")[0]))


def generator(folder: str, command: str) -> str:
    """The preparation's line running the project's own `command` (`svelte-kit sync`) in `folder`, its binary the
    one the restore installed (`npx --no` installs none; after `--` npm reads no flag of the command's, its
    `--version` the first): `DAODAN-GENERATED folder version command` on stderr when it wrote, else its failure as
    `preparation.generation_gaps` reads one."""
    binary, rest = command.split(" ", 1)
    log, path = preparation.LOG, shlex.quote(posixpath.normpath(f"{WORK}/{folder}"))
    return (f"( cd {path} && v=$(npx --no -- {binary} --version 2>/dev/null | tail -n 1)"
            f" && {{ [ -n \"$v\" ] || {{ echo 'the project installs no {binary} here' > {log}; false; }}; }}"
            f" && npx --no -- {command} > {log} 2>&1 && echo \"DAODAN-GENERATED {folder} ${{v##* }} {command}\" >&2 )"
            f" || {{ printf 'DAODAN-GENERATE-FAILED {binary} %s\\n' {shlex.quote(folder)};"
            f" {{ grep -Ei 'error' {log} || tail -n 30 {log}; }} | head -n 30; echo DAODAN-GENERATE-END; }} >&2")


def _not_generated(project_dir: Path, said: str, ran=frozenset()) -> list[dict]:
    """A `config_not_generated` gap for each file a tsconfig of the project extends that TypeScript could not read
    in the run (`said`, its output: TS5083): a file the framework generates (`GENERATORS`) that the preparation's
    run of its command in that folder (`ran`) did not write, or that no lifecycle script of the package runs,
    with the scripts that do, or else a file no install step wrote."""
    gaps = []
    for rel in dict.fromkeys(UNREAD.findall(said)):
        for here, folder, extended, command in _extending(project_dir):
            if extended != rel:
                continue
            if command and folder in ran:
                gaps.append({"kind": "config_not_generated", "path": here, "file": rel,
                             "detail": f"{here} extends {rel}, which `{command}` did not write in the preparation"})
                continue
            package = (project_dir / here).parent
            while package != project_dir and not (package / "package.json").is_file():
                package = package.parent
            try:
                scripts = json.loads((package / "package.json").read_text(encoding="utf-8")).get("scripts") or {}
            except (OSError, ValueError, AttributeError):
                scripts = {}
            named = [name for name, line in scripts.items() if command and command in str(line)]
            if command and any(name in LIFECYCLE for name in named):
                continue  # its install runs it: a failure is the generation's own gap
            detail = (f"{here} extends {rel}, a file the framework generates (`{command}`), which no install step of "
                      f"the project runs (no `prepare` script"
                      + (f"; it is only in {', '.join(f'`{name}`' for name in named)})" if named else ")")
                      if command else f"{here} extends {rel}, which the snapshot does not hold and no install step wrote")
            gaps.append({"kind": "config_not_generated", "path": here, "file": rel, "detail": detail})
    return gaps


def tasks(configs) -> dict:
    """What the run brought back for `missing`: `{"components": {rel: {tool, error}}}`, empty without it."""
    return configs if isinstance(configs, dict) else {}


def missing(index, rels: list[str], configs: dict | None = None) -> dict:
    """Why a file has no document: a component, the tool that could not turn it into TypeScript and its error; a
    `.d.ts` beside a `.ts` or `.tsx` of its name, TypeScript's own rule, which keeps the latter where an `include`
    matches both."""
    reasons = {}
    for rel in rels:
        entry = ((configs or {}).get("components") or {}).get(rel) or {}
        sibling = next((rel[:-len(".d.ts")] + suffix for suffix in (".ts", ".tsx")
                        if rel.endswith(".d.ts") and rel[:-len(".d.ts")] + suffix in index.documents), None)
        if entry.get("error"):
            reasons[rel] = (f"{entry['tool']} could not turn it into TypeScript: {entry['error']}" if entry.get("tool")
                            else entry["error"])
        elif sibling:
            reasons[rel] = (f"TypeScript leaves it out of the program: {sibling.rsplit('/', 1)[-1]} beside it has its "
                            "name, and an `include` that matches both keeps that one")
    return reasons


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: the folders it runs in (`roots`); the tsconfig a root without one
    extends (`tsconfig`: the root unit's first, else the only unit's that states one, since a program extends
    one); each unit's aliases (`paths`, with its folder, the root's first); the folder of each package
    another reaches by name (`members`): a workspace's member, or one a unit depends on; and the Node it states
    (`toolchains`)."""
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
                         if unit["root"] in reached or unit["name"] in named},
             "toolchains": [item for item in record.get("toolchains", []) if item.get("tool") == "node"]}
    return {key: value for key, value in found.items() if value or key == "roots"}


def _prepared(project_dir: Path, roots) -> dict:
    """The restores of the package folders the pre-map names (`preparation.node_prepare`), from the manifest, the
    lockfile and the pnpm workspace beside each."""
    names = ("package.json", "package-lock.json", "npm-shrinkwrap.json", "pnpm-workspace.yaml",
             *(lock for manager in MANAGERS for lock in preparation.RESTORES[manager].get("locks", ())))
    files = [posixpath.join(root, name) for root in sorted(roots) for name in names
             if (project_dir / root / name).is_file()]
    restored = preparation.node_prepare(files, lambda rel: (project_dir / rel).read_text(encoding="utf-8",
                                                                                       errors="replace"))
    return node_modules(project_dir, restored, "TypeScript's resolver reads no .pnp.cjs")


def node_modules(project_dir: Path, restored: dict, why: str) -> dict:
    """`restored` (`preparation.node_prepare`) with each Yarn folder on Plug'n'Play laid out in node_modules. Yarn 2
    and later use Plug'n'Play unless .yarnrc.yml says otherwise, and what reads the packages here reads no
    .pnp.cjs (`why`): the index's restore lays the same lockfile out in node_modules, in the container's copy only,
    and a `build_edited` gap per folder says so. The dynamic step keeps the project's own linker."""
    plug = [folder for folder in restored["restores"].get("yarn", ())
            if (project_dir / folder / ".yarnrc.yml").is_file() and not re.search(
                r"(?m)^\s*nodeLinker:\s*[\"']?(node-modules|pnpm)",
                (project_dir / folder / ".yarnrc.yml").read_text(encoding="utf-8", errors="replace"))]
    if not plug:
        return restored
    return {**restored, "lines": [f"export YARN_NODE_LINKER=node-modules; {line}" if "corepack yarn" in line else line
                                  for line in restored["lines"]],
            "gaps": [*restored["gaps"], *({"kind": "build_edited", "path": folder, "detail": (
                "Yarn's Plug'n'Play (.yarnrc.yml sets no nodeLinker, or pnp): the index's restore lays the same "
                f"lockfile out in node_modules (YARN_NODE_LINKER=node-modules) in the container's copy, as {why}")}
                for folder in plug)]}


def _runs(out_dir: Path, cause: str | None) -> list[dict]:
    """A run per phase the container's record holds, with its log's tail, `ERROR` lines and memory peak; the
    operation's `cause` leads the last one's tail."""
    record = out_dir / "container-runs.jsonl"  # `container.RECORD_NAME`
    rows = [json.loads(line) for line in record.read_text(encoding="utf-8").splitlines()
            if line.strip()] if record.is_file() else []
    runs = []
    for row in rows:
        log = out_dir / f"{row.get('phase')}.log"
        text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
        peak = re.findall(r"DAODAN_PEAK (\d+)", text)
        errors = [line[line.find(" ERROR ") + 7:][:200] for line in text.splitlines() if " ERROR " in line]
        runs.append({"prefix": "", "phase": row.get("phase"), "returncode": row.get("exit_code"),
                     "seconds": row.get("duration_seconds", 0), "image": IMAGE,
                     "peak_mb": round(int(peak[-1]) / 2**20) if peak else None, "stdout_tail": "",
                     "stderr_tail": text[-2500:], "stderr_errors": len(errors),
                     "stderr_error_examples": list(dict.fromkeys(errors))[:5]})
    if runs and cause:
        runs[-1]["stderr_tail"] = f"{cause}\n{runs[-1]['stderr_tail']}"
    return runs


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, tsconfig: str | None = None, *,
          roots: set[str], paths=(), members: dict | None = None, toolchains=(), engine=None,
          memory: int = MIN_FREE, declared: dict | None = None) -> dict:
    """The scip-typescript index of `project_dir` for `files` (default: every JS/TS file outside
    `node_modules`), `tsconfig` the configuration a root without one extends, `roots` the folders of its packages,
    `paths` the aliases of its units, `members` the folders of the packages reached by name and `toolchains` the
    Node it states, all as the pre-map names them (`structure`); `engine` and `memory` are the container's. See
    the module's docstring."""
    import container
    import node_preparation
    from indexers import runtime
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    runtime.clear(work_dir, "scip-typescript")
    aliases, gaps = _aliases(paths, members)
    restored = _prepared(project_dir, roots)
    plan = restored["restores"]
    # A package another reaches by name (a member, a `file:` dependency) is installed by the restore that reaches it.
    reached = set((members or {}).values())
    gaps += [gap for gap in restored["gaps"] if gap["path"] not in reached]
    # The project runs on the Node it states at an exact version (mise), else on Daodan's: its `@types/node`.
    stated = [item for item in toolchains if item.get("tool") == "node"
              and preparation.EXACT.match(str(item.get("version") or ""))]
    chains = preparation.toolchains(stated)
    major = str(stated[0]["version"] if stated else preparation.NEEDS["node"]["version"]).lstrip("v").split(".")[0]
    types = " ".join(["python3", TYPES, WORK, major, TYPES_DIR, *(shlex.quote(root or ".") for root in sorted(roots))])
    found = sorted(path.relative_to(project_dir).as_posix() for path in project_dir.rglob("*")
                   if path.suffix in (*SUFFIXES, *components.SUFFIXES)
                   and "node_modules" not in path.relative_to(project_dir).parts)
    files = [rel for rel in found if rel.endswith(SUFFIXES)] if files is None else files
    parts = components.listed(project_dir, [rel for rel in found if rel.endswith(tuple(components.SUFFIXES))])
    plan_file = work_dir / "components.json"
    plan_file.write_text(json.dumps(parts), encoding="utf-8")
    config = work_dir / "tsconfig.generated.json"
    extends = _tsconfig(project_dir, config, [*(rel for rel in files if rel.endswith(SUFFIXES)),
                                              *components.include(parts)], tsconfig, aliases)
    generators = sorted({(folder, command) for _here, folder, _file, command in _extending(project_dir) if command})
    restore_lines, shared = node_preparation.options(restored, stated, (declared or {}).get("hosts", ()))
    prepare = PREPARE.format(node="\n".join(preparation.setup(["node"])["lines"]), chains="\n".join(chains["lines"]),
                             restores="\n".join(restore_lines), types=types,
                             generators="\n".join(generator(folder, command) for folder, command in generators),
                             frameworks="\n".join(components.install(parts)))
    out_dir = work_dir / "container"
    shutil.rmtree(out_dir, ignore_errors=True)
    execute = EXECUTE.format(heap=memory * 4 // 5 // 2**20,
                             components=components.generate(WORK, INDEXER) if parts else "")
    result = container.run_in_container(
        project_dir, ["bash", "-c", execute], image=IMAGE, out_dir=out_dir,
        prepare=["bash", "-c", prepare], outputs=[OUT], env={**preparation.ENV, "TERM": "dumb"}, timeout=3 * 3600,
        prepare_timeout=3600, memory=memory, engine=engine, **shared,
        registries=tuple(dict.fromkeys([*preparation.NODE_REGISTRIES, *restored["hosts"], *chains["hosts"],
                                        *(declared or {}).get("hosts", ())])),
        inputs=lambda: {CONFIG: config, TYPES: Path(__file__).with_name("typescript_types.py"),
                        UNBOUND: Path(__file__).with_name("typescript_unbound.js"),
                        **({components.LIST: plan_file, components.SCRIPT: Path(__file__).with_name("components.cjs")}
                           if parts else {}),
                        **{f"{preparation.IN}/{name}": preparation.fetched(url, digest, name)
                           for url, digest, name in (preparation.NODE, *chains["files"])}})
    if result["state"] == "gap":
        return runtime.refused("scip-typescript", VERSION, runtime.Unavailable(result["cause"], result["remedy"]))
    cut = "cut off at its time limit" if result["state"] == "timeout" else None
    runs = _runs(out_dir, result.get("cause") or cut)
    log = out_dir / "prepare.log"
    prepared = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    missing = preparation.missing(prepared)
    if any(gap["tool"] == "scip-typescript" for gap in missing):
        cause = f"scip-typescript {VERSION} could not be installed in the container: {runtime.excerpt(prepared)}"
        return runtime.refused("scip-typescript", VERSION, runtime.Unavailable(
            cause, "check the network: Daodan installs scip-typescript from the npm registry"))
    gaps += result.get("gaps") or []  # what the container run reports itself (a tracked link it did not copy)
    gaps += chains["gaps"] + missing + preparation.restore_gaps(prepared) + preparation.generation_gaps(prepared)
    generated = [{"command": command, "path": folder, "version": version}
                 for folder, version, command in GENERATED.findall(prepared)]
    ran = {item["path"] for item in generated} | {folder for binary, folder, _lines in
                                                   preparation.GENERATE.findall(prepared)
                                                   if any(command.startswith(f"{binary} ") for _f, command in generators)}
    log = out_dir / "execute.log"
    gaps += _not_generated(project_dir, log.read_text(encoding="utf-8", errors="replace") if log.is_file() else "",
                           ran)
    output = work_dir / "scip-typescript-0.scip"
    if (out_dir / "out/index.scip").is_file():
        os.replace(out_dir / "out/index.scip", output)
    if (out_dir / "out/unbound.jsonl").is_file():  # beside its index, where `unanswered` reads it
        os.replace(out_dir / "out/unbound.jsonl", output.with_suffix(".unbound.jsonl"))
    # The Vue components' generated documents become theirs, with the checker's pass beside the index.
    report = components.rewrite(output, out_dir / "out/components.json", project_dir) if parts else {}
    gaps += components.gaps(report)
    if runs and runs[-1]["phase"] == "execute":
        runs[-1].update(index=str(output) if output.is_file() else None,
                        index_bytes=output.stat().st_size if output.is_file() else 0)
    out = runtime.outcome("scip-typescript", VERSION, runs)
    # On the indexer's record, which the stage's report and each language's store entry carry.
    out["indexer"]["types"] = re.findall(r"DAODAN-TYPES-ADDED (\S+)", prepared)
    if report.get("tools"):
        out["indexer"]["frameworks"] = sorted(report["tools"].values(), key=lambda item: item["tool"])
    if generated:
        out["indexer"]["generated"] = generated
    configs = {"configs": {"components": {rel: {key: entry[key] for key in ("tool", "error") if key in entry}
                                          for rel, entry in report.get("components", {}).items()}}} if report else {}
    return {**out, "restores": plan, "tsconfig_extends": extends, **configs, **({"gaps": gaps} if gaps else {})}
