# Codebase Mapper Plugin

> Generate a human-readable guide for any unfamiliar codebase. The pipeline explores the project, profiles it (type, audience, register) for a quick user confirmation, builds a structured interconnect map, writes the documents in parallel and runs a cross-reference review. It produces a plain-language executive summary, 10 numbered narrative documents with Mermaid diagrams, a glossary and an `INDEX.md` entry point.

## Prerequisites

Four hard dependencies, all installed with this plugin:

- `agent-teams@claude-code-workflows` (upstream `wshobson/agents`): coordination skills for `/codebase-mapper:team-codebase-map`
- `codebase-xray`: ships the `semantic-interconnect-mapper` agent that builds the interconnect map
- `text-humanizer`: the AI trace removal pass in `/codebase-mapper:docs-create` and `/codebase-mapper:humanize-docs`
- `senior-review`: the `defect-taxonomy` skill's `logic-integrity.md` reference, which `guide-reviewer` uses for documentation-reality drift detection

## How it works

The `/codebase-mapper:map-codebase` command orchestrates the pipeline:

1. **Phase 1 (Explore):** The `codebase-explorer` agent scans the project (README, configs, entry points, directory structure) and writes a context brief to `.codebase-map/_internal/context-brief.md`, opening with a `## Project Profile` section (project type and domain, primary audience, register, scope).
2. **Phase 1.5 (Confirm Project Profile):** The command surfaces the profile, including anything the explorer marked low-confidence, and asks one question: confirm or adjust. Adjustments are written back into the context brief so the writers read the confirmed profile. This is the only interactive checkpoint.
3. **Phase 1b (Interconnect Map):** The `codebase-xray:semantic-interconnect-mapper` agent reads the context brief and produces `.codebase-map/_internal/interconnect.md`: a structured map of contracts, invariants, domain rules, assumptions, integration hot-spots, and call graph. Writers cite these structured facts instead of paraphrasing code. If the run itself fails to produce the file, the pipeline logs a warning and continues in degraded mode with writers using only the context brief.
4. **Phase 2 (Write):** Six writer agents are spawned simultaneously, each producing its documents from the context brief and (when present) the interconnect map, calibrated to the confirmed profile per the skill's `audience-adaptation.md`.
5. **Phase 3 (Review):** The `guide-reviewer` agent reviews all documents for consistency, adds cross-references, detects documentation-reality drift against the interconnect map's invariants and domain rules, checks register consistency and the plain-language layer, writes `11-glossary.md`, and produces `INDEX.md` with per-audience reading paths.

**Output directory:** `.codebase-map/` in the project root, containing `00-executive-summary.md`, the numbered documents `01` to `10`, `11-glossary.md` and `INDEX.md`. Internal artifacts (context brief, interconnect map) live in `.codebase-map/_internal/`.

**Target audience:** whoever the confirmed Project Profile names; a smart colleague on their first day when no profile exists.

---

## Agents

### Phase 1: Discovery

#### `codebase-explorer`

Explores an unfamiliar project to build a context brief, including the Project Profile, for the writer agents.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Bash, Glob, Grep |
| **Produces** | `.codebase-map/_internal/context-brief.md` |

---

### Phase 2: Writers (run in parallel)

| Agent | Model | Produces | Content |
|-------|-------|----------|---------|
| `overview-writer` | `inherit` | `00-executive-summary.md`, `01-overview.md`, `02-features.md` | Plain-language summary for anyone, project overview with mindmap and scope, feature catalog |
| `tech-writer` | `inherit` | `03-tech-stack.md`, `04-architecture.md` | Technologies, dependencies, architectural layers with component diagrams |
| `flow-writer` | `inherit` | `05-workflows.md`, `06-data-model.md` | User/system workflows with flowcharts, data structures with ER diagrams |
| `onboarding-writer` | `inherit` | `07-getting-started.md`, `08-open-questions.md` | Developer onboarding steps, knowledge gaps |
| `ops-writer` | `inherit` | `09-project-anatomy.md` | Config files, env vars, startup scripts, directory tree |
| `config-writer` | `inherit` | `10-configuration-guide.md` | Environment setup, configuration scenarios, troubleshooting |

All writer agents use the tools: Read, Write, Glob, Grep.

---

### Phase 3: Review

#### `guide-reviewer`

Reviews all generated documents for terminology consistency, adds cross-references, unifies tone, validates Mermaid syntax, and flags gaps and contradictions. It also verifies that the register matches the Project Profile across all documents, that the executive summary and glossary serve a non-technical reader, and flags documentation-reality drift as a known-inconsistency note plus an item in `08-open-questions.md`.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Edit, Glob, Grep |
| **Produces** | `11-glossary.md`, `INDEX.md` (navigable summary plus per-audience reading paths: a non-technical path starting at `00` and `11`, then developer paths) |

---

## Skills

### `codebase-mapper`

Knowledge base providing writing guidelines, tone rules, audience adaptation and diagram conventions for all codebase-mapper agents. References: `writing-guidelines.md`, `audience-adaptation.md`, `diagram-patterns.md`.

| | |
|---|---|
| **Invoke** | All codebase-mapper agents reference this automatically |
| **Use for** | Writing style, register calibration, Mermaid diagram conventions, output structure rules |

---

## Commands

### `/codebase-mapper:map-codebase`

Generate a human-readable codebase guide.

```
/codebase-mapper:map-codebase                   # map current directory
/codebase-mapper:map-codebase ../other-project  # map a different project
```

**Pre-flight:** Checks for existing `.codebase-map/` directory and asks before overwriting.

**Output:** `00-executive-summary.md`, `01` to `10`, `11-glossary.md` and an `INDEX.md` entry point in `.codebase-map/`.

---

## Standalone Documentation Agents

### `documentation-engineer`

Creates accurate technical documentation by analyzing existing code first. Uses bottom-up analysis with the shared writing guidelines.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Edit, Glob, Grep, WebFetch, WebSearch |
| **Use for** | API docs, architecture docs, tutorials, documentation management |

---

### `doc-humanizer`

Rewrites existing documentation to follow human-centered writing guidelines. Transforms dense, AI-style docs into clear, scannable content.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Write, Edit, Glob, Grep |
| **Use for** | Improving readability of existing docs without changing content |

---

## Additional Commands

### `/codebase-mapper:docs-create`

Analyze code bottom-up and generate documentation on one dimension or many. The 20 dimensions are grouped into surface (`--interfaces`, `--config`, `--integrations`), internals (`--architecture`, `--data-model`, `--data-flows`, `--state-machines`, `--dependencies`, `--concurrency`, `--glossary`), operations (`--auth`, `--errors`, `--observability`, `--deployment`), process (`--build-release`, `--testing`, `--migrations`), cross-cutting (`--performance`, `--compliance`) and targeted (`--component`). Several dimensions combine into one document with a section each; `--full` runs them all.

```
/codebase-mapper:docs-create src/api --interfaces
/codebase-mapper:docs-create UserService --component
/codebase-mapper:docs-create --integrations --auth
/codebase-mapper:docs-create --full --output docs/technical.md
```

Other flags: `--scope <dim1,dim2,...>`, `--format markdown|html`, `--output <path>` (default `docs/`), `--audience technical|general|mixed` (inferred from the source when omitted).

**Flow:** analyzes the target, presents a documentation plan and waits for confirmation, has `documentation-engineer` generate the document (every claim cited as `**Source:** path/file.ext:line`, `[NEEDS VERIFICATION]` where the code is unclear), runs a `text-humanizer` pass to remove AI writing traces, then offers to write, preview or revise.

---

### `/codebase-mapper:docs-maintain`

Audit and refactor existing documentation for accuracy and completeness. The audit runs a per-dimension drift check against the code, reporting added, removed, renamed and retyped items with citations to the source of truth, then builds a refactoring plan and asks before executing it.

```
/codebase-mapper:docs-maintain                                        # full workflow, all dimensions
/codebase-mapper:docs-maintain docs/                                  # only the docs/ folder
/codebase-mapper:docs-maintain --audit-only                           # report only, no changes
/codebase-mapper:docs-maintain --scope interfaces,integrations,auth   # drift on selected dimensions
```

| Flag | Effect |
|------|--------|
| `--audit-only` | Audit report only, no plan and no changes |
| `--plan-only` | Audit plus refactoring plan, no execution |
| `--merge-duplicates` | Focus on identifying and merging duplicate content |
| `--scope <dim,...>` | Restrict the drift audit to the named dimensions (default: all) |

---

### `/codebase-mapper:humanize-docs`

Rewrite existing documentation for readability: strips AI-style density and applies progressive disclosure. Confirms scope, has `doc-humanizer` restructure the content, then ends with a `text-humanizer` pass to catch remaining AI writing patterns in the prose.

```
/codebase-mapper:humanize-docs docs/
```

---

### `/codebase-mapper:team-codebase-map`

Agent-team variant of the mapping pipeline, with the same phases and the same document set as `/codebase-mapper:map-codebase`. Both spawn the six writers at once; here they run as a team with task tracking, capped with `--writers N`.

**Prerequisites:** the `agent-teams:task-coordination-strategies` and `agent-teams:team-communication-protocols` skills from `agent-teams@claude-code-workflows` (a hard dependency of this plugin; install `/plugin marketplace add wshobson/agents`, then `/plugin install agent-teams@claude-code-workflows`). Teammate spawning is an experimental Claude Code feature that also requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; if teammate spawning is unavailable in the session, the command stops and tells the user to enable the flag and restart.

| | |
|---|---|
| **Invoke** | `/codebase-mapper:team-codebase-map [target-path] [--skip-review] [--writers N]` |

**Pipeline:**

1. **Explore** (sequential): `codebase-explorer` builds `.codebase-map/_internal/context-brief.md`, opening with the `## Project Profile` section.
2. **Confirm Project Profile** (sequential): the same one-question checkpoint as `/codebase-mapper:map-codebase` Phase 1.5; adjustments are written back into the context brief before the writers run.
3. **Interconnect map** (sequential): `codebase-xray:semantic-interconnect-mapper` reads the context brief and produces `.codebase-map/_internal/interconnect.md` (contracts, invariants, domain rules, assumptions, integration hot-spots, call graph). If the run fails to produce the file, writers continue with only the context brief and a warning is logged.
4. **Write** (parallel, up to 6 writers at once): `overview-writer` (including `00-executive-summary.md`), `tech-writer`, `flow-writer`, `onboarding-writer`, `ops-writer`, `config-writer`, each calibrated to the confirmed profile. `tech-writer`, `flow-writer`, and `ops-writer` additionally cite the interconnect map's structured facts instead of paraphrasing code.
5. **Review** (sequential, skipped with `--skip-review`): `guide-reviewer` checks documents `00` to `10` for consistency, detects documentation-reality drift against the interconnect map using `senior-review:defect-taxonomy`'s `logic-integrity.md`, checks register consistency and the plain-language layer, writes `11-glossary.md`, and produces `INDEX.md` with per-audience reading paths.

```
/codebase-mapper:team-codebase-map                  # map the entire current project, 6 parallel writers
/codebase-mapper:team-codebase-map src/auth          # map a subdirectory
/codebase-mapper:team-codebase-map . --writers 3     # cap parallel writers
```

**Output:** the same set as `/codebase-mapper:map-codebase`: `00-executive-summary.md`, `01` to `10`, `11-glossary.md` and `INDEX.md`. The one team-specific difference is `--skip-review`: the reviewer writes `11-glossary.md` and `INDEX.md`, so a skipped review produces neither.

---

**Related:** [codebase-xray](codebase-xray.md) (structural analysis)
