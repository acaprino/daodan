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
- `modal_catalog.py` fa girare su Modal il controllo, `catalog.py` e le tabelle di `score.py`, e sul PC scrive solo ANAGRAFICA.md.

## Regole di riconoscimento di Specfy e Daodan

La misura del 21 novembre 2026 conta ogni nome atteso una volta per progetto. La faccetta `frameworks` comprende anche librerie e strumenti. I 180 progetti hanno 590 nomi attesi in questa faccetta e 541 nei servizi. Le registrazioni della pre-mappa coprono 178 progetti. Mancano 21 nomi di framework e 23 di servizi nei due progetti senza registrazione, `real-stack-jellyfin` e `real-stack-kuvasz`.

| Misura | Progetti | Framework, librerie e strumenti | Servizi |
| --- | ---: | ---: | ---: |
| Specfy 1.27.6, risultati originali archiviati | 122 | 55 / 198 | 28 / 123 |
| Registro distribuito in `ca89d6387`, su dichiarazioni registrate | 178 | 341 / 569 | 142 / 518 |
| Registro aggiornato, sulle stesse dichiarazioni | 178 | 475 / 569 | 232 / 518 |

Il file `service-registry.json` misurato contiene 2.562 voci e ha SHA-256 `e93c2970c83d892ff5cf8922fcc63f2d6037c459a8158652b3625319cda83f87`.

Il replay applica `service_registry.check_packages` e `check_files` a entrambi i registri. Usa i pacchetti estratti da Renovate, le immagini dichiarate nei workflow, le immagini base di BuildKit e i percorsi di go-enry ammessi dall’inventario. Legge gli attesi solo per assegnare il punteggio. Il rilevamento per modulo, i modelli di build che richiedono una checkout, il testo delle configurazioni e i riferimenti nel sorgente si misurano con `modal_stack.py`. Ad esempio il modello Gradle archiviato per `jvm-spring-boot-managed` riporta gli starter Web e Data JPA. Lo stack completo archiviato vi trova Spring MVC e Spring Data JPA.

Il conteggio originale di Specfy usa tutti gli ID emessi, compresi quelli classificati come builder. L’identità del prodotto tiene conto di varianti come «CypressCI» e «Cypress» e, quando il nome omette il fornitore, dell’ID specifico come `gcp.gcs`. «Vite» e «Vite+» contano separatamente. Le correzioni di punteggio si applicano anche al registro di partenza. Spring Boot era già riconoscibile dai pacchetti nei sette progetti che lo attendono. I cinque con uscita Specfy originale disponibile lo omettono tutti.

Sui 122 progetti in comune, Specfy aveva omesso 143 nomi di framework e 95 servizi. Il replay recuperava rispettivamente 90 e 19 di queste omissioni con il vecchio registro, 107 e 38 con quello aggiornato. Sulle 178 registrazioni il nuovo catalogo recupera 134 occorrenze di framework, librerie o strumenti e 90 di servizi, distribuite su 47 progetti. Conserva tutti i nomi attesi già rilevati. Trova inoltre 81 nuove occorrenze di framework, librerie o strumenti fuori dagli attesi, che in questa faccetta sono selettivi. Per i servizi le annotazioni mirano alla completezza. I due nuovi servizi fuori dagli attesi sono i driver MySQL e PostgreSQL di `tools/go.mod` in Owncast, da verificare rispetto allo stack dell’applicazione. I servizi fuori dagli attesi nel complesso passano da 58 a 57.

| Perché un nome atteso resta senza riscontro nel replay | Framework, librerie e strumenti | Servizi |
| --- | ---: | ---: |
| La voce ha regole per pacchetti o file, ma nessuna dichiarazione registrata corrisponde | 84 | 149 |
| La voce non ha regole per pacchetti o file. Altri segnali possibili includono un import Swift o un URL nel sorgente | 4 | 34 |
| Il catalogo non presenta il nome nella faccetta attesa, dopo aver applicato le equivalenze documentate nel codice | 6 | 103 |

Tra gli ultimi casi figurano Firebase, atteso anche come framework e catalogato come servizio, e SMTP, atteso come servizio in 23 progetti. Una libreria compatibile con un protocollo non identifica il fornitore che un progetto usa.

Questo comando, dalla radice del repository, scrive per progetto il percorso che prova ciascun nuovo riconoscimento, i nomi mancanti e le segnalazioni aggiuntive.

```sh
python benchmarks/project-model/replay_registry_coverage.py --baseline ca89d63877f8e3f9f94d8387a4b9154c5cdf9f1f --out registry-coverage.json
```

Il comando `smoke` misura Specfy con le regole Daodan e l’eseguibile originale sullo stesso progetto e nella stessa immagine Modal.

```sh
modal deploy benchmarks/project-model/modal_frameworks.py
python benchmarks/project-model/modal_frameworks.py smoke --tools specfy_stack_analyser,specfy_daodan --fixtures py-fastapi-compose
```

La tabella riporta l’archivio dell’eseguibile originale e il replay dei registri. La prova end-to-end dell’adattatore Specfy aggiornato resta da misurare su Modal.

## Dopo una modifica

Il corpus si riprova dopo ogni modifica a Daodan, a un adattatore, a un `expected.json` o a `cases.json`. Su questo PC non gira niente: ogni passo va su Modal, dalla radice del repository.

1. `python benchmarks/project-model/modal_catalog.py`: controlla ogni `expected.json` (forma, casi contro `cases.json` e contro i dati, casi che nessun progetto usa), riscrive ANAGRAFICA.md e stampa le tabelle per strumento e faccetta; `modal_catalog.py <tool> <famiglia>` stampa solo quelle.
2. `python tests/modal_pytest.py benchmarks/project-model/test_score.py benchmarks/project-model/test_catalog.py benchmarks/project-model/test_pipeline_report.py -q`: test del punteggio, dell'anagrafica e del rapporto della pipeline; falliscono anche se un `expected.json` non passa il controllo o se ANAGRAFICA.md è da riscrivere.
3. Il driver `modal_<gruppo>.py` del gruppo toccato: riscrive i suoi `results/<tool>.json`; poi di nuovo il passo 1, per le tabelle da confrontare con quelle di REPORT.md.

## Parametri

### Corpus

Ogni fixture mette alla prova un punto in cui un lettore ingenuo sbaglia; il dettaglio è nel suo campo `traps`.

Le famiglie `js`, `py`, `jvm`, `sys` e `mix` sono progetti in miniatura scritti per il benchmark. La famiglia `real` è fatta di repository veri di GitHub con più moduli (front end, back end, servizi, più linguaggi e build system affiancati), descritti senza copiarne i file:

- `source.json` dà repository e commit, e i runner li clonano a quel commit nel container;
- `expected.json` viene dai file del repository a quel commit ed è completo per unità, workspace, toolchain, framework, servizi ed esclusi;
- le dipendenze sono complete solo per al massimo tre unità piccole per repository (`unknown` con `known`);
- `connections` elenca i punti di contatto fra unità per il grafo unico, senza entrare nel punteggio.
- le 40 cartelle `real-stack-*` misurano solo `frameworks` e `services` per unità, per lo step `stack`: ogni voce porta l'evidenza con la riga (`pom.xml#L42`) e le altre facce stanno in `unknown`.

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

Ripristino Node su Modal, 21 novembre 2026 (`modal run modal_pipeline.py --cases js-npm-single,py-uv-src-layout`, sul commit `a664e869d` con l'albero di lavoro del giorno). Dopo la condivisione del ripristino Node (`node_preparation`) le righe del ripristino arrivano al motore in `node_restore`, che `sandbox_run` ignorava: su `js-npm-single` scip-typescript girava senza i pacchetti del progetto (tipi: solo `@types/node`) e `npm test` usciva con 1, «Cannot find module 'ms'», passo dinamico `not-run`. Ora `sandbox_run` esegue il ripristino nella sandbox di preparazione di ogni run. Rilanciato sullo stesso caso: tipi di `lodash` e `ms`, test uscito con 0, 6 siti osservati e 6 archi, copertura `complete`, 95,5 secondi. `py-uv-src-layout`: scip-python 0.6.8 e Pyright 1.1.414, `fresh`, 8 siti su 8, nessun test dichiarato, 126,3 secondi. Su Modal ogni run ripristina per sé: la condivisione fra i run di un'analisi qui non si misura.

## Lo step `stack` sul corpus

Misura lo step `stack` della pipeline (`scripts/technologies.py`, `daodan/technologies/v1`): le tecnologie del progetto per unità di build, dal solo registro (`data/service-registry.json`, 2.172 voci), senza eseguire nulla del progetto. Il 14 novembre il registro era stato misurato solo sui servizi (`daodan_registry`, 45 su 123); questo è il primo giro dello step nuovo.

### Parametri

- Corpus: tutte le fixture con `expected.json`, 180 (`js`, `py`, `jvm`, `sys`, `mix`, `real` e le 40 `real-stack-*`, che misurano solo framework e servizi). Il driver prende anche le fixture nuove, senza modifiche: quelle con `source.json` dal loro archivio sul volume (`modal_native.py prepare`) o, senza archivio, da un clone alla revisione fissata. `expected.json` e `source.json` non entrano nel progetto che lo step legge.
- Giro, su Modal e mai su questo PC: `modal deploy modal_stack.py`, poi `python modal_stack.py spawn [--fixtures a,b | --families js,py,jvm,sys,mix,real]` e `fetch`. Il container (1 CPU, 3 GB) scrive la snapshot, la pre-mappa e `technologies.ensure`; ogni fixture ha 900 secondi in un processo a parte (`bounded`): scaduti, il record dice `no answer in 900 s` e dove stava (faulthandler), e il resto del gruppo va avanti. `spawn` rifiuta il giro se i file caricati (`UPLOADED`, con i dati accanto agli script: D-287) non sono quelli di questa copia, e `fetch` confronta l'impronta del codice dei due lati.
- Pre-mappa: i comandi di modello non girano. Le loro risposte sono quelle registrate da `modal_premap.py --runs` (`results/premap-runs`), riprodotte come fa `tools/premap_replay.py`; una fixture senza registrazione ha i comandi `not_run` (`model: none`), una registrazione a cui manca una risposta è `partial`. Le registrazioni sono 178 su 180: mancano `real-stack-jellyfin` e `real-stack-kuvasz`, che hanno superato i 2.400 secondi della funzione di `modal_premap.py` (D-302). Le 18 `jvm-ver-*` e le 40 `real-stack-*` sono state registrate il 17 novembre 2026, sul codice `5bcc6674211c593c`.
- Punteggio: `score.technologies_faces` porta il record nelle facce `frameworks` (ogni voce la cui `category` non è `service`, per ogni unità che la tiene, con il primo segno dentro l'unità come prova) e `services` (ogni voce di `category` `service`) di `expected.json`; `score.score_technologies` le confronta. Dal 19 novembre 2026 ogni voce `project` riconoscibile ha la sua `category` (`framework`, `library`, `tool` o `service`), ma `expected.json` elenca fra i framework anche librerie e strumenti (Zod, Vite, Vitest, Jest) e non tutti: la faccia tiene le tre classi come prima, e ciò che offre in più di `expected.json` fra i framework non è un falso: è `counted_apart`. I servizi di `expected.json` sono completi, e un servizio in più resta `extra`. `frameworks_by_name` toglie le unità, che ogni lettore nomina a modo suo, e conta un nome una volta per fixture.
- Due fatti per fixture: `executed_project_code`, dai processi che `ensure` avvia (`spawned`: `no` solo se tutti sono il `git` del perimetro, con gli hook e il monitor spenti; la snapshot e la pre-mappa riprodotta non sono osservate), e `seconds` (snapshot con pre-mappa, e lo step). Il costo del giro viene dal rapporto di Modal.

### Replay del riconoscimento dei pacchetti PyPI

`replay_stack_packages.py` rilegge le risposte di Renovate conservate in `results/premap-runs`. Per ogni progetto applica il lettore della pre-mappa e misura `service_registry.check_packages` sulle coppie pacchetto PyPI/file. Il JSON di uscita contiene le triple tecnologia, pacchetto e file per fixture. I parametri sono la revisione Git, le fixture da escludere, il numero di ripetizioni del matcher e il file di uscita. Il replay legge dati archiviati senza avviare strumenti esterni di analisi o codice delle fixture.

Dal repository, con due percorsi di uscita a scelta:

```sh
python benchmarks/project-model/replay_stack_packages.py --revision 98f360b --exclude real-app-full-stack-fastapi --repeat 11 --out baseline.json
python benchmarks/project-model/replay_stack_packages.py --exclude real-app-full-stack-fastapi --repeat 11 --out candidate.json
```

Il 20 novembre 2026, escluso il template FastAPI usato per la correzione, 35 delle 177 registrazioni rimaste contenevano pacchetti PyPI rilevati da Renovate. Su 1.185 coppie pacchetto/file, la normalizzazione PyPI ha portato le triple da 177 a 178. È comparso solo `sentry / sentry-sdk / pyproject.toml` in `real-stack-netbox`, dove il riferimento atteso elenca Sentry. Tutte le triple precedenti sono rimaste. La mediana per analizzare i 35 casi in 11 ripetizioni è stata 210 ms per la base e 214 ms per la modifica. Il replay misura esclusivamente il matcher su questa fonte. L'attribuzione ai moduli, le configurazioni Compose e i tempi dell'intera pipeline richiedono prove distinte.

Per i servizi configurati, il rapporto del benchmark conserva `configured_services` accanto al punteggio dei servizi riconosciuti dal catalogo. Il controllo `test_compose_files_in_the_corpus_keep_each_service_name_even_if_built_without_an_image` in `test_stack.py` verifica i tre file Compose presenti direttamente nelle fixture. Il lettore recupera nove dichiarazioni su nove, comprese le tre che contengono una build senza immagine esplicita. Ogni dichiarazione conserva il punto nel file.

### Risultati

Dopo le categorie scritte delle 245 voci `project` che non ne avevano (19 novembre 2026, codice `c6be10745cedb94d` uguale ai due lati, registro di 2.345 voci), 178 fixture su 180 con record (jellyfin e kuvasz ancora `no answer in 900 s`, D-302), `executed_project_code: no` in 178:

| Faccia | js | py | jvm | sys | mix | real | stack | tutte |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Framework per nome, trovati / attesi | 10 / 10 | 4 / 4 | 36 / 42 | 2 / 2 | 29 / 31 | 99 / 127 | 182 / 352 | 362 / 568 |
| Framework per unità, trovati / attesi (sbagliati) | 11 / 11 | 4 / 4 | 37 / 43 | 1 / 2 (1) | 32 / 37 | 177 / 251 (12) | 290 / 653 (37) | 552 / 1.001 (50) |
| Servizi trovati / attesi (in più) | 1 / 1 | 2 / 3 | 1 / 2 | 0 / 0 | 11 / 33 (1) | 30 / 84 (9) | 96 / 395 (55) | 141 / 518 (65) |

- Framework per nome e per unità invariati: la faccia tiene ancora ogni classe che non è `service`.
- Servizi trovati da 137 a 141. Due vengono dalle categorie: MailHog in bookstack e Kafka in otel-demo, prima `counted_apart` fra i framework, ora voci di categoria `service`. Gli altri due (Pusher in koel, LiveKit in mattermost-mobile) e i tre in più (Jellyfin in jellyfin-ios, Chromatic in owncast, LangChain Corporate in otel-demo) vengono da voci `service` aggiunte al registro dopo il giro del 17 novembre (`from`: `additions`, `simple-icons`).

Dopo la pulizia dello stack (`136cd87ca`: tre controlli, e un segno solo da una variabile d'ambiente resta `mentioned`), 17 novembre 2026, codice `d96bc1ec3246636d`, 178 fixture su 180 con record:

| Faccia | js | py | jvm | sys | mix | real | stack | tutte |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Framework per nome, trovati / attesi | 10 / 10 | 4 / 4 | 36 / 42 | 2 / 2 | 29 / 31 | 99 / 127 | 182 / 352 | 362 / 568 |
| Framework per unità, trovati / attesi (sbagliati) | 11 / 11 | 4 / 4 | 37 / 43 | 1 / 2 (1) | 32 / 37 | 177 / 251 (12) | 290 / 653 (37) | 552 / 1.001 (50) |
| Servizi trovati / attesi (in più) | 1 / 1 | 2 / 3 | 1 / 2 | 0 / 0 | 11 / 33 (1) | 29 / 84 (8) | 93 / 395 (53) | 137 / 518 (62) |

- Servizi in più da 77 a 62 (via Discord, Segment, Facebook e altri da un prefisso o da un identificatore), ma trovati da 159 a 137: 22 servizi veri avevano come solo prova una variabile d'ambiente e ora sono `mentioned` (PostgreSQL in atuin, fiber-go-template e quarkus-super-heroes, Sentry in fastapi, epic-stack e netbox, Redis in mix-infra-k8s-helm e lobsters, Slack, Discord, Telegram e Twilio in healthchecks). OpenTelemetry di eShop non è più un framework per nome. È D-304.

Dopo D-303 (`819964b55`: lo stack nomina le unità come la pre-mappa e dà un pacchetto di catalogo allo script che lo usa), 17 novembre 2026, 178 fixture su 180 con record:

| Faccia | js | py | jvm | sys | mix | real | stack | tutte |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Framework per nome, trovati / attesi | 10 / 10 | 4 / 4 | 36 / 42 | 2 / 2 | 29 / 31 | 100 / 127 | 182 / 352 | 363 / 568 |
| Framework per unità, trovati / attesi (sbagliati) | 11 / 11 | 4 / 4 | 37 / 43 | 1 / 2 (1) | 32 / 37 | 178 / 251 (12) | 290 / 653 (37) | 553 / 1.001 (50) |
| Servizi trovati / attesi (in più) | 1 / 1 | 2 / 3 | 1 / 2 | 0 / 0 | 15 / 33 (2) | 33 / 84 (8) | 107 / 395 (67) | 159 / 518 (77) |

- Per unità da 364 a 553 su 1.001, gli sbagliati da 208 a 50; JVM da 2 a 37 su 43. Per nome e servizi invariati.

Dopo la mappa dei moduli e lo stack ([pipeline di analisi](../../docs/specs/2026-11-15-pipeline-di-analisi.md), sezione 1; `3b961646a`, `1a33518f4`), 17 novembre 2026, codice `107d16779072c4cd` uguale ai due lati, 178 fixture su 180 con record (jellyfin e kuvasz ancora no, D-302):

| Faccia | js | py | jvm | sys | mix | real | stack | tutte |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fixture con record | 20 | 21 | 34 | 25 | 30 | 10 | 38 | 178 |
| Framework per nome, trovati / attesi | 10 / 10 | 4 / 4 | 36 / 42 | 2 / 2 | 29 / 31 | 100 / 127 | 182 / 352 | 363 / 568 |
| Framework per unità, trovati / attesi (sbagliati) | 11 / 11 | 4 / 4 | 2 / 43 (35) | 2 / 2 | 24 / 37 (8) | 95 / 251 (77) | 226 / 653 (88) | 364 / 1.001 (208) |
| Servizi trovati / attesi (in più) | 1 / 1 | 2 / 3 | 1 / 2 | 0 / 0 | 15 / 33 (2) | 33 / 84 (8) | 107 / 395 (67) | 159 / 518 (77) |

- Framework per nome da 211 a 363 su 568: JVM da 0 a 36 su 42, i repository veri da 42 a 100 su 127, le `real-stack-*` da 135 a 182 su 352. Servizi da 148 a 159 su 518, con 77 in più invece di 100.
- Per unità i framework trovati salgono da 268 a 364, ma gli sbagliati da 35 a 208: la tecnologia è giusta e l'unità no (JVM 2 su 43 con 35 sbagliati). Di 208: 76 sono lo stesso modulo con un altro nome (`:app` atteso, `app` dato), 15 attendono la radice `:` e ricevono il nome del progetto, 117 vanno a un'altra unità, spesso la radice o il padre al posto del sottomodulo (kotlinconf `:backend` dato a `kotlinconfapp`, mealie `frontend` dato a `mealie`). È D-303.

Prima della mappa dei moduli, 17 novembre 2026. 178 fixture su 180 con record; `real-stack-jellyfin` e `real-stack-kuvasz` no (D-302). `results/daodan_stack.json` tiene, per fixture, le facce, il punteggio, gli id delle tecnologie, i secondi e i processi avviati. I record vengono da tre versioni del driver (`2dafe3d6678aa4c6`, `63a0f46b0eacc825`, `8720a450c5b16739`, elencate in `code.container`; `code.local` è la terza, quella di questa copia): cambiano solo il tempo per fixture e il testo dell'errore, non la misura.

| Faccia | js | py | jvm | sys | mix | real | stack | tutte |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fixture con record | 20 | 21 | 34 | 25 | 30 | 10 | 38 | 178 |
| Framework per nome, trovati / attesi | 10 / 10 | 4 / 4 | 0 / 42 | 1 / 2 | 19 / 31 | 42 / 127 | 135 / 352 | 211 / 568 |
| Framework per unità, trovati / attesi (sbagliati) | 10 / 11 (1) | 4 / 4 | 0 / 43 | 1 / 2 | 18 / 37 (2) | 46 / 251 (8) | 189 / 653 (24) | 268 / 1.001 (35) |
| Servizi trovati / attesi (in più) | 1 / 1 | 2 / 3 | 1 / 2 | 0 / 0 | 14 / 33 (9) | 26 / 84 (15) | 104 / 395 (76) | 148 / 518 (100) |

- Il codice del progetto non gira, ma questo giro lo mostra poco: con la pre-mappa già scritta `ensure` non avvia nessun processo (`spawned` vuoto in 178 fixture su 178), e la snapshot e la riproduzione della pre-mappa non sono osservate. Nel primo giro del 17 novembre, in cui `ensure` scriveva la pre-mappa, le 140 fixture avevano solo `git check-ignore` e `git ls-files` del perimetro.
- Lo step `technologies.ensure` impiega, con la pre-mappa già scritta, 0,03 s di mediana e 5,72 s al massimo (`real-stack-owncast`); la snapshot con la pre-mappa 354 s su owncast e 333 su kotlinconf.
- I servizi sono quelli di `daodan_registry` (45 su 123 il 14 novembre; qui 44 sulle stesse 123): lo step li prende dal registro e non ne aggiunge. Sulle 40 `real-stack-*` 104 su 395, con 76 in più.
- Fuori da JVM e .NET, js e py non perdono nessun framework per nome; le `real-stack-*` perdono 217 framework su 352, 181 di una voce che il registro non ha.
- 62 fixture su 178 hanno `technologies` vuote e 18 non hanno nessuna unità di build.
- Le cause sono le schede D-294 (Maven, NuGet, Pub, Hex e Swift non letti: JVM 0 su 42), D-295 (il `kind` `service` fa servizi dei framework e delle librerie: Playwright, Firebase, OpenTelemetry, Cypress, Celery, Puppeteer), D-296 (prefissi di variabile, di identificatore e di pacchetto: Zoom, Ghost, Segment, GCP, Postman), D-297 (CI, strumenti ed esempi sotto `docs/` come servizi: Renovate, Crowdin, Codecov, Railway), D-298 (servizi senza voce o senza segno), D-299 (framework senza voce o senza segno nel manifest), D-300 (un segno nomina solo il pacchetto della voce, non i suoi componenti), D-301 (un file di requisiti con un altro nome) e D-302 (la snapshot di jellyfin e kuvasz non finisce). «Tailwind» e «Tailwind CSS» si contano come lo stesso framework dal commit `b2f431eb4`.

## Lo step `stack` dal fork

Misura che cosa cambia sul corpus se lo step `stack` riconosce le tecnologie con stack-analyser (il rilascio `1.27.6-daodan.2` del fork `acaprino/stack-analyser`) al posto del registro (`service_registry.run`): nomi attesi persi e guadagnati, servizi in più, tempo della scansione veloce. Il prodotto non cambia: `technologies.derive` chiama ancora il registro ([spec](../../docs/specs/2026-11-21-stack-dal-fork.md), «Verifica»).

### Parametri

- Corpus: le 180 fixture con `expected.json`. Giro, su Modal e mai su questo PC: `modal deploy benchmarks/project-model/modal_stack_fork.py`, poi `python benchmarks/project-model/modal_stack_fork.py spawn [--fixtures a,b | --families js,py,jvm,sys,mix,real]` e `fetch`, che scrive `results/daodan_stack_fork.json` e confronta l'impronta del codice dei due lati. Container Linux di 1 CPU e 4 GB, 1.800 secondi per fixture.
- Strumento: stack-analyser `1.27.6-daodan.2`, sha256 `57dfe8d1b2e37ecb95c331b3f74c8c2aecead59a4ef95835c71a02d5397a9774`, sul Node v22.23.4 che il prodotto avvia (`indexers.runtime.NODE_VERSION`). Prima di ogni gruppo gira una volta su una cartella vuota, fuori da ogni tempo, per l'avvio a freddo di Node.
- Prova di non esecuzione: `tests/test_codebase_map_host_programs.py` (solo su Modal), rifatta per `.2` il 22 novembre 2026 con `python tests/modal_pytest.py tests/test_codebase_map_host_programs.py tests/test_codebase_map_stack_analyser.py -q -rw`: 32 test passati, nessuno saltato; il rapporto nei warning dice che `node-options` e `planted-node` scattano se il rilascio parte alla maniera ingenua e che gli altri quattro vettori il rilascio non li esegue. Che cosa non copre: «Non misurato».
- `executed_project_code`: `no` se ogni processo che il Python di Daodan ha avviato nella misura è `git` (il perimetro) o Node sul `cli.mjs` del rilascio; che cosa Node stesso avvii non è osservato qui, lo copre la prova su Modal.
- «Prima» e «dopo»: per fixture, la snapshot e la pre-mappa con le risposte registrate dei comandi di modello (`results/premap-runs`: lo stesso ingresso ai due lati); poi `technologies.derive` con `service_registry.run` («prima») e con `fork_stack.recognize` («dopo»), dopo un `derive` di riscaldamento che fa il grafo dei moduli. Nel «dopo» i fatti della pre-mappa vanno al rilascio come dichiarazioni, con le cartelle che la pre-mappa esclude, e le sue prove tornano come voci del registro: la prova di una dichiarazione resta qualunque sia il suo file (come per il registro), quella che il rilascio legge da solo solo per un file della snapshot; gli host negli URL restano di `registry_hosts`.
- Perso, guadagnato: un nome di `expected.json` (come lo conta `score.score_technologies`, per nome e non per unità) che c'è solo prima, o solo dopo. `new`, `gone`: id di `technologies` solo dopo, solo prima. `not_in_registry`: id del fork che il registro non ha. Servizi in più: servizi riconosciuti che `expected.json`, completo per i servizi, non elenca (`extra` del punteggio).
- Scansione veloce: la pre-mappa senza comandi di modello (`premap.derive(runner=None)`), con ogni riconoscitore da solo; si confrontano gli id con un segno `declared` (`fast.lost`: del registro, non del fork). Ogni tempo è di una chiamata (`time.monotonic()`), una misura per fixture, senza ripetizioni; `fork_fast` comprende l'avvio di Node.
- La traduzione e le misure sono in `tools/fork_stack.py`, provate da `test_fork_stack.py` senza Node. `accepted-losses.json` ha una riga `{fixture, name, id, reason, verdict}` per ogni nome perso (`accepted`: il registro sbagliava, o lo hanno deciso la spec o la porta del registro nel fork, `benchmarks/registry-port.json` del fork; `to_fix`: da cambiare, con dove); due test lo tengono uguale a `lost` e dicono che nessuna fixture ha eseguito il codice del progetto.

### Risultati

Secondo giro, 22 novembre 2026, codice `9be947a3bbf0c61d` uguale ai due lati, 180 fixture, 178 con record (le altre due: «Senza risposta»); `executed_project_code: no` in 178, `fork_failed` in 0. `model: partial` in 178: alle registrazioni mancano da 1 a 41 comandi per fixture, ai due lati allo stesso modo.

| Faccia | Attesi | Prima | Dopo |
| --- | --- | --- | --- |
| Framework per nome, trovati | 569 | 531 | 533 |
| Framework per unità, trovati (sbagliati) | 1.001 | 834 (70) | 838 (69) |
| Servizi, trovati | 518 | 227 | 228 |
| Servizi in più | | 67 | 86 |

I «prima» non sono quelli della sezione sopra (362 / 568 e 141 / 518): il codice è un altro (`c6be10745cedb94d`) e questo giro non lo spiega.

Servizi in più: da 67 a 86 (in 32 e poi in 36 fixture). Il fork ne aggiunge 22 (`azure` 6, `aws` 4, `google` 3, `gcp` 3, `firebase` 2, e uno ciascuno `microsoft`, `cloudflare`, `vercel`, `apple`) e ne toglie 3 (`okta`, `gcp`, `kafka`). Le 22 sono gli id di `new` che il punteggio conta come servizi; nessuna è un nome atteso.

Nomi persi: 0 (`fixtures_with_lost`), quindi `accepted-losses.json` è `[]`. Guadagnati: 3, Meilisearch in `real-stack-koel` (`meilisearch/meilisearch-php`, `composer.json` riga 30: la regola del fork lo elenca, nel registro il pacchetto ha uno spazio in fondo e non combacia mai), Maestro in `real-stack-mattermost-mobile` (i file di flusso in `detox/maestro`, letti dal fork; id non nel registro) e WinUI in `real-stack-peopleinspace` (`UseWinUI` in un `.csproj`, letto dal fork; id non nel registro).

**Primo giro**, 21 novembre 2026, rilascio `.1`, codice `b3719332398056ec` (commit `a2613d8`): 5 nomi persi in 5 fixture (framework 531 → 530, servizi 227 → 226) e 33 coppie di id spariti. Lo zero del secondo viene dopo due correzioni:

- Spring MVC (`jvm-spring-boot-managed`, `real-stack-mall`, `real-svc-robot-shop`): `org.springframework.boot:spring-boot-starter-web` andava solo a Spring Boot (differenza registrata della porta); il proprietario ha deciso di correggerlo nel fork, e `.2` lo dà a Spring Boot e a Spring MVC (`src/rules/framework/spring-mvc.ts`).
- GitHub Pages (`real-app-kotlinconf`) e Gotenberg (`real-stack-documenso`): la traduzione scartava la prova di un file fuori dalla snapshot (`.github/workflows/web-deploy.yml`, `docker/development/Dockerfile.gotenberg`). Corretto in `tools/fork_stack.py` (`22e9b03`), che ha tolto anche altre 22 coppie dagli id spariti (da 33 a 6 con il rilascio): non lette una per una, causa verificata solo per `github.pages` in `real-stack-peopleinspace`.

Id spariti (`gone`): 6 coppie id/fixture in 6 fixture, su 4 id, nessuno un nome atteso; `fast.lost` ha 7 coppie su 5 id (gli stessi quattro e `github.pages`).

- `react-email` (3: `real-app-full-stack-fastapi`, `real-stack-documenso`, `real-stack-epic-stack`; anche nella veloce): il registro ha due id, `react-email` e `reactemail`; il fork uno, `reactemail` (`src/rules/tool/reactEmail.ts`), e la porta rinomina `react-email` in `reactemail`. Tutti i segni tornano sotto `reactemail`, nuovo solo in epic-stack, dove l'unico pacchetto, `@react-email/components`, nel registro era solo di `react-email`.
- `kafka` (1: `real-svc-otel-demo`; anche nella veloce): rinomino della porta in `apache_kafka`, che c'era già prima e la cui regola elenca i tre pacchetti di `kafka` (`src/rules/queue/apacheKafka.ts`); dopo, `apache_kafka` ha tutti i segni per valore e percorso, e il segno di `kafka-clients` che dà il rilascio non ha riga.
- `okta` (1: `real-stack-bookstack`; anche nella veloce): `socialiteproviders/okta` (`composer.json` riga 39) andava a `okta` e a `okta.oauth`; il fork lo dà a `okta.oauth` soltanto, differenza registrata della porta. Il pacchetto resta riconosciuto, e `expected.json` elenca «Okta OAuth». I cinque `OKTA_*` del «prima»: «Menzioni `env`».
- `gcp` (1: `real-stack-nestjs-boilerplate`; anche nella veloce): `google-auth-library` (`package.json` riga 77) andava a `gcp`, ora va a `google` (`src/rules/cloud/google.ts`): differenza registrata della porta. Il pacchetto resta riconosciuto.
- `github.pages` (1: `mix-real-tinyxml2`, solo nella veloce; nella completa nessuno dei due lati lo ha): per esclusione il segno è `docs/_config.yml` (il solo `_config` registrato, nessuna azione di Pages nei workflow). Nella completa go-enry lo marca documentazione e finisce fra gli esclusi, per i due lati (`premap/enry.py`); nella veloce enry non gira e il registro lo prende per `github.pages`, mentre la porta ha tolto `_config.yml` e `_config.yaml` dalla voce (configurazione di Jekyll, non prova di hosting). È l'unico degli id spariti il cui segno dichiarato non passa a un altro id; se valga come prova di Pages, i dati non lo dicono.

Menzioni `env`: il percorso tradotto non produce segni `env`. Nei 10 record letti (sul volume, ridotti a otto segni per voce) il «prima» ha segni `env` in 8 record, da 8 a 20 ciascuno (al minimo), il «dopo» 0 in tutti; per i cinque `OKTA_*` di `real-stack-bookstack` (`app/Config/services.php`, righe 82-88) il record «dopo» non ha né l'id `okta` né un segno `env`. Una menzione senza segno dichiarato non è misurabile: `derive` non porta in `technologies` una voce di sole menzioni. Il percorso tradotto ha i controlli `stack-analyser` e `host`, senza `check_env`; il rilascio legge le variabili solo nei modelli `.env*.example`, `.sample`, `.template` (`src/rules/spec/dotenv/index.ts`), file che la politica di Daodan non legge mai (`source_files.FORBIDDEN_GLOBS`, `.env.*`): li apre comunque e ne scarta la prova fra le `evidence_outside_snapshot`. Conseguenza: un token come `OKTA_CLIENT_ID` in un sorgente è una menzione per il registro (`check_env`) e non è letto dal percorso tradotto; la spec tiene gli host negli URL a `registry_hosts.py` (2.4), toglie `check_env` (2.6) e mette fuori scopo il riconoscere servizi dall'uso nel codice.

Limite trovato, non corretto: `stack_analyser.py` passa `--skip-dirs` e `--ignore` sulla riga di comando, e `fork_stack.perimeter` mette in `ignore` ogni percorso che la pre-mappa esclude, nella completa anche ogni file che go-enry chiama documentazione, binario, generato o vendored. Dalle risposte registrate di go-enry, `real-stack-owncast` ha 760 percorsi esclusi (535 generati, 192 binari, 21 documentazione, 12 vendored) e un `--ignore` di almeno 36.678 caratteri; la seconda fixture, `real-stack-quarkus-super-heroes`, 19.287. Il limite di `CreateProcess` su Windows è 32.767 caratteri per la riga intera: lì la scansione di owncast finirebbe come gap «could not start», senza riconoscimento; su Linux il limite per argomento è più alto, e il giro (`fork_failed` 0) non l'ha incontrato. Nelle 178 fixture `fork_full − fork_fast` cresce con la lunghezza di quella lista (correlazione 0,87; 0,85 con il numero dei percorsi; owncast 13,4 s, il registro 0,7 s): la causa non è stabilita, perché il numero delle dichiarazioni varia con essa e il file dei risultati non lo registra. Il filtro della traduzione scarta già le prove sotto un percorso escluso, quindi le voci di file in `ignore` sono ridondanti; che cosa farne è del piano successivo.

Id nuovi (`new`, con i tre guadagnati): 148 coppie in 106 fixture, 30 id, per fixture in `compare.new`; oltre ai servizi in più, `gradle` 26, `maven` 23, `cargo` 17. Rispetto al primo giro compaiono `pnpm` (7), `bunsh`, `nodejs` e un `azure` in più, dalle dichiarazioni che ora restano. Fuori dal registro (`not_in_registry`), in quante fixture: `gradle` 26, `setuptools` 9, `rich` 4, `maestro` 1, `winui` 1, col proprio id per nome e categoria `framework` (`entry_category`).

Gap del fork:

- `declaration_not_sent`: una dichiarazione che la traduzione non manda al rilascio (nessun file, percorso escluso dalla pre-mappa o fuori dal progetto, tipo che il rilascio non prende, nessun nome o fonte). In questo giro 213, tutte nella completa e in 9 fixture; secondo i record del primo giro sul volume la sola causa è il percorso escluso dalla pre-mappa (nuget 141, crates 23, pypi 12, docker 12, github-actions 9, npm 8, maven 7, go 1), e il registro scarta le stesse dichiarazioni senza registrare un gap (`service_registry.run`, `_is_excluded`, riga 241; `tools/fork_stack.py`, riga 98).
- `evidence_outside_snapshot`: in 69 fixture nella completa, 71 nella veloce. Prove che il rilascio legge da solo in file che Daodan non mette nella snapshot (`.dockerignore`, `.env.example`, `artisan`, `bun.lock`, la cartella `.github`; conto e primi cinque percorsi, da 1 a 21 nei 10 record letti), non tecnologie perse. Per i segni di file il registro quei file non li vede nemmeno (`check_files` legge i file della snapshot); le dichiarazioni su un percorso fuori dalla snapshot il registro le tiene, e dopo la correzione anche la traduzione.
- `not_in_registry`: 41 gap in 37 fixture, per scansione, uno per id fuori dal registro.

Tempi in secondi, sulle 178 fixture con record (completa: mediana 0,029 e massimo 5,277 `real-stack-netbox` per il registro, 0,548 e 16,736 `real-stack-owncast` per il fork):

| Scansione veloce | Mediana | Massimo | Più lente |
| --- | --- | --- | --- |
| Registro (`registry_fast`) | 0,013 | 4,972 | `real-stack-netbox` 4,972, `real-stack-plausible` 4,568, `real-stack-owncast` 4,542 |
| Fork (`fork_fast`) | 0,523 | 5,791 | `mix-real-tududi` 5,791, `real-stack-plausible` 5,611, `real-stack-actual` 4,742 |

- `fork_fast`: minimo 0,302 (registro 0,008); 149 fixture su 178 sotto 1 s, 29 da 1 s in su, 16 da 2 s, 10 da 3 s, 6 da 4 s, 2 da 5 s; `py-fastapi-compose`, il progetto di prova della spec, 0,331 (registro 0,011); mediana di `fork_fast` meno `registry_fast`, per fixture, 0,472. In `mix-real-tududi` il registro impiega 3,770.
- Nel primo giro, con lo stesso registro, `registry_fast` aveva mediana 0,013 e massimo 4,544, e `fork_fast` mediana 0,456 e massimo 4,982: fra due giri lo stesso codice si muove, e i tempi del fork si leggono con quella variazione.
- Senza risposta: `real-stack-jellyfin` e `real-stack-kuvasz`, `no answer in 1800 s`; il record dice dove stavano (`snapshot_store._unpack`, da `import_resolution.declaring`). Sono le stesse due senza record nel giro sopra e in `modal_premap.py` (D-302).

### Non misurato

- Windows: il giro è su container Linux; l'avvio di Node e la scansione veloce sulla macchina dell'utente non sono misurati, e un `node.bat` piantato o `.` nel `PATH` non sono provati con una esecuzione vera, solo dai test puri delle condizioni di avvio (percorso assoluto del programma, directory di lavoro propria).
- L'installazione del prodotto: la prova su Modal e il driver (`_image_tool`) sostituiscono `stack_analyser.cli` e `stack_analyser.node`, quindi `cli()` (`engine_tools.download`, `unpack`, `publish` sull'archivio vero) e `indexers.runtime.node()` non hanno mai girato con i file veri (i loro test usano un piccolo archivio locale e un sostituto). La prova gira sul Node dell'immagine di test (v24.22.3, `tests/modal_pytest.py`); il prodotto avvia v22.23.4.
- La prima esecuzione su una macchina con la cache di compilazione di Node fredda: è fuori da ogni tempo per costruzione.
- Le due fixture senza risposta (178 su 180); la variazione fra due giri; il tempo sotto `project_lock` e con il resto del server in funzione.
- Di quali tecnologie siano le prove scartate da `evidence_outside_snapshot` e quante menzioni `env` si perdono: `compare` conta id e nomi, non segni.
- I record completi di ogni fixture (`before`, `after`, `fast`, gap con i percorsi, processi avviati) stanno sul volume Modal, `project-model/stack-fork/<fixture>.json`; il file committato ha differenze, punteggi e tempi.

### Verdetto

- «Nessuna perdita»: passa sulle 178 fixture misurate (nessun nome atteso perso, nessuna riga `to_fix`, `accepted-losses.json` vuoto) e non è verificata sulle 2 senza risposta. Viene dopo la correzione della traduzione e la nuova regola del fork (Primo giro). `compare` conta id e nomi: delle 6 coppie sparite (4 id), tutte passano a un altro id con il loro segno dichiarato; nella sola veloce, `github.pages` in `mix-real-tinyxml2` non passa a nessun id, per una scelta registrata della porta. Le menzioni `env` non passano: il percorso tradotto non ne produce, ed è un secondo riconoscimento che il registro ha e il percorso non ha.
- Scansione veloce, su Linux, contro l'obiettivo della spec (meno di un secondo dall'avvio al risultato su `py-fastapi-compose`; circa un secondo a ogni modifica sotto `project_lock`): `py-fastapi-compose` 0,331 s, mediana 0,523 s, 29 fixture su 178 da 1 s in su, massimo 5,791 s. La soglia è del proprietario; se l'obiettivo non è raggiunto, la spec ferma il lavoro al passo 3.
- Tornano al proprietario: i tempi; i servizi in più (da 67 a 86: 22 aggiunti, 3 tolti); le tre differenze della porta che spostano un id senza cambiare nessun nome atteso (`okta`, `gcp`, `_config.yml` di Jekyll); le menzioni `env` e i modelli `.env` che il rilascio apre benché la politica di Daodan non li legga; il `--ignore` oltre i 32.767 caratteri su Windows (`real-stack-owncast`); ciò che «Non misurato» non copre.

## Esplorazione dell'app avviata

Passo 11 del [piano degli ingressi](../../docs/plans/2026-11-20-ingressi-e-flussi.md): Daodan avvia l'app dichiarata nel container, apre un browser senza interfaccia, legge i controlli di ogni pagina dall'albero di accessibilità di Playwright, ne preme ognuno una volta e registra le funzioni del progetto che partono (copertura V8 fra due letture, meno ciò che la pagina ferma esegue da sola).

### Parametri

- Script: `modal_explore.py` (`python -m modal run benchmarks/project-model/modal_explore.py::explore_main --source <cartella del volume | folder> --analysis <cartella del volume> --out <file>`). `--source folder` prende la cartella di `DAODAN_FOLDER`; l'analisi di confronto è una cartella del volume `daodan-flow-results` (`manifest.sqlite`, `engine-edges.sqlite` e i file accanto).
- Sorgenti: `premap/npm_start.py` (`starts`, `builds`), `dynamic/app.py` e `app.cjs` (avvio, porta, arresto), `dynamic/explore.cjs` (esplorazione), `observed_entries.py` (candidati con fonte `observed`).
- Tetti di `explore.cjs`: 25 pagine, 300 pressioni, 900 s, 3 s per il click, 3 livelli di profondità. I controlli che un click rivela (un menu, una finestra) hanno un budget a parte di 100 pressioni e al più 30 per click, e non si cercano dopo un collegamento: un collegamento naviga o scorre, non apre. Ogni controllo si preme dopo aver ricaricato la pagina in un contesto pulito e dopo i click che lo mostrano; la lettura dei controlli aspetta che l'elenco resti fermo per un secondo (fino a 3 s).
- Un controllo è un candidato `observed` se la pressione ha fatto partire una funzione del progetto o ha inviato una richiesta, e nessun candidato statico ha la stessa etichetta e lo stesso evento.
- Non misura nessun flusso: il confronto con i flussi del riferimento non è stato fatto.

### Risultati

Su phazly, 22 novembre 2026, file `results/explore/phazly-full-src.json`; la corsa sulla sorgente incompleta del volume è `results/explore/phazly-volume-src.json` (sorgente: una copia ridotta del progetto vero, senza `node_modules`, `target` e senza alcun file `.env*` o chiave; analisi di confronto `possible-in/phazly5`, 194 candidati statici):

| App | Avvio | Pagine | Controlli | Premuti | Saltati | Falliti |
|---|---|---|---|---|---|---|
| `landing-app` | `npm run dev`, porta 5173 stampata | 8 | 140 | 118 | 19 | 3 |
| `admin-app` | parte, porta 5174 | 1 | 3 | 1 | 2 | 0 |
| `react-app` | parte, porta 5173 | 1 | 14 | 10 | 4 | 0 |

Totale: 10 pagine, 157 controlli (76 rivelati da un click), 129 premuti, 126 con una funzione del progetto partita o una richiesta inviata, 97 con il gestore isolato. Saltati: 16 collegamenti fuori dall'app, 8 campi che chiedono un valore, 1 controllo non operabile. Nessun tetto raggiunto. Falliti 3, nella `landing-app`: «Skip to main content», un collegamento fuori dal viewport finché non prende il fuoco, e «Cookie preferences», coperto dal banner dei cookie fisso in basso (la ragione registrata nomina l'elemento che intercetta il click).

- Valori di prova: le variabili dei file `.env.example` (e `.env.local.sample`) che Git traccia nella cartella dell'app passano all'app come ambiente (`dotenv_env` con `("*", file)`, `container.exported`): sono ciò che il progetto pubblica, segnaposto e non segreti. Senza, `admin-app` e `react-app` mostravano una pagina vuota («Missing required Firebase configuration», lacuna `page_without_controls`); con i valori mostrano la schermata di accesso: 3 controlli in `admin-app` (2 campi che chiedono un valore, 1 premuto, nessuna funzione partita) e 6 in `react-app` (2 campi e 4 premuti: «Log in», «Continue with Google», «Forgot password?», «Sign up»). Non si entra nell'app: manca una credenziale di prova.
- Ogni pressione parte da un contesto di browser pulito (una prima visita): con lo stato condiviso, i 4 controlli di `react-app` risultavano «non ritrovati» dopo il ricaricamento, e i controlli premuti erano 40 invece di 59. La lettura dei controlli aspetta fino a 3 s che l'app li disegni.
- La corsa è un checkout emulato: lo script fa `git init` e commit della cartella caricata, perché l'upload perde `.git` e solo i file tracciati sono quelli che il progetto pubblica.
- Candidati `observed`: 126, della `landing-app` e di `react-app` (il `matched` per etichetta è 0). I candidati statici di phazly5 non hanno etichetta con evento `click` (0 su 194): quindi la corrispondenza per nome non ne trova nessuno (`matched` 0) e i 126 sono tutti «recuperati» rispetto a quel confronto, che è debole. Gli eventi scartati su un componente sono 0 in quell'analisi: la domanda «quanti ne recupera» non ha un denominatore e non si risponde qui.
- Il gestore di un click è la prima funzione del progetto che l'evento raggiunge: punto di interruzione ufficiale di Chrome sul `click` (`DOMDebugger.setEventListenerBreakpoint`) con le dipendenze e gli script del server di sviluppo in blackbox (`Debugger.setBlackboxPatterns`); l'indirizzo dello script viene da `Debugger.scriptParsed`, perché `callFrames[0].url` è vuoto. Su phazly: 97 dei 126 controlli con effetto hanno il gestore (per esempio i pulsanti lingua e tema, `Nav.tsx` riga 125 e 135, con file e riga dalla mappa dei sorgenti). I 29 senza gestore sono per lo più collegamenti a un'ancora della stessa pagina (`#features`): non hanno un gestore di click, e le «funzioni partite» dopo la pressione sono lo scorrimento e i ridisegni. Resta una lista di funzioni partite (`observed_calls`) che include i ridisegni di React dopo il cambio di stato; la catena sotto il gestore non è registrata.
- Controlli rivelati: dopo una pressione (senza navigazione, e non su un collegamento) la pagina si rilegge e i controlli nuovi si premono dopo il click che li mostra; ogni voce porta `opened_by`, i nomi dei click che la mostrano. Una prima versione confrontava con una lettura presa troppo presto e contava 947 «rivelati» sulla `landing-app`, esaurendo le 300 pressioni su 3 pagine: ora il confronto parte da una lettura ferma, e il test del rendering a scatti lo prova (Modal). Su phazly i rivelati sono 76; il file dei risultati non ne conserva i nomi, quindi non ho verificato di che tipo siano (menu, finestre o altro).
- Lacuna `calls_unmapped`: 13 script dell'app (per lo più pacchetti già compilati dal server di sviluppo) girano senza mappa dei sorgenti.

### Non misurato

- Un progetto con un backend raggiungibile: l'esecuzione non ha rete, e `react-app` e `admin-app` mostrano solo la schermata di accesso, senza credenziali di prova per entrare.
- Il motore di Daodan su Windows (Kiri in WSL, `container.own_engine`): la prova col motore vero sotto è su Linux con Docker.
- I flussi del riferimento e il loro numero chiuso: nessuna misura.
- pnpm, Yarn e Bun: `start_runner_not_supported`, non eseguiti.
- La sorgente `phazly3-src` sul volume è incompleta (mancano `react-app/src/data` e `landing-app/src/assets/lp`): le app non si compilano, e la corsa su quella sorgente dà solo pagine di errore del bundler. Il risultato sopra usa la copia ridotta del progetto vero.

### Col motore container vero

`modal_engine.py` avvia un demone Docker (rete normale) in una VM Sandbox di Modal e lancia `dynamic.app.observe` con `container.find_engine()`, cioè `container.run_in_container` di Daodan e non il sostituto `sandbox_run` di Modal: preparazione con i registri, `keep_root` per il browser, esecuzione senza rete, uscite riportate. Fixture: `explore-fixtures/vite-react` (la stessa del test). Risultato, `results/explore/engine.json`: motore `docker`, app `ready` su 5173, 2 controlli premuti, nessuna lacuna, 42,6 s; Save → `validate` e `save`, Reset → `reset`, con file e riga di `src/lib/actions.ts`.
