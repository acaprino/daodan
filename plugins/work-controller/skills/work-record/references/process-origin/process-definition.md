# Process definition

The runtime accepts one YAML document with schema `process-controller/process/v1` and kind `graph`. The legacy `deadly-brain/process/v1` schema remains accepted for compatibility. Validation is closed: unknown fields, unknown component kinds, missing producers, duplicate artifact producers, cycles and paths outside the workspace are rejected.

```yaml
schema: process-controller/process/v1
kind: graph
id: api-review
objective: Review the public API and record a verified report
jobs:
  - id: analyze
    type: agent
    summary: Inspect the API and write a bounded report
    produces:
      - name: report
        type: markdown
        path: artifacts/report.md
    write_set: [artifacts/report.md]
    max_attempts: 2
    timeout_seconds: 300
  - id: review
    type: agent
    summary: Verify the report against the API contract
    needs: [analyze]
    consumes: [report]
    produces:
      - name: review
        type: markdown
        path: artifacts/review.md
    write_set: [artifacts/review.md]
budget:
  max_attempts: 20
  max_seconds: 3600
```

## Inputs and dependencies

An entry in `consumes` names either a process-level external input or an artifact declared in another job's `produces`. A producer dependency is added automatically; `needs` declares additional ordering without inferring dependencies from source-code call edges.

```yaml
inputs:
  - name: source
    type: markdown
    path: docs/input.md
```

External files are copied into the content-addressed store at run admission. Their later mutation does not change the bytes bound to that run.

## Job kinds

`agent` creates a host packet. The host must start the attempt, perform the work and complete it with a unique event ID. `command` executes an argv array without a shell and requires the run's `shell` grant. Its exit code is the deterministic gate. Both kinds use the same artifact and attempt contracts.

Every produced path must be declared in `write_set`. Artifact admission requires the file to exist and be copied successfully into the immutable store. The engine does not claim that this proves semantic correctness; use downstream verification jobs for independent checks.

`write_set` is a scope contract, not an operating-system sandbox. Command jobs execute trusted argv with the user's permissions, and agent jobs run through the host. Grant execution only to definitions you authorize; an installed-host adapter must prove any stronger confinement it claims.

## Partial commits

A job may declare:

```yaml
commit:
  message: "process-controller: update API review"
```

The run needs the separate `commit` grant and a clean Git baseline. After the job's outputs pass admission preparation, the engine stages only the declared write set, rejects staged paths outside it and records the resulting commit SHA in the attempt. YAML alone never supplies the grant.

## Immutable admission

A run stores both the normalized definition digest and the source YAML digest. It also binds the workspace used for every subsequent handoff and completion. Changing a file after admission does not mutate the active definition. Revision and selective replan are not part of the first slice; start a new run instead.
