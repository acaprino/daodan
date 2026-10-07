# Project Lifecycle

Five complete paths coordinate the same canonical owners used by standalone
specialists: assess, repair, change, verify and consolidate.

assess produces evidence and a dependency-aware plan across knowledge, structure,
tests and workspace artifacts. repair validates an exact run/plan and applies only
authorized compatible remedies. change covers bootstrap, feature, bugfix, refactor
and migration. verify binds checks to the actual candidate. consolidate preserves
verified experiment conclusions before retaining or disposing of owned output.

Use --focus=knowledge|structure|tests|artifacts|all and
--depth=quick|standard|deep. Default assessment is one initial quick pass.
The plan discloses expensive context steps, unavailable dimensions and commit-only
cleanup before application. Unknown token consumption stays unknown.

State belongs in .daodan/runs/<id>/. Resume an exact run ID; alternative dedicated
roots must stay inside the project. The project-protocol helper validates identity,
snapshots, revisions, deliveries and required gates. No arbitrary workflow executor
or automatic optional-specialist registry is introduced.

--fix permits scoped edits, --commit additionally permits commits; application
subtraction retains its commit-only prerequisite. --purge requires a separate
explicit grant for concluded owned artifacts. Retention is confined, fingerprinted
and resumable, preserving necessary evidence and rejecting links or changed paths.

Static evidence, runtime exercise and installed-host probes are distinct.
Read [the migration](../migration-to-coherent-harness.md) and
[architecture](../superpowers/specs/2026-10-07-daodan-coherent-harness-design.md).

