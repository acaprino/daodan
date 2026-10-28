<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
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

# Usage Patterns & Revenue Modeling

## Usage Pattern Analysis

### Detecting Usage Patterns from Code

Scan codebase for usage tracking and analytics:

```typescript
// Look for these patterns in code
const USAGE_INDICATORS = {
  // Analytics events
  'track(': 'Event tracking',
  'analytics.': 'Analytics SDK',
  'mixpanel.': 'Mixpanel events',
  'amplitude.': 'Amplitude events',
  'posthog.': 'PostHog events',
  
  // Rate limiting (indicates metered features)
  'rateLimit': 'Rate-limited endpoint',
  'rateLimiter': 'Rate limiting',
  'quota': 'Quota tracking',
  
  // Usage counters
  'increment': 'Usage counter',
  'usageCount': 'Usage tracking',
  'apiCalls': 'API usage',
};
```

### Usage Pattern Categories

```
Usage Patterns:
├── Frequency-Based
│   ├── Daily Active (core features)
│   ├── Weekly Active (reports, exports)
│   └── Monthly Active (admin, settings)
├── Volume-Based
│   ├── API calls per period
│   ├── Storage consumption
│   ├── Bandwidth usage
│   └── Compute time
├── Event-Based
│   ├── Transactions processed
│   ├── Messages sent
│   ├── Documents generated
│   └── AI requests made
└── Seat-Based
    ├── Active team members
    ├── Concurrent users
    └── Named users
```

### Usage Estimation Framework

```typescript
interface UsageProfile {
  feature: string;
  usageType: 'frequency' | 'volume' | 'event';
  
  // Estimated usage per user segment
  casual: number;    // Light users (bottom 50%)
  regular: number;   // Average users (middle 40%)
  power: number;     // Heavy users (top 10%)
  
  unit: string;      // 'per day' | 'per month' | 'per GB'
  costPerUnit: number;
}

const USAGE_PROFILES: UsageProfile[] = [
  {
    feature: 'API calls',
    usageType: 'event',
    casual: 50,
    regular: 500,
    power: 5000,
    unit: 'per month',
    costPerUnit: 0.001,
  },
  {
    feature: 'AI generations',
    usageType: 'event',
    casual: 5,
    regular: 50,
    power: 500,
    unit: 'per month',
    costPerUnit: 0.03,
  },
  {
    feature: 'Storage',
    usageType: 'volume',
    casual: 0.1,
    regular: 1,
    power: 10,
    unit: 'GB',
    costPerUnit: 0.023,
  },
  {
    feature: 'PDF exports',
    usageType: 'event',
    casual: 2,
    regular: 20,
    power: 100,
    unit: 'per month',
    costPerUnit: 0.01,
  },
];
```

## Revenue Modeling

### Key Metrics

```typescript
interface RevenueMetrics {
  // Average Revenue Per User
  arpu: {
    monthly: number;
    annual: number;
  };
  
  // Lifetime Value
  ltv: number;
  
  // Customer Acquisition Cost ratio
  ltvToCac: number;
  
  // Monthly Recurring Revenue
  mrr: number;
  
  // Annual Recurring Revenue
  arr: number;
  
  // Churn rate
  monthlyChurn: number;
  
  // Net Revenue Retention
  nrr: number;
}
```

### ARPU Calculation by Tier

```typescript
function calculateARPU(tierDistribution: TierDistribution): number {
  // Typical SaaS distribution
  const distribution = {
    free: { percent: 0.80, price: 0 },
    starter: { percent: 0.12, price: 9 },
    pro: { percent: 0.06, price: 29 },
    enterprise: { percent: 0.02, price: 99 },
  };
  
  const arpu = Object.values(distribution).reduce(
    (sum, tier) => sum + (tier.percent * tier.price),
    0
  );
  
  return arpu; // e.g., $4.80 blended ARPU
}
```

### LTV Calculation

```typescript
function calculateLTV(
  arpu: number,
  monthlyChurnRate: number,
  grossMargin: number = 0.80
): number {
  // LTV = (ARPU × Gross Margin) / Churn Rate
  const avgLifetimeMonths = 1 / monthlyChurnRate;
  return arpu * grossMargin * avgLifetimeMonths;
}

// Example:
// ARPU: $29, Churn: 5%, Margin: 80%
// LTV = ($29 × 0.80) / 0.05 = $464
```

### Revenue Projection Model

```typescript
interface RevenueProjection {
  month: number;
  users: number;
  paying: number;
  mrr: number;
  costs: number;
  profit: number;
  margin: number;
}

function projectRevenue(
  initialUsers: number,
  monthlyGrowthRate: number,
  conversionRate: number,
  arpu: number,
  costPerUser: number,
  months: number
): RevenueProjection[] {
  const projections: RevenueProjection[] = [];
  let users = initialUsers;
  
  for (let month = 1; month <= months; month++) {
    users = Math.floor(users * (1 + monthlyGrowthRate));
    const paying = Math.floor(users * conversionRate);
    const mrr = paying * arpu;
    const costs = users * costPerUser;
    const profit = mrr - costs;
    const margin = mrr > 0 ? (profit / mrr) * 100 : 0;
    
    projections.push({ month, users, paying, mrr, costs, profit, margin });
  }
  
  return projections;
}
```

## Tier Optimization

### Usage-Based Tier Limits

```typescript
interface TierLimits {
  tier: string;
  limits: {
    feature: string;
    limit: number;
    percentileTarget: number; // What % of users stay under limit
  }[];
}

// Set limits so most users stay within tier
const TIER_LIMITS: TierLimits[] = [
  {
    tier: 'free',
    limits: [
      { feature: 'API calls', limit: 100, percentileTarget: 0.80 },
      { feature: 'Storage', limit: 0.5, percentileTarget: 0.90 },
      { feature: 'AI generations', limit: 10, percentileTarget: 0.95 },
    ],
  },
  {
    tier: 'pro',
    limits: [
      { feature: 'API calls', limit: 5000, percentileTarget: 0.95 },
      { feature: 'Storage', limit: 10, percentileTarget: 0.95 },
      { feature: 'AI generations', limit: 100, percentileTarget: 0.90 },
    ],
  },
];
```

### Optimal Pricing Calculator

```typescript
interface PricingRecommendation {
  tier: string;
  recommendedPrice: number;
  priceRange: { min: number; max: number };
  rationale: string;
}

function calculateOptimalPrice(
  costToServe: number,
  perceivedValue: number,
  competitorPrice: number,
  targetMargin: number
): PricingRecommendation {
  // Price floor: cost + minimum margin
  const priceFloor = costToServe / (1 - targetMargin);
  
  // Price ceiling: perceived value or competitor price
  const priceCeiling = Math.min(perceivedValue, competitorPrice * 1.2);
  
  // Optimal: weighted average leaning toward value
  const optimal = priceFloor * 0.3 + priceCeiling * 0.7;
  
  return {
    tier: 'calculated',
    recommendedPrice: Math.round(optimal),
    priceRange: { 
      min: Math.round(priceFloor), 
      max: Math.round(priceCeiling) 
    },
    rationale: `Cost floor: $${priceFloor.toFixed(2)}, Value ceiling: $${priceCeiling.toFixed(2)}`,
  };
}
```

### Revenue per Tier Analysis

```typescript
interface TierRevenue {
  tier: string;
  price: number;
  estimatedUsers: number;
  conversionRate: number;
  monthlyRevenue: number;
  costToServe: number;
  grossProfit: number;
  margin: number;
}

function analyzeTierRevenue(tiers: TierConfig[]): TierRevenue[] {
  return tiers.map(tier => {
    const paying = tier.estimatedUsers * tier.conversionRate;
    const revenue = paying * tier.price;
    const costs = tier.estimatedUsers * tier.costPerUser;
    const profit = revenue - costs;
    
    return {
      tier: tier.name,
      price: tier.price,
      estimatedUsers: tier.estimatedUsers,
      conversionRate: tier.conversionRate,
      monthlyRevenue: revenue,
      costToServe: costs,
      grossProfit: profit,
      margin: revenue > 0 ? (profit / revenue) * 100 : 0,
    };
  });
}
```

## Consumption Tracking Implementation

### Database Schema for Usage Tracking

```sql
CREATE TABLE usage_events (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  feature VARCHAR(100) NOT NULL,
  quantity INTEGER DEFAULT 1,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE usage_aggregates (
  user_id UUID REFERENCES users(id),
  feature VARCHAR(100) NOT NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  total_usage INTEGER DEFAULT 0,
  PRIMARY KEY (user_id, feature, period_start)
);

-- Index for fast lookups
CREATE INDEX idx_usage_user_period ON usage_aggregates(user_id, period_start);
```

### Usage Tracking Service

```typescript
class UsageTracker {
  async trackUsage(userId: string, feature: string, quantity: number = 1) {
    // Record event
    await db.usageEvent.create({
      data: { userId, feature, quantity },
    });
    
    // Update aggregate
    const periodStart = startOfMonth(new Date());
    await db.usageAggregate.upsert({
      where: { userId_feature_periodStart: { userId, feature, periodStart } },
      update: { totalUsage: { increment: quantity } },
      create: { userId, feature, periodStart, totalUsage: quantity },
    });
  }
  
  async getUsage(userId: string, feature: string): Promise<number> {
    const periodStart = startOfMonth(new Date());
    const aggregate = await db.usageAggregate.findUnique({
      where: { userId_feature_periodStart: { userId, feature, periodStart } },
    });
    return aggregate?.totalUsage ?? 0;
  }
  
  async checkLimit(userId: string, feature: string): Promise<boolean> {
    const usage = await this.getUsage(userId, feature);
    const plan = await this.getUserPlan(userId);
    const limit = plan.limits[feature] ?? Infinity;
    return usage < limit;
  }
}
```

### Usage Analytics Queries

```sql
-- Average usage per feature by tier
SELECT 
  s.plan_id,
  ue.feature,
  AVG(ua.total_usage) as avg_usage,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ua.total_usage) as median_usage,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY ua.total_usage) as p90_usage,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY ua.total_usage) as p99_usage
FROM usage_aggregates ua
JOIN subscriptions s ON ua.user_id = s.user_id
WHERE ua.period_start = DATE_TRUNC('month', CURRENT_DATE)
GROUP BY s.plan_id, ue.feature;

-- Users approaching limits (upgrade candidates)
SELECT 
  u.id,
  u.email,
  ua.feature,
  ua.total_usage,
  p.limits->ua.feature as tier_limit,
  (ua.total_usage::float / (p.limits->ua.feature)::float * 100) as usage_percent
FROM usage_aggregates ua
JOIN users u ON ua.user_id = u.id
JOIN subscriptions s ON u.id = s.user_id
JOIN plans p ON s.plan_id = p.id
WHERE ua.period_start = DATE_TRUNC('month', CURRENT_DATE)
  AND ua.total_usage::float / (p.limits->ua.feature)::float > 0.8;
```

## Industry Benchmarks

### SaaS Metrics Benchmarks

| Metric | Poor | Average | Good | Excellent |
|--------|------|---------|------|-----------|
| Monthly Churn | >5% | 3-5% | 1-3% | <1% |
| Free→Paid Conversion | <2% | 2-5% | 5-10% | >10% |
| Net Revenue Retention | <90% | 90-100% | 100-120% | >120% |
| LTV:CAC Ratio | <1:1 | 1:1-3:1 | 3:1-5:1 | >5:1 |
| Gross Margin | <60% | 60-70% | 70-80% | >80% |

### Pricing Benchmarks by Category

| Category | Free Tier | Starter | Pro | Enterprise |
|----------|-----------|---------|-----|------------|
| Dev Tools | Yes | $9-19 | $29-49 | $99-299 |
| Productivity | Limited | $5-12 | $15-25 | $30-50/seat |
| AI/ML Tools | Credits | $20-50 | $100-200 | Custom |
| Analytics | Yes | $29-49 | $99-199 | $500+ |
| Marketing | Yes | $19-49 | $99-199 | $299+ |
