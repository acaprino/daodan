# Risoluzione delle chiamate: motore di default e metrica

Data: 8 novembre 2026.

**Stato:** applicata in `plugins/codebase-map`, non ancora committata. Misurata su Daodan stesso. I requisiti 23 e 24 sono applicati. La copertura dipende dalle prove fornite dal motore; i benchmark completi dei progetti vanno rimisurati.

**Collocazione:** `resolve_edges.py` (motori, passaggio, stato dello store, rapporto), `languages/semantic.py` (posizione del nome delle dichiarazioni), `edge_view.py` (vista degli archi), `snapshot.py write` e `mcp_service.py` (avvio con lo snapshot); riferimenti `docs/plugins/codebase-map.md` (sezione Risolvibilità), `snapshot.md`, `mcp.md`, `evidence.md`.

## Problema

Il grafo delle chiamate nasceva dal solo risolutore lessicale di `resolution.py`, che lega un binding unico e non inferisce tipi. Il passaggio con motore (`resolve_edges.py --engine jedi`) esisteva ma nessun flusso lo avviava. Esito sul run `daodan-lite-20261107-2`: 3.927 risolte su 27.187 chiamate, riportate come "14%". Il denominatore contava anche le chiamate che nessun risolutore può portare a un simbolo del progetto. La tabella per insieme è in `docs/plugins/codebase-map.md`, sezione Risolvibilità.

## Requisiti

1. **Il passaggio motore è uno store derivato dello snapshot**, come l'indice lessicale e il grafo dei moduli: lo avviano `snapshot.py write` e `codebase_map_create_run`, lo riavvia `codebase_map_index` quando non è fresco. `--no-engine` e `engine=false` lo saltano; il run registra la scelta e nessuna riparazione la scavalca.
2. **Il passaggio non blocca.** Parte come processo staccato e scrive accanto al manifest `engine-edges.sqlite`, `engine-report.json` e `engine-pass.log`. Lo stato (`running`, `fresh`, `sampled`, `stale`, `failed`, `unavailable`, `stopped`, `off`) compare nello stato del run e nella vista degli archi, complessivo e per linguaggio in `languages`; i consumatori leggono lo store appena esiste, senza parametri.
3. **Stesso parser dello snapshot.** Ogni motore gira in uno stage con un ambiente `uv` suo: la stessa versione minore di Python, i requisiti del motore e le versioni esatte dei pacchetti di parsing installati (`snapshot.PARSER_PACKAGES`), così l'impronta del parser coincide e l'ambiente vive quanto lo stage. Due motori non condividono l'ambiente, perché i requisiti di uno possono cambiare la versione dell'altro (multilspy fissa una versione più vecchia di Jedi). Senza `uv` lo stage usa l'interprete corrente se importa il motore; senza entrambi il linguaggio è `unavailable` con la riga di installazione. Un processo figlio dell'interprete di `uv run` non basta: `uv` cancella quell'ambiente all'uscita del comando e Jedi fallisce con `InvalidPythonEnvironment`.
4. **I nomi del progetto danno priorità alle richieste, non provano la provenienza.** Dopo i file modificati, il passaggio privilegia i nomi di funzioni, metodi, classi e import del progetto; interroga anche gli altri nomi. Solo i builtin già riconosciuti sono esclusi prima del motore. I callee dinamici restano nel denominatore con la lacuna dichiarata.
5. **La copertura si legge come risolte su risolvibili.** `external` = builtin + definizioni esterne trovate dal motore; `resolvable` = chiamate − `external`; `resolved` = lessicali + archi confermati. Il rapporto sta in `edge_view.coverage.resolution` e nello stato del motore, con i conteggi assoluti, la quota non ancora chiesta (`unasked`) e la ripartizione per linguaggio, dove `engine` è nullo per un linguaggio che nessun passaggio copre.
6. **Si verificano i sorgenti che il motore legge.** L'hash si controlla prima e dopo l'inferenza sui file dei linguaggi del motore; un documento modificato durante il passaggio non lo invalida. Ogni file dell'inventario resta protetto come destinazione.
7. **Un run fermato ferma il suo passaggio.** `codebase_map_stop` termina l'albero dei processi, stage e language server compresi, e registra `stopped`; nessuna riparazione lo riavvia, solo un nuovo snapshot.
8. **Nessuna regola nuova in `resolution.py`.** Ciò che il risolutore lessicale non prova lo prova il motore.
9. **Il membro di un valore calcolato conserva il suo nome.** `Path(__file__).resolve()` si registra come `(expr).resolve`, come già fanno gli adattatori tree-sitter: il nome permette di individuare la posizione da chiedere al motore. Prima di questa regola 2.195 chiamate restavano nel denominatore senza poter essere chieste.
10. **Jedi vede le cartelle che il progetto mette su `sys.path`.** Un `import snapshot` che lo snapshot non sa collocare, da un test o da uno script, è come un file raggiunge uno strumento dopo averne inserito la cartella in `sys.path`. Se un solo modulo Python dell'inventario ha quel nome, la sua cartella entra nei percorsi di Jedi, dopo quelli dell'ambiente: un modulo standard o installato con lo stesso nome vince comunque. I nomi della libreria standard non aggiungono cartelle; il report del passaggio le elenca in `import_roots`.

11. **Un motore per ogni linguaggio analizzato, uno alla volta.** Il passaggio esegue gli stage in sequenza e salta i linguaggi già `fresh` nello store. Prima di ogni stage controlla la memoria libera (almeno 2 GB); dopo uno stage finito per esaurimento della memoria non ne avvia altri. Un language server ha memoria e thread limitati. Lo store tiene una voce per linguaggio, con il motore che l'ha scritta, e uno stage sostituisce solo le voci e gli archi dei propri linguaggi.
12. **Daodan scarica da sé ciò che serve al motore, senza chiedere.** Motore, runtime e librerie del progetto finiscono in una cartella condivisa fra i progetti (`%LOCALAPPDATA%\Daodan`, `$XDG_CACHE_HOME/daodan`), annunciati da una riga del log, e ciascuno si scarica una volta sola per la macchina, verificato con il suo checksum. Le librerie si leggono dai file di build senza eseguirli: nessuna build, nessun import di build (Maven, Gradle), nessuno script del progetto, nessuna scrittura nel progetto. Go si scarica alla versione fissata, con il checksum del sito ufficiale, e gopls si compila con quel Go; per Rust cargo, rustc e i sorgenti della libreria standard si scaricano dal manifest della release se quelli sul PATH non hanno i sorgenti. Un runtime che Daodan non sa ancora scaricare (Node.js, .NET SDK) rende il linguaggio `unavailable`, con la causa e la riga di installazione, mai `failed`. Una libreria si scarica solo se cambia una misura. Per Python la cambia dal requisito 23: un nome che il progetto non dichiara resta da risolvere finché il motore non lo prova esterno, e senza i pacchetti il motore non risponde (polar `ee8e1c0`: 44.192 posizioni senza risposta). Daodan legge i pacchetti dichiarati da `uv.lock`, `pyproject.toml` e `requirements*.txt` dello snapshot e li installa una volta in un ambiente della cartella condivisa, da soli wheel: nessuno script di build e nessun codice del progetto. Installazioni editabili, percorsi locali e URL restano fuori. Sotto 3 GB liberi l'ambiente non si crea e il log lo dice. Dopo l'installazione il passaggio lavora senza rete: uv parte offline quando l'ambiente dello stage è già nella sua cache, e un motore che all'avvio contatta servizi esterni si configura per non farlo. Si verifica con le connessioni di rete dell'albero dei processi durante un passaggio reale.
13. **Le posizioni si convertono in modo esplicito.** Al confine del motore la colonna è in byte UTF-8, l'unità dello snapshot; ogni motore converte nella propria (Jedi in code point, LSP in unità UTF-16, SCIP nella codifica che il documento dichiara) e riconverte la risposta. Un byte dentro un carattere non è una posizione.
14. **L'arco arriva dove il motore nomina la dichiarazione.** La risposta è la posizione di un nome; la dichiarazione dello snapshot che ha il nome in quella posizione dà identità e `type` dell'arco. Gli adattatori tree-sitter registrano la posizione del nome (`name_span`) e quella delle firme di overload dello stesso corpo (`signature_spans`); per Python la si ricava dai token del sorgente verificato. Una posizione che nomina due dichiarazioni è ambigua. Una risposta che non è un file del progetto (un archivio, una classe compilata) è esterna. Una risposta su una variabile, un parametro o una proprietà non callable indica dove il callable è tenuto, non il bersaglio: accanto a un callable non conta, da sola non fa arco. Un costruttore nomina la sua classe.
15. **Il callee di un adattatore tree-sitter finisce sul suo nome.** Lo span va dal ricevitore al nome, mai sugli argomenti o sui type arguments; il membro di un valore calcolato conserva il suo nome in ogni linguaggio (`res.status(500).render()` registra `(expr).render`, `make().run()` registra `(expr).run`, come il requisito 9 per Python).
16. **Un contratto è una dichiarazione.** I membri callable di un'interfaccia o di un tipo (firma di metodo, proprietà con tipo funzione o con call signature, call e construct signature) sono dichiarazioni `method` marcate `contract`, mai binding lessicali, come un metodo di un Protocol Python. Una proprietà non callable è una `property`. Un arco su un contratto è vero e non dice quale implementazione gira. Lo stesso vale per un metodo di interfaccia Go, per la firma senza corpo di un trait Rust e per una variante di enum, che `Variante(x)` costruisce.
17. **Vue e Svelte si chiedono al motore di TypeScript.** Il motore riceve un documento virtuale con i soli blocchi script agli stessi offset in byte dello snapshot, quindi una posizione vale in entrambi.
18. **Al motore si chiede solo ciò che può essere cambiato.** Una risposta resta valida finché non cambiano il suo file, i file che quel file importa (anche in modo transitivo e attraverso `sys.path`) e i file del progetto in cui la risposta punta, sotto lo stesso contesto: motore e versione, ambienti, target, impronta del parser e versione del risolutore. Le risposte vivono in `engine-answers.sqlite`, accanto allo store delle schede, con una generazione per file e un contesto per motore. Un passaggio che non ha niente da chiedere non avvia il motore; un dry run chiede tutto e non scrive.
19. **Prima le posizioni che valgono di più.** I file modificati o nuovi rispetto alla cache vengono prima di quelli cambiati solo nelle dipendenze; a parità decide il rango del file (PageRank), poi la posizione.
20. **Il passaggio pubblica mentre lavora.** Lo store esce subito con le risposte riusate, poi ogni 30 secondi. La voce del linguaggio è `partial`, e lo stato riporta `answered` su `population`. Un passaggio fermato o fallito lascia ciò che ha provato, e il successivo riprende da lì.
21. **Il server riceve il testo esatto del file, fine riga comprese.** Un server legge da disco i file chiusi e dal client quelli aperti: se il client normalizza CRLF in LF, ogni riga sposta le risposte di un carattere in più (su javapoet 192 risposte cadevano su posizioni che non nominano dichiarazioni).
22. **Il progetto si descrive al motore, non si importa.** Un motore che costruisce il modello del progetto dalla build lo riceve da Daodan come descrizione scritta fuori dal repository: le radici dei pacchetti come cartelle sorgente e le librerie risolte come classpath (per JDT LS un progetto Eclipse in una cartella temporanea). Un motore che cerca le librerie solo nelle cartelle sopra un file (TypeScript e `node_modules`) apre uno specchio del progetto in una cartella temporanea: un collegamento per cartella, una copia per file di primo livello e le librerie collegate dalla cartella condivisa; la rimozione dello specchio non entra mai nei collegamenti. Anche cargo e Go lavorano in uno specchio, con la cartella di destinazione in una cartella temporanea: un `Cargo.lock` o un `go.sum` mancante si scrive nello specchio e mai nel progetto.

24. **L'ambiente del progetto si sceglie con un parametro, e per default lo prepara Daodan.** `environment` su `codebase_map_index` e `--environment` sulla riga di comando: omesso o `auto` usa l'ambiente del progetto (`.venv`, `venv`, `VIRTUAL_ENV`) e, se manca, quello che Daodan costruisce (requisito 12); un percorso usa quell'ambiente; `none` non ne usa. Per JavaScript e TypeScript i pacchetti si installano per ogni cartella del progetto con un suo `package.json` e senza `node_modules`, non solo per la radice; i membri di un workspace li serve la sua radice. Un pacchetto preso da un percorso locale (`file:`, `link:`, `workspace:`) è codice del progetto: si toglie dalla copia del manifest, altrimenti l'installazione fallisce per tutti gli altri. Lo specchio riceve un collegamento a `node_modules` anche sotto il primo livello, in una cartella reale dello specchio e mai nel progetto.

## Provenienza della funzione chiamata

**Stato:** criterio comune e interrogazione dei binding applicati. Una risposta che torna sullo stesso binding resta non risolta. Il compilatore TypeScript 5.9.3 è verificato su provider esterno e callback interna; il passaggio completo di Phazly non è stato rieseguito.

**Caso riproducibile.** `HomonymHolderTests` in `tests/test_codebase_map_resolve_edges.py` distingue le risposte sulla sola variabile dalle risposte che identificano anche la funzione contenuta, in TypeScript e Python. La prima non prova una destinazione esterna: il vecchio fallimento atteso chiedeva una conclusione non ricavabile dalle risposte dello stub.

23. **Una chiamata si classifica per la provenienza della funzione chiamata, mai per il nome.** Il criterio vale per ogni linguaggio. Gli adattatori dei linguaggi e i motori forniscono le informazioni necessarie, senza eccezioni per singole librerie o singoli nomi.
    1. Il riferimento è quello preciso della chiamata, nel suo file e nel suo scope: due nomi uguali non provano un collegamento.
    2. La funzione si segue attraverso variabili, alias, proprietà, parametri e valori restituiti. Né la posizione della variabile, né la libreria chiamata per riempirla, stabiliscono da sole dove la funzione è implementata: una libreria può restituire una funzione del progetto.
    3. L'esito segue le prove:

       | Evidenza | Esito |
       | --- | --- |
       | Una sola destinazione interna, identificata senza ambiguità | Risolta |
       | Tutte le destinazioni possibili sono provate esterne | Esterna |
       | Provenienza incompleta, ambigua o decisa a runtime | Non risolta |

    4. Il filtro per nome (requisito 4) decide solo cosa chiedere prima al motore, non cosa esce dal denominatore. Anche «nome assente dal progetto, quindi esterna» va superato: una funzione interna si può chiamare con un alias.

    Il passaggio comune interroga il motore sulla posizione esatta dei binding, parametri e proprietà. Deduplica le destinazioni, memorizza gli esiti per chiamata e limita la ricerca a 64 richieste e 32 livelli; cicli, errori e limiti mantengono l’incertezza. La cache include anche i file intermedi. Un motore che offre soltanto navigazione alla dichiarazione può non fornire nuove prove; non si inferisce l’origine dalla libreria produttrice.

    «Funziona sempre» significa classificazioni giustificate e incertezza dichiarata. Una destinazione decisa a runtime resta non risolta.

## Misura con il motore

Snapshot di HEAD (`42a63a9ac`, 527 file, 27.586 chiamate Python), Jedi 0.20.1 in modalità project-only, un processo.

| | Solo lessicale | Jedi | Jedi con le cartelle di `sys.path` |
|---|---|---|---|
| Esterne | 15.833 | 18.424 | 18.503 |
| Risolvibili | 11.753 | 9.162 | 9.083 |
| Risolte | 3.968 | 6.212 | 7.399 |
| **Risolte su risolvibili** | **33,8%** | **67,8%** | **81,5%** |
| Durata del passaggio | 0 | 9 min 16 s | 12 min 35 s |

L'ultima colonna è il comportamento predefinito, misurato con il passaggio staccato del prodotto: 7.782 posizioni chieste, media 95,3 ms, p95 321,9 ms. Restano 1.681 posizioni senza risposta: 1.665 non risolte e 16 ambigue. Lo stesso comando in primo piano, con il computer carico, ha dato 49 errori interni di Jedi e 7.399 su 9.112.

### TypeScript e JavaScript

Scelta misurata fra due strade, sullo stesso snapshot e con la stessa valutazione degli archi: **A**, typescript-language-server 4.3.3 (con TypeScript 5.5.4) interrogato per posizione attraverso multilspy 0.1.1; **B**, un indice di scip-typescript 0.6.1 letto da `ScipEngine`. Progetti: ky `3541888` (TypeScript, 98 file) ed express `43fca52` (JavaScript, 142 file), senza dipendenze installate salvo dove indicato.

| | ky, A | ky, B | express, A | express, B |
|---|---|---|---|---|
| Archi confermati (ky: campione 1 su 3; express: tutto) | 82 | 30 | 163 | 107 |
| Compila o installa dipendenze | no | sì: senza `npm install` fallisce (`TS6053`) | no | no |
| File coperti | tutti | solo quelli di un tsconfig: `test/` resta fuori | tutti | tutti |
| Durata | 47 s | 2,6 s di indice | 21 s | 5,9 s di indice |
| RAM di picco | 1.066 MB | 258 MB | 651 MB | 322 MB |

Vince A sul primo e sul secondo criterio. Il comportamento predefinito, misurato con lo stage del prodotto su tutta la popolazione:

| | ky, lessicale | ky, motore | express, lessicale | express, motore |
|---|---|---|---|---|
| Esterne | 8.503 | 10.847 | 9.195 | 9.205 |
| Risolvibili | 6.113 | 3.769 | 2.877 | 2.867 |
| Risolte | 791 | 1.631 | 207 | 385 |
| **Risolte su risolvibili** | **12,9%** | **43,3%** | **7,2%** | **13,4%** |
| Con i contratti (requisito 16) | | **90,9%** (3.911 su 4.302), 45 s | | 13,4% |
| Durata dello stage | 0 | 52 s | 0 | 24 s |
| RAM di picco | | 1.294 MB | | 675 MB |

Con i contratti su ky le posizioni chieste salgono a 5.999, perché i nomi dei membri dei tipi entrano fra quelli del progetto; restano 264 callee dinamici (`obj[key]()`), 81 posizioni senza risposta e 46 fra non simboli e ambigue. Senza contratti: 1.713 risposte cadevano su membri di tipi che lo snapshot non dichiarava. Le misure di ky sono con `node_modules` installato. Senza, le risolte su risolvibili scendono al 59,1% (3.908 su 6.615): 1.500 chiamate a librerie cadono su posizioni che il progetto non dichiara e 941 restano senza risposta. Con le librerie installate da Daodan nella cartella condivisa (`npm ci` o `npm install` con `--ignore-scripts` sui soli manifest, 122 MB) e lo specchio del requisito 22 il risultato torna identico: 90,9% (3.911 su 4.302), 170 s compresa l'installazione, nessun file scritto nel progetto. Posizioni chieste prima dei contratti: 5.058 su ky (media 8,4 ms, p95 24,2 ms) e 2.652 su express (media 7,1 ms, p95 29,0 ms). Su express 2.424 posizioni restano senza risposta: sono metodi di `req`, `res` e `app`, oggetti che Express costruisce a runtime con `Object.create` e mixin, che nessuna analisi statica tipizza. Con le dipendenze installate le risolte restano 385 e 143 chiamate passano fra le esterne (14,1%). Il motore occupa 24 MB su disco nella cartella condivisa, più 12 MB di ambiente `uv`.

### Java

Scelta fra due strade su javapoet `b9017a9` (Maven, 39 file Java): **A**, Eclipse JDT LS 1.46.0 con il runtime Java che la sua release porta, interrogato per posizione; **B**, scip-java 0.12.3. B su Windows non parte, perché lancia `mvn` senza estensione (`CreateProcess error=2`); in ogni caso richiede Maven, scarica le dipendenze e compila il progetto. Vince A.

Il server vede il progetto attraverso un progetto Eclipse che Daodan scrive in una cartella temporanea (requisito 22): le radici dei pacchetti come cartelle sorgente collegate, e come classpath le librerie lette da `pom.xml`, file Gradle e version catalog e risolte da Coursier 2.1.24 nella cartella condivisa. JDT LS rifiuta il progetto invisibile accanto a un `pom.xml` (`isPartOfMatureProject`), e l'import Maven offline non rispondeva a nessuna posizione.

| javapoet | Solo lessicale | JDT LS senza librerie | JDT LS con le librerie |
|---|---|---|---|
| Esterne | 2.471 | 2.900 | 3.569 |
| Risolvibili | 3.972 | 3.543 | 2.874 |
| Risolte | 289 | 2.865 | 2.864 |
| **Risolte su risolvibili** | **7,3%** | **80,9%** | **99,7%** |
| Durata del passaggio | 0 | 64 s | 107 s |
| RAM di picco | | 1.162 MB | 1.094 MB |

Con le librerie le 664 chiamate di Truth e JUnit nei test diventano esterne; restano 10 posizioni senza risposta. Il primo uso scarica Coursier (43 MB) e 22 jar; poi l'elenco risolto si legge da `classpaths/` senza avviare Coursier. Con l'heap a 2 GB lo stage arrivava a 1.814 MB; ora è a 1 GB. Durante un passaggio JDT LS apriva una connessione HTTPS a services.gradle.org: Buildship, che il server avvia anche con l'import Gradle spento, scarica l'elenco delle release di Gradle se non ne trova una cache di meno di un giorno. Con una cache vuota e fresca in `XDG_CACHE_HOME` nessuna connessione lascia la macchina. Il motore occupa 167 MB su disco.

### Kotlin

Motore: la Kotlin Analysis API di JetBrains in modalità standalone (Apache 2.0), cioè la libreria del compilatore che risponde a "dove è dichiarato questo riferimento", senza server e senza licenze da accettare. Daodan la prende da Maven Central come la pubblica KSP (`symbol-processing-aa` 2.3.13), compila al primo uso un risolutore di un centinaio di righe (`engines/KotlinResolver.kt`) con il compilatore Kotlin 2.4.21 e lo avvia come un solo processo JVM con heap a 1,5 GB. La sessione carica i file Kotlin e Java dello snapshot, la JDK del runtime, la libreria standard di Kotlin e le librerie del progetto risolte come per Java. La modalità standalone non è stabile, quindi la versione è fissata. Scartati: kotlin-lsp di JetBrains (1,2 GB, parti chiuse, licenza che vincola chi lo scarica), kotlin-language-server di fwcd (deprecato dal suo autore), scip-kotlin (compila ed è legato a una versione maggiore di Kotlin).

| klaxon `1173bdc` (99 file Kotlin) | Solo lessicale | Analysis API senza librerie | con le librerie |
|---|---|---|---|
| Esterne | 1.192 | 1.354 | 1.527 |
| Risolvibili | 1.241 | 1.079 | 906 |
| Risolte | 311 | 811 | 812 |
| **Risolte su risolvibili** | **25,1%** | **75,2%** | **89,6%** |
| Durata del passaggio (con gli stage di Java e JavaScript) | 0 | 61 s | 45 s |
| RAM di picco | | 535 MB | 587 MB |

Le librerie lette dai file Gradle sono quattro: quelle che gli script calcolano (`listOf("reflect").forEach { kotlin(it) }`) restano invisibili senza eseguirli. Il primo uso scarica 140 MB di jar nella cartella condivisa e compila il risolutore in 16 s; i passaggi successivi non aprono connessioni di rete.

### Rust

Motore: rust-analyzer 2026-11-09 (Apache 2.0 e MIT), il server LSP del progetto Rust, dal binario della release con il suo checksum (40 MB). Legge il progetto con `cargo metadata`, senza compilare: build script e macro procedurali restano spenti, quindi nessun codice del progetto gira e ciò che una macro genera non si vede. Tutte le feature di Cargo sono attive, perché il codice sotto una feature spenta non ha tipi. Daodan usa cargo e rustc sul PATH se la loro sysroot ha i sorgenti della libreria standard; altrimenti scarica cargo, rustc e rust-src 1.99.1 dal manifest di static.rust-lang.org (550 MB, verificati con i suoi sha256). Le dipendenze vanno in `cargo/` nella cartella condivisa, mai nel cargo home dell'utente. Il server apre uno specchio del progetto con la cartella di destinazione in una cartella temporanea e si considera pronto quando dichiara `quiescent`: un documento virtuale non appartiene a nessun crate, quindi non serve da prova. Misurato contro rust-analyzer in modalità SCIP (`rust-analyzer scip`, 13 s, nessuna compilazione): su semver 96,3% contro 98,5%, perché SCIP tratta come esterno ogni simbolo che l'indice non definisce e nasconde le chiamate che non ha saputo risolvere; scelto il server.

| Progetto | Solo lessicale | Senza sorgenti di `std` | Con il motore | Durata | RAM di picco |
|---|---|---|---|---|---|
| semver `280ebcb` (22 file) | 15,7% | 88,8% | **98,5%** (447 su 454) | 22 s | 0,95 GB |
| serde_json `8c535a2` (77 file) | 21,3% | | **92,3%** (1.641 su 1.778) | 27 s | 0,86 GB |

Su serde_json restano 137 posizioni: 99 senza risposta e 38 su cui il motore nomina un'altra dichiarazione, per lo più metodi di trait chiamati su tipi del progetto e chiamate a funzioni generate da macro. Senza le feature attive erano 385; senza varianti di enum come costruttori 1.575 su 1.731. Il primo uso scarica rust-analyzer e, senza una toolchain completa, 550 MB di Rust in 157 s.

### Go

Motore: gopls 0.24.0 (BSD 3-clause) compilato al primo uso con Go 1.27.3 (BSD 3-clause), scaricato dal sito ufficiale con il suo sha256. gopls legge il progetto con `go list`, senza eseguirlo; i moduli si scaricano con `go mod download` nello specchio, nella cartella `go/` condivisa, con `GOTOOLCHAIN=local` e `GOTELEMETRY=off`. Come per Rust, la prova di prontezza è la prima richiesta, perché un documento virtuale non appartiene a nessun pacchetto. Misurato contro scip-go 0.2.9 su chi: 77,8% (948 su 1.218, 13 s, nessuna compilazione) contro 95,9% del server. Il lettore SCIP non leggeva il formato in uso, che scrive l'intervallo in `single_line_range` (campo 8) e `multi_line_range` (campo 9) invece dei tre interi del campo 1: con quel formato scip-go non dava nessun arco, ora li legge.

| Progetto | Solo lessicale | Con il motore | Durata | RAM di picco |
|---|---|---|---|---|
| chi `c64ed7d` (101 file) | 11,1% | **95,9%** (1.014 su 1.057) | 18 s | 0,45 GB |
| cobra `adbc881` (36 file) | 24,8% | **98,7%** (1.626 su 1.648) | 7 s | 0,35 GB |

Su chi restano 43 posizioni: chiamate su un valore di funzione o di interfaccia anonima. Il primo uso scarica Go (79 MB compressi, 236 MB sul disco) e compila gopls (44 MB); il motore e gopls occupano 264 MB e 43 MB.

### Distribuzione del lavoro

ky `3541888`, motore TypeScript, stage del prodotto. Ogni riga parte dalla cache lasciata dalla riga precedente.

| Caso | Chieste | Riusate | Durata | RAM di picco | Risolte su risolvibili |
|---|---|---|---|---|---|
| Primo passaggio | 5.058 | 0 | 49,6 s | 1.320 MB | 43,3% |
| Snapshot invariato | 0 | 5.058 | 2,1 s, motore non avviato | 115 MB | 43,3% |
| Modifica di un test (`test/headers.ts`) | 237 | 4.821 | 8,0 s | 607 MB | 43,3% |
| Modifica di `source/utils/merge.ts`, importato quasi ovunque | 4.902 | 156 | 38,5 s | 1.235 MB | 43,3% |

In tutti i casi gli archi confermati restano 840. Una modifica a un file centrale invalida quasi tutto per costruzione: il tipo inferito di ciò che il file esporta arriva a chi lo importa, anche in modo transitivo.

## Fuori perimetro

- Motore per C#, da fare: il parsing e il risolutore lessicale ci sono; il motore si sceglie misurando un server LSP contro un indice SCIP.
- C e C++: lo snapshot non li analizza, quindi non hanno simboli né chiamate.
- Le 154 chiamate `self.metodo()` che la regola lessicale dovrebbe già risolvere (`doc_review.py:427`).
- Un passaggio staccato su quattro si è chiuso dopo circa 6 minuti senza store e senza log; lo stesso comando in primo piano è terminato con successo. Lo stato riporta `failed` e `codebase_map_index` lo riavvia; il comando ora parte con `-X faulthandler` per lasciare nel log il traceback di un crash.

## Verifica

`tests/test_codebase_map_resolve_edges.py` (classe `ResolvabilityTests`: denominatore, filtro, stato dello store, avvio e fallimento, comando `uv`, ripartizione per linguaggio; `MultiLanguageTests`: posizione dei nomi e overload, membro di un valore calcolato, voci per linguaggio, un motore alla volta, memoria; `TypeScriptMirrorTests`: specchio e sua rimozione, solo i manifest a npm, script spenti; `DistributionTests`: riuso, invalidazione per import, ordine, pubblicazione e ripresa, dry run, digest; `JavaEngineTests`: nessuna build, nessun download; `JvmLibraryTests`: coordinate da pom, Gradle e catalog, classpath risolto una volta, progetto Eclipse esterno, fine riga esatte; `KotlinEngineTests`: jar riusati da `~/.m2` o scaricati con verifica, perimetro dello snapshot; `RustGoContractTests`: metodi di interfaccia Go, firme di trait e varianti di enum Rust come contratti; `ScipTypedRangeTests`: intervalli tipizzati dello schema SCIP corrente; `NativeToolchainTests`: Rust sul PATH riusato, cargo, rustc e rust-src scaricati con checksum, download rifiutato, Go scompattato una volta, specchio e scritture fuori dal progetto; `PositionUnitTests`: conversioni), `tests/test_xray_semantic_syntax.py` (`CalleeSpanTests`: span del callee e posizione dei nomi in Java), `tests/test_codebase_map_mcp.py` (avvio con il run, motore assente, stop), `tests/test_codebase_map_mcp_wire.py` (passaggio reale attraverso il protocollo MCP, Python, TypeScript, Java, Go e Rust).

**Per modificare questa spec:** un requisito in più solo per un'esigenza obbligatoria o un esito sbagliato riproducibile.
