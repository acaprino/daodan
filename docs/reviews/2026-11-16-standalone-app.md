Verificare i cinque P2 prima di usare `benchmarks/standalone-app/ui_flow.py` come validazione della versione corrente.

Oggetto: i 34 percorsi modificati fra `334ea4d9643b4a396deba9a2216965a68d2c016b` e `b1f14ac08fa3cc0e1b047150ff505a93b01f5a57`: `AGENTS.md`, `CLAUDE.md`, `docs/specs/2026-11-16-app-standalone.md`, `benchmarks/standalone-app/**`, `prototypes/daodan-app/**`. Carico assunto: una persona, prototipo offline e server locale. La proposta distingue correttamente UI dimostrativa, dati locali e risultati storici; il backend completo resta fuori ambito.

1. **P2 — Il retry riattiva una demo invalidata dal cambio di contesto.** Posizione: `prototypes/daodan-app/index.html:135`, ramo `run-toggle` con stato `error`; invalidazione in `prototypes/daodan-app/assets/premap-workspace.js:396`.
   - **Comportamento:** «Riprova demo» attende un secondo e riporta lo stato a `running`.
   - **Problema:** durante l'attesa si può aprire «Repository» e cambiare branch, oppure scollegare l'accesso privato. L'invalidazione azzera progresso e stato, ma il callback precedente imposta comunque `running`. Il timer riparte sul contesto nuovo o assente e può rendere disponibile la sintesi senza un nuovo avvio. L'avvio normale a `prototypes/daodan-app/index.html:132` controlla invece il binding repository/branch.
   - **Correzione minima:** prima dell'attesa conservare il contesto e verificare, al ritorno, che sia ancora quello attivo e che il retry non sia stato invalidato; in caso contrario terminare senza riattivare la run. Provare anche cambio branch e logout durante il retry.
   - **Se ignorato:** il cambio di progetto non annulla affidabilmente l'avanzamento precedente e persiste uno stato incoerente nel browser.

2. **P2 — Il benchmark UI richiede conteggi superati dall'exporter corrente.** Posizione: `benchmarks/standalone-app/ui_flow.py:90`.
   - **Comportamento:** `real_inventory_counts` confronta i dati incorporati con 2.592 file, 16 linguaggi, 5 unità e 18 dipendenze.
   - **Problema:** `prototypes/daodan-app/index.html:79` e `prototypes/daodan-app/assets/premap-preview.json:1` contengono ora 2.738 file e 9 linguaggi, mantenendo 5 unità e 18 dipendenze. Anche con browser disponibile il controllo registra un fallimento e l'uscita finale è 1. Le 44/44 del risultato salvato appartengono al dataset precedente.
   - **Correzione minima:** verificare che contatori visualizzati e dati esportati coincidano, lasciando eventuali conteggi esatti a una fixture stabile; acquisire poi un nuovo risultato nel container e aggiornare il README solo con misure effettivamente ottenute.
   - **Se ignorato:** il benchmark fallisce sulla versione distribuita e il risultato storico non dimostra la correttezza dell'exporter aggiornato.

3. **P2 — Il browser del benchmark è vincolato all'host Windows.** Posizione: `benchmarks/standalone-app/ui_flow.py:34`.
   - **Comportamento:** Playwright avvia esclusivamente `C:/Program Files/Google/Chrome/Application/chrome.exe`.
   - **Problema:** il container Daodan usa Linux e non possiede quell'eseguibile. Il benchmark termina all'avvio del browser senza esercitare la UI; eseguirlo sull'host contraddice la regola del progetto. Il comando pubblicato in `benchmarks/standalone-app/README.md:31` non fornisce un percorso riproducibile nel container.
   - **Correzione minima:** usare Chromium disponibile nel container e documentare il comando che esegue lì l'intero benchmark, con i prerequisiti del browser installati nell'immagine.
   - **Se ignorato:** la verifica UI resta riproducibile soltanto nell'ambiente host usato per la vecchia misura, vietato dalle istruzioni attuali.

4. **P2 — Un nome Git valido può interrompere l'albero delle directory.** Posizione: `prototypes/daodan-app/assets/premap-workspace.js:162`, `prototypes/daodan-app/assets/premap-workspace.js:168`.
   - **Comportamento:** `directoryTree()` usa oggetti `{}` indicizzati dai segmenti dei percorsi Git; l'exporter acquisisce tutti i file tracciati a `prototypes/daodan-app/scripts/export_premap_preview.py:26`.
   - **Problema:** dopo un aggiornamento dell'inventario che includa, per esempio, `constructor/probe.ts`, `node.children['constructor']` trova la proprietà ereditata `Object` e `||=` non crea il nodo. Al segmento successivo `node.children` è assente e la composizione della pre-mappa si interrompe. Anche `__proto__` collide con una proprietà ereditata. Il dataset corrente non contiene questi percorsi: il problema riguarda il refresh documentato con nomi Git consentiti.
   - **Correzione minima:** creare tutti i dizionari `children` con `Object.create(null)` oppure usare `Map`; verificare un percorso annidato chiamato `constructor` e uno chiamato `__proto__`.
   - **Se ignorato:** un file aggiunto al repository può rendere inutilizzabile l'intera pre-mappa dopo la rigenerazione dei dati.

5. **P2 — La calcolatrice non replica l'arrotondamento del finding mostrato.** Posizione: `prototypes/daodan-app/index.html:120`, `prototypes/daodan-app/index.html:121`.
   - **Comportamento:** il pannello presenta un ricalcolo della formula del benchmark, ma usa `Math.round((n+Number.EPSILON)*100)/100`.
   - **Problema:** il sorgente Python citato usa `round(..., 2)`, che tratta diversamente i pareggi. Con netto **1,25 €** e sconto **10%**, lo sconto esatto `0.125` diventa `0.12` in Python e `0.13` nella UI: totale atteso **1,38 €** contro **1,37 €**, candidato con doppio sconto **1,23 €** contro **1,21 €**. Sono valori ammessi dai controlli. Il confronto è ricavato dalle formule, non eseguito in questa review.
   - **Correzione minima:** allineare la funzione di arrotondamento alla semantica del sorgente mostrato e aggiungere questo caso al benchmark della calcolatrice.
   - **Se ignorato:** il lettore può ottenere importi diversi dal comportamento che il finding dichiara di spiegare.

**Verdetto:** correggere i cinque P2. Nessun P1 confermato nel perimetro del prototipo. Nessuna correzione applicata al sorgente.

**Copertura:** letti diff e sorgenti dei flussi repository pubblica/privata, preferenza branch, invalidazione e persistenza; pre-mappa, alberi e dettagli; avvio senza obiettivo, timer, crescita del grafo, pausa, errore, retry e sintesi; filtri e inspector; obiettivo facoltativo della review, perimetro storico e testo da inferire; decisioni, copia e report HTML storico. Esaminati exporter e contratti canonici collegati in `snapshot.py`, `pipeline/__init__.py`, `premap/__init__.py`, `technologies.py`, `modules.py` e `snapshot_store`; bootstrap HTTP, richiesta/claim/rilascio/chiusura in `visual.py` e `mcp_service.py`, con i relativi test esistenti letti. Verificati staticamente riferimenti locali di CSS/font, sorgenti SmoothUI, registry, licenze presenti, configurazione di build e lockfile. Il bundle minificato è stato considerato come artefatto di packaging, senza revisione riga per riga; il font è stato controllato come asset WOFF2, senza rendering.

**Evidenza e lacune:** solo letture statiche, Git e ispezione di dati; dipendenze core lette alla revisione fissata per evitare le modifiche contemporanee di altre sessioni. Nessun codice del progetto, test, browser, build, installazione o exporter è stato eseguito sull'host. Il daemon Docker non è disponibile (`npipe docker_engine` assente): nuove prove nel container non eseguite. I 9 controlli HTTP e i 44 controlli UI salvati sono misure storiche Windows, non risultati di questa review. Il vecchio risultato UI registra inoltre un hash HTML diverso; la prova principale della sua obsolescenza è il conteggio dei dati. Le formule base sono state lette anche da `2889c58`; il candidato storico `109c1d7` non è disponibile come tree locale, quindi la sua riga è stata verificata nei record e nelle evidenze salvate. Login, checkout, LLM, processi reali, integrazione produttiva e compatibilità fra provider restano fuori ambito dichiarato; non sono stati trasformati in difetti del prototipo.

Passo successivo: avviare il runtime container configurato per Daodan e verificarlo con `docker info`.
