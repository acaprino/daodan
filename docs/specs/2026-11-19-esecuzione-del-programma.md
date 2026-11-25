# Registro dell'esecuzione: come funziona il programma, visto girare

> Ciò che di questo documento resta da fare è condensato in [Il lavoro che resta, in ondate](2026-11-25-lavoro-residuo-a-ondate.md), ondata 7: lo stato di una voce si aggiorna là.

**Stato:** proposta, 19 novembre 2026. Nulla è applicato. Allineata il 20 novembre alle decisioni del proprietario di quel giorno (sezione 4); ogni scelta rimanda al suo motivo, in «Motivi delle scelte». È la «spec a parte» delle review dinamiche che la [spec del passo dinamico](2026-11-12-passo-dinamico.md) annuncia nella sezione 6, e ne riusa container, registri e fatti osservati.

Daodan deve saper rispondere a due domande che oggi restano aperte: «che cosa attraversa davvero un'esecuzione: quali funzioni, classi, file, processi, query e connessioni, e in che ordine?» e «la lacuna che un revisore ha dichiarato si chiude guardando il programma girare?».

## Parole

- **Catena:** la sequenza ordinata delle funzioni del progetto attive in un punto dell'esecuzione, dalla radice al sito.
- **Albero delle chiamate:** tutte le catene distinte di una corsa, ciascuna una volta sola, con il numero di volte che è stata percorsa.
- **Radice:** ciò che ha fatto partire una catena: un test, un ingresso, l'avvio di un processo.
- **Frontiera:** una chiamata che esce dal processo verso il sistema: file letto o scritto, database, connessione di rete, processo avviato, variabile d'ambiente letta.
- **Conto di sistema:** ciò che il container ha visto fare a ogni processo, qualunque libreria lo abbia chiesto.
- **Avvio:** il comando con cui il progetto dichiara di far partire il programma. Si distingue dal comando dei test.
- **Ingresso:** una rotta del grafo dei flussi (`service`, `method`, `path`), come la tiene `flows.py`. Qui la parola vale solo per le rotte; nella [spec dei flussi](2026-11-18-flussi-e-mappa-del-sistema.md) un ingresso è anche un controllo, un orario, un messaggio e gli altri tipi di Parole.
- **Scambio:** la richiesta mandata a un ingresso e la risposta ricevuta: stato, intestazioni, dimensione del corpo.

## Comportamento attuale

- I registri scrivono siti: per ogni punto di chiamata, l'insieme dei chiamati (`dynamic/__init__.py`, `python_record.py`, `javascript_record.js`). Non scrivono l'ordine, la catena né quante volte. Da quei siti si ricava chi chiama chi, non come si arriva a una funzione.
- Un chiamato fuori dal progetto è scritto con il suo pacchetto e la versione. Che cosa ha chiesto (quale query, quale host, quale file) non è scritto.
- I registri partono già in ogni processo e thread che la corsa avvia; ogni processo scrive il suo file, senza dire chi lo ha avviato.
- Il passo dinamico esegue solo il comando dei test. Il programma parte solo come `webServer` di un test Playwright (`dynamic/javascript.py`). La pre-mappa non tiene un comando di avvio del progetto.
- Un revisore che non può stabilire un fatto dal codice lo dichiara lacuna (`reviewer-common.md`). I ruoli di sicurezza chiedono fatti che solo un'esecuzione dà: la risposta effettiva (`browser-security-auditor`), ciò che arriva al client in caso di errore (`secret-exposure-auditor`), il percorso fino al sink. La classe `reproduced` esiste (`review-quality-gates/SKILL.md`), ma la riproduzione gira sull'host.

## Proposta

### 1. Albero delle chiamate

Motivo 1.

- Ogni registro esatto tiene, accanto ai siti, l'albero delle chiamate della corsa. Un nodo è `{parent, site, callee, count}`: il nodo da cui si arriva, il sito della chiamata, il chiamato come lo scrive già un sito, le volte percorse.
- Una catena si scrive una volta: la stessa chiamata dalla stessa catena aumenta `count`, non aggiunge nodi. Una funzione già presente nella catena non la allunga (ricorsione): il nodo esistente conta.
- Entra nell'albero ogni chiamata fra funzioni del progetto, e ogni chiamata dal progetto verso l'esterno come foglia. Ciò che l'esterno chiama al suo interno non entra.
- Vale per ogni corsa del registro, quindi già per i test di oggi: la radice è il test. La versione del registro cambia, e con lei il `resolver` delle righe osservate.
- I nodi si uniscono allo snapshot per posizione, come i siti (spec del passo dinamico, sezione 5): ogni nodo ha così funzione, classe e file dello snapshot.
- Un processo avviato dalla corsa ha il suo albero, con il comando e il nodo che lo ha avviato.

### 2. Frontiere

Motivo 2.

- A una frontiera il nodo porta anche `access` e `resource`. `access` è `legge`, `scrive`, `connette` o `avvia`, le parole dei collegamenti dei flussi dove esistono. `resource` identifica la cosa raggiunta: il percorso del file, il testo della query senza i valori dei parametri, `host:porta`, il comando del processo, il nome della variabile d'ambiente.
- Le funzioni di frontiera sono una tabella chiusa per linguaggio, come i comandi ammessi di `container.py`. Una frontiera fuori dalla tabella resta una foglia esterna con il suo pacchetto, senza `resource`.
- **Conto di sistema.** Accanto all'albero, per ogni processo della corsa: ogni file aperto, in lettura o in scrittura, ogni file creato, rinominato o cancellato, ogni connessione tentata, ogni processo avviato. Viene dalle chiamate di sistema che il container vede, quindi non dipende dal linguaggio né dalla tabella. Non ha catena: dice che cosa è successo, non da dove.
- Ciò che il conto vede e nessuna frontiera dell'albero spiega è una lacuna `frontier_not_in_table` con la risorsa e il processo: la tabella si corregge su quella, mai a intuito.
- Nessun valore di parametro, contenuto scritto, corpo o risposta si tiene. I valori dei file `.env` tracciati sono mascherati come nel registro della corsa (`container.masker`).

### 3. Avvio dichiarato

Motivo 3.

- La faccetta `starts` della pre-mappa, con `builds` e la scelta dell'esecutore, è definita in [Interfacce del progetto](2026-11-19-interfacce-del-progetto.md), sezione 5. Si legge solo da ciò che il progetto dichiara, mai da una convenzione di Daodan, e Daodan non modifica il comando dichiarato.
- Un progetto senza avvio dichiarato è una lacuna `no_start_command`. Una porta che il comando non dichiara e che il processo non stampa all'avvio è una lacuna `port_not_declared` ([interfacce del progetto](2026-11-19-interfacce-del-progetto.md), 7.3): nessuna scansione.

### 4. Corsa del programma

Motivo 4.

- Una corsa in più dell'osservatore, nello stesso container e con le regole della spec del passo dinamico (sezione 4): preparazione con i soli registri, esecuzione senza rete, servizi della CI accanto (`container.beside`). Parte dal container che la preparazione unica dell'analisi ha lasciato, senza ripristinare di nuovo le dipendenze ([pipeline di analisi](2026-11-15-pipeline-di-analisi.md), «Preparazione»; motivo 6).
- Daodan aspetta la porta come aspetta quella di un servizio; un programma che non risponde entro il limite è una lacuna `not_ready` con la coda del suo log.
- Un richiedente di Daodan, nello stesso pod, manda una richiesta alla volta a ogni ingresso `GET` senza parametri. Ogni altro ingresso è una lacuna `entry_not_exercised` con la causa (parametro, corpo, metodo che scrive), finché il progetto non dichiara un esempio (sezione «Da decidere»). Dove c'è un'interfaccia, rotte, collegamenti e controlli raggiungibili li prova l'esplorazione della fonte osservata ([interfacce del progetto](2026-11-19-interfacce-del-progetto.md), 7.4; motivo 7); questo richiedente resta per gli ingressi senza pagina.
- La radice di una catena che parte dal gestore della richiesta è l'ingresso. Una chiamata che gira fra l'invio e la fine della risposta per un'altra causa (un timer, un lavoro partito prima) resta senza radice: la finestra di tempo da sola non la attribuisce (revisione esterna del 20 novembre). Di ogni ingresso esercitato si tiene lo scambio.
- Alla fine il programma riceve il segnale su cui il registro scrive, come per i test oltre il limite.

### 5. Dove sta e chi lo legge

Motivo 5.

- L'albero sta nello store dello snapshot, accanto agli archi osservati, e dura quanto loro. Gli archi osservati di oggi restano come sono: l'albero non li sostituisce.
- Due letture: per simbolo (le catene che arrivano lì, con le loro radici) e per radice (l'albero sotto un test o un ingresso, con le sue frontiere).
- **Grafo e flussi:** le frontiere con `resource` danno ai flussi gli accessi osservati a store e servizi; le radici dicono quale ingresso arriva a quale funzione. Una frontiera `legge` o `scrive` su un file è un collegamento osservato verso il nodo `filesystem` proposto nella spec del 18 novembre.
- **Review:** il revisore riceve le catene dei simboli nel suo perimetro. Un fatto letto dall'albero ha `evidence_class` `measured`, con comando, radice e registro; `reproduced` resta per un esito diverso su base e candidato, come lo definisce `review-quality-gates`. Nessuna classe nuova.
- **Riproduzione:** la riproduzione di un finding e il test di un'indagine girano in questo container, non più sull'host (spec del passo dinamico, sezione 6). Oggi `review-quality-gates` e `investigation-method` la concedono con un workspace e un runner, senza chiedere il container: si correggono per primi (piano del 20 novembre, task 0).

Lacune che l'albero chiude, a titolo di esempio:

| Ruolo | Lacuna oggi | Fatto osservato |
|---|---|---|
| `authorization-auditor` | il controllo sta sul percorso fino all'accesso ai dati? | catene che arrivano alla frontiera del database, per radice |
| `input-validation-auditor` | l'ingresso raggiunge davvero il sink? | catena dall'ingresso al sito |
| `sql-efficiency-auditor` | quante query per una richiesta | `count` delle frontiere del database sotto la radice |
| `untrusted-resource-auditor` | dove scrive davvero questo ingresso? | frontiere `scrive` sotto la radice, con il percorso |
| `storage-durability-auditor` | la sostituzione passa da un file temporaneo e una rinomina? | creazioni e rinomine del conto di sistema |
| `browser-security-auditor` | politica effettiva della risposta | intestazioni dello scambio |

## Limiti

- Una corsa prova che una catena esiste, non che sia l'unica: una catena senza il controllo è un finding, una catena con il controllo non assolve le altre radici.
- L'albero non tiene l'ordine fra catene sorelle né i valori: dice per dove si passa, non con quali dati.
- `access` non ha la chiusura di una risorsa: «la connessione aperta viene chiusa?» non si legge dall'albero.
- Dove l'esecuzione riprende dopo un'attesa asincrona, la catena continua solo se il linguaggio dà il contesto; altrimenti riparte dalla funzione ripresa, e la corsa conta quante volte.
- I linguaggi osservati con Callgrind (Rust, C, C++) danno coppie, non catene: per loro l'albero è una lacuna finché un registro non le dà.
- Senza rete le API esterne non rispondono: la frontiera si vede, la risposta no.
- Il conto di sistema chiede al motore di tracciare le chiamate di sistema del container. Dove il motore non lo concede (il gVisor di Modal ha già fermato Valgrind) il conto è una lacuna, e resta la sola tabella.
- Ciò che sta dopo il programma (proxy, CDN, edge) non gira: le intestazioni sono quelle del programma.
- Con un database vuoto molte rotte rispondono vuoto. Gli ingressi dietro login non si raggiungono senza una credenziale che il progetto dichiara per le prove.
- I tempi misurati nel container non sono quelli degli utenti: nessun tempo entra nei fatti di questa spec.

## Prova

Parametri e soglie nei README dei benchmark, scritti prima di ogni misura.

1. **Costo del registro**, in [`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md): sugli stessi casi, durata e RAM di picco dei test con e senza l'albero; nodi dell'albero su siti osservati.
2. **Fedeltà:** su un programma di prova scritto per questo, l'albero letto è quello atteso, catena per catena, ricorsione, thread e processi figli compresi; ogni file che il programma scrive, ogni connessione e ogni processo che avvia stanno nel conto di sistema, e quelli della tabella anche nell'albero. Una richiesta insieme a un lavoro concorrente: le chiamate del lavoro restano senza radice.
3. **Grafo:** buchi chiusi dalla corsa del programma oltre quelli chiusi dai test; ingressi esercitati su ingressi del grafo.
4. **Review:** su una review già fatta con lacune dichiarate dai ruoli di sicurezza, lacune che l'albero chiude e finding confermati o smentiti.
5. **Isolamento:** il richiedente non raggiunge nulla fuori dal pod; sull'host non compare nessun file.

## Motivi delle scelte

Una voce per scelta; la regola la cita con «motivo n». Nessuna è ancora misurata: le prove sono quelle della sezione «Prova».

1. **L'albero delle chiamate** (1). Perché: i registri scrivono siti, non l'ordine né la catena, e da un sito si ricava chi chiama chi, non come si arriva a una funzione («Comportamento attuale»). Il registro esatto di oggi costa già da 6 a 10 volte il tempo della suite (534 test in 16 s invece di 2,5 s: [`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md), «Verdetto»), per questo il costo dell'albero è la prova 1. Scartato: tenere i valori e l'ordine fra catene sorelle (vedi «Limiti»).
2. **Le frontiere e il conto di sistema** (2). Perché: di un chiamato fuori dal progetto si scrive il pacchetto, non ciò che ha chiesto, e i ruoli di sicurezza chiedono proprio quello. La tabella delle frontiere è chiusa e si corregge solo su una lacuna `frontier_not_in_table`, mai a intuito. Scartato: tenere i valori dei parametri e i contenuti.
3. **L'avvio solo dichiarato** (3). Perché: la pre-mappa non tiene un comando di avvio, e un comando o una porta presunti avvierebbero il programma sbagliato. Scartato: convenzioni di Daodan e la scansione delle porte.
4. **La corsa del programma nel container** (4). Perché: oggi il programma parte solo come `webServer` di un test Playwright, e la riproduzione di un finding gira sull'host, contro la regola di `AGENTS.md`. Scartato: un richiedente che manda corpi e parametri inventati.
5. **L'albero accanto agli archi osservati** (5). Perché: due letture, per simbolo e per radice, servono sia ai flussi sia alla review, e le classi `measured` e `reproduced` esistono già. Scartato: una classe di evidenza nuova.
6. **Una preparazione per analisi** (4). Deciso dal proprietario il 20 novembre 2026, contro la raccomandazione di rimandarlo: [flussi e mappa](2026-11-18-flussi-e-mappa-del-sistema.md), motivo 15.
7. **L'esplorazione della fonte osservata** (4). Deciso dal proprietario il 20 novembre 2026, diverso dalla raccomandazione di aprire solo le pagine dichiarate: [interfacce del progetto](2026-11-19-interfacce-del-progetto.md), motivo 11.

## Da decidere

- L'ordine: l'albero sui test di oggi prima (sezioni 1, 2 e 5, senza avvio), poi la corsa del programma (sezioni 3 e 4). È l'ordine consigliato: dà catene vere subito, senza una faccetta nuova.
- Il primo linguaggio: Python o JavaScript, che hanno un registro di Daodan.
- La prima tabella delle frontiere: solo la libreria standard (file, socket, processi, ambiente, SQLite) o anche i driver che il progetto dichiara fra le dipendenze.
- Lo strumento del conto di sistema e ciò che chiede al motore: un tracciatore delle chiamate di sistema nel container, oppure, per le sole scritture, il confronto della copia usa e getta prima e dopo la corsa, che non chiede nulla.
- Da dove vengono gli esempi per gli ingressi con parametri o corpo: esempi OpenAPI, file `.http`, richieste dei test del progetto.
- Dati e credenziali di prova. **Deciso dal proprietario il 25 novembre 2026: solo quelli che la CI del progetto già prepara**, nessun seme dichiarato a Daodan. Ciò che sta dietro un accesso che la CI non prepara resta una lacuna con la causa.
- Un tetto ai nodi dell'albero per corsa, e che cosa si dichiara quando si raggiunge. Va fissato prima della misura 1.

**Per modificare questa spec:** un requisito in più solo per un'esigenza obbligatoria o un esito sbagliato riproducibile.
