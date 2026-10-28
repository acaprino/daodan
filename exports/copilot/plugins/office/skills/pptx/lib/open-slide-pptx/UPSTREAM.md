<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# Vendored open-slide PPTX exporter

Copied source kept under an owner-authorized scoped exception to this
repository's no-new-vendor policy. The exception covers exactly the eleven
upstream files listed below and nothing else. Office's MIT license does not
replace the bundled upstream terms.

Upstream: [open-slide/open-slide](https://github.com/open-slide/open-slide),
package `@open-slide/core` 2.3.1, commit
`82349cf2d07d37b75975170503a82fcaacae9298`, MIT, Copyright (c) 2026 Yiwei Ho,
full text in `LICENSE-open-slide-MIT.txt`. Registry evidence: tarball
`https://registry.npmjs.org/@open-slide/core/-/core-2.3.1.tgz`, integrity
`sha512-NpEB6NATbyGqaO0MSmJYEvhBsVx7ISiP0YzxT4QkMuosZRyPFyZcjYfxMO1gPc/mmfAZao+5wLizyPQ9OKMwPQ==`,
shasum `654c7b21947683027f227e2fb01cd6171927a80c`. The pinned source archive
compared in the conversion benchmark has SHA-256
`d8183a5f2c79d517e1793bc72e65e2e0c8936e77fbd8260486de9df944d17db8` and the
published tarball ships the same `src/app/lib/pptx` sources this vendor copies.

## What is copied

| Upstream path at the pin | Local path |
|---|---|
| `packages/core/src/app/lib/sdk.ts` | `src/lib/sdk.ts` |
| `packages/core/src/app/lib/pptx/color.ts` | `src/lib/pptx/color.ts` |
| `packages/core/src/app/lib/pptx/css.ts` | `src/lib/pptx/css.ts` |
| `packages/core/src/app/lib/pptx/fonts.ts` | `src/lib/pptx/fonts.ts` |
| `packages/core/src/app/lib/pptx/images.ts` | `src/lib/pptx/images.ts` |
| `packages/core/src/app/lib/pptx/measure.ts` | `src/lib/pptx/measure.ts` |
| `packages/core/src/app/lib/pptx/ooxml.ts` | `src/lib/pptx/ooxml.ts` |
| `packages/core/src/app/lib/pptx/raster.ts` | `src/lib/pptx/raster.ts` |
| `packages/core/src/app/lib/pptx/scene.ts` | `src/lib/pptx/scene.ts` |
| `packages/core/src/app/lib/pptx/text-lines.ts` | `src/lib/pptx/text-lines.ts` |
| `packages/core/src/app/lib/pptx/units.ts` | `src/lib/pptx/units.ts` |

The local layout keeps the upstream relative imports (`../sdk`) intact, so no
copied file is edited. `rebuild.mjs` records a SHA-256 for every copied file,
for the Office entry and for the built bundle in `manifest.json`;
`scripts/pptx_convert_bridge.py` recomputes those hashes before each conversion
and `tests/test_office_pptx_convert.py` recomputes them in the suite. An edit to
a vendored file therefore fails instead of drifting silently.

Excluded on purpose: `pptx/render.ts` (the React offscreen mount), every
`*.test.ts`, and the whole open-slide application, CLI, Vite plugin and React
tree. `render.ts` also fast-forwarded animations and waited for `data-waitfor`
targets before measuring; the Office entry reimplements that settle step, so a
design's entrance animations are measured at their end frame.

## Third-party code inside the bundle

`fflate` 0.8.3 (MIT, notice in `LICENSE-fflate-MIT.txt`) supplies the ZIP writer
and `html-to-image` 1.11.13 (MIT, notice in `LICENSE-html-to-image-MIT.txt`)
supplies the rasterizer's canvas capture. Both declare no dependencies of their
own, both are pinned in `build.deps.json` and bundled by `rebuild.mjs`, and
neither is vendored as source here.

## Office-owned additions

`entry/office-entry.ts`, `driver.mjs`, `rebuild.mjs`, `build.deps.json`,
`manifest.json`, `bundle/open-slide-pptx.js` and
`scripts/pptx_convert_bridge.py` are Office code under the plugin's MIT license.
They own the 1920x1080 panel contract, local-only asset serving, runtime
discovery, the hash guard and the conversion evidence record. The operational
contract is `references/html-to-pptx.md`.

## Rebuild

```text
node rebuild.mjs [--workdir PATH] [--no-minify] [--skip-install] [--check]
```

Build inputs install into the work directory, by default
`<repository>/.daodan/tmp/open-slide-pptx-build`, never into this plugin
directory, so no `node_modules` tree can reach a generated host package.
`--check` rebuilds without writing and reports drift against the committed
bundle and manifest. The committed bundle is minified; use `--no-minify` for
debugging and do not commit that output.

## Refresh protocol

1. Read the upstream diff for the eleven paths at a new pin before copying
   anything, and record why the advance is needed. Check `fflate` and
   `html-to-image` for fixes at the same time.
2. Edit the pin in `build.deps.json` (`upstream`, and the two library versions
   when they advance); it is the only place the pin is data. Re-copy the paths
   verbatim, keeping the local layout, then run `node rebuild.mjs` so
   `manifest.json`, the bundle banner and the bundle move together.
3. Run the fixture conversion in `tests/test_office_pptx_convert.py` and the
   Office suite; inspect the saved package with `office:deckcraft`'s
   `pptx_inspect.py` and render it before claiming any fidelity.
4. Update every prose record that states the pin: this note, the Office
   `README.md` source row, the copied-source row in the `upstream-sync` table and
   section 4.3 of `external-repo-intake` (then regenerate the Codex copies). The
   tests read the pin from `build.deps.json`.

Never hand-edit a vendored file: the hash guard treats it as drift, and a local
fix belongs in the Office entry or driver instead.

## Known limits

The exporter emits no native PPTX table, rasterizes vector effects it cannot
express, keeps an SVG image as a PNG with the original SVG alongside, and reads
speaker notes from `data-office-notes`. Microsoft PowerPoint fidelity requires
an actual render and independent review; see `references/html-to-pptx.md`.

## Why this vendor exists

The comparative conversion benchmark summarized in the Daodan repository's
Office documentation dossier (`verification.md`) measured six HTML to Office
lanes on one frozen source: this exporter kept 73/73 source text units as native
text and produced the strongest visual result, while the alternatives lost
captions, joined words, malformed a native table or dropped the composition.
The owner chose the scoped copy over a runtime dependency on the upstream
package on 2026-10-27, accepting the maintenance obligation recorded here.
