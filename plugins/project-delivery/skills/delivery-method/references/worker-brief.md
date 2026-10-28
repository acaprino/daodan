# Worker brief for one micro-task

Give the writer only this brief, filled from the run; missing fields block dispatch.
Include `work-controller:work-record`'s working discipline and isolated worker contract.

```
## Task
id: <task id>            wave: <wave id>            run: <run id>
process: <bound process/attempt IDs; otherwise legacy unbound>
objective: <one sentence>
specification: <bound path, SHA-256, approval question/run, relevant approved requirements; absent for legacy or pure repair/refactor>
examples to make pass: <EX-* ids/text>
invariants to keep: <INV-* ids/text; authoritative boundary contract/version, wire/errors, derived types/mocks, serialization check agreed before parallel producer/consumer work>
rejected alternatives: <relevant RA-* ids/text>

## Files
write_set: <exact paths; nothing else may change>
read context: <verified `task-packet`: write_set cards/sources, one-hop callers/callees, current signatures>
locate: packet alone is insufficient; follow `codebase-map:map-method` `references/locate.md`: `codebase_map_search` using objective/example names, `codebase_map_outline` and `codebase_map_graph` on hits, `codebase_map_read` by symbol, `codebase_map_edit_impact` before editing; without MCP, `snapshot.py search MANIFEST --query Q` and matching subcommands
protected paths: <preexisting modified files in IN_PLACE>

## Oracle
command: <test command>
expected failure before the change: <substring or assertion>
verification after the change: <command>

## Prior rulings in this run
<id: decision, reason>

## Evidence pack
<available tool results for these files, or "none">

## Authorization
write_set only; no commit/new dependency; public-contract changes only as named above

## Exit
Return exactly one of:
- OK, changed paths, before/after oracle output, verification output, rulings (decision, reason, cost if wrong, evidence)
- NEEDS_REPLAN, required file/reason, or missing human decision/evidence
- ORACLE_INVALID, oracle output and why failure differed from expectation
Do not widen write_set. Do not weaken the oracle. Do not retry past one attempt.
```

Split tasks whose brief exceeds the model's capacity.
