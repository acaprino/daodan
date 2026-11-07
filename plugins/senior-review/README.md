# senior-review

**Responsabilità:** comprendere l'oggetto da rivedere, scegliere i reviewer pertinenti leggendo i loro mandati e comporre il minimo lavoro di review giustificato dalle evidenze.

L'unica dipendenza di prodotto è **Codebase Map**. Le micro skill e i controlli restano di proprietà di senior-review; un reviewer è un incarico temporaneo sull'intero perimetro, composto da mandato, contesto, istruzioni selezionate e risultato atteso. Una skill non implica un agente separato.

Il risultato distingue difetti dimostrati, verifiche svolte e lacune. Nessuna selezione semantica garantisce di individuare tutti i difetti.

## Prerequisito

Prima di avviare una review, **Codebase Map deve aver già completato la mappatura dell'intero progetto**. La Phase 0 e la Phase 1 usano gli indici e i tool di quel run esistente; nessuna fase della review analizza il progetto al suo posto. Se la mappa completa manca, eseguire prima Codebase Map.

## Phase 0: cosa rivedere

La richiesta («rivedi X») diventa l'elenco dei file da rivedere, in quattro passi: trova i nomi con lo strumento più economico; conferma ogni file con la riga che dimostra la pertinenza, rispettando i limiti espliciti e trattando gli altri nomi come punti di partenza e includendo i chiamanti coinvolti se la richiesta riguarda una modifica; fermati quando le evidenze bastano o a circa 6 interrogazioni e 10 letture, dicendo perché; rispondi con uno di tre esiti, `resolved`, `partial` o `clarify`. Il perimetro è ciò che la review giudica; ciò che legge per giudicarlo è contesto di Phase 1. Tutto il resto è giudizio del reviewer, motivato.

Spec: [`docs/specs/2026-11-04-review-scope-resolution.md`](../../docs/specs/2026-11-04-review-scope-resolution.md). Strumenti di Codebase Map, una riga ciascuno: `plugins/codebase-map/skills/map/references/tools-guide.md`. Testo operativo: `skills/review-preparation/references/team-review.md`, sezione "Request to files". Prova: `benchmarks/scope-resolution/`, su 9 casi, una esecuzione per caso: i file indispensabili ci sono sempre, sia su Haiku sia su Opus; l'esito coincide con l'atteso in 7 casi su Haiku e 9 su Opus. Vale per la review di branch (`team-review.md`) e per quella leggera (`light.md`, `code-review.md` caso W). Una review completa con questa Phase 0 non è ancora stata eseguita.

## Stato

Versione **1.0.1**. Dipendenza richiesta: solo `codebase-map`. I ruoli compositi sono definiti in `[reviewers.compositions]` di `plugin.toml`, non come file ruolo.

Installazione: `claude plugin install senior-review@daodan` (marketplace `acaprino/daodan`; richiede `codebase-map`). Ingresso: la skill `/senior-review:review-method`. Le review eseguite sul benchmark `benchmarks/scope-resolution/` e i loro costi sono registrati nel suo README: il criterio di costo non è ancora raggiunto. Il catalogo dei reviewer è `plugin.toml`: `skills/review-preparation/scripts/composition.py catalog` lo legge e scrive `CATALOG.json`; `bind` lega il roster ai job.

Nei testi `${CLAUDE_PLUGIN_ROOT}` indica la radice del plugin installato; in Bash la variabile non è impostata e il percorso si ricava dalla directory della skill. I ruoli compositi (`code-auditor`, `security-auditor`, …) non hanno un file agente: `composition.py` li espande nei membri, mentre chi li nomina come agente da dispacciare (`investigation-method`) non li trova. React, TypeScript e i confini architetturali dichiarati hanno ruoli propri (`react-auditor`, `typescript-auditor`, `boundary-auditor`). Tauri/platform, testing, prior art e workspace hygiene non hanno un reviewer: restano lacune dichiarate.

La Phase 1 di `team-review` comprende l'oggetto nel perimetro già risolto, sceglie i reviewer adatti leggendo i loro mandati. `composition.py bind` riceve la scelta e senza di essa si ferma; i reviewer scelti partono insieme nella Phase 2, ciascuno sull'intero perimetro. Il rigor (`quick`, `standard`, `deep`) lo decide il modello leggendo la richiesta, `standard` se non dice nulla: stabilisce la verifica, da solo Critical a tutti i finding con il critico. I segnali di rischio lo portano a `deep`. Testo operativo: `skills/review-preparation/references/team-review.md`.

[Disegno comune](../../docs/specs/2026-11-03-semantic-review-foundation.md)
