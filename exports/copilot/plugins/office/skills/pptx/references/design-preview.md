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

# Design preview before construction

Render a static HTML wireframe of the presentation plan so the user chooses the
visual direction and the slide sequence before any image generation or native
construction. The preview is a review artifact: it is not a PowerPoint
deliverable, it is not a rendered deck, and it never replaces native construction
or the independent rendered review.

## When to prepare it

1. More than a few slides, a reusable template, or a substantial redesign.
2. Genuine direction uncertainty, or a user who asks to see options before the deck.
3. Before any harness image-generation call, so a direction choice is not paid for
   twice.

A fully autonomous request, or one that already fixed direction and outline,
skips the gate and records the inferred choices instead.

## Plan contract

Write one JSON file in the presentation workspace:

```json
{
  "deck_title": "Quarterly operating review",
  "deck_meta": "2026-10-23 | board",
  "direction": {"library": "A"},
  "slides": [
    {"pattern": "cover", "title": "Operating review", "subtitle": "Q3 results", "meta": "Board | 2026-10-23"},
    {"pattern": "executive summary", "kicker": "Summary", "headline": "One decision per slide",
     "content": {"cards": ["Growth", "Margin", "Risk"]}, "source_note": "Source: finance pack"}
  ]
}
```

- `direction`: `library` names a direction from `office:design`'s
  `references/directions.md` (`A` to `T`); `palette` carries the chosen
  palette's `background`, `ink`, `surface` and `accent` as `#RRGGBB` values;
  `name` labels the palette (its variant or the brand).
- `slides[]`: `pattern` must match a pattern name from `layout-patterns.md`
  (case-insensitive). `title`, `kicker`, `headline`, `source_note` and `content`
  are optional, except that any non-cover, non-divider pattern needs a `headline`
  unless the slide carries `"mode": "showcase"`, where the visual may stand alone.
- `content` lists are used for density checks; give them the real planned counts
  so the preview can flag a slide that exceeds its pattern's capacity.
- One direction per deck; one pattern per slide. Vary the pattern across slides.
- A plan from `content-planning.md` also carries `id`, `job`, `claims` (claim
  IDs) and, for an existing deck, `status`: `kept`, `updated`, `moved`, `new` or
  `merged` (cut slides are not in the plan). The sequence table shows status and
  claims; an unknown status is a plan problem.

Always put the chosen palette's actual colors in `direction.palette`: its
background, ink, surface and accent. Set `direction.name` to the palette's
name. Keep `library` for the composition direction. The explicit palette
overrides the direction's default seeds, so the preview and both format design
reports use the same colours.
This wireframe helper does not preview the selected fonts; verify them in the
saved native candidate. Do not infer that a palette change also updated fonts.

## Render and present

Invoke `scripts/design_preview.py` from this skill with the host's Python
executable, for example:

```text
<python> <skill root>/scripts/design_preview.py --plan plan.json --out preview.html
<python> <skill root>/scripts/design_preview.py --plan plan.json --view
```

where `<skill root>` is this skill's installed directory. The method body that
loaded this reference carries the host-resolved command.

The script reads the local library, so palettes and pattern capacity stay in one
place. It writes one HTML page with a 16:9 frame per slide, the planned pattern
wireframe, the real headline and a slide-sequence table. Open it with the host's
normal browser or file-opening interface and keep its own scope line visible:
`preview only`.

`--view` prints a text summary with the per-pattern capacity ratio; a run without
`--out` performs the same validation without writing a file. `--direction L`
overrides the plan's direction label for that run, so several candidate
directions can be previewed from one plan without editing it. Exit codes: `0`
written or checked, `1` plan problems (nothing written), `2` invocation or path
error.

The script refuses the whole run on a plan problem rather than writing a partial
preview. Reported problems are plan problems, not design verdicts: fix the plan
and rerun.

## What the preview does and does not prove

- It proves the palette, the slide order, the pattern choice and the density fit
  were agreed before construction.
- It does not prove rendering, fonts, native object behavior, or fidelity in
  Microsoft PowerPoint. Those require the saved candidate and the rendered review
  under `pptx-compatibility.md`.
- A style proof is a different artifact: one representative slide built
  natively with the construction engine and rendered, once per candidate
  direction the user chose. Generated imagery inside it follows `image-tools.md`
  and needs the user's explicit budget decision. Record the direction, the slide
  and any generations in the completion evidence.
