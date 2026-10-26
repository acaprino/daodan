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

# Pubblicita', marketing e metriche KPI

## Analisi delle strategie pubblicitarie competitor

Tre strumenti gratuiti per intelligence competitiva:

**Meta Ad Library** (facebook.com/ads/library) -- Mostra TUTTI gli annunci attivi su Facebook e Instagram di qualsiasi pagina business, senza login. Annunci attivi da 3+ mesi sono probabilmente performanti.

**Google Ads Transparency Center** (adstransparency.google.com) -- Mostra Search, Display, YouTube e Gmail ads per advertiser. Se i competitor fanno ads su keyword "alternative" o "reviews", stanno targetizzando comparison shopper.

**LinkedIn Ad Library** -- Piu' limitata ma la presenza e' significativa dato il costo elevato.

Tool avanzati: **SpyFu** (da $39/mese, 10+ anni storico), **SEMrush** (da $139,95/mese, all-in-one), **Adbeat** (da $249/mese, display/programmatic).

## SEO e content marketing per SaaS

### Programmatic SEO (tattica dominante 2024-2025)

Crea centinaia di pagine ottimizzate per long-tail keyword:
- **Pagine di integrazione** -- modello Zapier: "[Prodotto] + [Tool] integration" -> crescita traffico del 300%+
- **Pagine comparison/versus** -- "[Tuo SaaS] vs [Competitor]"
- **Pagine alternative** -- "[Competitor] alternatives"
- **Librerie di template** e **tool gratuiti** (calcolatori, grader)

### ROI del content marketing

Content marketing genera **$3 per ogni $1 investito** come minimo, ROI fino al **748%**. L'**82%** delle aziende SaaS ha team dedicati.

| Tipo contenuto | ROI/Impatto |
|---------------|-------------|
| Blog post SEO-ottimizzati | Base del traffico organico |
| Case study | Richiesti dal **73% dei buyer B2B** |
| Video | ROI **49% piu' veloce** del testo |
| Webinar | **73% dei marketer B2B**: miglior formato per lead qualificati |

## Performance marketing per canale

| Canale | CTR | CPC | Nota chiave |
|--------|-----|-----|-------------|
| **Google Ads** | 4,28% (il piu' alto) | $5-50 | Ideale per ACV >$500/anno. Budget share in calo: 55% (2022) -> 40% (2024) |
| **LinkedIn Ads** | 0,62% (il piu' basso) | $8-15 | **ROAS 113%** (il piu' alto B2B). SQL:CW **30-33%**. Budget share: 31% -> 39% (2024) |
| **Meta Ads** | 1,43% | ~$0,66 | Ideale B2C/prosumer, ACV EUR 100-1.000/anno |

**Regola strategica**: Google vince sulle metriche di volume (CTR, CPC); LinkedIn vince sulle metriche di qualita' (ROAS, pipeline). Scegli in base alla lunghezza del ciclo di vendita.

## Email marketing

ROI: **$36-42 per ogni $1 speso** (3.600-4.200% ROI).

- Campagne behavior-triggered: **+320% revenue** rispetto alle broadcast
- Email segmentate: **77% del ROI email totale**

Tool raccomandati: **Encharge** (specifico SaaS), **Customer.io** (event-driven, product-led), **ActiveCampaign** (automazioni), **HubSpot** (full CRM).

## North Star Metric

Il singolo indicatore che cattura il valore core per i clienti:

| Tipo SaaS | North Star | Esempio |
|-----------|-----------|---------|
| Engagement | DAU/WAU/MAU | Slack, Zoom |
| Produttivita' | Task completati, workflow eseguiti | Asana, Notion |
| Platform | Transazioni processate | Shopify, Stripe |
| Infrastructure | API call, risorse consumate | AWS, Twilio |

## Benchmark SaaS 2024-2025

| Metrica | Benchmark | Note |
|---------|-----------|------|
| **CAC medio** | $702 | Security SMB $805, Enterprise $10.221 |
| **CAC Payback** | 12-15 mesi target | ACV >$100K: 24 mesi; ACV <$5K: 9 mesi |
| **LTV:CAC** | 3:1 gold standard; mediana 3,6:1 (2024) | |
| **Churn mensile** | 3-5% (healthy B2B) | SMB churn e' 8,2x piu' alto di enterprise |
| **NRR** | Target 111%+ | Aziende con NRR >=100% crescono 2x piu' veloce |
| **MRR growth** | 10-20% MoM (early-stage) | Top startup raggiungono $1M ARR in 9 mesi |
| **Gross Margin** | 70-80%+ | Standard SaaS |
| **Rule of 40** | Growth rate + profit margin >= 40% | |

## Share of Voice (SOV)

*SOV = metriche del tuo brand / metriche totali di mercato x 100*

- Brand con SOV dominante: **1,5x conversioni** e **+30% retention**
- Brand con SOV > market share tendono a crescere; SOV < market share tendono a contrarsi
- **Trend 2025 -- AI Share of Voice**: traccia menzioni del brand nelle risposte di ChatGPT, Perplexity e Gemini (tool: HubSpot SOV, Ahrefs Brand Radar)

## Tool per metriche SaaS

- **ChartMogul** -- free fino a $120K ARR
- **Baremetrics** -- analytics + dunning + forecasting
- **ProfitWell** -- free, benchmarking su 14.000+ aziende
- **Stack a costo zero**: ProfitWell + Looker Studio + PostHog self-hosted

## Unit Economics e proiezioni finanziarie

### Burn Rate e Runway

**Burn Rate mensile** = costi fissi (team, infrastruttura, tool) + costi variabili (ads, CAC)

**Runway** = funding disponibile / burn rate mensile = mesi di sopravvivenza

Benchmark per fase:
- Pre-seed: 12-18 mesi di runway raccomandati
- Seed: 18-24 mesi
- Series A+: 24+ mesi

### Break-even

**Break-even MRR** = burn rate mensile / gross margin %

**Clienti necessari per break-even** = break-even MRR / (ACV / 12)

### Benchmark costi SaaS

| Voce | % del revenue (target) |
|------|----------------------|
| COGS (hosting, infra) | 20-30% |
| R&D / Engineering | 20-25% |
| Sales & Marketing | 30-50% (early-stage), 20-30% (growth) |
| G&A | 10-15% |

### Formula LTV semplificata

**LTV** = ARPA x Gross Margin % x (1 / Monthly Churn Rate)

Esempio: ARPA EUR 100/mese x 80% margin x (1 / 5% churn) = EUR 1.600 LTV
