# Project instructions and test practices for architectural refactoring

Research snapshot: 2026-10-08. This note explains the instruction and testing
clauses of the [README prompt](../../README.md#one-prompt-for-a-guided-project-rationalization).
It combines vendor guidance with Daodan's existing methods. Recommendations below
are a synthesis for architectural work, not a universal policy prescribed by any
one vendor. Documentation and source inspection do not establish installed-host
behavior or runtime coverage.

## Make the requested outcome verifiable

Describe the result, constraints and sequence explicitly. Provide the relevant
project context and use action verbs when implementation is intended. Avoid
model-specific settings in a portable prompt: a technique measured on one model
needs evaluation before transfer. General solutions must satisfy requirements,
rather than hardcode the inputs of existing tests.
[Anthropic prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
supports these distinctions.

For broad changes, explore and plan before implementation. Define observable
acceptance criteria, then select executable checks appropriate to the affected
behavior. Review the final diff against requirements in an independent context.
Persistent instructions should carry project-specific commands and non-obvious
constraints. [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
provides this workflow guidance; [verification-loop guidance](https://claude.com/resources/articles/building-verification-loops-in-claude-code-with-skills)
explains how repeatable checks can become reusable procedures.

Daodan supplies the local ownership and verification contract: [project-lifecycle](../plugins/project-lifecycle.md)
coordinates the outcome, [project-protocol](../plugins/project-protocol.md) binds
records and checks to snapshots, and [senior-review](../plugins/senior-review.md)
owns correctness review. The README's initial full-depth X-ray, new or updated from
an earlier run when the X-ray's own change set recommends it, and its severe-defect
priority are explicit choices for this global refactoring request. They are not a
claim that every small change must run a complete analysis.

The supplied [multica-ai instruction file](https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md)
adds four behavioral principles: expose assumptions, prefer simple solutions,
keep changes within scope and define verifiable goals. It favors caution and
allows proportional judgment for trivial work. Daodan already attributes these
principles to this source in its [working-principles reference](../../plugins/project-knowledge/skills/instructions-method/references/working-principles.md),
with a 2026-05-17 snapshot and local adaptations. The fifth principle, canonical
ownership of shared logic, is a local addition. No second instruction block is
needed. For an authorized global refactor, scope discipline means each change
serves that objective; it does not prohibit the requested restructuring.

## Maintain the instruction sources the harness actually loads

Discover instruction files, scopes and the repository's canonical-source or
regeneration rule before editing. Preserve project-specific decisions and
verified commands. Keep detailed procedures in appropriate guides or skills;
keep operational state in run records. Instruction text guides the agent, while
deterministic enforcement requires supported configuration, hooks or CI checks.
[Claude's memory documentation](https://code.claude.com/docs/en/memory) describes
the distinction between instructions and enforcement and emphasizes concise,
consistent guidance.

Host discovery is not interchangeable:

| Host | Verified documentation or source | Consequence for the portable prompt |
|---|---|---|
| Claude Code | [Memory and project instructions](https://code.claude.com/docs/en/memory) | Loading of `CLAUDE.md`, local instructions and `AGENTS.md` depends on scope, settings and supported version. Check actual loaded sources and coexistence rules. |
| Codex | [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Global and root-to-working-directory discovery includes override and fallback selection. Preserve scoped guidance and verify configuration. |
| Pi | [Resource loader](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/resource-loader.ts), [terminal usage](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/usage.md) | Startup loads selected instruction files through ancestor directories. The startup inventory can help check what was loaded; this does not prove arbitrary nested files reload automatically. |
| OpenCode V2 | [Instructions](https://opencode.ai/v2/docs/instructions/) | V2 documents `AGENTS.md` and scoped discovery. Combined instructions do not have automatic conflict resolution; changed loaded nested instructions need a fresh session. Avoid assuming legacy fallback behavior. |
| Copilot on GitHub | [Repository custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions) | Repository-wide, path-specific and agent instruction support depends on the feature. This page does not establish identical behavior in every IDE or CLI. |

The [OpenAI guidance on skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
also recommends reviewing accumulated instructions and narrowing applicability.
Its model-specific autonomy advice does not replace project verification gates.

For this repository, `CLAUDE.md` remains canonical and `AGENTS.md` is generated by
`scripts/sync_codex_instructions.py`. New vendor guidance does not authorize
changing that relationship. [Daodan's instructions method](../../plugins/project-knowledge/skills/instructions-method/SKILL.md)
already respects canonical sources, nested scopes and generated-copy parity.

## Put concrete test guidance in durable instructions

The useful testing section records the project's actual runners and commands,
required services, layer ownership, fixtures, isolation, cleanup, test-double
boundaries, failure diagnosis and verification gates. It should explain applicable
conventions and exceptions rather than demand one framework, directory layout or
test quota for every project. Runner APIs and commands must match installed
versions. [Vitest's AI test-writing guidance](https://vitest.dev/guide/learn/writing-tests-with-ai)
emphasizes source/configuration context, meaningful assertions, reviewing generated
tests, appropriate mocking and actually executing the result.

The following rules are generalizable when their underlying resources or behavior
exist in the project:

| Concern | Evidence and application |
|---|---|
| Observable contracts | [Playwright](https://playwright.dev/docs/best-practices) and [Testing Library](https://testing-library.com/docs/guiding-principles/) favor user-visible behavior and interfaces over UI internals. Applying the same reasoning to backend API results and persisted invariants is our inference. |
| Independent expected results | [Hypothesis on optimization testing](https://hypothesis.works/articles/testing-performance-optimizations/) explains why running the subject to obtain its expected answer is ineffective. Use requirements, independently stated examples, justified properties or a simpler reference calculation. Agreement between implementations alone does not prove correctness. |
| Isolation and cleanup | [Playwright isolation](https://playwright.dev/docs/browser-contexts) describes fresh browser contexts. [Vitest mocking](https://vitest.dev/guide/mocking.html) distinguishes cleanup of mocks, clocks, globals and environment state. Extend this reasoning to owned database records, files or background work where relevant. |
| Intermittent failures | [pytest's flaky-test guidance](https://docs.pytest.org/en/stable/explanation/flaky.html) identifies uncontrolled state, order, parallelism, strict timing assertions and thread cleanup. Retries can mitigate symptoms without repairing the cause. Rewriting or removing a test depends on preserving its functionality elsewhere. |
| Layer and risk | [Google SRE's testing chapter](https://sre.google/sre-book/testing-reliability/) distinguishes tests with different costs and confidence and prioritizes critical paths and known bugs. This supports selection by risk, not a mandatory test count or pyramid ratio. |
| Durable regressions | [Hypothesis replay guidance](https://hypothesis.readthedocs.io/en/latest/tutorial/replaying-failures.html) distinguishes explicit examples from caches and version-sensitive replay data. Required regression inputs deserve durable protection, rather than reliance on transient runner state alone. |

Audit the whole suite, then remediate in scoped batches. Preserve the requirement,
layer, preconditions and distinct failure mode protected by each surviving test.
Similar assertions can remain necessary at different boundaries. A call-order
assertion can be justified when ordering itself is a requirement, such as
authorization before a write.

Daodan's [testing method](../../plugins/testing/skills/test-remediation-method/SKILL.md)
classifies product defects, wrong expected results, environment failures,
test-isolation defects, intermittent behavior and unknown causes before
disposition. Its
[consolidation procedure](../../plugins/testing/skills/test-remediation-method/references/consolidate.md)
requires acceptance of the behavior inventory before rewriting and checks the
actual candidate before completion. These exact acceptance and quarantine rules
are Daodan governance, not a named universal standard in the vendor sources.

## Resolve apparent conflicts without weakening protection

Anthropic's long-horizon example discourages test editing, while the coding
section acknowledges incorrect tests. For an expressly authorized test
rationalization, the useful synthesis is to preserve verified requirements and
regressions while permitting evidenced corrections and replacement protection.
A blanket ban on test changes would prevent that work.
[Anthropic prompting guidance](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).

Playwright's recommendation to control third-party UI dependencies improves
reproducibility. It does not justify replacing real transactions or database
concurrency with mocks when those semantics are the requirement.
[Playwright best practices](https://playwright.dev/docs/best-practices).

The [Claude evaluation guide](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)
addresses LLM evaluation criteria, data and grading. Its advice on evaluation
volume is not evidence for retiring product regression tests. Likewise, a
suggested instruction-file size is guidance, not proof that a durable rule can
be discarded.

## Research scope and limitations

Research covered prompting, testing and instruction loading in three parallel
tracks, plus the supplied multica-ai instruction source. The 21 distinct primary
documentation pages or source files linked above were compared with the local
lifecycle, knowledge and testing methods. Sources were read, rather than used
solely as search snippets. OpenAI documentation was used after local material
did not establish the host's full loading behavior.

The portable prompt records requirements and evidence boundaries. It does not
establish enforcement, exercise an installed host or prove a project's runtime
behavior. Host/source details are a dated research snapshot. Validate applicability
against the actual host, installed stack versions and project rules before
changing durable obligations. Static X-ray, automated test results and browser,
database or production exercise remain distinct evidence.
