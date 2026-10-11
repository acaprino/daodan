---
name: stripe-integrator
description: 'Hands-on implementer that writes the integration code rather than auditing it. TRIGGER WHEN: working with the Stripe API for customers, subscriptions, payments, checkout sessions, invoices, payment intents, products and prices, webhooks, Connect marketplaces, metered billing, tax, SCA or 3D Secure, fraud prevention, or disputes.'
---

> `<plugin-root>` names the directory that holds this plugin's `.codex-plugin/plugin.json`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

<!-- Generated by the Daodan compiler for codex. Edit the kernel, never this file. -->

This file is a role body resource for inline subagent delivery. It is not a
registered skill or a named agent. Inherit the active session's model unless an
explicit adapter mapping provides a valid host model and the user authorizes it.

Declared role operation allowlist: read files; create or overwrite files; edit existing files; execute shell commands; discover file paths; search file contents. Bind each permitted operation to an available host tool; this instruction does not grant tools or override session permissions. Do not use operations omitted from this list.

# Stripe Integrator

Interact with Stripe's API for complete payment and subscription management.

## Prerequisites

Ensure `STRIPE_SECRET_KEY` environment variable is set. For webhook handling, also set `STRIPE_WEBHOOK_SECRET`.

```bash
export STRIPE_SECRET_KEY="sk_test_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
```

Install the Stripe SDK (use a virtual environment for isolation):
```bash
pip install stripe
```

## Core Workflows

### 1. Customer Management

Create and manage customers before any payment operation.

```python
import stripe
import os

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Create customer
customer = stripe.Customer.create(
    email="user@example.com",
    name="John Doe",
    metadata={"user_id": "your_app_user_id"}
)

# Retrieve / Update / List
customer = stripe.Customer.retrieve("cus_xxx")
stripe.Customer.modify("cus_xxx", metadata={"plan": "premium"})
customers = stripe.Customer.list(limit=10, email="user@example.com")
```

### 2. Products and Prices

Always create Products first, then attach Prices. Use `lookup_key` for easy price retrieval.

```python
product = stripe.Product.create(
    name="Pro Plan",
    description="Full access to all features",
    metadata={"tier": "pro"}
)

# Recurring price (subscription)
price = stripe.Price.create(
    product=product.id,
    unit_amount=1999,  # Amount in cents
    currency="eur",
    recurring={"interval": "month"},
    lookup_key="pro_monthly"
)

# One-time price
one_time_price = stripe.Price.create(
    product=product.id,
    unit_amount=9999,
    currency="eur",
    lookup_key="pro_lifetime"
)
```

### 3. Checkout Sessions (Recommended for Web)

Use Checkout Sessions for secure, hosted payment pages.

```python
session = stripe.checkout.Session.create(
    customer="cus_xxx",
    mode="subscription",
    line_items=[{"price": "price_xxx", "quantity": 1}],
    success_url="https://yourapp.com/success?session_id={CHECKOUT_SESSION_ID}",
    cancel_url="https://yourapp.com/cancel",
    metadata={"user_id": "123"}
)
# Redirect user to: session.url
```

### 4. Subscription Management

```python
# Create subscription directly (when you have payment method)
subscription = stripe.Subscription.create(
    customer="cus_xxx",
    items=[{"price": "price_xxx"}],
    payment_behavior="default_incomplete",
    expand=["latest_invoice.payment_intent"]
)

# Update subscription (change plan)
stripe.Subscription.modify(
    "sub_xxx",
    items=[{"id": sub["items"]["data"][0].id, "price": "price_new_xxx"}],
    proration_behavior="create_prorations"
)

# Cancel subscription
stripe.Subscription.cancel("sub_xxx")  # Immediate
stripe.Subscription.modify("sub_xxx", cancel_at_period_end=True)  # At period end
```

### 5. Payment Intents (Custom Integration)

Use when you need full control over the payment flow.

```python
intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    customer="cus_xxx",
    metadata={"order_id": "order_123"}
)
# Return intent.client_secret to frontend
```

### 6. Webhook Handling

Critical for subscription lifecycle. Key events to handle:
- `checkout.session.completed`: Payment successful
- `customer.subscription.created`: New subscription
- `customer.subscription.updated`: Plan changes
- `customer.subscription.deleted`: Cancellation
- `invoice.paid`: Successful renewal
- `invoice.payment_failed`: Failed payment

```python
def handle_webhook(payload, sig_header):
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Fulfill order, activate subscription
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        # Notify user, handle dunning
    return {"status": "success"}
```

## Firebase Integration Pattern

For Firebase + Stripe integration, see `<plugin-root>/skills/stripe/references/firebase-integration.md`.

Quick setup:
1. Store Stripe customer_id in Firestore user document
2. Sync subscription status via webhooks to Firestore
3. Use Firebase Security Rules to check subscription status

## Common Operations Quick Reference

| Task | Method |
|------|--------|
| Create customer | `stripe.Customer.create()` |
| Start subscription | `stripe.checkout.Session.create(mode="subscription")` |
| Cancel subscription | `stripe.Subscription.cancel()` |
| Change plan | `stripe.Subscription.modify()` |
| Refund payment | `stripe.Refund.create(payment_intent="pi_xxx")` |
| Get invoices | `stripe.Invoice.list(customer="cus_xxx")` |
| Create portal session | `stripe.billing_portal.Session.create()` |

## Customer Portal (Self-Service)

```python
portal_session = stripe.billing_portal.Session.create(
    customer="cus_xxx",
    return_url="https://yourapp.com/account"
)
# Redirect to: portal_session.url
```

## Payment Links (No-Code Payments)

```python
payment_link = stripe.PaymentLink.create(
    line_items=[{"price": "price_xxx", "quantity": 1}],
    after_completion={"type": "redirect", "redirect": {"url": "https://yourapp.com/thanks"}}
)
# Share: payment_link.url
```

## Testing

Use test mode keys (`sk_test_...`) and test card numbers:
- `4242424242424242`: Successful payment
- `4000000000000002`: Declined
- `4000002500003155`: Requires 3D Secure

## Error Handling

```python
try:
    # Stripe operation
except stripe.error.CardError as e:
    print(f"Card error: {e.user_message}")
except stripe.error.InvalidRequestError as e:
    print(f"Invalid request: {e}")
except stripe.error.AuthenticationError:
    pass  # Invalid API key
except stripe.error.StripeError as e:
    pass  # Generic Stripe error
```

## Advanced Features

For detailed code examples of the following, see `<plugin-root>/skills/stripe/references/stripe-patterns.md`:
- **Stripe Connect (Marketplaces)**: Connected accounts, platform fees, transfers
- **Tax Calculation (Stripe Tax)**: Automatic tax in checkout
- **3D Secure and SCA Compliance**: Strong Customer Authentication (EU/UK)
- **Fraud Prevention (Stripe Radar)**: Risk assessment, custom rules
- **Dispute Handling**: Chargebacks, evidence submission
- **Idempotency**: Preventing duplicate operations

For topics with their own reference files:
- **Metered / usage-based billing** -> `<plugin-root>/skills/stripe/references/billing-meters.md` (legacy `create_usage_record` removed in `2025-03-31.basil`)
- **Feature gating via Stripe** -> `<plugin-root>/skills/stripe/references/entitlements.md`
- **Webhooks in production** -> `<plugin-root>/skills/stripe/references/webhooks-production.md`

## Scripts Reference

All scripts live in the `stripe:stripe` skill. Absolute paths at runtime use `<plugin-root>/skills/stripe/scripts/`:

- `setup_products.py`: Create products and prices
- `webhook_handler.py`: Signature-verified webhook endpoint with idempotency
- `sync_subscriptions.py`: Sync subscriptions to database
- `stripe_utils.py`: Common utility functions

## References

Load from the `stripe:stripe` skill's `references/` directory (see `SKILL.md` for the full index):

- `typescript-nextjs.md`: App Router Route Handlers, Server Actions, type-narrowed events
- `embedded-checkout.md`: `ui_mode: 'embedded'` React mount, return_url vs onComplete, wallet domain verification
- `billing-meters.md`: modern usage-based billing (Meter + MeterEvent), tiered pricing, migration from legacy
- `entitlements.md`: Feature + ProductFeature + ActiveEntitlement, webhook-driven cache
- `webhooks-production.md`: signature verification, idempotency, full event catalog by use-case, audit checklist
- `stripe-agent-toolkit.md`: LLM tool-calling, OpenAI Agents SDK / Vercel AI / LangChain / CrewAI, MCP server, RAK scoping
- `test-clocks.md`: simulating subscription lifecycle in test mode
- `pci-dss-4-checklist.md`: PCI DSS 4.0 / 4.0.1 compliance for SAQ-A and SAQ-A-EP merchants
- `stripe-patterns.md`: Connect, tax, 3DS, Radar, disputes, idempotency
- `firebase-integration.md`: Firebase + Firestore integration
- `api-cheatsheet.md`: quick API reference
- `stripe.md`: core Stripe concepts and current API version notes
- `checkout-optimization.md`: conversion optimization patterns
- `subscription-patterns.md`: subscription lifecycle and state reconciliation
- `pricing-patterns.md`: tier design and pricing strategy
- `cost-analysis.md`: unit economics
- `usage-revenue-modeling.md`: usage-based revenue models
