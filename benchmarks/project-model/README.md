# Benchmark: la pre-mappa del progetto da strumenti esistenti

Misura quanto di una **pre-mappa** danno gli strumenti esistenti, prima di ogni analisi e senza codice di riconoscimento di Daodan. La pre-mappa contiene:

- linguaggi;
- file esclusi;
- unità che il build system dichiara, con radice, sorgenti, dipendenze fra unità e configurazione per gli indicizzatori;
- workspace;
- versioni di toolchain chieste;
- dipendenze esterne con versione;
- framework e servizi;
- bisogno di un container.

È una ricognizione, senza soglie. La ricerca che l'ha motivata è [2026-11-14-project-model-detection.md](../../docs/research/2026-11-14-project-model-detection.md); il verdetto e i risultati sono in [REPORT.md](REPORT.md).

## Come funziona

- `fixtures/<famiglia>-<nome>/` è un progetto in miniatura. Il suo `expected.json` è la verità scritta a mano, letta dai file e mai dall'uscita di uno strumento. La forma e le regole sono in [SCHEMA.md](SCHEMA.md).
- `tools/<tool>.py` è un adattatore per strumento: `run(fixture_dir, work_dir)` restituisce la stessa forma, con le sole faccette che lo strumento dà.
- `modal_<gruppo>.py` esegue gli strumenti di un gruppo su Modal, mai su questo PC.
- `results/<tool>.json` tiene, per fixture: uscita grezza riassunta, uscita normalizzata, punteggio, secondi, memoria di picco, tentativi di rete, seconda esecuzione offline, codice del progetto eseguito.
- `score.py` dà il punteggio di ogni faccetta: trovate, sbagliate, mancate, in più. Una faccetta che lo strumento non dà conta come "non data", non come zero.
- `cases.json` è il dominio chiuso dei casi di test; ogni `expected.json` elenca i suoi in `cases`.
- `catalog.py` scrive [ANAGRAFICA.md](ANAGRAFICA.md) dai dati: per ogni progetto origine, tecnologie, versioni dichiarate, framework, servizi e casi, poi la copertura dei casi.

## Dopo una modifica

Il corpus si riprova dopo ogni modifica a Daodan, a un adattatore, a un `expected.json` o a `cases.json`. Dalla cartella del benchmark:

1. `python -m unittest test_score.py test_catalog.py test_pipeline_report.py`: test del punteggio, dell'anagrafica e del rapporto della pipeline.
2. `python score.py --check all`: forma di ogni `expected.json`, casi contro `cases.json` e contro i dati, casi che nessun progetto usa.
3. `python catalog.py`: riscrive ANAGRAFICA.md; `python catalog.py --check` dice solo se è da riscrivere.
4. Su Modal, il driver `modal_<gruppo>.py` del gruppo toccato: riscrive i suoi `results/<tool>.json`.
5. `python score.py all all`, o `python score.py <tool> <famiglia>`: tabelle da confrontare con quelle di REPORT.md.

## Parametri

### Corpus

Ogni fixture mette alla prova un punto in cui un lettore ingenuo sbaglia; il dettaglio è nel suo campo `traps`.

Le famiglie `js`, `py`, `jvm`, `sys` e `mix` sono progetti in miniatura scritti per il benchmark. La famiglia `real` è fatta di repository veri di GitHub con più moduli (front end, back end, servizi, più linguaggi e build system affiancati), descritti senza copiarne i file:

- `source.json` dà repository e commit, e i runner li clonano a quel commit nel container;
- `expected.json` viene dai file del repository a quel commit ed è completo per unità, workspace, toolchain, framework, servizi ed esclusi;
- le dipendenze sono complete solo per al massimo tre unità piccole per repository (`unknown` con `known`);
- `connections` elenca i punti di contatto fra unità per il grafo unico, senza entrare nel punteggio.

Il frammento di `declared_in` di una toolchain Gradle è il nome che il modello di Gradle dà al valore: `kotlin { jvmToolchain(N) }` imposta la toolchain dell'estensione `java`, e il modello non sa dire quale DSL l'ha scritta, quindi anche lì è `#java.toolchain.languageVersion`.

I runner eseguono `real` in un secondo passaggio.

| Famiglia | Fixture | Cosa mette alla prova |
| --- | --- | --- |
| js | `js-angular` | unità dichiarate da `angular.json`, non da `package.json`; dipendenza via alias di `tsconfig` |
| js | `js-bun` | Bun riconosciuto solo da `bun.lock` testuale |
| js | `js-cjs-esm-exports` | `type: module`, `.cjs` e `.mjs`, condizioni `import` e `require` di `exports` |
| js | `js-deno` | nessun `package.json`; dipendenze nell'import map, uno schema per registro |
| js | `js-lerna` | membri in `lerna.json`, non in `workspaces` |
| js | `js-local-and-git-deps` | `file:` e dipendenze git senza workspace |
| js | `js-nextjs` | alias `@/` sulla radice; `next-env.d.ts` generato; servizio dal codice |
| js | `js-node-scripts` | nessun manifest: nessuna unità, un import esterno |
| js | `js-npm-single` | lockfile v3 senza versione di npm dichiarata |
| js | `js-npm-workspaces` | radice del workspace che possiede dipendenze; collegamenti interni |
| js | `js-nx` | progetti Nx con `project.json`, dipendenza solo da `paths` |
| js | `js-pnpm-workspace` | `catalog:` di pnpm; `workspace:*` |
| js | `js-static-html` | dipendenze solo da import map e `<script>` in HTML |
| js | `js-sveltekit` | `tsconfig` che estende un file generato assente |
| js | `js-turborepo` | Turborepo sopra workspace npm: lo strumento del workspace è npm |
| js | `js-vendored-generated` | file vendored e generati da escludere |
| js | `js-version-conflict` | quattro versioni di Node in disaccordo (`engines`, `volta`, `.nvmrc`, `packageManager`) |
| js | `js-vite-react-ts` | `tsconfig` radice con sole `references`; alias doppio in Vite e `tsconfig` |
| js | `js-vue-pnpm` | `.vue` con TypeScript e JavaScript; pnpm solo da `packageManager` |
| js | `js-yarn-berry` | lockfile Berry; radice senza nome |
| py | `py-conda-env` | dipendenze conda e lista `pip:` annidata; `python=` è toolchain |
| py | `py-django` | solo `requirements.txt`; migrazioni con intestazione "Generated" ma scritte a mano |
| py | `py-fastapi-compose` | PostgreSQL e Redis solo in `docker-compose.yml` |
| py | `py-hatch-envs` | ambienti Hatch, non extra né gruppi |
| py | `py-monorepo-path-deps` | tre progetti, dipendenze per percorso senza workspace |
| py | `py-namespace-packages` | pacchetto namespace PEP 420 diviso fra due unità |
| py | `py-notebooks` | dipendenza installata da una cella `%pip` |
| py | `py-pdm` | dipendenze di sviluppo in una tabella PDM |
| py | `py-pep723-scripts` | dipendenze nei blocchi PEP 723 degli script |
| py | `py-pip-tools` | `.in` dichiarazione, `.txt` lockfile compilato |
| py | `py-pipenv` | Pipfile senza nome; `develop` nel lock |
| py | `py-poetry-groups` | `python` fra le dipendenze di Poetry; gruppi e extra |
| py | `py-requirements-includes` | `-r` e `-c` annidati; un vincolo non è una dipendenza |
| py | `py-setup-cfg-extras` | metadati in `setup.cfg`; versione da `attr:` |
| py | `py-setup-py-dynamic` | `install_requires` calcolato: serve un container |
| py | `py-setup-py-static` | `package_dir` verso `lib/` |
| py | `py-undeclared-scripts` | nulla dichiarato: i nomi indovinati dagli import sono errori |
| py | `py-uv-src-layout` | layout `src`, gruppi PEP 735, `required-version` di uv |
| py | `py-uv-workspace` | radice virtuale; membro del workspace come dipendenza interna |
| py | `py-vendored-generated` | copia vendored con il suo `vendor.txt`; file protoc |
| py | `py-version-disagree` | sette versioni di Python in disaccordo, compresi i bersagli di Pyright, mypy e Ruff |
| jvm | `jvm-gradle-groovy-wrapper` | wrapper senza jar; script del wrapper vendored |
| jvm | `jvm-gradle-kts-catalog-composite` | versioni nel catalogo; radice dichiarata solo da `settings.gradle.kts`; build composito |
| jvm | `jvm-gradle-locking` | range nel build, versioni in `gradle.lockfile` |
| jvm | `jvm-maven-multi-bom-profile` | cartelle diverse dagli artifactId; modulo solo sotto un profilo; BOM |
| jvm | `jvm-maven-release-apt` | proprietà `java.version` che nessuno legge; processori di annotazioni |
| jvm | `jvm-maven-wrapper` | versione di Maven dichiarata solo dal wrapper |
| jvm | `jvm-ver-mvn-*` (11) | lo stesso progetto Maven con un livello Java per fixture: `source` e `target` da 1.5 a 25, `release` 8, 1.6 nella configurazione del plugin |
| jvm | `jvm-ver-gradle-tc*` (4), `-src*` (2) | lo stesso progetto Gradle con toolchain 8, 11, 21, 25 o con `sourceCompatibility` 1.6 e 1.8: un livello non è un JDK da trovare |
| jvm | `jvm-ver-gradle-mixed-tc8` | Java e Kotlin insieme con `jvmToolchain(8)` |
| sys | `sys-go-buildtags` | suffissi di piattaforma nei nomi dei file come vincoli di build |
| sys | `sys-go-cgo` | C compilato dal comando go; flag nei commenti `#cgo` |
| sys | `sys-go-generated` | file generato ma versionato e compilato |
| sys | `sys-go-nested` | modulo annidato che `./...` salta; cartella `_examples` |
| sys | `sys-go-single` | due righe di `go.sum` per modulo; `go` non è un toolchain fissato |
| sys | `sys-go-toolchain` | `go`, `toolchain` e versione fissata in disaccordo |
| sys | `sys-go-vendor` | `vendor/` non è codice del progetto; `-mod=vendor` implicito |
| sys | `sys-go-workspace` | `replace` di `go.work` che cambia una versione per tutto il workspace |
| sys | `sys-rust-buildrs` | `build.rs` per convenzione; `include!` di un file generato assente |
| sys | `sys-rust-features` | dipendenze opzionali fuori dal build di default |
| sys | `sys-rust-path-git` | dipendenze per percorso e git senza workspace |
| sys | `sys-rust-shared-test-module` | modulo di test condiviso fra due crate di test |
| sys | `sys-rust-single` | due target trovati per convenzione; nome del crate con il trattino |
| sys | `sys-rust-tauri` | pacchetto npm e crate Cargo con lo stesso nome |
| sys | `sys-rust-toolchain-conflict` | `rust-toolchain` e `rust-toolchain.toml` insieme; `rust-version` |
| sys | `sys-rust-workspace` | manifest virtuale, glob dei membri con `exclude` |
| mix | `mix-dart-flutter` | tre pacchetti pub senza workspace |
| mix | `mix-dotnet-central` | gestione centrale delle versioni NuGet con `VersionOverride` |
| mix | `mix-php-laravel` | app Composer e build Vite nella stessa radice |
| mix | `mix-ruby-rails` | progetto Bundler senza gemspec |
| mix | `mix-swift-spm` | target del pacchetto come source set; prodotto con un altro nome |

### Strumenti

Versioni, comandi e vincoli verificati si leggono in `results/<tool>.json`; la tabella si completa quando i runner hanno finito.

| Gruppo | Strumenti | Driver |
| --- | --- | --- |
| `lang` | scc, tokei, go-enry, Linguist, dati di Linguist, Magika | `modal_lang.py` |
| `sbom` | Syft, Trivy, osv-scanner, cdxgen, ScanCode, component-detection | `modal_sbom.py` |
| `native` | il comando di modello di ogni build tool (`go list`, `cargo metadata`, `npm`/`pnpm ls`, `uv`, `tsc --showConfig`, Gradle, Maven, …), `.gitmodules`, deptry, dependency-cruiser, uv per PEP 723; `modules.py` di Daodan come riferimento | `modal_native.py` |
| `versions` | mise, proto, Renovate, Railpack, `GOTOOLCHAIN`, uv, rustup, corepack | `modal_versions.py` |
| `frameworks` | Specfy stack-analyser, Vercel fs-detectors, Netlify build-info, devfile/alizer; il registro di Daodan come riferimento | `modal_frameworks.py` |

### Vincoli controllati per ogni strumento e fixture

| Vincolo | Come si misura |
| --- | --- |
| Esegue codice del progetto | `executed_project_code`: `yes`, `no` o `unknown`, dalla traccia dei processi del runner |
| Rete | `network_attempts`: connessioni tentate durante l'esecuzione |
| Seconda esecuzione offline | `offline_second_run`: la stessa uscita con la rete bloccata |
| Binario per Windows | dalla pagina delle release, una volta per strumento |
| Tempo e memoria | `seconds`, `peak_mb` |

## Risultati

14 novembre 2026: 59 strumenti e comandi sulle 122 fixture. Le tabelle vengono da `python score.py all all`; la lettura e il verdetto sono in [REPORT.md](REPORT.md). In breve:

- linguaggi ed esclusi vengono da go-enry o dai dati di Linguist;
- dipendenze e toolchain dichiarate da Renovate, le versioni bloccate da Trivy;
- le unità con sorgenti e configurazione solo dai comandi di modello di ogni build tool, parte dei quali va nel container;
- framework, servizi e bisogno di container restano scoperti.

## Il grafo completo sul corpus

Verifica che la pipeline di Daodan (`pipeline.run`: scan, stack, analyze, dynamic, union) dia il grafo completo di ogni progetto del corpus: per ogni linguaggio dello snapshot uno stato, i file nell'indice, i siti con risposta e i buchi con la loro classe. È una ricognizione, senza soglie.

### Parametri

Dalla cartella del benchmark:

- Corpus: le 140 fixture. `js`, `py`, `jvm`, `sys` e `mix` sono i 122 progetti in miniatura, `real` i 18 repository con `source.json`. Le 18 `jvm-ver-*` sono del 16 novembre 2026, dopo il giro finale sui 122 casi.
- Giro, su Modal e mai su questo PC: `python -m modal run modal_pipeline.py --cases js,py,jvm,sys,mix,real --out results/pipeline/<giro>.json`. `--cases` accetta anche nomi di fixture; `--chunk` (4) dice quante fixture di una famiglia vanno in un container. Accanto ai casi, `code` dice il codice di Daodan che il giro ha eseguito: il commit della checkout, l'albero git della copia caricata e i percorsi in cui la copia differisce dal commit.
- Rapporto: `python pipeline_report.py results/pipeline/<giro>.json [<altro>.json ...] [--compare <precedente>.report.json]`. Un caso di un file successivo sostituisce lo stesso caso dei precedenti. Scrive `<giro>.report.md` e, accanto, gli stessi numeri in `<giro>.report.json`; Il rapporto nomina il codice di ogni file; `--compare` dice prima se i due giri hanno eseguito lo stesso codice (lo stesso albero, non lo stesso commit), poi stampa cosa cambia per linguaggio e per caso: stati, buchi in più o in meno.

I giri stanno in `results/pipeline/`, una sottocartella: `score.py` legge come strumento ogni `.json` di `results/`.

Conta come risultato, per linguaggio su tutti i casi: i casi `fresh` sui casi che lo contengono, i file indicizzati sui file dello snapshot, la quota dei siti con risposta. Il rapporto dà anche casi falliti e secondi, i motivi degli stati diversi da `fresh`, i file fuori dall'indice, i linguaggi senza analizzatore, il punteggio della pre-mappa per faccetta, i gap per tipo e gli esiti dei container.

### Risultati

Giro finale, 16 novembre 2026, sui 122 casi (`results/pipeline/2026-11-16-finale.json`, rapporto in `2026-11-16-finale.report.md`), sul codice fino a `492a7b212`: nessun caso fallito, 23.280 secondi, mediana 124 per caso, circa 2,3 USD. I giri precedenti dello stesso giorno sono accanto (`2026-11-16-fixtures`, `-real-3`, `-giro-2`).

| Linguaggio | Casi `fresh` / casi | File indicizzati / nello snapshot | Quota risposta | Passo dinamico: casi osservati, siti |
| --- | --- | --- | --- | --- |
| c | 6 / 9 | 49 / 72 | 40,7 % | 2, 149 |
| cpp | 6 / 9 | 18 / 19 | 89,2 % | 0, 0 |
| csharp | 4 / 5 | 561 / 561 | 56,1 % | nessun osservatore |
| go | 14 / 15 | 678 / 679 | 99,5 % | 5, 13.365 |
| java | 16 / 18 | 261 / 278 | 99,7 % | 9, 7.695 |
| javascript | 31 / 32 | 1.254 / 1.254 | 72,9 % | 4, 763 |
| kotlin | 4 / 11 | 103 / 115 | 93,1 % | 4, 1.796 |
| python | 34 / 34 | 185 / 185 | 89,1 % | 2, 70 |
| rust | 13 / 13 | 145 / 154 | 88,5 % | 1, 1 |
| stylesheet | 23 / 24 | 3.336 / 3.402 | 26,3 % | nessun osservatore |
| svelte | 1 / 2 | 0 / 4 | 26,7 % | nessun osservatore |
| typescript | 20 / 21 | 2.965 / 2.967 | 90,4 % | 3, 73.230 |
| vue | 2 / 2 | 0 / 410 | 28,2 % | nessun osservatore |

- Il passo dinamico osserva 97.069 siti e chiude 4.954 buchi; nei progetti in miniatura quasi sempre non ci sono test da lanciare, e lo dice.
- Restavano aperti: i template di Vue e Svelte (nessun file letto), le classi Tailwind dello stylesheet, C# (56 % e nessun osservatore), il C dei contrib di zlib, i test che vogliono un servizio (un database) e Kotlin su Android, che scip-java non compila; i giri sotto dicono che cosa è cambiato.
- Rust, C e C++ si osservavano solo dove Valgrind partiva, e sotto il gVisor dei sandbox di Modal non parte: dopo questo giro il driver dà le VM Sandbox agli osservatori nativi, dove parte (`8ef21896f`), e alle corse con servizi, con Docker (`17babc624`).

Giro sulle 18 `jvm-ver-*`, 16 novembre 2026 (`results/pipeline/2026-11-16-java-versions.json`, rapporto in `2026-11-16-java-versions.report.md`), sul codice a `68a846a4a`: nessun caso fallito, 3.527 secondi, mediana 178 per caso.

- Java è `fresh` e osservato in tutte le 18: 37 file su 37 nell'indice, 453 siti tutti con risposta, 10-14 siti osservati per caso; Kotlin è `fresh` e osservato nella fixture mista.
- Prima di `21b3cb39b` sette non davano indice: Maven con livello 5 e 6 (tre), Gradle con toolchain 8 e 11, con livello 1.6 e la mista; con Java 25 i test fallivano sotto il registratore.
- Lo dicono i buchi: `jdk_unsupported` nelle Maven sotto il 17 (l'indice nomina le classi del JDK 17), `build_edited` dove il build dichiarato non dà indice e il secondo, con livelli o toolchain alzati, sì.
- Java 9 e 14 non hanno un JDK installabile: il passo dinamico li osserva sul JDK 17 e lo dice (`toolchain_unavailable`).
- Pre-mappa: il rapporto conta come sbagliate le toolchain delle 11 fixture Maven e della mista per il solo frammento di `declared_in`. Con il corpus di `1bd53689a`, che nomina un'impostazione del pom con il suo percorso nel pom (`pom.xml#properties.maven.compiler.source`) e una toolchain Gradle come la nomina il modello di Gradle, `score.py` sul giro salvato trova 28 toolchain su 30: le 2 di jvm-ver-mvn-cfg6 restano sbagliate per il solo frammento, perché il giro precede `eef3e1fef`, da cui la pre-mappa scrive `maven-compiler-plugin.configuration.source` e non più `maven-compiler-plugin.source`.

Giro di conferma, 16 novembre 2026, su 32 casi: le fixture di sistema e sette repository veri (`results/pipeline/2026-11-16-conferma.json`, rapporto in `2026-11-16-conferma.report.md`, salvato in `828b5413b`): nessun caso fallito, 6.344 secondi, mediana 133 per caso.

- Nelle VM Sandbox Rust, C e C++ si osservano: semver 558 siti, tinyxml2 552 con 26 buchi chiusi, zlib 148.
- python-semver è osservato, 1.046 siti, con i link e le dipendenze di tox; i test del backend di tududi girano con il PostgreSQL della sua CI: 3.779 siti JavaScript, 691 buchi chiusi.
- Restavano fastapi (la versione di Python), kotlinconf (un plugin del build vuole una JVM 21), i test del frontend di tududi (92 siti TypeScript) e C# su DotZLib di zlib, un progetto di Visual Studio .NET 2002-2003, che da `73b645531` è `unavailable` e non si lancia.

Giri JVM, 16 novembre 2026, sull'albero di lavoro con il codice poi committato:

- otel-demo, jvm-android-app-lib e mix-poly-firebase (`results/pipeline/2026-11-16-jvm-otel-android.json`, codice di `39805f5e7`): nessun caso fallito, 2.037 secondi. Java di otel-demo è `fresh`, 9 file su 9 e 693 siti tutti con risposta (nel giro finale `failed`), e l'osservatore registra 297 siti; Kotlin resta `failed` nei tre casi: in otel-demo nessun compito Kotlin compila i suoi file, i due Android si fermano su `google-services.json`, che il progetto tiene fuori dal repository (`build_input_missing`).
- kotlinconf (`results/pipeline/2026-11-16-jvm-kotlinconf.json`, codice di `22dca6da8`): 754 secondi; il modello di Gradle riparte sul JDK 21 che il devcontainer dichiara e dà le toolchain del build, e Kotlin si ferma dopo, su un compito `compileKotlinJvm` che `:app:adminApp` non ha.
- kotlinconf con ogni progetto che compila solo i compiti che ha (`results/pipeline/2026-11-16-jvm-kotlinconf-kmp.json`, codice di `a13d55787`): 1.915 secondi; Kotlin è `fresh`, 226 file su 271 nell'indice, 16.830 siti, 76,0 % con risposta, e l'osservatore registra 984 siti. I 45 file fuori dicono perché: nessun compito di compilazione Kotlin li elenca (34) o sono script Gradle (11).

Giro dei passi della CI, 16 novembre 2026, su tududi e fastapi (`results/pipeline/2026-11-16-ci-steps.json`, salvato in `aea1c8c3b`): nessun caso fallito, 1.909 secondi.

- tududi: i tre passi del job (installazione 36 secondi, lint 19, bootstrap e migrazioni 1) girano accanto a postgres:16-alpine prima dei test; il passo dinamico osserva 13.214 siti JavaScript e 20.202 TypeScript, contro i 3.779 e i 92 della conferma, un salto che viene anche dai bundle in memoria e dalle CPU scalate, non solo dai passi.
- fastapi: «Migrate DB» gira e fallisce, e pytest e Playwright si fermano sulle stesse impostazioni mancanti, che stanno nel `.env` tracciato del template e che la copia di Daodan allora non portava.

Giro del `.env` tracciato, 16 novembre 2026, su fastapi e tududi (`results/pipeline/2026-11-16-dotenv.json`, salvato in `b1f14ac08`): nessun caso fallito, 2.370 secondi.

- fastapi: db, mailpit e adminer partono e «Migrate DB» esce con 0; pytest si ferma alla raccolta (codice 4: manca `backend/app/frontend`) e i test del frontend escono con 1, quindi Python e TypeScript restano `not-run`. La password del `.env` del template non compare nel risultato.
- tududi: i tre passi del job escono con 0 accanto a postgres:16-alpine; il passo dinamico osserva 11.369 siti JavaScript e 20.192 TypeScript.

Prova della regola invalicabile per Rust, 16 novembre 2026 (`modal run modal_rust_container.py::rust_container`, `c714e6298`): un crate il cui build script imposta un cfg e una macro procedurale che genera una funzione, ognuno con un segno dove gira, e cargo, rustc, rust-analyzer e rustup sul PATH della macchina sostituiti da finti che lasciano un segno. Sulla macchina nessun segno e nessun finto chiamato; nell'indice del container la funzione sotto il cfg si risolve e quella generata ha il suo nome, definita in nessun file (`undefined-project-symbol`).
