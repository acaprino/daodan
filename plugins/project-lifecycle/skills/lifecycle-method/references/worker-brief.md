# Worker brief for one micro-task

The writer of a micro-task receives this brief and nothing else of the
conversation. Fill every field from the run record; a missing field is a
reason not to dispatch. The protocol's working discipline and the isolated
worker contract travel with the brief, as `project-protocol:project-protocol`
requires.

```
## Task
id: <task id>            wave: <wave id>            run: <run id>
objective: <one sentence, from the record>
examples to make pass: <EX-* ids and their text>
invariants to keep: <INV-* ids and their text>
rejected alternatives: <RA-* ids and their text, when they touch this task>

## Files
write_set: <exact paths; nothing else may change>
read context: <symbol cards of the write_set and their one-hop callers and callees, with current signatures>
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
- NEEDS_REPLAN, with the file that must change and why
- ORACLE_INVALID, with the oracle output and why it did not fail as expected
Do not widen write_set. Do not weaken the oracle. Do not retry past one attempt.
```

Size: the brief plus its read context stays small enough for an economical
model to hold it whole; when the context would exceed that, the task is too
large and goes back to the plan.
