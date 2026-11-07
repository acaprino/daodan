"""Task 4: unit test del validatore di protocollo su tracce sintetiche."""
from tracecheck import validate_trace

POLICY = {"max_queries": 6, "max_reads": 10, "version": 1}


def step(op, lineage=None, kind="hits", motivation="m", nodes=None, args=None):
    return {"op": op, "args": args if args is not None else {}, "lineage": lineage,
            "result_kind": kind, "motivation": motivation, "nodes": nodes or []}


def make_trace(**over):
    trace = {
        "steps": [
            step("modules", "anchor-shipping", motivation="module anchor before lexical",
                 nodes=["app/packages/shipping/rates.py"], args={"query": "shipping"}),
            step("search", "anchor-sconto", motivation="domain term",
                 nodes=["a.py", "b.py"], args={"query": "sconto"}),
            step("read", None, motivation="confirm membership", nodes=["a.py"],
                 args={"requests": [{"path": "a.py"}]}),
        ],
        "budget": {"queries": 2, "reads": 1, "unique_nodes": 3, "suppressed_duplicates": 1},
        "outcome": "resolved", "stop_reason": "delimited_by_evidence",
        "perimeter": ["a.py"], "unresolved_calls": [], "candidates": None,
        "residual": [], "exclusions": [], "question": None, "terminal_index": 2,
    }
    trace.update(over)
    return trace


def test_valid_trace_passes():
    assert validate_trace(make_trace(), POLICY) == []


def test_module_fallback_before_lexical():
    t = make_trace()
    t["steps"][0]["lineage"] = "anchor-x"
    t["steps"][1]["lineage"] = "anchor-x"
    t["steps"] = [t["steps"][1], t["steps"][0], t["steps"][2]]
    assert any("module-fallback-order" in x for x in validate_trace(t, POLICY))


def test_one_rewording_per_lineage():
    t = make_trace(steps=[
        step("search", "L", kind="empty", args={"query": "q1"}),
        step("search", "L", kind="empty", args={"query": "q2"}),
        step("search", "L", kind="empty", args={"query": "q3"}),
    ], terminal_index=2)
    assert any("one-rewording-per-lineage" in x for x in validate_trace(t, POLICY))


def test_new_lineage_search_allowed():
    t = make_trace(steps=[
        step("search", "L1", kind="empty", args={"query": "q1"}),
        step("search", "L1", kind="hits", nodes=["x.py"], args={"query": "q1 sinonimo"}),
        step("search", "L2", kind="empty", args={"query": "q2"}),
        step("search", "L2", kind="hits", nodes=["y.py"], args={"query": "q2 sinonimo"}),
    ], terminal_index=3)
    assert not any("one-rewording-per-lineage" in x for x in validate_trace(t, POLICY))


def test_no_steps_after_terminal():
    t = make_trace(terminal_index=1)
    assert any("no-steps-after-terminal" in x for x in validate_trace(t, POLICY))


def test_stop_reason_required():
    t = make_trace(stop_reason=None)
    assert any("stop-reason-required" in x for x in validate_trace(t, POLICY))


def test_budget_caps_enforced():
    t = make_trace()
    t["budget"] = dict(t["budget"], queries=7)
    assert any("budget-cap" in x for x in validate_trace(t, POLICY))


def test_duplicate_suppression_recorded():
    reads = [
        step("read", None, motivation="confirm a", nodes=["a.py"],
             args={"requests": [{"path": "a.py"}]}),
        step("read", None, motivation="re-check a", nodes=["a.py"],
             args={"requests": [{"path": "a.py"}]}),
    ]
    t = make_trace(steps=reads, terminal_index=1,
                   budget={"queries": 0, "reads": 2, "unique_nodes": 1, "suppressed_duplicates": 1})
    assert any("budget-accounting" in x for x in validate_trace(t, POLICY))
    t["budget"] = {"queries": 0, "reads": 1, "unique_nodes": 1, "suppressed_duplicates": 1}
    assert not any("budget-accounting" in x for x in validate_trace(t, POLICY))


def test_invalid_request_distinct_from_empty():
    t = make_trace(steps=[
        step("search", "L", kind="invalid", args={"query": ""}),
        step("search", "L", kind="hits", args={"query": "q"}),
    ], terminal_index=1)
    assert any("invalid-is-not-empty" in x for x in validate_trace(t, POLICY))


def test_gap_blocks_rewording():
    t = make_trace(steps=[
        step("search", "L", kind="gap", args={"query": "q"}),
        step("search", "L", kind="hits", args={"query": "q sinonimo"}),
    ], terminal_index=1)
    assert any("gap-is-not-empty" in x for x in validate_trace(t, POLICY))


def test_unresolved_call_not_an_edge():
    bad = make_trace(unresolved_calls=[{"caller": "c.py::f", "callee": "sender", "resolution": "resolved"}])
    assert any("unresolved-call-marked-resolved" in x for x in validate_trace(bad, POLICY))
    good = make_trace(unresolved_calls=[{"caller": "c.py::f", "callee": "sender", "resolution": "dynamic-globals"}])
    assert not any("unresolved-call-marked-resolved" in x for x in validate_trace(good, POLICY))


def test_dynamic_link_confirmation_needs_read():
    steps = [step("graph", None, motivation="dynamic-link-confirmed:n.py", nodes=["n.py"],
                  args={"paths": ["n.py"]})]
    t = make_trace(steps=steps, terminal_index=0)
    assert any("dynamic-link-confirmation-needs-read" in x for x in validate_trace(t, POLICY))
    steps = [
        step("read", None, motivation="confirm routing", nodes=["n.py"],
             args={"requests": [{"path": "n.py"}]}),
        step("graph", None, motivation="dynamic-link-confirmed:n.py", nodes=["n.py"],
             args={"paths": ["n.py"]}),
    ]
    t = make_trace(steps=steps, terminal_index=1)
    assert not any("dynamic-link-confirmation-needs-read" in x for x in validate_trace(t, POLICY))


def test_exclusion_needs_read():
    t = make_trace(exclusions=[{"path": "reporting.py", "motivation": "uso presentazionale"}])
    assert any("exclusion-needs-read" in x for x in validate_trace(t, POLICY))
    steps = t["steps"] + [step("read", None, motivation="inspect use", nodes=["reporting.py"],
                               args={"requests": [{"path": "reporting.py"}]})]
    t = make_trace(steps=steps, terminal_index=3,
                   exclusions=[{"path": "reporting.py", "motivation": "uso presentazionale"}],
                   budget={"queries": 2, "reads": 2, "unique_nodes": 4, "suppressed_duplicates": 1})
    assert not any("exclusion-needs-read" in x for x in validate_trace(t, POLICY))


def test_clarification_payload():
    t = make_trace(outcome="clarify", stop_reason="ambiguous_domain_term",
                   question=None, candidates=None)
    assert any("clarification-payload" in x for x in validate_trace(t, POLICY))
    t = make_trace(outcome="clarify", stop_reason="ambiguous_domain_term",
                   question="Quale sconto rivedere: cliente o volume?",
                   candidates=[{"target": "p.py", "motivation": "cliente"},
                               {"target": "r.py", "motivation": "volume"}])
    assert not any("clarification-payload" in x for x in validate_trace(t, POLICY))


def test_budget_residual_required():
    t = make_trace(outcome="partial", stop_reason="budget_exhausted", residual=[])
    assert any("budget-residual-required" in x for x in validate_trace(t, POLICY))
    t = make_trace(outcome="partial", stop_reason="budget_exhausted", residual=["left.py"])
    assert not any("budget-residual-required" in x for x in validate_trace(t, POLICY))


def test_resolved_requires_empty_residual():
    t = make_trace(residual=["x.py"])
    assert any("resolved-residual-empty" in x for x in validate_trace(t, POLICY))


def test_unknown_op_rejected():
    t = make_trace(steps=[step("embedding", None, args={"query": "q"})], terminal_index=0)
    assert any("unknown-op" in x for x in validate_trace(t, POLICY))


def test_modules_index_before_lexical():
    t = make_trace(steps=[
        step("search", "L", args={"query": "q"}),
        step("modules", None, args={"list": True}),
    ], terminal_index=1)
    assert any("modules-index-before-lexical" in x for x in validate_trace(t, POLICY))


def test_resolved_empty_perimeter():
    t = make_trace(perimeter=[])
    assert any("resolved-empty-perimeter" in x for x in validate_trace(t, POLICY))
