<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

# Stripe Integration Patterns - Detailed Examples

## Metered and Usage-Based Billing

**See `billing-meters.md`.** The legacy `usage_type=metered` price + `SubscriptionItem.create_usage_record` flow shown previously here was **removed in Stripe API version `2025-03-31.basil`**. New code must use the Billing Meters API (`stripe.billing.Meter` + `stripe.billing.MeterEvent`).

If you are still pinned to `2025-02-24.acacia` or earlier, your existing integration keeps working, but all new metered prices must be meter-backed. See `billing-meters.md` for a full migration recipe.

## Stripe Connect (Marketplaces)

Build platforms where you facilitate payments between buyers and sellers:

```python
# Create connected account (Express - recommended)
account = stripe.Account.create(
    type="express",
    country="US",
    email="seller@example.com",
    capabilities={"card_payments": {"requested": True}, "transfers": {"requested": True}}
)

# Generate onboarding link
account_link = stripe.AccountLink.create(
    account=account.id,
    refresh_url="https://yourapp.com/reauth",
    return_url="https://yourapp.com/return",
    type="account_onboarding"
)
# Redirect seller to: account_link.url

# Create payment with platform fee (destination charge)
payment_intent = stripe.PaymentIntent.create(
    amount=10000,
    currency="eur",
    application_fee_amount=1000,  # Platform takes 10
    transfer_data={"destination": "acct_xxx"}  # Seller receives 90
)

# Direct charge (charge on connected account)
payment_intent = stripe.PaymentIntent.create(
    amount=10000,
    currency="eur",
    stripe_account="acct_xxx",  # Charge on seller's account
    application_fee_amount=1000
)

# Transfer funds to connected account
transfer = stripe.Transfer.create(
    amount=5000,
    currency="eur",
    destination="acct_xxx"
)
```

## Tax Calculation (Stripe Tax)

Automatic tax calculation and collection:

```python
# Enable automatic tax in checkout
session = stripe.checkout.Session.create(
    mode="payment",
    line_items=[{"price": "price_xxx", "quantity": 1}],
    automatic_tax={"enabled": True},
    success_url="https://yourapp.com/success",
    cancel_url="https://yourapp.com/cancel"
)

# Tax calculation API (preview)
calculation = stripe.tax.Calculation.create(
    currency="eur",
    line_items=[{"amount": 1000, "reference": "L1"}],
    customer_details={"address": {"country": "DE"}, "address_source": "billing"}
)
```

## 3D Secure and SCA Compliance

Handle Strong Customer Authentication (required in EU/UK):

```python
# Payment intent with 3DS when required
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    payment_method="pm_xxx",
    confirmation_method="manual",
    confirm=True,
    return_url="https://yourapp.com/return"  # For 3DS redirect
)

# Check if authentication required
if payment_intent.status == "requires_action":
    # Redirect customer to: payment_intent.next_action.redirect_to_url.url
    pass

# Force 3DS (for high-risk transactions)
payment_intent = stripe.PaymentIntent.create(
    amount=50000,
    currency="eur",
    payment_method_options={
        "card": {"request_three_d_secure": "any"}  # or "automatic"
    }
)

# Webhook: handle authentication
# Event: payment_intent.requires_action
```

**Test cards for 3DS:**
- `4000002500003155` - Requires authentication
- `4000002760003184` - Always authenticates
- `4000008260003178` - Authentication fails

## Fraud Prevention (Stripe Radar)

Built-in fraud protection with Radar:

```python
# Payment with Radar rules
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    payment_method="pm_xxx",
    # Radar evaluates automatically
)

# Check radar outcome after payment
charge = stripe.Charge.retrieve("ch_xxx")
radar_outcome = charge.outcome
# radar_outcome.risk_level: "normal", "elevated", "highest"
# radar_outcome.risk_score: 0-100

# Custom metadata for Radar rules
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    metadata={
        "customer_account_age": "30",  # days
        "order_count": "5"
    }
)

# Block high-risk in Radar Dashboard:
# Rule: "Block if :risk_level: = 'highest'"
# Rule: "Review if ::customer_account_age:: < 7"
```

## Dispute Handling

Manage chargebacks and disputes:

```python
# List disputes
disputes = stripe.Dispute.list(limit=10)

# Retrieve dispute details
dispute = stripe.Dispute.retrieve("dp_xxx")
# dispute.reason: "fraudulent", "duplicate", "product_not_received", etc.
# dispute.status: "needs_response", "under_review", "won", "lost"

# Submit evidence
stripe.Dispute.modify(
    "dp_xxx",
    evidence={
        "customer_name": "John Doe",
        "customer_email_address": "john@example.com",
        "shipping_tracking_number": "1Z999AA10123456784",
        "uncategorized_text": "Customer confirmed receipt via email on..."
    },
    submit=True  # Submit evidence
)

# Webhook events for disputes
# charge.dispute.created - New dispute opened
# charge.dispute.updated - Evidence submitted or status changed
# charge.dispute.closed - Dispute resolved
```

## Idempotency and Best Practices

Prevent duplicate operations:

```python
import uuid

# Idempotent request (safe to retry)
payment_intent = stripe.PaymentIntent.create(
    amount=2000,
    currency="eur",
    idempotency_key=f"order_{order_id}"  # Unique per operation
)

# For retries, use same key
try:
    payment = stripe.PaymentIntent.create(
        amount=2000,
        currency="eur",
        idempotency_key="order_123"
    )
except stripe.error.StripeError:
    # Safe to retry with same idempotency_key
    payment = stripe.PaymentIntent.create(
        amount=2000,
        currency="eur",
        idempotency_key="order_123"
    )

# Generate unique keys
def idempotency_key(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"
```

**Best Practices:**
1. Always use idempotency keys for create/update operations
2. Store payment intent ID before confirming
3. Use webhooks as source of truth (not API responses)
4. Handle `requires_action` status for 3DS
5. Never log full card numbers or CVV
6. Use test mode for development (`sk_test_...`)
