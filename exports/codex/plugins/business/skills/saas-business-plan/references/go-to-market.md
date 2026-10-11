<daodan_host_binding host="codex">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Codex binding: the adapter binds repository read to read_file, writes to
apply_patch and shell execution to shell; use the equivalent registered tools of
the active Codex runtime and their actual fields. In particular, a shell example's
command, timeout and background fields are not automatically another runtime's
cmd, yield_time_ms or session controls.
Start the runtime's available isolated subagent mechanism with the complete
rendered role body in its task prompt. Role Markdown and generated dispatch bodies
are resources, not registered skills or a native role/subagent_type parameter.
Use only declared role bindings and report an unavailable isolation mechanism.
Load installed skills by their advertised exact IDs; workflow skills carry the
<workflow>-workflow suffix. Named-agent examples do not override inline delivery.
Required foreign providers use Codex's marketplace/install commands:
codex plugin marketplace add <source>, then codex plugin add <provider>@<marketplace>.
Register plugin-declared MCP servers through the active host's MCP configuration
using the generated server command. Do not assume registration makes every tool
available to a restricted worker.
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

# Strategie di go-to-market

## Product-Led Growth (PLG) vs Sales-Led Growth (SLG)

**PLG** -- Funziona quando il prodotto e' intuitivo, il time-to-value e' rapido, l'ACV e' sotto ~EUR 5.000/anno e ci sono effetti di rete (Slack, Dropbox, Calendly, Figma). Genera **+15-20% NRR** e CAC inferiore. Pero' il 60% delle iniziative PLG fallisce entro 18 mesi per problemi di implementazione.

**SLG** -- Appropriato per prodotti complessi, clienti enterprise, ACV sopra EUR 50.000, cicli di vendita lunghi con piu' stakeholder.

## Modello ibrido 2025: Product-Led, Sales-Assisted

Best practice 2025: gli utenti si iscrivono al piano free (PLG), l'uso attiva flag come Product-Qualified Leads (PQL -- es. aggiunta del 10mo membro del team, tentativo di feature premium), poi il team sales interviene per la conversione enterprise.

**I PQL convertono 2-3x meglio dei MQL tradizionali.**

Insight architetturale: costruisci l'instrumentazione per la transizione PLG-to-sales dal giorno uno, anche se nessuno legge ancora i dati.

## Channel-Market Fit: scegliere i canali giusti

| ACV | Canali raccomandati | Motion |
|-----|-------------------|--------|
| <EUR 1K/anno | SEO, content, viral loop, freemium, Product Hunt | Self-serve PLG |
| EUR 1K-10K/anno | Google Ads, content, SEO, email, social | PLG + sales assist leggero |
| EUR 10K-50K/anno | Google Ads, LinkedIn Ads, content, webinar, outbound | Ibrido PLG/SLG |
| EUR 50K-250K/anno | ABM, LinkedIn, SDR outbound, eventi, partnership | Sales-led |
| EUR 250K+/anno | Field sales, relazioni executive, ABM, system integrator | Enterprise sales-led |

## Community-Led Growth

Le aziende con community attive crescono **2,1x piu' velocemente** nel revenue e hanno un **+46% LTV**. Ogni EUR 1 investito in community genera EUR 6,40 di ritorno.

### Modello evolutivo: Lighthouse -> Port -> City

1. **Lighthouse** -- Piccolo gruppo curato (20 persone giuste) per definire la cultura
2. **Port** -- Apri gradualmente
3. **City** -- Scala con sotto-community e self-governance

Notion (100M+ utenti con community hub e ambassador program) e' il gold standard.

## Sequenza di lancio ottimale

**Pre-lancio (3-6 mesi)**
- Ricerca di mercato, definizione ICP/persona, MVP
- Waitlist con incentivi di condivisione social
- Contenuti teaser, costruzione lista email

**Beta (1-2 mesi)**
- Lancio a gruppo curato
- Meccanismi di feedback facili
- Iterazione rapida, raccolta testimonial

**Lancio pubblico (1-2 mesi)**
- Product Hunt (costruisci community su LinkedIn prima)
- Multi-channel promotion, PR
- Offerte lancio limitate nel tempo

**Post-lancio (6-12 mesi)**
- Monitoraggio metriche chiave
- A/B test su onboarding/pricing/messaging
- Raddoppio sui canali con miglior rapporto CAC/LTV
