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

<!-- upstream: ReScienceLab/opc-skills - skills/domain-hunter/references/registrars.md -->
# Domain Registrar Reference

## Recommended Registrars

| Registrar | Best For | Pros | Cons |
|-----------|----------|------|------|
| **Cloudflare** | At-cost pricing | No markup, same renewal price, free privacy | Must add zone first |
| **Spaceship** | Cheapest prices | Often lowest .ai/.io prices, clean UI | Newer company |
| **NameSilo** | Consistent pricing | Low renewal, bulk discounts | Basic UI |
| **Porkbun** | Budget friendly | Good prices, fun branding, free SSL | Limited enterprise features |
| **Namecheap** | Features | Free WhoisGuard year 1, good support | Renewal can be higher |
| **Dynadot** | Domain auctions | Good aftermarket, bulk tools | Interface dated |
| **GoDaddy** | Avoid | Name recognition | High renewal, upsells |

## Price Tiers by TLD

### Premium TLDs (rarely have promos)
- **.ai** - $65-80/year (Anguilla ccTLD, 2-year min)
- **.io** - $35-50/year (British Indian Ocean Territory)
- **.co** - $25-35/year (Colombia)

### Standard TLDs
- **.com** - $9-14/year
- **.net** - $12-16/year
- **.org** - $10-14/year

### Budget TLDs
- **.xyz** - $1-10/year
- **.club** - $1-5/year
- **.site** - $1-5/year

## Registrar Purchase Links

| Registrar | URL |
|-----------|-----|
| Cloudflare | https://dash.cloudflare.com/?to=/:account/domains/register |
| Spaceship | https://www.spaceship.com/ |
| NameSilo | https://www.namesilo.com/ |
| Porkbun | https://porkbun.com/ |
| Namecheap | https://www.namecheap.com/ |
| Dynadot | https://www.dynadot.com/ |

## Twitter Handles for Promo Search

```
@spaceship
@Dynadot
@Namecheap
@Porkbun
@namesilo
@Cloudflare
@GoDaddy
```

## Reddit Communities

- r/Domains - General domain discussion
- r/webhosting - Hosting + domains
- r/Entrepreneur - Sometimes domain deals shared
