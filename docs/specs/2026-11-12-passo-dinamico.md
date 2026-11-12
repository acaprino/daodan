# Passo dinamico: i test del progetto in un container

**Stato:** proposta, non applicata. Misurato su tududi, JavaScript: la copertura passa dal 37,9% al 47,1% con il profiler di V8 e al 72,2% con il registro esatto, sopra la soglia del 70%. Dettagli in [`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md). **Data:** 12 novembre 2026. **Piano:** [`docs/plans/2026-11-12-passo-dinamico.md`](../plans/2026-11-12-passo-dinamico.md).

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
2. Il container riceve una copia usa e getta del perimetro dello snapshot. Ciò che Git ignora non entra, quindi nemmeno i file di segreti ignorati. Il progetto non viene scritto.
3. Durante l'esecuzione la rete è chiusa. Tempo, memoria e numero di processi hanno un limite. Nessuna variabile d'ambiente dell'host passa al container.
4. Ogni esecuzione registra comando, immagine, durata ed esito.
5. Senza un motore di container l'operazione dichiara la lacuna, con la causa e il rimedio. Non ripiega mai su un'esecuzione sull'host.

### 3. Motore di container

- Daodan parla la Docker Engine API attraverso la riga di comando compatibile (`run`, `cp`, `rm`). Non dipende da un prodotto: un motore si sostituisce senza toccare il resto.
- Daodan porta il proprio motore: scarica Kiri a versione fissata nella cartella condivisa, con il checksum verificato, come ogni altro motore (requisito 12 della spec del motore), e lo usa senza interfaccia. L'utente non installa nulla. Daodan non esegue l'installer di Kiri, che cambia `PATH`, configurazione di Docker e avvio automatico dell'utente, e non modifica un motore già installato.
- Un motore si adotta solo se è attivo e supportato: licenza che consente la ridistribuzione, repository non archiviato, commit e release nell'ultimo anno. Il controllo si ripete a ogni cambio della versione fissata.
- Su Windows Kiri gira dentro WSL 2: Daodan importa una distribuzione propria nella sua cartella e parla al motore attraverso `wsl.exe`, senza l'applicazione di Kiri per Windows. Dove WSL 2 non è attivo serve un amministratore, una volta: Daodan dichiara la lacuna con il rimedio.

Motori controllati il 12 novembre 2026 sui loro repository:

| Motore | Isolamento | Windows | Licenza e stato | Esito |
| --- | --- | --- | --- | --- |
| Kiri 0.2.0 (`libracoder/kiri`) | Una piccola VM Linux; su Linux direttamente sul kernel | WSL 2 | Apache 2.0; repository creato il 2 novembre 2026, release del 10 novembre | Scelto: il più leggero, parla la Docker Engine API. La versione fissata copre la sua giovane età |
| Podman | Container | WSL 2 | Apache 2.0, maturo | Sostituto, stessa API |
| microsandbox 0.7.14 | Micro-VM | Con WHP attivo | Apache 2.0, dichiarato beta | Scartato: API propria |
| sandbox-runtime 0.0.82 | Nessuna VM: limiti del sistema operativo | Dichiarato alpha: utente locale e filtri di rete per tutta la macchina | Apache 2.0 | Scartato su Windows |

Pesi di Kiri 0.2.0: installer per Windows 58 MB, il solo motore per Linux (`kiri-lite`) 2,4 MB, macOS 47-57 MB. Dentro WSL il motore sono due file, 8 MB in tutto; l'applicazione per Windows aggiunge un ponte di 6,8 MB e 71 MB di WebView2, che a Daodan non servono.

### 4. Ambiente in due tempi

1. **Preparazione.** Nel container si installano i pacchetti dichiarati dal progetto. La rete è aperta solo verso i registri dei pacchetti. Gli script di installazione possono girare: restano nel container.
2. **Esecuzione.** I test girano con la rete chiusa.

L'ambiente del passo 2 resta com'è: lì nessuno script gira.

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

Operazione e fatti osservati sono gli stessi per ogni linguaggio; cambiano l'immagine, la preparazione e il registro delle chiamate. Un registro si adotta solo se fa parte del runtime o della sua toolchain e riporta chiamante e chiamato; quello a campioni perde le chiamate brevi.

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
- La preparazione costa tempo e spazio a ogni progetto: installazione dei pacchetti e immagine del runtime.

## Prova

Parametri e soglie in [`benchmarks/call-provenance`](../../benchmarks/call-provenance/README.md), scritti prima di ogni misura.

1. **Isolamento.** Dal container una richiesta di rete fallisce, una scrittura nel progetto è rifiutata e sull'host non compare nessun file.
2. **Copertura.** Sugli stessi casi del passo 2: risolte su risolvibili per linguaggio, con e senza gli archi osservati; quante posizioni senza risposta ricevono una destinazione; quanti archi osservati contraddicono un arco provato.
3. **Costo.** Durata di preparazione ed esecuzione, RAM di picco, spazio su disco.
4. **Ambiente per il passo 2.** Su un caso Gradle e su uno Rust: risolte su risolvibili con e senza i dati preparati nel container.
5. **Motore proprio.** Su una macchina senza Kiri: Daodan scarica il motore ed esegue un comando in un container senza aprire finestre. `PATH`, configurazione e contesto di Docker e avvio automatico dell'utente restano invariati; fuori dalla cartella di Daodan resta solo la registrazione della distribuzione WSL.

## Da decidere

- Quale registro adottare per ogni linguaggio (sezione 7). Il profiler di V8 dà coppie di funzioni senza la riga: la chiamata si ritrova dal nome, e due chiamate omonime nella stessa funzione restano ambigue. Su tududi vede il 35% delle chiamate senza risposta che stanno in file eseguiti. Il registro esatto (`benchmarks/call-provenance/dynamic_record.js`) le registra tutte e porta la copertura al 72,2%.
- Se il motore del passo 2 di un linguaggio gira dentro il container quando deve eseguire codice del progetto, come per le macro procedurali di Rust.
- Come convivono il motore di Daodan e un Kiri dell'utente. Kiri 0.2.0 rifiuta un secondo motore («another Kiri engine is running on this machine»): provato nella stessa distribuzione WSL, non tra due distribuzioni.
- Quale comando esegue i test e come si avviano i servizi che richiedono.
- Quanto vale un arco osservato dopo una modifica al file del chiamante o della destinazione.
- Come si accende il passo: un parametro del run o una domanda al primo uso.
- Se misurare accanto un motore statico per programmi interi. Jelly (`cs-au-dk/jelly`, BSD 3-clause, 0.13.0 dell'11 maggio 2026) copre anche il codice che i test non eseguono; il suo modo dinamico dipende da NodeProf, fermo dal 2023.

**Per modificare questa spec:** un requisito in più solo per un'esigenza obbligatoria o un esito sbagliato riproducibile.
