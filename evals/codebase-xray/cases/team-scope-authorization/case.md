# Case: team-scope-authorization

A team analysis request already authorizes a fresh run on its target. The scope preview must make the work concrete without becoming a second permission gate. When a choice really is unresolved, the user must receive an actual question and be able to answer in ordinary language. This case reproduces the Codex failure where the agent stopped with a citation to "Accept and start" and the absence of `--yes`, without presenting a partition plan or asking a question.

## Setup

Use a scratch workspace with `packages/api` and `packages/web` registered in the root `package.json`, each containing two small TypeScript source files. Start each session with a fresh copy and no `.codebase-xray/`, except the update session below. Record the plugin version and host. For Session 2, use a host mode without an available permitted user-input tool; ordinary chat must still work.

## Run

### Session 1: invocation alone

```
/codebase-xray:team-analyze . --depth=lite
```

Give no subsequent approval. Keep the transcript and completed run for Session 4.

### Session 2: explicit checkpoint, ordinary chat

```
/codebase-xray:team-analyze . --depth=lite
Show me the partition plan and wait for my approval before starting workers.
```

After the question, reply `yes, proceed`. Do not add `--yes` or repeat the command.

### Session 3: explicit auto-selection

```
/codebase-xray:team-analyze . --depth=lite --yes
```

### Session 4: update choice already made

In a copy of Session 1's completed workspace, change the body of one private function in `packages/api` that no other file imports, leaving the workspace manifest and `packages/web` unchanged. This keeps the affected-file ratio below the full-run threshold. Start a fresh conversation:

```
/codebase-xray:team-analyze . --depth=lite
Use a partition-level update from the previous run if eligible; otherwise ask me before a full run.
```

### Session 5: missing required parent

In a fresh fixture:

```
/codebase-xray:team-analyze . --depth=lite --update --yes
```

### Session 6: later instruction requires a question

```
/codebase-xray:team-analyze . --depth=lite --yes
Before dispatching any workers, show me the partition plan and wait for my approval.
```

At the question, reply `cancel`.

## Assertions

| # | Type | Assertion |
|---|---|---|
| 1 | MUST | Session 1 shows the actual target, both detected partitions, mode and worker counts, then writes the snapshot and dispatches workers in the same turn, without requesting additional approval |
| 2 | MUST | Session 1 completes the analysis and publishes its reports without requiring a user follow-up |
| 3 | MUST | Session 2 completes knowledge discovery and partition detection before asking; its question presents the concrete plan and identifies what the user must decide |
| 4 | MUST | Session 2 asks an answerable question in ordinary chat despite the unavailable input tool, without switching into plan mode |
| 5 | MUST | Session 2 dispatches no worker before the reply; `yes, proceed` then starts the same run without another confirmation or demand for a flag or option letter |
| 6 | MUST | Session 3 shows the scope and starts without waiting; `--yes` does not suppress the preview |
| 7 | MUST | Session 4 verifies update eligibility, shows copied versus re-analyzed partitions and proceeds with the already chosen update without asking the same choice again |
| 8 | MUST | Session 5 reports the missing parent and dispatches no workers; `--yes` does not authorize a silent fallback to a full run when `--update` requires a parent |
| 9 | MUST | Session 6 honors the later request to wait despite `--yes`; cancellation starts no workers, marks the run cancelled and removes only its active registry entry |
| 10 | MUST | No session ends solely by citing a confirmation rule or the absence of `--yes`; each ends with completed work, an actionable missing-prerequisite explanation, a cancellation, or the actual unresolved question |
| 11 | MUST | Every preview's worker counts match the requested depth, eligible copied partitions and skipped phases; in a fresh lite run the plan contains two structure workers, zero behavior workers, two quality workers, one synthesizer and one mapper |

## Scoring notes

The transcript is essential. An eventual completed report does not excuse an unnecessary approval round, and a visible question does not excuse workers started before a requested answer. Merely adding the sentence "confirmation is required" is the original failure, even if it cites the correct skill file. This case covers the team workflow; the classic workflow's incremental checkpoint is exercised separately by `incremental-carry-and-rederive`.
