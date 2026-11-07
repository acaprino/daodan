"""Validatore di protocollo per tracce di scope resolution (Task 4).

Regole indipendenti dal perimetro: ogni violazione è una stringa leggibile
col nome della regola. Nessun I/O. Le regole marcano la provenienza:
contratti della spec madre o convenzioni della reference policy v1.
"""

QUERY_OPS = ("search", "graph", "outline", "modules")
READ_OPS = ("read",)
ALLOWED_OPS = frozenset(QUERY_OPS + READ_OPS)
CONFIRM_MARKER = "dynamic-link-confirmed:"
BLOCKED_KINDS = ("gap", "invalid", "error")


def _lineage_rules(steps):
    violations = []
    lineages = {}
    for s in steps:
        lin = s.get("lineage")
        if lin:
            lineages.setdefault(lin, []).append(s)
    for lin, seq in lineages.items():
        ops = [s.get("op") for s in seq]
        if "modules" in ops and "search" in ops and ops.index("modules") > ops.index("search"):
            violations.append(f"module-fallback-order: ricerca lessicale prima di modules nel lineage {lin}")
        rewords = 0
        prev_kind = None
        for s in seq:
            if s.get("op") != "search":
                continue
            kind = s.get("result_kind")
            if prev_kind == "empty":
                rewords += 1
                if rewords > 1:
                    violations.append(f"one-rewording-per-lineage: terzo tentativo lessicale nel lineage {lin}")
            elif prev_kind in BLOCKED_KINDS:
                violations.append(f"{prev_kind}-is-not-empty: riformulazione dopo {prev_kind} nel lineage {lin}")
            prev_kind = kind
    return violations


def _terminal_rules(trace, steps):
    violations = []
    if trace.get("outcome"):
        idx = trace.get("terminal_index")
        if steps and idx is None:
            violations.append("missing-terminal-index: outcome presente senza passo terminale dichiarato")
        elif steps and idx != len(steps) - 1:
            violations.append(f"no-steps-after-terminal: terminal_index {idx} non è l'ultimo passo ({len(steps) - 1})")
        reason = trace.get("stop_reason")
        if not isinstance(reason, str) or not reason:
            violations.append("stop-reason-required: outcome presente senza stop_reason")
    return violations


def _budget_rules(trace, steps, policy):
    violations = []
    budget = trace.get("budget", {})
    queries, reads = budget.get("queries"), budget.get("reads")
    if queries > policy["max_queries"] or reads > policy["max_reads"]:
        violations.append(f"budget-cap: queries {queries}/{policy['max_queries']}, letture {reads}/{policy['max_reads']}")
    expected_queries = sum(1 for s in steps if s.get("op") in QUERY_OPS)
    selections = [req.get("path") for s in steps if s.get("op") == "read"
                  for req in s.get("args", {}).get("requests", [])]
    expected_reads = len(set(selections))
    if (queries, reads) != (expected_queries, expected_reads):
        violations.append(f"budget-accounting: dichiarati ({queries},{reads}), "
                          f"ricalcolati dai passi ({expected_queries},{expected_reads})")
    union = set()
    total = 0
    for s in steps:
        nodes = s.get("nodes") or []
        union.update(nodes)
        total += len(nodes)
    if budget.get("unique_nodes") != len(union) or budget.get("suppressed_duplicates") != total - len(union):
        violations.append(f"budget-accounting: nodi dichiarati ({budget.get('unique_nodes')},"
                          f"{budget.get('suppressed_duplicates')}), ricalcolati ({len(union)},{total - len(union)})")
    return violations


def _call_rules(trace, steps):
    violations = []
    for call in trace.get("unresolved_calls") or []:
        if not all(key in call for key in ("caller", "callee", "resolution")):
            violations.append(f"unresolved-calls-shape: voce senza chiavi richieste: {call}")
        elif call.get("resolution") == "resolved":
            violations.append(f"unresolved-call-marked-resolved: {call.get('caller')} -> {call.get('callee')}")
    read_paths = [(i, {req.get("path") for req in s.get("args", {}).get("requests", [])})
                  for i, s in enumerate(steps) if s.get("op") == "read"]
    for i, s in enumerate(steps):
        motivation = s.get("motivation") or ""
        if CONFIRM_MARKER in motivation:
            path = motivation.split(CONFIRM_MARKER, 1)[1].split()[0].strip(",;")
            if not any(ri < i and path in paths for ri, paths in read_paths):
                violations.append(f"dynamic-link-confirmation-needs-read: {path} dichiarato confermato senza lettura precedente")
    for exclusion in trace.get("exclusions") or []:
        path = exclusion.get("path")
        if not exclusion.get("motivation"):
            violations.append(f"exclusion-without-motivation: {path}")
        if not any(path in paths for _, paths in read_paths):
            violations.append(f"exclusion-needs-read: {path} escluso senza una lettura che lo motivi")
    return violations


def _outcome_rules(trace):
    violations = []
    outcome = trace.get("outcome")
    if outcome == "resolved" and trace.get("residual"):
        violations.append("resolved-residual-empty: resolved con residuo non vuoto")
    if outcome == "clarify" and (not trace.get("question")
                                             or len(trace.get("candidates") or []) < 2):
        violations.append("clarification-payload: clarify richiede domanda e almeno due candidati")
    if trace.get("stop_reason") == "budget_exhausted" and not trace.get("residual"):
        violations.append("budget-residual-required: arresto a budget senza residuo concreto")
    return violations


def _op_rules(trace, steps):
    violations = []
    for s in steps:
        if s.get("op") not in ALLOWED_OPS:
            violations.append(f"unknown-op: '{s.get('op')}' non ammesso (la policy v1 esclude embedding e altri tool)")
    list_idx = next((i for i, s in enumerate(steps)
                     if s.get("op") == "modules" and s.get("args", {}).get("list")), None)
    search_idx = next((i for i, s in enumerate(steps) if s.get("op") == "search"), None)
    if list_idx is not None and search_idx is not None and list_idx > search_idx:
        violations.append("modules-index-before-lexical: indice dei moduli dopo la prima ricerca lessicale")
    if trace.get("outcome") == "resolved" and not trace.get("perimeter"):
        violations.append("resolved-empty-perimeter: resolved senza perimetro")
    return violations


def validate_trace(trace, policy):
    """Restituisce la lista di violazioni della traccia; vuota = conforme."""
    steps = trace.get("steps") or []
    return sorted(set(
        _lineage_rules(steps)
        + _terminal_rules(trace, steps)
        + _budget_rules(trace, steps, policy)
        + _call_rules(trace, steps)
        + _outcome_rules(trace)
        + _op_rules(trace, steps)))
