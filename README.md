# Daodan

<p align="center">
  <img src="docs/assets/branding/daodan-logo-xenotron-glow.png" alt="Daodan logo" width="560">
</p>

Una nuova base dedicata soltanto a **Codebase Map** e **senior-review**.

- [Codebase Map](plugins/codebase-map/README.md) comprende il codice e fornisce contesto verificabile.
- [senior-review](plugins/senior-review/README.md) sceglie i controlli pertinenti e compone la revisione.
- [Disegno comune](docs/specs/2026-11-03-semantic-review-foundation.md)
- [Documentazione storica di Codebase Map](docs/plugins/codebase-map.md)
- [Ricerca sul contesto](docs/research/context-building-research.md)

Il percorso proposto è: **codice e richiesta → comportamenti coinvolti → domande da verificare → micro skill pertinenti → reviewer necessari**.

## Stato

Il 3 novembre 2026 l'utente ha richiesto di archiviare l'intero progetto precedente, ripartire da zero con questi due soli proprietari e azzerare la storia Git locale.

I kernel sorgente di **Codebase Map 1.0.1** e **senior-review 1.0.1** sono stati importati dal backup come baseline. I manifest sono stati adattati alla nuova architettura:

- Codebase Map non dichiara più `report-rendering`; il server MCP è ora una capability opzionale con binding storico da adattare.
- senior-review dichiara soltanto `codebase-map`.
- Il membro esterno `testing:test-reliability-auditor` è stato rimosso dalla composizione `code-auditor`.
- Le istruzioni obbligatorie che caricavano plugin assenti sono state rimosse o trasformate in lacune esplicite.

I plugin **non sono ancora installabili, integrati o validati**. Il reviewer catalog compilato di senior-review è un artefatto di export host e non è presente nel kernel sorgente. I percorsi `${CLAUDE_PLUGIN_ROOT}`, gli export per host e i comandi `/daodan:*` restano riferimenti storici: vanno adattati al nuovo host prima dell'attivazione. La copertura di React, TypeScript, Tauri/platform, testing, abstraction e workspace hygiene non è più fornita da plugin esterni: resta una lacuna dichiarata finché senior-review non possiederà micro skill equivalenti.

Efficacia, portabilità e risparmio di token non sono ancora misurati.

La vecchia implementazione, i suoi esperimenti e la storia Git sono conservati fuori dal progetto in `D:/Backups/daodan-as-is-2026-11-03T1310`. Il backup è una cartella completa, non un archivio compresso. Il vecchio marketplace e le sue dipendenze non sono la struttura del nuovo prodotto.
