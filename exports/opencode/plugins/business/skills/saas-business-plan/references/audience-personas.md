<daodan_host_binding host="opencode">
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

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
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

# Audience e User Persona

## Buyer persona per SaaS B2B e B2C

In B2B distingui tra **ICP** (profilo aziendale: settore, dimensione, fatturato, area geografica) e **buyer persona** (profilo individuale: motivazioni, pain point, criteri decisionali).

### Framework T2D3/Kalungi -- 3 persona fondamentali

- **P1 -- L'utente quotidiano** che usa il software
- **P2 -- Il decision maker** che deve giustificare l'acquisto internamente
- **P3 -- L'executive** con responsabilita' fiduciarie

### Vendite enterprise -- 5 ruoli nel comitato d'acquisto

End user, valutatore tecnico, buyer economico (CFO), champion interno, gatekeeper (legal/security).

### B2C e app mobile

Focus su psicografia: atteggiamenti, stile di vita, contesto d'uso (quando, dove, perche'), trigger emotivi, pattern comportamentali.

### Contenuto di ogni persona

Dati demografici, pain point specifici, obiettivi, trigger d'acquisto (es. round di funding, scadenza compliance), criteri decisionali, obiezioni comuni, canali preferiti. Le persona devono essere **documenti vivi** -- se non le aggiorni da 6 mesi, non stai ascoltando.

## Jobs-to-be-Done (JTBD)

I clienti non comprano prodotti, li "assumono" per fare un lavoro.

**Formula JTBD statement:** *"Quando mi trovo in [situazione], voglio [motivazione/lavoro], cosi' posso [risultato atteso]."*

### 3 dimensioni di ogni job

- **Funzionale** -- il task pratico
- **Emotiva personale** -- come vuole sentirsi l'utente
- **Emotiva sociale** -- come vuole essere percepito

### Tecnica della timeline (10-20 interviste)

Conduci interviste JTBD con acquirenti recenti o utenti che hanno cambiato prodotto. Ripercorri dal momento dell'acquisto fino al primo pensiero di cambiare soluzione per scoprire il **trigger event** e le alternative considerate (incluso il "non fare nulla").

Domande chiave:
- *"Cosa stavi cercando di realizzare quando hai iniziato a cercare una soluzione?"*
- *"Cosa avresti fatto se questo prodotto non esistesse?"*

## Ricerca qualitativa e quantitativa

### Interviste utente (Mom Test)

5-20 per segmento bastano per identificare pattern significativi. Principi:
- Chiedi del comportamento passato/presente, mai del futuro ipotetico
- Fai parlare il cliente
- Concentrati sui problemi, non sulle soluzioni
- Annota le **parole esatte** dell'utente -- diventeranno il tuo copy di marketing

### Survey

Micro-sondaggi in-app (2-3 domande) raggiungono un tasso di risposta medio del **12%** nei prodotti SaaS. Tool: Typeform (75% completamento), SurveyMonkey, Google Forms (gratuito, sufficiente per validazione iniziale).

### Stack analytics raccomandato per fase

- Stage iniziale/MVP: GA4 + Hotjar free (~EUR 0-40/mese)
- SaaS in crescita: Amplitude Growth o Mixpanel + Hotjar Business
- Enterprise: Amplitude Enterprise + FullStory
- **PostHog**: alternativa open-source che sostituisce Amplitude + LaunchDarkly + Hotjar in uno

## Come trovare early adopter

| Piattaforma | Ideale per | Risultati tipici |
|-------------|-----------|-----------------|
| **Product Hunt** | Visibilita' al lancio | Migliaia di visitatori in 24h |
| **BetaList** | Waitlist pre-lancio | 60-246 iscrizioni; **12,7% conversion rate** |
| **Indie Hackers** | Community building, "build in public" | Engagement continuativo di alta qualita' |
| **Hacker News (Show HN)** | Tool per developer, prodotti tech | Esposizione massiva; feedback brutalmente onesto |
| **Reddit** (r/SaaS, r/startups) | Audience di nicchia | Altamente targetizzato |
| **AppSumo** | Revenue + validazione via lifetime deal | Cash flow + base utenti ampia |

### Strategia LinkedIn testata

Cerca professionisti target per ruolo/titolo, crea una sequenza automatizzata: visualizza profilo -> segui -> connetti -> 2 follow-up. Un founder ha ottenuto **100 early adopter da 600 professionisti contattati**.
