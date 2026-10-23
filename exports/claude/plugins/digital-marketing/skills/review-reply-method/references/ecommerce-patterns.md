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

# E-commerce and App Review Patterns

Sector-specific reference for responding to reviews of products, online stores, and mobile/web applications.

## Platforms

Amazon, Trustpilot, App Store (iOS), Google Play, eBay, Etsy, G2, Capterra, Product Hunt

## Vocabulary Map

Common topics in e-commerce/app reviews and their typical phrasing:

| Category | Positive Signals | Negative Signals |
|----------|-----------------|------------------|
| Product Quality | excellent quality, well-made, durable, exceeded expectations, premium | cheap, broke quickly, poor quality, defective, flimsy, not as pictured |
| Shipping/Delivery | fast shipping, well-packaged, arrived early, free shipping | late delivery, damaged in transit, wrong item, lost package, slow shipping |
| Customer Service | helpful support, quick response, resolved immediately, went above and beyond | no response, unhelpful, rude, ignored, long wait, ticket closed without resolution |
| App Stability | smooth, fast, no crashes, works perfectly, reliable | crashes, freezes, bugs, slow, laggy, won't load, error messages |
| App Features | intuitive, easy to use, love the new feature, clean design | missing features, confusing UI, hard to navigate, cluttered, feature removed |
| Price/Value | great value, worth every penny, affordable, good deal | overpriced, not worth it, hidden fees, subscription too expensive, bait and switch |
| Returns/Refunds | easy return, quick refund, hassle-free, no questions asked | difficult return process, refused refund, restocking fee, took weeks for refund |
| Packaging | beautiful packaging, eco-friendly, gift-ready, well-protected | excessive packaging, damaged box, no protection, wasteful |

## Response Patterns by Severity

These are structural guides, not copy-paste templates. Every response must sound like a real person wrote it. Reference specific details from the actual review.

### Positive Review

Structure: Brief thanks -> Reference a specific detail -> Light forward-look

Example (friendly tone):
> [Name], glad the [specific product/feature] is working well for you. We put a lot of work into [specific aspect they mentioned]. Stick around, there's more coming.

Anti-patterns to avoid: "We're so glad you're enjoying", "it means a lot to hear", "exciting updates coming that we think you'll love".

### Negative - Unfounded/Unrealistic Expectations

Structure: Acknowledge the feeling -> One factual clarification -> Offer help

Example (friendly tone):
> [Name], we get the frustration. [Product/feature] does [actual scope], which is what we describe in [listing/docs]. If you need help getting the most out of it, write us at [contact].

Anti-patterns to avoid: "We understand X might not have met your expectations", "we're always improving", "our support team is happy to assist".

### Negative - Minor Real Problem

Structure: Acknowledge the issue -> What you fixed -> Offer to make it right

Example (friendly tone):
> That shouldn't have happened, [Name]. We fixed [specific action] so it won't repeat. Write us at [contact] and we'll sort out [specific remedy] for you.

Anti-patterns to avoid: "Thank you for letting us know", "that's not the standard we aim for", "We'd love to make this right".

### Negative - Major Real Problem

Structure: Direct apology -> Take responsibility -> Action taken -> Compensation -> Contact

Example (friendly tone):
> [Name], this one's on us. [Issue] shouldn't happen, period. We've already [urgent action] and changed [systemic fix]. Write us at [contact] for a [specific compensation]. We owe you that.

Anti-patterns to avoid: "We sincerely apologize", "is unacceptable, and we take full responsibility", "make sure this is fully resolved for you".

## Operational Actions by Category

| Issue Category | Suggested Internal Actions |
|---------------|---------------------------|
| Product Quality | Inspect current batch, contact supplier, update QC checklist, pull defective stock |
| Shipping/Delivery | Review carrier performance, improve packaging, update tracking notifications, switch carrier for region |
| Customer Service | Review agent interaction, retrain if needed, update response templates, escalate to supervisor |
| App Stability | Create bug ticket for dev team, check crash analytics, prioritize in next sprint, notify affected users of fix |
| App Features | Log feature request, review UX analytics, consider in product roadmap, communicate timeline if planned |
| Price/Value | Review pricing vs. competitors, clarify value proposition in listing, consider promotional offer |
| Returns/Refunds | Process refund immediately, review return policy clarity, simplify return flow |
| Packaging | Review packaging materials, improve protection for fragile items, consider eco-friendly options |
