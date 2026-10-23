<daodan_host_binding host="claude">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Claude binding: repository tools are Read/Glob/Grep and Write/Edit; shell execution
uses Bash and network fetch uses WebFetch. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A declared package MCP server is configured through the generated MCP manifest;
still check its tools are actually available in the active session.

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

# Checkout Optimization

## High-Converting Pricing Page

```tsx
function PricingPage() {
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('yearly');
  
  return (
    <div className="pricing-page">
      {/* Billing Toggle */}
      <div className="billing-toggle">
        <button onClick={() => setBillingInterval('monthly')}>Monthly</button>
        <button onClick={() => setBillingInterval('yearly')}>
          Yearly <span className="discount-badge">Save 20%</span>
        </button>
      </div>
      
      {/* Plan Cards */}
      <div className="plan-cards">
        {Object.values(PLANS).map(plan => (
          <PlanCard 
            key={plan.id}
            plan={plan}
            interval={billingInterval}
            recommended={plan.recommended}
          />
        ))}
      </div>
      
      {/* Trust Signals */}
      <TrustSignals />
      
      {/* FAQ */}
      <PricingFAQ />
    </div>
  );
}
```

## Plan Card with Conversion Elements

```tsx
function PlanCard({ plan, interval, recommended }) {
  return (
    <div className={`plan-card ${recommended ? 'recommended' : ''}`}>
      {recommended && <div className="badge">Most Popular</div>}
      
      <h3>{plan.name}</h3>
      
      <div className="price">
        <span className="amount">${plan.price[interval]}</span>
        <span className="interval">/{interval === 'yearly' ? 'year' : 'month'}</span>
      </div>
      
      {interval === 'yearly' && (
        <div className="savings">
          Save ${plan.price.monthly * 12 - plan.price.yearly}/year
        </div>
      )}
      
      <ul className="features">
        {plan.features.map(f => (
          <li key={f}><CheckIcon /> {f}</li>
        ))}
      </ul>
      
      <button 
        className={recommended ? 'cta-primary' : 'cta-secondary'}
        onClick={() => startCheckout(plan.id, interval)}
      >
        {plan.price.monthly === 0 ? 'Start Free' : 'Get Started'}
      </button>
      
      {plan.price.monthly > 0 && (
        <p className="guarantee">14-day money-back guarantee</p>
      )}
    </div>
  );
}
```

## Trust Signals Component

```tsx
function TrustSignals() {
  return (
    <div className="trust-signals">
      <div className="signal">
        <ShieldIcon />
        <span>256-bit SSL encryption</span>
      </div>
      <div className="signal">
        <RefundIcon />
        <span>14-day money-back guarantee</span>
      </div>
      <div className="signal">
        <CancelIcon />
        <span>Cancel anytime</span>
      </div>
      
      {/* Social Proof */}
      <div className="social-proof">
        <div className="customer-logos">
          <img src="/logos/company1.svg" alt="Company 1" />
          <img src="/logos/company2.svg" alt="Company 2" />
        </div>
        <p>Trusted by 10,000+ teams</p>
      </div>
      
      {/* Testimonial */}
      <blockquote className="testimonial">
        "This tool has 10x'd our productivity."
        <cite>-- Jane D., CEO at TechCo</cite>
      </blockquote>
    </div>
  );
}
```

## Checkout Flow Best Practices

### 1. Minimize Steps

```tsx
// BAD: Multi-page checkout
// Page 1: Select plan → Page 2: Account → Page 3: Billing → Page 4: Confirm

// GOOD: Single page or 2-step max
// Step 1: Plan + Email → Step 2: Payment (Stripe Checkout handles this)
```

### 2. Pre-fill Known Data

```typescript
const session = await stripe.checkout.sessions.create({
  customer_email: user.email, // Pre-fill email
  customer: user.stripeCustomerId, // Use existing customer
  client_reference_id: user.id,
  // ...
});
```

### 3. Show Price Breakdown

```tsx
function CheckoutSummary({ plan, interval, coupon }) {
  const basePrice = plan.price[interval];
  const discount = coupon ? basePrice * coupon.percentOff / 100 : 0;
  const total = basePrice - discount;
  
  return (
    <div className="checkout-summary">
      <div className="line-item">
        <span>{plan.name} ({interval})</span>
        <span>${basePrice}</span>
      </div>
      {coupon && (
        <div className="line-item discount">
          <span>Discount ({coupon.code})</span>
          <span>-${discount}</span>
        </div>
      )}
      <div className="line-item total">
        <span>Total</span>
        <span>${total}</span>
      </div>
    </div>
  );
}
```

## Upgrade Prompts (Conversion Triggers)

### Feature Gate Prompt

```tsx
function FeatureGate({ feature, children }) {
  const { hasAccess, requiredPlan } = useFeatureAccess(feature);
  
  if (hasAccess) return children;
  
  return (
    <div className="feature-gate">
      <LockIcon />
      <h3>Unlock {feature}</h3>
      <p>Upgrade to {requiredPlan} to access this feature.</p>
      <button onClick={() => showUpgradeModal(requiredPlan)}>
        Upgrade Now
      </button>
    </div>
  );
}
```

### Usage Limit Prompt

```tsx
function UsageLimitBanner({ resource, current, limit }) {
  const percentage = (current / limit) * 100;
  
  if (percentage < 80) return null;
  
  return (
    <div className={`usage-banner ${percentage >= 100 ? 'exceeded' : 'warning'}`}>
      <p>
        You've used {current} of {limit} {resource}.
        {percentage >= 100 ? ' Upgrade to continue.' : ' Consider upgrading.'}
      </p>
      <button onClick={showUpgradeModal}>Upgrade</button>
    </div>
  );
}
```

### Trial Ending Prompt

```tsx
function TrialBanner({ daysLeft }) {
  if (daysLeft > 3) return null;
  
  return (
    <div className="trial-banner">
      <p>
        Your trial ends in {daysLeft} day{daysLeft !== 1 ? 's' : ''}.
        Subscribe now to keep your data.
      </p>
      <button onClick={showSubscribeModal}>Subscribe</button>
    </div>
  );
}
```

## Coupon/Promo Codes

```typescript
// Enable promo codes in checkout
const session = await stripe.checkout.sessions.create({
  allow_promotion_codes: true, // User can enter codes
  // OR apply a specific coupon
  discounts: [{ coupon: 'LAUNCH20' }],
});

// Create coupon programmatically
const coupon = await stripe.coupons.create({
  percent_off: 20,
  duration: 'once', // or 'forever', 'repeating'
  id: 'LAUNCH20',
});
```

## A/B Testing Checkout

```tsx
function PricingPage() {
  const variant = useExperiment('pricing-page-v2');
  
  // Track view
  useEffect(() => {
    track('pricing_page_viewed', { variant });
  }, []);
  
  // Track conversion
  const handleCheckout = (plan) => {
    track('checkout_started', { variant, plan });
    startCheckout(plan);
  };
  
  if (variant === 'control') return <PricingPageV1 onCheckout={handleCheckout} />;
  return <PricingPageV2 onCheckout={handleCheckout} />;
}
```

## Conversion Tracking Events

```typescript
// Track full funnel
const CONVERSION_EVENTS = [
  'pricing_page_viewed',
  'plan_selected',
  'checkout_started',
  'checkout_completed',
  'subscription_activated',
];

// Implementation
function trackConversion(event: string, data: object) {
  // Analytics (Mixpanel, Amplitude, etc.)
  analytics.track(event, data);
  
  // Google Analytics
  gtag('event', event, data);
  
  // Meta/Facebook Pixel
  if (event === 'checkout_completed') {
    fbq('track', 'Purchase', { value: data.amount, currency: 'USD' });
  }
}
```
