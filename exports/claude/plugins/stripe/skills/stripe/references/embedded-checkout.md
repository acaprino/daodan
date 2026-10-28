<daodan_host_binding host="claude">
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

Claude binding: repository read, file discovery and content search use Read, Glob
and Grep; repository write and repository edit use Write and Edit; shell execution
uses Bash; network fetch uses WebFetch and network search uses WebSearch; a user
question uses AskUserQuestion. Pass the executable string in Bash's
command field, and use its registered timeout/background schema. Worker dispatch
uses the available native Agent mechanism and its registered agent-selection and
prompt fields. Do not turn a prose role label into an invented role argument.
Inherit the session model unless the declared workflow and active schema permit an
override. Load installed skills by qualified ID; named roles use their owning
plugin's agent identity, while workflow entries use /<plugin>:<workflow>.
Required foreign providers use Claude's marketplace/install commands:
claude plugin marketplace add <source>, then claude plugin install <provider>@<marketplace>.
A provider that is installed but disabled is enabled with
claude plugin enable <provider>@<marketplace>; check `claude plugin list --json`
before the first phase, and stop with that command when any plugin of this
package's dependency closure, direct or transitive, is off.
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

# Embedded Checkout

Stripe Checkout that mounts inside your React tree instead of redirecting. The middle option between hosted redirect and fully custom Payment Element.

## Decision matrix

| Mode | When |
|------|------|
| **Hosted redirect** | Fastest ship; no UI work. User leaves your domain. |
| **Embedded** (`ui_mode: 'embedded'`) | SPA feel, stays on your domain, Stripe controls payment form visuals. |
| **Custom Payment Element** | Full layout control, multi-step checkout, you handle SCA and error states. |

Default to hosted redirect for v0. Migrate to embedded when a full redirect breaks your UX. Go custom only when embedded's layout constraints are actually blocking.

Two embedded sub-modes: `ui_mode: 'embedded'` for inline mount within an existing page, `ui_mode: 'embedded_page'` for dedicated full-page embeds (SPA route that would otherwise be a redirect target).

## Gotchas

- **Return `client_secret` to the client, not `session.id`.** Anyone with the session ID can retrieve metadata. Only `client_secret` is safe in the browser.
- **`session.url` is null in embedded mode.** The `url` field works only for hosted redirect.
- **`fetchClientSecret` runs at mount time.** Don't pre-fetch -- the secret ages on the client. Fetch-on-mount.
- **`return_url` and `onComplete` are mutually exclusive.** Pick one: `return_url` redirects after success; `onComplete` fires a JS callback for modal/drawer flows.
- **Apple Pay / Google Pay need domain verification** when your domain is in the flow (embedded does this; hosted doesn't). Call `stripe.paymentMethodDomains.create` + `.validate` once per production domain. Test on a real device -- desktop Chrome hides the issue.
- **Grant access from the webhook, not the return page.** Return page is read-only UI; query params can be forged.
- **`payment_method_configuration` over hardcoded `payment_method_types`.** Lets you manage the PM list from Dashboard without redeploying.
- **Adaptive Pricing** (local-currency presentment) is a Dashboard toggle. Watch for refund/proration rounding deltas in non-default currencies.

## Official docs

- Quickstart with full code (server + React mount): https://docs.stripe.com/checkout/embedded/quickstart
- Embedded vs hosted vs custom: https://docs.stripe.com/payments/checkout/how-checkout-works
- React component reference: https://docs.stripe.com/checkout/embedded/react
- Apple Pay / Google Pay domain setup: https://docs.stripe.com/payments/payment-methods/pmd-registration
- Adaptive Pricing: https://docs.stripe.com/payments/checkout/adaptive-pricing
- `payment_method_configuration`: https://docs.stripe.com/payments/payment-method-configurations

## Related

- `typescript-nextjs.md` -- broader App Router patterns
- `webhooks-production.md` -- `checkout.session.completed` handling
- `checkout-optimization.md` -- conversion patterns (fields, trust signals)
