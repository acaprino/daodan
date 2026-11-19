"""The derived edge store beside a snapshot: its schema, its binding to the snapshot, the entries of
each language and their declared coverage."""
from __future__ import annotations

import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import semantic_store
from snapshot_store import _pack, _unpack, logical_digest


EDGE_SCHEMA = 5


# One row per end of a reference: `verdict` is the end's class, `confidence` confirmed, uncertain, `OBSERVED` or
# `SAMPLED`.
EDGE_COLUMNS = ("reference_id", "file", "language", "kind", "caller", "l0", "c0", "verdict", "target_id", "symbol",
                "resolver", "confidence", "payload")


HOLE_COLUMNS = ("reference_id", "file", "language", "kind", "l0", "c0", "class", "reason", "resolver")


EXTERNAL_COLUMNS = ("symbol", "manager", "package", "version")


# The confidence of an end seen in a run (the dynamic step): it holds for that run, and proves that the call can
# arrive there, not that it arrives only there. Its `resolver` names the recorder. `OBSERVED` is an exact
# recorder's (every call, at its site); `SAMPLED` a pair of a sampling profiler's stack, which may name no call
# site: then its row has no reference, an edge between two declarations. What a sample did not see is no fact.
OBSERVED, SAMPLED = "observed", "sampled"
SEEN = (OBSERVED, SAMPLED)  # the exact one first


def default_edge_store(manifest: Path) -> Path:
    """The derived store's place: beside the snapshot it is bound to."""
    return Path(manifest).with_name("engine-edges.sqlite")


def store_binding(store, manifest: Path, fingerprint: str, entries: dict, reports: dict) -> dict:
    """The store's meta: its snapshot, one entry per language an engine covered, and their totals.

    Each entry is what one engine pass established for one language. The totals
    exist for consumers that read one store as one population.
    """
    entries = dict(sorted(entries.items()))
    values = list(entries.values())
    verdicts: dict[str, int] = {}
    for entry in values:
        for key, count in (entry.get("verdicts") or {}).items():
            verdicts[key] = verdicts.get(key, 0) + count
    confirmed = sum(entry.get("confirmed", 0) for entry in values)
    candidates = sum(entry.get("candidates", 0) for entry in values)
    reasons = {entry.get("no_edges_reason") for entry in values} - {None}
    return {
        "schema": EDGE_SCHEMA,
        "manifest": Path(manifest).as_posix(),
        "manifest_digest": logical_digest(store),
        "parser_fingerprint": fingerprint,
        "resolver_version": semantic_store.RESOLVER_VERSION,
        "languages": entries,
        "engine_reports": dict(sorted(reports.items())),
        "engine": " + ".join(sorted({entry["engine"] for entry in values})) or None,
        "population": sum(entry.get("population", 0) for entry in values),
        "selected": sum(entry.get("selected", 0) for entry in values),
        "asked": sum(entry.get("asked", 0) for entry in values),
        "stride": max([entry.get("stride", 1) for entry in values] or [1]),
        "confirmed": confirmed,
        "candidates": candidates,
        "no_edges_reason": None if confirmed or candidates else (reasons.pop() if len(reasons) == 1 else
                                                                 "no-project-targets" if reasons else None),
        "verdicts": dict(sorted(verdicts.items())),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_edge_store(out: Path, edges: list[dict], binding: dict, holes: list[dict] = ()) -> Path:
    """Write the store atomically, so a partial pass leaves no store.

    An edge's `external` (`{manager, package, version}`) is kept once per symbol in `externals`.
    """
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".partial", dir=out.parent)
    os.close(descriptor)
    temporary = Path(name)
    externals = {edge["symbol"]: edge["external"] for edge in edges if edge.get("external") and edge.get("symbol")}
    try:
        connection = sqlite3.connect(temporary)
        try:
            connection.execute("CREATE TABLE meta(key TEXT PRIMARY KEY,value BLOB NOT NULL)")
            connection.execute(
                "CREATE TABLE edges(reference_id TEXT,file TEXT NOT NULL,language TEXT,kind TEXT NOT NULL,caller TEXT,"
                "l0 INTEGER,c0 INTEGER,verdict TEXT NOT NULL,target_id TEXT,symbol TEXT,resolver TEXT NOT NULL,"
                "confidence TEXT NOT NULL,payload BLOB NOT NULL)")
            connection.execute(
                "CREATE TABLE holes(reference_id TEXT,file TEXT NOT NULL,language TEXT,kind TEXT NOT NULL,"
                "l0 INTEGER,c0 INTEGER,class TEXT NOT NULL,reason TEXT,resolver TEXT NOT NULL)")
            connection.execute("CREATE TABLE externals(symbol TEXT PRIMARY KEY,manager TEXT,package TEXT,version TEXT)")
            connection.execute("CREATE INDEX edges_reference ON edges(reference_id)")
            connection.execute("CREATE INDEX edges_file ON edges(file)")
            connection.execute("CREATE INDEX edges_target ON edges(target_id)")
            connection.execute("CREATE INDEX holes_reference ON holes(reference_id)")
            connection.executemany("INSERT INTO meta VALUES(?,?)",
                                   [(key, _pack(value)) for key, value in sorted(binding.items())])
            connection.executemany(
                f"INSERT INTO edges VALUES({','.join('?' for _ in EDGE_COLUMNS)})",
                [tuple(_pack(edge[key]) if key == "payload" else edge.get(key) for key in EDGE_COLUMNS)
                 for edge in edges])
            connection.executemany(f"INSERT INTO holes VALUES({','.join('?' for _ in HOLE_COLUMNS)})",
                                   [tuple(hole.get(key) for key in HOLE_COLUMNS) for hole in holes])
            connection.executemany("INSERT INTO externals VALUES(?,?,?,?)",
                                   [(symbol, *(package.get(key) for key in EXTERNAL_COLUMNS[1:]))
                                    for symbol, package in sorted(externals.items())])
            connection.commit()
        finally:
            connection.close()
        os.replace(temporary, out)
    finally:
        temporary.unlink(missing_ok=True)
    return out


def read_edge_store(path: Path, store) -> tuple[list[dict] | None, dict | None, str | None]:
    """The edges bound to this exact snapshot, their binding, or the reason they are not.

    A store whose manifest digest, parser fingerprint or resolver version differs
    describes another snapshot or policy, and its edges are not this graph's: the
    caller gets the reason rather than a plausible-looking join.
    """
    path = Path(path)
    if not path.is_file():
        return None, None, f"no engine edge store at {path}"
    connection = None
    binding = None
    try:
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        binding = {key: _unpack(value) for key, value in connection.execute("SELECT key,value FROM meta")}
        if binding.get("schema") != EDGE_SCHEMA:
            return None, binding, f"engine edge store schema {binding.get('schema')} is not {EDGE_SCHEMA}"
        if binding.get("manifest_digest") != logical_digest(store):
            return None, binding, "the edge store is bound to a different snapshot revision"
        if binding.get("parser_fingerprint") != store.metadata.get("parser_fingerprint"):
            return None, binding, "the edge store was written under another parser fingerprint"
        if binding.get("resolver_version") != semantic_store.RESOLVER_VERSION:
            return (
                None,
                binding,
                f"the edge store was written under resolver version {binding.get('resolver_version')}, "
                f"expected {semantic_store.RESOLVER_VERSION}",
            )
        externals = {row[0]: dict(zip(EXTERNAL_COLUMNS[1:], row[1:]))
                     for row in connection.execute(f"SELECT {','.join(EXTERNAL_COLUMNS)} FROM externals")}
        edges = []
        for row in connection.execute(f"SELECT {','.join(EDGE_COLUMNS)} FROM edges ORDER BY file,l0,c0"):
            edge = {key: _unpack(value) if key == "payload" else value for key, value in zip(EDGE_COLUMNS, row)}
            if edge["verdict"] == "external":
                edge["external"] = externals.get(edge["symbol"])
            edges.append(edge)
        if getattr(store, "format", None) == "sqlite" and getattr(store, "connection", None) is not None:
            with semantic_store.semantic_reader(store) as sem_db:
                valid_targets = {
                    row[0]
                    for row in sem_db.execute(
                        "SELECT id FROM sem_declarations WHERE kind IN ('function','method','class')"
                    )
                }
                valid_refs = {
                    row[0]: (row[1], row[2])
                    for row in sem_db.execute(
                        "SELECT id,file,caller FROM sem_references WHERE kind IN ('call','read')"
                    )
                }
            for edge in edges:
                ref_id = edge.get("reference_id")
                if ref_id is None:
                    # A site the snapshot lists no reference for: kept, read by no consumer.
                    continue
                if ref_id not in valid_refs:
                    return None, binding, f"engine edge reference is not in snapshot: {ref_id}"
                ref_file, ref_caller = valid_refs[ref_id]
                if edge.get("file") != ref_file or edge.get("caller") != ref_caller:
                    return None, binding, f"engine edge callsite metadata mismatch for {ref_id}"
                if edge.get("verdict") == "project-callable" and edge.get("confidence") != "uncertain":
                    target_id = edge.get("target_id")
                    if not target_id or target_id not in valid_targets:
                        return None, binding, f"engine edge target is not in snapshot: {target_id}"
        return edges, binding, None
    except (sqlite3.Error, ValueError, TypeError) as error:
        return None, binding, f"invalid engine edge store: {error}"
    finally:
        if connection is not None:
            connection.close()


def kept_languages(destination: Path, store, replaced) -> tuple[dict, list[dict], list[dict], dict]:
    """What the store already holds for the languages a write does not replace: their entries, edges, holes and
    engine reports; nothing when there is no store or it belongs to another snapshot."""
    if not Path(destination).is_file():
        return {}, [], [], {}
    previous, binding, reason = read_edge_store(destination, store)
    if reason is not None:
        return {}, [], [], {}
    entries = {language: entry for language, entry in (binding.get("languages") or {}).items()
               if language not in replaced}
    edges = [edge for edge in previous if edge.get("language") in entries]
    holes = [hole for hole in read_edge_holes(destination) if hole["language"] in entries]
    reports = {key: value for key, value in (binding.get("engine_reports") or {}).items()
               if key in {entry["engine"] for entry in entries.values()}}
    return entries, edges, holes, reports


# The class a site is answered under: the first of these its store rows hold.
END_ORDER = ("project-callable", "external", "project-value")


def language_coverage(sites, edges, holes, files: dict | None = None) -> dict:
    """One language's coverage: what the store answers at each call and read the snapshot lists for it.

    `sites` are `{reference_id, kind, site, lexical}` (`site` names the place in examples, `lexical` is true when
    the lexical resolver resolved it); `edges` and `holes` are the store's rows. A site with an end other than a
    dead end is `answered` under the first class of `END_ORDER` it holds; one without, that the lexical resolver
    resolved, is answered `lexical`; any other is a hole, by its hole row's class, `dead-end` when only dead ends
    answer it, with up to three examples. `uncertain` counts the sites with an uncertain edge, `externals` the
    sites per package, and `files` is the index's (snapshot files, indexed files, the missing ones with their
    reason), None without an index. `state` is `complete` when no file is missing, no site is a hole and no call
    ends only in a value, else `lower-bound`. A site the store holds nothing for breaks sites = answered + holes:
    it is listed in `violations`, by kind, and never counted.

    The rows of a run (`SEEN`) are counted apart, by provenance, so what the static steps answer stays
    comparable: a site keeps its static class whatever a run saw there; a hole with an end of a run is answered
    `observed`, or `sampled` when no exact end answers it, and leaves `holes`, its class counted in that
    provenance's `closed`. `observed` and `sampled` (the sites with such an end, the `edges`, those between two
    declarations included, `closed` by hole class) are there only when the store holds such rows.
    """
    import collections
    rows, seen = collections.defaultdict(list), {provenance: collections.Counter() for provenance in SEEN}
    for edge in edges:
        if edge.get("confidence") in seen:
            seen[edge["confidence"]][edge.get("reference_id")] += 1
        elif edge.get("reference_id") is not None:
            rows[edge["reference_id"]].append(edge)
    holed = {hole["reference_id"]: hole["class"] for hole in holes if hole.get("reference_id") is not None}
    answered, counted, examples = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    externals, violations = collections.Counter(), collections.defaultdict(list)
    closed = {provenance: collections.Counter() for provenance in SEEN}
    uncertain = values = 0
    for site in sites:
        found = rows.get(site["reference_id"], ())
        classes = {row["verdict"] for row in found} - {"dead-end"}
        end = next((name for name in END_ORDER if name in classes), min(classes) if classes else None)
        uncertain += any(row.get("confidence") == "uncertain" for row in found)
        externals.update({f"{package['manager']} {package['package']}@{package['version']}"
                          for package in (row.get("external") for row in found if row["verdict"] == "external")
                          if package})
        if end is not None:
            answered[end] += 1
            values += end == "project-value" and site["kind"] == "call"
        elif site["lexical"]:
            answered["lexical"] += 1
        elif site["reference_id"] in holed or found:
            name = holed.get(site["reference_id"], "dead-end")
            run = next((provenance for provenance in SEEN if site["reference_id"] in seen[provenance]), None)
            if run is not None:
                answered[run] += 1
                closed[run][name] += 1
                continue
            counted[name] += 1
            if len(examples[name]) < 3:
                examples[name].append(site["site"])
        else:
            violations[site["kind"]].append(site["site"])
    complete = not counted and not values and not (files or {}).get("missing")
    out = {"sites": len(sites), "answered": dict(sorted(answered.items())),
           "holes": {name: {"count": counted[name], "examples": examples[name]} for name in sorted(counted)},
           "uncertain": uncertain, "externals": dict(externals.most_common()), "files": files,
           "state": "complete" if complete else "lower-bound"}
    if violations:
        out["violations"] = dict(sorted(violations.items()))
    for provenance, found in seen.items():
        if found:
            out[provenance] = {"sites": len(found.keys() - {None}), "edges": sum(found.values()),
                               "closed": dict(sorted(closed[provenance].items()))}
    return out


def coverage_violation(language: str, coverage: dict) -> str | None:
    """Why a store may not be written: the sites it would hold nothing for, by kind."""
    found = coverage.get("violations")
    if not found:
        return None
    return (f"{language}: the store breaks sites = answered + holes; "
            + "; ".join(f"{kind} {len(items)}: {', '.join(items[:5])}" for kind, items in found.items()))


def read_edge_holes(path: Path) -> list[dict]:
    """The holes of a store `read_edge_store` accepted: references with no answer, by class."""
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return [dict(zip(HOLE_COLUMNS, row)) for row in connection.execute(
            f"SELECT {','.join(HOLE_COLUMNS)} FROM holes ORDER BY file,l0,c0")]
    finally:
        connection.close()
