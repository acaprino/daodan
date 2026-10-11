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

# Concept Index Protocol

The concept index is the bridge between the two modes. Global mode builds it. Diff mode reads it and answers "does this change introduce a second authority" by consulting an index instead of re-censusing the repository on every review.

## Epistemic status

> **Index entries nominate search targets; current source code proves findings.**

The index is a discovery accelerator. It is never a cache of truth, and it is never the sole evidence for a finding. Before promoting any D1 to D4 finding, re-read the involved representations against current source.

Three obligations follow, and they exist because a shared artifact that corroborates itself is how a pipeline produces confident wrong answers:

- **Duty of autonomous rediscovery.** Search the changed area whether or not the index covers it. `unmapped_changed_files` from the script is the explicit worklist for this.
- **Contradiction is reportable.** When revalidation shows the index is wrong, a recorded canonical owner that no longer holds, a representation that is gone, a `settled` owner that is in fact ambiguous, report it in Gaps and correct the index on the next global write. Never silently prefer one source.
- **No metric rewards agreement.** No score, coverage percentage or quality gate may reward index utilisation or citation. Coverage is reported as counts of what was examined, never as a ratio of agreement.

## Who writes it

**Global mode writes `.abstraction-architect/concept-index.json`. Diff mode never writes it in 2.0.**

A diff run sees one change against a partial revalidation. Letting it write would let a narrow view overwrite a broad one and would make the index's provenance depend on whichever review happened to run last. Diff mode reports newly discovered concepts and contradictions in Gaps, and the next global audit consolidates them.

## Schema

```json
{
  "schema_version": 1,
  "generated_from_commit": "abc123...",
  "generated_from_tree": "9f48...",
  "generated_at": "2026-08-10T12:00:00Z",
  "scope": ".",
  "concepts": [
    {
      "concept": "Refund eligibility",
      "kind": "policy",
      "representations": [
        {"symbol": "RefundPolicy.can_refund", "file": "domain/refund_policy.py", "role": "candidate_owner"},
        {"symbol": "SupportRefundService.is_eligible", "file": "support/refunds.py", "role": "implementation"},
        {"symbol": "REFUND_WINDOW_DAYS", "file": "config/refunds.py", "role": "parameter"}
      ],
      "writers": ["RefundPolicy", "AdminRefundSettings"],
      "consumers": ["checkout", "support-api"],
      "canonical_owner": {"status": "ambiguous"},
      "evidence": [
        "same 30-day policy confirmed in three contexts",
        "support implementation bypasses RefundPolicy"
      ]
    }
  ]
}
```

Field notes:

- `kind` is free text describing the concept category, for example `policy`, `entity`, `state`, `vocabulary`, `parameter`.
- `role` on a representation is one of `candidate_owner`, `implementation`, `parameter`, `derived_field`, `mapping`, `consumer`.
- `canonical_owner.status` is one of `settled`, `ambiguous`, `absent`. When `settled`, add `"symbol"` naming the owner.
- `generated_at` is informational and is **never** used as a freshness criterion.
- JSON only. There is no Markdown twin: the report is the human-readable layer, and duplicating the index in prose creates two truths that drift.

## Three distinct notions of change

Freshness and review scope are different questions. Collapsing them produces false freshness.

```
INDEX BASELINE      the commit and tree the index was generated from
REPOSITORY STATE    HEAD plus staged plus working tree, right now
REVIEW DELTA        the change actually under review
```

The hazard a `baseline..HEAD` comparison misses is common and silent: the indexed tree can equal the HEAD tree while uncommitted local modifications are exactly what is under review. That reports `fresh` for an index that does not describe the code being judged. Staged-only work has the same shape.

**Freshness is computed against the repository state. The revalidation set is the union of the index-to-repository drift and the review delta**, because a concept can need revalidation either because the index is behind or because the review touches it.

## Freshness states

Computed from the **tree hash**, never from the date. An index from yesterday can be perfectly valid; one from thirty seconds ago can be stale after a commit. Two commits with the same tree do not make an index semantically stale.

| State | Condition | Behaviour |
|---|---|---|
| `fresh` | indexed tree equals the current tree for the recorded `scope`, and the worktree is clean within that scope | use as a reliable evidence seed |
| `delta-stale` | baseline commit reachable and the delta is computable | the normal case: mark touched concepts dirty, revalidate their neighbourhoods, treat the rest as seed |
| `unusable` | baseline unreachable, history rewritten, incompatible `schema_version`, different `scope`, malformed JSON, not a git repository, or the delta cannot be determined | degrade to diff-anchored discovery and say so in Gaps |

Freshness is never binary. Discarding the whole index on any HEAD movement throws away most of the benefit.

## The script

`${CLAUDE_PLUGIN_ROOT}/skills/abstraction-architect/scripts/concept_index.py`

**The script never discovers concepts.** It validates the schema, resolves the three notions of change above, intersects the delta with indexed file paths, and emits the partition. Every semantic judgement belongs to the agent.

```
SCRIPT (deterministic, Python)          AGENT (semantic, model)
  freshness_state                         semantic discovery over
  index_baseline                            unmapped_changed_files
  repository_state                        new concepts
  review_delta                            semantic neighbourhood of
  changed_files                             dirty_indexed_concepts
  dirty_indexed_concepts                  every promotion to a finding
  unmapped_changed_files
```

`unmapped_changed_files` is what makes the duty of autonomous rediscovery mechanical rather than aspirational. It is the explicit list of changed files that no indexed concept claims, handed over as work to do. Without it, "discover concepts the index does not contain" is an instruction that quietly evaporates on a busy run.

### Invocation

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/abstraction-architect/scripts/concept_index.py" \
  status --index .abstraction-architect/concept-index.json --repo . \
  --changed-files /tmp/changed.txt
```

Modes:

```
validate --index PATH
status   --index PATH [--repo PATH] [--base REF] [--head REF]
                      [--working-tree] [--changed-files PATH]
```

Review delta sources, in precedence order: `--changed-files` (one path per line, which is how `senior-review` passes scope), then `--base` with optional `--head`, then `--working-tree`. With none of them the review delta is empty and only the baseline drift drives revalidation.

### Validate mode

`validate` checks schema conformance of an index file without accessing git:

- Verifies `schema_version` is compatible (currently only version 1 is valid).
- Verifies all required top-level keys are present: `schema_version`, `generated_from_commit`, `generated_from_tree`, `generated_at`, `scope`, `concepts`.
- Verifies per-concept structural validity: a non-empty `concept` name, a non-empty `representations` list, and a `file` field on every representation.

On success, `validate` returns exit code 0 and prints a plain-text line:

```
ok    concept index: 42 concept(s), schema 1, baseline a13fe2f
```

On failure, returns exit code 1 and prints:

```
FAIL  concept index:
         concepts[0]: missing 'concept' name
         Refund eligibility: a representation has no 'file'
```

or, for a schema-level failure such as a missing required key:

```
FAIL  index is missing required keys: generated_from_commit, concepts
```

Plain text rather than JSON is deliberate: `validate` has no machine consumer (the agent invokes `status`, and CI runs the unittest suite, not `validate`), and plain text matches the shape this repository's other checkers already use, for example `scripts/check_version_bumps.py` and `scripts/lint_dependency_graph.py`, both of which print `ok    ...` or `FAIL  ...` lines. Do not "fix" this back to JSON; there is no reader for it.

The key difference from `status`: `validate` returns non-zero only when the index is structurally invalid. `status` always returns zero, even when it reports `unusable`, because for `status` an unusable index is a normal outcome the agent degrades around rather than an error.

### Output

```json
{
  "freshness_state": "delta-stale",
  "reason": "indexed tree 9f48 does not match current tree 3c21",
  "index_baseline": {"commit": "a13fe2", "tree": "9f48", "scope": "."},
  "repository_state": {"head_commit": "92ac10", "head_tree": "3c21", "dirty": false},
  "review_delta": {"source": "changed-files", "files": ["support/refunds.py"]},
  "changed_files": ["config/refunds.py", "support/refunds.py"],
  "dirty_indexed_concepts": ["Refund eligibility"],
  "unmapped_changed_files": []
}
```

All eight output keys are always present in `status` output, including in the `unusable` state. When a key could not be computed, its value is empty (an empty object, empty array, or `null`) rather than absent. A consumer must never test for key presence.

Field notes on the output:

- `changed_files` is the union of the index-to-repository drift and the review delta. It is the input to the partition: `dirty_indexed_concepts` and `unmapped_changed_files` are computed from it, and together they account for all of it. The two differ from `review_delta.files` only when the index is stale. When the index is `fresh`, `changed_files` and `review_delta.files` are equal.

Exit code 0 on success including `unusable`, 2 on bad invocation. An `unusable` result is a normal outcome, not an error: the agent degrades and reports it.

**On script failure or missing Python, treat the index as `unusable`.** Never assume `fresh`.

## What Gaps must say

Report numbers, not adjectives:

```
Concept index baseline: a13fe2      Current HEAD: 92ac10
Delta determined: yes               Indexed concepts revalidated: 4
Unindexed changed concepts discovered: 2
```

Or, degraded:

```
Concept index unavailable (baseline commit a13fe2 not reachable).
Knowledge-track coverage used diff-anchored discovery only;
global competing-authority coverage was not attempted.
```
