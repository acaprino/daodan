"""Exact import diagnostics using disk-backed work tables and bounded Python state."""
from __future__ import annotations

import math

from snapshot_store import _pack, _unpack


def build_metrics(db, *, prefix, temporary, nodes, edges):
    if prefix not in {"sem", "q"}:
        raise ValueError("invalid graph metrics namespace")
    modifier = "TEMP " if temporary else ""
    rank, links, cycles, meta = (prefix + suffix for suffix in ("_rank", "_metric_edges", "_cycles", "_graph_meta"))
    work, component = prefix + "_walk", prefix + "_component"
    db.execute(f"CREATE {modifier}TABLE {rank}(node TEXT PRIMARY KEY,score REAL,next REAL,degree INTEGER,visited INTEGER,finished INTEGER)")
    db.execute(f"INSERT INTO {rank}(node,visited) SELECT file,0 FROM ({nodes})")
    db.execute(f"CREATE TEMP TABLE {links}(source TEXT,target TEXT,PRIMARY KEY(source,target))")
    db.execute(f"INSERT OR IGNORE INTO {links} {edges}")
    db.execute(f"CREATE INDEX {links}_reverse ON {links}(target,source)")
    db.execute(f"UPDATE {rank} SET degree=(SELECT count(*) FROM {links} WHERE source=node)")
    count = db.execute(f"SELECT count(*) FROM {rank}").fetchone()[0]
    if count:
        db.execute(f"UPDATE {rank} SET score=?", (1 / count,))
    converged, iterations = not count, 0
    damping, tolerance, maximum = 0.85, 1e-10, 100
    if count:
        for iterations in range(1, maximum + 1):
            dangling = math.fsum(row[0] for row in db.execute(f"SELECT score FROM {rank} WHERE degree=0 ORDER BY node"))
            base = (1 - damping + damping * dangling) / count
            db.execute(f"UPDATE {rank} SET next=?", (base,))
            for source, score, degree in db.execute(f"SELECT node,score,degree FROM {rank} WHERE degree>0 ORDER BY node"):
                contribution = damping * score / degree
                for (target,) in db.execute(f"SELECT target FROM {links} WHERE source=? ORDER BY target", (source,)):
                    db.execute(f"UPDATE {rank} SET next=next+? WHERE node=?", (contribution, target))
            difference = math.fsum(abs(next_value - score) for score, next_value in db.execute(f"SELECT score,next FROM {rank} ORDER BY node"))
            db.execute(f"UPDATE {rank} SET score=next")
            if difference <= tolerance:
                converged = True
                break
    db.execute(f"CREATE {modifier}TABLE {meta}(key TEXT PRIMARY KEY,payload BLOB NOT NULL)")
    values = {"pagerank_converged": converged, "pagerank_iterations": iterations,
              "pagerank_damping": damping, "pagerank_tolerance": tolerance,
              "pagerank_max_iterations": maximum}
    db.executemany(f"INSERT INTO {meta} VALUES(?,?)", ((key, _pack(value)) for key, value in values.items()))
    db.execute(f"CREATE TEMP TABLE {work}(seq INTEGER PRIMARY KEY AUTOINCREMENT,node TEXT,exiting INTEGER)")
    db.execute(f"CREATE TEMP TABLE {component}(node TEXT PRIMARY KEY)")
    db.execute(f"CREATE {modifier}TABLE {cycles}(component TEXT,ordinal INTEGER,node TEXT,PRIMARY KEY(component,ordinal))")
    finished = 0
    for (root,) in db.execute(f"SELECT node FROM {rank} ORDER BY node"):
        if db.execute(f"SELECT visited FROM {rank} WHERE node=?", (root,)).fetchone()[0]:
            continue
        db.execute(f"INSERT INTO {work}(node,exiting) VALUES(?,0)", (root,))
        while True:
            row = db.execute(f"SELECT seq,node,exiting FROM {work} ORDER BY seq DESC LIMIT 1").fetchone()
            if row is None:
                break
            seq, node, exiting = row
            db.execute(f"DELETE FROM {work} WHERE seq=?", (seq,))
            if exiting:
                db.execute(f"UPDATE {rank} SET finished=? WHERE node=?", (finished, node))
                finished += 1
            elif not db.execute(f"SELECT visited FROM {rank} WHERE node=?", (node,)).fetchone()[0]:
                db.execute(f"UPDATE {rank} SET visited=1 WHERE node=?", (node,))
                db.execute(f"INSERT INTO {work}(node,exiting) VALUES(?,1)", (node,))
                db.executemany(f"INSERT INTO {work}(node,exiting) VALUES(?,0)",
                    ((target,) for (target,) in db.execute(
                        f"SELECT target FROM {links} JOIN {rank} ON node=target WHERE source=? AND visited=0 ORDER BY target DESC", (node,))))
    db.execute(f"UPDATE {rank} SET visited=0")
    for (root,) in db.execute(f"SELECT node FROM {rank} ORDER BY finished DESC"):
        if db.execute(f"SELECT visited FROM {rank} WHERE node=?", (root,)).fetchone()[0]:
            continue
        db.execute(f"DELETE FROM {component}")
        db.execute(f"INSERT INTO {work}(node,exiting) VALUES(?,0)", (root,))
        while True:
            row = db.execute(f"SELECT seq,node FROM {work} ORDER BY seq DESC LIMIT 1").fetchone()
            if row is None:
                break
            seq, node = row
            db.execute(f"DELETE FROM {work} WHERE seq=?", (seq,))
            if db.execute(f"SELECT visited FROM {rank} WHERE node=?", (node,)).fetchone()[0]:
                continue
            db.execute(f"UPDATE {rank} SET visited=1 WHERE node=?", (node,))
            db.execute(f"INSERT INTO {component} VALUES(?)", (node,))
            db.executemany(f"INSERT INTO {work}(node,exiting) VALUES(?,0)",
                           ((source,) for (source,) in db.execute(f"SELECT source FROM {links} WHERE target=? ORDER BY source", (node,))))
        size, first = db.execute(f"SELECT count(*),min(node) FROM {component}").fetchone()
        self_loop = db.execute(f"SELECT 1 FROM {links} WHERE source=? AND target=?", (root, root)).fetchone()
        if size > 1 or self_loop:
            db.executemany(f"INSERT INTO {cycles} VALUES(?,?,?)",
                ((first, number, node) for number, (node,) in enumerate(db.execute(f"SELECT node FROM {component} ORDER BY node"))))
    for table in (work, component, links):
        db.execute(f"DROP TABLE {table}")
    return values


def metric_metadata(db, prefix="sem"):
    if prefix not in {"sem", "q"}:
        raise ValueError("invalid graph metrics namespace")
    return {key: _unpack(payload) for key, payload in db.execute(f"SELECT key,payload FROM {prefix}_graph_meta")}
