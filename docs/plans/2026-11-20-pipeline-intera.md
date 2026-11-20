# Piano: la pipeline intera, dall'albero sintattico alla ricerca

**Obiettivo:** ogni pezzo dei due giorni attaccato a un passo che Daodan ha già, in ordine, e una prova che rifà tutto da zero sui cinque casi.
**Vincoli:** quelli del [piano del 19 novembre](2026-11-19-verso-i-riferimenti.md#vincoli); in più, nessun pezzo legge o installa di nuovo ciò che un passo già legge o installa.

**Diviso per aspetto il 20 novembre 2026**, su richiesta del proprietario: [analisi unificata](2026-11-20-analisi-unificata.md) (task 0–2b), [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) (task 3–8, 11 e 11b), [ricerca e pacchetto di review](2026-11-20-ricerca-e-pacchetto-di-review.md) (task 9–10c). Qui restano la pipeline (sezione 1), che cosa gira dove (2), l'ordine (3) con il task 12, la prova da zero (4), ciò che si toglie (5) e le decisioni (6).

## 1. La pipeline, un passo per riga

I passi sono quelli di `pipeline.STEPS` (`daodan/core/pipeline/__init__.py`), con lo snapshot prima e il passo semantico dopo, come li avvia il codice.

**0. snapshot** (`snapshot.py write`, l'ingresso di `pipeline.run`): tree-sitter e risolutore lessicale.
- c'è già: le grammatiche dei lettori, `angular` compresa (`languages/_treesitter.py`); un nome in un attributo o in un argomento è un riferimento `read` (`languages/semantic.py`).

**1. scan** (`pipeline.Scan`): grafo dei moduli e pre-mappa; i comandi del modello girano nel container (`premap/container_runner.py`).
- c'è già: `tsc --showConfig` dopo il ripristino delle dipendenze del progetto (`premap/tsc.py`).
- fatto oggi, da collegare: OWASP Noir. Il lettore del suo JSON c'è (`entries.noir`); lo avvia solo `modal_map.py::noir_case`. Si attacca qui come sorgente della pre-mappa: `premap/noir.py` e una voce di `container_runner.TOOLS` con url e sha256, come `daodan-enry` (task 5).

**2. stack** (`pipeline.Stack`, `technologies.ensure`): le tecnologie di ogni unità.
- nessun pezzo nuovo: le forme note di un framework sono dati del registro (task 6).

**3. analyze** (`pipeline.Analyze`, `engine_pass.run_pass`): un indicizzatore nativo per linguaggio.
- c'è già: scip-typescript nel container, dopo il ripristino del progetto con i suoi script (`indexers/typescript.py`, `preparation.node_prepare`); Vue con lo strumento di Vue (`indexers/components.cjs`), Svelte con il svelte2tsx di scip-typescript; Angular con nessuno.
- c'è già: il nome in `onClick={salva}` è un `read` con l'estremo dell'indice, anche in un altro file (`code_graph.build`); il lettore del markup non lo usa (task 3).
- c'è già: scip-python dà l'estremo di `self.salva` in `command=self.salva` (`indexers/python.py`); il lettore dell'argomento non lo usa (task 3).
- doppione tolto il 20 novembre: `framework.cjs`, un terzo programma TypeScript scritto a mano su un albero senza dipendenze. Vale lo strumento ufficiale, scip-typescript; restano due regole da leggere dall'albero (task 4): una funzione che restituisce solo markup non è un evento, e l'etichetta segue l'ordine del nome accessibile del W3C.

**4. dynamic** (`pipeline.Dynamic`, `dynamic.run`): i test del progetto nel container, sotto un registratore.
- c'è già: Playwright come esecutore dei test del progetto (`dynamic/javascript.py`, `RUNNERS`): ciò che un clic di un suo test chiama entra come arco osservato.
- da fare: la fonte osservata (ruolo e nome di ogni controllo a schermo, le chiamate di un clic), nella stessa run dell'osservatore, dopo la stessa preparazione (task 11).

**5. union** (`pipeline.Union`): il grafo completo e ciò che non contiene.
- nessun pezzo nuovo.

**6. semantico**, dopo `union` e fuori da `STEPS`: `App._follow` avvia `App.link` e poi `App.map` (`app.py`); nel plugin `entry-analyze.md` avvia `system-mapper`.
- c'è già: `App.link` poi `App.map` a fine passaggio, una volta per selezione.
- fatto oggi, da collegare: i lettori dall'albero (attributo con etichetta, argomento anche desktop, decoratori, residuo; `entries.candidates`, `data/entry-queries.json`), che chiama solo `modal_map.py::entries_case`. Si attaccano alla risposta `needs_rules` di `MapService.flows` (`mcp_service.py`) come tabella delle forme (`entries.shapes`), con i candidati di Noir (task 6).
- da fare: le regole scritte dalla macchina dalle forme classificate, `attiva`, `offre`, `ingresso` (task 6).
- c'è già: tipi di nodo, `inside`, campi dei servizi, nomi, «Sequence» (`system_map.py`, `system_levels.py`, `references/system-map.md`).
- c'è già: la confezione della scheda, voci numerate e `LIMIT` della risposta (`system_brief._text`, `fit`).
- fatto oggi, da collegare: le schede dei percorsi e i quattro punti (`benchmarks/system-map/traces.py`, `cards` e `verify`). Si attaccano a `MapService.flows`, con `verify` prima di `system_map.record` (task 7).
- fatto oggi, da collegare: Secretlint (`secret_mask.masked`), che oggi usa solo `code_archive.py`. Si attacca a `source_reader.read_packet`, a `system_brief._text` e al testo delle schede (task 8).
- da fare: l'anagrafica dei flussi e i legami `avvia`, `condivide`, `stesso dato`, in `system_map.py` dopo `record` (task 9).
- da fare: la ricerca per embedding sulle voci dell'anagrafica (task 10). `embedding_worker.py` c'è, con EmbeddingGemma 2 in ONNX, ma indicizza simboli del codice; la misura migliore (multilingual-e5-large, 82% e 93% sui flussi) è su voci scritte dai riferimenti, non da Daodan.
- c'è già: il grafo dell'app ai livelli codice e infrastruttura (`assets/app/app.js`, `app_view.py`); da fare: la mappa e il flusso acceso (task 12).

## 2. Che cosa gira dove

| Pezzo | Dove | Perché |
| --- | --- | --- |
| snapshot, lettori dall'albero, collegamenti, union, schede, `verify`, mappa | host | leggono testo, snapshot e grafo; non eseguono nulla |
| comandi del modello della pre-mappa, Noir compreso | container | leggono il progetto; `tsc` dopo un ripristino che ne esegue gli script |
| stack | host | dati del registro |
| scip-typescript e i componenti Vue | container | il ripristino esegue gli script del progetto |
| scip-python | host su Linux e macOS, container su Windows | solo wheel, nessun codice del progetto (`python_environment`) |
| test sotto il registratore e fonte osservata con Playwright | container | eseguono il progetto |
| Secretlint (`secret_mask.py`) | host, fuori dalla cartella del progetto | configurazione di Daodan, testo sull'ingresso; il test del segno c'è (`tests/test_codebase_map_host_programs.py`) |
| modello per regole, mappa e schede (`engines.py`) | il motore scelto | riceve solo testo passato da Secretlint (task 8) |
| embedding (`embedding_worker.py`) | host, in un processo suo | legge le voci di Daodan, non il progetto |
| grafo dell'app; la sua prova nel browser | host; la prova nel container | la pagina è di Daodan |

Le dipendenze le installa `preparation.node_prepare` (e gli altri `RESTORES`) in ogni run del container che le chiede: per un progetto Node oggi tre volte, `tsc` in scan, scip-typescript in analyze, l'osservatore in dynamic. Nessun pezzo di questo piano aggiunge un'installazione: la fonte osservata entra nella run dell'osservatore.

## 3. Ordine di lavoro

Ogni task: prima il test rosso, poi il codice; tocca solo i file che nomina. Dopo un task che cambia una colonna della prova (sezione 4) la prova si rifà. Dal 20 novembre 2026 i task stanno in tre piani, uno per aspetto, con i numeri invariati: l'ordine resta quello della tabella, e nessun modello vede un progetto privato prima del task 8.

| Task | Titolo | Piano |
| --- | --- | --- |
| 0 | Nessuna esecuzione sull'host nelle review e nei test | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 1 | Il container nella run della mappa su Modal | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 1b | Una preparazione sola per analisi | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 2 | Un job per tutta la catena e la sua tabella | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 2b | Tre corse sullo stesso progetto, i costi accanto alla copertura | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 3 | Il gestore dall'estremo del motore | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 4 | Evento o no, ed etichetta secondo accname | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 5 | Noir nella pre-mappa | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 6 | Le forme si classificano una volta | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 7 | Le schede dei percorsi nel nucleo | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 7b | La mappa non perde ciò che rifiuta | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 7c | I flussi dicono ciò che non sanno | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 8 | Secretlint su ciò che esce | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 9 | Anagrafica e legami fra flussi | [ricerca e pacchetto di review](2026-11-20-ricerca-e-pacchetto-di-review.md) |
| 10 | La ricerca sull'anagrafica | [ricerca e pacchetto di review](2026-11-20-ricerca-e-pacchetto-di-review.md) |
| 10b | Il pacchetto di una review dalla ricerca | [ricerca e pacchetto di review](2026-11-20-ricerca-e-pacchetto-di-review.md) |
| 10c | L'embedder propone gli abbinamenti, non li decide | [ricerca e pacchetto di review](2026-11-20-ricerca-e-pacchetto-di-review.md) |
| 11 | La fonte osservata | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 11b | Gli eventi fra pagina e guscio Tauri | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 12 | La mappa nel grafo dell'app | qui sotto |

12. **La mappa nel grafo dell'app** (F1, F2, F3, F5). `app_view.product` dalla mappa e dall'anagrafica, apertura sul posto e trascinamento (F2, che la prova di F5 controlla), un flusso acceso, la prova nel browser nel container.
   Test: `benchmarks/standalone-app/app_graph.py`. Riusa: `GRAPH.open`, `App.serve`.

## 4. La prova da zero

Dopo `modal deploy benchmarks/system-map/modal_map.py`, due comandi:

```text
python benchmarks/system-map/modal_map.py whole --tag TAG --tar CASO=ARCHIVIO ... --models qwen,haiku,opus --reps 2
python benchmarks/system-map/score.py whole benchmarks/system-map/results/system/TAG
```

Gli archivi vengono da `python benchmarks/system-map/code_archive.py OUT.tar REPOSITORY@COMMIT`, sul commit dei riferimenti. Una tabella per caso, una riga per modello:

| Colonna | Da dove |
| --- | --- |
| ingressi del riferimento con un candidato nello stesso file, per tipo e per fonte (residuo, argomento, attributo, decoratore, noir, osservato), con gli zeri e gli ingressi contati a parte: non dice che il controllo o il gestore sia quello | `entries.py measure` |
| controllo e gestore giusti, su un piccolo insieme confermato dal proprietario | da scrivere con il task 3 |
| nodi contro il riferimento: ritrovati, profondità 0 e 1, precisione, `inside`; flussi in tre numeri distinti: abbinati uno a uno, somiglianza media alla profondità 1 (non è un conto di flussi: con un flusso abbinato su tre può dare 100%), estremi giusti per ruolo; frecce rifiutate; stabilità fra due giri indipendenti | `score.py system`, `score.py stable` |
| flussi certificati e rifiutati, con i motivi | `verify` (task 7) |
| ricerca, sui quattro casi delle 531 richieste (262 su 131 flussi, 269 su parti): quante richieste hanno una risposta nella mappa di Daodan, e la risposta giusta prima e fra le prime tre sul denominatore di partenza, con EmbeddingGemma 2 e con multilingual-e5-large; il quinto caso ha richieste sue, a parte | le richieste di `embed_queries.py`; la risposta giusta è il flusso o il nodo di Daodan che `score.py system` abbina a quello del riferimento (task 10) |
| segreti mascherati, nell'archivio e nei testi usciti | `code_archive.py`, task 8 |
| costo, token, tempo per passo, preparazione compresa | `summary.json`, eventi della pipeline |

- Modelli: Qwen dal gateway (`--models qwen`, secret Modal `daodan-gateway`) e Haiku 5.5 sono il metro; Opus 5.5 sta accanto.
- Soglie: quelle proposte nel README del benchmark, da confermare dal proprietario.
- C'è: gli archivi; il container su Modal Sandbox (`benchmarks/project-model/modal_pipeline.py`); regole e mappa con `claude -p` (`modal_map.py`, `map_run`, `_prepare`); i candidati (`entries_case`); Noir (`noir_case`); `score.py system` e `stable`; `entries.py measure`; `traces.py cards`, `ask`, `verify`; `embed_queries.py`, `modal_embed.py`, `embed_probe.py rank`.
- Manca il container nei job di `modal_map.py`: senza Docker né Podman scip-typescript è `unavailable` e il passo dinamico è una lacuna (task 1).
- Manca il job unico con `score.py whole` (task 2).
- Mancano Noir avviato dalla pipeline (task 5), le schede nella run con il suo motore (task 7), i segreti dei testi usciti (task 8), l'anagrafica di Daodan su cui cercare (task 9 e 10), la fonte osservata (task 11).
- Fino a lì la colonna dice «non misurato», con la causa.
- Una cella distingue `ingresso omesso` (l'archivio di solo codice lascia fuori `fixtures/`, `data/`, `dist/` e i file oltre 400.000 byte: può mancare ciò che serve ad avviare il programma), `passo fallito`, `zero trovati` e `non misurato`.

## 5. Che cosa si toglie

Nulla si cancella ora: l'elenco dice che cosa questo piano sostituisce.

- tolti il 20 novembre (decisione 5): `benchmarks/system-map/framework.cjs`, `framework.py`, `test_framework.py`, la fixture e, in `modal_map.py`, `fe`, `fe_read`, `fe_case`, `fe_image`.
- `modal_map.py`: `noir`, `noir_case` e `noir_image` dopo il task 5; `entries_case` e `links_case`, senza container, dopo il task 2.
- `benchmarks/system-map/traces.py`: `cards` e `verify` passano al nucleo (task 7); `ask` resta come prova a costo zero.
- `entries._method` e `Facts.local_function` come fonte del gestore: restano solo senza motore (task 3).
- Piano del 19 novembre: C4.15 passi 1, 2 e 2b (task 3 e 4: il lettore del framework è scip-typescript, che gira già dopo la preparazione); C4.15 passo 3 e C4.14 passo 3 (task 11); C4.14 passi 1b e 2 (task 5 e 4); C4 passi 2 e 2b (task 7); C6 passo 2 (task 8); G1, G2, G2b passo 2 (task 9 e 10); F1, F2, F3, F5 (task 12).
- `README.md`, tabella dei passi: «Proposed» sul passo dinamico, che è in `pipeline.STEPS`.
- Restano nel piano del 19 novembre, dopo la prova: C4 passi 3-5, C4.6, C4.7, C4.9, C4.10, C4.11, le parti D, E e H.

## 6. Da decidere

1. **Il container su Modal.** Le Modal Sandbox di `modal_pipeline.py` costano tempo e denaro. Raccomandazione: sì; senza, la prova resta senza scip-typescript e senza passo dinamico, come le misure di `benchmarks/system-map` finora. **Deciso dal proprietario il 20 novembre 2026: sì, il container su Modal.**
2. **Quali pagine apre la fonte osservata.** Raccomandazione: solo quelle del `webServer` che il progetto dichiara, come il passo dinamico avvia solo comandi dichiarati; senza, una lacuna. **Deciso dal proprietario il 20 novembre 2026, diverso dalla raccomandazione:** un'esplorazione che prova ogni rotta, ogni collegamento e ogni controllo raggiungibile. Semi: le rotte lette in modo statico (pre-mappa, Noir, le pagine del meta-framework) e i collegamenti trovati aprendo le pagine; per ogni pagina i controlli dall'albero di accessibilità, ognuno azionato una volta, con il registratore che dice quali funzioni partono. Prima si valuta una soluzione pronta per l'esplorazione (regola di AGENTS.md). Nel container, senza rete verso l'esterno e su dati di prova: un controllo che cancella, paga o invia agisce solo lì. Limiti da dichiarare nella risposta: pagine dietro accesso senza una credenziale di prova, moduli che chiedono valori, stati non raggiunti entro il tetto di passi.
3. **Il modello della ricerca.** Raccomandazione: tutti e due nella prova; multilingual-e5-large entra solo se fa ciò che EmbeddingGemma 2 non fa (G2b), con tempo e memoria misurati su una macchina senza scheda grafica. **Deciso dal proprietario il 20 novembre 2026: EmbeddingGemma 2**, quello che Daodan ha già (ONNX q4, circa 175 MB, solo processore). La prova da zero lo misura sulle stesse 531 richieste, accanto a multilingual-e5-large come riferimento (91-93 fra le prime tre): il numero dice quanto si lascia, non rimette in discussione la scelta. Confermato lo stesso giorno il file: il grafo di testo `onnx/model_q4.onnx` (174 MB), solo testo, senza gli encoder di immagini e audio; un GGUF di un privato e il q8 di Ollama non si provano ([spec della ricerca](../specs/2026-11-20-ricerca-e-pacchetto-di-review.md), motivo 12). Per il proprietario la ricerca è il primo passo del pacchetto di una review (task 10b) e serve anche ad abbinare i flussi (task 10c, dopo la sua misura); chi prepara il modello è una decisione aperta (stessa spec, «Decisioni aperte», 11).
4. **Una preparazione sola per analisi.** Raccomandazione: non in questo piano; la prova misura il tempo di ogni ripristino, poi si decide se riusare il container preparato, che `run_in_container(keep_root=True)` sa già committare. **Deciso dal proprietario il 20 novembre 2026, diverso dalla raccomandazione: si sistema ora** (task 1b).
5. **`framework.*`.** Raccomandazione: si cancellano dopo il task 4 se la prova ridà almeno i 53 controlli su 60 di quel lettore; altrimenti si porta in `entries.py` solo ciò che manca. **Deciso dal proprietario il 20 novembre 2026: cancellato subito**, perché va contro la regola di usare ciò che è pronto: prima lo strumento ufficiale che c'è (scip-typescript nel container). `framework.cjs`, `framework.py`, il suo test, la fixture e il job `fe` sono tolti; resta il numero nel README. Dove questo piano nomina `framework.*` vale lo strumento ufficiale.
