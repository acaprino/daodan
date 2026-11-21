"""The `stack` step by stack-analyser: Daodan's pre-map facts go in as declarations, the tool's evidence comes out as the
registry entries `service_registry.run` returns, so the benchmark can put `recognize` where `run` stood.

`declarations` turns the pre-map's packages, service images and Dockerfile bases into what the tool takes, `perimeter`
names the folders it must not enter (only folders are listed on the disk, never entered when the snapshot holds nothing
in them), `found` reads its evidence, `recognize` runs it and adds the host mentions `service_registry.run` adds.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path, PurePosixPath

SCRIPTS = Path(os.environ.get("PM_PLUGIN_SCRIPTS") or
               (next((p / "daodan/core" for p in Path(__file__).resolve().parents
                      if (p / "daodan/core").is_dir()), "/daodan/map/core")))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import container  # noqa: E402
import flows  # noqa: E402
import premap  # noqa: E402
import registry_build  # noqa: E402
import service_registry  # noqa: E402
import stack_analyser  # noqa: E402
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
            seen.add((declared_image(item["name"]), path))
        yield item["ecosystem"], item["name"], item.get("version"), path, line, item.get("sources") or ()
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


def declarations(facts: dict) -> tuple[list[dict], list[dict]]:
    """What the tool takes, one declaration per source that states each fact, and the facts it cannot be given."""
    left_out, sent, gaps = _left_out(facts), [], []
    for ecosystem, name, version, path, line, sources in _rows(facts):
        kind = TYPE_OF.get(ecosystem, ecosystem)
        why = ("the pre-map names no file for it" if not path
               else "the pre-map leaves out its path" if service_registry._is_excluded(path, left_out)
               else f"the release takes no declaration of type {kind}" if kind not in TYPES else None)
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
    path the pre-map leaves out."""
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
    return tuple(sorted(skip)), tuple(sorted(ignore))


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
