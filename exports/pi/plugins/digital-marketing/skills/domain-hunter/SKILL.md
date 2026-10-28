---
name: domain-hunter
description: >
  Finds what is available and what it truly costs, promo codes included.
  TRIGGER WHEN: the user wants to buy a domain, check domain prices, compare registrars, find domain deals, or search for .ai/.com names.
---

> `<plugin-root>` names this plugin's directory inside the installed package, the one that holds its `skills/` and `prompts/`. Resolve it once from where this file was loaded, then substitute it into every path below that starts with it.

<daodan_host_binding host="pi">
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

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
Core Pi has no network tool: network fetch and network search run as shell
commands, and a user question is asked in the reply while the run waits for the
answer.
Core Pi supplies neither subagent nor MCP. Isolated workers require pi-subagents:
pi install npm:pi-subagents. Use that extension's registered subagent schema and
pass the full rendered role body inline. Role skills named <plugin>-<role> are
body resources with automatic invocation disabled, not a built-in named agent.
Workflow prompt entries use /<plugin>-<workflow>; ordinary skills use their exact
registered names. If isolation is mandatory and unavailable, stop the phase.
MCP requires pi-mcp-adapter: pi install npm:pi-mcp-adapter, then register the
generated server command in its supported MCP configuration.
Keep the selected package's full local dependency closure. Provision qualified
foreign providers as skills/resources this runtime can load; Pi does not install
another host's marketplace plugin from a Claude install command.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.
Kernel <owner>:<skill> references identify the logical provider. Ordinary Pi
skills retain their source frontmatter name, so resolve the actual registered name
and provider path from the active inventory; do not invent a prefixed native ID.

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

<!-- upstream: ReScienceLab/opc-skills - skills/domain-hunter/SKILL.md -->
<!-- Local drift: Step 3 (Find Promo Codes) uses network search queries instead of upstream Python scripts -->

# Domain Hunter Skill

Help users find and purchase domain names at the best price.

## Workflow

### Step 1: Generate Domain Ideas & Check Availability

Based on the user's project description, generate 5-10 creative domain name suggestions.

**Guidelines:**
- Keep names short (under 15 characters)
- Make them memorable and brandable
- Consider: `{action}{noun}`, `{noun}{suffix}`, `{prefix}{keyword}`
- Common suffixes: app, io, hq, ly, ify, now, hub

**CRITICAL: Always check availability before presenting domains to user!**

Use one of these methods to verify availability:

**Method 1: RDAP check (most reliable)**
```bash
# Prints the HTTP status: 404 = AVAILABLE, 200 = TAKEN, anything else = UNKNOWN
curl -s -o /dev/null -w "%{http_code}" "https://rdap.org/domain/{domain}.{tld}"
```

A failed command (no network, timeout, rate limit, empty output, any other status) means **UNKNOWN**. Never read a failure as TAKEN and never read it as AVAILABLE. Report UNKNOWN domains as unverified and retry them.

A `404` is only evidence of availability for a TLD that has an RDAP service. `.io`, `.co` and `.it` have none in the IANA bootstrap, and `rdap.org` answers `404` for them too, so `google.io` reads as AVAILABLE. For those TLDs the curl check proves nothing: use the Domain Checker Script (Method 2) or confirm with Method 1b. `rdap.org` also answers `429` after a short burst, so do not loop it over many names; the Domain Checker Script below talks to each registry directly.

**Method 1b: whois confirmation (only where the binary exists)**
```bash
whois {domain}.{tld}
```
Use this to confirm an RDAP result, not to replace it. A registration record means TAKEN. "No match" or "not found" in a successful response means AVAILABLE. A missing binary, a non-zero exit, or empty output means UNKNOWN, not TAKEN. Parked-domain banners can contain the word "available", so read the record itself rather than grepping for substrings.

**Method 2: Registrar search page, read headless by the script**
A TLD with no RDAP service is verified on a registrar's search page, and the Domain Checker Script below does that itself with Patchright in headless mode (Gandi's page, a throwaway browser, no window). Run the script; do not run `open`, `start` or `xdg-open` on a registrar URL and do not drive a visible browser for a domain check, because each of those opens the user's own browser. Spaceship and Porkbun cannot be read headless (a Cloudflare bot check and an anti-bot wall), so do not build a check on them.

**Method 3: Registrar links for the user**
When the script left a domain UNKNOWN, give the user these as links to click in the report, never open them yourself:
- https://www.namecheap.com/domains/registration/results/?domain={domain}
- https://www.dynadot.com/domain/search?domain={domain}

**IMPORTANT:**
- Only present domains that are confirmed AVAILABLE
- Mark any uncertain domains with "(unverified)". An UNKNOWN result is unverified, not taken, so never discard a candidate on it
- Present suggestions to user and **wait for confirmation** before proceeding
- Ask user to pick their preferred options or provide feedback
- Only move to Step 2 after user approves domain name(s)

### Step 2: Compare Prices

Use **network search** to find current prices:

```
Search query: "cheapest .{tld} domain registrar 2026 site:tld-list.com"
Search query: ".{tld} domain price comparison tldes.com"
```

**Key price comparison sites:**
- tld-list.com/tld/{tld}
- tldes.com/{tld}
- domaintyper.com/{tld}-domain

### Step 3: Find Promo Codes

Use **network search** to search registrar social accounts and communities for promo codes:

**Twitter/X search** - search registrar accounts for recent promos:
```
Search query: "site:x.com from:{registrar} promo code"
Search query: "site:x.com {registrar} promo code coupon"
```

**Reddit search** - search domain communities for deals:
```
Search query: "site:reddit.com r/Domains {registrar} promo code"
Search query: "site:reddit.com r/Domains {registrar} coupon discount"
```

**Major registrar Twitter handles:**
- @spaceship, @Dynadot, @Namecheap, @Porkbun, @namesilo, @Cloudflare

### Step 4: Recommend

Present final recommendation in this format:

```
## Recommendation

**Domain:** example.ai
**Best Registrar:** Spaceship
**Price:** $68.98/year (2-year minimum = $137.96)
**Promo Code:** None available for .ai
**Purchase Link:** https://www.spaceship.com/

### Price Comparison
| Registrar | Year 1 | Renewal | 2-Year Total |
|-----------|--------|---------|--------------|
| Spaceship | $68.98 | $68.98  | $137.96      |
| Cloudflare| $70.00 | $70.00  | $140.00      |
| Porkbun   | $71.40 | $72.40  | $143.80      |
```

## Important Notes

1. **Premium TLDs** (.ai, .io) rarely have promo codes - wholesale costs are too high
2. **.ai domains** require 2-year minimum registration
3. **Cloudflare** offers at-cost pricing with no markup
4. **Renewal prices** often differ from registration - always check both
5. **WHOIS privacy** is free at most registrars (Cloudflare, Namecheap, Porkbun)

## Domain Checker Script

For bulk availability checks, use the domain checker script:

```bash
python "<plugin-root>/skills/domain-hunter/scripts/domain_checker.py" name1 name2 --tlds .com,.io
```

The script checks availability via RDAP. No API key is needed, and RDAP uses the standard library only. It defaults to `.com`, `.app`, `.io`, `.co`; pass `--tlds` to override. Each line reports `AVAILABLE`, `TAKEN`, or `UNKNOWN`, and UNKNOWN means the lookup failed rather than that the domain is free.

- **Registry direct.** It reads the IANA RDAP bootstrap once and sends each lookup to the registry that runs the TLD (Verisign for `.com`, Google for `.app`), not through `rdap.org`.
- **Parallel.** Lookups run in a thread pool: `--workers N`, default 8, at most 16. At most four are in flight per registry host, and a `429` or `5xx` from a host slows every worker aimed at it. Results print in request order.
- **No RDAP service, read headless.** A TLD absent from the bootstrap (`.io`, `.co`, `.it`) cannot be read from a registry, so the script reads Gandi's search page with Patchright in headless mode: one throwaway browser started on the first such domain, a temporary profile, no visible window, closed at the end. The line says `(Gandi page, headless Patchright)`; the registry itself was not read, so say that in the report. The verdict is accepted only when the page names the exact domain asked about: for a TLD Gandi does not sell it searches another name (`example.gov` becomes `examplegov.com`) and reports that one as available, which the script prints as UNKNOWN. `--no-registrar` skips this step.
- **Patchright is needed for that step.** Install with `pip install patchright && patchright install chromium`. Without it, or when the page does not load (Gandi sits behind a bot check at times), those domains print `UNKNOWN` with the reason and the run continues. That is a missing dependency to report, not a pass: never read it as available, and never fall back to opening the user's own browser.
- **Exit status.** `2` when every result is UNKNOWN, `0` otherwise.

If the script cannot run at all, fall back to the RDAP curl check (Step 1, Method 1) with its TLD caveat, or network search queries.

## References

- [references/registrars.md](./references/registrars.md) - Detailed registrar comparison
- [references/spaceship-api.md](./references/spaceship-api.md) - Spaceship API for automated domain operations
