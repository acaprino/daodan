"""resolver.py — prima versione eseguibile della Phase 0 (search+retrieval).

Politica di riferimento v1 congelata in CASES.md: i giudizi che la spec madre
lascia al modello sono implementati con la regola più semplice coerente col
testo; le ambiguità della spec vanno annotate in results/findings.md, non
risolte in silenzio. Nessun embedding (disabilitati), nessuna rete.
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "plugins" / "codebase-map" / "skills" / "map" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from mcp_service import MapService  # noqa: E402

# Reference policy del resolver: approssimazione deterministica dei giudizi che la spec
# affida al modello. Misura il protocollo, non il perimetro: dove serve giudizio fallisce.
POLICY = {
    "version": 3, "max_queries": 6, "max_reads": 10, "top_files": 5, "exhaustive_limit": 100,
    "exhaustive_words": ["ogni", "tutti", "ciascuno", "ognuno", "every", "all"],
    "behavior_words": ["catena", "come arriva", "come viene", "quale funzione", "percorso", "flusso", "dispatch", "chain", "flow"],
    "required_dest_words": ["quale funzione", "chi esegue", "chi invia", "destinazione", "davvero", "which function", "actually"],
    "impact_words": ["chi usa", "impatto", "importa", "chi chiama", "who uses", "impact"],
    "reword_lexicon": {"sconto": "discount", "discount": "sconto", "rimborsi": "refund", "refund": "rimborsi",
                       "notifica": "notification", "canale": "channel", "iva": "vat", "vat": "iva"},
}
PREFIX = "benchmarks/scope-resolution/app/"
PATH_SUFFIXES = (".py", ".toml", ".md", ".json", ".cfg", ".txt")
QUERY_OPS = ("search", "graph", "outline", "modules")


def ensure_run(benchmark_dir, run_id="bench-1"):
    """Crea un run reale bindato su app/; se esiste già lo ricostruisce (la fixture può cambiare tra task)."""
    benchmark_dir = Path(benchmark_dir)
    service = MapService(project_root=benchmark_dir / "app")
    run_dir = service.root / "runs" / run_id
    if run_dir.exists():
        shutil.rmtree(run_dir, ignore_errors=True)
    service.create_run(target=".", run_id=run_id)
    return service, run_id


class _Trace:
    def __init__(self, policy):
        self.policy = policy
        self.steps = []
        self.queries = 0
        self.node_occurrences = []
        self.read_selections = []

    def can_query(self):
        return self.queries < self.policy["max_queries"]

    def can_read(self, path):
        return path in set(self.read_selections) or len(set(self.read_selections)) < self.policy["max_reads"]

    def add(self, op, args, lineage, result_kind, motivation, nodes, truncated=False):
        step = {"op": op, "args": args, "lineage": lineage, "result_kind": result_kind,
                "motivation": motivation, "nodes": list(nodes)}
        if truncated:
            step["truncated"] = True
        self.steps.append(step)
        self.node_occurrences.extend(nodes)
        if op in QUERY_OPS:
            self.queries += 1
        if op == "read":
            self.read_selections.extend(req["path"] for req in args.get("requests", []))

    def budget(self):
        unique = set(self.node_occurrences)
        return {"queries": self.queries, "reads": len(set(self.read_selections)),
                "unique_nodes": len(unique),
                "suppressed_duplicates": len(self.node_occurrences) - len(unique)}


def _is_path(anchor):
    return "/" in anchor or anchor.endswith(PATH_SUFFIXES)


def _finish(t, state):
    perimeter = sorted(set(state["perimeter"]) | set(state["module_files"]))
    residual = list(dict.fromkeys(state["residual"]))
    return {"steps": t.steps, "budget": t.budget(), "outcome": state["outcome"],
            "stop_reason": state["stop_reason"], "perimeter": perimeter,
            "unresolved_calls": state["unresolved"], "candidates": state["candidates"],
            "residual": residual, "exclusions": state["exclusions"],
            "question": state["question"], "terminal_index": len(t.steps) - 1}


def _stop(state, outcome, reason):
    state["outcome"] = outcome
    state["stop_reason"] = reason


def _module_index(service, run_id, t, state):
    """Elenco moduli senza query (1 query); None se il grafo moduli non è fresh."""
    if not t.can_query():
        _stop(state, "partial", "budget_exhausted")
        return []
    result = service.modules(run_id)
    fresh = result.get("graph_state") == "fresh"
    modules = result.get("modules") or []
    nodes = [PREFIX + p if not p.startswith(PREFIX) else p
             for m in modules for p in m.get("paths", []) if p != "."]
    t.add("modules", {"list": True}, None, "hits" if fresh else "gap",
          "indice dei moduli prima della ricerca lessicale (fallback moduli)", nodes)
    if not fresh:
        _stop(state, "partial", "prerequisite_gap")
        return []
    return [(m.get("name", ""), [_full(p) for p in m.get("paths", []) if p != "."], m.get("id", ""))
            for m in modules]


def _full(path):
    """I path dei moduli sono project-relative nello spike e repo-relative nei run dentro il repo."""
    return path if path.startswith(PREFIX) else PREFIX + path


def _module_of(path, index):
    best, best_id = 0, None
    for name, paths, mid in index:
        for p in paths:
            if path.startswith(p) and len(p) > best:
                best, best_id = len(p), mid or name
    return best_id


def _matches_module(anchor, index):
    norm = anchor.lower().replace("-", "_")
    for name, paths, _ in index:
        if name.lower().replace("-", "_") == norm:
            return True
        if any(p.rstrip("/").split("/")[-1].lower() == norm for p in paths):
            return True
    return False


def _search(service, run_id, t, query, lineage, limit, state):
    """Una ricerca lessicale; restituisce ('gap'|'empty'|'hits', files, envelope)."""
    try:
        envelope = service.search(run_id, query, limit=limit)
    except ValueError as exc:
        t.add("search", {"query": query, "limit": limit}, lineage, "error", f"richiesta non valida: {exc}", [])
        return "error", [], {}
    gaps = envelope.get("gaps") or []
    results = envelope.get("results") or []
    files = list(dict.fromkeys(r["path"] for r in results if r.get("path")))
    nodes = [r.get("entity_id") or r.get("path") for r in results]
    if any("retrieval_" in g for g in gaps):
        t.add("search", {"query": query, "limit": limit}, lineage, "gap",
              "indice mancante/stale: lacuna del prerequisito, nessuna riformulazione", nodes)
        _stop(state, "partial", "prerequisite_gap")
        return "gap", files, envelope
    kind = "hits" if files else "empty"
    t.add("search", {"query": query, "limit": limit}, lineage, kind,
          f"anchor lessicale '{query}'", nodes)
    return kind, files, envelope


def _confirm_read(service, run_id, t, path, motivation):
    # Richiesta nuda: read_packet restituisce i blocchi di contesto (header,
    # import, costanti) senza ranges — sicuro anche su file grandi.
    result = service.read(run_id, [{"path": path}])
    t.add("read", {"requests": [{"path": path}]}, None, "hits", motivation, [path])
    return result


def _outline_path(service, run_id, t, full, motivation):
    result = service.outline(run_id, path=full, limit=100)
    items = result.get("items") or []
    t.add("outline", {"path": full, "limit": 100}, None,
          "hits" if items else "empty", motivation, [full],
          truncated=bool(result.get("truncated")))
    return bool(items)


def _reword(anchor, policy):
    key = anchor.lower().strip()
    if key in policy["reword_lexicon"]:
        return policy["reword_lexicon"][key]
    words = key.split()
    return words[0] if len(words) > 1 else None


def resolve(service, run_id, case, policy=POLICY):
    t = _Trace(policy)
    intent = case["intent"]
    lower = intent.lower()
    exhaustive = any(w in lower for w in policy["exhaustive_words"])
    behavior = any(w in lower for w in policy["behavior_words"])
    required_dest = any(w in lower for w in policy["required_dest_words"])
    impact = any(w in lower for w in policy["impact_words"])
    anchors = list(case["anchors"])
    path_anchors = [a for a in anchors if _is_path(a)]
    word_anchors = [a for a in anchors if not _is_path(a)]
    state = {"outcome": None, "stop_reason": None, "question": None, "candidates": None,
             "perimeter": [], "module_files": [], "unresolved": [], "exclusions": [], "residual": []}
    pending = []

    if not intent.strip() or not anchors:
        # richiesta invalida: transizione distinta da ricerca vuota o errore tool
        t.add("search", {"query": intent}, None, "invalid",
              "richiesta invalida: intent o anchor vuoti", [])
        _stop(state, "partial", "invalid_request")
        return _finish(t, state)

    def queue(path):
        if path not in pending and path not in state["perimeter"] and path not in state["module_files"]:
            pending.append(path)

    index = []
    if word_anchors:
        index = _module_index(service, run_id, t, state)
        if state["outcome"]:
            return _finish(t, state)

    module_anchors, lexical_anchors = [], []
    for a in word_anchors:
        (module_anchors if _matches_module(a, index) else lexical_anchors).append(a)

    for a in path_anchors:
        full = a if a.startswith(PREFIX) else PREFIX + a
        if not t.can_query():
            state["residual"].append(full)
            continue
        if _outline_path(service, run_id, t, full, f"anchor percorso esplicito '{a}': verifica esistenza"):
            queue(full)
        else:
            state["residual"].append(full)

    for a in module_anchors:
        if state["outcome"]:
            break
        if not t.can_query():
            state["residual"].append(f"anchor:{a}")
            break
        result = service.modules(run_id, query=a)
        status = result.get("status")
        candidates = result.get("candidates") or []
        nodes = [f for c in candidates for f in c.get("files", [])]
        t.add("modules", {"query": a}, f"anchor:{a}", "hits" if nodes else "empty",
              f"anchor modulo '{a}': status {status}", nodes)
        if status == "resolved" and candidates:
            state["module_files"].extend(candidates[0].get("files", []))
        elif status == "clarify":
            state["candidates"] = [{"target": (c.get("files") or c.get("paths") or [c.get("name")])[0],
                                    "motivation": f"modulo candidato '{c.get('name')}'"} for c in candidates]
            state["question"] = f"Più moduli corrispondono a '{a}': {result.get('reason', '')}. Quale rivedere?"
            _stop(state, "clarify", "ambiguous_domain_term")
        elif status == "partial":
            for f in nodes:
                queue(f)
        else:
            lexical_anchors.append(a)

    ambiguity = None
    all_plain = bool(lexical_anchors) and all(a.isalpha() and a.islower() for a in lexical_anchors)
    for a in lexical_anchors:
        if state["outcome"]:
            break
        lineage = f"anchor:{a}"
        limit = policy["exhaustive_limit"] if exhaustive else 20
        if not t.can_query():
            state["residual"].append(f"anchor:{a}")
            continue
        kind, files, envelope = _search(service, run_id, t, a, lineage, limit, state)
        if kind == "gap":
            break
        if kind == "error":
            state["residual"].append(f"anchor:{a}")
            continue
        if kind == "empty":
            alt = _reword(a, policy)
            if alt and t.can_query():
                kind, files, envelope = _search(service, run_id, t, alt, lineage, limit, state)
                if kind == "gap":
                    break
            if kind == "empty":
                state["residual"].append(f"anchor:{a}")
                continue
        selected = files if exhaustive else files[:policy["top_files"]]
        for f in selected:
            queue(f)
        if all_plain and ambiguity is None:
            by_module = {}
            for f in selected:
                mid = _module_of(f, index)
                if mid:
                    by_module.setdefault(mid, f)
            if len(by_module) >= 2:
                ambiguity = (a, by_module, envelope)

    if ambiguity is not None and not state["outcome"]:
        anchor, by_module, envelope = ambiguity
        records = {r.get("path"): r for r in (envelope.get("results") or []) if r.get("path")}
        state["candidates"] = []
        for mid, f in sorted(by_module.items()):
            rec = records.get(f, {})
            state["candidates"].append({
                "target": f,
                "motivation": f"'{anchor}' nel modulo {mid}: {rec.get('entity_id') or f}"})
        names = ", ".join(sorted(by_module))
        state["question"] = (f"'{anchor}' corrisponde a target materialmente diversi nei moduli {names}. "
                             "Quale rivedere?")
        _stop(state, "clarify", "ambiguous_domain_term")
        return _finish(t, state)

    budget_stop = False
    for f in list(pending):
        if state["outcome"]:
            break
        if t.can_read(f):
            _confirm_read(service, run_id, t, f, "lettura di conferma dell'appartenenza al perimetro")
            state["perimeter"].append(f)
        else:
            state["residual"].append(f)
            budget_stop = True

    if behavior and not state["outcome"] and state["perimeter"] and t.can_query():
        seed = sorted(set(state["perimeter"]))
        packet = service.graph(run_id, paths=seed, hops=1)
        touched = sorted({(c.get("caller") or c.get("file") or "").split("::")[0] for c in packet.get("calls", [])}
                         | {(c.get("target_id") or "").split("::")[0] for c in packet.get("calls", [])}
                         | {r.get("source") or "" for r in packet.get("imports", [])}
                         | {r.get("target") or "" for r in packet.get("imports", [])})
        t.add("graph", {"paths": seed, "hops": 1}, None, "hits",
              "onda comportamentale: callee/caller/importer a un hop dai file confermati",
              [x for x in touched if x], truncated=bool(packet.get("truncated")))
        seed_set = set(seed)
        wave_new, importers_only = [], []
        for c in packet.get("calls", []):
            caller_file = (c.get("caller") or c.get("file") or "").split("::")[0]
            if c.get("resolution") != "resolved":
                state["unresolved"].append({"caller": c.get("caller") or c.get("file") or "?",
                                            "callee": ".".join(c.get("parts") or []) or c.get("id", "?"),
                                            "resolution": c.get("resolution", "unresolved")})
                continue
            target_file = (c.get("target_id") or "").split("::")[0]
            if not target_file.startswith(PREFIX):
                continue
            if caller_file in seed_set and target_file not in seed_set:
                wave_new.append(target_file)
            if target_file in seed_set and caller_file not in seed_set and caller_file.startswith(PREFIX):
                wave_new.append(caller_file)
        for row in packet.get("imports", []):
            src, tgt = row.get("source"), row.get("target")
            if tgt in seed_set and src not in seed_set and src not in wave_new and (src or "").startswith(PREFIX):
                importers_only.append(src)
        excluded_paths = {e["path"] for e in state["exclusions"]}
        for f in dict.fromkeys(wave_new):
            if f in state["perimeter"] or f in excluded_paths:
                continue
            if t.can_read(f):
                _confirm_read(service, run_id, t, f, "calleo/caller confermato dal grafo: lettura di appartenenza")
                state["perimeter"].append(f)
            else:
                state["residual"].append(f)
                budget_stop = True
        for f in dict.fromkeys(importers_only):
            if impact:
                if t.can_read(f):
                    _confirm_read(service, run_id, t, f, "intent di impatto: importer incluso previa lettura")
                    state["perimeter"].append(f)
            elif t.can_read(f):
                _confirm_read(service, run_id, t, f, "verifica pertinenza importer")
                state["exclusions"].append({"path": f,
                                            "motivation": (f"importer accessorio di {sorted(seed_set)}: la lettura mostra "
                                                           "uso non comportamentale (formattazione/presentazione) fuori "
                                                           "dal percorso richiesto dall'intent")})
            else:
                state["residual"].append(f)
                budget_stop = True

    if state["outcome"]:
        return _finish(t, state)
    pending_residual = [r for r in state["residual"] if not r.startswith("anchor:")]
    anchor_residual = [r for r in state["residual"] if r.startswith("anchor:")]
    if required_dest and any(u["caller"].split("::")[0] in set(state["perimeter"]) for u in state["unresolved"]):
        _stop(state, "partial", "unresolved_required_link")
    elif budget_stop or pending_residual:
        _stop(state, "partial", "budget_exhausted")
    elif anchor_residual and not state["perimeter"] and not state["module_files"]:
        # nessun ancoraggio risolto: le lacune impediscono di delimitare il comportamento
        _stop(state, "partial", "unresolved_required_link")
    else:
        # anchor_residual con perimetro non vuoto: nota non bloccante (spec gap: la spec
        # non definisce quando un anchor irrisolto non necessario blocchi la risoluzione)
        _stop(state, "resolved", "delimited_by_evidence")
    return _finish(t, state)
