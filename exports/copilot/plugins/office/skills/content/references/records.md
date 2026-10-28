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

# Office record representation

`scripts/office_records.py` is the executable structural contract. Use its
public `load_record(Path)`, `validate_content(record, pptx_plan=...)`,
`validate_design(record, require_selected=True)` and `write_record(record, Path)`
interfaces. Validators return error strings and never mutate their arguments.
No errors means structural consistency within the supplied data.

Records are UTF-8 JSON objects, either standalone or inside exactly one
`json` fence in Markdown. The loader rejects duplicate keys at every depth,
nonfinite numbers, malformed/non-object data and files above 4 MiB. The writer
validates before publishing a new Markdown artifact, preserves actual Unicode
data and refuses any existing output, including aliases and links. Publication
uses a temporary sibling and an atomic publication that refuses replacement
(Windows rename, hard link elsewhere). An unsupported filesystem fails safely.
Choose a new candidate path for revisions.

## CONTENT.md

The schema is `office/content/v1`. Required fields:

| Field | Representation |
|---|---|
| Identity | `project_id`: nonempty stable text; `revision`: positive integer |
| `brief` | Nonempty `operation`, `intent`, `goal`, `audience`, `market`, `channel`, `scope`, `depth`, `extent`, `density`, `tone`; unique requested `formats` (`docx`, `pptx`); `transformation` mode |
| `sources` | Nonempty list of `{id, path, sha256, role}`. IDs are unique; hashes describe original source bytes, never canonicalized text. Source roles identify information, binding brand/template, reference or existing artifact as appropriate. |
| `claims` | Nonempty list of `{id, text, priority, sources, locked, conditions, conflicts}`. `priority` is `core`, `supporting` or `optional`; `sources` is a nonempty list of `{source_id, locator}`. `locked` is boolean; conditions/conflicts are lists of text. |
| `units` | Nonempty list of `{id, message, text, claim_ids, relationship, detail, transformation}`. Claim references are nonempty and known. Each unit carries complete content, not a promise to write it later. |
| `sequence` | All unit IDs, each exactly once, in logical order |
| `projections` | Exactly the requested format keys, as below |
| `transformations` | List of `{unit_id, mode, source_ids, destination:{format,id}, reason}`. Each destination exists and places the named unit. |
| `gaps` | List of unresolved evidence or editorial gaps as text |
| `exclusions` | List of `{claim_id, format, reason, authority, source}`. Known claim, requested format, decision source and explicit `user` or authorized `autonomous` authority. |

Permitted transformation modes are `verbatim`, `copyedit`, `restructure`,
`rewrite`, `summarize`, `synthesize` and `expand`. Set permission per unit; the
brief's overall mode does not override local locks. A unit carrying a locked
claim uses verbatim mode and exactly that claim's text. Keep distinct locked
blocks in distinct units. A transformation entry cannot release a lock.
Its mode must agree with the named unit's transformation permission.
Every requested format covers every core claim through placed units, unless
an explicit authorized exclusion names the claim and format. Mapping alone
cannot prove that a free rewrite preserves meaning, conditions or uncertainty.

DOCX projection:

```json
{"content_revision":1,"structure":"technical brief","sections":[{"id":"D1","title":"Editorial authority","unit_ids":["U1"]}]}
```

PPTX projection:

```json
{"content_revision":1,"plan":{"path":"plan.json","hash_mode":"canonical-json-v1","sha256":"<64 hex digits>"},"placements":[{"slide_id":"S1","unit_ids":["U1"]}]}
```

Both projection revisions equal the content revision. The PPTX plan remains the
existing native plan, with stable slide `id` and `claims` plus a
`content_revision` binding. This record adds placements, never a competing
slide schema. Validate with the supplied plan to check its revision, unique
slide IDs, known claim IDs, placement destinations and exact agreement between
each slide's claims and placed unit claims. A slide with claims needs a placement;
slides without claims may remain outside the editorial mapping. Native pattern,
object and capacity validation remains with the PPTX tools.

The binding digest is SHA-256 of these bytes:

```python
json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
```

`hash_mode` must explicitly be `canonical-json-v1`. A whitespace change in the
original plan file leaves this binding unchanged. The CLI separately prints
`pptx_plan_file_sha256`, the hash of the supplied file's original bytes, as
input evidence. Do not substitute one hash for the other. Without a supplied
plan, serialization and validation check record structure and declared digest
shape only; they do not verify external plan content or source file bytes.

## DESIGN.md

The schema is `office/design/v1`. Design owns these decisions; the content helper
also validates their shared representation for its consumers.

| Field | Representation |
|---|---|
| Identity | `project_id`, positive `revision`; `content:{project_id,revision}` names the same project and positive content revision. The consumer compares it with the exact loaded content record. |
| `formats` | Unique, nonempty subset of `docx`, `pptx` |
| `direction` | `{name, idea, principles:[text,...]}` with all fields populated |
| `palette` | Existing helper roles `background`, `surface`, `ink`, `accent`, `muted` as `#RRGGBB`; nonempty `data` colour list; `provenance:{source,method}`; `proportions:{background,surface,ink,accent}` as finite fractions summing to one |
| `typography` | `heading`, `body`, `caption`, each `{family,fallbacks:[...],weight}`. Safe family names and explicit nonempty fallbacks; integer weight 1 through 1000. |
| `spacing` | `{unit,scale:[...],density}`. Finite positive unit/scale values, with increasing unique scale values; density is a safe style name. Units describe a scale; format methods choose native geometry. |
| `imagery` | `{treatment,source_policy}` as nonempty text |
| `data` | `{table,chart,source_notes}` as safe style names |
| `components` | `{title,callout,quote,navigation}` as safe style names |
| `adaptations` | Exactly the requested format keys, each `{reading,emphasis}` as nonempty text |
| `selection` | `{candidate_id,authority,source}`; nonempty exact candidate identity and decision source; authority `user` or authorized `autonomous`. Optional original-choice `preview` fingerprints are described below. |

Font/style names contain only Unicode word characters, spaces, periods and
hyphens. They contain no CSS declarations, functions, URLs or markup. Consumers
still escape displayed text and map style names through their own fixed
renderer; validation is not permission to interpolate arbitrary data into CSS.
Use the existing palette helper for contrast/distinctness mathematics. This
validator checks role/value completeness and does not recompute palette quality.

`validate_design(record, require_selected=False)` accepts a proposal without
selection, but rejects a malformed supplied selection. Final records require
selection. Neither browser highlighting nor validation implies approval.

Optional `selection.preview` has exactly `comparison_sha256`,
`hash_mode:"canonical-json-v1"`, `sample_sha256`, `design_sha256` and `frames`.
Digests are SHA-256 values. `frames` is a nonempty map of original `docx`/`pptx`
format keys, each with one to three `{slot_id,sha256}` entries and unique populated
slot IDs. Unknown preview/frame keys or malformed values fail, even when the
selected-record requirement is disabled. The comparison helper supplies these
fingerprints only after validating the exact original proof bindings and bytes.
They describe that historical choice, so this validator does not compare them
with current design/content hashes or require current format-key equality.
Inherited rebinding preserves the block unchanged; it cannot certify a new render.

The design consumer explicitly loads the record and compares content identity,
revision and requested formats before native production. Actual font availability,
source fidelity, accessibility and saved-file rendering need separate evidence.
