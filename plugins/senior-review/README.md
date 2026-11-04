# senior-review

**Responsabilità:** ricavare dal contesto le domande di correttezza da verificare, selezionare i controlli applicabili e comporre il minimo lavoro di review giustificato dalle evidenze.

Nella nuova base l'unica dipendenza di prodotto è **Codebase Map**. Le micro skill e i controlli restano di proprietà di senior-review; un reviewer è un incarico temporaneo composto da domanda, sorgenti pertinenti, istruzioni selezionate e risultato atteso. Una skill non implica un agente separato.

Il risultato distingue difetti dimostrati, verifiche svolte e lacune. Nessuna selezione semantica garantisce di individuare tutti i difetti.

## Stato

Baseline sorgente **1.0.1** importata dal backup integrale del precedente Daodan. Il manifest è stato adattato alla nuova architettura:

- dipendenze richieste: solo `codebase-map`;
- rimosso il membro esterno `testing:test-reliability-auditor` dalla composizione `code-auditor`;
- i ruoli compositi dichiarati restano validi perché definiti in `[reviewers.compositions]`, non come file ruolo individuali.

Il plugin non è ancora installabile, integrato o validato. `references/reviewer-catalog.json` è un artefatto generato durante l'export per host e **non è presente nel kernel sorgente**; la preparazione legacy non è quindi eseguibile finché non viene generato o sostituito dal nuovo selettore.

Le istruzioni obbligatorie che caricavano work-controller, skill-catalog, report-rendering, testing o altri plugin assenti sono state rese host-generiche o trasformate in lacune esplicite. I riferimenti storici residui sono solo documentali. `${CLAUDE_PLUGIN_ROOT}`, gli export per host e i comandi `/daodan:*` restano da adattare prima dell'attivazione. La copertura di React, TypeScript, Tauri/platform, testing, abstraction e workspace hygiene non è più fornita da plugin esterni: resta una lacuna dichiarata finché senior-review non possiederà micro skill equivalenti.

Il nuovo selettore minimale descritto nel disegno comune non è ancora implementato.

[Disegno comune](../../docs/specs/2026-11-03-semantic-review-foundation.md)
