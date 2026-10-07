# Abstraction Architect Plugin

> Structural entropy auditor: finds where the same concept is represented, owned, computed or implemented more than once, and what it costs when that concept changes. Seven dimensions over two evidence tracks: a knowledge track judged by semantic identity and ownership, and a form track judged by recurrence. Report-only, grounded in canonical theory (Metz, Beck, Fowler, Gross, North, DDD).

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Prerequisites

The `codebase-xray` plugin is a hard dependency: the global audit consumes `.codebase-xray/` output and `/abstraction-architect:audit` auto-launches X-ray when that output is missing. Diff mode needs only whatever X-ray output is on disk and runs on the concept index plus Glob and Grep when there is none, at reduced confidence declared in its Gaps section.

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

Adversarial auditor with two modes. Global mode censuses the whole codebase from `.codebase-xray/` plus its own discovery pass. Diff mode anchors on the changed files and asks whether the change introduces or aggravates structural entropy relative to the codebase that already exists. Its governing rules: precision over recall governs what is reported, not what is searched; index entries nominate search targets, current source code proves findings.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Glob, Grep, Bash |
| **Use for** | Structural entropy audits, "who canonically owns this fact" questions, "did what I just wrote already exist" checks on changed code |

**Invocation:**
```
Use the abstraction-architect-agent agent to audit [path] for structural entropy
```
Also spawned by `/abstraction-architect:audit` and, in diff mode, as the structural entropy dimension of `/senior-review:team-review` and `/senior-review:code-review`.

**Key behaviors (global mode):**
- Reads `01-structure.md`, `02-interfaces.md`, `03-flows.md`, `04-semantics.md`, plus `08-interconnect-map.md` when `/codebase-xray:team-analyze` produced it (that file enables the bounded-context check; without it knowledge-track findings carry `Bounded-context exception: unverified`)
- Builds a seed map from the X-ray, extracts entity and behavioural concepts, then runs four search families per concept: by name and near-synonym, by literal, by call, by shape of decision. The seed map seeds the census and never bounds it
- Builds a Concept Evidence Index (representations with roles, writers, consumers, canonical owner status), then tests every concept with more than one representation against its dimension gate and the lenses
- Re-reads every cited representation on current source before promoting a finding
- Writes the concept index to `.abstraction-architect/concept-index.json` (refusing to overwrite an index recorded with a broader scope) and the report to `.abstraction-architect/findings.md`

**Key behaviors (diff mode):**
- Extracts two kinds of changed unit: structural units (new functions, methods, classes, modules, constant tables, inline blocks longer than roughly five lines) and semantic units (rules and policies, predicates and thresholds, persisted fields and state, models, DTOs, types and enums, mappings, configuration and defaults, formulas). A threshold moved from 1000 to 1500 is a semantic unit with no structural unit at all
- Checks concept index freshness with `scripts/concept_index.py`, revalidates the dirty concepts on current source, and works through every changed file the index does not claim, because that is where a diff introduces a new concept
- Asks each of D1 to D7 as "introduced or aggravated by this change" (does this diff add another representation of an existing policy, create a second authority over an existing fact, store something already derivable, become the third occurrence, reimplement something already available, worsen abstraction friction)
- Never restricts the search to the changed files: what it looks for is by definition outside the diff
- Needs only `01-structure.md` and `02-interfaces.md` (lite X-ray is enough)
- Writes the report to `.abstraction-architect/findings-diff.md`, or wherever the calling review pipeline directs it. **Diff mode never writes the concept index**; new concepts and index contradictions go in Gaps for the next global audit

**Report sections (both modes):** A competing sources of truth (D2), B duplicated or derivable state (D4), C redundant representation (D3), D duplicated domain knowledge (D1), E prior art available (D6), F missed unification (D5), G abstraction fitness (D7), H second occurrences noted but not flagged (form track only, exempt from the severity floor), I confidence and gaps. Each finding names its dimension, its catalogued pattern or `uncatalogued`, tight line-range evidence with roles, the L1 count, a one-sentence suggested direction, and an evidence-track block.

## Skills

### `abstraction-architect`

Knowledge base for structural entropy. Covers the two evidence tracks, the seven dimensions and four lenses, the census method, the concept index protocol, severity and remediation framing, 18 essential-duplication patterns (P1 to P12 infrastructural, P13 to P18 domain-facing), 12 wrong-abstraction patterns (A1 to A12), the canonical theory, and a verified reading list. The pattern catalogs are discovery aids, never admission gates: a candidate that passes its gate and matches no pattern is still a finding.

References, loaded on demand by the agent (`dimensions.md` first): `dimensions.md`, `evidence-tracks.md`, `concept-census.md`, `concept-index-protocol.md`, `decision-frame.md`, `unification-patterns.md`, `anti-patterns.md`, `scope-boundaries.md`, `theory.md`, `further-reading.md`. The skill also ships `scripts/concept_index.py`, which reports concept index freshness.

## Commands

### `/abstraction-architect:audit`

```
/abstraction-architect:audit                                    # audit current directory
/abstraction-architect:audit src/services                       # audit a subpath
/abstraction-architect:audit --severity-floor high              # only high-severity findings
/abstraction-architect:audit --focus knowledge                  # D1-D4 only
/abstraction-architect:audit --focus D2                         # competing sources of truth only
/abstraction-architect:audit --diff                             # does my change add entropy?
/abstraction-architect:audit --diff origin/master               # same, against an explicit base ref
/abstraction-architect:audit --rebuild-index                    # ignore any existing concept index
```

| Argument | Effect |
|------|--------|
| `[path]` | Codebase root. Default: current working directory |
| `--diff [<base-ref>]` | Diff-anchored mode: the seven questions as "introduced or aggravated by this change". Skips the X-ray auto-launch. Base ref defaults to the merge base with the default branch, falling back to `HEAD` for uncommitted work. Requires a git repository |
| `--scope <subpath>` | Limit findings to a subtree. The X-ray still runs on the full codebase |
| `--severity-floor low\|medium\|high` | Drop findings below this severity (default `medium`) |
| `--focus all\|knowledge\|form\|D1..D7` | Restrict to a dimension subset (default `all`). `knowledge` is D1 to D4, `form` is D5 to D7, or name a single dimension |
| `--no-index` | Do not read or write `concept-index.json` |
| `--rebuild-index` | Global mode only: ignore any existing index and census the codebase from scratch |

Without `--diff`, the command checks for `.codebase-xray/` and auto-launches `/codebase-xray:analyze` when it is missing or incomplete. Unless `--no-index`, it then runs the freshness script and prints the concept index state before spawning the agent, so a stale index is visible rather than silent:

```
Concept index: delta-stale (baseline a13fe2, HEAD 92ac10, 4 concepts to revalidate)
```

The states are `fresh` (indexed tree equals the current tree and the worktree is clean within scope), `delta-stale` (the normal case: touched concepts are marked dirty and revalidated) and `unusable` (the audit proceeds without the index and declares the reduced coverage in Gaps). In global mode the agent rewrites `.abstraction-architect/concept-index.json`; diff mode never does. Report-only: no file outside `.abstraction-architect/` is ever edited, and the suggested direction in each finding is one sentence, not a refactoring plan.

## Ecosystem integration

- **`/senior-review:team-review`** runs the agent in diff mode as its structural entropy dimension whenever the review target resolves to a diff that adds at least one function, method, class, module, constant table or block longer than roughly five lines. `senior-review` hard-depends on this plugin, so the only thing conditional about the dimension is that signal. Plain file/directory targets have no diff to anchor on and point here instead. The reviewer reads the concept index when one exists and never writes it.
- **`/senior-review:code-review`** runs it as Agent J (Structural Entropy Review) on the same signal.
- **`senior-review:code-auditor`** keeps the smells fully visible inside one file (god functions, a leaky signature, an interface with one implementation); this agent owns the cross-file question. The dedup boundary is declared on both sides.
- **`/codebase-xray:team-analyze`** adds `08-interconnect-map.md` to the X-ray output, which enables the bounded-context check in global mode.

**Related:** [codebase-xray](codebase-xray.md) (produces the `.codebase-xray/` input) | [senior-review](senior-review.md) (`/senior-review:team-review` structural entropy dimension, code-review Agent J, code-auditor dedup boundary) | [clean-code](clean-code.md) (readability cleanup, different concern)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `4.0.0`. **Source:** [plugin.toml](<../../plugins/abstraction-architect/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | [codebase-xray](<codebase-xray.md>) |
| Direct external | None |
| Local closure (2) | [abstraction-architect](<abstraction-architect.md>), [codebase-xray](<codebase-xray.md>) |
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
| Skill | `abstraction-architect:abstraction-architect` | Knowledge base for structural entropy: the cost of change when one concept lives in many places. TRIGGER WHEN: the user asks "should I extract this", "who owns this rule", "is this DRY enough", "is this the wrong abstraction"; centralizing, inlining or removing a layer; auditing for duplicated domain knowledge, competing sources of truth, redundant models or derivable state stored anyway; loaded under /abstraction-architect:audit or the /senior-review:team-review abstraction dimension. DO NOT TRIGGER WHEN: the concern is formatting (use clean-code:clean-code), Python refactoring (use python-development:python-refactor-method), dead-code removal (use /senior-review:code-review --commit), security (use senior-review:security-auditor), contract drift (use senior-review:api-contract-auditor), or cycles, cohesion and single-file patterns (use senior-review:code-auditor and senior-review:chicken-egg-detector). | [abstraction-architect](<../../plugins/abstraction-architect/skills/abstraction-architect/SKILL.md>) |
| Role | `abstraction-architect:abstraction-architect-agent` | Adversarial auditor for structural entropy, report-only. Global mode censuses the whole codebase from .codebase-xray/ plus its own discovery pass; diff mode anchors on the changed files. TRIGGER WHEN: spawned by /abstraction-architect:audit, or as the abstraction dimension of /senior-review:team-review or /senior-review:code-review; the user asks who canonically owns a fact, policy or state, asks about missed unification or wrong abstractions, or asks whether what they just wrote already exists elsewhere. DO NOT TRIGGER WHEN: the task is implementation, security review (use senior-review:security-auditor), distributed-flow tracing (use senior-review:distributed-flow-auditor), dead-code removal (use senior-review:cleanup-auditor), or cycles, cohesion and single-file patterns (use senior-review:code-auditor and senior-review:chicken-egg-detector). | [abstraction-architect-agent](<../../plugins/abstraction-architect/roles/abstraction-architect-agent.md>) |
| Workflow | `abstraction-architect:audit` | Audit a codebase for structural entropy, or with --diff check whether a change introduces new entropy. Report-only; auto-launches /codebase-xray:analyze when .codebase-xray/ is missing. TRIGGER WHEN: the user asks to audit duplicated knowledge, competing sources of truth, redundant models, derivable state, or wrong abstractions. | [audit](<../../plugins/abstraction-architect/workflows/audit.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `abstraction-architect:audit`

**Arguments:** <code>[path] [--diff [&lt;base-ref&gt;]] [--scope &lt;subpath&gt;] [--severity-floor low&#124;medium&#124;high] [--focus all&#124;knowledge&#124;form&#124;D1..D7] [--no-index] [--rebuild-index]</code>

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `audit-completed` |
| Artifacts | `audit-report` |
| Schemas | None declared |
| Declared workers | `abstraction-architect/abstraction-architect-agent` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [audit.toml](<../../plugins/abstraction-architect/workflows/audit.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `review` | `scope` | `abstraction-architect-agent` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/abstraction-architect](<../../exports/claude/plugins/abstraction-architect>) | `native` | `audit: native-team` |
| copilot | [exports/copilot/plugins/abstraction-architect](<../../exports/copilot/plugins/abstraction-architect>) | `native` | `audit: parallel-subagents` |
| codex | [exports/codex/plugins/abstraction-architect](<../../exports/codex/plugins/abstraction-architect>) | `adapted` | `audit: parallel-subagents` |
| pi | [exports/pi/plugins/abstraction-architect](<../../exports/pi/plugins/abstraction-architect>) | `adapted` | `audit: parallel-subagents` |
| opencode | [exports/opencode/plugins/abstraction-architect](<../../exports/opencode/plugins/abstraction-architect>) | `native` | `audit: parallel-subagents` |

<!-- daodan:reference:end -->
