"""`find_entry_points`: where a flow of the project starts, as the official tools read it, outside the pre-map.

`entry-points.json` (`daodan/entry-points/v1`) beside the manifest, in Daodan's store, never in the project. Its sources are
model sources of the pre-map's kind (`NAME`, `VERSION`, `RANK`, `commands`, `read`): OWASP Noir (`noir_entries`) and each
framework's own tool (`framework_entries`), run in Daodan's container by the runner the caller supplies. They run with the
pre-map's machinery (`premap.Context`, `premap._run`, `premap.join`), each reading the pre-map (`Context.stated`): the
toolchains a runner prepares and the restores it refuses come from there («Pacchetti ripristinati: da `find_modules`»). The record
is bound to the snapshot as the pre-map is, to the pre-map it read (its `inputs_digest`) and to its sources' versions. A framework's
source runs only for a framework the stack found (`_chosen`, from `registry_build.READERS`); Noir runs on every project.
Once the snapshot is read, the step also binds the routes to its functions with no rule (`bound`, kept under `bound`); the flows
read the rows with the manifests' own (`flow_entries.evidence`) and take that binding where the rules of the session name no handler.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import confinement  # noqa: E402
import premap  # noqa: E402
import preparation  # noqa: E402
from snapshot_store import inventory_digest, open_snapshot  # noqa: E402

from entry_points import angular, astro, nextjs, noir, nuxt, react_router, sveltekit  # noqa: E402

SCHEMA = "daodan/entry-points/v1"
FILE = "entry-points.json"
SOURCES = (noir, nextjs, react_router, nuxt, sveltekit, angular, astro)
# The sources whose `framework_entries` rows are entries of their own (a page, a route handler): `flow_entries.evidence` reads
# each one's rows and gaps, and the key of the cached links hashes each one's file (`flows._links_reader_digest`). Another
# framework's source is one more name here, with its table in `entry-queries.json` under its `NAME`. `angular` and `astro` are not:
# their rows stand for, or join, the tree reader's at the same events (`entries.compiled`), and their gaps are told on their own.
FRAMEWORK_SOURCES = (nextjs, react_router, nuxt, sveltekit)
# The sources whose rows stand for, or join, the tree reader's at the same events (`entries.compiled`: the events of a template): their
# gaps are told by `flow_entries.evidence`, and the key of the cached links hashes each one's file. Their script is not in it: a
# record is fresh for the `NAME@VERSION` that made it, and the version goes with the script (each one's test of the recorded print).
TEMPLATE_SOURCES = (angular, astro)
IDENTITY = {  # individual observations: no two rows are one fact
    "noir_entries": (),  # of a single scanner
    "framework_entries": (),  # of a framework's own tool (`next`, `react-router`, `angular`)
}


def path(manifest: Path) -> Path:
    return Path(manifest).with_name(FILE)


def _reader(source) -> str:
    """The module of `source` as `registry_build.READERS` names it, from `core/`."""
    return Path(source.__file__).resolve().relative_to(SCRIPT_DIR).as_posix()


def _chosen(sources, found) -> tuple:
    """`sources` without those `registry_build.READERS` names for no id of `found` (the registry ids the stack found): they run
    no command and state no gap. With `found` None (no stack record of this inventory, or the tool did not run) all run, as
    `premap._chosen` does with the build tools."""
    sources = tuple(SOURCES if sources is None else sources)
    if found is None:
        return sources
    from registry_build import READERS
    named, wanted = set(READERS.values()), {READERS[ident] for ident in found if ident in READERS}
    return tuple(source for source in sources if _reader(source) not in named or _reader(source) in wanted)


def _found(manifest: Path, digest: str):
    """The registry ids the stack step found for the inventory of `digest` (`stack_recognition.found_ids`)."""
    import stack_recognition
    return stack_recognition.found_ids(manifest, digest)


def _inputs(digest, root, premap_digest, sources) -> str:
    value = [digest, root, premap_digest, [premap.label(s) for s in sources], SCHEMA]
    if noir in sources:
        value.append("noir-entry-paths-v3")
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def derive(manifest: Path, store, stated: dict, sources=None, runner=None, report=None, found=None) -> dict:
    """The record of the snapshot in `store`, its sources run in `SOURCES`' order on the pre-map `stated`; `runner` and
    `report` as `premap.derive` takes them; `found`, the registry ids the stack found, chooses the sources (`_chosen`)."""
    sources = _chosen(sources, found)
    context = premap.Context(manifest, store)
    context.stated = stated
    toolchains, refused = stated.get("toolchains", ()), preparation.refusals(stated)
    statuses, parts, gaps = [], [], []
    for source in sources:
        status, part, found = premap._run(source, context, runner, toolchains, refused, IDENTITY)
        statuses.append(status)
        if part:
            parts.append(part)
        gaps.extend(found)
        if report is not None:  # `report(status, done, total)`: each source as it ends
            report(status, len(statuses), len(sources))
    digest = inventory_digest(store)
    return {"schema": SCHEMA,
            "binding": {"manifest": str(Path(manifest).resolve()), "inventory_digest": digest, "root": store["root"],
                        "unread": store.get("unread") or {}, "excluded": store.get("excluded") or [],
                        "premap": stated.get("inputs_digest")},
            "inputs_digest": _inputs(digest, store["root"], stated.get("inputs_digest"), sources), "sources": statuses,
            **premap.join(parts, IDENTITY), "gaps": gaps}


def rows(record: dict) -> tuple[list[dict], list[dict]]:
    """The routes of `record` (Noir's and those of `FRAMEWORK_SOURCES`) and the gaps of its sources. A template source's rows are no
    routes: they stand for, or join, the tree reader's at the same events (`entries.compiled`); its gaps are told here."""
    routes, gaps = noir.from_record(record)
    for source in FRAMEWORK_SOURCES:
        found, said = source.from_record(record)
        routes, gaps = routes + found, gaps + said
    for source in TEMPLATE_SOURCES:
        gaps += source.from_record(record)[1]
    return routes, gaps


def reading(db, routes: list[dict]) -> str:
    """What a binding holds for: the routes it binds, the snapshot the semantic store `db` was built from (`sem_meta`) and the code
    of the binder and of the links' readers (`flows._links_reader_digest`)."""
    import flows
    import semantic_store
    row = db.execute("SELECT payload FROM sem_meta WHERE key='manifest_digest'").fetchone()
    value = [semantic_store._unpack(row[0]) if row else None, flows._links_reader_digest(), routes]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def bound(manifest: Path, record: dict, facts=None, routes: list[dict] | None = None) -> dict:
    """The routes of `record` (`rows`, or `routes`) bound to the snapshot's functions with no rule (`binder.bind`): `{reading, rows,
    route_named}`, each row with its `symbol` or its `gap`, and the names the routes give functions written with no name, which the
    nodes of the links take (`Facts.name_routes`). The binding `record` keeps for the same `reading` is given as it is. The step calls
    it once the snapshot is read and keeps it in the record; the links call it with their own `facts` where the rules of the session
    name no handler written in place (`flows.bind_declared`)."""
    import binder
    import flows
    import semantic_store
    if facts is None:
        with open_snapshot(manifest) as store, semantic_store.semantic_reader(store) as db:
            return bound(manifest, record, flows.Facts(store, db), routes)
    routes = rows(record)[0] if routes is None else routes
    stamp = reading(facts.db, routes)
    kept = record.get("bound") or {}
    if kept.get("reading") == stamp:
        return kept
    found = binder.bind(routes, facts, facts.resolver)
    return {"reading": stamp, "rows": found, "route_named": dict(facts.route_named)}


def write(manifest: Path, sources=None, runner=None, report=None, stated: dict | None = None) -> dict:
    """Derive and publish `entry-points.json` beside the manifest, on the pre-map `stated`: by default the one beside it, of
    this snapshot, else one derived now (`premap.ensure`)."""
    from entry_points import flow_entries
    manifest = Path(manifest).resolve()
    target = path(manifest)
    confinement.reject_link_chain(target)
    if stated is None:
        try:
            stated = flow_entries.read_record(manifest)
        except (OSError, KeyError, TypeError, ValueError):
            stated = premap.ensure(manifest)
    with open_snapshot(manifest) as store:
        stamp = premap._snapshot_stamp(manifest)
        record = derive(manifest, store, stated, sources, runner, report, _found(manifest, inventory_digest(store)))
        if store.metadata.get("reading") != "not-started":  # the binder reads the snapshot's functions: only once it is read
            try:
                record["bound"] = bound(manifest, record)
            except ValueError:  # a semantic store of another resolver: the links bind the rows, and say why they cannot
                pass
        if inventory_digest(store) != record["binding"]["inventory_digest"] or premap._snapshot_stamp(manifest) != stamp:
            raise ValueError("snapshot changed during the entry points; retry")
        record["binding"]["snapshot_stamp"] = stamp
    descriptor, name = tempfile.mkstemp(prefix=".entry-points-", dir=target.parent)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    os.replace(name, target)
    return json.loads(target.read_text(encoding="utf-8"))


def read_record(manifest: Path) -> dict:
    """The record beside `manifest`, refused when it belongs to another snapshot."""
    target = path(manifest)
    confinement.reject_link_chain(target)
    record = json.loads(target.read_text(encoding="utf-8"))
    if record.get("schema") != SCHEMA:
        raise ValueError(f"schema {record.get('schema')!r}")
    if not premap.binding_matches(Path(manifest), record["binding"]):
        raise ValueError("the record of the entry points belongs to a different snapshot")
    return record


def state(manifest: Path, sources=None, runner=None) -> dict:
    """Freshness without executing a source, as `premap.state` says it: also stale when the pre-map it read is not the one
    beside the manifest."""
    manifest = Path(manifest).resolve()
    target = path(manifest)
    report = {"entry_points": str(target), "manifest": str(manifest)}
    if not target.is_file():
        return {**report, "state": "missing", "reason": "no record of the entry points beside the manifest"}
    try:
        record = json.loads(target.read_text(encoding="utf-8"))
        if record.get("schema") != SCHEMA:
            raise ValueError(f"schema {record.get('schema')!r}")
    except (OSError, ValueError) as error:
        return {**report, "state": "corrupt", "reason": str(error)}
    binding = record.get("binding") or {}
    try:
        stated = json.loads(premap.path(manifest).read_text(encoding="utf-8")).get("inputs_digest")
    except (OSError, ValueError):
        stated = None
    sources = _chosen(sources, _found(manifest, binding.get("inventory_digest")))
    inputs = _inputs(binding.get("inventory_digest"), binding.get("root"), stated, sources)
    if record.get("inputs_digest") != inputs or not premap.binding_matches(manifest, binding):
        return {**report, "state": "stale", "reason": "snapshot, pre-map or sources changed since the entry points"}
    return {**report, **premap.freshness(record, runner)}


def ensure(manifest: Path, sources=None, runner=None, report=None) -> dict:
    """The record of `manifest`, derived again when it is not fresh; with a runner, also when model commands were left
    `not_run`."""
    if state(manifest, sources, runner)["state"] == "fresh":
        return json.loads(path(manifest).read_text(encoding="utf-8"))
    return write(manifest, sources, runner, report)
