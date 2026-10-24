# Abstraction Architect Plugin

> Structural entropy auditor: finds where the same concept is represented, owned, computed or implemented more than once, and what it costs when that concept changes. Seven dimensions over two evidence tracks: a knowledge track judged by semantic identity and ownership, and a form track judged by recurrence. Report-only, grounded in canonical theory (Metz, Beck, Fowler, Gross, North, DDD).

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Prerequisites

The `codebase-map` plugin is a hard dependency: the global audit consumes `.codebase-map/` output and its method, run by `/daodan:check-health`, auto-launches Codebase Map when that output is missing. Diff mode needs only whatever Codebase Map output is on disk and runs on the concept index plus Glob and Grep when there is none, at reduced confidence declared in its Gaps section.

## The seven dimensions

| | Dimension | Track | Proof rule |
|---|---|---|---|
| D1 | Duplicated domain knowledge | Knowledge | Same policy, formula or invariant; two or more representations; they must stay consistent |
| D2 | Competing sources of truth | Knowledge | Same fact; two or more authoritative writers or definitions; canonical owner absent or ambiguous |
| D3 | Redundant representation | Knowledge | Same concept; parallel representations; real mapping or synchronization cost |
| D4 | Duplicated or derivable state | Knowledge | Derivable but maintained separately, plus sync, invalidation or repair code |
| D5 | Missed unification | Form | Mechanism independently repeated three or more times; Rule of Three |
| D6 | Prior art available | Form | A clearly canonical implementation exists and something else reimplements or bypasses it |
| D7 | Abstraction fitness | Form | Proven internal friction: flags, per-caller exceptions, caller bypass, leakage |

**The track determines the nature of the evidence; the dimension determines the gate.** On the knowledge track (D1 to D4) the count is the wrong instrument: two representations suffice behind a strict semantic gate (gates K1 to K6), and the discriminating question is whether the representations can legitimately disagree. On the form track (gates A1 to A5) the Rule of Three applies to D5 only. D6 needs one canonical implementation plus one bypass, and D7 is friction inside a single abstraction, so neither ever counts copies.

Every candidate is also scored on four lenses, reported as fields and never as categories of their own: L1 change amplification, L2 indirection cost (Locality of Behaviour), L3 bounded context (a hard gate on the knowledge track), L4 option price (Tidy First). One defect gets one primary dimension, the deepest on the precedence D2, D4, D3, D1, D6, D5, D7; the others become supporting evidence.

**Severity follows consequence, never occurrence count.** High for security, data-correctness or operational risk; Medium (the default) for maintenance drag; Low for a smell with no concrete pressure. Occurrence count is reported as evidence strength only. Confidence is reported separately, and a knowledge-track finding whose bounded context could not be determined carries `Bounded-context exception: unverified`, which caps it at Low confidence and at Medium severity.

## Agents

### `abstraction-architect-agent`

Adversarial auditor with two modes. Global mode censuses the whole codebase from `.codebase-map/` plus its own discovery pass. Diff mode anchors on the changed files and asks whether the change introduces or aggravates structural entropy relative to the codebase that already exists. Its governing rules: precision over recall governs what is reported, not what is searched; index entries nominate search targets, current source code proves findings.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Glob, Grep, Bash |
| **Use for** | Structural entropy audits, "who canonically owns this fact" questions, "did what I just wrote already exist" checks on changed code |

**Invocation:**
```
Use the abstraction-architect-agent agent to audit [path] for structural entropy
```
Also spawned by the audit method of `/daodan:check-health` and, in diff mode, as the structural entropy dimension of the reviews of `/daodan:review-branch` and `/daodan:review-changes`.

**Key behaviors (global mode):**
- Reads `01-structure.md`, `02-interfaces.md`, `03-flows.md`, `04-semantics.md`, plus `08-interconnect-map.md` when the team entry of `codebase-map:map-method` produced it (that file enables the bounded-context check; without it knowledge-track findings carry `Bounded-context exception: unverified`)
- Builds a seed map from the Codebase Map, extracts entity and behavioural concepts, then runs four search families per concept: by name and near-synonym, by literal, by call, by shape of decision. The seed map seeds the census and never bounds it
- Builds a Concept Evidence Index (representations with roles, writers, consumers, canonical owner status), then tests every concept with more than one representation against its dimension gate and the lenses
- Re-reads every cited representation on current source before promoting a finding
- Writes the concept index to `.abstraction-architect/concept-index.json` (refusing to overwrite an index recorded with a broader scope) and the report to `.abstraction-architect/findings.md`

**Key behaviors (diff mode):**
- Extracts two kinds of changed unit: structural units (new functions, methods, classes, modules, constant tables, inline blocks longer than roughly five lines) and semantic units (rules and policies, predicates and thresholds, persisted fields and state, models, DTOs, types and enums, mappings, configuration and defaults, formulas). A threshold moved from 1000 to 1500 is a semantic unit with no structural unit at all
- Checks concept index freshness with `scripts/concept_index.py`, revalidates the dirty concepts on current source, and works through every changed file the index does not claim, because that is where a diff introduces a new concept
- Asks each of D1 to D7 as "introduced or aggravated by this change" (does this diff add another representation of an existing policy, create a second authority over an existing fact, store something already derivable, become the third occurrence, reimplement something already available, worsen abstraction friction)
- Never restricts the search to the changed files: what it looks for is by definition outside the diff
- Needs only `01-structure.md` and `02-interfaces.md` (lite Codebase Map is enough)
- Writes the report to `.abstraction-architect/findings-diff.md`, or wherever the calling review pipeline directs it. **Diff mode never writes the concept index**; new concepts and index contradictions go in Gaps for the next global audit

**Report sections (both modes):** A competing sources of truth (D2), B duplicated or derivable state (D4), C redundant representation (D3), D duplicated domain knowledge (D1), E prior art available (D6), F missed unification (D5), G abstraction fitness (D7), H second occurrences noted but not flagged (form track only, exempt from the severity floor), I confidence and gaps. Each finding names its dimension, its catalogued pattern or `uncatalogued`, tight line-range evidence with roles, the L1 count, a one-sentence suggested direction, and an evidence-track block.

## Skills

### `abstraction-architect`

Knowledge base for structural entropy. Covers the two evidence tracks, the seven dimensions and four lenses, the census method, the concept index protocol, severity and remediation framing, 18 essential-duplication patterns (P1 to P12 infrastructural, P13 to P18 domain-facing), 12 wrong-abstraction patterns (A1 to A12), the canonical theory, and a verified reading list. The pattern catalogs are discovery aids, never admission gates: a candidate that passes its gate and matches no pattern is still a finding.

References, loaded on demand by the agent (`dimensions.md` first): `dimensions.md`, `evidence-tracks.md`, `concept-census.md`, `concept-index-protocol.md`, `decision-frame.md`, `unification-patterns.md`, `anti-patterns.md`, `scope-boundaries.md`, `theory.md`, `further-reading.md`. The skill also ships `scripts/concept_index.py`, which reports concept index freshness.

## Entry and method

The plugin has no command of its own. `/daodan:check-health` runs the audit as its structure dimension: the entry loads `abstraction-architect:abstraction-architect` and follows its `references/audit.md`. A coordinator that already holds a run loads the same method.

What were flags are now decisions the method takes from the free-text target:

- **Mode.** No path, or a path, audits that codebase root in global mode (default: the current working directory). A commit, a branch or a PR selects diff mode against that base: the seven questions as "introduced or aggravated by this change". With no ref the base defaults to the merge base with the default branch, falling back to `HEAD` for uncommitted work. Diff mode requires a git repository and never launches a Codebase Map.
- **Scope.** A subtree named beside the target limits findings to it. The Codebase Map still runs on the full codebase.
- **Severity floor.** `medium` by default; `low` or `high` only when the caller passes it.
- **Focus.** `all` by default. Knowledge-track concerns in the text select D1 to D4, form-track concerns select D5 to D7, and a dimension id selects that dimension.
- **Concept index.** Not read or written when the target is not a Git repository. Global mode ignores an existing index and censuses the codebase from scratch only when the freshness check reports `unusable` for an unreachable baseline or rewritten history, or when the text names a large refactor.

In global mode the method checks for a current `.codebase-map/` run holding the first four phases and, when that output is missing or stale, runs the analyze entry of `codebase-map:map-method` through phase 4. Unless the index is not used, it then runs the freshness script and prints the concept index state before spawning the agent, so a stale index is visible rather than silent:

```
Concept index: delta-stale (baseline a13fe2, HEAD 92ac10, 4 concepts to revalidate)
```

The states are `fresh` (indexed tree equals the current tree and the worktree is clean within scope), `delta-stale` (the normal case: touched concepts are marked dirty and revalidated) and `unusable` (the audit proceeds without the index and declares the reduced coverage in Gaps). In global mode the agent rewrites `.abstraction-architect/concept-index.json`; diff mode never does. Report-only: the report goes to the run directory (`findings.md`, or `findings-diff.md` in diff mode), the concept index is the only write outside it, and the suggested direction in each finding is one sentence, not a refactoring plan.

## Ecosystem integration

- **`/daodan:review-branch`** (the team-review variant of `senior-review:review-method`) runs the agent in diff mode as its structural entropy dimension whenever the review target resolves to a diff that adds at least one function, method, class, module, constant table or block longer than roughly five lines. `senior-review` hard-depends on this plugin, so the only thing conditional about the dimension is that signal. Plain file/directory targets have no diff to anchor on and point to the global audit of `/daodan:check-health` instead. The reviewer reads the concept index when one exists and never writes it.
- **The code-review variant** of `senior-review:review-method` runs it as Agent J (Structural Entropy Review) on the same signal.
- **`senior-review:code-auditor`** keeps the smells fully visible inside one file (god functions, a leaky signature, an interface with one implementation); this agent owns the cross-file question. The dedup boundary is declared on both sides.
- **The team entry of `codebase-map:map-method`** adds `08-interconnect-map.md` to the Codebase Map output, which enables the bounded-context check in global mode.

**Related:** [codebase-map](codebase-map.md) (produces the `.codebase-map/` input) | [senior-review](senior-review.md) (`/daodan:review-branch` structural entropy dimension, code-review Agent J, code-auditor dedup boundary) | [clean-code](clean-code.md) (readability cleanup, different concern)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `5.2.0`. **Source:** [plugin.toml](<../../plugins/abstraction-architect/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [codebase-map](<codebase-map.md>) |
| Direct external | None |
| Local closure (3) | [abstraction-architect](<abstraction-architect.md>), [codebase-map](<codebase-map.md>), [report-rendering](<report-rendering.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** None.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `abstraction-architect:abstraction-architect` | Structural entropy knowledge base: canonical ownership, duplicated domain rules, redundant models and abstraction fitness. TRIGGER WHEN: deciding whether to extract, centralize or inline; asking who owns a rule or state; auditing duplicated knowledge or competing sources of truth under the audit method (references/audit.md, run by /daodan:check-health) or the reviews of /daodan:review-changes and /daodan:review-branch. DO NOT TRIGGER WHEN: formatting (use clean-code:readability-method), Python refactoring (use python-development:python-refactor-method), dead code (use senior-review:application-cleanup-method), security (use senior-review:security-auditor), or contract drift (use senior-review:api-contract-auditor). | [abstraction-architect](<../../plugins/abstraction-architect/skills/abstraction-architect/SKILL.md>) |
| Role | `abstraction-architect:abstraction-architect-agent` | Composed review of abstraction-architect:concept-ownership-auditor, abstraction-architect:abstraction-fit-auditor. TRIGGER WHEN: any member applies: reviewing duplicated policies, competing authorities, redundant representations and maintained derivable state across files.; reviewing repeated mechanisms, bypassed canonical implementations and abstractions that impose cross-file friction.. DO NOT TRIGGER WHEN: no member applies; missing required input remains a coverage gap. | [abstraction-architect-agent](<../../plugins/abstraction-architect/plugin.toml>) |
| Role | `abstraction-architect:concept-ownership-auditor` | Review duplicated policies, competing authorities, redundant representations and maintained derivable state across files. TRIGGER WHEN: reviewing duplicated policies, competing authorities, redundant representations and maintained derivable state across files. DO NOT TRIGGER WHEN: implementing changes or applying remediation. | [concept-ownership-auditor](<../../plugins/abstraction-architect/roles/concept-ownership-auditor.md>) |
| Role | `abstraction-architect:abstraction-fit-auditor` | Review repeated mechanisms, bypassed canonical implementations and abstractions that impose cross-file friction. TRIGGER WHEN: reviewing repeated mechanisms, bypassed canonical implementations and abstractions that impose cross-file friction. DO NOT TRIGGER WHEN: implementing changes or applying remediation. | [abstraction-fit-auditor](<../../plugins/abstraction-architect/roles/abstraction-fit-auditor.md>) |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/abstraction-architect](<../../exports/claude/plugins/abstraction-architect>) | `native` | No workflow entry points |
| copilot | [exports/copilot/plugins/abstraction-architect](<../../exports/copilot/plugins/abstraction-architect>) | `native` | No workflow entry points |
| codex | [exports/codex/plugins/abstraction-architect](<../../exports/codex/plugins/abstraction-architect>) | `adapted` | No workflow entry points |
| pi | [exports/pi/plugins/abstraction-architect](<../../exports/pi/plugins/abstraction-architect>) | `adapted` | No workflow entry points |
| opencode | [exports/opencode/plugins/abstraction-architect](<../../exports/opencode/plugins/abstraction-architect>) | `native` | No workflow entry points |

<!-- daodan:reference:end -->
