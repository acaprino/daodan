# Daodan

Daodan is a development harness for projects built with AI. It augments your coding
agent with a coherent way to understand a project, make changes, verify their
consequences and preserve what was learned.

Its job is to keep behavior, code, tests, instructions, documentation and artifacts
in agreement. It helps recover fragmented projects and avoid adding another layer
of duplication, dead code, misleading tests or forgotten experimental output.

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
| [project-lifecycle](docs/plugins/project-lifecycle.md) | Complete project work and coordination |
| [project-protocol](docs/plugins/project-protocol.md) | Run identity, snapshots, state, verification and recovery |
| [project-knowledge](docs/plugins/project-knowledge.md) | Durable instructions, guides, documentation and README |
| [senior-review](docs/plugins/senior-review.md) | Unified correctness review, automatic stack specialists and application subtraction |
| [testing](docs/plugins/testing.md) | Meaningful test authoring, suite diagnosis and protection-preserving remediation |
| [abstraction-architect](docs/plugins/abstraction-architect.md) | Concept ownership, duplication and design diagnosis |
| [codebase-xray](docs/plugins/codebase-xray.md) | Static structure, behavior and interconnection evidence |
| [repo-hygiene](docs/plugins/repo-hygiene.md) | Filesystem/Git hygiene and reversible workspace operations |
| [clean-code](docs/plugins/clean-code.md) | Readability with behavior preserved |
| [text-humanizer](docs/plugins/text-humanizer.md) | Voice and clarity of written content |

Knowledge offers instructions, guide, maintain and readme. It distinguishes
approved intent from observed implementation and updates existing documents first.
Operational state never belongs in AGENTS.md or CLAUDE.md.

A failed test can expose a product bug, wrong oracle, environment problem or
flakiness. Testing classifies the cause before quarantine. Refactoring alone does
not retire behavioral protection; count and coverage do not prove equivalence.

The three cleanup owners have different evidence: senior-review understands
application source, testing understands protection, repo-hygiene understands
filesystem and Git. Consolidation manages a run's owned evidence and retention.
It does not grant arbitrary repository deletion.

## Specialist extras

| Area | Independent plugins |
|---|---|
| Languages | [python-development](docs/plugins/python-development.md), [typescript-development](docs/plugins/typescript-development.md), [kotlin-development](docs/plugins/kotlin-development.md) |
| UI and desktop | [react-development](docs/plugins/react-development.md), [frontend-review](docs/plugins/frontend-review.md), [pwa-expert](docs/plugins/pwa-expert.md), [browser-extensions](docs/plugins/browser-extensions.md), [tauri-development](docs/plugins/tauri-development.md), [xterm](docs/plugins/xterm.md) |
| Architecture and infrastructure | [platform-engineering](docs/plugins/platform-engineering.md), [docker](docs/plugins/docker.md), [messaging](docs/plugins/messaging.md), [opentelemetry](docs/plugins/opentelemetry.md), [dependency-audit](docs/plugins/dependency-audit.md) |
| AI and evidence | [ai-tooling](docs/plugins/ai-tooling.md), [rag-development](docs/plugins/rag-development.md), [research](docs/plugins/research.md), [peer-review](docs/plugins/peer-review.md), [app-analyzer](docs/plugins/app-analyzer.md) |
| Product and business | [business](docs/plugins/business.md), [digital-marketing](docs/plugins/digital-marketing.md), [stripe](docs/plugins/stripe.md) |
| Specialized development | [grabber-development](docs/plugins/grabber-development.md), [trading-broker-integration](docs/plugins/trading-broker-integration.md), [libgdx-development](docs/plugins/libgdx-development.md), [obsidian-development](docs/plugins/obsidian-development.md), [csp](docs/plugins/csp.md) |
| Supporting tools | [marketplace-ops](docs/plugins/marketplace-ops.md), [learning](docs/plugins/learning.md), [system-utils](docs/plugins/system-utils.md) |

Extra outputs can be evidence for a project run. Automatic composition requires a
consumer with an explicit hard dependency; the core does not install every domain.
Playwright is required by the browser-facing plugins that declare it. Design
specialists used by frontend-review remain upstream.

## What is verified

The compiler validates kernels, bindings, contracts and generated packages.
Atomic helpers mechanically protect their own records and retained artifacts.
Semantic truth, test oracles and permission provenance still require evidence and
the coordinator's judgment. Prompt obligations are identified as such.

X-ray is static: inventory, files read in depth and runtime-exercised paths are
reported separately. A generated package test is distinct from an installed-host
execution probe. External private app storage is not a supported run root until
its permission binding is demonstrated.

Tri-Tech Code can consume these OpenCode packages and run contracts as an external
application. The marketplace stays public and neutral.

## Contributing

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
