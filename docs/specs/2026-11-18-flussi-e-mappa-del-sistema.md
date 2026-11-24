# Flussi e mappa del sistema

**Stato:** In parte: ogni sezione dichiara il suo stato, riassunto in «Stato per parte». Questa spec è la mappa del sistema: parole, principi, collegamenti, nodi, flussi, livelli, registro, scheda, verifica, interrogazione. Tre spec ne tengono un aspetto, con gli stessi numeri di sezione, di motivo, di limite e di decisione: [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md) (6.5–6.8 e sezione 7), [ricerca dei flussi e pacchetto di una review](2026-11-20-ricerca-e-pacchetto-di-review.md) (3.8, sezioni 11 e 12) e la [pipeline di analisi](2026-11-15-pipeline-di-analisi.md) (preparazione e indicizzatori). I flussi poggiano sul grafo dopo tutta la pipeline: gli archi provati dallo step `analyze` e quelli osservati dal [passo dinamico](2026-11-12-passo-dinamico.md); una misura fatta sul solo statico lo dice (limite 10). L'uso nella review si misura in [flussi nella review](2026-11-09-flows-in-review.md). **Piano:** l'ordine corrente è nel [piano della pipeline intera](../plans/2026-11-20-pipeline-intera.md). Il «piano del 19 novembre» citato nel testo non è mai stato in git: le decisioni che gli si attribuiscono non hanno prova nel repository.

Daodan deve saper rispondere a quattro domande:

1. Di quali cose è fatto questo sistema e che cosa fa?
2. Che cosa succede quando arriva questa azione o questa richiesta, e chi scrive il dato che il sistema mostra o restituisce?
3. Come appare lo stesso processo a chi lo usa, a chi lo progetta, a chi lo scrive e a chi lo fa girare?
4. Che cosa tocca questa richiesta di review?

La risposta ha due usi: studiare un sistema sconosciuto e trovare dove fare una review partendo dall'intento di chi la chiede. L'utente fornisce il sistema; nomi, partecipanti, ingressi, esiti e varianti emergono dall'analisi. Vale per qualsiasi app o servizio: i casi concreti stanno nei README dei benchmark.

## Come leggere questa spec

1. **Tre stati.** **Applicato:** il codice lo fa. **In corso:** una parte è nel codice, e il testo dice quale. **Proposta:** non è nel codice. Lo stato sta in testa alla sezione e, dove un punto se ne scosta, sul punto.
2. **La prova di «applicato»** è un test o un benchmark che si riesegue: il file del test, con il nome del test quando il file ne ha molti, oppure la sezione del README di un benchmark, che dà il comando. Dove la prova non c'è, il punto dice «applicato, prova non trovata»; dove il codice fa altro da ciò che il testo dava per applicato, il punto dice che cosa fa il codice e lo stato è corretto. Gli uni e gli altri sono elencati in fondo, in «Prove non trovate, parole in due sensi».
3. **Ancore.** Un punto si cita con sezione e numero: «7.3». In §4 i punti dei livelli sono 4.L1–4.L6 e quelli del dettaglio 4.1–4.11, come li citano i documenti già scritti. Le misure della sezione «Prova» si citano con il loro benchmark: «system-map 7». Un punto aggiunto prende il numero seguente della sua sezione; un numero non si riusa. Un punto, un motivo, un limite o una decisione che sta in un'altra delle quattro spec tiene il suo numero.
4. **Motivi.** Una regola rimanda al suo motivo: «(motivo 6)» è la voce 6 di «Motivi delle scelte», che dice chi l'ha decisa, il perché con il numero misurato, che cosa si è scartato e dove sta la prova. I motivi stanno in una sezione sola, così il testo che decide resta leggibile. Le misure stanno nei README dei benchmark: qui solo i rimandi.
5. Ciò su cui le misure poggiano, e ciò che non misurano, è in «Assunzioni e limiti noti»; gli errori di misura e di lettura già fatti sono in «Errori registrati»; le scelte che vincolano tutto il prodotto sono elencate in «Decisioni di architettura da registrare dopo la validazione».
6. I «Principi» valgono per ogni sezione; si citano «Principio 2».

## Parole

Ogni parola ha un solo significato.

| Parola | Significato |
| --- | --- |
| Nodo | Una cosa del sistema con un nome, al livello a cui la nomina una persona. Raccoglie i suoi membri. Un simbolo da solo non è un nodo |
| Tipo di nodo | Elenco chiuso: attore, schermata, applicazione, funzionalità, servizio o API, gateway, database, coda, filesystem, autenticazione, dispositivo, lavoro a orario, entità, altro |
| Filesystem | File e cartelle su disco che il programma legge o scrive mentre gira, qualunque uso se ne faccia (archivio, semaforo, cache, temporaneo). I percorsi toccati sono i suoi membri |
| Applicazione | Un'app o un sito intero che una persona apre, con le sue schermate e la sua logica |
| Lavoro a orario | Un lavoro che un orario avvia. Chi consuma una coda resta una coda |
| Posizione | Interno: ha codice nello snapshot. Esterno: è di altri. Non visto: fa parte del sistema, ma i suoi file stanno fuori dallo snapshot |
| Servizio esterno | Un servizio di altri che gira altrove: Stripe, Firebase |
| Progetto esterno | Software di altri su cui il sistema è costruito o dentro cui gira: un framework, una libreria, un runtime, un motore di container (Angular, NumPy) |
| Membro | Ciò che un nodo raccoglie: file, simboli, chiavi di store, rotte |
| Padre | Il nodo dentro cui un nodo si apre (`inside`), uno solo: un'applicazione nel sistema, una schermata nell'applicazione. Il nodo è suo figlio |
| Entità | Un dato con un nome (un ordine, un utente), ovunque sia salvato. I suoi membri sono le rappresentazioni: una tabella, una chiave di stato, una cache |
| Store | Dove un dato vive: stato globale, tabella o collezione, file, cache |
| Collegamento | Da un membro a un altro, con tipo ed evidenza. **Diretto** se sta nel codice (chiamata, import). **Dedotto** se una regola di collegamento riconosce lo stesso dato o la stessa rotta in chi offre e in chi usa. **Dichiarato** se tocca un nodo senza codice. **Osservato** se lo vede il passo dinamico |
| Tipo di collegamento | `chiama`, `scrive`, `legge`, `attiva` (un'azione dell'utente attiva il suo handler) |
| Regola di collegamento | Come, in questo progetto, si riconosce chi offre e chi usa uno store o una rotta |
| Ingresso | Dove un flusso comincia, uno fra: un controllo dell'interfaccia (un clic, un testo scritto, un invio); una rotta o una chiamata (un endpoint di una API REST, una chiamata RPC, uno strumento chiamato da un assistente; un avviso di ritorno, hook o webhook, è una rotta che un servizio di altri chiama); un messaggio (una coda, un socket, un evento fra processi); un comando; un orario (cron, timer); un cambio di un dato (un trigger del database, la scrittura di un file o di un documento che qualcuno osserva); l'avvio di un processo; un evento del repository (un push, un tag, un rilascio che avvia un flusso di CI); un evento del sistema operativo (la rete che torna, una notifica toccata, un collegamento aperto da fuori); un evento hardware (un dispositivo fisico). Dieci tipi (motivo 5). L'effetto di un flusso può essere l'ingresso di un altro: un errore che avvia un flusso è questo, non un tipo |
| Effetto | Dove un flusso arriva: un valore mostrato o restituito, un cambio di stato, un evento emesso, un comando a un dispositivo |
| Estremi | Gli ingressi e gli effetti di un flusso, con chi li avvia e chi li riceve |
| Percorso | La sequenza ordinata di collegamenti da un ingresso. È la prova di un flusso al livello codice |
| Flusso | Qualcosa che il sistema fa, con un nome nel linguaggio di chi lo usa o lo gestisce: i nodi che vi partecipano e le frecce fra loro. È uno solo, a qualunque livello lo si guardi |
| Variante | Un ramo dello stesso flusso, distinto dal suo ingresso o dalle sue condizioni |
| Tipo di flusso | Uno o più fra: funzionale (una cosa che il prodotto fa per chi lo usa), operativo (gira senza una persona: un orario, una coda, un avviso esterno), tecnico (la macchina del prodotto che gira: cache, sincronizzazione, registro degli errori), dati (segue un dato: dove nasce, dove vive, chi ne tiene copia), hardware (passa da dispositivi fisici o dalla rete), devops (costruire, impacchettare, rilasciare, addestrare a tempo di sviluppo) |
| Area | Un gruppo di flussi che una persona nomina insieme. È ciò che una richiesta nomina più spesso |
| Freccia | Da un nodo a un altro dentro un flusso, con il dato che passa. Riassume i collegamenti fra i membri dei due nodi e afferma solo ciò che provano |
| Grado | Quanto una freccia è provata: «provata» dai collegamenti che la compongono, «dichiarata» quando un capo non ha codice, «da verificare» quando il flusso la chiede e il grafo non la mostra |
| Livello | Quali nodi si guardano: persone, funzioni, dati, codice, infrastruttura. Più d'uno insieme è «misto» |
| Dettaglio | Quanto si apre, a qualunque livello |
| Corrispondenza | Il legame fra nodi di livelli diversi che sono la stessa cosa: una funzione e i file che la realizzano, un servizio e la macchina su cui gira, un'entità e il database in cui vive |
| Candidato | Un gruppo di membri che la macchina ricava dal grafo, sempre uguale per lo stesso snapshot |
| Punto d'appoggio | Ciò che il modello indica per costruire un flusso: un ingresso, una rotta, una chiave di store, un servizio esterno da cui il flusso parte, per cui passa o a cui arriva |
| Scheda del sistema | Il riassunto che la macchina compone dai passi di analisi per chi propone la mappa |
| Mappa del sistema | Nodi, flussi, aree e corrispondenze di un progetto, con le loro prove |
| Nome | Nella lingua del prodotto, lo stesso per la stessa cosa in ogni mappa e in ogni run. Un flusso porta il nome dell'azione e il suo oggetto, con parole del prodotto, senza verbo né parola vuota in testa (gestione, elaborazione, processo), e ha un esito solo; una parte si chiama come la chiama chi ci lavora, senza il nome del prodotto, che porta solo il nodo dell'intero sistema; una schermata ha il titolo che l'utente vede, un'entità è al singolare, un servizio di altri ha il nome proprio del registro, mai il ruolo. La macchina controlla solo la parola vuota e il nome del registro: il resto ha eccezioni vere (motivo 4) |
| Granularità e significato | Ciò a cui un dato si riferisce (un ordine, una sua riga, un utente) e, in una frase, che cosa afferma |
| Perimetro, contesto, unità | I file che un lavoro copre; quelli che si consultano per giudicarli, senza giudicarli; quelli affidati a un revisore in un solo incarico |

## Stato per parte

| Parte | Stato |
| --- | --- |
| Principi | 1, 2 e 4 applicati (in 4, la scelta fra candidati incerti: prova non trovata); 3 in corso: il motore generale con un adattatore per tipo non è nel nucleo (motivo 18) |
| Regole di collegamento, collegamenti dedotti, percorsi, unità, scheda di un percorso (sezioni 1, 9, 10, 11) | Applicato nel plugin: `flows.py`, `codebase_map_flows`. Nell'app le regole le scrive il motore scelto e i collegamenti dedotti sono relazioni del grafo. Prova: `tests/test_codebase_map_flows.py`, `tests/test_codebase_map_app.py`. Senza prova: 1.5, il limite di 1.6, 9.1 |
| Registro dei servizi e dei progetti esterni (sezione 5) | Applicato, tranne il nome di 5.5; gli obiettivi di 5.9 e 5.10 sono in corso. I numeri sono nella [tabella generata](../plugins/codebase-map-supporto.md) (5.11). Prova: `tests/test_codebase_map_service_registry.py`, `tests/test_codebase_map_support_table.py` |
| Scheda del sistema, proposta, verifica, livelli (sezioni 2, 4, 6, 7, 8) | Applicato nel plugin: `system_brief.py`, `system_map.py`, `system_levels.py`, ruolo `system-mapper`. Nell'app la proposta parte da sola a fine analisi (`App.map`, dopo `App.link`) e lo stato dice nodi, flussi e resti; la pagina non mostra ancora la mappa. L'agente propone ancora anche le frecce e i membri dei nodi (2.1, 7.3), e la scheda fa un gruppo per risorsa condivisa (6.2): candidati e frecce dalla macchina e il grado «da verificare» sono misurati senza modello, non applicati. I tipi di nodo `filesystem`, `applicazione` e `lavoro a orario` e il tipo di flusso `devops` sono nel codice: coda e filesystem stanno al livello infrastruttura, un'applicazione a persone, un lavoro a orario a funzioni (motivo 3). Dei nomi, `record` rifiuta il flusso che comincia con una parola vuota e il nodo esterno il cui nome non comincia con quello della sua voce del registro; `reference.py check` li dà come problemi (motivo 4). Prova: `tests/test_codebase_map_system_brief.py`, `tests/test_codebase_map_system_map.py`, `tests/test_codebase_map_system_levels.py`, `tests/test_codebase_map_app.py` |
| Grafo dell'app (sezione 4) | Mostra i livelli codice e infrastruttura: moduli o cartelle con le tessere del loro stack, e i servizi esterni riconosciuti con il marchio. Si apre sul posto fino alle classi e ai loro membri. Non ancora visto in un browser né misurato su un progetto grande. Prova: `tests/test_codebase_map_app.py` |
| Estremi a ogni livello; attori, schermate e dispositivi nell'app | Proposta |
| Posta SMTP come servizio nel registro; schermate riconosciute dall'ingresso e dispositivo dedotto sopra di loro ([interfacce del progetto](2026-11-19-interfacce-del-progetto.md)) | Proposta, con i motivi nella spec delle interfacce («Motivi delle scelte»); della posta SMTP nessun altro documento scrive |
| Flusso acceso a qualunque dettaglio, nodi trascinabili, percorso da un nodo (sezione 4); vista sul prodotto (sezione 3) | Proposta, dalle parole del proprietario (motivo 22; piano della pipeline intera, task 12). Il testo li dava provati sulla pagina dei riferimenti di [`benchmarks/system-map`](../../benchmarks/system-map/README.md), non nell'app: quella pagina non si trova nel repository |
| Ingressi letti dalla macchina e scoperta dei flussi (6.5–6.8, sezione 7) | Nella spec [Ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), «Stato» |
| Anagrafica e legami fra flussi, ricerca, perimetro di una review (3.8, sezioni 11 e 12) | Nella spec [Ricerca dei flussi e pacchetto di una review](2026-11-20-ricerca-e-pacchetto-di-review.md), «Stato» |
| Esploratore e nomi vecchi | L'esploratore lavora su simboli, file e percorsi, con le viste «logica» e «fisica»; il parametro `level` dei percorsi dice ancora fisico, logico, dati, ux. `03-flows.md` è prosa scritta dai ruoli |

## Principi

Valgono per ogni sezione. Li ha dati il proprietario: per 1, 2 e 3 con le sue parole, per 4 il principio, con la forma proposta.

1. **Lo scopo è il grafo dei moduli, e le sue relazioni sono i flussi.** Un grafo che non trova le relazioni è inutile. Un flusso è ogni ingresso → processo → uscita, qualunque sia l'ingresso (Parole, «Ingresso»). Una vista per cartella o per import non è il grafo (motivo 16).
2. **Si censiscono i tipi di legame; le implementazioni restano aperte.** Daodan tiene il censimento: tre coppie chiuse di ruoli (chiama e offre, scrive e legge, emette e ascolta) e tipi aperti, ognuno con un nome, una coppia e la forma della sua chiave ([guida ai punti di connessione](../research/2026-11-14-punti-di-connessione.md)). Come un progetto o un framework scrive un legame non sta nel codice di Daodan né in regole incorporate: è un dato, dato come suggerimento a chi scrive le regole del progetto (5.9). Nessun nome di framework nel codice che unisce i legami (motivo 17).
3. **Un motore generale e un adattatore per tipo di legame.** Il motore unisce i punti per coppia di ruoli e chiave e non conosce nessun tipo. Un tipo è un adattatore con un solo contratto: il nome, la coppia, come un valore diventa una chiave o una lacuna, come due chiavi si incontrano (certo, incerto, no). Se c'è il legame lo decide sempre l'adattatore, cioè codice con i suoi test; un legame incerto non si disegna come certo. Il primo è REST, con chiave metodo e schema del percorso (1.2). *In corso* (motivo 18).
4. **Il modello propone, la macchina verifica.** L'aiuto del modello ha quattro posti: scrive le regole del progetto, una volta (1.1); riceve solo i resti, cioè i lati singoli e le lacune, e propone una correzione alle regole, che la macchina riapplica (1.6); sceglie fra candidati incerti, e il legame resta marcato `proposto`; dà i nomi. Ogni legame dice da dove viene, con la sua evidenza (Parole, «Collegamento»). Le regole si salvano accanto allo snapshot, così rifare il grafo non richiama il modello. Senza modello Daodan funziona e dichiara le lacune. La stessa divisione vale per nodi e flussi (sezioni 7 e 8) (motivo 19).

## 1. Collegamenti

**Applicato.** Prova: `tests/test_codebase_map_flows.py`; per 1.6, `tests/test_codebase_map_app.py`. Senza prova: 1.5 e il limite di 1.6. 1.7 dice il suo stato.

1. Il modello legge il progetto una volta e scrive le regole di collegamento: «lo stato globale si legge con `<hook>`», «le chiamate al servizio passano da `<client>`», «la tabella `<nome>` si scrive solo da `<modulo>`». Una regola indica il costrutto come funzione del progetto, come chiamata così come è scritta (limitata a un insieme di cartelle) o come attributo del markup che lega un'azione al suo handler. Il formato è nel docstring di `flows.py`.
2. La macchina applica le regole a tutto il sorgente: elenca chi offre e chi usa, e li accoppia sull'identità che la regola precisa. Per uno store sono lo store e la chiave; per una rotta sono servizio, metodo e schema del percorso. Condividere lo store o il solo nome non basta: scrivere `store.theme` non collega a chi legge `store.cart`.
3. Ogni coppia è un collegamento dedotto con la sua evidenza. Nel grafo è una relazione fra i file dei due lati (`calls` per una rotta, `reads` da chi legge a chi scrive), riportata fra moduli o cartelle. Identità ambigue, accessi dinamici non risolti e accessi spaiati restano lacune dichiarate. Una rotta con più candidati è una relazione incerta, mai contata come certa.
4. Un nodo senza codice è un modulo `external`, dichiarato dal progetto o proposto con la sua evidenza. Il collegamento che lo raggiunge è dichiarato; se il modulo è solo proposto, resta `inferred`.
5. Le regole sono legate ai digest dei file che citano: se quei file cambiano, vanno rilette. *Applicato, prova non trovata: il codice tiene le regole accanto allo snapshot (`flow-rules.json`, `mcp_service.py`) e i collegamenti in cache finché cambiano regole, snapshot o motore (`flows.cached_links`), senza i digest dei file citati.*
6. Nell'app il motore scelto scrive le regole, legge ciò che la macchina ha unito e ciò che è rimasto fuori, e le corregge al più tre volte. L'esito lo dà il servizio, mai le parole del modello. Prova: `test_the_engine_records_the_rules_through_the_flows_tool_and_the_service_says_what_they_link`, `test_an_engine_that_records_no_valid_rules_fails_with_the_cause`. *Il limite di tre volte sta solo nel prompt (`app.ROUNDS` in `LINKS`): applicato, prova non trovata.*
7. **Non tutto lo scibile: tre livelli.** Non si può prevedere ogni tipo di scambio fra due nodi: si danno basi solide e una gamma vasta di casi reali. Un tipo conosciuto ha il suo adattatore (Principio 3) ed entra nel prodotto con un caso reale in `benchmarks/`, attese scritte prima del codice. Un tipo non previsto si esprime nelle regole del progetto e lo unisce il motore generale, a chiave uguale. Ciò che nulla unisce resta una lacuna dichiarata o un lato singolo spiegato, mai un legame inventato (motivo 20). *Il terzo livello è applicato (1.3); i primi due seguono il Principio 3.*

## 2. Nodi

**Applicato nel plugin, tranne 2.1.** Prova: `tests/test_codebase_map_system_map.py`.

1. Un nodo con codice è un gruppo di membri con un nome, un tipo e una posizione. I membri vengono dai candidati che il nodo comprende: chi propone non li scrive. Un file si divide per funzione solo quando la macchina vede le sue funzioni in candidati diversi. *Proposta (motivo 6): oggi chi propone scrive `members`, anche funzioni, e la macchina rifiuta il nodo il cui membro non esiste (`test_a_missing_member_refuses_the_node_and_names_it`). Un membro `store:` che i collegamenti non hanno (nessuna regola lo legge ancora) non rifiuta il nodo se un altro membro si risolve: il nodo è accettato, il rapporto ha `unlinked`, il nodo non possiede lo store e nessuna freccia si prova per lui.*
2. Un nodo senza codice (attore, dispositivo, macchina o servizio su cui il sistema gira, servizio esterno, progetto esterno, parte non vista) non ha membri e cita l'evidenza che lo lega al progetto. Un attore cita gli ingressi che usa; una macchina cita la configurazione che la nomina; un progetto esterno cita la dipendenza dichiarata. Prova: `test_a_node_without_code_cites_its_evidence`, `test_an_unseen_node_says_where_it_is`.
3. Lo stesso membro può stare in più nodi: un file che serve due schermate appartiene a entrambe. *Applicato, prova non trovata.*
4. Una dipendenza non è un nodo. Un progetto esterno che il registro conosce è una tessera del modulo che lo dichiara (sezione 4); diventa un nodo solo quando un flusso lo nomina. Le altre dipendenze restano contate. Prova: `tests/test_codebase_map_app.py`, `test_a_framework_a_module_declares_is_in_its_stack_open_or_closed_and_never_a_node_and_a_tool_or_a_mention_is_not`.
5. La mappa del sistema sta accanto al grafo dei moduli e non ne cambia strati, conflitti e archi. *Applicato, prova non trovata.*
6. Un nodo nomina il suo padre, che deve stare nella mappa; un cerchio di padri è rifiutato. Un nodo nuovo con lo stesso tipo e gli stessi membri di uno esistente, o annidati, è un doppione, salvo quando uno è avo dell'altro (motivo 3). Prova: `test_inside_that_goes_round_in_a_circle_is_refused`, `test_a_node_inside_another_is_its_part_and_stays_outside_the_flows`.
7. Un nodo lascia la mappa quando nessun flusso lo usa, non ha padre e nessun `on` o `inside` lo nomina (motivo 3). Prova: `test_a_node_inside_another_is_its_part_and_stays_outside_the_flows`.

## 3. Flussi

**Tipi e aree applicati nel plugin; varianti ed estremi: proposta.** Prova dei tipi e delle aree: `tests/test_codebase_map_system_map.py` (`test_a_flow_has_known_types`, `test_the_new_node_types_and_a_devops_flow_are_accepted`, `test_every_area_is_declared_without_scope`, `test_a_flow_sits_in_a_present_area`).

1. Un flusso può attraversare più componenti, avere più ingressi e terminare con esiti diversi. Un modulo logico ha una responsabilità riconoscibile anche quando i suoi membri stanno in cartelle diverse.
2. Le varianti emergono dai fatti del progetto. Esempio su un sistema di ordini: «Annullamento ordini» ha le varianti «Su richiesta dell'utente», che parte da un controllo dell'interfaccia, e «Automatico per scadenza», che parte da un orario. Possono convergere sullo stesso servizio; se l'orario aggiorna direttamente lo stato, quel ramo resta distinto fino alla scrittura. Nomi e numero delle varianti sono dell'esempio, non delle istruzioni di chi propone.
3. Raggruppare due rami sotto un flusso non stabilisce un legame causale fra loro: un clic e un webhook possono appartenere allo stesso acquisto, ma collegarli chiede un riscontro, per esempio dove l'identificativo della transazione viene scritto e poi usato.
4. Chi avvia un flusso senza essere una persona è il servizio esterno che chiama o il dispositivo. Un orario o una coda è l'ingresso del servizio che esegue, non un attore.
5. Un dato che vive in più nodi (un listino, un elenco di permessi, un limite) è un flusso di tipo dati: le sue frecce dicono «stessa informazione». La macchina non verifica che i valori coincidano.
6. Le aree passate in rassegna: accesso e identità; funzioni principali; pagamenti e abbonamenti; dati dell'utente; integrazioni esterne; comunicazioni; amministrazione; esercizio. Chi propone dichiara ogni area presente o assente e aggiunge quelle che il progetto ha e l'elenco no.
7. Il tipo di flusso `devops` raccoglie costruire, impacchettare, rilasciare, addestrare a tempo di sviluppo; `tecnico` resta per la macchina del prodotto che gira (cache, sincronizzazione, registro degli errori) (motivo 3). **Proposta, dalle parole del proprietario (motivo 22):** un flusso funzionale che parte da un controllo di una schermata è un flusso di interfaccia. Il grafo si apre sul prodotto: i flussi `devops`, e i nodi che servono solo a loro, compaiono quando si chiedono.

**3.8.** L'anagrafica dei flussi e i legami fra flussi: [Ricerca dei flussi e pacchetto di una review](2026-11-20-ricerca-e-pacchetto-di-review.md), 3.8.

## 4. Livelli e dettaglio

I controlli sono due e sono distinti: il livello sceglie quali nodi si guardano, il dettaglio quanto si apre.

**Livelli: applicato nel plugin. Nell'app: codice e infrastruttura.** Prova: `tests/test_codebase_map_system_levels.py`; nell'app, `tests/test_codebase_map_app.py`.

| Livello | Domanda | Nodi |
| --- | --- | --- |
| Persone | Chi agisce, attraverso quale controllo e con quale risultato visibile? | Attori e schermate |
| Funzioni | Quali responsabilità e servizi collaborano, e con quale ruolo? | Funzionalità, servizi, gateway, autenticazione, servizi esterni |
| Dati | Quale entità cambia, dove vive e chi ne legge il nuovo stato? | Entità e le loro rappresentazioni |
| Codice | Quali moduli, file e funzioni lo realizzano, e su che cosa poggiano? | Moduli, cartelle, file, classi e funzioni; su ogni modulo, le tessere dei progetti esterni su cui poggia |
| Infrastruttura | Dove gira, e quale dispositivo, coda o servizio di altri usa? | Dispositivi, container, servizi in esecuzione, database, code, reti, servizi esterni |

- **4.L1.** Un servizio esterno sta a due livelli, funzioni e infrastruttura: è un nodo a sé, accanto a ciò che lo usa. Un dispositivo sta a infrastruttura. Un progetto esterno sta a codice, sul modulo che lo dichiara: il modulo ne porta la tessera, con marchio e nome, chiuso o aperto; la riga che lo dichiara sta nell'ispettore. Lo stack e i nodi esterni si vedono sempre: nessuno dei due sta dietro un gruppo chiuso. Prova: `test_each_level_shows_its_node_types`, `test_the_home_level_of_the_new_types_and_of_a_queue`; la tessera nell'app come in 2.4.
- **4.L2.** Un flusso esiste ai livelli in cui ha nodi: un flusso tecnico può non avere il livello persone. Prova: `test_a_flow_exists_at_the_levels_where_it_has_nodes`.
- **4.L3.** Le corrispondenze dicono quali nodi di due livelli sono la stessa cosa. Quella verso il codice è l'appartenenza dei membri. Le altre si dichiarano citando la configurazione o il codice che le prova. Prova: `test_code_shows_files_from_the_links`, `test_infrastructure_puts_a_node_on_what_it_runs_on`.
- **4.L4.** Due flussi si incrociano nei nodi che hanno in comune: un nodo elenca i flussi che lo attraversano, e un servizio condiviso resta un nodo solo anche se vi arrivano più rami. Prova: `tests/test_codebase_map_system_map.py`, `test_about_answers_for_a_node_and_an_area`.
- **4.L5.** I livelli si guardano uno alla volta, alcuni o tutti insieme. Insieme, ogni nodo mostra le sue corrispondenze agli altri livelli e dichiara i livelli a cui non esiste. *Applicato, prova non trovata.*
- **4.L6.** **Proposta.** Gli estremi di un flusso si vedono a ogni livello, con il proprio tipo: chi lo avvia e ciò su cui termina. Oggi un livello mostra solo i suoi tipi di nodo.

**Dettaglio: applicato nell'app per il livello codice (4.1–4.5); il resto è proposta.**

La discesa è la stessa a ogni livello: area, flusso, variante, nodi del livello scelto. Al livello codice prosegue: modulo, cartella, file, classi e funzioni del file, membri di una classe.

1. **L'apertura è locale.** Un gruppo si apre e si richiude sul posto lasciando compatto il resto del grafo, anche con più gruppi aperti a dettagli diversi; il grafo si ridispone a ogni passo. Richiudere riporta al nodo e alla selezione di prima. Prova: `test_a_group_opens_in_place_and_its_summary_arrows_become_the_arrows_of_what_it_holds`. *Richiudere che riporta la selezione: applicato, prova non trovata (nessuna prova nel browser).*
2. **Si legge solo ciò che si apre.** Il primo livello non legge i simboli di nessun file; quelli di un file si leggono quando si apre quel file. Oltre una soglia di leggibilità i gruppi restano chiusi finché non si aprono. Prova: `test_the_first_level_is_the_graph_in_groups_and_reads_no_outline`, `test_the_first_level_and_an_opening_ask_the_readers_as_often_however_many_symbols_the_files_hold`. *La soglia di leggibilità: applicato, prova non trovata.*
3. **Un simbolo compare solo dentro il suo file aperto,** mai al primo livello. Resta un membro, non un nodo della mappa. Le righe stanno nell'ispettore e nei percorsi. Prova: `test_a_symbol_holding_others_opens_into_them_and_a_closed_class_keeps_its_calls_counts_and_lines`, `test_the_inspector_of_a_file_has_its_symbols_and_calls_with_lines_read_for_that_file_only`.
4. **Nessuna scomposizione inventata.** Fra modulo e file l'aggregatore è la cartella, che in molti linguaggi è il package. Prova: `test_the_graph_groups_files_by_their_smallest_module_or_else_by_their_directory`.
5. **Le frecce riassunte conservano grado, evidenze e lacune.** Chiudere un gruppo riassume i collegamenti; aprirlo mostra i nodi e le frecce che sostengono il riassunto, con le frecce solo dichiarate e le lacune. La contrazione non promuove una freccia dichiarata a provata e non nasconde una lacuna. Prova: come 4.1; nel plugin `test_an_arrow_keeps_its_state_and_proof`.
6. **Cambiare livello conserva flusso e variante** e, dove esiste una corrispondenza, il nodo osservato. Dove le corrispondenze sono più d'una si mostrano tutte. Un cambio di livello o di dettaglio costa zero chiamate al modello.
7. **Si naviga nei due versi:** da una variante fino ai file e alle funzioni che la realizzano, oppure da un effetto a tutti gli ingressi che possono produrlo. Nel plugin, per i percorsi, è `start` con `direction` (sezione 10).
8. **Le relazioni valgono per ciò che provano.** Riferirsi alla stessa entità o avere una freccia «stessa informazione» non dimostra che due copie siano sincronizzate. Nel plugin: `test_two_copies_of_an_entity_are_a_gap_not_an_arrow`.
9. **Proposta, dalle parole del proprietario (motivo 22): un flusso scelto si accende a qualunque dettaglio.** Scegliere un flusso evidenzia tutti i suoi nodi e le sue frecce. Un nodo del flusso che sta dentro un gruppo chiuso accende il gruppo; aprendolo la luce scende sul nodo. Il resto si attenua, non sparisce.
10. **Proposta, dalle parole del proprietario (motivo 22): i nodi si spostano a mano.** Un nodo si trascina; un gruppo aperto porta con sé ciò che contiene. Aprire o chiudere un gruppo fa spazio attorno a lui senza ridisporre il resto, e la posizione data a mano resta finché la persona non chiede di riordinare. Corregge il punto 4.1 dove dice che il grafo si ridispone a ogni passo.
11. **Proposta, dalle parole del proprietario (motivo 22): da un nodo si accende un percorso,** ciò che raggiunge oppure ciò da cui arriva.

## 5. Registro dei servizi e dei progetti esterni

**Applicato, tranne il nome di 5.5, parte di 5.7 e gli obiettivi di 5.9 e 5.10.** File: `daodan/data/service-registry.json`, costruito e rigenerato da `registry_build.py`. Prova: `tests/test_codebase_map_service_registry.py`, `tests/test_codebase_map_support_table.py`.

1. Per ogni voce il registro tiene nome, tipo di nodo, sito, marchio e i segni da cui la si riconosce in un progetto: nomi dei pacchetti, host, prefissi delle variabili di configurazione, file. Ogni voce riconoscibile ha una categoria scritta: framework (dà la struttura all'applicazione), libreria (il codice la chiama per una cosa sola), strumento (serve intorno al codice: build, test, lint) o servizio (gira accanto al sistema e il codice ci si collega). Framework e librerie sono le tessere del modulo che li dichiara; uno strumento sta solo nel suo stack; un servizio è un nodo esterno. Prova: `test_every_recognisable_project_has_its_category_written_and_none_is_a_framework_by_default`.
2. La macchina confronta dipendenze dichiarate, host delle chiamate e nomi delle variabili con i segni. Una corrispondenza dichiarata diventa un nodo esterno proposto, con nome, tipo, sito e marchio, senza modello. Una voce solo menzionata non è un nodo. Prova: `test_packages_files_and_images_are_recognized`, `test_the_checkers_are_one_per_kind_of_sign_each_with_its_strength`. *Gli host li legge `registry_hosts.check_hosts` dai letterali dei sorgenti e dai valori di configurazione: un host è una menzione, non un nodo.*
3. Il registro nasce da cataloghi pubblici con licenza adatta ([ricognizione](../research/2026-11-12-external-service-catalogs.md)). Un modello propone solo ciò che manca; la macchina tiene solo ciò che verifica: che il sito risponda e che il pacchetto esista. Prova: `test_a_model_proposal_keeps_only_what_the_machine_verifies`.
4. Il marchio è un file nel prodotto oppure si scarica al primo uso dalla fonte ufficiale, quando le sue condizioni non ne permettono la ridistribuzione. Origine e condizioni stanno in `REGISTRY-NOTICES.md`. Senza marchio il nodo prende l'icona generica del suo tipo. Il marchio viene da Simple Icons e, dove manca, dall'SVG ufficiale che il proprietario del servizio pubblica, ripulito, con l'origine annotata. Le raccolte di icone dei fornitori cloud (AWS, Azure, Google Cloud), le cui condizioni parlano di diagrammi e non di ridistribuzione, non si distribuiscono: Daodan le scarica dalla fonte ufficiale al primo uso, sulla macchina di chi lo usa; poi le ridisegnerà il proprietario (motivo 21). Prova: `test_a_shipped_mark_that_is_not_of_simple_icons_says_where_it_comes_from`, `test_a_package_mark_is_downloaded_through_the_verified_download_and_comes_out_clean`.
5. Un servizio che nessuna fonte riconosce prende il nome del pacchetto o dell'host e resta marcato come non riconosciuto. *Applicato, prova non trovata.*
6. Ogni nodo esterno mostra nome e marchio in ogni grafo e a ogni livello. Prova: `tests/test_codebase_map_app.py`, `test_the_mark_of_a_registry_entry_is_served_by_its_id_and_nothing_else_is`.
7. La macchina legge anche i file che dichiarano l'esecuzione o l'architettura: docker-compose, Dockerfile, manifest di Kubernetes, configurazioni di hosting e di CI. Ciò che dichiarano diventa nodi proposti, con il file come evidenza. *In corso: Compose e Dockerfile si leggono (`tests/test_codebase_map_system_brief.py`, `test_compose_declares_services_and_the_image_is_recognized`); dei manifest di Kubernetes e dei file di hosting e di CI la scheda dà il nome, non il contenuto (`system_brief._runtime`).*
8. Un altro strumento di riconoscimento entra solo se è pubblico, ha licenza adatta e nel benchmark riconosce qualcosa che le altre fonti non vedono. Con questo criterio stack-analyser è stato tolto il 16 novembre 2026; il suo fork torna come riconoscitore unico con la [spec dello stack dal fork](2026-11-21-stack-dal-fork.md), non ancora collegata. Prova: README di `benchmarks/system-map`, «Il registro dei servizi esterni».
9. **Obiettivo dei framework:** almeno 200 riconosciuti ed elaborati. Per ogni framework, come dati, i segni per riconoscerlo e i suggerimenti sui suoi legami (Principio 2), più un caso reale misurato; nessun codice per framework. *Proposta* (motivo 21).
10. **Obiettivo dei servizi:** almeno 500 riconoscibili con il marchio, per disegnarli come nodi esterni (5.4, 5.6). *In corso* (motivo 21).
11. **Una tabella generata di ciò che è supportato,** divisa per tipologia (linguaggi, build tool e toolchain, framework e librerie, servizi esterni, tipi di legame), con copertura e percentuale di riuscita dove una misura esiste. La genera uno script dai dati del prodotto e dai risultati dei benchmark, e un test fallisce se resta indietro (motivo 21). Prova: [`docs/plugins/codebase-map-supporto.md`](../plugins/codebase-map-supporto.md), `tests/test_codebase_map_support_table.py` (`test_the_committed_document_is_the_one_the_script_writes`).

## 6. Scheda del sistema

**Applicato nel plugin: 6.1, 6.3 e 6.4; 6.2 e 6.5–6.8 dicono il loro stato.** Prova: `tests/test_codebase_map_system_brief.py`.

1. La macchina compone, senza modello, un riassunto di ciò che i passi di analisi hanno prodotto: moduli e cartelle con il numero di file; ingressi, store e rotte; servizi esterni riconosciuti; file che configurano esecuzione e rilascio; collegamenti provati, dedotti e osservati, contati fra gruppi; titoli delle schede già scritte. Dichiara i passi non eseguiti. Prova: `test_the_steps_that_did_not_run_are_declared`, `test_externals_say_their_source`.
2. La scheda porta i candidati. La macchina parte dagli ingressi e segue i collegamenti: un file raggiunto solo attraverso un ingresso sta nel candidato di quell'ingresso; un file che più ingressi raggiungono per strade diverse apre un candidato suo. Ogni chiave di store, ogni servizio esterno e ogni progetto esterno è un candidato. Un candidato prende l'identità dal suo primo file, così resta lo stesso fra due snapshot. *Proposta: oggi la scheda fa un gruppo per risorsa toccata da almeno due ingressi (`system_brief._groups`, `test_one_candidate_group_per_shared_resource`); questa partizione sta in `benchmarks/system-map/candidates.py`, misurata nel README, «Che cosa dà il grafo senza modello, sull'area dei pagamenti di phazly».*
3. La scheda ha un tetto di dimensione, scritto nel README del benchmark. Oltre il tetto i candidati meno collegati si riassumono per cartella e restano interrogabili. Il tetto è ciò che resta dell'intera risposta sotto `system_brief.LIMIT` (motivo 11). Prova: `test_the_text_keeps_within_the_cap`, `test_a_group_past_the_holders_counts_its_entry_points_by_directory`, `test_an_answer_at_full_cap_keeps_under_the_limit`. *«Restano interrogabili»: applicato, prova non trovata.*
4. Per ogni candidato la scheda dà identificativi, segnale, eventuale gestore, effetti e fonte. Un riferimento condiviso conserva lo stesso identificativo in tutti i gruppi. Prova degli identificativi: `test_sections_have_fixed_labels_and_one_numbered_item_per_line`. *Gestore ed effetti: applicato, prova non trovata.*

**6.5–6.8.** Ciò che la macchina dà al modello (gli ingressi letti dalla macchina, un percorso per ingresso, la confezione, i segreti): [Ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), 6.5–6.8.

## 7. Scoperta dei flussi

I punti 7.1–7.8 sono in [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 7.

## 8. Verifica

**Applicato nel plugin in parte: lo stato è su ogni punto.** Prova: `tests/test_codebase_map_system_map.py`, `tests/test_codebase_map_system_levels.py`.

La macchina non giudica ciò che il modello sostiene: lo prova quando il grafo lo mostra e dice quanto è provato. Rifiuta solo ciò che si riferisce a cose che non esistono, con il motivo, e l'agente corregge una volta.

1. **Nodo:** nome unico e tipo dell'elenco; comprende candidati che esistono. Un nodo senza codice viene da un candidato esterno o da un ingresso; un nodo non visto dichiara dove sta. Prova: `test_a_node_type_out_of_the_list`, `test_two_names_equal_but_for_case_and_accents`, `test_an_unseen_node_says_where_it_is`. *Nel codice: oggi il nodo comprende membri che esistono (2.1), e un nodo senza codice cita la sua evidenza (`test_a_node_without_code_cites_its_evidence`).*
2. **Flusso e frecce:** la macchina prende ciò che sta su un percorso del grafo da un punto di partenza a un punto di arrivo, seguendo chiamate, attivazioni, scritture e letture, senza limite di passi. Fra due nodi la freccia è l'insieme dei collegamenti dai membri del primo ai membri del secondo, che sono la sua prova. Quando tocca un'entità la freccia è legata alla rappresentazione che la prova nomina: entrare da una rappresentazione e uscire da un'altra è una lacuna, non una freccia. Fra un nodo senza codice e uno con codice la freccia è dichiarata, con il punto che li lega. Una partenza che non raggiunge nessun arrivo è un buco: la macchina dice dove il grafo si ferma, mostra l'ultimo punto noto, e la freccia attesa resta «da verificare». Prova: `test_arrows_are_proved_by_the_links`, `test_an_arrow_no_link_proves_is_refused`, `test_an_arrow_with_an_end_without_code_is_declared`, `test_two_copies_of_an_entity_are_a_gap_not_an_arrow`. *Il verificatore conserva le frecce rifiutate con la causa. Con ingressi ed effetti dichiarati, ogni partecipante deve stare su un percorso orientato fra i due. Tronconi scollegati o effetti irraggiungibili lasciano il flusso incompleto. Le schede storiche senza estremi espongono `reachability=not_declared`. La prova di una singola freccia riguarda un collegamento diretto fra membri o una scrittura e lettura della stessa chiave.*
3. **Corrispondenza:** quella verso il codice è verificata sui membri. Le altre sono dichiarate, con il punto citato che esiste. Prova: `test_code_shows_files_from_the_links`, `test_a_declared_arrow_cites_a_point_of_the_code_end`. *Nel codice: `on` fra due nodi con codice è accettato senza un punto citato; la prova nominata controlla `cite` su una freccia (task 7b).*
4. **Copertura:** quanti ingressi, store e rotte stanno in almeno un flusso, e quanti candidati in almeno un nodo. Il resto è elencato, non nascosto. Prova: `test_coverage_counts_what_the_accepted_flows_hold`. *Nel codice: la copertura conta ingressi, store e rotte; i candidati no.*
5. **Identità e conferma:** ogni nodo e ogni flusso ha un'identità che non dipende dal nome. Un nodo nuovo è rifiutato come doppione quando uno esistente dello stesso tipo ha gli stessi candidati, li contiene o ne è contenuto. Una proposta resta `inferred` finché il progetto non la conferma. Un nome confermato cambia solo con una rinomina esplicita, e una proposta non toglie ciò che è confermato. Prova: `test_identity_does_not_follow_the_name`, `test_a_rename_does_not_take_the_name_of_another_node`, `test_a_proposal_removes_nothing_it_does_not_name`. *Nel codice: il doppione si riconosce dai membri, non dai candidati (`test_a_node_inside_another_is_its_part_and_stays_outside_the_flows`); il progetto conferma in `codebase-system-map.json` (`system_map.DECLARED_FILE`).*
6. **Freschezza:** nodi, frecce e corrispondenze sono legati ai digest dei file da cui dipendono. Quando un file cambia, la macchina ricalcola senza modello candidati e frecce, e torna all'agente solo un nodo i cui candidati cambiano. Ciò che è solo dichiarato torna all'agente quando cambia il file che cita. Prova: `test_a_changed_file_is_proved_again_or_sent_back`. *Il salvataggio conserva il digest dei record fuori dalla proposta. Una citazione cambiata resta scaduta finché viene riesaminata. L'app mostra quali record richiedono un riesame.*

## 9. Etichette e scheda di un percorso

**Applicato, tranne 9.1.** Prova: `tests/test_codebase_map_flows.py`.

1. Su richiesta il modello legge un collegamento `scrive` o `legge` e ne scrive granularità e significato, legati ai digest dei due simboli. Senza etichetta il campo resta vuoto: non si deduce. Servono a vedere quando chi scrive e chi legge lo stesso store intendono granularità diverse ([caso misurato](../../benchmarks/phazly-flow/README.md)). *Applicato, prova non trovata: nel codice non si trova dove le etichette si scrivono e si legano ai digest; la misura del caso, con la soglia non valutata, è in [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md), «Etichette di granularità e significato».*
2. Per «dove va questo dato» il modello dà i punti di partenza, la macchina traccia i collegamenti, il modello riceve l'elenco dei passaggi e apre il sorgente solo dove il dato si scrive, si legge o si trasforma. Prova: `test_display_reaches_the_service_store_through_the_route`.
3. La scheda di un percorso dice nome, tipo, rami e che cosa accade al dato a ogni tappa. Ogni frase cita un passaggio dell'elenco: una riga che non ne cita uno rifiuta la scheda. La scheda diventa scaduta quando cambiano i file o le prove del percorso, anche dopo una modifica alle sole regole. Prova: `test_the_service_asks_for_rules_records_them_and_answers_at_a_level`. *Nel codice: il controllo è per riga, non per frase (una riga con due frasi passa con una citazione), e guarda nome, tipo e citazioni: rami e significato non li verifica.*

## 10. Interrogazione

**Applicato nel plugin.** Prova: `tests/test_codebase_map_flows.py` (`test_the_service_asks_for_rules_records_them_and_answers_at_a_level`), `tests/test_codebase_map_mcp.py` (`test_brief_map_about_and_levels`, `test_a_wrong_map_or_a_mix_of_questions_names_what_is_wrong`). `codebase_map_flows` risponde a una domanda per volta:

1. `rules` registra le regole di collegamento; senza regole la risposta è il loro formato.
2. `start` con `direction`: `from` un ingresso (che cosa deve reagire), `to` un effetto o uno store (chi lo scrive e che cosa significa), `through` un nodo (quali flussi lo attraversano). La risposta elenca i collegamenti con granularità, significato, freschezza, lacune e ciò che resta da esplorare, e distingue un flusso incompleto da uno completo diviso in più unità. *Granularità e significato: come 9.1.*
3. `card` registra la scheda di un percorso.
4. `brief` dà la scheda del sistema; `map` registra una proposta e la riporta; `about` risponde per un'area, un flusso o un nodo, e con `levels` mostra un flusso a quei livelli.
5. **Proposta:** `03-flows.md` si genera dalla mappa del sistema; il grafo dell'app, l'esploratore, MCP e review leggono lo stesso risultato.

## 11. Perimetro di una review

I punti 11.1–11.6 sono in [ricerca dei flussi e pacchetto di una review](2026-11-20-ricerca-e-pacchetto-di-review.md), sezione 11; l'uso dell'embedder è la sua sezione 12.

## Assunzioni e limiti noti

Del metodo:

- **1.** Nomi, tipi e tagli sono proposte del modello, e per questo il progetto conferma. Candidati e frecce sono della macchina, che vede solo ciò che il grafo contiene.
- **2.** Il passo statico descrive le chiamate ricostruite dal codice. Il passo dinamico aggiunge le destinazioni osservate nei test. Flusso, vista del codice e prove della mappa conservano il registratore e distinguono osservazioni esatte e campioni. Un sito di chiamata può avere più destinazioni. La scheda indica quando ci sono prove dinamiche.
- **3.** Dove il grafo ha un buco (un valore passato attraverso un contesto, un componente reso senza una chiamata, una chiave scritta in una forma che le regole non leggono) la freccia resta da verificare e il buco va dichiarato, mai taciuto. Una freccia provata dice che un collegamento esiste, non che il flusso sia completo.
- **4.** Granularità e significato sono affermazioni del modello, da verificare sul sorgente.
- **5.** Il livello infrastruttura poggia su ciò che configurazione e codice dichiarano: quello che esiste solo in una console esterna non si vede. Ciò che sta fuori dallo snapshot entra solo se dichiarato.
- **6.** Dove il linguaggio aggrega con una dichiarazione e non con una cartella (un namespace, un modulo annidato), il grafo mostra la cartella.
- **7.** Dove la mappa non analizza un linguaggio, la macchina non deduce collegamenti.

Delle prove (i limiti 14, 16, 17 e 21 sono in [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), 11 e 19 in [ricerca e pacchetto di review](2026-11-20-ricerca-e-pacchetto-di-review.md), 10 e 20 nella [pipeline di analisi](2026-11-15-pipeline-di-analisi.md)):

- **8.** **Riferimenti non confermati.** I cinque riferimenti dell'intero sistema li ha scritti un agente per progetto (Opus 5.5), leggendo i file senza eseguirli; il proprietario ha confermato le regole (i tipi, `devops`, il database al primo livello), non i nodi né i flussi. Ogni numero misurato contro di loro è una bozza (README di `benchmarks/system-map`, «Riferimenti dell'intero sistema»).
- **9.** **Il tetto viene da un caso.** L'accordo fra due mappatori è misurato sul caso più piccolo (62 nodi): sui flussi alla loro grana è 33%, sugli ingressi 36%, sugli effetti 27% [prova non nel repository]. Finché il proprietario non conferma i flussi vale la profondità 1 (74%); le soglie, 0,85 volte l'accordo, sono proposte (motivo 1).
- **12.** **Una lingua, un proprietario.** Cinque casi di quattro prodotti, tutti dello stesso proprietario e in italiano; quattro sono privati, e le loro misure si rifanno solo con i progetti, che stanno fuori dal repository (motivo 2).
- **13.** **Letture, non misure.** Alcuni numeri sono letture a mano, e il README le chiama così: i nomi delle schede riconosciuti (15 su 23), i flussi della mappa letti per nome («Misura di partenza» [prova non nel repository]).
- **15.** **Non misurato:** il giro intero da zero ([piano della pipeline intera](../plans/2026-11-20-pipeline-intera.md), sezione 2); la stabilità con i lettori nuovi; EmbeddingGemma 2, scelto il 20 novembre (motivo 12), e tempo e memoria di ogni embedder; il tempo di un avvio di Secretlint; gli ingressi dell'interfaccia da scip-typescript dopo la preparazione; la fonte osservata; la scoperta cieca; le misure system-map 7 e 8.
- **18.** **Il 74% non è un conto di flussi** (I6) [prova non nel repository]. È la media della somiglianza migliore sui nodi alzati alla profondità 1, e una proposta può servire più riferimenti: con un flusso abbinato su tre il test del comparatore dà 100%. Ingressi (36%) ed effetti (27%) contano il nodo nel flusso abbinato, non il suo ruolo. La soglia a 0,85 volte è una scelta, su un caso.

## Prova

Le soglie stanno nel README di ogni benchmark, scritte prima di ogni misura. Le prove girano su Modal.

**[`benchmarks/flow-model`](../../benchmarks/flow-model/README.md)**, senza modello tranne la 4; casi reali in [`polar-flow`](../../benchmarks/polar-flow/README.md), [`tududi-flow`](../../benchmarks/tududi-flow/README.md) e [`phazly-flow`](../../benchmarks/phazly-flow/README.md). Misure 2, 3 e 5 sulla fixture; 1 fatta su phazly; della 4 lette due coppie delle venti previste, soglia non valutata (README di `phazly-flow`, «Etichette di granularità e significato»).

1. **File di un difetto noto:** a parità di perimetro e di limite, in quanti incarichi `pack()` mette i file dei difetti attesi e in quante unità li mette la proposta.
2. **Fixture** su due strati, con uno store condiviso fra due funzionalità, una rotta, una violazione fra chi scrive e chi legge e una variante lecita simile: collegamenti trovati contro attesi, collegamenti falsi e lacune dichiarate.
3. **Caso reale fra strati:** da un fatto mostrato il flusso arriva allo store che lo contiene, attraverso la rotta dichiarata dal caso.
4. **Etichette:** granularità e significato su un campione, contro una lettura manuale; costo per collegamento.
5. **Simboli e funzionalità:** una catena di almeno tre chiamate fra file diversi, un ciclo, una funzionalità con più ingressi; i file entrati in un flusso senza appartenere agli attesi; tutti i file assegnati anche con un limite basso.

**[`benchmarks/system-map`](../../benchmarks/system-map/README.md).** Misure 2, 3 e 4 raggiunte; 1, 5 e 6 no; il modello dell'agente non è fissato. Le misure dell'intero sistema si fanno contro i riferimenti dell'intero sistema di cinque casi, con un controllo che apre i file citati senza eseguire nulla (`reference.py check`) e un comparatore che abbina i nodi per file, gli esterni per id del registro, i flussi per nodi, mai per nome (`score.py system`); il tetto di ogni misura è l'accordo fra due mappatori indipendenti, e i flussi alla loro grana non hanno soglia finché il proprietario non li conferma (motivo 1). Ciò che nomina un progetto privato (riferimenti, risultati, campioni) sta fuori da git; su Modal vanno archivi di solo codice e configurazione, fatti sul commit a cui il riferimento è legato (motivo 2).

1. **Riproduzione:** per un'area di un caso reale, la mappa proposta contro una fatta a mano che l'agente non vede: nodi confrontati per membri, flussi, frecce per grado.
2. **Secondo progetto:** lo stesso prompt su un altro caso: frecce provate, copertura, lettura di un campione di nomi.
3. **Livelli:** per un flusso del riferimento, a ogni livello i nodi mostrati sono dei tipi di quel livello e le corrispondenze citano punti che esistono.
4. **Costo:** token e costo per mappa e per modello; quante volte l'agente apre il sorgente.
5. **Stabilità:** due esecuzioni sullo stesso snapshot danno gli stessi nodi, confrontati per candidati.
6. **Registro:** quanti servizi e progetti esterni usati dal progetto vengono riconosciuti, e quanti riconoscimenti sono sbagliati.
7. **Dall'intento ai controlli:** per un intento in linguaggio comune, le cose da controllare che la mappa restituisce contro l'elenco scritto prima dal proprietario.
8. **Review:** lo stesso intento con perimetro e brief dalla mappa, contro la review di oggi. È a pagamento: si chiede prima.

**Scoperta cieca sull'intero sistema.** È la prova decisiva della sezione 7. L'atteso è accessibile solo al valutatore, che verifica identità dei processi e dei rami, falsi raggruppamenti, copertura, motivazioni del perimetro e costo complessivo. Il protocollo la distingue dal controllo con estremi noti. Nel benchmark storico di phazly l'agente ha ritrovato 0 dei 3 flussi dell'area pagamenti; con partenze e arrivi indicati a mano il grafo ha aggiunto 0 file estranei, lasciando fuori alcuni tratti attesi. [Parametri, risultati storici e misure da eseguire](../../benchmarks/system-map/README.md#grafo-contro-modello-il-confronto-ancora-da-fare).

**Grafo dell'app.** Un test conta le letture: il primo livello non legge nulla che cresca con i simboli dei file (`test_the_first_level_and_an_opening_ask_the_readers_as_often_however_many_symbols_the_files_hold`). Il 18 novembre, prima del caricamento per livelli, il grafo di un progetto di 2.408 file rispondeva in 245 secondi; la misura dopo va fatta su Modal.

## Ordine di lavoro

Dove differisce, vale il [piano della pipeline intera](../plans/2026-11-20-pipeline-intera.md), sezione 1.

1. Grafo dell'app: vederlo in un browser e misurarlo su un progetto grande, su Modal.
2. Mappa del sistema nell'app: scheda, proposta con il motore dell'app, verifica, livelli; estremi a ogni livello.
3. Candidati e frecce dalla macchina, grado «da verificare»; misure da 1 a 5 di nuovo.
4. Scoperta dai due capi, varianti, riesame dei resti; scoperta cieca.
5. Esploratore sulla mappa del sistema; i nomi vecchi dei livelli escono dal codice.
6. Review: dall'intento ai controlli, poi i revisori; misure 7 e 8.

**Aperta: da approfondire:** quali buchi del grafo si chiudono con una regola statica e quali con il passo dinamico: non misurato dopo il passo dinamico sui casi della mappa (limite 10). **Da decidere:** dove il progetto registra ciò che conferma (il codice usa già `codebase-system-map.json`, 8.5); il tetto della scheda del sistema (oggi ciò che `system_brief.LIMIT` lascia, 6.3); come si raggruppano i candidati quando sono troppi per la scheda; il limite di un'unità e se le unità estendono `scope_planner.py`; come mostrare un aggregatore dichiarato dal linguaggio quando non è una cartella. Le altre sono in «Decisioni aperte».

## Prove non trovate, parole in due sensi

**Applicato, prova non trovata:** 1.5 (le regole legate ai digest dei file citati); 1.6 (il limite di tre correzioni, solo nel prompt); 2.3; 2.5; 4.L5; 4.1 (richiudere riporta la selezione); 4.2 (la soglia di leggibilità); 5.5; 6.3 («restano interrogabili»); 6.4 (gestore ed effetti); 7.6 (budget cumulativo e ripresa); 9.1 e 10.2 (granularità e significato: il codice non le tiene); Principio 2 (nessun test controlla che il codice dei legami non nomini un framework); Principio 4 (la scelta fra candidati incerti marcata `proposto`).

**Parole usate in due sensi,** segnalate e non corrette, perché correggerle tocca testo che decide:

- **Ingresso:** dove un flusso comincia (Parole) e un ingresso della skill `map` (`analyze`, `team-analyze`: stato e sezione 7). In 6.1 e 8.4 «ingressi, store e rotte» lo distingue dalla rotta, che per Parole è un ingresso. La [spec dell'esecuzione](2026-11-19-esecuzione-del-programma.md) lo usa per una rotta sola.
- **Candidato:** un gruppo di membri (Parole, 2.1, 6.2) e un possibile ingresso trovato da un lettore (6.5); in 1.3, una rotta che potrebbe accoppiarsi.
- **Percorso:** una sequenza di collegamenti (Parole) e il percorso di un file (Parole, «Filesystem»; 11.3) o di una rotta («schema del percorso», 1.2).
- **Livello:** un punto di vista (Parole) e la profondità del grafo aperto («primo livello», 4.2, 4.3, «Prova»).
- **Nodo:** una cosa con un nome, mai un simbolo (Parole) e un elemento del grafo dell'app, che al livello codice comprende classi e funzioni (tabella di §4).
- **Collegamento:** fra due membri (Parole) e un indirizzo che apre l'app da fuori (Parole, «Ingresso»).
- **Dichiarato:** un grado e un'evidenza (Parole, «Collegamento» e «Grado») e scritto dal progetto («dichiarato dal progetto», 1.4; «la dipendenza dichiarata», 2.2; «una corrispondenza dichiarata», 5.2).
- **Contesto:** i file che si consultano senza giudicarli (Parole) e il quadro per interpretare un gruppo (7.1) o ciò che il modello ha davanti a una domanda (7.7).
- **Scheda di un percorso:** quella che il modello scrive e la macchina controlla (9.3) e quella che la macchina compone per il modello (6.6; README, «Schede dei percorsi» [prova non nel repository]).

Sinonimi per uno stesso concetto: «servizio esterno» e «servizio di altri».

## Motivi delle scelte

Una voce per regola; la regola la cita con «(motivo n)». I motivi 5–11 e 14 sono in [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), 12 e 13 in [ricerca e pacchetto di review](2026-11-20-ricerca-e-pacchetto-di-review.md), 15 nella [pipeline di analisi](2026-11-15-pipeline-di-analisi.md) («Scelte», 7). Ogni voce dice chi ha deciso, il perché con il suo numero, che cosa si è scartato e dove sta la prova. «README» è quello di [`benchmarks/system-map`](../../benchmarks/system-map/README.md), salvo dove è detto un altro. Le sezioni del README segnate «[prova non nel repository]» non sono mai state in git, e così il «piano del 19 novembre» (`2026-11-19-verso-i-riferimenti.md`): i numeri e le decisioni che li citano restano qui, senza una prova che si rilegge o si riesegue.

- **1.** **Il bersaglio e il tetto** («Prova», system-map). Le regole dei riferimenti le ha confermate il proprietario; nodi, flussi e soglie no. Perché: il riferimento d'area usato fino al 13 novembre (11 nodi, 3 flussi) non misura il richiamo globale; sul caso più piccolo due mappatori che non si vedono concordano su nodi (77%), profondità 0 e 1 (93%), tipo (96%), `inside` (91%), ma sui flussi alla loro grana al 33% (74% con i nodi alzati alla profondità 1). Scartato: contare i nomi, che due mappatori scrivono diversi per la stessa cosa; un abbinamento dei flussi più largo, provato il 19 novembre, che li accoppiava a caso. Prova: README, «Il tetto: l'accordo fra due mappatori» [prova non nel repository] e «Soglie proposte» [prova non nel repository]; `tests/test_benchmark_system_map_score.py`; `benchmarks/system-map/test_reference.py`.
- **2.** **Fuori da git ciò che nomina un progetto privato** («Prova», system-map). Deciso dal proprietario il 19 novembre, come eccezione alla regola di `AGENTS.md` che una prova resti nel repository. Perché: il repository è pubblico; un caso traccia 589 MB di cui meno di 2 MB di codice, un altro file `.env` veri; poche ore dopo la scrittura tre riferimenti su sei avevano 28 citazioni fuori riga, da cui il legame al commit. Scartato: tenere in git il caso pubblico (era la raccomandazione); l'archivio di tutto il tracciato; il controllo sull'albero di lavoro. Prova: `.gitignore`, `benchmarks/system-map/test_code_archive.py`, `test_reference.py`. Conseguenza: chi non ha i progetti non rifà le misure dei cinque casi.
- **3.** **Tipi, padre e campi dei servizi di altri** (Parole; 2.6, 2.7, 3.7). Tipi e `devops` confermati dal proprietario per i riferimenti; id del registro, famiglia, ruolo e modo decisi da lui il 19 novembre; il livello dei tipi nuovi è la raccomandazione 5 del piano del 19 novembre, senza decisione scritta. Perché: nei riferimenti 14–45 nodi per caso sono figli dello stesso tipo del padre e 8–29 stanno fuori dai flussi, che `record` toglieva; dopo i tipi e `inside` la precisione sale da 4 nodi su 7 a 6 su 6, `inside` regge in 19 coppie su 24, la famiglia è giusta su 11 servizi su 13 (il gate non passa: mappe di 6–15 nodi). Scartato: ritrovare un esterno per testo libero; build e rilascio sotto `tecnico`. Prova: README, «Dopo la Parte B» [prova non nel repository]; `tests/test_codebase_map_system_map.py`, `tests/test_codebase_map_system_levels.py`.
- **4.** **I nomi** (Parole, «Nome»). Deciso dal proprietario il 19 novembre. Perché: con la sola regola «come li direbbe chi usa il prodotto» lo stesso flusso usciva con due nomi; rinominati, i riferimenti avevano 3 flussi con una parola vuota, 9 servizi con un nome diverso dal registro, 6 parti con il nome del prodotto. La macchina fa due controlli soli perché sono i soli che fa senza sbagliare. Scartato: controllare forma, singolare e nome del prodotto, che hanno eccezioni vere. Prova: `tests/test_codebase_map_system_map.py` (`test_a_flow_name_that_begins_with_an_empty_word`, `test_an_external_node_begins_with_the_name_of_its_registry_entry`).
- **16.** **Lo scopo è il grafo dei moduli** (Principio 1). Parole del proprietario del 18 novembre. Perché: quel giorno l'app ha analizzato un progetto d'esempio pubblico fino in fondo e ha mostrato un grafo con un nodo solo, poi con sedici gruppi e due relazioni: il grafo nasceva solo da import e chiamate dentro lo stesso linguaggio, e i flussi trovati restavano un elenco a parte. Scartato: una vista per cartella o per import. Prova: `tests/test_codebase_map_visual.py` (`test_a_route_call_is_a_relation_with_its_key_both_sides_and_a_count`, `test_a_store_written_in_one_module_and_read_in_another_is_a_relation`); il grafo non è misurato su un progetto grande (stato, «Grafo dell'app»).
- **17.** **Il censimento dei tipi di legame, nessun nome di framework nel codice** (Principio 2; 5.9). Parole del proprietario del 18 novembre; nessuna misura. Perché: le forme con cui i framework scrivono un legame sono aperte, il censimento dei ruoli no ([guida ai punti di connessione](../research/2026-11-14-punti-di-connessione.md), «Regola»). Scartato: regole incorporate per framework. Prova: le forme stanno come dati in `daodan/data/entry-queries.json` e nel registro (motivo 8); in `flows.py` ed `entries.py` nessun nome di framework, salvo un commento; nessun test lo controlla.
- **18.** **Un motore generale e un adattatore per tipo** (Principio 3). Parole del proprietario del 18 novembre. Perché: quel giorno `flows.py` univa una richiesta alla sua rotta solo a testo identico: `/api/dogs/${dogId}` e `/api/dogs/<int:id>` non si incontravano. Stato: nel nucleo la rotta si accoppia per metodo e schema del percorso dentro `flows.py` (`tests/test_codebase_map_flows.py`: `test_a_call_joins_the_route_its_method_and_path_schema_meet`, `test_a_schema_that_meets_several_routes_is_uncertain_and_no_link`); il motore con un adattatore per tipo era scritto e provato su Modal il 18 novembre, non su `main`, e il piano del 19 novembre lo dà nel branch `feat/link-key-shape`.
- **19.** **Il modello propone, la macchina verifica** (Principio 4). Principio del proprietario del 18 novembre, forma proposta. Perché: le regole le scrive un modello per ogni progetto, e se c'è un legame deve deciderlo codice con i suoi test, non le parole del modello. Prova: le regole stanno accanto allo snapshot (`flow-rules.json`, `mcp_service.py`); senza motore l'app dice che cosa fare (`tests/test_codebase_map_app.py`, `test_finding_the_links_without_an_engine_says_what_to_do_and_starts_nothing`); l'esito lo dà il servizio (1.6). La scelta fra candidati incerti marcata `proposto`: prova non trovata.
- **20.** **Tre livelli per i tipi di legame** (1.7). Principio del proprietario del 18 novembre, forma proposta: non si può prevedere ogni tipo di scambio fra due nodi. Scartato: un adattatore per ogni scambio immaginabile. Prova: il primo tipo, REST, ha il suo caso in [`benchmarks/connection-points`](../../benchmarks/connection-points/README.md); il terzo livello è 1.3.
- **21.** **Obiettivi del registro e tabella generata** (5.4, 5.9, 5.10, 5.11). Marchi, obiettivo dei servizi e tabella: parole del proprietario del 18 novembre; obiettivo dei framework: principio suo, forma proposta. Perché: un servizio esterno si disegna come nodo con il suo marchio, e le condizioni delle raccolte cloud parlano di diagrammi, non di ridistribuzione. Stato: il 18 novembre 222 servizi su 495 erano riconoscibili con il marchio; oggi il test ne tiene almeno 432 (`tests/test_codebase_map_service_registry.py`, `test_the_recognisable_services_that_have_a_mark_do_not_drop_below_432`); i suggerimenti per framework sono da fare; la tabella c'è, con il suo test.
- **22.** **Il grafo dell'app sul prodotto** (3.7, 4.9–4.11). Parole del proprietario del 19 novembre; nessuna misura. Prova prevista: `benchmarks/standalone-app/app_graph.py`, nel container (piano del 20 novembre, task 12).

## Errori registrati

- Un abbinamento più largo dei flussi, provato il 19 novembre, li accoppiava a caso attraverso i nodi grandi ed è stato tolto.
- Il piano del 19 novembre lascia da fare il secondo riferimento (A4), che il README usa per il tetto.
- Gli errori sulle schede dei percorsi e sulla lettura dall'albero sono in [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), «Errori registrati».

## Decisioni aperte

Le decisioni 1, 5, 6, 8 e 9 sono in [ingressi e scoperta dei flussi](2026-11-20-ingressi-e-scoperta-dei-flussi.md), 2, 10 e 11 in [ricerca e pacchetto di review](2026-11-20-ricerca-e-pacchetto-di-review.md), 3 nella [pipeline di analisi](2026-11-15-pipeline-di-analisi.md).

- **4.** Le soglie (0,85 volte il tetto) e la conferma dei riferimenti sui campioni di `results/system/<caso>-conferma.md`, del proprietario; fino ad allora ogni numero è una bozza.
- **7.** Dal piano del 19 novembre restano aperte le decisioni 4 (marchi senza SVG ridistribuibile), 6 (branch degli altri), 7 (worktree `app-flows`) e 8 (forza di un host).

## Decisioni di architettura da registrare dopo la validazione

- Lo scopo è il grafo dei moduli, e le sue relazioni sono i flussi: Principio 1.
- Si censiscono i tipi di legame; nessun nome di framework nel codice, la conoscenza di un framework è un dato: Principio 2.
- Un motore generale e un adattatore per tipo di legame: Principio 3.
- Il modello propone, la macchina verifica: Principio 4.
- La macchina mostra, il modello nomina: 6.5, 6.6 e 7.7.
- Ogni testo che esce verso un modello passa il controllo dei segreti: 6.8.
- Una mappa dei moduli sola, con natura, linguaggi, toolchain e pacchetti: [pipeline di analisi](2026-11-15-pipeline-di-analisi.md), sezione 1, «Scansione: la mappa dei moduli».
- Sotto il blocco del progetto nulla aspetta il container: [pipeline di analisi](2026-11-15-pipeline-di-analisi.md), sezione 6.
