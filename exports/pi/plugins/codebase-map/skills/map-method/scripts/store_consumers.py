"""File analysis and symbol lookups over bounded, source-bound SQLite queries."""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
from pathlib import Path
import sqlite3
import tempfile

from snapshot_store import open_snapshot, _pack, _unpack
from semantic_store import semantic_reader
from store_graph_metrics import metric_metadata


@contextmanager
def temporary_snapshot(target, *, parse_results=None):
    """Own one snapshot for a standalone operation; workflow callers pass their run snapshot."""
    import snapshot
    with tempfile.TemporaryDirectory(prefix="map-analysis-") as temporary:
        path = Path(temporary) / "manifest.sqlite"
        snapshot.write_snapshot(target, path, parse_results=parse_results)
        with open_snapshot(path, expected_format="sqlite") as store:
            yield store


@contextmanager
def consumer_reader(store, *, fresh=False, observations=None):
    """Fresh means the snapshot was extracted by this very operation."""
    from store_graph import _preflight
    with ExitStack() as stack:
        db = stack.enter_context(semantic_reader(store))
        if fresh:
            db.execute("CREATE TEMP TABLE q_cover AS SELECT file,status,verified,payload FROM sem_coverage")
        else:
            rebuild, _ = _preflight(store, db, set(), False, observations)
            if rebuild:
                db = stack.enter_context(semantic_reader(store, rebuild=True))
                _preflight(store, db, set(), False, observations)
        yield db


def fan_in(store, db, perimeter=None):
    root = Path(store["root"])
    db.execute("CREATE TEMP TABLE IF NOT EXISTS consumer_allowed(file TEXT PRIMARY KEY)")
    db.execute("DELETE FROM consumer_allowed")
    db.executemany("INSERT INTO consumer_allowed VALUES(?)",
                   ((rel,) for rel in store.iter_paths() if perimeter is None or perimeter.covers(root / rel)))
    return dict(db.execute("""SELECT a.file,count(DISTINCT e.source) FROM consumer_allowed a
        LEFT JOIN sem_edges e ON e.target=a.file AND e.source<>a.file
          AND EXISTS(SELECT 1 FROM consumer_allowed b WHERE b.file=e.source)
        GROUP BY a.file ORDER BY a.file"""))


def file_analysis(store, db, rel, limit=100):
    """Return exact counts and explicitly bounded evidence for one source file."""
    def rows(sql, parameters=()):
        total = db.execute("SELECT count(*) FROM (" + sql + ")", parameters).fetchone()[0]
        values = [_unpack(row[0]) for row in db.execute(sql + " LIMIT ?", (*parameters, limit))]
        return total, values
    declarations_count, declarations = rows(
        "SELECT payload FROM sem_declarations WHERE file=? AND kind IN ('function','class') ORDER BY rowid", (rel,))
    calls_count, calls = rows(
        "SELECT payload FROM sem_references WHERE file=? AND kind='call' ORDER BY rowid", (rel,))
    incoming_count, incoming = rows("""SELECT r.payload FROM sem_references r JOIN sem_declarations d
        ON d.id=r.target_id WHERE d.file=? AND d.kind IN ('function','class')
        AND r.file<>? AND r.kind='call' ORDER BY r.file,r.rowid""", (rel, rel))
    resolved = db.execute("SELECT count(*) FROM sem_references WHERE file=? AND kind='call' AND resolution='resolved'", (rel,)).fetchone()[0]
    coverage = db.execute("SELECT payload FROM q_cover WHERE file=?", (rel,)).fetchone()
    semantic = {
        "coverage": _unpack(coverage[0]) if coverage else {"status": "unavailable"},
        "project_coverage": dict(db.execute("SELECT status,count(*) FROM q_cover GROUP BY status")),
        "raw_hash": (store.get_file(rel, semantic=False) or {}).get("raw_hash"),
        "parser_fingerprint": store.get("parser_fingerprint"),
        "declarations": declarations, "callsites": calls, "incoming_calls": incoming,
        "counts": {"declarations": declarations_count, "callsites": calls_count,
                   "resolved_callsites": resolved, "unresolved_callsites": calls_count - resolved,
                   "incoming_calls": incoming_count,
                   "project_unresolved_calls": db.execute(
                       "SELECT count(*) FROM sem_references WHERE kind='call' AND resolution<>'resolved'").fetchone()[0]},
        "limit": limit,
        "truncated": [name for name, count in (("declarations", declarations_count), ("callsites", calls_count),
                                              ("incoming_calls", incoming_count)) if count > limit],
        "notes": ["Static bindings only; unknown receivers and ambiguous bindings have no asserted target.",
                  "An empty incoming list does not establish that a declaration is unused.",
                  "Application runtime coverage: none."],
    }
    modules = {}
    for module, target in db.execute("SELECT module,target FROM sem_modules WHERE file=? AND target<>? ORDER BY module,target", (rel, rel)):
        modules.setdefault(module, []).append(target)
    # Keep reverse reachability on disk even when the transitive closure is large.
    db.execute("CREATE TEMP TABLE consumer_reach(file TEXT PRIMARY KEY,depth INTEGER,seed TEXT,via TEXT)")
    db.execute("INSERT INTO consumer_reach VALUES(?,0,?,NULL)", (rel, rel))
    depth = 0
    while True:
        before = db.total_changes
        db.execute("""INSERT OR IGNORE INTO consumer_reach
            SELECT e.source,?,r.seed,e.target FROM sem_edges e JOIN consumer_reach r ON r.file=e.target
            WHERE r.depth=? ORDER BY r.file,e.source""", (depth + 1, depth))
        if db.total_changes == before:
            break
        depth += 1
    reach_total = db.execute("SELECT count(*) FROM consumer_reach WHERE depth>0").fetchone()[0]
    reach = [dict(zip(("file", "depth", "seed", "via"), row)) for row in db.execute(
        "SELECT file,depth,seed,via FROM consumer_reach WHERE depth>0 ORDER BY depth,file LIMIT ?", (limit,))]
    components = "SELECT DISTINCT component FROM sem_cycles WHERE component IN (SELECT component FROM sem_cycles WHERE node=?)"
    own_cycles = db.execute("SELECT count(*) FROM (" + components + ")", (rel,)).fetchone()[0]
    cycles, clipped = [], False
    for (component,) in db.execute(components + " ORDER BY component LIMIT ?", (rel, limit)):
        members = [row[0] for row in db.execute("SELECT node FROM sem_cycles WHERE component=? ORDER BY ordinal LIMIT ?", (component, limit + 1))]
        clipped |= len(members) > limit
        cycles.append(members[:limit])
    rank = db.execute("SELECT score FROM sem_rank WHERE node=?", (rel,)).fetchone()
    diagnostics = {
        "nodes": db.execute("SELECT count(*) FROM sem_rank").fetchone()[0],
        "edges": db.execute("SELECT count(*) FROM sem_edges").fetchone()[0],
        "import_cycles": cycles,
        "project_cycle_count": db.execute("SELECT count(DISTINCT component) FROM sem_cycles").fetchone()[0],
        "transitive_importers": reach, "pagerank": rank[0] if rank else 0.0,
        **metric_metadata(db),
        "totals": {"import_cycles": own_cycles, "transitive_importers": reach_total},
        "limit": limit, "truncated": (["transitive_importers"] if reach_total > limit else [])
                                    + (["import_cycles"] if own_cycles > limit else [])
                                    + (["cycle_members"] if clipped else []),
        "interpretation": "Static import reachability and centrality; no runtime propagation or criticality claim.",
    }
    return semantic, diagnostics, modules


def _importing_symbols(store, db, source_key, symbols, searched):
    """Apply the existing import-binding policy to indexed module targets."""
    from snapshot import _python_module_candidates
    root, source = Path(store["root"]), Path(store["root"]) / source_key
    target = root / store["target"]
    default_export = (store.get_file(source_key, semantic=False) or {}).get("default_export")
    for (rel,) in db.execute("SELECT DISTINCT file FROM sem_modules WHERE target=? ORDER BY file", (source_key,)):
        if rel == source_key or rel not in searched:
            continue
        entry = store.get_file(rel, semantic=False)
        for binding in entry.get("import_bindings", []):
            if db.execute("SELECT 1 FROM sem_modules WHERE file=? AND module=? AND target=?",
                          (rel, binding["module"], source_key)).fetchone() is None:
                continue
            names = list(binding.get("names", []))
            default_import = binding.get("default_import")
            if default_import in names:
                names.remove(default_import)
            wildcard = any(name.startswith("*") for name in names)
            if not binding.get("from"):
                wildcard = not names or not names[0].lstrip().startswith("{")
                if Path(rel).suffix.lower() == ".py":
                    wildcard = True
            elif Path(rel).suffix.lower() == ".py":
                candidates = _python_module_candidates(binding["module"], (root / rel).parent, target)
                wildcard |= any(source.resolve() == Path(candidate.rstrip("/") + "/" + name + ending).resolve()
                                for candidate in candidates for name in names if name != "*"
                                for ending in (".py", "/__init__.py"))
            declared = {part.strip().split(" as ")[0].split(":")[0].strip()
                        for name in names for part in name.strip("{} ").split(",")}
            for symbol in symbols:
                if wildcard or symbol in declared or ((default_import or "default" in declared) and symbol == default_export):
                    yield symbol, rel


def find_usages(store, db, symbols, source_file, project_root, *, limit=None, observations=None):
    """Count complete matches on disk, then decode only the requested sample."""
    from usage_finder import (UsageLocation, UsageResult, SEARCH_EXTENSIONS, SOURCE_EXTENSIONS,
                              DEFAULT_EXCLUDES, is_excluded, _is_same_file, _classify_usage,
                              _source_module_for, _import_patterns)
    root = Path(store["root"])
    source_key = next((rel for rel in store.iter_paths() if _is_same_file(str(root / rel), source_file)), None)
    # Paths/coverage are small inventory metadata; semantic records stay in SQLite.
    coverage = {rel: _unpack(payload) for rel, payload in db.execute("SELECT file,payload FROM q_cover ORDER BY file")}
    searched = {rel for rel, entry in coverage.items() if entry.get("verified_source")
                and Path(rel).suffix.lower() in SEARCH_EXTENSIONS
                and not _is_same_file(str(root / rel), source_file)
                and not is_excluded(root / rel, DEFAULT_EXCLUDES)}
    db.execute("CREATE TEMP TABLE usage_searched(file TEXT PRIMARY KEY)")
    db.executemany("INSERT INTO usage_searched VALUES(?)", ((rel,) for rel in searched))
    db.execute("""CREATE TEMP TABLE usage_matches(seq INTEGER PRIMARY KEY,symbol TEXT,file TEXT,
                  line INTEGER,column INTEGER,precision TEXT,payload BLOB)""")
    db.execute("CREATE INDEX usage_matches_order ON usage_matches(symbol,file,line,column,seq)")
    db.execute("CREATE TEMP TABLE usage_importing(symbol TEXT,file TEXT,PRIMARY KEY(symbol,file))")
    def add(symbol, rel, location):
        payload = location.__dict__.copy()
        db.execute("INSERT INTO usage_matches(symbol,file,line,column,precision,payload) VALUES(?,?,?,?,?,?)",
                   (symbol, rel, location.line_number, location.column or 0, location.precision, _pack(payload)))
    exported_names = {symbol: {symbol} for symbol in symbols}
    if source_key and coverage.get(source_key, {}).get("status") == "ast":
        for exported in store.iter_records("exports", path=source_key):
            if not exported.get("module") and exported.get("local") in exported_names:
                exported_names[exported["local"]].add(exported["exported"])
    for symbol in symbols:
        # Candidate projection mirrors the conservative legacy predicate, including
        # unknown receivers with no candidate_files. Payloads are decoded after SQL selection.
        query = """SELECT r.payload FROM sem_references r JOIN usage_searched s ON s.file=r.file
            WHERE r.target_id IN (SELECT id FROM sem_declarations
                WHERE file=? AND name=? AND kind IN ('function','class'))
            OR (r.known_unrelated=0 AND r.resolution<>'resolved' AND (
                EXISTS(SELECT 1 FROM sem_reference_candidates c WHERE c.reference=r.id
                    AND c.file=? AND c.imported IN (?,'default'))
                OR (r.has_candidates=0 AND r.last_name=?)))
            ORDER BY r.file,r.rowid"""
        targets = {row[0] for row in db.execute(
            "SELECT id FROM sem_declarations WHERE file=? AND name=? AND kind IN ('function','class')", (source_key, symbol))}
        for (payload,) in db.execute(query, (source_key, symbol, source_key, symbol, symbol)):
            ref = _unpack(payload)
            l0, c0, l1, c1 = ref["span"]
            add(symbol, ref["file"], UsageLocation(
                str(root / ref["file"]), l0, "", "call" if ref["kind"] == "call" else "reference",
                "resolved-static" if ref["target_id"] in targets else "ast-candidate",
                c0, l1, c1, ref["span"], ref["caller"], ref["target_id"], ref["reason"]))
    graph_language = source_file.suffix.lower() in {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
    for rel in sorted(searched):
        if coverage[rel]["status"] == "ast":
            for imported in store.iter_records("imports", path=rel):
                if db.execute("SELECT 1 FROM sem_modules WHERE file=? AND module=? AND target=?",
                              (rel, imported["module"], source_key)).fetchone() is None:
                    continue
                for symbol in symbols:
                    relevant = (imported["mode"] == "namespace"
                                or (imported["mode"] == "named" and imported["imported"] in exported_names[symbol])
                                or (imported["mode"] == "default" and "default" in exported_names[symbol]))
                    if relevant:
                        l0, c0, l1, c1 = imported["span"]
                        add(symbol, rel, UsageLocation(str(root / rel), l0, "", "import", "ast-candidate",
                            c0, l1, c1, imported["span"], reason="import-binding-not-call"))
            if graph_language:
                continue
        data = observations.get(rel) if observations is not None else None
        if data is None:
            data = (root / rel).read_bytes()
        import hashlib
        if hashlib.sha256(data).hexdigest() != coverage[rel].get("raw_hash"):
            raise ValueError(f"source identity changed for {rel}; refresh the snapshot")
        text = data.decode("utf-8")
        if coverage[rel]["status"] != "ast":
            for number, line in enumerate(text.splitlines(), 1):
                for symbol in symbols:
                    if symbol in line:
                        add(symbol, rel, UsageLocation(str(root / rel), number, line.strip(),
                            _classify_usage(line, symbol), reason=coverage[rel].get("reason")))
        if not graph_language and Path(rel).suffix.lower() in SOURCE_EXTENSIONS:
            for symbol in symbols:
                if any(pattern.search(text) for pattern in _import_patterns(symbol, _source_module_for(source_file, project_root))):
                    db.execute("INSERT OR IGNORE INTO usage_importing VALUES(?,?)", (symbol, rel))
    if graph_language and source_key is not None:
        db.executemany("INSERT OR IGNORE INTO usage_importing VALUES(?,?)",
                       _importing_symbols(store, db, source_key, symbols, searched))
    ast_files = sum(coverage[rel]["status"] == "ast" for rel in searched)
    precision = "ast-and-lexical" if ast_files and len(searched) > ast_files else "ast" if ast_files else "lexical"
    results = {}
    for symbol in symbols:
        counts = dict(db.execute("SELECT precision,count(*) FROM usage_matches WHERE symbol=? GROUP BY precision", (symbol,)))
        total = sum(counts.values())
        sample, current_file, lines = [], None, []
        for rel, payload in db.execute(
                "SELECT file,payload FROM usage_matches WHERE symbol=? ORDER BY file,line,column,seq LIMIT ?",
                (symbol, -1 if limit is None else limit)):
            item = _unpack(payload)
            if item["precision"] != "lexical-candidate":
                if rel != current_file:
                    data = observations.get(rel) if observations is not None else None
                    if data is None:
                        data = (root / rel).read_bytes()
                    import hashlib
                    if hashlib.sha256(data).hexdigest() != coverage[rel].get("raw_hash"):
                        raise ValueError(f"source identity changed for {rel}; refresh the snapshot")
                    current_file, lines = rel, data.decode("utf-8").splitlines()
                item["line_content"] = lines[item["line_number"] - 1].strip() if item["line_number"] <= len(lines) else ""
            sample.append(UsageLocation(**item))
        importing = [row[0] for row in db.execute("SELECT file FROM usage_importing WHERE symbol=? ORDER BY file", (symbol,))]
        results[symbol] = UsageResult(
            symbol, str(source_file), sample, importing, counts.get("resolved-static", 0),
            counts.get("ast-candidate", 0), counts.get("lexical-candidate", 0), precision, coverage,
            ["Resolved static bindings, unresolved AST candidates and lexical matches are separate evidence.",
             "Static bindings only; no type inference or runtime execution coverage."]
            + [f"{rel}: {item['status']} ({item.get('reason')})" for rel, item in coverage.items() if item["status"] != "ast"],
            total_count=total, truncated=limit is not None and total > limit, limit=limit)
    return results
