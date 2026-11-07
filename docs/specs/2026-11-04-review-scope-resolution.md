# Identificazione del perimetro di review

Data: 4 novembre 2026, ridotta il 7 novembre 2026.

**Stato:** applicata nel testo di `team-review.md`, non ancora eseguita in una review completa. Provata su `benchmarks/scope-resolution/`: una esecuzione per caso, risultati e limiti nel suo README.

**Collocazione:** Phase 0 "Target Resolution" di `plugins/senior-review/skills/review-preparation/references/team-review.md`, sezione "Request to files"; la review leggera vi rimanda da `review-method/references/light.md` e da `review-preparation/references/code-review.md` (caso W). Aggiunge alla Phase 0 le richieste a parole: modulo, feature, funzione, errore, termine di dominio. La Phase 1 "Context Building" resta invariata.

```text
Richiesta + Codebase Map → file da rivedere → contesto → review
            Phase 0                           Phase 1
```

## Phase 0 — Cosa rivedere

Traduce la richiesta nei file da rivedere. Prerequisito: la mappa completa del progetto esiste già; se manca, prima Codebase Map. Quale strumento risponde a quale domanda: `plugins/codebase-map/skills/map-method/references/tools-guide.md`.

1. **Trova.** Dalla richiesta prendi i nomi: file, funzioni, moduli, errori, termini. Per ognuno lo strumento più economico: file esplicito → nessuno; modulo → `codebase_map_modules`; nome o parola → `codebase_map_search`; flusso → `codebase_map_graph`, un hop alla volta dai file già confermati. Una ricerca vuota si riprova una volta con un sinonimo; un indice mancante o stale non è una ricerca vuota, è un prerequisito mancante.
2. **Conferma.** Rispetta i limiti espliciti («solo questo file», un diff); altrimenti i nomi sono punti di partenza e includi solo i file pertinenti alla richiesta, con la riga che lo dimostra: `codebase_map_outline` per i simboli, `codebase_map_read` solo del pezzo che decide. Una richiesta su una modifica include i chiamanti che la modifica coinvolge (`codebase_map_edit_impact`). Il grafo non vede collegamenti dinamici né copie: non inventarli, cercali per nome e leggi; se non si confermano, dillo.
3. **Fermati** quando le evidenze bastano, quando non ci sono più piste, o a circa 6 interrogazioni e 10 letture. Di' sempre perché.
4. **Rispondi** con uno di tre esiti: `resolved` (i file, ciascuno con la sua evidenza); `partial` (i file trovati, cosa serve ancora alla richiesta e perché); `clarify` (la richiesta può voler dire due cose diverse: i candidati e la domanda).

Il perimetro è ciò che la review giudica; ciò che legge per giudicarlo è contesto di Phase 1. Il coordinatore non legge gli artefatti di analisi di Codebase Map prima della discovery indipendente: regola e motivo nel contratto del coordinatore (`team-review.md`, Phase 0c). Tutto il resto è giudizio del reviewer, motivato.

**Per modificare questa spec:** una regola in più solo per un requisito obbligatorio scoperto o un errore riproducibile; prima prova a correggere una regola esistente. Un'ambiguità segnalata da un modello non è un errore.

## Esempi

Mini-app ordini di `benchmarks/scope-resolution/app/`.

**Limite esplicito o punto di partenza.** «Rivedi solo `pricing.py`» → `resolved`: `pricing.py`. «Rivedi la modifica dello sconto cliente in `pricing.py`» → `pricing.py` è il punto di partenza: `codebase_map_edit_impact` mostra che `compute_discount` è chiamata da `compute_total`, e questa da `service.py::OrderService.checkout` → `resolved`: `pricing.py`, `service.py`; `reporting.py` usa solo `VAT_RATE`, resta fuori.

**Collegamento dinamico non confermabile.** «Quale funzione invia davvero la notifica?» → `service.py::checkout` chiama `notifications.send_via`, che carica il gestore da una variabile d'ambiente: nessuna lettura lo conferma → `partial`: `service.py`, `notifications.py`; manca la destinazione, in configurazione esterna.

**Termine ambiguo.** «C'è un bug nello sconto» → `search("sconto")` trova `pricing.py::compute_discount` (sconto cliente) e `rates.py::volume_discount` (sconto spedizioni) → `clarify`: quale dei due?

## Testo operativo

In inglese, in `plugins/senior-review/skills/review-preparation/references/team-review.md`, sezione "Request to files". I target già esatti (file o directory passati come target, diff, PR, documenti) restano gestiti come prima.

## Verifica

`benchmarks/scope-resolution/`: README, casi, ground truth e risultati. Il resolver deterministico misura il protocollo (budget, una riformulazione, nessun collegamento inventato, tre esiti); il giudizio sul perimetro si misura con sessioni del modello sugli stessi casi, con tre metriche separate: file indispensabili mancanti, inclusioni senza motivazione, protocollo. Un fallimento si classifica prima di correggere: difetto del benchmark, lacuna della spec, giudizio del modello.
