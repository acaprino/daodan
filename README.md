# Daodan

<p align="center">
  <img src="docs/assets/branding/shinatama-logo-oni.png" alt="Shinatama from Oni beside the Shinatama wordmark" width="800">
</p>

Shinatama is the companion marketplace to [Daodan](https://github.com/acaprino/daodan).
While Daodan holds the core software engineering harness (`codebase-map`,
`project-lifecycle`, `senior-review`, `testing`, `project-knowledge` and core
language/stack providers), Shinatama holds 24 independent domain verticals,
research, office workflows and specialized framework toolkits. Cross-model
deliberation (`peer-review`, `moe`) ships with Daodan.

One hand-authored source ships to Claude Code, GitHub Copilot, Codex, Pi and
OpenCode V2. Useful language, framework and domain specialists remain independent.

## Start with the project outcome

| Command | Use it for | Result |
|---|---|---|
| /project-lifecycle:handover | Take responsibility for an unfamiliar project | A consultant dossier with verified facts, readiness, risks and open questions |
| /project-lifecycle:maintain | Lead a complete rationalization | A staged Senior Maintainer campaign with an approved roadmap and verified outcomes |
| /project-lifecycle:assess | Understand incoherence and accumulated debt | Evidence, coverage and an actionable plan with owners and dependencies |
| /project-lifecycle:repair | Apply an identified plan | Scoped remedies, verified phases and visible open decisions |
| /project-lifecycle:change | Bootstrap, feature, bugfix, refactor or migration | Working behavior and coherent code, tests and knowledge |
| /project-lifecycle:verify | Check a candidate revision and its consequences | Snapshot-bound checks, review and honest limitations |
| /project-lifecycle:consolidate | Close experiments and reduce residual output | Verified conclusions, retained evidence and artifact disposition |

These entries use the same specialist methods as their standalone commands.
Choose a focus (knowledge, structure, tests, artifacts or all) and a depth
(quick, standard or deep). Assessment starts with one scoped pass. Development work
uses checks proportional to its risk, rather than launching every auditor each time.

Run records live in .daodan/runs/<id>/ inside the project. Resume by exact run ID.
The record identifies intent, scope, file snapshots, authorization, plan, deliveries
and checks. A missing worker or an unexecuted gate remains visible.

Preview is the default for repair and retention. --fix applies authorized edits;
--commit adds commits and enables commit-only application cleanup. --purge is a
separate explicit grant for concluded, owned experimental output. Quarantine moves
preserve data and do not count as bytes deleted.

## Take over a project, then maintain it

Two separate entries serve an incoming consultant and the subsequent maintenance
work. Both reuse Daodan's canonical specialists and keep their evidence in owned
project runs.

| Entry | Outcome |
|---|---|
| `project-lifecycle` `handover` | A consultant dossier: product purpose, modules and critical flows, setup and test procedures, constraints, evidenced risks, real open questions and a first scoped work plan |
| `project-lifecycle` `maintain` | The Senior Maintainer campaign: baseline review and assessment, an approved roadmap, corrections, rationalization, verification and closure |

Start with handover when you need to understand and take responsibility for an
unfamiliar project. It writes run-owned reports and leaves project files alone.
Checks default to `none`; `--checks=local` requests permitted local checks after
reviewing their commands and environment. The dossier distinguishes procedures
read from source from commands actually exercised. It proposes maintenance work
and never starts it automatically.

Run maintain when you want the complete rationalization. Its canonical campaign
method owns the guidance previously pasted from this README. Each stage uses its
owning method and separate lifecycle run; the command keeps the stage handoffs,
authorizations and resume references together.

| Host | Handover entry | Maintain entry |
|---|---|---|
| Claude Code / OpenCode V2 | `/project-lifecycle:handover` | `/project-lifecycle:maintain` |
| Codex | `handover-workflow` skill | `maintain-workflow` skill |
| GitHub Copilot | `handover` prompt with `handover-coordinator` | `maintain` prompt with `maintain-coordinator` |
| Pi | `/project-lifecycle-handover` | `/project-lifecycle-maintain` |

For example, on Claude Code or OpenCode V2:

```text
/project-lifecycle:handover . --depth=standard --checks=none
/project-lifecycle:maintain . --fix --pace=guided --from-handover <exact-assess-run-id>
```

Run the second entry after reading the dossier and choosing the maintenance scope.
On the other hosts pass the same arguments through the entry listed above. See
[host setup](docs/hosts.md) for worker and external-method support.

Maintain accepts a target path or module, exclusions, focus
`all|knowledge|structure|tests|artifacts`, depth `quick|standard|deep`, pace
`guided|autonomous`, authorization `--dry-run|--fix|--commit`, exact resume IDs and
an optional `--from-handover` assess run. Defaults are whole project, focus all,
depth deep, guided pace and dry-run. Dry-run ends at the roadmap. Fix permits
scoped edits; commit also permits local commits and commit-only application cleanup,
subject to its own prerequisites. Push, deployment and permanent purge each need
separate authorization.

Guided pace waits at the campaign brief and at the findings/roadmap. Autonomous pace
removes those two waits while retaining every decision and gate owned by a method.
Second opinions such as peer-review or dependency-audit are offered when available
and never run unasked. A handover result supplies evidence; it grants no permission
to change the project.

Every brief names the exact runs and the next entry. Resume those IDs after validating
scope, candidate and authorization; an unrelated latest report is never a resume
source. Completed stage results remain evidence of their recorded candidates. The
final verification must match the current project, with missing deliveries and
mandatory checks visible. [Lifecycle details](docs/plugins/project-lifecycle.md)
describe both entries. Instruction and testing guidance follows the
[source-backed research note](docs/references/project-instructions-and-test-practices.md).

## Install

Register the repository marketplace on the corresponding host:

```bash
claude plugin marketplace add acaprino/shinatama
copilot plugin marketplace add acaprino/shinatama
codex plugin marketplace add acaprino/shinatama
```

For plugins that declare cross-marketplace dependencies on `@daodan`
(`digital-marketing`, `frontend-review`), also register
`acaprino/daodan`:

```bash
claude plugin marketplace add acaprino/daodan
copilot plugin marketplace add acaprino/daodan
codex plugin marketplace add acaprino/daodan
```

Install project-lifecycle@daodan for the complete project paths, or individual
specialists for a narrower task. Required local dependencies form the mandatory
closure; external dependencies must also be available on the host.

The lifecycle uses upstream development methods from
superpowers@claude-plugins-official. Testing uses
mattpocock-skills@mattpocock and developer-essentials@claude-code-workflows.
The [dependency catalog](.claude-plugin/marketplace.json) records the exact declarations.
No upstream method is copied into a second local implementation.

Pi installs the tagged repository as one package:

```bash
pi install git:github.com/acaprino/daodan@v<metadata.version>
```

Select components through package globs in Pi settings. Isolated workers use
pi-subagents; MCP uses pi-mcp-adapter, as declared by the adapter.

OpenCode V2 installs the generated package through npm's repository-path selector:

```bash
opencode plugin add 'github:acaprino/daodan#v<metadata.version>::path:exports/opencode'
```

OpenCode Desktop uses its bundled V2 service. Loader options select plugins and
close mandatory local dependencies; exclusions cannot remove a required dependency.
Use an existing released tag in place of <metadata.version>.

See [host distribution and migration](docs/migration-from-claude-code-daodan.md)
and [the harness migration](docs/migration-to-coherent-harness.md).

The [complete plugin catalog](docs/catalog.md) lists every registered skill, role
and workflow through its plugin page, with mandatory direct and transitive
dependencies. The [host reference](docs/hosts.md) explains the corresponding
commands, paths, installation requirements and runtime limits on each host.

## Canonical owners

| Plugin | Responsibility |
|---|---|
| AI and research | [ai-tooling](docs/plugins/ai-tooling.md), [rag-development](docs/plugins/rag-development.md), [research](docs/plugins/research.md) |
| Office, business and marketing | [office](docs/plugins/office.md), [business](docs/plugins/business.md), [digital-marketing](docs/plugins/digital-marketing.md), [stripe](docs/plugins/stripe.md) |
| Writing | [text-humanizer](docs/plugins/text-humanizer.md) |
| UI, web and desktop frameworks | [frontend-review](docs/plugins/frontend-review.md), [pwa-expert](docs/plugins/pwa-expert.md), [browser-extensions](docs/plugins/browser-extensions.md), [tauri-development](docs/plugins/tauri-development.md), [xterm](docs/plugins/xterm.md), [obsidian-development](docs/plugins/obsidian-development.md), [libgdx-development](docs/plugins/libgdx-development.md) |
| Domain and infrastructure verticals | [trading-broker-integration](docs/plugins/trading-broker-integration.md), [grabber-development](docs/plugins/grabber-development.md), [app-analyzer](docs/plugins/app-analyzer.md), [csp](docs/plugins/csp.md), [messaging](docs/plugins/messaging.md), [opentelemetry](docs/plugins/opentelemetry.md) |
| Supporting utilities | [learning](docs/plugins/learning.md), [system-utils](docs/plugins/system-utils.md), [marketplace-ops](docs/plugins/marketplace-ops.md) |

## Presentations, spreadsheets and documents

The [Office plugin](docs/plugins/office.md) creates and revises editable `.pptx`,
works with native `.xlsx` cells, formulas, tables and charts, and reads, creates
or edits `.docx` paragraphs, styles, tables and sections. Existing-file edits
include preservation checks for content and features the task needs to retain.
Presentations combine creative designer/reviewer roles, SlidePoise generation,
DeckCraft editing and preview, and the active harness's image-generation tool.

On Claude Code or OpenCode V2, use `/office:presentation`,
`/office:workbook` or `/office:document`. The [host guide](docs/hosts.md#office-entry-points)
lists the corresponding Codex skills, Copilot prompts and Pi commands. A normal
request can describe the outcome, source files, language and template:

```text
Create an editable Italian PowerPoint from this workbook and Word report.
Preserve the source figures, use our brand assets and include a reviewed preview.
```

SlidePoise needs its separate runtime, image-generation tools and a compatible
presentation renderer. Excel and Word use an available engine that supports the
requested file features. The plugin's read-only inspectors provide structure and
preservation evidence; actual recalculation, field updates and visual page review
need the corresponding engines. See [Office setup and examples](docs/plugins/office.md#setup-and-first-use).

## What is verified

The compiler validates kernels, bindings, contracts and generated packages.
Atomic helpers mechanically protect their own records and retained artifacts.
Semantic truth, test oracles and permission provenance still require evidence and
the coordinator's judgment. Prompt obligations are identified as such.

Codebase Map is static: inventory, files read in depth and runtime-exercised paths are
reported separately. Since Map 7.0.0 / marketplace 35.0.0, snapshots default to
SQLite; `--format json` explicitly selects upstream compatibility. Source tools
send selected text with counts and truncation, while reports remain Markdown.
See [snapshot formats and source reading](docs/plugins/codebase-map.md#reading-source-from-a-snapshot)
and the [release verification record](docs/superpowers/reports/2026-10-16-codebase-map-binary-storage.md).
A generated package test is distinct from an installed-host
execution probe. External private app storage is not a supported run root until
its permission binding is demonstrated.

Tri-Tech Code can consume these OpenCode packages and run contracts as an external
application. The marketplace stays public and neutral.

## Upstream projects and inspiration

[agent-html-kit](https://github.com/leex279/agent-html-kit) inspired the separation
of agent-authored content from reusable HTML presentation. Daodan's
[report renderer](docs/plugins/report-rendering.md) is an original implementation
that preserves Markdown as the canonical report and adds optional offline HTML
views for analyses, brand naming and reviews.

[andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)
is the MIT-licensed source of four working principles adopted by Daodan: Think
Before Coding, Simplicity First, Surgical Changes and Goal-Driven Execution.
[Project knowledge](docs/plugins/project-knowledge.md) adapts them for project
instruction creation and maintenance, preserving equivalent project guidance and
adding local rules for verification and shared ownership.

## Upstream projects and inspiration

[blader/humanizer](https://github.com/blader/humanizer), by Siqi Chen (MIT), is an
upstream source for [text-humanizer](docs/plugins/text-humanizer.md). The local
derivative keeps local pattern numbering, fact-preservation safeguards,
registers, an Italian language profile and its own file-editing contract. Upstream
changes are reconciled selectively rather than replacing those local rules.

## Contributing

> [!WARNING]
> **Never repair generated exports by hand or equate registration with execution.**
> Correct kernels, adapters or compiler source, then review all five hosts through
> nested references and worker resources. Agents/coordinators execute and verify;
> harnesses own supported continuation and state; skills supply methods. A turn
> end or empty child is not task success. Real tools, identities, isolation,
> permissions, dependencies, capture controls and output contracts require the
> [operational checks](docs/hosts.md#operational-compatibility-review), separately
> from manifest parity and live workflow evidence.

Edit kernels under plugins/ and host mechanisms under adapters/. All exports and
root catalogs are generated. Runtime resources belong under skills/. The toolchain
is stdlib Python; OpenCode's fixed loader uses Node's standard library.

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check --support
python -m unittest discover -s tests
python scripts/sync_codex_instructions.py --check
python scripts/sync_plugin_docs.py --check
```

Follow [CLAUDE.md](CLAUDE.md) for dependency, version and publication rules.
[Architecture](docs/superpowers/specs/2026-10-07-daodan-coherent-harness-design.md)
and [implementation plan](docs/superpowers/plans/2026-10-07-daodan-coherent-harness.md)
record this migration. [Behavioral evals](evals/) complement deterministic compiler
and helper tests.

MIT licensed. The Daodan is the symbiote that augments its host.


## Scope-aware knowledge selection

The shared [Skill Catalog](docs/plugins/skill-catalog.md) selects knowledge from
actual available host/project skills for each evidenced task scope. Senior Review
uses it across languages and frameworks with one preparation, delivery ledger,
verification panel and report. Skills declare their own SKILL.toml metadata; adding
a competence needs no new reviewer or central stack table. Selected inputs carry
content fingerprints and per-worker delivery accounting. External unclassified
skills and unavailable inventory remain explicit coverage gaps.
