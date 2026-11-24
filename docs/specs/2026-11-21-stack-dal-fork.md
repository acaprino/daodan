# Stack dal fork di stack-analyser

**Stato:** quarta stesura, approvata dal proprietario il 21 novembre 2026 insieme alle «Scelte di chi scrive». La stesura precedente è stata rivista in [`docs/reviews/2026-11-21-stack-dal-fork.md`](../reviews/2026-11-21-stack-dal-fork.md): questa ne risolve i rilievi B1, B2 e M1–M7. Il processo com'è nel codice: [Codebase Map, «Lo step `stack`»](../plugins/codebase-map.md#lo-step-stack).

Al 24 novembre 2026:

- **Codice:** applicato nel ramo `stack-dal-fork`, non unito a `develop`: l'unione la decide il proprietario. Piani [1](../plans/2026-11-21-stack-dal-fork-1-fork.md) e [2](../plans/2026-11-21-stack-dal-fork-2-benchmark.md) consegnati; [3](../plans/2026-11-22-stack-dal-fork-3-passaggio.md), parte A fatta e pubblicata (rilasci `1.27.6-daodan.3`, `.4` e `.5`, fork rinominato `acaprino/stack-analyser-daodan`), B1–B5 nel ramo, B6 in corso.
- **Scelte:** le sette «Scelte di chi scrive» del piano 3 confermate dal proprietario il 24 novembre 2026.
- **Diverso dal disegno:** il fork gira sul Node che Daodan scarica al primo uso (`indexers.runtime.node`), non sul Node della macchina che dicono 2.1 e «Vincoli». Le menzioni delle variabili d'ambiente nei sorgenti non si fanno più (scelta 2 del piano 3).
- **Prova con il rilascio vero `.3`**, suite locale con `DAODAN_STACK_ANALYSER` su un container Linux con Node 22: 4.401 passati, 11 falliti, 140 saltati. Gli 11: Quarkus non riconosciuto dalle sue estensioni (2), il valore di un'immagine Docker dichiarata ridotto dal fork (7), una distribuzione Python locale letta come esterna (2). Corretti nel fork, ramo `feature/stack-detection`, commit `69c77c2`…`348051b`, CI verde (run 45410124486). Il rilascio `.4` è pubblicato (tag `v1.27.6-daodan.4`, costruito da GitHub Actions da `ff2fef4`) . Il rilascio `.5` (tag `v1.27.6-daodan.5`, da `453a2a9`) riprende i segni veri che il porting aveva lasciato fuori e dà a uno starter di Spring Data il suo server: è la scelta del proprietario del 24 novembre 2026, «più cose riconosciamo e meglio è». Daodan è fissato a `.5`: suite locale, non Modal, con il rilascio `.5` vero sullo stesso container (Linux, Node v22.23.5): 4.415 passati, 0 falliti, 140 saltati; senza il rilascio (misurato con `.4` fissato): 4.316 passati, 0 falliti, 239 saltati.
- **Aperti noti:** un test di `tests/test_codebase_map_app.py` instabile per una corsa in `engine_pass`, che a fine passaggio riscrive la pre-mappa senza runner (c'era prima, il nuovo tempo lo mostra); 4.441 problemi di lint vecchi nel fork, mostrati e non bloccanti nel suo flusso di rilascio; nel fork, `replace => ../local` di Go e i repository `path` di Composer ancora letti come esterni; 37 marchi nuovi in `daodan/data/marks` senza cornice, diversi dagli altri; la voce «Avro» del CNCF non si unisce più ad «Apache Avro» del fork e compare due volte (`avro`, `avro-cncf`); `technologies.state` non scrive più la pre-mappa quando legge lo stato.

«Verifica», riga per riga (Modal non era raggiungibile dalla macchina di questo lavoro):

| Riga | Stato |
| --- | --- |
| Nessuna perdita | Aperta. Il piano 2, con il rilascio `.2` e la traduzione nel benchmark, non perde nomi attesi su 178 fixture su 180. Il giro sul corpus dopo il passaggio aspetta Modal |
| Scansione veloce | Scritta: `test_a_fast_scan_keeps_the_signs_of_the_sources_it_did_not_run` (`tests/test_codebase_map_stack_sources.py`) |
| Senza Node | Scritta: `test_without_the_tool_the_previous_signs_stay_and_a_gap_says_why` (`tests/test_codebase_map_stack_sources.py`), `test_an_install_that_failed_is_not_tried_again_in_the_same_process` (`tests/test_codebase_map_stack_analyser.py`) |
| Tempo | Aperta. «Prima» e «dopo» misurati dal piano 2, con `.2`: scansione veloce, mediana 0,013 s col registro, 0,523 s col fork. Dopo il passaggio non misurato: aspetta Modal |
| Nessun codice eseguito | Aperta. La prova con l'installazione vera (`cli()` e il Node di Daodan) aspetta Modal (piano 3, B6) |

Aspetta Modal anche la nuova misura su `develop` `68b784e` (piano 3, punto 7 di «Che cosa il piano 2 ha trovato»).

Il riconoscimento delle tecnologie di un progetto passa dal registro di Daodan al programma [`acaprino/stack-analyser-daodan`](https://github.com/acaprino/stack-analyser-daodan) (prima `acaprino/stack-analyser`), il «fork». Tocca due repository: il fork e Daodan.

## Perché

Il proprietario chiede «confinamento di responsabilità, pulizia, ordine e unico punto di analisi». Oggi le conoscenze stanno in due posti: le regole del fork (1.076 tecnologie al commit `c8476c6`) e `data/service-registry.json`, che Daodan confronta in Python con ciò che legge dal progetto. Il registro nasce dalle regole di stack-analyser 1.27.6 più aggiunte curate in Daodan, e il fork non gira mai durante un'analisi.

## Parole

- **Dichiarazione:** un pacchetto, un'immagine o un'azione che un file del progetto nomina, con il file e, se nota, la riga.
- **Fonte:** chi ha letto una dichiarazione. Il fork stesso, un lettore di Daodan (`requirements`, `jvm-files`…), Renovate, il modello di un build tool (`gradle`, `maven`…).
- **Risultato:** una tecnologia riconosciuta, con le sue prove.
- **Prova:** ciò che ha fatto riconoscere una tecnologia: che cosa, in quale file, a quale riga, da quale fonte.
- **Scansione veloce:** quella che parte a ogni modifica e dal server MCP, senza container (`pipeline.run(stop="stack", fast_scan=True)`).
- **Scansione completa:** il passaggio staccato, con Renovate e i build tool nel container.
- **Registro:** `data/service-registry.json`. **Aggiunte:** `data/registry-additions.json`.

## Decisioni del proprietario

Prese il 21 novembre 2026, nell'ordine.

1. **Un confine a tre.** Il fork riconosce ciò che il progetto dichiara. L'analisi successiva (flussi e mappa del sistema) trova ciò che il codice usa senza dichiararlo, come una chiamata HTTP a un servizio senza SDK. Il registro è anagrafica: nome, categoria, tipo, sito, marchio.
2. **Riconosce sempre il fork**, anche nella scansione veloce. Fra veloce e completa cambia solo l'ingresso.
3. **Ogni risultato ha la sua fonte.**
4. **La scansione veloce tocca solo ciò che viene dalle sue fonti:** aggiunge, aggiorna o ritira quello, e lascia il resto com'era dall'ultima scansione completa.
5. **Renovate non è il riconoscitore:** «utile per trovare nuovi perimetri, ma non è il tool corretto». Resta una fonte di dichiarazioni nella scansione completa.

## Obiettivi

- Una tecnologia compare in `technologies.json` solo perché il fork l'ha riconosciuta, in entrambe le scansioni.
- Il fork riconosce da due ingressi: i file che legge da solo e le dichiarazioni che Daodan ha già (dai suoi lettori nella veloce; anche da Renovate e dai build tool nella completa).
- Ogni prova dice file, riga se nota, e fonte.
- Dopo una modifica nessun risultato sparisce solo perché la sua fonte non ha girato.
- Sul corpus nessun nome atteso che Daodan trova oggi va perso, tranne le perdite elencate per nome («Verifica»).

## Fuori scopo

- Riconoscere servizi dall'uso nel codice.
- Insegnare al fork i formati che i lettori di Daodan leggono già (`requirements` con altri nomi, `setup.cfg`): arrivano come dichiarazioni.
- Riordinare le tipologie del fork; proporre le modifiche a `specfy/stack-analyser`; la pipeline che ne segue gli aggiornamenti.

## Da evitare

- Un secondo riconoscitore nel prodotto, anche temporaneo: il confronto fra vecchio e nuovo vive nei benchmark.
- Concetti di Daodan nel codice del fork.
- Segni di riconoscimento nelle aggiunte di Daodan.

## Vincoli

- **Nessun codice del progetto eseguito.** Il fork legge file e basta. Gira sulla macchina, fuori dal container, quindi ha il test che AGENTS.md chiede a ogni strumento lanciato sull'host: un file del progetto che, se eseguito, lascia un segno.
- **Node sulla macchina.** È un requisito nuovo di Daodan. Senza Node il fork non gira e vale la decisione 4: i risultati restano quelli dell'ultima scansione riuscita, con la causa fra i gap.
- **Tempo della scansione veloce.** Gira a ogni modifica sotto `project_lock`. Oggi il fork impiega circa 3,3 secondi solo per caricare le regole («Misure»).
- **ID stabili.** Li citano `review_roster.TECHNOLOGY_ROLE`, gli `id` dei nodi esterni della mappa, i marchi in `data/marks/` e gli attesi di `benchmarks/system-map`. Eccezioni, entrambe per doppioni: `react-email` diventa `reactemail`, l'ID che stack-analyser 1.27.6 aveva già; la regola `jinja2` del fork, nata in questo ramo, prende `jinja`, l'ID del registro.
- **Forma di `technologies.json`.** I consumatori (`system_brief.py`, `visual.py`, `app_view.py`, `review_roster.py`, `mcp_service.py`, `snapshot.py`) leggono di ogni voce `category`, `type`, `mark` e `signs` con `sign`, `value`, `path`, `line`, `strength`. La forma resta; a ogni segno si aggiunge la fonte.
- **Versione fissata.** Un rilascio preciso del fork, verificato con sha256, con le dipendenze dentro: si scompatta e gira, senza installare nulla.

## Strade considerate

1. **Il fork legge tutto da solo, nel container.** Scartata dopo la review: la scansione veloce non ha container, quindi a ogni modifica le tecnologie sparirebbero (B1); il fork salta cartelle che Daodan analizza (M1); andrebbero riscritti nel fork lettori che Daodan ha già (M4).
2. **Daodan applica in Python le regole del fork.** Scansione veloce in millisecondi e nessun requisito nuovo. Scartata dal proprietario: riconosce sempre il fork (decisione 2).
3. **Il programma del fork gira in entrambe le scansioni, con ingressi diversi.** Scelta. Costa Node sulla macchina e il lavoro per rendere rapido l'avvio (1.5).

## Disegno

### 1. Nel fork

1. **Test verdi.** Falliscono 15 test su 2.326: 14 snapshot non rigenerati e due test che danno al lettore dei workflow un file vuoto.
2. **Prova strutturata.** Oggi il motivo di un riconoscimento è una frase (`react matched: /^react$/`). Ogni tecnologia porta anche un elenco di prove: da che cosa viene (pacchetto, immagine, azione, risorsa Terraform, file, estensione, variabile, sorgente), il valore, il file, la riga se nota, la fonte. La frase resta.
3. **Dichiarazioni in ingresso.** Un'opzione del CLI e della libreria accetta un elenco di dichiarazioni `{tipo, nome, versione?, file, riga?, fonte}`. Il fork le riconosce con le stesse regole e ne riporta la fonte nella prova. Ciò che legge da solo ha come fonte il fork.
4. **Perimetro.** Oggi il fork salta per nome, a ogni profondità, cartelle come `tests`, `public`, `bin`, `vendor`, `migrations`, e il CLI non permette di cambiarlo. Un'opzione sostituisce l'elenco delle cartelle da saltare: lo decide chi lo lancia.
5. **Avvio rapido.** Le regole si caricano da un solo file invece che da più di mille. L'obiettivo è misurato nel benchmark del fork sul progetto di prova `py-fastapi-compose`: meno di un secondo dall'avvio al risultato.
6. **I segni che ha solo il registro.** 146 ID che il fork non ha, con 194 pacchetti; e, sugli ID in comune, 173 pacchetti, 51 espressioni e 1 variabile che il fork non elenca. Ognuno diventa una regola del fork o entra in un elenco di differenze volute, con il motivo (esempi: le risorse Terraform di App Service che il registro dava ad `azure.staticwebapps`; la variabile `ROOLBAR_`, un refuso). I 22 nomi di file e gli 8 segni di sorgente che il registro ha in più sono cose che il fork riconosce con un lettore invece che con una regola (`Dockerfile`, gli import Swift): per ognuno un test lo prova, altrimenti diventa una regola. I segni che le aggiunte dichiarano sbagliati (`wrong_signs`, 13 voci) diventano correzioni delle regole. I due doppioni noti seguono il vincolo sugli ID; prima di portare una voce si cerca un doppione anche per nome e per pacchetti.
7. **Rilascio.** Un tag e il pacchetto di `npm pack` come asset del rilascio GitHub, con le dipendenze di esecuzione incluse.

### 2. In Daodan

1. **Lo strumento.** Daodan scarica una volta il rilascio fissato, ne verifica lo sha256 e lo esegue con il Node della macchina. Un test prova che un file del progetto fatto per lasciare un segno, se eseguito, non lo lascia.
2. **Il passo `stack`.** Scrive le dichiarazioni che la pre-mappa ha, ognuna con la sua fonte, lancia il fork sul progetto con quell'elenco e con le cartelle escluse dalla pre-mappa, e ne legge il risultato al posto di `service_registry.run`. L'assegnazione ai moduli resta: una tecnologia è del modulo che possiede il file della sua prova. Corrispondenza con i segni di oggi: una prova di pacchetto, immagine, azione, risorsa, file o sorgente è `declared`; una prova di variabile è `mentioned`, come oggi; una tecnologia che ha solo prove di estensione non esce, perché i linguaggi sono di go-enry.
3. **La regola delle fonti.** Il record tiene per ogni segno la fonte e la scansione che l'ha prodotto. Una scansione sostituisce i segni delle fonti che ha eseguito e conserva gli altri. Un segno conservato dice da quale scansione viene. Una tecnologia resta finché ha almeno un segno.
4. **Gli host negli URL.** Restano fuori dal riconoscimento, come oggi: `registry_hosts.py` li legge dai sorgenti con tree-sitter e li dà come `mentioned`. L'elenco degli host viene dal catalogo del fork. Le menzioni che il fork calcola da solo non si usano.
5. **Il registro come anagrafica.** `registry_build.py` prende ID, nome, tipologia e host dal rilascio fissato, e unisce Simple Icons, CNCF Landscape e le aggiunte. Le aggiunte perdono `signs` e `wrong_signs`; un test lo impedisce in futuro. La `category` curata resta; per un ID nuovo viene da una tabella tipologia → categoria.
6. **Rimozioni.** In `service_registry.py`: `check_packages`, `check_files`, `check_env`, `CHECKERS`, `run`, `recognize`. Poi `stack_source.py` (gli import Swift e le chiamate Elixir li riconosce il fork da solo), `specfy_rules.mjs`, e in `registry_build.py` i comandi che scrivono segni nelle aggiunte (`derive`, `verify-additions`, `model-input`, `accept`). Le attese dei test `test_corpus_*_rules.py` passano nei test del fork.
7. **Benchmark.** In `benchmarks/project-model`, per progetto: `technologies.json` prima e dopo, i nomi attesi persi e quelli nuovi, il tempo della scansione veloce.

### 3. Ordine

1. Fork: 1.1, 1.2, 1.3, 1.4.
2. Fork: 1.5 e 1.6, poi 1.7.
3. Daodan: 2.1 e 2.7. Il passo `stack` usa ancora il registro; il benchmark confronta i due.
4. Daodan: 2.2–2.6 in un solo cambio, quando «Verifica» passa.

## Verifica

- **Nessuna perdita.** Sul corpus di `benchmarks/project-model`, su Modal, con la scansione completa: per ogni progetto, nessun nome atteso presente in `technologies.json` prima del cambio manca dopo, tranne un elenco di perdite accettate scritto per nome nel README, ognuna con il motivo. I nomi nuovi fuori dagli attesi sono elencati accanto.
- **Scansione veloce.** Un test modifica un manifest dopo una scansione completa: il risultato della fonte modificata cambia, quelli delle fonti non eseguite restano e dicono da quale scansione vengono.
- **Senza Node.** Un test prova che il passo finisce, conserva i risultati precedenti e scrive il gap con la causa.
- **Tempo.** Il benchmark riporta il tempo della scansione veloce prima e dopo.
- **Nessun codice eseguito.** Il test del vincolo.

## Rischi

| Rischio | Che cosa si fa |
| --- | --- |
| La scansione veloce passa da millisecondi a circa un secondo, sotto `project_lock`, a ogni modifica | 1.5 e la misura in «Verifica». Se l'obiettivo non si raggiunge, il lavoro si ferma al passo 3 e si torna dal proprietario |
| Chi installa Daodan non ha Node | Il passo non fallisce: conserva i risultati e segnala la causa |
| Un risultato conservato è vecchio: il file della sua fonte è cambiato ma la scansione completa non è ancora ripartita | Il segno dice da quale scansione viene; la completa lo sostituisce |
| Il fork e un lettore di Daodan leggono lo stesso file in modo diverso | Entrambe le prove restano, ognuna con la sua fonte: la differenza si vede |
| Ciò che sa solo un build tool eseguito arriva solo con la scansione completa | È il comportamento di oggi; la decisione 4 lo migliora, perché dopo la completa non sparisce più alla prima modifica |
| Il fork si allontana da `specfy/stack-analyser` | Fuori scopo qui; la pipeline di aggiornamento è un lavoro successivo |

## Scelte di chi scrive

1. **Il fork gira sempre sulla macchina, mai nel container**, anche nella scansione completa: un solo modo di lanciarlo.
2. **Nella scansione veloce il fork riceve anche le dichiarazioni dei lettori di Daodan**, non solo i file: così non si riscrivono nel fork lettori che esistono.
3. **Gli host negli URL restano a `registry_hosts.py`** (2.4), e il lettore tree-sitter non si sostituisce.
4. **Una variabile d'ambiente vale `mentioned`**, come oggi, anche se per il fork è una tecnologia piena.
5. **Si tolgono i comandi che propongono pacchetti per le aggiunte** (2.6): la loro funzione, se serve ancora, andrà rifatta verso il fork.
6. **Rilascio su GitHub**, non su npm, e nessuna pull request verso `specfy/stack-analyser`.

## Lasciato a chi costruisce

- I nomi dei campi della prova, delle opzioni del CLI e del campo che porta fonte e scansione nei segni.
- La versione minima di Node e il numero di versione del rilascio.
- Come generare la prima stesura delle regole dal registro e come dividerle in commit.
- L'aggiornamento di `docs/plugins/`, `REGISTRY-NOTICES.md`, della tabella di supporto e della riga «Stack» in `2026-11-15-pipeline-di-analisi.md`, che prometteva lo stack in millisecondi: fatto nel piano 3, task B7.

## Misure

Tutte del 21 novembre 2026, con script provvisori che 2.7 e i benchmark del fork rendono ripetibili.

- **Regole contro registro.** Le regole del fork a `c8476c6`, esportate con il raccoglitore di `registry_build.py`, confrontate con il registro distribuito (2.562 voci, 1.162 con segni): da qui i numeri di 1.6.
- **Avvio.** Su questa macchina, tre prove: circa 3,3 secondi per caricare le regole e riconoscere tre pacchetti; circa 4,8 secondi per analizzare `py-fastapi-compose`; 0,2 secondi per Node da solo.
- **Scansione veloce senza container.** `snapshot.py:1570`, `mcp_service.py:499`, `pipeline/__init__.py:66`: una fonte con comandi lì è `not_run` (`premap/__init__.py:387`).
- **Cartelle saltate.** `IGNORED_DIVE_PATHS` in `src/provider/base.ts` del fork.
