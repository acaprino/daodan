"""The `stack` step by stack-analyser on the files `list_files` keeps: the tool's evidence comes out as the registry entries
(each with its signs), with the host mentions it adds; it runs before `find_modules` and takes no fact of the pre-map
(spec `architettura.md`, «I file: da `list_files`»).

`perimeter` names the folders and files the tool must not enter (only folders are listed on the disk, never entered when
the snapshot holds nothing in them), `found` reads its evidence, `run` runs it and adds the host mentions, `ensure` keeps
its record beside the snapshot (`stack.json`) and `tools` names the build tools it found, which choose the sources of
`find_modules` (`premap.BUILD_TOOLS`). A failure of the tool or a malformed evidence item is a gap with its cause, never an
error: the others still come out.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path, PurePosixPath

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import confinement  # noqa: E402
import container  # noqa: E402
import service_registry  # noqa: E402
import stack_analyser  # noqa: E402
from languages._treesitter import get_parser  # noqa: E402
from registry_hosts import check_hosts  # noqa: E402
from snapshot_store import inventory_digest, open_snapshot  # noqa: E402
from module_inventory import _Inventory  # noqa: E402
from source_files import SECRET_NAME_GLOBS, is_forbidden  # noqa: E402

SCHEMA, FILE = "daodan/stack/v1", "stack.json"
SOURCES = ("stack-analyser", "registry_hosts")  # the sources of the signs this step makes
SIGN_OF = {"image": "package", "action": "package", "terraform": "package"}  # the evidence kinds that are a package sign
_derived: set[tuple[str, str]] = set()  # (record, inputs digest) derived by this process: not derived again here


def _left_out(facts) -> tuple[str, ...]:
    """The paths `excluded` names, of the snapshot's header (`file_inventory.excluded`) or of the pre-map."""
    return tuple(item["path"] for item in facts.get("excluded") or ()
                 if isinstance(item, dict) and isinstance(item.get("path"), str) and item["path"])


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
    every link (never followed; `skipDirs` does not stop the tool opening a link to a file), each path the snapshot leaves
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
    `extension` or under a path the snapshot leaves out. The sign is the kind of the evidence, a package for an image, an
    action or a Terraform resource (`SIGN_OF`). Evidence stays only for a file of the snapshot, the rest is a gap with its
    count and its first paths. Evidence that names no technology cannot name an entry: a gap with its count, and so is a
    component or an evidence item that is malformed."""
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
                elif path in files:
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


def run(manifest: Path, registry: dict | None = None) -> dict:
    """`{"found", "checkers", "gaps", "ran"}` for `manifest`, from the tool's evidence on the snapshot's files and the host
    mentions; the perimeter leaves out what the snapshot's header excludes (`file_inventory.excluded`). `ran` is the
    sources whose signs this run made, sorted: `stack-analyser` when the tool ran, `registry_hosts` when the host check
    did. A failure of the tool is a gap with its cause and remedy; the host mentions stay. The snapshot's store is closed
    while the tool runs."""
    manifest = Path(manifest)
    registry = registry or service_registry.load()
    checkers, gaps, payload, mentions, ran = [], [], {}, [], set()
    with open_snapshot(manifest) as store:  # the files the inventory lists: `stack` runs before `scan` and `parse`
        root, left_out = Path(store["root"]), _left_out(store)
        files = [rel for rel in _Inventory(store).files if not service_registry._is_excluded(rel, left_out)]
    skip_dirs, ignore, more = perimeter(root, files, left_out)
    gaps += more
    try:
        payload = stack_analyser.run(root, skip_dirs=skip_dirs, ignore=ignore)
        checkers.append({"checker": "stack-analyser", "state": "ran"})
        ran.add("stack-analyser")
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


def ids(record: dict, categories=None) -> list[str] | None:
    """The registry ids the tool found by itself (of `categories`, of any without), sorted; None when it did not run, and
    every source the stack chooses runs as without it."""
    if not any(c.get("checker") == "stack-analyser" and c.get("state") == "ran" for c in record.get("checkers") or ()):
        return None
    return sorted({entry["id"] for entry in record.get("found") or ()
                   if (categories is None or entry.get("category") in categories)
                   and any(sign.get("source") == "stack-analyser" for sign in entry.get("signs") or ())})


def tools(record: dict) -> list[str] | None:
    """The registry ids of the build tools (`category` `tool`) the tool found by itself (`ids`): they choose the sources of
    `find_modules`."""
    return ids(record, ("tool",))


# --------------------------------------------------------------------------------------------- the record

def path(manifest: Path) -> Path:
    return Path(manifest).with_name(FILE)


def _inputs(manifest: Path, registry: dict) -> tuple[str, str]:
    """The digest of what the record is derived from, and the snapshot's inventory digest."""
    with open_snapshot(manifest) as store:
        digest = inventory_digest(store)
        value = [digest, store["root"], store.get("excluded") or [], registry, SCHEMA, stack_analyser.VERSION,
                 stack_analyser.SHA256]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest(), digest


def recorded(manifest: Path) -> dict:
    """The record beside `manifest`, as written (`ensure` derives it, this only reads): empty when there is none, or not of
    this schema."""
    try:
        record = json.loads(path(manifest).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return record if isinstance(record, dict) and record.get("schema") == SCHEMA else {}


def named(manifest: Path, digest: str) -> list[str] | None:
    """The build tools of the record beside `manifest` (`tools`) when it was derived from the inventory of `digest`;
    None without one: every source of `find_modules` runs."""
    record = recorded(manifest)
    return record.get("tools") if record.get("inventory_digest") == digest else None


def found_ids(manifest: Path, digest: str) -> list[str] | None:
    """Every registry id the tool found by itself (`ids`) in the record beside `manifest`, when it was derived from the
    inventory of `digest`; None without one: every source of `find_entry_points` runs."""
    record = recorded(manifest)
    return ids(record) if record.get("inventory_digest") == digest else None


def _read(manifest: Path, digest: str) -> dict | None:
    record = recorded(manifest)
    if record.get("inputs_digest") != digest or "found" not in record:
        return None
    # A grammar may have been placed since a previous run recorded its absence.
    missing = {g["language"] for g in record.get("gaps", ()) if g.get("kind") == "source_grammar_unavailable"}
    if any(get_parser(language) is not None for language in missing):
        return None
    # Node or the network may have come since the tool failed, unless this process remembers the failure or derived this
    # record itself: a timeout or an exit with an error is not remembered as an install is.
    if (not stack_analyser._failed and (str(path(manifest)), digest) not in _derived
            and any(g.get("kind") == "checker_failed" and g.get("checker") == "stack-analyser"
                    for g in record.get("gaps", ()))):
        return None
    return record


def state(manifest: Path, registry: dict | None = None) -> str:
    """fresh, stale or missing; a read."""
    manifest = Path(manifest).resolve()
    if not path(manifest).is_file():
        return "missing"
    return "fresh" if _read(manifest, _inputs(manifest, registry or service_registry.load())[0]) else "stale"


def ensure(manifest: Path, registry: dict | None = None) -> dict:
    """The record of `manifest` (`run`, with `tools`), derived and written again when it is not fresh."""
    manifest = Path(manifest).resolve()
    registry = registry or service_registry.load()
    digest, inventory = _inputs(manifest, registry)
    record = _read(manifest, digest)
    if record is None:
        target = path(manifest)
        confinement.reject_link_chain(target)
        answer = run(manifest, registry)
        record = {"schema": SCHEMA, "inputs_digest": digest, "inventory_digest": inventory, **answer,
                  "tools": tools(answer)}
        descriptor, name = tempfile.mkstemp(prefix=".stack-", dir=target.parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        os.replace(name, target)
        _derived.add((str(target), digest))
    return record
