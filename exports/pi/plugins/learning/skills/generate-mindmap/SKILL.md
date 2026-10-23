---
name: generate-mindmap
description: >
  Produce a Buzan-style radiant outline as structured JSON, optimized for recall over symmetry:
  single keywords, emoji anchors, cross-links.
  TRIGGER WHEN: the user asks to create a mind map, mappa mentale, concept map, or visual summary
  of a topic, text, or file, typically to learn or brainstorm.
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

# Generate Mindmap (Buzan Method)

Analyze content and produce a structured mindmap JSON outline. This skill focuses on the intellectual work: extracting core themes, building organic hierarchy, assigning visual attributes, and finding non-linear associations. The output is a renderer-agnostic JSON structure.

## Philosophy: Effectiveness > Efficiency

Do not force symmetrical or perfectly balanced branches. Human thought is organic. Prioritize **cognitive impact**: use highly evocative single words, vivid emojis, and let branches grow naturally based on the richness of the associations.

## Parameters

The user can specify these parameters. If not specified, use **normal** complexity.

### Complexity

| Level         | L2 branches | Max depth | Description                                |
| ------------- | ----------- | --------- | ------------------------------------------ |
| **essential** | 3-5         | 2         | Core concepts only, high-impact synthesis. |
| **normal**    | 5-7         | 4         | Balanced organic exploration (default).    |
| **detailed**  | 7-9         | 6         | Deep, comprehensive associative dive.      |

*Note: Node counts per branch are NOT fixed. Let them flow organically. Some L2 branches may have 10 children, others only 1.*

## Workflow

### Step 1: Analyze content

Identify the core subject, main radiating themes, and hidden connections between different concepts.

### Step 2: Build outline (Radiant Thinking)

1. **Identify the Central Nucleus:** 1-2 words maximum. Create a vivid `central_image_prompt` describing a visual representation of this core.
2. **Extract Main Branches (L2):** The primary categories radiating from the center.
3. **Extract Sub-branches (L3+):** Apply the **Rule of One**: use a SINGLE powerful keyword per node (absolute max 2 words if strictly necessary). Strip all articles, prepositions, and filler words.
4. **Assign Emoji:** Every single node (L2, L3+) MUST have an emoji placed *before* the keyword to act as a visual anchor.
5. **Assign Colors:** Assign a unique hex color to each L2 branch. All children of that branch conceptually inherit this color.
6. **Identify Cross-Links:** Find 1 to 4 non-linear connections between different branches (e.g., a node in Branch 1 that heavily relates to a node in Branch 3).

### Step 3: Output

Write the mindmap in the requested format. Default is **JSON**. Save to a file (e.g., `/tmp/mindmap-outline.json`).

#### JSON format (default)

```json
{
  "root": "🎯 Brainstorming",
  "central_image_prompt": "A glowing human brain with colorful lightning bolts radiating outward",
  "branches":[
    {
      "id": "b1",
      "text": "🎨 Creativity",
      "color": "#ff6b6b",
      "children":[
        { "id": "b1_1", "text": "💡 Ideas" },
        { "id": "b1_2", "text": "🔗 Connections" }
      ]
    },
    {
      "id": "b2",
      "text": "⚙️ Process",
      "color": "#4ecdc4",
      "children":[
        { "id": "b2_1", "text": "⏳ Time" }
      ]
    }
  ],
  "cross_links":[
    { "from": "b1_2", "to": "b2_1", "label": "accelerates" }
  ]
}
```

#### Markdown format

If markdown is requested, produce a nested list. Omit colors and cross-links, but strictly maintain the single-keyword rule and emojis.

## Content Principles (Buzan Rules)

- **The Rule of One:** One node = ONE keyword. Never a phrase, never a sentence. Nouns and strong action verbs only.
- **Visual Memory:** Emojis are not decorative; they are cognitive anchors. Match the emoji to the meaning, not just the word.
- **Organic Growth:** Allow asymmetry. If a concept triggers a deep chain of associations, let it go deep (up to max depth).
- **Opposites/Tensions:** Use contrasting symbols (e.g., ☀️/🌧️, ✅/❌).

## Semantic Emoji Code (Fallback)

Use specific emojis when applicable, otherwise use domain-specific ones:

| Function         | Emoji | Function         | Emoji |
| :--------------- | :---- | :--------------- | :---- |
| Central Concept  | 🎯    | Concrete Example | 💡    |
| Definition/Core  | 📌    | Metric/Data      | 📊    |
| Process/Action   | ⚙️    | Person/Role      | 👤    |
| Advantage/Pro    | ✅    | Time/Phase       | ⏳    |
| Limit/Con        | ❌    | Warning/Risk     | ⚠️    |

## Color Palette (L2 branches)

Use these high-contrast, brain-friendly colors for L2 branches:

| #  | Color    | Hex     |
| -- | -------- | ------- |
| 1  | Coral    | #ff6b6b |
| 2  | Teal     | #4ecdc4 |
| 3  | Lime     | #95e77e |
| 4  | Mint     | #a8e6cf |
| 5  | Peach    | #ffd3b6 |
| 6  | Lavender | #d4a5f5 |
| 7  | Yellow   | #f7dc6f |
| 8  | Sky      | #85c1e9 |

## JSON Schema Requirements

- **root** (string): Central theme (1-2 words + emoji).
- **central_image_prompt** (string): A short prompt describing a visual illustration of the root.
- **branches** (array): List of branch objects.
- **Branch object:** Must include `id` (unique string, e.g., "node_1"), `text` (emoji + single keyword), and `color` (L2 only).
- **cross_links** (array): Objects containing `from` (id), `to` (id), and optional `label` (1 word).
