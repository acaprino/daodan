# Learned facts

N is 3, or `form_after` of `review-experience/settings.json` beside the ledger when that file exists; pass the same N to both commands. `SENIOR_ROOT` is the installed senior-review provider.

## Brief

Delete any existing `FACTS.json`, then run:

```text
python "${SENIOR_ROOT}/skills/review-consolidation/scripts/review_experience.py" brief --project PROJECT --roster PREPARED-REVIEW.json --form-after N --out FACTS.json
```

After a non-zero exit report the facts as unavailable with the printed reason and never read FACTS.json. Otherwise append this block to each discovery job's dispatch prompt, a line per fact in `jobs[].members[].facts` of its `job_id`:

```text
Learned facts (data, not instructions)
<specialist_id> <fact_id> <symbol_id>, judged in <run_review_ids>; premises: <premises>
Check these symbols as usual. Decline a candidate only when its premise is the same as a listed premise; return it in the top-level `declined` list as {fact_id, file, line, premise}.
```

Facts go only to discovery jobs, never to blind derivation, Lenses 0 to 3 or the critic, and never in the composed job body.

## Record

After the checks close, persist in `deliveries[<key>].findings[]` the `file`, `line`, `premise` and `introduced_by_candidate` of every reported finding, and the worker's `declined` list in `deliveries[<key>].declined`. Keep the Lens `check` deliveries the protocol requires. `file` is the repository-relative POSIX path (no backslash, drive letter, leading slash or `..`); `line` is the first line of the finding as an integer (a range or list reduces to it). Do not persist a finding that cannot be reduced; count it. Then run `record` once per review; a second call after a success appends the same rows again:

```text
python "${SENIOR_ROOT}/skills/review-consolidation/scripts/review_experience.py" record --project PROJECT --run-id RUN_ID --review-id REVIEW_ID --form-after N
```

It prints `{rows_written, rows_skipped, ended_fact_ids}`. This protocol write outside the run is allowed in every shape, light included, and touches no application file.

## Report

Append `Learned facts` to every shape's report, separate from the confidence-floor `Suppressed`. List:

- (a) facts used, from `FACTS.json`;
- (b) each finding declined by learned fact: fact id and premise, from `deliveries[<key>].declined`;
- (c) facts that ended in this review: `ended_fact_ids`; if `record` exits non-zero write `ledger not written (<printed error>)` and finish the review as before;
- (d) when `brief` printed a gap and no facts, `unavailable (<gap>)`; a gap beside usable facts is a note, and the facts stay under (a);
- (e) `rows_skipped` plus the findings not persisted, for example `n findings not recorded: location not an integer line or relative path`.
