"""scip-dotnet for C#: how it runs, and what its index leaves to the reader.

scip-dotnet (github.com/sourcegraph/scip-dotnet, Apache-2.0) loads a solution or a project with MSBuild's
workspace and reads Roslyn's semantic model of each document. Loading evaluates the project's MSBuild logic and
runs the analyzers and source generators its packages bring, so it happens only in a container
(`container.run_in_container`, spec `docs/specs/2026-11-12-passo-dinamico.md`, sections 2-4), never on the host:
without a container the language is `unavailable`, with the gap's cause and remedy.

- What runs: one run per solution file in the folder of each `dotnet` workspace of the pre-map, the build a
  developer runs (a project may read `$(SolutionDir)`), and one per C# or Visual Basic project no solution lists,
  by its own file (`targets`). Each from the checkout's root, where scip-dotnet names its documents from.
- The tool is its NuGet package at `VERSION` (`TOOL`), not its image (`sourcegraph/scip-dotnet:v<VERSION>`), which
  brings an SDK of its own where `global.json` asks for the project's: a .NET tool holding one build per runtime
  (net8.0, net9.0, net10.0) with every library it needs. Daodan downloads it once on the host into the shared
  directory, checked by sha256, and the copy carries it; the preparation unpacks it and nothing is installed from
  a registry. `dotnet <build>/scip-dotnet.dll` runs the build of the SDK's own runtime.
- The SDK is the one the pre-map states (`toolchains`, tool `dotnet`: `global.json`), installed by mise at that
  version (`preparation.toolchains`), else the one the preparation carries (`preparation.NEEDS["dotnet"]`). A
  stated SDK mise could not install is a gap, and the run fails with what `dotnet` says: `global.json` accepts
  no other.
- Preparation, on a network that reaches only `REGISTRIES` (NuGet's read API; packages are pushed to another
  host) and mise's hosts when it installs the SDK: the SDK, the tool unpacked, then the project's own restore
  (`preparation.restore`) in the folder of each run. A restore that fails is a gap (`preparation.restore_gaps`)
  and the run goes on.
- Execution, with no network: `scip-dotnet index <file> --skip-dotnet-restore` per run, each index under `OUT`,
  which comes back into `<work_dir>/container/out`. scip-dotnet exits 0 and writes an index even when the
  workspace loaded nothing: a run that says `NO_DOCUMENTS` is a build without an index, and each `Failure` the
  workspace reports is a gap (`workspace_failure`).
- `EnableWindowsTargeting` is set as scip-dotnet's own restore passes it: a project that targets Windows
  restores and loads on Linux.

A phase is one bash script. Each step prints `DAODAN_STEP` lines, read back by `jvm.steps` as the runs of the
contract.

What the index states (from `ScipDocumentIndexer.cs`, `ScipCSharpSyntaxWalker.cs` and the tool's snapshot tests):
one occurrence per identifier, a definition at each declared name, no enclosing range, no symbol kind. Every
symbol defined in source has the package `. .`, whatever its project. `is_implementation` is on a type for its
base types and interfaces, on a method for the methods it overrides and the interface members it implements:
the shared traversal follows the methods'. An alias names its target at each use, and no definition shares a
range with a reference: no `same_range` rule. The hooks, each for what the index leaves out:

- `prepare`: two runs that load one project both write its documents, and no definition has an enclosing range:
  each occurrence once, and each definition the body the snapshot declares at its name, so an edge starts at the
  method that holds it (`clang.dedupe`, `clang.enclose`).
- `classify`: `namespace` and `using` reference every segment as a `. .` symbol nothing defines: a namespace.
- `hops`: a symbol the index references and defines nowhere, whose declaration the language puts elsewhere. A
  record's positional property leads to its parameter (`positional`), a constructor the class does not write to
  the class (`implicit-constructor`: an attribute references it), a setter's `value` to its property or event
  (`accessor-value`). `new X()` is written at the type itself and needs none.
- `static`: `base.M()` runs that method, never an override.
- `refine`: a type's symbol holds the last segment of its namespace and no arity, so two declarations may share
  one: every edge to it is `uncertain`, each declaration a candidate (the parts of one partial declaration are
  one). An overload's number comes from comparing the called symbol with the type's members, and a reduced
  extension call and a constructed generic call equal none: they are written as the first overload, so a
  reference to it is `uncertain` where a later overload is an extension or generic method. A constructor called
  at no identifier (`: base(...)`, `: this(...)`, `new(...)`) is in neither the index nor the snapshot's
  references: a hole (`unnamed-constructor`).
- `missing`: why a file has no document (`tasks` hands it the units and what each run said).

A name with type arguments (`Set<Order>()`, `new List<Order>()`) has no occurrence: scip-dotnet visits
identifier names only. Those references stay holes.
"""
from __future__ import annotations

import collections
import re
import shlex
import shutil
from pathlib import Path, PurePosixPath

import code_graph
import preparation

VERSION = "0.2.16"  # the NuGet package scip-dotnet, published 2026-10-21: its sha512 is the one NuGet's catalog
# states, its licence the LICENSE it holds (Apache-2.0, the repository's)
TOOL = (f"https://api.nuget.org/v3-flatcontainer/scip-dotnet/{VERSION}/scip-dotnet.{VERSION}.nupkg",
        "70255008a2f3054701bafb551b51c3af0c1e0ac7624e63ec2e852b3f72e5df58", "scip-dotnet.nupkg")
NEWEST = "net10.0"  # the newest runtime the package holds a build for
IMAGE = "buildpack-deps:noble@sha256:890e8b5c0040e1deff5cc7dc7b4414e67069f79e3301afc4ec5bd49d64ef13e5"  # what the
# SDK needs (glibc, libssl, zlib) and python3 for the unpacking: the image of `premap/container_runner.py`
HOME, OUT, WORK = f"{preparation.STATE}/scip-dotnet", "/daodan/out", "/work"
REGISTRIES = ("api.nuget.org",)  # packages are read here and pushed to www.nuget.org, never listed
ENV = {**preparation.ENV, "TERM": "dumb", "DOTNET_SYSTEM_GLOBALIZATION_INVARIANT": "1",
       "EnableWindowsTargeting": "true"}  # MSBuild reads an environment variable as a property
MIN_FREE = 4 * 2**30  # the container's memory, not measured yet: Roslyn's workspace and MSBuild's build host
PIDS = 4096  # threads count: MSBuild starts a node per CPU for the restore
SOLUTIONS, PROJECTS = (".sln", ".slnx"), (".csproj", ".vbproj")  # what `scip-dotnet index` takes
NO_DOCUMENTS = "no documents were indexed"  # scip-dotnet's own warning, IndexCommandHandler.cs
FAILURE = re.compile(r"\bFailure: (.+?)(?: \(occurred \d+ times\))?\s*$")  # a workspace diagnostic, as it logs it
# The analyzer this adapter is: the pass's entry, the languages it indexes, the unit kinds of the pre-map it takes
# its structure from, and whether its build runs only in a container (`indexers.analyzers`).
ENTRY, LANGUAGES, UNIT_KINDS, NEEDS_CONTAINER = "scip-dotnet", ("csharp",), frozenset({"dotnet-project"}), True


# ---------------------------------------------------------------------------------------------------------
# What the index leaves to the reader

TYPES = {"class_declaration", "struct_declaration", "interface_declaration", "record_declaration",
         "enum_declaration", "delegate_declaration"}
METHOD = re.compile(r"^(.*[#/])([^#/().`]+|`[^`]+`)\((\+\d+)?\)\.$")  # owner, name, overload number
CONSTRUCTOR = re.compile(r"^(.*#)`\.ctor`\((?:\+\d+)?\)\.$")
PARAMETER = re.compile(r"^(.*#)`\.ctor`\((?:\+\d+)?\)\.\((.+)\)$")  # a constructor's parameter: its type, its name
ACCESSOR = re.compile(r"^(.*#)(?:set|add|remove)_(.+)\((?:\+\d+)?\)\.\(value\)$")


def prepare(index, snapshot) -> dict:
    """Each occurrence once, and each definition the body the snapshot declares at its name (see the module
    docstring); returns what each step did."""
    from indexers import clang
    deduplicated = clang.dedupe(index)
    index.declarations = clang._declarations(index, snapshot)
    return {"deduplicated": deduplicated, "enclosed": clang.enclose(index)}


def classify(index):
    """A namespace: `namespace` and `using` lines reference each segment, which nothing defines."""
    return lambda key: "namespace" if key.endswith("/") else None


def _node(index, rel: str, occurrence):
    """The identifier an occurrence of a C# document is written at; None without the file or the grammar."""
    return index.node(rel, occurrence, "csharp") if rel.endswith(".cs") else None


def _nodes(index, rel: str):
    tree = index.tree(rel, "csharp") if rel.endswith(".cs") else None
    stack = [tree.root_node] if tree is not None else []
    while stack:
        node = stack.pop()
        stack.extend(node.children)
        yield node


def _positional(index, rel: str, occurrence) -> bool:
    """Whether a parameter is one of a record's own: `record Order(int Id)`."""
    node, above = _node(index, rel, occurrence), []
    while node is not None and len(above) < 3:
        node = node.parent
        above.append(node.type if node is not None else None)
    return above == ["parameter", "parameter_list", "record_declaration"]


def hops(index) -> dict:
    """From a symbol the index references and defines nowhere to where the language declares it: a record's
    positional property to its parameter, a constructor a class does not write to the class, a setter's `value`
    to its property or event."""
    out = collections.defaultdict(list)
    for rel, occurrences in index.documents.items():
        for item in occurrences:
            if item.definition:
                match = PARAMETER.match(item.key)
                declared = f"{match.group(1)}{match.group(2)}." if match else None
                if declared and declared not in index.defs and _positional(index, rel, item):
                    out[declared].append((item.key, "positional"))
                continue
            if item.key in index.defs:
                continue
            constructor, value = CONSTRUCTOR.match(item.key), ACCESSOR.match(item.key)
            if constructor and constructor.group(1) in index.defs:
                out[item.key].append((constructor.group(1), "implicit-constructor"))
            for target in (f"{value.group(1)}{value.group(2)}{suffix}" for suffix in ".#") if value else ():
                if target in index.defs:
                    out[item.key].append((target, "accessor-value"))
    return {key: list(dict.fromkeys(items)) for key, items in out.items()}


def static(index) -> set[tuple[str, int, int]]:
    """`(rel, line, byte column)` of each member name reached through `base`, bound statically."""
    out = set()
    for rel in index.documents:
        for node in _nodes(index, rel):
            name = node.child_by_field_name("name") if node.type == "member_access_expression" else None
            if name is not None and node.children[0].type == "base":
                out.add((rel, name.start_point[0] + 1, name.start_point[1]))
    return out


def _declaration(index, rel: str, occurrence) -> tuple | None:
    """Where the source declares a definition: its namespace in full, then its types with their arity, outermost
    first; None without the file or the grammar."""
    node = _node(index, rel, occurrence)
    if node is None:
        return None
    namespaces, types, top = [], [], node
    while node is not None:
        name = node.child_by_field_name("name")
        if node.type in TYPES and name is not None:
            arity = sum(len(child.named_children) for child in node.children if child.type == "type_parameter_list")
            types.append(f"{name.text.decode()}`{arity}")
        elif node.type == "namespace_declaration" and name is not None:
            namespaces.append(name.text.decode())
        top, node = node, node.parent
    namespaces += [child.child_by_field_name("name").text.decode() for child in top.children
                   if child.type == "file_scoped_namespace_declaration"]
    return (".".join(reversed(namespaces)), *reversed(types))


def _shared(index) -> dict[str, list[str]]:
    """Each symbol several declarations share, with their places: the parts of one partial declaration are one."""
    out = {}
    for key, places in index.defs.items():
        if len(places) > 1 and code_graph.split_symbol(code_graph._global(key)) \
                and len({_declaration(index, rel, item) for rel, item in places}) > 1:
            out[key] = sorted({f"{rel}:{item.line}" for rel, item in places})
    return out


def _reduced_or_generic(index, key: str) -> bool:
    """Whether a method is declared an extension (`this` on its first parameter) or generic: a call of it in
    reduced or constructed form carries no overload number."""
    for rel, item in index.defs[key]:
        node = _node(index, rel, item)
        method = node.parent if node is not None else None
        if method is None or method.type != "method_declaration":
            continue
        parameters = method.child_by_field_name("parameters")
        first = parameters.named_children[:1] if parameters is not None else []
        if method.child_by_field_name("type_parameters") is not None or any(
                child.type == "modifier" and child.text == b"this" for held in first for child in held.children):
            return True
    return False


def _first_overloads(index) -> dict[str, list[str]]:
    """The first overload of each method name, with all its overloads, where a later one is an extension or
    generic method: a reference to the first may stand for a call of that one."""
    groups = collections.defaultdict(list)
    for key in index.defs:
        match = METHOD.match(key) if code_graph.split_symbol(code_graph._global(key)) else None
        if match:
            groups[match.group(1, 2)].append(key)
    return {f"{owner}{name}().": sorted(keys) for (owner, name), keys in groups.items()
            if any(METHOD.match(key).group(3) and _reduced_or_generic(index, key) for key in keys)}


def _unnamed(index) -> list[dict]:
    """The constructor calls written at no identifier: scip-dotnet has no occurrence for them."""
    holes = []
    for rel in sorted(index.documents):
        for node in _nodes(index, rel):
            if node.type == "constructor_initializer":
                name = next((child.type for child in node.children if child.type in ("base", "this")), "base")
                reason = "constructor initializer"
            elif node.type == "implicit_object_creation_expression":
                name, reason = "new", "target-typed new"
            else:
                continue
            holes.append({"site": f"{rel}:{node.start_point[0] + 1}", "name": name, "kind": "call",
                          "class": "unnamed-constructor", "reason": reason})
    return sorted(holes, key=lambda hole: (hole["site"].rsplit(":", 1)[0], int(hole["site"].rsplit(":", 1)[1])))


def refine(index, graph: dict, configs: dict | None = None) -> None:
    """Mark the edges the symbol scheme can make wrong, and add the holes of the constructor calls written at no
    identifier (see the module docstring)."""
    shared, first = _shared(index), _first_overloads(index)
    for edge in graph["edges"]:
        if edge["to"] in shared:
            edge["uncertain"] = {"reason": "several declarations under one symbol", "candidates": shared[edge["to"]]}
        elif edge["symbol"] in first:
            edge["uncertain"] = {"reason": "first overload of a reduced or generic call",
                                 "candidates": first[edge["symbol"]]}
    graph["holes"] += _unnamed(index)


def tasks(configs) -> dict:
    """What the run brought back for `missing`: `{"units": [the pre-map's], "failed": {run: cause}, "unloaded":
    {project file: the workspace's failure}}`, empty without it."""
    return configs if isinstance(configs, dict) else {}


def missing(index, rels: list[str], configs: dict | None = None) -> dict:
    """Why a C# file has no document: no project of the pre-map holds it, its project's run gave no document,
    MSBuild's default items leave it out, or its project was indexed without it."""
    units = {_folder(unit["root"]): unit for unit in reversed((configs or {}).get("units") or [])}
    failed, unloaded = (configs or {}).get("failed") or {}, (configs or {}).get("unloaded") or {}
    indexed = {code_graph.owner(rel, set(units)) for rel in index.documents}
    reasons = {}
    for rel in rels:
        root = code_graph.owner(rel, set(units))
        if root is None:
            reasons[rel] = "in no .NET project of the pre-map: no project compiles it"
            continue
        unit, inside = units[root], rel[len(root) + 1:] if root else rel
        run = unit["manifest"] if unit.get("solution") is None else unit["solution"]
        cause = unloaded.get(unit["manifest"]) or failed.get(run)
        if inside.split("/")[0] in ("bin", "obj") and "/" in inside:
            reasons[rel] = "under bin/ or obj/ of its project: MSBuild's default items leave build output out"
        elif cause:
            reasons[rel] = f"scip-dotnet gave no document of its project {unit['manifest']}: {cause}"
        elif root in indexed:
            reasons[rel] = (f"its project {unit['manifest']} is indexed without it: no Compile item of the project "
                            "as MSBuild evaluated it (removed, or left out by a condition or the target framework)")
        else:
            reasons[rel] = f"its project {unit['manifest']} has no document in the index"
    return reasons


# ---------------------------------------------------------------------------------------------------------
# Running the indexer

# As `jvm.HEAD`: the working folder, and each step between its markers in the phase log.
HEAD = r'''set -u
WORK=${DAODAN_WORK:-/work}
mkdir -p "$HOME"
cd "$WORK" || exit 70
step() {
  local name=$1 code
  shift
  echo "DAODAN_STEP begin $name $(date +%s.%N)"
  "$@"
  code=$?
  echo "DAODAN_STEP end $name $code $(date +%s.%N)"
  return $code
}
trap 'echo "DAODAN_PEAK $(cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo -)"' EXIT
'''
# The package holds a build of scip-dotnet per runtime: the one of the SDK that answers here (`global.json`
# decides), the newest for an SDK newer than them all.
EXECUTE = rf'''OUT={OUT}
mkdir -p "$OUT"
if ! SDK=$(dotnet --version 2>&1); then
  step sdk sh -c 'echo "$1"; exit 70' sh "no .NET SDK runs here: $SDK"
  exit 70
fi
DLL={HOME}/tools/net${{SDK%%.*}}.0/any/scip-dotnet.dll
if [ ! -f "$DLL" ]; then
  DLL={HOME}/tools/{NEWEST}/any/scip-dotnet.dll
  export DOTNET_ROLL_FORWARD=Major
fi
'''


def _folder(path: str | None) -> str:
    """A folder as the runs name it: '' for the checkout's root."""
    return "" if path in (None, "", ".") else path


def structure(record: dict) -> dict:
    """What `index` takes from the pre-map: the folders of its solutions (the `dotnet` workspaces), each .NET
    project with the solution folder that lists it (None: no solution does) and the SDK it states."""
    import premap
    held = {_folder(member): _folder(item["root"]) for item in record.get("workspace", [])
            if item.get("tool") == "dotnet" for member in item.get("members", ())}
    units = [{"root": unit["root"], "manifest": unit.get("manifest"), "solution": held.get(_folder(unit["root"]))}
             for unit in record.get("units", []) if unit["kind"] in UNIT_KINDS]
    return {"roots": premap.roots(record, (), {"dotnet"}), "units": units,
            "toolchains": [item for item in record.get("toolchains", []) if item.get("tool") == "dotnet"]}


def targets(project_dir: Path, roots, units) -> tuple[list[tuple[str, str]], list[dict]]:
    """`(file, key)` of each run, from the checkout: the solution files in each workspace folder of `roots`
    (key: the folder), then each C# or Visual Basic project no solution lists (key: its file). And the state of
    each workspace folder that holds no solution file."""
    wanted, states = [], []
    for root in sorted(roots):
        folder = Path(project_dir) / root
        found = sorted(path.name for path in folder.iterdir() if path.suffix.lower() in SOLUTIONS) \
            if folder.is_dir() else []
        wanted += [(f"{root}/{name}" if root else name, root) for name in found]
        if not found:
            states.append({"root": root, "state": "failed",
                           "reason": "no solution file in the folder of this workspace"})
    wanted += sorted((unit["manifest"], unit["manifest"]) for unit in units if unit.get("solution") is None
                     and str(unit.get("manifest") or "").lower().endswith(PROJECTS))
    return wanted, states


def scripts(setup: list[str], wanted: list[tuple[str, str]]) -> tuple[str, str]:
    """The bash scripts of the two phases: the preparation installs the SDK with `setup`, unpacks the tool and
    restores the folder of each run; the execution runs scip-dotnet over each file of `wanted`."""
    folders = list(dict.fromkeys(PurePosixPath(target).parent.as_posix() for target, _key in wanted))
    lines = "\n".join(setup)
    prepare = (f"# daodan prepare\n{HEAD}mkdir -p {preparation.T}/bin\n"
               f"sdk() {{\n{lines}\n}}\ndependencies() {{\n{preparation.restore('dotnet', folders)}\n}}\n"
               "step sdk sdk\n"
               f"step unpack python3 -m zipfile -e {preparation.IN}/{TOOL[2]} {HOME} || exit 70\n"
               "step restore dependencies\nexit 0\n")
    runs = "".join(f'step index-{number} dotnet "$DLL" index {shlex.quote(target)} --working-directory "$WORK" '
                   f'--output "$OUT/index-{number}.scip" --skip-dotnet-restore\n'
                   for number, (target, _key) in enumerate(wanted, 1))
    return prepare, f"# daodan execute\n{HEAD}{EXECUTE}{runs}exit 0\n"


def unavailable(cause: str, remedy: str) -> dict:
    """No index can be built here: the contract's `unavailable`, with `reason` and `install`."""
    indexer = {"name": "scip-dotnet", "version": VERSION, "seconds": 0, "peak_mb": None}
    return {"indexes": [], "runs": [], "indexer": indexer, "state": "unavailable", "reason": cause, "install": remedy}


def _indexer(runs: list[dict]) -> dict:
    return code_graph.indexer("scip-dotnet", VERSION, [run for run in runs if run["seconds"] is not None])


def workspace_failures(log: str) -> dict[str, list[str]]:
    """Per step of an execution log, what MSBuild's workspace could not load: scip-dotnet logs each `Failure`
    diagnostic once its index is written."""
    out, step = collections.defaultdict(list), None
    for line in log.splitlines():
        match = FAILURE.search(line)
        if line.startswith("DAODAN_STEP begin "):
            step = line.split()[2]
        elif step and match:
            out[step].append(match.group(1)[:600])
    return {step: list(dict.fromkeys(found)) for step, found in out.items()}


def index(project_dir: Path, work_dir: Path, files: list[str] | None = None, *, roots, units=(), toolchains=(),
          engine=None, memory: int = MIN_FREE, timeout: float = 3600) -> dict:
    """The index of each solution in `roots` and of each project of `units` no solution lists, in one container
    run, with its runs, each run's state (`builds`) and what `missing` reads (`configs`); `files` is not used:
    MSBuild decides what a project compiles. `gaps` says what the preparation could not install or restore and
    what the workspace could not load. Without a container, `unavailable`; without an index, `failed`."""
    import container
    from indexers import jvm
    project_dir, work_dir = Path(project_dir).resolve(), Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    wanted, states = targets(project_dir, roots, units)
    if not wanted:
        said = "".join(f"; {item['root'] or '.'}: {item['reason']}" for item in states)
        return {**unavailable(f"no solution or C# project in the pre-map: nothing builds these files{said}",
                              "declare the project (a .csproj, or a solution that lists it)"),
                **({"builds": states} if states else {})}
    out_dir = work_dir / "container"
    back = out_dir / Path(OUT).name
    shutil.rmtree(back, ignore_errors=True)
    for phase in ("prepare", "execute"):
        (out_dir / f"{phase}.log").unlink(missing_ok=True)
    chains = preparation.toolchains(list(toolchains))
    sdk = chains if chains["lines"] else preparation.setup(["dotnet"])  # the stated SDK, else the pin
    prepare, execute = scripts(sdk["lines"], wanted)
    result = container.run_in_container(
        project_dir, ["bash", "-c", execute], image=IMAGE, out_dir=out_dir, prepare=["bash", "-c", prepare],
        outputs=[OUT], env=dict(ENV), timeout=timeout, memory=memory, pids=PIDS,
        registries=(*REGISTRIES, *sdk["hosts"]), engine=engine,
        inputs=lambda: {f"{preparation.IN}/{name}": preparation.fetched(url, digest, name)
                        for url, digest, name in (TOOL, *sdk["files"])})
    logs = {phase: (out_dir / f"{phase}.log").read_text(encoding="utf-8", errors="replace")
            if (out_dir / f"{phase}.log").is_file() else "" for phase in ("prepare", "execute")}
    runs = [run for phase, text in logs.items() for run in jvm.steps(text, phase)]
    failures = workspace_failures(logs["execute"])
    gaps = [*chains["gaps"], *preparation.missing(logs["prepare"]), *preparation.restore_gaps(logs["prepare"]),
            *({"kind": "workspace_failure", "path": wanted[int(step.rsplit("-", 1)[1]) - 1][0], "detail": message}
              for step, found in failures.items() for message in found)]
    part = _contract(result, runs, back, work_dir, wanted, states, list(units), failures)
    return {**part, **({"gaps": gaps} if gaps else {})}


def _cause(result: dict, run: dict | None, placed: Path | None) -> str | None:
    """Why a run gave no index, None when it did: it never started, was cut off, failed, or wrote none."""
    ended = result.get("cause") or f"the container run ended {result['state']}"
    if run is None:
        return ended if result["state"] != "done" else f"exit code {result.get('exit_code')}"
    if run["returncode"] is None:
        return ended
    if run["returncode"]:
        return f"exit code {run['returncode']}"
    return None if placed is not None and placed.stat().st_size else "no index came back"


def _contract(result: dict, runs: list[dict], back: Path, work_dir: Path, wanted, states: list[dict],
              units: list[dict], failures: dict) -> dict:
    """The contract from what came back into `back`: each run's index placed in `work_dir`, its state after
    `states`, and for `missing` the runs without a document and the projects the workspace could not load."""
    from indexers import jvm
    if result["state"] == "gap":
        return unavailable(result["cause"], result["remedy"])
    steps = {run["step"]: run for run in runs if run["phase"] == "execute"}
    indexes, done, causes = [], set(), {}
    for number, (target, key) in enumerate(wanted, 1):
        run = steps.get(f"index-{number}")
        placed = jvm.place(back / f"index-{number}.scip", work_dir / f"index-{number}.scip")
        cause = _cause(result, run, placed)
        if cause is None and NO_DOCUMENTS in run["stderr_tail"]:
            cause = "; ".join([NO_DOCUMENTS, *failures.get(run["step"], ())])
        if cause is None:
            run["index_bytes"] = placed.stat().st_size
            indexes.append([str(placed), ""])
            done.add(key)
            states.append({"root": target, "state": "done"})
            continue
        causes.setdefault(key, cause)
        states.append({"root": target, "state": "failed", "reason": cause})
    failed = {key: cause for key, cause in causes.items() if key not in done}
    if not indexes:
        tail = (runs[-1].get("stderr_tail") or "").strip()[-800:] if runs else ""
        return {"indexes": [], "runs": runs, "indexer": _indexer(runs), "state": "failed", "builds": states,
                "reason": f"scip-dotnet wrote no index ({next(iter(failed.values()))})" + (f": {tail}" if tail else "")}
    unloaded = {unit["manifest"]: message for found in failures.values() for message in found for unit in units
                if f"{WORK}/{unit['manifest']}'" in message}
    return {"indexes": indexes, "runs": runs, "indexer": _indexer(runs), "builds": states,
            "configs": {"units": units, "failed": failed, "unloaded": unloaded}}
