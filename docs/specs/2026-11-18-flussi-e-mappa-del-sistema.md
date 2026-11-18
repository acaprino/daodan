# Flussi e mappa del sistema

**Stato:** unica spec dei flussi, dal 18 novembre 2026. Sostituisce «Fase 2: flussi e unità ricavati dal grafo» (9 novembre), «Mappa del sistema» (12 novembre, approvata) e «Scoperta dei flussi multilivello» (18 novembre, proposta). Le prime due restano nella storia di git (ultima modifica `b6f877bad`): i numeri di sezione citati dai documenti scritti prima di oggi sono i loro. Ogni sezione dichiara il suo stato: **applicato**, **in corso** o **proposta**. L'uso nella review si misura nella [fase 3](2026-11-09-flows-in-review.md); i collegamenti osservati in esecuzione sono del [passo dinamico](2026-11-12-passo-dinamico.md). **Piano:** [`docs/plans/2026-11-12-mappa-del-sistema.md`](../plans/2026-11-12-mappa-del-sistema.md).

Daodan deve saper rispondere a quattro domande:

1. Di quali cose è fatto questo sistema e che cosa fa?
2. Che cosa succede quando arriva questa azione o questa richiesta, e chi scrive il dato che il sistema mostra o restituisce?
3. Come appare lo stesso processo a chi lo usa, a chi lo progetta, a chi lo scrive e a chi lo fa girare?
4. Che cosa tocca questa richiesta di review?

La risposta ha due usi: studiare un sistema sconosciuto e trovare dove fare una review partendo dall'intento di chi la chiede. L'utente fornisce il sistema; nomi, partecipanti, ingressi, esiti e varianti emergono dall'analisi. Vale per qualsiasi app o servizio: i casi concreti stanno nei README dei benchmark.

## Parole

Ogni parola ha un solo significato.

| Parola | Significato |
| --- | --- |
| Nodo | Una cosa del sistema con un nome, al livello a cui la nomina una persona. Raccoglie i suoi membri. Un simbolo da solo non è un nodo |
| Tipo di nodo | Elenco chiuso: attore, schermata, funzionalità, servizio o API, gateway, database, coda, autenticazione, dispositivo, entità, altro |
| Posizione | Interno: ha codice nello snapshot. Esterno: è di altri. Non visto: fa parte del sistema, ma i suoi file stanno fuori dallo snapshot |
| Servizio esterno | Un servizio di altri che gira altrove: Stripe, Firebase |
| Progetto esterno | Software di altri su cui il sistema è costruito o dentro cui gira: un framework, una libreria, un runtime, un motore di container (Angular, NumPy) |
| Membro | Ciò che un nodo raccoglie: file, simboli, chiavi di store, rotte |
| Entità | Un dato con un nome (un ordine, un utente), ovunque sia salvato. I suoi membri sono le rappresentazioni: una tabella, una chiave di stato, una cache |
| Store | Dove un dato vive: stato globale, tabella o collezione, file, cache |
| Collegamento | Da un membro a un altro, con tipo ed evidenza. **Diretto** se sta nel codice (chiamata, import). **Dedotto** se una regola di collegamento riconosce lo stesso dato o la stessa rotta in chi offre e in chi usa. **Dichiarato** se tocca un nodo senza codice. **Osservato** se lo vede il passo dinamico |
| Tipo di collegamento | `chiama`, `scrive`, `legge`, `attiva` (un'azione dell'utente attiva il suo handler) |
| Regola di collegamento | Come, in questo progetto, si riconosce chi offre e chi usa uno store o una rotta |
| Ingresso | Dove un flusso comincia: un controllo dell'interfaccia, una rotta o una chiamata, un comando, un messaggio, un evento hardware, un orario |
| Effetto | Dove un flusso arriva: un valore mostrato o restituito, un cambio di stato, un evento emesso, un comando a un dispositivo |
| Estremi | Gli ingressi e gli effetti di un flusso, con chi li avvia e chi li riceve |
| Percorso | La sequenza ordinata di collegamenti da un ingresso. È la prova di un flusso al livello codice |
| Flusso | Qualcosa che il sistema fa, con un nome nel linguaggio di chi lo usa o lo gestisce: i nodi che vi partecipano e le frecce fra loro. È uno solo, a qualunque livello lo si guardi |
| Variante | Un ramo dello stesso flusso, distinto dal suo ingresso o dalle sue condizioni |
| Tipo di flusso | Uno o più fra: funzionale (una cosa che il prodotto fa per chi lo usa), operativo (gira senza una persona: un orario, una coda, un avviso esterno), tecnico (cache, sincronizzazione, build, rilascio), dati (segue un dato: dove nasce, dove vive, chi ne tiene copia), hardware (passa da dispositivi fisici o dalla rete) |
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
| Granularità e significato | Ciò a cui un dato si riferisce (un ordine, una sua riga, un utente) e, in una frase, che cosa afferma |
| Perimetro, contesto, unità | I file che un lavoro copre; quelli che si consultano per giudicarli, senza giudicarli; quelli affidati a un revisore in un solo incarico |

## Stato al 18 novembre 2026

| Parte | Stato |
| --- | --- |
| Regole di collegamento, collegamenti dedotti, percorsi, unità, scheda di un percorso (sezioni 1, 9, 10, 12) | Applicato nel plugin: `flows.py`, `codebase_map_flows`. Nell'app le regole le scrive il motore scelto e i collegamenti dedotti sono relazioni del grafo |
| Registro dei servizi e dei progetti esterni (sezione 5) | Applicato. I numeri sono nella [tabella generata](../plugins/codebase-map-supporto.md) |
| Scheda del sistema, proposta, verifica, livelli (sezioni 2, 4, 6, 7, 8) | Applicato nel plugin: `system_brief.py`, `system_map.py`, `system_levels.py`, ruolo `system-mapper`. Nell'app no. L'agente propone ancora anche le frecce: candidati e frecce dalla macchina e il grado «da verificare» sono misurati senza modello, non applicati. Nel codice una coda sta ancora al livello funzioni |
| Grafo dell'app (sezione 4) | Mostra i livelli codice e infrastruttura: moduli o cartelle con le tessere del loro stack, e i servizi esterni riconosciuti con il marchio. Si apre sul posto fino alle classi e ai loro membri. Non ancora visto in un browser né misurato su un progetto grande |
| Estremi a ogni livello; attori, schermate e dispositivi nell'app | Proposta |
| Scoperta dai due capi, varianti, riesame dei resti (sezione 7) | Proposta |
| Esploratore e nomi vecchi | L'esploratore lavora su simboli, file e percorsi, con le viste «logica» e «fisica»; il parametro `level` dei percorsi dice ancora fisico, logico, dati, ux. `03-flows.md` è prosa scritta dai ruoli |

## 1. Collegamenti

**Applicato.**

1. Il modello legge il progetto una volta e scrive le regole di collegamento: «lo stato globale si legge con `<hook>`», «le chiamate al servizio passano da `<client>`», «la tabella `<nome>` si scrive solo da `<modulo>`». Una regola indica il costrutto come funzione del progetto, come chiamata così come è scritta (limitata a un insieme di cartelle) o come attributo del markup che lega un'azione al suo handler. Il formato è nel docstring di `flows.py`.
2. La macchina applica le regole a tutto il sorgente: elenca chi offre e chi usa, e li accoppia sull'identità che la regola precisa. Per uno store sono lo store e la chiave; per una rotta sono servizio, metodo e schema del percorso. Condividere lo store o il solo nome non basta: scrivere `store.theme` non collega a chi legge `store.cart`.
3. Ogni coppia è un collegamento dedotto con la sua evidenza. Nel grafo è una relazione fra i file dei due lati (`calls` per una rotta, `reads` da chi legge a chi scrive), riportata fra moduli o cartelle. Identità ambigue, accessi dinamici non risolti e accessi spaiati restano lacune dichiarate. Una rotta con più candidati è una relazione incerta, mai contata come certa.
4. Un nodo senza codice è un modulo `external`, dichiarato dal progetto o proposto con la sua evidenza. Il collegamento che lo raggiunge è dichiarato; se il modulo è solo proposto, resta `inferred`.
5. Le regole sono legate ai digest dei file che citano: se quei file cambiano, vanno rilette.
6. Nell'app il motore scelto scrive le regole, legge ciò che la macchina ha unito e ciò che è rimasto fuori, e le corregge al più tre volte. L'esito lo dà il servizio, mai le parole del modello.

## 2. Nodi

**Applicato nel plugin.**

1. Un nodo con codice è un gruppo di membri con un nome, un tipo e una posizione. I membri vengono dai candidati che il nodo comprende: chi propone non li scrive. Un file si divide per funzione solo quando la macchina vede le sue funzioni in candidati diversi.
2. Un nodo senza codice (attore, dispositivo, macchina o servizio su cui il sistema gira, servizio esterno, progetto esterno, parte non vista) non ha membri e cita l'evidenza che lo lega al progetto. Un attore cita gli ingressi che usa; una macchina cita la configurazione che la nomina; un progetto esterno cita la dipendenza dichiarata.
3. Lo stesso membro può stare in più nodi: un file che serve due schermate appartiene a entrambe.
4. Una dipendenza non è un nodo. Un progetto esterno che il registro conosce è una tessera del modulo che lo dichiara (sezione 4); diventa un nodo solo quando un flusso lo nomina. Le altre dipendenze restano contate.
5. La mappa del sistema sta accanto al grafo dei moduli e non ne cambia strati, conflitti e archi.

## 3. Flussi

**Tipi e aree applicati nel plugin; varianti ed estremi: proposta.**

1. Un flusso può attraversare più componenti, avere più ingressi e terminare con esiti diversi. Un modulo logico ha una responsabilità riconoscibile anche quando i suoi membri stanno in cartelle diverse.
2. Le varianti emergono dai fatti del progetto. Esempio su un sistema di ordini: «Annullamento ordini» ha le varianti «Su richiesta dell'utente», che parte da un controllo dell'interfaccia, e «Automatico per scadenza», che parte da un orario. Possono convergere sullo stesso servizio; se l'orario aggiorna direttamente lo stato, quel ramo resta distinto fino alla scrittura. Nomi e numero delle varianti sono dell'esempio, non delle istruzioni di chi propone.
3. Raggruppare due rami sotto un flusso non stabilisce un legame causale fra loro: un clic e un webhook possono appartenere allo stesso acquisto, ma collegarli chiede un riscontro, per esempio dove l'identificativo della transazione viene scritto e poi usato.
4. Chi avvia un flusso senza essere una persona è il servizio esterno che chiama o il dispositivo. Un orario o una coda è l'ingresso del servizio che esegue, non un attore.
5. Un dato che vive in più nodi (un listino, un elenco di permessi, un limite) è un flusso di tipo dati: le sue frecce dicono «stessa informazione». La macchina non verifica che i valori coincidano.
6. Le aree passate in rassegna: accesso e identità; funzioni principali; pagamenti e abbonamenti; dati dell'utente; integrazioni esterne; comunicazioni; amministrazione; esercizio. Chi propone dichiara ogni area presente o assente e aggiunge quelle che il progetto ha e l'elenco no.

## 4. Livelli e dettaglio

I controlli sono due e sono distinti: il livello sceglie quali nodi si guardano, il dettaglio quanto si apre.

**Livelli: applicato nel plugin. Nell'app: codice e infrastruttura.**

| Livello | Domanda | Nodi |
| --- | --- | --- |
| Persone | Chi agisce, attraverso quale controllo e con quale risultato visibile? | Attori e schermate |
| Funzioni | Quali responsabilità e servizi collaborano, e con quale ruolo? | Funzionalità, servizi, gateway, autenticazione, servizi esterni |
| Dati | Quale entità cambia, dove vive e chi ne legge il nuovo stato? | Entità e le loro rappresentazioni |
| Codice | Quali moduli, file e funzioni lo realizzano, e su che cosa poggiano? | Moduli, cartelle, file, classi e funzioni; su ogni modulo, le tessere dei progetti esterni su cui poggia |
| Infrastruttura | Dove gira, e quale dispositivo, coda o servizio di altri usa? | Dispositivi, container, servizi in esecuzione, database, code, reti, servizi esterni |

1. Un servizio esterno sta a due livelli, funzioni e infrastruttura: è un nodo a sé, accanto a ciò che lo usa. Un dispositivo sta a infrastruttura. Un progetto esterno sta a codice, sul modulo che lo dichiara: il modulo ne porta la tessera, con marchio e nome, chiuso o aperto; la riga che lo dichiara sta nell'ispettore. Lo stack e i nodi esterni si vedono sempre: nessuno dei due sta dietro un gruppo chiuso.
2. Un flusso esiste ai livelli in cui ha nodi: un flusso tecnico può non avere il livello persone.
3. Le corrispondenze dicono quali nodi di due livelli sono la stessa cosa. Quella verso il codice è l'appartenenza dei membri. Le altre si dichiarano citando la configurazione o il codice che le prova.
4. Due flussi si incrociano nei nodi che hanno in comune: un nodo elenca i flussi che lo attraversano, e un servizio condiviso resta un nodo solo anche se vi arrivano più rami.
5. I livelli si guardano uno alla volta, alcuni o tutti insieme. Insieme, ogni nodo mostra le sue corrispondenze agli altri livelli e dichiara i livelli a cui non esiste.
6. **Proposta.** Gli estremi di un flusso si vedono a ogni livello, con il proprio tipo: chi lo avvia e ciò su cui termina. Oggi un livello mostra solo i suoi tipi di nodo.

**Dettaglio: applicato nell'app per il livello codice; il resto è proposta.**

La discesa è la stessa a ogni livello: area, flusso, variante, nodi del livello scelto. Al livello codice prosegue: modulo, cartella, file, classi e funzioni del file, membri di una classe.

1. **L'apertura è locale.** Un gruppo si apre e si richiude sul posto lasciando compatto il resto del grafo, anche con più gruppi aperti a dettagli diversi; il grafo si ridispone a ogni passo. Richiudere riporta al nodo e alla selezione di prima.
2. **Si legge solo ciò che si apre.** Il primo livello non legge i simboli di nessun file; quelli di un file si leggono quando si apre quel file. Oltre una soglia di leggibilità i gruppi restano chiusi finché non si aprono.
3. **Un simbolo compare solo dentro il suo file aperto,** mai al primo livello. Resta un membro, non un nodo della mappa. Le righe stanno nell'ispettore e nei percorsi.
4. **Nessuna scomposizione inventata.** Fra modulo e file l'aggregatore è la cartella, che in molti linguaggi è il package.
5. **Le frecce riassunte conservano grado, evidenze e lacune.** Chiudere un gruppo riassume i collegamenti; aprirlo mostra i nodi e le frecce che sostengono il riassunto, con le frecce solo dichiarate e le lacune. La contrazione non promuove una freccia dichiarata a provata e non nasconde una lacuna.
6. **Cambiare livello conserva flusso e variante** e, dove esiste una corrispondenza, il nodo osservato. Dove le corrispondenze sono più d'una si mostrano tutte. Un cambio di livello o di dettaglio costa zero chiamate al modello.
7. **Si naviga nei due versi:** da una variante fino ai file e alle funzioni che la realizzano, oppure da un effetto a tutti gli ingressi che possono produrlo.
8. **Le relazioni valgono per ciò che provano.** Riferirsi alla stessa entità o avere una freccia «stessa informazione» non dimostra che due copie siano sincronizzate.

## 5. Registro dei servizi e dei progetti esterni

**Applicato.** File: `plugins/codebase-map/skills/map/data/service-registry.json`, costruito e rigenerato da `registry_build.py`.

1. Per ogni voce il registro tiene nome, tipo di nodo, sito, marchio e i segni da cui la si riconosce in un progetto: nomi dei pacchetti, host, prefissi delle variabili di configurazione, file.
2. La macchina confronta dipendenze dichiarate, host delle chiamate e nomi delle variabili con i segni. Una corrispondenza dichiarata diventa un nodo esterno proposto, con nome, tipo, sito e marchio, senza modello. Una voce solo menzionata non è un nodo.
3. Il registro nasce da cataloghi pubblici con licenza adatta ([ricognizione](../research/2026-11-12-external-service-catalogs.md)). Un modello propone solo ciò che manca; la macchina tiene solo ciò che verifica: che il sito risponda e che il pacchetto esista.
4. Il marchio è un file nel prodotto oppure si scarica al primo uso dalla fonte ufficiale, quando le sue condizioni non ne permettono la ridistribuzione. Origine e condizioni stanno in `REGISTRY-NOTICES.md`. Senza marchio il nodo prende l'icona generica del suo tipo.
5. Un servizio che nessuna fonte riconosce prende il nome del pacchetto o dell'host e resta marcato come non riconosciuto.
6. Ogni nodo esterno mostra nome e marchio in ogni grafo e a ogni livello.
7. La macchina legge anche i file che dichiarano l'esecuzione o l'architettura: docker-compose, Dockerfile, manifest di Kubernetes, configurazioni di hosting e di CI. Ciò che dichiarano diventa nodi proposti, con il file come evidenza.
8. Un altro strumento di riconoscimento entra solo se è pubblico, ha licenza adatta e nel benchmark riconosce qualcosa che le altre fonti non vedono. stack-analyser è stato tolto il 16 novembre 2026 con questo criterio.

## 6. Scheda del sistema

**Applicato nel plugin.**

1. La macchina compone, senza modello, un riassunto di ciò che i passi di analisi hanno prodotto: moduli e cartelle con il numero di file; ingressi, store e rotte; servizi esterni riconosciuti; file che configurano esecuzione e rilascio; collegamenti provati, dedotti e osservati, contati fra gruppi; titoli delle schede già scritte. Dichiara i passi non eseguiti.
2. La scheda porta i candidati. La macchina parte dagli ingressi e segue i collegamenti: un file raggiunto solo attraverso un ingresso sta nel candidato di quell'ingresso; un file che più ingressi raggiungono per strade diverse apre un candidato suo. Ogni chiave di store, ogni servizio esterno e ogni progetto esterno è un candidato. Un candidato prende l'identità dal suo primo file, così resta lo stesso fra due snapshot.
3. La scheda ha un tetto di dimensione, scritto nel README del benchmark. Oltre il tetto i candidati meno collegati si riassumono per cartella e restano interrogabili.
4. Per ogni candidato la scheda dà identificativi, segnale, eventuale gestore, effetti e fonte. Un riferimento condiviso conserva lo stesso identificativo in tutti i gruppi.

## 7. Scoperta dei flussi

**La proposta dell'agente su una scheda è applicata nel plugin. La scoperta dai due capi, le varianti e il riesame sono proposta.**

Quando l'utente chiede di analizzare un sistema, l'analisi si conclude con la scoperta dei flussi dell'intero sistema. Parte con l'analisi che l'utente chiede, mai da sola, e richiede le regole di collegamento. Lavora su tutto il sistema oppure su una sola area, quando una review parte da un intento e la mappa di quell'area manca o non regge più; una proposta per un'area aggiorna solo quell'area. Se il modello o una fonte necessaria mancano, il rapporto finale dice la parte rimasta scoperta e la causa.

1. **Leggere il contesto.** La scheda del sistema dà il quadro per interpretare un gruppo locale: lo stesso componente che scrive «scaduto» può gestire una prenotazione, una sessione o un ordine.
2. **Esplorare il grafo dai due capi.** In avanti dagli ingressi, all'indietro dagli effetti. La macchina riunisce i percorsi che si incontrano e conserva provenienza, direzione e punto d'arresto. Una funzione pubblica può essere ingresso del modulo e passo interno di un flusso più ampio.
3. **Far interpretare i candidati al modello.** Per ogni gruppo il modello dà nome, area, tipi, intento in una frase, esito, partecipanti, varianti e punti d'appoggio. Può unire più gruppi nello stesso flusso o separare processi che attraversano lo stesso servizio. Una libreria condivisa o due scritture sulla stessa tabella sono indizi deboli. Cita candidati e punti d'appoggio per identificativo: non scrive file, funzioni, righe né frecce. Dice il dato che passa su ogni freccia.
4. **Verificare e ricomporre.** La macchina costruisce ogni flusso dal grafo e gli dà i gradi (sezione 8).
5. **Riesaminare ciò che resta fuori.** Ogni estremo inventariato rimanda ad almeno un flusso, ha un'esclusione motivata o compare fra gli irrisolti. Il rapporto distingue gli irrisolti esaminati da quelli rimasti da esaminare per budget o per analisi mancante, e pubblica conteggi e riferimenti per gruppo.

Per contenere errori e token: i gruppi li costruisce la macchina; il modello restituisce decisioni e riferimenti, la macchina conserva i percorsi e calcola le viste. Su un'ambiguità concreta il modello legge la scheda aggiornata del gestore o del punto di scrittura, e apre l'estratto di codice solo se la scheda manca o è superata. Il budget è cumulativo per run; una ripresa riusa identità ed evidenze ancora valide. Il prompt si mette a punto sul benchmark, con il modello meno costoso che supera le soglie.

## 8. Verifica

**Applicato nel plugin, tranne il grado «da verificare».**

La macchina non giudica ciò che il modello sostiene: lo prova quando il grafo lo mostra e dice quanto è provato. Rifiuta solo ciò che si riferisce a cose che non esistono, con il motivo, e l'agente corregge una volta.

1. **Nodo:** nome unico e tipo dell'elenco; comprende candidati che esistono. Un nodo senza codice viene da un candidato esterno o da un ingresso; un nodo non visto dichiara dove sta.
2. **Flusso e frecce:** la macchina prende ciò che sta su un percorso del grafo da un punto di partenza a un punto di arrivo, seguendo chiamate, attivazioni, scritture e letture, senza limite di passi. Fra due nodi la freccia è l'insieme dei collegamenti dai membri del primo ai membri del secondo, che sono la sua prova. Quando tocca un'entità la freccia è legata alla rappresentazione che la prova nomina: entrare da una rappresentazione e uscire da un'altra è una lacuna, non una freccia. Fra un nodo senza codice e uno con codice la freccia è dichiarata, con il punto che li lega. Una partenza che non raggiunge nessun arrivo è un buco: la macchina dice dove il grafo si ferma, mostra l'ultimo punto noto, e la freccia attesa resta «da verificare».
3. **Corrispondenza:** quella verso il codice è verificata sui membri. Le altre sono dichiarate, con il punto citato che esiste.
4. **Copertura:** quanti ingressi, store e rotte stanno in almeno un flusso, e quanti candidati in almeno un nodo. Il resto è elencato, non nascosto.
5. **Identità e conferma:** ogni nodo e ogni flusso ha un'identità che non dipende dal nome. Un nodo nuovo è rifiutato come doppione quando uno esistente dello stesso tipo ha gli stessi candidati, li contiene o ne è contenuto. Una proposta resta `inferred` finché il progetto non la conferma. Un nome confermato cambia solo con una rinomina esplicita, e una proposta non toglie ciò che è confermato.
6. **Freschezza:** nodi, frecce e corrispondenze sono legati ai digest dei file da cui dipendono. Quando un file cambia, la macchina ricalcola senza modello candidati e frecce, e torna all'agente solo un nodo i cui candidati cambiano. Ciò che è solo dichiarato torna all'agente quando cambia il file che cita.

## 9. Etichette e scheda di un percorso

**Applicato.**

1. Su richiesta il modello legge un collegamento `scrive` o `legge` e ne scrive granularità e significato, legati ai digest dei due simboli. Senza etichetta il campo resta vuoto: non si deduce. Servono a vedere quando chi scrive e chi legge lo stesso store intendono granularità diverse ([caso misurato](../../benchmarks/phazly-flow/README.md)).
2. Per «dove va questo dato» il modello dà i punti di partenza, la macchina traccia i collegamenti, il modello riceve l'elenco dei passaggi e apre il sorgente solo dove il dato si scrive, si legge o si trasforma.
3. La scheda di un percorso dice nome, tipo, rami e che cosa accade al dato a ogni tappa. Ogni frase cita un passaggio dell'elenco: una riga che non ne cita uno rifiuta la scheda. Si rilegge solo se un file del percorso cambia.

## 10. Interrogazione

**Applicato nel plugin.** `codebase_map_flows` risponde a una domanda per volta:

- `rules` registra le regole di collegamento; senza regole la risposta è il loro formato.
- `start` con `direction`: `from` un ingresso (che cosa deve reagire), `to` un effetto o uno store (chi lo scrive e che cosa significa), `through` un nodo (quali flussi lo attraversano). La risposta elenca i collegamenti con granularità, significato, freschezza, lacune e ciò che resta da esplorare, e distingue un flusso incompleto da uno completo diviso in più unità.
- `card` registra la scheda di un percorso.
- `brief` dà la scheda del sistema; `map` registra una proposta e la riporta; `about` risponde per un'area, un flusso o un nodo, e con `levels` mostra un flusso a quei livelli.

**Proposta:** `03-flows.md` si genera dalla mappa del sistema; il grafo dell'app, l'esploratore, MCP e review leggono lo stesso risultato.

## 11. Perimetro di una review

**Unità applicate nel plugin; dall'intento ai controlli: proposta, da misurare prima di adottarla ([fase 3](2026-11-09-flows-in-review.md)).**

1. Il modello legge l'intento e lo riporta sulla mappa: quali aree, flussi e nodi tocca, e a quali livelli. Lo dichiara in `00-scope.md`; chiede solo se due letture cambiano correttezza o costo. «Review dell'annullamento ordini» prende il flusso con tutte le varianti, anche quelle automatiche; «review dell'annullamento automatico» prende quel ramo e la logica condivisa che ne decide l'esito; un componente nominato porta al nodo e ai flussi che lo attraversano.
2. La mappa restituisce, per ogni ramo: i file e i simboli da revisionare con il motivo; i riferimenti da consultare come contesto; le frecce con i dati che passano; i servizi esterni; i dati tenuti in più posti, da confrontare; le lacune che limitano il giudizio. Un componente condiviso compare una volta, con i rami interessati. Il brief dei revisori elenca queste cose, non solo i file.
3. Senza mappa, l'unità si forma da ciò che la richiesta nomina:

   | La richiesta nomina | Punti di partenza | Come si forma l'unità |
   | --- | --- | --- |
   | Una cartella o un modulo | I suoi file | Per percorso del file |
   | Una funzione | La funzione | Con chi la chiama e chi chiama |
   | Un componente dell'interfaccia | Il componente | Dal fatto mostrato a chi lo scrive; dalle azioni a chi reagisce |
   | Una funzionalità | I suoi ingressi | Seguendo i collegamenti, anche fra strati |
   | Un flusso di dati | Lo store o il fatto mostrato | Chi scrive e chi legge, anche fra strati |
   | Un aspetto (sicurezza, prestazioni, concorrenza) | L'aspetto sceglie i revisori, non i file | Dagli ingressi se l'aspetto segue il dato, altrimenti per percorso del file |

4. La macchina segue `chiama`, `scrive`, `legge` e `attiva` dai punti di partenza, senza limite di salti e ciascuno una volta sola. Si ferma quando il collegamento esce dal confine di lettura, quando un limite del budget si esaurisce o quando il collegamento non si risolve. Ciò che non ha seguito resta elencato, e il flusso è dichiarato incompleto. Come contesto aggiunge solo ciò che dista un `chiama` dal flusso.
5. Divide il perimetro in unità entro un limite di byte. Chi scrive e chi legge lo stesso dato stanno nella stessa unità; se superano il limite il taglio è registrato. Un file condiviso da due flussi compare in entrambe le unità. Un file che molti flussi toccano è membro di poche unità, in numero fissato, e contesto nelle altre. I file che nessun flusso tocca vengono dopo, per percorso. Ogni file del perimetro è assegnato almeno una volta, e i collegamenti fra unità restano consultabili.

## Limiti

- Nomi, tipi e tagli sono proposte del modello, e per questo il progetto conferma. Candidati e frecce sono della macchina, che vede solo ciò che il grafo contiene.
- L'analisi è statica: un flusso dice che cosa il codice rende possibile, non che cosa avviene in esecuzione. Il passo dinamico aggiunge i collegamenti osservati nei test.
- Dove il grafo ha un buco (un valore passato attraverso un contesto, un componente reso senza una chiamata, una chiave scritta in una forma che le regole non leggono) la freccia resta da verificare e il buco va dichiarato, mai taciuto. Una freccia provata dice che un collegamento esiste, non che il flusso sia completo.
- Granularità e significato sono affermazioni del modello, da verificare sul sorgente.
- Il livello infrastruttura poggia su ciò che configurazione e codice dichiarano: quello che esiste solo in una console esterna non si vede. Ciò che sta fuori dallo snapshot entra solo se dichiarato.
- Dove il linguaggio aggrega con una dichiarazione e non con una cartella (un namespace, un modulo annidato), il grafo mostra la cartella.
- Dove la mappa non analizza un linguaggio, la macchina non deduce collegamenti.

## Prova

Le soglie stanno nel README di ogni benchmark, scritte prima di ogni misura. Le prove girano su Modal.

**[`benchmarks/flow-model`](../../benchmarks/flow-model/README.md)**, senza modello tranne la 4; casi reali in [`polar-flow`](../../benchmarks/polar-flow/README.md), [`tududi-flow`](../../benchmarks/tududi-flow/README.md) e [`phazly-flow`](../../benchmarks/phazly-flow/README.md). Misure 2, 3 e 5 sulla fixture; 1 e 4 fatte su phazly.

1. **File di un difetto noto:** a parità di perimetro e di limite, in quanti incarichi `pack()` mette i file dei difetti attesi e in quante unità li mette la proposta.
2. **Fixture** su due strati, con uno store condiviso fra due funzionalità, una rotta, una violazione fra chi scrive e chi legge e una variante lecita simile: collegamenti trovati contro attesi, collegamenti falsi e lacune dichiarate.
3. **Caso reale fra strati:** da un fatto mostrato il flusso arriva allo store che lo contiene, attraverso la rotta dichiarata dal caso.
4. **Etichette:** granularità e significato su un campione, contro una lettura manuale; costo per collegamento.
5. **Simboli e funzionalità:** una catena di almeno tre chiamate fra file diversi, un ciclo, una funzionalità con più ingressi; i file entrati in un flusso senza appartenere agli attesi; tutti i file assegnati anche con un limite basso.

**[`benchmarks/system-map`](../../benchmarks/system-map/README.md).** Misure 2, 3 e 4 raggiunte; 1, 5 e 6 no; il modello dell'agente non è fissato.

1. **Riproduzione:** per un'area di un caso reale, la mappa proposta contro una fatta a mano che l'agente non vede: nodi confrontati per membri, flussi, frecce per grado.
2. **Secondo progetto:** lo stesso prompt su un altro caso: frecce provate, copertura, lettura di un campione di nomi.
3. **Livelli:** per un flusso del riferimento, a ogni livello i nodi mostrati sono dei tipi di quel livello e le corrispondenze citano punti che esistono.
4. **Costo:** token e costo per mappa e per modello; quante volte l'agente apre il sorgente.
5. **Stabilità:** due esecuzioni sullo stesso snapshot danno gli stessi nodi, confrontati per candidati.
6. **Registro:** quanti servizi e progetti esterni usati dal progetto vengono riconosciuti, e quanti riconoscimenti sono sbagliati.
7. **Dall'intento ai controlli:** per un intento in linguaggio comune, le cose da controllare che la mappa restituisce contro l'elenco scritto prima dal proprietario.
8. **Review:** lo stesso intento con perimetro e brief dalla mappa, contro la review di oggi. È a pagamento: si chiede prima.

**Scoperta cieca sull'intero sistema.** È la prova decisiva della sezione 7. L'atteso è accessibile solo al valutatore, che verifica identità dei processi e dei rami, falsi raggruppamenti, copertura, motivazioni del perimetro e costo complessivo. Il protocollo la distingue dal controllo con estremi noti. Nel benchmark storico di phazly l'agente ha ritrovato 0 dei 3 flussi dell'area pagamenti; con partenze e arrivi indicati a mano il grafo ha aggiunto 0 file estranei, lasciando fuori alcuni tratti attesi. [Parametri, risultati storici e misure da eseguire](../../benchmarks/system-map/README.md#confronto-proposto-per-i-flussi-multilivello).

**Grafo dell'app.** Un test conta le letture: il primo livello non legge nulla che cresca con i simboli dei file. Il 18 novembre, prima del caricamento per livelli, il grafo di un progetto di 2.408 file rispondeva in 245 secondi; la misura dopo va fatta su Modal.

## Ordine di lavoro

1. Grafo dell'app: vederlo in un browser e misurarlo su un progetto grande, su Modal.
2. Mappa del sistema nell'app: scheda, proposta con il motore dell'app, verifica, livelli; estremi a ogni livello.
3. Candidati e frecce dalla macchina, grado «da verificare»; misure da 1 a 5 di nuovo.
4. Scoperta dai due capi, varianti, riesame dei resti; scoperta cieca.
5. Esploratore sulla mappa del sistema; i nomi vecchi dei livelli escono dal codice.
6. Review: dall'intento ai controlli, poi i revisori; misure 7 e 8.

**Da decidere:** dove il progetto registra ciò che conferma; il tetto della scheda del sistema; come si raggruppano i candidati quando sono troppi per la scheda; quali buchi del grafo si chiudono con una regola statica e quali con il passo dinamico; il limite di un'unità e se le unità estendono `scope_planner.py`; come mostrare un aggregatore dichiarato dal linguaggio quando non è una cartella.
