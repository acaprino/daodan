---
description: >
  Quality review of the content of any Claude Code plugin marketplace.
  TRIGGER WHEN: the user asks to review plugin, agent or skill quality, audit descriptions or trigger keywords, or evaluate activation accuracy and cross-plugin coherence.
  DO NOT TRIGGER WHEN: just validating marketplace.json structure (use /marketplace-ops:marketplace-health) or authoring new components (use /marketplace-ops:marketplace-scaffold-plugin).
argument-hint: "[plugin-name] [--all] [--fix]"
---

## Source profile preflight

Load marketplace-ops:kernel-marketplace before this procedure. Detect the target's
source model from its manifests and instructions. For daodan/v1 neutral kernels,
follow that skill's operation-specific procedure and finish there. Generated
exports and catalog entries are inspected as output, never authored as source.
The procedure below applies only to a legacy Claude marketplace with hand-authored
agents/ and commands/. It must not be applied to a neutral kernel checkout.



# Marketplace AI Review

Perform an AI-driven quality evaluation of plugin content across any Claude Code plugin marketplace.

## What this evaluates

This review goes beyond structural validation (which `/marketplace-health` handles) and analyzes the **semantic quality** of every plugin component using AI judgment.

## Procedure

### Step 1: Load marketplace data

Read `.claude-plugin/marketplace.json` at the project root to get the full plugin registry.

### Step 2: For each plugin (or the specified one), evaluate these dimensions

#### A. Plugin Description Quality (marketplace.json)

Evaluate the `description` field:
- **Clarity**: Is it immediately clear what the plugin does?
- **Trigger coverage**: Does it mention enough trigger scenarios for Claude to auto-invoke?
- **Specificity**: Does it name concrete actions, not just abstract categories?
- **Length**: Under 1024 chars, ideally under 300 for auto-load discoverability
- **Keyword coverage**: Keywords array contains the concrete domain terms users will search for

#### B. Agent Quality (for each agent in the plugin)

Read the agent `.md` file:
- **Description calibration**: Clear third-person purpose and concrete `TRIGGER WHEN` (avoid passive vagueness like "Helps with" and avoid emphasis escalation like "CRITICAL: ALWAYS invoke")
- **TRIGGER WHEN clause**: present on user-triggered agents, specific, uses concrete verbs / domain terms
- **DO NOT TRIGGER WHEN clause**: present only where a confusable sibling exists, and naming it (which other agent should handle this case instead). A clause that names none is context cost with no routing value: flag it for deletion
- **Body structure**: clear sections (ROLE, CAPABILITIES, CONVENTIONS, OUTPUT FORMAT or similar)
- **Body size**: 60-200 lines for simple agents, up to ~700 lines for complex; domain textbooks belong in a skill's `references/`
- **Tool restrictions**: minimal but sufficient (a read-only reviewer should NOT have Write/Edit; omit `tools` only when MCP or full host defaults are needed)
- **Model choice**: `inherit` by default
- **Color consistency**: matches siblings in the same plugin where appropriate

#### C. Skill Quality (for each skill in the plugin)

Read the skill `SKILL.md`:
- **Description**: clear purpose + `TRIGGER WHEN` / `DO NOT TRIGGER WHEN` checks (internal coordinator-loaded method skills may state purpose and caller concisely)
- **Body size**: under 500 lines; larger content belongs in `references/`
- **Progressive disclosure**: uses `references/` for deep content with a router table in `SKILL.md`
- **Action-oriented**: teaches what the model does not already know; avoids restating general best practices
- **Examples**: zero-shot by default for agent instructions; add reviewed input/output examples only to resolve an ambiguous format or boundary

#### D. Command Quality (for each command in the plugin)

Read the command `.md` file:
- **Frontmatter shape**: `description` and `argument-hint` as separate YAML keys (not a single concatenated string)
- **Argument hint**: accurate, shows the expected arguments
- **Body**: actionable procedure, not just marketing copy
- **Integration**: references the agent or skill that does the real work

### Step 3: Cross-plugin coherence

- Detect overlapping triggers between plugins (two agents competing for the same activation)
- Detect orphan references (agent X references skill Y that doesn't exist)
- Identify missing sibling-conflict DO NOT TRIGGER clauses when two plugins cover adjacent domains

### Step 4: Report

Write `.marketplace-review/REPORT.md` with:

```markdown
# Marketplace AI Review -- <marketplace-name> -- <date>

## Summary
- Plugins evaluated: N
- Critical issues: K
- Recommendations: M

## Per-plugin findings
### <plugin-name>
- Description score: X/5 -- <reasoning>
- Agents: ...
- Skills: ...
- Commands: ...
- Recommended fixes:
  - [CRITICAL] ...
  - [WARNING] ...

## Cross-plugin observations
- ...
```

### With --fix flag

For each recommendation, offer to apply the fix with user confirmation. Stage changes via Edit, do not auto-commit.

## Notes

- Marketplace-agnostic: works on any project with a standard Claude Code plugin layout.
- Complements (does not replace) the deterministic audit run by `/marketplace-ops:marketplace-health` and the detailed lint in `/marketplace-ops:skills-validate`.
