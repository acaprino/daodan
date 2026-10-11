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

# Analisi della concorrenza

## Le Cinque Forze di Porter applicate al SaaS

- **Minaccia nuovi entranti: ALTA** -- L'infrastruttura cloud (AWS, GCP, Azure) ha abbattuto le barriere d'ingresso. Nascono 400-450 nuove aziende SaaS ogni anno.
- **Potere dei fornitori: BASSO-MODERATO** -- Storage, compute e database sono commoditizzati.
- **Potere degli acquirenti: ALTO** -- Sottoscrizioni mensili rendono facile il cambio. Piattaforme come G2/Capterra permettono confronti trasparenti.
- **Rivalita' di settore: ESTREMAMENTE INTENSA** -- Oltre 15.000 aziende SaaS solo negli USA.
- **Implicazione strategica**: costruisci switching cost tramite integrazioni profonde, dati proprietari e workflow specifici.

## Framework per l'analisi competitiva

### Strategic Group Mapping

Plotta i competitor su due assi strategici (es. prezzo vs. profondita' funzionale, oppure focus SMB vs. Enterprise). Identifica "white space" non occupati.

### Feature Comparison Matrix

Confronta competitor per features, pricing, integrazioni e supporto con scoring ponderato.

### Perceptual Map / Positioning Matrix

Strumento visivo 2x2 dove la dimensione dei cerchi rappresenta il market share relativo.

Come creare una perceptual map efficace:
1. Scegli due attributi determinanti per il buyer (es. facilita' d'uso vs. completezza funzionale)
2. Identifica 6-10 competitor
3. Plottali basandoti su **dati di percezione del cliente** (rating G2, NPS, interviste) -- non sulla tua opinione
4. Aggiungi la tua posizione per ultima
5. I quadranti vuoti rappresentano opportunita' di posizionamento

## Reverse engineering delle strategie competitor

**Pricing intelligence** -- Monitora le pagine prezzi con Visualping (alert automatici entro 24h). Crea un canale Slack #competitor-pricing dove i venditori condividono i prezzi negoziati dai deal reali.

**Messaggistica** -- Iscriviti alle email nurture sequence dei competitor (email personale). Analizza landing page e homepage. Traccia i cambiamenti con Wayback Machine.

**Prodotto** -- Iscriviti ai free trial di tutti i competitor chiave. Monitora changelog e release notes. Traccia le posizioni aperte (hiring di ML engineers = feature AI in arrivo).

**Strategie di crescita** -- SEMrush/Ahrefs per keyword organiche e paid. SimilarWeb per la breakdown completa del traffico (organic, paid, social, referral). BuzzSumo per i contenuti top-performing.

## Analisi sistematica delle recensioni competitor

### Framework "Love / Hate / Want"

1. Raccogli 100+ recensioni recenti per competitor principale da G2, Capterra e TrustRadius
2. Organizzale in un foglio strutturato
3. Categorizza in tre colonne:
   - **Love** -- cosa amano i clienti (feature di adozione)
   - **Hate** -- cosa odiano (la tua arma competitiva)
   - **Want** -- cosa vogliono (domanda non soddisfatta = segnale per la tua roadmap)

Se "onboarding lento" appare come lamentela su 3+ competitor, hai trovato un gap di mercato. Trasforma le lamentele in marketing: recensioni su "onboarding lento" -> la tua promessa "Setup in 24 ore".

## Tool per analisi competitiva

| Tool | Funzione | Costo |
|------|---------|-------|
| **SEMrush** | All-in-one: SEO, PPC, content, competitor | $139,95-449,95/mese |
| **Ahrefs** | Backlink, Content Gap, keyword storici | Da $129/mese |
| **SpyFu** | 10+ anni di storico ads, ad copy, stime di spesa | $39-249/mese |
| **SimilarWeb** | Traffico, market share, audience overlap | Da $149/mese |
| **BuiltWith** | Identificazione tech stack competitor | Free basic; da $295/mese |
| **Crayon/Klue** | Piattaforme CI enterprise con battlecard AI | Enterprise pricing |
| **Visualping** | Monitoraggio automatico modifiche siti web | Da $13/mese (free plan) |
