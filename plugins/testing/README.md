# Testing

Maintain useful protection as code changes: reuse and update existing tests,
add checks for unprotected failure modes, and rationalize an accumulated suite.
Fewer tests or a green run alone do not establish better protection.

## Responsibilities and entry points

| Intention | Daodan entry | Canonical owner |
|---|---|---|
| Add or update behavior-driven checks | `/daodan:write-tests` | `testing:test-writer`, with `test-hygiene` placement and existing-protection rules |
| Diagnose suite health | `/daodan:check-health` | `testing:test-preparation` and `testing:test-remediation-method`, mode `audit` |
| Review, clean up and reorganize existing tests | `/daodan:maintain-tests` | `testing:test-remediation-method`, mode `consolidate`, and its cause-specific repair owners |
| Include test consolidation in repository cleanup | `/daodan:tidy-repo` | The same consolidation method; repository cleanup has no second test policy |

For each requested behavior and independent failure mode, inspect current checks
and choose reuse, update or a justified addition. Zero additions is a valid
outcome. Revise affected tests when contracts change; a refactor preserves and
retargets their protection. Consolidation inventories behavioral oracles and
bugfix provenance before accepted replacement or retirement. Unresolved rows
stay protected. Runners, configuration, exact-candidate gates and recovery belong
to the existing preparation and remediation methods.

## Upstream projects and licenses

Local governance, preparation, auditing and remediation are original Daodan
content under the repository's [MIT license](../../LICENSE). External methods
are required delegated providers, installed and updated through their owners.
Their methods are not copied into this plugin. The inspected revisions below
record intake evidence, not installation pins or a claim about later releases.

| Provider | Method and inspected revision | License and retained notice | Local integration |
|---|---|---|---|
| [mattpocock/skills](https://github.com/mattpocock/skills) | [`skills/engineering/tdd/`](https://github.com/mattpocock/skills/tree/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/tdd), `5beb35b040e3de97e54fa9e386d7e42d15c295c2` | MIT, Copyright 2026 Matt Pocock; [full notice](skills/test-hygiene/references/LICENSE-mattpocock-skills-MIT.txt) | `mattpocock-skills:tdd` supplies TDD, behavioral tests and mocking knowledge. Daodan owns placement, existing-test review and delivery gates. |
| [wshobson/agents](https://github.com/wshobson/agents) | [`plugins/developer-essentials/skills/e2e-testing-patterns/`](https://github.com/wshobson/agents/tree/0874a27b17a22e2b7c2e2bcd725768e0803cad06/plugins/developer-essentials/skills/e2e-testing-patterns), `0874a27b17a22e2b7c2e2bcd725768e0803cad06` | MIT, Copyright 2024 Seth Hobson; [full notice](skills/test-hygiene/references/LICENSE-wshobson-agents-MIT.txt) | `developer-essentials:e2e-testing-patterns` supplies browser-test techniques when the accepted scope needs them. |

The [shipped provenance reference](skills/test-hygiene/references/upstream.md)
records source paths, verification, integration boundaries and host availability.
Only the license notices are reproduced. The former local TDD and E2E copies
were retired in marketplace 18.0.0; this intake preserves that delegation.

Read the [plugin guide](../../docs/plugins/testing.md) for preparation, auditing,
consolidation, failure classification and the generated component reference.
