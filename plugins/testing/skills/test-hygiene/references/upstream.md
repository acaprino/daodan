# Testing upstream provenance

Intake inspected on 2026-10-26. Both providers are already required by
`testing/plugin.toml`. This record retains delegation and supplies provenance;
it does not import an upstream method or create a copied-source sync target.
The full retained license notices below belong to their respective authors;
Daodan's MIT license does not replace them.

## TDD: Matt Pocock

Repository: [mattpocock/skills](https://github.com/mattpocock/skills).
Inspected commit: `5beb35b040e3de97e54fa9e386d7e42d15c295c2`.
Read [`skills/engineering/tdd/SKILL.md`](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/tdd/SKILL.md),
its `tests.md` and `mocking.md`, and the repository's
[`LICENSE`](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/LICENSE).
License: MIT, Copyright (c) 2026 Matt Pocock. Retained unmodified in
`LICENSE-mattpocock-skills-MIT.txt` in this directory.
Notice SHA-256: `0e7ac423bf2c6e223b7c5b156f8cf72da49d748e56a1641402c31f22ad07dbb5`.

Required identity: `mattpocock-skills@mattpocock`; method:
`mattpocock-skills:tdd`. Its owner supplies the test-first loop and public-contract,
oracle and mocking guidance. The inspected method also consults its owner's
`codebase-design` knowledge when interface design needs it. Keep that provider
reference with its owner rather than inventing a local TDD method.

Daodan supplies its own inventory, placement, review of existing protection,
cause classification, scope acceptance and snapshot-bound gates. Preserve
justified real-boundary and diagnostic regressions: a test's internal access,
mock or ordering check requires inspecting its actual contract before disposal.
An accepted contract/boundary decision is reused; ask only for an unresolved
decision. Automated TDD returns observed red evidence to the implementation
owner; only explicitly selected interactive teaching waits for human code.

## Browser E2E: Seth Hobson

Repository: [wshobson/agents](https://github.com/wshobson/agents).
Inspected commit: `0874a27b17a22e2b7c2e2bcd725768e0803cad06`.
Read [`plugins/developer-essentials/skills/e2e-testing-patterns/SKILL.md`](https://github.com/wshobson/agents/blob/0874a27b17a22e2b7c2e2bcd725768e0803cad06/plugins/developer-essentials/skills/e2e-testing-patterns/SKILL.md)
and the repository's
[`LICENSE`](https://github.com/wshobson/agents/blob/0874a27b17a22e2b7c2e2bcd725768e0803cad06/LICENSE).
License: MIT, Copyright (c) 2024 Seth Hobson. Retained unmodified in
`LICENSE-wshobson-agents-MIT.txt` in this directory.
Notice SHA-256: `f89abb55d9f073f38f1703e4518f0613c788c6174be7f13b8dfe48a1c076c746`.

Required identity: `developer-essentials@claude-code-workflows`; method:
`developer-essentials:e2e-testing-patterns`. Its owner supplies browser-test
techniques and nested examples. Load those examples only when needed. Daodan
keeps independent failure-mode protection, real-boundary verification and
causal diagnosis before quarantine. No browser runner, dependency installation,
retry policy or mutation job is introduced by this intake.

## Availability and maintenance

On the active host, resolve and load the actual provider before its method is
needed. Dependency registration and generated packages do not establish that a
host can run the provider. Missing providers leave dependent actions open;
recover through that host's supported installation mechanism as specified by
`test-hygiene`. Keep independent static diagnosis available. The local Codex
catalog exposes both methods at intake; this is availability evidence, not an
installed-host execution probe for all five hosts.

Inspected source revisions are evidence references; provider installations
receive updates independently. Recheck their canonical sources and licenses
when refreshing this integration. No upstream implementation was modified or
copied; no copied-source sync row is added. The local TDD and E2E copies retired
in marketplace 18.0.0 remain retired. This reference and the two full notices
live under the skill so all five host packages ship them.
