"""Raw answers of one inference engine on a snapshot that already had its engine pass.

Runs inside the engine's own stage environment (the one `resolve_edges.stage_command` builds), imports
the product scripts and asks the engine again, on samples, what the pass asked and what it does not ask,
keeping every answer as the engine gives it: P1 to P5 and P7 of the README.

    python probe.py SCRIPTS_DIR MANIFEST ENGINE OUT.json
"""
from __future__ import annotations

import collections
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

SCRIPTS, MANIFEST, ENGINE, OUT = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
sys.path.insert(0, str(SCRIPTS))

import resolve_edges as rx  # noqa: E402
from snapshot_store import _unpack, open_snapshot  # noqa: E402

PER_VERDICT, READS, LEXICAL, EXAMPLES = 20, 60, 30, 4
CALLABLE = ("function", "method", "class")


def every(rows: list, wanted: int) -> list:
    """Up to `wanted` rows at a fixed stride over the id order."""
    rows = sorted(rows, key=lambda r: r[0])
    if len(rows) <= wanted:
        return rows
    step = len(rows) / wanted
    return [rows[int(i * step)] for i in range(wanted)]


def package_of(path: Path) -> str:
    """Which library an external file belongs to, from the conventions of each ecosystem."""
    parts = path.as_posix().split("/")
    for marker, width in (("node_modules", 1), ("site-packages", 1), ("dist-packages", 1)):
        if marker in parts:
            i = len(parts) - 1 - parts[::-1].index(marker)
            name = parts[i + 1] if i + 1 < len(parts) else "?"
            if name.startswith("@") and i + 2 < len(parts):
                name = f"{name}/{parts[i + 2]}"
            return f"{marker}:{name.split('-')[0] if marker != 'node_modules' else name}"
    text = path.as_posix()
    if "/rustlib/" in text:
        return "rust:std"
    if "/registry/src/" in text:
        return "crate:" + text.split("/registry/src/")[1].split("/")[1]
    if "/pkg/mod/" in text:
        return "go:" + text.split("/pkg/mod/")[1].split("@")[0]
    if "/go/src/" in text or "/goroot" in text.lower():
        return "go:std"
    if "typeshed" in text or "/lib/python" in text:
        return "python:" + ("typeshed" if "typeshed" in text else "stdlib")
    if text.endswith(".jar") or "/maven" in text or "/coursier" in text:
        return "jvm:" + "/".join(parts[-3:-1])
    return "external:" + "/".join(parts[-3:-1])


class Context:
    def __init__(self, store, root: Path, inventory: set[str]):
        self.connection, self.root, self.inventory = store.connection, root, inventory
        self.declarations = collections.defaultdict(list)
        for ident, file, name, kind, l0, c0, blob in self.connection.execute(
                "SELECT id, file, name, kind, l0, c0, payload FROM sem_declarations"):
            payload = _unpack(blob)
            lines = {l0}
            span = payload.get("name_span")
            if isinstance(span, (list, tuple)) and span:
                lines.add(span[0])
            for line in lines:
                self.declarations[(file, line)].append(
                    {"id": ident, "name": name, "kind": kind, "contract": bool(payload.get("contract"))})

    def where(self, target: str | None, line: int | None) -> dict:
        """Where one raw destination falls; `line` is 1-based."""
        if target is None:
            return {"place": "no-location"}
        if "://" in target and not target.startswith("file:"):
            return {"place": "not-a-file", "scheme": target.split(":", 1)[0]}
        if target.startswith("file:"):
            from urllib.parse import unquote, urlparse
            from urllib.request import url2pathname
            target = url2pathname(unquote(urlparse(target).path))
        path = Path(target).resolve()
        try:
            rel = path.relative_to(self.root).as_posix()
        except ValueError:
            return {"place": "external", "package": package_of(path)}
        if rel not in self.inventory:
            return {"place": "project-outside-snapshot", "dir": rel.split("/")[0]}
        found = self.declarations.get((rel, line), [])
        callables = [d for d in found if d["kind"] in CALLABLE]
        if callables:
            d = callables[0]
            return {"place": "project-contract" if d["contract"] else "project-callable", "kind": d["kind"],
                    "id": d["id"], "in_view": d["kind"] in ("function", "class")}
        if found:
            return {"place": "project-value", "kind": found[0]["kind"], "id": found[0]["id"]}
        return {"place": "project-no-declaration", "file": rel}


def lsp_raw(engine, path: Path, line: int, column: int, method: str) -> list[tuple[str, int]]:
    """One LSP request at a UTF-8 byte column, every destination as the server gives it."""
    uri, lines = engine._document(path)
    units = engine._to_server(lines[line - 1], column) if 1 <= line <= len(lines) else None
    if units is None:
        raise ValueError("no character at that column")
    send = getattr(engine.handler.send, method)
    response = engine._run(send({"textDocument": {"uri": uri}, "position": {"line": line - 1, "character": units}}),
                           rx.LSP_REQUEST_TIMEOUT)
    if isinstance(response, dict):
        response = [response]
    out = []
    for item in response or ():
        target = item.get("targetUri") or item.get("uri")
        area = item.get("targetSelectionRange") or item.get("targetRange") or item.get("range")
        if not target or not area:
            continue
        if target.startswith("file:"):
            from urllib.parse import unquote, urlparse
            from urllib.request import url2pathname
            resolved = Path(url2pathname(unquote(urlparse(target).path))).resolve()
            resolved = engine.virtual.get(resolved, resolved)
            if engine.workspace_root() != engine.project_root and resolved.is_relative_to(engine.workspace_root()):
                resolved = engine.project_root / resolved.relative_to(engine.workspace_root())
            target = str(resolved)
        out.append((target, area["start"]["line"] + 1))
    return out


def jedi_raw(engine, path: Path, line: int, column: int, method: str) -> list[dict]:
    import jedi
    text = engine.lines.get(path, line)
    character = rx.byte_to_char(text, column) if text is not None else None
    if character is None:
        raise ValueError("no character at that column")
    project, environment, _mode = engine.environment_for(path)
    script = jedi.Script(path=str(path), project=project, environment=environment)
    found = script.infer(line=line, column=character) if method == "infer" else \
        script.goto(line=line, column=character, follow_imports=True)
    return [{"target": str(d.module_path) if d.module_path else None, "line": d.line, "type": d.type,
             "full_name": d.full_name} for d in found]


def main() -> int:
    started = time.time()
    out: dict = {"engine": ENGINE}
    with open_snapshot(MANIFEST) as store:
        connection = store.connection
        spec = next(s for s in rx.ENGINES if s.name == ENGINE)
        present = set(rx.snapshot_languages(connection))
        languages = [lang for lang in spec.languages if lang in present]
        out["languages"] = languages
        if not languages:
            OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
            return 0
        store_root, source_paths, _ = rx.verify_sources(store, languages)
        project_root = (Path(store["root"]) / store["target"]).resolve()
        inventory = rx.inventory_files(connection)
        ctx = Context(store, store_root, inventory)
        callee_names = rx.project_callee_names(connection)
        marks = ",".join("?" for _ in languages)
        refs = connection.execute(
            f"SELECT r.id, r.file, r.payload, r.l0, r.c0, r.l1, r.c1, c.language, r.kind, r.resolution, r.target_id "
            f"FROM sem_references r JOIN sem_coverage c ON c.file=r.file WHERE c.language IN ({marks})",
            tuple(languages)).fetchall()
        callable_names = {row[0] for row in connection.execute(
            "SELECT DISTINCT name FROM sem_declarations WHERE kind IN ('function','method','class')")}

        # P1, P2: what the static step holds, what the pass asks.
        kinds = collections.Counter()
        classes = collections.Counter()
        reads_naming = []
        for row in refs:
            payload = _unpack(row[2])
            kinds[f"{row[7]} {row[8]} {row[9]}"] += 1
            if row[8] == "call" and row[9] == "unresolved":
                classes[f"{row[7]} {rx.classify_reference(payload, callee_names)}"] += 1
            if row[8] != "call" and (payload.get("parts") or [""])[-1] in callable_names:
                reads_naming.append(row)
        out["references"] = dict(sorted(kinds.items()))
        out["unresolved_calls_by_class"] = dict(sorted(classes.items()))
        out["reads_naming_project_callables"] = dict(collections.Counter(
            f"{r[7]} {r[8]} {Path(r[1]).suffix}" for r in reads_naming))

        # P2, P5: what the pass answered and what it stored.
        answers = {}
        cache = rx.default_answers_path(MANIFEST)
        if cache.is_file():
            db = sqlite3.connect(cache)
            for reference_id, verdict, target_id in db.execute(
                    "SELECT reference_id, verdict, target_id FROM answers WHERE engine=?", (ENGINE,)):
                answers[reference_id] = (verdict, target_id)
            db.close()
        out["answers_cached"] = len(answers)
        out["answer_verdicts"] = dict(collections.Counter(v for v, _ in answers.values()))
        edges, binding, reason = rx.read_edge_store(rx.default_edge_store(MANIFEST), store)
        out["edge_store"] = {"reason": reason, "entries": {k: {f: v.get(f) for f in (
            "engine", "state", "population", "selected", "asked", "confirmed", "candidates", "verdicts",
            "excluded_classes", "no_edges_reason")} for k, v in ((binding or {}).get("languages") or {}).items()
            if k in languages}}
        kind_of = {row[0]: (row[1], bool(_unpack(row[2]).get("contract"))) for row in connection.execute(
            "SELECT id, kind, payload FROM sem_declarations")}
        stored = collections.Counter()
        for edge in edges or ():
            if edge.get("language") not in languages:
                continue
            kind, contract = kind_of.get(edge.get("target_id"), (None, False))
            stored[f"{edge['confidence']} {edge['verdict']} target={kind}{' contract' if contract else ''}"] += 1
        out["stored_edges"] = dict(sorted(stored.items()))

        # P3, P4, P7: ask again and keep the raw answers.
        environments = []
        if ENGINE == "jedi":
            names = [row[0] for row in connection.execute("SELECT file FROM sem_coverage")]
            prepared = rx.python_environment(Path(store["root"]).resolve(), names)
            environments = [prepared] if prepared else rx.default_environments(project_root)
        engine = rx.build_engine(ENGINE, project_root, environments)
        if hasattr(engine, "import_roots"):
            engine.import_roots = [store_root / rel for rel in rx.runtime_import_roots(connection)]
        if hasattr(engine, "sources"):
            wanted = set(engine.source_languages)
            engine.sources = sorted(source_paths[rel] for rel, language in connection.execute(
                "SELECT file, language FROM sem_coverage") if language in wanted and rel in source_paths)
        ready, why = engine.probe()
        out["probe"] = {"ready": ready, "reason": why}
        if not ready:
            OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
            return 0
        lsp = isinstance(engine, rx.LspEngine)
        methods = ("definition", "implementation", "type_definition") if lsp else \
            ("infer", "goto") if ENGINE == "jedi" else ("definitions",)

        tables: dict = {}

        def table_for(name):
            return rx.symbol_table(connection, name, (store_root / name).read_text(encoding="utf-8"))

        declared_at = {(file, l0, c0): kind for file, kind, l0, c0 in connection.execute(
            "SELECT file, kind, l0, c0 FROM sem_declarations WHERE kind IN ('binding','parameter','property')")}

        def shape(rel: str, line: int, column: int) -> str:
            """What a value answer holds: the measure behind problem 5 of the README."""
            kind = declared_at.get((rel, line, column))
            if kind != "binding":
                return kind or "unknown"
            try:
                text = (store_root / rel).read_text(encoding="utf-8").split("\n")[line - 1].encode("utf-8")
            except (OSError, IndexError):
                return "binding"
            head, rest = text[:column].decode("utf-8", "replace"), text[column:].decode("utf-8", "replace")
            if re.search(r"[{\[][^=]*$", head):
                return "binding destructured"
            init = re.match(r"\s*[\w$]*\s*(?::[^=]*)?=\s*(.*)", rest)
            value = init.group(1) if init else ""
            if re.match(r"(async\s+)?(function\b|\(|[A-Za-z_$][\w$]*\s*=>)", value):
                return "binding function in place"
            called = re.match(r"(await\s+)?([A-Za-z_$][\w$.]*)\s*\(", value)
            if called:
                written = "=>" in value or re.search(r"\bfunction\b", value)
                name = called.group(2).split(".")[-1]
                return f"binding call {'with' if written else 'without'} a function in place: {name}"
            return "binding other value"

        def exact(location) -> dict:
            """One location graded at its exact position, as the pass grades it."""
            verdict, target = rx.grade(location, inventory, tables, store_root, table_for)
            entry = {"verdict": verdict}
            if target:
                kind, is_contract = kind_of.get(target["id"], (None, False))
                entry["kind"] = f"{kind}{' contract' if is_contract else ''}"
            elif verdict == "binding":
                rel = Path(location.module_path).resolve().relative_to(store_root).as_posix()
                entry["kind"] = shape(rel, location.line, location.column)
            return entry

        def tally_exact(items: list[dict]) -> dict:
            summary = {}
            for method in ("exact_definition", "exact_implementation"):
                counts = collections.Counter()
                for item in items:
                    if method in item:
                        seen = sorted({e["verdict"] + (f" {e['kind']}" if e.get("kind") else "") for e in item[method]})
                        counts[" + ".join(seen) or "nothing"] += 1
                if counts:
                    summary[method] = dict(counts.most_common())
            return summary

        def ask(row, only=None):
            rid, rel, blob, l0, c0, l1, c1 = row[:7]
            payload = _unpack(blob)
            parts = payload.get("parts") or []
            lines = source_paths[rel].read_text(encoding="utf-8").split("\n")
            if not parts or not l1 or not 1 <= l1 <= len(lines):
                return {"skipped": "no position"}
            column = rx.callee_column(lines[l1 - 1], [l0, c0, l1, c1], parts[-1])
            if column is None:
                return {"skipped": "position unverified"}
            result = {"site": f"{rel}:{l1}", "name": ".".join(str(p) for p in parts)}
            for method in only or methods:
                try:
                    if lsp:
                        raw = [ctx.where(t, line) for t, line in lsp_raw(engine, source_paths[rel], l1, column, method)]
                    elif ENGINE == "jedi":
                        raw = []
                        for d in jedi_raw(engine, source_paths[rel], l1, column, method):
                            where = ctx.where(d["target"], d["line"])
                            if where["place"] in ("external", "no-location"):
                                where["full_name"] = d["full_name"]
                            where["type"] = d["type"]
                            raw.append(where)
                    else:
                        raw = [ctx.where(str(loc.module_path) if loc.module_path else None, loc.line)
                               for loc in engine.definitions(source_paths[rel], l1, column)]
                except Exception as error:  # an unsupported request is a fact of the audit
                    raw = [{"place": "error", "error": f"{type(error).__name__}: {str(error)[:120]}"}]
                result[method] = raw
            for method, call in (("exact_definition", "definitions"), ("exact_implementation", "implementations")):
                if not hasattr(engine, call):
                    continue
                try:
                    result[method] = [exact(location) for location in getattr(engine, call)(source_paths[rel], l1, column)]
                except Exception as error:  # an unsupported request is a fact of the audit
                    result[method] = [{"verdict": "error", "error": f"{type(error).__name__}: {str(error)[:120]}"}]
            return result

        def tally(items: list[dict]) -> dict:
            summary = {}
            for method in methods:
                places = collections.Counter()
                for item in items:
                    if method not in item:
                        continue
                    seen = sorted({p["place"] + (f" {p['kind']}" if "kind" in p else "") for p in item[method]})
                    places[" + ".join(seen) or "nothing"] += 1
                if places:
                    summary[method] = dict(places.most_common())
            return summary

        by_id = {row[0]: row for row in refs}
        samples = {}
        verdicts = collections.defaultdict(list)
        for rid, (verdict, _t) in answers.items():
            if rid in by_id:
                verdicts[f"{by_id[rid][7]} {verdict}"].append(by_id[rid])
        for key, rows in sorted(verdicts.items()):
            items = [ask(row) for row in every(rows, PER_VERDICT)]
            asked = [i for i in items if "skipped" not in i]
            samples[key] = {"population": len(rows), "sampled": len(asked), "places": tally(asked),
                            "exact": tally_exact(asked), "examples": asked[:EXAMPLES]}
        out["asked_again_by_verdict"] = samples

        first = methods[:2] if lsp else methods[:1]
        reads = [ask(row, first) for row in every(reads_naming, READS)]
        reads = [r for r in reads if "skipped" not in r]
        out["reads_asked"] = {"population": len(reads_naming), "sampled": len(reads), "places": tally(reads),
                              "exact": tally_exact(reads), "examples": reads[:EXAMPLES]}

        lexical = [row for row in refs if row[8] == "call" and row[9] == "resolved" and row[10]]
        agreement = collections.Counter()
        disagreements = []
        for row in every(lexical, LEXICAL):
            item = ask(row, methods[:1])
            if "skipped" in item:
                continue
            ids = {p.get("id") for p in item[methods[0]]}
            if row[10] in ids:
                agreement["same declaration"] += 1
            elif not item[methods[0]]:
                agreement["engine has no answer"] += 1
            else:
                agreement["engine says another place"] += 1
                if len(disagreements) < EXAMPLES:
                    disagreements.append({**item, "lexical": row[10]})
        out["lexical_agreement"] = {"population": len(lexical), "counts": dict(agreement),
                                    "examples": disagreements}
        closer = getattr(engine, "close", None)
        if closer:
            closer()
    out["seconds"] = round(time.time() - started, 1)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
