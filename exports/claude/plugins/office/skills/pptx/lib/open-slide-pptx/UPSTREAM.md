<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

Excluded on purpose: `pptx/render.ts` (the React offscreen mount this wrapper
does not use), every `*.test.ts`, and the whole open-slide application, CLI,
Vite plugin and React tree.

## Third-party code inside the bundle

`fflate` 0.8.3 (MIT, notice in `LICENSE-fflate-MIT.txt`) supplies the ZIP writer
and `html-to-image` 1.11.13 (MIT, notice in `LICENSE-html-to-image-MIT.txt`)
supplies the rasterizer's canvas capture. Both declare no dependencies of their
own, both are bundled by `rebuild.mjs` and neither is vendored as source here.

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
   anything, and record why the advance is needed.
2. Re-copy those paths verbatim, keeping the local layout, then run
   `node rebuild.mjs` so `manifest.json` and the bundle move together.
3. Run the fixture conversion in `tests/test_office_pptx_convert.py` and the
   Office suite; inspect the saved package with `office:deckcraft`'s
   `pptx_inspect.py` and render it before claiming any fidelity.
4. Update this note, the Office `README.md` source row and the copied-source row
   in the `upstream-sync` table with the new pin.

Never hand-edit a vendored file: the hash guard treats it as drift, and a local
fix belongs in the Office entry or driver instead.

## Known limits

The exporter emits no native PPTX table, rasterizes vector effects it cannot
express, keeps an SVG image as a PNG with the original SVG alongside, and reads
speaker notes from `data-office-notes`. Microsoft PowerPoint fidelity requires
an actual render and independent review; see `references/html-to-pptx.md`.

## Why this vendor exists

The comparative conversion benchmark in
`office-conversion-benchmark/20261027-graphical/` measured six HTML to Office
lanes on one frozen source: this exporter kept 73/73 source text units as native
text and produced the strongest visual result, while the alternatives lost
captions, joined words, malformed a native table or dropped the composition.
The owner chose the scoped copy over a runtime dependency on the upstream
package on 2026-10-27, accepting the maintenance obligation recorded here.
