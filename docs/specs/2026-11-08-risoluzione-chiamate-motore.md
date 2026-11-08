# Risoluzione delle chiamate: motore di default e metrica

Data: 8 novembre 2026.

**Stato:** applicata in `plugins/codebase-map`, non ancora committata. Misurata su Daodan stesso.

**Collocazione:** `resolve_edges.py` (passaggio motore, stato dello store, rapporto), `edge_view.py` (vista degli archi), `snapshot.py write` e `mcp_service.py` (avvio con lo snapshot); riferimenti `docs/plugins/codebase-map.md` (sezione Risolvibilità), `snapshot.md`, `mcp.md`, `evidence.md`.

## Problema

Il grafo delle chiamate nasceva dal solo risolutore lessicale di `resolution.py`, che lega un binding unico e non inferisce tipi. Il passaggio con motore (`resolve_edges.py --engine jedi`) esisteva ma nessun flusso lo avviava. Esito sul run `daodan-lite-20261107-2`: 3.927 risolte su 27.187 chiamate, riportate come "14%". Il denominatore contava anche le chiamate che nessun risolutore può portare a un simbolo del progetto. La tabella per insieme è in `docs/plugins/codebase-map.md`, sezione Risolvibilità.

## Requisiti

1. **Il passaggio motore è uno store derivato dello snapshot**, come l'indice lessicale e il grafo dei moduli: lo avviano `snapshot.py write` e `codebase_map_create_run`, lo riavvia `codebase_map_index` quando non è fresco. `--no-engine` e `engine=false` lo saltano; il run registra la scelta e nessuna riparazione la scavalca.
2. **Il passaggio non blocca.** Parte come processo staccato e scrive accanto al manifest `engine-edges.sqlite`, `engine-report.json` e `engine-pass.log`. Lo stato (`running`, `fresh`, `sampled`, `stale`, `failed`, `unavailable`, `stopped`, `off`) compare nello stato del run e nella vista degli archi; i consumatori leggono lo store appena esiste, senza parametri.
3. **Stesso parser dello snapshot.** Il processo parte con `uv` sulla stessa versione minore di Python, Jedi e le versioni esatte dei pacchetti di parsing installati (`snapshot.PARSER_PACKAGES`), così l'impronta del parser coincide e l'ambiente vive quanto il passaggio. Senza `uv` usa l'interprete corrente se ha Jedi; senza entrambi lo stato è `unavailable` con la riga di installazione. Un processo figlio dell'interprete di `uv run` non basta: `uv` cancella quell'ambiente all'uscita del comando e Jedi fallisce con `InvalidPythonEnvironment`.
4. **Al motore si chiedono solo i callee con un nome del progetto.** Una chiamata il cui ultimo nome non è una funzione, una classe o un alias di import dell'inventario è esterna (`no-project-name`). Misura sullo snapshot di HEAD: su 1.143 posizioni escluse campionate (1 su 10), 911 chieste a Jedi danno 1 arco, 836 definizioni esterne e 73 non risolte. Chiederle tutte costerebbe circa 9.100 inferenze, cioè 14 minuti per passaggio.
5. **La copertura si legge come risolte su risolvibili.** `external` = builtin + `no-project-name` + definizioni esterne trovate dal motore; `resolvable` = chiamate − `external`; `resolved` = lessicali + archi confermati. Il rapporto sta in `edge_view.coverage.resolution` e nello stato del motore, con i conteggi assoluti, la quota non ancora chiesta (`unasked`) e la ripartizione per linguaggio, dove `engine` è nullo per un linguaggio che nessun passaggio copre.
6. **Si verificano i sorgenti che il motore legge.** L'hash si controlla prima e dopo l'inferenza sui file dei linguaggi del motore; un documento modificato durante il passaggio non lo invalida. Ogni file dell'inventario resta protetto come destinazione.
7. **Un run fermato ferma il suo passaggio.** `codebase_map_stop` termina l'albero dei processi e registra `stopped`; nessuna riparazione lo riavvia, solo un nuovo snapshot.
8. **Nessuna regola nuova in `resolution.py`.** Ciò che il risolutore lessicale non prova lo prova il motore.
9. **Il membro di un valore calcolato conserva il suo nome.** `Path(__file__).resolve()` si registra come `(expr).resolve`, come già fanno gli adattatori tree-sitter: il nome decide se la chiamata è esterna e, se è un nome del progetto, il motore viene interrogato. Prima di questa regola 2.195 chiamate restavano nel denominatore senza poter essere chieste.
10. **Il motore vede le cartelle che il progetto mette su `sys.path`.** Un `import snapshot` che lo snapshot non sa collocare, da un test o da uno script, è come un file raggiunge uno strumento dopo averne inserito la cartella in `sys.path`. Se un solo modulo Python dell'inventario ha quel nome, la sua cartella entra nei percorsi di Jedi, dopo quelli dell'ambiente: un modulo standard o installato con lo stesso nome vince comunque. I nomi della libreria standard non aggiungono cartelle; il report del passaggio le elenca in `import_roots`.

## Misura con il motore

Snapshot di HEAD (`42a63a9ac`, 527 file, 27.586 chiamate Python), Jedi 0.20.1 in modalità project-only, un processo.

| | Solo lessicale | Jedi | Jedi con le cartelle di `sys.path` |
|---|---|---|---|
| Esterne | 15.833 | 18.424 | 18.503 |
| Risolvibili | 11.753 | 9.162 | 9.083 |
| Risolte | 3.968 | 6.212 | 7.399 |
| **Risolte su risolvibili** | **33,8%** | **67,8%** | **81,5%** |
| Durata del passaggio | 0 | 9 min 16 s | 12 min 35 s |

L'ultima colonna è il comportamento predefinito, misurato con il passaggio staccato del prodotto: 7.782 posizioni chieste, media 95,3 ms, p95 321,9 ms. Restano 1.681 posizioni senza risposta: 1.665 non risolte e 16 ambigue. Lo stesso comando in primo piano, con il computer carico, ha dato 49 errori interni di Jedi e 7.399 su 9.112.

## Fuori perimetro

- Motore per Java, Kotlin, Rust, Go, C# e TypeScript: il parsing e il risolutore lessicale ci sono, `ScipEngine` legge un `index.scip` già prodotto, ma nessun flusso lo produce. Servono gli indicizzatori SCIP del linguaggio (scip-java, rust-analyzer, scip-dotnet, scip-typescript, scip-go), che compilano il progetto.
- C e C++: lo snapshot non li analizza, quindi non hanno simboli né chiamate.
- Riuso degli archi tra run per i file invariati.
- Le 154 chiamate `self.metodo()` che la regola lessicale dovrebbe già risolvere (`doc_review.py:427`).
- Un passaggio staccato su quattro si è chiuso dopo circa 6 minuti senza store e senza log; lo stesso comando in primo piano è terminato con successo. Lo stato riporta `failed` e `codebase_map_index` lo riavvia; il comando ora parte con `-X faulthandler` per lasciare nel log il traceback di un crash.

## Verifica

`tests/test_codebase_map_resolve_edges.py` (classe `ResolvabilityTests`: denominatore, filtro, stato dello store, avvio e fallimento, comando `uv`, ripartizione per linguaggio), `tests/test_codebase_map_mcp.py` (avvio con il run, motore assente, stop), `tests/test_codebase_map_mcp_wire.py` (passaggio reale attraverso il protocollo MCP).

**Per modificare questa spec:** un requisito in più solo per un'esigenza obbligatoria o un esito sbagliato riproducibile.
