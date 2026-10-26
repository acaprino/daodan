<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network tools are webfetch/websearch, and clarification
uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
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

# Stripe Integration Patterns

## Setup

```bash
npm install stripe @stripe/stripe-js
```

Environment variables:
```
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Server-Side Setup

```typescript
// lib/stripe.ts
import Stripe from 'stripe';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2026-05-27.dahlia',  // pin to a current dated version; check https://stripe.com/docs/upgrades for latest
});
```

## Checkout Session (One-Time or Subscription)

```typescript
// api/checkout/route.ts
export async function POST(req: Request) {
  const { priceId, userId, mode = 'subscription' } = await req.json();
  
  const session = await stripe.checkout.sessions.create({
    mode, // 'subscription' or 'payment'
    payment_method_types: ['card'],
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${process.env.APP_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${process.env.APP_URL}/pricing`,
    client_reference_id: userId,
    customer_email: user.email, // Pre-fill if known
    allow_promotion_codes: true,
    billing_address_collection: 'auto',
    metadata: { userId },
  });
  
  return Response.json({ url: session.url });
}
```

## Webhook Handler

```typescript
// api/webhooks/stripe/route.ts
export async function POST(req: Request) {
  const body = await req.text();
  const sig = req.headers.get('stripe-signature')!;
  
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err) {
    return new Response('Webhook signature verification failed', { status: 400 });
  }

  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutComplete(session);
      break;
    }
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;
      await syncSubscription(subscription);
      break;
    }
    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      await handlePaymentFailed(invoice);
      break;
    }
  }
  
  return new Response('OK');
}
```

## Subscription Sync

```typescript
async function syncSubscription(subscription: Stripe.Subscription) {
  const customerId = subscription.customer as string;
  const user = await db.user.findFirst({ where: { stripeCustomerId: customerId } });
  
  await db.subscription.upsert({
    where: { stripeSubscriptionId: subscription.id },
    update: {
      status: subscription.status,
      priceId: subscription.items.data[0].price.id,
      currentPeriodEnd: new Date(subscription.current_period_end * 1000),
      cancelAtPeriodEnd: subscription.cancel_at_period_end,
    },
    create: {
      userId: user.id,
      stripeSubscriptionId: subscription.id,
      stripeCustomerId: customerId,
      status: subscription.status,
      priceId: subscription.items.data[0].price.id,
      currentPeriodEnd: new Date(subscription.current_period_end * 1000),
    },
  });
}
```

## Customer Portal

```typescript
// api/billing/portal/route.ts
export async function POST(req: Request) {
  const user = await getCurrentUser();
  
  const session = await stripe.billingPortal.sessions.create({
    customer: user.stripeCustomerId,
    return_url: `${process.env.APP_URL}/settings/billing`,
  });
  
  return Response.json({ url: session.url });
}
```

## Usage-Based Billing

The legacy `createUsageRecord` API was **removed in Stripe API version `2025-03-31.basil`**. Use Billing Meters instead:

```typescript
await stripe.billing.meterEvents.create({
  event_name: 'api_request',
  payload: { stripe_customer_id: 'cus_xxx', value: String(apiCallCount) },
  identifier: requestId,  // idempotency
  timestamp: Math.floor(Date.now() / 1000),
});
```

See `billing-meters.md` for the full model, tiered pricing, bulk event streams, backfill, and migration recipe.

## Price Configuration (Dashboard or API)

```typescript
// Create products and prices programmatically
const product = await stripe.products.create({
  name: 'Pro Plan',
  description: 'Full access to all features',
});

const monthlyPrice = await stripe.prices.create({
  product: product.id,
  unit_amount: 2900, // $29.00
  currency: 'usd',
  recurring: { interval: 'month' },
  lookup_key: 'pro_monthly', // Use for easy lookup
});

const yearlyPrice = await stripe.prices.create({
  product: product.id,
  unit_amount: 29000, // $290.00 (save ~17%)
  currency: 'usd',
  recurring: { interval: 'year' },
  lookup_key: 'pro_yearly',
});
```

## Client-Side (React)

```tsx
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

function PricingButton({ priceId }: { priceId: string }) {
  const handleClick = async () => {
    const res = await fetch('/api/checkout', {
      method: 'POST',
      body: JSON.stringify({ priceId }),
    });
    const { url } = await res.json();
    window.location.href = url;
  };
  
  return <button onClick={handleClick}>Subscribe</button>;
}
```

## Essential Webhooks to Handle

| Event | Action |
|-------|--------|
| `checkout.session.completed` | Create subscription record, grant access |
| `customer.subscription.updated` | Sync plan changes, handle upgrades/downgrades |
| `customer.subscription.deleted` | Revoke access, send win-back email |
| `invoice.payment_succeeded` | Update billing status, send receipt |
| `invoice.payment_failed` | Mark past_due, send dunning email |
| `customer.subscription.trial_will_end` | Send trial ending reminder (3 days before) |
