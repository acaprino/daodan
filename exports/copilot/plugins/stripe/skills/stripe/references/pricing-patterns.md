<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
agent dispatch uses the agent allowlist alias; the current CLI documents a task
dispatch tool. Call the mechanism actually registered in this session, not an
allowlist alias assumed to be a callable tool.
Use each registered tool's input fields; Claude's subagent_type, role and
run_in_background fields are not a portable dispatch schema. Dispatch only the
custom agent named by the generated owner-qualified binding and agents allowlist.
An omitted tools restriction retains host defaults; an explicit list constrains
the worker and does not grant omitted shell, write or MCP tools.
Skills use their exact installed registry identity; workflows are prompt entries.
A dispatched workflow also has its generated <workflow>-coordinator custom agent.
Required foreign providers use Copilot's marketplace/install commands:
copilot plugin marketplace add <source>, then copilot plugin install <provider>@<marketplace>.
Register plugin-declared MCP server commands in this host's MCP configuration as
the generated note directs. Registration and a dependency declaration alone do
not demonstrate that browser/server tools are callable by the selected worker.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Coordinator MCP allowances use <declared-server>/* for only the package's named
servers. This requires actual server registration and tool discovery; it grants
no undeclared server and does not prove MCP is callable in an installed run.
Schema reference: https://docs.github.com/en/copilot/reference/custom-agents-configuration

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

# Pricing Tier Patterns

## Good-Better-Best (3-Tier)

Most effective for SaaS. Anchor users to middle tier.

```typescript
const PLANS = {
  starter: {
    id: 'starter',
    name: 'Starter',
    price: { monthly: 9, yearly: 90 },
    features: ['5 projects', '1 user', 'Basic support', '1GB storage'],
    limits: { projects: 5, users: 1, storage: 1_000_000_000 },
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    price: { monthly: 29, yearly: 290 },
    features: ['Unlimited projects', '5 users', 'Priority support', '10GB storage', 'Advanced analytics'],
    limits: { projects: Infinity, users: 5, storage: 10_000_000_000 },
    recommended: true, // Highlight this tier
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    price: { monthly: 99, yearly: 990 },
    features: ['Everything in Pro', 'Unlimited users', 'SSO/SAML', 'Custom integrations', 'Dedicated support'],
    limits: { projects: Infinity, users: Infinity, storage: 100_000_000_000 },
  },
};
```

## Freemium Model

```typescript
const PLANS = {
  free: {
    id: 'free',
    name: 'Free',
    price: { monthly: 0, yearly: 0 },
    features: ['3 projects', 'Basic features', 'Community support'],
    limits: { projects: 3, apiCalls: 100 },
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    price: { monthly: 19, yearly: 190 },
    features: ['Unlimited projects', 'All features', 'Email support'],
    limits: { projects: Infinity, apiCalls: 10000 },
  },
};
```

## Usage-Based / Metered

```typescript
const PLANS = {
  payAsYouGo: {
    id: 'pay_as_you_go',
    name: 'Pay As You Go',
    basePrice: 0,
    usage: [
      { metric: 'api_calls', price: 0.001, unit: 'per call' },
      { metric: 'storage', price: 0.02, unit: 'per GB/month' },
    ],
  },
  business: {
    id: 'business',
    name: 'Business',
    basePrice: 99,
    included: { api_calls: 50000, storage: 50 },
    overage: [
      { metric: 'api_calls', price: 0.0005, unit: 'per call' },
      { metric: 'storage', price: 0.01, unit: 'per GB/month' },
    ],
  },
};
```

## Per-Seat Pricing

```typescript
const PLAN = {
  id: 'team',
  name: 'Team',
  pricePerSeat: { monthly: 12, yearly: 120 },
  minimumSeats: 3,
  features: ['All features', 'Team collaboration', 'Admin controls'],
};

function calculatePrice(seats: number, interval: 'monthly' | 'yearly') {
  const effectiveSeats = Math.max(seats, PLAN.minimumSeats);
  return effectiveSeats * PLAN.pricePerSeat[interval];
}
```

## Hybrid: Base + Seats + Usage

```typescript
const PLAN = {
  basePrice: { monthly: 49, yearly: 490 },
  includedSeats: 5,
  additionalSeatPrice: { monthly: 10, yearly: 100 },
  usage: {
    apiCalls: { included: 10000, overagePrice: 0.001 },
  },
};
```

## Entitlement Check Implementation

```typescript
// types/plans.ts
interface PlanLimits {
  projects: number;
  users: number;
  storage: number;
  features: string[];
}

// lib/entitlements.ts
export async function canAccessFeature(userId: string, feature: string): Promise<boolean> {
  const sub = await getSubscription(userId);
  if (!sub || sub.status !== 'active') return false;
  return PLANS[sub.planId].features.includes(feature);
}

export async function checkLimit(userId: string, resource: string, current: number): Promise<boolean> {
  const sub = await getSubscription(userId);
  const plan = sub ? PLANS[sub.planId] : PLANS.free;
  return current < plan.limits[resource];
}

// Usage
if (!await canAccessFeature(user.id, 'advanced_analytics')) {
  throw new UpgradeRequiredError('advanced_analytics');
}
```

## Feature Matrix Display

```tsx
function PricingTable() {
  const features = [
    { name: 'Projects', starter: '5', pro: 'Unlimited', enterprise: 'Unlimited' },
    { name: 'Team members', starter: '1', pro: '5', enterprise: 'Unlimited' },
    { name: 'Storage', starter: '1 GB', pro: '10 GB', enterprise: '100 GB' },
    { name: 'API access', starter: false, pro: true, enterprise: true },
    { name: 'SSO/SAML', starter: false, pro: false, enterprise: true },
    { name: 'Support', starter: 'Community', pro: 'Priority', enterprise: 'Dedicated' },
  ];
  
  return (
    <table>
      <thead>
        <tr>
          <th>Feature</th>
          {Object.keys(PLANS).map(plan => <th key={plan}>{PLANS[plan].name}</th>)}
        </tr>
      </thead>
      <tbody>
        {features.map(f => (
          <tr key={f.name}>
            <td>{f.name}</td>
            <td>{renderValue(f.starter)}</td>
            <td>{renderValue(f.pro)}</td>
            <td>{renderValue(f.enterprise)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

## Pricing Psychology Tips

- **Anchor high**: Show enterprise first or highlight middle tier
- **Annual discount**: 15-20% off encourages commitment
- **Round numbers**: $29 feels simpler than $29.99 for B2B
- **Limit free tier**: Enough to hook, not enough to satisfy
- **Feature differentiation**: Each tier should have 1-2 "hero" features
