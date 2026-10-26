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

# Tool e risorse

## Mappa tool per fase di ricerca

**Ricerca di mercato**: Google Trends (free) -> Statista (freemium) -> Crunchbase Pro ($49/mese) -> SimilarWeb -> IBISWorld/Gartner (enterprise)

**Ricerca audience**: Google Forms/Typeform (free/freemium) -> Hotjar (free tier) -> SparkToro ($38/mese) -> Mixpanel/Amplitude (free tier) -> Maze per usability testing

**Analisi competitor**: G2/Capterra (free) -> BuiltWith/Wappalyzer (free extension) -> SEMrush/Ahrefs ($129-140/mese) -> SpyFu ($39/mese) -> Crayon/Klue (enterprise)

**Pricing**: Van Westendorp via Typeform (free) -> ProfitWell (free) -> ChartMogul (free tier) -> Price Intelligently/Conjointly (consulenza)

**SEO/Content**: Google Search Console (free) -> SurferSEO ($89/mese) -> Clearscope ($170/mese) -> BuzzSumo ($199/mese)

**Advertising analysis**: Meta Ad Library + Google Ads Transparency (free) -> SpyFu ($39/mese) -> SEMrush

**Analytics e metriche**: GA4 (free) -> PostHog (open-source) -> Mixpanel/Amplitude (free tier) -> ChartMogul/Baremetrics/ProfitWell

## Framework e template

- **April Dunford Positioning Canvas** -- workbook gratuito di 12 pagine su aprildunford.com (iscrizione newsletter)
- **Miro** -- template per April Dunford Positioning, GTM Strategy (roadmap 5 fasi), Business Model Canvas, Product Positioning Canvas
- **Notion** -- template "Positioning and Messaging Frameworks" di Olena Bomko con ICP, buyer persona, JTBD, UVP, tono di voce
- **ClickUp** -- Product Positioning Template e Product Launch Checklist
- **MRR Unlocked** -- guida con worksheet Notion, decision tree, template positioning
- **PMFSurvey.com** -- tool gratuito di Sean Ellis per il test di Product-Market Fit

## Community e risorse online

- **SaaStr** (saastr.com) -- la piu' grande community B2B SaaS al mondo
- **Indie Hackers** (indiehackers.com) -- 140.000+ membri, ideale per bootstrapper e "build in public"
- **Product Hunt** (producthunt.com) -- piattaforma di discovery e lancio prodotti
- **ProductLed** (productled.com) -- 15.000 membri focalizzati su PLG
- **Lenny's Podcast** -- episodi con April Dunford, Rahul Vohra e altri leader
- **Reddit** -- r/SaaS, r/startups, r/SideProject, r/Entrepreneur
- **Y Combinator Startup Library** -- risorse gratuite su ogni aspetto delle startup

## Libri fondamentali

1. **"Obviously Awesome"** di April Dunford -- il riferimento definitivo per il posizionamento
2. **"Crossing the Chasm"** di Geoffrey Moore -- adozione tecnologica
3. **"The Mom Test"** di Rob Fitzpatrick -- interviste clienti
4. **"Building a StoryBrand"** di Donald Miller -- messaging
5. **"Product-Led Growth"** di Wes Bush -- strategia PLG

## Piano di lavoro: da zero al lancio in 7 settimane

**Settimana 1-2 -- Fondamenta e landscape di mercato**
- Assembla team cross-funzionale (prodotto, marketing, sales, CS, leadership)
- Conduci analisi TAM/SAM/SOM
- Raccogli dati di settore (Statista, Crunchbase, SimilarWeb)
- Identifica tutti i competitor potenziali (diretti, indiretti, status quo)
- Configura Google Trends e Google Alerts

**Settimana 3 -- Ricerca cliente**
- 15-20 interviste con clienti o prospect
- Survey via Typeform (target 100+ risposte)
- Analizza dati di utilizzo prodotto se disponibili
- Applica Mom Test. Domanda chiave (Dunford): *"Cosa faresti se il nostro prodotto non esistesse?"*

**Settimana 4 -- Deep-dive competitivo**
- Analisi SEMrush/Ahrefs (SEO, content, traffico)
- Analizza positioning, messaging e pricing dei competitor
- Esamina ads via Meta Ad Library, SpyFu, Google Ads Transparency
- Studia recensioni G2/Capterra
- Crea la competitive positioning map

**Settimana 5 -- Value proposition e pricing**
- Applica il processo di April Dunford in ordine
- Conduci ricerca di pricing con Van Westendorp o Gabor-Granger
- Testa la willingness-to-pay per segmento

**Settimana 6 -- Positioning statement e messaging**
- Positioning statement nel formato Geoffrey Moore: *"Per [cliente target] che [bisogno], [prodotto] e' un [categoria] che [beneficio chiave]. A differenza di [competitor], [prodotto] [differenziazione primaria]."*
- Messaging hierarchy: headline -> subheadline -> punti di supporto -> proof point
- Positioning per ogni buyer persona
- Battlecard per il team sales

**Settimana 7 -- Validazione e documentazione**
- Testa il positioning con 5-10 clienti target
- Affina sulla base del feedback
- Crea il documento finale di positioning strategy
- Allinea stakeholder tramite workshop
- Pianifica il rollout sui canali marketing

### Timeline per tipo di azienda

| Stage | Timeline | Note |
|-------|---------|------|
| Startup pre-lancio | 4-8 settimane | Piu' veloce, meno stakeholder |
| Early-stage (post-PMF) | 6-10 settimane | Interviste clienti = input chiave |
| Growth-stage (repositioning) | 8-12 settimane | Piu' stakeholder, piu' dati |
| Enterprise (repositioning) | 12-16+ settimane | Linee di prodotto multiple |

## Documento finale di positioning strategy

Il deliverable finale deve includere:
1. Executive Summary (1 pagina)
2. Contesto di mercato (TAM/SAM/SOM, trend, crescita)
3. Profilo cliente target (ICP + buyer persona + JTBD)
4. Categoria di mercato
5. Landscape competitivo (alternative, positioning map, tabella comparativa)
6. Differenziatori chiave (feature uniche + valore)
7. Value Proposition e Positioning Statement
8. Framework di messaging (tono di voce, feature -> capabilities -> vantaggi -> benefici, proof point)
9. Strategia di pricing
10. Strategia di canale
11. Metriche di successo

## Errori da evitare assolutamente

1. **Posizionamento "per tutti"** -- "Tutti sono il nostro cliente" diluisce la rilevanza. Nicchia prima, espansione dopo.
2. **Confondere positioning con messaging** -- Il positioning e' strategico (chi, cosa, perche'); il messaging e' tattico (come lo comunichi).
3. **Sotto-prezzare** -- Il sotto-pricing e' **2x piu' comune** del sovra-pricing e significativamente piu' difficile da correggere.
4. **Saltare la ricerca cliente** -- Positioning basato sulle assunzioni del founder = causa #1 di fallimento.
5. **Non rivisitare mai il positioning** -- I mercati cambiano; revisione trimestrale raccomandata.
