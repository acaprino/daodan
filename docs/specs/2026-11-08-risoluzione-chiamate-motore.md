# Risoluzione delle chiamate: motore di default e metrica

Data: 8 novembre 2026.

**Stato:** applicata in `plugins/codebase-map`, non ancora committata. Misurata su Daodan stesso.

**Collocazione:** `resolve_edges.py` (motori, passaggio, stato dello store, rapporto), `languages/semantic.py` (posizione del nome delle dichiarazioni), `edge_view.py` (vista degli archi), `snapshot.py write` e `mcp_service.py` (avvio con lo snapshot); riferimenti `docs/plugins/codebase-map.md` (sezione Risolvibilità), `snapshot.md`, `mcp.md`, `evidence.md`.

## Problema

Il grafo delle chiamate nasceva dal solo risolutore lessicale di `resolution.py`, che lega un binding unico e non inferisce tipi. Il passaggio con motore (`resolve_edges.py --engine jedi`) esisteva ma nessun flusso lo avviava. Esito sul run `daodan-lite-20261107-2`: 3.927 risolte su 27.187 chiamate, riportate come "14%". Il denominatore contava anche le chiamate che nessun risolutore può portare a un simbolo del progetto. La tabella per insieme è in `docs/plugins/codebase-map.md`, sezione Risolvibilità.

## Requisiti

1. **Il passaggio motore è uno store derivato dello snapshot**, come l'indice lessicale e il grafo dei moduli: lo avviano `snapshot.py write` e `codebase_map_create_run`, lo riavvia `codebase_map_index` quando non è fresco. `--no-engine` e `engine=false` lo saltano; il run registra la scelta e nessuna riparazione la scavalca.
2. **Il passaggio non blocca.** Parte come processo staccato e scrive accanto al manifest `engine-edges.sqlite`, `engine-report.json` e `engine-pass.log`. Lo stato (`running`, `fresh`, `sampled`, `stale`, `failed`, `unavailable`, `stopped`, `off`) compare nello stato del run e nella vista degli archi, complessivo e per linguaggio in `languages`; i consumatori leggono lo store appena esiste, senza parametri.
3. **Stesso parser dello snapshot.** Ogni motore gira in uno stage con un ambiente `uv` suo: la stessa versione minore di Python, i requisiti del motore e le versioni esatte dei pacchetti di parsing installati (`snapshot.PARSER_PACKAGES`), così l'impronta del parser coincide e l'ambiente vive quanto lo stage. Due motori non condividono l'ambiente, perché i requisiti di uno possono cambiare la versione dell'altro (multilspy fissa una versione più vecchia di Jedi). Senza `uv` lo stage usa l'interprete corrente se importa il motore; senza entrambi il linguaggio è `unavailable` con la riga di installazione. Un processo figlio dell'interprete di `uv run` non basta: `uv` cancella quell'ambiente all'uscita del comando e Jedi fallisce con `InvalidPythonEnvironment`.
4. **Al motore si chiedono solo i callee con un nome del progetto.** Una chiamata il cui ultimo nome non è una funzione, una classe o un alias di import dell'inventario è esterna (`no-project-name`). Misura sullo snapshot di HEAD: su 1.143 posizioni escluse campionate (1 su 10), 911 chieste a Jedi danno 1 arco, 836 definizioni esterne e 73 non risolte. Chiederle tutte costerebbe circa 9.100 inferenze, cioè 14 minuti per passaggio.
5. **La copertura si legge come risolte su risolvibili.** `external` = builtin + `no-project-name` + definizioni esterne trovate dal motore; `resolvable` = chiamate − `external`; `resolved` = lessicali + archi confermati. Il rapporto sta in `edge_view.coverage.resolution` e nello stato del motore, con i conteggi assoluti, la quota non ancora chiesta (`unasked`) e la ripartizione per linguaggio, dove `engine` è nullo per un linguaggio che nessun passaggio copre.
6. **Si verificano i sorgenti che il motore legge.** L'hash si controlla prima e dopo l'inferenza sui file dei linguaggi del motore; un documento modificato durante il passaggio non lo invalida. Ogni file dell'inventario resta protetto come destinazione.
7. **Un run fermato ferma il suo passaggio.** `codebase_map_stop` termina l'albero dei processi, stage e language server compresi, e registra `stopped`; nessuna riparazione lo riavvia, solo un nuovo snapshot.
8. **Nessuna regola nuova in `resolution.py`.** Ciò che il risolutore lessicale non prova lo prova il motore.
9. **Il membro di un valore calcolato conserva il suo nome.** `Path(__file__).resolve()` si registra come `(expr).resolve`, come già fanno gli adattatori tree-sitter: il nome decide se la chiamata è esterna e, se è un nome del progetto, il motore viene interrogato. Prima di questa regola 2.195 chiamate restavano nel denominatore senza poter essere chieste.
10. **Jedi vede le cartelle che il progetto mette su `sys.path`.** Un `import snapshot` che lo snapshot non sa collocare, da un test o da uno script, è come un file raggiunge uno strumento dopo averne inserito la cartella in `sys.path`. Se un solo modulo Python dell'inventario ha quel nome, la sua cartella entra nei percorsi di Jedi, dopo quelli dell'ambiente: un modulo standard o installato con lo stesso nome vince comunque. I nomi della libreria standard non aggiungono cartelle; il report del passaggio le elenca in `import_roots`.

11. **Un motore per ogni linguaggio analizzato, uno alla volta.** Il passaggio esegue gli stage in sequenza e salta i linguaggi già `fresh` nello store. Prima di ogni stage controlla la memoria libera (almeno 2 GB); dopo uno stage finito per esaurimento della memoria non ne avvia altri. Un language server ha memoria e thread limitati. Lo store tiene una voce per linguaggio, con il motore che l'ha scritta, e uno stage sostituisce solo le voci e gli archi dei propri linguaggi.
12. **Daodan installa il motore al primo uso, senza chiedere.** Lo dice in una riga del log e lo mette in una cartella condivisa fra i progetti (`%LOCALAPPDATA%\Daodan\engines`, `$XDG_CACHE_HOME/daodan/engines`). Se manca un toolchain che non si installa in modo isolato (Node.js, cargo, go, .NET SDK), il linguaggio è `unavailable` con la causa e la riga di installazione, mai `failed`. Il motore non scarica tipi né dipendenze del progetto e non compila.
13. **Le posizioni si convertono in modo esplicito.** Al confine del motore la colonna è in byte UTF-8, l'unità dello snapshot; ogni motore converte nella propria (Jedi in code point, LSP in unità UTF-16, SCIP nella codifica che il documento dichiara) e riconverte la risposta. Un byte dentro un carattere non è una posizione.
14. **L'arco arriva dove il motore nomina la dichiarazione.** La risposta è la posizione di un nome; la dichiarazione dello snapshot che ha il nome in quella posizione dà identità e `type` dell'arco. Gli adattatori tree-sitter registrano la posizione del nome (`name_span`) e quella delle firme di overload dello stesso corpo (`signature_spans`); per Python la si ricava dai token del sorgente verificato. Una posizione che nomina due dichiarazioni è ambigua.
15. **Il membro di un valore calcolato conserva il suo nome anche negli adattatori tree-sitter.** `res.status(500).render()` registra `(expr).render`, come il requisito 9 per Python.
16. **Vue e Svelte si chiedono al motore di TypeScript.** Il motore riceve un documento virtuale con i soli blocchi script agli stessi offset in byte dello snapshot, quindi una posizione vale in entrambi.
17. **Al motore si chiede solo ciò che può essere cambiato.** Una risposta resta valida finché non cambiano il suo file, i file che quel file importa (anche in modo transitivo e attraverso `sys.path`) e i file del progetto in cui la risposta punta, sotto lo stesso contesto: motore e versione, ambienti, target, impronta del parser e versione del risolutore. Le risposte vivono in `engine-answers.sqlite`, accanto allo store delle schede, con una generazione per file e un contesto per motore. Un passaggio che non ha niente da chiedere non avvia il motore; un dry run chiede tutto e non scrive.
18. **Prima le posizioni che valgono di più.** I file modificati o nuovi rispetto alla cache vengono prima di quelli cambiati solo nelle dipendenze; a parità decide il rango del file (PageRank), poi la posizione.
19. **Il passaggio pubblica mentre lavora.** Lo store esce subito con le risposte riusate, poi ogni 30 secondi. La voce del linguaggio è `partial`, e lo stato riporta `answered` su `population`. Un passaggio fermato o fallito lascia ciò che ha provato, e il successivo riprende da lì.

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

### TypeScript e JavaScript

Scelta misurata fra due strade, sullo stesso snapshot e con la stessa valutazione degli archi: **A**, typescript-language-server 4.3.3 (con TypeScript 5.5.4) interrogato per posizione attraverso multilspy 0.1.1; **B**, un indice di scip-typescript 0.6.1 letto da `ScipEngine`. Progetti: ky `3541888` (TypeScript, 98 file) ed express `43fca52` (JavaScript, 142 file), senza dipendenze installate salvo dove indicato.

| | ky, A | ky, B | express, A | express, B |
|---|---|---|---|---|
| Archi confermati (ky: campione 1 su 3; express: tutto) | 82 | 30 | 163 | 107 |
| Compila o installa dipendenze | no | sì: senza `npm install` fallisce (`TS6053`) | no | no |
| File coperti | tutti | solo quelli di un tsconfig: `test/` resta fuori | tutti | tutti |
| Durata | 47 s | 2,6 s di indice | 21 s | 5,9 s di indice |
| RAM di picco | 1.066 MB | 258 MB | 651 MB | 322 MB |

Vince A sul primo e sul secondo criterio. Il comportamento predefinito, misurato con lo stage del prodotto su tutta la popolazione:

| | ky, lessicale | ky, motore | express, lessicale | express, motore |
|---|---|---|---|---|
| Esterne | 8.503 | 10.847 | 9.195 | 9.205 |
| Risolvibili | 6.113 | 3.769 | 2.877 | 2.867 |
| Risolte | 791 | 1.631 | 207 | 385 |
| **Risolte su risolvibili** | **12,9%** | **43,3%** | **7,2%** | **13,4%** |
| Durata dello stage | 0 | 52 s | 0 | 24 s |
| RAM di picco | | 1.294 MB | | 675 MB |

Posizioni chieste: 5.058 su ky (media 8,4 ms, p95 24,2 ms) e 2.652 su express (media 7,1 ms, p95 29,0 ms). Su express 2.424 posizioni restano senza risposta: sono metodi di `req`, `res` e `app`, oggetti che Express costruisce a runtime con `Object.create` e mixin, che nessuna analisi statica tipizza. Con le dipendenze installate le risolte restano 385 e 143 chiamate passano fra le esterne (14,1%). Il motore occupa 24 MB su disco nella cartella condivisa, più 12 MB di ambiente `uv`.

### Distribuzione del lavoro

ky `3541888`, motore TypeScript, stage del prodotto. Ogni riga parte dalla cache lasciata dalla riga precedente.

| Caso | Chieste | Riusate | Durata | RAM di picco | Risolte su risolvibili |
|---|---|---|---|---|---|
| Primo passaggio | 5.058 | 0 | 49,6 s | 1.320 MB | 43,3% |
| Snapshot invariato | 0 | 5.058 | 2,1 s, motore non avviato | 115 MB | 43,3% |
| Modifica di un test (`test/headers.ts`) | 237 | 4.821 | 8,0 s | 607 MB | 43,3% |
| Modifica di `source/utils/merge.ts`, importato quasi ovunque | 4.902 | 156 | 38,5 s | 1.235 MB | 43,3% |

In tutti i casi gli archi confermati restano 840. Una modifica a un file centrale invalida quasi tutto per costruzione: il tipo inferito di ciò che il file esporta arriva a chi lo importa, anche in modo transitivo.

## Fuori perimetro

- Motore per Java, Kotlin, Rust, Go e C#: il parsing e il risolutore lessicale ci sono; `ScipEngine` legge un `index.scip` già prodotto, che nessun flusso produce.
- C e C++: lo snapshot non li analizza, quindi non hanno simboli né chiamate.
- Le 154 chiamate `self.metodo()` che la regola lessicale dovrebbe già risolvere (`doc_review.py:427`).
- Un passaggio staccato su quattro si è chiuso dopo circa 6 minuti senza store e senza log; lo stesso comando in primo piano è terminato con successo. Lo stato riporta `failed` e `codebase_map_index` lo riavvia; il comando ora parte con `-X faulthandler` per lasciare nel log il traceback di un crash.

## Verifica

`tests/test_codebase_map_resolve_edges.py` (classe `ResolvabilityTests`: denominatore, filtro, stato dello store, avvio e fallimento, comando `uv`, ripartizione per linguaggio; `MultiLanguageTests`: posizione dei nomi e overload, membro di un valore calcolato, voci per linguaggio, un motore alla volta, memoria; `DistributionTests`: riuso, invalidazione per import, ordine, pubblicazione e ripresa, dry run, digest; `PositionUnitTests`: conversioni), `tests/test_codebase_map_mcp.py` (avvio con il run, motore assente, stop), `tests/test_codebase_map_mcp_wire.py` (passaggio reale attraverso il protocollo MCP, Python e TypeScript).

**Per modificare questa spec:** un requisito in più solo per un'esigenza obbligatoria o un esito sbagliato riproducibile.
