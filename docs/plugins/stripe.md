# Stripe Plugin

> Integrate Stripe without reading 500 pages of docs. Covers payments, subscriptions, Connect marketplaces, billing, webhooks, and revenue optimization with ready-to-use patterns.

Command examples and named tools in this guide use Claude notation. For other
hosts, use the entry points and bindings in the source-derived reference below
and [host setup](../hosts.md).

## Agents

### `stripe-integrator`

Complete Stripe API integrator covering payments, subscriptions, Connect marketplaces, billing, webhooks, and compliance.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Payment processing, subscriptions, marketplaces, billing, webhooks, SCA/3DS compliance, fraud prevention, dispute handling |

**Invocation:**
```
Use the stripe-integrator agent to [integrate/audit/extend] [Stripe feature]
```

**Core capabilities:**
- **Payments**: Payment intents, checkout sessions, payment links
- **Subscriptions**: Recurring billing, metered usage, tiered pricing
- **Connect**: Marketplace payments, platform fees, seller onboarding
- **Billing**: Invoices, customer portal, tax calculation
- **Webhooks**: Signature-verified event handling, subscription lifecycle, idempotency
- **Security**: 3D Secure, SCA compliance, fraud prevention (Radar)
- **Disputes**: Chargeback handling, evidence submission

**Quick reference:**
| Task | Method |
|------|--------|
| Create customer | `stripe.Customer.create()` |
| Checkout session | `stripe.checkout.Session.create()` |
| Subscription | `stripe.Subscription.create()` |
| Payment link | `stripe.PaymentLink.create()` |
| Report usage | `stripe.billing.MeterEvent.create()` (the legacy usage-record API was removed in `2025-03-31.basil`) |
| Connect account | `stripe.Account.create(type="express")` |

**Prerequisites:**
```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
pip install stripe
```

---

### `revenue-optimizer`

Monetization expert. Analyzes your codebase to discover features, calculate service costs, model usage patterns, and create data-driven pricing strategies with revenue projections.

| | |
|---|---|
| **Model** | `inherit` |
| **Use for** | Feature cost analysis, pricing strategy, usage modeling, revenue projections, tier design |

**Invocation:**
```
Use the revenue-optimizer agent to [analyze/design/project] [pricing|tiers|revenue]
```

**5-Phase Workflow:**
1. **Discover**: Scan codebase for features, services, and integrations
2. **Cost Analysis**: Calculate per-user and per-feature costs
3. **Design**: Create pricing tiers based on value + cost data
4. **Implement**: Build payment integration and checkout flows
5. **Optimize**: Add conversion optimization and revenue tracking

**Key Metrics Calculated:**
| Metric | Formula |
|--------|---------|
| ARPU | (Free x $0 + Pro x $X + Biz x $Y) / Total Users |
| LTV | (ARPU x Margin) / Monthly Churn |
| Break-even | Fixed Costs / (ARPU - Variable Cost) |
| Optimal Price | (Cost Floor x 0.3) + (Value Ceiling x 0.7) |

---

### `stripe-webhooks-auditor`

Adversarial auditor for Stripe webhook integrations. Given a Stripe account plus a codebase, hunts for missing event coverage, signature verification pitfalls, missing idempotency, wrong runtime configuration, and stale endpoints. Report-only; never modifies code or Stripe state.

| | |
|---|---|
| **Model** | `inherit` |
| **Tools** | Read, Bash, Glob, Grep, WebFetch |
| **Use for** | Auditing an existing Stripe webhook setup, preparing for a production launch, after a webhook-related incident, or when adding Billing Meters / Entitlements and the event list needs to grow |

**Invocation:**
```
Use the stripe-webhooks-auditor agent to audit webhook setup
```
Also runnable as `/stripe:audit-webhooks` (see Commands below).

**Three surfaces to check:**
1. **Stripe account state**: configured endpoints, subscribed events, disabled endpoints, per-endpoint API version (via `webhook_audit.py`)
2. **Codebase implementation**: signature verification, raw body preservation, idempotency via `event.id`, runtime config, handler coverage
3. **Gap analysis**: required events per declared feature, against the events enabled on Stripe and the events the code actually handles

Pass criteria come from the canonical checklist in `skills/stripe/references/webhooks-production.md`.

**Inputs:**
- `STRIPE_SECRET_KEY` or `STRIPE_RESTRICTED_KEY` (read-only scope is enough)
- Optional `--account <acct_id>` for Connect platforms
- Optional `--features <flags>` (e.g. `meters,entitlements,connect,trials`); inferred from codebase if omitted

---

## Skills

### `stripe`

Stripe knowledge base: API patterns, checkout optimization, subscription lifecycle, pricing strategies, webhook reliability, Firebase integration, cost analysis, revenue modeling. Loaded by `stripe-integrator` and `revenue-optimizer`; also usable standalone when you need patterns without agent invocation.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Trigger** | Working with Stripe API (Payment Intents, Customers, Subscriptions, Checkout Sessions, Connect, webhooks, tax, usage-based billing), pricing strategy, or revenue modeling |

**References** (under `skills/stripe/references/`):
| File | Content |
|------|---------|
| `stripe.md` | Core concepts, current API version notes, pin patterns |
| `api-cheatsheet.md` | Quick API reference |
| `stripe-patterns.md` | Metered billing, Connect, tax, 3DS, Radar, disputes, idempotency |
| `checkout-optimization.md` | Conversion optimization patterns |
| `embedded-checkout.md` | Embedded Checkout integration patterns |
| `subscription-patterns.md` | Subscription lifecycle + state reconciliation |
| `pricing-patterns.md` | Tier design, pricing strategy |
| `cost-analysis.md` | Unit economics |
| `usage-revenue-modeling.md` | Usage-based revenue models |
| `billing-meters.md` | Billing Meters product setup and event ingestion |
| `entitlements.md` | Entitlements product, feature flag mapping, customer access |
| `webhooks-production.md` | Production webhook hardening checklist |
| `test-clocks.md` | Test clock workflows for subscription scenario testing |
| `typescript-nextjs.md` | TypeScript / Next.js integration patterns |
| `stripe-agent-toolkit.md` | Stripe Agent Toolkit usage for LLM-driven flows |
| `pci-dss-4-checklist.md` | PCI DSS 4.0 compliance reference |
| `firebase-integration.md` | Firebase + Firestore integration |

**Scripts** (`skills/stripe/scripts/`, reference via `${CLAUDE_PLUGIN_ROOT}/skills/stripe/scripts/`):
- `setup_products.py` - bootstrap Products and Prices
- `webhook_handler.py` - signature-verified receiver with idempotency
- `webhook_audit.py` - enumerate Stripe-side webhook endpoints and event coverage for `/stripe:audit-webhooks`
- `sync_subscriptions.py` - reconcile local DB vs Stripe subscription state
- `simulate_subscription.py` - drive a subscription through test clock scenarios
- `stripe_utils.py` - shared utilities

**Key section:** webhook reliability checklist (signature verification, raw body preservation, idempotency via `event.id`, 10-second 2xx response, replay testing).

---

## Commands

### `/stripe:audit-webhooks`

Runs the `stripe-webhooks-auditor` agent against the current project. Enumerates Stripe-side state via `scripts/webhook_audit.py` (reads `STRIPE_SECRET_KEY`), greps the codebase for webhook handlers, verifies each against the pass criteria in `webhooks-production.md`, and produces a prioritized remediation report. Report-only.

```
/stripe:audit-webhooks --features meters,entitlements,trials
/stripe:audit-webhooks --account acct_xxx
```

**When to invoke:**
- Before a production launch
- After adding Billing Meters or Entitlements (event list grows)
- Quarterly webhook hygiene
- During PR review of a webhook route
- After a webhook-related incident

**Prerequisites:** `STRIPE_SECRET_KEY` (or a read-only Restricted API Key) in env; Python with `stripe` installed.

---

**Related:** [python-development](python-development.md) (Python implementation patterns) | [business](business.md) (legal and compliance for payment flows)

<!-- daodan:reference:start -->
## Source-derived reference

Generated by `python scripts/sync_plugin_docs.py`. Edit the kernel and regenerate
this block; keep explanations above it. `--check` detects stale references.

**Version:** `2.6.1`. **Source:** [plugin.toml](<../../plugins/stripe/plugin.toml>).

### Required dependencies

Every listed plugin dependency is mandatory. Transitive requirements remain
mandatory when using this plugin alone. The local closure includes this plugin.

| Requirement | Plugins |
|---|---|
| Direct local | None |
| Direct external | None |
| Local closure (1) | [stripe](<stripe.md>) |
| External closure (0) | None |

External bundles are separate upstream installations, not copied local skills.
See [host setup](<../hosts.md>) for selection and availability requirements.

**Required capabilities:** `repository.read`, `shell.execute`, `repository.write`, `network.fetch`, `contexts.isolate`, `roles.dispatch`.
**Optional capabilities:** None.
Optional capabilities are host mechanisms, not optional local plugin dependencies.

### Registered components

Names below are kernel IDs. Host entry points and paths follow the adapter
mapping in [the host reference](<../hosts.md>).
The source links carry the complete instructions and accepted arguments.

| Kind | ID | Purpose and trigger | Source |
|---|---|---|---|
| Skill | `stripe:stripe` | Knowledge base loaded by the stripe-integrator and revenue-optimizer agents, also consumable directly. TRIGGER WHEN: working with the Stripe API (Payment Intents, Customers, Subscriptions, Checkout Sessions, Connect, webhooks, tax, usage-based billing), Firebase integration, pricing strategy, or revenue modeling. | [stripe](<../../plugins/stripe/skills/stripe/SKILL.md>) |
| Role | `stripe:revenue-optimizer` | Turns a codebase's real service costs into a defensible price. TRIGGER WHEN: modeling pricing tiers, calculating unit economics, setting quota or usage limits from consumption percentiles, designing monetization strategy, or projecting revenue, ARPU, LTV or break-even. DO NOT TRIGGER WHEN: implementing Stripe plumbing only (use stripe-integrator), or doing general business strategy not tied to pricing (use business-planner). | [revenue-optimizer](<../../plugins/stripe/roles/revenue-optimizer.md>) |
| Role | `stripe:stripe-integrator` | Hands-on implementer that writes the integration code rather than auditing it. TRIGGER WHEN: working with the Stripe API for customers, subscriptions, payments, checkout sessions, invoices, payment intents, products and prices, webhooks, Connect marketplaces, metered billing, tax, SCA or 3D Secure, fraud prevention, or disputes. | [stripe-integrator](<../../plugins/stripe/roles/stripe-integrator.md>) |
| Role | `stripe:stripe-webhooks-auditor` | Cross-checks what the dashboard says against what the code actually handles. TRIGGER WHEN: auditing a Stripe webhook setup before launch or after an incident, hunting missing event coverage, signature verification pitfalls, missing idempotency or stale endpoints, or growing the event list for Billing Meters and Entitlements. DO NOT TRIGGER WHEN: implementing webhooks from scratch (use stripe-integrator), or general code review (use senior-review:code-auditor). | [stripe-webhooks-auditor](<../../plugins/stripe/roles/stripe-webhooks-auditor.md>) |
| Workflow | `stripe:audit-webhooks` | Runs the stripe-webhooks-auditor agent over the current project. TRIGGER WHEN: the user asks to audit or verify a Stripe webhook setup: endpoint configuration, signature verification, idempotency or event coverage. | [audit-webhooks](<../../plugins/stripe/workflows/audit-webhooks.md>) |

### Workflow contracts

Contracts describe observable outputs; Markdown bodies define decisions,
flags, safety gates and execution. Declared `invoke` execution is unsupported.

#### `stripe:audit-webhooks`

**Arguments:** `[--features trials,entitlements,meters,connect] [--account acct_xxx]`

| Contract | Value |
|---|---|
| Inputs | `repository` |
| Outcomes | `audit-webhooks-completed` |
| Artifacts | `audit-webhooks-report` |
| Schemas | None declared |
| Declared workers | `stripe/stripe-webhooks-auditor` |
| Composed worker isolation | See phase isolation below |
| Task-specific isolated workers | Not declared |
| Sidecar | [audit-webhooks.toml](<../../plugins/stripe/workflows/audit-webhooks.toml>) |

| Phase | Needs | Dispatch | Isolation | Join | Concurrency |
|---|---|---|---|---|---|
| `scope` | None | None | `shared` | None declared | `preferred` |
| `audit` | `scope` | `stripe-webhooks-auditor` | `required` | None declared | `preferred` |

### Host exports

Package paths and coordination are derived from the host adapters. `native`
and `adapted` describe bindings, not successful installed-host execution.

The selected strategy is an adapter binding even for a flat workflow body.
A dispatch harness is rendered only for declared method workers, task-specific
workers or phase fan-out; the host reference explains the entry artifacts.

| Host | Package | Binding | Selected workflow strategy |
|---|---|---|---|
| claude | [exports/claude/plugins/stripe](<../../exports/claude/plugins/stripe>) | `native` | `audit-webhooks: native-team` |
| copilot | [exports/copilot/plugins/stripe](<../../exports/copilot/plugins/stripe>) | `native` | `audit-webhooks: parallel-subagents` |
| codex | [exports/codex/plugins/stripe](<../../exports/codex/plugins/stripe>) | `adapted` | `audit-webhooks: parallel-subagents` |
| pi | [exports/pi/plugins/stripe](<../../exports/pi/plugins/stripe>) | `adapted` | `audit-webhooks: parallel-subagents` |
| opencode | [exports/opencode/plugins/stripe](<../../exports/opencode/plugins/stripe>) | `native` | `audit-webhooks: parallel-subagents` |

<!-- daodan:reference:end -->
