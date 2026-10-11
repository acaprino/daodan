<daodan_host_binding host="pi">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Pi binding: repository reads use read/find/grep, writes use edit/write, and shell
execution uses bash or the registered powershell alternative. Use their actual
command, timeout and process-control schema rather than capitalized foreign tools.
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

# Strategia di pricing

Il pricing e' il moltiplicatore di crescita piu' sottovalutato. Un miglioramento dell'1% nella strategia di pricing produce un **aumento dell'11% dei profitti**.

## Modelli di pricing per SaaS (2025)

**Tiered pricing** -- Il piu' diffuso. Media 3,5 tier per azienda, ma le pagine con **3 tier convertono il 31% meglio** di quelle con 4+.

**Usage-based** -- In forte crescita: adottato dal **38-39%** delle aziende SaaS. Genera **+10% NRR**, **-22% churn** e crescita 2x piu' veloce.

**Hybrid** (base + per-user + usage + add-on) -- Adottato dal **31%** delle aziende (High Alpha 2025).

**Pricing a crediti** -- Trend dominante 2025: 79 delle top 500 aziende SaaS lo offrono (crescita del **126% YoY**). Nuovi adottanti: Figma, HubSpot, Salesforce. Particolarmente adatto per prodotti AI dove il per-seat tradizionale non funziona.

**Monetizzazione AI** -- Il **74%** delle aziende con prodotti AI sta monetizzando o testando. Trend: ri-integrare add-on AI nel piano base con aumento di prezzo (es. Notion Business da $15 a $20/utente/mese dopo il bundling).

## Value-based vs. cost-plus vs. competitor-based

**Value-based** -- Preferito dal **78%** delle aziende SaaS. Genera **+32% LTV** e payback del CAC piu' rapido. Richiede profonda comprensione del cliente.

**Cost-plus** -- Utile come punto di partenza quando i dati di mercato sono limitati.

**Competitor-based** -- Funziona per entrare in categorie consolidate, ma rischia la commoditizzazione.

## Testare la sensibilita' al prezzo

### Van Westendorp Price Sensitivity Meter

4 domande:
1. A quale prezzo il prodotto sarebbe troppo economico, da dubitarne della qualita'?
2. Un affare?
3. Caro ma accettabile?
4. Cosi' caro da non considerarlo mai?

Plottando le curve cumulative, le intersezioni identificano il **prezzo ottimale** e il **range di prezzi accettabili**. Servono minimo **100 rispondenti per segmento**. Fornire contesto del prodotto (demo, screenshot) prima delle domande.

### Conjoint Analysis (Choice-Based)

Presenta scenari di trade-off tra feature e prezzo per rivelare come i clienti valutano ogni componente. Richiede 200+ rispondenti e investimento di $15.000-50.000+ con consulenti. Le aziende che la usano vedono un **30% di miglioramento nella monetizzazione**. Tool: Sawtooth Software (standard di settore), Conjointly, Qualtrics.

## Best practice per la pagina prezzi

Struttura ideale in 4 sezioni:
1. Hero con value prop + toggle mensile/annuale
2. Menu con **3 tier** evidenziando il "Piu' popolare"
3. Tabella comparativa feature
4. FAQ su cancellazione e fatturazione

Benchmark:
- Mostrare prezzo annuale come default: **+19% adozione annuale**
- Garanzie di rimborso: **+12-18% conversione**
- L'utente deve poter scegliere un piano in **30 secondi** (benchmark ProfitWell)
