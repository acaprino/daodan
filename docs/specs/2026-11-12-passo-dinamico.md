# Passo dinamico: i test del progetto in un container

**Stato:** sezione 2 applicata in `plugins/codebase-map/skills/map/scripts/container.py` (`run_in_container`) e verificata con una riga di comando finta e con un container sul Kiri dell'utente; del motore proprio della sezione 3 è verificato solo lo scaricamento con il checksum; sezioni 5-7 non applicate, nessun passo dell'analisi usa ancora l'operazione. Misurato su tududi, JavaScript: la copertura passa dal 37,9% al 47,1% con il profiler di V8 e al 72,2% con il registro esatto, sopra la soglia del 70%. Dettagli in [`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md). **Data:** 12 novembre 2026. **Piano:** [`docs/plans/2026-11-12-passo-dinamico.md`](../plans/2026-11-12-passo-dinamico.md).

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
| 3. Dinamico | I test girano in un container; ciò che si osserva entra nel grafo | Sì, solo nel container | Su richiesta | Questa proposta |
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
2. **Preparazione.** Un comando che esegue codice del progetto per risolvere le dipendenze (Gradle e Maven, Yarn, una build, un indicizzatore che lancia gli script di build) raggiunge solo i registri del suo strumento. Gli script di installazione possono girare: restano nel container [costruito per Gradle e Maven].
   - La rete è `--internal`. Il proxy risolve solo i nomi dei registri ammessi e rifiuta ogni altro host, ogni porta diversa da 443 e ogni richiesta che non sia CONNECT [costruito]. Il container chiede i nomi al motore: che il motore non inoltri all'esterno il DNS di una rete interna, e che `--network none` lasci la sola interfaccia di loopback, va misurato con una sonda su ogni motore [da misurare: su Kiri 0.2.0 non ancora; Moby prima di 26.0.0, 25.0.4 e 23.0.11 inoltra il DNS di una rete interna, CVE-2024-29018].
   - Il proxy registra i byte e la durata di ogni CONNECT, chiude oltre un tetto di byte verso un host, e le righe entrano nel record della run [specificato].
3. **Esecuzione.** Senza rete: oggi gli indicizzatori Java e Kotlin e i comandi di `run_commands` [costruito]; i test del progetto, quando il passo dinamico sarà costruito [specificato].

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

### 6. Chi lo usa

- **Grafo delle chiamate:** i linguaggi in cui l'inferenza lascia molte chiamate senza risposta. JavaScript è il primo.
- **Flussi:** un arco osservato è un collegamento `chiama` con la sua provenienza.
- **Review e indagine:** la riproduzione di un finding e il test di riproduzione girano nel container al posto del workspace sull'host. Il disegno delle review dinamiche è una spec a parte.

### 7. Per linguaggio

Operazione e fatti osservati sono gli stessi per ogni linguaggio; l'immagine è la stessa (sezione 3); cambiano gli strumenti che il linguaggio scarica, la preparazione e il registro delle chiamate. Un registro si adotta solo se fa parte del runtime o della sua toolchain e riporta chiamante e chiamato; quello a campioni perde le chiamate brevi.

| Linguaggio | Preparazione | Registro candidato | Limite noto che può chiudere |
| --- | --- | --- | --- |
| JavaScript, TypeScript | `npm ci` o l'equivalente del lockfile | Profiler di V8 (`--cpu-prof`), a campioni, senza la riga della chiamata | Metodi su valori senza tipo e su oggetti costruiti a runtime |
| Python | `uv sync` o `pip install` | `sys.monitoring` (Python 3.12+), ogni chiamata con la sua riga | Parametri senza tipo |
| Java, Kotlin | Gradle o Maven, script compresi | JFR del JDK, a campioni; un agente Java registra ogni chiamata | Librerie calcolate dagli script Gradle (sezione 4) |
| Go | `go mod download` | pprof (`go test -cpuprofile`), a campioni | Valori di funzione, interfacce anonime |
| Rust | `cargo fetch`, build script accesi | perf, a campioni; richiede `perf_event_open`, che il profilo seccomp predefinito di Docker blocca | Codice generato dai build script (sezione 4) |
| C# | `dotnet restore` | dotnet-trace, a campioni | Nessuno: il motore del passo 2 non è ancora scelto |

## Limiti

- Il passo vede solo ciò che i test eseguono. Un progetto senza test, o con test che non partono, non dà nulla: è una lacuna dichiarata.
- I test che richiedono servizi (database, code, API esterne) partono solo se il progetto dichiara come avviarli.
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

- Quale registro adottare per ogni linguaggio (sezione 7). Il profiler di V8 dà coppie di funzioni senza la riga: la chiamata si ritrova dal nome, e due chiamate omonime nella stessa funzione restano ambigue. Su tududi vede il 35% delle chiamate senza risposta che stanno in file eseguiti. Il registro esatto (`benchmarks/call-provenance/dynamic_record.js`) le registra tutte e porta la copertura al 72,2%.
- Se il motore del passo 2 di un linguaggio gira dentro il container quando deve eseguire codice del progetto, come per le macro procedurali di Rust.
- Come convivono il motore di Daodan e un Kiri dell'utente. Kiri 0.2.0 rifiuta un secondo motore nella stessa distribuzione WSL («another Kiri engine is running on this machine»). Anche in distribuzioni diverse i due motori condividono la rete della VM di WSL, e ciascuno ricostruisce all'avvio e toglie all'arresto la stessa tabella nftables `kiri` (`crates/kiri-init/src/linux/net.rs`). Lettura applicata: Daodan usa il motore dell'utente quando risponde e non avvia il proprio accanto a un Kiri attivo; dichiara la lacuna.
- Quale comando esegue i test e come si avviano i servizi che richiedono.
- Quanto vale un arco osservato dopo una modifica al file del chiamante o della destinazione.
- Come si accende il passo: un parametro del run o una domanda al primo uso.
- Se misurare accanto un motore statico per programmi interi. Jelly (`cs-au-dk/jelly`, BSD 3-clause, 0.13.0 dell'11 maggio 2026) copre anche il codice che i test non eseguono; il suo modo dinamico dipende da NodeProf, fermo dal 2023.

**Per modificare questa spec:** un requisito in più solo per un'esigenza obbligatoria o un esito sbagliato riproducibile.
