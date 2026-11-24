"""What `scan` costs on the corpus (spec 8.10, 8.11 step 5 pieces D and E1), measured on Modal in three parts.

Nothing of a project runs: its files are read, and the pre-map is the recorded one (`tools/premap_replay.py`: each model
command is answered from `results/premap-runs/<name>.json.gz`, so no number here holds the container's time). The Daodan
code is the clone of HEAD that `DAODAN_SCRIPTS` names, as `modal_pipeline.py` uploads it.

A. Per reason of exclusion (the `why` of the pre-map's `excluded` facet), the files the reading reads and the pre-map then
   labels excluded (`excluded` below, which `pipeline.plan` had until the owner's decision of 24 November 2026 to keep one
   reading: the product's reading leaves out no file now): files, those a parser read, bytes, symbols, and the resolved
   imports that cross the line. The snapshot is the whole reading (the inventory, then `snapshot.write_reading`).
B. On the real projects, `repetitions` times, one after the other: the inventory (`file_inventory.write`), the reading
   (`snapshot.write_reading`), the single pass (`snapshot.build_manifest`) and, inside the reading, the seconds spent in
   `snapshot._read_source` (stat and bytes of each file, which the inventory has read before) and in `_SnapshotPass.seal`
   (the semantic store and the publication). Medians.
C. Angular: the TypeScript files whose tree `premap.angular` reads now and before 648efd2b7, and its seconds; and the
   rhythm of `premap.angular._components` on the TypeScript files of every project, to size it on the largest.
D. (`--languages`, `results/scan-cost/languages.json`) the language go-enry gives each file against the inventory's
   (`file_inventory.write`), from the recorded answer of `daodan-enry .` alone: the pairs that differ, by kind, with examples.
E. In the same mode, the files each reason of exclusion holds, `submodule` too, and the entries `.gitmodules` states.

    PYTHONUTF8=1 python -m modal run benchmarks/project-model/modal_scan_cost.py --cases js-angular,mix-real-klaxon --out OUT.json
    DAODAN_SCRIPTS=<clean clone>/daodan/core python -m modal run benchmarks/project-model/modal_scan_cost.py

The function has a fixed machine (`CPU`, `MEMORY`: request = limit); each real project has a function call of its own, the
miniatures go in groups of `--chunk`. The result lands in `results/scan-cost/scan-cost.json`: counts and seconds, no source.
"""
from __future__ import annotations

import collections
import gc
import gzip
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import traceback
import types
from pathlib import Path, PurePosixPath

import modal

import modal_pipeline as mp

HERE = Path(__file__).resolve().parent
BENCH = "/bench/project-model"  # the repository's layout, two levels deep: `premap_replay` finds its folders from its path
TOOLS = ("premap_replay.py", "daodan_modules.py", "native_common.py")  # what `premap_replay` imports from `tools/`
ARCHIVES = Path("/results/project-model/native-real")  # the volume: a real repository's archive, as `modal_native.py prepare` keeps it
OUT = HERE / "results/scan-cost/scan-cost.json"
CPU, MEMORY, REPS = 4.0, 16384, 3  # the function's cores and megabytes (request = limit); the repetitions of measure B
TIMEOUT = 4 * 3600  # seconds a project may take: with 7200 two of the biggest ended unmeasured
CORPORA = ("miniature", "real")
PARSED = ("parsed", "parse-error")  # the statuses of a file a parser read
DECORATOR = ("@angular/core", "Component")  # what the rule before 648efd2b7 looked for in the imports of a TypeScript file
SUMS = ("files", "parsed", "bytes", "parsed_bytes", "symbols", "to_pairs", "to_importers", "from_pairs")
READING = ("inventory", "reading", "seal", "pass", "reread", "reread_files", "reread_bytes")

image = mp.image.add_local_file(HERE / "modal_pipeline.py", "/root/modal_pipeline.py")
if mp.LOCAL:
    image = image.add_local_dir(HERE / "results/premap-runs", f"{BENCH}/results/premap-runs")
    for _tool in TOOLS:
        image = image.add_local_file(HERE / "tools" / _tool, f"{BENCH}/tools/{_tool}")
app = modal.App("daodan-scan-cost")


# ------------------------------------------------------------------ the pure part

def excluded(rows, record) -> dict[str, str]:
    """The files of `rows` that an entry of the pre-map's `excluded` facet holds (the entry's path, a file under a folder
    entry ending in `/`, or any file for `.`), each with the `why` of the outermost entry that holds it (the first one, of
    several for the same path). It is `pipeline.plan.excluded` as that was, kept here so the measure can be run again."""
    held: dict[str, str] = {}
    for entry in ((record or {}).get("excluded") or []):
        held.setdefault(entry["path"].rstrip("/") or ".", entry.get("why") or "excluded")
    if not held:
        return {}
    found = {}
    for path, _row in rows:  # each file's ancestors, not `premap._inside` pairwise: files x entries (go-enry lists thousands)
        parts = path.split("/")
        for why in (held.get(".") or None, *(held.get("/".join(parts[:cut])) for cut in range(1, len(parts) + 1))):
            if why:
                found[path] = why
                break
    return found


def by_reason(held: dict, headers: dict, symbols: dict) -> dict:
    """Per reason of exclusion, what the files `held` (`{path: why}`) are: how many, how many a parser read (`PARSED`) and
    their bytes, the statuses and languages of the lot, and the symbols they hold (`symbols`: a count per path)."""
    found = {}
    for path, why in held.items():
        header = headers.get(path) or {}
        item = found.setdefault(why, {"files": 0, "parsed": 0, "statuses": {}, "bytes": 0, "parsed_bytes": 0,
                                      "symbols": 0, "languages": {}})
        status, size, language = header.get("status", "missing"), header.get("size", 0), header.get("language") or "none"
        item["files"] += 1
        item["bytes"] += size
        item["symbols"] += symbols.get(path, 0)
        item["statuses"][status] = item["statuses"].get(status, 0) + 1
        item["languages"][language] = item["languages"].get(language, 0) + 1
        if status in PARSED:
            item["parsed"] += 1
            item["parsed_bytes"] += size
    return found


def top_folders(held: dict, headers: dict, symbols: dict, limit: int = 5) -> dict:
    """Per reason, the folders (the first two segments of the path, `.` for a file at the root) that hold most of the files
    a parser read, with their files and symbols: where the code that the reason would drop lies."""
    found = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    for path, why in held.items():
        if (headers.get(path) or {}).get("status") in PARSED:
            entry = found[why]["/".join(path.split("/")[:-1][:2]) or "."]
            entry[0] += 1
            entry[1] += symbols.get(path, 0)
    return {why: [{"folder": folder, "files": files, "symbols": count}
                  for folder, (files, count) in sorted(folders.items(), key=lambda item: (-item[1][0], item[0]))[:limit]]
            for why, folders in found.items()}


def import_pairs(resolved: dict, held: dict) -> dict:
    """The resolved imports (`{importer: {specifier: [targets]}}`) that cross the line of the files `held` (`{path: why}`),
    as distinct (importer, target) pairs per reason: `to`, from a file that stays to one that goes (with the importers
    they come from), and `from`, from one that goes to one that stays."""
    to, out = collections.defaultdict(set), collections.defaultdict(set)
    for importer, specifiers in resolved.items():
        for target in {target for targets in specifiers.values() for target in targets}:
            if importer in held and target not in held:
                out[held[importer]].add((importer, target))
            elif target in held and importer not in held:
                to[held[target]].add((importer, target))
    return {"to": {why: {"pairs": len(pairs), "importers": len({importer for importer, _ in pairs})}
                   for why, pairs in to.items()},
            "from": {why: {"pairs": len(pairs)} for why, pairs in out.items()}}


def summarize(fixtures: dict) -> dict:
    """The projects' records added up per corpus and per reason. A project whose exclusions are not known (go-enry's
    answer is not recorded, or it has no recording) is counted apart, in `incomplete` with what is missing; the commands
    not recorded (their number per tool, any project) are in `not_recorded`; a project that failed is in `failed`."""
    found = {corpus: {"projects": 0, "files": 0, "parsed": 0, "excluded": 0, "by_reason": {}} for corpus in CORPORA}
    incomplete, failed, tools = {}, {}, collections.Counter()
    for name, item in sorted(fixtures.items()):
        if "error" in item:
            failed[name] = item["error"]
            continue
        tools.update(item["not_recorded"])
        if not item["known"]:
            incomplete[name] = {"corpus": item["corpus"], "not_recorded": item["not_recorded"]}
        else:
            total = found[item["corpus"]]
            total["projects"] += 1
            total["files"] += item["files"]
            total["parsed"] += item["parsed_files"]
            total["excluded"] += item["excluded"]["files"]
            for why, entry in item["excluded"]["by_reason"].items():
                row = total["by_reason"].setdefault(why, {"projects": 0, **dict.fromkeys(SUMS, 0)})
                row["projects"] += 1
                for key in SUMS:
                    row[key] += entry.get(key, 0)
    return {**found, "incomplete": incomplete, "not_recorded": dict(tools), "failed": failed}


def median_runs(runs: list[dict]) -> dict:
    """The median of each measure over the repetitions."""
    return {key: round(statistics.median(run[key] for run in runs), 4) for key in runs[0]}


def reading_totals(fixtures: dict) -> dict:
    """The medians of measure B added up over the real projects that have them, the share of the re-read bytes in the
    inventory and the reading together, and the five projects that take longest."""
    medians = {name: item["reading"]["median"] for name, item in fixtures.items() if item.get("reading")}
    total = {key: round(sum(row[key] for row in medians.values()), 3) for key in READING}
    scan = total["inventory"] + total["reading"]
    slowest = sorted(medians, key=lambda name: -(medians[name]["inventory"] + medians[name]["reading"]))[:5]
    return {"projects": len(medians), **total, "reread_share": round(total["reread"] / scan, 4) if scan else None,
            "repetitions": dict(collections.Counter(len(fixtures[name]["reading"]["runs"]) for name in medians)),
            "slowest": [{"project": name, "files": fixtures[name]["files"], "bytes": fixtures[name]["bytes"],
                         **medians[name]} for name in slowest]}


def old_component_files(headers: dict, module: str, decorator: str) -> list[str]:
    """The TypeScript files that import `decorator` from `module`: the files `premap.angular` read before 648efd2b7."""
    return [path for path, header in headers.items() if header.get("language") == "typescript"
            and any(item.get("module") == module and decorator in item.get("names", ())
                    for item in header.get("import_bindings") or ())]


def rate(files: int, size: int, seconds: float) -> dict | None:
    """Files and megabytes per second; none without time."""
    if not seconds:
        return None
    return {"files_per_second": round(files / seconds, 2), "mb_per_second": round(size / 2**20 / seconds, 2)}


def largest(samples: dict) -> str | None:
    """The project with most bytes of TypeScript (`samples[name]["typescript"]`), none if no project has any."""
    sized = {name: (item.get("typescript") or {}).get("bytes", 0) for name, item in samples.items()}
    best = max(sized, key=sized.get, default=None)
    return best if best and sized[best] else None


def rhythm(fixtures: dict) -> dict:
    """The rhythm of `_components` on the largest project's TypeScript, and on all of them together."""
    sweeps = {name: item["typescript"] for name, item in fixtures.items() if item.get("typescript")}
    name = largest(fixtures)
    total = {key: sum(item[key] for item in sweeps.values()) for key in ("files", "bytes", "seconds")}
    return {"largest": {"project": name, **sweeps[name], **(rate(sweeps[name]["files"], sweeps[name]["bytes"],
                                                                  sweeps[name]["seconds"]) or {})} if name else None,
            "all": {"projects": len(sweeps), **total, **(rate(total["files"], total["bytes"], total["seconds"]) or {})}}


# ------------------------------------------------------------------ the languages: go-enry against the inventory

# What `premap.suffix_table.NAMES` (Daodan's name -> Linguist's, with `premap.ALSO`) does not say: the Linguist names that a
# coarse name of Daodan covers, from its extension table (`languages.SUPPORTED_EXTENSIONS`), and the one Linguist spells apart.
FAMILIES = {
    "css": ("CSS", "SCSS", "Sass", "Less", "PostCSS"),
    "markup": ("HTML", "HTML+ERB", "HTML+Razor", "EJS", "FreeMarker", "Handlebars", "Jinja", "Java Server Pages", "Liquid",
               "Mustache", "Nunjucks", "Twig", "Velocity Template Language"),
    "javascript": ("JSX",),
}
NONE = "(none)"
SUFFIXES = (".h", ".ts", ".sql")  # the languages Daodan gives by the text too (`languages.detect_language`)
KINDS = ("a-reads-other", "a-unreadable", "a-enry-none", "b-readable", "b-other")
LANGUAGES_OUT = HERE / "results/scan-cost/languages.json"


def equivalents(names: dict, also: dict) -> dict:
    """Each language of Daodan with the Linguist names that mean it: the product's own table (`names`, `also`) and `FAMILIES`."""
    return {language: frozenset([*([names[language]] if language in names else ()), *also.get(language, ()),
                                 *FAMILIES.get(language, ())])
            for language in {*names, *also, *FAMILIES}}


def language_pairs(rows, enry: dict, same: dict, limit: int = 2) -> dict:
    """The inventory's `rows` (`(path, {"language": ...})`) against go-enry's answer (`enry`, `{path: language}`): only the files
    of `rows` count, one go-enry does not list is `no_answer`. `agree` where go-enry's name is one of those that mean Daodan's
    (`same`), `both_none` where neither has a language, and the rest as `pairs` (`"<go-enry> -> <Daodan>"`, `(none)` for none),
    each with `limit` example paths. For the `SUFFIXES`, the pairs of every file, those that agree too."""
    found = {"files": 0, "agree": 0, "both_none": 0, "no_answer": 0, "pairs": collections.Counter(), "suffix": {},
             "examples": {}}
    for path, row in rows:
        found["files"] += 1
        if path not in enry:
            found["no_answer"] += 1
            continue
        theirs, daodan = enry[path] or None, row.get("language") or None
        pair = f"{theirs or NONE} -> {daodan or NONE}"
        suffix = PurePosixPath(path).suffix.lower()
        if suffix in SUFFIXES:
            found["suffix"].setdefault(suffix, collections.Counter())[pair] += 1
        if theirs is None and daodan is None:
            found["both_none"] += 1
        elif daodan is not None and theirs in same.get(daodan, ()):
            found["agree"] += 1
        else:
            found["pairs"][pair] += 1
            seen = found["examples"].setdefault(pair, [])
            if len(seen) < limit:
                seen.append(path)
    return {**found, "pairs": dict(found["pairs"]), "suffix": {key: dict(value) for key, value in found["suffix"].items()}}


def classify(theirs: str | None, daodan: str | None, readable) -> str:
    """What a pair of languages that differ is. `a-`: Daodan gives the file a language (so a parser reads it) and go-enry
    another: the file `a-reads-other` (go-enry's language is one Daodan reads, `readable`), `a-unreadable` (it is not: the file
    would be file-level) or go-enry gives it none (`a-enry-none`). `b-`: Daodan gives none and go-enry one, `b-readable` or `b-other`."""
    if daodan is not None:
        return "a-enry-none" if theirs is None else "a-reads-other" if theirs in readable else "a-unreadable"
    return "b-readable" if theirs in readable else "b-other"


def summarize_languages(fixtures: dict, same: dict) -> dict:
    """The projects of `language_pairs` added up per corpus: the pairs that differ by kind (`classify`) with the most frequent ten
    of each and an example, the pairs of the `SUFFIXES`, and the exclusion entries and files per reason (measure E). A project
    without a recording is in `not_recorded`."""
    readable = set().union(*same.values()) if same else set()
    found = {corpus: {"projects": 0, "files": 0, "agree": 0, "both_none": 0, "no_answer": 0, "differ": 0} for corpus in CORPORA}
    pairs = {corpus: {kind: {} for kind in KINDS} for corpus in CORPORA}
    suffixes = {corpus: {} for corpus in CORPORA}
    excluded = {"entries": collections.Counter(), "files": collections.Counter(), "projects": collections.Counter()}
    not_recorded = []
    for name, item in sorted(fixtures.items()):
        if not item.get("recorded"):
            not_recorded.append(name)
            continue
        compare, total = item["compare"], found[item["corpus"]]
        total["projects"] += 1
        for key in ("files", "agree", "both_none", "no_answer"):
            total[key] += compare[key]
        total["differ"] += sum(compare["pairs"].values())
        for pair, count in compare["pairs"].items():
            theirs, daodan = (None if part == NONE else part for part in pair.split(" -> "))
            entry = pairs[item["corpus"]][classify(theirs, daodan, readable)].setdefault(
                pair, {"pair": pair, "files": 0, "projects": 0, "example": f"{name}: {compare['examples'][pair][0]}"})
            entry["files"] += count
            entry["projects"] += 1
        for suffix, counts in compare["suffix"].items():
            counter = suffixes[item["corpus"]].setdefault(suffix, collections.Counter())
            counter.update(counts)
        for why, count in item["excluded"]["entries"].items():
            excluded["entries"][why] += count
            excluded["projects"][why] += count > 0
        for why, count in item["excluded"]["files"].items():
            excluded["files"][why] += count

    def agrees(pair: str) -> bool:
        theirs, daodan = pair.split(" -> ")
        return daodan != NONE and theirs in same.get(daodan, ())

    for corpus in CORPORA:
        found[corpus]["classes"] = {kind: {"files": sum(entry["files"] for entry in table.values()),
                                         "pairs": sorted(table.values(), key=lambda entry: (-entry["files"], entry["pair"]))[:10]}
                                  for kind, table in pairs[corpus].items()}
        found[corpus]["suffix"] = {suffix: [{"pair": pair, "files": count, "agrees": agrees(pair)}
                                            for pair, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]
                                   for suffix, counter in sorted(suffixes[corpus].items())}
    return {**found, "excluded": {key: dict(value) for key, value in excluded.items()}, "not_recorded": not_recorded}


# ------------------------------------------------------------------ what runs on Modal

class Counted:
    """`premap.angular._components`, the reader of a TypeScript file's tree, counted while this is entered: its calls, the
    bytes of the files it is given (their size in the inventory) and its seconds, in all and of each file."""

    def __init__(self):
        from premap import angular
        self.angular, self.original = angular, angular._components
        self.calls, self.bytes, self.seconds, self.by_file = 0, 0, 0.0, {}

    def __enter__(self):
        self.angular._components = self.call
        return self

    def __exit__(self, *_):
        self.angular._components = self.original

    def call(self, context, file, gaps):
        started = time.perf_counter()
        try:
            return self.original(context, file, gaps)
        finally:
            spent = time.perf_counter() - started
            self.calls += 1
            self.bytes += (context.inventory.headers.get(file) or {}).get("size", 0)
            self.seconds += spent
            self.by_file[file] = self.by_file.get(file, 0.0) + spent


def machine() -> dict:
    """What the function ran on, as it can be read from inside."""
    try:
        model = next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                      if line.startswith("model name")), None)
    except OSError:
        model = None
    return {"cpu_request": CPU, "memory_mb": MEMORY, "cpu_model": model, "cpus_seen": os.cpu_count(),
            "cpus_allowed": len(os.sched_getaffinity(0)), "python": sys.version.split()[0]}


def passes(project: Path, folder: Path) -> dict:
    """One repetition of measure B on `project`: the inventory, the reading and the single pass, one after the other on
    the same files, whose cache is warm (the project has just been unpacked, and the inventory has just read it). The
    reading's store stays in `folder` as `manifest.sqlite`."""
    import file_inventory
    import snapshot
    folder.mkdir(parents=True)
    inventory, manifest = folder / "inventory.sqlite", folder / "manifest.sqlite"
    started = time.perf_counter()
    file_inventory.write(project, inventory)
    seconds = {"inventory": time.perf_counter() - started}
    spent, original = {"reread": 0.0, "reread_files": 0, "reread_bytes": 0}, snapshot._read_source
    seal = snapshot._SnapshotPass.seal

    def reading(path, supplied, metrics):  # `_SnapshotPass.sources` calls its own global, imported from `file_inventory`
        started = time.perf_counter()
        try:
            read = original(path, supplied, metrics)
        finally:
            spent["reread"] += time.perf_counter() - started
        spent["reread_files"] += 1
        spent["reread_bytes"] += len(read[1]) if read else 0
        return read

    def sealing(self, *args):
        started = time.perf_counter()
        try:
            return seal(self, *args)
        finally:
            seconds["seal"] = time.perf_counter() - started

    snapshot._read_source, snapshot._SnapshotPass.seal = reading, sealing
    try:
        started = time.perf_counter()
        snapshot.write_reading(inventory, manifest)
        seconds["reading"] = time.perf_counter() - started
    finally:
        snapshot._read_source, snapshot._SnapshotPass.seal = original, seal  # `build_manifest` reads through the same name
    inventory.unlink()
    started = time.perf_counter()
    snapshot.build_manifest(project)
    seconds["pass"] = time.perf_counter() - started
    gc.collect()
    return {**{key: round(value, 4) for key, value in seconds.items()}, **spent, "reread": round(spent["reread"], 4)}


def angular_facts(manifest: Path, store, headers: dict, before: list[str], record: dict | None,
                  whole: Counted) -> dict | None:
    """Measure C for a project that declares Angular: the trees `commands` reads (on a Context of its own, nothing of the
    files cached), what the rule before 648efd2b7 chose (`before`), and the pre-map's own counts when it ran."""
    import premap
    from premap import angular, frameworks
    folders = frameworks.folders(premap.Context(manifest, store), angular.PACKAGES)
    if not folders:
        return None
    with Counted() as now:
        started = time.perf_counter()
        commands = angular.commands(premap.Context(manifest, store))
        seconds = time.perf_counter() - started
    source = next((item for item in (record or {}).get("sources", ()) if item["source"].startswith("angular@")), None)
    return {"folders": len(folders), "typescript_files": sum(1 for h in headers.values() if h.get("language") == "typescript"),
            "before_files": len(before),
            "before_bytes": sum(headers[path].get("size", 0) for path in before), "commands": len(commands or ()),
            "commands_seconds": round(seconds, 4), "trees": now.calls, "tree_bytes": now.bytes,
            "tree_seconds": round(now.seconds, 4), "premap_trees": whole.calls, "premap_tree_seconds": round(whole.seconds, 4),
            "source": {"state": source["state"], "seconds": source["seconds"]} if source else None}


def typescript_rhythm(manifest: Path, store, ts_files: list[str], before: list[str]) -> dict:
    """`_components` on each TypeScript file of the project, on a Context whose texts are not cached: its seconds hold the
    read of the bytes, the hash check, the decoding, the tree and the query."""
    import premap
    from premap import angular
    context, gaps, errors = premap.Context(manifest, store), [], 0
    with Counted() as sweep:
        for file in ts_files:
            try:
                angular._components(context, file, gaps)
            except (OSError, ValueError):
                errors += 1
    return {"files": sweep.calls, "bytes": sweep.bytes, "seconds": round(sweep.seconds, 4), "errors": errors,
            "before_seconds": round(sum(sweep.by_file.get(path, 0.0) for path in before), 4)}


def lay_out(name: str, work: Path) -> tuple[Path, bool]:
    """The project as the recording's container laid it out (`premap_replay`): a miniature copied whole, `expected.json` too, a
    real one unpacked from its archive on the volume. Its path, and whether it is a real one."""
    import premap_replay as replay
    fixture = Path(mp.REMOTE_PM) / "fixtures" / name
    if not (fixture / "source.json").is_file():
        return Path(shutil.copytree(fixture, work / name)), False
    if not (ARCHIVES / f"{name}.tar.gz").is_file():
        raise FileNotFoundError(f"no archive of {name} on the volume")
    return replay.real_project(name, ARCHIVES, work), True


def one(name: str, reps: int, work: Path) -> dict:
    """The three measures on one project of the corpus."""
    import premap
    import premap_replay as replay
    import snapshot
    from snapshot_store import open_snapshot
    started = time.perf_counter()
    project, real = lay_out(name, work)
    out = {"corpus": "real" if real else "miniature"}
    runs, count = [], reps if real else 1  # a miniature is read once: its seconds are not measured
    for number in range(count):
        folder = work / "out" / str(number)
        if real:
            runs.append(passes(project, folder))
        else:
            folder.mkdir(parents=True)
            snapshot.write_snapshot(project, folder / "manifest.sqlite")
        manifest = folder / "manifest.sqlite"
        if number < count - 1:  # the last store is the one the pre-map reads
            shutil.rmtree(folder)
    if runs:
        out["reading"] = {"runs": runs, "median": median_runs(runs)}
    recording = replay.RUNS / f"{name}.json.gz"
    record, missing, whole = None, [], None
    if recording.is_file():
        data = json.loads(gzip.decompress(recording.read_bytes()).decode("utf-8"))
        with Counted() as whole:
            started_premap = time.perf_counter()
            record = premap.write(manifest, runner=replay.replayer(data, missing))
            out["premap_seconds"] = round(time.perf_counter() - started_premap, 4)
    not_recorded = dict(collections.Counter(command["tool"] for command in missing))
    if record is None:
        not_recorded["(no recording)"] = 1
    # the exclusions are go-enry's answer and `.gitmodules`, which is read: a command of another tool changes none of them
    known = record is not None and not any(gap["kind"] == "model_failed" and str(gap.get("source", "")).startswith("go-enry")
                                           for gap in record["gaps"])
    out.update(known=known, not_recorded=not_recorded)
    with open_snapshot(manifest) as store:
        headers = dict(store.iter_file_headers_only())
        out.update(files=len(headers), bytes=sum(header.get("size", 0) for header in headers.values()),
                   parsed_files=sum(1 for header in headers.values() if header.get("status") in PARSED))
        if record is not None:
            held = excluded(list(store.iter_inventory()), record)
            symbols = dict(store.connection.execute("SELECT file, COUNT(*) FROM symbols GROUP BY file")) if held else {}
            reasons = by_reason(held, headers, symbols)
            pairs = import_pairs(snapshot.resolved_imports(store) if held else {}, held)
            for why, item in reasons.items():
                item.update(to_pairs=pairs["to"].get(why, {}).get("pairs", 0),
                            to_importers=pairs["to"].get(why, {}).get("importers", 0),
                            from_pairs=pairs["from"].get(why, {}).get("pairs", 0))
            # No `reading_leaves_out` check: it compared `excluded` with the files `write_reading(record=...)` left out, and the
            # reading takes no pre-map now (24 November 2026). The recorded results keep the check as it was run.
            out["excluded"] = {"files": len(held), "by_reason": reasons, "parsed_in": top_folders(held, headers, symbols)}
        ts_files = [path for path, header in headers.items() if header.get("language") == "typescript"]
        before = old_component_files(headers, *DECORATOR)
        out["angular"] = angular_facts(manifest, store, headers, before, record, whole or Counted())
        out["typescript"] = typescript_rhythm(manifest, store, ts_files, before) if ts_files else None
    out["seconds"] = round(time.perf_counter() - started, 1)
    return out


@app.function(image=image, cpu=(CPU, CPU), memory=(MEMORY, MEMORY), timeout=TIMEOUT, volumes={"/results": mp.volume})
def measure(names: list, reps: int = REPS) -> dict:
    sys.path[:0] = [mp.REMOTE_SCRIPTS, mp.REMOTE_PM, f"{BENCH}/tools"]
    answer = {"machine": machine(), "fixtures": {}}
    for name in names:
        work = Path(tempfile.mkdtemp(prefix=f"scan-cost-{name}-"))
        try:
            answer["fixtures"][name] = one(name, reps, work)
        except Exception as error:  # noqa: BLE001 - a project's failure is its result
            answer["fixtures"][name] = {"error": f"{type(error).__name__}: {error}", "trace": traceback.format_exc()[-1500:]}
        finally:
            shutil.rmtree(work, ignore_errors=True)
    return answer


def languages_one(name: str, work: Path, same: dict) -> dict:
    """Measures D and E on one project, from its inventory and the recorded answer of `daodan-enry .` alone: no snapshot, no
    pre-map. The exclusion entries are what `premap.enry.read` and `premap.gitmodules.run` state, in the pre-map's order (a
    reader's first), and the files they hold `excluded`."""
    import file_inventory
    import premap_replay as replay
    from premap import enry, gitmodules
    from snapshot_store import open_snapshot
    project, real = lay_out(name, work)
    out = {"corpus": "real" if real else "miniature", "recorded": False}
    recording = replay.RUNS / f"{name}.json.gz"
    if not recording.is_file():
        return out
    data = json.loads(gzip.decompress(recording.read_bytes()).decode("utf-8"))
    result = next((run["result"] for run in data["runs"] if run["command"]["tool"] == "daodan-enry"), None)
    if result is None:
        return out
    inventory = work / "inventory.sqlite"
    file_inventory.write(project, inventory)
    with open_snapshot(inventory) as store:
        rows = list(store.iter_inventory())
    answered = json.loads(result["stdout"]) if result["returncode"] == 0 else []
    # a dot folder is outside the map's perimeter: `premap.enry.read` leaves its files out, so does this
    theirs = {row["path"]: row.get("language") or None for row in answered
              if not any(part.startswith(".") for part in row["path"].split("/")[:-1])}
    submodules = gitmodules.run(types.SimpleNamespace(root=project)) or {}
    entries = [*submodules.get("facts", {}).get("excluded", []), *enry.read(None, None, [result])["facts"].get("excluded", [])]
    held = collections.Counter(excluded(rows, {"excluded": entries}).values())
    stated = collections.Counter(entry["why"] for entry in entries)
    out.update(recorded=True, compare=language_pairs(rows, theirs, same),
               excluded={"entries": dict(stated), "files": {why: held.get(why, 0) for why in {*stated, *held}}},
               submodule_absent=sum(1 for gap in submodules.get("gaps", []) if gap["kind"] == "submodule_absent"))
    return out


@app.function(image=image, cpu=(CPU, CPU), memory=(MEMORY, MEMORY), timeout=3600, volumes={"/results": mp.volume})
def inventory_languages(names: list) -> dict:
    sys.path[:0] = [mp.REMOTE_SCRIPTS, mp.REMOTE_PM, f"{BENCH}/tools"]
    from premap import ALSO, suffix_table
    same = equivalents(suffix_table.NAMES, ALSO)
    answer = {"machine": machine(), "equivalents": {key: sorted(value) for key, value in same.items()}, "fixtures": {}}
    for name in names:
        work = Path(tempfile.mkdtemp(prefix=f"scan-cost-languages-{name}-"))
        try:
            answer["fixtures"][name] = languages_one(name, work, same)
        except Exception as error:  # noqa: BLE001 - a project's failure is its result
            answer["fixtures"][name] = {"error": f"{type(error).__name__}: {error}", "trace": traceback.format_exc()[-1500:]}
        finally:
            shutil.rmtree(work, ignore_errors=True)
    return answer


def save(target: Path, runs: list, machines: list, fixtures: dict) -> None:
    """The result so far: `runs` the calls that made it (each its code, cases and repetitions), the first one's code is `code`."""
    document = {"code": runs[0]["code"], "runs": runs, "machine": machines, "summary": summarize(fixtures),
                "reading": reading_totals(fixtures), "rhythm": rhythm(fixtures) if fixtures else None,
                "fixtures": dict(sorted(fixtures.items()))}
    target.write_text(json.dumps(document, indent=1), encoding="utf-8")


def languages_main(batches: list, target: Path) -> None:
    """Measures D and E on `batches`, the languages of go-enry against the inventory's: `results/scan-cost/languages.json`."""
    ran, fixtures, machines, same = mp.code(mp.REPO, mp.UPLOADED), {}, [], {}
    for answer in inventory_languages.map(batches, order_outputs=False, return_exceptions=True):
        if isinstance(answer, Exception):
            print("a container failed:", answer, flush=True)
            continue
        fixtures.update(answer["fixtures"])
        same = {key: frozenset(value) for key, value in answer["equivalents"].items()}
        machines += [answer["machine"]] if answer["machine"] not in machines else []
        document = {"code": ran, "machine": machines, "equivalents": answer["equivalents"],
                    "summary": summarize_languages(fixtures, same), "fixtures": dict(sorted(fixtures.items()))}
        target.write_text(json.dumps(document, indent=1), encoding="utf-8")
        for name, item in answer["fixtures"].items():
            print(name, item.get("error") or {key: item.get(key) for key in ("corpus", "recorded")}, flush=True)
    print("ran", len(fixtures), "->", target, flush=True)


@app.local_entrypoint()
def main(cases: str = "mini,real", out: str = "", chunk: int = 8, reps: int = REPS, resume: bool = False,
         languages: bool = False):
    names = sorted(p.name for p in (HERE / "fixtures").iterdir() if (p / "expected.json").is_file())
    real = [name for name in names if (HERE / "fixtures" / name / "source.json").is_file()]
    batches = []
    for spec in filter(None, cases.split(",")):
        if spec == "mini":
            small = [name for name in names if name not in real]
            batches += [small[i:i + chunk] for i in range(0, len(small), chunk)]
        elif spec == "real":
            group = chunk if languages else 1  # an inventory is quick: several real projects in one function
            batches += [real[i:i + group] for i in range(0, len(real), group)]
        else:
            batches.append([spec])
    target = Path(out or (LANGUAGES_OUT if languages else OUT))
    target.parent.mkdir(parents=True, exist_ok=True)
    if languages:
        return languages_main(batches, target)
    ran, fixtures, machines, runs = mp.code(mp.REPO, mp.UPLOADED), {}, [], []
    scripts = Path(os.environ.get("DAODAN_SCRIPTS") or mp.REPO / "daodan/core")  # the commit of what was uploaded
    ran["scripts_commit"] = subprocess.run(["git", "-C", str(scripts), "rev-parse", "HEAD"], capture_output=True,
                                           text=True, check=False).stdout.strip()
    if resume and target.is_file():  # a call that comes after another: it adds the projects the other has not
        before = json.loads(target.read_text(encoding="utf-8"))
        fixtures, machines = before["fixtures"], before["machine"]
        runs = before.get("runs") or [{"code": before["code"], "cases": sorted(fixtures), "repetitions": before["repetitions"]}]
        batches = [left for left in ([name for name in batch if name not in fixtures] for batch in batches) if left]
    runs.append({"code": ran, "cases": sorted({name for batch in batches for name in batch}), "repetitions": reps})
    for answer in measure.map(batches, kwargs={"reps": reps}, order_outputs=False, return_exceptions=True):
        if isinstance(answer, Exception):
            print("a container failed:", answer, flush=True)
            continue
        fixtures.update(answer["fixtures"])
        machines += [answer["machine"]] if answer["machine"] not in machines else []
        save(target, runs, machines, fixtures)
        for name, item in answer["fixtures"].items():
            print(name, item.get("error") or {key: item.get(key) for key in ("corpus", "files", "seconds")}, flush=True)
    print("ran", len(fixtures), "->", target, flush=True)
