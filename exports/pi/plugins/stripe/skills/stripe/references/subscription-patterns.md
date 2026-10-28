<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
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
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
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

# Subscription System Patterns

## Database Schema

```sql
-- Users table (add these columns)
ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);

-- Subscriptions table
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) NOT NULL,
  stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
  stripe_customer_id VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL, -- active, canceled, past_due, trialing, paused
  price_id VARCHAR(255) NOT NULL,
  current_period_start TIMESTAMP NOT NULL,
  current_period_end TIMESTAMP NOT NULL,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  canceled_at TIMESTAMP,
  trial_end TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

## Prisma Schema

```prisma
model Subscription {
  id                   String   @id @default(cuid())
  userId               String   @unique
  user                 User     @relation(fields: [userId], references: [id])
  stripeSubscriptionId String   @unique
  stripeCustomerId     String
  status               String   // active, canceled, past_due, trialing
  priceId              String
  currentPeriodStart   DateTime
  currentPeriodEnd     DateTime
  cancelAtPeriodEnd    Boolean  @default(false)
  canceledAt           DateTime?
  trialEnd             DateTime?
  createdAt            DateTime @default(now())
  updatedAt            DateTime @updatedAt
}
```

## Subscription State Machine

```
                    ┌──────────────┐
                    │   trialing   │
                    └──────┬───────┘
                           │ trial ends + payment succeeds
                           ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   canceled   │◄───│    active    │───►│   past_due   │
└──────────────┘    └──────────────┘    └──────┬───────┘
       ▲                   ▲                    │
       │                   │ payment succeeds   │ payment fails 3x
       │                   └────────────────────┤
       └────────────────────────────────────────┘
```

## Subscription Service

```typescript
// lib/subscription.ts
export class SubscriptionService {
  async getSubscription(userId: string) {
    return db.subscription.findFirst({
      where: { userId, status: { in: ['active', 'trialing'] } },
    });
  }

  async isActive(userId: string): Promise<boolean> {
    const sub = await this.getSubscription(userId);
    return !!sub && ['active', 'trialing'].includes(sub.status);
  }

  async getPlan(userId: string) {
    const sub = await this.getSubscription(userId);
    if (!sub) return PLANS.free;
    return PLANS[this.getPlanIdFromPriceId(sub.priceId)];
  }

  async hasFeature(userId: string, feature: string): Promise<boolean> {
    const plan = await this.getPlan(userId);
    return plan.features.includes(feature);
  }

  async checkLimit(userId: string, resource: string, current: number): Promise<boolean> {
    const plan = await this.getPlan(userId);
    return current < (plan.limits[resource] ?? Infinity);
  }
}
```

## Webhook Idempotency

```typescript
// Prevent duplicate processing
async function handleWebhook(event: Stripe.Event) {
  const processed = await db.webhookEvent.findUnique({
    where: { stripeEventId: event.id },
  });
  
  if (processed) {
    console.log(`Event ${event.id} already processed`);
    return;
  }

  await db.$transaction(async (tx) => {
    // Record that we're processing this event
    await tx.webhookEvent.create({
      data: { stripeEventId: event.id, type: event.type },
    });
    
    // Process the event
    await processEvent(event, tx);
  });
}
```

## Trial Implementation

```typescript
// Create subscription with trial
const session = await stripe.checkout.sessions.create({
  mode: 'subscription',
  subscription_data: {
    trial_period_days: 14,
  },
  // ... other options
});

// Check trial status
function getTrialStatus(subscription: Subscription) {
  if (subscription.status !== 'trialing') return null;
  
  const daysLeft = Math.ceil(
    (subscription.trialEnd.getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );
  
  return { isTrialing: true, daysLeft, endsAt: subscription.trialEnd };
}
```

## Upgrade/Downgrade Handling

```typescript
async function changePlan(userId: string, newPriceId: string) {
  const sub = await getSubscription(userId);
  
  const updated = await stripe.subscriptions.update(sub.stripeSubscriptionId, {
    items: [{
      id: sub.items.data[0].id,
      price: newPriceId,
    }],
    proration_behavior: 'create_prorations', // or 'none', 'always_invoice'
  });
  
  await syncSubscription(updated);
  return updated;
}
```

## Cancellation Flow

```typescript
// Cancel at period end (recommended)
async function cancelSubscription(userId: string) {
  const sub = await getSubscription(userId);
  
  await stripe.subscriptions.update(sub.stripeSubscriptionId, {
    cancel_at_period_end: true,
  });
  
  // Optionally collect feedback
  await db.cancellationFeedback.create({
    data: { userId, reason: 'too_expensive' }, // from user input
  });
}

// Reactivate before period ends
async function reactivateSubscription(userId: string) {
  const sub = await getSubscription(userId);
  
  await stripe.subscriptions.update(sub.stripeSubscriptionId, {
    cancel_at_period_end: false,
  });
}
```

## Dunning (Failed Payment Recovery)

```typescript
// Handle failed payments
async function handlePaymentFailed(invoice: Stripe.Invoice) {
  const customerId = invoice.customer as string;
  const user = await getUserByCustomerId(customerId);
  
  const attemptCount = invoice.attempt_count;
  
  if (attemptCount === 1) {
    await sendEmail(user.email, 'payment-failed-soft', {
      updatePaymentUrl: await getUpdatePaymentUrl(customerId),
    });
  } else if (attemptCount === 2) {
    await sendEmail(user.email, 'payment-failed-warning', {
      updatePaymentUrl: await getUpdatePaymentUrl(customerId),
      daysUntilCancellation: 7,
    });
  } else if (attemptCount >= 3) {
    await sendEmail(user.email, 'subscription-canceled', {
      reactivateUrl: `${APP_URL}/pricing`,
    });
  }
}

async function getUpdatePaymentUrl(customerId: string) {
  const session = await stripe.billingPortal.sessions.create({
    customer: customerId,
    return_url: `${APP_URL}/settings/billing`,
  });
  return session.url;
}
```

## Grace Period Access

```typescript
// Allow limited access during past_due
async function checkAccess(userId: string, feature: string): Promise<boolean> {
  const sub = await getSubscription(userId);
  
  if (!sub) return PLANS.free.features.includes(feature);
  
  if (sub.status === 'active' || sub.status === 'trialing') {
    return PLANS[sub.planId].features.includes(feature);
  }
  
  // Grace period: 7 days after going past_due
  if (sub.status === 'past_due') {
    const daysPastDue = Math.floor(
      (Date.now() - sub.currentPeriodEnd.getTime()) / (1000 * 60 * 60 * 24)
    );
    if (daysPastDue <= 7) {
      return PLANS[sub.planId].features.includes(feature);
    }
  }
  
  return false;
}
```
