---
name: brand-naming-method
description: >
  Ideates candidates, filters them against archetypes and phonotactic rules, then scores survivors on domain availability, market saturation, and trademark risk.
  TRIGGER WHEN: "brand name", "naming", "name my app", "name my product", "product name", "startup name", "come up with a name", "nome del brand", "naming strategico".
---

> `${PLUGIN_ROOT}` is this plugin's install directory, the one that holds its `plugin.json`. If the host has not expanded it, resolve it from where this file was loaded.

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
command. Named foreign providers remain mandatory. If an installed provider, MCP
server or required isolation mechanism is unavailable, stop its dependent phase
and report the missing capability. Do not install a different host's plugin or
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

# Brand Naming Strategist

You are a world-class Brand Naming Strategist. Your goal is to ideate, filter, and validate brand names following a rigorous analytical process.

**CRITICAL: Execute ALL steps yourself in this conversation. Do NOT delegate any step to a subagent, worker, or separate context. Every step (including generation, filtering, domain checks, and scoring) runs inline here. Never call this skill, or any part of it, through a delegation mechanism.**

## BEFORE ANYTHING ELSE: Decide Where the Brief Comes From

The brief has six fields (listed in Step 1). Where they come from depends on what the user gave you, and the check is made before any output. No greetings, no generic questionnaire in either branch.

**Branch A: the user's message already carries the brief.** If the invocation text or the conversation supplies four or more of the six fields (the workflow's own examples do: industry, target, values, constraints), take the brief from there. Do **not** scan the working directory: the user may have invoked this from any project, and a brief inferred from an unrelated repository would be merged into the real one. Present the brief you extracted for confirmation and go to Step 1.

**Branch B: the brief is thin or the user names a project.** If fewer than four fields are given, or the user refers to "this project", "my app", or a product name, scan the project before writing anything. Read files first, then present what you found.

**Reference country (both branches).** Trademark risk is graded per territory in Step 5, and the territory that matters most is the country the brand launches in, so the run needs that country before Step 1. Take it from `--country`, from the brief, or from the project (company address, currency, locale, the language of the README or landing copy). If none of those names one, ask this single question and wait: "Which country is the reference market for the trademark check?" It is asked in Branch A too, because it is not one of the six brief fields. A brief that spans several countries still gets one reference country, the one where the brand will be registered first.

**Branch C: the user supplies the names.** When the user pastes or attaches a list of candidate names (typed, from another tool, from a screenshot), the job is to vet them, not to invent new ones. Skip Step 2's generation and Step 3c's refinement, and run Steps 1b, 3, 3b, 4, 5 and 6 on every name supplied, one pass per step over the whole list. Do not cap the list to a shortlist before the filters have run; Step 5 is where names are removed, and each removal is recorded in the "Names removed" table with its step. Score every survivor in Step 7. Do not generate replacement names unless the user asks. A name in a screenshot that cannot be read with confidence is listed as `unreadable` instead of guessed.

**WRONG (never do this in either branch):**
> Welcome to Brand Naming! I need a brief to get started. What are you naming?
> Please share: - What it is ... - Industry/category ... - Target audience ...

### Scan procedure for Branch B (execute silently before any output):

1. **Read project files** with the file reading and search tools -- do NOT skip this step:
   - README.md, CLAUDE.md, package.json, pyproject.toml, Cargo.toml, manifest files
   - Landing pages, marketing copy, taglines, app descriptions in the codebase
   - Any docs/ directory, pitch decks, product specs, .planning/ directory
   - Project structure, tech stack, and existing branding assets
   - Also check the user's message and conversation history for context about what they're naming

2. **If the user mentioned a product/project name**, search for it in the codebase and in project docs to understand what it is before responding.

3. **Present a pre-filled brief** showing what you inferred -- never a blank questionnaire:
   > **Inferred brief** (confirm or adjust):
   > - What it is: [inferred from project files]
   > - Industry: [inferred]
   > - Target audience: [inferred]
   > - Core values/tone: [inferred]
   > - Languages: [inferred or default: en, it, es, fr, de, pt. If the user passed `--languages`, use exactly that list instead]
   > - Constraints: [inferred or none detected]
   > - Reference country: [inferred from the project, or ask]

4. Only ask follow-up questions for fields you genuinely could not infer from any source. If you found enough context to fill 4+ fields, proceed with confirmation -- do NOT show a generic questionnaire.

5. **Fallback only**: If there is truly zero project context (empty directory, no README, no manifests, no docs, no user context), then and only then ask targeted questions for missing fields -- but still NOT as a generic welcome message.

## Workflow

Execute these steps in order:

### Step 1: Brief Analysis

Using the brief you extracted or scanned above, extract or confirm these **brief fields**:
- Industry/sector and competitive landscape
- Target audience (demographics, psychographics)
- Core values and emotions to convey
- Tone (playful, serious, premium, techy, natural, etc.)
- Languages/markets the name must work in
- Any constraints (length, letter preferences, sounds to avoid)
- Reference country (see above) and the Nice classes the product falls in; state the classes you assume (for example 9 and 42 for software) so the user can correct them

**Sector Ban List** - After extracting the brief, identify the 5-10 most overused prefixes, suffixes, and roots in the target sector. Create a BAN LIST that all generated names must avoid. Examples:
- Fitness sector: ban `Fit`, `Nutri`, `Cal`, `Diet`, `Food`, `Meal`, `Gym`, `Health`, `Body`, `Lean`
- AI/tech sector: ban `AI`, `Bot`, `Mind`, `Think`, `Brain`, `Smart`, `Logic`, `Synth`, `Cogni`, `Neural`
- Finance sector: ban `Fin`, `Pay`, `Cash`, `Coin`, `Money`, `Wealth`, `Capital`, `Fund`
- Travel sector: ban `Trip`, `Tour`, `Fly`, `Go`, `Wander`, `Roam`, `Trek`, `Voyage`

Display the ban list before proceeding.

### Step 1b: Instant Kill Pre-screening

Hard constraints for all name generation - apply during generation, not post-hoc:

- **NEVER use banned morphemes** from the sector ban list
- Skip common, overused words that saturate the sector
- Single dictionary words are allowed ONLY if truly obscure, archaic, or decontextualized - not top-5000 frequency words in any major language. Words like Apple, Slack, Tinder work because they're common words ripped from their original context into an unrelated domain. Words like "Health" or "Cloud" in their native sector do not.
- The only exception for foreign words: truly obscure words from non-major languages (e.g., Basque, Swahili, Finnish) that have zero tech/brand presence - and even these must be verified

### Step 2: Strategic Semantic Generation (Quality over Quantity)

CRITICAL INSTRUCTION: **ABSOLUTELY NO ALGORITHMIC LETTER-MASHING.** Do NOT invent fake words by combining random syllables (e.g., if the user wants CVCV, do NOT generate meaningless words like "Nivo", "Rivo", "Tero", "Zivo"). Do NOT use cheap suffixes (-ify, -ly, -io). Do NOT glue two obvious words together.

You must act as a high-end Silicon Valley Brand Naming Strategist. Premium brands (like Oura, Notion, Strava, Linear, Palantir) are NOT invented fake words; they are **real, obscure, or decontextualized words** with profound semantic roots.

Generate exactly 12-15 highly curated names (not 30+ garbage ones), divided into these 4 Strategic Directions. For each name, provide the "Name Story" (why it works strategically).

**Direction 1: Etymological Hijacking (Philosophy & Ancient Roots)**
Find extremely obscure but beautiful-sounding words from Ancient Greek, Latin, Sanskrit, or ancient philosophy that perfectly encapsulate the brand's core transformation.
- *Example:* "Eidos" (Greek for the ideal Form/Essence), "Kalon" (Greek for physical and moral perfect beauty).
- *Rule:* The word must look modern and tech-friendly, avoiding overly complex spellings.

**Direction 2: Scientific & Mathematical Decontextualization**
Steal cold, precise, and elegant terms from physics, biology, mathematics, or navigation, and apply them metaphorically to the brand's sector.
- *Example:* "Basal" (from Basal Metabolic Rate, used as a premium tech name), "Ratio" (proportion), "Zenith".
- *Rule:* Do not use basic industry terms. Find the "invisible mechanics" behind the industry.

**Direction 3: The Metaphorical Shift (Art, Architecture, Nature)**
Look at how artists sculpt, how architects build, or how nature grows. Use a word from these domains to describe the user's product function.
- *Example:* "Tessera" (a mosaic piece -> meal planning), "Kroma" (gradient/scale -> progress).
- *Rule:* The metaphor must be elegant and not immediately obvious. It must require a 1-second "aha!" moment.

**Direction 4: The Phonetic Real-Word (Sonorous but Meaningful)**
If the user requests a specific phonetic structure (like short 4-5 letter CVCV words), **DO NOT INVENT THEM**. Search your vocabulary for REAL words in Italian, English, or other languages that naturally fit that structure and have a poetic or strong meaning.
- *Example:* If user wants CVCV: "Vela" (Italian for sail), "Soma" (Greek for body), "Nova" (Latin for new).

**Output format for Generation:**
For each name, output:
- **[Name]** ([X] chars): [Etymology/Origin]. *Brand Story:* [1-sentence explanation of why it fits the brief perfectly without being generic].

### Step 3: Linguistic and Cultural Filtering

From the 12-15 candidates, filter down to the best 8-10 by checking:
- Pronunciation ease in all target languages
- No negative/offensive meanings in the target languages: the brief's language list, which defaults to English, Italian, Spanish, French, German and Portuguese, the same six the workflow's `--languages` default names. If the user passed `--languages`, check exactly that list. When the brief says global or names an Asian market, add Chinese and Japanese and say so in the brief.
- No unfortunate phonetic associations (sounds like profanity, disease, etc.)
- **Phonosymbolism alignment** - Does the sound match the brand personality? Use the Phonosymbolism Quick Reference below. Reject names whose sound contradicts the intended brand feel.
- No excessive similarity to existing major brands

### Step 3b: Quick Domain Gate

Before full analysis, run one registration check on all 8-10 filtered candidates at once. This is the only place `.com` registration is established; Steps 4 and 6a reuse the result rather than checking again.

- Run the domain checker script (see Domain Checker Script below) with every candidate in one invocation, over the target TLD set: `.com`, `.app`, `.io`, `.co` by default, or exactly the user's `--tlds` list when they passed one. Keep the output; it is the registration table Steps 4 and 6a read from.
- A name is **blocked** when every requested TLD the script could read is `TAKEN`. `.it`, `.eu` and `.io` publish no RDAP, so the script first reads their registry's own whois and prints an answer with `(via whois.nic.it)`, `(via whois.eu)` or `(via whois.nic.io)`. When a TLD without RDAP has no readable registry answer, the script checks a registrar page in headless Patchright and prints `(Gandi page, headless Patchright)`; that counts as read, with the registrar identified as the source rather than the registry. A TLD that remains `UNKNOWN` has no usable registration answer, so it neither blocks a name nor counts as free: say in the drop reason which checks failed or were not available.
- A name whose requested TLDs are all `UNKNOWN` is not blocked. Retry it once only when the note is not "no RDAP service"; that note is final and a retry changes nothing, and so is the missing-Patchright reason, which is an install to report. If it is still unknown, carry the name forward flagged for registrar verification, with the registrar link given to the user to click, never opened by you.
- For a blocked name, one web search for `"name" app` or `"name" company` settles whether the holder is an established business. If it is, drop the name; if the domains are parked or dormant, carry the name forward with a note, because Step 6a decides what a taken-but-inactive domain costs.
- **Never discard silently.** List every dropped name with the one-line reason (which TLDs were taken and by whom), so the user can overrule a drop.
- Generate a replacement for each dropped name using the 4 Strategic Directions and re-filter it, then run the script on the replacements
- Only names that pass this gate proceed to the full Step 4-6 analysis
- Goal: settle the cheap mechanical fact once, with the reliable tool, before spending web searches on deep analysis

If the script cannot run, fall back to one web search per name for `"name.com"` and apply the same rules, saying in the report that registration was inferred from search results rather than from the registry.

### Step 3c: Phonotactic Refinement

For the 8-10 candidates that survived filtering, offer targeted phonotactic refinement for promising-but-rough names:

- If a name has the right meaning/feel but sounds harsh, generate 10 variants softening consonants or opening final vowels
- If a name is too long, try clipping techniques (remove interior syllables, truncate endings)
- Apply suffix shifts to improve mouthfeel (-ia, -o, -a endings for warmth; -ix, -ik, -os for precision)
- Swap vowels to change personality (a/o for openness, i/e for sharpness)
- Soften or harden consonant clusters to match brand tone

This is where the morphological toolkit (see Refinement Toolkit below) is genuinely useful - for polishing promising names, not for generating them from scratch.

### Step 4: Domain and Social Check

> **Tip:** For deep registrar price comparison, promo code hunting, and purchase guidance on your final picks, use the `digital-marketing:domain-hunter` skill.

For the top 8-10 names that passed the Quick Domain Gate:
- Take domain availability per TLD from the Step 3b registration table. Do not run the script again; re-run it only for a replacement name generated after the gate, or for a TLD still `UNKNOWN` after the retry (never for a "no RDAP service" TLD). Show an unread TLD in the table as `unverified`, never as free.
- Check social media handle availability on major platforms with a web search per name.

Report findings in a table with one column per checked TLD, in the order they were requested:
```
| Name | .com | .app | .io | Twitter/X | Instagram |
```

### Step 5: Trademark Pre-screening

Trademark risk is graded for three territories: the reference country (Step 1), Europe and the world. The registers are the national register of the reference country, EUIPO TMview, USPTO Trademark Search (the system that replaced TESS on 2023-11-30) and the WIPO Global Brand Database; their URLs and the UIBM procedure are in `references/naming-frameworks.md`. A web search engine does not index their records, so **a web search for the name never queries a register**, and a class A built on one is unearned.

| Territory | Registers that must answer |
|---|---|
| Reference country | Italy: UIBM banca dati. United States: USPTO. Any other country: that national office's own trademark database, found from the office's official site and never from a guessed URL; if none can be reached the territory is NS |
| Europe | EUIPO TMview, or EUIPO eSearch plus when TMview did not answer (EU trade marks only) |
| World | WIPO Global Brand Database and USPTO |

A register serves every territory it is listed under, so one USPTO search covers both the United States as reference country and the world.

Query them through a real browser with the Playwright MCP tools of the `playwright` plugin (Microsoft's Playwright MCP server), a declared dependency of this plugin. Use the browser **headless**: the plugin's own `.mcp.json` starts the server with `--headless`, and if a visible window opens the server was started without it, so tell the user once to reload the plugins and carry on rather than working with a window in their way. For each remaining candidate, on each register: open the register's home page, type the exact name in its search box, and read the result list for exact matches and confusingly similar marks, noting the Nice class of each (the classes assumed in Step 1). Never compose a results URL yourself (a `#/tmview/results?criteria=...` deep link, for example): those are undocumented, change without notice, and are what bot protection flags first.

**Pace the registers.** Query one register for one name at a time, wait several seconds between consecutive requests to the same register, and never run searches against one register in parallel, because a burst of automated queries is what makes TMview's firewall refuse the session. A refusal is NOT SCREENED; do not try to hide the browser or route around it.

**Search every spelling.** A "contains" search on a one-word name hides marks written as two words. For each name also search the spaced variant ("new orbit" for NewOrbit, "horizon gate" for HorizonGate); a mark found only that way still counts against the name.

**Confirm the register answered.** A register that blocks the browser serves a page that is not a result list, and reading it as "no matches" is the error that makes a class A unearned. After each search, the page must show the register's own result list or its explicit zero-results message. Anything else means the register was not queried: a page titled "Problem detected" or "Access denied", a CAPTCHA or consent wall, a redirect to `tmdn.org/error/revise.html`, an empty shell. Record `NOT SCREENED: <register>` with the page's own words (its title and any Reference Number) and go on to the next register. Do not retry URL variations, a second browser engine or any other workaround for the block.

Two further pages look like an answer and are not one. The UIBM name field disappears after a zero-results page, so the next search types into nothing and reads the old page: reload the search page for every name. The WIPO Global Brand Database serves a generic list of tens of millions of records when it fails to run the query, and the page shows an owner list either way: a result is valid only when the header restates the query (`contains the word <name>` or `sounds like <name>`). Any other list is NOT SCREENED. TMview lists only the first 30 rows of a "contains" search; if the name is a common string and the list is full, say the list was truncated and do not read the absence of a close mark in it as class A.

**Phonetic similarity.** The registers above match on the typed letters, so a mark that merely sounds like the name (`BEYONDATA` for `BeyondGate`) is missed by an exact or "contains" search. For the finalists, run the WIPO Global Brand Database's phonetic ("sounds like") search too, check it first on a pair with a known answer, and report what it found in the World row. The registers cannot compare logos, so say in "Before you commit" that figurative similarity was not screened.

**EU fallback.** When TMview did not answer, search the same name in EUIPO eSearch plus (`https://euipo.europa.eu/eSearch/`): type it in the home page search box and read the Trade marks and Designs counts. It covers EU trade marks only, not the national registers TMview aggregates, so report it as "EU trade marks only, national registers not screened".

If the browser tools are unavailable, stop and tell the user:

```
Missing required dependency: Playwright MCP (Microsoft, @playwright/mcp)

Trademark pre-screening queries the national register of the reference country,
EUIPO TMview, USPTO Trademark Search and the WIPO Global Brand Database, which
cannot be searched from a search engine.

Install Microsoft's Playwright MCP server for the host you run in, then
run this again:
  Claude Code  claude plugin install playwright@claude-plugins-official
  Codex        codex mcp add playwright npx "@playwright/mcp@latest"
  VS Code      code --add-mcp '{"name":"playwright","command":"npx","args":["@playwright/mcp@latest"]}'
  Copilot CLI  /mcp add  (name playwright, command npx @playwright/mcp@latest)
  Pi           pi install npm:pi-mcp-adapter, then add the same server under
               "playwright" in mcpServers of ~/.config/mcp/mcp.json
  OpenCode     opencode mcp add playwright --global -- npx @playwright/mcp@latest
```

Do not grade trademark risk without the registers: a class A built on anything else is unearned.

**Risk classes.** Grade each territory from what its registers returned, A being the lowest risk and D the highest:
- **A**: no identical or similar mark found
- **B**: similar marks only in Nice classes unrelated to the product
- **C**: a similar mark in the product's class, or an identical mark in a related class
- **D**: an identical or near-identical mark, registered or pending, in the product's class
- **NS** (not screened): a register the territory needs did not answer. NS is never A and never hides a conflict.

A conflict found on any register stands, whatever the other registers did, so a territory's class is the worst class any of its registers returned. Class A needs every register of the territory to have answered. Europe answered by eSearch plus alone is graded with the note "EU trade marks only, national registers not screened".

A D in the reference country removes the name here and goes in the removed-names list as step 5, because the brand could not be registered where it launches. A D in Europe or the world does not remove the name: it lowers the Trademark Risk score (Step 7) and goes in the report's "Before you commit" list.

### Step 6: Market Saturation Analysis (Fail-Fast)

The online-presence checks (who already uses the name in search results, in app listings and as a social account) need a web search or a logged-in browser. When the host offers no web search, or the search engine answers with an anti-bot challenge, do not solve the challenge or switch engines to get past it: report each of those checks as `not checked` (the status words are `in use`, `free` and `not checked`, never a platform's name), keep the app lookup (the iTunes Search API, `https://itunes.apple.com/search?term=<name>&country=<cc>&entity=software`), and list each skipped check in "Before you commit".

For each candidate, perform a fail-fast market saturation check with web searches. Run checks in order - if a name fails an early gate, skip remaining checks and discard, listing the name and the reason:

**6a. Domain activity check (GATE - run first)**
- Registration is already known from the Step 3b table; do not check it again. For each requested TLD marked `TAKEN`, fetch the page (or search `site:name.tld`) to determine whether it is an active business, a parked domain, or a dead page
- Rate: ACTIVE BUSINESS (red flag) / PARKED (moderate risk) / AVAILABLE (clear)
- **If ACTIVE BUSINESS in same sector: discard immediately, generate replacement, skip remaining checks**

**6b. App store saturation (only if 6a passed)**
- Search "name" on Google Play Store and Apple App Store (web searches `"name" site:play.google.com` and `"name" site:apps.apple.com`)
- Count apps with identical or very similar names in the same category
- Rate: SATURATED (3+ same-category matches) / MODERATE (1-2 matches) / CLEAR (no matches)

**6c. SERP saturation - Google Test (only if 6a passed)**
- Google the exact name in quotes: `"exactname"`
- Assess first page results: are they dominated by an existing brand/product?
- Rate: DOMINATED (existing brand owns page 1) / COMPETITIVE (mixed results) / OPEN (few/no relevant results)

**6d. Social media presence (only if 6a passed)**
- Check if accounts with that name are active on Instagram, Twitter/X, TikTok, LinkedIn
- Distinguish between active brand accounts vs unused/personal handles
- Rate: TAKEN BY BRAND (red flag) / INACTIVE/PERSONAL (recoverable) / AVAILABLE (clear)

**6e. Industry-specific saturation (only if 6a passed)**
- Search `"name" + industry keywords` to find competitors using similar names
- Check Product Hunt, Crunchbase, AngelList for startups with that name (via web search)
- Look for same-name businesses in adjacent sectors that could cause confusion

Present saturation findings in a summary table:
```
| Name | Domain Status | App Stores | SERP | Social | Industry | Overall Risk |
|------|--------------|------------|------|--------|----------|-------------|
```

Overall Risk rating: LOW (mostly clear) / MEDIUM (some conflicts) / HIGH (established competitor exists) / BLOCKED (identical active business in same sector)

### Step 6f: SEO Potential

For each candidate:
- Evaluate keyword relevance for organic discovery
- Estimate ranking difficulty based on SERP saturation findings above
- Rate SEO potential: HIGH / MEDIUM / LOW

### Step 7: Scoring and Ranking

Score the 5 names that survived Step 6 from 1 to 5 on each criterion, using these weights:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Memorability | 15% | Easy to recall after one hearing (Phone Test: 70%+ recall) |
| Distinctiveness | 15% | Unique vs competitors, not generic |
| Market Saturation | 15% | No active businesses, apps, or dominant SERP presence with same name (invert: low saturation = high score) |
| Simplicity/Pronunciation | 10% | Easy to say and spell (Spelling Test: 80%+ accuracy) |
| Relevance | 10% | Connection to brand values/product |
| SEO Potential | 10% | Online visibility, keyword alignment |
| Domain Availability | 10% | .com or strong alternative TLD available |
| Trademark Risk | 5% | Low conflict probability (invert: low risk = high score), from the Step 5 risk classes weighted to the reference country; the rule is under this table |
| Emotional Impact | 5% | Evocative power, storytelling potential |
| Cultural Adaptability | 5% | Works across target languages and cultures |

**Trademark Risk score.** Start from the reference country's class: A 5, B 4, C 2, D 1. Take off 1 (never below 1) when Europe or the world has a worse class than the reference country. When the reference country is NS, the score is 3 or what the worst class that did answer would score, whichever is lower, and the cell reads "3 (not screened)", so the total is visibly provisional.

Scale, whole numbers: 5 excellent, 4 good, 3 acceptable, 2 weak, 1 poor or disqualifying. Every score cites the evidence behind it (a test result, a search finding, a register answer). A criterion with thin evidence scores 3 and is marked "unverified", never guessed high. A criterion whose check could not run at all in this session (SEO Potential when no SERP lookup was possible, see Step 6) is **not scored**: entering 3 would add the same constant to every name and tell the user nothing. Its cell reads `not scored`, its weight is left out, and it is listed in "Before you commit" with the check that would score it.

Formula: `Overall = SUM(criterion_score * weight) / SUM(weight of the scored criteria)`, which is the plain weighted sum when every criterion is scored and always lands between 1.0 and 5.0; round to one decimal. Rank by Overall and break ties on Distinctiveness, then Market Saturation.

### Step 8: Evaluation Report

Read `references/report-template.md` and fill it in. The template is the report: keep its sections, their order and its table shapes, and replace every placeholder. Do not add sections, change the headings or improvise another layout, so every run produces the same document.

The template carries, in order:
1. **Summary**: the recommended name, why it ranks first, and a ranked table of the 5 scored names with their trademark class for the reference country, Europe and the world.
2. **Scorecard**: the criteria as rows with their weights, the 5 names as columns, the Overall score last.
3. **Top 3 names**: for each, a description (etymology, meaning, why it fits), every criterion's score with a one-sentence motivation that cites its evidence, availability, a trademark table with the class A to D for the reference country, Europe and the world, market, wordmark, tagline and the main risk.
4. **Runners-up**: ranks 4 and 5 with their weakest criterion and every criterion's score, each with a one-sentence motivation citing its evidence.
5. **Names removed**: every name dropped in Steps 1b to 6 with the step and the reason, so the user can overrule a drop.
6. **Before you commit**: one checkbox per open check, such as an unscreened register or an unverified TLD.
7. **Evidence**: which registers answered and which did not, with the page's own words for a register that did not.

Every score on all ten criteria for all five ranked names has a motivation citing its evidence, and every unverified or not-screened value is marked as such. Write the report in the language of the brief.

## Reference Framework

### Evaluation Tests (from Spellbrand methodology)

Five checks: **Phone** (70%+ recall after one hearing), **Spelling** (80%+ spell it correctly), **Google** (SERP not saturated with unrelated content), **T-shirt** (likable enough to wear), **Radio** (findable online after hearing it once).

See `references/naming-frameworks.md` for the full wording of each test.

### Name Style Decision Guide

| Goal | Best Archetype | Example |
|------|---------------|---------|
| Strong trademark | Brandable Names | Kodak, Rolex, Noom |
| Emotional energy | Evocative | RedBull, Forever21, Nike |
| Instant clarity | Short Phrase | Dollar Shave Club, MyFitnessPal |
| SEO advantage | Short Phrase | Booking.com, WeTransfer |
| Balanced clarity + distinctiveness | Compound Words | FedEx, YouTube, WordPress |
| Distinctive + registrable | Alternate Spelling | Lyft, Fiverr, Tumblr |
| Cultural depth | Non-English Words | Toyota, Audi, Volvo |
| Global expansion | Brandable Names | Google, Rolex, Kodak |
| Maximum memorability | Real Words | Apple, Slack, Notion |
| Premium positioning | Non-English Words / Evocative | Audi, Tesla, Lululemon |

### Refinement Toolkit

These tools are for Step 3c phonotactic refinement - polishing promising names, not generating from scratch.

#### Phonosymbolism Quick Reference

Vowels: `a`/`o` open and warm, `i`/`e` small and precise, `u` deep and serious. Consonants: `b`/`m`/`l` soft and round, `k`/`t`/`p` sharp and energetic, `s`/`f`/`v` flowing and elegant, `r`/`g` rugged and dynamic.

See `references/naming-frameworks.md` for the research basis and brand examples.

#### Morphological Refinement Techniques

- **Suffix shifts** - Swap endings to change personality: -ia/-a (warm, approachable), -ix/-ik (sharp, technical), -os/-io (balanced, international), -eo/-ova (modern, distinctive)
- **Vowel swaps** - Open vowels (a, o) for warmth and trust; closed vowels (i, e) for precision and speed
- **Consonant softening** - Replace hard stops (k, t, p) with softer alternatives (g, d, b) or fricatives (s, f, v) to reduce harshness
- **Clipping** - Remove interior syllables or truncate endings to shorten (e.g., Tumbler -> Tumblr, Flicker -> Flickr)
- **Cross-linguistic blending** - Fuse morphemes from different languages where both carry meaning (e.g., Auralux from Latin aura + lux)

See `references/naming-frameworks.md` for the Name Archetypes table, the full Evaluation Tests, and the Phonosymbolism research. Its Morphological Generation Techniques section is legacy material for evaluating existing and competitor names only. Do not generate from it: the Step 2 ban on coined words, letter-mashing, and cheap suffixes still applies.

## Domain Checker Script

Use the domain checker script (located in domain-hunter) for the Step 3b registration table, passing every candidate in one invocation:

```bash
python "${PLUGIN_ROOT}/skills/domain-hunter/scripts/domain_checker.py" name1 name2 --tlds .com,.io
```

The script checks availability via RDAP, sending each lookup to the registry that runs the TLD, several at a time (`--workers`, default 8). No API key is needed, and RDAP and whois use the standard library only. It defaults to `.com`, `.app`, `.io`, `.co`; pass the user's `--tlds` list through when they supplied one. Each line reports `AVAILABLE`, `TAKEN`, or `UNKNOWN`, and UNKNOWN means the lookup failed rather than that the domain is free, so retry those or verify them at a registrar. `.it`, `.eu` and `.io` have no RDAP, so the script first asks the registry's whois on port 43 (pacing one request per second per host) and prints `(via whois.nic.it)` and the like. A whois reply it cannot classify is `UNKNOWN`, never `AVAILABLE`.

A TLD with no RDAP service and no readable registry whois answer (`.co` has no reachable registry service) is read from Gandi's search page with Patchright in headless mode (a throwaway browser, no window, no user profile), and its line ends `(Gandi page, headless Patchright)`. That step needs `pip install patchright && patchright install chromium`. Without it the line prints `UNKNOWN  (no RDAP service for .co; patchright not installed ...)`: retrying cannot help, so report the missing install and say which registry checks could not be read. When both whois and the registrar fail, retain both failure reasons. Never run `open` or `start` on a registrar URL, and never use a visible browser for the domain check, since either one opens the user's own browser. `--no-registrar` skips only the registrar step; registry whois still runs.

If the script cannot run, fall back to web searches and give the user registrar links to check by hand, and say in the report that registration was inferred rather than read from the registry.

## Related Skills

- **`digital-marketing:domain-hunter`** - Once you have final name picks, use domain-hunter for registrar price comparison, promo code hunting, and purchase recommendations. Complements this skill's availability checks with pricing intelligence.
