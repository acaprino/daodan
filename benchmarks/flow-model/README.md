# Benchmark: flussi e unità della fase 2

**Stato:** In uso come fixture: `app/`, `rules.json` ed `expected.json` sono letti dai test dei flussi, della mappa del sistema, degli ingressi, dell'esploratore e del server MCP (`tests/test_codebase_map_flows.py` e altri). Le sei misure della fase 2 sui casi reali sono misurate altrove, o non misurate: vedi la tabella.

**Domanda.** La [spec della fase 2](../../docs/specs/2026-11-18-flussi-e-mappa-del-sistema.md) regge? I collegamenti che la macchina deduce bastano a formare flussi e unità di review giusti, sulla fixture e sui casi reali [`polar-flow`](../polar-flow/README.md), [`tududi-flow`](../tududi-flow/README.md) e [`phazly-flow`](../phazly-flow/README.md)?

## Misure, soglie e dove sta il risultato di oggi

| Misura | Cosa si conta | Soglia | Risultato valido oggi |
|---|---|---|---|
| 0. Collegamenti `chiama` | risolte su risolvibili, per caso e per linguaggio | un caso entra nelle misure 1 e 3 con almeno il 70% | [`call-provenance`](../call-provenance/README.md): dopo il passo statico e dopo il passo dinamico. Il conteggio di qui sotto è superato |
| 1. File di un difetto noto | incarichi di `pack()` e unità che contengono i file di ogni difetto atteso, a parità di perimetro e limite di byte | ogni difetto in meno unità che incarichi di `pack()`; stessi file distinti assegnati; due esecuzioni identiche | [`phazly-flow`](../phazly-flow/README.md#file-di-un-difetto-noto-misura-1-della-fase-2); polar e tududi non misurati |
| 2. Fixture a due strati | collegamenti trovati contro attesi, dedotti a parte; collegamenti falsi; lacune dichiarate | tutti i collegamenti attesi; nessun collegamento falso fra campi indipendenti o rotte omonime; ogni identità ambigua è una lacuna | raggiunta, nei test (sotto) |
| 3. Caso fra strati | dal fatto mostrato allo store, attraverso la rotta del caso | il flusso arriva allo store in tududi e phazly | phazly: riuscita per G2, non per G1 ([`phazly-flow`](../phazly-flow/README.md#con-e-senza-il-passaggio-del-motore)); tududi non misurato |
| 4. Etichette | granularità e significato contro una lettura manuale, su 20 collegamenti; costo per collegamento | almeno 16 su 20 concordi | non valutata: [`phazly-flow`](../phazly-flow/README.md#etichette-di-granularità-e-significato-scritte-da-un-modello-misura-4-della-fase-2) |
| 5. Simboli e funzionalità | flussi attesi ritrovati; file entrati senza appartenere a quelli attesi; flussi incompleti | tutti i flussi attesi, zero file estranei; ogni causa di arresto lascia il flusso incompleto; un nodo senza codice compare con il collegamento dichiarato | raggiunta, nei test (sotto) |

Le misure 2 e 5 sono senza modello, con regole scritte a mano. Le regole scritte da un modello sono misurate su phazly ([regole scritte alla cieca](../phazly-flow/README.md#regole-scritte-alla-cieca-da-un-modello)), non su questa fixture.

## Fixture

`app/` è un negozio su due strati: interfaccia in TypeScript (`web/`), servizio `shop` e servizio `admin` in Python. Contiene uno stato globale con campi indipendenti, due rotte omonime in servizi diversi, una rotta chiamata con un percorso dinamico, due azioni dell'utente, un lavoro pianificato, un fornitore di pagamento esterno dichiarato in `codebase-modules.json`, una catena di chiamate fra tre file con un ciclo e due lettori della stessa collezione, uno coerente con chi scrive e uno no. I valori attesi stanno in `expected.json`, fuori da `app/`: chi analizza la fixture non li vede.

## Misure 2 e 5 sulla fixture

`tests/test_codebase_map_flows.py`, regole di `rules.json`: tutti i collegamenti attesi, nessun collegamento vietato, la lacuna del percorso dinamico dichiarata, il flusso dal badge arriva alla collezione passando per la rotta, unità che tengono insieme chi scrive e chi legge con limite di 120.000 e di 1.500 byte. `WrittenRuleTests` copre i costrutti che passano da oggetti di libreria. I test girano in CI, non su questa macchina.

## Misura 0: conteggio superato

`modal run benchmarks/flow-model/modal_engine_count.py --phazly-tar <archivio>` (l'archivio è `git archive 46c92b28 react-app shared functions-python` di phazly-app, senza file `.env`), 11 novembre 2026, Modal, 4 CPU e 16 GB per caso. I valori per caso sono in `results/engine-count-*.json`: polar `server/` 55,9%, tududi 52,8%, phazly 59,7%, nessuno alla soglia del 70%.

Questi numeri non sono lo stato di oggi: contano le chiamate con il criterio precedente al requisito 23 (provenienza) e misurano il solo passo statico, senza l'ambiente del progetto. Il conteggio con il criterio di oggi, con l'ambiente che Daodan prepara e dopo il passo dinamico, e l'esito di ogni caso sulla soglia del 70%, stanno in [`call-provenance`](../call-provenance/README.md).
