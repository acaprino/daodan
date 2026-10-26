---
name: marketplace-audit
description: >
  Validate structural integrity, dependencies, naming, colors and doc counts of a plugin marketplace.
  TRIGGER WHEN: verifying marketplace.json integrity, finding orphan components, checking dependencies or doc count drift.
  DO NOT TRIGGER WHEN: content quality review (use marketplace-review) or scaffolding (use skills-creator).
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

## Source profile preflight

Load marketplace-ops:kernel-marketplace before this procedure. Detect the target's
source model from its manifests and instructions. For daodan/v1 neutral kernels,
follow that skill's operation-specific procedure and finish there. Generated
exports and catalog entries are inspected as output, never authored as source.
The procedure below applies only to a legacy Claude marketplace with hand-authored
agents/ and commands/. It must not be applied to a neutral kernel checkout.



# Marketplace Audit

Run a comprehensive structural validation of any Claude Code plugin marketplace. Works against any project that follows the standard `.claude-plugin/marketplace.json` + `plugins/<name>/` layout.

## Audit steps

### Step 1: Run the validation script

Execute the audit script to get a machine-readable report:

```bash
# Validate only
python "<plugin-root>/skills/marketplace-audit/scripts/audit_marketplace.py"

# Validate and auto-fix color issues (invalid, missing, disharmonious)
python "<plugin-root>/skills/marketplace-audit/scripts/audit_marketplace.py" --fix
```

The script resolves the target project root by walking up from the script location, or respects a `--project-root <path>` flag if invoking it from a different marketplace than where the plugin is installed.

### Step 2: Review findings

The script checks:

1. **File existence** -- every path in marketplace.json `agents` / `skills` / `commands` arrays resolves to a real file or directory
2. **Orphaned files** -- agent `.md` files, skill directories, or command `.md` files on disk not registered in any plugin
3. **Frontmatter validation**
   - Agents: must have `name`, `description`, `model`, `color`
   - Skills: must have `name`, `description`
   - Commands: must have `description`
4. **Color consistency and harmony**
   - All agents within a plugin should use the same color
   - Warn when a single color is overused across too many plugins (threshold configurable)
   - Report color distribution across all plugins
   - Valid colors: red, blue, green, yellow, purple, orange, pink, cyan
   - Use `--fix` to auto-correct invalid or missing colors
5. **Naming conventions**
   - All names are kebab-case
   - Agent filename matches frontmatter `name` field
   - Plugin directory name matches marketplace.json `name` field
   - Skill directory name matches frontmatter `name` field
   - Workflow command output directories match command filename (e.g., `feature-e2e.md` typically writes to `.feature-e2e/`)
   - No naming collisions between commands in different plugins
   - No dash-aside constructs (`—`, `--`, or ` - ` wrapping parenthetical clauses; rewrite with colons, parentheses, or separate sentences)
6. **Cross-reference consistency (project-specific, best-effort)**
   - If a git remote is configured, suggest that the marketplace `name` align with the repo name (warning only)
   - If a `CLAUDE.md` is present at the project root, suggest that its project header match the marketplace name (warning only)
   - These are advisory -- different marketplace maintainers have different conventions
7. **Marketplace.json schema**
   - Every plugin has: `name`, `source`, `description`, `version`, `author`, `license`, `keywords`, `category`, `strict`
   - No duplicate plugin names
   - Duplicate keywords across plugins (warning only -- may be intentional)
8. **Version sanity**
   - All versions are valid semver (`MAJOR.MINOR.PATCH`)
   - `metadata.version` is present at the root
9. **Dependency resolution and acyclicity**
   - An unqualified `dependencies` entry must name a plugin in this marketplace
   - A cross-marketplace entry must use the qualified `name@marketplace` form, which is checked for shape only, since it is unresolvable from here by design. A bare name silently resolves against the local marketplace and fails the whole plugin load, so the qualified form is mandatory, not stylistic
   - The hard-dependency graph must be acyclic. Optional dependencies are excluded from the cycle walk on purpose: they exist precisely to express an edge that would otherwise close a loop
   - External marketplaces are reported as info, grouped by which plugins require them
10. **Documentation count drift**
   - Per-plugin agent, skill, and command counts restated in `docs/README.md`'s index table and in `README.md`'s plugin table must match what marketplace.json declares
   - Rows naming a plugin that is not registered, and registered plugins missing from a table that already lists the others, are both flagged
   - Every `N plugins` phrase in `README.md`, `docs/README.md`, `CLAUDE.md`, and the marketplace `metadata.description` must match the real plugin count
   - This is the check that catches the most common silent decay: adding or removing one file leaves every table that counted it stale, and nothing else fails. Each sub-check is skipped when the file or the table is absent, so it stays valid for marketplaces with a different documentation layout

### Step 3: Fix issues

Address findings by severity:

- **CRITICAL**: Missing referenced files, broken paths, missing required frontmatter fields, duplicate plugin names
- **WARNING**: Orphaned files, naming mismatches, overlapping keywords, color inconsistencies, git/CLAUDE.md alignment
- **INFO**: Suggestions for improvement, consolidation opportunities

### Step 4: Evaluate color harmony

After the script passes, review the color distribution and evaluate semantic harmony:

1. Read each plugin's description and category from marketplace.json
2. Consider domain: similar domains should have visually related colors; distinct domains should contrast
3. Guiding principles:
   - Warm colors (red, orange, yellow, pink) for creative / outward-facing plugins
   - Cool colors (blue, cyan, purple) for analytical / development plugins
   - Neutral (green) for tooling / infrastructure
4. If colors feel disharmonious, propose a new assignment with reasoning and apply after user confirmation

### Step 5: Re-validate

Run the script again after fixes to confirm a clean audit.

## Notes for marketplace maintainers

- This skill is marketplace-agnostic. It assumes the standard Claude Code plugin layout (`.claude-plugin/marketplace.json` + `plugins/<name>/`) but makes no assumption about which plugins, authors, or upstream sources are specific to your marketplace.
- Plugin categories, default author, upstream sources, and any project-specific conventions should be documented in your `CLAUDE.md` at the project root. The script and this skill respect those conventions but do not enforce a particular taxonomy.
