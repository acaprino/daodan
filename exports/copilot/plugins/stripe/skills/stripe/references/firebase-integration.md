<daodan_host_binding host="copilot">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. Custom
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

# Firebase + Stripe Integration Guide

This guide covers integrating Stripe payments with Firebase/Firestore for subscription-based web applications.

## Architecture Overview

The integration follows this pattern:

1. **Frontend** creates Checkout Sessions via Cloud Functions
2. **Stripe** handles payment collection securely
3. **Webhooks** sync subscription state to Firestore
4. **Security Rules** control access based on subscription status

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│ Cloud Func   │────▶│   Stripe    │
│   (React)   │     │  (Backend)   │     │   Checkout  │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
                    ┌──────────────┐              │
                    │  Firestore   │◀─────────────┘
                    │  (Database)  │    Webhooks update
                    └──────┬───────┘    subscription status
                           │
                    ┌──────▼───────┐
                    │   Security   │
                    │    Rules     │
                    └──────────────┘
```

## Firestore Data Model

### Users Collection

```
/users/{userId}
{
  email: "user@example.com",
  displayName: "John Doe",
  createdAt: Timestamp,
  
  // Stripe data
  stripeCustomerId: "cus_xxx",
  
  // Subscription (synced by webhooks)
  subscription: {
    status: "active" | "trialing" | "past_due" | "canceled" | "none",
    plan: "pro_monthly",
    subscriptionId: "sub_xxx",
    currentPeriodEnd: Timestamp,
    cancelAtPeriodEnd: false
  }
}
```

### Products Collection (Optional - for dynamic pricing)

```
/products/{productId}
{
  name: "Pro Plan",
  description: "Full access",
  active: true,
  
  // Prices subcollection
  /prices/{priceId}
  {
    unit_amount: 999,
    currency: "eur",
    interval: "month",
    lookup_key: "pro_monthly"
  }
}
```

## Cloud Functions Implementation

### 1. Create Checkout Session

```typescript
// functions/src/stripe.ts
import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2025-09-30.preview',  // pin to a current dated version; check https://stripe.com/docs/upgrades for latest
});

admin.initializeApp();
const db = admin.firestore();

export const createCheckoutSession = functions.https.onCall(
  async (data, context) => {
    // Require authentication
    if (!context.auth) {
      throw new functions.https.HttpsError(
        'unauthenticated',
        'Must be logged in'
      );
    }

    const userId = context.auth.uid;
    const { priceId, successUrl, cancelUrl } = data;

    // Get or create Stripe customer
    const userDoc = await db.collection('users').doc(userId).get();
    const userData = userDoc.data();
    
    let customerId = userData?.stripeCustomerId;
    
    if (!customerId) {
      // Create new Stripe customer
      const customer = await stripe.customers.create({
        email: context.auth.token.email,
        metadata: { firebaseUID: userId }
      });
      
      customerId = customer.id;
      
      // Save to Firestore
      await db.collection('users').doc(userId).set(
        { stripeCustomerId: customerId },
        { merge: true }
      );
    }

    // Create checkout session
    const session = await stripe.checkout.Session.create({
      customer: customerId,
      mode: 'subscription',
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: successUrl,
      cancel_url: cancelUrl,
      metadata: { firebaseUID: userId }
    });

    return { sessionId: session.id, url: session.url };
  }
);
```

### 2. Create Billing Portal Session

```typescript
export const createPortalSession = functions.https.onCall(
  async (data, context) => {
    if (!context.auth) {
      throw new functions.https.HttpsError('unauthenticated', 'Must be logged in');
    }

    const userId = context.auth.uid;
    const userDoc = await db.collection('users').doc(userId).get();
    const customerId = userDoc.data()?.stripeCustomerId;

    if (!customerId) {
      throw new functions.https.HttpsError('not-found', 'No subscription found');
    }

    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: data.returnUrl
    });

    return { url: session.url };
  }
);
```

### 3. Webhook Handler

```typescript
export const stripeWebhook = functions.https.onRequest(async (req, res) => {
  const sig = req.headers['stripe-signature'] as string;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(req.rawBody, sig, webhookSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    res.status(400).send(`Webhook Error: ${err}`);
    return;
  }

  // Handle events
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutComplete(session);
      break;
    }
    
    case 'customer.subscription.updated':
    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;
      await syncSubscriptionToFirestore(subscription);
      break;
    }
    
    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      await handlePaymentFailed(invoice);
      break;
    }
  }

  res.json({ received: true });
});

async function handleCheckoutComplete(session: Stripe.Checkout.Session) {
  const customerId = session.customer as string;
  const subscriptionId = session.subscription as string;

  // Find user by customer ID
  const usersRef = db.collection('users');
  const snapshot = await usersRef
    .where('stripeCustomerId', '==', customerId)
    .limit(1)
    .get();

  if (snapshot.empty) {
    console.error('No user found for customer:', customerId);
    return;
  }

  const userDoc = snapshot.docs[0];
  
  // Get full subscription details
  const subscription = await stripe.subscriptions.retrieve(subscriptionId);
  
  // Update user document
  await userDoc.ref.update({
    subscription: {
      status: subscription.status,
      subscriptionId: subscription.id,
      plan: subscription.items.data[0].price.lookup_key || subscription.items.data[0].price.id,
      currentPeriodEnd: admin.firestore.Timestamp.fromMillis(subscription.current_period_end * 1000),
      cancelAtPeriodEnd: subscription.cancel_at_period_end
    }
  });
}

async function syncSubscriptionToFirestore(subscription: Stripe.Subscription) {
  const customerId = subscription.customer as string;
  
  const usersRef = db.collection('users');
  const snapshot = await usersRef
    .where('stripeCustomerId', '==', customerId)
    .limit(1)
    .get();

  if (snapshot.empty) return;

  const userDoc = snapshot.docs[0];
  
  const subscriptionData = {
    status: subscription.status,
    subscriptionId: subscription.id,
    plan: subscription.items.data[0].price.lookup_key || subscription.items.data[0].price.id,
    currentPeriodEnd: admin.firestore.Timestamp.fromMillis(subscription.current_period_end * 1000),
    cancelAtPeriodEnd: subscription.cancel_at_period_end
  };

  await userDoc.ref.update({ subscription: subscriptionData });
}

async function handlePaymentFailed(invoice: Stripe.Invoice) {
  // Optionally notify user, update UI state, etc.
  console.log('Payment failed for invoice:', invoice.id);
}
```

## Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Helper function to check subscription status
    function hasActiveSubscription() {
      return get(/databases/$(database)/documents/users/$(request.auth.uid)).data.subscription.status in ['active', 'trialing'];
    }
    
    function isPremiumPlan() {
      let sub = get(/databases/$(database)/documents/users/$(request.auth.uid)).data.subscription;
      return sub.status in ['active', 'trialing'] && sub.plan in ['pro_monthly', 'pro_yearly', 'enterprise_monthly', 'enterprise_yearly'];
    }
    
    // Users can read/write their own data
    match /users/{userId} {
      allow read: if request.auth.uid == userId;
      allow write: if request.auth.uid == userId && 
                      !request.resource.data.diff(resource.data).affectedKeys()
                        .hasAny(['stripeCustomerId', 'subscription']);
    }
    
    // Premium content - requires active subscription
    match /premium/{document=**} {
      allow read: if request.auth != null && hasActiveSubscription();
    }
    
    // Pro-only features
    match /pro-features/{document=**} {
      allow read, write: if request.auth != null && isPremiumPlan();
    }
  }
}
```

## Frontend Implementation (React)

### Checkout Button Component

```tsx
import { getFunctions, httpsCallable } from 'firebase/functions';
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLIC_KEY!);

export function CheckoutButton({ priceId }: { priceId: string }) {
  const [loading, setLoading] = useState(false);

  const handleCheckout = async () => {
    setLoading(true);
    
    try {
      const functions = getFunctions();
      const createCheckout = httpsCallable(functions, 'createCheckoutSession');
      
      const { data } = await createCheckout({
        priceId,
        successUrl: `${window.location.origin}/success`,
        cancelUrl: `${window.location.origin}/pricing`
      });
      
      // Redirect to Stripe Checkout
      window.location.href = (data as any).url;
      
    } catch (error) {
      console.error('Checkout error:', error);
      setLoading(false);
    }
  };

  return (
    <button onClick={handleCheckout} disabled={loading}>
      {loading ? 'Loading...' : 'Subscribe'}
    </button>
  );
}
```

### Subscription Status Hook

```tsx
import { useEffect, useState } from 'react';
import { doc, onSnapshot } from 'firebase/firestore';
import { useAuth } from './useAuth';
import { db } from './firebase';

interface Subscription {
  status: 'active' | 'trialing' | 'past_due' | 'canceled' | 'none';
  plan: string;
  currentPeriodEnd: Date;
  cancelAtPeriodEnd: boolean;
}

export function useSubscription() {
  const { user } = useAuth();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setSubscription(null);
      setLoading(false);
      return;
    }

    const unsubscribe = onSnapshot(
      doc(db, 'users', user.uid),
      (doc) => {
        const data = doc.data();
        if (data?.subscription) {
          setSubscription({
            ...data.subscription,
            currentPeriodEnd: data.subscription.currentPeriodEnd.toDate()
          });
        } else {
          setSubscription({ status: 'none', plan: '', currentPeriodEnd: new Date(), cancelAtPeriodEnd: false });
        }
        setLoading(false);
      }
    );

    return unsubscribe;
  }, [user]);

  const isActive = subscription?.status === 'active' || subscription?.status === 'trialing';
  const isPro = isActive && ['pro_monthly', 'pro_yearly'].includes(subscription?.plan || '');

  return { subscription, loading, isActive, isPro };
}
```

### Manage Subscription Button

```tsx
export function ManageSubscriptionButton() {
  const [loading, setLoading] = useState(false);

  const handleManage = async () => {
    setLoading(true);
    
    try {
      const functions = getFunctions();
      const createPortal = httpsCallable(functions, 'createPortalSession');
      
      const { data } = await createPortal({
        returnUrl: window.location.href
      });
      
      window.location.href = (data as any).url;
      
    } catch (error) {
      console.error('Portal error:', error);
      setLoading(false);
    }
  };

  return (
    <button onClick={handleManage} disabled={loading}>
      {loading ? 'Loading...' : 'Manage Subscription'}
    </button>
  );
}
```

## Deployment Checklist

1. **Environment Variables**
   - Set `STRIPE_SECRET_KEY` in Cloud Functions config
   - Set `STRIPE_WEBHOOK_SECRET` in Cloud Functions config
   - Set `REACT_APP_STRIPE_PUBLIC_KEY` in frontend .env

2. **Stripe Dashboard**
   - Create products and prices
   - Configure Customer Portal settings
   - Set up webhook endpoint pointing to your Cloud Function

3. **Firebase**
   - Deploy Cloud Functions
   - Update Firestore Security Rules
   - Enable required Firebase services

4. **Testing**
   - Use Stripe test mode
   - Test complete checkout flow
   - Verify webhook events are processed
   - Test subscription cancellation and reactivation
