---
name: dependency-audit
description: >
  Evidence-first dependency audit method: per-ecosystem tool matrix, license obligation model and supply-chain signal catalog.
  TRIGGER WHEN: auditing dependencies for CVEs, license obligations, outdated packages or supply-chain risk; the audit method in references/audit.md is run by /daodan:check-health and by the dependency perspective of /daodan:review-changes and /daodan:review-branch.
  DO NOT TRIGGER WHEN: dead-code or unused-dependency removal (use senior-review:application-cleanup-method or typescript-development:knip), or code-level security review (use senior-review:security-auditor).
---

# Dependency Audit Knowledge Base

Method for auditing third-party dependencies without inventing facts. `references/audit.md` orchestrates the audit; the other references hold the depth, loaded on demand.

## Core principles

1. **Tool-first.** The audit runs the ecosystem's own tooling and reads registries and advisory databases (OSV, GitHub Advisories, RustSec, PyPA). It never re-implements a scanner in pseudo-code and never guesses what a tool would have said.
2. **Evidence tiers.** Every reported fact is `TOOL-REPORTED`, `INFERRED` (with the derivation stated), or `UNKNOWN` (with what would resolve it). Fabricated quantities of any kind are forbidden: no estimated hours, no invented percentages, no dollar figures.
3. **Non-destructive remediation.** Never `--force`, never unapproved major-version upgrades, never lockfile regeneration, never dependency replacement without first presenting the proposed change, its compatibility risk, and a test/rollback plan.
4. **Licenses are obligations, not a matrix.** License analysis asks what obligations a dependency's license imposes given how the project combines and distributes it. Binary "X is incompatible with Y" tables are wrong often enough to be banned.
5. **Honest coverage.** Missing tools and unreachable registries are reported as gaps, with install commands, instead of being papered over.

## References

| File | Load when |
|---|---|
| `references/audit.md` | Running the audit for a caller: target forms, ecosystem, depth and license decisions, the update authorization, the workflow steps and the report format |
| `references/ecosystems.md` | Selecting or running audit / outdated / license tooling for any ecosystem, or parsing its output |
| `references/license-analysis.md` | Writing any license finding, classifying an SPDX identifier, or answering a copyleft question |
| `references/supply-chain.md` | Evaluating supply-chain risk signals or reviewing a dependency diff for tampering |
