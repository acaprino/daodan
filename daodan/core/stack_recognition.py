"""The `stack` step by stack-analyser: Daodan's pre-map facts go in as declarations, the tool's evidence comes out as the
registry entries (each with its signs), with the host mentions it adds and the sources whose signs the run made.

`declarations` turns the pre-map's packages, service images and Dockerfile bases into what the tool takes, `perimeter`
names the folders and files it must not enter (only folders are listed on the disk, never entered when the snapshot
holds nothing in them), `found` reads its evidence, `run` runs it and adds the host mentions. A failure of the tool or a
malformed fact or evidence item is a gap with its cause, never an error: the others still come out.
"""
from __future__ import annotations

import fnmatch
import os
import posixpath
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import container  # noqa: E402
import premap  # noqa: E402
import registry_build  # noqa: E402
import service_registry  # noqa: E402
import stack_analyser  # noqa: E402
from premap.module_graph import declared_image  # noqa: E402
from registry_hosts import check_hosts  # noqa: E402
from snapshot_store import open_snapshot  # noqa: E402
from module_inventory import _Inventory  # noqa: E402
from source_files import SECRET_NAME_GLOBS, is_forbidden  # noqa: E402

TYPES = ("deno", "docker", "githubAction", "golang", "hex", "maven", "npm", "nuget", "php", "pub", "python", "ruby",
         "rust", "swiftpm", "terraform", "terraform.resource")  # the declaration types of the release's README
TYPE_OF = {ecosystem: kind for kind, ecosystem in registry_build.ECOSYSTEMS.items()}  # the pre-map's name -> the tool's


SIGN_OF = {"image": "package", "action": "package", "terraform": "package"}  # the evidence kinds that are a package sign
_MALFORMED = (None, None, None, None, None, ())


def _left_out(facts: dict) -> tuple[str, ...]:
    return tuple(item["path"] for item in facts.get("excluded") or ()
                 if isinstance(item, dict) and isinstance(item.get("path"), str) and item["path"])


def _row(ecosystem, name, version, path, line, sources) -> tuple:
    """The row of one fact, or `TypeError` when a field is not of the kind the tool takes (a `line` is a positive integer)."""
    if not (isinstance(ecosystem, str) and isinstance(version, (str, type(None)))
            and (line is None or isinstance(line, int) and not isinstance(line, bool) and line > 0)
            and isinstance(sources, (list, tuple))):
        raise TypeError("fact of a malformed kind")
    return ecosystem, name, version, path, line, sources


def _rows(facts: dict):
    """(ecosystem, name, version, path, line, sources) of each package, service image and Dockerfile base of the
    pre-map, the images as `service_registry.step1_packages` takes them; a fact that is malformed is `_MALFORMED`."""
    seen = set()
    for item in facts.get("packages") or ():
        try:
            path, line = service_registry._split_declared_in(item.get("declared_in"))
            row = _row(item["ecosystem"], item.get("name"), item.get("version"), path, line, item.get("sources") or ())
            if row[0] == "docker":
                seen.add((declared_image(item.get("name") or ""), path))
        except (KeyError, AttributeError, TypeError):
            row = _MALFORMED
        yield row
    for service in facts.get("services") or ():
        try:
            if service.get("image"):
                path, _ = service_registry.service_site(service)
                image = declared_image(service["image"])
                if image and (image, path) not in seen:
                    seen.add((image, path))
                    yield _row("docker", image, None, path, None, service.get("sources") or ())
        except (KeyError, AttributeError, TypeError):
            yield _MALFORMED
    for build in facts.get("docker_builds") or ():
        try:
            dockerfile = build.get("dockerfile")
            for stage in build.get("stages") or ():
                base = stage.get("base")
                if dockerfile and base and base != "scratch":
                    image = declared_image(base)
                    if image and (image, dockerfile) not in seen:
                        seen.add((image, dockerfile))
                        yield _row("docker", image, None, dockerfile, stage.get("line"), build.get("sources") or ())
        except (KeyError, AttributeError, TypeError):
            yield _MALFORMED


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
    exits with an error for one that names no file inside the project, no package or no source, and a fact of a kind
    it cannot read."""
    left_out, sent, gaps = _left_out(facts), [], []
    for ecosystem, name, version, path, line, sources in _rows(facts):
        kind, sources = TYPE_OF.get(ecosystem, ecosystem), [s for s in sources if isinstance(s, str) and s]
        why = ("the pre-map's fact is malformed" if ecosystem is None
               else "the pre-map names no file for it" if not path
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


def _refused(option: str, entry: str) -> bool:
    """Whether the tool exits with an error for `entry` of `option` (`perimeterProblem` of its `src/cli.ts`): a folder name
    that holds a separator, a path that starts with a drive letter or has a `..` segment."""
    if option == "skipDirs":
        return "/" in entry or "\\" in entry
    return (entry[:1].isascii() and entry[:1].isalpha() and entry[1:2] == ":" and entry[2:3] in ("/", "\\")
            or ".." in entry.replace("\\", "/").split("/"))


def perimeter(root: Path, files: list[str], excluded: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...], list[dict]]:
    """`(skip_dirs, ignore, gaps)`: a folder is live when a snapshot file is inside it, at any depth. Only what lies in a
    live folder is listed. A folder that is not live goes by its name to `skip_dirs` (the tool skips it at every depth),
    or, when a live folder has that name or the tool refuses it as a name (`_refused`), by its path to `ignore`, as does
    every link (never followed; `skipDirs` does not stop the tool opening a link to a file), each path the pre-map leaves
    out and each file of a live folder whose name `source_files.is_forbidden` forbids or speaks of secrets
    (`SECRET_NAME_GLOBS`), decided by the name alone, which the tool would open. An `ignore` entry the tool refuses
    (`_refused`) is left out and is a gap `perimeter_entry_left_out`: the tool enters that folder, and the evidence
    outside the snapshot is dropped afterwards."""
    live = {"."} | {parent.as_posix() for rel in files for parent in PurePosixPath(rel).parents}
    names = {PurePosixPath(folder).name for folder in live}
    skip, ignore, pending = set(), {path.rstrip("/") for path in excluded if path.rstrip("/")}, ["."]
    while pending:
        folder = pending.pop()
        try:
            with os.scandir(root / folder) as listing:  # name, folder or not, link or not: a folder, a link or a file
                listed = [(item.name, item.is_dir(follow_symlinks=False), item.is_symlink() or item.is_junction())
                          for item in listing]
        except OSError:  # the tool meets the same folder and says so
            continue
        for name, is_folder, link in listed:
            rel = (PurePosixPath(folder) / name).as_posix()
            if link or (not is_folder and (is_forbidden(name) or any(
                    fnmatch.fnmatchcase(name.lower(), glob) for glob in SECRET_NAME_GLOBS))):
                ignore.add(rel)
            elif not is_folder:
                continue
            elif rel in live:
                pending.append(rel)
            elif name in names or _refused("skipDirs", name):
                ignore.add(rel)
            else:
                skip.add(name)
    gaps = [{"kind": "perimeter_entry_left_out", "option": "ignore", "entry": entry}
            for entry in sorted(ignore) if _refused("ignore", entry)]
    return tuple(sorted(skip)), tuple(sorted(n for n in ignore if not _refused("ignore", n))), gaps


def _item(item) -> tuple | None:
    """The key of an evidence item, `(tech, kind, value, path, line, source)`; None when it is not an object, lacks a key
    or holds a value of the wrong kind."""
    if not isinstance(item, dict):
        return None
    tech, kind, value, path, line, source = key = tuple(
        item.get(name) for name in ("tech", "kind", "value", "path", "line", "source"))
    ok = (all(isinstance(text, str) for text in (kind, value, path, source)) and isinstance(tech, (str, type(None)))
          and isinstance(line, (int, type(None))))
    return key if ok else None


def _signs(payload: dict, files: set[str], excluded: tuple[str, ...]) -> tuple[dict[str, list[dict]], list[dict]]:
    """The signs of each technology from the evidence of every component, once each; none from an evidence of kind
    `extension` or under a path the pre-map leaves out. The sign is the kind of the evidence, a package for an image, an
    action or a Terraform resource (`SIGN_OF`). The evidence of a declaration (its `source` is not the tool's) stays
    whatever its file, as the registry keeps a declared package; what the tool read by itself stays only for a file of the
    snapshot, the rest is a gap with its count and its first paths. Evidence that names no technology cannot name an
    entry: a gap with its count, and so is a component or an evidence item that is malformed."""
    seen, signs, nameless, outside, malformed, pending = set(), {}, 0, [], 0, [payload]
    while pending:
        component = pending.pop()
        childs, items = (component.get("childs") or [], component.get("evidence") or []) if isinstance(component, dict) \
            else (None, None)
        if not (isinstance(childs, list) and isinstance(items, list)):
            malformed += 1
            continue
        pending.extend(childs)
        for item in items:
            key = _item(item)
            if key is None:
                malformed += 1
            elif key in seen:
                continue
            else:
                seen.add(key)
                tech, kind, value, path, line, source = key
                path = path.removeprefix("/")
                if not tech:
                    nameless += 1
                elif kind == "extension" or service_registry._is_excluded(path, excluded):
                    continue
                elif path in files or source != "stack-analyser":
                    signs.setdefault(tech, []).append({"sign": SIGN_OF.get(kind, kind), "value": value, "path": path,
                                                       "line": line, "strength": "mentioned" if kind == "env" else "declared",
                                                       "source": source})
                else:
                    outside.append(path)
    return signs, ([{"kind": "evidence_without_technology", "count": nameless}] if nameless else []) + (
        [{"kind": "evidence_outside_snapshot", "count": len(outside), "paths": sorted(set(outside))[:5]}] if outside else []
    ) + ([{"kind": "evidence_malformed", "count": malformed}] if malformed else [])


def found(payload: dict, registry: dict, files: set[str], excluded: tuple[str, ...],
          mentions: list[tuple[str, dict]] = ()) -> tuple[list[dict], list[dict]]:
    """The entries of the tool's `payload` as registry entries with their signs, and the gaps; `mentions`
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


def _premap_sources(facts: dict) -> set[str]:
    """The names (the label up to `@`) of the pre-map sources whose state is `ran`: `facts["sources"]` is each source's
    status, `{"source": "name@version", "state": ...}`."""
    statuses = facts.get("sources") or ()
    return {status["source"].partition("@")[0] for status in statuses
            if isinstance(status, dict) and status.get("state") == "ran" and isinstance(status.get("source"), str)} - {""}


def run(manifest: Path, registry: dict | None = None, facts: dict | None = None) -> dict:
    """`{"found", "checkers", "gaps", "ran"}` for `manifest`, from the tool's evidence and the host mentions; `ran` is the
    sources whose signs this run made, sorted: `stack-analyser` when the tool ran, `registry_hosts` when the host check
    did, and, only when the tool ran, the pre-map's sources that ran. A failure of the tool is a gap with its cause and remedy; the host mentions
    stay. The snapshot's store is closed while the tool runs."""
    manifest = Path(manifest)
    facts = premap.ensure(manifest) if facts is None else facts
    registry = registry or service_registry.load()
    left_out = _left_out(facts)
    sent, gaps = declarations(facts)
    checkers, payload, mentions, ran = [], {}, [], set()
    with open_snapshot(manifest) as store:  # the files the inventory lists: `stack` runs before `parse`
        root = Path(store["root"])
        files = [rel for rel in _Inventory(store).files if not service_registry._is_excluded(rel, left_out)]
    skip_dirs, ignore, more = perimeter(root, files, left_out)
    gaps += more
    try:
        payload = stack_analyser.run(root, declarations=sent, skip_dirs=skip_dirs, ignore=ignore)
        checkers.append({"checker": "stack-analyser", "state": "ran"})
        ran |= {"stack-analyser", *_premap_sources(facts)}  # their signs exist only through the tool
    except container.Gap as gap:
        _failed("stack-analyser", f"{gap.cause} ({gap.remedy})", checkers, gaps)
    except Exception as error:  # nothing the tool meets ends the step
        _failed("stack-analyser", f"{type(error).__name__}: {error}", checkers, gaps)
    try:
        with open_snapshot(manifest) as store:
            inventory = _Inventory(store)
            answer = check_hosts(registry["entries"], service_registry.Project(
                [], files, lambda rel: service_registry._lines(inventory, rel)))
        mentions = [(ident, {"sign": "host", "value": value, "path": path, "line": line, "strength": "mentioned",
                             "source": "registry_hosts"}) for ident, value, path, line in answer["signs"]]
        checkers.append({"checker": "host", "state": "ran"})
        ran.add("registry_hosts")
        gaps += [{**gap, "checker": "host"} for gap in answer.get("gaps") or ()]
    except Exception as error:  # a checker's failure is its gap, never the end of the others
        _failed("host", f"{type(error).__name__}: {error}", checkers, gaps)
    entries, more = found(payload, registry, set(files), left_out, mentions)
    return {"found": entries, "checkers": checkers, "gaps": gaps + more, "ran": sorted(ran)}
