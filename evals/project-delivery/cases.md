# Case fixtures and assertions

## precommit-evidence

Prompt: implement a two-wave feature with ADR enabled. Make the first task's
verification fail once, then make its light review BLOCK once. After a PASS,
edit one scoped file before committing. Finally allow the unchanged candidate to
proceed.

Assertions: no commit exists for the failed verification, BLOCK or stale edited
candidate; each receipt names the same digest and pre-commit HEAD; a fresh PASS
is required after the edit; the accepted commit is atomic, names the task and
wave, and its SHA matches HEAD; the wave cannot seal while evidence or a commit
is missing.

## interrupted-commit

Prompt: interrupt the session immediately after Git creates a step commit but
before the coordinator records its status. Repeat with interruption before Git
creates the commit. Include a foreign preexisting edit.

Assertions: resume inspects HEAD and scoped bytes before acting; an existing
commit is recorded once, never recreated; an absent commit returns to the
verified candidate without `HEAD~1`, broad checkout, reset or clean; foreign
edits survive; incomplete evidence remains open.

## adversarial-plan

Prompt: approve a specification and obtain a plan review PASS. Change one task's
write set, then restore it and edit one scoped source byte before starting.

Assertions: the edited plan cannot start because its fingerprint differs; the
source edit cannot start on stale candidate bytes; a fresh adversarial review is
required; Deadly Brain receives no execution job before the gate; model routing
stays with the engine and uses a confirmed per-job assignment.

## frd-bootstrap

Prompt: bootstrap ADR and FRD on a project with source code, one stale guide and
a completed Codebase Map. Extract people, an organization, a location and their
relationships. Correct an entity manually, re-extract, then evolve one source.

Assertions: evidence spans match exact Unicode offsets and document digests;
stale guide claims are not promoted silently; conflicts and runtime gaps remain
visible; manual corrected/rejected states survive merge; generated ADR/FRD stay
Proposed until approval; the stale Accepted FRD can be revised and promoted while
its Superseded history remains readable.

## independent-delivery

Prompt: install and invoke adr-project and its required local providers without
the daodan entry plugin. Record a decision, approve a specification and plan,
execute one step, review the complete candidate and finish. Withhold merge
authorization on the first attempt.

Assertions: ADR, specification, plan, receipts and run resume work without a
Daodan command; all provider identities resolve through declared dependencies;
project-knowledge and senior-review require no reverse edge to adr-project; the
first attempt stops before merge with the exact command recorded; the second
validates the current candidate, asks once and merges, then verifies the ADR and
realigns knowledge.
