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

# TypeScript and Next.js

Canonical TypeScript reference. Counterweight to the Python-heavy rest of this skill.

## Setup

```bash
pnpm add stripe @stripe/stripe-js @stripe/react-stripe-js
```

Pin the API version on the server client: `new Stripe(key, { apiVersion: '2026-05-27.dahlia', typescript: true })`.

Env var hygiene: `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` server-only; `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` is the *only* key prefixed with `NEXT_PUBLIC_`. Never prefix a secret this way -- it ships to the browser.

## Gotchas specific to Next.js

- **Webhooks must run on Node.** Set `export const runtime = 'nodejs'` and `export const dynamic = 'force-dynamic'` on `app/api/webhooks/stripe/route.ts`. Edge runtime breaks raw-body handling silently.
- **Read body with `req.text()`, not `req.json()`.** Re-serialization breaks signature verification.
- **Don't call Stripe from Client Components.** Importing `lib/stripe.ts` into a `'use client'` tree leaks the secret key into the browser bundle. Keep Stripe imports server-only (API routes, Server Actions, Server Components).
- **`redirect()` in Server Actions must be outside try/catch.** It throws `NEXT_REDIRECT`; catching it swallows the redirect.
- **Don't grant access on the success page.** The page runs with query params; anyone can forge `session_id`. Grant access from the `checkout.session.completed` webhook. Success page is read-only UI.
- **Middleware runs on Edge by default.** Don't put Stripe calls in `middleware.ts`. Auth checks only.
- **Static caching on the return page.** Wrap in `export const dynamic = 'force-dynamic'` or use Suspense streaming; otherwise `searchParams` can be stale.

## Type-narrowed event handling

`Stripe.Event` is a discriminated union. `switch (event.type)` narrows `event.data.object` per case -- no casts needed. If the compiler doesn't narrow, your SDK is behind the API version you're pinning; upgrade rather than cast.

## Preferred patterns

- **Server Actions** for triggering Checkout from forms.
- **Route Handlers** (`app/api/.../route.ts`) for webhooks.
- **Discriminated-union `switch`** for event routing.
- **Return-page reads `checkout.sessions.retrieve`** for confirmation UI, but webhook is the source of truth for access.

## Official docs

- Node SDK reference: https://docs.stripe.com/api?lang=node
- Next.js + Stripe quickstart: https://docs.stripe.com/payments/checkout/how-checkout-works (language switcher: Node)
- Sample Next.js app: https://github.com/stripe-samples/nextjs-typescript-react-stripe-js
- Webhooks in Node: https://docs.stripe.com/webhooks/quickstart

## Related

- `webhooks-production.md` -- runtime + signature + idempotency checklist
- `embedded-checkout.md` -- client-mountable Checkout in React
- `stripe.md` -- core patterns (overlap with this file is intentional)
