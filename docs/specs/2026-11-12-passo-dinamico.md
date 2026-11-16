# Passo dinamico: i test del progetto in un container

**Stato:** sezione 2 applicata in `plugins/codebase-map/skills/map/scripts/container.py` (`run_in_container`) e verificata con una riga di comando finta e con un container sul Kiri dell'utente; del motore proprio della sezione 3 è verificato solo lo scaricamento con il checksum; le sezioni 5 e 7 sono applicate per Python e Go nello step `dynamic` della pipeline (`plugins/codebase-map/skills/map/scripts/dynamic/`), provate con un container finto e con il registro eseguito davvero. Python anche con una corsa su Modal sugli script e i test di Daodan, senza `benchmarks/` (16 novembre 2026: analisi 26 minuti, passo dinamico 2,6): 1.361 siti osservati e 82 buchi chiusi, ma solo dall'import dei moduli di test, perché pytest si fermava agli errori di raccolta; ora gira con `--continue-on-collection-errors` (sezione 7), da rimisurare. Gli altri linguaggi sono in corso; la sezione 6 non è applicata. Misurato su tududi, JavaScript: la copertura passa dal 37,9% al 47,1% con il profiler di V8 e al 72,2% con il registro esatto, sopra la soglia del 70%. Dettagli in [`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md). **Data:** 12 novembre 2026. **Piano:** [`docs/plans/2026-11-12-passo-dinamico.md`](../plans/2026-11-12-passo-dinamico.md).

Daodan deve saper rispondere a due domande che la lettura del codice lascia aperte: «quale funzione viene chiamata davvero, dove la destinazione si decide in esecuzione?» e «questo difetto si riproduce?». Vale per qualsiasi app o servizio: i casi concreti stanno nei README dei benchmark.

## Parole

- **Passo di analisi:** uno dei quattro modi con cui Daodan ricava fatti dal codice (statico, inferenza, dinamico, semantico). «Livello» resta la parola delle viste di un flusso ([fase 2](2026-11-09-flow-model.md), sezione 5).
- **Osservato:** provenienza di un fatto visto durante un'esecuzione. Si distingue da «provato» (il motore lo dimostra dal codice) e da «dedotto» (una regola accoppia i due capi).
- **Container:** processo isolato dall'host, con il suo file system e con rete e risorse limitate.
- **Motore di container:** il programma che avvia i container e parla la Docker Engine API.

## Comportamento attuale

- Codebase Map non esegue il programma: la copertura a runtime è nulla (`docs/plugins/codebase-map.md`). Il requisito 12 della [spec del motore](2026-11-08-risoluzione-chiamate-motore.md) vieta build e script del progetto.
- Le chiamate la cui destinazione si decide in esecuzione restano senza risposta dopo l'inferenza: metodi su valori senza tipo, oggetti costruiti a runtime, valori di funzione (`docs/plugins/codebase-map-linguaggi.md`, Limiti noti).
- senior-review esegue codice in due punti, sull'host: la riproduzione di un finding, quando il brief concede un workspace usa e getta (`review-quality-gates/SKILL.md`, classe `reproduced`), e il test di riproduzione di un'indagine, in un worktree usa e getta (`investigation-method/SKILL.md`, sezioni 4 e 5). Il worktree protegge il checkout, non il resto della macchina.

## Proposta

### 1. Quattro passi di analisi

| Passo | Cosa fa | Esegue codice del progetto | Quando parte | Stato |
| --- | --- | --- | --- | --- |
| 1. Statico | Parser e risolutore lessicale: file, simboli, import, chiamate | No | Con ogni snapshot | Applicato |
| 2. Inferenza | Il motore del linguaggio risolve le chiamate con le librerie del progetto | No | Con ogni snapshot, in background | Applicato |
| 3. Dinamico | I test girano in un container; ciò che si osserva entra nel grafo | Sì, solo nel container | Con ogni analisi, dopo il passo 2, quando un motore di container risponde | Applicato per Python e Go |
| 4. Semantico | Il modello scrive schede e regole di collegamento; i flussi uniscono chi scrive, chi legge e le azioni | No | Con l'analisi richiesta | Applicato; flussi in prova |

Ogni passo legge ciò che gli altri hanno già prodotto. Solo il primo è un prerequisito: il quarto lavora con o senza il terzo.

### 2. Un'operazione: eseguire un comando in un container

Il passo dinamico e la review usano la stessa operazione, con queste garanzie:

1. Il codice del progetto gira solo nel container, mai sull'host.
2. Il container riceve una copia usa e getta: i file del perimetro dello snapshot e ogni file che Git traccia, cartelle con il punto comprese (come `.mvn/`), tolti i file di segreti che lo snapshot non legge mai. Ciò che Git ignora non entra; dove c'è un `.git` e Git non risponde, la run è una lacuna dichiarata invece di una copia che porterebbe anche i file ignorati [costruito]. Un file tracciato conserva il bit di esecuzione che Git registra. I file che Daodan porta (un indicizzatore, uno strumento di build) entrano con la copia, ciascuno nel suo percorso. Il progetto non viene scritto.
3. Il codice del progetto non gira mai con una rete diversa dai registri del suo strumento. Daodan chiede al motore nessuna rete in esecuzione (`--network none`) e in preparazione una rete `--internal` con il solo proxy di Daodan, che apre la strada solo ai registri dello strumento: per Java e Kotlin Maven Central, Google Maven, JCenter e, per Gradle, il Plugin Portal [costruito]. Che il motore onori le due reti va misurato su ogni motore (sezione 4) [da misurare]. Il limite è dichiarato nella sezione 4: il proxy non vede percorso e corpo delle richieste, e un registro ammesso che accetta caricamenti è un canale verso l'esterno per un progetto che porta una credenziale di pubblicazione. Tempo, memoria, swap e numero di processi hanno un limite, con `no-new-privileges` [costruito]; `--cap-drop ALL`, un utente diverso da root dove l'immagine lo consente e un tetto sul log della fase [specificato]. Nessuna variabile d'ambiente dell'host passa al container [costruito].
4. Ogni esecuzione registra comando, immagine, durata ed esito.
5. Senza un motore di container l'operazione dichiara la lacuna, con la causa e il rimedio. Non ripiega mai su un'esecuzione sull'host.

### 3. Motore di container

- Daodan parla la Docker Engine API attraverso la riga di comando compatibile (`run`, `cp`, `rm`). Non dipende da un prodotto: un motore si sostituisce senza toccare il resto.
- Daodan porta il proprio motore: scarica Kiri a versione fissata nella cartella condivisa, con il checksum verificato, come ogni altro motore (requisito 12 della spec del motore), e lo usa senza interfaccia. L'utente non installa nulla. Daodan non esegue l'installer di Kiri, che cambia `PATH`, configurazione di Docker e avvio automatico dell'utente, e non modifica un motore già installato.
- Un motore si adotta solo se è attivo e supportato: licenza che consente la ridistribuzione, repository non archiviato, commit e release nell'ultimo anno. Il controllo si ripete a ogni cambio della versione fissata.
- Su Windows Kiri gira dentro WSL 2: Daodan importa una distribuzione propria nella sua cartella e parla al motore attraverso `wsl.exe`, senza l'applicazione di Kiri per Windows. Dove WSL 2 non è attivo serve un amministratore, una volta: Daodan dichiara la lacuna con il rimedio.
- Un'immagine sola per ogni linguaggio, C e C++ compresi: una base glibc fissata per digest, di circa 28 MB compressi, scelta sulla glibc che chiedono gli strumenti già compilati [specificato]. Ciò che un linguaggio chiede (interprete, compilatore, strumento di build, indicizzatore) Daodan lo scarica nel suo magazzino degli strumenti al primo uso del linguaggio, con il checksum verificato. Non c'è un'immagine per linguaggio né un'immagine con il compilatore [specificato]. Oggi Java e Kotlin usano Temurin 17, Python `python:3.13-slim`, C e C++ `buildpack-deps:noble` e il proxy `python:3.13-alpine`. Che un compilatore C e C++ rilocabile dia gli stessi risultati di quello dell'immagine è [da misurare].
- Il motore è sempre il Kiri di Daodan, portatile e incorporato: mai il Docker, il Podman o il Kiri che l'utente ha già (deciso dal proprietario il 15 novembre 2026) [specificato]. Oggi `find_engine` prova prima il motore dell'utente. La convivenza con un altro Kiri nella stessa macchina WSL 2 è [da misurare].
- Le librerie di un progetto stanno in un magazzino per progetto, mai condiviso: la build di un progetto non tocca ciò che un altro userà (deciso il 15 novembre 2026) [specificato].
- I limiti si calcolano all'avvio di ogni analisi da ciò che la macchina riporta in quel momento, e restano fermi fino alla fine; l'analisi successiva li ricalcola (deciso il 15 novembre 2026) [specificato]. Un container alla volta.
  - Processori: un quarto dei processori logici, almeno 1, al massimo 8 (massimo provvisorio). Quali indicizzatori ne usano più di uno è [da misurare].
  - Memoria: il bisogno misurato dell'indicizzatore più un quarto, entro la memoria libera meno una riserva per la macchina. Sotto il bisogno l'analisi è `unavailable`, con il bisogno e il rimedio: mai un risultato a metà.
  - Disco: metà dello spazio libero oltre una riserva di 5 GiB, fra 2 e 20 GiB. Oltre il tetto Daodan toglie per nome il magazzino usato meno di recente e lo scarica di nuovo quando serve.

Motori controllati il 12 novembre 2026 sui loro repository:

| Motore | Isolamento | Windows | Licenza e stato | Esito |
| --- | --- | --- | --- | --- |
| Kiri 0.2.0 (`libracoder/kiri`) | Una piccola VM Linux; su Linux direttamente sul kernel | WSL 2 | Apache 2.0; repository creato il 2 novembre 2026, release del 10 novembre | Scelto: il più leggero, parla la Docker Engine API. La versione fissata copre la sua giovane età |
| Podman | Container | WSL 2 | Apache 2.0, maturo | Sostituto, stessa API |
| microsandbox 0.7.14 | Micro-VM | Con WHP attivo | Apache 2.0, dichiarato beta | Scartato: API propria |
| sandbox-runtime 0.0.82 | Nessuna VM: limiti del sistema operativo | Dichiarato alpha: utente locale e filtri di rete per tutta la macchina | Apache 2.0 | Scartato su Windows |

Pesi di Kiri 0.2.0: installer per Windows 58 MB, il solo motore per Linux (`kiri-lite`) 2,4 MB, macOS 47-57 MB. Dentro WSL il motore sono due file, 8 MB in tutto; l'applicazione per Windows aggiunge un ponte di 6,8 MB e 71 MB di WebView2, che a Daodan non servono.

### 4. Ambiente in tre tempi

1. **Scaricamento.** Si scarica ciò che il progetto dichiara, con gli strumenti che già lo leggono: Daodan non reimplementa un gestore di pacchetti [specificato, non costruito].
   - Gira su una rete `--internal` come la preparazione. L'unica uscita è il proxy di Daodan in modalità pubblica: CONNECT verso qualsiasi host sulla porta 443. Il proxy risolve il nome, rifiuta ogni indirizzo non pubblico (reti private, loopback, link-local, 100.64.0.0/10, fc00::/7, multicast, riservati) e si collega all'indirizzo che ha controllato, non di nuovo al nome [specificato].
   - I comandi ammessi sono una tabella chiusa in `container.py`, non dichiarata dagli adattatori: lo strumento, il sottocomando e i flag obbligatori di ciascuno. Ogni altro comando con la rete pubblica è rifiutato prima che parta [specificato].
   - Prima che un gestore parta, Daodan legge come dati il lockfile o il file dei requisiti. Rifiuta le dipendenze da git, da URL, da `file:` e quelle modificabili (`-e`): un gestore le risolverebbe avviando git, una build o codice del progetto [specificato].
   - La versione del gestore la sceglie Daodan, mai il progetto. Il campo `packageManager` non avvia Corepack (nessuno shim di Corepack sul PATH, `COREPACK_ENABLE_PROJECT_SPEC=0`). pnpm non cambia versione da sé (`manage-package-manager-versions=false`). Gira il binario che Daodan porta, alla versione fissata [specificato].
   - Ogni indirizzo raggiunto si registra. Un checksum dichiarato che non torna scarta il file [specificato].
2. **Preparazione.** Un comando che esegue codice del progetto per risolvere le dipendenze (Gradle e Maven, Yarn, una build, un indicizzatore che lancia gli script di build) raggiunge solo i registri del suo strumento e, come una CI, gli host da cui il progetto dichiara le sue dipendenze (requisiti VCS, indici, repository, feed), letti dal manifest o dal modello della build e nient'altro: i `registries` delle unità della pre-mappa, che i lettori di pip, uv, Poetry, npm, pnpm, Yarn, Cargo, Maven, Gradle e NuGet scrivono [costruito]. `preparation.declared` ne dà gli host, github.com con quelli da cui GitHub serve i suoi download, dove npm prende una dipendenza da GitHub; un ripristino fallito le cui parole dicono che non ha raggiunto un host dichiarato è una lacuna `host_unreachable` che nomina l'host e i file che lo dichiarano (`preparation.unreached`). Il passo dinamico li dà a ogni osservatore e il passaggio degli indicizzatori a ogni indicizzatore che li prende; li aprono gli osservatori di Python, JavaScript, Go, Rust, C e C++ e della JVM e gli indicizzatori di Java, Kotlin, TypeScript, C# e C e C++ [costruito]. Il modello di Gradle della pre-mappa che fallisce si ripete una volta raggiungendo le repository che le impostazioni della build dichiarano (`pluginManagement`); se fallisce ancora è una lacuna `declared_hosts_failed` che le nomina [costruito]. Gli script di installazione possono girare: restano nel container [costruito per Gradle e Maven].
   - La rete è `--internal`. Il proxy risolve solo i nomi dei registri ammessi e degli host VCS dichiarati e rifiuta ogni altro host, ogni porta diversa da 443 e ogni richiesta che non sia CONNECT [costruito]. Il container chiede i nomi al motore: che il motore non inoltri all'esterno il DNS di una rete interna, e che `--network none` lasci la sola interfaccia di loopback, va misurato con una sonda su ogni motore [da misurare: su Kiri 0.2.0 non ancora; Moby prima di 26.0.0, 25.0.4 e 23.0.11 inoltra il DNS di una rete interna, CVE-2024-29018].
   - Il proxy registra i byte e la durata di ogni CONNECT, chiude oltre un tetto di byte verso un host, e le righe entrano nel record della run [specificato].
3. **Esecuzione.** Senza rete: oggi gli indicizzatori Java e Kotlin e i comandi di `run_commands` [costruito]; i test del progetto, quando il passo dinamico sarà costruito [specificato].
   - I servizi che la CI del progetto avvia accanto ai test (i service container dei job di GitHub Actions: faccetta `services` della pre-mappa, che `premap/renovate.py` legge con la libreria YAML di Renovate) partono accanto a ogni esecuzione di un osservatore, nella forma di un pod di Kubernetes: un container con `--network none` tiene uno spazio di rete, ogni servizio e l'esecuzione vi entrano (`--network container:<pod>`), così i test raggiungono il servizio a localhost, o al nome che gli host del pod gli danno, e nient'altro (`container.beside`, che il passo dinamico apre intorno a ogni osservatore) [costruito]. L'immagine si scarica prima della preparazione e gira per il digest che il registro ha dato; l'esecuzione aspetta il controllo di salute che la CI dichiara, che su Podman Daodan lancia da sé all'intervallo dichiarato (senza systemd Podman non ne lancia); i test ricevono le variabili che i job danno ai loro passi [costruito]. Un servizio che non parte (immagine irraggiungibile, controllo di salute mai superato, container uscito) è una lacuna `service_unavailable` con servizio, immagine e causa; uno che parte senza una parte di ciò che il job dichiara (una porta mappata su un'altra, volumi, opzioni diverse dal controllo di salute, variabili che la CI calcola) è `service_incomplete` [costruito]. Sul driver Modal dei benchmark i servizi girano in una VM Sandbox con Docker, nella rete della sandbox, che `block_network` chiude all'esterno [costruito].

Un ambiente git comune vale per ogni comando di ogni fase [specificato]:
- `GIT_CONFIG_NOSYSTEM=1` e `GIT_CONFIG_GLOBAL=/dev/null`;
- `GIT_TERMINAL_PROMPT=0`, nessun `GIT_ASKPASS` né `SSH_ASKPASS`, `GIT_SSH_COMMAND=false`;
- `GIT_ALLOW_PROTOCOL=https`, `protocol.allow=never` con il solo `https` ammesso, sottomoduli compresi;
- `core.fsmonitor=false`, `core.hooksPath=/dev/null`, nessun `git-lfs` nell'immagine.

L'ambiente del passo 2 resta com'è: lì nessuno script gira.

#### Perimetro della regola di rete

Gli script spenti non bastano: i file di configurazione del progetto possono far eseguire qualcosa a un comando di solo scaricamento, o cambiare dove si collega. Per ogni gestore, tutto [specificato]: nessun comando pubblico è ancora costruito. L'elenco dei gestori è chiuso: un gestore che la tabella non nomina (Bun, Poetry, Composer, Bundler, NuGet) non riceve la rete pubblica, e il suo comando è rifiutato.

| Vettore | Neutralizzazione | Prova |
| --- | --- | --- |
| npm e pnpm, `.npmrc`: `script-shell`, il comando `git`, `registry` e registri per scope, token | `.npmrc` non entra mai nella copia: è fra i file di segreti (`snapshot.FORBIDDEN_GLOBS`). La configurazione dell'utente e quella globale sono file vuoti di Daodan (`npm_config_userconfig`, `npm_config_globalconfig`), con `ignore-scripts` acceso. Un pacchetto che chiede un registro per scope diventa `failed` con la causa. | Fixture con `.npmrc` che punta `script-shell` e `git` a una sentinella e un `preinstall` sentinella: dopo `npm ci --ignore-scripts` nessuna sentinella ha girato. Una dipendenza git con il suo `.npmrc` (`git=` sentinella) è rifiutata leggendo il lockfile, prima che npm parta. |
| pnpm, `.pnpmfile.cjs` (hook eseguiti alla risoluzione) e le impostazioni di `pnpm-workspace.yaml` | `pnpm fetch --ignore-pnpmfile --ignore-scripts`. Un'impostazione che nomina un comando (una shell, un eseguibile) rifiuta il comando. | `.pnpmfile.cjs` sentinella non eseguito. |
| Yarn Berry e Yarn classic: `.yarnrc.yml` con `yarnPath` e i plugin in `.yarn/plugins`, `.yarnrc` con `yarn-path`, che sono codice del progetto | Come Gradle e Maven: un comando che esegue codice del progetto per risolvere le dipendenze. Gira in preparazione verso i soli registri, mai con la rete pubblica; `failed` o `unavailable` con la causa solo se chiede un host fuori dai registri. | Un `yarnPath` sentinella gira solo nella fase con i soli registri. |
| Cargo, `.cargo/config.toml` del progetto: fornitori di credenziali, `net.git-fetch-with-cli`, sostituzione delle sorgenti, `build.rustc`, `rustc-wrapper`, `runner`, alias | `CARGO_HOME` è di Daodan, senza credenziali. Un `.cargo/config` o `.cargo/config.toml` nel progetto fa di `cargo fetch` un comando che esegue codice del progetto: va in preparazione, verso i soli registri. `cargo fetch` è un comando interno: un alias non lo sostituisce. | Fixture con un `rustc-wrapper` sentinella: classificata come codice del progetto. Senza configurazione, un `build.rs` sentinella non gira con `cargo fetch`. |
| Go, `GOFLAGS`, `GOPROXY`, `GONOSUMDB`, `GOPRIVATE`, `GOINSECURE`, `GOVCS`, `GOTOOLCHAIN` dall'ambiente o dal file di `go env -w`; la riga `toolchain` di `go.mod` | Daodan li fissa tutti nel comando: `GOENV=off`, `GOPROXY=https://proxy.golang.org` senza `direct`, `GOSUMDB=sum.golang.org`, `GONOSUMDB`, `GOPRIVATE` e `GOINSECURE` vuoti, `GOVCS=*:off`, `GOTOOLCHAIN=local`. Nessuna variabile dell'host entra comunque (garanzia 3). | `go.mod` con un modulo raggiungibile solo da VCS, e `//go:generate` sentinella: `go mod download` non avvia git né la sentinella e fallisce con la causa. |
| pip, opzioni dentro `requirements.txt` (`--index-url`, `--extra-index-url`, `--find-links`), righe `-e` e requisiti che esistono solo come sorgenti o da VCS (si costruiscono eseguendo `setup.py`) | `pip download --isolated --only-binary=:all:` con `PIP_CONFIG_FILE` vuoto. Gli indici indicati dal progetto passano solo se pubblici. Le righe che si dovrebbero costruire falliscono, e l'unità le elenca come causa. | `-e .` e un pacchetto solo sorgente con `setup.py` sentinella: nessuna sentinella, causa con i due requisiti. |
| uv, `uv.toml` e `[tool.uv]`: indici, `find-links`, sorgenti git e locali, `no-build-isolation`, `keyring-provider` | `uv sync --frozen --no-build --no-install-project` con `UV_KEYRING_PROVIDER=disabled` e senza `.netrc` (`HOME` è di Daodan). `--no-build` vieta di costruire qualsiasi sorgente. | Sorgente locale con `setup.py` sentinella, e un indice su 127.0.0.1: nessuna sentinella, indice rifiutato. |
| Scaricamento semplice di una sorgente indicata da uno strumento (registro dei provider di CMake, link di una pagina) | `curl` o `wget` in GET su https, con un tetto di dimensione; ogni redirect ripassa dal controllo dell'indirizzo. | Un redirect verso 127.0.0.1 rifiutato. |

- **Il passo pubblico ha la copia montata.** Un lockfile ostile può far chiedere file a qualsiasi host pubblico che nomina. Così rivela che un'analisi è avvenuta, quando, da quale indirizzo pubblico e con quali versioni. Nessun file della sorgente viene inviato: i comandi della tabella chiusa scaricano soltanto, e pubblicazione e caricamento (`npm publish`, `cargo publish`, `uv publish` e simili) non sono nella tabella [specificato].
- **Preparazione con codice del progetto (Gradle, Maven).** La rete è `--internal`, senza uscita.
  - Il proxy risolve solo i registri ammessi; il DNS del motore su una rete interna va misurato (sezione 4, punto 2).
  - Il proxy stampa i CONNECT che rifiuta, ma nessuno li raccoglie: il registro di ogni CONNECT nel record della run è [specificato] (sezione 4, punto 2).
  - Il percorso e il corpo delle richieste sono dentro TLS e il proxy non li vede. Un registro ammesso che accetta caricamenti è quindi un canale verso l'esterno, pubblico, per un progetto che porta una credenziale di pubblicazione (punto Credenziali): per questo ogni strumento raggiunge solo i registri suoi [costruito per Java e Kotlin]. Fra quelli di Java e Kotlin solo il Plugin Portal di Gradle accetta caricamenti, plugin con la chiave dell'editore; Maven Central, Google Maven e JCenter si pubblicano altrove o sono in sola lettura. Senza il Plugin Portal nessun progetto Gradle che applica un plugin si costruisce, perciò resta ammesso. È un limite accettato e dichiarato. Che gli altri registri ammessi non accettino caricamenti va misurato [da misurare].
- **Credenziali dell'utente.** Nessun token, chiave o helper di credenziali dell'utente entra in nessuna fase [costruito].
  - Le variabili dell'host non passano [costruito].
  - Con una preparazione `HOME` è la cartella di Daodan nel volume di stato [costruito]; senza, è quella dell'immagine fissata, che non ne porta. Con il passo di scaricamento sarà sempre quella di Daodan [specificato].
  - `.npmrc`, `.pypirc`, `.netrc` e le chiavi non entrano nella copia, in nessuna cartella [costruito].
  - Gli helper (keyring di uv, credenziali di Cargo e di git) sono spenti o assenti [specificato].
  - Un registro privato che chiede credenziali rende l'unità `unavailable`, con la causa [specificato].
- **Credenziali del progetto.** Una credenziale che il progetto porta in un file che entra nella copia (`npmAuthToken` in `.yarnrc.yml`, `bunfig.toml`, `pip.conf`, un URL con utente e chiave in `uv.toml` o in `requirements.txt`, `nuget.config`, `gradle.properties`, un `*.env`) vale verso ogni registro che lo strumento di quella fase raggiunge e che accetta caricamenti: con lei il codice del progetto in preparazione può pubblicare la copia. Daodan non modifica il progetto e il file serve allo strumento, quindi resta nella copia. Daodan cerca nel contenuto dei file di configurazione dei gestori le forme di credenziale (utente e chiave in un URL, `npmAuthToken`, `_authToken`, `ClearTextPassword`, `gradle.publish.key`); se ne trova una e la fase raggiunge un registro che accetta caricamenti, la run dichiara il limite nel suo record e in ciò che l'utente vede [specificato]. Un file che contiene solo credenziali, come `.npmrc`, resta fuori dalla copia [costruito].
- **Cosa torna sull'host.** Solo i file d'uscita dichiarati, letti come dati: SCIP, JSON, testo. Niente di quello che esce dal container viene eseguito sull'host.
  - L'archivio si legge a flusso fino al tetto, come tar semplice. Sono ammessi solo file regolari e cartelle, e le dimensioni si sommano prima di scrivere: il tetto è 1 GiB per run, oltre la run è `failed` con la causa [costruito].
  - Daodan non usa l'estrazione di `tarfile` né i suoi filtri. Controlla ogni nome (niente percorsi assoluti, `..`, barre rovesce, unità, caratteri di controllo, nomi riservati di Windows), crea le cartelle e scrive ogni file dal suo contenuto in una cartella nuova e vuota, senza mai aprirlo sopra un file che c'è già. Nessun collegamento viene mai creato, quindi i difetti dei filtri (CVE-2025-4517 e seguenti) non hanno su cosa agire. Poi sposta, mai sopra un file che c'è già né sopra i file della run (record e log) [costruito].
  - La lettura delle intestazioni rifiuta una dimensione negativa, che riporta il lettore di CPython prima della sua correzione alla stessa intestazione per sempre (CVE-2025-8194), e un'intestazione pax oltre 8 KiB, che prima di 3.12.6 si analizza con backtracking (CVE-2024-6232); un nome lungo GNU oltre 8 KiB è rifiutato allo stesso modo. Il controllo sta in una sottoclasse di `TarInfo` passata al lettore, senza toccare la libreria standard, sui metodi che `tarfile` ha da 3.12 in su; provato su questo interprete anche con il lettore di prima della correzione [costruito].
- **Cosa la regola non copre.**
  - Una fuga dal motore di container o dal kernel della VM di WSL, condiviso con le distribuzioni dell'utente.
  - Un pacchetto ostile che agisce solo in esecuzione: senza rete può falsare le uscite (un indice sbagliato, quindi un grafo sbagliato) o consumare risorse fino ai limiti.
  - Un caricamento verso un registro ammesso che lo accetta, con una credenziale che il progetto porta: è dichiarato nella run, non impedito.
  - L'inoltro DNS del motore, finché non è misurato.
  - Canali laterali come i tempi.

Lo stesso container può preparare anche dati per il passo 2: le librerie che gli script di build calcolano (Gradle) e i file che i build script generano (Rust). Il passo 2 li legge come legge i file di build, e sull'host continua a non girare nulla. Le macro procedurali di Rust restano escluse: espanderle significa eseguirle.

### 5. Fatti osservati

- Un arco osservato entra nello store degli archi con un risolutore proprio (campo `resolver`, come `builtin-lexical` e i motori) e con la provenienza «osservato», distinta da `confirmed` e `candidate`.
- Vale per l'esecuzione che lo ha prodotto. Prova che la chiamata può arrivare a quella destinazione, non che arrivi solo lì. Una chiamata non osservata resta senza risposta: non prova che il codice non venga chiamato.
- La destinazione si classifica per la sua provenienza, come chiede il requisito 23: una funzione definita fuori dal progetto è esterna ed esce dal denominatore.
- Il rapporto «risolte su risolvibili» riporta gli archi osservati a parte, così il valore dei passi 1 e 2 resta confrontabile nel tempo.
- Un arco osservato che contraddice un arco provato è un difetto di uno dei due passi: si riporta, non si sceglie.
- Una coppia chiamante-chiamato vista in uno stack campionato è un fatto osservato di una seconda fonte (sezione 7): `confidence` `sampled` e resolver `ENTRY@VERSION:sampled`, distinti da quelli esatti. Non dice mai che una chiamata che nessun campione ha visto non avviene.

Applicato così (`dynamic/__init__.py`, `edge_store.py`, `code_graph.write_observed`, `edge_view.py`):

- **Unione per posizione.** Un sito osservato risponde al riferimento dello snapshot che ha il nome del chiamato nello stesso punto (file, riga, colonna in byte) con lo stesso nome. Un riferimento di chiamata prende i siti raggiunti come chiamate; una lettura qualsiasi sito (una property gira su una lettura); una chiamata con il chiamato calcolato prende il sito che inizia dove inizia lei. I siti senza riferimento (confronti, operatori, ingressi e uscite di `with`) non diventano archi: si contano per ruolo (`unjoined`).
- **Riga.** Una riga per destinazione nella tabella `edges`, con `confidence` `observed` e `resolver` il registro e la sua versione (`dynamic-record-python@1`). Una funzione del progetto è `project-callable` con la dichiarazione dello snapshot; un wrapper vale la funzione del progetto che avvolge (`chain` `wraps`); un chiamabile del progetto che lo snapshot non dichiara è `project-value`; ogni altra destinazione è `external` con il suo pacchetto. Un mock non è una destinazione.
- **Copertura.** Le righe osservate si contano a parte: un sito tiene la classe statica che aveva, qualunque cosa la corsa abbia visto. Un buco con una destinazione osservata esce da `holes`, entra in `answered.observed` e la sua classe si conta in `observed.closed`; la riga del buco resta nello store. Vale sempre siti = risposte + buchi. `observed` porta anche i fatti della corsa: registro, test eseguiti con il loro esito, siti non uniti, file con chiamate che nessun test ha eseguito, conflitti.
- **Conflitto.** Un riferimento con un bersaglio provato (`confirmed`) e nessuna destinazione osservata fra i bersagli, o con un esterno provato dove la corsa arriva nel progetto. Le due righe restano nello store, quella osservata con `conflict`; l'unione lo riporta come lacuna `observed-conflict`.
- **Campioni.** Un osservatore dà le coppie del profiler in `sampled`, accanto ai siti esatti (contratto in `dynamic/__init__.py`). Con la riga della chiamata, una coppia risponde al riferimento del chiamante che copre quella riga e ha il nome del chiamato, se è uno solo (`dynamic.join_sampled`); altrimenti è una riga senza riferimento, un arco fra due dichiarazioni che non chiude nessun buco, con la causa (`no-line`, `not-found`, `ambiguous`). Si contano a parte, in `answered.sampled` e `sampled`; un buco con una destinazione esatta si chiude come `observed`. Dai campioni non vengono conflitti né file non eseguiti.
- **Vista.** `edge_view` risponde con un arco osservato solo dove non rispondono né le righe provate né il risolutore lessicale, con `confidence` `observed`, o `sampled` dove nessun arco esatto risponde; il buco resta scritto sul riferimento.
- **Durata.** Le righe osservate stanno nello store legato allo snapshot: uno snapshot nuovo riscrive il grafo statico e l'osservazione si rifà. Sullo stesso store il passo non gira due volte con lo stesso registro.
- **Corsa senza righe.** Nessun test girato (`not-run`) o test girati senza righe di un linguaggio (`not-observed`): non si salva nulla e la prossima analisi riprova. La causa dice cosa ha visto il registro: siti nei file del linguaggio a nessun riferimento, contati per ruolo; chiamate solo in file che lo snapshot non ha; oppure nessuna chiamata dai file del linguaggio, con i file con chiamate che nessun test esegue (test che importano e confrontano soltanto).

### 6. Chi lo usa

- **Grafo delle chiamate:** i linguaggi in cui l'inferenza lascia molte chiamate senza risposta. JavaScript è il primo.
- **Flussi:** un arco osservato è un collegamento `chiama` con la sua provenienza.
- **Review e indagine:** la riproduzione di un finding e il test di riproduzione girano nel container al posto del workspace sull'host. Il disegno delle review dinamiche è una spec a parte.

### 7. Per linguaggio

Operazione e fatti osservati sono gli stessi per ogni linguaggio; l'immagine è la stessa (sezione 3); cambiano gli strumenti che il linguaggio scarica, la preparazione e il registro delle chiamate. Il registro si sceglie in quest'ordine (deciso dal proprietario il 16 novembre 2026):

1. Un registro esatto che esiste già (ogni chiamata, con chiamante, chiamato e posizione del sito) si adotta, fissato per versione e sha256 e con la licenza dichiarata; Daodan scrive solo l'adattatore.
2. Dove nessuno lo è, Daodan scrive il registro esatto e dice quali candidati esistenti ha scartato e su che cosa.
3. Il profiler a campioni della toolchain è una seconda fonte dichiarata (sezione 5): di solito dà coppie da funzione a funzione, senza la posizione del sito, e perde le chiamate brevi.

| Linguaggio | Preparazione | Registro | Limite noto che può chiudere |
| --- | --- | --- | --- |
| JavaScript, TypeScript | `npm ci` o l'equivalente del lockfile | In corso | Metodi su valori senza tipo e su oggetti costruiti a runtime |
| Python | `uv sync`, `poetry install` o `pip install`, come dice il lockfile | Adottato (punto 2): il registro di Daodan su `sys.monitoring`, l'API del runtime (Python 3.12+), ogni chiamata con la sua posizione (`dynamic/python_record.py`); `cProfile` dà le coppie per funzione, senza il sito | Parametri senza tipo |
| Java, Kotlin | Gradle o Maven, script compresi | In corso | Librerie calcolate dagli script Gradle (sezione 4) |
| Go | `go mod download` | Adottato (punto 2): una riscrittura dei sorgenti nella copia del container (`dynamic/go_record.go`); la toolchain non ha un aggancio che dia chiamante e chiamato, pprof campiona (`dynamic/go.py`) | Valori di funzione, interfacce anonime |
| Rust | `cargo fetch`, build script accesi | In corso | Codice generato dai build script (sezione 4) |
| C, C++ | Il ripristino che il progetto dichiara (vcpkg, Conan) | In corso | Puntatori a funzione |
| C# | `dotnet restore` | Nessun osservatore | Nessuno: il motore del passo 2 non è ancora scelto |

#### Python, applicato

Un osservatore è un modulo di `dynamic/` che si dichiara (`ENTRY`, `VERSION`, `LANGUAGES`), come un analyzer; `dynamic.observers()` li elenca. Quello di Python è `dynamic/python.py`.

- **Comando.** È quello che il progetto dichiara, letto dalla pre-mappa (faccetta `tests`, lettore `premap/python_tests.py`), mai una convenzione di Daodan. pytest dove il progetto lo dichiara o lo configura: una configurazione di pytest, pytest o un suo plugin fra le dipendenze dichiarate, un `conftest.py`. unittest solo dove un file scrive il comando: una riga `python -m unittest ...` in `tox.ini` o in un makefile. I soli file di test non dichiarano nulla: lacuna `no_test_command`, e nessun container parte. Un pytest dichiarato dentro le cartelle che un altro pytest riceve non parte da sé: lo raccoglie quello (un progetto di fixture, un membro). A pytest Daodan aggiunge solo `--continue-on-collection-errors`, un'opzione di pytest che non tocca il progetto: senza, un modulo di test che non si importa nel container (una dipendenza opzionale, un servizio) ferma tutti gli altri. unittest non ne ha bisogno: carica un modulo alla volta e un import fallito è un test in errore.
- **Python.** Il registro chiede Python 3.12. Un progetto che dichiara un Python più vecchio (una versione, o un intervallo che finisce sotto 3.12) è una lacuna `python_too_old` e i suoi test non girano. Una versione esatta che l'immagine non ha la installa la preparazione (mise). Un intervallo che esclude il Python dell'immagine senza nominare una versione è `python_unavailable`. Nel container il Python dell'ambiente si misura prima dei test.
- **Preparazione**, con i soli registri: la toolchain, uv, il ripristino condiviso dell'ambiente della cartella che contiene i test (`preparation.restores`); se i test stanno fuori da ogni progetto Python, l'unico ambiente del progetto (un manifest dentro le cartelle dei test è di una fixture), altrimenti uno vuoto. Il progetto stesso si installa nell'ambiente, modificabile e senza dipendenze, dove la cartella ha una configurazione di build: è codice del progetto, quindi sta in questa fase. Dove il progetto dichiara pytest e l'ambiente ripristinato non lo contiene, Daodan porta pytest alla sua versione fissata e lo dice (`runner_brought`). Dove il progetto dichiara requisiti VCS (`nome @ git+https://…`, `#egg=nome`, una sorgente `{ git = "…" }` di uv o Poetry), la preparazione installa git dall'archivio Debian dell'immagine (`deb.debian.org`, su https) e raggiunge gli host dei loro URL. Una cartella la cui installazione fallisce si installa di nuovo senza quei requisiti: pip con un override di uv che nessun ambiente soddisfa, uv sync con `--no-install-package`. La lacuna `vcs_not_installed` riporta le parole di uv, che nominano il requisito e la causa (host rifiutato, autenticazione, ref mancante); il resto dell'ambiente c'è. Se fallisce anche la seconda, il ripristino fallito riporta le parole di entrambe.
- **Esecuzione**, senza rete: ogni comando sotto il registro, caricato da un `sitecustomize.py` sul `PYTHONPATH`. Un'interruzione dopo un'ora lascia al registro il tempo di scrivere ciò che ha visto.
- **Lacune della corsa:** test che non partono (con la coda del log), che falliscono, che non trovano test, moduli di test che pytest non riesce a importare (`tests_not_collected`, una lacuna con ogni modulo e la prima riga del suo errore; se nessun altro test gira, la corsa non è partita), che superano il tempo, che cercano un servizio o la rete (`services_unreachable`), un progetto che non si installa, un ripristino fallito, un requisito VCS che non si installa (`vcs_not_installed`), un host dichiarato che il ripristino non raggiunge (`host_unreachable`).

## Limiti

- Il passo vede solo ciò che i test eseguono. Un progetto senza test, o con test che non partono, non dà nulla: è una lacuna dichiarata.
- I test che richiedono servizi (database, code, API esterne) partono solo se il progetto dichiara come avviarli. Oggi il passo avvia i service container di GitHub Actions, non i `services:` di GitLab CI né un file compose che la CI o gli script di test avviano: quei test falliscono, e la corsa lo dice.
- Un ambiente Python riceve le dipendenze che il ripristino condiviso installa: gli extra e i gruppi che il gestore non installa da sé mancano, e i test che li importano non partono.
- Un container protegge l'host da errori e da script comuni, non da un attacco mirato al kernel. Su Linux i container di Kiri condividono il kernel dell'host.
- La preparazione costa tempo e spazio a ogni progetto: installazione dei pacchetti e, al primo uso di un linguaggio, i suoi strumenti.

## Prova

Parametri e soglie in [`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md), scritti prima di ogni misura.

1. **Isolamento.** Dal container una richiesta di rete fallisce, una scrittura nel progetto è rifiutata e sull'host non compare nessun file.
2. **Copertura.** Sugli stessi casi del passo 2: risolte su risolvibili per linguaggio, con e senza gli archi osservati; quante posizioni senza risposta ricevono una destinazione; quanti archi osservati contraddicono un arco provato.
3. **Costo.** Durata di preparazione ed esecuzione, RAM di picco, spazio su disco.
4. **Ambiente per il passo 2.** Su un caso Gradle e su uno Rust: risolte su risolvibili con e senza i dati preparati nel container.
5. **Motore proprio.** Su una macchina senza Kiri: Daodan scarica il motore ed esegue un comando in un container senza aprire finestre. `PATH`, configurazione e contesto di Docker e avvio automatico dell'utente restano invariati; fuori dalla cartella di Daodan resta solo la registrazione della distribuzione WSL. Provata su Windows il 12 novembre 2026, con un Kiri dell'utente già attivo: riuscita (README del benchmark).

## Da decidere

- Se il motore del passo 2 di un linguaggio gira dentro il container quando deve eseguire codice del progetto, come per le macro procedurali di Rust.
- Come convivono il motore di Daodan e un Kiri dell'utente. Kiri 0.2.0 rifiuta un secondo motore nella stessa distribuzione WSL («another Kiri engine is running on this machine»). Anche in distribuzioni diverse i due motori condividono la rete della VM di WSL, e ciascuno ricostruisce all'avvio e toglie all'arresto la stessa tabella nftables `kiri` (`crates/kiri-init/src/linux/net.rs`). Lettura applicata: Daodan usa il motore dell'utente quando risponde e non avvia il proprio accanto a un Kiri attivo; dichiara la lacuna.
- Come si avviano i servizi che la CI dichiara fuori da GitHub Actions: i `services:` di GitLab CI, un file compose che un passo della CI o uno script di test avvia.
- Quanto vale un arco osservato dopo una modifica: oggi vale per lo store del suo snapshot (sezione 5); se tenerlo per i file non toccati è da decidere.
- Se misurare accanto un motore statico per programmi interi. Jelly (`cs-au-dk/jelly`, BSD 3-clause, 0.13.0 dell'11 maggio 2026) copre anche il codice che i test non eseguono; il suo modo dinamico dipende da NodeProf, fermo dal 2023.

Deciso il 16 novembre 2026:

- **Registro:** l'ordine di scelta della sezione 7.
- **Comando dei test:** quello che il progetto dichiara, dalle voci `tests` della pre-mappa (`premap/python_tests.py`, `premap/npm_tests.py`), mai una convenzione di Daodan.
- **Accensione:** il passo è uno step della pipeline, fra l'analisi e l'unione, acceso quando un motore di container risponde. Senza motore dichiara la lacuna e la pipeline arriva all'unione. `DAODAN_DYNAMIC=off` lo salta; `pipeline.run(..., stop="analyze")` si ferma prima.

**Per modificare questa spec:** un requisito in più solo per un'esigenza obbligatoria o un esito sbagliato riproducibile.
