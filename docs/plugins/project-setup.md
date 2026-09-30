# Project Setup Plugin

> Keep your CLAUDE.md accurate and effective. Audits every claim against your actual codebase, detects outdated information, and generates tailored configuration through interactive questionnaires.

## Agents

### `claude-md-auditor`

Audits `CLAUDE.md` files by verifying ground truth, detecting obsolete information, and checking alignment with best practices.

| | |
|---|---|
| **Invoke** | Agent reference |
| **Use for** | CLAUDE.md auditing, creation, verification, improvement |

**Core capabilities:**
- **Ground Truth Verification**: validates every claim against the actual codebase
- **Obsolescence Detection**: finds outdated file paths, dependencies, commands
- **Best Practices Compliance**: checks proportional sizing, the character cap, instruction economy, progressive disclosure
- **X-ray ingestion**: on both create and maintain, detects `.codebase-xray/` output from a previous `/codebase-xray:analyze` run (`01-structure.md` and `02-interfaces.md`) and offers to use it as the ground-truth baseline, with 3-5 spot-checks against current code; if the spot-checks show the X-ray is stale, it falls back to its own bottom-up analysis. Findings derived from it cite the `.codebase-xray/<file>:<section>` anchor
- **Duplication detection (Phase 4b)**: counts every file path, pointer and external resource across the document and flags reference outliers (one path appearing several times while its peers appear once), conceptual restatements, and duplicates kept only for weak reasons. Each candidate is a per-finding question showing all occurrences; a merge is treated as a deletion and needs explicit approval. The same pass runs on a new draft before it is shown
- **Working Principles enforcement**: every generated CLAUDE.md includes the canonical `## Working Principles` block inline (5 numbered principles with sub-bullets, distilled from Karpathy's guidelines plus a locally authored fifth principle); audits flag a missing or gutted block as a High-priority finding and offer to insert it
- **Test-Suite Rules (conditional)**: when the project has a test suite, generated CLAUDE.md files also carry the canonical `## Test-Suite Rules` block (7 binding rules condensed from the `testing` plugin's hygiene knowledge base: search before writing, mirrored placement, explicit layers, behavior over implementation, no skip markers, assertion integrity, delete tests with the feature); offered on create (default yes), verified on audit, never flagged in projects without tests
- **Tailored Creation**: generates CLAUDE.md based on your preferences
- **Guided Improvement**: surfaces every drift as its own question, with "leave unchanged" as the default for anything unanswered

**Enforces these best practices:**
- Length proportional to complexity: simple projects <100 lines, medium <300, complex or monorepo 500+. Completeness over brevity
- A hard 40,000-character cap (Claude Code's performance warning threshold), target <35k. Over 40k is a Critical audit finding and 35k-40k is High; the fix is extracting sections to `docs/` behind thin `Read docs/<topic>.md` pointers
- Instruction economy (~150-200 instructions, a soft guideline rather than a hard cap)
- Progressive disclosure (reference docs, don't embed)
- Pointers over copies (reference files, not code)
- An evergreen project-structure section: top-level layout, repeating structural patterns and the role of each category, with file-level notes only where a name is ambiguous or the file is a key entry point. An exhaustive file-by-file tree is flagged as a Medium consolidation candidate, never collapsed without asking
- No transient state (task lists, "currently" notes, open branches, one-run numbers): flagged as Critical when already stale, High when still accurate but time-bound

## Commands

### `/project-setup:create-claude-md`

Create a new `CLAUDE.md` file through an interactive questionnaire about your workflow and preferences. Offers existing `.codebase-xray/` output as the technical backbone before analyzing the codebase, and runs the Phase 4b duplication pass on the draft before showing it.

### `/project-setup:maintain-claude-md`

Audit and optionally improve your existing `CLAUDE.md` file with ground truth verification. Offers existing `.codebase-xray/` output as the audit baseline first.

**Two workflows:**
1. **Audit-only**: Review findings, no changes applied
2. **Audit + improvements**: Fix issues with guided prioritization

**How changes are decided:**
- Every drift is asked about as its own question, with concrete options (fix as proposed, keep verbatim, extract to `docs/<topic>.md` with a pointer, skip). Nothing is batch-applied, not even Critical fixes, and a finding you have not answered is left unchanged
- Existing content is preserved unless cross-verification proves it false or obsolete. Length, perceived redundancy and style are not grounds for removal; extraction to `docs/` with a pointer is the way to shrink the file
- The canonical `## Working Principles` block is always checked and backfilled when missing or incomplete (High)

---

**Related:** [marketplace-ops](marketplace-ops.md) (plugin management and validation)
