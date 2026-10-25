# Initialize a project

Initialize new or existing projects. Idempotent: keep every valid existing part.
Every work command runs it when no loop block exists.

## An empty folder

Ask what to build: purpose, stack, kind (service, library, command-line tool,
application). For Python, load the skill `python-development:python-scaffold-method`,
whose plan-and-confirm step is the authorization. For another stack, use its
official initializer with the user's choices and show the command before
running it. Then continue below.

## An existing project

1. **Map.** Execute the analyze entry's preflight at the first use's depth, lite
   by default (none skips this step), dispatch
   `codebase-map:map-analyst` in an isolated context, and bind the run. An
   existing completed run on the same target is offered as the update parent.
   Areas deepen later, where tasks work.
2. **Requirement records.** When requested, draft missing ADR/FRD through
   `project-delivery:project-bootstrap` from verified evidence, Proposed only.
   Validate both through their owners.
3. **Environment.** Probe the interpreter and runners as
   `references/preflight.md` does and record them in the run's `environment`.
4. **Instructions.** Load `project-knowledge:instructions-method`; create the
   authoritative file when authorized, or audit it, and write the loop block
   with the verified test, lint, type and build commands, the workspace
   convention and the active records resolved in step 2.
5. **Baseline.** Run the declared test command once and record the baseline
   as `references/preflight.md` classifies it; record `last_synced` as the
   current head.
6. **Report.** What exists, what was created, what could not be verified (a
   runner missing, a command that needs an environment), and the first task's
   command.
