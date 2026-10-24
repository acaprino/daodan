# External corpus expansion plan

## Objective

Expand the reviewer-routing benchmark beyond the eight Jupiter snippets before
changing any question wording. The target is a frozen pool of 48 to 60 unique
real-source cases, split by project, with source-backed positive and explicit
negative judgments for the eight model lenses:

- `security-auditor`
- `data-integrity-auditor`
- `temporal-resilience-auditor`
- `resource-lifecycle-auditor`
- `ui-race-auditor`
- `distributed-flow-auditor`
- `logic-integrity-auditor`
- `cleanup-auditor`

The fixed `code-auditor` and filename-based TypeScript/React selections remain
outside the model comparison, as in the current follow-up.

This stage does not tune prompts, run the model, or change production routing.

## Source inventory

| Source | Verified access and fields | Label signal | Planned use | Main limit |
| --- | --- | --- | --- | --- |
| SWE-bench Verified, `princeton-nlp/SWE-bench_Verified` | Hugging Face rows API; 500 test rows; fields include `repo`, `base_commit`, `patch`, `test_patch`, `problem_statement`, `FAIL_TO_PASS`, `PASS_TO_PASS`; parquet download is about 2 MB | Human-validated GitHub issue/PR pairs; issue text and tests are external evidence for adjudication | Main pool for logic, data, temporal, resource and distributed cases in Python | Python only; issue text must never enter the model state |
| Multi-SWE-bench, `ByteDance-Seed/Multi-SWE-bench` | Hugging Face dataset with per-repository JSONL files; 1,632 instances across Java, TypeScript, JavaScript, Go, Rust, C and C++ | Expert-curated issue/PR pairs | UI, distributed, logic and resource cases outside Python, especially TypeScript/JavaScript repositories | Large aggregate storage; fetch only selected repository files or rows |
| Devign, `DetectVul/devign` | Hugging Face rows API; test split has 2,732 rows; fields include `func`, `target`, `project`, `commit_id`, vulnerable-line data | Function-level vulnerable/non-vulnerable labels from FFmpeg, QEMU, Linux and Wireshark | Security positives and security-only explicit negatives | C/C++ only; a non-vulnerable label does not label the other seven lenses |
| CVEfixes v1.0.8 | Zenodo DOI `10.5281/zenodo.13118970`; 12,107 vulnerability-fixing commits, 4,249 projects, 11,873 CVEs, 272 CWE types; data CC BY 4.0 | CVE/CWE provenance at commit, file and method level | Security provenance and later targeted security examples | The Zenodo ZIP is 12,708,711,268 bytes; do not download it for the first pool unless a selective query path is justified |
| HaPy-Bug | GitHub `ncusi/HaPy-Bug`; 793 Python bug-fix commits with annotations from three experts, including file purpose, line categories and confidence | Human annotation and linked bug/CVE descriptions | Small high-confidence development pool and label-protocol checks | Python only; annotations describe changes, not reviewer applicability directly |
| CommitBench, `Maxscha/commitbench` | Hugging Face rows API; fields include `hash`, `diff`, `message`, `project`, `split`, `diff_languages`; test split has 249,688 rows | Real diffs plus commit messages as weak label evidence | Backup candidate generation for cleanup and broad diff shapes | Dataset license is CC BY-NC 4.0; keep out of any commercial path and do not use it as gold labels |
| Public GitHub repositories | Git history and issue/PR pages for permissively licensed projects | Commit, issue, PR and test evidence at a pinned revision | Fill gaps left by packaged datasets, especially cleanup and UI cases | Mining and label adjudication cost; record the project license for every case |

## Sampling target

Build the pool by assignments, not by raw row count. A multi-label case can
cover several lenses, so 48 to 60 unique cases should provide:

- at least 6 positive assignments per lens;
- at least 4 positive assignments per lens in development and 2 in verification;
- at least 24 explicit negative assignments across the pool;
- at least 8 cases with no expected specialist lens;
- at least 12 projects, with no project contributing more than 15% of cases;
- verification projects disjoint from development projects for every lens
  where the source pool allows it;
- Python plus at least three other languages, including TypeScript or
  JavaScript for UI cases.

Prefer one or two input windows per case for the first external run. Record
larger candidates as excluded by the input-size rule rather than silently
truncating them.

## Label protocol

Labels are applicability judgments for the shown code, not claims that the code
is defective.

1. **Candidate generation.** Select candidates from source-native signals:
   CVE/CWE records, vulnerable-function targets, issue statements, linked pull
   requests, test names, commit messages and reviewer comments. Store those
   signals only in provenance.
2. **Gold labels.** Use dataset-native labels where they directly answer the
   lens question, for example a vulnerable-function target for
   `security-auditor`.
3. **Silver labels.** Use explicit source text where it directly states the
   concern, for example an issue describing a stale cache, a retry storm, a
   dropped failure event or a connection leak.
4. **Adjudication.** For every remaining lens on a selected case, assign
   positive, explicit negative or unknown from the source evidence and the
   shown code. Unknown roles are omitted from scoring; they are never converted
   to negatives.
5. **Ambiguity rule.** If the external evidence does not settle a lens, leave it
   unknown or reject the candidate. Do not fill gaps from the prompt author's
   intuition alone.
6. **Separation.** `cases.json` keeps expected roles, negative roles, rationale
   and provenance. Model jobs receive only the opaque case ID, source path and
   range, and code text. They never receive issue text, CVE identifiers, commit
   messages, test names, case titles or expected roles.

## Input protocol

- Use the pre-fix function or the old side of the fixing diff, matching the
  historical benchmark's convention.
- Keep the current lossless per-file windows and the 2,800-character window
  rule for comparability.
- Keep handwritten module context out of external cases. A later grounding
  experiment must use provenance-bearing map cards, not summaries written for
  the benchmark.
- Deduplicate by repository plus commit, and by normalized function or diff
  hash.
- Record the upstream project license and the dataset license separately.

## Stages and gates

### Stage 1: source inventory and candidate pool

`external_corpus.py inventory` and `external_corpus.py pool` generate this stage.
The candidate pool may overgenerate relative to the 48 to 60 frozen cases; its
role lists are source-signal proposals for adjudication, not benchmark labels,
except for Devign's dataset-native security target.

Deliverables:

- `external_sources.json`: source identity, revision or dataset SHA, access
  method, fields, license, label signal and known limits;
- `candidate_pool.json`: selected candidates with code, source provenance,
  label evidence, proposed split and label status (`gold`, `silver` or
  `needs-adjudication`);
- a short label packet listing every ambiguous candidate and the external
  evidence needed to settle it.

Gate: no model calls. Do not proceed if a family's positives come from one
project only or if explicit negatives are missing.

### Stage 2: label freeze

Deliverables:

- frozen `cases.json`, `jobs.json`, `prompts.json` and `plan.json` for the
  external run;
- label rationales tied to source evidence for every positive and explicit
  negative role.

Gate: verification cases are locked before any model output is inspected.
Any verification case later used for tuning moves to development, and the
verification partition is replaced with fresh projects.

### Stage 3: frozen slot-restore run

Run the current V2 and candidate questions on identical windows in slot-restore
mode. Report, separately for development and verification:

- expected-role recall by lens;
- explicit-negative activations by lens;
- abstentions and invalid outputs;
- model selections versus fixed filename/generalist selections;
- calls, latency, sampled memory and input coverage.

Gate: question wording changes are proposed only from development outcomes.
Verification outcomes decide whether a frozen change generalizes; they are not
used to rewrite the same change and retest it on the same cases.

## Stage 1 status

Built in `runs/20261021-external-corpus-stage1/`:

- `source_inventory.json`: six sources with live Hugging Face or Zenodo metadata;
- `candidate_pool.json`: 72 candidates from 31 projects: 24 SWE-bench Verified,
  24 Multi-SWE-bench, 12 Devign and 12 CommitBench backup candidates;
- split proposal: 39 development and 33 verification candidates;
- validation: `external_corpus.py validate` passed; every stored input hash
  matches its text and no candidate carries frozen `expected_roles` fields.

Only the 12 Devign security judgments are gold. All other role lists are
source-signal proposals for adjudication. Signal proposals are intentionally
noisy: distributed-flow appears often because issue and patch text mentions APIs,
clients and servers, while cleanup and temporal proposals remain thin. Stage 2
must adjudicate from source evidence and fill those families before any label
freeze.

## Stage 2 status

`external_corpus.py label-packet` built `label_packet.json` and
`label_packet.md` in the same Stage 1 run directory. The packet groups all 72
candidates by lens and records one adjudication state per lens.

Only Devign security is gold: 6 positives and 6 explicit negatives. Every other
positive is `proposed_positive_silver` or `proposed_positive_weak`; every
non-Devign negative is only `candidate_negative_from_absence`, which is not
usable as an explicit negative. Inspection of the packet confirms that several
silver proposals are false text signals, especially for temporal, resource and
cleanup. They must be adjudicated or rejected from the external evidence, not
converted mechanically into labels.

## Stage 2 adjudication status

`external_corpus.py adjudicate` wrote `adjudicated_candidates.json` and
`ADJUDICATION.md`. It accepts non-Devign positives only from external evidence
(issue, PR or commit text), never from patch keywords alone.

The original pool alone did not pass the freeze gate: resource had no accepted
positives, cleanup had one, temporal had two, and data-integrity and ui-race
had five each. A targeted fill from external evidence only (`fill_candidates.json`)
added adjudicated positives for those families. The combined gate in
`combined_gate.json` now passes:

| Lens | Accepted positives | Explicit negatives | Positive projects |
| --- | ---: | ---: | ---: |
| security | 8 | 62 | 4 |
| data-integrity | 13 | 31 | 9 |
| temporal-resilience | 6 | 43 | 4 |
| resource-lifecycle | 6 | 45 | 5 |
| ui-race | 11 | 40 | 6 |
| distributed-flow | 30 | 12 | 15 |
| logic-integrity | 8 | 33 | 6 |
| cleanup | 7 | 56 | 6 |

Distributed-flow remains overrepresented because external issue text often
mentions APIs, clients and servers; it needs down-selection, not more
candidates. Passing this gate does not freeze labels or authorize a model run.

## Freeze status

`external_corpus.py freeze` down-selected the combined adjudicated pool to
52 cases: 27 development and 25 verification. The frozen selection preserves
at least six positives per lens, at least two positive projects per lens and
more than 24 explicit negatives. Distributed-flow was down-selected from 30
accepted positives to 12 in the frozen set. The executable freeze is
`runs/20261021-external-corpus-frozen-run/`; its `plan.json` records the
`gutsy_followup.py` runner hash. The earlier
`runs/20261021-external-corpus-frozen/` directory is the same selection with a
pre-fix runner hash and is superseded. `cases.json`, `jobs.json` (1,312 jobs),
`prompts.json` and `plan.json` are frozen and hash-verified.

## Stage 3 status

Stage 3 ran on `runs/20261021-external-corpus-frozen-run/`: all 1,312 planned
calls returned a valid letter, prefix reuse was verified on every call, and the
sampled combined peak was 972,275,712 bytes.

The result is negative for both question variants:

| Variant | Expected found | Explicit negatives activated | Mean model selections per case |
| --- | ---: | ---: | ---: |
| V2 | 7/63 (11.1%) | 12/214 | 0.60 |
| Candidate | 7/63 (11.1%) | 5/214 | 0.46 |

Security and data-integrity were missed everywhere (0/6 and 0/11 for both
variants). The candidate found distributed-flow more often (6/12 against 0/12),
but did not improve total recall. This does not support tuning wording on the
verification split.

Interpretation: the external labels were adjudicated mainly from issue, PR,
commit and dataset evidence, while the model received only pre-fix code or
old-side diff fragments. Many accepted positives are therefore not visibly
decidable from the shown code alone. The external corpus measures a different
target from the Jupiter function-applicability cases unless the label protocol
also requires code-visible applicability.

The development-only visibility audit (`VISIBILITY_AUDIT.md` in the frozen run)
classifies 32 development positives as: 2 with a visible code signal, 9 with a
weak code signal and 21 with no code signal, meaning the label is knowable only
from external evidence. Cleanup is external-only in all 4 development positives;
data-integrity is external-only in 5 of 8.

## Blind code-only audit status

`external_corpus.py score-blind` scored two independent blind code-only readers
(`blind_reader_1.json` and `blind_reader_2.json`) against the hidden key and
the frozen model answers in `BLIND_AUDIT_RESULTS.md`:

- **Inter-reader agreement:** `264/280` slots (`94.3%`) across all 35 items x 8 lenses.
- **Jupiter rubric calibration gate (`J01`..`J08`):** **passed** (`11/11`
  positives recovered by both readers, `0/30` explicit negatives activated by
  either reader).
- **External development positives (`32` assignments across `D01`..`D27`):**
  - `code_supported` (both readers `applicable`): **9 / 32 (28.1%)**
  - `disputed_applicable` (one reader `applicable`): **2 / 32 (6.3%)**
  - `insufficient_or_external_only` (both `insufficient_evidence`): **4 / 32 (12.5%)**
  - `code_not_applicable` (both `not_applicable` on the shown snippet): **17 / 32 (53.1%)**
- **Frozen-model recall by visibility stratum:**
  - On `code_supported` (`9` assignments): V2 `2/9 (22.2%)`, Candidate `1/9 (11.1%)`.
  - On the remaining `23` assignments: V2 `1/23 (4.3%)`, Candidate `2/23 (8.7%)`.

Conclusion: both effects are present. First, **21 of 32 external development
positives (`65.6%`) are judged by both blind readers as either not applicable to
the shown snippet (`17`) or insufficient without external context (`4`)**,
confirming that issue/commit keyword adjudication over-assigns lenses that are
not supported by the old-side diff fragment alone. Second, even on the **9
code-supported external positives**, frozen-model recall remains low (`2/9` for
V2, `1/9` for Candidate), showing that fragmentary old-side diff inputs and
prompt/model sensitivity also limit recall when a human reader can see the lens.

## Immediate next action

Rebuild the external development benchmark around whole enclosing functions (or
expanded context hunks) and `code_supported` applicability labels from the
blind audit before any further question tuning. Keep the verification partition
locked.
