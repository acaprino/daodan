# Piano: passo dinamico in un container

Eseguire i task nell'ordine e segnare solo i passi verificati. La Parte A misura senza toccare i plugin; la Parte B resta subordinata alla misura e al via dell'utente.

**Obiettivo:** sapere quante chiamate senza risposta ricevono una destinazione quando i test del progetto girano in un container, e a quale costo; poi, se la misura lo giustifica, portare l'operazione e gli archi osservati in Codebase Map.

**Funzionamento:** un motore di container che parla la Docker Engine API esegue i test su una copia del perimetro dello snapshot. Le chiamate osservate si riportano alle posizioni che il passaggio del motore lascia senza risposta e si contano con lo stesso criterio, risolte su risolvibili.

**Tecnologie:** Python 3 solo libreria standard, riga di comando compatibile con `docker`, Kiri 0.2.0, Markdown.

**Spec:** `docs/specs/2026-11-12-passo-dinamico.md`

## Vincoli

- Il codice di un progetto gira solo in un container, mai sull'host, anche durante la misura.
- Run pesanti: chiedere prima all'utente, un processo alla volta, memoria libera controllata. Dove gira la misura, in locale o su Modal, lo decide l'utente prima del lancio.
- Soglie e parametri si scrivono nel README del benchmark prima di misurare.
- Nessun bump di versione di plugin o marketplace.
- Documenti in italiano al presente; riferimenti e brief in inglese, come sono.
- I commit si eseguono solo su richiesta dell'utente.

## Parte A: misura

### Task 1: avvio di un container isolato

- [x] **Passo 1:** container senza rete su Kiri: la richiesta di rete fallisce.
- [x] **Passo 2:** cartella montata in sola lettura: la scrittura è rifiutata e sull'host non compare nessun file.
- [x] **Passo 3:** tempi a freddo e a caldo nel README di `benchmarks/call-provenance`.

### Task 2: copertura osservata su un caso JavaScript

**File:**
- Crea: uno script in `benchmarks/call-provenance/` che prepara il container, esegue i test e scrive le coppie chiamante-chiamato osservate.
- Modifica: `benchmarks/call-provenance/README.md` (risultati).

- [x] **Passo 1:** parametri e soglia nel README.
- [x] **Passo 2:** copia del perimetro, installazione dei pacchetti con la rete aperta ai soli registri, test con la rete chiusa e il profiler attivo. Eseguito con le deviazioni scritte nel README.
- [x] **Passo 3:** riporto delle coppie osservate alle posizioni senza risposta dello store del motore, classificate per provenienza.
- [x] **Passo 4:** conteggio con e senza gli archi osservati, archi che contraddicono un arco provato, durata, RAM di picco e spazio.
- [x] **Passo 5:** risultati nel README, con i test che non sono partiti e il motivo.

### Task 3: decisione

- [x] **Passo 1:** l'utente decide dai numeri del Task 2 se la Parte B parte, per quali linguaggi e con quale registratore.
  - Registratore per JavaScript, deciso il 12 novembre 2026: il registro esatto (`benchmarks/call-provenance/dynamic_record.js`), da misurare sullo stesso caso prima di decidere il resto. Misurato lo stesso giorno: 72,2%, soglia raggiunta (README del benchmark).
  - Deciso il 14 novembre 2026: la Parte B parte e il container entra nel prodotto. È uno strato comune con tre utenti: il passo dinamico (JavaScript per primo, con il registro esatto), gli indicizzatori che devono costruire il progetto (scip-java per Java e Kotlin, il database di compilazione di scip-clang per C e C++: Task 9 e 10 di `docs/plans/2026-11-14-grafo-dall-indice.md`) e poi le review dinamiche.

## Parte B: nel plugin (dopo la misura)

I passi di ogni task si scrivono dopo il Task 3, perché dipendono dalle scelte ancora aperte nella spec.

### Task 4: operazione «esegui un comando in un container»

Le cinque garanzie della sezione 2 della spec, ciascuna con il suo test; ricerca del motore presente e scaricamento di Kiri a versione fissata con checksum; lacuna dichiarata dove il motore manca.

**File:**
- Crea: `plugins/codebase-map/skills/map/scripts/container.py`, solo libreria standard; scaricamento, cartella condivisa e memoria libera vengono da `resolve_edges.py`.
- Crea: `tests/test_codebase_map_container.py`, con una riga di comando finta compatibile con `docker`.

**Letture delle scelte aperte.** Le altre voci di «Da decidere» non servono a questo task.
- **Motore di Daodan e motore dell'utente.** Prima un motore dell'utente che risponde (`docker`, poi `podman`), usato com'è: nessun contesto, nessuna configurazione, nessuna opzione `--context`. Solo se nessuno risponde parte il Kiri di Daodan, nella sua distribuzione, con i router dei domini su 47080 e 47443 invece di 80 e 443. Non parte se un'altra distribuzione Kiri è attiva: le distribuzioni WSL 2 condividono la rete, e ogni motore Kiri ricostruisce all'avvio e toglie all'arresto la stessa tabella nftables `kiri` (Kiri 0.2.0, `crates/kiri-init/src/linux/net.rs`). Il demone parte con l'operazione e la distribuzione si ferma alla fine; se prima non c'era una distribuzione predefinita, quella di Daodan si toglie dopo l'uso, perché non diventi la predefinita dell'utente.
- **Perimetro della copia.** I file che il perimetro dello snapshot attraversa (`tree_scope.Perimeter`), meno quelli che lo snapshot non legge mai (`snapshot.is_forbidden`). Non solo i file analizzati: i test leggono anche configurazione e dati.
- **Come entra la copia.** Un archivio tar sullo standard input di `cp -`, in un container creato e non ancora avviato. Il progetto non viene mai montato; i file dichiarati escono con `cp <container>:<percorso> -`.
- **Rete della preparazione.** Una rete `--internal` senza uscita e un proxy che apre `CONNECT` sulla porta 443 dei soli registri dei pacchetti, in un container dell'immagine `python` a digest fissato. Il risultato della preparazione si salva con `commit` e l'esecuzione parte da quell'immagine con `--network none`.
- **Riga di comando per il Kiri di Daodan.** `kiri-lite` non ha la riga di comando `docker` e `kiri run` la richiede: Daodan prende `kiri`, `kiri-init` e `docker` dal pacchetto completo della stessa release (`kiri-0.2.0-1.<arch>.rpm`, 47 MB), verificato con il checksum di `SHA256SUMS`, e li estrae con `lzma` e il formato cpio, senza zstd.
- **Linux e macOS.** Il Kiri di Daodan solo su Windows, nella sua distribuzione WSL. Su Linux Kiri gira come root e cambia le tabelle nftables dell'host; su macOS serve l'applicazione con la VM. Senza un motore dell'utente l'operazione dichiara la lacuna.

- [x] **Passo 1:** test scritti prima del codice e visti rossi, uno per garanzia: hash del progetto identici prima e dopo, nessun montaggio; nella copia entra solo il perimetro, fuori i file ignorati da Git e quelli proibiti; esecuzione con `--network none`, preparazione sulla rete interna con il proxy; limiti di memoria, processi e tempo passati, e un container scaduto rimosso; nessuna variabile dell'host nella riga di comando; un record per ogni esecuzione; senza motore la lacuna con causa e rimedio e nessuna esecuzione sull'host; un checksum sbagliato rifiutato; il motore dell'utente usato e la sua configurazione identica byte per byte; il proxy rifiuta un host fuori dai registri. Verificato il 14 novembre 2026: 13 test rossi su uno stub dell'interfaccia, poi verdi; dopo la prova reale un test in più, sotto 1 GB liberi sul disco della cartella condivisa la lacuna prima di ogni scaricamento.
- [x] **Passo 2:** copia del perimetro, `create`, `cp -`, `start -a` con il tempo massimo, file dichiarati riportati fuori in una cartella esterna al progetto, `rm -f` in ogni caso, record in JSON Lines. Test: le prime sei garanzie del passo 1.
- [x] **Passo 3:** preparazione con rete interna, proxy e `commit`; alla fine `rm -f` del proxy, `network rm` e `rmi -f` dell'immagine preparata. Test: rete e proxy della preparazione, allowlist del proxy. Verificato con la riga di comando finta e con il proxy sull'host; su un motore reale la preparazione non è provata.
- [ ] **Passo 4:** ricerca del motore, scaricamento di Alpine e Kiri a versione fissata con checksum nella cartella condivisa, distribuzione WSL importata dalla cartella di Daodan con `/etc/wsl.conf` senza unità di Windows né interop; memoria libera sotto il limite del container, WSL 2 assente, cgroup v1 o scaricamento fallito danno la lacuna. Test: motore dell'utente, lacuna, checksum.
  - Verificato il 14 novembre 2026: ricerca del motore, lacune, checksum rifiutato; su questo PC lo scaricamento del pacchetto completo con il checksum e l'estrazione di `kiri`, `kiri-init` e `docker` (52 MB). Su C: l'import della distribuzione con i tre file è fallito con `Wsl/Service/RegisterDistro/E_FAIL`, perché restavano 80 MB. Ripetuto lo stesso giorno con la cartella condivisa su D: (`LOCALAPPDATA` del solo processo di prova): scaricamento con il checksum, estrazione, import, `docker --version` attraverso `wsl.exe` (29.9.2), `kiri` che risponde, cgroup v2 montato, poi `wsl --unregister`; `wsl -l -v`, `PATH` e `~/.docker` identici prima e dopo. Non verificati: la lacuna con cgroup v1 e il demone di Daodan, che qui non può partire accanto al Kiri dell'utente.
- [x] **Passo 5:** prova reale su questo PC, con `DAODAN_CONTAINER_SMOKE=1`, saltata sotto 4 GB liberi o senza motore: un progetto minimo, un solo container con il motore che l'operazione trova, una richiesta di rete e una scrittura nel progetto che falliscono, un file riportato fuori. `PATH`, configurazione e contesti di Docker e distribuzione WSL predefinita confrontati prima e dopo.
  - Eseguita il 14 novembre 2026 sul Kiri dell'utente, trovato come `docker`: richiesta di rete rifiutata, scrittura finita nella copia, progetto identico, tre file riportati fuori, 7-11 s; impostazioni identiche. Resta nel Kiri dell'utente l'immagine `alpine@sha256:f59abe65…`, scaricata dalla prova. Con il Kiri di Daodan la prova resta da fare (passo 4).
- [x] **Passo 6:** stato della spec e del piano: applicato solo ciò che i passi 1-5 verificano.

### Task 5: archi osservati nello store

Un risolutore nuovo in `resolve_edges.py` con la provenienza «osservato»; il rapporto li conta a parte; un arco osservato che contraddice un arco provato viene riportato.

### Task 6: riferimenti del plugin

`docs/plugins/codebase-map.md`, `docs/plugins/codebase-map-linguaggi.md` e i `references/` della skill descrivono il passo come comportamento attuale solo quando i Task 4 e 5 sono verificati.

### Task 7: review dinamiche

Spec propria in senior-review: la riproduzione di un finding e il test di riproduzione di un'indagine usano l'operazione del Task 4.

### Task 8: ambiente del passo 2 dal container

Le librerie calcolate dagli script Gradle e i file generati dai build script di Rust (sezione 4 della spec), misurati su un caso per linguaggio (misura 4) prima di adottarli.
