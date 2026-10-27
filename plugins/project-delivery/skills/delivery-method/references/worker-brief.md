# Worker brief for one micro-task

The writer receives only this brief. Fill every field from the run record;
missing fields block dispatch. Include the working discipline and isolated
worker contract required by `work-controller:work-record`.

```
## Task
id: <task id>            wave: <wave id>            run: <run id>
process: <bound process ID and attempt ID when present; legacy unbound otherwise>
objective: <one sentence>
specification: <bound path, SHA-256, approval question/run and relevant approved requirements; absent for legacy or pure repair/refactor>
examples to make pass: <EX-* ids and their text>
invariants to keep: <INV-* ids and text; authoritative boundary contract/version, wire/errors, derived types/mocks and serialization check agreed before parallel producer/consumer work>
rejected alternatives: <RA-* ids and their text, when they touch this task>

## Files
write_set: <exact paths; nothing else may change>
read context: <verified `task-packet`: cards and sources of the write_set, one-hop callers and callees, current signatures>
protected paths: <preexisting modified files, in IN_PLACE mode>

## Oracle
command: <test command>
expected failure before the change: <substring or assertion>
verification after the change: <command>

## Prior rulings in this run
<id: decision, reason>

## Evidence pack
<tool results already available for these files, or "none">

## Authorization
edits inside write_set only; no commit; no new dependency; no change to a public contract not named above

## Exit
Return exactly one of:
- OK, with the changed paths, the oracle output before and after, the verification output, and any ruling (decision, reason, cost if wrong, evidence)
- NEEDS_REPLAN, with the file that must change and why, or the human decision missing and its evidence
- ORACLE_INVALID, with the oracle output and why it did not fail as expected
Do not widen write_set. Do not weaken the oracle. Do not retry past one attempt.
```

Split tasks whose brief exceeds the model's capacity.
