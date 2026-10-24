# TypeScript Type-Safety Audit

Audit type soundness and typed runtime boundaries. The coordinator prepares evidence, dispatches the declared reviewer and writes the native final report below. Canonical member roles own detection; do not copy their checklists into a second worker prompt.

Caller: `/daodan:check-health`. Senior-review supplies its own prepared scope and native format when it dispatches `typescript-development:type-safety-auditor`; do not also run this method for that assignment.

## Inputs and scope

Use the caller's target, candidate/snapshot, requirements, run directory and permissions. A project uses full scope; a path uses that directory/file scope; a caller-resolved diff uses changeset scope with both sides, staged/unstaged work, untracked paths, removals and renames. Follow implicated callers, configuration and unchanged counterparts within admitted read scope. Do not infer that a preexisting content defect was introduced by the change.

Include TypeScript modules, first-party declarations, boundary producers/consumers and the effective tsconfig closure, including extends and project references. Preserve runtime schemas and serialization evidence; compiler success alone does not prove boundary validity.

Keep a complete scoped inventory and the paths read in depth separately. Prioritize entrypoints and consequential paths, then finish the assigned checks or report the unexamined scope. Sampling or a read limit never proves full coverage. If no applicable source exists, record the inspected inventory and reason.

## Prepare evidence

Inspect relevant source and project configuration before dispatch. Collect the project-configured type check (including referenced projects) and linting when available and authorized. Use existing local tooling, preserve the actual command, exit status, candidate and output, and report unavailable tooling rather than hiding errors or treating it as a clean run. Do not install tools implicitly.

Bind supplied performance profiles, budgets, compiler/linter output and product requirements to their source and conditions. Source reasoning is not a measured runtime result. Resolve the installed provider root and assigned knowledge once; an unknown target, missing mandatory input or stale binding remains a gap.

## Step 3: Run Review Agent

Dispatch `typescript-development:type-safety-auditor` in its required isolated context through the host harness. Supply the full prepared scope, source/evidence paths, provider root, snapshot, requirements, working discipline, permissions and intermediate report path `<run>/ts-review/worker-findings.md`. Use the actual rendered role, including each canonical member; loading a role as a skill is not dispatch.

The reviewer returns its findings and a delivered or failed outcome; it does not write the final report. Record that outcome before the report phase. A failed or missing delivery leaves the review incomplete and must be reported.

Supply the native report fields below as the assignment's common review conventions, once. Findings carry severity, current file:line evidence, the required behavior or budget, causal impact, counterevidence, numeric confidence and a concrete correction. Preserve rejected candidates, coverage/gaps, assigned knowledge usage and any required member_results in the one intermediate report. No automatic violation follows merely from an absent optimization, new API, compiler flag or preferred technique.

The coordinator verifies delivery and every assigned member before consolidation. Deduplicate the same cause without hiding independent failure modes. Keep all mandatory gaps open. Scores use evidenced category judgments and explicitly mark unassessed categories; do not derive a score from file counts or API adoption alone.

## Step 4: Generate Markdown Report

After the agent completes, create the `<run>/ts-review/` directory and write `report.md`.

Order findings by severity, then file name.

**Output file:** `<run>/ts-review/report.md`

```markdown
# TypeScript Type-Safety Review: [date]

[Mode, scoped inventory, paths read in depth, runtime paths exercised and remaining gaps]

## Ground Truth

[tsc error count and eslint summary, or "Compiler/linter unavailable: static source analysis only; unverified checks and impact listed below."]

## Scores

| Category | Score |
|----------|-------|
| Any Hygiene | X/10 |
| Cast Discipline | X/10 |
| Config Strictness | X/10 |
| Boundary Validation | X/10 |
| **Overall** | **X/10** |

Critical: X | High: X | Medium: X | Low: X

## Files Audited

- `tsconfig.json`, `api/client.ts`, ...

---

## Critical & High Issues

### [rule-id]

#### `file.ts:42` [issue title]
- **Severity**: Critical
- **Confidence**: 90
- **Issue**: [what breaks at runtime]
- **Fix**: [fix instruction with code]
- [ ] Fixed

## Medium & Low Issues

[same structure, compact]

## Positives

- [what is done well]
```

Present the report summary to the user with the top findings and the report path.
