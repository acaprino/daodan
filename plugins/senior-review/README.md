# senior-review

**Responsabilità:** ricavare dal contesto le domande di correttezza da verificare, selezionare i controlli applicabili e comporre il minimo lavoro di review giustificato dalle evidenze.

Nella nuova base l'unica dipendenza di prodotto è **Codebase Map**. Le micro skill e i controlli restano di proprietà di senior-review; un reviewer è un incarico temporaneo composto da domanda, sorgenti pertinenti, istruzioni selezionate e risultato atteso. Una skill non implica un agente separato.

Il risultato distingue difetti dimostrati, verifiche svolte e lacune. Nessuna selezione semantica garantisce di individuare tutti i difetti.

## Prerequisito

Prima di avviare una review, **Codebase Map deve aver già completato la mappatura dell'intero progetto**. La Phase 0 usa gli indici di quel run esistente; l'eventuale analisi mirata della Phase 1a costruisce il contesto della review e non sostituisce questo prerequisito. Se la mappa completa manca, eseguire prima Codebase Map.

## Stato

Baseline sorgente **1.0.1** importata dal backup integrale del precedente Daodan. Il manifest è stato adattato alla nuova architettura:

- dipendenze richieste: solo `codebase-map`;
- rimosso il membro esterno `testing:test-reliability-auditor` dalla composizione `code-auditor`;
- i ruoli compositi dichiarati restano validi perché definiti in `[reviewers.compositions]`, non come file ruolo individuali.

Il plugin non è ancora installabile, integrato o validato. Il catalogo dei reviewer è plugin.toml, scritto da skills/review-preparation/scripts/composition.py catalog; lo stesso script lega il roster ai job (ind).

Le istruzioni obbligatorie che caricavano work-controller, skill-catalog, report-rendering, testing o altri plugin assenti sono state rese host-generiche o trasformate in lacune esplicite. I riferimenti storici residui sono solo documentali. `${CLAUDE_PLUGIN_ROOT}`, gli export per host e i comandi `/daodan:*` restano da adattare prima dell'attivazione. La copertura di React, TypeScript, Tauri/platform, testing, abstraction e workspace hygiene non è più fornita da plugin esterni: resta una lacuna dichiarata finché senior-review non possiederà micro skill equivalenti.

Il nuovo selettore minimale descritto nel disegno comune non è ancora implementato.

[Disegno comune](../../docs/specs/2026-11-03-semantic-review-foundation.md)
