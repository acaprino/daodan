<daodan_host_binding host="copilot">
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

Copilot binding: repository reads use search, writes use edit, shell execution uses
runCommands and network fetch uses fetch in the adapter's tool allowlist. fetch
retrieves a known URL and does not search: network search needs a search tool
registered in this session. A user question is asked in the reply, and the run
waits for the answer. Custom
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

# Anti-AI Writing Patterns: Detailed Catalog and Specimens

On-demand reference for `text-humanizer:anti-ai-writing-patterns`. Contains before/after specimens, open-point examples, and the full end-to-end report example for the 25 local patterns. Numbering is local, not upstream's. Patterns 11 and 12 remain readability checks, not evidence of AI authorship.

## Content Patterns (1-6)

### 1. Undue Emphasis on Significance, Legacy, and Broader Trends
- **Words to watch:** stands/serves as, is a testament/reminder, a vital/significant/crucial/pivotal/key role/moment, underscores/highlights its importance/significance, reflects broader, symbolizing its ongoing/enduring/lasting, contributing to the, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted.
- **Before:** > The Statistical Institute of Catalonia was officially established in 1989, marking a pivotal moment in the evolution of regional statistics in Spain. This initiative was part of a broader movement across Spain to decentralize administrative functions and enhance regional governance.
- **After:** > The Statistical Institute of Catalonia was established in 1989, as part of a wider move in Spain to decentralize administration and strengthen regional government.

### 2. Undue Emphasis on Notability and Media Coverage
- **Words to watch:** independent coverage, local/regional/national media outlets, trade publications, cited/featured in, was identified by, written by a leading expert, active social media presence.
- **Before:** > Her views have been cited in The New York Times, BBC, Financial Times, and The Hindu. She maintains an active social media presence with over 500,000 followers.
- **After:** > Her views have been cited by The New York Times, the BBC, the Financial Times, and The Hindu, and she has over 500,000 followers on social media.
- **Open point:** name one article and what she argued in it. A list of outlets shows reach, not substance.

### 3. Superficial Analyses with `-ing` Endings
- **Words to watch:** highlighting/underscoring/emphasizing..., ensuring..., reflecting/symbolizing..., contributing to..., cultivating/fostering..., encompassing..., enhancing..., showcasing...
- **Problem:** GPT-4o writes present participial clauses at 5.3 times the human rate (Reinhart et al., PNAS 2025). Cut the rider, or give it a sentence of its own when it carries a fact.
- **Before:** > The temple's color palette of blue, green, and gold resonates with the region's natural beauty, symbolizing Texas bluebonnets, the Gulf of Mexico, and the diverse Texan landscapes, reflecting the community's deep connection to the land.
- **After:** > The temple's colors, blue, green, and gold, symbolize Texas bluebonnets, the Gulf of Mexico, and the Texan landscape.

### 4. Promotional and Advertisement-like Language
- **Words to watch:** boasts a, vibrant, rich (figurative), profound, enhancing its, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking (figurative), renowned, breathtaking, must-visit, stunning.
- **Before:** > Nestled within the breathtaking region of Gonder in Ethiopia, Alamata Raya Kobo stands as a vibrant town with a rich cultural heritage and stunning natural beauty.
- **After:** > Alamata Raya Kobo is a town in the Gonder region of Ethiopia.
- **Open point:** what the town is known for.

### 5. Vague Attributions and Weasel Words
- **Words to watch:** Industry reports, Observers have cited, Experts argue, Some critics argue, several sources/publications; in connection with, connected with/to, in association with, associated with.
- **Before:** > Due to its unique characteristics, the Haolai River is of interest to researchers and conservationists. Experts believe it plays a crucial role in the regional ecosystem.
- **After:** > The Haolai River is of interest to researchers and conservationists.
- **Open point:** "Experts believe it plays a crucial role in the regional ecosystem" was cut. Name the experts or the study, and the role, to restore it.

### 6. Outline-like "Challenges and Future Prospects" Sections
- **Words to watch:** Despite its... faces several challenges..., Despite these challenges, Challenges and Legacy, Future Outlook.
- **Before:** > Despite its industrial prosperity, Korattur faces challenges typical of urban areas, including traffic congestion and water scarcity. Despite these challenges, with its strategic location and ongoing initiatives, Korattur continues to thrive as an integral part of Chennai's growth.
- **After:** > Korattur is a prosperous industrial area of Chennai. It has traffic congestion and water scarcity.
- **Open point:** which "ongoing initiatives", and what makes the location "strategic".

---

## Language and Grammar Patterns (7-12)

### 7. Overused "AI Vocabulary" Words
- **High-frequency AI words:** Additionally (opening a sentence), align with, boasts (meaning "has"), bolstered, crucial, deep dive, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate/intricacies, key (adjective), landscape (abstract noun), meticulous/meticulously, pivotal, robust, showcase, tapestry (abstract noun), testament, underscore (verb), valuable, vibrant.
- **Note:** Density is the tell. "delve", "tapestry" and "testament" belong to 2023-24 models, while "enhance", "emphasizing", "highlighting" and "showcasing" persist in 2025-26 models (Kobak et al., Science Advances 2025).
- **Before:** > Additionally, a distinctive feature of Somali cuisine is the incorporation of camel meat. An enduring testament to Italian colonial influence is the widespread adoption of pasta in the local culinary landscape, showcasing how these dishes have integrated into the traditional diet.
- **After:** > Camel meat is a distinctive part of Somali cuisine. Pasta, a legacy of Italian colonial influence, is widely eaten and has become part of the traditional diet.

### 8. Avoidance of "is"/"are" (Copula Avoidance)
- **Words to watch:** serves as/stands as/functions as/operates as/marks/represents [a], refers to, maintains, boasts/features/offers [a].
- **Before:** > Gallery 825 serves as LAAA's exhibition space for contemporary art. The gallery features four separate spaces and boasts over 3,000 square feet.
- **After:** > Gallery 825 is LAAA's exhibition space for contemporary art. It has four separate spaces and over 3,000 square feet.

### 9. Negative Parallelisms
- **Problem:** "Not only...but...", "It's not just about..., it's...", "Y rather than X", staged reveals ("The result? ...", "Here's the thing:"), arguing with no one ("This isn't about speed").
- **Guard:** keep a contrast that corrects an actual misconception, an attributed objection, or two informative alternatives. A contrast split across sentences has the same test; do not remove its negative half mechanically.
- **Before:** > It's not just about the beat riding under the vocals; it's part of the aggression and atmosphere. It's not merely a song, it's a statement.
- **After:** > The beat under the vocals adds to the aggression and the atmosphere.

### 10. Rule of Three Overuse (**weak alone**)
- Check paragraph-scale parallelism and repeated sentence openings as well as triads. Keep three real items and deliberate rhetorical repetition.
- **Before:** > The event features keynote sessions, panel discussions, and networking opportunities. Attendees can expect innovation, inspiration, and industry insights.
- **After:** > The event has keynote sessions, panel discussions, and time for networking.

### 11. Elegant Variation / Synonym Cycling (**weak alone**)
- This is not diagnostic of AI writing. Change only variation that makes the referent unclear; ordinary synonym variation, especially in Italian, stays.
- **Before:** > The protagonist faces many challenges. The main character must overcome obstacles. The central figure eventually triumphs. The hero returns home.
- **After:** > The protagonist faces many challenges and must overcome obstacles, but eventually triumphs and returns home.

### 12. False Ranges (**weak alone**)
- This is not diagnostic of AI writing. Keep an intelligible expression of breadth; edit only when the range obscures what is being claimed.
- **Before:** > Our journey through the universe has taken us from the singularity of the Big Bang to the grand cosmic web, from the birth and death of stars to the enigmatic dance of dark matter.
- **After:** > We have covered the Big Bang, the cosmic web, the life cycle of stars, and dark matter.

---

## Style, Communication, and Filler Specimens (13-24)

### 13. Em Dash and Hyphen Overuse
- This is a punctuation pass, not a ban on compound words. Keep dictionary-required hyphens (`third-party`, `cross-functional`), technical names, ranges, dialogue, code, commands, paths and URLs. Do not apply English compound-modifier rules to Italian.
- **Before:** > The term is primarily promoted by Dutch institutions — not by the people themselves. You don't say "Netherlands, Europe" as an address — yet this mislabeling continues — even in official documents.
- **After:** > The term is primarily promoted by Dutch institutions, not by the people themselves. You don't say "Netherlands, Europe" as an address, yet this mislabeling continues, even in official documents.
- **Before:** > She built the prototype in two weeks--a record for the team--and launched it to beta users immediately.
- **After:** > She built the prototype in two weeks (a record for the team) and launched it to beta users immediately.

### 14. Overuse of Boldface
- **Before:** > It blends **OKRs (Objectives and Key Results)**, **KPIs (Key Performance Indicators)**, and visual strategy tools such as the **Business Model Canvas (BMC)** and **Balanced Scorecard (BSC)**.
- **After:** > It blends OKRs (objectives and key results), KPIs (key performance indicators), and visual strategy tools such as the Business Model Canvas (BMC) and the Balanced Scorecard (BSC).

### 15. Inline-Header Vertical Lists
- **Before:**
  > - **User Experience:** The user experience has been significantly improved with a new interface.
  > - **Performance:** Performance has been enhanced through optimized algorithms.
  > - **Security:** Security has been strengthened with end-to-end encryption.
- **After:** > A new interface improves the user experience, optimized algorithms improve performance, and end-to-end encryption strengthens security.

### 16-24. Additional Specimens
- **16. Title Case in Headings (**weak alone** in English, strong in Italian):** `## Strategic Negotiations And Global Partnerships` -> `## Strategic negotiations and global partnerships`.
  Headings written only for effect should name their subject, but preserve proper names, titles and linked anchors; do not break docs links to improve a heading.
- **17. Emojis (**weak alone**):** Strip decorative line-initial emojis only when the weak-alone test applies. Example in an otherwise formulaic heading: `## 🚀 Deployment` -> `## Deployment`. A meaningful status symbol is not decoration.
- **18. Curly Quotation Marks (**weak alone**):** Unify mixed curly and straight quotes for the same use while preserving native quotation marks and direct quotations. Inconsistent scare quotes around interface labels: `Choose the “fast” mode or the "safe" mode.` -> `Choose the “fast” mode or the “safe” mode.`
- **19. Collaborative Communication Artifacts:** Strip empty chatbot openings/closers ("I hope this helps", "Certainly!"), citation tokens (`:contentReference[oaicite:N]{index=N}`, `citeturn0search0`), and tracking params (`utm_source=chatgpt.com`, `utm_source=openai`, `utm_source=copilot.com`, `referrer=grok.com`). Keep genuine greetings, thanks, sign-offs and requests for a decision in correspondence.
- **20. Knowledge-Cutoff Disclaimers:** `While specific details about the company's founding are not extensively documented in readily available sources, it appears to have been established sometime in the 1990s.` -> `The founding date is not documented in the available sources.` Log the unsupported 1990s estimate under Open points rather than turning it into a finding.
- **21. Sycophantic/Servile Tone:** `Great question! You're absolutely right...` -> state the relevant point directly.
- **22. Filler Phrases (**weak alone** for wordiness; strong for meta-commentary like "In this section, we will explore"):** `"In order to achieve this goal"` -> `"To achieve this"`, `"Due to the fact that"` -> `"Because"`, `"At this point in time"` -> `"Now"`.
  Cut needless narration of sourcing, assembly or visible layout. Keep source credits, required provenance, relevant method limitations and caveats; change history belongs in documents about change.
- **23. Excessive Hedging:** `"It could potentially possibly be argued that the policy might have some effect"` -> `"The policy may affect outcomes"`.
- **24. Generic Conclusions and Dramatic Closers:** Cut upbeat closers ("The future looks bright", "Exciting times lie ahead"), "That distinction matters", or a line that explains what the example already showed. Keep a new fact or consequence and any summary the user requested. `Caching cuts repeat work. That is the real win.` -> `Caching cuts repeat work.`

## Replies (25)

### 25. Re-explaining Shared Context

Use only visible conversation or an unmistakable reply. A standalone note may need its background; when context is missing, do not guess what the reader knows. Put the answer first without losing facts, evidence, protected content or requested detail. The local fidelity contract does not adopt upstream's removal of substantive diagnostic detail from its reply example.

**Visible context:** the recipient has already said to keep the general fix outside this account-specific ticket.

**Before:**
> As you noted, this ticket is account-specific, and we should keep the general fix separate. QA found six affected rows. The service is shared. I propose keeping the workaround for account A here and opening a separate ticket for the shared service fix and those six rows.

**After:**
> I propose keeping the workaround for account A here and opening a separate ticket to fix the shared service and the six affected rows found in QA.

For realistic Italian examples and false-positive guards, read `italiano.md` in this reference directory.

---

## Full End-to-End Example

**Before (AI-sounding):**
> Great question! Here is an essay on this topic. I hope this helps!
>
> AI-assisted coding serves as an enduring testament to the transformative potential of large language models, marking a pivotal moment in the evolution of software development. In today's rapidly evolving technological landscape, these groundbreaking tools--nestled at the intersection of research and practice--are reshaping how engineers ideate, iterate, and deliver, underscoring their vital role in modern workflows.
>
> At its core, the value proposition is clear: streamlining processes, enhancing collaboration, and fostering alignment. It's not just about autocomplete; it's about unlocking creativity at scale, ensuring that organizations can remain agile while delivering seamless, intuitive, and powerful experiences to users. The tool serves as a catalyst. The assistant functions as a partner. The system stands as a foundation for innovation.
>
> Industry observers have noted that adoption has accelerated from hobbyist experiments to enterprise-wide rollouts, from solo developers to cross-functional teams. The technology has been featured in The New York Times, Wired, and The Verge. Additionally, the ability to generate documentation, tests, and refactors showcases how AI can contribute to better outcomes, highlighting the intricate interplay between automation and human judgment.
>
> - **Speed:** Code generation is significantly faster, reducing friction and empowering developers.
> - **Quality:** Output quality has been enhanced through improved training, contributing to higher standards.
> - **Adoption:** Usage continues to grow, reflecting broader industry trends.
>
> While specific details are limited based on available information, it could potentially be argued that these tools might have some positive effect. Despite challenges typical of emerging technologies--including hallucinations, bias, and accountability--the ecosystem continues to thrive. In order to fully realize this potential, teams must align with best practices.
>
> In conclusion, the future looks bright. Exciting times lie ahead as we continue this journey toward excellence. Let me know if you'd like me to expand on any section!

**Report (`docs` register):**

**Final text**

````text
AI coding assistants generate code, documentation, tests, and refactors. With them, code generation is faster and output quality has improved with better training. Usage keeps growing. The New York Times, Wired, and The Verge have covered them.

Known problems include hallucinations, bias, and questions of accountability.

Teams must follow best practices.
````

**Changes:**
- 19, 21: chatbot wrappers removed ("Great question!", "Here is an essay", "I hope this helps!", "Let me know...")
- 1, 4, 7, 8: significance inflation, promotional language, AI vocabulary and copula avoidance cut ("enduring testament", "pivotal moment", "groundbreaking", "nestled", "serves as", "functions as", "stands as", "showcases", "intricate interplay")
- 8, 9, 10: copula inflation, negative parallelism and forced abstract triads cut ("catalyst/partner/foundation", "It's not just about autocomplete", "ideate, iterate, and deliver"). Patterns 11 and 12 alone do not justify those cuts.
- 5: the unnamed observers' adoption claim moved to Open points rather than promoted to an unattributed fact; the separate usage-growth claim in the input remains
- 15: the inline-header list merged into prose
- 6, 20, 23: the challenges formula, the knowledge-cutoff disclaimer and the stacked hedging cut; the named problems kept
- 22, 24: "At its core", "In order to" and the generic conclusion cut
- 13: dash asides removed

**Open points:**
- "significantly faster": by how much, measured how? Kept as "faster".
- "improved training" raising output quality: which models, what evidence?
- "Industry observers have noted" adoption spreading from hobbyists and solo developers to enterprise-wide rollouts and cross-functional teams: name the observers or sources before restoring the claim.
- "streamlining processes, enhancing collaboration, and fostering alignment": no concrete benefit named; cut.
- "teams must align with best practices": which practices? The obligation remains in the final text; missing specifics do not authorize changing "must" or removing it.
