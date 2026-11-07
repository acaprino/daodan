# Modules

Snapshot digest `60f8c8a168e8ac9fba0640898cd325b079c326b20814fe3be9065bc93a974541`. Files: 15. Modules: build: 4; declared: 0; proposed: 0. Statuses: confirmed: 4; inferred: 0; incomplete: 0. Edges: declares: 0; contains: 3; imports: 0; calls: 0; uses: 0.

| Id | Name | Provenance | Kind | Status | Paths | Files | Gaps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `orders` | orders | build | workspace-member | confirmed | `benchmarks/scope-resolution/app/packages/orders` | 9 | 0 |
| `orders-demo` | orders-demo | build | uv-workspace | confirmed | `benchmarks/scope-resolution/app` | 1 | 0 |
| `payments` | payments | build | workspace-member | confirmed | `benchmarks/scope-resolution/app/packages/payments` | 3 | 0 |
| `shipping` | shipping | build | workspace-member | confirmed | `benchmarks/scope-resolution/app/packages/shipping` | 2 | 0 |

## `orders`

- Name: orders; build, workspace-member, internal, confirmed
- Paths: `benchmarks/scope-resolution/app/packages/orders`; 9 files
- Evidence: `benchmarks/scope-resolution/app/pyproject.toml:7`
- contains (confirmed): `orders-demo` -> `orders`, evidence 1

## `orders-demo`

- Name: orders-demo; aliases: app; build, uv-workspace, internal, confirmed
- Mini-app dimostrativa per il benchmark di scope resolution (solo stdlib).
- Paths: `benchmarks/scope-resolution/app`; excluded: `benchmarks/scope-resolution/app/packages/orders`, `benchmarks/scope-resolution/app/packages/payments`, `benchmarks/scope-resolution/app/packages/shipping`; 1 files
- Evidence: `benchmarks/scope-resolution/app/pyproject.toml:2`
- contains (confirmed): `orders-demo` -> `orders`, evidence 1
- contains (confirmed): `orders-demo` -> `payments`, evidence 1
- contains (confirmed): `orders-demo` -> `shipping`, evidence 1

## `payments`

- Name: payments; build, workspace-member, internal, confirmed
- Paths: `benchmarks/scope-resolution/app/packages/payments`; 3 files
- Evidence: `benchmarks/scope-resolution/app/pyproject.toml:7`
- contains (confirmed): `orders-demo` -> `payments`, evidence 1

## `shipping`

- Name: shipping; build, workspace-member, internal, confirmed
- Paths: `benchmarks/scope-resolution/app/packages/shipping`; 2 files
- Evidence: `benchmarks/scope-resolution/app/pyproject.toml:7`
- contains (confirmed): `orders-demo` -> `shipping`, evidence 1

## Gaps

- none

## Changes

- added: `orders`, `orders-demo`, `payments`, `shipping`
- removed: none
- changed: none
- unchanged: none

## Notes

- Build units come from manifests only; declared modules from codebase-modules.json; proposed modules from the ledger beside the snapshot and stay inferred until declared. No Markdown is interpreted here.
- Static edges prove no runtime behavior; a missing call edge proves no independence (lexical resolver).
