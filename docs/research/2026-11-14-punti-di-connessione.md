# Punti di connessione: guida ai tipi

**Natura del documento:** guida del 14 novembre 2026, non esaustiva e non una spec. Elenca i modi in cui due parti di un sistema senza un simbolo in comune si collegano, con la chiave da leggere e un esempio per lato. La sezione «Stato» dice cosa il prodotto legge oggi; il catalogo è materiale per le regole di collegamento, non comportamento. Misure: [`connection-points`](../../benchmarks/connection-points/README.md), [`phazly-flow`](../../benchmarks/phazly-flow/README.md).

## Regola

- Un punto di connessione è un nodo con un tipo e una chiave. I siti del codice vi si attaccano con un ruolo; due ruoli complementari sulla stessa chiave si uniscono.
- I ruoli sono tre coppie, e l'elenco è chiuso: **chiama / offre** (uno si rivolge a un indirizzo, l'altro risponde), **scrive / legge** (uno lascia un dato, l'altro lo trova dopo), **emette / ascolta** (uno manda a un nome, ascoltano in zero o in molti).
- I tipi sono aperti: un tipo è un nome, una coppia e la forma della sua chiave.
- La chiave è la risorsa più il nome (`mongo` + `orders`, `POST` + `/api/tasks/{}`). Conta solo un letterale o una costante: una chiave calcolata è una lacuna, una chiave a schema che incontra più candidati è un collegamento incerto.

## Stato

- `flows.py` unisce le rotte (`rotta` / `offre`) per servizio, metodo e schema del percorso (tipo `REST`: parametri come `{}`, query e URL di base fuori dalla chiave; più candidati sono una lacuna con i candidati), e gli store (`scrive` / `legge`) per store e chiave uguali. Uno store è «dove un dato vive: stato globale, tabella o collezione, file, cache» ([fase 2](../specs/2026-11-09-flow-model.md)), e una regola di store può dichiararlo `coda`.
- `snapshot.py` unisce `invoke` di Tauri al suo `#[tauri::command]`.
- Il benchmark `connection-points` unisce le rotte HTTP per schema, con collegamenti incerti e lati singoli; il prodotto ne riprende il confronto per segmenti, provato sulla fixture `pets`.
- Prova del 14 novembre 2026, due file Python e tre regole di store: `basic_publish("orders", "order.created", …)` e `basic_consume("order.created", on_order)` si uniscono in `store:amqp/order.created`. Due limiti:
  - chi legge è la funzione che registra il consumatore, non `on_order`: una regola `legge` non ha il campo `handler`;
  - `open(p, "w")` e `open(p)` non si distinguono: una regola riconosce la chiamata, non il valore di un altro argomento.
- Nessun tipo oltre rotte, store di stato e di database e comandi Tauri è misurato su un caso reale.

## Catalogo

### Chiama / offre

| Tipo | Chiave | Chi chiama ↔ chi offre | Attenzione |
| --- | --- | --- | --- |
| REST | metodo e schema del percorso | `fetch('/api/tasks/' + id)` ↔ `router.get('/tasks/:id', h)` | il prefisso di mount e l'URL di base stanno altrove; un handler sotto due versioni |
| GraphQL | tipo di operazione e campo | `query { order(id: 1) }` ↔ resolver `Query.order` | l'endpoint HTTP è uno solo: la rotta non distingue nulla |
| gRPC, RPC | servizio e metodo | `stub.GetOrder(req)` ↔ `OrderService.GetOrder` | il client è generato: l'indice lo vede come simbolo, il servizio no |
| Comando IPC | nome del comando o del canale | `invoke('save')` ↔ `#[tauri::command] fn save`; `ipcRenderer.invoke('x')` ↔ `ipcMain.handle('x')` | |
| Sottoprocesso, CLI | eseguibile e sottocomando | `subprocess.run(['tool', 'sync'])` ↔ punto d'ingresso `tool sync` | l'eseguibile può essere di altri |
| Funzione o job remoto | nome della funzione | `lambda.invoke(FunctionName='resize')` ↔ handler nel manifest di deploy | il nome sta nella configurazione |
| Navigazione, deep link | schema dell'URL | `<a href="/checkout">`, `app://plan/{}` ↔ rotta del router, filtro di intent | unisce sito e app; non c'è risposta |
| Webhook | metodo e percorso | servizio esterno ↔ `POST /webhooks/payments` | chi chiama non ha codice: freccia dichiarata; l'URL è registrato in una console esterna |
| Stored procedure | database e nome | `CALL close_month()` ↔ `CREATE PROCEDURE close_month` | |

### Scrive / legge

| Tipo | Chiave | Chi scrive ↔ chi legge | Attenzione |
| --- | --- | --- | --- |
| Tabella, collezione | database e nome | `INSERT INTO orders` ↔ `SELECT … FROM orders` | con un ORM il nome sta nel modello; lo stesso nome in due database |
| Stato dell'app | store e campo | `set({ plan })` ↔ `useStore(s => s.plan)` | |
| Cache, chiave-valore | istanza e chiave o prefisso | `redis.set('user:' + id, v)` ↔ `redis.get('user:' + id)` | chiavi quasi sempre composte: schema; il dato scade |
| File | percorso normalizzato | `open('out/report.csv', 'w')` ↔ `read_csv('out/report.csv')` | percorsi relativi alla cartella di lavoro; stessa macchina o stesso volume |
| Object storage | bucket e chiave o prefisso | `put_object(Bucket=b, Key=k)` ↔ `get_object(Bucket=b, Key=k)` | |
| Storage del browser, cookie | origine e nome | `localStorage.setItem('token', t)` ↔ `getItem('token')`; `Set-Cookie: sid` ↔ `req.cookies.sid` | un cookie passa fra client e server |
| Configurazione, variabili, flag | nome | `API_URL=` in `.env` o compose ↔ `process.env.API_URL` | chi scrive è un file, non codice; dice anche quale risorsa sta dietro le altre chiavi |
| Contesto della richiesta | nome del campo | `req.user = u` ↔ `req.user` | dentro lo stesso processo, fra middleware e handler |

### Emette / ascolta

| Tipo | Chiave | Chi emette ↔ chi ascolta | Attenzione |
| --- | --- | --- | --- |
| Coda AMQP | broker, exchange, routing key | `basic_publish('orders', 'order.created', b)` ↔ `queue_bind(q, 'orders', 'order.*')` | il binding con jolly è uno schema, e può stare in configurazione |
| Log di eventi | cluster e topic | `producer.send('orders', v)` ↔ `consumer.subscribe(['orders'])` | più gruppi di consumo: ognuno riceve tutto |
| Coda di lavori | nome del lavoro | `send_email.delay(id)` ↔ `@task def send_email` | spesso c'è il simbolo e l'indice lo collega già, come chiamata: è asincrona |
| Canale in tempo reale | canale o nome dell'evento | `socket.emit('typing')` ↔ `socket.on('typing', h)` | due versi sulla stessa connessione |
| Evento nel processo | emettitore e nome | `bus.emit('saved')` ↔ `bus.on('saved', h)` | |
| Notifica push | argomento o tipo di messaggio | `messaging.send({ topic })` ↔ handler nell'app | passa da un servizio esterno |
| Cambiamento di un dato | database e tabella | scrittura della tabella ↔ trigger, change stream, listener | chi emette è una scrittura: il punto è lo stesso dello store |
| Orario | nome del lavoro | cron, scheduler ↔ funzione pianificata | chi emette è il tempo: è un punto d'ingresso |
| Hook del ciclo di vita | nome dell'hook | framework o strumento ↔ `beforeSave`, `postinstall`, `pre-commit` | chi emette non ha codice nel progetto |

## Fuori dalle tre coppie

- **Contratti a tempo di build:** schemi condivisi, client generati, pacchetti comuni. Sono dipendenze fra unità, nel grafo dei moduli.
- **Infrastruttura:** nomi dei servizi in compose, DNS, proxy, volumi. Non è un ruolo: dice quale risorsa sta dietro una chiave.

## Cosa un collegamento non prova

1. Stessa chiave non è stesso momento: scrive / legge dice «stessa informazione», non che la copia sia aggiornata.
2. Chi emette non sa chi ascolta: zero ascoltatori è lecito, e un lato solo va spiegato, non corretto.
3. Un nodo che tutti toccano (log, configurazione) collega senza informare: si conta a parte.

## Quando un tipo entra nel prodotto

Con un caso reale in `benchmarks/`, attese scritte prima del codice, in cui il tipo unisce isole che altrimenti restano separate e spiega i suoi lati singoli.
