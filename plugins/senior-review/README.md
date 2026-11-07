# senior-review

**Responsabilità:** ricavare dal contesto le domande di correttezza da verificare, selezionare i controlli applicabili e comporre il minimo lavoro di review giustificato dalle evidenze.

Nella nuova base l'unica dipendenza di prodotto è **Codebase Map**. Le micro skill e i controlli restano di proprietà di senior-review; un reviewer è un incarico temporaneo composto da domanda, sorgenti pertinenti, istruzioni selezionate e risultato atteso. Una skill non implica un agente separato.

Il risultato distingue difetti dimostrati, verifiche svolte e lacune. Nessuna selezione semantica garantisce di individuare tutti i difetti.

## Prerequisito

Prima di avviare una review, **Codebase Map deve aver già completato la mappatura dell'intero progetto**. La Phase 0 usa gli indici di quel run esistente; l'eventuale analisi mirata della Phase 1a costruisce il contesto della review e non sostituisce questo prerequisito. Se la mappa completa manca, eseguire prima Codebase Map.

## Phase 0: cosa rivedere

La richiesta («rivedi X») diventa l'elenco dei file da rivedere, in quattro passi: trova i nomi con lo strumento più economico; conferma ogni file con la riga che dimostra la pertinenza, rispettando i limiti espliciti e trattando gli altri nomi come punti di partenza e includendo i chiamanti coinvolti se la richiesta riguarda una modifica; fermati quando le evidenze bastano o a circa 6 interrogazioni e 10 letture, dicendo perché; rispondi con uno di tre esiti, `resolved`, `partial` o `clarify`. Il perimetro è ciò che la review giudica; ciò che legge per giudicarlo è contesto di Phase 1. Tutto il resto è giudizio del reviewer, motivato.

Spec: [`docs/specs/2026-11-04-review-scope-resolution.md`](../../docs/specs/2026-11-04-review-scope-resolution.md). Strumenti di Codebase Map, una riga ciascuno: `plugins/codebase-map/skills/map-method/references/tools-guide.md`. Testo operativo: `skills/review-preparation/references/team-review.md`, sezione "Request to files". Prova: `benchmarks/scope-resolution/`, su 9 casi, una esecuzione per caso: i file indispensabili ci sono sempre, sia su Haiku sia su Opus; l'esito coincide con l'atteso in 7 casi su Haiku e 9 su Opus. Vale per la review di branch (`team-review.md`) e per quella leggera (`light.md`, `code-review.md` caso W). Una review completa con questa Phase 0 non è ancora stata eseguita.

## Stato

Baseline sorgente **1.0.1** importata dal backup integrale del precedente Daodan. Il manifest è stato adattato alla nuova architettura:

- dipendenze richieste: solo `codebase-map`;
- rimosso il membro esterno `testing:test-reliability-auditor` dalla composizione `code-auditor`;
- i ruoli compositi dichiarati restano validi perché definiti in `[reviewers.compositions]`, non come file ruolo individuali.

Installazione: `claude plugin install senior-review@daodan` (marketplace `acaprino/daodan`; richiede `codebase-map`). Ingresso: la skill `/senior-review:review-method`. Una review completa non è ancora stata eseguita. Il catalogo dei reviewer è `plugin.toml`: `skills/review-preparation/scripts/composition.py catalog` lo legge e scrive `CATALOG.json`; `bind` lega il roster ai job.

Le istruzioni obbligatorie che caricavano work-controller, skill-catalog, report-rendering, testing o altri plugin assenti sono state rese host-generiche o trasformate in lacune esplicite. I riferimenti storici residui sono solo documentali. Nei testi `${CLAUDE_PLUGIN_ROOT}` indica la radice del plugin installato; in Bash la variabile non è impostata e il percorso si ricava dalla directory della skill. I ruoli compositi (`code-auditor`, `security-auditor`, …) non hanno un file agente: `composition.py` li espande nei membri, mentre chi li nomina come agente da dispacciare (`investigation-method`) non li trova. La copertura di React, TypeScript, Tauri/platform, testing, abstraction e workspace hygiene non è più fornita da plugin esterni: resta una lacuna dichiarata finché senior-review non possiederà micro skill equivalenti.

Il nuovo selettore minimale descritto nel disegno comune non è ancora implementato.

[Disegno comune](../../docs/specs/2026-11-03-semantic-review-foundation.md)
