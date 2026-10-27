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

# Native proposal comparison and design selection

The shared representation and structural validator live in
`../../content/references/records.md` and
`../../content/scripts/office_records.py`. Load accepted `CONTENT.md` and
`DESIGN.md` explicitly; compare content identity/revision and requested formats
before composition. Palette contrast, font capabilities, native styles/themes,
production and saved-file review retain their existing owners.

## Native proposals on real content (v2)

Use `office/design-candidates/v2` for a complete creative comparison. The format
designers and native producers first create representative saved DOCX/PPTX
specimens for the unselected candidates. This helper displays their retained
renders; it supplies no page/slide layout or design recipe. The coordinator and
reviewers establish actual render derivation, source fidelity and native
properties separately. A matching file suffix or hash does not establish them.

Required wrapper fields are `schema`, `project_id`, unique requested `formats`,
`sample`, `sources`, `representatives` and two or three `candidates`. New wrapper
and proof objects reject unknown fields; DESIGN keeps its existing extensions.

| Object | Required representation |
|---|---|
| `sample` | Populated real `title`, `lead`, complete `body`, `source_note`; `table:{headers,rows}`; `content:{project_id,revision,unit_ids,claim_ids}`; `evidence:[{id,text,source_refs:[{source_id,locator}]}]`. Editorial IDs are unique populated strings; the positive revision and project match every candidate. |
| Absent jobs | Use `table:null` or `evidence:[]` only with the matching nonempty reason in optional `sample.not_applicable:{table:reason,evidence:reason}`. Include only absent-job keys; never invent a table or excuse a present job. |
| Optional sample image | `sample.image:{path,alt,sha256}` identifies actual local PNG/JPEG bytes. Its verified raw-byte digest participates in the sample's canonical JSON hash. |
| `sources` | `[{id,sha256,provenance}]`: unique IDs, original-byte source digest and populated inert provenance text. Evidence references resolve to these IDs and populated locators. This is declared lineage, not a helper source audit. |
| `representatives` | Exactly requested format keys, each containing an ordered one to three `{slot_id,roles}` list. Unique slots cover every present `title`, `lead`, `body`, `source_note`, `table` and `evidence` role for that format; roles may recur across slots. No page/slide parity or fixed geometry is imposed. |
| Candidate | `{id,design,previews}`, optionally `parent_ids` as described below. Complete unselected `office/design/v1` passes the public validator with `require_selected=False`; no v1 CSS recipe enum restricts authored v2 decisions. |
| `previews` | Exactly requested format keys, each `{binding,frames,assets}`. Assets are zero to twenty `{id,sha256,provenance}` entries with unique populated IDs and inert provenance text. |
| `binding` | `{candidate_id,design_revision,design_sha256,content:{project_id,revision},sample_sha256,format}`. Every identity, revision, format and canonical digest matches its actual candidate and common sample. |
| Frame | `{slot_id,path,sha256,alt,provenance}` in exactly the representative slot order. Provenance is `{kind:"native-render",source,source_sha256,locator,tool,tool_version,capture_id}`, with populated text and raw-byte digests. `source` names the retained `.docx` or `.pptx` specimen matching that format. |

Canonical JSON uses UTF-8, `ensure_ascii=False`, sorted keys and compact
separators, the existing `canonical-json-v1` convention. Source/image digests
instead cover original bytes. The coordinator verifies the common sample against
the actual CONTENT revision and its complete units, sources and claims; metadata
alone cannot establish that relationship. Imagegen mockups or authored HTML may
be references/assets, but cannot stand in for saved-native proof.

Frame, sample-image and native-source paths must be relative local files under
the input directory. Nested paths are supported; absolute/drive/UNC/ADS paths,
traversal, links, missing files and escapes fail. Native files are streamed only
for SHA-256, never executed or unpacked. Limits are 64 MiB per native source,
4 MiB and 16,000,000 pixels per image, eighteen frames overall and 16 MiB of
embedded image references (the sample once plus every frame occurrence, including
reused files). Each actual image is read/validated/hashed once per invocation.
Exact duplicate frame-digest vectors across candidates of one format fail;
different bytes do not prove a different or attractive artistic idea.

```text
python "<plugin-root>/skills/design/scripts/design_compare.py" candidates.json --out COMPARE.html
```

The safe gallery embeds exact image bytes at their original proportions without
cropping, recoloring or applying candidate fonts to the pixels. It renders the
common readable sample once, with escaped lineage/proof disclosures, keyboard
anchors and a restrictive no-network page policy. Open and inspect the gallery
and the actual saved-native renders. Both preview and selection validate all
bindings and referenced bytes before publishing anything.

## Limited theme sampler (v1)

V1 remains available for its existing theme-treatment comparison. It does not
satisfy the complete creative comparison above and cannot demonstrate candidate
compositions or arbitrary imagery/forms through its fixed recipes.

Write an `office/design-candidates/v1` JSON object with `project_id`, unique
requested `formats` (`docx`, `pptx`), `sample` and two or three `candidates`.
Every candidate is `{id, design}`, where `design` is a complete
`office/design/v1` proposal. The helper imports the actual sibling validator
with `require_selected=False`; it does not copy its schema or palette math.
Candidates share project identity, requested formats and content revision.

`sample` contains populated `title`, `lead`, complete dense `body`, `source_note`
and `table:{headers:[text,...],rows:[[text,...],...]}`. Rows have the same width
as the headers. Supply actual source-backed content, conditions and comparisons;
missing material is a gap to resolve, never permission to invent stock claims,
statistics or images. The same complete sample appears in every requested frame.

An optional `sample.image={path,alt}` names a relative local PNG/JPEG under the
input file's directory. Nested paths within that root are allowed; absolute and
remote paths, traversal, escaping directory links, missing files and other
formats are rejected. Both supplied path and nonempty alt text are required.
Limits are 4 MiB and 16,000,000 pixels. PNG chunks/checksums and JPEG frame/scan
headers supply signature/dimension evidence; no raster decoder is run. The
preview embeds validated bytes as an image data URL and fetches no remote asset.

```text
python "<plugin-root>/skills/design/scripts/design_compare.py" candidates.json --out COMPARE.html
```

The reusable renderer applies font families/weights and declared fallbacks,
semantic colours, spacing unit/density, title alignment, imagery treatment,
callout and table styles. Shared spacing units become CSS pixels in this
preview; native composition chooses its own geometry.
The first three scale entries set small/middle/large gaps, reusing the last
entry when fewer are supplied; the final entry sets the source-note separation.
The fixed recipes are:

| Decision | Supported preview values |
|---|---|
| `components.title`, `components.callout` | `left-aligned` or `centered`; `rule` or `panel` |
| `data.table`, `spacing.density` | `ruled` or `striped`; `compact`, `comfortable` or `spacious` |
| `imagery.treatment` | `documentary` (preserve supplied appearance), `monochrome` (grayscale preview) |
| Remaining recipes | `components.quote=inset`, `components.navigation=section-label`, `data.chart=direct-labels`, `data.source_notes=required` |

Unsupported values fail with an explicit gap; the helper never implies that an
unimplemented visual recipe was applied. Use v2 for complete authored native
compositions rather than extending this sampler into a layout engine. Chart and quote recipes remain
unexercised when the sample contains neither. Fonts use local availability and
fallbacks; this tool does not fetch or prove font installation. Palette
proportions appear as a labelled colour strip without recalculating contrast.

Inspect the HTML in an available browser, including both formats when requested,
real images, visible type/style differences, keyboard links, narrow viewport
reading and text/table overflow. Native anchor navigation highlights proposals
without hiding content or recording a choice. All text is escaped, CSS is fixed
or constrained validated data, and a restrictive page policy prevents remote
resources. The page explicitly states its preview limits.

## Explicit selection and authored combinations

After the user's answer or within recorded autonomous authority:

```text
python "<plugin-root>/skills/design/scripts/design_compare.py" candidates.json --select technical --authority user --source "Decision Q2" --out DESIGN.md
```

This validates the full input, including any supplied image, then writes the
exact authored design with `selection={candidate_id,authority,source}` through
the shared record writer. Preview highlighting never counts as approval.
Selection does not generate a second preview or mutate the proposal file.
Only `user` or `autonomous` authority is accepted; the caller retains the actual
grant/answer evidence.

V2 additionally preserves `selection.preview={comparison_sha256,
hash_mode:"canonical-json-v1",sample_sha256,design_sha256,frames}`. The comparison
hash covers the complete unmodified input object; design/sample hashes cover
their actual payloads. `frames` maps the original requested formats to ordered
`{slot_id,sha256}` lists for the chosen candidate. These are fingerprints of the
original choice, not proof of current native-render derivation. The shared record
validator checks this optional block's exact shape and supported format keys.

A requested compatible combination is another complete authored candidate,
with a new ID, explicit `parent_ids` naming at least two distinct known other
candidates, and design revision greater than every parent's revision. Preview
that candidate before selecting its ID. Selection preserves exact parent IDs in
`selection.parent_ids`. No automatic merge synthesizes design decisions.

Both commands publish a new artifact atomically and refuse replacement, input
aliases and asset aliases. Temporary siblings are removed on failure. Preserve
accepted artifacts and choose new paths for revised candidates. The input uses
the shared parser's 4 MiB, duplicate-key and finite-number protections. Structural
success, valid image headers and an HTML preview do not prove semantic fidelity,
font availability, native editability, saved render quality or application
fidelity. Retain those independent checks and report unavailable capabilities.

## Inherited design rebinding

For an expand, revise or derive that retains the accepted look, rebind the
inherited design when the content identity, `content.revision` or requested
formats change. Copy the accepted record to working JSON, increment its design
revision and publish to a new candidate path through `office_records.py write`.
Update `project_id`, `content` and `formats` to the actual final CONTENT record.
Preserve all visual values and the original `selection` evidence. Project
existing adaptations onto the requested formats; a missing necessary adaptation
is a design task within the inherited identity, not permission to invent a
historical choice. No new visual selection is needed for this binding update.

Preserve any original `selection.preview` unchanged as historical evidence,
including its original format keys and hashes. Do not relabel those fingerprints
to the new content/design revision or current requested-format subset. New native
composition still needs its own scoped saved-file and reviewer evidence.

Add `inheritance={path,sha256,project_id,revision,reason}` identifying the
predecessor DESIGN record and the authorized content operation. The extra
provenance is caller evidence; structural validation alone does not verify its
truth. Load both new records, validate the actual PPTX plan when requested and
compare their identities/revisions/formats before dependent layout or production.
Keep predecessor bytes unchanged. A changed visual identity follows the ordinary
proposal/selection route instead of being disguised as metadata rebinding.

For a legacy derive, expand or revise without shared records, serialize the
source content and observed inherited theme within the existing operation.
Bind the source native path/hash in `inheritance`; distinguish observed values,
necessary continuation decisions and unresolved gaps. Record the current reuse
authorization as `selection.authority=autonomous` with its actual source, never
an invented historical user approval. Resolve only material missing values;
local edits/reviews still need no retrospective global record. Both format
methods and native producers use this same procedure.
