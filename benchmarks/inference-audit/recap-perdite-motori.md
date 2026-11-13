# Perdite fra i motori di inferenza e il grafo

Aggiornato il 13 novembre 2026. La misura di partenza è il benchmark su Modal del commit `e3be8d0c3`: phazly, tududi, javapoet, klaxon, semver e chi. Dati e parametri sono nel [README](README.md). Non è stata eseguita una nuova misura completa dopo le correzioni.

**Diagnosi:** Daodan perde informazioni che i motori hanno già risolto. Questo è dimostrato; non dimostra che tutti i limiti di risoluzione dipendano da Daodan. Codice corretto, plugin installato e risultati rimisurati sono tre stati distinti.

Questo recap raccoglie anche i finding dell'indagine iniziale. **Corretto nel working tree** significa modifica locale verificata, ancora non committata né installata; **aperto** indica un difetto o una funzionalità incompleta; **da verificare** indica una prova mancante, non un ulteriore bug dimostrato. Lo stato riportato è quello dell'ultima verifica del 13 novembre.

## Stato dei sette problemi

I numeri della tabella appartengono alla misura di partenza, non descrivono la versione corretta.

| # | Problema | Misura di partenza | Stato attuale |
| --- | --- | --- | --- |
| 1 | Le chiamate fuori da una funzione con nome non arrivano ai flussi | tududi: 8.314 su 17.377 chiamate risolte; phazly: 485 su 13.339 | Correzione in `b8eaef663`: nodo `file::<module>`. Test locale passato; benchmark da aggiornare e ripetere. |
| 2 | Riferimenti a componenti e funzioni passate come valori non diventano collegamenti | tududi: 29.380 riferimenti; phazly: 14.071 Python e 3.614 TypeScript | Rendering JSX semplice aggiunto in `84ad00da9`. Funzioni passate come valori ancora da completare. Questi conteggi non equivalgono a chiamate mancanti. |
| 3 | La vista degli archi scarta i metodi, compresi quelli dei contratti | tududi: 2.199 su 7.681 archi; phazly TypeScript: 304 su 733; chi: 156; semver: 19 | `edge_view.py` corretto in `d05d12b33`. Corretti nel working tree anche i filtri di `store_graph.py` e `store_consumers.py`: ricerca dal metodo, chiamanti entranti e utilizzi. La copia installata verificata conserva ancora il vecchio filtro. |
| 4 | Le risposte esterne perdono l'identità del pacchetto | tududi: 35.863; phazly: 18.763; chi: 2.299; javapoet: 1.076 | Da fare. Un pacchetto esterno non identifica automaticamente un servizio remoto: anche quel collegamento richiede evidenza. |
| 5 | Funzioni contenute in valori restano candidati non utilizzati | tududi JavaScript: 1.087 risposte; phazly TypeScript: 2.072 | Da completare distinguendo funzioni, parametri, proprietà e risultati di altre chiamate. Il totale include valori che non sono funzioni del progetto. |
| 6 | Kotlin non si installa nell'ambiente del benchmark: HTTP 403 | phazly e klaxon senza motore; klaxon al 17,7% | `3a34b3c5c` aggiunge il User-Agent `daodan` ai download. Il test verifica l'header; manca una prova d'installazione da zero, senza Java e cache. L'avvio locale con dipendenze già presenti riesce, ma non verifica il caso del 403. |
| 7 | Il passo non chiedeva `implementation` | Il campione indicava possibili destinazioni aggiuntive | Richiesta aggiunta in `4f91f98a7`. Non chiuso: resta il falso positivo descritto sotto. |

## Finding iniziali: perdita degli archi e refresh

### F01 — Il plugin installato scarta ancora i metodi senza segnalare la perdita

**Aperto nella copia installata.** In `C:\Users\alfio\.codex\plugins\cache\daodan\codebase-map\1.0.1\skills\map\scripts\edge_view.py`, `_build_target_kinds` seleziona solo `function` e `class`. La promozione di una risposta `confirmed` richiede che il target compaia in quell'insieme: i metodi vengono esclusi.

La stessa fixture TypeScript con due risposte confermate, un metodo di classe e uno di interfaccia, produce:

| Versione | Archi risolti | `engine_confirmed` | Esito |
| --- | --- | --- | --- |
| Sorgenti della repo dopo `d05d12b33` | 2 | 2 | Destinazioni conservate |
| Plugin installato verificato | 0 | 0 | Due archi irrisolti, target nulli, `gaps=[]` |

Quindi la correzione nei sorgenti non basta: la perdita nella copia installata è anche silenziosa. Il manifest conserva la versione `1.0.1`; non è stata eseguita una pubblicazione o un aggiornamento del plugin. La directory installata non è scrivibile in questa sessione. Resta da aggiornare la copia effettivamente caricata e ripetere la verifica.

### F02 — Cercare dal file del metodo chiamato perdeva gli archi entranti

**Corretto nel working tree.** `store_graph.py`, nella selezione iniziale di `_packet`, escludeva `method` anche dopo la correzione di `edge_view.py`. La ricerca dal file chiamante restituiva due chiamate risolte; dal file della classe restituiva solo `Shop`, senza chiamate; dal file dell'interfaccia non restituiva dichiarazioni né chiamate.

Il filtro include ora `function`, `method` e `class`. Il test verifica dichiarazioni e archi entranti partendo dai file dei metodi concreti e dei contratti. La modifica deve ancora raggiungere il plugin installato.

### F03 — Analisi del file e ricerca degli utilizzi escludevano gli stessi metodi

**Corretto nel working tree.** Quattro filtri di `store_consumers.py` escludevano `method`: dichiarazioni e chiamanti nell'analisi del file, destinazioni nella ricerca degli utilizzi. Un arco presente nella vista poteva quindi sparire da `file_analysis` e `find_usages`.

I filtri includono ora i metodi. La regressione verifica il chiamante entrante e un utilizzo `resolved-static` del metodo. È una perdita distinta da F01 e F02: correggere soltanto la costruzione degli archi non correggeva i consumatori.

### F04 — Refresh e letture MCP usavano lock diversi

**Corretto nel working tree.** `MapService._operation` usava `confinement.project_lock`; `snapshot.refresh_working` usava i lock del refresh senza acquisire quello del progetto. Su Windows il refresh poteva tentare `os.replace` del manifest mentre una lettura MCP lo teneva aperto.

Riproduzione con una vera lettura `MapService.read` sospesa e un file modificato: il refresh chiamava `reset_pass`, poi falliva con `WinError 5`; `ensure_edges` non veniva chiamato. Ora il refresh acquisisce anche il lock del progetto. Il test verifica che attenda la chiusura del lettore prima di fermare gli engine, completi il refresh e richieda il nuovo passaggio degli engine.

### F05 — MCP rilasciava il lock prima di chiudere gli snapshot

**Corretto nel working tree.** In `mcp_service.py` l'`ExitStack` era esterno al lock: esisteva un intervallo in cui il lock era libero ma i database erano ancora aperti. È un secondo difetto di sincronizzazione, da correggere insieme a F04.

Il lock ora contiene l'`ExitStack`; gli snapshot vengono chiusi prima del rilascio. Il test controlla esplicitamente che lo snapshot sia già chiuso all'uscita dal lock.

### F06 — Un refresh fallito poteva lasciare store obsoleto ed engine senza riavvio

**Conseguenza verificata; recupero dell'ambiente reale da verificare.** L'ordine osservato era `reset_pass → write_snapshot → ensure_edges`: un errore nella scrittura interrompeva il percorso prima dell'ultimo passo. Nel run reale `refresh.json` riportava il fallimento nella sostituzione di `manifest.sqlite`; `edge_state` riportava uno store legato a una revisione diversa dello snapshot, linguaggi mancanti e zero archi `engine_confirmed` esposti.

F04–F05 correggono la concorrenza riprodotta, ma non dimostrano il recupero del run reale né gestiscono ogni possibile errore di scrittura dopo `reset_pass`. Resta da completare un refresh con il codice aggiornato e verificare revisione dello store e riavvio degli engine. Non è stato identificato il processo che teneva aperto il manifest nell'episodio originale: la riproduzione dimostra il meccanismo, non l'identità di quel processo.

**Ipotesi iniziale esclusa:** il lettore `previous` del refresh non era, da solo, la causa. `write_snapshot` lo chiude già prima della sostituzione; il refresh incrementale senza un secondo lettore riesce. Non è stato eseguito un bisect per identificare il primo commit responsabile.

## Kotlin: cause distinte da non confondere

### F07 — Il mancato avvio locale non dimostra un guasto del motore Kotlin

**Avvio con cache verificato; installazione da zero aperta.** Nel log locale esaminato, Kotlin aveva 39 elementi, 39 risposte riusate e zero nuove richieste: 28 esterne e 11 irrisolte, nessun target nel progetto. Il passo poteva terminare senza avviare la JVM perché non aveva nuove interrogazioni da eseguire; la dicitura di passo completato non prova un nuovo avvio del motore.

Una prova diretta con `Tool.kt` e `Use.kt`, usando dipendenze già presenti, ha restituito `ready=True`, due file caricati e una definizione corretta in `Tool.kt` con `kotlin-analysis-api@2.3.13`. Questo esclude un'incapacità generale di avvio in quell'ambiente, ma non risolve il 403 del benchmark.

Il codice esegue i motori in sequenza: Jedi, TypeScript, Java, Kotlin, Rust, Go. Kotlin può quindi essere in attesa dei precedenti. Il coordinatore applica inoltre una soglia di 2 GiB liberi e condizioni di esclusione dopo un esaurimento di memoria; non sono cause dimostrate dell'episodio esaminato, in cui risultavano circa 9,2 GiB liberi. Un refresh che fallisce prima di `ensure_edges`, invece, può impedire il passaggio di tutti i motori, Kotlin incluso.

Il problema HTTP 403 dell'installazione su Modal rimane distinto: il nuovo User-Agent è verificato da un test dell'header, manca l'installazione completa senza Java e senza cache.

## Altri difetti e limiti emersi dalla revisione

### F08 — `implementation` può trasformare una risposta ambigua in certezza

**Aperto, riprodotto.** `resolve_edges.py` conserva solo le implementazioni riconosciute come concrete nel progetto e sceglie la destinazione quando ne resta una. Due risposte, una interna e una esterna, producono così un arco interno `confirmed`.

Occorre considerare anche le alternative esterne o non classificabili e mantenere il contratto o l'ambiguità quando non si possono escludere. Una sola implementazione trovata non prova quale venga eseguita a runtime. La nuova richiesta `implementation` di `4f91f98a7` è quindi utile, ma il problema non è chiuso.

### F09 — P6 conta come persi collegamenti al modulo già presenti nei flussi

**Aperto, riprodotto.** `_graph_use` in `modal_audit.py` usa ancora `facts.node(caller)` senza il ripiego `file::<module>` introdotto nei flussi. Una funzione `mount` chiamata al livello del file genera realmente `app.py::<module> → app.py::mount`, mentre il contatore del benchmark dichiara perso quel collegamento.

Va aggiornata la misura prima di riutilizzarla per valutare la correzione. I risultati già prodotti descrivono la misura precedente.

### F10 — P6 non verifica tutti i consumatori pubblici del grafo

**Aperto, copertura insufficiente.** La misura approssima la conservazione degli archi attraverso i fatti, senza verificare i risultati effettivi di `graph_packet`, `file_analysis` e `find_usages`. Per questo non avrebbe rilevato F02–F03 anche con `edge_view` corretto.

Il benchmark deve confrontare archi e destinazioni effettivamente esposti, interrogando sia il chiamante sia il file del metodo chiamato, oltre ai flussi. Le nuove regressioni locali coprono i difetti riprodotti; non aggiornano automaticamente P6.

### F11 — Le vecchie sonde sovrastimavano alcune destinazioni callable

**Sonde corrette nei commit; misure da rigenerare.** La classificazione per riga poteva confondere un parametro con la funzione sulla stessa riga. `1eed00277` aggiunge la graduazione alla posizione esatta; `d6fb7dc8c` dettaglia il contenuto dei valori e la funzione chiamata.

Le stime precedenti, compreso il possibile recupero del 25–55%, non sono percentuali dimostrate di nuovi archi corretti. Anche il passaggio dal 41,7% al 46,9% di tududi è un ricalcolo degli archi scartati, non una nuova esecuzione completa dopo tutte le correzioni.

### F12 — Zero conflitti registrati non dimostra accordo né correttezza dei motori

**Conclusione del recap da limitare; divergenze da classificare.** Il passaggio principale interroga soprattutto chiamate irrisolte: l'assenza di conflitti nella vista non confronta tutte le risoluzioni lessicali con quelle dei motori. Le sonde P7 disponibili riportano:

| Progetto / motore | Stessa destinazione | Destinazione diversa | Nessuna risposta |
| --- | --- | --- | --- |
| chi / Go | 30 | 0 | 0 |
| javapoet / Java | 28 | 2 | 0 |
| phazly / Python | 28 | 2 | 0 |
| phazly / TypeScript | 30 | 0 | 0 |
| semver / Rust | 25 | 4 | 1 |
| tududi / TypeScript | 30 | 0 | 0 |

Le differenze osservate comprendono classe contro costruttore, funzione contro wrapper `lru_cache` e destinazioni `Err` della libreria standard contro simboli locali. Vanno valutate caso per caso: non sono automaticamente errori di uno dei due risolutori. Non ci sono campioni Kotlin validi nei due run falliti; il campione Rust di phazly ha popolazione zero. Campioni da 30 casi non costituiscono una verifica completa né una ground truth.

### F13 — Rendering, callback e valori richiedono relazioni distinte

**Copertura parziale; semantica da conservare.** Il nuovo collegamento JSX riconosce forme semplici come `<Paywall />`. Il codice richiede un nome con una sola parte: non copre in quel percorso `<UI.Paywall />`; componenti conservati in valori o wrapper ricadono anche nel problema 5. Questo limite è osservato nel codice, non verificato qui con un nuovo benchmark dedicato.

Il resolver delle chiamate irrisolte non ricostruisce automaticamente ogni riferimento letto o passato come argomento. Una callback registrata, una funzione letta, un componente renderizzato e una funzione invocata non sono la stessa relazione. Attribuire una callback al modulo o alla funzione che la contiene non prova che venga eseguita all'avvio. Ogni risposta deve conservare un esito e un motivo tracciabili, senza promuovere indiscriminatamente tutte le letture a chiamate.

### F14 — Valori ed esterni non autorizzano collegamenti concreti senza ulteriore evidenza

**Aperto, problemi 4–5.** Le risposte verso parametri, proprietà, variabili e risultati di factory non identificano sempre una funzione del progetto: occorre risolvere il contenuto del valore, quando possibile, e mantenere l'incertezza negli altri casi. I conteggi dei candidati non sono conteggi di chiamate recuperabili.

Per gli esterni viene persa l'identità utile della destinazione o dipendenza. Conservarla permetterebbe collegamenti con provenienza verificabile; la presenza di un pacchetto, per esempio Stripe, non prova da sola una chiamata a un servizio remoto.

## Paywall e verifiche locali

Il conteggio riportato di 11 componenti che rendono il Paywall va verificato sul nuovo grafo di phazly. Per `startCheckout`, conservare il metodo del contratto è corretto; raggiungere una funzione concreta richiede sia una risposta non ambigua sia la corretta risoluzione del valore che la contiene.

Sono passati 35 test mirati e correlati: 6 su metodi e sincronizzazione, 29 su flussi, Kotlin e download. I test di regressione dei difetti corretti sono in `tests/test_codebase_map_edge_view.py` e `tests/test_codebase_map_working_run.py`; anche `git diff --check` è passato.

La suite MCP completa non è stata validata: la pubblicazione dei context packet fallisce su `os.link` con `WinError 5`. Una prova isolata di hard link nella directory temporanea ha lo stesso esito, quindi il blocco è attribuito ai permessi dell'ambiente, non dimostrato come regressione del prodotto. Non è stato introdotto un aggiramento nel codice.

Le quattro modifiche locali in `store_graph.py`, `store_consumers.py`, `snapshot.py` e `mcp_service.py`, con i due file di test, restano da committare e distribuire. Non è stato verificato un refresh completo del grafo reale usando il plugin aggiornato; erano presenti refresh concorrenti di altre sessioni. I test locali non sostituiscono tale verifica né una nuova misura sui sei progetti.

## Lavoro da completare

1. Portare le correzioni F02–F05 nella copia effettivamente caricata, insieme a F01; verificare un refresh completo, revisione dello store e riavvio degli engine (F06).
2. Correggere la selezione delle implementazioni ambigue (F08) e completare valori e provenienza esterna senza confondere le relazioni (F13–F14).
3. Aggiornare P6 per misurare i flussi e tutti i consumatori del grafo, nei due versi di interrogazione (F09–F10).
4. Provare l'installazione Kotlin da zero senza Java/cache e completare la suite MCP in un ambiente che permetta gli hard link (F07).
5. Ripetere i sei casi su Modal con commit e sonde aggiornati; classificare le divergenze, verificare Paywall e registrare risultati e limiti nel README (F11–F12).

Il nuovo run Modal non è stato lanciato. La stima precedente di circa 0,5 USD non è un costo nuovamente misurato.
