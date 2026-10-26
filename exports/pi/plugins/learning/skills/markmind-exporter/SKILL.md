---
name: markmind-exporter
description: >
  Render a JSON outline into a drop-in vault file for the Obsidian plugin.
  TRIGGER WHEN: the user says 'markmind' or needs MarkMind Rich output from a mindmap structure,
  typically one produced by generate-mindmap.
  DO NOT TRIGGER WHEN: the user wants an interactive HTML mindmap (use forcegraph-exporter).
---

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
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# MarkMind Exporter

Render a mindmap JSON outline into Obsidian MarkMind Rich format. This skill takes a pre-built mindmap JSON structure (produced by `generate-mindmap` or any other source) and converts it into a `.md` file the user can drop directly into their Obsidian vault and open with the MarkMind plugin.

## Input

A JSON file with the standard mindmap outline format:

```json
{
  "root": "🎯 Central Theme",
  "branches": [
    {
      "text": "🔴 Branch One",
      "color": "#ff6b6b",
      "children": [
        {
          "text": "⚙️ Sub-concept A",
          "children": [
            { "text": "Detail 1" },
            { "text": "Detail 2" }
          ]
        }
      ]
    }
  ]
}
```

## Workflow

### Step 0: Check for input

If no mindmap JSON is available (no file path, no prior `generate-mindmap` output, no inline JSON in the conversation), invoke the `learning:generate-mindmap` skill first to brainstorm and produce the JSON outline from the user's topic or content. Then continue with Step 1.

### Step 1: Locate the mindmap JSON

Find the mindmap outline JSON -- either a file path provided by the user, output from a prior `generate-mindmap` invocation, or inline JSON.

### Step 2: Run the renderer

Pipe the JSON outline to `scripts/generate_markmind.py`:

```bash
cat <<'EOF' | python scripts/generate_markmind.py --output /path/to/output.md --max-depth 4
{...mindmap JSON...}
EOF
```

Or from a file:

```bash
python scripts/generate_markmind.py --input outline.json --output /path/to/output.md --max-depth 4
```

The script automatically:
- Generates unique node IDs
- Splits branches left/right of root
- Calculates x/y coordinates with proper spacing (recursive, supports any depth)
- Truncates nodes beyond `--max-depth` (default: 4)
- Creates 8 empty free nodes
- Wraps everything in valid MarkMind Rich format

### Step 3: Deliver

Present the generated `.md` file to the user. Mention it's ready to drop into Obsidian.

## Reference

Read `references/markmind-rich-spec.md` for the full MarkMind Rich JSON schema if needed.

## Checklist Before Delivery

- All `pid` references point to existing `id` values
- Root has `isRoot: true`, `main: true`, layout object
- No `pid` on root node
- Each L2 branch has a unique stroke color
- All descendants inherit their L2 ancestor's stroke
- Coordinates don't overlap (V_SPACING respected)
- JSON is valid (no trailing commas, balanced brackets)
- 8 empty free nodes present
- No node exceeds the configured max depth
