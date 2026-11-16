# Registro dei difetti dal 13 novembre 2026

Ogni difetto e buco trovato nel plugin codebase-map dal 13 novembre 2026, con la causa, il rimedio e la prova. Ogni campo viene dal commit, dal risultato di un giro o dal codice. Una scheda si aggiunge con il commit che corregge o dichiara il difetto.

Convenzioni:

- Gli id non cambiano: una scheda nuova prende il numero libero successivo e sta nella sua area.
- I percorsi `scripts/…` stanno sotto `plugins/codebase-map/skills/map/`.
- I giri della pipeline, tutti del 16 novembre 2026, stanno in `benchmarks/project-model/results/pipeline/2026-11-16-<giro>.json`, con il rapporto `.report.md` accanto:
  - `fixtures`: 104 progetti in miniatura (`68d8f4c59`);
  - `real-3`: chi, javapoet e tududi (`7532ed2e7`);
  - `giro-2`: i 15 repository veri restanti e 12 fixture corrette (`b41e0d6e8`);
  - `finale`: 122 casi, sul codice fino a `492a7b212` (`ee1e83fc8`);
  - `java-versions`: le 18 `jvm-ver-*`, sul codice a `68a846a4a` (`347bc1403`);
  - `conferma`: 32 casi (`828b5413b`);
  - `jvm-otel-android`: otel-demo, jvm-android-app-lib e mix-poly-firebase, sull'albero di lavoro con il codice poi committato in `39805f5e7`;
  - `jvm-kotlinconf`: kotlinconf, sull'albero di lavoro con il codice poi committato in `22dca6da8`.
- I repository veri sono fissati a un commit in `benchmarks/project-model/fixtures/<caso>/source.json`:
  - chi `c64ed7d6635f`, javapoet `b9017a9503b7`, klaxon `1173bdc568a6`, python-semver `b6e83e3e40d3`, semver `280ebcb6edac`, tinyxml2 `9148bdf719e9`, tududi `71da9d7b34df`, zlib `51b7f2abdade`;
  - fastapi `aabb90126964`, hoppscotch `55908a76a1d0`, jhipster-sample `6b000b5d23a3`, kotlinconf `146e891c150c`, memos `509e41bd1a1b`;
  - eShop `913acea66708`, otel-demo `b825c7c25726`, petclinic-microservices `e8b747ab5227`, robot-shop `55292e2199f2`, voting-app `63e9150ca17a`.
- Stato:
  - risolto;
  - aperto, con chi ci lavora dove qualcuno ci lavora;
  - buco dichiarato: un limite che il risultato dice, con il nome della lacuna.
- Verifica:
  - «solo test»: lo confermano solo le suite, che dal commit `233618aa1` girano su Modal;
  - «da verificare»: nessun commit o risultato lo prova ancora;
  - «in stage»: il lavoro è nell'indice di git, non ancora in un commit.
- Il commit `b6f276fee` e il benchmark `f63ed542d` sono di senior-review e restano fuori. I commit feat che non correggono nulla sono elencati in fondo.

## Indice

238 schede: 177 risolte, 22 aperte, 39 buchi dichiarati.

### Pre-mappa, snapshot e preparazione

64 schede: 58 risolto, 0 aperto, 6 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit |
| --- | --- | --- | --- | --- |
| D-001 | Due build system nella stessa cartella fusi in un'unità | corpus della pre-mappa | risolto | `708eae48f` |
| D-002 | Go: requisiti indiretti letti e moduli legati fuori da un workspace | corpus della pre-mappa | risolto | `708eae48f` |
| D-003 | Maven: dipendenze non lette come gruppo:artefatto e profili taciuti | corpus della pre-mappa | risolto | `708eae48f` |
| D-004 | Un glob di workspace crea un'unità per cartella | corpus della pre-mappa | risolto | `708eae48f` |
| D-005 | Un bersaglio ambiguo scelto invece che dichiarato | corpus della pre-mappa | risolto | `708eae48f` |
| D-006 | Gruppi di sviluppo di pyproject non letti | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-007 | setup.cfg non letto | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-008 | Import map di Deno non lette | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-009 | angular.json non letto | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-010 | Soluzioni .NET fuori dalla radice non lette | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-011 | Sottoprogetti sbt non letti | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-012 | Umbrella di Mix non letto | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-013 | Dipendenze `file:` di npm non lette dal lettore dei moduli | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-014 | Rinomina e tabelle target di Cargo non lette | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-015 | Requisiti di piattaforma di Composer e SDK di pub contati come dipendenze | corpus della pre-mappa | risolto | `a04ab36e1` |
| D-016 | Un build incluso contato come membro del workspace | corpus della pre-mappa | risolto | `a04ab36e1`, `9c17c7686` |
| D-017 | Pacchetti locali `file:` di npm senza archi nella pre-mappa | js-local-and-git-deps | risolto | `db45bcc93` |
| D-018 | Una dipendenza di un file centrale data all'unità più vicina | eShop e il corpus della pre-mappa | risolto | `de353d251` |
| D-019 | Un arco fra unità contato anche come dipendenza | corpus della pre-mappa | risolto | `99112d0b9` |
| D-020 | Go: un arco fra moduli senza replace né go.work | corpus della pre-mappa | risolto | `99112d0b9` |
| D-021 | Una versione scritta in un file centrale non completava la voce dell'unità | corpus della pre-mappa | risolto | `99112d0b9` |
| D-022 | Un vincolo dichiarato contato come pacchetto | corpus della pre-mappa | risolto | `99112d0b9` |
| D-023 | Script, task, replace e import verso un percorso contati come pacchetti | corpus della pre-mappa | risolto | `99112d0b9` |
| D-024 | Una toolchain diversa da quella che il file scrive | corpus della pre-mappa | risolto | `99112d0b9` |
| D-025 | Il wrapper Maven dava sé stesso invece di Maven | corpus della pre-mappa | risolto | `99112d0b9` |
| D-026 | POM genitore e BOM importato senza scope parent e bom | corpus della pre-mappa | risolto | `99112d0b9` |
| D-027 | Uno scope dato alle dipendenze di Gradle | corpus della pre-mappa | risolto | `99112d0b9` |
| D-028 | Un file di pip-compile contato come dichiarazione | corpus della pre-mappa | risolto | `99112d0b9` |
| D-029 | Pacchetti di Bazel, Helm, Terraform, Conan e Deno non dichiarati | corpus della pre-mappa | risolto | `99112d0b9` |
| D-030 | Cargo e SwiftPM: il pacchetto con un nome diverso da quello del build tool | corpus della pre-mappa | risolto | `99112d0b9` |
| D-031 | Un collegamento simbolico a un file del progetto: «UNIQUE constraint failed: files.path» | python-semver (`b6e83e3e40d3`) | risolto | `ea92f3fed` |
| D-032 | Un collegamento verso l'esterno portava dentro un file di fuori | snapshot | risolto | `ea92f3fed` |
| D-033 | Un collegamento rotto spariva senza traccia | snapshot | risolto | `ea92f3fed` |
| D-034 | Grammatiche scaricate da GitHub al primo uso, senza versione fissata | snapshot | risolto | `d6545b074` |
| D-035 | Senza rete un file passava in silenzio al lettore a espressioni regolari | snapshot | risolto | `d6545b074` |
| D-036 | Grammatiche scelte senza l'architettura del processo | host Windows | risolto | `68e39dcde` |
| D-037 | Grammatiche piazzate fra processi senza sicurezza | parser | risolto | `d94f92470` |
| D-038 | La cartella condivisa di Daodan chiedeva la versione a Windows | host Windows | risolto | `bfdca190b` |
| D-039 | Il sistema e l'architettura chiesti a Windows con il modulo platform | host Windows | risolto | `b5d218801` |
| D-040 | Un rustup vecchio installava per conto di un progetto | host con rustup vecchio | buco dichiarato (Rust `unavailable`) | `b5d218801` |
| D-041 | Cargo, rustc e rust-analyzer installavano nella home dell'utente | host | risolto | `6856a0980` |
| D-042 | uv scaricava interpreti e leggeva la configurazione del progetto | host | risolto | `6856a0980` |
| D-043 | I makefile erano «tipo di file non inventariato» | zlib e tinyxml2 su Kiri | risolto | `c6767743f` |
| D-044 | Android: compileSdk e buildToolsVersion non letti, SDK non installato | jvm-android-app-lib, mix-poly-firebase | risolto | `a633ebd72` |
| D-045 | Go: girava una versione diversa dalla più alta dichiarata | preparazione Go | risolto | `a633ebd72` |
| D-046 | `node:22-alpine` non letto come Node 22 | pre-mappa delle immagini | risolto | `a633ebd72` |
| D-047 | Gli errori di uv troncati | preparazione Python | risolto | `a633ebd72` |
| D-048 | Dipendenze git di Python senza l'host né git | preparazione Python | risolto | `a633ebd72` |
| D-049 | I registri dichiarati assenti dalla pre-mappa | pre-mappa | risolto | `a633ebd72` |
| D-050 | Gradle avrebbe scaricato i JDK delle toolchain | build composte con toolchain 17 e 21 | risolto | `a633ebd72` |
| D-051 | pnpm e Yarn: «Cannot find matching keyid» | preparazione Node | risolto | `a94de85fb` |
| D-052 | Preparazione Python senza gli host dichiarati e senza il loro nome | preparazione Python | risolto | `2f0353c03` |
| D-053 | Dipendenze GitHub di npm senza gli host di download | preparazione Node | risolto | `2f0353c03` |
| D-054 | Build JVM senza gli host che il progetto dichiara | javapoet (`b9017a9503b7`) | risolto | `609ca96dd` |
| D-055 | Il modello di Gradle senza i repository dei plugin delle impostazioni | kotlinconf (`146e891c150c`) | risolto | `17babc624` |
| D-056 | Bun dichiarato solo nei workflow non era una toolchain | fastapi (`aabb90126964`) | risolto | `5148e8eb3` |
| D-057 | L'immagine `devcontainers/java:1-21` letta come Java 1 | kotlinconf | risolto | `22dca6da8` |
| D-058 | «Dependency requires at least JVM runtime version 21. This build uses a Java 17 JVM.» | kotlinconf | risolto | `22dca6da8` |
| D-059 | Template ERB, Handlebars, Jinja e Nunjucks fuori dallo snapshot | snapshot | buco dichiarato (`template language | `e15f2ff88` |
| D-060 | Avviso «senza analyzer» per i linguaggi fatti solo di file di build | pre-mappa | risolto | `d14200dce` |
| D-061 | Un profilo Conan che chiede una build dal sorgente | pre-mappa CMake con profili Conan | buco dichiarato (`restore_failed`) | `7b1e9ee9f` |
| D-062 | Senza container le fonti di modello non girano | scansione | buco dichiarato (`model_not_run`) | `8e85b2c1e` |
| D-063 | Un wrapper Gradle o Maven che punta a un host non ufficiale | build JVM | buco dichiarato (`unavailable`) | `f48df5c7d` |
| D-064 | Gradle raggiunge anche il Plugin Portal | perimetro di rete, dopo la revisione indipendente | buco dichiarato (perimetro di rete di Gradle) | `177dcae02` |

### Analizzatori

105 schede: 65 risolto, 14 aperto, 26 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit |
| --- | --- | --- | --- | --- |
| D-065 | Un linguaggio con 0 file indicizzati risultava `fresh` | audit della copertura | risolto | `2bc7c7459` |
| D-066 | I file mancanti di un linguaggio riuscito taciuti | audit della copertura | risolto | `2bc7c7459` |
| D-067 | Un build o un run fallito accanto a uno riuscito spariva | audit della copertura | risolto | `2bc7c7459` |
| D-068 | Un linguaggio letto dallo snapshot senza analyzer non era dichiarato | audit della copertura | risolto | `2bc7c7459` |
| D-069 | Le coppie di linguaggi che si chiamano non erano unite né dichiarate | audit della copertura | buco dichiarato (`not-joined`) | `2bc7c7459` |
| D-070 | La tabella «chi indicizza cosa» della pre-mappa scritta a mano | audit della copertura | risolto | `2bc7c7459` |
| D-071 | Linguaggio senza file con AST, e un linguaggio non elencato `fresh` per difetto | audit della copertura | risolto | `2bc7c7459` |
| D-072 | TypeScript: alias di percorso e membri del workspace non presi dalla pre-mappa | audit della copertura, «stessa famiglia di Kotlin sotto Maven» | risolto | `64edfb930` |
| D-073 | TypeScript: installazione fallita e dipendenza locale scartata taciute | audit della copertura | risolto | `64edfb930` |
| D-074 | Python: cartelle sorgenti e manifest dichiarati non passati a Pyright | audit della copertura | risolto | `64edfb930` |
| D-075 | Python: un file fuori da ogni progetto senza motivo | audit della copertura | risolto | `64edfb930` |
| D-076 | C/C++: MSBuild trattato a parte | audit della copertura | risolto | `64edfb930` |
| D-077 | C/C++: un configure senza compile_commands.json faceva morire lo stadio | audit della copertura | risolto | `64edfb930` |
| D-078 | Rust e Go: un file senza documento non diceva se il run era fallito | audit della copertura | risolto | `64edfb930` |
| D-079 | Go: la regola dei nomi dei file (_GOOS, _GOARCH) non conosciuta | audit della copertura | risolto | `64edfb930` |
| D-080 | Vue e Svelte: un componente con template non dichiarato letto in parte | audit della copertura | risolto | `64edfb930` |
| D-081 | Lo stadio di posizione rispondeva per linguaggi non suoi | audit della copertura | risolto | `64edfb930` |
| D-082 | Markup senza lettore non dichiarato (Razor, JSP, Freemarker, Velocity, XHTML) | audit della copertura | buco dichiarato (markup senza lettore) | `64edfb930` |
| D-083 | Le correzioni degli adattatori Java e Kotlin le usava solo il banco | stadio del grafo | risolto | `d06df0522` |
| D-084 | scip-python: «Cannot find module» | PC di sviluppo | risolto | `faf7a3b22` |
| D-085 | 80 file Python su 211 senza documento | il codice di Daodan | risolto | `118689f69` |
| D-086 | scip-python 0.6.8 non parte su Windows | host Windows | risolto | `626ebb3a2` |
| D-087 | phazly: bersagli Python diversi da quelli del passaggio per posizione | phazly | risolto | `09537b2b9` |
| D-088 | Buchi Python senza causa | corpus Python | risolto | `a6156b7a2` |
| D-089 | Kotlin sotto Maven: 0 file su 2 indicizzati | il pilota su 5 casi del driver Modal | risolto | `ea1e2b7d6` |
| D-090 | Java sotto Gradle: aggregazione in avanti e javap sulla cartella sbagliata | build JVM | risolto | `7b1a77e8d` |
| D-091 | Sotto Maven l'indice Java senza il Kotlin dei moduli | Maven misto Java e Kotlin | risolto | `7b1a77e8d` |
| D-092 | Un build JVM che Daodan non esegue (sbt, Bazel) non era nominato | build JVM | buco dichiarato (sbt e Bazel non eseguiti) | `7b1a77e8d` |
| D-093 | Un indice lasciato da un build finito in errore non lo diceva | build JVM | risolto | `7b1a77e8d` |
| D-094 | Java e Kotlin giravano solo alla radice del progetto | robot-shop (`55292e2199f2`), otel-demo (`b825c7c25726`) | risolto | `1dcfba42a` |
| D-095 | Maven e Gradle nella stessa cartella: occorrenze doppie | jvm-java-version-conflict | risolto | `9fe650a3a` |
| D-096 | Una radice con solo settings.gradle.kts non riconosciuta da scip-java | jvm-gradle-kts-catalog-composite | risolto | `9fe650a3a` |
| D-097 | Kotlin presente solo negli script di build dato `failed` | jvm-gradle-kts-catalog-composite, jvm-java-version-conflict, jvm-spring-boot-managed | buco dichiarato («the build's own Kotlin only») | `9fe650a3a` |
| D-098 | File Kotlin che nessun compito di compilazione compila o elenca | jvm-kmp-common-jvm, jvm-kotlin-source-sets, klaxon (`1173bdc568a6`) | buco dichiarato (i motivi citati) | `2bc7c7459` |
| D-099 | javapoet: scip-java 0.14.2 non indicizza Java 8 | javapoet (`b9017a9503b7`) | buco dichiarato (`jdk_unsupported`) | `492a7b212` |
| D-100 | javapoet: il compilerId di Error Prone scavalca il wrapper di javac | javapoet | buco dichiarato (`build_edited`) | `492a7b212` |
| D-101 | Una toolchain Gradle sotto il 17 compilava sul JDK dell'immagine | build Gradle con toolchain 8 e 11 | buco dichiarato (`jdk_unsupported`) | `0997b5d4f` |
| D-102 | Maven con Java 5 e 6: nessun indice | jvm-ver-* | buco dichiarato (`build_edited`, `jdk_unsupported`) | `21b3cb39b` |
| D-103 | Gradle con toolchain 8 e 11, anche con Kotlin accanto: nessun indice | jvm-ver-* | buco dichiarato (`build_edited`) | `21b3cb39b` |
| D-104 | Gradle con livello 6: nessun indice | jvm-ver-* | buco dichiarato (`build_edited`) | `21b3cb39b` |
| D-105 | otel-demo: «Cannot invoke method toPath() on null object» in ad e recommendation | otel-demo (`b825c7c25726`) | risolto | `39805f5e7` |
| D-106 | otel-demo fraud-detection sul JDK 21 di un altro build | otel-demo | risolto | `39805f5e7` |
| D-107 | otel-demo fraud-detection: protos che solo il Dockerfile copia | otel-demo (`b825c7c25726`) | aperto (android-sdk) | `f024ba3a3`, `f04dab9d5` |
| D-108 | Android: classpath dei test unitari non risolti, nessun compito Android | jvm-android-app-lib, mix-poly-firebase | aperto (dynamic-jvm-2) | `39805f5e7` |
| D-109 | Android: build fermo su `google-services.json` mancante | jvm-android-app-lib, mix-poly-firebase | buco dichiarato (`build_input_missing`) | `39805f5e7` |
| D-110 | kotlinconf: «Task with name 'compileKotlinJvm' not found in project ':app:adminApp'» | kotlinconf (`146e891c150c`) | aperto (dynamic-jvm-2) | — |
| D-111 | jhipster: 14 file Java con il documento senza occorrenze | jhipster-sample (`6b000b5d23a3`) | aperto | — |
| D-112 | Un file Java senza documento in due fixture Maven | jvm-maven-multi-bom-profile, jvm-protobuf-generated | aperto | — |
| D-113 | C#: un progetto che Msbuild rifiuta ferma il ripristino intero | zlib (`51b7f2abdade`) | risolto | `73b645531`, `0cdbae9b2` |
| D-114 | C#: 56,1 % di risposta | mix-dotnet-central, eShop (`913acea66708`), otel-demo, voting-app (`63e9150ca17a`) | aperto (csharp-dotnet) | `56e65e114`, `73b645531`, `0cdbae9b2` |
| D-115 | La colonna della riga 1 di un file con il BOM | i casi C# | risolto | `0cdbae9b2` |
| D-116 | C#: nomi del chiamato con argomenti di tipo | eShop | buco dichiarato (`TYPE_ARGUMENTS`) | `73b645531`, `0cdbae9b2` |
| D-117 | C#: nomi del chiamato qualificati | i casi C# | risolto | `0cdbae9b2` |
| D-118 | C#: i membri dei tipi anonimi erano locali senza definizione | eShop | risolto | `73b645531` |
| D-119 | C#: membri dei source generator e `args` dei top-level statement senza causa | eShop | buco dichiarato (GENERATED, TOP_LEVEL) | `73b645531` |
| D-120 | C#: Catalog.API non si caricava sotto la globalizzazione invariante | eShop | risolto | `73b645531` |
| D-121 | Lo script di C e C++ cancellava la cartella in cui scrive il risultato | indicizzatore C/C++ | risolto | `c089b3540` |
| D-122 | CMake: il fornitore delle dipendenze nominato prima di essere definito | prova reale di C e C++ nel container | risolto | `a3dad5e39` |
| D-123 | scip-clang usava i processori della macchina | indicizzatore C/C++ | risolto | `d28dc1442` |
| D-124 | L'errore di CMake riscritto con righe ricavate dal testo | indicizzatore C/C++ | risolto | `377925c52` |
| D-125 | vcpkg e Conan: il configure senza l'installazione del gestore | sys-cpp-vcpkg-conan | risolto | `f9fde7c1e` |
| D-126 | Un configure che legge un submodule non scaricato | sys-git-submodule-absent | buco dichiarato (`unavailable`) | `f9fde7c1e` |
| D-127 | `namespace a::b {` non letto come C++17 | lettura C/C++ | risolto | `f9fde7c1e` |
| D-128 | Un `.h` con una direttiva Objective-C letto come C | lettura C/C++ | risolto | `f9fde7c1e` |
| D-129 | Un `.ts` di Qt Linguist letto come TypeScript | lettura | risolto | `f9fde7c1e` |
| D-130 | C: macro di decorazione e nomi da header non risolti | zlib | risolto | `8054a410c` |
| D-131 | Un configure che ha bisogno di ciò che l'unità scarica fuori dai registri | indicizzatore C/C++ | buco dichiarato (`unavailable`) | `98743babd` |
| D-132 | `file(DOWNLOAD)` ed ExternalProject non annotati | otel-demo src/currency | buco dichiarato (`failed` con la frase citata) | `6c2aa069e` |
| D-133 | zlib: file C e C++ che nessun build compila | zlib | buco dichiarato (`no compile command`) | `d4e6d9046` |
| D-134 | zlib minizip: il build autotools non eseguito | zlib contrib/minizip | risolto | `22dca6da8` |
| D-135 | otel-demo currency: il build dichiarato solo nel Dockerfile | otel-demo (`b825c7c25726`) | aperto (android-sdk) | `f024ba3a3` |
| D-136 | C: 5.147 buchi `no-document` | i casi C della conferma | aperto | — |
| D-137 | File C e C++ fuori dalla configurazione predefinita | sys-cmake-presets, tinyxml2 (`9148bdf719e9`) | buco dichiarato (`no compile command | `2bc7c7459` |
| D-138 | Go: i builtin erano buchi | indicizzatore Go | risolto | `a633ebd72` |
| D-139 | Go: file esclusi dai vincoli di build senza indice | indicizzatore Go | risolto | `a633ebd72` |
| D-140 | Go: un file senza go.mod non diceva perché | robot-shop (`55292e2199f2`) | risolto | `d4e6d9046` |
| D-141 | robot-shop dispatch: il modulo Go dichiarato solo nel Dockerfile | robot-shop (`55292e2199f2`) | buco dichiarato (`restore_failed` a `dispatch/Dockerfile:7`) | `f024ba3a3`, `f04dab9d5` |
| D-142 | Un file cgo fuori dall'indice Go | sys-go-cgo | buco dichiarato («a cgo file») | — |
| D-143 | Rust: file senza documento | hoppscotch (`55908a76a1d0`), semver (`280ebcb6edac`) | aperto | `a3801beed` |
| D-144 | Rust: file che nessun crate carica | hoppscotch | buco dichiarato («no crate includes it») | — |
| D-145 | TypeScript: `{ t } = useTranslation()` legato a un simbolo che l'indice non definisce | tududi (`71da9d7b34df`) | risolto | `3595d571b` |
| D-146 | TypeScript: pacchetti senza nome (heroicons) | tududi | risolto | `3595d571b` |
| D-147 | TypeScript e JavaScript: buchi senza causa | tududi | risolto | `3595d571b` |
| D-148 | `module` di `module.exports` come locale senza definizione | js-yarn-berry, js-npm-single | risolto | `eacfad80e` |
| D-149 | Una chiamata senza nome del chiamato era sempre un buco `no-position` | chi (`c64ed7d6635f`) e il corpus | risolto | `334ea4d96` |
| D-150 | TypeScript: `x.f!()` non nominava `x.f` | lettura TypeScript | risolto | `334ea4d96` |
| D-151 | TypeScript: `await f<T>(x)` non nominava `f` | lettura TypeScript | risolto | `334ea4d96` |
| D-152 | TypeScript 6: i tipi di Node non caricati | TypeScript nel container | risolto | `12775fee3` |
| D-153 | Svelte con nulla di letto non era `failed` | js-sveltekit | risolto | `12775fee3` |
| D-154 | Vue diverso fra analisi e unione | js-vue-pnpm | risolto | `12775fee3` |
| D-155 | L'import di un `.vue` non tipizzato senza causa | progetti Vue | risolto | `12775fee3` |
| D-156 | SvelteKit: «error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'» | js-sveltekit | buco dichiarato (TS5083 nominato nel motivo) | `12775fee3` |
| D-157 | TypeScript: i tipi sotto Yarn | TypeScript nel container | aperto (da verificare) | — |
| D-158 | JavaScript: riceventi non tipizzati | kotlinconf e il corpus JavaScript | buco dichiarato («a member of a value of type any») | `3595d571b` |
| D-159 | Template di Vue e Svelte non letti | hoppscotch, js-vue-pnpm, js-sveltekit | aperto (csharp-2) | `64edfb930` |
| D-160 | TypeScript: un file senza documento | hoppscotch, memos (`509e41bd1a1b`) | aperto | — |
| D-161 | Tailwind caricato sull'host con la configurazione del progetto | analyzer dei fogli di stile | risolto | `3595d571b` |
| D-162 | Fogli di stile: buchi `no-rule` | il corpus | aperto (ts-container-2) | — |
| D-163 | hoppscotch: lo stadio dei fogli di stile esce con 1 senza rapporto | hoppscotch | aperto (ts-container-2) | — |
| D-164 | Fogli remoti senza testo | il corpus | buco dichiarato (`remote-sheet`) | `9c719fc1a` |
| D-165 | Parser: `base` di C# non letto | parser | risolto | `d94f92470` |
| D-166 | Parser: `this` e `super` di Kotlin non letti | parser | risolto | `d94f92470` |
| D-236 | C++: il simbolo di un argomento di macro stava sul nome della macro | tinyxml2 (`9148bdf719e9`) | risolto | `a3801beed` |
| D-237 | Rust: i riferimenti e i file che un `#[cfg]` esclude non dicevano perché | hoppscotch (`55908a76a1d0`) | buco dichiarato (la causa cfg) | `a3801beed` |
| D-238 | Rust: il turbofish su un ricevitore calcolato toglieva il nome al chiamato | semver (`280ebcb6edac`) | risolto | `a3801beed` |

### Passo dinamico e osservatori

36 schede: 29 risolto, 2 aperto, 5 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit |
| --- | --- | --- | --- | --- |
| D-167 | «Osservato» con zero osservazioni | passo dinamico | risolto | `12775fee3` |
| D-168 | Un risultato malformato di un osservatore fermava la pipeline | passo dinamico | risolto | `12775fee3` |
| D-169 | pytest fermo agli errori di raccolta | il codice di Daodan, senza `benchmarks/` | risolto | `12775fee3` |
| D-170 | JavaScript: il TypeScript che Node toglie da solo | osservatore JavaScript | risolto | `12775fee3` |
| D-171 | Un comando di test fallito senza l'errore vero nel buco | osservatore JavaScript | risolto | `12775fee3` |
| D-172 | `not-observed` non diceva cosa aveva visto il registratore | py-setup-cfg-extras, il cui unico test non chiama nulla e dove cli.py non gira | risolto | `0c57a839a` |
| D-173 | Go e Rust non pianificavano i test della radice | osservatori Go e Rust | risolto | `a491415e6` |
| D-174 | Go fuori dal contratto dell'osservatore | osservatore Go | risolto | `a491415e6` |
| D-175 | Rust: «can't find crate for std» | osservatore Rust | risolto | `ef69774f9` |
| D-176 | Launchpad 502: Rust perde l'osservazione | giro `fixtures` | risolto | `d5964e7b9` |
| D-177 | L'osservatore C/C++ installava con vcpkg dove l'analizzatore usa Conan | progetti con vcpkg e Conan insieme | risolto | `a8a1ebdb5` |
| D-178 | L'osservatore JVM compilava sul JDK dell'immagine | javapoet | risolto | `a633ebd72` |
| D-179 | Java 25: «No access to RETAIN_CLASS_REFERENCE» | jvm-ver-* | risolto | `21b3cb39b` |
| D-180 | Test JVM multipiattaforma: nessun compito `test` | jvm-kmp-common-jvm | risolto | `9fe650a3a` |
| D-181 | Java 9 e 14 senza un JDK installabile | jvm-ver-* | buco dichiarato (`toolchain_unavailable`) | — |
| D-182 | I servizi della CI non avviati: tududi chiede PostgreSQL | tududi | risolto | `17babc624` |
| D-183 | Python: le dipendenze dei test non venivano dall'ambiente del runner | python-semver (`b6e83e3e40d3`) | risolto | `17babc624` |
| D-184 | Python: l'interprete non veniva da requires-python o .python-version | osservatore Python | risolto | `17babc624` |
| D-185 | tududi: `test` non arriva ai test del frontend | tududi | risolto con D-186 | `4ee44da0a` |
| D-186 | L'osservatore JavaScript non lanciava gli script di test che `test` non raggiunge | tududi | risolto | `7e5eb092e` |
| D-187 | tududi: i worker di Jest uccisi per memoria | tududi | risolto | `37c7ee093` |
| D-188 | fastapi: uv.lock non visto, l'intervallo di Python rifiutato | fastapi | risolto | `37c7ee093` |
| D-189 | I test JavaScript con 16 GB fissi anche dove la macchina non li ha | osservatore JavaScript | risolto | `a42dc1d86` |
| D-190 | Turborepo: il registratore non partiva | osservatore JavaScript | risolto | `cdc1660dd` |
| D-191 | npm-tests non riconosceva `turbo run … test` | pre-mappa dei test npm | risolto | `cdc1660dd` |
| D-192 | Un run di Node senza test letto come un registratore che non raggiunge i processi | osservatore JavaScript | risolto | `cdc1660dd` |
| D-193 | ES module non registrati su Node prima della 22.15 | mix-infra-gha | risolto | `756ebbcb3` |
| D-194 | jhipster: 162 chunk di Vitest in memoria non registrati | jhipster-sample | risolto | `e8bc485d7` |
| D-195 | `bun test` non registrato | fastapi | buco dichiarato (`runner_not_observed`) | `5148e8eb3` |
| D-196 | Un progetto senza test dichiarati, o con test che non partono | spec del passo dinamico, sezione «Limiti»; i progetti in miniatura del giro `fixtures` | buco dichiarato (`no_test_command`, `tests_not_declared`, `tests-not-run`) | — |
| D-197 | I test di fastapi non ancora girati davvero | fastapi | aperto | `5148e8eb3`, `37c7ee093` |
| D-198 | I test di eShop non ancora girati | eShop | aperto | — |
| D-199 | Python: extra e gruppi che il gestore non installa | spec del passo dinamico | buco dichiarato (test che non partono, `tests-not-run`) | — |
| D-200 | Python più vecchio del 3.12 | spec del passo dinamico | buco dichiarato (`python_too_old`) | — |
| D-201 | I servizi che `docker compose up` avvia non partivano | passo dinamico | risolto | `22dca6da8` |
| D-202 | I servizi di GitLab CI non avviati | passo dinamico | risolto | `23de469c4` |

### Container, servizi e driver Modal

17 schede: 12 risolto, 3 aperto, 2 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit |
| --- | --- | --- | --- | --- |
| D-203 | Il motore di container dell'utente usato anche se non risponde in locale | container | risolto | `177dcae02` |
| D-204 | Con un .git e Git che non risponde si copiavano i file ignorati | container | risolto | `177dcae02` |
| D-205 | Ciò che torna dal container non controllato | container | risolto | `177dcae02` |
| D-206 | Link simbolici tracciati seguiti nella copia del container | python-semver | risolto | `17babc624` |
| D-207 | I link lasciati fuori dalla copia non arrivavano ai buchi delle corse | container | risolto | `756ebbcb3` |
| D-208 | JVM: i buchi della preparazione sovrascrivevano quelli del container | analisi JVM | risolto | `756ebbcb3` |
| D-209 | Valgrind muore all'avvio nei sandbox di Modal (gVisor) | semver, tinyxml2, zlib e le fixture Rust e C/C++ | risolto | `8ef21896f` |
| D-210 | Bear sotto gVisor fallisce circa una build su dieci | build Make sotto Bear | risolto | `f829df4b0` |
| D-211 | Il server visuale resettava la connessione su una POST rifiutata | suite su Modal | risolto | `426626fbe` |
| D-212 | Servizi di Compose che il passo non avvia | spec del passo dinamico | buco dichiarato (`compose_not_read` e lacune dei servizi) | — |
| D-213 | I passi del job della CI prima dei test non giravano | passo dinamico | risolto | `f024ba3a3` |
| D-214 | Compose: i file del progetto montati nei servizi | passo dinamico | risolto | `f024ba3a3` |
| D-215 | Compose: `depends_on` | passo dinamico | risolto | `f024ba3a3` |
| D-216 | GitLab CI: i file che `.gitlab-ci.yml` include | passo dinamico | aperto (test-services) | `23de469c4` |
| D-217 | GitLab CI: `!reference` | da verificare | aperto (test-services) | — |
| D-218 | Kiri non stacca un container dalla sua prima rete | motore Kiri | buco dichiarato (`ci_step_not_run`) | `f024ba3a3` |
| D-219 | Kiri 0.2.0 rifiuta un secondo motore nella stessa distribuzione WSL | spec del passo dinamico | aperto (da decidere) | — |

### Benchmark e documenti

16 schede: 13 risolto, 3 aperto, 0 buco dichiarato.

| Id | Nome | Progetto o caso | Stato | Commit |
| --- | --- | --- | --- | --- |
| D-220 | Risposte attese: il workspace di javapoet e le soluzioni .NET di zlib | javapoet, zlib | risolto | `a04ab36e1` |
| D-221 | Lo schema del banco senza BOM, POM genitore e versioni centrali | dieci progetti del corpus | risolto | `1420247ad` |
| D-222 | `test_catalog` rosso: ANAGRAFICA.md non era l'uscita del generatore | benchmark project-model | risolto | `68a846a4a` |
| D-223 | Le risposte attese delle fixture Android senza i build-tools | jvm-android-app-lib, mix-poly-firebase | risolto | `68a846a4a` |
| D-224 | I test del registratore JVM saltati: l'immagine dei test senza JDK | `tests/modal_pytest.py` | risolto | `a633ebd72` |
| D-225 | Due fixture con `node --test test/` | due fixture JavaScript | risolto | `12775fee3` |
| D-226 | Toolchain Maven contate sbagliate per il frammento di `declared_in` | jvm-ver-* e le fixture Maven | aperto | — |
| D-227 | README del benchmark: Rust, C e C++ «solo dove Valgrind parte» | `benchmarks/project-model/README.md` | aperto | — |
| D-228 | Il rapporto dichiarava nulla la copertura a runtime | il metodo di codebase-map | risolto | `78c03d6e8` |
| D-229 | Spec: il passo 2 «non esegue codice del progetto» | `docs/specs/2026-11-12-passo-dinamico.md` | risolto | `78c03d6e8` |
| D-230 | Spec: Rust, C e C++ «non provati» su Modal | `docs/specs/2026-11-12-passo-dinamico.md` | risolto | `78c03d6e8` |
| D-231 | README, SKILL e riferimenti dicevano Jedi e «solo statica» | README, SKILL, `references/snapshot.md` | risolto | `e617127c3` |
| D-232 | L'osservatore Python diceva che il passo non avvia servizi | `scripts/dynamic/python.py` | risolto | `0ca9f1650` |
| D-233 | Due script del benchmark dell'inferenza mai eseguiti | `benchmarks/inference-audit` | aperto | `137512c11` |
| D-234 | Un file dello snapshot senza dichiarazioni usciva dal progetto nel grafo | `benchmarks/inference-audit` | risolto | `53e219638` |
| D-235 | Pre-mappa: dipendenze sotto la soglia | corpus della pre-mappa | risolto | `de353d251`, `99112d0b9` |

## Schede

### Pre-mappa, snapshot e preparazione

#### D-001 Due build system nella stessa cartella fusi in un'unità
- **Descrizione:** il lettore dei moduli dava una sola unità dove una cartella ha due build system.
- **Spiegazione:** `scripts/modules.py` fondeva le build affiancate della stessa cartella; ora restano due unità.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f` (14 novembre), `scripts/modules.py`.
- **Verifica:** per l'intero commit, sulle 122 fixture nessuna faccetta di nessuna famiglia peggiora:
  - membri di workspace in più: da 486 a 1;
  - dipendenze trovate: da 508 a 574, quelle in più da 332 a 52;
  - dipendenze fra unità: da 70 a 81.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-002, D-003, D-004 e D-005.

#### D-002 Go: requisiti indiretti letti e moduli legati fuori da un workspace
- **Descrizione:** la pre-mappa dava a un modulo Go dipendenze e archi che non dichiara.
- **Spiegazione:** il lettore leggeva anche i requisiti indiretti di go.mod e legava moduli che nessun workspace unisce; ora legge i soli requisiti diretti e lega i moduli solo dentro un workspace.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f`, `scripts/modules.py`.
- **Verifica:** la misura del commit, in D-001.
- **Stato:** risolto.
- **Note:** D-020 corregge gli archi Go della pre-mappa (`99112d0b9`).

#### D-003 Maven: dipendenze non lette come gruppo:artefatto e profili taciuti
- **Descrizione:** le dipendenze Maven non erano quelle di primo livello e i profili non valutati non comparivano.
- **Spiegazione:** ora il lettore legge le dipendenze di primo livello come gruppo:artefatto e dichiara i profili che non valuta.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f`, `scripts/modules.py`.
- **Verifica:** la misura del commit, in D-001.
- **Stato:** risolto.
- **Note:** —

#### D-004 Un glob di workspace crea un'unità per cartella
- **Descrizione:** membri di workspace inventati: 486 in più sulle 122 fixture.
- **Spiegazione:** un glob di workspace diventava un'unità per ogni cartella che lo soddisfa; ora sceglie fra le unità dichiarate.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f`, `scripts/modules.py`.
- **Verifica:** la misura del commit, in D-001: membri in più da 486 a 1.
- **Stato:** risolto.
- **Note:** —

#### D-005 Un bersaglio ambiguo scelto invece che dichiarato
- **Descrizione:** fra due bersagli possibili il lettore ne sceglieva uno.
- **Spiegazione:** un bersaglio ambiguo ora è una lacuna, non una scelta.
- **Progetto e caso:** corpus della pre-mappa — misura sulle 122 fixture, 14 novembre 2026.
- **Rimedio:** `708eae48f`, `scripts/modules.py`.
- **Verifica:** la misura del commit, in D-001.
- **Stato:** risolto.
- **Note:** —

#### D-006 Gruppi di sviluppo di pyproject non letti
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva i gruppi di sviluppo di pyproject; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1` (15 novembre), `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-007–D-016 e D-220.

#### D-007 setup.cfg non letto
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva setup.cfg; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-008 Import map di Deno non lette
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva le import map di Deno; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-009 angular.json non letto
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva angular.json; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-010 Soluzioni .NET fuori dalla radice non lette
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non trovava le soluzioni fuori dalla radice; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** la risposta attesa delle soluzioni .NET di zlib è corretta nello stesso commit (D-220).

#### D-011 Sottoprogetti sbt non letti
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva i sottoprogetti sbt; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-012 Umbrella di Mix non letto
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva un progetto umbrella di Mix; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-013 Dipendenze `file:` di npm non lette dal lettore dei moduli
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva le dipendenze `file:` di npm; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** la fonte npm della pre-mappa ha un difetto simile, D-017.

#### D-014 Rinomina e tabelle target di Cargo non lette
- **Descrizione:** una delle undici cause misurate sui 122 progetti di prova.
- **Spiegazione:** il lettore dei moduli non leggeva la rinomina di una dipendenza né le tabelle target di Cargo; il commit non dice di più.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-030 tratta il nome del pacchetto di Cargo nella pre-mappa.

#### D-015 Requisiti di piattaforma di Composer e SDK di pub contati come dipendenze
- **Descrizione:** dipendenze in più nelle unità PHP e Dart.
- **Spiegazione:** i requisiti di piattaforma di Composer e gli SDK di pub non sono pacchetti, e il lettore li contava come tali.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-016 Un build incluso contato come membro del workspace
- **Descrizione:** un build incluso compariva fra i membri.
- **Spiegazione:** un build incluso non è un membro del workspace; il lettore lo contava.
- **Progetto e caso:** corpus della pre-mappa — 122 progetti, 15 novembre 2026; la risposta attesa del workspace di javapoet ne dipende.
- **Rimedio:** `a04ab36e1`, `scripts/modules.py`. Anche l'adattatore del banco non lo conta più fra i membri (`9c17c7686`).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-220.

#### D-017 Pacchetti locali `file:` di npm senza archi nella pre-mappa
- **Descrizione:** in js-local-and-git-deps la risposta di npm copriva un arco verso un pacchetto locale che `modules.py` trova; la misura del 15 novembre lo dava come aperto (`22524b57b`).
- **Spiegazione:**
  - fuori da un workspace, npm elenca un pacchetto collegato a una cartella del progetto solo con `:link`;
  - la fonte chiedeva la radice e i membri, quindi dichiarava nessun arco e copriva quello che `modules.py` legge.
- **Progetto e caso:** js-local-and-git-deps — misura sui 122 progetti, 15 novembre 2026.
- **Rimedio:** `db45bcc93` (15 novembre), `scripts/premap/npm.py`:
  - la fonte chiede anche `:link`;
  - se `:link` non risponde, non dichiara archi e lascia la lacuna.
- **Verifica:** le risposte degli strumenti sono registrate di nuovo nel container; per il resto, solo test.
- **Stato:** risolto.
- **Note:** —

#### D-018 Una dipendenza di un file centrale data all'unità più vicina
- **Descrizione:** dipendenze inventate; in eShop 72 voci in più.
- **Spiegazione:**
  - un catalogo di versioni o un file centrale delle versioni dice quali versioni esistono, non quale unità le usa;
  - la pre-mappa le attribuiva all'unità più vicina, cioè le inventava;
  - ora l'unità la dà solo il manifesto di un'unità.
- **Progetto e caso:** eShop e il corpus della pre-mappa — misura salvata, 15 novembre 2026.
- **Rimedio:** `de353d251` (15 novembre), `scripts/premap/renovate.py`.
- **Verifica:** la misura salvata, simulata:
  - dipendenze trovate: da 720 a 733;
  - in più: da 150 a 83;
  - sbagliate: da 35 a 32;
  - in più in eShop: da 72 a 1.
- **Stato:** risolto.
- **Note:** —

#### D-019 Un arco fra unità contato anche come dipendenza
- **Descrizione:** nella misura le voci in più erano invenzioni della pre-mappa, nessuna una lacuna delle risposte attese.
- **Spiegazione:** un arco fra due unità del progetto veniva contato anche come dipendenza esterna.
- **Progetto e caso:** corpus della pre-mappa — misura sui 122 progetti su Modal, 15 novembre 2026.
- **Rimedio:** `99112d0b9` (15 novembre):
  - file: `scripts/premap/__init__.py`, `premap/go.py`, `premap/module_graph.py`, `premap/renovate.py`;
  - riproduzione: `benchmarks/project-model/tools/premap_replay.py`.
- **Verifica:** per l'intero commit, le risposte registrate dei 122 progetti sono rigiocate con `tools/premap_replay.py`:
  - dipendenze: 746 trovate, 76 in più e 45 sbagliate diventano 785, 30 e 13;
  - toolchain: 135, 47 e 24 diventano 137, 6 e 16;
  - archi in più: da 2 a 0;
  - sulle faccette che il commit non tocca, la riproduzione dà gli stessi numeri della misura su Modal.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-020–D-030.

#### D-020 Go: un arco fra moduli senza replace né go.work
- **Descrizione:** archi Go in più nella pre-mappa.
- **Spiegazione:** ora Go traccia un arco solo se un replace punta alla cartella o un go.work elenca entrambi.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`, `scripts/premap/go.py`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** D-002.

#### D-021 Una versione scritta in un file centrale non completava la voce dell'unità
- **Descrizione:** voci senza versione dove la versione sta in un file centrale.
- **Spiegazione:** una versione scritta in un file centrale ora completa la voce dell'unità che nomina il pacchetto. Sono file centrali le props di NuGet, il catalogo di pnpm e la tabella del workspace di Cargo.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`, `scripts/premap/renovate.py`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** D-018; lo schema del banco ha la stessa regola (`1420247ad`, D-221).

#### D-022 Un vincolo dichiarato contato come pacchetto
- **Descrizione:** toolchain in più o sbagliate fra le dipendenze.
- **Spiegazione:** un vincolo che il file dichiara è una toolchain, non un pacchetto.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019: toolchain in più da 47 a 6.
- **Stato:** risolto.
- **Note:** —

#### D-023 Script, task, replace e import verso un percorso contati come pacchetti
- **Descrizione:** dipendenze in più.
- **Spiegazione:** script, task, replace e import verso un percorso non sono pacchetti.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** —

#### D-024 Una toolchain diversa da quella che il file scrive
- **Descrizione:** toolchain sbagliate.
- **Spiegazione:** ora una toolchain è ciò che un file scrive.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019: toolchain sbagliate da 24 a 16.
- **Stato:** risolto.
- **Note:** —

#### D-025 Il wrapper Maven dava sé stesso invece di Maven
- **Descrizione:** una voce del wrapper al posto di Maven.
- **Spiegazione:** il wrapper Maven dà Maven, non sé stesso.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** —

#### D-026 POM genitore e BOM importato senza scope parent e bom
- **Descrizione:** POM genitore e BOM importato contati come dipendenze ordinarie.
- **Spiegazione:** il genitore e un BOM importato hanno scope parent e bom: il build li scarica e il codice non li usa.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** lo schema del banco ha la stessa regola (`1420247ad`, D-221).

#### D-027 Uno scope dato alle dipendenze di Gradle
- **Descrizione:** dipendenze Gradle con uno scope che il build non dice.
- **Spiegazione:** Gradle non dice la configurazione, quindi nessuno scope.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** —

#### D-028 Un file di pip-compile contato come dichiarazione
- **Descrizione:** dipendenze in più dai file generati da pip-compile.
- **Spiegazione:** un file di pip-compile non dichiara dipendenze.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** —

#### D-029 Pacchetti di Bazel, Helm, Terraform, Conan e Deno non dichiarati
- **Descrizione:** dipendenze mancanti per cinque gestori.
- **Spiegazione:** Bazel, Helm, Terraform, Conan e Deno dichiarano pacchetti che la pre-mappa non riportava.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019: dipendenze trovate da 746 a 785.
- **Stato:** risolto.
- **Note:** —

#### D-030 Cargo e SwiftPM: il pacchetto con un nome diverso da quello del build tool
- **Descrizione:** nomi di pacchetto che non corrispondono alle risposte attese.
- **Spiegazione:** Cargo e SwiftPM ora nominano il pacchetto come lo nomina il build tool.
- **Progetto e caso:** corpus della pre-mappa — misura del 15 novembre 2026.
- **Rimedio:** `99112d0b9`.
- **Verifica:** la riproduzione del commit, in D-019.
- **Stato:** risolto.
- **Note:** D-014.

#### D-031 Un collegamento simbolico a un file del progetto: «UNIQUE constraint failed: files.path»
- **Descrizione:** python-semver non si riusciva ad analizzare: lo snapshot falliva con «UNIQUE constraint failed: files.path».
- **Spiegazione:** lo snapshot leggeva attraverso i collegamenti e chiamava ogni file con il nome del suo bersaglio, così un collegamento a un file del progetto dava lo stesso percorso due volte.
- **Progetto e caso:** python-semver (`b6e83e3e40d3`) — 15 novembre 2026.
- **Rimedio:** `ea92f3fed` (15 novembre), `scripts/snapshot.py` e `scripts/tree_scope.py`:
  - un collegamento sotto il target non si legge e non si attraversa;
  - è elencato in `scope.skipped.links`;
  - ogni file ha il nome del posto in cui sta.
- **Verifica:** python-semver dà 95 file.
- **Stato:** risolto.
- **Note:** D-032, D-033; nella copia del container, D-206.

#### D-032 Un collegamento verso l'esterno portava dentro un file di fuori
- **Descrizione:** un file fuori dal progetto entrava nello snapshot.
- **Spiegazione:** lo snapshot seguiva il collegamento fino al suo bersaglio esterno.
- **Progetto e caso:** snapshot — 15 novembre 2026.
- **Rimedio:** `ea92f3fed`, come in D-031.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-031.

#### D-033 Un collegamento rotto spariva senza traccia
- **Descrizione:** un collegamento rotto non compariva da nessuna parte.
- **Spiegazione:** lo snapshot non trovava il bersaglio e saltava il file in silenzio; ora è elencato in `scope.skipped.links`.
- **Progetto e caso:** snapshot — 15 novembre 2026.
- **Rimedio:** `ea92f3fed`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-031.

#### D-034 Grammatiche scaricate da GitHub al primo uso, senza versione fissata
- **Descrizione:** la libreria dei parser scaricava da sola le grammatiche al primo uso.
- **Spiegazione:** scaricava da GitHub, in una cartella sua, una versione non fissata.
- **Progetto e caso:** snapshot — 14 novembre 2026.
- **Rimedio:** `d6545b074` (14 novembre), `scripts/languages/_treesitter.py`, `scripts/snapshot.py` e `requirements.txt`:
  - le versioni sono fissate;
  - il pacchetto entra nella cache di Daodan, verificato con lo sha256;
  - lo copia in sola lettura da quello che la macchina ha già, oppure lo scarica.
- **Verifica:** con le grammatiche presenti lo snapshot è identico a prima; per il resto, solo test.
- **Stato:** risolto.
- **Note:** D-035.

#### D-035 Senza rete un file passava in silenzio al lettore a espressioni regolari
- **Descrizione:** una grammatica mancante non dava errore: il file veniva letto con un lettore più debole.
- **Spiegazione:** senza rete il download falliva e il file finiva al lettore a espressioni regolari, senza dirlo.
- **Progetto e caso:** snapshot — 14 novembre 2026.
- **Rimedio:** `d6545b074`. Lo snapshot segna il file come saltato con la causa, senza lettura più debole, ed elenca le grammatiche mancanti.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-034.

#### D-036 Grammatiche scelte senza l'architettura del processo
- **Descrizione:** su Windows ARM64 un Python x64 emulato rischiava librerie di grammatiche dell'architettura sbagliata, e la scelta interrogava Windows.
- **Spiegazione:** la scelta passava dal modulo platform; ora il pacchetto si sceglie da `sys.platform` e, su Windows, dall'architettura del processo, così un Python x64 emulato su ARM64 carica le librerie x64.
- **Progetto e caso:** host Windows — 14 novembre 2026.
- **Rimedio:** `68e39dcde` (14 novembre), `scripts/languages/_treesitter.py`. Nessun processo parte.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-038, D-039.

#### D-037 Grammatiche piazzate fra processi senza sicurezza
- **Descrizione:** il commit dice che le grammatiche ora si piazzano in modo sicuro tra processi.
- **Spiegazione:** da verificare: il commit non dice cosa accadeva prima.
- **Progetto e caso:** parser — 16 novembre 2026.
- **Rimedio:** `d94f92470` (16 novembre).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-038 La cartella condivisa di Daodan chiedeva la versione a Windows
- **Descrizione:** trovare la cartella condivisa poteva lanciare il comando `ver`.
- **Spiegazione:** `platform.system()` può lanciare `ver` quando Windows non risponde; `os.name` non lancia nulla.
- **Progetto e caso:** host Windows — 14 novembre 2026.
- **Rimedio:** `bfdca190b` (14 novembre), `scripts/embedding_worker.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-036, D-039.

#### D-039 Il sistema e l'architettura chiesti a Windows con il modulo platform
- **Descrizione:** `ver` partiva anche quando Windows non risponde, e il test dell'indice Java se lo aspettava.
- **Spiegazione:** il sistema e l'architettura si leggevano con il modulo platform; ora si leggono dal processo.
- **Progetto e caso:** host Windows — 14 novembre 2026.
- **Rimedio:** `b5d218801` (14 novembre), `scripts/resolve_edges.py`; il test ora pretende che `ver` non parta.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-040.

#### D-040 Un rustup vecchio installava per conto di un progetto
- **Descrizione:** con un rustup che non conosce l'interruttore dell'installazione automatica, un progetto che fissa una toolchain la faceva installare.
- **Spiegazione:** quel rustup non permette di spegnere l'installazione automatica.
- **Progetto e caso:** host con rustup vecchio — 14 novembre 2026.
- **Rimedio:** `b5d218801`. Rust è unavailable, con la causa e il rimedio.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (Rust `unavailable`).
- **Note:** D-041; vale fino a quando le analisi girano nel container.

#### D-041 Cargo, rustc e rust-analyzer installavano nella home dell'utente
- **Descrizione:** gli strumenti dell'host potevano installare o scaricare per conto di un progetto.
- **Spiegazione:**
  - Cargo, rustc e rust-analyzer partivano con l'installazione automatica di rustup accesa;
  - la sonda leggeva il file di toolchain del progetto.
- **Progetto e caso:** host — 14 novembre 2026.
- **Rimedio:** `6856a0980` (14 novembre), `scripts/resolve_edges.py`:
  - l'installazione automatica è spenta;
  - la sonda non legge il file di toolchain di nessun progetto;
  - se il progetto fissa una toolchain che rustup non ha, Rust è unavailable con la causa e il rimedio.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-042.

#### D-042 uv scaricava interpreti e leggeva la configurazione del progetto
- **Descrizione:** uv sull'host scaricava interpreti, leggeva la configurazione del progetto e teneva la cache fuori dalla cartella di Daodan.
- **Spiegazione:** uv partiva con i valori predefiniti.
- **Progetto e caso:** host — 14 novembre 2026.
- **Rimedio:** `6856a0980`. uv non scarica interpreti, non legge la configurazione del progetto e tiene la cache nella cartella condivisa.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-041.

#### D-043 I makefile erano «tipo di file non inventariato»
- **Descrizione:** la pre-mappa non vedeva i target dei makefile.
- **Spiegazione:** lo snapshot non registrava i makefile (Makefile, GNUmakefile, *.mak, *.mms) e non c'era una fonte make.
- **Progetto e caso:** zlib e tinyxml2 su Kiri — 15 novembre 2026.
- **Rimedio:** `c6767743f` (15 novembre):
  - file: `scripts/premap/make.py`, `scripts/source_files.py`, `scripts/module_inventory.py`, `scripts/premap/container_runner.py`;
  - la fonte make gira nell'esecutore con il Make dell'immagine.
- **Verifica:** su Kiri, con tutte le fonti: zlib da 39 a 50 su 122, tinyxml2 da 1 a 6 su 7.
- **Stato:** risolto. I makefile di altri dialetti sono un buco dichiarato.
- **Note:** —

#### D-044 Android: compileSdk e buildToolsVersion non letti, SDK non installato
- **Descrizione:** le build Android non avevano l'SDK.
- **Spiegazione:**
  - la pre-mappa non leggeva compileSdk e buildToolsVersion dal modello di Gradle;
  - la preparazione non installava l'SDK.
- **Progetto e caso:** jvm-android-app-lib, mix-poly-firebase — 16 novembre 2026.
- **Rimedio:** `a633ebd72` (16 novembre):
  - la preparazione installa da Google gli strumenti a riga di comando fissati per sha256;
  - accetta le licenze come fa una CI e installa solo i pacchetti dichiarati;
  - ANDROID_HOME vale in entrambe le fasi.
- **Verifica:** le risposte attese dichiarano android-build-tools 34.0.0 (`68a846a4a`, D-223); per il resto, solo test.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-045–D-050, D-138, D-139, D-178 e D-224. Dopo il rimedio le build Android si fermano su `google-services.json`, D-109.

#### D-045 Go: girava una versione diversa dalla più alta dichiarata
- **Descrizione:** con più righe `go`, la preparazione non installava la più alta.
- **Spiegazione:** ogni riga `go` è un minimo (go.dev/doc/toolchain), quindi deve girare il Go più alto dichiarato.
- **Progetto e caso:** preparazione Go — 16 novembre 2026.
- **Rimedio:** `a633ebd72`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-046 `node:22-alpine` non letto come Node 22
- **Descrizione:** un'immagine Docker con una variante non dava la versione di Node.
- **Spiegazione:** il versioning docker di Renovate legge `node:22-alpine` come Node 22; la pre-mappa non lo faceva.
- **Progetto e caso:** pre-mappa delle immagini — 16 novembre 2026.
- **Rimedio:** `a633ebd72`; le risposte attese del benchmark sono corrette di conseguenza.
- **Verifica:** solo test. ANAGRAFICA.md, da rigenerare dopo questa modifica, resta rossa fino a `68a846a4a` (D-222).
- **Stato:** risolto.
- **Note:** D-222.

#### D-047 Gli errori di uv troncati
- **Descrizione:** l'errore di un ripristino Python arrivava tagliato.
- **Spiegazione:** la preparazione non teneva intero l'errore di uv.
- **Progetto e caso:** preparazione Python — 16 novembre 2026.
- **Rimedio:** `a633ebd72`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-048 Dipendenze git di Python senza l'host né git
- **Descrizione:** le dipendenze git di un progetto Python non si installavano.
- **Spiegazione:** la preparazione non raggiungeva l'host che quelle dipendenze dichiarano e non aveva git.
- **Progetto e caso:** preparazione Python — 16 novembre 2026.
- **Rimedio:** `a633ebd72`:
  - le dipendenze git raggiungono l'host che dichiarano;
  - git arriva da Debian, solo se serve;
  - se non si installano, si installa il resto e il buco le nomina.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-049 I registri dichiarati assenti dalla pre-mappa
- **Descrizione:** la preparazione non sapeva quali registri il progetto dichiara.
- **Spiegazione:** la pre-mappa non riportava i registri dichiarati, cioè gli indici di pip e uv, i lock di npm, pnpm e Yarn, i repository Maven e Gradle e i feed NuGet.
- **Progetto e caso:** pre-mappa — 16 novembre 2026.
- **Rimedio:** `a633ebd72`: finiscono in `units.registries`, senza credenziali.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-052, D-053, D-054.

#### D-050 Gradle avrebbe scaricato i JDK delle toolchain
- **Descrizione:** una build con toolchain Gradle diverse dal JDK su cui gira non trovava i JDK senza rete.
- **Spiegazione:** Gradle scarica da sé i JDK delle toolchain, e nell'esecuzione la rete è chiusa.
- **Progetto e caso:** build composte con toolchain 17 e 21 — 16 novembre 2026.
- **Rimedio:** `a633ebd72`, `scripts/indexers/jvm.py`:
  - la preparazione installa ogni JDK che le toolchain chiedono;
  - lo dà a Gradle con `org.gradle.java.installations.paths` in `$GRADLE_USER_HOME/gradle.properties`;
  - spegne lo scaricamento con `org.gradle.java.installations.auto-download=false`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-101.

#### D-051 pnpm e Yarn: «Cannot find matching keyid»
- **Descrizione:** pnpm e Yarn non partivano sui Node vecchi: «Cannot find matching keyid».
- **Spiegazione:** i corepack forniti con le versioni vecchie di Node portano le chiavi di npm ruotate nel 2025 e non verificano più i gestori pubblicati dopo.
- **Progetto e caso:** preparazione Node — 16 novembre 2026.
- **Rimedio:** `a94de85fb` (16 novembre), `scripts/preparation.py`:
  - la preparazione installa, con l'npm di quel Node, il corepack più recente compatibile (>=0.31.0);
  - lo mette primo nel PATH, con la verifica accesa;
  - se nessuno si installa, è un buco con la causa.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-052 Preparazione Python senza gli host dichiarati e senza il loro nome
- **Descrizione:** un ripristino fallito su un host dichiarato non diceva quale host.
- **Spiegazione:** la preparazione non raggiungeva gli host che la pre-mappa elenca per le dipendenze di ogni unità.
- **Progetto e caso:** preparazione Python — 16 novembre 2026.
- **Rimedio:** `2f0353c03` (16 novembre), `scripts/preparation.py` e `scripts/dynamic/python.py`:
  - `preparation.declared` dà gli host e i manifest che li dichiarano;
  - l'osservatore Python li aggiunge a ciò che la preparazione raggiunge;
  - un host dichiarato che non risponde è `host_unreachable`, con l'host e i file.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-053, D-054.

#### D-053 Dipendenze GitHub di npm senza gli host di download
- **Descrizione:** npm non scaricava le dipendenze GitHub.
- **Spiegazione:** un github.com dichiarato non apriva gli host di download di GitHub, da cui npm le scarica.
- **Progetto e caso:** preparazione Node — 16 novembre 2026.
- **Rimedio:** `2f0353c03`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-054 Build JVM senza gli host che il progetto dichiara
- **Descrizione:** le build JVM non raggiungevano i repository che dichiarano (JitPack, repository aziendali).
- **Spiegazione:** gli host di `preparation.declared` non arrivavano a `jvm.run`, all'indice di Java e Kotlin né all'osservatore JVM.
- **Progetto e caso:** javapoet (`b9017a9503b7`) — 16 novembre 2026.
- **Rimedio:** `609ca96dd` (16 novembre):
  - `scripts/indexers/jvm.py`, `java.py`, `kotlin.py`;
  - `scripts/dynamic/jvm.py`.
- **Verifica:** su Modal, javapoet:
  - indice Java fresh con i buchi `jdk_unsupported` e `build_edited`;
  - l'osservatore compila sul JDK 8 dichiarato, con Error Prone al suo posto;
  - 389 test e 6.021 siti osservati.
- **Stato:** risolto.
- **Note:** D-099, D-100.

#### D-055 Il modello di Gradle senza i repository dei plugin delle impostazioni
- **Descrizione:** il modello di Gradle di kotlinconf non risolveva i plugin.
- **Spiegazione:** la corsa raggiungeva solo i registri standard, non i repository dei plugin che le impostazioni dichiarano.
- **Progetto e caso:** kotlinconf (`146e891c150c`) — 16 novembre 2026.
- **Rimedio:** `17babc624` (16 novembre). Se il modello di Gradle fallisce, riprova raggiungendo i repository dei plugin delle impostazioni.
- **Verifica:** conferma: kotlinconf supera i repository e si ferma sulla JVM (D-058).
- **Stato:** risolto.
- **Note:** —

#### D-056 Bun dichiarato solo nei workflow non era una toolchain
- **Descrizione:** fastapi in finale e in conferma: «sh: 1: bun: not found», `npm test` uscito con 127.
- **Spiegazione:** fastapi dichiara Bun solo nei workflow (oven-sh/setup-bun, bun-version 1.3.12), e il suo script di test lancia `bun run`.
- **Progetto e caso:** fastapi (`aabb90126964`) — finale e conferma, 16 novembre 2026.
- **Rimedio:** `5148e8eb3` (16 novembre), `scripts/premap/renovate.py` e `scripts/dynamic/javascript.py`:
  - la pre-mappa tiene la versione che Renovate già riporta;
  - l'osservatore JavaScript la installa accanto a Node.
- **Verifica:** su Modal `npm test` arriva a Playwright sotto il registratore; dalla pre-mappa, `tests/test_codebase_map_premap.py` (`test_the_bun_a_workflow_sets_up_is_the_bun_toolchain`, in `f024ba3a3`).
- **Stato:** risolto.
- **Note:** `bun test` resta `runner_not_observed`, D-195; il resto dei test di fastapi in D-197.

#### D-057 L'immagine `devcontainers/java:1-21` letta come Java 1
- **Descrizione:** kotlinconf dichiara nel devcontainer `mcr.microsoft.com/devcontainers/java:1-21`, e la pre-mappa ne leggeva la versione `1`.
- **Spiegazione:** i tag di quella famiglia di immagini sono `<versione dell'immagine>-<versione di Java>[-<OS>]` oppure `<versione di Java>[-<OS>]`, come dice il README di devcontainers/images (src/java). La pre-mappa ne prendeva il primo numero.
- **Progetto e caso:** kotlinconf — conferma, 16 novembre 2026.
- **Rimedio:** `22dca6da8` (16 novembre), `scripts/premap/renovate.py`: `DEV_CONTAINERS` e `_image_version(tag, name)`, che per queste immagini prendono l'ultimo di al massimo due numeri del tag.
- **Verifica:** giro `jvm-kotlinconf`: la toolchain `java 21` è dichiarata in `.devcontainer/devcontainer.json` (fonte renovate@44.239.1).
- **Stato:** risolto.
- **Note:** D-058.

#### D-058 «Dependency requires at least JVM runtime version 21. This build uses a Java 17 JVM.»
- **Descrizione:** in conferma kotlinconf si ferma nel modello di Gradle della pre-mappa e nell'analisi Kotlin: «Could not resolve dev.zacsweers.metro:gradle-plugin:1.5.2. … Dependency requires at least JVM runtime version 21. This build uses a Java 17 JVM.».
- **Spiegazione:** Gradle girava sul JDK 17 dell'immagine; un plugin del build chiede una JVM 21.
- **Progetto e caso:** kotlinconf — conferma, 16 novembre 2026.
- **Rimedio:** `22dca6da8`:
  - file: `scripts/premap/gradle.py` (`asked_jdk`), `scripts/premap/container_runner.py`, `scripts/indexers/jvm.py`;
  - la pre-mappa e l'analisi ripartono sul JDK dichiarato a quel livello o sopra;
  - se nessuno lo è, ripartono sulla versione che l'errore nomina, con la lacuna `jdk_from_build_error`.
- **Verifica:** giro `jvm-kotlinconf`, 754 secondi:
  - il modello di Gradle riparte su mise java@21.0.13 (`premap-runs/gradle-jdk`) e dà le toolchain del build (core 21, androidApp 11, android-sdk 37.2);
  - nessun `jdk_from_build_error`, perché il devcontainer dichiara il 21;
  - l'analisi passa la configurazione del progetto radice.
- **Stato:** risolto.
- **Note:** l'analisi Kotlin si ferma poi su un altro errore, D-110.

#### D-059 Template ERB, Handlebars, Jinja e Nunjucks fuori dallo snapshot
- **Descrizione:** questi template non arrivavano nemmeno al passaggio: nessun grafo e nessun avviso.
- **Spiegazione:** lo snapshot non li registrava.
- **Progetto e caso:** snapshot — 16 novembre 2026; nel finale eShop (58 file), otel-demo (7) e mix-ruby-rails (1).
- **Rimedio:** `e15f2ff88` (16 novembre), `scripts/languages/__init__.py` e `scripts/source_files.py`. Entrano nello snapshot dichiarati senza lettore; Jade resta una voce a livello di file, come Pug.
- **Verifica:** finale: «template language: no reader» con eShop 58, otel-demo 7 e mix-ruby-rails 1.
- **Stato:** buco dichiarato (`template language: no reader`).
- **Note:** —

#### D-060 Avviso «senza analyzer» per i linguaggi fatti solo di file di build
- **Descrizione:** CMake, Starlark, Meson e i makefile davano l'avviso di linguaggio senza analyzer.
- **Spiegazione:** quei file dichiarano il build che la pre-mappa esegue, e ciò che dichiarano è già nei suoi fatti.
- **Progetto e caso:** pre-mappa — 16 novembre 2026.
- **Rimedio:** `d14200dce` (16 novembre), `scripts/premap/__init__.py` e `scripts/premap/enry.py`. Un linguaggio con anche altri file, come uno script di shell o un frammento .mk che nessun build tool nomina, resta un buco.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-061 Un profilo Conan che chiede una build dal sorgente
- **Descrizione:** con un profilo Conan del progetto il configure non si completa.
- **Spiegazione:** quel profilo chiede una build dal sorgente, e Daodan non apre host in più.
- **Progetto e caso:** pre-mappa CMake con profili Conan — 15 novembre 2026.
- **Rimedio:** `7b1e9ee9f` (15 novembre). Ogni profilo aggiunge un install e un configure; quello che chiede la build dal sorgente resta `restore_failed`, con il profilo e la causa.
- **Verifica:** risposte da un run vero.
- **Stato:** buco dichiarato (`restore_failed`).
- **Note:** —

#### D-062 Senza container le fonti di modello non girano
- **Descrizione:** senza un motore di container i comandi di modello della pre-mappa non si eseguono.
- **Spiegazione:** quei comandi girano solo nel container di Daodan.
- **Progetto e caso:** scansione — 15 novembre 2026.
- **Rimedio:** `8e85b2c1e` (15 novembre): la lacuna `model_not_run` dice causa e rimedio, e la scansione riprova quando un motore risponde.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (`model_not_run`).
- **Note:** —

#### D-063 Un wrapper Gradle o Maven che punta a un host non ufficiale
- **Descrizione:** Daodan non scarica lo strumento da un host non ufficiale.
- **Spiegazione:** Gradle e Maven si prendono dalle proprietà del wrapper, e solo dagli host ufficiali.
- **Progetto e caso:** build JVM — 14 novembre 2026.
- **Rimedio:** `f48df5c7d` (14 novembre): `unavailable` con la causa.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (`unavailable`).
- **Note:** —

#### D-064 Gradle raggiunge anche il Plugin Portal
- **Descrizione:** fra i registri di Gradle c'è anche il Plugin Portal.
- **Spiegazione:**
  - ogni strumento raggiunge solo i suoi registri;
  - Maven e Gradle raggiungono Maven Central, Google e JCenter, che non accettano caricamenti;
  - Gradle raggiunge anche il Plugin Portal, ed è un limite dichiarato.
- **Progetto e caso:** perimetro di rete, dopo la revisione indipendente — 15 novembre 2026.
- **Rimedio:** `177dcae02` (15 novembre), `scripts/container.py`; il limite è scritto nella spec del passo dinamico.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (perimetro di rete di Gradle).
- **Note:** D-203.

### Analizzatori

#### D-065 Un linguaggio con 0 file indicizzati risultava `fresh`
- **Descrizione:** un linguaggio poteva dirsi `fresh` senza un file nell'indice.
- **Spiegazione:** lo stato non guardava quanti file l'indice copre.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459` (16 novembre):
  - file: `scripts/engine_pass.py`, `scripts/pipeline/__init__.py`, `scripts/premap/__init__.py`, `scripts/premap/enry.py`, `scripts/premap/enry_facts.go`;
  - un linguaggio con 0 file indicizzati fallisce con la causa.
- **Verifica:** finale e conferma: «cpp failed: none of the 8 cpp files is in the index: …» per zlib.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-066–D-071.

#### D-066 I file mancanti di un linguaggio riuscito taciuti
- **Descrizione:** un linguaggio `fresh` con file fuori dall'indice non lo diceva.
- **Spiegazione:** il passaggio non contava i file dello snapshot assenti dall'indice.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`: un evento di buco `files-missing` con il numero e i motivi.
- **Verifica:** finale: la tabella «Linguaggi fresh con file fuori dall'indice» elenca 20 righe, con i motivi.
- **Stato:** risolto.
- **Note:** —

#### D-067 Un build o un run fallito accanto a uno riuscito spariva
- **Descrizione:** in un progetto con più build, il fallimento di una non compariva se un'altra riusciva.
- **Spiegazione:** il rapporto dello stadio teneva solo l'esito complessivo.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`: il build fallito resta nel rapporto dello stadio come buco.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-068 Un linguaggio letto dallo snapshot senza analyzer non era dichiarato
- **Descrizione:** un linguaggio senza analyzer non compariva da nessuna parte, nemmeno nello stato MCP.
- **Spiegazione:** il passaggio guardava solo i linguaggi degli analyzer.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`:
  - il linguaggio è dichiarato, anche nello stato MCP;
  - la pre-mappa lo dichiara per i linguaggi di programmazione che go-enry vede, ora con il tipo.
- **Verifica:**
  - prova vera su Kiri di go-enry con il tipo: solo C# segnalato in un progetto .NET;
  - finale: «Linguaggi senza analizzatore», plsql in 1 caso (1 file) e sql in 7 casi (51 file).
- **Stato:** risolto; i linguaggi senza analyzer sono un buco dichiarato (`no-analyzer`).
- **Note:** —

#### D-069 Le coppie di linguaggi che si chiamano non erano unite né dichiarate
- **Descrizione:** Go/C, Python/C, Java/C e simili: le chiamate fra i due linguaggi non sono risolte, e nulla lo diceva.
- **Spiegazione:** ogni stadio carica solo il proprio indice.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`, `scripts/pipeline/__init__.py` (`Union.APART`): il buco `not-joined`.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (`not-joined`).
- **Note:** —

#### D-070 La tabella «chi indicizza cosa» della pre-mappa scritta a mano
- **Descrizione:** la tabella poteva divergere dagli analyzer.
- **Spiegazione:** era scritta a mano.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`: la tabella deriva dagli analyzer.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-071 Linguaggio senza file con AST, e un linguaggio non elencato `fresh` per difetto
- **Descrizione:** un linguaggio di cui lo snapshot non legge nessun file entrava nel passaggio come gli altri, e un linguaggio non elencato era `fresh`.
- **Spiegazione:** il valore predefinito di un linguaggio non elencato era «fresh».
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `2bc7c7459`:
  - un linguaggio senza file con AST entra come non disponibile;
  - il predefinito diventa «missing».
- **Verifica:** finale, otel-demo: «c unavailable: none of the 1 c files was parsed by the snapshot (lexical: 1)».
- **Stato:** risolto.
- **Note:** —

#### D-072 TypeScript: alias di percorso e membri del workspace non presi dalla pre-mappa
- **Descrizione:** gli alias di percorso e i membri del workspace che il build tool dichiara non arrivavano all'indicizzatore.
- **Spiegazione:** l'indicizzatore non li prendeva dalla pre-mappa, cioè da tsc e da npm, pnpm o Yarn.
- **Progetto e caso:** audit della copertura, «stessa famiglia di Kotlin sotto Maven» — 16 novembre 2026.
- **Rimedio:** `64edfb930` (16 novembre), `scripts/engine_tools.py` e gli indicizzatori.
- **Verifica:** solo test locali; il commit dice che le prove vere su monorepo vanno fatte su Modal.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-073–D-082.

#### D-073 TypeScript: installazione fallita e dipendenza locale scartata taciute
- **Descrizione:** un'installazione fallita o una dipendenza locale scartata non comparivano.
- **Spiegazione:** non erano registrate come buchi.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: sono buchi dichiarati.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-074 Python: cartelle sorgenti e manifest dichiarati non passati a Pyright
- **Descrizione:** Pyright non aveva le cartelle sorgenti e i manifest che il progetto dichiara.
- **Spiegazione:** l'indicizzatore non li passava a Pyright né all'ambiente.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`, `scripts/indexers/python.py`.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-075 Python: un file fuori da ogni progetto senza motivo
- **Descrizione:** un file Python fuori da ogni progetto mancava dall'indice senza una causa.
- **Spiegazione:** nessun motivo era scritto per quel file.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: il file ha il suo motivo.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** quei file entrano poi nel grafo con `118689f69` (D-085).

#### D-076 C/C++: MSBuild trattato a parte
- **Descrizione:** i progetti MSBuild non seguivano la strada degli altri build non CMake.
- **Spiegazione:** l'indicizzatore C/C++ li trattava a parte.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`, `scripts/indexers/clang.py` e `scripts/indexers/clang_run.py`.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-077 C/C++: un configure senza compile_commands.json faceva morire lo stadio
- **Descrizione:** lo stadio C/C++ moriva quando un configure non scrive compile_commands.json.
- **Spiegazione:** il file mancante non era gestito come esito.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: il configure fallisce con la causa.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-078 Rust e Go: un file senza documento non diceva se il run era fallito
- **Descrizione:** un file assente dall'indice non diceva che il run del suo crate o modulo era fallito.
- **Spiegazione:** il motivo non guardava l'esito del run.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`, `scripts/indexers/rust.py` e `scripts/indexers/go.py`.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-079 Go: la regola dei nomi dei file (_GOOS, _GOARCH) non conosciuta
- **Descrizione:** un file escluso per il suo nome non aveva il motivo giusto.
- **Spiegazione:** l'indicizzatore Go non conosceva la regola dei suffissi _GOOS e _GOARCH.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`, `scripts/indexers/go.py`.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** D-139.

#### D-080 Vue e Svelte: un componente con template non dichiarato letto in parte
- **Descrizione:** un componente con template risultava letto per intero.
- **Spiegazione:** il template non è letto, e nulla lo diceva.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: il componente è dichiarato letto in parte.
- **Verifica:** finale, hoppscotch: «template not read: calls and bindings in it are not sites (400)».
- **Stato:** risolto; il template resta non letto, D-159.
- **Note:** D-159.

#### D-081 Lo stadio di posizione rispondeva per linguaggi non suoi
- **Descrizione:** lo stadio di posizione dava risposte fuori dai suoi linguaggi.
- **Spiegazione:** non filtrava per i suoi linguaggi.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: risponde solo per i suoi linguaggi.
- **Verifica:** solo test locali.
- **Stato:** risolto.
- **Note:** —

#### D-082 Markup senza lettore non dichiarato (Razor, JSP, Freemarker, Velocity, XHTML)
- **Descrizione:** quei file mancavano senza che nulla lo dicesse.
- **Spiegazione:** nessun lettore, e nessuna dichiarazione.
- **Progetto e caso:** audit della copertura — 16 novembre 2026.
- **Rimedio:** `64edfb930`: sono dichiarati mancanti.
- **Verifica:** solo test locali.
- **Stato:** buco dichiarato (markup senza lettore).
- **Note:** D-059.

#### D-083 Le correzioni degli adattatori Java e Kotlin le usava solo il banco
- **Descrizione:** un test di guardia segnalava passi definiti dagli adattatori e mai raggiunti dal driver: `same_range` di Java e `classify` di Kotlin (`8e89e94dc`, 14 novembre).
- **Spiegazione:** lo stadio costruiva il percorso a mano e applicava solo alcune correzioni; quelle due le usava il banco di prova, non il prodotto.
- **Progetto e caso:** stadio del grafo — 14 e 15 novembre 2026.
- **Rimedio:** `d06df0522` (15 novembre), `scripts/resolve_edges.py`: il percorso viene da `adapter_traversal`, l'unico punto che conosce le correzioni.
- **Verifica:**
  - il test di guardia non è più atteso rosso;
  - un test dello stadio controlla che ogni correzione sia chiamata;
  - sulle fixture Go, TypeScript e Rust le righe salvate sono identiche a prima.
- **Stato:** risolto.
- **Note:** —

#### D-084 scip-python: «Cannot find module»
- **Descrizione:** lo stadio Python moriva nel container con «Cannot find module».
- **Spiegazione:** su questo PC l'installazione npm di scip-python aveva perso `index.js`, e il tool si usava lo stesso.
- **Progetto e caso:** PC di sviluppo — 16 novembre 2026.
- **Rimedio:** `faf7a3b22` (16 novembre), `scripts/indexers/runtime.py`:
  - il tool si usa solo se lo script che esegue c'è;
  - altrimenti si reinstalla una volta, e se manca ancora lo dice con la causa.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-085 80 file Python su 211 senza documento
- **Descrizione:** sul codice di Daodan con i suoi test, 80 file Python su 211 restavano senza documento.
- **Spiegazione:** l'analyzer indicizzava solo i progetti dichiarati.
- **Progetto e caso:** il codice di Daodan — 16 novembre 2026.
- **Rimedio:** `118689f69` (16 novembre), `scripts/indexers/python.py` e `scripts/premap/__init__.py`:
  - quando la pre-mappa trova Python che nessuna unità tiene, il checkout è il run;
  - ogni progetto interno resta la radice dei propri import;
  - il codice fuori non si vede per nome, perché sarebbe una supposizione; lo chiude il passo dinamico.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-075.

#### D-086 scip-python 0.6.8 non parte su Windows
- **Descrizione:** l'indicizzatore Python non partiva sull'host Windows.
- **Spiegazione:** scip-python 0.6.8 non parte su Windows (dal commit).
- **Progetto e caso:** host Windows — 14 novembre 2026.
- **Rimedio:** `626ebb3a2` (14 novembre): Python gira nel container.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-087 phazly: bersagli Python diversi da quelli del passaggio per posizione
- **Descrizione:** su phazly il grafo dall'indice e il passaggio per posizione davano 13 bersagli Python diversi, e 114 riferimenti li aveva solo il passaggio per posizione.
- **Spiegazione:** «le due cause corrette», che il commit non nomina: da verificare.
- **Progetto e caso:** phazly — 14 novembre 2026.
- **Rimedio:** `09537b2b9` (14 novembre).
- **Verifica:** bersagli diversi da 13 a 1, riferimenti del solo passaggio per posizione da 114 a 94.
- **Stato:** risolto.
- **Note:** —

#### D-088 Buchi Python senza causa
- **Descrizione:** buchi Python che non dicono perché:
  - conferma, 3 casi: no-occurrence 117, undefined-project-symbol 74, dangling-local 9 (96,0 % di risposta);
  - finale: no-occurrence 484, undefined-project-symbol 199, dangling-local 117, no-position 13.
- **Spiegazione:** dal commit `a6156b7a2`:
  - undefined-project-symbol: tre difetti di scip-python 0.6.8. Un nome che l'`__init__` di una distribuzione riesporta (`sa.Column`, `typer.Typer`, `pytest.fail`) non andava alla distribuzione; `__name__`, `__file__`, `__package__` e `__doc__` non erano della libreria standard; `import semver`, definito come `src.semver`, non passava per la radice sorgente dichiarata;
  - no-occurrence e dangling-local: un valore che il checker tipizza Unknown o Any, oppure un nome che il checker lega e scip-python non nomina.
- **Progetto e caso:** corpus Python — finale e conferma; fastapi (`aabb90126964`) e python-semver (`b6e83e3e40d3`) nella misura del commit; 16 novembre 2026.
- **Rimedio:** `a6156b7a2` (16 novembre), `scripts/indexers/python.py` e `scripts/indexers/python_unbound.py`:
  - l'adattatore risolve i tre difetti; la distribuzione si cerca nel file d'ambiente della corsa;
  - una passata del checker (l'hover del language server di Pyright 1.1.414 su ogni membro) dà a ogni buco restante la sua causa.
- **Verifica:** dal commit, su Modal ai commit fissati: fastapi da 167 a 102 buchi (risposte dal 93,3 % al 95,9 %), python-semver da 64 a 54 (dal 97,2 % al 97,7 %); undefined-project-symbol da 65 e 10 a 0.
- **Stato:** risolto; i buchi restanti sono dichiarati con la causa del checker.
- **Note:** —

#### D-089 Kotlin sotto Maven: 0 file su 2 indicizzati
- **Descrizione:** nel pilota su Modal del 15 novembre (`dcdffacb0`) Kotlin sotto Maven dava 0 file su 2 indicizzati, senza source set Gradle.
- **Spiegazione:** scip-java indicizza Kotlin solo sotto Gradle.
- **Progetto e caso:** il pilota su 5 casi del driver Modal — 15 novembre 2026.
- **Rimedio:** `ea1e2b7d6` (15 novembre), `scripts/indexers/kotlin.py` e `scripts/premap/maven.py`:
  - sotto Maven la preparazione lancia, per ogni modulo, l'indicizzatore Kotlin che scip-java porta con sé;
  - lo lancia sui file delle cartelle sorgenti che il modello di Maven dichiara: l'effective-pom, anche quelle di kotlin-maven-plugin e build-helper;
  - usa il classpath di Maven, poi riunisce l'indice.
- **Verifica:** su Modal: 2 file su 2, 10 chiamate su 10, cartelle sorgenti 3 su 3 (erano 0 file e 1 cartella).
- **Stato:** risolto.
- **Note:** il motivo di un file mancante non nomina più Gradle.

#### D-090 Java sotto Gradle: aggregazione in avanti e javap sulla cartella sbagliata
- **Descrizione:** Java sotto Gradle aveva il buco delle implementazioni.
- **Spiegazione:** l'aggregazione in avanti e javap leggevano `target/`, la cartella di Maven, anche sotto Gradle.
- **Progetto e caso:** build JVM — 15 novembre 2026.
- **Rimedio:** `7b1a77e8d` (15 novembre), `scripts/indexers/java.py`, `jvm.py` e `kotlin.py`:
  - leggono la cartella del build che ha girato, `target/` per Maven e `build/` per Gradle, in ogni modulo;
  - senza un indice in avanti uguale, il contratto lo dichiara come buco.
- **Verifica:** su Modal, Gradle Java completo senza il buco delle implementazioni.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-091, D-092 e D-093.

#### D-091 Sotto Maven l'indice Java senza il Kotlin dei moduli
- **Descrizione:** una chiamata da Java a Kotlin non arrivava a destinazione.
- **Spiegazione:** sotto Maven il build di Java non indicizzava il Kotlin dei moduli.
- **Progetto e caso:** Maven misto Java e Kotlin — 15 novembre 2026.
- **Rimedio:** `7b1a77e8d`: anche il build di Java indicizza il Kotlin dei moduli (`jvm.MAVEN_KOTLIN`, condiviso), così la chiamata finisce dove lo stesso indice la definisce.
- **Verifica:** su Modal, Maven misto: Java 4 chiamate su 4, Kotlin 10 su 10, nessun buco.
- **Stato:** risolto.
- **Note:** D-089.

#### D-092 Un build JVM che Daodan non esegue (sbt, Bazel) non era nominato
- **Descrizione:** il motivo non diceva che il build è sbt o Bazel.
- **Spiegazione:** il motivo non nominava il build.
- **Progetto e caso:** build JVM — 15 novembre 2026.
- **Rimedio:** `7b1a77e8d`: il build è nominato nel motivo.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (sbt e Bazel non eseguiti).
- **Note:** —

#### D-093 Un indice lasciato da un build finito in errore non lo diceva
- **Descrizione:** un indice poteva venire da un build fallito senza che il risultato lo dicesse.
- **Spiegazione:** il risultato non guardava l'esito del build.
- **Progetto e caso:** build JVM — 15 novembre 2026.
- **Rimedio:** `7b1a77e8d`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-094 Java e Kotlin giravano solo alla radice del progetto
- **Descrizione:** una build in una sottocartella, come il servizio Java di robot-shop o le build Gradle di otel-demo, restava fuori.
- **Spiegazione:** gli indicizzatori JVM partivano solo dalla radice.
- **Progetto e caso:** robot-shop (`55292e2199f2`), otel-demo (`b825c7c25726`) — 15 novembre 2026.
- **Rimedio:** `1dcfba42a` (15 novembre), `scripts/indexers/java.py`, `jvm.py` e `kotlin.py`:
  - le cartelle sono il Gradle e il Maven più esterni della pre-mappa, ognuno in un container suo;
  - ogni indice è nominato dal checkout con la cartella della sua build, e ogni build dice il suo stato;
  - una build che fallisce lascia gli indici delle altre;
  - senza build nella pre-mappa nulla parte, e la causa è detta.
- **Verifica:** finale, otel-demo: le sue build Gradle girano e falliscono per D-105.
- **Stato:** risolto.
- **Note:** D-105.

#### D-095 Maven e Gradle nella stessa cartella: occorrenze doppie
- **Descrizione:** una cartella con pom.xml e build Gradle dava due indici degli stessi file.
- **Spiegazione:** due indici degli stessi file raddoppiano le occorrenze, perché `code_graph.Index.load` li accoda.
- **Progetto e caso:** jvm-java-version-conflict — 16 novembre 2026.
- **Rimedio:** `9fe650a3a` (16 novembre), `scripts/indexers/java.py`, `jvm.py` e `kotlin.py`:
  - scip-java riceve `--build-tool` dalla pre-mappa;
  - gira Gradle, e Maven solo se Gradle non dà indice.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-096, D-097 e D-180.

#### D-096 Una radice con solo settings.gradle.kts non riconosciuta da scip-java
- **Descrizione:** scip-java non partiva su una build composta con solo `settings.gradle.kts` alla radice.
- **Spiegazione:** scip-java 0.14.2 non riconosce una radice con solo settings.gradle.kts.
- **Progetto e caso:** jvm-gradle-kts-catalog-composite — 16 novembre 2026.
- **Rimedio:** `9fe650a3a`, `scripts/indexers/jvm.py`: la preparazione vi scrive un `gradlew` che lancia il Gradle portato da Daodan.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-097 Kotlin presente solo negli script di build dato `failed`
- **Descrizione:** un progetto con Kotlin solo negli script di build (.gradle.kts, buildSrc) aveva Kotlin `failed`.
- **Spiegazione:** nessun compito di compilazione Kotlin compila quei file.
- **Progetto e caso:** jvm-gradle-kts-catalog-composite, jvm-java-version-conflict, jvm-spring-boot-managed — finale, 16 novembre 2026.
- **Rimedio:** `9fe650a3a`, `scripts/indexers/kotlin.py`: Kotlin è `unavailable` con la causa, prima di ogni container.
- **Verifica:** finale, 3 casi: «the build's own Kotlin only (… Gradle scripts and buildSrc files): the pre-map reads them through Gradle, and no Kotlin compile task compiles them».
- **Stato:** buco dichiarato («the build's own Kotlin only»).
- **Note:** —

#### D-098 File Kotlin che nessun compito di compilazione compila o elenca
- **Descrizione:** file Kotlin fuori dall'indice in Kotlin `fresh`:
  - jvm-kmp-common-jvm: 2 su 5, «Gradle script: no KotlinCompile task compiles it»;
  - jvm-kotlin-source-sets: 3 su 5, di cui 2 script Gradle e 1 «no Kotlin compile task of the build lists it»;
  - klaxon: 7 su 103, cioè 5 script Gradle, 1 «buildSrc: compiled by its own build, where scip-java's tasks do not run» e 1 che nessun compito elenca.
- **Spiegazione:** quei file non sono compilati dai compiti in cui girano i compiti di scip-java.
- **Progetto e caso:** jvm-kmp-common-jvm, jvm-kotlin-source-sets, klaxon (`1173bdc568a6`) — finale, 16 novembre 2026.
- **Rimedio:** il motivo per file (`2bc7c7459`, D-066).
- **Verifica:** finale.
- **Stato:** buco dichiarato (i motivi citati).
- **Note:** —

#### D-099 javapoet: scip-java 0.14.2 non indicizza Java 8
- **Descrizione:**
  - in real-3 l'osservatore di javapoet falliva perché la build girava sul JDK dell'immagine (`7532ed2e7`);
  - nessuna versione di scip-java indicizza javapoet come è dichiarato.
- **Spiegazione:** scip-java 0.14.2 non supporta più Java 8 (dalla 0.13.0).
- **Progetto e caso:** javapoet (`b9017a9503b7`) — real-3, 16 novembre 2026.
- **Rimedio:** `492a7b212` (16 novembre), `scripts/indexers/java.py` e `scripts/indexers/jvm.py`:
  - l'analisi sceglie il JDK con la regola dell'osservatore (`build_jdk`, ora in `indexers/jvm.py`);
  - un JDK dichiarato sotto il 17 si indicizza sul 17, con il buco `jdk_unsupported`.
- **Verifica:** su Modal, javapoet: indice Java `fresh` con i buchi `jdk_unsupported` e `build_edited` (`609ca96dd`).
- **Stato:** buco dichiarato (`jdk_unsupported`).
- **Note:** D-100, D-178.

#### D-100 javapoet: il compilerId di Error Prone scavalca il wrapper di javac
- **Descrizione:** la build di javapoet non dava l'indice.
- **Spiegazione:** il compilerId di Error Prone nel pom scavalca il wrapper di javac con cui scip-java aggancia il suo plugin.
- **Progetto e caso:** javapoet — 16 novembre 2026.
- **Rimedio:** `492a7b212`:
  - se l'indice arriva solo togliendo Error Prone dal pom, il buco `build_edited` dice cosa è stato tolto e gli errori della prima build;
  - prima lo diceva solo il log.
- **Verifica:** come D-099.
- **Stato:** buco dichiarato (`build_edited`).
- **Note:** —

#### D-101 Una toolchain Gradle sotto il 17 compilava sul JDK dell'immagine
- **Descrizione:** analisi e osservatore non compilavano sul JDK della toolchain dichiarata.
- **Spiegazione:**
  - Gradle 9 gira su Java 17 ma compila e testa con le toolchain dichiarate, come dice la sua documentazione;
  - quei JDK non erano installati;
  - il plugin del compilatore di scip-java 0.14.2 è costruito per Java 17 e non si carica in un javac più vecchio.
- **Progetto e caso:** build Gradle con toolchain 8 e 11 — 16 novembre 2026.
- **Rimedio:** `0997b5d4f` (16 novembre), `scripts/indexers/java.py`:
  - la preparazione installa il JDK di ogni toolchain e lo passa a Gradle;
  - quella build dà il buco `jdk_unsupported` con la versione dichiarata e dove.
- **Verifica:** un test fissa l'osservatore su una toolchain 11.
- **Stato:** buco dichiarato (`jdk_unsupported`).
- **Note:** D-050, D-103.

#### D-102 Maven con Java 5 e 6: nessun indice
- **Descrizione:** nella misura su Modal con 18 progetti, uno per versione, Maven con Java 5 e 6 falliva.
- **Spiegazione:** javac 17 non compila sotto il 7.
- **Progetto e caso:** jvm-ver-* — 16 novembre 2026.
- **Rimedio:** `21b3cb39b` (16 novembre), `scripts/indexers/java.py`, `jvm.py` e `kotlin.py`:
  - il secondo tentativo dichiarato alza a 8 i livelli sotto l'8 nei pom;
  - ogni modifica è nel buco `build_edited`, con l'errore del build dichiarato.
- **Verifica:**
  - java-versions, sul codice a `68a846a4a`: Java `fresh` e osservato in tutte le 18 fixture, 37 file su 37 e 453 siti tutti con risposta;
  - prima di `21b3cb39b` sette non davano indice (README del benchmark).
- **Stato:** buco dichiarato (`build_edited`, `jdk_unsupported`).
- **Note:** dallo stesso commit vengono D-103, D-104 e D-179.

#### D-103 Gradle con toolchain 8 e 11, anche con Kotlin accanto: nessun indice
- **Descrizione:** stessa misura di D-102.
- **Spiegazione:** il plugin di scip-java non si carica sotto il 17.
- **Progetto e caso:** jvm-ver-* — 16 novembre 2026.
- **Rimedio:** `21b3cb39b`. Sotto Gradle `jvm.RAISE_LEVELS` sostituisce la toolchain sotto il JDK su cui gira il build e alza i livelli, per Java, Kotlin e l'osservatore; tutto è nel buco `build_edited`.
- **Verifica:** come D-102.
- **Stato:** buco dichiarato (`build_edited`).
- **Note:** D-101.

#### D-104 Gradle con livello 6: nessun indice
- **Descrizione:** stessa misura di D-102: Gradle con livello 1.6.
- **Spiegazione:** javac 17 non compila quel livello.
- **Progetto e caso:** jvm-ver-* — 16 novembre 2026.
- **Rimedio:** `21b3cb39b`, `jvm.RAISE_LEVELS`.
- **Verifica:** come D-102.
- **Stato:** buco dichiarato (`build_edited`).
- **Note:** —

#### D-105 otel-demo: «Cannot invoke method toPath() on null object» in ad e recommendation
- **Descrizione:** finale, otel-demo: Java e Kotlin `failed`, «scip-java wrote no index (preparation exited with code 1)».
- **Spiegazione:**
  - le build, in `src/ad/build.gradle:70` e `src/recommendation/build.gradle:55`, calcolano `project.projectDir.parentFile.parentFile.toPath()` per arrivare a `pb/` alla radice del repository;
  - la cartella del build era copiata da sola in `/work`, così il nonno era null.
- **Progetto e caso:** otel-demo (`b825c7c25726`) — finale, 16 novembre 2026.
- **Rimedio:** `39805f5e7` (16 novembre), `scripts/indexers/jvm.py`, `java.py` e `kotlin.py`, `scripts/dynamic/jvm.py`:
  - il container di ogni build contiene l'intero checkout (`jvm.run(..., checkout=)`);
  - il build gira nella sua cartella (`DAODAN_ROOT`, `WORK=/work/$DAODAN_ROOT`).
- **Verifica:** giro `jvm-otel-android`, otel-demo:
  - Java `fresh`, 9 file su 9, 693 siti tutti con risposta (in finale: `failed`, senza indice);
  - l'osservatore Java registra 297 siti e 297 archi, e chiude 2 buchi.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-106, D-108 e D-109.

#### D-106 otel-demo fraud-detection sul JDK 21 di un altro build
- **Descrizione:** fraud-detection falliva con «Inconsistent JVM-target compatibility … (21) and (17)».
- **Spiegazione:**
  - fraud-detection dichiara Kotlin jvmTarget 17, senza target Java né toolchain, e il suo Dockerfile costruisce su gradle:9.8.2-jdk17;
  - l'indice riceveva le toolchain dell'intero repository, e `wanted_jdk` sceglieva il 21 di ad e recommendation;
  - compileJava puntava al 21, e il plugin di Kotlin falliva.
- **Progetto e caso:** otel-demo — finale, 16 novembre 2026.
- **Rimedio:** `39805f5e7`, `scripts/indexers/jvm.py` (`applying`): un JDK conta per un build solo se lo dichiarano i suoi file o un file in una cartella sopra; vale anche per l'osservatore (`build_jdk`).
- **Verifica:** giro `jvm-otel-android`: l'errore di compatibilità non c'è più, e fraud-detection si ferma su D-107.
- **Stato:** risolto.
- **Note:** D-107.

#### D-107 otel-demo fraud-detection: protos che solo il Dockerfile copia
- **Descrizione:** giro `jvm-otel-android`, otel-demo: Kotlin `failed`, «none of the 3 kotlin files is in the index: Gradle script: no KotlinCompile task compiles it (2), no Kotlin compile task of the build lists it (1)».
- **Spiegazione:**
  - `src/fraud-detection/src/main/kotlin/frauddetection/main.kt:14` importa `oteldemo.Demo.*`, le classi che il plugin protobuf genera dai proto;
  - il blocco `protobuf { }` di `src/fraud-detection/build.gradle.kts:78-99` non nomina una cartella dei proto, quindi usa `src/main/proto`;
  - quella cartella la riempie solo il Dockerfile del servizio: `src/fraud-detection/Dockerfile:10`, `COPY ./pb/ ./src/main/proto/`;
  - il build dichiarato, girato sul checkout, non genera quelle classi.
- **Progetto e caso:** otel-demo (`b825c7c25726`) — giro `jvm-otel-android`, 16 novembre 2026.
- **Rimedio:** —. Gli stadi di un Dockerfile si leggono da `f024ba3a3`, ma oggi indicizza dentro uno stadio solo Go (`f04dab9d5`, D-141); la via per C e C++ è in corso (D-135), e la JVM non la usa.
- **Verifica:** —
- **Stato:** aperto (android-sdk): build dichiarata solo in un Dockerfile.
- **Note:** D-135, D-141.

#### D-108 Android: classpath dei test unitari non risolti, nessun compito Android
- **Descrizione:** finale: Kotlin `failed` con «Could not resolve all artifacts for configuration ':core:releaseUnitTestRuntimeClasspath'» e «':app:debugUnitTestCompileClasspath'».
- **Spiegazione:**
  - il plugin Gradle di scip-java non mette nessun compito Android in `scipCompileAll` (issue 177 di scip-java, chiusa come non pianificata);
  - eppure aggiunge il suo plugin javac a ogni JavaCompile e scrive la configurazione di ogni KotlinCompile.
- **Progetto e caso:** jvm-android-app-lib, mix-poly-firebase — finale, 16 novembre 2026.
- **Rimedio:** `39805f5e7`:
  - `scripts/indexers/jvm.py` (`SCIP_INDEX`, `ANDROID_INIT`), `java.py` e `kotlin.py`;
  - con l'SDK installato, un build Gradle lancia dopo i compiti di scip-java `daodanAndroidCompile`, che dipende dai compiti `compile*Debug(UnitTest)?Sources` di ogni progetto.
- **Verifica:** giro `jvm-otel-android`: i due casi non si fermano più sui classpath e lanciano le compilazioni debug, fino a `:app:processFreeDebugGoogleServices` e `:app:processDebugGoogleServices`, dove si fermano su `google-services.json` (D-109). Che le varianti diano l'indice è da verificare.
- **Stato:** aperto (dynamic-jvm-2): manca la prova su un build con il suo `google-services.json`.
- **Note:** D-109.

#### D-109 Android: build fermo su `google-services.json` mancante
- **Descrizione:** giro `jvm-otel-android`, Kotlin `failed`: «Execution failed for task ':app:processFreeDebugGoogleServices'. > File google-services.json is missing. The Google Services Plugin cannot function without it.»:
  - jvm-android-app-lib cerca da `/work/app/src/free/debug/google-services.json` fino a `/work/app/google-services.json`;
  - mix-poly-firebase si ferma in `:app:processDebugGoogleServices` e cerca in `/work/android/app/…`.
- **Spiegazione:** il plugin Google Services (com.google.gms.google-services) legge la configurazione del progetto Firebase, che lo sviluppatore scarica dalla console e il repository non tiene; le fixture non l'hanno.
- **Progetto e caso:** jvm-android-app-lib, mix-poly-firebase — giro `jvm-otel-android`, 16 novembre 2026.
- **Rimedio:** `39805f5e7`, `scripts/indexers/jvm.py` (`INPUTS`, `missing_inputs`). Il buco `build_input_missing` dice: «the build stopped without google-services.json, which the Google Services Gradle plugin (com.google.gms.google-services) reads: the Firebase project's configuration, which a developer downloads from the Firebase console, kept out of the repository; Daodan makes none, so the build gives nothing».
- **Verifica:** giro `jvm-otel-android`: il buco è in `steps.analyze.engines.scip-kotlin.gaps` di entrambi i casi.
- **Stato:** buco dichiarato (`build_input_missing`).
- **Note:** D-108.

#### D-110 kotlinconf: «Task with name 'compileKotlinJvm' not found in project ':app:adminApp'»
- **Descrizione:** giro `jvm-kotlinconf`, Kotlin `failed`: «scip-java wrote no index (preparation exited with code 1): determine the dependencies of task ':app:adminApp:scipCompileAll'. > Task with name 'compileKotlinJvm' not found in project ':app:adminApp'.».
- **Spiegazione:**
  - il plugin Gradle di scip-java 0.14.2 (`scip-gradle-plugin/src/main/java/org/scip_code/scip_java/gradle/ScipGradlePlugin.java`) mette in `triggers`, per ogni progetto con il plugin Kotlin Multiplatform, i nomi `compileKotlinJvm` e `compileTestKotlinJvm`, senza guardare se il progetto ha un target `jvm()`;
  - poi `project.getTasks().create("scipCompileAll").dependsOn(triggers)` li chiede per nome, e Gradle si ferma su un nome che il progetto non ha;
  - in kotlinconf `app/adminApp` dichiara solo `js(IR)` e `app/webApp` solo `wasmJs` e `js`: nessuno dei due ha `compileKotlinJvm`.
- **Progetto e caso:** kotlinconf (`146e891c150c`) — giro `jvm-kotlinconf`, 16 novembre 2026.
- **Rimedio:** in corso (dynamic-jvm-2).
- **Verifica:** —
- **Stato:** aperto (dynamic-jvm-2).
- **Note:** D-058.

#### D-111 jhipster: 14 file Java con il documento senza occorrenze
- **Descrizione:** finale: 15 file Java su 136 fuori dall'indice, 14 «document without occurrences» e 1 «no document in the index».
- **Spiegazione:** da verificare.
- **Progetto e caso:** jhipster-sample (`6b000b5d23a3`) — finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** —

#### D-112 Un file Java senza documento in due fixture Maven
- **Descrizione:** finale: jvm-maven-multi-bom-profile 1 file su 4 e jvm-protobuf-generated 1 su 2, «no document in the index».
- **Spiegazione:** da verificare.
- **Progetto e caso:** jvm-maven-multi-bom-profile, jvm-protobuf-generated — finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** —

#### D-113 C#: un progetto che Msbuild rifiuta ferma il ripristino intero
- **Descrizione:** zlib in giro-2, finale e conferma: «scip-dotnet wrote no index (no documents were indexed; Msbuild failed when processing the file '/work/contrib/dotzlib/DotZLib/DotZLib.csproj' with message: The project file "" must be opened in a version of Visual Studio IDE that supports it and converted to the latest version before it can be built».
- **Spiegazione:** un solo progetto che non si può trattare fermava tutti gli altri:
  - in zlib è DotZLib.csproj, un progetto `<VisualStudioProject>` del vecchio formato, che Msbuild rifiuta;
  - in eShop `dotnet restore eShop.slnx` falliva per intero su un solo progetto che vuole un workload MAUI (NETSDK1147): nessun progetto aveva i suoi pacchetti, Roslyn non legava nessun simbolo di pacchetto, e ne venivano circa 4.400 buchi no-occurrence (dal commit `0cdbae9b2`).
- **Progetto e caso:** zlib (`51b7f2abdade`) — giro-2, finale, conferma; eShop (`913acea66708`) — misura di csharp-dotnet; 16 novembre 2026.
- **Rimedio:**
  - `73b645531` (16 novembre), `scripts/indexers/csharp.py`: un progetto `<VisualStudioProject>`, o una soluzione che ha solo quelli, è `unavailable` con il formato nominato, e non viene lanciato;
  - `0cdbae9b2` (16 novembre), `scripts/preparation.py` (`RESTORES`): se la soluzione non si ripristina, si ripristina ogni progetto che `dotnet sln list` nomina, e il fallimento resta il buco `restore_failed`.
- **Verifica:** solo test (`tests/test_codebase_map_preparation.py`, `test_a_dotnet_solution_that_does_not_restore_restores_each_of_its_projects_and_stays_a_gap`); nessun giro su zlib o eShop dopo i commit: da verificare.
- **Stato:** risolto; il progetto legacy è un buco dichiarato (`unavailable`), e un progetto che non si ripristina resta `restore_failed`.
- **Note:** D-114.

#### D-114 C#: 56,1 % di risposta
- **Descrizione:** finale: C# `fresh` in 4 casi su 5, 561 file su 561, quota di risposta 56,1 %.
  - buchi: no-occurrence 5.358, no-position 1.021, dangling-local 144, undefined-project-symbol 20;
  - casi `fresh`: mix-dotnet-central, eShop, otel-demo, voting-app.
- **Spiegazione:** le cause misurate da csharp-dotnet, poi corrette in `0cdbae9b2`:
  - il ripristino falliva intero per un solo progetto di workload (D-113): circa 4.400 buchi no-occurrence in eShop;
  - la colonna della riga 1 di un file con il BOM (D-115);
  - i nomi del chiamato qualificati (D-117) e con argomenti di tipo (D-116).
- **Progetto e caso:** mix-dotnet-central, eShop (`913acea66708`), otel-demo, voting-app (`63e9150ca17a`) — finale, 16 novembre 2026.
- **Rimedio:**
  - l'analyzer C# arriva con `56e65e114` (16 novembre);
  - `73b645531` dà una causa a parte dei buchi di eShop (D-116, D-118, D-119, D-120);
  - `0cdbae9b2` corregge il ripristino, il BOM e i nomi (D-113, D-115, D-116, D-117).
- **Verifica:** nessun giro sul corpus dopo `0cdbae9b2`: la nuova quota di risposta è da verificare.
- **Stato:** aperto (csharp-dotnet).
- **Note:** D-113, D-115, D-116, D-117, D-198.

#### D-115 La colonna della riga 1 di un file con il BOM
- **Descrizione:** csharp-dotnet ha misurato riferimenti della riga 1 senza risposta nei file che iniziano con il BOM.
- **Spiegazione:** un BOM UTF-8 in testa al file spostava di uno le colonne della riga 1 fra lo snapshot, che conta i suoi tre byte, e Roslyn o tsc, le cui colonne UTF-16 iniziano dopo di esso.
- **Progetto e caso:** i casi C# — misura di csharp-dotnet, 16 novembre 2026; vale per ogni linguaggio.
- **Rimedio:** `0cdbae9b2` (16 novembre), `scripts/code_graph.py` (`BOM`): `Index.to_bytes` e `from_bytes` lo saltano, per ogni linguaggio.
- **Verifica:** solo test (`tests/test_codebase_map_indexers_csharp.py`, `test_a_byte_order_mark_moves_no_column_of_the_first_line`).
- **Stato:** risolto.
- **Note:** D-114.

#### D-116 C#: nomi del chiamato con argomenti di tipo
- **Descrizione:** un chiamato scritto con argomenti di tipo non ha occorrenza nell'indice ed è un buco.
- **Spiegazione:** `ScipCSharpSyntaxWalker` non ha `VisitGenericName`, nella 0.2.16 come sul suo ramo main: scip-dotnet scrive occorrenze solo per i nomi semplici.
- **Progetto e caso:** eShop — misura su Modal al suo commit, con scip-dotnet 0.2.16, 16 novembre 2026.
- **Rimedio:**
  - `73b645531` (16 novembre), `scripts/indexers/csharp.py`: il buco porta la causa `TYPE_ARGUMENTS`;
  - `0cdbae9b2` (16 novembre), `scripts/languages/semantic.py` (`_generic_name`): una chiamata come `AddSingleton<A, B>()` è nominata dal suo nome, e resta un buco della classe giusta.
- **Verifica:** la misura su eShop di `73b645531`; `tests/test_codebase_map_indexers_csharp.py` (`test_a_call_written_with_type_arguments_is_named_by_its_name_and_its_hole_says_why`).
- **Stato:** buco dichiarato (`TYPE_ARGUMENTS`).
- **Note:** dallo stesso commit vengono D-118–D-120; i nomi qualificati, D-117.

#### D-117 C#: nomi del chiamato qualificati
- **Descrizione:** csharp-dotnet ha misurato, fra le cause del 56,1 % (D-114), i nomi del chiamato qualificati, come `new Shop.Core.Models.User()`.
- **Spiegazione:** il lettore dei nomi del chiamato (`_TreeSitterEvidence.parts`, `scripts/languages/semantic.py`) non trattava il `qualified_name` di C#, il tipo scritto con il suo namespace.
- **Progetto e caso:** i casi C# — misura di csharp-dotnet, 16 novembre 2026.
- **Rimedio:** `0cdbae9b2` (16 novembre), `scripts/languages/semantic.py`: un `qualified_name` di C# è nominato attraverso il suo namespace, e si risolve.
- **Verifica:** solo test (`tests/test_codebase_map_indexers_csharp.py`, `test_a_type_written_with_its_namespace_is_named_by_it`).
- **Stato:** risolto.
- **Note:** D-114, D-116.

#### D-118 C#: i membri dei tipi anonimi erano locali senza definizione
- **Descrizione:** eShop: 138 buchi dangling-local.
- **Spiegazione:** scip-dotnet chiama locali i membri dei tipi anonimi e non li definisce.
- **Progetto e caso:** eShop — misura su Modal, 16 novembre 2026.
- **Rimedio:** `73b645531`:
  - 135 membri di tipi anonimi sono definiti dove `new { X = }` li nomina;
  - i membri dei blocchi di estensione di C# 14 hanno la classe EXTENSION.
- **Verifica:** dangling-local da 138 a 1.
- **Stato:** risolto; i membri dei blocchi di estensione sono un buco dichiarato (EXTENSION).
- **Note:** —

#### D-119 C#: membri dei source generator e `args` dei top-level statement senza causa
- **Descrizione:** eShop: 17 buchi undefined-project-symbol.
- **Spiegazione:** scip-dotnet indicizza solo i documenti del progetto, quindi non i membri generati, e `args` dei top-level statement lo dichiara il compilatore.
- **Progetto e caso:** eShop — misura su Modal, 16 novembre 2026.
- **Rimedio:** `73b645531`: le classi GENERATED e TOP_LEVEL.
- **Verifica:** undefined-project-symbol da 17 a 0.
- **Stato:** buco dichiarato (GENERATED, TOP_LEVEL).
- **Note:** —

#### D-120 C#: Catalog.API non si caricava sotto la globalizzazione invariante
- **Descrizione:** eShop: NETSDK1188 su Catalog.API.
- **Spiegazione:** la globalizzazione invariante rifiuta ogni cultura salvo quella invariante, e le risorse per cultura di un pacchetto fanno fallire MSBuild.
- **Progetto e caso:** eShop — misura su Modal, 16 novembre 2026.
- **Rimedio:** `73b645531`: l'ambiente ha `DOTNET_SYSTEM_GLOBALIZATION_PREDEFINED_CULTURES_ONLY=false`.
- **Verifica:** la misura su eShop del commit.
- **Stato:** risolto.
- **Note:** —

#### D-121 Lo script di C e C++ cancellava la cartella in cui scrive il risultato
- **Descrizione:** l'indice C/C++ finiva `failed` senza una run.
- **Spiegazione:** la cartella del risultato sta dentro quella di lavoro, e lo script la creava prima di svuotare quella di lavoro, così il risultato non veniva mai scritto.
- **Progetto e caso:** indicizzatore C/C++ — 15 novembre 2026.
- **Rimedio:** `c089b3540` (15 novembre), `scripts/indexers/clang_run.py`: la crea dopo.
- **Verifica:** la prova reale nel container passa con `a3dad5e39` (D-122).
- **Stato:** risolto.
- **Note:** —

#### D-122 CMake: il fornitore delle dipendenze nominato prima di essere definito
- **Descrizione:** la configurazione moriva a `project()` e non registrava nulla.
- **Spiegazione:** CMake accetta come fornitore delle dipendenze solo un comando già definito, e lo script lo nominava prima.
- **Progetto e caso:** prova reale di C e C++ nel container — 15 novembre 2026.
- **Rimedio:** `a3dad5e39` (15 novembre), `scripts/indexers/clang_run.py`: l'ordine è giusto.
- **Verifica:** la prova nel container dà l'unità `unavailable` con fmt e il suo URL, come deve.
- **Stato:** risolto.
- **Note:** D-132.

#### D-123 scip-clang usava i processori della macchina
- **Descrizione:** scip-clang lanciava tanti compilatori quanti processori ha la macchina.
- **Spiegazione:** `--jobs` veniva dalla macchina, non dalla parte che il chiamante dà al container.
- **Progetto e caso:** indicizzatore C/C++ — 15 novembre 2026.
- **Rimedio:** `d28dc1442` (15 novembre), `scripts/indexers/clang.py` e `clang_run.py` (`clang_run.py UNITS_JSON OUT_DIR JOBS`, `--jobs={jobs}`).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-124 L'errore di CMake riscritto con righe ricavate dal testo
- **Descrizione:** l'errore di CMake arrivava con righe ricostruite, non com'è scritto.
- **Spiegazione:** lo script estraeva righe dal testo dell'errore.
- **Progetto e caso:** indicizzatore C/C++ — 14 novembre 2026.
- **Rimedio:** `377925c52` (14 novembre), `scripts/indexers/clang.py` e `clang_run.py`: l'errore resta com'è scritto.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-125 vcpkg e Conan: il configure senza l'installazione del gestore
- **Descrizione:** in sys-cpp-vcpkg-conan il configure falliva; con `ee456d55a` (15 novembre) quel caso restava «invariato, perché il suo configure fallisce».
- **Spiegazione:** il configure dell'analizzatore non eseguiva l'installazione del gestore né leggeva la cache iniziale che questa scrive.
- **Progetto e caso:** sys-cpp-vcpkg-conan — 15 e 16 novembre 2026.
- **Rimedio:** `f9fde7c1e` (16 novembre), `scripts/indexers/clang.py` e `clang_run.py`:
  - riusa la scelta della pre-mappa: il gestore che il toolchain file del preset nomina, altrimenti vcpkg;
  - riusa la sua riga di installazione e `init.cmake`;
  - la preparazione ha il CMake fissato, i registri e gli host del gestore;
  - un'installazione fallita è `restore_failed`.
- **Verifica:** finale e conferma: sys-cpp-vcpkg-conan, cpp `fresh`.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-126–D-129; per l'osservatore, D-177.

#### D-126 Un configure che legge un submodule non scaricato
- **Descrizione:** finale e conferma: «.: the configure reads third_party/fmt: a git submodule not checked out (git submodule update --init)».
- **Spiegazione:** il submodule non è nel checkout.
- **Progetto e caso:** sys-git-submodule-absent — finale e conferma, 16 novembre 2026.
- **Rimedio:** `f9fde7c1e`: è `unavailable` e lo nomina.
- **Verifica:** finale e conferma.
- **Stato:** buco dichiarato (`unavailable`).
- **Note:** —

#### D-127 `namespace a::b {` non letto come C++17
- **Descrizione:** il lettore non riconosceva il namespace annidato di C++17.
- **Spiegazione:** la lettura non lo trattava come C++17.
- **Progetto e caso:** lettura C/C++ — 16 novembre 2026.
- **Rimedio:** `f9fde7c1e`, `scripts/languages/__init__.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-128 Un `.h` con una direttiva Objective-C letto come C
- **Descrizione:** un header Objective-C entrava nel grafo come C.
- **Spiegazione:** l'estensione `.h` decideva da sola il linguaggio.
- **Progetto e caso:** lettura C/C++ — 16 novembre 2026.
- **Rimedio:** `f9fde7c1e`: il file torna al suo linguaggio.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-129 Un `.ts` di Qt Linguist letto come TypeScript
- **Descrizione:** un file XML di traduzione di Qt entrava nel grafo come TypeScript.
- **Spiegazione:** l'estensione `.ts` decideva da sola il linguaggio.
- **Progetto e caso:** lettura — 16 novembre 2026.
- **Rimedio:** `f9fde7c1e`: il file torna al suo linguaggio.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-130 C: macro di decorazione e nomi da header non risolti
- **Descrizione:** su zlib 37 file C su 66 non avevano fatti semantici, e le chiamate risolte erano 303.
- **Spiegazione:**
  - il lettore non toglieva le macro che il sorgente definisce come decorazione o come involucro di un prototipo, anche quando arrivano da un file incluso;
  - un nome che arriva da un header non portava alla sua unica definizione con collegamento esterno, anche dentro un namespace C++.
- **Progetto e caso:** zlib — 14 novembre 2026.
- **Rimedio:** `8054a410c` (14 novembre), `scripts/languages/cfamily.py`, `scripts/resolution.py`, `scripts/semantic_index.py`, `scripts/semantic_store.py` e `scripts/snapshot.py`.
- **Verifica:** zlib: file senza fatti semantici da 37 a 12 su 66, chiamate risolte da 303 a 510; per gli altri linguaggi lo snapshot è identico.
- **Stato:** risolto.
- **Note:** —

#### D-131 Un configure che ha bisogno di ciò che l'unità scarica fuori dai registri
- **Descrizione:** l'indice C/C++ di un'unità non si fa senza i download che la sua configurazione chiede.
- **Spiegazione:** la configurazione gira senza rete, con CMake e scip-clang portati da Daodan e fissati per sha256.
- **Progetto e caso:** indicizzatore C/C++ — 14 novembre 2026.
- **Rimedio:** `98743babd` (14 novembre):
  - l'indice di quell'unità è `unavailable`, con gli indirizzi e la riga d'errore di CMake;
  - l'unità tiene i fatti statici.
- **Verifica:** provato su un container finto; la prova vera in D-122.
- **Stato:** buco dichiarato (`unavailable`).
- **Note:** D-132.

#### D-132 `file(DOWNLOAD)` ed ExternalProject non annotati
- **Descrizione:** finale, otel-demo: «scip-clang wrote no index (src/currency: the configure ended with exit code 1; FetchContent asked for nothing; file(DOWNLOAD) and ExternalProject are not recorded)».
- **Spiegazione:**
  - un fornitore di dipendenze passato a CMake annota nome e indirizzi di ciò che il progetto chiede a FetchContent, senza scaricare;
  - file(DOWNLOAD) ed ExternalProject non passano di lì.
- **Progetto e caso:** otel-demo src/currency — finale, 16 novembre 2026.
- **Rimedio:** `6c2aa069e` (14 novembre):
  - una configurazione fallita con un'annotazione è `unavailable` con quella causa;
  - senza annotazione è `failed`, e lo dice.
- **Verifica:** finale.
- **Stato:** buco dichiarato (`failed` con la frase citata).
- **Note:** D-135.

#### D-133 zlib: file C e C++ che nessun build compila
- **Descrizione:** conferma, zlib:
  - C con 22 file su 54 fuori dall'indice: 12 «not built by the default configuration», 8 header che nessuna unità indicizzata include in un ramo attivo, 2 con «make ended with exit code 2»;
  - C++ `failed`: nessuno degli 8 file nell'indice.
- **Spiegazione:**
  - i contrib con un Makefile sono già indicizzati sotto Bear;
  - i file mancanti non li compila nessun build: examples/, contrib/infback9, il solo target cover e il build autotools di minizip;
  - team-lead nomina anche iowin32.c, che nessun commit nomina: da verificare.
- **Progetto e caso:** zlib — finale e conferma, 16 novembre 2026.
- **Rimedio:** `d4e6d9046` (16 novembre), `scripts/indexers/clang.py`: il motivo nomina la cartella invece di «not built by the default configuration».
- **Verifica:** dopo `d4e6d9046` nessun giro: da verificare.
- **Stato:** buco dichiarato (`no compile command`).
- **Note:** D-134; il build autotools di minizip ora c'è.

#### D-134 zlib minizip: il build autotools non eseguito
- **Descrizione:** mztools.c di contrib/minizip non era indicizzato.
- **Spiegazione:** Daodan non eseguiva i build autotools.
- **Progetto e caso:** zlib contrib/minizip — 16 novembre 2026.
- **Rimedio:** `22dca6da8` (16 novembre), `scripts/indexers/clang.py` e `clang_run.py`:
  - il configure.ac più esterno è un'unità autotools-project, con i sorgenti dei Makefile.am;
  - clang lancia autoreconf, configure in una cartella sua e make sotto Bear.
- **Verifica:** provato su contrib/minizip di zlib: mztools.c è indicizzato.
- **Stato:** risolto.
- **Note:** D-133.

#### D-135 otel-demo currency: il build dichiarato solo nel Dockerfile
- **Descrizione:** finale e giro `jvm-otel-android`: il configure di src/currency esce con 1 (D-132), con «CMake Error at CMakeLists.txt:7 (find_package): Could not find a package configuration file provided by "Protobuf"».
- **Spiegazione:** Protobuf e le altre dipendenze del servizio le installa il suo Dockerfile, che è l'unico a dichiarare come si costruisce; il configure sul checkout non le trova.
- **Progetto e caso:** otel-demo (`b825c7c25726`) — finale e giro `jvm-otel-android`, 16 novembre 2026.
- **Rimedio:** in corso (android-sdk). Da `f024ba3a3` (16 novembre) la lettura e il piano ci sono, ma nessun analizzatore C/C++ li usa:
  - la pre-mappa legge ogni Dockerfile con il parser di BuildKit v0.34.2 (fatto `docker_builds`), con il contesto e gli argomenti di build da Compose (`scripts/premap/dockerfile.py`);
  - `scripts/docker_build.py` pianifica lo stadio fino al suo ultimo RUN, con l'immagine di base fissata per digest, e ogni istruzione non riproducibile è un buco `not_reproduced` con la sua riga;
  - la via per C e C++ non è in un commit (`scripts/indexers/clang.py`, non committato): scip-clang gira sull'Alpine dello stadio attraverso il loader di glibc in una prova; mancano le sorgenti dei pacchetti dell'immagine di base e `.dockerignore`.
- **Verifica:** del piano solo test (`tests/test_codebase_map_docker_build.py`, `test_currency_runs_base_then_builder_with_compose_s_argument_and_maps_each_copy_back`); dell'indice, —.
- **Stato:** aperto (android-sdk).
- **Note:** D-107, D-141.

#### D-136 C: 5.147 buchi `no-document`
- **Descrizione:** conferma, C su 7 casi: 10.271 siti, 40,7 % di risposta; fra i buchi, no-document 5.147 e no-occurrence 941.
- **Spiegazione:** da verificare.
- **Progetto e caso:** i casi C della conferma — 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** D-133.

#### D-137 File C e C++ fuori dalla configurazione predefinita
- **Descrizione:** sys-cmake-presets ha 1 file C su 4 e tinyxml2 1 file C++ su 3 «no compile command: not built by the default configuration».
- **Spiegazione:** la configurazione predefinita del build non li compila.
- **Progetto e caso:** sys-cmake-presets, tinyxml2 (`9148bdf719e9`) — finale e conferma, 16 novembre 2026.
- **Rimedio:** il motivo per file (`2bc7c7459`).
- **Verifica:** finale e conferma.
- **Stato:** buco dichiarato (`no compile command: not built by the default configuration`).
- **Note:** —

#### D-138 Go: i builtin erano buchi
- **Descrizione:** le chiamate ai builtin di Go non avevano risposta.
- **Spiegazione:** non erano esterni di nessun pacchetto.
- **Progetto e caso:** indicizzatore Go — 16 novembre 2026.
- **Rimedio:** `a633ebd72`: sono esterni del pacchetto builtin.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-139 Go: file esclusi dai vincoli di build senza indice
- **Descrizione:** i file esclusi da un vincolo di build mancavano dall'indice.
- **Spiegazione:** scip-go indicizza la sola configurazione corrente.
- **Progetto e caso:** indicizzatore Go — 16 novembre 2026.
- **Rimedio:** `a633ebd72`: quei file hanno un passaggio di scip-go sotto una configurazione che li compila.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-079.

#### D-140 Go: un file senza go.mod non diceva perché
- **Descrizione:** finale, robot-shop: «go failed: none of the 1 go files is in the index: no document in the index (1)».
- **Spiegazione:** il file non ha un go.mod nella sua cartella né sopra; il go.mod lo scrive il Dockerfile al build.
- **Progetto e caso:** robot-shop (`55292e2199f2`) — finale, 16 novembre 2026.
- **Rimedio:** `d4e6d9046`, `scripts/indexers/go.py`: il motivo dice «no Go module holds it».
- **Verifica:** dopo `d4e6d9046` nessun giro: da verificare.
- **Stato:** risolto; il build resta D-141.
- **Note:** D-141.

#### D-141 robot-shop dispatch: il modulo Go dichiarato solo nel Dockerfile
- **Descrizione:** finale: «go failed: none of the 1 go files is in the index: no document in the index (1)»; il servizio dispatch non entra nel grafo Go.
- **Spiegazione:**
  - il go.mod lo scrive il Dockerfile al build: `WORKDIR /go/src/app`, `COPY *.go .`, `RUN go mod init dispatch && go get`, `RUN go install`;
  - quel Dockerfile oggi non costruisce più: `go get` senza versione prende un go-sensor che chiede Go 1.21 (dal commit).
- **Progetto e caso:** robot-shop (`55292e2199f2`) — finale, 16 novembre 2026.
- **Rimedio:** `f024ba3a3` e `f04dab9d5` (16 novembre, android-sdk), `scripts/indexers/go.py` e `scripts/docker_build.py`:
  - `f024ba3a3` legge il Dockerfile e ne pianifica lo stadio;
  - `f04dab9d5` indicizza: un file Go che nessun modulo contiene, ma che uno stadio del Dockerfile copia, ha una corsa di scip-go dentro quello stadio, che registra Dockerfile, stadio, comandi eseguiti, go.mod e go.sum risolti; gli ARG dello stadio arrivano dove gira il build;
  - il passo che fallisce è il buco `restore_failed`, con `dispatch/Dockerfile:7` e la riga d'errore dello strumento, non il progresso di go.
- **Verifica:**
  - `tests/test_codebase_map_docker_build.py` (`test_dispatch_runs_its_stage_up_to_the_go_install_that_builds_it`, `test_go_files_no_module_holds_are_indexed_in_the_stage_their_dockerfile_builds`);
  - dal commit `f04dab9d5`: su uno stadio della stessa forma che costruisce, da 0 a 1 file indicizzato, completo, con le versioni che `go get` ha risolto;
  - su robot-shop il commit riporta l'errore vero del Dockerfile di oggi.
- **Stato:** buco dichiarato (`restore_failed` a `dispatch/Dockerfile:7`): è il Dockerfile del progetto a non costruire.
- **Note:** D-107, D-135, D-140.

#### D-142 Un file cgo fuori dall'indice Go
- **Descrizione:** finale e conferma, sys-go-cgo 1 file su 3: «a cgo file (`import "C"`): scip-go indexes the copy cgo writes into the build cache, not the file».
- **Spiegazione:** scip-go indicizza la copia che cgo scrive nella cache del build, non il file.
- **Progetto e caso:** sys-go-cgo — finale e conferma, 16 novembre 2026.
- **Rimedio:** il motivo per file.
- **Verifica:** finale e conferma.
- **Stato:** buco dichiarato («a cgo file»).
- **Note:** il C di cgo entra nel grafo con `f829df4b0` (Bear attorno a `go build`).

#### D-143 Rust: file senza documento
- **Descrizione:** «no document in the index» per 6 file Rust su 105 in hoppscotch (finale) e 1 su 19 in semver (finale e conferma).
- **Spiegazione:** da verificare.
- **Progetto e caso:** hoppscotch (`55908a76a1d0`), semver (`280ebcb6edac`) — finale e conferma, 16 novembre 2026.
- **Rimedio:** —. Da `a3801beed` un file dietro un `mod` con cfg falso dice perché manca (D-237); quanti dei 7 lo siano è da verificare.
- **Verifica:** —
- **Stato:** aperto.
- **Note:** D-144, D-237.

#### D-144 Rust: file che nessun crate carica
- **Descrizione:** finale, hoppscotch: 2 file «no crate includes it: no `mod` item of an indexed file loads it».
- **Spiegazione:** nessun `mod` di un file indicizzato li carica.
- **Progetto e caso:** hoppscotch — finale, 16 novembre 2026.
- **Rimedio:** il motivo per file.
- **Verifica:** finale.
- **Stato:** buco dichiarato («no crate includes it»).
- **Note:** —

#### D-145 TypeScript: `{ t } = useTranslation()` legato a un simbolo che l'indice non definisce
- **Descrizione:** in tududi i nomi presi per destrutturazione finivano su un simbolo senza definizione.
- **Spiegazione:** il join legava il nome a un simbolo che l'indice non definisce.
- **Progetto e caso:** tududi (`71da9d7b34df`) — 16 novembre 2026.
- **Rimedio:** `3595d571b` (16 novembre), `scripts/indexers/typescript.py` e `scripts/code_graph.py`: il nome finisce alla sua definizione.
- **Verifica:** tududi, insieme a D-147.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-146, D-147 e D-161.

#### D-146 TypeScript: pacchetti senza nome (heroicons)
- **Descrizione:** i riferimenti ai pacchetti senza nome, come heroicons, non avevano un esterno valido.
- **Spiegazione:** un difetto di scip-typescript, corretto nella 0.6.2.
- **Progetto e caso:** tududi — 16 novembre 2026.
- **Rimedio:** `3595d571b`: scip-typescript passa alla 0.6.2.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-147 TypeScript e JavaScript: buchi senza causa
- **Descrizione:** in tududi 8.010 buchi TypeScript erano senza spiegazione.
- **Spiegazione:** l'indice non dice perché un riferimento non ha occorrenza.
- **Progetto e caso:** tududi — 16 novembre 2026.
- **Rimedio:** `3595d571b`, `scripts/indexers/typescript_unbound.js`:
  - dopo l'indice gira il checker di TypeScript;
  - l'aggancio `unanswered` dà a ogni buco la causa: ricevente any, firma a indice, membro creato dal checker, non dichiarato.
- **Verifica:** tududi: «da 8.010 buchi TypeScript senza spiegazione a 3.193 con la causa» (dal commit).
- **Stato:** risolto.
- **Note:** D-158.

#### D-148 `module` di `module.exports` come locale senza definizione
- **Descrizione:** in un file CommonJS `module` restava un buco.
- **Spiegazione:** l'indice scrive `module` come una locale senza definizione, perché TypeScript legge `module.exports =` come l'export del file.
- **Progetto e caso:** js-yarn-berry, js-npm-single — 16 novembre 2026.
- **Rimedio:** `eacfad80e` (16 novembre), `scripts/indexers/typescript.py`:
  - se l'indice usa i tipi di Node, l'estremo è esterno (@types/node dichiara `module` accanto a `require`);
  - altrimenti resta un buco con la causa.
- **Verifica:** prova vera su Modal: js-yarn-berry e js-npm-single completi, 0 buchi. Finale: «module.exports: the index names `module` with a local it defines nowhere, and references no Node types that declare it» 2.
- **Stato:** risolto; il buco resta dove il progetto non usa i tipi di Node.
- **Note:** —

#### D-149 Una chiamata senza nome del chiamato era sempre un buco `no-position`
- **Descrizione:** lo snapshot registra una chiamata senza nome del chiamato con una lista vuota, e il grafo ne faceva sempre un buco no-position.
- **Spiegazione:** il grafo non leggeva l'espressione chiamata.
- **Progetto e caso:** chi (`c64ed7d6635f`) e il corpus — 16 novembre 2026.
- **Rimedio:** `334ea4d96` (16 novembre), `scripts/code_graph.py` e `scripts/languages/semantic.py`; `Snapshot.computed` legge l'espressione:
  - una funzione dichiarata lì (`func(){..}()` di Go, defer e go, IIFE e frecce di JavaScript e TypeScript) è un arco certo al suo letterale;
  - `super(...)` prende l'occorrenza dell'indice;
  - il resto è un buco con la sua classe, che il passo dinamico chiude per posizione: call-result, element, dynamic-import, super-call, computed-callee.
- **Verifica:** chi: 36 di 43 con risposta (dal commit); nessun giro dopo il commit.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-150 e D-151; il lavoro era di dynamic-step-2.

#### D-150 TypeScript: `x.f!()` non nominava `x.f`
- **Descrizione:** lo snapshot non dava il nome del chiamato per una chiamata con l'asserzione non-null.
- **Spiegazione:** il lettore non toglieva `!` dal chiamato.
- **Progetto e caso:** lettura TypeScript — 16 novembre 2026.
- **Rimedio:** `334ea4d96`, `scripts/languages/semantic.py`: `x.f!()` nomina `x.f`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-151 TypeScript: `await f<T>(x)` non nominava `f`
- **Descrizione:** lo snapshot non dava il nome del chiamato per una chiamata generica sotto await.
- **Spiegazione:** il lettore non toglieva gli argomenti di tipo sotto await.
- **Progetto e caso:** lettura TypeScript — 16 novembre 2026.
- **Rimedio:** `334ea4d96`: `await f<T>(x)` nomina `f`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-152 TypeScript 6: i tipi di Node non caricati
- **Descrizione:** con TypeScript 6 l'indice non aveva i tipi di Node.
- **Spiegazione:** non caricati con quella versione (dal commit).
- **Progetto e caso:** TypeScript nel container — 16 novembre 2026.
- **Rimedio:** `12775fee3` (16 novembre): i tipi di Node si caricano anche con TypeScript 6.
- **Verifica:** prova vera su Modal: TypeScript del workspace pnpm completo.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-153–D-156, D-167–D-171 e D-225.

#### D-153 Svelte con nulla di letto non era `failed`
- **Descrizione:** `d94f92470` lasciava aperto lo stato di Svelte con 0 file letti.
- **Spiegazione:** lo stato non guardava i file letti.
- **Progetto e caso:** js-sveltekit — 16 novembre 2026.
- **Rimedio:** `12775fee3`: Svelte senza nulla di letto è `failed`, con la causa.
- **Verifica:** finale, js-sveltekit: «nothing of the 2 svelte files is read: template not read: calls and bindings in it are not sites (2); none of their 2 calls is asked: builtin (2)».
- **Stato:** risolto.
- **Note:** D-159.

#### D-154 Vue diverso fra analisi e unione
- **Descrizione:** `d94f92470` lasciava aperto Vue «tra analisi e unione».
- **Spiegazione:** lo stato di Vue nell'analisi e nell'unione non coincideva.
- **Progetto e caso:** js-vue-pnpm — 16 novembre 2026.
- **Rimedio:** `12775fee3`: Vue è uguale fra analisi e unione.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-155 L'import di un `.vue` non tipizzato senza causa
- **Descrizione:** un import di un componente `.vue` non tipizzato era un buco senza causa.
- **Spiegazione:** il motivo non c'era.
- **Progetto e caso:** progetti Vue — 16 novembre 2026.
- **Rimedio:** `12775fee3`: l'import ha la sua causa.
- **Verifica:** finale: «no declaration of *.js?v=explicit-esm-dependencies modules: the import is not typed» 1.
- **Stato:** risolto.
- **Note:** —

#### D-156 SvelteKit: «error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'»
- **Descrizione:** finale, js-sveltekit: TypeScript e JavaScript `failed`, «scip-typescript wrote no index (exit code 1): error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'. error: no files got indexed.».
- **Spiegazione:** il tsconfig lo genera SvelteKit, e nessuna installazione lo crea.
- **Progetto e caso:** js-sveltekit — finale, 16 novembre 2026.
- **Rimedio:** `12775fee3`: un buco che nomina il tsconfig generato.
- **Verifica:** finale.
- **Stato:** buco dichiarato (TS5083 nominato nel motivo).
- **Note:** `d94f92470` lo lasciava aperto come «causa del tsconfig generato».

#### D-157 TypeScript: i tipi sotto Yarn
- **Descrizione:** `d94f92470` lascia aperti «tipi sotto Yarn».
- **Spiegazione:** da verificare; nessun commit successivo lo nomina.
- **Progetto e caso:** TypeScript nel container — 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (da verificare).
- **Note:** —

#### D-158 JavaScript: riceventi non tipizzati
- **Descrizione:** buchi «a member of a value of type any: only execution knows it», per esempio 10 in kotlinconf `app/webApp/src/webMain/resources/service-worker.js`; conferma, JavaScript: no-occurrence 39.563.
- **Spiegazione:** senza tipo del ricevente l'indice non sa quale membro si chiama; solo l'esecuzione lo sa.
- **Progetto e caso:** kotlinconf e il corpus JavaScript — conferma e corsa su Modal di kotlinconf, 16 novembre 2026.
- **Rimedio:** `3595d571b` (la causa). Il passo dinamico chiude quei buchi dove i test girano.
- **Verifica:** conferma: JavaScript con 691 risposte osservate.
- **Stato:** buco dichiarato («a member of a value of type any»).
- **Note:** D-147.

#### D-159 Template di Vue e Svelte non letti
- **Descrizione:** finale:
  - Vue 0 file su 410 nell'indice, 28,2 % di risposta; Svelte 0 su 4, 26,7 %;
  - hoppscotch Vue 407 su 407 (400 «template not read: calls and bindings in it are not sites», 7 «no script block»), Svelte 2 su 2;
  - js-vue-pnpm 3 su 3.
- **Spiegazione:** le chiamate e i binding nei template non sono siti.
- **Progetto e caso:** hoppscotch, js-vue-pnpm, js-sveltekit — finale, 16 novembre 2026.
- **Rimedio:** dichiarati letti in parte (`64edfb930`, D-080).
- **Verifica:** —
- **Stato:** aperto (csharp-2).
- **Note:** D-080, D-153.

#### D-160 TypeScript: un file senza documento
- **Descrizione:** finale: hoppscotch 1 file TypeScript su 1.115, memos 1 su 620, «no document in the index».
- **Spiegazione:** da verificare.
- **Progetto e caso:** hoppscotch, memos (`509e41bd1a1b`) — finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** —

#### D-161 Tailwind caricato sull'host con la configurazione del progetto
- **Descrizione:** l'adattatore Tailwind eseguiva codice del progetto fuori dal container.
- **Spiegazione:** `css_tailwind.js` caricava sull'host il tailwindcss del progetto, la sua configurazione e i suoi plugin.
- **Progetto e caso:** analyzer dei fogli di stile — 16 novembre 2026.
- **Rimedio:** `3595d571b`, `scripts/indexers/css_tailwind.py`:
  - Tailwind gira con `run_in_container`: preparazione con i registri e il ripristino dei pacchetti, esecuzione senza rete;
  - senza container o con un ripristino fallito i token restano sconosciuti con la causa, e nulla gira sull'host;
  - gli altri motori CSS leggono il progetto come testo e restano dove sono.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-162.

#### D-162 Fogli di stile: buchi `no-rule`
- **Descrizione:** conferma: 42.757 buchi no-rule su 58.534 siti dei fogli di stile, 26,3 % di risposta; nel finale 48.808.
- **Spiegazione:** un riferimento di classe, id o composes senza una regola che lo definisca è `no-rule` (`scripts/indexers/css.py`); fra questi le classi Tailwind (`ee1e83fc8`). Da verificare quanti sono classi che nessun foglio definisce e quanti un difetto.
- **Progetto e caso:** il corpus — finale e conferma, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (ts-container-2).
- **Note:** D-161.

#### D-163 hoppscotch: lo stadio dei fogli di stile esce con 1 senza rapporto
- **Descrizione:** giro-2 e finale: «the stylesheet stage exited with code 1 without a report; see engine-pass.log».
- **Spiegazione:** da verificare.
- **Progetto e caso:** hoppscotch — giro-2 e finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (ts-container-2).
- **Note:** —

#### D-164 Fogli remoti senza testo
- **Descrizione:** finale: 10 buchi `remote-sheet`.
- **Spiegazione:** il lettore non scarica nulla; un foglio remoto senza testo lascia buchi con il suo indirizzo.
- **Progetto e caso:** il corpus — finale, 16 novembre 2026.
- **Rimedio:** `9c719fc1a` (14 novembre).
- **Verifica:** finale.
- **Stato:** buco dichiarato (`remote-sheet`).
- **Note:** —

#### D-165 Parser: `base` di C# non letto
- **Descrizione:** il commit elenca `base` in C# fra le correzioni del parser.
- **Spiegazione:** da verificare: il commit non dice cosa accadeva prima.
- **Progetto e caso:** parser — 16 novembre 2026.
- **Rimedio:** `d94f92470` (16 novembre).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** con `56e65e114` una chiamata attraverso `base` non prende override.

#### D-166 Parser: `this` e `super` di Kotlin non letti
- **Descrizione:** il commit elenca `this` e `super` in Kotlin fra le correzioni del parser.
- **Spiegazione:** da verificare: il commit non dice cosa accadeva prima.
- **Progetto e caso:** parser — 16 novembre 2026.
- **Rimedio:** `d94f92470`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-236 C++: il simbolo di un argomento di macro stava sul nome della macro
- **Descrizione:** tinyxml2, 255 buchi no-occurrence (misura del commit `a3801beed`, su Modal al commit fissato).
- **Spiegazione:** scip-clang scrive un riferimento nel punto di espansione, così il simbolo di un argomento di macro stava sul nome della macro.
- **Progetto e caso:** tinyxml2 (`9148bdf719e9`) — misura su Modal del commit, 16 novembre 2026.
- **Rimedio:** `a3801beed` (16 novembre), `scripts/indexers/clang.py` (`macro_arguments`): riporta il simbolo al nome dell'argomento, tiene quello del corpo della macro e salta i nomi ambigui.
- **Verifica:** dal commit, no-occurrence da 255 a 43; `tests/test_codebase_map_code_graph.py` (`test_clang_a_macros_arguments_take_the_symbols_the_index_writes_at_the_macro`).
- **Stato:** risolto; i 43 restanti dicono il ramo `#if` che il build non compila, o sono chiamate alla libreria C che l'indice C++ non nomina.
- **Note:** —

#### D-237 Rust: i riferimenti e i file che un `#[cfg]` esclude non dicevano perché
- **Descrizione:** hoppscotch, 549 buchi no-occurrence e 8 no-position (misura del commit `a3801beed`, su Modal al commit fissato).
- **Spiegazione:** i cfg li decide la configurazione che rust-analyzer legge: ogni feature accesa, il target dell'host, niente build script né macro procedurali. Un riferimento sotto un `#[cfg(X)]` falso in quella configurazione non ha occorrenza, e un file dietro un `mod` con cfg falso non ha documento.
- **Progetto e caso:** hoppscotch (`55908a76a1d0`) — misura su Modal del commit, 16 novembre 2026.
- **Rimedio:** `a3801beed` (16 novembre), `scripts/indexers/rust.py`: il buco dice il cfg falso, e il file dice perché manca.
- **Verifica:** dal commit, «no-occurrence da 549 a 135, di cui 425 ora con la causa cfg; no-position da 8 a 0»; `tests/test_codebase_map_indexers_reasons.py` (`test_rust_code_a_cfg_leaves_out_says_so`).
- **Stato:** buco dichiarato (la causa cfg).
- **Note:** D-143.

#### D-238 Rust: il turbofish su un ricevitore calcolato toglieva il nome al chiamato
- **Descrizione:** semver: `black_box(t).parse::<V>()` non era nominato.
- **Spiegazione:** il lettore dei nomi del chiamato (`scripts/languages/semantic.py`) cercava il membro sul nodo `generic_function`, il turbofish, invece che sulla funzione che esso contiene.
- **Progetto e caso:** semver (`280ebcb6edac`) — commit `a3801beed`, 16 novembre 2026.
- **Rimedio:** `a3801beed` (16 novembre), `scripts/languages/semantic.py`: il turbofish non fa parte del nome del membro.
- **Verifica:** solo test (`tests/test_xray_semantic_syntax.py`, `test_a_rust_method_with_type_arguments_keeps_its_name`).
- **Stato:** risolto.
- **Note:** —

### Passo dinamico e osservatori

#### D-167 «Osservato» con zero osservazioni
- **Descrizione:** un linguaggio poteva risultare osservato senza una sola osservazione.
- **Spiegazione:** lo stato non distingueva una corsa senza test, o senza righe, da una corsa che osserva.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `12775fee3` (16 novembre), `scripts/dynamic/__init__.py`: `not-run` e `not-observed` al posto di un falso «osservato».
- **Verifica:** giro `fixtures` sui 104 progetti: nei progetti in miniatura quasi sempre non ci sono test da lanciare, e il risultato lo dice (README del benchmark).
- **Stato:** risolto.
- **Note:** D-172.

#### D-168 Un risultato malformato di un osservatore fermava la pipeline
- **Descrizione:** un osservatore che restituisce un risultato fuori contratto fermava la pipeline con un errore.
- **Spiegazione:** il contratto dell'osservatore non era scritto né controllato.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `12775fee3`, `scripts/dynamic/__init__.py` (`malformed`): il contratto è scritto e controllato, e un risultato malformato è un buco che nomina l'osservatore.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-169 pytest fermo agli errori di raccolta
- **Descrizione:** la prima corsa della pipeline con il passo dinamico, su Daodan stesso su Modal, osserva 1.361 punti e chiude 82 buchi (`d94f92470`), ma solo dall'import dei moduli di test.
- **Spiegazione:** pytest si fermava agli errori di raccolta, così i test Python non partivano oltre la raccolta.
- **Progetto e caso:** il codice di Daodan, senza `benchmarks/` — corsa su Modal, 16 novembre 2026 (analisi 26 minuti, passo dinamico 2,6).
- **Rimedio:** `12775fee3`: pytest prosegue oltre i moduli che non si importano (`--continue-on-collection-errors`), e quei moduli sono dichiarati come buco.
- **Verifica:** da verificare: la spec del passo dinamico lo dà da rimisurare.
- **Stato:** risolto.
- **Note:** —

#### D-170 JavaScript: il TypeScript che Node toglie da solo
- **Descrizione:** il commit elenca nell'osservatore JavaScript il TypeScript che Node toglie da solo.
- **Spiegazione:** da verificare: il commit non dice di più.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `12775fee3`.
- **Verifica:** prova vera su Modal: JavaScript osservato (6 chiamate).
- **Stato:** risolto.
- **Note:** —

#### D-171 Un comando di test fallito senza l'errore vero nel buco
- **Descrizione:** il buco di un comando di test fallito non portava l'errore vero.
- **Spiegazione:** il buco non riportava l'uscita d'errore del comando.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `12775fee3`: l'errore vero entra nel buco.
- **Verifica:** finale, fastapi: «no test ran: npm test in . exited with code 127 and recorded no call: > test | > bun run --filter frontend test | | sh: 1: bun: not found».
- **Stato:** risolto.
- **Note:** —

#### D-172 `not-observed` non diceva cosa aveva visto il registratore
- **Descrizione:** `not-observed` diceva solo che nessuna chiamata era caduta su un riferimento, seguito da buchi estranei.
- **Spiegazione:** la causa non veniva da ciò che il registratore aveva visto.
- **Progetto e caso:** py-setup-cfg-extras, il cui unico test non chiama nulla e dove cli.py non gira — 16 novembre 2026.
- **Rimedio:** `0c57a839a` (16 novembre), `scripts/dynamic/__init__.py` (`_unplaced`); la causa dice una di queste cose:
  - siti nei file del linguaggio senza riferimento, contati per ruolo;
  - chiamate solo in file fuori dallo snapshot;
  - nessuna chiamata dai file del linguaggio, con i file che i test non hanno eseguito.

  La spec ne ha la sezione «Corsa senza righe».
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-167.

#### D-173 Go e Rust non pianificavano i test della radice
- **Descrizione:** i test del modulo o del crate alla radice non giravano.
- **Spiegazione:** la pre-mappa nomina la radice del progetto con il percorso vuoto, e Go e Rust non la riconoscevano.
- **Progetto e caso:** osservatori Go e Rust — 16 novembre 2026.
- **Rimedio:** `a491415e6` (16 novembre), `scripts/dynamic/go.py` e `scripts/dynamic/rust.py`.
- **Verifica:** prova vera su Modal: Go osservato (1 chiamata), C/C++ osservato su Callgrind (5 chiamate).
- **Stato:** risolto.
- **Note:** D-174.

#### D-174 Go fuori dal contratto dell'osservatore
- **Descrizione:** `12775fee3` dice Go «ancora da adeguare» al contratto.
- **Spiegazione:** Go non riportava runner e stato come chiede il contratto.
- **Progetto e caso:** osservatore Go — 16 novembre 2026.
- **Rimedio:** `a491415e6`, `scripts/dynamic/go.py`.
- **Verifica:** prova vera su Modal, come D-173.
- **Stato:** risolto.
- **Note:** —

#### D-175 Rust: «can't find crate for std»
- **Descrizione:** ogni cargo test falliva su «can't find crate for std».
- **Spiegazione:** il rustc fissato non contiene le librerie standard.
- **Progetto e caso:** osservatore Rust — 16 novembre 2026.
- **Rimedio:** `ef69774f9` (16 novembre), `scripts/dynamic/rust.py` e `scripts/dynamic/callgrind.py`: rust-std 1.99.1, fissato per sha256.
- **Verifica:** in una Function di Modal con gli script dell'osservatore: cargo test sotto Callgrind, 8 siti, nessun buco.
- **Stato:** risolto.
- **Note:** sotto gVisor resta D-209.

#### D-176 Launchpad 502: Rust perde l'osservazione
- **Descrizione:** nel giro sulle fixture Launchpad ha risposto 502, e il passo dinamico Rust ha perso l'osservazione.
- **Spiegazione:** Valgrind aveva una sola fonte.
- **Progetto e caso:** giro `fixtures` — 16 novembre 2026.
- **Rimedio:** `d5964e7b9` (16 novembre), `scripts/dynamic/callgrind.py`:
  - lo stesso file, con lo stesso sha256, viene prima da archive.ubuntu.com e poi da Launchpad;
  - se cadono entrambe, il buco nomina i due errori.
- **Verifica:** conferma: Rust osservato in semver (558 siti).
- **Stato:** risolto.
- **Note:** —

#### D-177 L'osservatore C/C++ installava con vcpkg dove l'analizzatore usa Conan
- **Descrizione:** con vcpkg.json, conanfile.txt e un preset che nomina il toolchain di Conan, osservatore e analizzatore usavano gestori diversi.
- **Spiegazione:** l'osservatore sceglieva il gestore da sé.
- **Progetto e caso:** progetti con vcpkg e Conan insieme — 16 novembre 2026.
- **Rimedio:** `a8a1ebdb5` (16 novembre), `scripts/dynamic/clang.py`: prende da `indexers/clang.restores` la riga di installazione e la preparazione del gestore di ogni radice.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-125.

#### D-178 L'osservatore JVM compilava sul JDK dell'immagine
- **Descrizione:** real-3: su javapoet il passo dinamico fallisce perché la build gira sul JDK dell'immagine e non su quello dichiarato (`7532ed2e7`).
- **Spiegazione:** l'osservatore non installava il JDK dichiarato, e l'agente non era costruito per Java 8.
- **Progetto e caso:** javapoet — real-3, 16 novembre 2026.
- **Rimedio:** `a633ebd72` (16 novembre):
  - `scripts/dynamic/jvm.py`, e in `scripts/dynamic/jvm_record/` `Agent.java`, `Modular.java`, `Recorder.java` e `Walker.java`;
  - l'osservatore compila sul JDK dichiarato, Java 8 compreso;
  - l'agente è costruito per Java 8 e provato su JDK 8 e 17.
- **Verifica:** su Modal, javapoet (`609ca96dd`): l'osservatore compila sul JDK 8 dichiarato con Error Prone al suo posto, 389 test e 6.021 siti osservati.
- **Stato:** risolto.
- **Note:** D-099, D-224.

#### D-179 Java 25: «No access to RETAIN_CLASS_REFERENCE»
- **Descrizione:** sotto Java 25 i test fallivano tutti sotto il registratore.
- **Spiegazione:** i JDK recenti pretendono un permesso che `Walker` non chiedeva.
- **Progetto e caso:** jvm-ver-* — misura su Modal con 18 progetti, 16 novembre 2026.
- **Rimedio:** `21b3cb39b` (16 novembre), `scripts/dynamic/jvm_record/Walker.java`: chiede il permesso.
- **Verifica:** java-versions: Java osservato in tutte le 18 fixture, 10-14 siti osservati per caso.
- **Stato:** risolto.
- **Note:** —

#### D-180 Test JVM multipiattaforma: nessun compito `test`
- **Descrizione:** in un progetto Kotlin multipiattaforma i test JVM stanno in `jvmTest`, non in `test`.
- **Spiegazione:** l'osservatore lanciava `gradle test`.
- **Progetto e caso:** jvm-kmp-common-jvm — 16 novembre 2026.
- **Rimedio:** `9fe650a3a` (16 novembre), `scripts/dynamic/jvm.py` e `scripts/dynamic/jvm_record/tests.gradle`:
  - un init script sceglie per progetto `test` o, se manca, ogni compito Test;
  - nella preparazione scarica il loro classpath;
  - l'esecuzione offline gira quelli.
- **Verifica:** finale: Kotlin osservato in 4 casi, 1.796 siti.
- **Stato:** risolto.
- **Note:** —

#### D-181 Java 9 e 14 senza un JDK installabile
- **Descrizione:** java-versions: per Java 9 e 14 non c'è un JDK da installare.
- **Spiegazione:** non esiste un JDK installabile di quelle versioni (README del benchmark).
- **Progetto e caso:** jvm-ver-* — java-versions, 16 novembre 2026.
- **Rimedio:** il passo dinamico li osserva sul JDK 17 e lo dice.
- **Verifica:** java-versions.
- **Stato:** buco dichiarato (`toolchain_unavailable`).
- **Note:** —

#### D-182 I servizi della CI non avviati: tududi chiede PostgreSQL
- **Descrizione:** real-3: su tududi i test del backend chiedono PostgreSQL (`7532ed2e7`).
- **Spiegazione:** il passo non avviava i servizi che la CI dichiara.
- **Progetto e caso:** tududi — real-3, 16 novembre 2026.
- **Rimedio:** `17babc624` (16 novembre), `scripts/container.py` e `scripts/dynamic/`:
  - i `services:` dei workflow di GitHub Actions, letti con la libreria YAML di Renovate, diventano la faccetta `services`;
  - ogni container dei test gira in un pod (`--network none`) con i servizi dichiarati, immagini fissate per digest e controllo di salute atteso;
  - i test li trovano su localhost, e fuori non si esce;
  - su Modal girano in sandbox a macchina virtuale con Docker;
  - un servizio che non parte è `service_unavailable`.
- **Verifica:**
  - `b85aa1b9f`: il pod è provato su un Docker vero in un sandbox a macchina virtuale di Modal, con il postgres di tududi raggiunto a localhost e per nome, sano in 5 secondi, 1.1.1.1 irraggiungibile e nessun container lasciato;
  - conferma: i test del backend girano con il PostgreSQL della CI, 3.779 siti JavaScript e 691 buchi chiusi.
- **Stato:** risolto.
- **Note:** D-201, D-202.

#### D-183 Python: le dipendenze dei test non venivano dall'ambiente del runner
- **Descrizione:** finale: python-semver Python `not-run`.
- **Spiegazione:** le dipendenze dei test non venivano dall'ambiente tox che lancia il runner, né dal gruppo, extra o file che nomina pytest.
- **Progetto e caso:** python-semver (`b6e83e3e40d3`) — finale, 16 novembre 2026.
- **Rimedio:** `17babc624`: le dipendenze dei test vengono da quell'ambiente.
- **Verifica:** conferma: python-semver osservato, 1.046 siti, «con i link e le dipendenze di tox» (`828b5413b`).
- **Stato:** risolto.
- **Note:** D-206.

#### D-184 Python: l'interprete non veniva da requires-python o .python-version
- **Descrizione:** il Python dei test non era quello che il progetto dichiara.
- **Spiegazione:** uv non sceglieva l'interprete come fa `uv sync`.
- **Progetto e caso:** osservatore Python — 16 novembre 2026.
- **Rimedio:** `17babc624`: uv sceglie e scarica l'interprete da requires-python o .python-version, come `uv sync`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-188.

#### D-185 tududi: `test` non arriva ai test del frontend
- **Descrizione:** in tududi `test` lancia jest solo in backend/, mentre `frontend:test` e altri quattro script lanciano jest nella radice, dove stanno i test del frontend.
- **Spiegazione:** l'osservatore lanciava solo lo script `test`.
- **Progetto e caso:** tududi — 16 novembre 2026.
- **Rimedio:** `4ee44da0a` (16 novembre), `scripts/premap/npm_tests.py` (npm-tests v4) e `scripts/dynamic/javascript.py`: il buco `tests_not_declared {path, runner, scripts}`, che il motivo del linguaggio nomina.
- **Verifica:** solo test.
- **Stato:** risolto con D-186.
- **Note:** D-186.

#### D-186 L'osservatore JavaScript non lanciava gli script di test che `test` non raggiunge
- **Descrizione:** come D-185.
- **Spiegazione:** uno script di package.json che avvia un runner noto è il comando dichiarato per quei test, anche se la CI non lo chiama.
- **Progetto e caso:** tududi — 16 novembre 2026.
- **Rimedio:** `7e5eb092e` (16 novembre), `scripts/premap/npm_tests.py` (npm-tests v5) e `scripts/dynamic/javascript.py`:
  - per ogni cartella e runner che `test` non raggiunge, un ingresso `tests` con lo script che lo avvia con meno argomenti;
  - mai in modalità watch né in attesa di un debugger (dalle documentazioni di Jest, Vitest, Mocha, Node, Bun e Turborepo);
  - l'osservatore lo lancia come `npm run <script>`;
  - `tests_not_declared` resta solo dove ogni candidato è escluso.
- **Verifica:** su Modal, tududi: `frontend:test` gira, 1.077 test su 1.080 passano, 20.985 siti osservati; finale: tududi TypeScript osservato, 20.204 siti.
- **Stato:** risolto.
- **Note:** D-187.

#### D-187 tududi: i worker di Jest uccisi per memoria
- **Descrizione:**
  - conferma: i test del frontend di tududi scesi a 92 siti (`828b5413b`);
  - SIGKILL in 154 suite del frontend su 156.
- **Spiegazione:** Jest avvia un worker per CPU che vede, circa 20 sull'host, ognuno da 2-3 GB sotto il registratore, in un container da 4 GB.
- **Progetto e caso:** tududi — conferma, 16 novembre 2026.
- **Rimedio:** `37c7ee093` (16 novembre), `scripts/dynamic/javascript.py`: i test girano come sul runner ubuntu-latest di GitHub, con 16 GB e `taskset` sulle prime 4 CPU.
- **Verifica:** su Modal, il frontend: 156 suite, 23.274 siti, nessuno non osservato.
- **Stato:** risolto.
- **Note:** D-189.

#### D-188 fastapi: uv.lock non visto, l'intervallo di Python rifiutato
- **Descrizione:** finale e conferma, fastapi: «the project states Python >=3.14,<4.0 (backend/pyproject.toml): a range that excludes the image's 3.13.18 and names no version to install».
- **Spiegazione:** lo snapshot non tiene i lockfile, così l'osservatore Python non vedeva uv.lock, trattava la cartella come pip e rifiutava l'intervallo.
- **Progetto e caso:** fastapi — finale e conferma, 16 novembre 2026.
- **Rimedio:** `37c7ee093`, `scripts/dynamic/python.py`: il piano conta uv.lock e poetry.lock accanto al manifest quando il checkout li ha, e uv sceglie Python 3.14.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-197.

#### D-189 I test JavaScript con 16 GB fissi anche dove la macchina non li ha
- **Descrizione:** la forma fissa di D-187 poteva superare la memoria libera.
- **Spiegazione:** CPU e memoria non seguivano la macchina.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `a42dc1d86` (16 novembre), `scripts/dynamic/javascript.py`:
  - la forma del runner della CI (4 CPU, 16 GB) è il tetto;
  - con meno memoria libera le corse hanno tante CPU quante la memoria ne regge a 2,5 GB per processo (misurati su Jest di tududi), almeno una;
  - sotto 2,5 GB liberi nessun container parte, e il buco dice la memoria trovata e quella che serve;
  - ogni corsa dichiara le CPU e la memoria con cui è girata.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-190 Turborepo: il registratore non partiva
- **Descrizione:** i test lanciati da Turborepo giravano non registrati.
- **Spiegazione:** la modalità strict di Turborepo, quella predefinita, passa ai task NODE_OPTIONS ma non le variabili del registratore; il preload si caricava e il registratore non partiva.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `cdc1660dd` (16 novembre), `scripts/dynamic/javascript.py`:
  - l'esecuzione imposta `TURBO_ENV_MODE=loose`, l'equivalente documentato di `--env-mode=loose` (turbo >= 2.1.0);
  - se turbo non registra nulla, il buco nomina turbo e il motivo.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-191, D-192.

#### D-191 npm-tests non riconosceva `turbo run … test`
- **Descrizione:** uno script di test che passa da turbo non aveva runner.
- **Spiegazione:** il lettore degli script npm non conosceva turbo.
- **Progetto e caso:** pre-mappa dei test npm — 16 novembre 2026.
- **Rimedio:** `cdc1660dd`, `scripts/premap/npm_tests.py` (npm-tests v3).
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-192 Un run di Node senza test letto come un registratore che non raggiunge i processi
- **Descrizione:** un run di Node che non trova test risultava un guasto del registratore.
- **Spiegazione:** l'esito «nessun test» non era distinto.
- **Progetto e caso:** osservatore JavaScript — 16 novembre 2026.
- **Rimedio:** `cdc1660dd`: è `no_tests`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-193 ES module non registrati su Node prima della 22.15
- **Descrizione:** su un Node senza `module.registerHooks` gli ES module giravano non registrati.
- **Spiegazione:** il registratore usava `module.registerHooks`, che manca prima della 22.15.
- **Progetto e caso:** mix-infra-gha — 16 novembre 2026.
- **Rimedio:** `756ebbcb3` (16 novembre), `scripts/dynamic/javascript_record.js`: il registratore usa `module.register` con un modulo di hook che stampa con lo stesso plugin Babel.
- **Verifica:** mix-infra-gha su Node 20.18.1: 6 siti registrati, niente di non osservato.
- **Stato:** risolto.
- **Note:** —

#### D-194 jhipster: 162 chunk di Vitest in memoria non registrati
- **Descrizione:** jhipster: `ng test`, il builder di Angular con Vitest, valuta chunk tenuti in memoria con una mappa inline verso i .ts originali, e i 162 chunk giravano non registrati.
- **Spiegazione:** il registratore usava una mappa inline solo per un file che esiste e porta a sé stesso.
- **Progetto e caso:** jhipster-sample — 16 novembre 2026.
- **Rimedio:** `e8bc485d7` (16 novembre), `scripts/dynamic/javascript_record.js`:
  - il codice con una mappa inline si registra anche senza un file;
  - una chiamata è un sito del file a cui la mappa porta, se lì è scritto lo stesso nome.
- **Verifica:** su Modal: 6.769 siti in 179 file del progetto, nessuno non osservato.
- **Stato:** risolto.
- **Note:** —

#### D-195 `bun test` non registrato
- **Descrizione:** in fastapi `bun test` gira senza registratore.
- **Spiegazione:** il registratore non osserva il runner di Bun.
- **Progetto e caso:** fastapi — 16 novembre 2026.
- **Rimedio:** `5148e8eb3` lo dichiara.
- **Verifica:** su Modal.
- **Stato:** buco dichiarato (`runner_not_observed`).
- **Note:** D-056.

#### D-196 Un progetto senza test dichiarati, o con test che non partono
- **Descrizione:** il passo vede solo ciò che i test eseguono.
- **Spiegazione:** senza un comando dichiarato il passo non lancia nulla: il comando è quello che il progetto dichiara, mai una convenzione di Daodan.
- **Progetto e caso:** spec del passo dinamico, sezione «Limiti»; i progetti in miniatura del giro `fixtures`.
- **Rimedio:** le lacune `no_test_command` e `tests_not_declared`, e `tests-not-run` nell'unione.
- **Verifica:** fixtures e finale.
- **Stato:** buco dichiarato (`no_test_command`, `tests_not_declared`, `tests-not-run`).
- **Note:** —

#### D-197 I test di fastapi non ancora girati davvero
- **Descrizione:** finale e conferma, fastapi: TypeScript e Python `not-run` (D-056, D-188).
- **Spiegazione:** le due cause hanno un rimedio, ma nessun giro le prova insieme.
- **Progetto e caso:** fastapi — finale e conferma, 16 novembre 2026.
- **Rimedio:** `5148e8eb3`, `37c7ee093`.
- **Verifica:** su Modal `npm test` arriva a Playwright (`5148e8eb3`); Python su 3.14, solo test.
- **Stato:** aperto.
- **Note:** D-056, D-188, D-195.

#### D-198 I test di eShop non ancora girati
- **Descrizione:** finale, eShop: C# `no-observer`; JavaScript e TypeScript «no package.json of the project declares a test script (`scripts.test`): nothing is observed».
- **Spiegazione:** C# non ha osservatore, e gli script npm non dichiarano test.
- **Progetto e caso:** eShop — finale, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto: C# senza osservatore (csharp-dotnet).
- **Note:** D-114.

#### D-199 Python: extra e gruppi che il gestore non installa
- **Descrizione:** un ambiente Python riceve le dipendenze che il ripristino condiviso installa.
- **Spiegazione:** gli extra e i gruppi che il gestore non installa da sé mancano, e i test che li importano non partono (spec, «Limiti»).
- **Progetto e caso:** spec del passo dinamico.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** buco dichiarato (test che non partono, `tests-not-run`).
- **Note:** D-183 prende le dipendenze dall'ambiente del runner.

#### D-200 Python più vecchio del 3.12
- **Descrizione:** un progetto che dichiara un Python più vecchio, una versione o un intervallo che finisce sotto 3.12, non ha i test osservati.
- **Spiegazione:** il registratore chiede Python 3.12 (spec, sezione 7).
- **Progetto e caso:** spec del passo dinamico.
- **Rimedio:** la lacuna `python_too_old`.
- **Verifica:** solo test.
- **Stato:** buco dichiarato (`python_too_old`).
- **Note:** —

#### D-201 I servizi che `docker compose up` avvia non partivano
- **Descrizione:** i test che vogliono i servizi avviati da Compose in un passo di GitHub Actions o in uno script di test npm non li avevano.
- **Spiegazione:** il passo avviava solo i service container dei job.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `22dca6da8` (16 novembre):
  - un passo o uno script che lancia `docker compose up` è un fatto `compose`;
  - `scripts/premap/compose.py` lancia il `config` di Compose 5.6.1, binario fissato, senza rete né motore, e dichiara ogni servizio che partirebbe;
  - un comando non leggibile è `compose_not_read`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-212, D-214, D-215.

#### D-202 I servizi di GitLab CI non avviati
- **Descrizione:** i `services:` di `.gitlab-ci.yml` non partivano accanto ai test.
- **Spiegazione:** il lettore dei servizi leggeva solo GitHub Actions.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `23de469c4` (16 novembre):
  - entrano i servizi di ogni job: i suoi, quelli dei template via `extends`, altrimenti quelli di `default:` o globali salvo `inherit`;
  - i nomi sono gli alias e quelli che gitlab-runner ricava dall'immagine, con le variabili espanse come fa il runner;
  - GitLab non ha controlli di salute, quindi il passo aspetta, come il suo runner, che le porte esposte dall'immagine rispondano (`wait: ports`).
- **Verifica:** su un Docker vero in un sandbox di Modal: un postgres di GitLab senza controllo di salute risponde in 1,8 secondi, i test aprono una sessione a db:5432, e fuori non si esce.
- **Stato:** risolto.
- **Note:** un file incluso è `include_not_read`, D-216.

### Container, servizi e driver Modal

#### D-203 Il motore di container dell'utente usato anche se non risponde in locale
- **Descrizione:** la revisione indipendente del perimetro di rete e di copia lo chiedeva.
- **Spiegazione:** il motore dell'utente si usava senza controllare come risponde.
- **Progetto e caso:** container — 15 novembre 2026.
- **Rimedio:** `177dcae02` (15 novembre), `scripts/container.py`: il motore dell'utente si usa solo se risponde su una pipe o un socket locale.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** dallo stesso commit vengono D-064, D-204 e D-205.

#### D-204 Con un .git e Git che non risponde si copiavano i file ignorati
- **Descrizione:** la copia del progetto poteva portare nel container i file che Git ignora.
- **Spiegazione:** senza risposta di Git la copia non sapeva cosa è ignorato.
- **Progetto e caso:** container — 15 novembre 2026.
- **Rimedio:** `177dcae02`: la run è una lacuna.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-205 Ciò che torna dal container non controllato
- **Descrizione:** l'uscita del container poteva scrivere fuori misura o fuori posto.
- **Spiegazione:** la revisione indipendente lo segnalava.
- **Progetto e caso:** container — 15 novembre 2026.
- **Rimedio:** `177dcae02`: ciò che torna lo scrive il codice di Daodan, con queste regole:
  - solo file e cartelle, nomi controllati;
  - somma delle dimensioni prima di scrivere, tetto di 1 GiB;
  - una cartella nuova, nomi della run riservati;
  - senza le funzioni di estrazione di tarfile e senza rifiutare versioni di Python.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-206 Link simbolici tracciati seguiti nella copia del container
- **Descrizione:** python-semver non trovava i suoi moduli di test.
- **Spiegazione:** la copia seguiva i link simbolici.
- **Progetto e caso:** python-semver — 16 novembre 2026.
- **Rimedio:** `17babc624`, `scripts/container.py`:
  - i link tracciati entrano nella copia come link, mai seguiti;
  - quelli che puntano fuori dal progetto restano fuori, come `link_outside`.
- **Verifica:** su Modal python-semver trova i suoi moduli di test, 533 test; conferma: 1.046 siti osservati.
- **Stato:** risolto.
- **Note:** D-031, D-207.

#### D-207 I link lasciati fuori dalla copia non arrivavano ai buchi delle corse
- **Descrizione:** i `link_outside` della copia non comparivano nei risultati.
- **Spiegazione:** osservatori, analisi e pre-mappa non aggiungevano ai propri buchi quelli della copia.
- **Progetto e caso:** container — 16 novembre 2026.
- **Rimedio:** `756ebbcb3` (16 novembre): li aggiungono osservatori (Go, C/C++, Rust, JavaScript, Python), analisi (C/C++, C#, JVM, Python) e pre-mappa.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-208.

#### D-208 JVM: i buchi della preparazione sovrascrivevano quelli del container
- **Descrizione:** nella JVM si perdevano i buchi del container.
- **Spiegazione:** i buchi della preparazione sovrascrivevano quelli del container.
- **Progetto e caso:** analisi JVM — 16 novembre 2026.
- **Rimedio:** `756ebbcb3`, `scripts/indexers/jvm.py`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-209 Valgrind muore all'avvio nei sandbox di Modal (gVisor)
- **Descrizione:**
  - `12775fee3`: «Valgrind non parte nei container di Modal (gVisor)»;
  - `a491415e6`: «Valgrind si ferma nel caricatore dinamico prima del codice Rust»;
  - finale, README: «Rust, C e C++ si osservano solo dove Valgrind parte».
- **Spiegazione:** sotto gVisor un fault sotto lo stack principale arriva come SEGV_ACCERR, e Valgrind non lo estende; nessuna opzione lo cambia. Docker, Podman e Kiri (runc) lo eseguono (`ef69774f9`).
- **Progetto e caso:** semver, tinyxml2, zlib e le fixture Rust e C/C++ — fixtures e finale, 16 novembre 2026.
- **Rimedio:** `8ef21896f` (16 novembre), `benchmarks/project-model/modal_pipeline.py` e `scripts/dynamic/callgrind.py`:
  - il driver usa i sandbox a macchina virtuale (experimental_options vm_runtime, Linux 7.3.4) per entrambe le fasi, quando l'esecuzione avvia Valgrind o ci sono servizi;
  - lì `valgrind true` passa a tutte le 48 dimensioni d'ambiente provate;
  - uno stack profondo dà 105 SEGV_MAPERR e 105 estensioni;
  - il cargo test della fixture gira sotto Callgrind.
- **Verifica:** conferma: semver 558 siti osservati, tinyxml2 552 con 26 buchi chiusi, zlib 148.
- **Stato:** risolto.
- **Note:** D-175, D-227, D-230.

#### D-210 Bear sotto gVisor fallisce circa una build su dieci
- **Descrizione:** il database di compilazione di un build Make poteva mancare.
- **Spiegazione:** sotto gVisor un rapporto di Bear fallisce circa una build su dieci.
- **Progetto e caso:** build Make sotto Bear — 16 novembre 2026.
- **Rimedio:** `f829df4b0` (16 novembre): una build fallita ha un secondo passaggio che aggiunge al database.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-211 Il server visuale resettava la connessione su una POST rifiutata
- **Descrizione:** verificando su Modal l'albero di `eacfad80e`, un test del server visuale cadeva solo sotto carico, con la connessione chiusa su una POST rifiutata.
- **Spiegazione:** il server rifiutava prima di leggere il corpo e chiudeva con il corpo non letto; il kernel resettava la connessione, e il reset poteva cancellare il 403 prima che il client lo leggesse.
- **Progetto e caso:** suite su Modal — 16 novembre 2026.
- **Rimedio:** `426626fbe` (16 novembre), `scripts/visual.py`:
  - chiude a tappe (RFC 9112 §9.6): prima SHUT_WR;
  - poi legge e scarta ciò che il client sta ancora mandando, al massimo 5 secondi, e chiude;
  - il corpo non viene mai interpretato.
- **Verifica:** test con una POST da 16 MiB oltre il limite.
- **Stato:** risolto.
- **Note:** —

#### D-212 Servizi di Compose che il passo non avvia
- **Descrizione:** spec, «Limiti»: sono lacune un'immagine che Compose costruisce, un comando con una variabile, uno script che cambia cartella, un bind mount fuori dal progetto, Compose in un job di GitLab.
- **Spiegazione:** quei casi non si leggono senza eseguire codice del progetto.
- **Progetto e caso:** spec del passo dinamico.
- **Rimedio:** dichiarati: quei test falliscono, e la corsa lo dice.
- **Verifica:** —
- **Stato:** buco dichiarato (`compose_not_read` e lacune dei servizi).
- **Note:** D-201.

#### D-213 I passi del job della CI prima dei test non giravano
- **Descrizione:** i test partivano senza ciò che la CI fa prima di loro, come una migrazione che crea le tabelle accanto al database di servizio.
- **Spiegazione:** il passo dinamico avviava i servizi del job, ma non i passi `run:` del job prima di quello dei test.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `f024ba3a3` (16 novembre, test-services), `scripts/container.py` e `scripts/dynamic/__init__.py`:
  - in ogni job il passo di test è il primo `run:` che lancia un ingresso `tests`;
  - i passi prima sono fatti `ci_steps`, eseguiti in ordine nella preparazione con i servizi accanto, con le variabili del workflow, del job e del passo e `CI=true`, sotto `bash -e` o `sh -e`;
  - prima dell'esecuzione il proxy se ne va e il pod si stacca dalla rete, così i test vedono i servizi già migrati e nient'altro;
  - altre azioni, `if:` e `${{ }}` sono `ci_step_not_run`; un passo che fallisce è `ci_step_failed`, con le ultime righe.
- **Verifica:**
  - dal commit, su Modal e su un Docker vero in un sandbox a macchina virtuale: una migrazione scrive una tabella accanto a postgres, i test la leggono, fuori non si esce (`tests/test_codebase_map_dynamic_services.py`, `test_on_modal_the_ci_s_steps_run_beside_the_services_and_the_tests_find_what_they_wrote`);
  - il giro della pipeline su tududi e fastapi è in corso (test-services): da verificare.
- **Stato:** risolto; i passi che non si possono eseguire sono un buco dichiarato (`ci_step_not_run`).
- **Note:** D-218.

#### D-214 Compose: i file del progetto montati nei servizi
- **Descrizione:** i file del progetto che Compose lega a un servizio non arrivavano al servizio.
- **Spiegazione:** il passo non portava nel servizio i bind mount che il file compose dichiara.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `f024ba3a3` (16 novembre, test-services), `scripts/premap/compose.py` e `scripts/dynamic/__init__.py`:
  - i file del progetto montati nei servizi vi sono copiati;
  - quelli fuori dal progetto sono `service_incomplete`;
  - gli script di shell che avviano Compose si leggono fino a tre livelli.
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`: `test_a_service_has_the_project_s_files_its_bind_mounts_name_before_it_starts`, `test_a_shell_script_a_step_or_a_test_script_runs_is_read_for_docker_compose_as_its_caller_is`); il giro su tududi e fastapi è in corso (D-213).
- **Stato:** risolto; un bind mount fuori dal progetto è un buco dichiarato (`service_incomplete`).
- **Note:** D-201, D-215.

#### D-215 Compose: `depends_on`
- **Descrizione:** l'ordine di avvio dei servizi di Compose non era seguito.
- **Spiegazione:** il passo non aspettava i servizi da cui un altro dipende.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** `f024ba3a3`: `depends_on` è rispettato, con le condizioni avviato, sano e uscito a 0; un servizio la cui dipendenza fallisce non parte, e la sua causa la nomina.
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`: `test_a_service_starts_after_those_it_depends_on_as_compose_s_condition_says`, `test_a_service_whose_dependency_fails_does_not_start_and_its_cause_names_it`).
- **Stato:** risolto.
- **Note:** D-214.

#### D-216 GitLab CI: i file che `.gitlab-ci.yml` include
- **Descrizione:** i servizi dichiarati in un file incluso non partono.
- **Spiegazione:** il lettore non segue gli `include`; la spec lo lascia fra le cose da decidere.
- **Progetto e caso:** passo dinamico — 16 novembre 2026.
- **Rimedio:** dichiarato con `23de469c4`: `include_not_read`.
- **Verifica:** solo test.
- **Stato:** aperto (test-services); oggi è il buco `include_not_read`.
- **Note:** D-202, D-217.

#### D-217 GitLab CI: `!reference`
- **Descrizione:** segnalato da team-lead.
- **Spiegazione:** da verificare: nessun commit lo descrive ancora.
- **Progetto e caso:** da verificare.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (test-services).
- **Note:** D-216.

#### D-218 Kiri non stacca un container dalla sua prima rete
- **Descrizione:** il sospetto era che Kiri non avesse `network connect`. Non è un difetto: test-services ha letto il sorgente di Kiri, il cui `ops.rs:54-58` serve `network connect` e `network disconnect`, e la via del pod funziona.
- **Spiegazione:**
  - Kiri 0.2.0 rifiuta solo di togliere un container dalla sua prima rete (`crates/kiri/src/daemon/engine.rs:2357`, citato in `scripts/container.py`, `leaves`);
  - il pod dei servizi deve lasciare la rete della preparazione prima dei test (D-213), e su Kiri non può.
- **Progetto e caso:** motore Kiri — 16 novembre 2026.
- **Rimedio:** `f024ba3a3` (16 novembre, test-services), `scripts/container.py` (`leaves`):
  - una prova crea un container sulla rete e lo stacca;
  - se il motore rifiuta, i passi della CI accanto ai servizi sono `ci_step_not_run`, con la risposta del motore: «… cannot take the pod of the services off the preparation's network before the tests, so no step runs beside them».
- **Verifica:** solo test (`tests/test_codebase_map_dynamic_services.py`, `test_an_engine_that_cannot_take_the_pod_off_its_network_runs_no_step_beside_the_services`).
- **Stato:** buco dichiarato (`ci_step_not_run`).
- **Note:** D-213, D-219.

#### D-219 Kiri 0.2.0 rifiuta un secondo motore nella stessa distribuzione WSL
- **Descrizione:** spec, «Da decidere»: «another Kiri engine is running on this machine».
- **Spiegazione:** anche in distribuzioni diverse i due motori condividono la rete della VM di WSL.
- **Progetto e caso:** spec del passo dinamico.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto (da decidere).
- **Note:** —

### Benchmark e documenti

#### D-220 Risposte attese: il workspace di javapoet e le soluzioni .NET di zlib
- **Descrizione:** le risposte attese di javapoet e zlib erano sbagliate.
- **Spiegazione:** contavano un build incluso come membro (javapoet) e le soluzioni .NET di zlib in modo diverso dal lettore corretto (D-010, D-016).
- **Progetto e caso:** javapoet, zlib — 15 novembre 2026.
- **Rimedio:** `a04ab36e1`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-010, D-016.

#### D-221 Lo schema del banco senza BOM, POM genitore e versioni centrali
- **Descrizione:** le risposte attese non distinguevano BOM, platform() e POM genitore, e una versione centrale dava più voci.
- **Spiegazione:**
  - un BOM importato, un platform() e un POM genitore sono dipendenze con scope bom o parent, e un arco se sono un'unità del progetto;
  - una versione scritta lontano dal punto che nomina il pacchetto dà una voce sola: l'unità dal file che nomina il pacchetto, la versione e `declared_in` dal file che la scrive.
- **Progetto e caso:** dieci progetti del corpus — 15 novembre 2026.
- **Rimedio:** `1420247ad` (15 novembre): otto voci aggiunte, undici cambiate, undici archi.
- **Verifica:** dipendenze attese da 861 a 869.
- **Stato:** risolto.
- **Note:** D-021, D-026.

#### D-222 `test_catalog` rosso: ANAGRAFICA.md non era l'uscita del generatore
- **Descrizione:** `test_catalog` era rosso da `a633ebd72`.
- **Spiegazione:** dopo le versioni delle immagini senza variante (D-046) ANAGRAFICA.md non era stata rigenerata.
- **Progetto e caso:** benchmark project-model — 16 novembre 2026.
- **Rimedio:** `68a846a4a` (16 novembre): ANAGRAFICA.md torna a essere l'uscita del generatore.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-046.

#### D-223 Le risposte attese delle fixture Android senza i build-tools
- **Descrizione:** le risposte attese di jvm-android-app-lib e mix-poly-firebase non dichiaravano android-build-tools.
- **Spiegazione:** android-build-tools 34.0.0 è il valore che dà il modello di Gradle, il predefinito di AGP 8.7.
- **Progetto e caso:** jvm-android-app-lib, mix-poly-firebase — 16 novembre 2026.
- **Rimedio:** `68a846a4a`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** D-044.

#### D-224 I test del registratore JVM saltati: l'immagine dei test senza JDK
- **Descrizione:** i test dell'agente JVM venivano saltati.
- **Spiegazione:** l'immagine dei test su Modal non aveva un JDK.
- **Progetto e caso:** `tests/modal_pytest.py` — 16 novembre 2026.
- **Rimedio:** `a633ebd72`: l'immagine dei test ha un JDK (openjdk-17-jdk-headless).
- **Verifica:** i test del registratore girano sulle suite di Modal; l'agente è provato su JDK 8 e 17 (dal commit).
- **Stato:** risolto.
- **Note:** D-178.

#### D-225 Due fixture con `node --test test/`
- **Descrizione:** due progetti di prova lanciavano `node --test test/`.
- **Spiegazione:** da Node 21 `node --test test/` non funziona.
- **Progetto e caso:** due fixture JavaScript — 16 novembre 2026.
- **Rimedio:** `12775fee3`: ora `node --test`.
- **Verifica:** solo test.
- **Stato:** risolto.
- **Note:** —

#### D-226 Toolchain Maven contate sbagliate per il frammento di `declared_in`
- **Descrizione:** java-versions: le toolchain delle 11 fixture Maven e della mista contano come sbagliate.
- **Spiegazione:** il solo frammento di `declared_in` differisce: `pom.xml#properties.maven.compiler.source` contro `pom.xml#maven.compiler.source`, come nelle altre fixture Maven del corpus (README del benchmark).
- **Progetto e caso:** jvm-ver-* e le fixture Maven — java-versions, 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** —

#### D-227 README del benchmark: Rust, C e C++ «solo dove Valgrind parte»
- **Descrizione:** il risultato del finale nel README dice ancora che Rust, C e C++ si osservano solo dove Valgrind parte, e che nei sandbox di Modal (gVisor) dipende dalla macchina.
- **Spiegazione:** è stato scritto prima di `8ef21896f`; la conferma li osserva nei sandbox a macchina virtuale.
- **Progetto e caso:** `benchmarks/project-model/README.md` — 16 novembre 2026.
- **Rimedio:** —
- **Verifica:** —
- **Stato:** aperto.
- **Note:** D-209.

#### D-228 Il rapporto dichiarava nulla la copertura a runtime
- **Descrizione:** i riferimenti del metodo dicevano «Exercised at runtime: none» e «runtime: none unless supplied».
- **Spiegazione:** il rapporto non leggeva il risultato del passo dinamico.
- **Progetto e caso:** il metodo di codebase-map — 16 novembre 2026.
- **Rimedio:** `78c03d6e8` (16 novembre):
  - `snapshot.py runtime <run-dir>` (`pipeline.runtime`) dà per linguaggio siti, archi, buchi chiusi, file eseguiti e non, come è finita ogni corsa, e i buchi;
  - phase-7, entry-analyze, entry-team-analyze, mcp ed evidence, il ruolo semantic-interconnect-mapper e `docs/plugins/codebase-map.md` rimandano a quel comando.
- **Verifica:** tre test in `tests/test_codebase_map_dynamic.py`; solo test.
- **Stato:** risolto.
- **Note:** D-229, D-230.

#### D-229 Spec: il passo 2 «non esegue codice del progetto»
- **Descrizione:** la tabella dei passi della spec del passo dinamico diceva «No» per il passo 2.
- **Spiegazione:** il passo 2 esegue la build da cui l'indice nasce: Java e Kotlin, TypeScript e JavaScript, C#, C e C++.
- **Progetto e caso:** `docs/specs/2026-11-12-passo-dinamico.md` — 16 novembre 2026.
- **Rimedio:** `78c03d6e8`: «Sì, solo nel container».
- **Verifica:** —
- **Stato:** risolto.
- **Note:** —

#### D-230 Spec: Rust, C e C++ «non provati» su Modal
- **Descrizione:** lo stato della spec diceva provati con il registro vero «salvo Rust, C e C++».
- **Spiegazione:** è stato scritto prima di `8ef21896f`.
- **Progetto e caso:** `docs/specs/2026-11-12-passo-dinamico.md` — 16 novembre 2026.
- **Rimedio:** `78c03d6e8`: osservati nei sandbox a macchina virtuale, con i numeri della conferma.
- **Verifica:** conferma: semver 558, tinyxml2 552 con 26 buchi chiusi, zlib 148.
- **Stato:** risolto.
- **Note:** D-209, D-227.

#### D-231 README, SKILL e riferimenti dicevano Jedi e «solo statica»
- **Descrizione:** documenti in ritardo sul codice.
- **Spiegazione:** non erano aggiornati dopo il passo dinamico e l'arrivo degli indici.
- **Progetto e caso:** README, SKILL, `references/snapshot.md` — 16 novembre 2026.
- **Rimedio:** `e617127c3` (16 novembre), insieme a riferimento, linguaggi e licenze: 16 linguaggi con 63 estensioni, ogni strumento con versione e licenza.
- **Verifica:** —
- **Stato:** risolto.
- **Note:** —

#### D-232 L'osservatore Python diceva che il passo non avvia servizi
- **Descrizione:** il docstring, il dettaglio di `services_unreachable` e quello del test lo dicevano ancora.
- **Spiegazione:** scritti prima di D-182.
- **Progetto e caso:** `scripts/dynamic/python.py` — 16 novembre 2026.
- **Rimedio:** `0ca9f1650` (16 novembre).
- **Verifica:** —
- **Stato:** risolto.
- **Note:** D-182.

#### D-233 Due script del benchmark dell'inferenza mai eseguiti
- **Descrizione:** `modal_scip.py` e `ts_compiler.py` seguono la nuova firma, ma «non sono stati eseguiti».
- **Spiegazione:** lo dice il commit.
- **Progetto e caso:** `benchmarks/inference-audit` — 16 novembre 2026.
- **Rimedio:** `137512c11` (16 novembre).
- **Verifica:** da verificare.
- **Stato:** aperto.
- **Note:** —

#### D-234 Un file dello snapshot senza dichiarazioni usciva dal progetto nel grafo
- **Descrizione:** un file che lo snapshot legge in modo lessicale non era più del progetto nel grafo del benchmark.
- **Spiegazione:** il grafo cercava le dichiarazioni del file nell'inventario.
- **Progetto e caso:** `benchmarks/inference-audit` — 13 novembre 2026.
- **Rimedio:** `53e219638` (13 novembre), `benchmarks/inference-audit/scip_graph.py`: un file così è `value`, «file without declarations in the snapshot».
- **Verifica:** `test_scip_graph.py`; solo test.
- **Stato:** risolto.
- **Note:** —

#### D-235 Pre-mappa: dipendenze sotto la soglia
- **Descrizione:** misura del 15 novembre sui 122 progetti: dipendenze 682, soglia 716 non raggiunta.
- **Spiegazione:** le cause sono D-018–D-030.
- **Progetto e caso:** corpus della pre-mappa — 15 novembre 2026 (`22524b57b`).
- **Rimedio:** `de353d251`, `99112d0b9`.
- **Verifica:** riproduzione di `99112d0b9`: 785 dipendenze trovate.
- **Stato:** risolto.
- **Note:** D-019.

## Commit feat senza difetto

Commit feat dal 13 novembre che aggiungono una funzione e non correggono nulla. Dove il messaggio dice ciò che resta da fare, lo dice la riga.

| Commit | Data | Cosa aggiunge | Resta da fare, dal messaggio |
| --- | --- | --- | --- |
| `adb40ece9` | 15/11 | .NET sull'SDK di global.json; standard C/C++ ed edizione Rust nella pre-mappa | — (prova vera su Kiri: 15 tool su 15 nel container) |
| `4af3f2ccf` | 15/11 | Meson configura ogni file cross del progetto | — |
| `623e1e8d3` | 15/11 | gli analyzer nel container usano la preparazione della pre-mappa | le prove vere su Kiri (JVM, clang) |
| `bf28909d5` | 15/11 | Gradle, Maven, sbt, .NET e i file di progetto come fonti della pre-mappa | — |
| `8e6d119c9` | 15/11 | il ripristino dei progetti .NET | — |
| `776e21487` | 15/11 | il ripristino di Go e Cargo, con il Rust dichiarato | — |
| `3b71648bc` | 15/11 | il ripristino di uv, Poetry e pip | — |
| `623880897` | 15/11 | il ripristino di npm, pnpm e Yarn | — |
| `fb6b15185` | 15/11 | il ripristino di Gradle e Maven (`restore_failed`) | gli analyzer non lo chiamano ancora (poi `623e1e8d3`) |
| `1a32c8a97` | 15/11 | toolchain e dipendenze dichiarate prima di ogni strumento | — (su Kiri, fixture CMake da 1 a 10 unità su 10; zlib da 39 a 44 su 122; tinyxml2 da 1 a 4 su 7) |
| `e4c54c8a0` | 15/11 | le versioni dei linguaggi che mancavano nella pre-mappa | le fonti project_files e gradle non ancora registrate (poi `bf28909d5`) |
| `12b2a2f15` | 15/11 | l'esecutore dei comandi della pre-mappa nel container | non ancora collegato alla pipeline; la prova su Kiri non fatta |
| `b75f4a450` | 15/11 | le unità chieste a CMake, Meson e Bazel | non eseguite finché manca l'esecutore |
| `7122b0aeb` | 15/11 | le fonti CMake, Meson e Bazel | non ancora registrate (poi `b75f4a450`) |
| `0e5d39892` | 15/11 | i fogli di stile come analyzer, con il loro runner Node | — |
| `e5fb3e34c` | 15/11 | eventi e avanzamento della pipeline per un client MCP | — |
| `8abdf7cfe` | 15/11 | ogni analyzer si dichiara da solo | — |
| `2825b5dfc` | 15/11 | la pipeline da un punto solo, fino al grafo completo | — |
| `e5d554f08` | 15/11 | la pipeline a step con il bus degli eventi | — |
| `7e15d4ee9` | 15/11 | C e C++ dall'indice di scip-clang con le unità della pre-mappa | — |
| `57457cb8d` | 15/11 | Java e Kotlin dall'indice di scip-java, una build per cartella | — |
| `1c2e7bc95` | 15/11 | Python dall'indice di scip-python, con le esecuzioni della pre-mappa | il passaggio per posizione resta provato su Jedi |
| `2ba02dfa3` | 15/11 | le cartelle di ogni indicizzatore dalla pre-mappa | — (nessun risultato cambia) |
| `70daa02d4` | 15/11 | la pre-mappa subito dopo lo snapshot | — |
| `f8984bb9c` | 15/11 | le cartelle di un indicizzatore nella pre-mappa | — |
| `73bae40e0` | 14/11 | affected misurato come fonte dei moduli | — (59 unità esatte su 447, contro 200 del lettore di Daodan) |
| `402277c65` | 14/11 | l'anagrafica dei 122 progetti di prova | — |
| `cfa07cdd3` | 14/11 | Python dall'indice nello stage | il cambio di fonte aspetta la pre-mappa |
| `7c80454f2` | 14/11 | una run nel container senza resti, con due volumi a nome | Kotlin e klaxon da rifare con i volumi |
| `706a75a03` | 14/11 | la pre-mappa, con le fonti unite per unità | — |
| `a8d5733b1` | 14/11 | adattatori dei fogli di stile con percorsi relativi | — |
| `d96b919c2` | 14/11 | Go, TypeScript, JavaScript e Rust dall'indice, con la copertura | — |
| `2e1480e8c` | 14/11 | frontend e backend di tududi uniti dalle rotte | — (il componente più grande dal 50 % al 96,4 % dei nodi) |
| `9a45fe6b3` | 14/11 | la prova di 36 strumenti per la pre-mappa su 122 progetti | — |
| `2f8988d19` | 14/11 | il grafo degli stili confermato su sei progetti veri | — |
| `182fa73b4` | 14/11 | il registro esatto delle chiamate per Python | — |
| `11db4a661` | 14/11 | la lettura di C, C++ e dei fogli di stile | — |
| `88c21ea89` | 14/11 | il registro dei collegamenti | — |
| `2adc041f1` | 14/11 | l'operazione che esegue un comando in un container | — |
| `7f6d71803` | 14/11 | la parte comune del grafo e gli adapter nel plugin | — |
| `420987ab0` | 14/11 | le seconde fonti di JavaScript e TypeScript, e Jelly | — |
| `b7c06adef` | 14/11 | il grafo CSS dichiara i file non letti | — |
| `82bfa2579` | 14/11 | il grafo di C e C++ dall'indice | — |
| `ec872b5ea` | 14/11 | il grafo dei fogli di stile | — |
| `dea9be296` | 14/11 | le domande mirate al motore Kotlin | — |
| `21f3c34fc` | 14/11 | le seconde fonti di Go e Python | — |
| `4cb6514c8` | 13/11 | l'adapter Kotlin marca incerti gli overload fra moduli | — |
| `2bed601e8` | 13/11 | l'adapter Java dichiara le chiamate super e le costanti enum | — |
| `a954ced86` | 13/11 | le prove del grafo nel repository e l'adapter Python | — |
| `496ba3721` | 13/11 | la parte comune lascia decidere all'adapter | — |
| `2b220ea5d` | 13/11 | il grafo letto per intero dall'indice | — |
| `05c1c5de4` | 13/11 | la misura dell'indice SCIP contro i motori | — |
| `1bcee848b` | 13/11 | la verifica dei motori con etichette | — |
