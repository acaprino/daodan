# Shinatama

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
OpenCode V2.

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

Pi installs the tagged repository as one package:

```bash
pi install git:github.com/acaprino/shinatama@v<metadata.version>
```

OpenCode V2 installs the generated package through npm's repository-path selector:

```bash
opencode plugin add 'github:acaprino/shinatama#v<metadata.version>::path:exports/opencode'
```

The [complete plugin catalog](docs/catalog.md) lists every registered skill, role
and workflow through its plugin page, with mandatory direct and transitive
dependencies. The [host reference](docs/hosts.md) explains the corresponding
commands, paths, installation requirements and runtime limits on each host.

## Catalog overview

| Area | Plugins |
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
lists the corresponding Codex skills, Copilot prompts and Pi commands.

## Upstream projects and inspiration

[blader/humanizer](https://github.com/blader/humanizer), by Siqi Chen (MIT), is an
upstream source for [text-humanizer](docs/plugins/text-humanizer.md). The local
derivative keeps local pattern numbering, fact-preservation safeguards,
registers, an Italian language profile and its own file-editing contract. Upstream
changes are reconciled selectively rather than replacing those local rules.

## Contributing

Edit kernels under `plugins/` and host mechanisms under `adapters/`. All exports and
root catalogs are generated. Runtime resources belong under `skills/`.

```bash
python scripts/daodan_build.py
python scripts/daodan_build.py --check --support
python -m unittest discover -s tests
python scripts/sync_codex_instructions.py --check
python scripts/sync_plugin_docs.py --check
```

Follow [CLAUDE.md](CLAUDE.md) for dependency, version and publication rules.
MIT licensed.
