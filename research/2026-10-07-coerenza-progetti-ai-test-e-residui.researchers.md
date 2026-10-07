# Schede della ricerca: coerenza dei progetti AI

Compagno del rapporto del 7 ottobre 2026. Schede dei sei incarichi, conservate in ordine di assegnazione. Le ripetizioni mostrano le verifiche indipendenti; per la sintesi e i denominatori verificati fare riferimento al rapporto principale.

## Prima passata, incarico 1

# Wave 1: test validity, maintenance and obsolete expectations

Exit reason: thematic saturation for test validity; retirement after migrations still merits a focused follow-up.
Backend: native websearch. Scope cutoff: 2026-10-06.
Activity: 6 refinement rounds, 20 search queries, 17 unique substantive source pages/manuscripts read in selected relevant sections. Repeated reads, failed fetches and navigation excluded. Google’s 2015 article fetched only its title/comments, so it is excluded from the read count and claim evidence; its argument is documented in Google’s official book.

## Claims

**C1. AI can generate tests that actively preserve a bug. [S1]**
The ISSTA/PACMSE paper studies 318 non-private Java focal methods containing 233 real defects across all 17 Defects4J v3.0 projects. Eleven models produce thirteen settings (reasoning on/off for hybrids). A “misguided” test passes on buggy code and fails on the fixed version; an effective test does the reverse. In Table 4, GPT-4.1 generated 2,841 tests from buggy input: 92 misguided and 86 effective. From fixed input it generated 2,905: 11 misguided and 236 effective. Figure 1 gives StringUtils.equals: a generated assertion expects equal text in String and StringBuilder to be unequal, encoding the defect. A two-stage behavioral-docstring approach reduces misguidance, but is not infallible. Limitations: benchmark fixes are the oracle, method-level Java context, potential training overlap; inferred intent can hallucinate. Locations: §§2.2–2.6, 3.1, 4, 6.

**C2. A “make tests pass” pipeline can discard evidence of defects. [S2]**
The preprint evaluates Copilot, CoverAgent and CoverUp on 287 filtered buggy Python student submissions from four assignment problems. CoverAgent/CoverUp use GPT-4o-2024-08-06. Table I reports 171/287 CoverAgent final suites passing buggy code but failing the correct reference; CoverUp has 62/91 such final suites, while 196/287 inputs yield no final suite. Their filters also reject candidates failing buggy code but passing the reference (470 and 400 recorded candidates respectively). These are suite/candidate-pipeline counts, not a population percentage of all AI tests. Copilot’s model is undisclosed. Limitations: small single-function educational examples, default historical tool versions, reference correctness assumptions. Locations: III-A/C, IV, VI.

**C3. Regenerating tests after harmless transformations can degrade them. [S3]**
Eight models are evaluated through 22,374 generation tasks on CodeNet-derived Java/Python programs. The original-program baseline is deliberately selected to have 100% passing suites. After semantic-preserving transformations, regenerated suites average 78.9% test pass rate; branch coverage drops 76.1%→69.2%. This is NOT a result that existing tests fail after refactoring. Fresh models generate new tests for transformed programs. Transformations include redundant blocks, unused parameters and misleading names/comments, so this is a controlled, partly adversarial proxy for evolution. The dataset is single-file and self-contained. Models include GPT-OSS-20B, Nemotron-3-Nano, GPT-5.2, Haiku-4.5, Sonnet-4.6, Gemini-2.5-Flash, Gemini-3.1-Pro; the paper inconsistently labels the remaining model GPT-5 versus GPT-5 Mini. Locations: §§4.1–4.4, 5.3, 7.

**C4. Implementation-coupled, overspecified mocks are an older problem, with important exceptions. [S4]**
Google’s official book explains that assertions on internal calls can confirm a request was made without proving its effect. Stubbing can encode an incorrect or obsolete contract; a fake also drifts if not maintained. Prefer observable values/state and contract-tested fakes. Interaction tests remain useful when side effects, call count/order or performance are part of the intended behavior, or real/fake implementations cannot be exercised. “Uses mocks” is therefore not sufficient grounds to delete a test. Locations: chapter 13, “The Dangers of Overusing Stubbing,” “Prefer State Testing Over Interaction Testing,” “When Is Interaction Testing Appropriate?,” “Fakes Should Be Tested.”

**C5. Obsolete and forgotten test artifacts predate AI. [S5]**
FSE 2021 mines about 122,000 commits and 3,111 disabling changes in 15 Java projects. Its life-cycle analysis reports 41% of disabled tests never re-enabled within observed history, and many persist for years. Manual analysis finds explicit obsolescence, dependency-version issues, redundancy, and tests left disabled even after their linked bugs are fixed. This does not mean 41% are obsolete, or that every disabled test should be removed. The observation window limits “never.” Locations: abstract, §§4–6; Table 7 and §5 contain reasons. The report’s initial sampled-test count (349) and later analyzed denominators vary, so avoid a single prevalence claim for the manually coded subset.

**C6. Migration maintenance and behavioral obsolescence must be distinguished. [S6]**
TOSEM 2023 examines 44 well-tested projects, 33,567 candidate production/test change pairs, and 380 manually reviewed pairs. Its taxonomy includes migration from JUnit imports to JUnit Jupiter and removal of public test-method modifiers, maintenance of test helper dependencies, fixes inside tests, and extraction of common test cases. These can be required test changes with no change to the behavior being protected. Temporal proximity or a matching filename alone does not establish why a test changed. Locations: §§2.1–2.3, pp. 7–13. Author PDF carries September 2023. This is concrete evidence against retiring all tests merely because a migration/refactor occurred.

**C7. Coverage and mutation are conditional evidence, not oracle correctness certificates. [S7]**
A July 2026 replication analyzes 8,268 suites / 101,123 test cases, from 318 Defects4J methods and thirteen settings of eleven models (same families as S1). Tests generated from fixed code can show useful inter-model relationships: average branch coverage versus real-defect detection has Pearson r=0.861 (p=0.00016), Table 10. Within-model correlations are much weaker. For tests generated from buggy input, coverage/real-bug correlations are weak in all aggregation views (§5.4). A larger suite does not reliably mean better detection. Mutation analyses require a passing baseline, potentially excluding tests exposing an existing defect. Do not simplistically claim “mutation testing solves self-reference.” Locations: §§3.2–3.7, 5.1–5.5, 6–7. S1 and S7 share authors/data design, so count them as complementary analyses, not independent replications.

**C8. Generated tests can help when assessed in a deliberate engineering process. [S8]**
Meta reports two anonymous internal models, four prompts, and 86 Kotlin components with existing tests (31 Stories, 55 Reels). §3.3: 75% of classes had at least one buildable new test; 57% had at least one buildable, reliably passing new test; 25% had at least one such test adding line coverage. These are CLASS denominators, despite abstract/figure wording suggesting test cases. The previous chat’s “57% of tests pass / 25% improve coverage” should be corrected. Engineers rejected one of 17 November test-a-thon proposals because it increased coverage without an assertion; 16 landed. §4 reports 73% acceptance of test improvements. Added coverage and acceptance are not directly measured real-fault detection. Locations: §§3.2.1, 3.3, 4.

**C9. More elaborate prompting can also produce irrelevant assertions. [S9]**
AIware 2025 completes bug-triggering test prefixes for 36 GHRB Java defects, with GPT-4o and StarCoder, three contexts, five repetitions and 2,160 total runs. It evaluates the same generated oracle against buggy/fixed code. Manual inspection finds over-generation, irrelevant functionalities and overly complex comparisons; reasoning prompts did not uniformly improve the task. Because the prefixes already expose the defect and localization is supplied, results do not measure full end-to-end testing. Locations: II, III, IV-E, V.

**C10. Smell flags are leads requiring semantic review. [S10, S11]**
The expanded 2026 Java study compares 20,505 class-level LLM suites, 972 method-level cases, EvoSuite and 779,585 human-written tests, with two detectors plus manual validation. Model families include GPT-3.5/GPT-4/Mistral-7B/Mixtral/CodeLlama. Similar smells occur in human tests; detector disagreements and Java-only scope limit automatic judgment. A separate GPT-4-Turbo/Llama-3-70B/Gemini-1.5-Pro study finds that removing one smell can introduce others. Neither permits treating every smell as an invalid test. Locations: S10 §§3.3, 4, 5.4; S11 IV-B.

**C11. Independent behavioral information helps, but is itself an oracle to validate. [S12–S16]**
The classic oracle survey distinguishes observed from desired behavior. Doc2OracLL studies documentation as additional context; its original arXiv and expanded FSE versions differ, so their numeric results should not be mixed. A July 2026 requirement-only pilot uses ten Lang defects, five models, manually derived requirements/oracles and test cases; its small scope and author judgment limit generalization. Bug-report-driven tests and differential testing against independently generated variants offer alternative signals. They still need input validity checks and trustworthy specifications/reference implementations.

## Practices justified by the sources

These are a synthesis, not a universally validated cleanup protocol:
- Record the current requirement and the source of each important expected result before changing a test.
- Separate tests preserving accepted behavior from tests intended to expose existing defects.
- Review failures as possible product defects before repairing assertions to match implementation.
- Keep user-visible regression protection during refactors; adapt scaffolding/framework APIs when migrating.
- Review skipped tests with their issue/history. Retire only when the protected contract is intentionally gone or an equivalent maintained check replaces it; age alone is insufficient.
- Use targeted mutation/fault-injection as a supplementary probe, with independent behavioral review. Google’s mutation engineering account [S17] suppresses unproductive/equivalent mutants because testing them can create more brittle tests.
- Check mocks/fakes against real contracts and assertions against observable outcomes.

## Sources read

Ranks: R1 official engineering/maintainer source; R4 peer-reviewed original study; R4p original research preprint (weaker publication assurance).

| ID | Source / URL | Date carried | Rank |
|---|---|---|---|
| S1 | [Misguidance effect](https://arxiv.org/html/2607.22883v1) | 24 Jul 2026; ISSTA/PACMSE DOI 10.1145/3832204 | R4 |
| S2 | [Design choices prevent bug finding](https://arxiv.org/html/2412.14137v1) | 18 Dec 2024 | R4p |
| S3 | [Test generation under evolution](https://arxiv.org/html/2603.23443v1) | 24 Mar 2026 | R4p |
| S4 | [Software Engineering at Google, chapter 13](https://abseil.io/resources/swe-book/html/ch13.html) | book 2020; page undated | R1 |
| S5 | [Disabled tests](https://petertsehsun.github.io/papers/fse2021_disabled_test.pdf) | FSE, 23–28 Aug 2021 | R4 |
| S6 | [Production/test co-evolution](https://yanmeng.github.io/papers/TOSEM231.pdf) | PDF September 2023 | R4 |
| S7 | [Coverage, mutation and effectiveness replication](https://arxiv.org/html/2607.22880v1) | 24 Jul 2026; ISSTA/PACMSE DOI 10.1145/3832093 | R4 |
| S8 | [TestGen-LLM at Meta](https://arxiv.org/html/2402.09171v1) | 14 Feb 2024; FSE 2024 | R4 |
| S9 | [Understanding LLM-driven oracle generation](https://valerio-terragni.github.io/assets/pdf/bodicoat-aiware-2025.pdf) | AIware 2025 | R4 |
| S10 | [Diffusion of test smells](https://arxiv.org/html/2410.10628v3) | 1 Aug 2026; TOSEM DOI 10.1145/3838597 | R4 |
| S11 | [LLMs detecting/correcting test smells](https://arxiv.org/html/2506.07594) | June 2025 | R4p |
| S12 | [Oracle problem survey](https://philmcminn.com/publications/barr2015.pdf) | TSE 2015; DOI 10.1109/TSE.2014.2372785 | R4 |
| S13 | [Doc2OracLL original manuscript](https://arxiv.org/html/2412.09360) | December 2024; expanded FSE publication June 2025 | R4p |
| S14 | [Requirements to test assertions](https://arxiv.org/html/2607.10277) | 11 Jul 2026 | R4p |
| S15 | [Tests from bug reports](https://arxiv.org/html/2310.06320) | initial October 2023; latest HTML read | R4p |
| S16 | [Tests for plausible programs](https://arxiv.org/html/2404.10304) | initial 16 Apr 2024; latest HTML title is TrickCatcher paper | R4p |
| S17 | [Mutation testing at Google](https://testing.googleblog.com/2021/04/mutation-testing.html) | April 2021 | R1 |

## Contradictions seen

- S1 explicitly corrects an earlier metric that counted every test passing buggy code as misguided: most such tests also pass fixed code.
- S3 uses 22,374 both as “variants” and generation-task count, and GPT-5/GPT-5 Mini inconsistently. Use aggregate findings with precise experimental scope.
- S8 abstracts/figure label percentages as test cases; §3.3 defines classes containing at least one candidate. Prefer the methods-section denominator.
- “Generate regression protection from accepted current behavior” and “discover existing bugs” are different objectives. A passing-only filter is reasonable for the former and can undermine the latter.

## Open threads for wave 2

Direct longitudinal evidence that AI agents amplify obsolete tests specifically after real migrations is thinner than evidence for bug-validating generation. Follow up with original Pinto/Sinha/Orso 2012 study and test-maintenance issue histories. Author PDF https://faculty.cc.gatech.edu/~orso/papers/pinto.sinha.orso.ICSE12.pdf failed; two author-host variants failed too. No conclusion about the paper’s reliability follows from access failure. Google’s 2015 change-detector article required a rendered/browser read because fallback extraction omitted its body. The official book already supplies its substantive argument.

## Searched and not found

No trustworthy population estimate for the proportion of self-referential/incorrect/obsolete tests across “vibe-coded” repositories. No validated universal rule that classifies retirement from filenames, age, coverage, mocks or test counts alone. No direct causal proof that the same model writing code and tests necessarily fails; supplied buggy implementation and passing-only selection are demonstrated mechanisms. No grounds to erase regression tests merely because their implementation or framework was migrated.


## Prima passata, incarico 2

# Researcher report: project memory and coherence

Scope: fragmented documentation, conflicting instructions, decision/understanding debt, instruction-file effectiveness, cross-session handoff. Cutoff: 2026-10-06. Backend: native websearch. No local repository audit or edits.

Exit reason: scope saturation for a first wave. Four search rounds, 16 distinct queries, 16 substantive works read (17 substantive URLs because Storey v3 was superseded by v4), plus an abstract/history page. Targeted follow-up reads of methods/results were not counted as new pages. Publisher mirrors for Storey failed; the current author preprint PDF was read successfully.

## Claims

**C1. Workflow fragmentation has direct qualitative evidence.** Interviews with 22 product-team members, recruited from 50 respondents and conducted May–June 2025, document different AI tools undoing/misreading each other's work, unstructured redundant code growth, opaque change attribution, forgetting earlier goals, and copying old versions into temporary documents. Only four participants were software engineers; nine were designers, with others in product/research/founder roles. These are participant reports, mostly prototyping, not repository audits or measured population prevalence. [S1]

**C2. Instruction overlap is observable, while its harm is not measured in the adoption study.** Across 2,853 selected GitHub repositories, the study finds 4,768 context files in 2,586 repositories and 497 reference pairs. CLAUDE.md points to AGENTS.md 301 times. Authors recommend a shared AGENTS.md core and explicitly discuss conflicting/redundant instruction risks. File counts and pointers demonstrate practices, not contradictory-content prevalence or effectiveness. Snapshot: February 2026; extended v5 corrects the older 2,926-repository count. [S2]

**C3. Context files do not automatically improve task resolution.** Four agent/model configurations (Sonnet 4.5/Claude Code; GPT-5.2 and GPT-5.1 mini/Codex; Qwen3-30B/Qwen Code) evaluate 300 SWE-bench Lite tasks from 11 Python repositories and 138 CTXbench tasks from 12 repositories. Generated files show no significant success improvement, with mean inference cost increases of 20% and 23%. Developer files gain 2.4 percentage points versus absence (p=.21), outperform generated files (p=.038), and also raise cost. September v3 reports a +2.7-point generated-file gain when other documentation is removed, and no clear effect of file length. Specific added requirements matter more than duplicated overviews. [S3]

**C4. Understanding debt has qualitative evidence, including a mitigating use of AI.** A preprint analyzes 621 reflective diaries from 207 undergraduates over eight weeks, in one Scrum-based software-engineering course. Themes: black-box acceptance, missing codebase context, dependence reducing independent comprehension, and verification bypass. Students also use AI as an explanation scaffold or rewrite code to understand it. No control group, quantified causal effect, or professional-team prevalence estimate. [S4]

**C5. Stale instruction references have direct preliminary evidence.** DOCER analyzes 612 instruction files across 356 randomly sampled repositories from an eligible set of 4,420. It flags 230 of 18,048 historically verified references, affecting 82 repositories (23.0%). Manual inspection of 50 flags finds 32 genuine, 12 false positives and six ambiguous. The paper explicitly calls 23% a feasibility signal, not precise prevalence: first-commit comparisons miss later references, while broad regexes overcount. Actual examples include deleted scripts, renamed functions, removed dependencies and nonexistent paths. Downstream agent harm remains an open experiment. [S5]

**C6. Contradictory instructions are confirmed in popular applications, but detector precision is weak.** The January 2026 sample contains root files from the 100 most-starred selected application repositories (39 AGENTS.md, 61 CLAUDE.md). Gemini 3.1 Flash Lite flags 28 conflicting files; first-author review confirms 16 (57% precision). Other confirmed detections: 29/35 task-specific skill content, 58/62 lint-style content, 14/16 unqualified documentation pointers. Forty-two files exceed a 200-line heuristic; 24 have a single commit. These last two proxies are not demonstrated defects. The abstract's raw detection rates and 91-files-with-a-flag are not validated prevalence. [S6]

**C7. A smaller current-model ablation also finds no correctness improvement, with limited power.** Three Python repositories; 17 Codex/gpt-5.5 tasks, 15 Claude Code/Sonnet-4.6 tasks, three strategies and three repeats (288 evaluated runs). Hidden gold tests: Claude 53.3/55.6/55.6% and Codex 58.8/56.9/52.9% for absent/always-on/selective context. No significant strategy effect. Minimum detectable effect exceeds 30 percentage points, so this does not prove equivalence. Selective wikis contain substantially more material for two repositories, a corpus confound. Exploratory opshin results suggest explicit slow-suite guidance can reduce wasteful full-suite runs for Claude. [S7]

**C8. Relevant new knowledge can help greatly in a vendor evaluation.** Vercel's focused Next.js 16 evaluation reports 53% baseline, 53% unprompted skill, 79% explicitly prompted skill and 100% with an 8KB version-matched documentation index in AGENTS.md. The post acknowledges correcting ambiguous prompts, contradictory tests, leakage and implementation-specific assertions first. It does not report total task/model/repeat denominators sufficient for an independent general efficacy claim. Treat as a vendor experiment about framework knowledge, not proof that all instruction files improve all tasks. [S8]

**C9. There is positive evidence on efficiency under a different design.** Codex with gpt-5.2-codex, 124 historically merged PRs from ten repositories, each at most 100 changed lines/five files and code-only, run with/without a single root AGENTS.md. Median runtime falls 28.64%, median output tokens 16.58%; both significant. Median total tokens slightly increase (1.29%). Correctness is explicitly outside scope: 50 outputs receive only a manual nondegenerate-output sanity check. Efficiency benefits do not establish preserved functional correctness. [S9]

**C10. The agent's own account of its change is not a reliable ground truth.** A peer-reviewed MSR study analyzes 23,247 PRs from five agents, filtered from popular permissively licensed GitHub repositories. A heuristic flags 406 high message/code inconsistencies (1.7%); 974 PRs are manually annotated across validation and further candidate analysis. In 432 partial/misaligned cases, unimplemented claimed changes are the most frequent type (45.4%). Associations with acceptance/merge time are observational, not causal. The detector F1=.630 and calibrated threshold limit prevalence interpretation. [S10]

**C11. Cross-session loss is reported by an agent vendor as an observed engineering failure.** Anthropic describes Opus 4.5 attempting too much, leaving half-built undocumented features, or declaring completion early after resets. Its harness uses progress summaries, git history, a requirements/status artifact and incremental work to orient fresh sessions. This is an original engineering account with examples, not a controlled population study or quantified comparison. [S11]

**C12. Consolidation can preserve decisions while discarding repeated output, but requires fidelity checks.** Anthropic describes compaction preserving architectural decisions, unresolved bugs and necessary implementation details while removing redundant tool output. It warns that overly aggressive compaction can lose subtle information needed later and recommends tuning for recall before pruning. This supports a design analogy for consolidating experiment outputs; it directly discusses conversational context, not deleting disk artifacts. [S12]

**C13. AI assistance does not inevitably degrade maintainability.** A preregistered two-phase Java-app study includes 151 completed participant tasks, about 95% professional developers. Phase 1: AI n=39, no AI n=37; phase 2 manual evolution: treatment n=40, control n=35. Phase 2 finds no systematic significant difference in completion time, code quality or coverage. Conducted in late 2024 with human co-development, not present-day autonomous vibe coding. One application/two tasks and an underrecruited follow-up sample do not resolve long-term agentic risks. [S13]

**C14. Instruction maintenance often adds rather than removes context.** The current Agent READMEs preprint studies 2,303 files in 1,925 repositories. Multi-commit files: Claude 67.0%, Copilot 59.8%, Codex 59.4%; changes are mostly small additions with negligible deletions. Median update intervals: 23.8/68.0/22.3 hours respectively. This supports treating instructions as maintained configuration; it neither proves growing contradiction nor establishes causal coupling to particular code changes. [S14]

**C15. Vendor documentation recognizes conflicts as an operational problem.** Current Claude Code documentation says conflicting rules can lead to arbitrary selection, recommends reviewing nested instruction/rules files, and warns that imports still load context rather than saving tokens. It documents a prompt audit covering nonexistent commands/paths, old-model instructions and conflicts (v2.1.283+). This is official operational guidance, not experimental validation of its remedy. [S15]

**C16. Intent debt is a useful conceptual framing, not a measured epidemic.** Storey's latest preprint distinguishes code-level technical debt, shared-understanding cognitive debt and missing goals/constraints/rationale as intent debt. It argues that recovering why software exists differs from describing present behavior, and suggests decision records and specifications. The introductory student-team incident is an anecdote; the triple-debt model is an expert conceptual argument. AI-generated documentation can create an appearance of understanding without human comprehension. [S16]

## Sources read

Rank: 1=official documentation; 4=peer-reviewed/public original research; 5=original engineering post or unreviewed conceptual account. Preprints remain marked as such. Date is carried publication/version date, not crawler date.

| ID | Title and primary URL | Date | Rank/status |
|---|---|---|---|
| S1 | [Vibe Coding in Product Teams](https://arxiv.org/html/2509.10652v3) | 2026-05-01 v3 | 4, HCI work conference paper |
| S2 | [Harness Engineering for Agentic AI Coding Tools](https://arxiv.org/html/2602.14690v5) | 2026-06-30 v5 | 4, extended AIware paper |
| S3 | [Evaluating AGENTS.md](https://arxiv.org/html/2602.11988v3) | 2026-09-29 v3 | 4, updated preprint; earlier workshop paper |
| S4 | [Comprehension Debt in GenAI-Assisted Projects](https://arxiv.org/html/2604.13277) | 2026-04-14 v1 | 4, qualitative preprint |
| S5 | [Context Rot in AI-Assisted Software Development](https://arxiv.org/html/2606.09090) | 2026-06-08 v1 | 4, preliminary preprint |
| S6 | [Configuration Smells in AGENTS.md](https://arxiv.org/html/2606.15828v5) | 2026-07-30 v5 | 4, preprint |
| S7 | [Do Context Files Help Coding Agents?](https://arxiv.org/html/2607.27250) | 2026-07-28 v1 | 4, independent preprint |
| S8 | [AGENTS.md outperforms skills in our agent evals](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals) | 2026-01-27 | 5, original vendor experiment |
| S9 | [On the Impact of AGENTS.md on Efficiency](https://arxiv.org/html/2601.20404v2) | 2026-03-30 v2 | 4, JAWs workshop paper |
| S10 | [Message-Code Inconsistency in AI Agent PRs](https://arxiv.org/html/2601.04886v2) | 2026-01-26 v2 | 4, MSR 2026 paper |
| S11 | [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 2025-11-26 | 5, original vendor engineering account |
| S12 | [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | 2025-09-29 | 5, original vendor engineering account |
| S13 | [Echoes of AI](https://arxiv.org/html/2507.00788v3) | 2026-02-26 v3 | 4, preregistered study; journal version indexed |
| S14 | [Agent READMEs](https://arxiv.org/html/2511.12884v2) | 2026-08-09 v2 | 4, current preprint |
| S15 | [How Claude remembers your project](https://code.claude.com/docs/en/memory) | Undated live docs, accessed 2026-10-06 | 1 |
| S16 | [From Technical Debt to Cognitive and Intent Debt](https://arxiv.org/pdf/2603.22106v4) | 2026-04-06 v4 | 5, expert conceptual preprint; ACM Queue June article indexed but inaccessible |

## Contradictions seen and adjudication

- S3, S7, S8 and S9 ask different questions. Framework knowledge absent from training, small-PR efficiency, correctness under existing documentation and implementation skill are different treatments/outcomes. There is no universal result for presence of AGENTS.md.
- S3's updated appendix supports selective new information, and weakens the simplistic claim that length alone explains its negative cost result. Operational vendor length limits are guidance, not a universal causal threshold.
- S6's abstract/detection prevalence overstates what manual validation confirms, especially contradictions. S5 explicitly disclaims precise prevalence. Preserve both distinctions.
- S13 contradicts an inevitable-maintainability-damage narrative, without testing modern long-horizon agent projects.
- S16 warns that generating more documentation does not itself create shared understanding. Canonical documentation should distinguish implemented facts, recorded decisions, unverified hypotheses and superseded conclusions. This last design recommendation is synthesis, not an evaluated cleanup intervention.

## Open threads

Controlled stale-file harm experiments; long-term coherent vs fragmented agent-project comparisons; intervention studies on canonical source/pointer strategies; measuring retention of decision intent after summary/deletion; independent verification of Vercel model/task counts. Traditional DOCER and just-in-time comment/documentation repair tools are promising routes, but their papers were not independently read in this wave.

## Searched and not found

No reliable population estimate of contradictory decisions across vibe-coded projects, no evidence that most lack AGENTS.md, and no measured end-to-end cleanup workflow that reconciles intent, consolidates experimental evidence and reduces residual storage. No causal demonstration that stale instruction files alone create the reported maintenance incidents. Disk/test-specific topics were assigned to other researchers.


## Prima passata, incarico 3

# Researcher report: test proliferation and experiment-artifact consolidation

Backend: native web search. Scope cutoff: 2026-10-06. Role: wave 1, tests and artifacts. No repository inspection or modification.

Exit reason: six-round search budget reached, with saturation on retention mechanisms and strong counterevidence to simplistic suite minimization. 21 queries; 17 unique substantive sources read. Two primary-source access failures resolved through primary mirrors (JUnit paper on Illinois; notebook paper on PLOS); canonical Google URL failed, parameterized publisher URL succeeded. Some search results were candidates only and support no claims here.

## Main finding

The proposed workflow has established precedents, but three different operations must be distinguished: deleting obsolete test code, selecting fewer tests for a particular change, and deleting bulky execution artifacts while retaining results. There is direct industrial evidence of LLM-generated superficially different tests, and smaller experiments report redundant scenario generation. There is no reliable quantitative evidence here for the prevalence of GB-sized residue specifically in vibe-coded projects. Redundant line coverage does not establish redundant defect protection. A readable report alone does not necessarily preserve reproducibility.

## Sourced claims

1. **Direct AI duplicate evidence.** Meta's initial TestGen-LLM trial submitted eight diffs. One initially contained four test cases that engineers judged only superficially different. The team added contribution measurement at individual-test level to remove duplicated effort. Later, one of 17 Instagram diffs was rejected because its new test increased coverage by executing a method but contained no assertion. These are observed industrial cases, not prevalence estimates. [S1, sections 3.1 and 3.2.1]

2. **Correct denominator for the frequently cited 25%.** Section 3.3 evaluates 86 Kotlin components with existing test classes (31 Stories, 55 Reels), two unnamed internal models and four prompting strategies. 75% of classes had at least one new case that built; 57% had one that built and passed reliably; 25% had one that additionally increased line coverage over other classes sharing its build target. It does not report a 25% coverage increase. Prefer this detailed class-level denominator over the abstract's inconsistent case-level wording. [S1]

3. **Small-scale overgeneration evidence.** Walczak et al. compare six models (GPT-4.5, o3, o4-mini-high, Claude 3.7 Sonnet, Gemini 2.5 Pro, DeepSeek-V3), two prompting strategies and three context levels on an isolated Python shopping-cart component. They report more tests and redundant scenario coverage with staged reasoning prompts. Table IV gives mean counts of 36 vs. 59, 43 vs. 64 and 45 vs. 62 across the models for the three contexts. This is not longitudinal evidence about real repository proliferation. Their prose's approximate 20–40% claim does not match all tabulated increases. [S2, III-C, III-F, IV-B, Tables III–IV]

4. **The minimization tradeoff is empirically real and context-dependent.** An ISSRE 2011 study implemented four reduction techniques over 19 versions of four Java projects, 1.89–80.44 KLoC. It found useful reductions without severe fault-detection loss in that setting, while granularity and coverage criteria substantially changed both benefit and cost. The earlier Rothermel study reports that reduction can severely compromise fault detection in other settings (publisher abstract only read). These are countervailing empirical findings, not a universal endorsement or rejection of minimization. [S4; S5]

5. **Preserving coverage can still miss future failures.** ISSTA 2018 studies 1,478 failed builds, from 27,461 builds across 32 Java/Maven GitHub projects using Travis. Reduced suites were evaluated against future failed builds. Failed-Build Detection Loss reached 52.2% for coverage-based Greedy with the most pessimistic mapping (each failed test treated as a separate fault), excluding builds whose failed tests were all added after reduction. This means a build did not retain detection of every inferred fault found by the original suite; it does not mean 52.2% of all defects or projects were missed. Coverage and mutation-based reduction metrics were weak predictors of this future loss. [S6, sections 1, 5.1–5.2, Table 3]

6. **Selection is an alternative to permanent deletion.** Facebook's 2018 engineering account describes selecting approximately one third of tests transitively dependent on changed code while detecting more than 99.9% of problematic changes. That target means catching at least one failing test for a problematic change, unlike S6's requirement to retain detection of every fault. It depends on historical outcomes, ongoing model retraining, and treatment of flaky results. It is change-specific selection, not proof that the unselected tests are useless and should be removed. [S14]

7. **Noise has a real maintenance cost.** Google's 2016 engineering report says about 1.5% of test runs were flaky, nearly 16% of tests exhibited some flakiness, and about 84% of observed pass-to-fail transitions involved a flaky test. These are three different denominators in Google's historical environment. The report describes repeated investigation, delays and legitimate failures dismissed as noise. Flakiness can come from actual product nondeterminism as well as tests or infrastructure; a failing or flaky test is not automatically disposable. [S13]

8. **Bulk artifact disposal with durable metadata is already implemented.** Allure TestOps cleanup removes attachments, fixture data and scenario artifacts for closed launches, leaving launch/result metadata indefinitely. Attachments are identified as the largest storage consumer. Current defaults keep successful-test attachments one week, other-status attachments one month, and fixture/scenario artifacts one month. The launch can also be exported to PDF (summary and individual details) or CSV (metadata, status, error). Logical deletion and physical database disk reclamation are distinct operations. These vendor mechanisms demonstrate feasibility, not measured average GB savings or complete evidence preservation. [S3; S12]

9. **Prevent accumulation at its source.** Playwright supports traces/videos retained only on failures and screenshots only on failures; its trace guide recommends first-retry recording in CI and warns that tracing every test is expensive. pytest creates dedicated per-test temporary directories, retains the last three runs by default, and has configurable retention policies; expensive common generated data can be shared through a session fixture. These policies are concrete examples of managed transient storage. They do not consolidate the meaning of experiments by themselves. [S7; S8; S11]

10. **The research precedent explicitly includes cleanup, but also preservation.** The 2022 PLOS workflow-ready guidance says to consider very large outputs and large numbers of small files, clean tool-created temporary directories after successful completion, and optionally retain them for debugging. The 2013 reproducibility guidance requires inputs, parameters, software versions, scripts, random seeds, data behind plots and connections between claims and results. It recommends retaining intermediate files when storage is not prohibitive because they may reveal bugs invisible in the final result. Digital-storage guidance similarly distinguishes regenerate-vs-store tradeoffs and warns that derived data alone can prevent reanalysis. [S10; S9; S17]

11. **Exploration can be curated into a reusable narrative.** PLOS's notebook guidance recommends recording the reasoning and dead ends of interactive explorations, then cleaning and annotating after each meaningful experiment. Stable analyses can become reproducible pipelines, rerun from a fresh kernel to check that cleaning removed no required step. It advocates tiered datasets when full inputs are too large and static HTML/PDF records for long-term readability. This supports a compact report plus executable recipe and selected data, rather than merely retaining an unstructured pile or only a prose summary. [S15]

12. **Test activity is not test quality.** The MSR 2026 agentic-PR study examines 33,596 PRs (31,284 closed for lifecycle metrics), observes increasing test-file inclusion and repeated modifications, but explicitly does not assess coverage, effectiveness, test type or reviewer intent. This is evidence that test maintenance is part of agentic workflows, not evidence that its additional test code is pointless. [S16, section 6]

## Sources read

Authority ranks follow the loaded skill: 1 official docs; 4 primary peer-reviewed research or original engineering reports. Preprints are marked as such rather than implied peer-reviewed. Accessed 2026-10-06; undated documentation is the fetched current page, not historical proof of a particular release.

| ID | Title and URL | Date carried | Rank/type |
|---|---|---|---|
| S1 | [Automated Unit Test Improvement using Large Language Models at Meta](https://arxiv.org/html/2402.09171v1) | 2024-02-14 v1; FSE 2024 | 4, original industrial paper |
| S2 | [Impact of Code Context and Prompting Strategies on Automated Unit Test Generation with Modern General-Purpose Large Language Models](https://arxiv.org/html/2507.14256v1) | 2025-07-18 v1 | 4, original preprint |
| S3 | [Allure TestOps cleanup policies](https://docs.qameta.io/administer/maintenance/cleanup-policies/) | Undated | 1, official docs |
| S4 | [An Empirical Study of JUnit Test-Suite Reduction](https://mir.cs.illinois.edu/marinov/publications/ZhangETAL11JUnitReduction.pdf) | ISSRE 2011 | 4, authors' full paper |
| S5 | [Empirical studies of test-suite reduction](https://onlinelibrary.wiley.com/doi/abs/10.1002/stvr.256) | 2002-12-04 | 4, publisher abstract; not full text |
| S6 | [Evaluating Test-Suite Reduction in Real Software Evolution](https://mir.cs.illinois.edu/gyori/pubs/issta18.pdf) | ISSTA 2018-07 | 4, authors' full paper |
| S7 | [Playwright Trace viewer](https://playwright.dev/docs/trace-viewer) | Undated | 1, official docs |
| S8 | [Playwright Configuration (use)](https://playwright.dev/docs/test-use-options) | Undated | 1, official docs |
| S9 | [Ten Simple Rules for Reproducible Computational Research](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003285) | 2013-10-24 | 4, peer-reviewed guidance |
| S10 | [Ten simple rules for making a software tool workflow-ready](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1009823) | 2022-03-24 | 4, peer-reviewed guidance |
| S11 | [pytest: How to use temporary directories and files in tests](https://docs.pytest.org/en/stable/how-to/tmp_path.html) | Undated | 1, official docs |
| S12 | [Allure TestOps Launches](https://docs.qameta.io/use-testops/test-plans-and-launches/launches-overview/) | Undated | 1, official docs |
| S13 | [Flaky Tests at Google and How We Mitigate Them](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html?hl=ar&showComment=1465474312128) | 2016-05-27 | 4, original engineering report |
| S14 | [Predictive test selection: A more efficient way to ensure reliability of code changes](https://engineering.fb.com/2018/11/21/developer-tools/predictive-test-selection/) | 2018-11-21 | 4, original engineering report |
| S15 | [Ten simple rules for writing and sharing computational analyses in Jupyter Notebooks](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1007007) | 2019-07-25 | 4, peer-reviewed guidance |
| S16 | [An Empirical Study of Tests in Agentic Pull Requests](https://ranger.uta.edu/~csallner/papers/Haque26Empirical.pdf) | MSR 2026-04-13/14 | 4, authors' full paper |
| S17 | [Ten Simple Rules for Digital Data Storage](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005097) | 2016-10-20 | 4, peer-reviewed guidance |

## Contradictions seen

- S1's abstract, figure caption and conclusion use case-level language for percentages that section 3.3 explicitly reports over classes. Use the detailed denominator.
- S2's 20–40% generalization differs from its table means (roughly 64%, 49%, 38%). Its small constructed subject also precludes repository-wide extrapolation.
- Reduction studies report different tradeoffs; differing subjects, test granularity, criteria and seeded-vs-future-real-failure evaluation account for important differences.
- S14's detecting at least one failure per change is a weaker objective than S6's detecting all inferred faults per failed build. Their percentages cannot be compared directly.
- S16 text calls Codex's test-to-code ratio highest although Table 4 lists Copilot 0.87 and Codex 0.61. Omit that ranking. No claim about unnecessary tests follows from either ratio.
- Research preservation guidance favors keeping raw/intermediate evidence; execution tools favor removing repetitive success artifacts. These serve different purposes. Choose preservation by evidentiary value and reproducibility, not solely by size.

## Open threads

- An operational cleaning workflow should map maintained tests to active requirements, boundary inputs, assertions/oracles and historical regressions; two tests with the same executed lines may check different properties.
- Evaluate a proposed reduction against historical failures and mutation sensitivity where appropriate, with semantic review. Coverage is a lead for possible overlap, not sufficient deletion authority.
- A plausible compact experiment record contains purpose, code revision, environment, inputs and checksums, command/seed, status, measurements, interpretation, retained evidence, reproduction path and a disposition list. This schema is a synthesis of the sources, not a validated vibe-coding intervention.
- Stable test code protects future behavior; an experiment report records past knowledge. Archiving a report does not replace useful regression tests.

## Searched and not found

- No robust estimate of MB/GB residual artifacts specifically caused by vibe coding or coding agents.
- No validated universal percentage of AI-written tests that are redundant, disposable, obsolete or incorrect.
- No study validating the entire proposed process of automatically summarizing experiments, deleting artifacts and restoring repository coherence.
- No universal minimum set of screenshots, logs or raw data sufficient for all debugging/reproducibility purposes.

Candidate-only leads not used for claims: Microsoft filesystem-misuse study, AI-code maintenance study, over-mocked agent-tests study, anecdotal Reddit repository-junk reports. They are adjacent to this scope but were not read within the budget.


## Seconda passata, incarico 1

# Wave 2 researcher report: test validity and lifecycle

Exit reason: central checks complete; saturation on test lifecycle after finding original longitudinal evidence and two concrete project reports. The AI-specific migration prevalence question remains open.
Backend: native web search. Cutoff: 2026-10-07.
Activity: 4 refinement rounds, 12 search queries, 10 unique substantive works read at 12 content URLs (relevant sections). Metadata pages, failed fetches and repeated reads excluded. No repository audit or implementation.

## Claims and verification verdicts

**C1. PASS: misguided tests explicitly preserve a defect. [S1]**
Section 2.6/Table 2 defines misguided tests as passing buggy code and failing its fixed counterpart; merely passing buggy code is insufficient. Section 2.2 verifies 318 focal Java methods, 233 defects, all 17 Defects4J v3.0 projects. Table 4 verifies GPT-4.1: buggy input produces 92 misguided and 86 effective tests out of 2,841; fixed input produces 11 and 236 out of 2,905. Eleven models provide thirteen settings. Fixed benchmark versions supply the behavioral oracle. Method-level context, historical defects and possible training overlap limit extrapolation to whole projects. This independently checks the manuscript, not a replication of its experiment. [Misguidance study](https://arxiv.org/html/2607.22883v1)

**C2. PASS: 171/287 and 62/91 are final-suite counts. FAIL: treating them as individual-test prevalence. [S2]**
Table I evaluates suites against original/reference implementations. CoverAgent has 171 bug-validating final suites among 287 inputs/final suites. CoverUp has 62 among its 91 final suites (29+62); 196 other inputs yield no final suite. Rejected intermediate outputs have separate counts and cannot share that denominator. The experiment uses 287 filtered, mostly single-function Python student submissions from four assignments; CoverAgent/CoverUp use GPT4O version 2024-08-06, and Copilot's model is unspecified. Its passing-only selection mechanism is independent corroboration of a risk identified in S1, using different authors, programs and tooling. It does not establish present-day product behavior. [Generator design study](https://arxiv.org/html/2412.14137v1)

**C3. PASS: fresh test generation deteriorates after controlled transformations. FAIL: retained suites were tracked through refactors. [S3]**
Sections 4.3–4.4 give changed code to independent model instances to generate new suites; 5.3 explicitly says suites are regenerated. The baseline deliberately contains only programs with fully passing generated suites. Across eight models, regenerated suites after semantic-preserving changes average 78.9% passing tests and branch coverage 69.2%, versus baseline 100% and 76.1%. CodeNet Java/Python programs are self-contained; transformations include misleading names/comments and redundant blocks. This is a controlled proxy for evolution, not observation of migrations in maintained repositories. It supplies no estimate of existing tests becoming obsolete. [Evolution experiment](https://arxiv.org/html/2603.23443v1)

**C4. PASS: meaningful test maintenance often preserves the oracle while adapting the executable test. [S4]**
The original FSE 2012 study covers six programs, 88 releases, 14,312 tests and 17,427 changes. Only 111/1,121 repairs (9.9%) change assertions alone (Table 4). PMD Figure 1 adapts setup and API calls while preserving the expected token count, 9. Conversely, JFreeChart's test expecting the predecessor of year 1900 to be absent becomes obsolete when earlier years become supported (§4.4). Moves/renames can resemble deletion and addition. These are distinct lifecycle events requiring different action. Limitations include release-level sampling and small manually inspected subsets; the study's automated category labels are hypotheses refined by inspection. [Original manuscript, archived institutional copy](https://web.archive.org/web/20240413135742if_/https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=efe8079160bb66d4df86b1531ec03c17b0ecd3e2)

**C5. PASS: real projects retire tests with removed production code, sometimes later. [S5]**
MSR 2025 DelTest manually confirms 24,431 deleted tests in 2,125 commits among 449,592 commits from seven Java projects, filtering moved/refactored tests. The reason analysis excludes Android CTS: of 7,326 deletions in six projects, 6,694 (91.4%) are operationally obsolete because invoked production methods disappeared or tests no longer compile. Of these, 2,530 (38%) are deleted in later commits: median delay one day, maximum 31. The remaining passing deleted tests are labeled redundant, but 103/518 (20%) lose coverage; mutation execution failed for 149, leaving 369 evaluable. Therefore passing is not proof of redundancy, and code removal is not independent proof that the underlying requirement disappeared. The dataset omits partial deletion inside retained methods and is Java-specific. [DelTest paper](https://hifromajay.github.io/papers/msr25.pdf)

**C6. PASS: framework migration can require maintenance without retiring the protected behavior. [S6]**
TOSEM 2023 examines 44 well-tested projects, 33,567 candidate production/test change pairs and 380 manually analyzed pairs. Its Cactoos example changes JUnit imports to Jupiter and removes public test-method modifiers, while associated production code undergoes separate API replacement. The taxonomy also includes helper/library maintenance and test refactoring. Co-occurring edits or filename similarity are insufficient evidence of causal co-evolution. This independently verifies wave 1's source; it is not another dataset. [Co-evolution paper](https://yanmeng.github.io/papers/TOSEM231.pdf)

**C7. PASS: pruning obsolete test setup need not mean deleting a test. [S7]**
ARUS finds unnecessary Mockito stubbings in 40/128 Java projects: 280 definitions create 1,529 unnecessary runtime stubbings. Its evaluation uses project versions collected in January 2022; all updated suites pass, and developers merge changes removing 83 definitions. This demonstrates maintained cleanup of unused setup. It does not certify assertion correctness or test deletion, and some developers reject transformations that duplicate setup code. [ARUS manuscript](https://arxiv.org/html/2407.20924v1)

**C8. Firsthand reports distinguish intentional retirement from migration failure. [S8, S9]**
On 11 July 2026, OpenClaw maintainer steipete reports legacy compatibility paths keeping obsolete tests alive. The requested removal is bounded by a support decision: older unmigrated installations upgrade through 2026.6, while June SQLite imports remain supported. This is firsthand maintenance evidence, not a measured AI effect; the issue is closed, but I did not verify the linked implementation. [OpenClaw issue](https://github.com/openclaw/openclaw/issues/104648)

On 31 October 2025, a MUI contributor reports that migrating 23 packages from Vitest v3 to v4 makes tests fail because projects become interleaved with isolation disabled. The issue is marked Bug and closed with a linked PR. Its original body supports a runner/configuration problem, not obsolete assertions; the actual repair was not independently inspected. [Vitest issue](https://github.com/vitest-dev/vitest/issues/8894)

**C9. UNCERTAIN: AI agents increase obsolete retained tests after real migrations at a measurable population rate.**
The three AI studies establish controlled generation/selection mechanisms; S4–S7 establish lifecycle problems that predate current agents. Neither set supplies the missing longitudinal causal comparison. NetBSD's independent exploratory study tracks x86 test results from August 2011 through September 2025 and finds long-run suite growth with uneven failure periods. It measures neither oracle validity nor obsolete-test prevalence, so it cannot fill this gap. [NetBSD study, current v2](https://arxiv.org/html/2511.00915v2)

## Lifecycle ruling

Synthesis, not a validated universal retirement algorithm:

- Semantic-preserving refactor: retain current behavioral expectations; adapt setup/API calls or replace implementation-coupled checks with maintained behavioral equivalents.
- Framework/library migration: distinguish product regressions, harness failures and invalid expectations before changing assertions. Updated imports, fixtures and mocks are maintenance tasks.
- Intentional requirement retirement: remove or replace the old expectation after confirming the new support contract. Migration and backward-compatibility obligations may continue after an internal implementation disappears.
- A passing test, old filename, disabled status or disappearing method is a review lead, not a sufficient deletion rule. Examine replacements and the protection lost by removal.

## Sources read

Ranks: R3 firsthand repository evidence; R4 original peer-reviewed research; R4p original preprint. URLs sharing a row are the same work.

| ID | Title and URL | Date/version read | Rank/publication status |
|---|---|---|---|
| S1 | [Evaluating and Mitigating the Misguidance Effect of Buggy Code in LLM-Generated Unit Tests](https://arxiv.org/html/2607.22883v1) | 24 July 2026, v1; current submission history has only v1 | R4, accepted ISSTA 2026, PACMSE forthcoming; DOI 10.1145/3832204 |
| S2 | [Design choices made by LLM-based test generators prevent them from finding bugs](https://arxiv.org/html/2412.14137v1) | 18 December 2024, v1; current history has only v1 | R4p |
| S3 | [Evaluating LLM-Based Test Generation Under Software Evolution](https://arxiv.org/html/2603.23443v1) | 24 March 2026, v1; current history has only v1 | R4p |
| S4 | [Understanding Myths and Realities of Test-Suite Evolution, PDF](https://web.archive.org/web/20240413135742if_/https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=efe8079160bb66d4df86b1531ec03c17b0ecd3e2), [IBM institutional abstract](https://research.ibm.com/publications/understanding-myths-and-realities-of-test-suite-evolution) | FSE 11–16 November 2012; IBM catalog date 24 December 2012 | R4 |
| S5 | [Understanding Test Deletion in Java Applications, PDF](https://hifromajay.github.io/papers/msr25.pdf), [official conference abstract](https://2025.msrconf.org/details/msr-2025-technical-papers/24/Understanding-Test-Deletion-in-Java-Applications) | MSR 28–29 April 2025 | R4 |
| S6 | [Revisiting the Identification of the Co-evolution of Production and Test Code](https://yanmeng.github.io/papers/TOSEM231.pdf) | TOSEM 32(6), article 152, September 2023 | R4 |
| S7 | [Automatically Removing Unnecessary Stubbings from Test Suites](https://arxiv.org/html/2407.20924v1) | 30 July 2024, v1; January 2022 dataset snapshots | R4p, publication venue not independently established |
| S8 | [Remove pre-2026.4 compatibility shims and legacy migrations](https://github.com/openclaw/openclaw/issues/104648) | 11 July 2026 | R3, maintainer report |
| S9 | [Project order changed with v4](https://github.com/vitest-dev/vitest/issues/8894) | 31 October 2025; reported Vitest 4.0.5 | R3, firsthand user report |
| S10 | [Empirical Derivations from an Evolving Test Suite](https://arxiv.org/html/2511.00915v2) | current v2, 7 May 2026; observations end September 2025 | R4p |

## Contradictions and rulings

- The Pinto paper is FSE 2012, despite the old author PDF filename ICSE12. The full manuscript and IBM agree on venue. The direct author URL returns 404 in a real browser; CiteSeer's browser redirect supplies the archived original, successfully retrieved and read.
- S3 uses 22,374 for both program variants and generation tasks; its GPT-5/GPT-5 Mini labels also vary. Do not report a precise unique-variant count or that model identity without inspecting artifacts. Its causal explanation involving pretraining patterns is interpretation, not direct training-data observation.
- S5's 91.4% and S4's earlier roughly 58% are not a historical increase: observation granularity, refactoring filters and category construction differ. S5 extends the same six projects, so this is not independent population replication.
- S5's redundant label operationally includes passing deleted tests with lost protection. Report the label and the counterevidence together.
- Re-reading S1–S3 and S6 verifies wave 1; it adds no independent experiment.

## Open threads

A longitudinal matched study of AI-assisted projects through real refactors/migrations, with independent requirement histories and oracle review, remains missing. The OpenClaw and Vitest linked PR outcomes were not verified and must not be presented as confirmed successful cleanups. S4's small manually investigated categories and S5's Java-specific definitions merit care when generalizing.

## Searched and not found

No trustworthy population percentage of obsolete tests in vibe-coded projects; no causal estimate isolating agent use from project age, churn, framework migration or changing requirements; no justified rule to delete tests merely because they pass, age, use mocks or target replaced internals. Broad retirement searches surfaced commercial/SEO claims, which were excluded as evidence.


## Seconda passata, incarico 2

# Wave 2 researcher report: project memory and interventions

Scope: incoherent AI-assisted projects, instruction-file effectiveness, decision rationale, documentation drift and consolidation. Cutoff: 2026-10-07. Backend: native web search. No repository audit, no subagents.

**Exit reason:** scope saturation and the substantive-work cap. Four search rounds, 16 queries, 18 substantive source pages/works (17 full texts and one institutional abstract), two metadata/version pages and two failed URL reads. Follow-up section reads are not new works. ACM's Storey page and CiteSeerX's ICPC copy failed; author/preprint or institutional alternatives supplied the needed claims. ICPC evidence below is limited to an author-institution abstract, explicitly identified.

## Sourced claims

**C1. Stale references are real; 23% is not validated prevalence.** Context Rot v1 flags 230 references in 82/356 randomly sampled eligible repositories. A single author manually checks 50 flags: 32 genuine, 12 false positives, six ambiguous. Its first-commit comparison misses references introduced later; regexes also capture non-code tokens. The authors explicitly interpret 23% as a feasibility signal. Whether stale context changes agent outcomes and whether hybrid repair helps are research questions, not completed experiments. [S1](https://arxiv.org/html/2606.09090)

**C2. Confirmed instruction conflicts occur, but the detector's 28% is not confirmed prevalence.** Configuration Smells v5 selects the 100 most-starred application repositories with root instructions (39 AGENTS.md, 61 CLAUDE.md). It flags 28 conflicting files; first-author validation confirms 16, yielding 57% precision. Six PRs discuss consolidating agent documentation, but this is observed maintenance, without a before/after efficacy evaluation. Line-count and single-commit thresholds are smell heuristics, not proof of damage. [S2](https://arxiv.org/html/2606.15828v5)

**C3. Accuracy evidence supports relevant information, not universal benefit.** Evaluating AGENTS v3 tests four agent/model pairs on 300 SWE-bench Lite and 138 CTXbench tasks. Generated files bring no significant general resolution improvement; developer files average +2.4 percentage points versus absence (p=.21), with increased cost. A distinct appendix condition removes Markdown, examples and docs after file generation: generated context then improves average success by 2.7 points and beats developer context (Claude excluded for cost). No clear length–accuracy or length–cost relationship appears. This is an intervention on documentation availability, not an evaluated canonical-source cleanup. [S3](https://arxiv.org/html/2602.11988v3)

**C4. Efficiency gains do not establish correctness.** The efficiency paper v2 runs Codex/gpt-5.2-codex on 124 small, code-only historical PRs from ten selected repositories. A single root AGENTS.md reduces median runtime 28.64% and output tokens 16.58%; median total tokens increase 1.29%. Fifty tasks receive a nondegenerate-output sanity check. Semantic correctness and functional equivalence are explicitly outside scope. [S4](https://arxiv.org/html/2601.20404v2)

**C5. Vercel evaluates a different treatment.** Its Next.js 16 experiment reports 53% baseline/default skill, 79% explicitly triggered skill and 100% with a version-matched documentation index; shrinking the index from 40KB to 8KB retains that score. The vendor first repairs ambiguous prompts, contradictory tests and leakage, and targets APIs absent from training. Task/model/repeat denominators are not sufficiently reported for universal efficacy inference. This suggests the value of accessible new knowledge, not that more repository prose always helps. [S5](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals)

**C6. Narrow detection has led to real documentation repair.** Traditional DOCER reports issues to 15 active Google projects selected after manual annotation. Across 19 reported outdated-documentation instances, five are fixed; four projects respond positively, four report false positives, seven do not respond. Repairs include replacing renamed references and deleting an obsolete document. This is a small field intervention with observed uptake, without a control group or measured downstream comprehension/productivity effect. Its broader historical counts remain detector-defined. [S6](https://arxiv.org/html/2212.01479)

**C7. Comment maintenance is evaluated, with narrower targets than project intent.** Deep JIT combines change-aware inconsistency detection with comment updating. On a manually cleaned test sample, pretrained detection plus updating reaches 62.3% exact match versus 50% for never updating; a jointly trained hybrid obtains 87.8 F1 for detection. Half the balanced examples need no change, so exact match alone overstates actual repair success. DocChecker reports 72.3% accuracy/74.3 F1 on the full JIT set and BLEU-4 33.64 for summarization. These are benchmark outcomes for comments, not measured restoration of architectural intent or AI instruction coherence. [S7](https://arxiv.org/html/2010.01625v2), [S8](https://arxiv.org/html/2306.06347v3)

**C8. Architecture drift detection also has benchmark evidence.** ArDoCo links natural-language architecture descriptions to formal models in five projects. It reports trace-link F1=.81, accuracy .93 for undocumented model elements and .75 for described-but-missing elements. Missing elements are simulated by removing model elements; historical text is partly assumed consistent with current models. It detects leads for human adjudication, rather than proving that every mismatch is harmful or repairing missing rationale. Transfer to agent instructions is still open. [S9](https://publikationen.bibliothek.kit.edu/1000158208/150680132)

**C9. Preserving rationale has human experimental support, with limits.** Bratthall et al. test 17 industry/academic participants on two embedded systems. Rationale improves change-impact speed and correctness for one system (57 tasks; significance threshold p≤.10); the other is inconclusive (20 tasks). The 2014 ICPC study's institutional abstract reports two controlled experiments: better architecture understanding in one experiment and the combined analysis, no completion-time improvement, and greater benefit for experienced participants. Neither studies AI cleanup or proves all ADR formats effective. [S10](https://ase.in.tum.de/lehrstuhl_1/files/teaching/Lehrstuhl/DesignRationaleWiSe2003/bratthall_et_al_2000.pdf), [S11](https://research.monash.edu/en/publications/do-architectural-design-decisions-improve-the-understanding-of-so/)

**C10. A recent template study measures writing usability, not lasting comprehension.** Thirty-three undergraduates compare Nygard and MADR in a crossover experiment. Nygard has a higher weighted score (p=.002). The score weights template-field identification 15%, completion time/help consultations/objectivity 50%, and adoption recommendation 35%. It does not measure future maintainers' understanding or decision recall. Participants describe a tradeoff between concise records and richer rationale. [S12](https://arxiv.org/html/2604.27333v1)

**C11. ADR existence does not guarantee rationale completeness.** A September 2026 analysis covers approximately 4,300 ADRs from 550 repositories, using topic modeling, LLM classification and template checks. A 200-ADR manually annotated subset calibrates classification. The authors find alternatives and decision drivers underdocumented and content placed in mismatched sections. This is observational content analysis, without a consolidation intervention or a causal measure of maintenance harm. [S13](https://arxiv.org/html/2609.07375v1)

**C12. Generated rationale is not automatically recovered historical intent.** A five-model study of 100 architecture problems reports human-rationale overlap precision .267–.278 and recall .627–.715 across prompting strategies. Many unmatched arguments are judged helpful; the low precision therefore is not a hallucination rate. Generated rationales contain roughly 4.6–5.8 arguments versus 2.0 in expert sources, with 1.59–3.24% classified misleading. The experiment and six practitioner interviews assess rationale generation, not faithful preservation of the original decision history. Treat new explanations as candidate reasoning until supported by records or decision owners. The last sentence is synthesis. [S14](https://arxiv.org/html/2504.20781v3)

**C13. More artifacts can coexist with less human understanding.** Comprehension Debt analyzes 621 diaries from 207 students, without a control group: black-box acceptance, missing context, dependency and verification bypass coexist with using AI as an explanation scaffold. Storey's triple-debt model separates code problems, shared understanding in people, and missing goals/constraints/rationale in artifacts. Her warning about autogenerated documentation substituting apparent understanding for mental models is an expert conceptual argument; walkthroughs, review and intent records are proposed remedies, not experimentally evaluated in that article. [S15](https://arxiv.org/html/2604.13277), [S16](https://arxiv.org/pdf/2603.22106v4)

**C14. Status and handoff practices are expert engineering guidance.** Microsoft recommends consequential decisions only, recording context, alternatives, tradeoffs, confidence and Proposed/Accepted/Superseded status. Anthropic's long-running-agent account uses a requirements/status artifact, progress file, git history, incremental changes and clean handoffs to address repeated context resets. Both support concrete designs; neither supplies a controlled end-to-end comparison of canonical-source consolidation. [S17](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record), [S18](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

## Sources read

Rank: 1 official guidance; 4 original research (review status stated separately); 5 conceptual or original engineering account. Dates belong to the read version, not crawler timestamps.

| ID | Title / primary URL | Date / version | Status; rank |
|---|---|---|---|
| S1 | [Context Rot](https://arxiv.org/html/2606.09090) | 2026-06-08 v1 | Preliminary preprint; 4 |
| S2 | [Configuration Smells](https://arxiv.org/html/2606.15828v5) | 2026-07-30 v5 | Preprint; 4 |
| S3 | [Evaluating AGENTS.md](https://arxiv.org/html/2602.11988v3) | 2026-09-29 v3 | Updated preprint; 4 |
| S4 | [AGENTS.md Efficiency](https://arxiv.org/html/2601.20404v2) | 2026-03-30 v2 | JAWs paper author version; 4 |
| S5 | [Vercel AGENTS.md evals](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals) | 2026-01-27 | Vendor experiment; 5 |
| S6 | [Detecting Outdated Code Element References](https://arxiv.org/html/2212.01479) | 2022-12-02 v1 | Author preprint; EMSE 2024 publication; 4 |
| S7 | [Deep JIT Inconsistency Detection](https://arxiv.org/html/2010.01625v2) | 2020-12-26 v2 | AAAI 2021 author version; 4 |
| S8 | [DocChecker](https://arxiv.org/html/2306.06347v3) | 2024-02-03 v3 | Tool/benchmark paper; 4 |
| S9 | [ArDoCo inconsistency detection](https://publikationen.bibliothek.kit.edu/1000158208/150680132) | ICSA 2023 | Institutional full paper; 4 |
| S10 | [Design Rationale and Change Impact](https://ase.in.tum.de/lehrstuhl_1/files/teaching/Lehrstuhl/DesignRationaleWiSe2003/bratthall_et_al_2000.pdf) | PROFES 2000 | Controlled experiment; 4 |
| S11 | [Architectural Decisions and Understanding](https://research.monash.edu/en/publications/do-architectural-design-decisions-improve-the-understanding-of-so/) | ICPC 2014 | Institutional abstract only; 4 |
| S12 | [One Size Fits All? ADR Templates](https://arxiv.org/html/2604.27333v1) | 2026-04-30 v1 | Controlled-experiment preprint; 4 |
| S13 | [Text Mining and Classification of ADRs](https://arxiv.org/html/2609.07375v1) | 2026-09-07 v1 | ECSA-related preprint; 4 |
| S14 | [LLMs Generating Design Rationale](https://arxiv.org/html/2504.20781v3) | 2025-12-09 v3 | Author preprint; TOSEM publication indexed 2026; 4 |
| S15 | [Comprehension Debt](https://arxiv.org/html/2604.13277) | 2026-04-14 v1 | Qualitative preprint; 4 |
| S16 | [Cognitive and Intent Debt](https://arxiv.org/pdf/2603.22106v4) | 2026-04-06 v4 | Expert conceptual article; 5 |
| S17 | [Maintain an ADR](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record) | Undated live page, read 2026-10-07 | Official guidance; 1 |
| S18 | [Harnesses for Long-running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 2025-11-26 | Engineering account; 5 |

## Contradictions and rulings

- Accuracy, runtime efficiency and supplying new framework knowledge are distinct outcomes/treatments. S3, S4 and S5 do not justify a universal verdict for or against instruction files.
- S2's context-bloat heuristic cannot override S3's lack of a clear length effect; concise records can reduce authoring burden (S12), without proving universal agent accuracy gains.
- Useful generated reasons (S14) need not be the historical reasons. Preserve the distinction when consolidating intent.
- Detector flags measure leads, not confirmed prevalence, harm or successful repair. Detection, repair uptake, human understanding and agent task success need separate evaluation.

## Proposed consolidation design and outcome measures (synthesis)

Create a compact canonical account of current intent and verified behavior, with pointers to evidence. Record why consequential decisions were made, constraints, rejected alternatives, confidence and supersession; distinguish implemented facts, accepted decisions, hypotheses and generated explanations. Keep a reviewed handoff of completed work, unresolved issues and next steps. Do not infer undocumented historical rationale from present code alone.

Measure before/after:

1. Valid-reference rate and manually adjudicated detector precision, separating harmless mismatches.
2. Accepted repairs, time to repair and recurrence after later changes.
3. Rationale retention: proportion of known goals, constraints, alternatives and tradeoffs recoverable with correct provenance.
4. Fresh human/agent questions: correct current decision, why, affected components and predicted change impact; time and uncertainty.
5. Representative agent changes: task success alongside time, tokens and instruction violations, with matched conditions.
6. Authoring/maintenance effort and time to find the governing source. File-count reduction alone is not success.

## Open threads

Controlled stale-instruction harm/repair experiments; prospective canonical-source/handoff comparisons; long-term intent retention after consolidation; validation on professionals and modern models. Adaptive-context work such as ACE is a remaining lead, not read within this cap. The 2014 full paper and the 2026 journal rationale version would refine older/current-version limits.

## Searched and not found

No controlled end-to-end intervention that reconciles contradictory agent documents, preserves historical intent, consolidates knowledge and demonstrates durable human/agent gains. No reliable population prevalence of incoherent vibe-coded projects. No proof that adding prose repairs comprehension. These are bounded search gaps, not claims that such work cannot exist.


## Seconda passata, incarico 3

# Researcher report: evidence curation before artifact cleanup

Backend: native web search; stealth fetch used only for two primary pages blocked by native retrieval. Scope cutoff: 2026-10-07. Role: wave 2, evidence curation. No repository audit or cleanup.

Exit reason: five search rounds and 20-query budget reached, with convergence on provenance, executable preservation and filesystem-effect verification. Read 15 substantive primary works/pages, plus two primary GitHub metadata pages (17 primary pages total). Candidate aggregators and unsuccessful fetches support no claims. ACM policy and Microsoft's clarification were recovered through the skill's fetch fallback. The inaccessible 2018 Sciunit article was not treated as read; the 2017 authors' conference paper was read instead.

## Main finding

Compact reporting and disposal of bulky outputs have credible precedents, including an unusually close NVIDIA agent-workflow convention. The strongest evaluated storage precedent preserves reconstructable versions through deduplication. Provenance standards describe what produced a result, but neither metadata conformance nor a polished report proves scientific correctness or successful reproduction. No source here validates the entire proposed agent-driven consolidation-and-cleanup process.

## Claims

**C1. Preserve relationships, not merely a list of filenames. High confidence, standard.** W3C PROV models entities, activities and responsible agents, including which inputs an activity used and which outputs it generated. Its worked example connects an article's chart to original data and aggregation steps so a reader can investigate an apparent error. This supports a report-to-measurement-to-run-to-input chain; it is an interchange model, not evidence that the chain's assertions are true. [E1]

**C2. Portable provenance has actual implementations and explicit coverage limits. High confidence, bounded empirical demonstration.** Workflow Run RO-Crate (WRROC) provides three granularities, from tool/process execution to detailed workflow steps. The 2024 paper reports implementations in six workflow systems plus runcrate, and successful re-execution of one digital-pathology workflow. Its qualitative comparison represented 13 of 20 provenance subtypes (9 fully, 4 partially), versus 8 in CWLProv RDF. That 65% measures subtype representation in a particular analysis, not reproducibility success or evidence completeness. Data may remain at remote URIs rather than inside the metadata bundle. The authors expressly say general re-execution is not guaranteed; formal input mapping and environment preservation matter. [E2]

**C3. Capture necessary dependencies, then curate and test the package. High confidence, implemented mechanism with limits.** ReproZip traces execution to capture commands, environment variables, binaries, data and dependencies. Its 2013 paper permits excluding temporary files and large files obtainable elsewhere to control package size. Current 2.0.0 documentation likewise allows curated exclusions and stores files shared across runs once, but warns that replacing captured packages with incompatible repository versions may break reproduction. Packaging is Linux-only. The original paper does not guarantee identical outcomes for nondeterministic processes or incompatible kernels/hardware. These mechanisms support a checked reproduction package; they do not prove arbitrary exclusion is safe. [E3, E4]

**C4. A minimal reporting standard does not certify validity. High confidence, guidance.** MIASE requires accessible models, parameters and initial/boundary conditions, ordered procedures and algorithms, platform-dependent qualifications, and post-processing from raw numerical results to final outputs. Its scope is life-science simulations; it explicitly excludes deciding whether a model or experimental approach is correct, and does not require identical numerical results or the reasons for choosing the approach. Therefore a separate rationale and validation record are needed when consolidating decisions. [E5]

**C5. Compact experimental records are established software practice. High confidence, implemented mechanism.** Sumatra's interface gives each computation a record with reason, outcome, input/output data, code and executable versions, command arguments and tags; record details include dependencies, platform and stdout/stderr. Its data handling stores locations and SHA-1 checksums by default, with optional archived output copies. It warns that simultaneous runs sharing an output directory confuse file attribution and recommends separate directories. A checksum can detect a changed file; it cannot reconstruct a deleted file. The interface can delete records, optionally also their generated data, so this is not an automatic preservation guarantee. [E6, E7]

**C6. Preserve failed learning and correct records visibly. High confidence, editorial guidance.** The computational laboratory-notebook rules call for recording every experiment and result, dating entries, retaining the reason for the work, correcting mistakes without erasing the previous entry, and linking versioned code and raw values underlying figures. This supports retaining unsuccessful attempts and rejected hypotheses in a concise ledger. It does not establish that every failed run's full log or intermediate output must survive forever. [E8]

**C7. Availability, auditability and reproduced results are different achievements. High confidence, official standard.** ACM's 2020 policy separates Artifacts Available, Artifacts Evaluated and Results Validated. Functional artifacts need an inventory, sufficient execution instructions, consistency with the paper, relevant components and runnable analysis. Results Reproduced requires another team to obtain the principal results using author artifacts. Exact identity is unnecessary when acceptable tolerance preserves the main claims. An archive or report should therefore state whether it was merely assembled, inspected, or actually rerun. [E9]

**C8. MB/GB savings need not require deleting experimental versions. High confidence, two-workflow evaluation.** Sciunits used content-defined deduplication to retain reconstructable containers: four Food Inspection Evaluation versions occupied 907 MB separately and 333 MB together; four Variable Infiltration Capacity versions occupied 7 GB separately and 3 GB together. These are two scientific workflows, not typical coding-agent residue. Provenance graphs were condensed while retaining expandable detail; reduction in displayed nodes did not mean discarding the underlying graph. Performance costs varied: packaging/repeating the I/O-intensive VIC applications nearly doubled runtime, whereas FIE overhead was small. [E10, VII]

**C9. Wrongful deletion is documented, but public incident counts are not prevalence. Moderate confidence, original preprint study.** YoloFS classifies 290 public reports across 13 frameworks as 158 incidents, 49 exploits and 83 weaknesses. Impact percentages use the 207 incidents/exploits and different known-information denominators per dimension. This cannot estimate the probability that a user's cleanup will fail. In 11 deliberately constructed, 10–41-line projects with hidden destructive side effects, Claude Code 2.1.45/Sonnet 4.6 with the Linux prototype self-corrected in 8; the remaining effects stayed staged for user rejection. A post-task checker inspected expected file existence, contents and permissions. This is evidence for observing and retaining reversible filesystem effects, not production-wide safety or a Windows-ready cleaning tool. [E11, 3 and 5]

**C10. Report fidelity needs verification against evidence. Moderate confidence, controlled stress test.** DELEGATE-52 evaluates 19 models across 52 textual professional domains using chained transformation/inversion tasks and domain parsers. After 20 interactions, Gemini 3.1 Pro, Claude 4.6 Opus and GPT 5.4 lost approximately 25% of semantic reconstruction fidelity on average. This is neither 25% of documents destroyed nor an error rate for one experiment summary. The authors' May clarification describes a diagnostic stress test with limited intervention and a simplified harness, explicitly excluding overall task success and user satisfaction; Python was substantially more robust. Appendix C's generic similarity scores and LLM judgments were weak substitutes for domain checks. [E12, E13; E14 is the official publication listing]

**C11. A near-direct operational precedent exists. High confidence for the published instruction, effectiveness unmeasured here.** NVIDIA's NeMo-RL Brev skill at commit 63c02e122e (2026-07-02, GitHub commit metadata) keeps committed hypotheses and concise reproduction records in the checkout, heavy checkpoints/logs/evaluation dumps under per-campaign ephemeral directories, and reusable caches separately. It ends runs by summarizing metrics and paths in the git ledger. Cleanup is restricted to the current campaign's files, with enough small metadata retained for reproduction. This is practitioner guidance for Brev training experiments, not an evaluated general repository-cleaning intervention. [E15]

## Sources read

Ranks: 1 official documentation; 2 specification/policy; 3 primary repository; 4 original research or practitioner guidance. Accessed 2026-10-07. Undated documentation is the fetched version.

| ID | Primary title and URL | Date/version; status; rank |
|---|---|---|
| E1 | [PROV Model Primer](https://www.w3.org/TR/prov-primer/) | 2013-04-30; W3C non-normative Note; 2 |
| E2 | [Recording provenance of workflow runs with RO-Crate](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0309210) | 2024-09-10; peer-reviewed full paper; 4 |
| E3 | [ReproZip: Using Provenance to Support Computational Reproducibility](https://www.usenix.org/system/files/conference/tapp13/tapp13-final16.pdf) | TaPP 2013; full paper; 4 |
| E4 | [Using reprozip](https://docs.reprozip.org/en/latest/packing.html) | Undated, 2.0.0; official docs; 1 |
| E5 | [Minimum Information About a Simulation Experiment](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1001122) | 2011-04-28; Perspective/reporting guidance; 4 |
| E6 | [Sumatra: Using the web interface](https://sumatra.readthedocs.io/en/latest/web_interface.html) | Undated; official docs; 1 |
| E7 | [Sumatra: Input and output data](https://sumatra.readthedocs.io/en/latest/handling_data.html) | Undated; official docs; 1 |
| E8 | [Ten Simple Rules for a Computational Biologist's Laboratory Notebook](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004385) | 2015-09-10; Editorial/guidance; 4 |
| E9 | [Artifact Review and Badging](https://www.acm.org/publications/policies/artifact-review-and-badging-current) | 2020-08-24, v1.1; official policy; 2 |
| E10 | [Sciunits: Reusable Research Objects](https://cdmdicewebprd01.dpu.depaul.edu/pdfs/pubs/C23.pdf) | IEEE eScience 2017; authors' full paper; 4 |
| E11 | [Don't Let AI Agents YOLO Your Files](https://arxiv.org/html/2604.13536v1) | 2026-04-15 v1; original preprint; 4 |
| E12 | [LLMs Corrupt Your Documents When You Delegate](https://arxiv.org/html/2604.15597v1) | 2026-04-17 v1; full preprint; 4 |
| E13 | [Further Notes on AI Delegation and Long-Horizon Reliability](https://www.microsoft.com/en-us/research/blog/further-notes-on-our-recent-research-on-ai-delegation-and-long-horizon-reliability/) | 2026-05-15; authors' methodological clarification; 4 |
| E14 | [LLMs Corrupt Your Documents: publication listing](https://www.microsoft.com/en-us/research/publication/llms-corrupt-your-documents-when-you-delegate/) | April 2026, COLM 2026 listing; official abstract; 4 |
| E15 | [NeMo-RL Brev Etiquette](https://raw.githubusercontent.com/NVIDIA/skills/63c02e122e/skills/nemo-rl-brev-etiquette/SKILL.md) | [2026-07-02 commit](https://github.com/NVIDIA/skills/commit/63c02e122e); published workflow instruction; 3 |

## Contradictions and limits

- A reproducible recipe, a truthful report and a valid conclusion are separate properties. PROV/MIASE metadata do not settle correctness; ACM distinguishes availability from reproduced results.
- Summary size and information loss are different. Sciunit's condensed visualization preserves expandable provenance; a narrative summary that deletes its source cannot claim the same property.
- Scientific preservation guidance can require raw values and intermediate evidence; NVIDIA allows bulky ephemeral disposal. These have different evidentiary purposes, with no universal safe retention threshold.
- YoloFS's selected incident corpus and tiny constructed tasks do not establish general failure rates. DELEGATE-52's reconstruction score does not measure report-summarization accuracy.

## Proposed operational synthesis, not a validated intervention

Maintain three linked outputs: (1) durable findings and decisions, including negative or inconclusive attempts and limitations; (2) executable future protection, comprising useful regression tests and a reproduction recipe; (3) temporary execution output with an explicit retention decision.

Before disposal, connect each retained claim to run identifiers and supporting measurements; preserve code/input/environment versions, parameters, command/seed where relevant, result status and stable evidence locations. Recompute claimed figures or domain checks from retained material in an isolated fresh run, recording tolerances and mismatches. Keep irreplaceable inputs, unresolved-failure evidence and intermediate data needed to inspect disputed conclusions. Record the proposed file disposition and actual file changes, with a recoverable staging/archive period. These steps are an inference from the precedents above, not proof that a report replaces raw evidence or regression tests.

## Open threads

- Other workers own obsolete/invalid tests and AGENTS/documentation coherence; evidence records should link to those decisions without replacing their checks.
- Define claim-specific sufficiency: what exact retained evidence could falsify the conclusion after cleanup?
- Measure both reclaimed bytes and retained reproduction/diagnostic capability; avoid reporting only file count.
- Investigate how to automate disposition and claim checks without relying solely on an LLM's own judgment.

## Searched and not found

No representative estimate of AI-specific GB residue; no evaluated end-to-end automatic experiment-summary-plus-cleanup workflow; no universal minimum evidence bundle; no measured general effectiveness for NVIDIA's Brev cleanup convention. Failed retrieval of the 2018 Sciunit article and the Sumatra conference abstract yielded no claims.

