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

# Analisi del mercato: dimensionare l'opportunita' reale

Mercato globale SaaS: $266 miliardi nel 2024 (proiezione $1.131 mld al 2032), >31.000 aziende attive.

## Come calcolare TAM, SAM e SOM

La dimensione del mercato si misura su tre livelli. La credibilita' dipende dalla convergenza di almeno due metodi diversi.

### TAM (Total Addressable Market)

Opportunita' totale di revenue se il prodotto raggiungesse il 100% del mercato. Tre metodologie in parallelo:

**Metodo top-down** -- Parte da report di settore (Gartner, IDC, Forrester, Grand View Research). Formula: *dimensione del mercato di settore x % del segmento rilevante*. Rapido, apprezzato dagli investitori, ma tende a sovrastimare anche di 10-100x.

**Metodo bottom-up** -- Il piu' affidabile per SaaS. Identifica l'ICP, conta le aziende corrispondenti, moltiplica per l'ACV. Esempio: 45.000 aziende mid-market (200-2.000 dipendenti) x EUR 50.000 ACV = EUR 2,25 miliardi TAM.

**Metodo value-based** -- Quantifica il costo del problema che il prodotto risolve x numero di aziende affette. Il piu' utile per informare il pricing.

**Regola di validazione**: se top-down e bottom-up convergono entro +-15%, la stima e' credibile.

### SAM e SOM

**SAM (Serviceable Addressable Market)** -- Filtra il TAM per vincoli geografici, capacita' del prodotto, verticali e dimensioni aziendali target.

**SOM (Serviceable Obtainable Market)** -- Cio' che puoi realisticamente catturare in 1-3 anni. Per una startup SaaS: **0,5-2% del TAM** nei primi 3 anni.

## Valutare la saturazione del mercato

Cinque indicatori chiave di saturazione:
1. Piu' di 30 competitor diretti nella sottocategoria
2. Le prime 3 aziende controllano >75% del market share
3. La competizione avviene principalmente sul prezzo
4. Il CAC di settore e' in crescita costante
5. Il tasso di innovazione e' in declino

Un mercato con crescita sostenuta, differenziazione chiara tra player e nicchie non servite rappresenta ancora un'opportunita' -- anche se affollato.

## Tool e fonti per dati di mercato

| Tool | Cosa offre | Costo |
|------|-----------|-------|
| **Google Trends** | Interesse nel tempo, confronto topic, breakdown geografico | Gratuito |
| **Statista** | 1M+ statistiche, dossier di settore, previsioni | Freemium; da ~EUR 199/mese |
| **Crunchbase** | Funding, stime revenue, dati aziendali | Free tier; Pro: $49/mese |
| **SimilarWeb** | Traffico web come proxy del market share | Free tier; paid da ~$149/mese |
| **IBISWorld** | 700+ report industriali (US), market size, previsioni | Enterprise (EUR 1K+/anno) |
| **G2 Grid Reports** | Ranking per presenza di mercato + soddisfazione | Gratuito per consultazione |
| **Gartner Magic Quadrant** | Analisi leader di categoria enterprise | Enterprise ($30K+/anno) |
| **CB Insights** | Funding, analytics, market maps per tech/SaaS | Da $9.800/anno |
| **Grand View Research** | Report con TAM, segmentazione, forecast | Per report ($2.500-5.000) |
| **SEC EDGAR / Google Finance** | 10-K report per aziende pubbliche | Gratuito |

**Suggerimento pratico**: le biblioteche universitarie offrono spesso accesso gratuito a IBISWorld, Statista completo, Euromonitor Passport e S&P Global.
