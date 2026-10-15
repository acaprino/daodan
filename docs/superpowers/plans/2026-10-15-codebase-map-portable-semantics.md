# Portable semantic references and import graph diagnostics

The approved increment improves the existing portable engine. It covers Python
stdlib AST and optional JavaScript/TypeScript Tree-sitter references, callsite
positions and conservative declaration links, plus import cycles and transitive
reachability. It excludes Tri-Tech integration, embeddings, new language adapters,
compiler type inference and a mandatory SQLGlot dependency.

## Compatibility and evidence contract

Keep `symbols`, `calls_made`, existing usage fields and the one-hop incremental
update recommendation readable. New metadata is additive. A lexical match, an AST
reference and a resolved static binding are distinct facts. None proves execution.

`ParseResult.semantic: dict | None = None` is additive. Native Python and JS/TS
adapters populate the payload from their already-parsed tree. Regex adapters
leave it absent, as does damaged native syntax.
The manifest serializes it with the same raw source hash and helper fingerprint.
The payload contains JSON primitives:

```json
{
  "version": 1,
  "backend": "stdlib-ast",
  "status": "ast",
  "notes": [],
  "scopes": [{"id": "module", "parent": null, "kind": "module"}],
  "declarations": [
    {"id": "function@1:0", "name": "save", "kind": "function", "scope": "module", "span": [1, 0, 2, 8]}
  ],
  "imports": [
    {"scope": "module", "local": "persist", "module": "core", "imported": "save", "mode": "named", "span": [4, 0, 4, 39]}
  ],
  "exports": [{"exported": "save", "local": "save"}],
  "references": [
    {"scope": "module", "parts": ["persist"], "kind": "call", "span": [5, 0, 5, 7], "caller": null}
  ]
}
```

Lines are one-based, UTF-8 byte columns zero-based, and span ends exclusive.
Declarations have source-local IDs qualified by file path in the project index.
IDs describe this snapshot; they are not cross-revision citation anchors.
Bindings include parameters and assignments so shadowing blocks outer imports.
Repeated bindings remain ambiguous. Unsupported forms carry notes or unresolved
reasons rather than guessed targets. A call reference is its callsite; repeated
calls retain separate locations and their nearest callable owner.

## Resolution and usage behavior

The resolver consumes semantic payloads and the existing `resolved_imports`
mapping. It does not independently interpret project configurations. Unique
lexical function/class declarations, named/default import aliases and imported
namespace members can resolve to declaration IDs. Dynamic receivers, computed
properties, constants, re-export chains and ambiguous overloads/redefinitions
retain unresolved reasons. Type-only imports cannot create resolved call edges.

Inspect all permitted semantic entries so a renamed import can be found without
the original symbol text at the callsite. Keep bounded lexical results for
unsupported or unavailable backends and mark their precision explicitly. Expose
resolved reference counts separately from lexical or unresolved candidates.
Source identities and current helper fingerprints gate exact source locations.
`build_manifest(..., source_observations=...)` captures the bytes already read,
keyed by manifest-relative path. Index consumers reuse those observations or
read live permitted sources once. Hash, fingerprint, payload shape, scope and
span validation prevent stale or malformed metadata from asserting targets.
Observation reuse applies to that source operation, not future filesystem
freshness. The target keeps its single read/parse path; the established inventory
perimeter does not expand.

The file analyzer exposes `semantic_analysis` independently of `--find-usages`,
with declarations, outgoing callsites, resolved incoming calls, source identity,
per-file and project coverage, and separate resolved/unresolved call counts.
Optional usage results retain their total but add `resolved_count`,
`ast_candidate_count` and `lexical_candidate_count`. Locations expose precision,
span, caller, target and uncertainty. Unresolved candidates do not prove a
declaration is used, and an empty incoming list does not establish dead code.

## Import graph diagnostics

`dependency_graph.py` consumes the existing resolved file graph, with edges from
importer to dependency, without reading source. It computes deterministic
strongly connected cycle components, including self edges, using iterative
traversal. Reverse reachability emits `{file, depth, via, seed}` with shortest hop
counts and a deterministic immediate predecessor and seed for reconstructing a
witness. Seeds are omitted from results, and missing targets gain no invented
edges. Deep chains avoid Python recursion limits.

Keep the current one-hop `importers`, `affected_files`, claim invalidation and
recommendation unchanged. File analysis and change reports expose cycles,
transitive importers and PageRank as separate diagnostics. PageRank defaults to
damping 0.85, L1 tolerance 1e-10 and a maximum of 100 iterations, with uniform
teleportation and redistributed dangling-node mass. The output includes all
parameters, iteration count and convergence status, including a final iterate
that reached the limit. Centrality is an architectural reading aid and does not
automatically classify a file as product-critical.

## Reuse and dependency decisions

Reuse Python's standard-library AST, the installed optional Tree-sitter
grammars and the existing confined import resolver. They provide syntax and
module targets, but not this source-bound cross-file declaration contract. The
new layer deliberately handles only unique direct bindings. A compiler or LSP
would add language-specific processes and project dependency requirements beyond
this portable scope; it would not remove the need to represent uncertainty.
[Stack Graphs](https://github.com/github/stack-graphs) was archived by its owner
on 2025-09-09 and declares that GitHub no longer supports or updates it, so it is
not introduced as a new foundation.

The graph helper uses standard-library containers and numerical primitives.
[`graphlib`](https://docs.python.org/3/library/graphlib.html) provides topological
ordering rather than SCC enumeration or PageRank. Adding NetworkX for this small
fixed graph contract would break the stdlib-only helper constraint. The two
bounded algorithms keep their parameters, edge direction and convergence
observable rather than introducing a general graph framework.

SQLGlot remains a separate SQL/PLSQL evaluation, without a product dependency.
Oracle dialect support alone does not demonstrate procedure/package coverage;
that coverage needs a representative corpus and independent expected results.
No host-specific integration, embedding model or new language adapter is added.

## Precision cost

Semantic extraction enriches eligible snapshots by default and adds traversal
time and metadata size despite reusing the parsed tree. The measured sample and
environment are recorded in the engine documentation's
[performance section](../../plugins/codebase-map.md#bounded-work-and-performance).
It compares the same adapters with and without the semantic hook, using one real
Python source and generated JS/TS functions, warm grammars and nine repetitions
per mode. The observed overhead is a cost for richer evidence, not a repository
speedup or a scaling claim. Index construction and graph diagnostics add their
own project-wide work and are not covered by that adapter-only measurement.

## Owners and delivery order

1. Syntax worker owns `languages/base.py`, Python/JS/TS adapter hooks, new
   `languages/semantic.py` extraction and dedicated syntax tests.
2. Resolver worker owns `semantic_index.py`, `usage_finder.py` and dedicated
   resolver tests. Tests use the agreed metadata contract while extraction is
   implemented independently.
3. Graph worker owns `dependency_graph.py` and dedicated graph tests.
4. Coordinator owns manifest serialization/fingerprint, file/change report
   integration, documentation, versions, generation and publication.

Workers edit only the isolated LF candidate. The primary checkout contains
unrelated atomic-method changes. Publication carries only owned engine edits;
the primary `snapshot.py` content beginning at `cmd_carry` is foreign and must
retain its current bytes. Generated host exports are compiler output.

## Observable acceptance and verification

- Comments, literal strings, substrings, unrelated receivers and shadowed names
  produce no resolved references to the original declaration. Expressions in
  formatted/template strings remain code.
- Python and JS/TS aliases and namespace imports resolve to the correct file,
  even when two modules export the same spelling. Rebinding stays uncertain.
- Repeated calls, nested callables and non-ASCII prefixes retain correct owners
  and positions. Malformed files and missing grammars remain explicit fallback.
- Stale bytes, changed fingerprints, old manifests and excluded paths cannot
  supply authoritative semantic references. Existing one-read/parse and batch
  regressions continue to pass.
- Graph chains, diamonds, self/mutual cycles, removed files and long chains have
  deterministic results. A regression proves the one-hop recommendation remains
  unchanged while transitive diagnostics expose additional reachable files.
- Measure metadata size and parsing time on a documented representative input;
  do not infer a speedup or runtime coverage from structure alone.
- Run meaningful native and forced-fallback checks, the full repository suite,
  linters, instruction/documentation parity and all five generated-host gates.
  Resolve independent review findings, preserve foreign bytes, bump versions,
  publish the verified candidate and verify CI for its exact commit.
