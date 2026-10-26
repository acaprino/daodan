"""Bounded graph packets over persisted facts and SQL frontiers."""
from __future__ import annotations

import hashlib
from pathlib import Path

import snapshot
from snapshot_store import file_headers, logical_digest, _pack, _unpack
from semantic_store import semantic_reader
from store_graph_metrics import build_metrics, metric_metadata

NOTES = [
    "Static resolved bindings expand in both directions; unresolved calls never establish an edge.",
    "Module configuration uses only verified inventoried observations; newly added files require a refreshed inventory.",
    "Imports, transitive reachability and PageRank guide reading; they do not establish runtime propagation or change update invalidation.",
    "Coverage gaps and truncation prevent completeness claims; an empty incoming list does not prove a symbol unused.",
    "Read the selected requests through source_reader read before making source-supported claims. Application runtime coverage: none.",
]


def _preflight(store, db, selected, explicit, observations=None):
    from source_reader import _relative, _binding, _source_path
    root, target, perimeter = _binding(store)
    if store.get("parser_fingerprint") != snapshot.parser_fingerprint():
        raise ValueError("parser fingerprint changed or is missing; refresh the manifest")
    db.execute("CREATE TEMP TABLE q_cover(file TEXT PRIMARY KEY,status TEXT,verified INTEGER,payload BLOB)")
    db.execute("CREATE TEMP TABLE q_allowed(file TEXT PRIMARY KEY)")
    rebuild = False
    for rel, entry in store.iter_files(semantic=False):
        _relative(rel)
        modules, bindings = entry.get("imports", []), entry.get("import_bindings", [])
        if (not isinstance(modules, list) or any(not isinstance(module, str) or not module for module in modules)
                or not isinstance(bindings, list) or any(
                    not isinstance(binding, dict) or not isinstance(binding.get("module"), str)
                    or not isinstance(binding.get("names", []), list)
                    or any(not isinstance(name, str) for name in binding.get("names", []))
                    or ("from" in binding and type(binding["from"]) is not bool) for binding in bindings)):
            raise ValueError(f"invalid import metadata for {rel}; refresh the manifest")
        path = root / rel
        within = path.is_relative_to(target) if target.is_dir() else path == target
        row = db.execute("SELECT status,verified,payload FROM sem_coverage WHERE file=?", (rel,)).fetchone()
        if row is None:
            raise ValueError("semantic inventory is incomplete; refresh the manifest")
        if not within or snapshot.is_forbidden(path.name) or not perimeter.covers(path):
            if explicit and rel in selected:
                raise ValueError(f"graph seed is outside the current perimeter: {rel}")
            excluded = {"status": "excluded", "reason": "outside-current-perimeter", "verified_source": False,
                        "reference_count": 0, "resolved_count": 0}
            db.execute("INSERT INTO q_cover VALUES(?,?,0,?)", (rel, "excluded", _pack(excluded)))
            rebuild |= row[0] != "excluded"
            continue
        _source_path(rel, root, target, perimeter)
        if entry.get("parser_profile") != snapshot.parser_profile(path, entry.get("language")):
            raise ValueError(f"parser backend changed for {rel}; refresh the manifest")
        db.execute("INSERT INTO q_cover VALUES(?,?,?,?)", (rel, *row))
        db.execute("INSERT INTO q_allowed VALUES(?)", (rel,))
        rebuild |= row[0] == "excluded"
    # Finish the whole path/backend preflight before opening a source.
    for (rel,) in db.execute("SELECT file FROM q_allowed ORDER BY file"):
        entry = store.get_file(rel, semantic=False)
        path = root / rel
        try:
            data = observations.get(rel) if observations is not None else None
            if data is None:
                data = path.read_bytes() if path.stat().st_size <= snapshot.MAX_FILE_BYTES else None
        except OSError as error:
            raise ValueError(f"cannot verify graph source {rel}; refresh the manifest") from error
        if data is None:
            oversized = {"status": "oversized", "reason": "source-size-limit", "verified_source": False,
                         "reference_count": 0, "resolved_count": 0}
            db.execute("UPDATE q_cover SET status='oversized',verified=0,payload=? WHERE file=?", (_pack(oversized), rel))
            rebuild = True
        else:
            if hashlib.sha256(data).hexdigest() != entry.get("raw_hash"):
                raise ValueError(f"source identity changed or is missing for {rel}; refresh the manifest")
            lines = data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n").split("\n")
            if type(entry.get("lines")) is not int or entry["lines"] != len(lines):
                raise ValueError(f"line metadata is inconsistent for {rel}; refresh the manifest")
            del data, lines
    invalid = db.execute("SELECT file,status FROM q_cover WHERE status IN ('stale','fingerprint-mismatch','unbound-source','malformed') LIMIT 1").fetchone()
    if invalid:
        raise ValueError(f"graph evidence is {invalid[1]} for {invalid[0]}; refresh the manifest")
    digest = logical_digest(store, ensure_ascii=False)
    recorded = db.execute("SELECT payload FROM sem_meta WHERE key='manifest_digest'").fetchone()
    if recorded is None or _unpack(recorded[0]) != digest:
        raise ValueError("recorded semantic facts changed; refresh the snapshot")
    return rebuild, digest


def _packet(store, db, selected, hops, limit, digest):
    from source_reader import _reference, _merge
    db.execute("CREATE TEMP TABLE q_seed(file TEXT PRIMARY KEY)")
    db.executemany("INSERT INTO q_seed VALUES(?)", ((path,) for path in selected))
    db.execute("CREATE TEMP TABLE q_dist(node TEXT PRIMARY KEY,depth INTEGER)")
    db.execute("""INSERT OR IGNORE INTO q_dist SELECT d.id,0 FROM sem_declarations d
                  JOIN q_seed s ON s.file=d.file JOIN q_cover c ON c.file=d.file AND c.verified=1
                  WHERE d.kind IN ('function','class')""")
    db.execute("""INSERT OR IGNORE INTO q_dist SELECT s.file||'::@module',0 FROM q_seed s
                  JOIN q_cover c ON c.file=s.file AND c.verified=1""")
    caller = "coalesce(r.caller,r.file||'::@module')"
    for depth in range(hops):
        db.execute(f"""INSERT OR IGNORE INTO q_dist SELECT r.target_id,? FROM sem_references r
            JOIN q_cover c ON c.file=r.file AND c.verified=1
            JOIN q_dist d ON d.node={caller} AND d.depth=?
            WHERE r.kind='call' AND r.resolution='resolved' ORDER BY r.target_id""", (depth + 1, depth))
        db.execute(f"""INSERT OR IGNORE INTO q_dist SELECT {caller},? FROM sem_references r
            JOIN q_cover c ON c.file=r.file AND c.verified=1
            JOIN q_dist d ON d.node=r.target_id AND d.depth=?
            WHERE r.kind='call' AND r.resolution='resolved' ORDER BY 1""", (depth + 1, depth))
    db.execute("CREATE TEMP TABLE q_calls(id TEXT PRIMARY KEY,file TEXT,depth INTEGER)")
    db.execute(f"""INSERT INTO q_calls SELECT id,file,distance+1 FROM (
        SELECT r.id,r.file,min(coalesce(a.depth,?),
            CASE WHEN r.resolution='resolved' THEN coalesce(b.depth,?) ELSE ? END) AS distance
        FROM sem_references r JOIN q_cover c ON c.file=r.file AND c.verified=1
        LEFT JOIN q_dist a ON a.node={caller} LEFT JOIN q_dist b ON b.node=r.target_id
        WHERE r.kind='call') WHERE distance<?""", (hops, hops, hops, hops))
    db.execute("CREATE TEMP TABLE q_declarations(id TEXT PRIMARY KEY,file TEXT,depth INTEGER)")
    db.execute("""INSERT INTO q_declarations SELECT d.id,d.file,q.depth FROM sem_declarations d
                  JOIN q_dist q ON q.node=d.id JOIN q_cover c ON c.file=d.file AND c.verified=1""")
    db.execute("CREATE TEMP TABLE q_related(file TEXT PRIMARY KEY)")
    db.execute("INSERT OR IGNORE INTO q_related SELECT file FROM q_seed UNION SELECT file FROM q_calls UNION SELECT file FROM q_declarations")
    packet = _reference(store, file_headers(store))
    packet.update(schema="xray/source-graph/v1", manifest_digest=digest,
                  query={"hops": hops, "limit": limit, "path_count": len(selected),
                         "whole_inventory": False}, totals={}, truncated=[])

    def bounded(name, count_sql, rows_sql, decode=lambda row: row[0], parameters=()):
        total = db.execute(count_sql).fetchone()[0]
        packet["totals"][name] = total
        if total > limit:
            packet["truncated"].append(name)
        return [decode(row) for row in db.execute(rows_sql + " LIMIT ?", (*parameters, limit))]

    packet["query"]["paths"] = bounded("query_paths", "SELECT count(*) FROM q_seed", "SELECT file FROM q_seed ORDER BY file")
    packet["calls"] = bounded("calls", "SELECT count(*) FROM q_calls",
        """SELECT r.payload,q.depth FROM q_calls q JOIN sem_references r ON r.id=q.id
           ORDER BY q.depth,r.file,r.l0,r.c0,r.l1,r.c1,r.id""",
        lambda row: {**_unpack(row[0]), "depth": row[1]})
    packet["declarations"] = bounded("declarations", "SELECT count(*) FROM q_declarations",
        """SELECT d.payload,q.depth FROM q_declarations q JOIN sem_declarations d ON d.id=q.id
           ORDER BY q.depth,d.file,d.l0,d.c0,d.l1,d.c1,d.id""",
        lambda row: {**_unpack(row[0]), "depth": row[1]})
    db.execute("CREATE TEMP TABLE q_imports(source TEXT,target TEXT,PRIMARY KEY(source,target))")
    db.execute("""INSERT INTO q_imports SELECT e.source,e.target FROM sem_edges e
        JOIN q_cover a ON a.file=e.source AND a.verified=1 JOIN q_cover b ON b.file=e.target AND b.verified=1
        WHERE EXISTS(SELECT 1 FROM q_related WHERE file=e.source OR file=e.target)""")
    packet["imports"] = bounded("imports", "SELECT count(*) FROM q_imports", "SELECT source,target FROM q_imports ORDER BY source,target",
                                lambda row: {"source": row[0], "target": row[1]})
    packet["coverage"] = {
        "counts": dict(db.execute("SELECT status,count(*) FROM q_cover GROUP BY status ORDER BY status")),
        "files": bounded("coverage", "SELECT count(*) FROM q_cover",
            """SELECT c.file,c.payload FROM q_cover c LEFT JOIN q_related r ON r.file=c.file
               ORDER BY r.file IS NULL,c.file""", lambda row: {"path": row[0], **_unpack(row[1])})}
    # Reverse BFS keeps SQL queue order, preserving the existing deterministic witness.
    db.execute("CREATE TEMP TABLE q_reach(seq INTEGER PRIMARY KEY AUTOINCREMENT,file TEXT UNIQUE,seed TEXT,via TEXT,depth INTEGER)")
    db.executemany("INSERT INTO q_reach(file,seed,via,depth) VALUES(?,?,NULL,0)", ((path, path) for path in selected))
    previous = 0
    while True:
        row = db.execute("SELECT seq,file,seed,depth FROM q_reach WHERE seq>? ORDER BY seq LIMIT 1", (previous,)).fetchone()
        if row is None:
            break
        previous, file, seed, depth = row
        db.executemany("""INSERT OR IGNORE INTO q_reach(file,seed,via,depth) VALUES(?,?,?,?)""",
            ((importer, seed, file, depth + 1) for (importer,) in db.execute(
                """SELECT e.source FROM sem_edges e JOIN q_cover a ON a.file=e.source AND a.verified=1
                   JOIN q_cover b ON b.file=e.target AND b.verified=1 WHERE e.target=? ORDER BY e.source""", (file,))))
    prefix = "sem"
    changed = db.execute("""SELECT 1 FROM q_cover q JOIN sem_coverage s ON q.file=s.file
                            WHERE q.verified<>s.verified LIMIT 1""").fetchone()
    if changed:
        prefix = "q"
        build_metrics(db, prefix="q", temporary=True,
            nodes="SELECT file FROM q_cover WHERE verified=1",
            edges="""SELECT e.source,e.target FROM sem_edges e JOIN q_cover a ON a.file=e.source AND a.verified=1
                     JOIN q_cover b ON b.file=e.target AND b.verified=1""")
    cycle_count = db.execute(f"SELECT count(DISTINCT component) FROM {prefix}_cycles").fetchone()[0]
    packet["totals"]["import_cycles"] = cycle_count
    if cycle_count > limit:
        packet["truncated"].append("import_cycles")
    cycles = []
    for (component,) in db.execute(f"SELECT DISTINCT component FROM {prefix}_cycles ORDER BY component LIMIT ?", (limit,)):
        members = [row[0] for row in db.execute(f"SELECT node FROM {prefix}_cycles WHERE component=? ORDER BY ordinal LIMIT ?", (component, limit + 1))]
        if len(members) > limit and "cycle_members" not in packet["truncated"]:
            packet["truncated"].append("cycle_members")
        cycles.append(members[:limit])
    packet["diagnostics"] = {
        "import_cycles": cycles,
        "transitive_importers": bounded("transitive_importers", "SELECT count(*) FROM q_reach WHERE depth>0",
            "SELECT file,depth,seed,via FROM q_reach WHERE depth>0 ORDER BY depth,file",
            lambda row: {"file": row[0], "depth": row[1], "seed": row[2], "via": row[3]}),
        "pagerank": bounded("pagerank", f"SELECT count(*) FROM {prefix}_rank", f"SELECT node,score FROM {prefix}_rank ORDER BY score DESC,node",
                            lambda row: {"file": row[0], "score": row[1]}),
        **metric_metadata(db, prefix),
    }
    packet["totals"]["cycle_members"] = db.execute(f"SELECT count(*) FROM {prefix}_cycles").fetchone()[0]
    ranges = {path: [] for (path,) in db.execute("SELECT s.file FROM q_seed s JOIN q_cover c ON s.file=c.file AND c.verified=1 ORDER BY s.file")}
    def add_range(item):
        ranges.setdefault(item["file"], []).append((item["span"][0], item["span"][2]))
    for item in packet["declarations"]:
        add_range(item)
    for call in packet["calls"]:
        add_range(call)
        row = db.execute("SELECT payload FROM sem_declarations WHERE id=?", (call["target_id"],)).fetchone()
        if row:
            add_range(_unpack(row[0]))
    requests, total_ranges = [], 0
    for rel, intervals in sorted(ranges.items()):
        intervals = _merge(intervals)
        total_ranges += len(intervals)
        if len(intervals) > limit and "request_ranges" not in packet["truncated"]:
            packet["truncated"].append("request_ranges")
        requests.append({"path": rel, "ranges": [{"start": start, "end": end} for start, end in intervals[:limit]]}
                        if intervals else {"path": rel, "full_file": True})
    packet["totals"]["requests"] = len(requests)
    if len(requests) > limit:
        packet["truncated"].append("requests")
    packet["requests"] = requests[:limit]
    packet["totals"]["request_ranges"] = total_ranges
    packet["truncated"].sort()
    packet["notes"] = list(NOTES)
    return packet


def query_graph(store, paths=None, hops=2, limit=100):
    from source_reader import _relative
    if type(hops) is not int or not 1 <= hops <= 3:
        raise ValueError("hops must be an integer from 1 to 3")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer from 1 through 1000")
    if paths is not None and (not isinstance(paths, list) or not paths):
        raise ValueError("paths must be a nonempty list of exact inventoried files")
    selected = sorted(set(store.iter_paths() if paths is None else [_relative(path) for path in paths]))
    if any(not store.has_file(path) for path in selected):
        raise ValueError("graph seed path is not inventoried")
    with semantic_reader(store) as db:
        rebuild, digest = _preflight(store, db, set(selected), paths is not None)
        if rebuild:
            with semantic_reader(store, rebuild=True) as current:
                _, digest = _preflight(store, current, set(selected), paths is not None)
                packet = _packet(store, current, selected, hops, limit, digest)
        else:
            packet = _packet(store, db, selected, hops, limit, digest)
    packet["query"]["whole_inventory"] = paths is None
    return packet
