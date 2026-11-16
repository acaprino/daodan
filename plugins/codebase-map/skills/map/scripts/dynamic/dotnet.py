"""The .NET observer: the tests of each C# test project, `dotnet test`, under an exact recorder of Daodan's own.

The recorder. The rule is the JVM observer's: every call, with its caller, its callee and the call site's line,
in the processes `dotnet test` starts. Compared from their own documentation and source (November 2026), no
existing recorder meets it:

- the CLR profiling API's enter and leave hooks (`FunctionEnter3WithInfo`) give the callee only: a caller needs a
  shadow stack, a call site a stack snapshot and a PDB lookup per call; the profilers built on it (the CLR
  Instrumentation Engine, MIT; OpenTelemetry's and Datadog's, Apache-2.0) hook chosen library methods as spans.
- coverlet and AltCover (MIT) rewrite the built assemblies with Mono.Cecil before the tests run, as this recorder
  does, but count sequence points and branches, not calls.
- Harmony (MIT) detours the methods it is given at run time: their entries only, and an inlined method escapes;
  Mono's log profiler traces calls on Mono's runtime only; SharpDetect (Apache-2.0) is a CoreCLR profiler for
  races and deadlocks.
- EventPipe's sample profiler (dotnet-trace, MIT) samples stacks: a declared second source at most, not planned.

So the recorder is Daodan's own, `dotnet_record/`: `rewrite/Rewrite.cs` rewrites in place, with Mono.Cecil
(`CECIL`, MIT, one package from NuGet pinned by sha256), each assembly the tests built from the project's sources,
and `record/Record.cs` (netstandard2.0) is what the rewritten code calls. Both are built in the container's
preparation by the project's SDK, so no binary of Daodan's is carried. The recorder reaches the tests without
changing the project: every .NET process reads DOTNET_STARTUP_HOOKS when it starts (the host's startup hooks), the
processes `dotnet test` starts inherit its environment, and the hook resolves the rewritten assemblies' reference
to the recorder. A process that clears its environment runs unrecorded: the `not_observed` gap.

`plan` reads the snapshot's C# project files: each that names a test framework (`TESTS`: MSTest.Sdk,
Microsoft.NET.Test.Sdk, MSTest, xUnit, NUnit, TUnit, `IsTestProject`) runs its tests with the SDK's own command
from its folder, `dotnet test`: with `--project` where the global.json above it states Microsoft.Testing.Platform
as the test runner (the SDK then takes no bare path), with the path alone otherwise. A framework a
Directory.Build.props adds is not seen. A test project that is an Aspire app host, or tests one with
Aspire.Hosting.Testing (`ASPIRE`), starts its services as containers through Aspire: the container engine that
needs is one the execution does not give, since it would let a test start any container on any network, so its
tests do not run (`tests_need_container_engine`); one that only references an app host reads its model, and runs. `observe` is one container run on the SDK the pre-map states
(`csharp.structure`), else Daodan's: the preparation, with the registries, builds Daodan's two projects and each
test project (which restores it); the execution, with no network, rewrites the assemblies under the copy of the
checkout and runs each project's tests, `--no-build`, stopped after `LIMIT` seconds. Back come the rewriter's
table, the recorder's files (one per process) and each run's log and exit code.

What a site is: a call, callvirt or newobj instruction, with the method it names and the statement its PDB says it
belongs to (a sequence point: lines and columns). `place` puts a site on the reference of the snapshot's parse of
its file whose callee name lies in that statement and is the one it calls (a constructor's is its class's, an
accessor's its property's), as `code_graph.Snapshot.callee` places a reference; two in one statement are
ambiguous (`sites_ambiguous`). A call the source does not name so (`: base(...)`, a delegate's `Invoke`, an
operator) is counted, never placed. A callee is the declaration of the snapshot's parse whose name it has and which
holds its first line (an async or iterator method's is its state machine's); a lambda is `(lambda)`, an accessor
or local function a project callable the snapshot does not declare. A call that entered none of the project's
methods is an external end named by the type it declares; on a project type it ran in code from outside the
project (a mock, a proxy) and is no destination (`mock`).
"""
from __future__ import annotations

import collections
import json
import posixpath
import re
import shlex
from pathlib import Path, PurePosixPath

import preparation
from indexers import csharp, jvm

# The observer this module is (`dynamic.observers`): its entry, its recorder's version, the languages it observes.
ENTRY, VERSION, LANGUAGES = "dynamic-record-dotnet", "1", ("csharp",)
CECIL = ("https://api.nuget.org/v3-flatcontainer/mono.cecil/0.11.6/mono.cecil.0.11.6.nupkg",
         "d2a23832aaa948ba9a01acc42b5726e34c5f995958f1b30d45c0e7c70b3a72d5", "mono.cecil.0.11.6.nupkg")  # MIT,
# published 2024-10-02: its sha512 is the one NuGet's catalog states
RECORD = Path(__file__).resolve().parent / "dotnet_record"
AGENT = f"{preparation.IN}/dynamic-dotnet"  # the sources, the package and what is built from them, in the container
BUILT = f"{preparation.STATE}/dynamic-dotnet"  # a mark per test project the preparation built
OUT = csharp.OUT
HOOK = f"{AGENT}/out/record/Daodan.Record.dll"
TESTS = re.compile(r'Sdk="MSTest\.Sdk|<Sdk\s+Name="MSTest\.Sdk|Include="(?:Microsoft\.NET\.Test\.Sdk|MSTest|xunit|NUnit|'
                   r'TUnit)\b|<IsTestProject>\s*true\s*<', re.I)
# A test project that is an Aspire app host, or tests one with Aspire.Hosting.Testing, starts its services as
# containers through Aspire's orchestrator: what it is, said after its path.
ASPIRE = (("is an Aspire app host (Aspire.AppHost.Sdk)",
           re.compile(r'Sdk="Aspire\.AppHost\.Sdk\b|<Sdk\s+Name="Aspire\.AppHost\.Sdk"|<IsAspireHost>\s*true\s*<', re.I)),
          ("tests an Aspire app host with Aspire.Hosting.Testing",
           re.compile(r'Include="Aspire\.Hosting\.Testing"', re.I)))
PLATFORM = "Microsoft.Testing.Platform"
LIMIT = 1800  # the seconds one project's tests may take
EXAMPLES = 20
NO_CALL = "no call of that name in its statement"
# What a summary of `dotnet test` says: Microsoft.Testing.Platform's lines, then VSTest's.
COUNT = re.compile(r"^\s*(total|failed|skipped):\s*(\d+)\s*$", re.M | re.I)
VSTEST = re.compile(r"Failed:\s*(\d+),\s*Passed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Total:\s*(\d+)")
# The first test that failed and its error: `failed <test> (<duration>)` and the message indented below it, or
# VSTest's `Failed <test> [<duration>]` with its `Error Message:`.
FIRST = re.compile(r"^\s*[Ff]ailed (\S.*)\n(?:\s*Error Message:\s*\n)?\s*(\S.*)", re.M)


def external(callee: dict) -> dict:
    """The package of a callee outside the project: the assembly of the type the call names; the run does not see
    the package's version."""
    return {"manager": "nuget", "package": callee.get("assembly") or callee.get("module") or "", "version": None}


def _global(rel: str, files: set, read) -> dict:
    """The global.json the SDK reads for a project at `rel`: the nearest at or above its folder."""
    folder = PurePosixPath(rel).parent
    for above in (folder, *folder.parents):
        path = (above / "global.json").as_posix().removeprefix("./")
        if path in files:
            try:
                value = json.loads(read(path) or "{}")
            except ValueError:
                return {}
            return value if isinstance(value, dict) else {}
    return {}


def plan(record: dict, files: list[str], read) -> dict:
    """`{runs, gaps, sources, toolchains}` from the pre-map `record` and the snapshot's `files`: a run is `{root,
    runner, project, argv}`, the folder and file of a test project and its `dotnet test`; without one, a `no_tests`
    gap. `sources` are the C# files `place` reads, `toolchains` the SDK the pre-map states."""
    common = {"sources": sorted(rel for rel in files if rel.endswith(".cs")),
              "toolchains": csharp.structure(record)["toolchains"]}
    listed, runs, gaps = set(files), [], []
    for rel in sorted(files):
        text = (read(rel) or "") if rel.lower().endswith(".csproj") else ""
        if not TESTS.search(text):
            continue
        aspire = next((what for what, pattern in ASPIRE if pattern.search(text)), None)
        if aspire:
            gaps.append({"kind": "tests_need_container_engine", "path": rel, "detail": (
                f"{rel} {aspire}, which starts its services as containers: Aspire needs a container engine reachable "
                "from the tests, which Daodan's execution does not give (no network, no engine socket: one would let "
                "a test start any container on any network); its tests do not run")})
            continue
        root, name = posixpath.dirname(rel), posixpath.basename(rel)
        runner = ((_global(rel, listed, read).get("test") or {}).get("runner") or "")
        argv = ["dotnet", "test", *(["--project"] if runner == PLATFORM else []), name, "--no-build"]
        runs.append({"root": root, "runner": "dotnet test", "project": rel, "argv": argv})
    if not runs and not gaps:
        gaps.append({"kind": "no_tests", "detail": "no C# project names a test framework (MSTest.Sdk, "
                     "Microsoft.NET.Test.Sdk, MSTest, xUnit, NUnit, TUnit, IsTestProject): no test runs"})
    return {"runs": runs, "gaps": gaps, **common}


def agent_commands(folder: str) -> str:
    """The shell line that builds, in `folder` (a copy of `RECORD` with Mono.Cecil's package in `packages/`), the
    recorder into `out/record` and the rewriter, for the runtime of the SDK that answers there, into `out/rewrite`."""
    return (f"cd {shlex.quote(folder)} && dotnet build record -c Release -o out/record -nologo"
            " && dotnet build rewrite -c Release -o out/rewrite -nologo"
            " -p:DaodanRuntime=$(dotnet --version | cut -d. -f1-2)")


def scripts(runs: list[dict], setup: list[str]) -> tuple[str, str]:
    """The two phases' bash scripts: the preparation installs the SDK with `setup`, builds Daodan's recorder and
    rewriter and each test project, marking the ones built; the execution rewrites the copy's assemblies and runs
    the tests of each project built, under the recorder."""
    lines = "\n".join(setup)
    agent = agent_commands(AGENT)
    builds = "".join(f"step build-{number} build {shlex.quote(run['root'] or '.')} "
                     f"{shlex.quote(posixpath.basename(run['project']))} && touch {BUILT}/built-{number}\n"
                     for number, run in enumerate(runs, 1))
    prepare = (f"# daodan prepare\n{csharp.HEAD}mkdir -p {preparation.T}/bin {BUILT}\nsdk() {{\n{lines}\n}}\n"
               'build() {\n  ( cd "$WORK/$1" && dotnet build "$2" -nologo )\n}\n'
               f"step sdk sdk\nstep agent sh -c {shlex.quote(agent)} || exit 70\n{builds}exit 0\n")
    record = f"DOTNET_STARTUP_HOOKS={HOOK} DAODAN_RECORD={OUT}/calls DAODAN_RECORD_TABLE={OUT}/table.tsv"
    tests = "".join(f"if [ -f {BUILT}/built-{number} ]; then ( cd {_folder(run)} && {record} timeout -k 30 {LIMIT}"
                    f" {shlex.join(run['argv'])} ) > {OUT}/tests-{number}.log 2>&1; echo $? > {OUT}/tests-{number}.code;"
                    " fi\n" for number, run in enumerate(runs, 1))
    execute = (f"# daodan execute\n{csharp.HEAD}mkdir -p {OUT}/calls\n"
               f'step rewrite dotnet {AGENT}/out/rewrite/Daodan.Rewrite.dll "$WORK" {OUT}/table.tsv "$WORK"\n'
               f"{tests}exit 0\n")
    return prepare, execute


def _folder(run: dict) -> str:
    return f'"$WORK"/{shlex.quote(run["root"])}' if run["root"] else '"$WORK"'


def read(folder: Path) -> dict:
    """What the rewriter's table and the recorder's files in `folder` say: `sites`, each call site that ran, with
    its file, its statement (`line`, `column`, `end_line`, `end_column`, from 1), the name, type and assembly it
    calls, the project methods it reached (`callees`, each with its kind, name, type, assembly, file and first line)
    and whether it also ran `outside` the rewritten code; `assemblies`, the rewritten ones; `skipped`, the project's
    assemblies left as built, with why; `processes`, the files read; `errors`, what the recorder could not do."""
    methods, sites, assemblies, skipped = {}, {}, set(), {}
    table = Path(folder) / "table.tsv"
    for line in table.read_text(encoding="utf-8", errors="replace").splitlines() if table.is_file() else ():
        cells = line.split("\t")
        if cells[0] == "m" and len(cells) >= 13:
            methods[int(cells[1])] = {"kind": cells[6], "kickoff": int(cells[7]) if cells[7] else None,
                                      "file": cells[8] or None, "line": int(cells[9]) if cells[9] else None,
                                      "name": cells[10], "type": cells[11], "assembly": cells[12]}
        elif cells[0] == "s" and len(cells) >= 12:
            sites[int(cells[1])] = {"method": int(cells[2]), "file": cells[4] or None,
                                    **{key: int(value) if value else None for key, value in
                                       zip(("line", "column", "end_line", "end_column"), cells[5:9])},
                                    "name": cells[9], "type": cells[10], "scope": cells[11]}
        elif cells[0] == "a" and len(cells) >= 4:
            assemblies.add(cells[3])
        elif cells[0] == "x" and len(cells) >= 3:
            skipped[cells[1]] = cells[2]
    for machine in methods.values():  # an async or iterator method's body is its state machine's
        written = methods.get(machine["kickoff"]) if machine["kickoff"] else None
        if written is not None and written["line"] is None:
            written.update(file=machine["file"], line=machine["line"])
    files = {method["type"]: method["file"] for method in methods.values() if method["file"]}
    for method in methods.values():  # a constructor the class does not write is in the class's file
        if method["file"] is None and method["kind"] == "constructor":
            method["file"] = files.get(method["type"])
    calls, outside, errors, processes = collections.defaultdict(set), set(), [], 0
    for path in sorted((Path(folder) / "calls").glob("*.jsonl")):
        processes += 1
        for text in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(text)
            except ValueError:
                continue  # the line a process was writing when it was killed
            if "call" in row:
                calls[row["call"][0]].add(row["call"][1])
            elif "outside" in row:
                outside.add(row["outside"])
            elif "error" in row:
                errors.append(str(row["error"]))
    observed = []
    for identity in sorted(set(calls) | outside):
        site = sites.get(identity)
        if site is None:
            continue
        callees = [methods[method] for method in sorted(calls.get(identity, ())) if method in methods]
        observed.append({**site, "callees": callees, "outside": identity in outside})
    return {"sites": observed, "assemblies": sorted(assemblies),
            "skipped": [{"assembly": name, "why": why} for name, why in sorted(skipped.items())],
            "processes": processes, "errors": list(dict.fromkeys(errors))}


def _units(line: str, column: int) -> int:
    """A byte column as the PDB counts it: UTF-16 units from 1, after the byte order mark Roslyn does not read."""
    head = line.encode("utf-8")[:column].decode("utf-8", errors="ignore").removeprefix("﻿")
    return len(head.encode("utf-16-le")) // 2 + 1


def _simple(type_name: str) -> str:
    """A type's name as the source writes it: `Shop.Orders/Line`1` is `Line`."""
    return type_name.rpartition("/")[2].rpartition(".")[2].partition("`")[0]


def _named(method: dict) -> tuple[str, str]:
    """The name a callee is declared under in the source, and its kind."""
    kind, name = method["kind"], method["name"]
    if kind == "constructor":
        return _simple(method["type"]), kind
    if kind == "lambda":
        return "(lambda)", kind
    if kind == "accessor":
        return name.partition("_")[2], kind
    if kind == "local":
        return name.partition(">g__")[2].partition("|")[0], "local function"
    return name, kind


def place(observed: dict, sources: list[str], text) -> tuple[list[dict], dict]:
    """The contract's sites from what the recorder saw (`read`), over the snapshot's C# `sources` (`text(rel)`
    their text), and what the placing says of itself: the sites `recorded`, `placed`, `ambiguous` (count and
    examples) and `unplaced` by cause (see the module docstring)."""
    import languages
    from edge_grading import callee_column
    files, parsed = set(sources), {}
    project = set(observed.get("assemblies") or ())

    def parse(rel: str) -> tuple[list[str], dict]:
        """The file's lines and its semantic facts, by the parser the snapshot's are from."""
        if rel not in parsed:
            content = text(rel) or ""
            try:
                result = languages.get_adapter("csharp").parse(content, rel)
                semantic = result.semantic if isinstance(result.semantic, dict) else {}
            except (ValueError, RecursionError):
                semantic = {}
            parsed[rel] = (content.split("\n"), semantic)
        return parsed[rel]

    def callee(method: dict) -> dict:
        name, kind = _named(method)
        rel, line, column = method["file"], method["line"], None
        if rel in files and kind in ("constructor", "lambda", "method"):
            # A constructor the class does not write has no line: the class is its declaration.
            spans = [tuple(item["span"]) for item in parse(rel)[1].get("declarations", ())
                     if item["kind"] in ("function", "method", "class") and item["name"] == name
                     and (item["span"][0] <= line <= item["span"][2] if line else item["kind"] == "class")]
            inner = [span for span in spans if not any(other != span and span[:2] <= other[:2] and other[2:] <= span[2:]
                                                      for other in spans)]
            if len(inner) == 1:
                line, column = inner[0][0], inner[0][1]
        file = rel if rel in files else f"{method['assembly']}::{method['type']}"
        return {"kind": "project", "file": file, "line": max((line or 1) - 1, 0), "column": column, "name": name,
                "type": kind}

    found, ambiguous, unplaced = collections.defaultdict(dict), [], collections.Counter()
    for site in observed["sites"]:
        rel = site["file"]
        if rel is None or site["line"] is None:
            unplaced["no statement in the PDB"] += 1
            continue
        if rel not in files:
            unplaced["no source file in the snapshot"] += 1
            continue
        lines, semantic = parse(rel)
        called = site["name"]
        names = {_simple(site["type"])} if called == ".ctor" else {called}
        reads = {called[4:]} if called.startswith(("get_", "set_")) else set()
        start = (site["line"], site["column"] or 0)
        end = (site["end_line"] or site["line"], site["end_column"] or 10**9)
        at = set()
        for reference in semantic.get("references", ()):
            parts, span = reference.get("parts") or [], reference["span"]
            if not parts or not (parts[-1] in names if reference["kind"] == "call" else parts[-1] in reads) \
                    or not 1 <= span[2] <= len(lines):
                continue
            column = callee_column(lines[span[2] - 1], list(span), parts[-1])
            if column is not None and start <= (span[2], _units(lines[span[2] - 1], column)) <= end:
                at.add((span[2], column, parts[-1]))
        if len(at) != 1:
            if at:
                ambiguous.append(f"{rel}:{site['line']} {called}")
            else:
                unplaced[NO_CALL] += 1
            continue
        [(line, column, name)] = at
        callees = found[(rel, line - 1, column, name)]
        for item in site["callees"]:
            item = callee(item)
            callees[json.dumps(item, sort_keys=True)] = item
        if site["outside"]:
            item = {"kind": "external", "module": site["type"].replace("/", "."), "name": called,
                    "assembly": site["scope"], **({"mock": True} if site["scope"] in project else {})}
            callees[json.dumps(item, sort_keys=True)] = item
    sites = [{"file": rel, "line": line, "column": column, "name": name, "role": "call",
              "callees": list(callees.values())} for (rel, line, column, name), callees in sorted(found.items())]
    return sites, {"recorded": len(observed["sites"]), "placed": len(observed["sites"]) - len(ambiguous)
                   - sum(unplaced.values()), "ambiguous": {"count": len(ambiguous),
                                                           "examples": sorted(set(ambiguous))[:EXAMPLES]},
                   "unplaced": dict(sorted(unplaced.items()))}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def _outcome(run: dict, code: str, log: str, ended: str) -> tuple[dict, list[dict]]:
    """One project's entry (`root`, `runner`, how its tests ended as `dynamic.TESTS` says) and its gaps, from the
    tests' exit code and the summary `dotnet test` printed (Microsoft.Testing.Platform's or VSTest's)."""
    counts = collections.Counter()
    for key, value in COUNT.findall(log):
        counts[key.lower()] += int(value)
    for failed, _passed, skipped, total in VSTEST.findall(log):
        counts.update(failed=int(failed), skipped=int(skipped), total=int(total))
    entry = {"root": run["root"], "runner": run["runner"], "state": "ran", "project": run["project"],
             "argv": run["argv"], "exit_code": int(code) if code.strip().lstrip("-").isdigit() else None,
             "tests": counts["total"], "failures": counts["failed"], "skipped": counts["skipped"]}
    command = f"{' '.join(run['argv'])} in {run['root'] or '.'}"
    tail = " | ".join(line.strip() for line in log.strip().splitlines()[-8:])[-600:]
    tests, exit_code = counts["total"], entry["exit_code"]

    def gap(kind: str, detail: str) -> dict:
        return {"kind": kind, "path": run["project"], "detail": detail}

    gaps = []
    if exit_code is None:
        entry["state"] = "not_started"
        gaps.append(gap("tests_not_started", f"{command}: the run ended before the tests' exit ({ended})"))
    elif exit_code == 124:
        entry["state"] = "timeout"
        gaps.append(gap("tests_timeout", f"{command} did not end in {LIMIT} s: what ran until then is observed"))
    elif exit_code == 137:
        entry["state"] = "killed"
        gaps.append(gap("tests_killed", f"{command} was killed before its end, at the container's memory limit "
                                        f"({csharp.MIN_FREE // 2**30} GB) or {LIMIT} s: what ran until then is "
                                        f"observed: {tail}"))
    elif not tests:
        entry["state"] = "no_tests" if exit_code in (0, 8) else "not_started"  # 8: the platform ran zero tests
        gaps.append(gap("no_tests", f"{command} ran no test") if entry["state"] == "no_tests" else
                    gap("tests_not_started", f"{command}: no test started (exit code {exit_code}): {tail}"))
    if counts["failed"]:
        first = FIRST.search(log)
        said = f"the first: {first[1].strip()}: {first[2].strip()}"[:600] if first else tail
        gaps.append(gap("tests_failed", f"{command}: {counts['failed']} of {tests} tests failed, and a test that "
                                        f"fails may stop before its calls: {said}"))
    return entry, gaps


def observe(project: Path, planned: dict, out_dir: Path, engine=None) -> dict:
    """The planned runs, in one container run over a copy of the checkout, read back from `out_dir`: `{state,
    sites, runs, gaps, facts}`, `state` `ran`, `gap` (no container: `cause`, `remedy`) or `failed` (the SDK or
    Daodan's projects could not be built: `cause`, `remedy`); a test project that did not build is a run
    `not_started` with its `tests_not_started` gap. `facts` is what the recorder and the placing say of
    themselves."""
    import container
    runs, out_dir = planned["runs"], Path(out_dir)
    if not runs:
        return {"state": "ran", "sites": [], "runs": [], "gaps": [], "facts": {}}  # the plan's gaps say why
    chains = preparation.toolchains(list(planned.get("toolchains") or ()))
    sdk = chains if chains["lines"] else preparation.setup(["dotnet"])  # the stated SDK, else the pin
    prepare, execute = scripts(runs, sdk["lines"])
    sources = {f"{AGENT}/{path.relative_to(RECORD).as_posix()}": path for path in sorted(RECORD.rglob("*"))
               if path.is_file() and not {"bin", "obj", "out"} & set(path.relative_to(RECORD).parts)}
    work = out_dir / "container"
    back = work / Path(OUT).name
    result = container.run_in_container(
        Path(project), ["bash", "-c", execute], image=csharp.IMAGE, out_dir=work, prepare=["bash", "-c", prepare],
        outputs=[OUT], env=dict(csharp.ENV), timeout=LIMIT * len(runs) + 600, memory=csharp.MIN_FREE,
        pids=csharp.PIDS, registries=(*csharp.REGISTRIES, *sdk["hosts"], *planned.get("declared", {}).get("hosts", ())),
        engine=engine, inputs=lambda: {**sources, f"{AGENT}/packages/{CECIL[2]}": preparation.fetched(*CECIL),
                                       **{f"{preparation.IN}/{name}": preparation.fetched(url, digest, name)
                                          for url, digest, name in sdk["files"]}})
    if result["state"] == "gap":
        return {"state": "gap", "cause": result["cause"], "remedy": result["remedy"], "sites": [], "runs": [],
                "gaps": [], "facts": {}}
    logs = {phase: _text(work / f"{phase}.log") for phase in ("prepare", "execute")}
    steps = {run["step"]: run for phase, log in logs.items() for run in jvm.steps(log, phase)}
    gaps = [*result.get("gaps", []), *chains["gaps"], *preparation.missing(logs["prepare"])]
    stopped = next((steps.get(name) for name in ("sdk", "agent") if (steps.get(name) or {}).get("returncode")), None)
    if stopped is not None or "agent" not in steps:
        tail = ((stopped or {}).get("stderr_tail") or "").strip()[-800:]
        cause = result.get("cause") or ("the .NET SDK or Daodan's recorder did not build" if stopped else
                                        "the preparation did not reach the recorder's build")
        return {"state": "failed", "cause": f"{cause}: {tail}" if tail else cause, "sites": [], "runs": [],
                "gaps": gaps, "remedy": f"see prepare.log and execute.log in {work}", "facts": {}}
    entries = []
    for number, run in enumerate(runs, 1):
        built = steps.get(f"build-{number}")
        if built is None or built["returncode"]:
            tail = ((built or {}).get("stderr_tail") or "").strip().splitlines()[-6:]
            entries.append({"root": run["root"], "runner": run["runner"], "state": "not_started",
                            "project": run["project"], "argv": run["argv"]})
            gaps.append({"kind": "tests_not_started", "path": run["project"], "detail": f"{run['project']} did not "
                         f"build: {' | '.join(line.strip() for line in tail)[-600:] or 'the preparation ended first'}"})
            continue
        entry, own = _outcome(run, _text(back / f"tests-{number}.code"), _text(back / f"tests-{number}.log"),
                              result["state"])
        entries.append(entry)
        gaps += own
    rewrite = steps.get("rewrite") or {}
    if rewrite.get("returncode"):
        gaps.append({"kind": "recorder_failed", "detail": "the rewriter stopped, and what it did not rewrite ran "
                     f"unrecorded: {(rewrite.get('stderr_tail') or '').strip()[-400:]}"})
    observed = read(back)
    sites, said = place(observed, planned.get("sources") or [], lambda rel: _text(Path(project) / rel))
    ran = sum(entry["tests"] for entry in entries if entry["state"] in ("ran", "timeout", "killed"))
    if ran and not observed["processes"]:
        gaps.append({"kind": "not_observed", "detail": f"{ran} tests ran and no process recorded a call: the tests "
                     "ran without DOTNET_STARTUP_HOOKS, or the rewriter rewrote no assembly they loaded"})
    if observed["skipped"]:
        first = observed["skipped"][0]
        gaps.append({"kind": "assemblies_unrecorded", "detail": f"{len(observed['skipped'])} assemblies of the "
                     f"project ran as built, unrecorded: the rewriter could not rewrite them ({first['assembly']}: "
                     f"{first['why'][:200]})"})
    if observed["errors"]:
        gaps.append({"kind": "recorder_failed", "detail": f"the recorder stopped in some process: "
                                                          f"{observed['errors'][0][:300]}"})
    if said["ambiguous"]["count"]:
        gaps.append({"kind": "sites_ambiguous", "detail": f"{said['ambiguous']['count']} observed call sites share "
                     "their statement with another call of the same name, so the reference each answers is unknown "
                     f"and they are not placed: {', '.join(said['ambiguous']['examples'][:3])}"})
    facts = {"processes": observed["processes"], "assemblies": len(observed["assemblies"]),
             "skipped": len(observed["skipped"]), **said}
    return {"state": "ran", "sites": sites, "runs": entries, "gaps": gaps, "facts": facts}
