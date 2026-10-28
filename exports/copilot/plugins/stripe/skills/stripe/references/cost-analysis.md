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

# Cost Analysis Patterns

## Service Detection

### 1. Scan Configuration Files

```bash
# Find environment variables
grep -r "API_KEY\|SECRET\|TOKEN" .env* config/

# Find infrastructure definitions
find . -name "*.tf" -o -name "serverless.yml" -o -name "docker-compose.yml"
```

### 2. Scan Dependencies

```javascript
// package.json indicators
const COST_INDICATORS = {
  // Cloud providers
  'aws-sdk': 'AWS services',
  '@aws-sdk/*': 'AWS services',
  '@google-cloud/*': 'GCP services',
  '@azure/*': 'Azure services',
  
  // AI/ML
  'openai': 'OpenAI API',
  'anthropic': 'Anthropic API',
  'replicate': 'Replicate API',
  
  // Communications
  'twilio': 'Twilio SMS/Voice',
  '@sendgrid/mail': 'SendGrid Email',
  'postmark': 'Postmark Email',
  'nodemailer': 'Email (check provider)',
  
  // Payments
  'stripe': 'Stripe fees (2.9% + $0.30)',
  
  // Storage/Database
  '@prisma/client': 'Database (check provider)',
  'mongoose': 'MongoDB',
  '@supabase/supabase-js': 'Supabase',
  '@planetscale/*': 'PlanetScale',
  
  // Search
  'algoliasearch': 'Algolia',
  '@elastic/*': 'Elasticsearch',
  
  // Auth
  '@auth0/*': 'Auth0',
  'firebase-admin': 'Firebase',
  '@clerk/*': 'Clerk',
};
```

### 3. Scan Code for Usage

```typescript
// Find service instantiations
const SERVICE_PATTERNS = [
  /new S3Client/g,           // AWS S3
  /new OpenAI/g,             // OpenAI
  /Anthropic\(/g,            // Anthropic
  /twilio\.messages/g,       // Twilio SMS
  /sendgrid\.send/g,         // SendGrid
  /stripe\.(customers|subscriptions|charges)/g, // Stripe
];
```

## Common Service Pricing

### AI/ML Services

| Service | Cost | Unit |
|---------|------|------|
| OpenAI GPT-4 | $0.03 | per 1K input tokens |
| OpenAI GPT-4 | $0.06 | per 1K output tokens |
| OpenAI GPT-4o | $0.005 | per 1K input tokens |
| OpenAI GPT-4o | $0.015 | per 1K output tokens |
| OpenAI GPT-4o-mini | $0.00015 | per 1K input tokens |
| OpenAI Whisper | $0.006 | per minute audio |
| OpenAI DALL-E 3 | $0.04-0.12 | per image |
| Anthropic Claude Sonnet | $0.003 | per 1K input tokens |
| Anthropic Claude Sonnet | $0.015 | per 1K output tokens |
| Replicate (varies) | $0.0001-0.01 | per second GPU |

### Cloud Infrastructure

| Service | Cost | Unit |
|---------|------|------|
| AWS S3 Storage | $0.023 | per GB/month |
| AWS S3 Requests | $0.0004 | per 1K GET |
| AWS Lambda | $0.0000166 | per GB-second |
| AWS Lambda | $0.20 | per 1M requests |
| Vercel Pro | $20 | per month base |
| Vercel Functions | $0.40 | per 1M invocations |
| PlanetScale | $29 | per month (Scaler) |
| Supabase | $25 | per month (Pro) |

### Communications

| Service | Cost | Unit |
|---------|------|------|
| SendGrid | $0.00100 | per email (free tier: 100/day) |
| Twilio SMS | $0.0079 | per outbound SMS |
| Twilio Voice | $0.014 | per minute |
| Postmark | $0.00100 | per email |

### Auth Providers

| Service | Cost | Unit |
|---------|------|------|
| Auth0 | $0.00 | first 7,500 MAU free |
| Auth0 | $0.07 | per MAU (Essentials) |
| Clerk | $0.00 | first 10,000 MAU free |
| Clerk | $0.02 | per MAU beyond free |
| Firebase Auth | Free | unlimited |

### Payment Processing

| Service | Cost | Unit |
|---------|------|------|
| Stripe | 2.9% + $0.30 | per transaction |
| Stripe Billing | 0.5% | subscription revenue |
| PayPal | 2.99% + $0.49 | per transaction |

## Cost Calculation Patterns

### Per-User Cost Estimation

```typescript
interface CostBreakdown {
  fixed: {
    monthly: number;
    description: string;
  }[];
  perUser: {
    monthly: number;
    description: string;
  }[];
  perFeature: {
    feature: string;
    costPerUse: number;
    avgUsesPerUser: number;
  }[];
}

function calculateCostPerUser(costs: CostBreakdown, userCount: number): number {
  const totalFixed = costs.fixed.reduce((sum, c) => sum + c.monthly, 0);
  const fixedPerUser = totalFixed / userCount;
  
  const variablePerUser = costs.perUser.reduce((sum, c) => sum + c.monthly, 0);
  
  const featureCostPerUser = costs.perFeature.reduce(
    (sum, f) => sum + (f.costPerUse * f.avgUsesPerUser), 
    0
  );
  
  return fixedPerUser + variablePerUser + featureCostPerUser;
}
```

### Feature Cost Attribution

```typescript
// Map features to their cost drivers
const FEATURE_COSTS = {
  'ai_analysis': {
    services: ['openai'],
    estimatedCostPerUse: 0.03, // ~1K tokens in, 500 out
    category: 'high',
  },
  'pdf_export': {
    services: ['lambda', 'puppeteer'],
    estimatedCostPerUse: 0.01,
    category: 'medium',
  },
  'email_notification': {
    services: ['sendgrid'],
    estimatedCostPerUse: 0.001,
    category: 'low',
  },
  'file_upload': {
    services: ['s3'],
    estimatedCostPerUse: 0.001, // ~1MB avg
    category: 'low',
  },
  'sms_alert': {
    services: ['twilio'],
    estimatedCostPerUse: 0.008,
    category: 'medium',
  },
};
```

### Break-Even Analysis

```typescript
function calculateBreakEven(
  fixedCosts: number,      // Monthly fixed costs
  variableCostPerUser: number,
  pricePerUser: number
): number {
  // Break-even users = Fixed Costs / (Price - Variable Cost)
  const contribution = pricePerUser - variableCostPerUser;
  if (contribution <= 0) {
    throw new Error('Price must exceed variable cost per user');
  }
  return Math.ceil(fixedCosts / contribution);
}

// Example
const breakEvenUsers = calculateBreakEven(
  95,    // $95/month fixed
  0.50,  // $0.50/user variable
  9.00   // $9/user price
);
// Result: 12 users to break even
```

### Margin Calculation

```typescript
function calculateMargin(
  revenue: number,
  fixedCosts: number,
  variableCosts: number
): { grossMargin: number; netMargin: number } {
  const grossProfit = revenue - variableCosts;
  const netProfit = revenue - fixedCosts - variableCosts;
  
  return {
    grossMargin: (grossProfit / revenue) * 100,
    netMargin: (netProfit / revenue) * 100,
  };
}
```

## Cost Analysis Report Template

```markdown
# Cost Analysis Report

## Services Detected
| Service | Purpose | Pricing Model |
|---------|---------|---------------|
| [Service] | [Usage] | [$/unit] |

## Fixed Costs (Monthly)
| Item | Cost | Notes |
|------|------|-------|
| Hosting | $X | [Provider] |
| Database | $X | [Provider] |
| **Total** | **$X** | |

## Variable Costs (Per User/Month)
| Item | Cost | Calculation |
|------|------|-------------|
| Auth | $X | [MAU rate] |
| Storage | $X | [avg GB × rate] |
| **Total** | **$X/user** | |

## Feature Costs (Per Use)
| Feature | Cost | Avg Uses/User/Month |
|---------|------|---------------------|
| [Feature] | $X | X times |

## Pricing Recommendations
- **Minimum price** (break-even): $X/user
- **Recommended price** (60% margin): $X/user
- **Premium features**: Gate features costing >$X/use

## Tier Suggestions
| Tier | Features | Cost Basis | Suggested Price |
|------|----------|------------|-----------------|
| Free | [list] | <$0.50/user | $0 |
| Pro | [list] | ~$2/user | $9-15 |
| Enterprise | [list] | ~$10/user | $49+ |
```

## Automated Cost Scanning Script

```typescript
// Pseudocode for automated cost analysis
async function analyzeCosts(projectPath: string) {
  // 1. Detect services
  const packageJson = await readFile(`${projectPath}/package.json`);
  const envVars = await readFile(`${projectPath}/.env.example`);
  const services = detectServices(packageJson, envVars);
  
  // 2. Scan code for usage patterns
  const usagePatterns = await scanCodebase(projectPath, services);
  
  // 3. Estimate costs
  const costs = services.map(service => ({
    service,
    pricing: SERVICE_PRICING[service],
    estimatedUsage: usagePatterns[service],
    monthlyCost: calculateMonthlyCost(service, usagePatterns[service]),
  }));
  
  // 4. Generate report
  return generateCostReport(costs);
}
```
