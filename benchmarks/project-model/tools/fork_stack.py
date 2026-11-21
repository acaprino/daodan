"""The `stack` step by stack-analyser: Daodan's pre-map facts go in as declarations, the tool's evidence comes out as the
registry entries `service_registry.run` returns, so the benchmark can put `recognize` where `run` stood.

`declarations` turns the pre-map's packages, service images and Dockerfile bases into what the tool takes, `perimeter`
names the folders it must not enter (only folders are listed on the disk, never entered when the snapshot holds nothing
in them), `found` reads its evidence, `recognize` runs it and adds the host mentions `service_registry.run` adds.

The benchmark's measures are here too, as functions the container only calls: `measure` takes one project's two records
and its fast scan, `compare` sets the two records side by side against `expected.json`, `executed` judges the processes
started, `summary` gives the totals. `benchmarks/project-model/test_fork_stack.py` tests them on this PC.
"""
from __future__ import annotations

import os
import posixpath
import statistics
import sys
import time
from pathlib import Path, PurePosixPath, PureWindowsPath
from unittest import mock

SCRIPTS = Path(os.environ.get("PM_PLUGIN_SCRIPTS") or
               (next((p / "daodan/core" for p in Path(__file__).resolve().parents
                      if (p / "daodan/core").is_dir()), "/daodan/map/core")))
PROJECT_MODEL = Path(__file__).resolve().parents[1]  # `score.py`
for _path in (SCRIPTS, PROJECT_MODEL):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import container  # noqa: E402
import flows  # noqa: E402
import premap  # noqa: E402
import registry_build  # noqa: E402
import score  # noqa: E402
import service_registry  # noqa: E402
import stack_analyser  # noqa: E402
import technologies  # noqa: E402
from premap.module_graph import declared_image  # noqa: E402
from registry_hosts import check_hosts  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402

TYPES = ("deno", "docker", "githubAction", "golang", "hex", "maven", "npm", "nuget", "php", "pub", "python", "ruby",
         "rust", "swiftpm", "terraform", "terraform.resource")  # the declaration types of the release's README
TYPE_OF = {ecosystem: kind for kind, ecosystem in registry_build.ECOSYSTEMS.items()}  # the pre-map's name -> the tool's


def _left_out(facts: dict) -> tuple[str, ...]:
    return tuple(item["path"] for item in facts.get("excluded") or () if item.get("path"))


def _rows(facts: dict):
    """(ecosystem, name, version, path, line, sources) of each package, service image and Dockerfile base of the
    pre-map, the images as `service_registry.step1_packages` takes them."""
    seen = set()
    for item in facts.get("packages") or ():
        path, line = service_registry._split_declared_in(item.get("declared_in"))
        if item["ecosystem"] == "docker":
            seen.add((declared_image(item.get("name") or ""), path))
        yield item["ecosystem"], item.get("name"), item.get("version"), path, line, item.get("sources") or ()
    for service in facts.get("services") or ():
        if service.get("image"):
            path, _ = service_registry.service_site(service)
            image = declared_image(service["image"])
            if image and (image, path) not in seen:
                seen.add((image, path))
                yield "docker", image, None, path, None, service.get("sources") or ()
    for build in facts.get("docker_builds") or ():
        dockerfile = build.get("dockerfile")
        for stage in build.get("stages") or ():
            base = stage.get("base")
            if dockerfile and base and base != "scratch":
                image = declared_image(base)
                if image and (image, dockerfile) not in seen:
                    seen.add((image, dockerfile))
                    yield "docker", image, None, dockerfile, stage.get("line"), build.get("sources") or ()


def _inside(path: str) -> bool:
    """Whether the tool reads `path` as a file of the analysed root: a backslash is a separator, the path is not
    absolute in either sense and has no drive letter, and once normalised it does not leave the root."""
    posix, windows = path.replace("\\", "/"), PureWindowsPath(path)
    letter = windows.drive[:1]
    if PurePosixPath(posix).is_absolute() or windows.is_absolute() or (
            windows.drive[1:2] == ":" and letter.isascii() and letter.isalpha()):
        return False
    normal = posixpath.normpath(posix)
    return normal not in (".", "..") and not normal.startswith("../")


def declarations(facts: dict) -> tuple[list[dict], list[dict]]:
    """What the tool takes, one declaration per source that states each fact, and the facts it cannot be given: it
    exits with an error for one that names no file inside the project, no package or no source."""
    left_out, sent, gaps = _left_out(facts), [], []
    for ecosystem, name, version, path, line, sources in _rows(facts):
        kind, sources = TYPE_OF.get(ecosystem, ecosystem), [s for s in sources if isinstance(s, str) and s]
        why = ("the pre-map names no file for it" if not path
               else "the pre-map leaves out its path" if service_registry._is_excluded(path, left_out)
               else "its path is outside the project" if not _inside(path)
               else f"the release takes no declaration of type {kind}" if kind not in TYPES
               else "the pre-map names no package for it" if not isinstance(name, str) or not name
               else "no source states it" if not sources else None)
        if why:
            gaps.append({"kind": "declaration_not_sent", "value": name, "path": path, "ecosystem": ecosystem,
                         "detail": why})
            continue
        sent += [{"type": kind, "name": name, **({"version": version} if version else {}), "path": path,
                  **({"line": line} if line else {}), "source": source} for source in sources]
    return sent, gaps


def perimeter(root: Path, files: list[str], excluded: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """`(skip_dirs, ignore)`: a folder is live when a snapshot file is inside it, at any depth. Only what lies in a live
    folder is listed. A folder that is not live goes by its name to `skip_dirs` (the tool skips it at every depth), or,
    when a live folder has that name, by its path to `ignore`, as does a link, which is never followed, and each
    path the pre-map leaves out. The tool splits both options at commas, so a name or path with one is left out of
    both: the tool enters that folder, and the evidence outside the snapshot is dropped afterwards."""
    live = {"."} | {parent.as_posix() for rel in files for parent in PurePosixPath(rel).parents}
    names = {PurePosixPath(folder).name for folder in live}
    skip, ignore, pending = set(), {path.rstrip("/") for path in excluded}, ["."]
    while pending:
        folder = pending.pop()
        try:
            with os.scandir(root / folder) as listing:  # a folder or a link: its name, and whether it is a link
                children = [(item.name, item.is_symlink() or item.is_junction()) for item in listing
                            if item.is_dir(follow_symlinks=False) or item.is_symlink() or item.is_junction()]
        except OSError:  # the tool meets the same folder and says so
            continue
        for name, link in children:
            rel = (PurePosixPath(folder) / name).as_posix()
            if rel in live and not link:
                pending.append(rel)
            elif name in names:
                ignore.add(rel)
            else:
                skip.add(name)
    return tuple(sorted(n for n in skip if "," not in n)), tuple(sorted(n for n in ignore if "," not in n))


def _signs(payload: dict, files: set[str], excluded: tuple[str, ...]) -> tuple[dict[str, list[dict]], list[dict]]:
    """The signs of each technology from the evidence of every component, once each; none from an evidence of kind
    `extension`, of a file the snapshot lacks or under a path the pre-map leaves out. Evidence that names no technology
    cannot name an entry: a gap with its count."""
    seen, signs, nameless, pending = set(), {}, 0, [payload]
    while pending:
        component = pending.pop()
        pending.extend(component.get("childs") or ())
        for item in component.get("evidence") or ():
            key = (item.get("tech"), item["kind"], item["value"], item["path"], item.get("line"), item["source"])
            if key in seen:
                continue
            seen.add(key)
            tech, kind, value, path, line, source = key
            path = path.removeprefix("/")
            if not tech:
                nameless += 1
            elif kind != "extension" and path in files and not service_registry._is_excluded(path, excluded):
                signs.setdefault(tech, []).append({"sign": kind, "value": value, "path": path, "line": line,
                                                   "strength": "mentioned" if kind == "env" else "declared",
                                                   "source": source})
    return signs, [{"kind": "evidence_without_technology", "count": nameless}] if nameless else []


def found(payload: dict, registry: dict, files: set[str], excluded: tuple[str, ...],
          mentions: list[tuple[str, dict]] = ()) -> tuple[list[dict], list[dict]]:
    """The entries of the tool's `payload` in the form of `service_registry.run()["found"]`, with the gaps; `mentions`
    are signs already made, `(entry id, sign)`. An id the registry lacks comes out with its own name and a gap."""
    signs, gaps = _signs(payload, files, excluded)
    for ident, sign in mentions:
        signs.setdefault(ident, []).append(sign)
    known, out = {entry["id"]: entry for entry in registry["entries"]}, []
    for ident in sorted(signs):
        if ident not in known:
            gaps.append({"kind": "not_in_registry", "entry": ident})
        entry = known.get(ident, {"id": ident, "name": ident})
        category = service_registry.entry_category(entry)
        out.append({"id": ident, "name": entry.get("name"), "kind": "project" if category != "service" else "service",
                    "category": category, "type": entry.get("type"), "site": entry.get("site"),
                    "mark": entry.get("mark"), "source": "registry",
                    "signs": sorted(signs[ident], key=lambda s: (s["sign"], s["path"] or "", s["line"] or 0, s["value"]))})
    return out, gaps


def _failed(checker: str, reason: str, checkers: list[dict], gaps: list[dict]) -> None:
    checkers.append({"checker": checker, "state": "failed", "reason": reason})
    gaps.append({"kind": "checker_failed", "checker": checker, "detail": reason})


def recognize(manifest: Path, registry: dict | None = None, facts: dict | None = None) -> dict:
    """`service_registry.run`'s answer for `manifest`, from the tool's evidence and the host mentions. A failure of
    the tool is a gap with its cause and remedy; the host mentions stay."""
    manifest = Path(manifest)
    facts = premap.ensure(manifest) if facts is None else facts
    registry = registry or service_registry.load()
    left_out = _left_out(facts)
    sent, gaps = declarations(facts)
    checkers, payload, mentions = [], {}, []
    with open_snapshot(manifest) as store:
        root, source = Path(store["root"]), flows.Source(store)
        files = [rel for rel in sorted(dict(store.iter_file_headers_only()))
                 if not service_registry._is_excluded(rel, left_out)]
        project = service_registry.Project(
            [s for s in service_registry.step1_packages(manifest, facts) if not service_registry._is_excluded(s[2], left_out)],
            files, lambda rel: source.lines(rel) or [])
        skip_dirs, ignore = perimeter(root, files, left_out)
        try:
            payload = stack_analyser.run(root, declarations=sent, skip_dirs=skip_dirs, ignore=ignore)
            checkers.append({"checker": "stack-analyser", "state": "ran"})
        except container.Gap as gap:
            _failed("stack-analyser", f"{gap.cause} ({gap.remedy})", checkers, gaps)
        try:
            answer = check_hosts(registry["entries"], project)
            mentions = [(ident, {"sign": "host", "value": value, "path": path, "line": line, "strength": "mentioned",
                                 "source": "registry_hosts"}) for ident, value, path, line in answer["signs"]]
            checkers.append({"checker": "host", "state": "ran"})
            gaps += [{**gap, "checker": "host"} for gap in answer.get("gaps") or ()]
        except Exception as error:  # as `service_registry.run`: a checker's failure is its gap, never the end
            _failed("host", f"{type(error).__name__}: {error}", checkers, gaps)
    entries, more = found(payload, registry, set(files), left_out, mentions)
    return {"found": entries, "checkers": checkers, "gaps": gaps + more}


# ---------------------------------------------------------------------------------------------- the measures

def _found_names(expected: dict, record: dict) -> list[str]:
    """The names `expected` lists (frameworks, then services) that `score.score_technologies` finds in `record`: the
    frameworks by name alone, as its `frameworks_by_name` counts them, with the score's own spellings and aliases."""
    scored = score.score_technologies(expected, record)
    names = []
    for facet, key in (("frameworks", "frameworks_by_name"), ("services", "services")):
        if key in scored:  # the expected file's `unknown` takes a facet out
            missed = set(scored[key]["missed"])  # spelt as the score spells them
            names += [item["name"] for item in expected.get(facet) or ()
                      if score._framework(item["name"]) not in missed and item["name"] not in names]
    return names


def compare(expected: dict, before: dict, after: dict) -> dict:
    """The record `before` (the registry's) and `after` (the fork's, with its `gaps`), in the form
    `score.score_technologies` takes, against each other: the expected names found only before (`lost`) or only after
    (`gained`), the ids of `technologies` only after (`new`) or only before (`gone`), and the ids the fork named that
    the registry lacks (`not_in_registry`)."""
    names_before, names_after = _found_names(expected, before), _found_names(expected, after)
    ids_before, ids_after = ({t["id"] for t in record["technologies"]} for record in (before, after))
    gaps = after.get("gaps") or ()
    return {"lost": [n for n in names_before if n not in names_after],
            "gained": [n for n in names_after if n not in names_before],
            "new": sorted(ids_after - ids_before), "gone": sorted(ids_before - ids_after),
            "not_in_registry": sorted({gap["entry"] for gap in gaps if gap.get("kind") == "not_in_registry"})}


def executed(spawned: list[str], node: str, cli: str, git: str) -> str:
    """`"no"` when each process started is the perimeter's `git` (the start of its command line) or `node` with `cli` as
    its first argument, else `"unknown"`. A process comes as one string, cut at 200 characters: the program and its
    first argument are at the start."""
    program = f"{node} {cli}"
    return "no" if all(line.startswith(git) or line == program or line.startswith(program + " ") for line in spawned) \
        else "unknown"


def _timed(function, *args) -> tuple[dict, float]:
    started = time.monotonic()
    answer = function(*args)
    return answer, round(time.monotonic() - started, 3)


def _declared(answer: dict) -> set[str]:
    """The ids of the entries with a declared sign: the ones `technologies.derive` keeps, the others it leaves mentioned."""
    return {entry["id"] for entry in answer["found"] if any(s["strength"] == "declared" for s in entry["signs"])}


def measure(manifest: Path, registry: dict, full: dict, fast: dict) -> dict:
    """One project, two ways. `technologies.derive` on the pre-map's facts `full` with the registry's recogniser and with
    the fork's (`service_registry.run` replaced by `recognize`), and each recogniser alone on the facts `fast` (the
    pre-map without its model commands), compared by the ids each declares; the seconds are each call's. `derive` makes
    the module graph the first time and finds it the second, so one derive, not timed, comes first: the graph is
    already there under both."""
    manifest = Path(manifest)
    technologies.derive(manifest, registry, full)
    before, registry_full = _timed(technologies.derive, manifest, registry, full)
    with mock.patch.object(service_registry, "run", recognize):
        after, fork_full = _timed(technologies.derive, manifest, registry, full)
    by_registry, registry_fast = _timed(service_registry.run, manifest, registry, fast)
    by_fork, fork_fast = _timed(recognize, manifest, registry, fast)
    ours, theirs = _declared(by_registry), _declared(by_fork)
    return {"before": before, "after": after,
            "fast": {"registry": sorted(ours), "fork": sorted(theirs), "lost": sorted(ours - theirs)},
            "seconds": {"registry_full": registry_full, "fork_full": fork_full, "registry_fast": registry_fast,
                        "fork_fast": fork_fast}}


def _spread(fixtures: dict, key: str) -> dict:
    times = {name: entry["seconds"][key] for name, entry in fixtures.items() if "seconds" in entry}
    slowest = max(times, key=times.get, default=None)
    return {"median": round(statistics.median(times.values()), 3) if times else None,
            "max": times.get(slowest), "slowest": slowest}


def summary(fixtures: dict) -> dict:
    """The totals over the fixtures `fetch` writes (name -> `{"error": ...}`, or the result with its `compare`, its
    `seconds` and the `score` of each record): the expected names found before and after, the fixtures that lose some,
    the spread of the fast scans."""
    found = {}
    for facet, key in (("frameworks", "frameworks_by_name"), ("services", "services")):
        row = {"expected": 0, "before": 0, "after": 0}
        for entry in fixtures.values():
            scores = entry.get("score")
            if scores and key in scores["before"]:
                row["expected"] += scores["before"][key]["expected"]
                row["before"] += scores["before"][key].get("found", 0)
                row["after"] += scores["after"][key].get("found", 0)
        found[facet] = row
    return {"fixtures": len(fixtures), "errors": sum("error" in entry for entry in fixtures.values()),
            "fixtures_with_lost": sum(bool(entry.get("compare", {}).get("lost")) for entry in fixtures.values()),
            "found": found, "fork_fast": _spread(fixtures, "fork_fast"), "registry_fast": _spread(fixtures, "registry_fast")}
