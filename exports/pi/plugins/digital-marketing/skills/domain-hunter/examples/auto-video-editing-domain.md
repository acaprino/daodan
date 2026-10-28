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

<!-- upstream: ReScienceLab/opc-skills - skills/domain-hunter/examples/auto-video-editing-domain.md -->
# Domain Hunter Example: Finding a Domain for Auto Video Editing Project

This is a complete conversation example showing how the domain-hunter skill helps users find and purchase domain names at the best price.

---

## Conversation

### User

> I am working on an auto video editing project. I need to buy a new domain. Please find one for me.

### Assistant

I'll help you find a domain for your auto video editing project. Let me generate some creative domain name suggestions and check their availability.

**Checking domain availability via RDAP:**

```bash
for domain in "autoedit.io" "clipcraft.io" "videoedit.ai" "cutflow.io" "autocuts.io" "editsnap.io" "vidflow.ai" "clipflow.io" "autoclipper.io" "smartcut.io"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://rdap.org/domain/$domain")
  case "$code" in
    404) echo "Checking $domain... -> AVAILABLE" ;;
    200) echo "Checking $domain... -> TAKEN" ;;
    *)   echo "Checking $domain... -> UNKNOWN (lookup failed, retry)" ;;
  esac
done
```

Any status other than 404 or 200 is UNKNOWN. A failed lookup is never reported as TAKEN or AVAILABLE.

**Results - First Batch:**
```
Checking autoedit.io...   -> TAKEN
Checking clipcraft.io...  -> TAKEN
Checking videoedit.ai...  -> TAKEN
Checking cutflow.io...    -> AVAILABLE
Checking autocuts.io...   -> AVAILABLE
Checking editsnap.io...   -> AVAILABLE
Checking vidflow.ai...    -> TAKEN
Checking clipflow.io...   -> TAKEN
Checking autoclipper.io...-> AVAILABLE
Checking smartcut.io...   -> TAKEN
```

**Results - Second Batch:**
```
Checking autovidz.io...   -> AVAILABLE
Checking clipauto.io...   -> AVAILABLE
Checking videotrim.ai...  -> AVAILABLE
Checking cliphero.io...   -> AVAILABLE
Checking quickclip.io...  -> TAKEN
Checking autosnip.io...   -> AVAILABLE
Checking vidauto.io...    -> TAKEN
Checking clipmagic.io...  -> TAKEN
Checking autorender.io... -> TAKEN
Checking editbot.io...    -> AVAILABLE
```

Here are the **available domain suggestions** for your auto video editing project:

## Available Domains

| Domain | Notes |
|--------|-------|
| **cutflow.io** | Short, memorable - "cut" + "flow" for editing workflow |
| **autocuts.io** | Direct - auto video cuts |
| **editsnap.io** | Quick, snappy editing |
| **autoclipper.io** | Descriptive - auto video clipping |
| **autovidz.io** | Casual/trendy - auto videos |
| **clipauto.io** | Simple - clip automation |
| **videotrim.ai** | .ai TLD - video trimming |
| **cliphero.io** | Brandable - hero for clips |
| **autosnip.io** | Short clips/snips |
| **editbot.io** | Bot/AI angle for editing |

**My top picks:**
1. **cutflow.io** - Short (7 chars), professional, memorable
2. **autocuts.io** - Clear purpose, good branding
3. **videotrim.ai** - .ai TLD fits AI/auto theme well

**Which domain(s) would you like me to check prices for?** Once you pick your favorites, I'll compare prices across registrars and look for promo codes.

---

### User

> cutflow.io looks good, I need to know where can I get the cheapest price to buy it? Also, is there any promo code?

### Assistant

*Searching Twitter/X and Reddit for promo codes...*

**Step 1: Web Search for Price Comparison**

Fetched data from https://tld-list.com/tld/io showing current .io domain prices:

| Registrar | Registration | Renewal | Notes |
|-----------|--------------|---------|-------|
| Spaceship | $14.98 | $46.58 | Promo code **IO85** (85% off, limit 1) |
| Sav | $14.99 | $38.95 | No promo needed |
| Dynadot | $28.89 | $47.70 | - |
| Regery | $28.99 | $47.99 | - |
| Gandi.net | $31.99 | $69.99 | - |

**Step 2: Twitter/X Search for Promo Codes**

```
Search query: "site:x.com from:spaceship promo code"
```

**Results from @spaceship:**
- @spaceship: "Feel free to use the SPSR86 promo code for the disc"
- @spaceship: "Yes, you are right. You can use this promo c"

```
Search query: "site:x.com from:Dynadot promo code"
```

**Results from @Dynadot:**
- @Dynadot: "Transfer your .COM domains to Dynadot for just $10.49 with..."
- @Dynadot: "We did have a .com promo code in April a..."

```
Search query: "site:x.com from:Namecheap promo code"
```

**Results from @Namecheap:**
- @Namecheap: "If you are a new customer, you can get..."
- @Namecheap: "For new users, we've got our NEWCOM598 code at..."

**Step 3: Reddit Search for Promo Codes**

```
Search query: "site:reddit.com r/Domains spaceship domain promo code"
```

**Results from r/Domains:**
- Domain pricing question: Cloudflare vs Spaceship renewals
- Best registrar for a throwaway .com domain
- Spaceship Buyer Hub

---

## Final Recommendation

**Domain:** cutflow.io

### Price Comparison

| Registrar | Year 1 | Renewal | Notes |
|-----------|--------|---------|-------|
| **Spaceship** | **$14.98** | $46.58 | Use promo code **IO85** (85% off, limit 1) |
| Sav | $14.99 | $38.95 | No promo needed |
| Dynadot | $28.89 | $47.70 | No .io promo found |
| Regery | $28.99 | $47.99 | - |
| Namecheap | $34.98 | $57.98 | 40% off first year |
| Hostinger | $31.99 | $67.99 | - |

### Best Deal

**Winner: Spaceship at $14.98/year** (with promo code **IO85**)

- **Promo Code:** `IO85` (85% off .io registration, limit 1 per customer)
- **Free Features:** DNS, Email Forwarding, WHOIS Privacy
- **Renewal:** $46.58/year (industry standard for .io)

**Purchase Link:** https://www.spaceship.com/

### Alternative if renewal matters

**Sav.com at $14.99/year** with the **cheapest renewal at $38.95/year** - best 3-year value if you plan to keep the domain long-term.

---

**Note:** .io domains have high wholesale costs (~$45), so the first-year promos are significant discounts. Renewal prices are similar across registrars.

---

## Key Takeaways

1. **RDAP checks** are used to verify domain availability before presenting options (404 available, 200 taken, anything else unknown)
2. **Price comparison** from tld-list.com provides up-to-date registrar pricing
3. **network search with site:x.com** searches registrar accounts for promo codes
4. **network search with site:reddit.com** searches r/Domains community for user-shared deals
5. **Final recommendation** includes best price, promo code, and purchase link
