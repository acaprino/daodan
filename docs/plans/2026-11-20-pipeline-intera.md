# Piano: la pipeline intera, dall'albero sintattico alla ricerca

**Stato:** In parte. È l'indice dei tre piani per aspetto e tiene ciò che è di tutti: l'ordine dei task, la prova da zero e ciò che si toglie. Di suo ha un solo task, il 12, aperto.

**Obiettivo:** ogni pezzo attaccato a un passo che Daodan ha già, in ordine, e una prova che rifà tutto da zero sui cinque casi.

**Vincoli:** nessun pezzo legge o installa di nuovo ciò che un passo già legge o installa; prima il test rosso, poi il codice; ogni task tocca solo i file che nomina. I passi e ciò che gira sull'host o nel container sono in [`docs/plugins/codebase-map.md`](../plugins/codebase-map.md#pipeline) e in `docs/specs/2026-11-15-pipeline-di-analisi.md`.

## 1. Ordine e stato dei task

L'ordine è quello della tabella. Lo stato è quello del codice; i punti aperti di ogni task sono nel suo piano.

| Task | Titolo | Stato | Piano |
| --- | --- | --- | --- |
| 0 | Nessuna esecuzione sull'host nelle review e nei test | fatto | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 1 | Il container nella run della mappa su Modal | fatto, con punti aperti | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 1b | Una preparazione sola per analisi | fatto, non misurato su Modal | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 2 | Un job per tutta la catena e la sua tabella | fatto; prova 0 con Qwen e Opus da fare | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 2b | Tre corse sullo stesso progetto | misurato, una corsa per tipo | [analisi unificata](2026-11-20-analisi-unificata.md) |
| 3–8 | Gestore dal motore, evento ed etichetta, Noir nella pre-mappa, forme, schede dei percorsi, la mappa non perde ciò che rifiuta, i flussi dicono ciò che non sanno, Secretlint | fatto, tranne un punto di 7b | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 9–10c | Anagrafica dei flussi, ricerca, pacchetto di una review, embedder | non iniziato | [ricerca e pacchetto di review](2026-11-20-ricerca-e-pacchetto-di-review.md) |
| 11, 11b | La fonte osservata; gli eventi fra pagina e guscio Tauri | 11 in parte, 11b fatto | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 12 | La mappa nel grafo dell'app | non iniziato | qui sotto |
| 13 | Lo strumento ufficiale del framework (13a–13f) | fatto, con punti aperti per framework | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 14 | Le rotte che nascono all'avvio (14a–14j) | misurato: le sorgenti che caricano il framework non si collegano | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 15, 16 | La forma della risposta; i contratti fra repository | non iniziato | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |
| 17–19 | Lettori di GitNexus, chiave dello store, identità della dichiarazione, servizi in ingresso | chiusi o fermi con la causa | [ingressi e flussi](2026-11-20-ingressi-e-flussi.md) |

### Task 12: la mappa nel grafo dell'app

`daodan/core/app_view.py` disegna oggi il grafo ai livelli codice e infrastruttura. Manca: la mappa del sistema e l'anagrafica dei flussi come vista di prodotto (`app_view.product`), l'apertura sul posto e il trascinamento, un flusso acceso, e la prova nel browser nel container.

Test: `benchmarks/standalone-app/app_graph.py`, da scrivere. Riusa: `App.serve`. Dipende dai task 9 e 10.

## 2. La prova da zero

Dopo `modal deploy benchmarks/system-map/modal_map.py`, due comandi:

```text
python benchmarks/system-map/modal_map.py whole --tag TAG --tar CASO=ARCHIVIO ... --models qwen,haiku,opus --reps 2
python benchmarks/system-map/score.py whole benchmarks/system-map/results/system/TAG
```

Gli archivi vengono da `python benchmarks/system-map/code_archive.py OUT.tar REPOSITORY@COMMIT`, sul commit dei riferimenti. Una tabella per caso, una riga per modello:

| Colonna | Da dove | Oggi |
| --- | --- | --- |
| ingressi del riferimento con un candidato nello stesso file, per tipo e per fonte, con gli zeri e gli ingressi contati a parte: non dice che il controllo o il gestore sia quello | `entries.py measure` | c'è |
| controllo e gestore giusti, su un piccolo insieme confermato dal proprietario | da scrivere | manca |
| nodi contro il riferimento (ritrovati, profondità 0 e 1, precisione, `inside`); flussi in tre numeri distinti (abbinati uno a uno, somiglianza media alla profondità 1, estremi giusti per ruolo); frecce rifiutate; stabilità fra due giri indipendenti | `score.py system`, `score.py stable` | c'è |
| flussi certificati e rifiutati, con i motivi | `daodan/core/flow_paths.py` | manca nella tabella con il modello |
| ricerca, sui quattro casi delle 531 richieste (262 su 131 flussi, 269 su parti): quante hanno una risposta nella mappa di Daodan, e la risposta giusta prima e fra le prime tre | le richieste di `embed_queries.py`; task 10 | manca |
| segreti mascherati, nell'archivio e nei testi usciti | `code_archive.py`, `secret_mask.tool_result` | c'è |
| costo, token, tempo per passo, preparazione compresa | `summary.json`, eventi della pipeline | c'è |

- Modelli: Qwen dal gateway (`--models qwen`, secret Modal `daodan-gateway`) e Haiku 5.5 sono il metro; Opus 5.5 sta accanto.
- Soglie: quelle proposte nel README di [`benchmarks/system-map`](../../benchmarks/system-map/README.md), da confermare dal proprietario.
- Una colonna che manca dice «non misurato», con la causa. Una cella distingue `ingresso omesso` (l'archivio di solo codice lascia fuori `fixtures/`, `data/`, `dist/` e i file oltre 400.000 byte), `passo fallito`, `zero trovati` e `non misurato`.
- Fatta: senza modello e con Haiku 5.5, sui cinque casi. I numeri sono nel README del benchmark, «Il mappatore con un modello, sull'intero sistema, alla cieca».

## 3. Che cosa si toglie

Ancora nel repository, da togliere quando la condizione è vera:

- `benchmarks/system-map/modal_map.py`: `noir`, `noir_case` e l'immagine di Noir (la sorgente `daodan/core/premap/noir.py` è nella pipeline: si possono togliere); `entries_case` e `links_case`, senza container, dopo la prova 0 completa.
- `benchmarks/system-map/traces.py`: `cards` e `verify`, che nel nucleo sono `daodan/core/flow_paths.py`; `ask` resta come prova a costo zero. Con loro `test_traces.py`, dopo aver controllato che i suoi sei casi siano coperti dai test del nucleo.

## 4. Decisioni prese

1. **Il container su Modal: sì.** Senza, la prova resta senza scip-typescript e senza passo dinamico.
2. **La fonte osservata esplora:** prova ogni rotta, ogni collegamento e ogni controllo raggiungibile, nel container, senza rete verso l'esterno e su dati di prova; non solo le pagine del `webServer` dichiarato. Motivo e limiti: `docs/specs/2026-11-19-interfacce-del-progetto.md`, 7.4.
3. **Il modello della ricerca è EmbeddingGemma 2**, quello che Daodan ha già (ONNX q4, solo processore). multilingual-e5-large resta accanto come riferimento nella prova: il numero dice quanto si lascia, non rimette in discussione la scelta. Motivo: `docs/specs/2026-11-20-ricerca-e-pacchetto-di-review.md`, motivo 12.
4. **Una preparazione sola per analisi:** fatta (task 1b).
5. **Un lettore del framework scritto a mano non entra:** vale lo strumento ufficiale (scip-typescript nel container, poi gli strumenti dei framework del task 13).
