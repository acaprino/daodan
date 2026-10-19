# Daodan Economy-Model Vibe and Cycle Harness Upgrade Plan

> **For agentic workers:** REQUIRED: use `superpowers:subagent-driven-development` (if subagents are available) or `superpowers:executing-plans` to implement the open items. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** make a fast, low-cost model working inside Daodan reach the same or better outcomes than the same task done by an unassisted frontier model, in both the fast interactive loop (vibe) and the structured lifecycle loop (assess, change, repair, verify, consolidate).

**Thesis, stated as a hypothesis.** Much of what separates a frontier model from an economy model on a code task is navigation and memory: finding the right passage without reading twenty files, remembering which callers depend on a signature, and noticing that an edit changed a contract. Those are lookups. `codebase-map` can answer them deterministically and cheaply (Python and SQLite, no tokens), so the model spends its context on the edit. Nothing in this plan has been measured against that thesis yet. Section 5 defines the measurement, and no cost or token figure below is a result.

---

## 1. Status

Implemented and verified in this repository (uncommitted at the time of writing):

| Item | Where | Evidence |
|---|---|---|
| Inventory of contract, build, infrastructure and template files | `snapshot.py` `DOC_EXTENSIONS`, `PRESENTATION_EXTENSIONS` | `tests/test_xray_snapshot.py` `PresentationInventoryTests` |
| `edit_impact` packet: digests, card, one-hop callers and callees with cards, blind spots, recent changes, verified source | `semantic_store.build_edit_impact`, CLI `snapshot.py edit-impact`, MCP `codebase_map_edit_impact` | `tests/test_codebase_map_edit_impact.py` (12 tests, two checked by mutation) |
| Read-only Meta-Code query over MCP | MCP `codebase_map_meta_query` | same file |
| Go as a parsed language, through the whole chain | `languages/go.py` and its registrations | `tests/test_xray_go.py` (15 tests) |
| Project-level card store; freshness computed at read time against any snapshot | `card_store.py`, `semantic_store.upsert_meta_cards` / `query_meta_code` | `tests/test_codebase_map_card_store.py` (22 tests, one checked by mutation), `tests/test_codebase_map_storage.py` |
| Incremental SQLite reuse, triple-hash symbols, bounded changesets | shipped in `codebase-map` 7.1.0, `effects_hash` corrected in 7.2.0 | `tests/test_codebase_map_storage.py` |

### Corrections to earlier statements

An earlier draft of this plan, and some messages that led to it, contained errors that were checked against the code and are corrected here:

- `.xml` was already inventoried. `.bash`, `.zsh`, `.mdx`, `.adoc` and `.conf` were not, and were never listed as present in the code. `PRESENTATION_EXTENSIONS` held only `.htm .html .sass .svelte .vue`.
- The PL/SQL extensions are `.pks .pkb .plsql .pls .pck .prc .fnc .trg`. Python is `.py .pyi`.
- `FORBIDDEN_GLOBS` filters by file name only (`.env`, `*secret*`, `*credential*`, keys, keystores, tfstate). It does not filter `*password*`, `*token*` or `*apikey*`, and nothing filters by content.
- The earlier cost and token table ($0.15 to $0.80 per run, 85 to 95% reduction, 4K to 12K tokens per turn) had no measurement behind it and is withdrawn.
- A card write into a run's snapshot changes the digest of its bytes. `snapshot.py` binds inherited artifacts and child runs to that digest (`_valid_inheritance`), so such a write breaks resume and inheritance. The `meta-upsert` shipped in 7.1.0 had this defect. Cards no longer live in any snapshot (section 3). Cards written by 7.1.0 sit in `meta_cards` tables of old snapshots and are not migrated.
- `effects_hash` in 7.1.0 hashed positional target ids (`function@4:0`). An edit that added a line to one function renamed every callee below it, so an untouched caller read as changed and its card as stale. This contradicted the claim that a body-only edit does not invalidate callers. Targets are now named by file and qualified name. The first test of the card store found it.
- The 7.1.0 documentation listed a `relocated` delta kind that does not exist, and said `PRAGMA auto_vacuum = INCREMENTAL` reclaimed freed pages. No code ran `incremental_vacuum`, and every refresh writes a new file, so there are no free pages. The pragma is removed and the text corrected.

---

## 2. Decisions taken while implementing

1. **Secrets.** `.properties`, `.config` and `.tfvars` were left out of the inventory on purpose. They routinely hold passwords and the forbidden list cannot see content. `.ini`, `.toml`, `.yaml` and `.json` are already inventoried, so this limits the exposure rather than removing it.
2. **One language at a time.** The adversarial review of the first proposal (`.tritech/local/moe/20261018-proposal-review/answer.md`) rejected batching ten adapters. Go went first, with the complete chain (extensions, dispatch, comment lexer, parser profile, braced-language set, call query, formatter, classifier patterns, tests, docs). The next language repeats the same checklist.
3. **No `context_mode` and no cards inside `read_packet`.** The reader's context rule is pinned by tests that require sibling declarations to stay visible, and `ranges` already gives a raw interval. The impact packet is a separate read-only tool.
4. **Interface methods are not callables.** The first Go adapter recorded them as `method` symbols, and a one-line signature then pushed the reader back to the whole file for every interface. Members now live in `class_variables`.
5. **No card writes over MCP.** Cards cannot be written through a run. See section 3.

---

## 3. Decision: where cards live

Cards used to sit inside the run's snapshot, which is immutable evidence, so no workflow could write them. They now live in one project-level file, `cards.sqlite`, in the analysis root beside `runs/`. Each card stores the digests of its symbol (body, interface, effects) and of its callees' interfaces as they were when it was written. Freshness is computed when a card is read, by comparing those digests with the snapshot being queried. Nothing is carried forward, a card survives any run, and it goes back to `fresh` when the code returns to what it described. See [the guide](../../plugins/codebase-map.md#cards).

- [x] **3.1** Decide: project-level store.
- [x] **3.2** Add the store, move writes and freshness to it, remove `meta_cards` from the snapshot schema.
- [ ] **3.3** Change the `map-method` instructions so analysis workers write cards for hubs, entry points and critical-path symbols, and `update` skips fresh cards. `SKILL.md` is at its 835-word cap, so the instruction belongs in a phase unit, with the load-budget test updated deliberately.
- [ ] **3.4** Decide whether MCP should write cards. It does not today: the shell command is enough on every host that can run workers.

---

## 4. Remaining work

### Phase 1: coverage

- [ ] **1.A** Next languages, each through the full checklist of section 2, in this order of value: Kotlin (the repository ships `kotlin-development`), C#, C and C++, then PHP, Ruby, Swift, Dart, Scala. A regex-only language must record start lines only, so its spans are inferred and reads use the whole file.
- [ ] **1.B** Decide whether to inventory `.properties` and `.config` behind a content guard. Do not add them without one.
- [ ] **1.C** Resolve Go imports through `go.mod` so Go files get import edges. Until then Go has symbols and selective reading but no callers and callees.

### Phase 2: edit-time packets

- [x] `edit_impact` and `meta_query` (CLI and MCP).
- [ ] **2.A** Measure the packet on a real repository: bytes per target, and how often a caller or callee is missing because the reference was unresolved. The 8 KB budget in the tests covers a four-file fixture only.
- [ ] **2.B** Add a post-edit check to the workflows: after a refresh, list symbols whose `interface_hash` or `effects_hash` changed and whose one-hop callers were not in the edit set. The data is in `meta_changeset_deltas`; the workflow instruction is missing.

### Phase 3: workflows consume the map

- [ ] **3.A** Step 3.3 above.
- [ ] **3.B** Retire the per-run duplication of `manifest.sqlite` for incremental updates, or state why runs stay.

### Phase 4: downstream plugins

- [ ] **4.A** `project-lifecycle` `change` and `repair`: order steps callees first along resolved edges, and hand the worker the impact packet for its target.
- [ ] **4.B** `senior-review` preparation: scope auditors by `body_only` versus `interface_changed` and `effects_changed`, adding the one-hop callers for the latter. The map supplies leads; the auditor confirms by reading.
- [ ] **4.C** `project-knowledge`: use stale cards and changed digests to find the documentation that drifted.

Every plugin change follows the marketplace workflow in `CLAUDE.md`: bump the plugin version, bump `metadata.version`, rebuild, run the gates, commit together.

---

## 5. How the thesis gets tested

The claim is that an economy model with the harness matches or beats a frontier model without it. Test it, do not assume it.

- **Tasks.** A fixed set of change and bugfix tasks on two or three real repositories in different languages, with an objective oracle each (tests that fail before and pass after, plus a hidden regression check on a caller).
- **Arms.** Frontier model alone, economy model alone, economy model with the packet and the post-edit check. Same prompts, same budget cap, same seed policy where the host allows one.
- **Measures.** Solve rate, regression rate on the hidden caller check, input and output tokens as reported by the host, wall time, and cost computed from the provider's published prices on the day of the run.
- **Rule.** A result that is not measured stays out of the documentation. The earlier pilot (`analysis-speed-pilot-verdict` in project memory) showed how a headline number can come from low uptake and a ceiling effect rather than from the tool, so record how often the model actually called the packet.
- [ ] **5.A** Write the task set and the oracle scripts under `evals/codebase-map/`.
- [ ] **5.B** Run the three arms and record the result, including a negative one, in `evals/codebase-map/RESULTS.md`.
