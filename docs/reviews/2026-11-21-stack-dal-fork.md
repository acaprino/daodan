# Review della spec «Stack dal fork di stack-analyser»

**21 novembre 2026.** Documento esaminato: [`docs/specs/2026-11-21-stack-dal-fork.md`](../specs/2026-11-21-stack-dal-fork.md), nella versione «il fork legge e riconosce da solo».

**Metodo.** Sei revisori senza memoria della conversazione, secondo il protocollo di review di [google/elephant-goldfish-model](https://github.com/google/elephant-goldfish-model) (commit `8e2a5ed`): visione d'insieme, alternative, comprensione, critica del design, struttura, stile. Non eseguite: il secondo sguardo d'insieme, che ricontrolla dopo le correzioni, e la prontezza all'implementazione, che riguarda il piano. I rilievi sotto sono uniti e senza doppioni; «verificato» vuol dire controllato sul codice da chi ha unito i rapporti.

**Esito.** Due bloccanti, sette importanti, e una serie di incoerenze interne al documento. La spec non è pronta per il passaggio definitivo in Daodan. I compiti 1–5 del piano 1 (test verdi, prova strutturata, confronto con Renovate) non dipendono da nessun rilievo e possono partire.

## Bloccanti

### B1. La scansione veloce resta senza tecnologie

*Revisori: visione d'insieme, alternative, critica del design. Verificato.*

Hook e server MCP eseguono `pipeline.run(stop="stack", fast_scan=True)` (`snapshot.py:1570`, `mcp_service.py:499`), cioè senza runner (`pipeline/__init__.py:66`). Una fonte che ha comandi lì è `not_run` (`premap/__init__.py:387`). Oggi il registro riconosce subito dai fatti dei lettori che girano sull'host; con il fork come comando di container, a ogni modifica `frameworks`, `services` e `tools` restano vuoti finché non finisce il passaggio staccato. La spec della pipeline li promette «senza aspettare il container» (`2026-11-15-pipeline-di-analisi.md`, punto 5 del servizio). La spec tratta solo il caso «manca il container» e non nomina questo percorso, che è quello normale. `review_roster.unit_technologies` non distingue «nessuna tecnologia» da «non ancora eseguito».

La regola invalicabile riguarda il codice del progetto; il fork non ne esegue, quindi il container è una scelta e non un obbligo. Daodan però oggi non esegue Node sull'host: lì servirebbe una dipendenza nuova sulla macchina dell'utente.

Strade:
1. **Eseguire il fork anche sull'host**, con il test del file che lascia un segno. Un solo riconoscitore, sempre. Chiede Node sulla macchina dell'utente.
2. **Riusare l'ultimo risultato del container** per i file con hash invariato, e segnare «in sospeso» il resto. La prova per file di 1.2 lo rende possibile. Chiede uno stato in più che i sei consumatori devono leggere.
3. **Tornare a «i lettori leggono, le regole del fork riconoscono»**: il registro si genera solo dal catalogo del fork e Daodan applica quelle regole ai fatti che ha già, come oggi. Nessun comando nuovo, percorso veloce intatto. Il fork resta l'unico catalogo, ma non l'unico motore: la logica di confronto resta anche in Python.

### B2. La soglia non misura ciò che l'obiettivo dichiara

*Revisore: critica del design. Verificato sul README del benchmark.*

475/569 e 232/518 vengono da `replay_registry_coverage.py`, che applica solo `check_packages` e `check_files` alle dichiarazioni di Renovate. Il prodotto riconosce anche dai pacchetti dei modelli di build (`premap/maven.py` dichiara `packages`), dalle variabili, dagli host e dai sorgenti. Il README cita `jvm-spring-boot-managed`, dove Spring MVC e Data JPA arrivano solo dal modello Gradle: è proprio la perdita che la spec chiama «non misurata». Lo script inoltre importa funzioni che 2.5 rimuove: dopo il passo 4 la misura non si può rieseguire. Il confronto di `modal_stack.py` prima e dopo non ha un criterio di passaggio.

Correzione: la soglia è la differenza di `technologies.json` per progetto, prima e dopo: zero nomi attesi persi, tranne un elenco nominativo di perdite accettate.

## Importanti

### M1. Il fork non entra in cartelle che Daodan analizza

*Critica del design. Verificato.* `IGNORED_DIVE_PATHS` (`src/provider/base.ts`) salta per nome, a ogni profondità, fra le altre `tests`, `e2e`, `migrations`, `public`, `static`, `bin`, `build`, `dist`, `vendor`, `.devcontainer`, `.gitlab`. Il CLI non ha opzioni per cambiarlo. La spec prevede solo il filtro inverso, e il confronto 305/373 classifica le mancanze per formato, non per cartella. Correzione: il perimetro diventa un parametro del fork e 1.5 lo misura.

### M2. Sui file `.env` la spec descrive un lettore che non c'è

*Visione d'insieme, critica del design. Verificato.* Il fork legge solo `.env*.example`, `.sample` e `.template`, mai `.env`; 1.3 non lo aggiunge. In più, nel fork una variabile dà una tecnologia piena, mentre in Daodan oggi è solo `mentioned`: una scelta del 17 novembre che aveva ridotto i servizi di troppo. Correzione: dire cosa si legge davvero e fissare che una prova `env` vale `mentioned`.

### M3. Le menzioni di host contraddicono il confine

*Visione d'insieme, critica del design, comprensione, struttura.* Gli import Swift escono dal passo `stack` perché «uso nel codice», ma gli URL nei letterali dei sorgenti restano, letti dal fork con espressioni regolari al posto del lettore tree-sitter di oggi (`registry_hosts.py`). Nessuna voce della sezione 1 dice che il fork le produce, né che cosa sono. Correzione: escono dal passo come gli import, e `registry_hosts.py` resta a disposizione dell'analisi successiva; oppure si motiva l'eccezione.

### M4. «Unico punto» vale per le regole, non per la lettura

*Visione d'insieme. Verificato in parte.* Gli stessi manifest li leggono il fork, Renovate e i lettori di Daodan: `premap/requirements.py` segue già `-r` e i nomi alternativi, `python_build.py` legge già `setup.cfg`. 1.3 riscrive in TypeScript formati già coperti, e ogni formato futuro costa un lettore nel fork. Questo costo permanente non è scritto. Correzione: scriverlo, oppure rivedere la scelta alla luce di B1, strada 3.

### M5. Il fatto `packages` del fork non entra «senza adattatore»

*Visione d'insieme.* Il fork dà `[ecosistema, nome, versione]` con `python` al posto di `pypi`, la versione normalizzata e nessun `declared_in`, che fa parte dell'identità del fatto. Contraddice anche l'obiettivo che lascia l'elenco delle librerie a Renovate e ai build tool. Correzione: togliere `packages` dalla fonte, o dire quale esigenza lo chiede.

### M6. Si perde l'autodiagnosi nel prodotto

*Alternative.* 2.5 toglie `check_packages`, che oggi emette il gap `no_ecosystem_sign`; dei `gaps` di riconoscimento la spec non dice nulla. Proposta: una dichiarazione che Renovate o un build tool dà in un file da cui il fork non dichiara nulla diventa un gap del record. Non è un riconoscimento, e misura il rischio accettato su ogni progetto reale.

### M7. Due fissaggi della stessa versione

*Alternative.* Lo sha256 del rilascio in `container_runner.TOOLS` e il catalogo da cui nasce il registro possono divergere: ne escono ID riconosciuti senza nome né marchio. Che cosa fa `technologies.derive` con un ID assente dal registro non è scritto. Correzione: un test confronta `versions["stack-analyser"]` del registro con il rilascio fissato; un ID assente esce comunque, con un gap.

## Incoerenze del documento

1. Lo «Stato» dice approvate le «Scelte di chi scrive»; il titolo della sezione dice «da confermare». *(tre revisori)*
2. «Nessun riconoscimento va perso» convive con le perdite dichiarate nelle scelte 1, 2 e 3. Serve una sola formulazione, con le eccezioni per nome. *(quattro revisori)*
3. I numeri del corpus non sono raccordati: 122, 50 e 178. «Circa l'1%» non ha numeratore né fonte; «circa 24, 22 e 20» somma 66, non 68. 475/232, 478/218, 729 e «sei voci» non citano da dove vengono.
4. Il vincolo «ID stabili» non dichiara l'eccezione `react-email` → `reactemail`, né chi cita il vecchio ID.
5. «Fino al passo 4 la fonte non è in `SOURCES`»: nessuna voce numerata dice di aggiungerla. Il rimando a 1.5 per il rischio dei build tool non regge: 1.5 confronta solo con Renovate.
6. Manca la corrispondenza fra la prova nuova (`kind`) e ciò che i consumatori leggono (`sign`, `strength`).
7. Parole con due significati: «prova» (evidenza e test), «adattatore», «passo», `kind`, «registro» e «registrazioni», «tipo» e «tipologia».
8. «Non serve un adattatore» è troppo: il CLI scrive solo su file e stampa un indicatore di avanzamento, mentre il runner restituisce l'uscita standard.
9. I rischi sono sparsi fra «Strade considerate», «Vincoli» e «Scelte», senza una mitigazione accanto. La spec sorella ha una sezione apposta.
10. Ripetizioni che AGENTS.md vieta: «senza container» compare quattro volte; le scelte 5, 6 e 7 ripetono altre sezioni.

## Cosa non è stato controllato

- I 15 test falliti del fork e le misure fatte con script provvisori (124/16/15, 305/373).
- Se una versione di Node sull'host sia accettabile per Daodan.
