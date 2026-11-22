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

Misura che cosa cambia sul corpus se lo step `stack` riconosce le tecnologie con stack-analyser (il rilascio `1.27.6-daodan.2` del fork `acaprino/stack-analyser`) al posto del registro (`service_registry.run`): i nomi attesi persi e guadagnati, e il tempo della scansione veloce. Il prodotto non cambia: `technologies.derive` chiama ancora il registro, e il confronto vive qui ([spec](../../docs/specs/2026-11-21-stack-dal-fork.md), «Verifica»).

### Parametri

- Corpus: le 180 fixture con `expected.json`, come nel giro sopra.
- Giro, su Modal e mai su questo PC: `modal deploy benchmarks/project-model/modal_stack_fork.py`, poi `python benchmarks/project-model/modal_stack_fork.py spawn [--fixtures a,b | --families js,py,jvm,sys,mix,real]` e `fetch`, che scrive `results/daodan_stack_fork.json` e confronta l'impronta del codice dei due lati. Container Linux di 1 CPU e 4 GB; ogni fixture ha 1.800 secondi in un processo a parte, scaduti i quali il record dice `no answer in 1800 s`.
- Strumento: stack-analyser `1.27.6-daodan.2`, sha256 `57dfe8d1b2e37ecb95c331b3f74c8c2aecead59a4ef95835c71a02d5397a9774`, sul Node v22.23.4 che il prodotto avvia (`indexers.runtime.NODE_VERSION`), scaricati e verificati come fa `tests/modal_pytest.py`. Prima di ogni gruppo gira una volta su una cartella vuota, fuori da ogni tempo, per l'avvio a freddo di Node. La prova che il rilascio non esegue il codice del progetto (`tests/test_codebase_map_host_programs.py`, che gira solo su Modal) è rifatta per `.2` il 22 novembre 2026 con `python tests/modal_pytest.py tests/test_codebase_map_host_programs.py tests/test_codebase_map_stack_analyser.py -q -rw`: 32 test passati, nessuno saltato; il rapporto nei warning dice che `node-options` e `planted-node` scattano se il rilascio parte alla maniera ingenua e che gli altri quattro vettori il rilascio non li esegue.
- «Prima» e «dopo»: per fixture, la snapshot e la pre-mappa con le risposte registrate dei comandi di modello (`results/premap-runs`, come nel giro sopra: lo stesso ingresso ai due lati). Un primo `technologies.derive` con il registro, non misurato, fa il grafo dei moduli; poi `derive` con `service_registry.run` («prima») e con `fork_stack.recognize` («dopo»), ognuno misurato. Nel «dopo» i fatti della pre-mappa vanno al rilascio come dichiarazioni, con le cartelle che la pre-mappa esclude, e le sue prove tornano come voci del registro; la prova che viene da una dichiarazione resta qualunque sia il suo file (come il registro tiene un pacchetto dichiarato), quella che il rilascio legge da solo resta solo per un file della snapshot; gli host negli URL restano di `registry_hosts`.
- Perso e guadagnato: un nome di `expected.json`, contato come fa `score.score_technologies` per nome e non per unità, che c'è solo prima o solo dopo. `new` e `gone`: gli id di `technologies` che ci sono solo dopo o solo prima. `not_in_registry`: gli id del fork che il registro non ha.
- Scansione veloce: la pre-mappa senza comandi di modello (`premap.derive(runner=None)`); ogni riconoscitore gira da solo su di essa e si confrontano gli id con un segno `declared` (`fast.lost`: quelli del registro che il fork non dichiara). Ogni tempo è di una chiamata (`time.monotonic()`), una misura per fixture, senza ripetizioni; `fork_fast` comprende l'avvio del processo Node.
- La traduzione e le misure sono in `tools/fork_stack.py`, provate da `test_fork_stack.py` senza Node. `accepted-losses.json` ha una riga `{fixture, name, id, reason, verdict}` per ogni nome perso, con il segno del registro, ciò che il fork ha o non ha e il verdetto (`accepted`: il registro sbagliava, oppure lo hanno deciso la spec o la porta del registro nel fork, `benchmarks/registry-port.json` del fork; `to_fix`: da cambiare, con dove). Due test tengono il file uguale a `lost` e dicono che nessuna fixture ha eseguito il codice del progetto.

### Risultati

Secondo giro, 22 novembre 2026, codice `9be947a3bbf0c61d` uguale ai due lati, 180 fixture, 178 con record (le altre due: «Senza risposta», sotto); `executed_project_code: no` in 178, `fork_failed` in 0. `model: partial` in 178: alle registrazioni mancano da 1 a 41 comandi per fixture, ai due lati allo stesso modo.

| Faccia | Attesi | Prima | Dopo |
| --- | --- | --- | --- |
| Framework per nome | 569 | 531 | 533 |
| Servizi | 518 | 227 | 228 |

I «prima» non sono quelli della sezione sopra (362 / 568 e 141 / 518): il codice è un altro (`c6be10745cedb94d` allora) e questo giro non lo spiega.

Nomi persi: 0 (`fixtures_with_lost`), quindi `accepted-losses.json` è `[]`. Nomi guadagnati: 3.

- Meilisearch in `real-stack-koel`: `meilisearch/meilisearch-php` in `composer.json` riga 30. La regola del fork lo elenca (`src/rules/db/meilisearch.ts`); la voce `meilisearch` del registro ha lo stesso pacchetto scritto con uno spazio in fondo (`"meilisearch/meilisearch-php "`), che non combacia mai.
- Maestro in `real-stack-mattermost-mobile`: i file di flusso in `detox/maestro/flows` e `detox/maestro/subflows`, che il fork riconosce con un lettore (`src/rules/spec/maestro` del fork). L'id non è nel registro.
- WinUI in `real-stack-peopleinspace`: `UseWinUI` in `windows/WinUiApp/PeopleInSpace.Windows.WinUiApp.csproj`, che il fork legge (`src/rules/spec/nuget` del fork). L'id non è nel registro.

**Primo giro**, 21 novembre 2026, rilascio `1.27.6-daodan.1`, codice `b3719332398056ec` (i risultati stanno nel commit `a2613d8`): 5 nomi persi in 5 fixture (framework 531 → 530, servizi 227 → 226). Il secondo giro viene dopo due correzioni, e il suo zero non è la prima misura.

- Spring MVC in `jvm-spring-boot-managed`, `real-stack-mall` e `real-svc-robot-shop`: il registro lo dava per `org.springframework.boot:spring-boot-starter-web`, che il rilascio `.1` dava solo a Spring Boot (una differenza registrata della porta). Il proprietario ha deciso di correggerlo nel fork: il rilascio `.2` lo dà a Spring Boot e a Spring MVC (`src/rules/framework/spring-mvc.ts`).
- GitHub Pages in `real-app-kotlinconf` e Gotenberg in `real-stack-documenso`: la traduzione scartava la prova di un file che la snapshot non ha, e la snapshot lascia fuori le cartelle col punto (`.github/workflows/web-deploy.yml`) e non registra `docker/development/Dockerfile.gotenberg`. Corretto in `tools/fork_stack.py` (`22e9b03`): vedi «Prima» e «dopo».
- Gli id spariti (`gone`) sono scesi da 33 coppie a 6: 3 per il rilascio (Spring MVC) e 24 per la traduzione, le due dei nomi persi e altre 22: `github.pages` in 6 fixture, `python` 3, `codecov` 2, `gcp` in `real-stack-hexpm`, e uno ciascuno `coveralls`, `depotdev`, `discord`, `docker`, `golangcilint`, `hugo`, `azure`, `azure.staticwebapps`, `click`, `ruff`. Non sono stati letti uno per uno; la causa è verificata per `github.pages` in `real-stack-peopleinspace` (`JamesIves/github-pages-deploy-action` in `.github/workflows/build-and-publish-web.yml`). Fra i due giri cambiano solo la traduzione, la regola `spring-mvc` del rilascio e i riferimenti al rilascio nel codice di Daodan (`daodan/core/stack_analyser.py`, `tests/modal_pytest.py`).

Id spariti (`gone`): 6 coppie id/fixture in 6 fixture, 4 id, nessuno è un nome atteso. Con `fast.lost` (7 coppie, 5 id: gli stessi quattro e `github.pages`) ognuno ha la sua causa; `okta` e `gcp` erano `extra` nel punteggio di prima (servizi in più rispetto a `expected.json`), e dopo non c'è `okta` e al posto di `gcp` c'è `google`, anch'esso `extra`.

- `react-email` (3: `real-app-full-stack-fastapi`, `real-stack-documenso`, `real-stack-epic-stack`; anche nella veloce): il registro ha due id per React Email, `react-email` (`@react-email/components`, `react-email`) e `reactemail` (`react-email`); il fork ne ha uno, `reactemail`, con i due pacchetti (`src/rules/tool/reactEmail.ts`), e la porta rinomina `react-email` in `reactemail` (`registry-port.json`, `renamed`). In fastapi e documenso `reactemail` c'era già prima, e se ne va solo il doppione; in epic-stack l'unico pacchetto è `@react-email/components` (`package.json` riga 60), che nel registro aveva solo `react-email`, e per questo lì `reactemail` è nuovo. Tutti i segni tornano sotto `reactemail`. Nessuna perdita.
- `kafka` (1: `real-svc-otel-demo`; anche nella veloce): `apache_kafka` c'era già prima (immagine `apache/kafka`, `src/kafka/Dockerfile` riga 5), per questo non è fra i nuovi. `kafka` (`Confluent.Kafka` in `src/accounting/Accounting.csproj` riga 12 e `Directory.Packages.props` riga 6, `org.apache.kafka:kafka-clients` in `src/fraud-detection/build.gradle.kts` riga 39) è un rinomino della porta in `apache_kafka`, la cui regola elenca i tre pacchetti (`src/rules/queue/apacheKafka.ts`); dopo, `apache_kafka` ha tutti i segni per valore e percorso (la riga di `kafka-clients`, 39, non è più data). Nessuna perdita.
- `okta` (1: `real-stack-bookstack`; anche nella veloce): il registro dava `socialiteproviders/okta` (`composer.json` riga 39) a `okta` e a `okta.oauth`; il fork lo dà a `okta.oauth` soltanto, una differenza registrata della porta (`registry-port.json`, `okta`). Il pacchetto resta riconosciuto, e `expected.json` elenca «Okta OAuth»; le menzioni `OKTA_*` non ci sono più (sotto, «Menzioni `env`»).
- `gcp` (1: `real-stack-nestjs-boilerplate`; anche nella veloce): `google-auth-library` (`package.json` riga 77) era di `gcp`, ora è di `google` (`src/rules/cloud/google.ts`): una differenza registrata della porta (`registry-port.json`, `gcp`). Il pacchetto resta riconosciuto.
- `github.pages` (1: `mix-real-tinyxml2`, solo nella veloce; nella completa nessuno dei due lati lo ha, né in questo giro né nel primo): per esclusione il segno è `docs/_config.yml`, il solo `_config` della lista dei file registrata, e nei workflow registrati non c'è nessuna azione di Pages. Nella completa go-enry marca quel file come documentazione e un file così va fra gli esclusi della pre-mappa, per i due lati (`premap/enry.py`); nella veloce enry non gira, il file resta e il registro lo prende per `github.pages`, mentre la porta ha tolto `_config.yml` e `_config.yaml` dalla voce (configurazione di Jekyll, non prova di hosting). È l'unico degli id spariti il cui segno dichiarato non passa a un altro id: se `docs/_config.yml` valga come prova di Pages, i dati non lo dicono.

Menzioni `env`: il percorso tradotto non produce segni `env`. Nei 10 record letti (sul volume: le fixture che mostrano ancora una differenza; ridotti, con di ogni voce i primi otto segni nell'ordine del registro, dove `env` viene per primo, e i segni dichiarati su altri percorsi) il «prima» ha segni `env` in 8 record, da 8 a 20 in ciascuno (al minimo, perché se ne mostrano al massimo otto per voce), e il «dopo» 0 in tutti e 10; `real-stack-bookstack` ha cinque `OKTA_*` nel «prima» (`app/Config/services.php`, righe 82-88) e dopo non ha né l'id `okta` né una menzione `OKTA_*`. I record non dicono se sopravviva una menzione senza segno dichiarato, perché `derive` non porta in `technologies` una voce con sole menzioni, né nel «prima» né nel «dopo»: dicono che nessuna voce con un segno dichiarato ha un segno `env`. I controlli del percorso tradotto sono `stack-analyser` e `host`, senza `check_env`; il rilascio legge le variabili solo nei modelli `.env*.example`, `.sample` e `.template` (`src/rules/spec/dotenv/index.ts`), file che Daodan non registra (`.env.*` è in `source_files.FORBIDDEN_GLOBS`), e quella prova è scartata fra le `evidence_outside_snapshot` (il gap nomina `.env.example` in 3 dei 10 record, che danno i primi cinque percorsi). Conseguenza: un token come `OKTA_CLIENT_ID` in un sorgente è una menzione per il registro (`check_env`) e non è letto dal percorso tradotto; la spec tiene gli host negli URL a `registry_hosts.py` (2.4), toglie `check_env` (2.6) e mette fuori scopo il riconoscere servizi dall'uso nel codice. `compare` conta id e nomi, non segni: quante menzioni si perdono non è nel file dei risultati.

Id nuovi (`new`, con i tre nomi guadagnati): 148 coppie in 106 fixture, 30 id: `gradle` 26, `maven` 23, `cargo` 17, `nuget` 9, `setuptools` 9, `pnpm` 7, `phpcomposer` 7, `bundler` 6, `azure` 6, `elixir` 4, `rich` 4, `aws` 4, `google` 3, `gcp` 3, `firebase` 2, `dart` 2, `swift` 2, `shadcn` 2, e uno ciascuno `docker`, `bunsh`, `microsoft`, `nodejs`, `cloudflare`, `vercel`, `reactemail`, `meilisearch`, `maestro`, `apple`, `typescript`, `winui`. Rispetto al primo giro compaiono `pnpm`, `bunsh`, `nodejs` e un `azure` in più, dalle dichiarazioni che ora restano: la regola `pnpm` del fork ha l'azione `pnpm/action-setup` (`src/rules/package_manager/pnpm.ts`) e `mix-infra-gha` la usa in `.github/workflows/ci.yml` riga 16 (gli altri non sono letti uno per uno). Fuori dal registro (`not_in_registry`), nel numero di fixture in cui compaiono: `gradle` 26, `setuptools` 9, `rich` 4, `maestro` 1, `winui` 1; escono col proprio id per nome e con categoria `framework`, che `entry_category` dà a chi non è un servizio.

Gap del fork, per tipo:

- `declaration_not_sent`: una dichiarazione della pre-mappa che la traduzione non manda al rilascio perché la pre-mappa ne lascia fuori il percorso; il registro la scarta allo stesso modo (`service_registry.run`, `_is_excluded`, riga 241; `tools/fork_stack.py`, riga 98), quindi il gap è lo stesso ai due lati. Sono 213, tutte nella scansione completa e in 9 fixture (`real-stack-ardalis-cleanarchitecture` 141, `real-stack-atuin` 41, `real-stack-openbudgeteer` 9, `real-stack-quarkus-super-heroes` 7, `real-stack-opengist` 5, `mix-real-python-semver`, `mix-real-tududi` e `real-stack-elk` 3 ciascuna, `real-stack-wallabag` 1). Il file dei risultati le conta per tipo di gap; la divisione per ecosistema (nuget 141, crates 23, pypi 12, docker 12, github-actions 9, npm 8, maven 7, go 1) e il motivo vengono dai record del primo giro sul volume (`project-model/stack-fork/<fixture>.json`), e i conteggi per fixture del secondo sono identici.
- `evidence_outside_snapshot`: in 69 fixture nella completa e in 71 nella veloce. Conta le prove che il rilascio legge da solo in file che Daodan non mette nella snapshot (`.dockerignore`, `.env.example`, `artisan`, `bun.lock`, la cartella `.github`; il gap dà il conto e i primi cinque percorsi, da 1 a 21 nelle 10 fixture dei record letti): non sono tecnologie perse. Per i segni di file il registro quei file non li vede nemmeno (`check_files` legge i file della snapshot); le dichiarazioni della pre-mappa su un percorso fuori dalla snapshot il registro le tiene, e dopo la correzione le tiene anche la traduzione.
- `not_in_registry`: 41 gap in 37 fixture, per ognuna delle due scansioni, uno per id fuori dal registro.

Tempi in secondi, sulle 178 fixture con record:

| Misura | Mediana | Massimo | Più lente |
| --- | --- | --- | --- |
| Veloce, registro (`registry_fast`) | 0,013 | 4,972 | `real-stack-netbox` 4,972, `real-stack-plausible` 4,568, `real-stack-owncast` 4,542 |
| Veloce, fork (`fork_fast`) | 0,523 | 5,791 | `mix-real-tududi` 5,791, `real-stack-plausible` 5,611, `real-stack-actual` 4,742 |
| Completa, registro (`registry_full`) | 0,029 | 5,277 | `real-stack-netbox` 5,277, `real-stack-owncast` 5,262, `real-stack-plausible` 4,339 |
| Completa, fork (`fork_full`) | 0,548 | 16,736 | `real-stack-owncast` 16,736, `real-stack-actual` 12,911, `real-stack-quarkus-super-heroes` 11,120 |

- `fork_fast`: minimo 0,302 (il registro 0,008); 149 fixture su 178 sotto 1 s, 29 da 1 s in su, 16 da 2 s, 10 da 3 s, 6 da 4 s, 2 da 5 s; `py-fastapi-compose`, il progetto di prova della spec, 0,331 (il registro 0,011); la mediana di `fork_fast` meno `registry_fast`, per fixture, è 0,472. In `mix-real-tududi`, la più lenta, il registro impiega 3,770. `registry_fast`: 19 fixture da 1 s in su.
- Nel primo giro, con lo stesso registro, `registry_fast` aveva mediana 0,013 e massimo 4,544, e `fork_fast` mediana 0,456 e massimo 4,982: fra due giri lo stesso codice si muove, e i tempi del fork si leggono con quella variazione.
- Senza risposta: `real-stack-jellyfin` e `real-stack-kuvasz`, `no answer in 1800 s`; il record dice dove stavano (`snapshot_store._unpack`, da `import_resolution.declaring`). Sono le stesse due senza record nel giro sopra e in `modal_premap.py` (D-302).

### Non misurato

- Windows: il giro è su container Linux; l'avvio di Node e la scansione veloce sulla macchina dell'utente non sono misurati.
- Le due fixture senza risposta: 178 su 180.
- La variazione fra due giri (sopra): non è spiegata.
- Il tempo sotto `project_lock` e con il resto del server in funzione.
- Di quali tecnologie siano le prove scartate da `evidence_outside_snapshot`: il file conta, e dà cinque percorsi.
- Quante menzioni `env` si perdono: `compare` conta id e nomi, non segni, e i record letti sono ridotti.

### Verdetto

- «Nessuna perdita»: passa sulle 178 fixture misurate (nessun nome atteso perso, nessuna riga `to_fix`, `accepted-losses.json` vuoto) e non è verificata sulle 2 senza risposta. Viene dopo la correzione della traduzione e la nuova regola del fork (Primo giro). `compare` conta id e nomi: dei 6 id spariti, tutti passano a un altro id con il loro segno dichiarato; nella sola veloce, `github.pages` in `mix-real-tinyxml2` non passa a nessun id, per una scelta registrata della porta. Le menzioni `env` non passano: il percorso tradotto non ne produce («Menzioni `env`»), ed è un secondo riconoscimento che il registro ha e il percorso non ha.
- Scansione veloce, su Linux, contro l'obiettivo della spec (meno di un secondo dall'avvio al risultato su `py-fastapi-compose`; circa un secondo a ogni modifica sotto `project_lock`): `py-fastapi-compose` 0,331 s, mediana 0,523 s, 29 fixture su 178 da 1 s in su, massimo 5,791 s. La soglia è del proprietario; se l'obiettivo non è raggiunto, la spec ferma il lavoro al passo 3.
- Tornano al proprietario i tempi, le tre differenze della porta che spostano un id senza cambiare nessun nome atteso (`okta`, `gcp`, `_config.yml` di Jekyll) e le menzioni `env`.
