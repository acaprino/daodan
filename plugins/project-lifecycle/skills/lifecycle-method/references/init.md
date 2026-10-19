# Initialize a project

The first entry of a project into the cycle, new or existing, and the only
assess operation that writes outside its run. It is idempotent: a part that
exists and validates is kept. Every work command runs it first when the
project has no map, no record index or no loop block.

## An empty folder

Ask what to build: purpose, stack, kind (service, library, command-line tool,
application). For Python, load the skill `python-development:python-scaffold-method`,
whose plan-and-confirm step is the authorization. For another stack, use its
official initializer with the user's choices and show the command before
running it. Then continue below.

## An existing project

1. **Map.** Execute the analyze entry's preflight at lite depth, dispatch
   `codebase-map:map-analyst` in an isolated context, and bind the run. An
   existing completed run on the same target is offered as the update parent.
   Areas deepen later, where tasks work.
2. **Decision records.** Load `project-knowledge:adr-method` and run
   `init-index`; an existing directory is validated, never rewritten.
3. **Environment.** Probe the interpreter and runners as
   `references/preflight.md` does and record them in the run's `environment`.
4. **Instructions.** Load `project-knowledge:instructions-method`; create the
   authoritative file when authorized, or audit it, and write the loop block
   with the verified test, lint, type and build commands, the workspace
   convention and the active records.
5. **Baseline.** Run the declared test command once and record the baseline
   as `references/preflight.md` classifies it; record `last_synced` as the
   current head.
6. **Report.** What exists, what was created, what could not be verified (a
   runner missing, a command that needs an environment), and the first task's
   command.
