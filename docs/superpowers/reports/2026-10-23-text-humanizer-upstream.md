# Text-humanizer: selective upstream reconciliation

## Scope and source

User-authorized update of Daodan's existing derivative of
[blader/humanizer](https://github.com/blader/humanizer), preserving local behavior
and adding realistic Italian guidance. No new upstream dependency, copied plugin,
sync-table row, commit or publication is authorized by this change.

Primary sources read at commit `8c307f367c91bd974002f10f2be2965d642c13df`
(16 October 2026):

- [SKILL.md](https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/SKILL.md), metadata version 3.1.0, 26 upstream patterns.
- [CHANGELOG.md](https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/CHANGELOG.md), including the 3.0.0 consolidation and 3.1.0 extensions.
- [LICENSE](https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/LICENSE), MIT, Copyright (c) 2025 Siqi Chen. The notice and license are bundled under the owning skill's references.
- [README.md](https://github.com/blader/humanizer/blob/8c307f367c91bd974002f10f2be2965d642c13df/README.md), including cross-agent installation guidance. The earlier claim that external delegation was inherently Claude-only was unsupported. No installed-host execution was verified here.

This is a reconciliation of an existing derived skill, not a full domain refresh.
The Wikipedia revision and Italian research citations inherited from the previous
refresh were not reverified. The prior attribution said v3.1.0 had been reconciled;
the local catalog did not fully express its reply-context guidance. Different
pattern counts alone do not prove incomplete adoption because local grouping differs.

## Mapping and decisions

Local numbering stays stable, with one new pattern (25). Upstream numbers are not
local IDs. The earlier proposed edits to local patterns 2 and 12 were misnumbered:
the closer extension belongs to local 24; compound-hyphen safeguards belong to 13.

| Upstream 3.1.0 | Local owner | Reconciliation |
|---|---|---|
| 1: contrast | 9 | Keep real corrections and meaningful alternatives; include split contrasts. |
| 2: closers | 24 | Include dramatic fragments and post-example repetition; preserve new consequences. |
| 3: sayings that sound deep | 1, 22 | Existing significance and filler rules; preserve facts beneath rhetoric. |
| 4: staged run-up | 9, 22 | Existing staged-reveal and opener guidance. |
| 5: arguing with no one | 9 | Add explicit protection for actual objections and plausible alternatives. |
| 6: forced triads | 10 | Include paragraph-scale examples; keep every substantive item. |
| 7: repeated openings | 10, second pass | Include repeated sentence openings; preserve deliberate repetition. |
| 8: dashes | 13 | Retain stricter local connector ban and protected code, compounds, dialogue and ranges. |
| 9: qualifiers | 23 | Keep genuine uncertainty, scope and legal/safety notices. |
| 10: hyphenated pairs | 13, Italian profile | Protect dictionary spelling. Do not import English compound-modifier rules into Italian. |
| 11: passive voice | 8, second pass | Prefer clarity only when the actor is known; no blanket active-voice rule. |
| 12: AI words | 7, Italian profile | Existing cluster-sensitive lists; no English word-list translation or blanket lexical bans. |
| 13: significance | 1, 6, 24 | Existing local split, no renumbering. |
| 14: vague association | 5 | Existing association phrases; never invent a relationship. |
| 15: -ing riders | 3 | Existing rider rule and Italian gerund equivalents. |
| 16: sales language | 4 | Existing promotional-language rule. |
| 17: borrowed authority | 2, 5 | Preserve supported media, reach and source details rather than copying lossy upstream examples. |
| 18: copula avoidance | 8, Italian profile | Keep actual semantic distinctions, not mechanical verb replacement. |
| 19: bold | 14, 15 | Preserve table structure and useful reference lists. |
| 20: headings | 16, 17 | Add headings written for effect; protect names, titles and linked anchors. |
| 21: quotes | 18, Italian profile | Preserve native typography instead of forcing straight quotes. |
| 22: chat residue | 19, 21 | Keep real Italian correspondence conventions and requests for a decision. |
| 23: disclaimers and guesses | 20, ground rules | Correct the local specimen that retained an unsupported founding-date guess. |
| 24: heading repeated | 16 | Existing coverage. |
| 25: document narration | 22 | Include sourcing, assembly and layout; retain usable credits, provenance, caveats and relevant methodology. |
| 26: reply context | 25 | Add answer-first reply structure with visible-context and factual-completeness guards. |

Upstream dropped synonym cycling and false ranges as diagnostic signs. Local 11
and 12 remain only as non-diagnostic readability checks, with no automatic edits.
The sample-voice policy keeps local fidelity and dash constraints; it never permits
invented reactions or opinions. All file authorization and output-mode contracts
are unchanged. New Italian examples are original, not literal translations.

## Italian acceptance criteria

Follow-up web verification: Angela Ferrari, [*La semplicità sintattica in
prospettiva testuale*](https://accademiadellacrusca.it/it/contenuti/la-semplicit-sintattica-in-prospettiva-testuale-riflessioni-a-partire-dalla-guida-alla-redazione-deg/9234),
Accademia della Crusca, 19 March 2021, was read in full on 23 October 2026. It
supports evaluating constituent order, subordinate placement, passive voice and
implicit subjects by textual coherence and information structure rather than
normalizing their surface form. The shipped profile cites the article and adds
original operational examples. This linguistic guidance is not evidence of AI
authorship and does not reverify the profile's inherited statistical citations.

The profile must preserve the writer's relationship with the recipient, including
tu/Lei/voi, legitimate courtesy, technical terms and purposeful uncertainty. It
must not manufacture slang, mistakes or personality. Sentence length follows the
thought rather than a mandatory short-sentence template.

The examples cover a scoped ticket reply, a formal client email, an operational
instruction and a personal hesitation. Negative examples preserve valid technical
uses of *valido*, a meaningful contrast, ordinary greetings and an expression of
breadth. The ticket rewrite keeps the shared service, QA finding and six records;
the email keeps the requested verification without inventing permanent resolution;
the instruction preserves the required backup before restart and the later log check.

## Verification boundaries

`tests/test_text_humanizer_contract.py` protects numbering, mandatory Italian
loading, context/fidelity guards, leaf identity, attribution and reference parity
across all five generated hosts. These are static instruction and packaging tests,
not evidence that an LLM will always produce natural Italian.

The existing operational-binding tests cover the humanize entry's isolated
dispatch contract. No production configuration, external installation, live host
workflow or independent linguistic evaluation is exercised by this update.
Local run evidence, baseline hashes and command logs are retained under
`.daodan/runs/20261023-humanizer-upstream/`. Verification results are recorded below
after execution; a missing gate remains open, not implicitly passed.

## Recorded checks

- Five humanizer contract tests passed after regeneration, including exact Italian/catalog content parity (apart from host wrappers) and the license on all five hosts. Before regeneration, those packaging assertions failed against the old exports, as expected.
- Thirteen existing operational-binding tests passed. Dependency graph, bundled paths, registration, fact anchors and host vocabulary linters passed.
- Build reproducibility, generated documentation parity, native instruction parity and `git diff --check` passed. The final build-check was retried with a longer foreground timeout after the earlier combined verification command timed out; the retry passed. A build warning reported a held-open root `package.json` and its supported in-place publication fallback; no generated drift remained at the subsequent check.
- Candidate version checks confirm text-humanizer 2.0.0 to 2.1.0 and a marketplace version above the captured 38.8.3. This task set 38.8.4; concurrent work subsequently advanced the shared marketplace to 38.8.5. That later bump is not attributed to this update. The commit-range version CLI is not a verification of uncommitted edits and was not claimed as such.

The generated-file backup comparison found changes confined to text-humanizer,
its skill-catalog metadata, Codex/Pi dispatch copies and root catalogs. An
unrelated retrieval-benchmark README also changed concurrently and was not edited
or reverted by this task. Preexisting changes remain uncommitted.

### Source byte fingerprints (SHA-256)

| Source at the pinned commit | SHA-256 |
|---|---|
| SKILL.md | `0612f1dfb1672b0ea9b97e139bf1f06cabe98d8b27424fe8ff01e1fb4cc99cad` |
| CHANGELOG.md | `b3591fe203429f1a6bd2f713c79272e9a8e58a487843d0908d2bbe0700722afa` |
| LICENSE | `4ac4810254ab36d45419141aeb8e69bf50652cfafe5b2dab947d06d44e5cbf96` |
| README.md | `500b53c0d29cd3219d160b5f9a109c0969f706aec74b49a4a081d2026ba48ec7` |
