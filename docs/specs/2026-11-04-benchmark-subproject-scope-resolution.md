# Subproject dimostrativo per scope resolution e ricerca per intent

Data: 4 novembre 2026.

**Stato:** proposta, in attesa di approvazione.

**Scopo:** un subproject di primo livello — codice di prova del progetto, non fixture sotto `tests/` — che **metta alla prova la spec** `docs/specs/2026-11-04-review-scope-resolution.md`: un resolver di riferimento esegue la Phase 0 come codice su una mini-app realistica e ogni casistica deve essere superata e gestita correttamente. Un caso fallito è un finding: o la spec ha una lacuna, o il resolver sbaglia, o il ground truth va corretto con motivo documentato.

**Collocazione:** `benchmarks/scope-resolution/` (scelta mia: coerente con `docs/research/context-building-benchmarks.md` già citato da `locate.md`).

## Obiettivi e non-obiettivi

Obiettivi:

- una mini-app credibile e importabile in cui le casistiche emergono dalla struttura reale, non da stub;
- **prima versione del codice search+retrieval della Phase 0** (`resolver.py`): dato un intent con anchor, produce perimetro, esito e traccia applicando le regole della spec — fallback moduli, una sola riformulazione lessicale, embedding solo dopo entrambi i fallimenti (qui disabilitati), budget ~6 query/10 letture con nodi deduplicati, stati resolved/incomplete/needs_clarification con motivo dell'arresto, chiamate irrisolte mantenute come `calls[].resolution != resolved`, conferma dei collegamenti dinamici tramite lettura del sorgente;
- ground truth per caso: intent, anchor, file attesi, esclusioni attese, esito atteso;
- runner che guida il resolver sui casi e asserisce sul perimetro: il benchmark valida la spec, non si limita a dimostrare i tool;
- scaffolding minimo per l'esperimento model-in-the-loop già previsto dal piano di validazione della spec (scelta mia: solo prompt pronte e template di misurazione, nessuna asserzione).

Non-obiettivi: modifiche ai plugin o alla spec; integrazione CI; embedding abilitati; linguaggi diversi da Python; test pytest dentro `tests/`.

## La mini-app

Servizio ordini, Python solo stdlib, layout workspace con moduli dichiarati:

```text
benchmarks/scope-resolution/
  app/
    pyproject.toml            # [tool.uv.workspace] members = ["packages/*"]
    packages/
      orders/                 # api.py, service.py, pricing.py, inventory.py,
                              # ledger.py, notifications.py, reporting.py, big_module.py
      payments/               # gateway.py, refunds.py
      shipping/               # rates.py
  CASES.md                    # intent pronte al paste per caso + procedura
  ground_truth.json           # esiti attesi per caso
  resolver.py                 # prima versione del codice Phase 0 (search+retrieval)
  run_cases.py                # runner: guida il resolver sui casi e asserisce
  results/                    # template di log per i run col modello
```

Strutture intenzionali nella mini-app:

- dispatch via callback: `api.on_event("checkout", handler)` → registro → `dispatcher._invoke` → `OrderService.checkout` → `pricing.compute_total` → `ledger.record` (catena ≥3 hop);
- alias per hop: in `payments/gateway.py`, `handler = REGISTRY["pay_online"]; handler(order)`;
- receiver sconosciuto: `self._pipeline.step(...)` con `_pipeline` assegnato dinamicamente;
- collegamento dinamico non risolvibile: `notifications.send_via(channel)` con `globals()[name]` da config;
- dipendenza accessoria: `reporting.py` importa `pricing` solo per formattare (da escludere nel caso multi-hop);
- termine di dominio ambiguo: "sconto/discount" in `pricing.compute_discount` (sconto cliente) e `shipping/rates.py` (sconto volume spedizione) — due target materialmente diversi;
- troncamento: `big_module.py` ~800 righe con molti simboli e funzioni lunghe;
- intent a dispersione: "IVA/VAT" toccata in ≥8 file per il caso budget esaurito;
- testo di errore reale: `KeyError: 'pay_online'` sollevato dal dispatcher quando manca la registrazione.

## Matrice delle casistiche

| # | Caso della spec | Struttura usata | Esito atteso |
|---|---|---|---|
| C1 | percorso esplicito | `packages/orders/pricing.py` nel prompt | resolved: quel file |
| C2 | identificatore/testo di errore | `KeyError: 'pay_online'` | resolved: api.py + payments/gateway.py |
| C3 | modulo/feature | modulo dichiarato "shipping"; feature "rimborsi" | resolved via grafo dei moduli / refunds.py |
| C4 | termine di dominio ambiguo | "sconto" pricing vs shipping | needs_clarification: due candidati motivati + domanda; mai unione risolta né scelta silenziosa |
| C5 | catena multi-hop con accessorio | callback → _invoke → checkout → compute_total → record | resolved con reporting.py escluso |
| C6 | collegamento necessario irrisolto | send_via dinamico | incomplete: chiamata con resolution ≠ resolved, niente archi inventati |
| C7 | troncamento | big_module.py | outline/read troncati per sezione nominata |
| C8 | budget esaurito | IVA dispersa in ≥8 file | incomplete con arresto "budget esaurito": perimetro parziale + residuo concreto, senza superare i cap congelati |

Controlli trasversali del runner: fallback moduli prima della ricerca lessicale; una sola riformulazione per ricerca vuota, per lineage di ricerca e non come tetto globale; nessun embedding dopo hit lessicali (gli embedding restano disabilitati). La spec dice "circa 6/10" e "le chiamate illustrate non sono un tetto": i cap numerici e le regole di consumo sono congelati dal benchmark come `reference_policy`, non spacciati per requisiti della spec.

## Resolver e runner

`resolver.py` è la prima versione eseguibile della Phase 0: riceve intent e anchor di un caso, interroga il run (search, graph, outline, modules, read) applicando le regole della spec e restituisce perimetro, esito (resolved/incomplete/needs_clarification), motivo dell'arresto, chiamate irrisolte e traccia delle query/letture con budget deduplicato. La politica di riferimento (ordine degli anchor, spesa del budget, forma dei candidati per l'ambiguità) è esplicita e versionata nel resolver. Dove la spec lascia un giudizio al modello (quale anchor privilegiare, quando una dipendenza è accessoria), il resolver implementa la regola più semplice coerente col testo; ogni punto in cui la spec risulta ambigua o insufficiente va annotato in `results/findings.md` invece di risolto in silenzio.

Gli assert sono a livelli, etichettati per provenienza: `spec_required` (contratti espliciti della spec), `fixture_ground_truth` (aspettative derivate dai sorgenti della mini-app, indipendenti dal resolver), `reference_policy` (convenzioni congelate del benchmark). Un validatore di traccia indipendente dal perimetro controlla gli invarianti di protocollo: fallback moduli prima del lessicale, una riformulazione per lineage di ricerca vuota, nessuna chiamata dopo l'arresto, motivo sempre presente, chiamate irrisolte senza archi inventati, troncamento gestito per sezione nominata, conferma dei collegamenti dinamici supportata da una lettura. `CASES.md` e `ground_truth.json` si scrivono prima del resolver, con rationale derivato dai sorgenti; i casi C5 e C8 richiedono che ogni spesa e ogni esclusione citino la lettura che le motiva (C5: `reporting.py` escluso dal perimetro finale, ispezione accessoria permessa). Varianti avversarie accompagnano gli otto casi: trasformazioni di sorgente (rinomina, spostamento, distrattori) con aspettative ritrasformate esplicitamente, e tracce sintetiche come unit test del validatore di protocollo.

`run_cases.py`:

1. apre con uno spike di binding headless su progetto temporaneo — gate del build: `MapService.create_run` + una chiamata per tool sullo stesso confine di servizio del resolver; se fallisce, il blocco è infrastrutturale e va dichiarato, non aggirato (un eventuale adapter locale è ammesso solo per test isolati del resolver, etichettato come non equivalente al run reale). Poi crea il run reale con project root `benchmarks/scope-resolution/app`;
2. per ogni caso C1-C8 esegue il resolver e confronta perimetro, esclusioni, esito, chiamate irrisolte e consumo di budget con `ground_truth.json`; i confronti canonicalizzano l'ordine, ma gli output grezzi di search/graph restano nei log per diagnosticare nondeterminismo;
3. stampa un report per caso ed esce non-zero su mismatch.

Un caso fallito è un finding da classificare dopo ispezione: lacuna della spec (la regola non determina il comportamento), bug del resolver (la regola c'è ma il codice sbaglia) o ground truth errato (l'aspettativa non corrisponde al comportamento reale e documentato degli strumenti). Si corregge la causa, documentando il motivo; gli assert non si piegano. L'esperimento model-in-the-loop riusa il validatore di traccia sulle tracce del modello; le scelte `reference_policy` restano misurazioni, non criteri di promozione o bocciatura del modello.

## Vincoli

- la mini-app deve essere codice plausibile e importabile (`python -c "import orders.api"` dall'ambiente giusto), non pseudo-codice;
- nessun cambiamento fuori da `benchmarks/scope-resolution/` e da questo documento;
- il runner non richiede rete né modelli.

## Lasciato al builder

Nomi esatti di file e simboli oltre quelli citati, dimensione finale di `big_module.py`, numero esatto di file che toccano l'IVA, formato dei log in `results/`.
