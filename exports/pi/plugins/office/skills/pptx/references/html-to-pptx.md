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

# HTML to PPTX conversion

Build a native deck mechanically from an approved HTML design instead of
transcribing it into engine commands. The conversion runs the vendored
open-slide exporter (`lib/open-slide-pptx/UPSTREAM.md`) inside a headless
browser page: text becomes native text boxes, boxes and borders become shapes,
images become pictures, and speaker notes come from the panel attribute. The
model authors the HTML once and never rewrites objects per slide.

Use it for construction: a new deck, a restyle, or a proposal proof that needs a
saved native candidate. Do not use it to edit an existing deck, for the
read-only route, or when the accepted design has no HTML source. Editing,
coverage and preservation stay with `office:deckcraft` on the saved file.

## Input contract

One self-contained HTML file. Every slide is one element marked
`data-office-slide`, in deck order:

- exactly 1920x1080 CSS pixels, `box-sizing: border-box`, with
  `position: relative` (or absolute/fixed) on the panel itself;
- self-contained: no rule that depends on a parent or sibling selector, because
  each panel is measured on its own;
- `overflow: hidden`, since the canvas is the slide edge;
- optional `data-office-notes="..."` for that slide's speaker notes;
- local assets only, resolved from the HTML directory or `--assets-root`;
- installed or locally embedded fonts. A webfont URL is blocked and recorded.

The converter refuses the whole run on a contract violation instead of scaling
or repairing a panel, and it names each offending panel. Requests outside the
local origin are aborted and listed in the evidence, so a conversion never
fetches a remote resource.

## Commands

```text
python "<plugin-root>/skills/pptx/scripts/pptx_convert_bridge.py" probe
python "<plugin-root>/skills/pptx/scripts/pptx_convert_bridge.py" convert \
  --html design.html --output candidate.pptx --evidence candidate.conversion.json
```

Optional: `--assets-root`, `--browser`, `--timeout-ms`, `--headed`, `--node`.
The bridge verifies the vendored hashes before every run, so an edited vendor
fails here rather than converting silently.

## Runtime prerequisites

- Node `^20.19.0` or `>=22.12.0`; `OFFICE_PPTX_NODE` overrides discovery.
- The Playwright Node module; `OFFICE_PPTX_PLAYWRIGHT` may point at a directory
  that contains it (`npm install playwright` in any directory works).
- A Chrome, Edge or Chromium executable; `OFFICE_PPTX_BROWSER` overrides the
  known installation paths, otherwise the Playwright-managed browser is used
  (`npx playwright install chromium`).

A missing runtime is a stop with these instructions and a recorded blocker. It
is not a silent fallback to another construction path; if the coordinator builds
the deck another way, the report says which path ran and why.

## Outputs and evidence

The saved `.pptx` plus one `office/pptx-html-conversion/v1` record carrying the
HTML and bundle hashes, the engine pin, Node/Playwright/browser versions, the
viewport, panel and part counts, the per-slide scene summary (node kinds,
background, notes), image inventory, conversion time, console warnings, page
errors, blocked and missing local requests, and its own limits. Verify the
package with `office:deckcraft`'s `pptx_inspect.py`, then render and review it
under `pptx-compatibility.md` like any other candidate.

## What it proves and what it does not

Native text objects, shapes, pictures and notes exist in the saved package, and
the conversion is deterministic with no model call. It does not prove visual
fidelity, Microsoft PowerPoint behavior, or that the design survived: the
independent rendered review still owns that verdict. Known losses: no native
PPTX table (a measured HTML table becomes shapes and text), vector effects the
exporter cannot express are rasterized, and an SVG image is kept as a PNG with
its original SVG alongside. Fonts are declared, never embedded here; embedding
still uses `office:design`'s `font_embed.py` on a separate candidate.
