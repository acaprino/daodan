<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# MarkMind Rich Format Specification

Reference document for the internal JSON structure used by the Obsidian MarkMind plugin in Rich mode.

## File Structure

A MarkMind Rich file is a standard `.md` with YAML frontmatter and a JSON code block:

```
---

mindmap-plugin: rich

---

# Root
``` json
{...full JSON...}
```
```

Important: the frontmatter requires blank lines before and after `mindmap-plugin: rich`.

## Top-Level JSON

```json
{
  "theme": "",
  "mindData": [ [main_nodes...], [freeNode1], [freeNode2], ... ],
  "induceData": [],
  "wireFrameData": [],
  "relateLinkData": [],
  "calloutData": [],
  "opt": {
    "background": "transparent",
    "fontFamily": "",
    "fontSize": 16
  },
  "scrollLeft": 3303,
  "scrollTop": 3330,
  "transformOrigin": [4253.5, 3860]
}
```

### mindData

Array of arrays. The first array contains all nodes of the main map (flat list, not nested). Subsequent arrays are free nodes (standalone nodes not connected to the tree).

### Node Fields

| Field     | Type    | Required | Description                                                    |
| --------- | ------- | -------- | -------------------------------------------------------------- |
| id        | string  | yes      | Unique identifier                                              |
| text      | string  | yes      | Display text. Supports emoji, `**bold**`, `![[image]]`         |
| pid       | string  | no       | Parent node ID. Absent only on root                            |
| isRoot    | boolean | root     | `true` only on root node                                       |
| main      | boolean | root     | `true` only on root node                                       |
| x         | number  | yes      | Absolute X coordinate on canvas                                |
| y         | number  | yes      | Absolute Y coordinate on canvas                                |
| stroke    | string  | yes      | Branch color (hex). Empty string on root                       |
| style     | object  | yes      | CSS properties: color, background-color, border-color, etc.    |
| layout    | object  | root     | `{"layoutName":"mindmap6","direct":"mindmap"}` on root, else `null` |
| isExpand  | boolean | yes      | Whether children are visible. Always `true` for generation     |

### Root Node Example

```json
{
  "id": "root-001",
  "text": "🎯 Central Theme",
  "isRoot": true,
  "main": true,
  "x": 4120,
  "y": 3700,
  "isExpand": true,
  "layout": {"layoutName": "mindmap6", "direct": "mindmap"},
  "stroke": "",
  "style": {
    "color": "#ffffff",
    "background-color": "#ffffff",
    "border-color": "#ffffff",
    "text-align": "center"
  }
}
```

### Child Node Example

```json
{
  "id": "node-abc123",
  "text": "⚙️ Process Flow",
  "stroke": "#ff6b6b",
  "style": {},
  "x": 4400,
  "y": 3575,
  "layout": null,
  "isExpand": true,
  "pid": "root-001"
}
```

### Free Node Example

Each free node is a separate array in mindData:

```json
[{
  "id": "fn-xyz789",
  "text": "freeNode",
  "main": false,
  "x": 0,
  "y": 0,
  "layout": {"layoutName": "mindmap2", "direct": "mindmap"},
  "isExpand": true,
  "stroke": "",
  "style": {}
}]
```

Standard generation includes 8 empty free nodes.

## Coordinate System

The canvas uses absolute pixel coordinates. Typical root position: (4120, 3700).

### Layout Algorithm

- Branches split left/right of root (first half + extra right, rest left)
- Horizontal offsets from parent:
  - Root to L2: 280px
  - L2 to L3: 150px
  - L3 to L4: 140px
- Vertical spacing between siblings: 33px
- Gap between branch clusters: 12px
- Each side centers vertically around ROOT_Y

### Viewport Settings

```
scrollLeft = ROOT_X - 817
scrollTop = ROOT_Y - 370
transformOrigin = [ROOT_X + 133.5, ROOT_Y + 160]
```

## Advanced Features

### induceData (Summary)

Groups consecutive sibling nodes under a label:

```json
{
  "induceData": {
    "nodeId": "first-node-id",
    "endNodeId": "last-node-id",
    "stroke": "#666",
    "root": "summary-root-id",
    "lineType": "solid",
    "id": 1234567890,
    "range": "0,2",
    "type": "left"
  },
  "mindData": [{
    "id": "summary-root-id",
    "text": "Summary Label",
    "style": {},
    "x": 3319,
    "y": 3681,
    "layout": null,
    "isExpand": true,
    "stroke": ""
  }]
}
```

### relateLinkData (Cross-branch connections)

Connects nodes from different branches with a styled line. Complex structure with bezier control points. Use sparingly and only for explicit cross-references.

### wireFrameData (Boundary)

Groups nodes visually with a surrounding frame. Currently empty array for standard generation.

## Color Palette

| # | Hex       | Name     |
| - | --------- | -------- |
| 1 | #ff6b6b   | Coral    |
| 2 | #4ecdc4   | Teal     |
| 3 | #95e77e   | Lime     |
| 4 | #a8e6cf   | Mint     |
| 5 | #ffd3b6   | Peach    |
| 6 | #d4a5f5   | Lavender |
| 7 | #f7dc6f   | Yellow   |
| 8 | #85c1e9   | Sky      |

Rule: all descendants of an L2 branch inherit that branch's stroke color.
