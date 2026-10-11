# Host export operational compatibility audit (2026-10-11)

## Scope and evidence

This is a static audit of the five adapters, current kernel/compiler sources and
existing exports in the Daodan worktree at HEAD
`a949f9ef5dc8c0b9dfb5322d0bf91bd0c70e3984`. The worktree contained preexisting
uncommitted compiler, X-ray and generated-output changes. They were preserved.
HEAD alone therefore does not identify every inspected input, and this report
is not release or source/export parity evidence.

The trigger was Tri-Tech Code's installed Scribd grabber session
`ses_ed4a07a67ffeWtUqklg3187sTV`: a worker tried unavailable `Bash`, and the parent
tried loading an agent identity as a skill. The run completed without producing
the requested grabber. This establishes a consumer execution failure; it does
not establish a host service crash or that every Daodan plugin is broken.

The audit followed entries, role bodies, skills and bundled references, compared
workflow sidecars with rendered dispatch, and checked local tool/permission
bindings. No Claude, Copilot, Codex, Pi or OpenCode live workflow was executed by
this audit. Host names and fields below describe the repository's declared
contracts, not a new claim about the latest vendor release.

## Host assessment

| Host | Verified static finding | Limits and corrective scope |
|---|---|---|
| Claude Code | Nested Senior Review methods request generic workers outside the enclosing allowlist. Review React declares one isolated phase without receiving a harness. | Claude-shaped tool names alone are not a translation error here. Shared dispatch/sidecar contradictions need correction; browser stdin is not proved by this audit. |
| Copilot | Bodies retain `Task`/`subagent_type`, `Agent` and `Bash` despite bindings to `agent` and `runCommands`. Missing source tool restrictions become `tools: ['search']`. | Correct role frontmatter does not translate nested instructions; output-writing/browser roles need compatible permissions. |
| Codex | Review React retains a named `Task` call without the required inline-role harness. Nested methods retain foreign shell, question and dispatch instructions. | The measured Codex fixture covers inline delivery, not these affected plugin paths. |
| Pi | The same entries retain named dispatch and foreign question/shell instructions instead of role-body delivery and the declared companion mechanism. | `pi-subagents` and `pi-mcp-adapter` are explicit requirements; installed execution remains unmeasured here. |
| OpenCode V2 | Bodies and references retain capitalized tools and foreign dispatch fields despite native `shell`/`subagent`/`question` bindings and qualified component registration. | Loader registration works as a separate contract. Shared adaptation and Tri-Tech Code's consumer bindings require separate corrective work. |

## Findings and repair ownership

### F1. Operational bodies are not adapted by frontmatter conversion

The [renderer](../../../scripts/daodan/render.py) maps role tool declarations at
lines 191-219. `_host_text` and `_write_markdown` at lines 346-394 adapt plugin-root
and argument placeholders and insert notes, not arbitrary executable tool/schema
instructions. A correct role header can therefore ship a conflicting body.

Concrete exported instructions include:

- [Copilot Review TypeScript](../../../exports/copilot/plugins/typescript-development/prompts/review-typescript.prompt.md), lines 71-72: `Task` with `subagent_type`.
- [Codex Review React](../../../exports/codex/plugins/react-development/skills/review-react-workflow/SKILL.md), lines 71-72, and [Pi Review React](../../../exports/pi/plugins/react-development/prompts/react-development-review-react.md), lines 69-70: the same named dispatch.
- [OpenCode Review TypeScript](../../../exports/opencode/plugins/typescript-development/commands/review-typescript.md), line 68: the foreign dispatch schema survives registration.
- [OpenCode PWA scaffold](../../../exports/opencode/plugins/pwa-expert/commands/pwa-scaffold.md): `AskUserQuestion` at lines 17, 21 and 32, and `Bash` at line 56.
- [Copilot web-search technique](../../../exports/copilot/plugins/research/skills/web-search-techniques/SKILL.md), line 102: operational guidance still requires `Bash` in an agent tools declaration. The equivalent instruction survives Codex, Pi and OpenCode exports too.

**Repair owner:** neutralize executable instructions in the kernel and render the
actual host mechanism, fields and permission actions through adapters/compiler.
Include skills and bundled references in regression coverage, not just role
frontmatter. Preserve language fence labels and code whose subject is a host API.

### F2. Single-role dispatch can bypass harness rendering

[Review React's sidecar](../../../plugins/react-development/workflows/review-react.toml),
lines 9-15, declares a single `react-performance-optimizer` worker with
`isolation = "required"`. In [render.py](../../../scripts/daodan/render.py), lines
739-740, the harness predicate considers dispatch roles, inline workers and
fan-out, but not a single phase's `role`. Its generated entry takes the flat
rendering branch and retains the source dispatch example.

[Review TypeScript's sidecar](../../../plugins/typescript-development/workflows/review-typescript.toml)
and [content strategy's sidecar](../../../plugins/digital-marketing/workflows/content-strategy.toml)
have a different inconsistency: shared phases without a declared worker despite
worker dispatch in the Markdown. These must be aligned with their actual behavior,
not described as the same isolated-phase bug.

**Repair owner:** compiler harness selection and canonical workflow metadata/body
agreement. Tests must cover a single isolated role, allowed dispatch identity,
provider references, delivered/failed result and report ownership on all hosts.

### F3. Shared review methods contradict the enclosing worker contract

[Claude code-review](../../../exports/claude/plugins/senior-review/commands/code-review.md),
lines 23 and 46, restricts dispatch to declared workers and permits inline work
only through `project-protocol:isolated-worker`. Its nested
[review-quality-gates](../../../exports/claude/plugins/senior-review/skills/review-quality-gates/SKILL.md),
lines 169-171, prescribes `role: general-purpose`, `Agent`, `model: sonnet` and
`run_in_background`. The
[consolidation reference](../../../exports/claude/plugins/senior-review/skills/review-consolidation/references/code-review.md),
lines 55 and 71, also prescribes generic panel/critic workers.

This is a shared worker-ownership contradiction, including on Claude, rather than
only a tool spelling issue. The same method in
[Copilot](../../../exports/copilot/plugins/senior-review/skills/review-quality-gates/SKILL.md),
[Codex](../../../exports/codex/plugins/senior-review/skills/review-quality-gates/SKILL.md),
[Pi](../../../exports/pi/plugins/senior-review/skills/review-quality-gates/SKILL.md)
and [OpenCode](../../../exports/opencode/plugins/senior-review/skills/review-quality-gates/SKILL.md)
also carries fields/model aliases not bound by those host wrappers.

**Repair owner:** canonical methods and declared worker bindings. Preserve the
review lenses and independent results, express generic work through the permitted
isolated worker, and render supported dispatch/model fields for each host. Default
inheritance and justified overrides are separate contracts.

### F4. Copilot introduces a read-only restriction when none was declared

`_copilot_tools` in [render.py](../../../scripts/daodan/render.py), lines 308-317,
returns `['search']` when no mapped tools exist, including an absent source tools
restriction. [Copilot respondent](../../../exports/copilot/plugins/peer-review/agents/respondent.agent.md),
line 4, therefore exposes only `search`, while lines 18 and 112 require writing
response and ledger files.
[Copilot app-analyzer](../../../exports/copilot/plugins/app-analyzer/agents/app-analyzer.agent.md),
line 4, has the same restriction while lines 32-37 require ADB execution and
line 43 requires Playwright MCP.

**Repair owner:** adapter/compiler permission handling. Preserve the distinction
between an omitted restriction and an explicit tool list. Derive or declare the
required actions without inventing capabilities. Add negative tests for writing,
shell and MCP availability; no live Copilot denial was measured by this audit.

### F5. Required-provider recovery still instructs other hosts to install Claude plugins

[Copilot respondent](../../../exports/copilot/plugins/peer-review/agents/respondent.agent.md),
line 28, requires `claude plugin install superpowers@claude-plugins-official` without
an active-host qualification. The same recovery command survives
[Codex](../../../exports/codex/plugins/peer-review/roles/respondent.md),
[Pi](../../../exports/pi/plugins/peer-review/skills/peer-review-respondent/SKILL.md)
and [OpenCode](../../../exports/opencode/plugins/peer-review/agents/respondent.md)
role bodies.

Provider declarations are present. The defect is the host-specific recovery
instruction, not proof that those providers are absent in any particular install.
[Test hygiene](../../../plugins/testing/skills/test-hygiene/SKILL.md), lines 62-68,
already requires the active host's installation guidance and explicitly limits
its Claude examples to Claude. It is not a confirmed recovery defect. The
[remediation method](../../../plugins/testing/skills/test-remediation-method/SKILL.md)
loads that protected method before its
[consolidation reference](../../../plugins/testing/skills/test-remediation-method/references/consolidate.md);
the reference's terse Claude example alone does not establish a broken pipeline.
Grabber's explicit Claude/other-host Playwright installation distinction and the
generated peer-review MCP registration notes are also appropriate adaptations.

**Repair owner:** kernel obligation plus host provisioning binding. Keep foreign
provider identities qualified and mandatory. Give active-host recovery or report
that provisioning is unavailable, without substituting unrelated skills.

### F6. Capture requires an interactive checkpoint without a proved stdin binding

[Grabber's canonical skill](../../../plugins/grabber-development/skills/grabber-development/SKILL.md),
lines 23-25 and 55, requires a shell script parked on `input()` and a user pressing
Enter while capture continues. All five exports preserve this requirement; the
non-Claude exports also preserve the `Bash` tool name.

Interactive stdin and foreground session control are not established by the
adapter's `shell.execute` capability alone. Tri-Tech Code's inspected native shell
uses ignored stdin, so this path needs an explicit noninteractive completion
signal there. This audit did not prove the interactive path on the other hosts.

**Repair owner:** host-specific terminal/browser binding with a capture stop signal,
background lifetime and delivery contract. Preserve user-driven authenticated
navigation. Test the supported checkpoint rather than assuming every shell is a PTY.

## Existing checks and evidence limits

The [host-vocabulary linter](../../../scripts/lint_host_vocabulary.py), lines 42-44,
checks a limited team-primitive token set. Lines 55-60 retain baselines for four
workflow bodies. That rule does not detect `Bash`, `Agent`, `AskUserQuestion`, model
aliases, permission/body contradictions or the single-role harness gap. A green
result is useful for the tokens it covers, not semantic compatibility evidence.

[Historical probes](../../../tests/host-probes/README.md), lines 84-89, report
measured Claude and Codex fixtures; Copilot, Pi and OpenCode remain unmeasured in
that evidence table. Codex's successful inline fixture does not demonstrate
Review React or the nested review panel. Existing MCP registration notes, OpenCode
qualified component IDs and loader permissions are separate implemented contracts.
Prompt-level write confinement (`mechanical_wired = false`) is documented and is
not recategorized here as a lost hook or a newly proved enforcement mechanism.

## Documentation changes and next verification

This change updates canonical `CLAUDE.md`, the repository `downstream-exports`
procedure, their synchronized Codex copies, the host reference and documentation
index. It does not change compiler/plugin behavior, regenerate exports, publish
a release, repin Daodan in Tri-Tech Code or deploy the desktop app.

Corrective implementation must address the shared kernel, five adapters/compiler
and permanent consumer bindings. Tri-Tech Code's earlier Grabber-only registration
fix is narrower: it does not fix these exports. Its project-output contract also
requires coordination between storage helpers, schemas and result readers before
relocating upstream `.daodan`/`.codebase-xray` output under `.tritech`.

Documentation verification results:

- `python -B scripts/sync_codex_instructions.py --check`: passed after synchronization.
- `python -B scripts/sync_plugin_docs.py --check`: passed, 42 plugin references and the dependency catalog unchanged.
- Local Markdown links in the seven affected Daodan instruction/documentation files: all targets resolved.
- Independent source review: completed; corrected the recovery false positive and source line references above.
- Targeted diff and whitespace checks: passed in Daodan and Tri-Tech Code.

Compiler/host/runtime repair remains unverified until the affected source and
exported execution paths receive the targeted checks described above. No build,
application suite or live host probe was run for these documentation-only changes.

## Implementation: marketplace 32.10.0

The audit above records the pre-fix inputs and examples; its old exported line
numbers are historical evidence. The release fixes the neutral kernels, host
adapters and compiler together and regenerates all five exports. Every plugin
gets a patch version so installed caches can acquire the new execution binding.

- Operational bindings are included in role/workflow/skill bodies, loaded
  references, inline dispatch resources and override content. Kernel execution
  instructions use neutral mechanisms, while domain code, canonical frontmatter
  and marketplace/SDK host-as-subject examples retain their original semantics.
- Harness rendering includes a single phase role. React and TypeScript separate
  isolated findings from coordinator-owned reporting; content strategy declares
  its selected audits, barriers, approved application and final delivery.
- Senior Review's nested panel, critic and fix assignments use the permitted
  isolated-worker. Peer Review declares all three method-owned roles.
- Copilot omits an absent tool restriction, preserves an explicit empty list and
  rejects an unknown explicit tool instead of silently supplying search-only
  access. All ordinary role models inherit the session.
- Required providers recover through the active host. Grabber capture uses a
  coordinator-owned completion signal with supported background/session control
  rather than assuming terminal stdin.
- The vocabulary baseline is empty and checks nested operational tool names and
  dispatch fields. New compiler and method-contract regressions cover these
  defects; final verification results are recorded below when run.

A delivered artifact still needs its own verification. These instructions do not
turn a model's stop or a host's idle event into proof of task completion. No live
model/browser run on every host is claimed by the compiler release.

The execution obligation belongs to the worker agent and its coordinator harness.
Skills describe methods and knowledge; loading them does not schedule work or
provide a mechanical continuation gate. These export changes bind the obligation
to generated agent bodies and coordinators as well as neutralizing conflicting
references. Host runners still own turn scheduling; no cross-host autonomous
scheduler is claimed.

Verification before publication: dependency, registration, bundled-path and
vocabulary lint passed; all 25 fact anchors agree; instruction and 42-plugin
documentation parity passed; Copilot confinement cases passed 36/36. The Windows
POSIX executable-state test is platform-skipped; CI on Linux owns that check.
The initial suite observed catalog drift while regeneration was still running and
resource-parity assertions needed to account for the exact generated binding.
Those oracles retain full domain-content comparison and explicitly reject absent,
wrong-host, duplicated or altered bindings. The final stable-input suite result
and drift check follow below.

### Final local validation

The stable candidate passed `python -B -m unittest discover -s tests`: 690 tests run, 689 passed, one Windows-only environment skip, zero failures or errors (334.736 seconds). The skipped POSIX executable-state test remains required on Linux CI. The final five-host compiler check with support reporting passed with no generated drift; all 210 plugin/host combinations are native or adapted. These are content and compiler checks, not evidence that every browser or model workflow was executed live.
