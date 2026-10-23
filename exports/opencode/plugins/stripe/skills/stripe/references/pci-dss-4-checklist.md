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

# PCI DSS 4.0 / 4.0.1 for Stripe Merchants

Short version of what changed with PCI DSS 4.0 and what a Stripe merchant on SAQ-A actually has to do. Canonical guidance lives at the PCI SSC and Stripe; this file captures the bits that affect the code you write.

## Scope note: SAQ-A merchants (the common case)

If you use hosted Checkout or Payment Links and **no PAN data ever touches your servers**, you're almost certainly SAQ-A. PCI SSC published a revised SAQ-A in January 2025 that removed Requirements 6.4.3 and 11.6.1 for fully-outsourced merchants and replaced them with an eligibility criterion stating the merchant is still responsible for hardening the *referring page* against script attacks.

If you use Stripe Elements, Payment Element, or Embedded Checkout (anything where Stripe JS runs inside your page), you're likely **SAQ-A-EP** -- the full 6.4.3 and 11.6.1 requirements apply.

Confirm your SAQ type with your acquirer / auditor. Don't self-classify.

## Gotchas

- **6.4.3 (script integrity)** -- every third-party script on a payment page must be authorized, justified, and integrity-checked. Practically: inventory your scripts, add Subresource Integrity (SRI) hashes on `<script>` tags, add a Content Security Policy (CSP) with a strict `script-src`.
- **11.6.1 (change detection on payment pages)** -- detect unauthorized modifications to HTTP headers and script content on payment pages. Practically: a tamper-detection tool (Feroot, Jscrambler, Akamai Page Integrity Manager, Human Security) or a homegrown CSP-report + script-hash pipeline.
- **Deadline context.** PCI DSS 4.0 was effective March 31 2024. The originally "future-dated" requirements (including 6.4.3 and 11.6.1) became mandatory March 31 2025. PCI DSS 4.0.1 is the current point release.
- **12.3.1 (TLS inventory)** -- keep a documented inventory of certificates and cipher suites. Cheap win: use a Qualys SSL Labs scan in your quarterly review cadence.
- **Stripe-hosted means Stripe's problem for those pages, not yours** -- but the page *linking to* Stripe Checkout is still yours. A malicious script on that page can rewrite the link to a phishing target. 6.4.3 and 11.6.1 (or the SAQ-A replacement criterion) apply to that referring page.
- **Dynamic script insertion** -- CSP without `unsafe-inline` breaks a lot of analytics/tag managers. Plan for nonce-based or hash-based CSP early; retrofitting is painful.
- **Don't rely on `defer`/`async` for security** -- they affect load order, not authorization or integrity.
- **SRI breaks on minor vendor bumps.** When a third-party script updates its file (common with analytics), the hash changes. Pin versions or automate hash refresh in CI.

## Concrete checklist

- [ ] Confirm SAQ type (A vs A-EP) with your acquirer.
- [ ] Inventory every `<script>` and external resource on any page that links to or embeds payment UI. Written justification per script.
- [ ] Add SRI hashes to all third-party scripts on those pages.
- [ ] Deploy a strict CSP with `script-src`, `frame-src https://js.stripe.com https://checkout.stripe.com`, `connect-src https://api.stripe.com`, and a CSP report endpoint.
- [ ] Set up change detection (tooling or homegrown with daily script-hash diff).
- [ ] Document TLS versions and cipher suites per public endpoint (Qualys SSL Labs once per quarter).
- [ ] Include the payment page hardening status in your annual SAQ submission.

## Official docs

- PCI DSS 4.0.1 document (registration required): https://www.pcisecuritystandards.org/document_library/
- PCI SSC SAQ A revision (Jan 2025) blog: https://blog.pcisecuritystandards.org/ (search for "SAQ A")
- Stripe PCI compliance guide: https://stripe.com/guides/pci-compliance
- Stripe Elements + PCI docs: https://docs.stripe.com/security/guide
- Stripe CSP guidance (frame/connect sources): https://docs.stripe.com/security/guide (see "content security policy" section)

## Related

- `webhooks-production.md` -- unrelated to PCI, but shares the "what does production-grade actually look like" framing
- `embedded-checkout.md` -- which integration mode puts you in SAQ-A vs SAQ-A-EP
