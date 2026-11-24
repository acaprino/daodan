# Pre-mappa del progetto: quali strumenti esistenti la danno

**Stato:** In parte. La pre-mappa esiste (`daodan/core/premap/`) e prende da strumenti esistenti linguaggi ed esclusi, versioni e pacchetti dichiarati, modelli dei build system e framework; restano di Daodan i lettori di manifest, e lo scanner di file e gli strumenti per i progetti senza build tool non sono nel codice (sezione 1). Gli strumenti sono misurati in [`benchmarks/project-model/REPORT.md`](../../benchmarks/project-model/REPORT.md); il passo che scrive la pre-mappa è descritto in [pipeline di analisi](../specs/2026-11-15-pipeline-di-analisi.md).

**Verifica delle fonti:** 14 novembre 2026. Ogni dato esterno viene dalla fonte primaria (repository, pagina o API delle release, file di licenza, documentazione, registro dei pacchetti). Dove non è stato possibile c'è scritto **non verificato**. Per questa ricerca niente è stato installato o eseguito.

## In breve

- **La regola del proprietario.** Daodan non porta codice di riconoscimento proprio: linguaggi, framework, build tool, struttura e versioni di toolchain vengono da strumenti esistenti e mantenuti. Le dipendenze non entrano nella pre-mappa: le risolve nel container il build tool di ogni analyzer. Il codice proprio è solo un adattatore sottile sopra la loro uscita, e solo dove nulla esiste. Lo scopo è una **pre-mappa**, fatta prima di ogni analisi. Dice quali analisi eseguire e come costruire il grafo. Dà la prima suddivisione in **moduli espliciti**, cioè le unità che il build system stesso dichiara.
- **Nessuno strumento dà da solo la pre-mappa.** Chi legge i file senza eseguire nulla (Trivy, Syft, component-detection, Renovate) dà manifest, lockfile, pacchetti con versioni e a volte i membri del workspace. Non dà cartelle sorgente, source set, task di compilazione, file per unità, linguaggi per unità né `tsconfig`. Chi dà unità con source set e dipendenze (BSP, Gradle Tooling API, ORT, Nx) esegue la build: va nel container.
- **La combinazione proposta,** normalizzata nel modello `BuildTarget` di BSP, ha tre pezzi:
  - uno scanner di file per l'inventario (Trivy o Syft);
  - i comandi di modello dei build tool che non eseguono codice del progetto: `go list`, `cargo metadata --frozen`, `pnpm`/`npm ls` in modalità solo lockfile, `uv --frozen --no-build`, `tsc --showConfig`;
  - nel container, il modello nativo di Gradle, Maven, .NET, CMake e Bazel.
- **Versioni di toolchain.** La pre-mappa riporta le versioni dichiarate e la preparazione nel container installa quelle esatte; un intervallo come `>=20` è un buco `toolchain_unavailable`.
- **Progetti senza build tool.** Esistono lettori onesti: uv per gli script PEP 723; deptry per Python, dependency-cruiser per JS/TS e `go list` per Go, quando ci sono solo gli import. Ognuno però indovina o esegue qualcosa in un punto preciso, scritto più sotto. Per una lista non bloccata (`requests>=2`), solo OSV-SCALIBR conserva il vincolo senza inventare una versione. Per le import map HTML non esiste nulla.

## 1. Nel codice oggi

Percorsi relativi a `daodan/core/`. Le fonti della pre-mappa sono `premap.SOURCES`; ogni comando di modello gira nel container di Daodan, nessuno sull'host.

| Responsabilità | Nel codice |
| --- | --- |
| Linguaggio per file ed esclusi | go-enry (`premap/enry.py`); la tabella dei suffissi dello snapshot resta come fonte che go-enry sostituisce (`premap/suffix_table.py`) |
| Unità di build, workspace, dipendenze fra unità | I lettori di manifest di Daodan (`build_units.py`, fonte `premap/module_graph.py`), più i comandi di modello di Go, Cargo, uv, npm, CMake, Meson, Bazel, Make, Gradle, Maven, sbt e .NET (una fonte per strumento in `premap/`) |
| Configurazione per gli indicizzatori | `tsc --showConfig` per ogni `tsconfig` (`premap/tsc.py`); cartelle dei pacchetti Python dalla configurazione di build (`premap/python_build.py`) |
| Versioni di toolchain e pacchetti dichiarati | Renovate in estrazione locale (`premap/renovate.py`); versioni di Swift e di MSBuild dai file di progetto (`premap/project_files.py`); installazione con mise (`preparation.py`) |
| Framework e servizi | Il fork di stack-analyser (`stack_analyser.py`) e il registro (`service_registry.py`), nel passo `stack` |
| Sottomoduli Git | `premap/gitmodules.py` legge `.gitmodules`; un sottomodulo assente è il buco `submodule_absent` |
| Lista di dipendenze senza build tool | `premap/requirements.py` legge i file requirements di pip |
| Non nel codice | Trivy, Syft, OSV-SCALIBR, deptry, dependency-cruiser; nessuna fonte per gli script PEP 723 |

## 2. Strumenti esistenti

I cinque vincoli valgono per ogni candidato:

1. non esegue codice del progetto sull'host;
2. funziona su Windows;
3. funziona offline dopo il primo download;
4. la licenza permette di ridistribuirlo o di scaricarlo al primo uso;
5. è mantenuto nel 2026.

Date lette dalle API delle release o dai registri il 14 novembre 2026.

### 2.1 Modelli di progetto su più ecosistemi

| Strumento | Cosa dà | Come lo ottiene | Vincoli |
| --- | --- | --- | --- |
| [Trivy](https://trivy.dev/latest/docs/coverage/language/) `fs` | Un `Result` per manifest o lockfile (`Target`, `Type`). Per ogni pacchetto dà `Name`, `Version`, `Relationship` (`root`, `workspace`, `direct`, `indirect`), `DependsOn` e `Locations`. Lockfile di Ruby, Python (anche uv), PHP, Node (anche bun), .NET, Go `go.mod`, Cargo, Conan, Mix, Pub, Swift, Julia; Java `pom.xml` e lockfile Gradle e sbt | Legge i file. Per `pom.xml` usa i genitori locali o `~/.m2`, altrimenti i repository remoti; `--offline-scan` lo impedisce "may skip some dependencies" | Apache-2.0, v0.76.2 del 2026-11-05, zip per Windows di 51 MB. Che non esegua mai un package manager è **non verificato**; come elencare senza scaricare il database delle vulnerabilità è **non verificato** |
| [Syft](https://oss.anchore.com/docs/guides/sbom/json/) | `artifacts` con `name`, `version`, `type`, `language`, `purl`, `locations[]` (evidenza primaria o di supporto); `artifactRelationships` (`contains`, `dependency-of`) | Legge i file; `golang.use-packages-lib` eseguirebbe gli strumenti Go del PATH (default mostrato vuoto: va spento) | Apache-2.0, v1.57.1 del 2026-11-09, 29-30 MB. Arricchimenti remoti spenti di default; controllo di aggiornamento acceso, va spento |
| [microsoft/component-detection](https://github.com/microsoft/component-detection/blob/main/docs/detectors/README.md) | `componentsFound` con `locationsFoundAt`, `dependencyScope`, `topLevelReferrers`; `dependencyGraphs` (chiave stringa: che sia il percorso del manifest è **non verificato**) | **Esegue** `mvn dependency:tree`, `go list -m -json all`, `cargo metadata`, `pip install --report`; il detector pip legacy esegue `setup.py`. Si spengono con `CD_MAVEN_DISABLE_CLI`, `DisableGoCliScan`, `DisableRustCliScan`. Gradle solo da lockfile | MIT, v9.1.0 del 2026-11-12, exe per Windows di 86,7 MB |
| [ORT analyzer](https://oss-review-toolkit.org/ort/docs/tools/analyzer) | `Project` con `definitionFilePath` e `scopes`; legame `PROJECT_DYNAMIC`/`PROJECT_STATIC` fra sottoprogetti. Copre Bazel, Gradle, Maven, npm, pnpm, Yarn, Bun, Cargo, GoMod, NuGet, SwiftPM, Pip, Poetry e altri | **Esegue** i build tool: Gradle con Tooling API, Maven embedded, `npm ci`; Pip con `analyzeSetupPyInsecurely` vero di default | Apache-2.0, 99.0.0 del 2026-11-12, Java 25 o più, zip di 251 MB, immagine container. Non offline |
| [Build Server Protocol 2.2.0](https://build-server-protocol.github.io/docs/specification) | Il modello giusto per la pre-mappa: `BuildTarget{id, displayName, baseDirectory, tags, languageIds, dependencies, capabilities, dataKind, data}`. Poi `buildTarget/sources` con `roots` e `generated`, `resources`, `outputPaths`, `dependencyModules` (nome e versione). Dati `jvm` (`javaHome`, `javaVersion`), `cargo` (`edition`, `requiredFeatures`), `python` (`version`, `interpreter`), `cpp` | Ogni server esegue la build: [build-server-for-gradle](https://github.com/microsoft/build-server-for-gradle) aggiunge un plugin con uno script di init. sbt e Mill sono server di se stessi; Maven passa solo da Bloop | Gradle: MIT, 0.4.0 del 2026-06-26, JDK 17. bazel-bsp è archiviato dal 2025-12-21; cargo-bsp è fermo al 2023; per Python non c'è server |
| [Nx](https://github.com/nrwl/nx/blob/master/packages/nx/src/config/project-graph.ts) | `ProjectGraph` con nodi (`root`, `sourceRoot`, `targets`), `externalNodes` `npm:pkg@ver`, dipendenze `static`, `dynamic`, `implicit` | **Esegue**: `@nx/vite` valuta `vite.config.*`; `@nx/gradle` lancia `gradlew`; `@nx/maven` lancia `mvn`; `@nx/dotnet` fa una valutazione MSBuild | MIT, 24.0.6 del 2026-11-10 |
| [moon](https://moonrepo.dev/docs/config/workspace) | Progetti e linguaggi | Richiede `.moon/workspace.*`: non deduce un progetto senza configurazione | MIT, v2.6.5 |
| [Renovate](https://docs.renovatebot.com/modules/platform/local/) `--platform=local --dry-run=extract` | 122 gestori: pacchetti per manifest e i file di versione (`gomod` con `go` e `toolchain`, `rust-toolchain`, `nvm`, `pyenv`, `asdf`, `mise`, `gradle-wrapper`, `maven-wrapper`), `git-submodules`, `pep723`, `kotlin-script`, `deno` | Parser statici: il gestore `gradle` "does not call `gradle` directly". La piattaforma locale è sperimentale | AGPL-3.0, 44.239.1 del 2026-11-13, Node `^24.11.0 \|\| ^26.13.0`. I maintainer prevedono di togliere il supporto ufficiale a Windows (discussione #32751). Formato dell'uscita e rete durante l'estrazione: **non verificati** |

### 2.2 Comandi di modello dei build tool

| Comando | Sull'host senza codice del progetto | Cosa dà per la pre-mappa |
| --- | --- | --- |
| `go list -m -json`, `go list -json ./...` | Sì: Go non ha script di build; evitare `-compiled` e `-export`; `GOPROXY=off` per non usare la rete | Modulo con `Dir` e `GoMod`; pacchetti con file e `Imports`. `./...` salta `_x`, `.x`, `testdata` e i moduli annidati, che vanno trovati come file `go.mod` |
| `cargo metadata --format-version 1 --frozen` | Probabile: la pagina non dice che esegua `build.rs` (**non verificato**) | `workspace_members`, `packages` con `targets` (tipo, `src_path`, `edition`), grafo `resolve` con versioni da `Cargo.lock` |
| `npm ls --json --all --package-lock-only`, `pnpm list --json -r --lockfile-only` | Probabile (che non eseguano script è **non verificato**) | Albero logico, membri del workspace (`--only-projects`) |
| `uv export --frozen --no-build`, `uv tree --frozen` | Sì con `--frozen --no-build`; senza, rifanno il lock e possono eseguire `setup.py` | Pacchetti e versioni da `uv.lock`, membri del workspace (`--all-packages`) |
| `tsc --showConfig -p <tsconfig>` | Sì: i `plugins` sono solo del language service, tsc non li carica | Configurazione finale con `extends` fuso e `paths` relativi; `include`/`exclude` come scritti; `references` elencate ma **non seguite**. TypeScript 6.0.3 su Node o 7.0.2 nativo |
| gopls `gopls.modules` | Come `go list` | Solo moduli delle viste già caricate: non cerca i `go.mod` sul disco |
| Maven `help:effective-pom`, Gradle Tooling API, `dotnet list package`, `bazel query`, `swift package dump-package`, CMake File API | **No**: estensioni Maven, script Gradle, MSBuild, regole Bazel, `Package.swift` e `CMakeLists.txt` sono codice | Solo nel container |

### 2.3 Linguaggio per file

| Strumento | Vincoli | Nota |
| --- | --- | --- |
| [Linguist](https://github.com/github-linguist/linguist) | MIT, v9.7.0 del 2026-08-26; gemma Ruby con estensioni native, Windows **non verificato** | I dati (`languages.yml`, `heuristics.yml`, `vendor.yml`, `documentation.yml`) sono riusabili; `generated.rb` e il classificatore sono codice Ruby |
| [go-enry](https://github.com/go-enry/go-enry) | Apache-2.0, v2.9.6 del 2026-04-04, commit fino a novembre 2026; nessun binario pubblicato | Porting di Linguist (segue la 9.5.0) con `IsVendor`, `IsGenerated`, `IsTest`, `IsDocumentation`. In uso: `daodan/core/premap/enry.py` |
| scc, tokei, Magika | MIT; MIT o Apache-2.0; Apache-2.0 | Contano righe o classificano il contenuto: non sostituiscono Linguist |

### 2.4 Versioni di toolchain

| Strumento | Vincoli | Cosa legge |
| --- | --- | --- |
| [mise](https://mise.jdx.dev/configuration/settings.html) `ls --current --json` | MIT, v2026.11.8 del 2026-11-13, 87 MB per Windows. `MISE_SAFE` ("Load project config without letting it run code or change the environment") e `MISE_OFFLINE` ("Block every HTTP request") verificati | Con `idiomatic_version_file_enable_tools` (vuoto di default) legge `.nvmrc`, `.node-version`, `package.json`, `.python-version`, `.java-version`, `.sdkmanrc`, `rust-toolchain.toml` (non il legacy), `.go-version`, `go.mod`/`go.work` (riga `toolchain` o `go X.Y.Z` esatto) |
| [Go `GOTOOLCHAIN`](https://go.dev/doc/toolchain) | BSD-3-Clause, go1.27.4 del 2026-11-10; download verificati dal database delle somme | `go` e `toolchain` |
| [uv](https://docs.astral.sh/uv/concepts/python-versions/) | MIT o Apache-2.0, 0.13.8 del 2026-11-12, `UV_OFFLINE` | `.python-version`, `requires-python` |
| [rustup](https://rust-lang.github.io/rustup/overrides.html) | Apache-2.0 | `rust-toolchain.toml` e legacy; installa da solo dalla 1.28.1 salvo `RUSTUP_AUTO_INSTALL=0` |
| proto, Railpack, CNB/Paketo, Nixpacks, Devbox, asdf, SDKMAN, Volta | Vari | Scartati: rete per risolvere (Railpack), detect solo in un ambiente Linux con Docker (CNB), manutenzione ferma (Nixpacks, Volta), niente Windows (asdf, SDKMAN, Devbox) |

Nessuno legge la release Java di `pom.xml` né il blocco `toolchain` di Gradle senza eseguire Gradle.

### 2.5 Framework e servizi

| Strumento | Vincoli | Nota |
| --- | --- | --- |
| [Specfy stack-analyser](https://github.com/specfy/stack-analyser) (in uso) | MIT, 1.27.6 del 2026-01-18, nessuna release da allora; Node; offline con `FSProvider` | Oltre 700 tecnologie, SaaS compresi, su più ecosistemi; Java e C# parziali |
| [@vercel/fs-detectors](https://registry.npmjs.org/@vercel%2ffs-detectors/latest) | Apache-2.0, 7.12.1 del 2026-11-13; Node; offline | Framework JS con versione, workspace e monorepo, solo ecosistema JS |
| [@netlify/build-info](https://github.com/netlify/build/tree/main/packages/build-info) | MIT, 11.3.1 del 2026-10-23; Node 22.12 o più | Solo JS |
| [devfile/alizer](https://github.com/devfile/alizer) | Apache-2.0, v1.11.0; binario Go per Windows | Linguaggi, framework, porte; l'abbinamento ai devfile chiama un registro in rete |
| [webappanalyzer](https://github.com/enthec/webappanalyzer), [deps.dev](https://docs.deps.dev/api/v3/) | GPL-3.0; servizio in rete | Siti in esecuzione, non codice; solo online |

### 2.6 Progetti senza build tool

| Caso | Strumento | Cosa riporta | Dove indovina o esegue | Vincoli |
| --- | --- | --- | --- | --- |
| Script Python PEP 723 | [uv](https://docs.astral.sh/uv/guides/scripts/) `export --script`, `tree --script` (dalla 0.5.17) | Le dipendenze del blocco, **risolte** a versioni | Può costruire sdist; `--no-build` lo rende un errore; `--offline` usa solo la cache | MIT o Apache-2.0, 0.13.8 |
| Script Python PEP 723 | Renovate `pep723` | Le stringhe PEP 508 come scritte | Statico, ma attivo solo con `managerFilePatterns` | AGPL-3.0, Windows in uscita |
| Lista non bloccata (`requests>=2`) | [OSV-SCALIBR](https://github.com/google/osv-scalibr/blob/main/extractor/filesystem/language/python/requirements/requirements.go) | Nome, versione e comparatore, più la riga originale in `Requirement` | Nessun indicatore "non risolto"; `>2.0` viene scartato | Apache-2.0, v0.5.3, Windows "sperimentale", solo libreria Go |
| Lista non bloccata | Syft | Le righe senza versione esatta sono **saltate** con un errore; `python.guess-unpinned-requirements` trasforma `>=2` in "2" | Indovina solo se gli si chiede di farlo | come sopra |
| Lista non bloccata | Trivy | Solo `==` di default | `--detection-priority comprehensive` prende il minimo | come sopra |
| Solo import, Python | [deptry](https://deptry.com/rules-violations/) DEP001 | Il **modulo** importato che non corrisponde a nessun pacchetto dichiarato | Senza pacchetto installato traduce il nome (`Foo-Bar` diventa `foo_bar`); che non importi mai i moduli è **non verificato** | MIT, 0.25.1 del 2026-03-18, wheel per Windows |
| Solo import, JS e TS | [dependency-cruiser](https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md) | Le importazioni non risolte come `unknown`, senza inventare il pacchetto; regola `npm-no-pkg` | Carica le configurazioni JS di webpack e babel e la propria `.dependency-cruiser.js`: va usato senza file di configurazione JS | MIT, v18.7.2 del 2026-11-02, Node |
| Solo import, Go | `go list -json file.go` | Fuori da un modulo carica solo la libreria standard e i file nominati: `Imports` dà la lista grezza | Nulla | come Go |
| Da scartare | pipreqs (tabella più ricerca su PyPI, cerca maintainer), pigar (chiede all'utente), FawltyDeps (mappa d'identità di default, fermo da metà 2025), Knip (esegue i file di configurazione con jiti), depcheck (archiviato) | | | |
| Script con dipendenze in altri linguaggi | JBang `info tools` (JSON, "still quite experimental", può installare un JDK); Renovate `kotlin-script`, `deno`; cargo script ancora instabile (`-Zscript`) | | | |
| Import map HTML | Nessuno strumento d'inventario mantenuto: jspm 4.7.0 è un generatore che risolve via CDN | | | |

## 3. Verdetto

### 3.1 Per responsabilità

| Responsabilità | Strumento, o piccolo insieme, che la dà | Cosa fa l'adattatore | Cosa resta scoperto |
| --- | --- | --- | --- |
| **Pre-mappa dei moduli espliciti** | Tre pezzi: lo scanner di file Trivy o Syft per manifest, lockfile, pacchetti e relazioni; sull'host `go list`, `cargo metadata --frozen`, `npm`/`pnpm ls` con solo lockfile, `uv --frozen --no-build`, `tsc --showConfig`; nel container il modello nativo di Gradle (BSP o Tooling API), Maven (`help:effective-pom`), .NET, CMake (File API), Bazel | Mette ogni uscita in un `BuildTarget` (radice, linguaggi, dipendenze fra unità, sorgenti, dipendenze esterne con versione) e scrive il record di `modules.py`. Un adattatore per comando, decine di righe ciascuno | File per unità dove non c'è comando di modello: un pacchetto Python senza eseguire il suo build backend, nulla va bene. Gradle e Maven senza container: buco dichiarato. Moduli Rust condivisi fra crate di test: li vede solo rust-analyzer. `modules.py` tiene record, `declared`, `proposed`, verifica dei membri, archi, grafo |
| Linguaggio per file | go-enry; oppure i dati di Linguist | Traduce il nome del linguaggio di go-enry nell'adattatore di Daodan e usa `IsVendor`, `IsGenerated`, `IsDocumentation` per il perimetro | go-enry segue Linguist 9.5.0 e manca di alcune euristiche (RE2). Con i soli dati di Linguist l'ordine delle strategie va riscritto: è codice proprio |
| Configurazione per gli indicizzatori | `tsc --showConfig -p` per ogni `tsconfig`; `cargo metadata` per i target; `go list` per i pacchetti; nel container, le cartelle sorgente di BSP | Segue le `references` del `tsconfig` radice e lancia `--showConfig` su ognuno | Le opzioni che Vite o webpack aggiungono a runtime (alias, `additionalData` dei CSS) esistono solo eseguendo la loro configurazione: buco dichiarato |
| Versioni di toolchain | Renovate per leggere (in REPORT.md legge più dichiarazioni di mise); mise per installare | Passa la versione letta al meccanismo che installa | Release Java del pom, `toolchain` di Gradle, `go X.Y` senza patch, range come `>=18` o `lts/*` (serve la rete). La versione Java si legge solo dal modello nativo nel container: **nulla va bene sull'host** |
| Dipendenze e file su disco | Inventario: Trivy o Syft. File su disco: i comandi nativi, più il gestore di pacchetti del progetto (pnpm, yarn) con `--ignore-scripts` e lockfile | Converte l'inventario nella lista da installare; sceglie il gestore dal lockfile | Gradle senza lockfile (solo il modello nativo nel container); nessuno SBOM scarica i file |
| Framework e servizi | Specfy stack-analyser per tutti gli ecosistemi; @vercel/fs-detectors se serve la versione del framework JS | Il registro è già l'adattatore (dati dalle regole di Specfy) | Specfy è fermo da dieci mesi; Java e C# parziali; nessun catalogo mantenuto copre i servizi lato codice per tutti i linguaggi |
| Progetto con sola lista di dipendenze | uv (`--script`, `--frozen`, `--no-build`) per Python; OSV-SCALIBR per conservare i vincoli | Marca "dichiarato, non bloccato" ogni riga senza `==` | Nessuno strumento segnala da solo che una versione non è bloccata |
| Progetto che dichiara nulla | deptry (Python), dependency-cruiser senza configurazione JS (JS e TS), `go list` sui file (Go) | Riporta il modulo importato come buco "importato, non dichiarato", mai un nome di pacchetto indovinato | Import map HTML, Deno senza rete, Groovy `@Grab`: nulla va bene |

### 3.2 I casi misurati in questo progetto: chi li avrebbe riportati prima

| Caso | Chi lo dà prima dell'analisi | Note |
| --- | --- | --- |
| chi: moduli Go annidati in `_examples/*` che `./...` salta | Trivy, Syft, Renovate: un risultato per ogni `go.mod`; poi `go list -m -json` in ognuno | gopls `gopls.modules` no: guarda solo le viste caricate |
| tududi: si installa da un solo `package.json` radice | Trivy e Syft (un solo lockfile, relazione `root`); `npm ls --package-lock-only` | |
| App React: alias `@/` in `tsconfig.app.json` sopra un `tsconfig` base | Solo `tsc --showConfig -p tsconfig.app.json`, seguendo a mano le `references` del radice | Nessuno scanner legge `tsconfig`; Nx lo dedurrebbe ma esegue `vite.config` |
| Workspace Rust: un modulo di test condiviso fra più crate di test | `cargo metadata` elenca ogni crate di test con il suo `src_path` | Quali crate includono il file condiviso lo sa solo rust-analyzer al caricamento |
| Kotlin: più task di compilazione, overload referenziati fra loro | Solo il modello Gradle (BSP o Tooling API), nel container | Nulla di statico |
| Android Gradle: serve l'SDK e chiama cargo | Prima: gli id dei plugin dal parser statico di Renovate (dipendenze di tipo `plugin`). Del tutto: solo Gradle nel container, che senza SDK fallisce e diventa buco | Tradurre un id di plugin in un requisito è codice proprio, piccolo |
| Sottomoduli Git assenti da un archivio | Git stesso: `git config -f .gitmodules --get-regexp path`, che funziona anche senza `.git`; `git ls-files --stage` (modo 160000) in un checkout. Anche Renovate `git-submodules` | Nel codice li legge `premap/gitmodules.py` |
| Progetto Python con versioni in `uv.lock` | Trivy, Syft, component-detection; `uv export --frozen` (`premap/uv.py`) | |
| App Vue: fogli globali caricati da `main.ts` | Nessuno: è un import nel sorgente, lo trova il grafo (adattatore dei fogli di stile) | Ciò che `vite.config` aggiunge resta un buco |

### 3.3 Vincoli dei candidati scelti

| Candidato | Niente codice sull'host | Windows | Offline | Licenza | Mantenuto |
| --- | --- | --- | --- | --- | --- |
| Trivy | Sì leggendo; che non esegua mai strumenti è **non verificato** | Sì | Con `--offline-scan` | Apache-2.0 | Sì |
| Syft | Sì con `golang.use-packages-lib` spento | Sì | Sì, controllo di aggiornamento spento | Apache-2.0 | Sì |
| `go list`, `cargo metadata`, `npm`/`pnpm ls`, `uv`, `tsc` | Sì; `cargo` e `npm`/`pnpm` **non verificati** del tutto | Sì | Sì, con la cache piena | BSD-3, MIT/Apache, Artistic-2.0 (npm, **non verificato**), MIT, Apache-2.0 | Sì |
| BSP per Gradle, Tooling API, Maven | No: solo nel container | Nel container | Dopo la preparazione | MIT, Apache-2.0 | Sì |
| mise | Sì con `MISE_SAFE` | Sì | `MISE_OFFLINE` | MIT | Sì |
| go-enry | Sì | Sì, compilato | Sì | Apache-2.0 | Sì, in ritardo su Linguist |
| Specfy stack-analyser | Sì | Node | `FSProvider` | MIT | Dubbio: nessuna release da gennaio 2026 |
| deptry | **Non verificato** | Sì | Sì | MIT | Sì |
| dependency-cruiser | Sì senza configurazioni JS | Node | Sì | MIT | Sì |
| Renovate | Sì per i parser | In uscita | **Non verificato** | AGPL-3.0 | Sì |

## 4. Misura e questioni aperte

Le adozioni proposte da questa ricerca sono state misurate su Modal in [`benchmarks/project-model`](../../benchmarks/project-model/README.md): il verdetto per strumento e per faccetta, e l'esito di ogni affermazione di questa ricerca, sono in [REPORT.md](../../benchmarks/project-model/REPORT.md) («La ricerca alla prova»). I numeri vivono lì.

Aperte: da approfondire.

- **Scanner di file (Trivy o Syft) per le versioni bloccate dai lockfile.** REPORT.md lo consiglia accanto a Renovate; nel codice non c'è.
- **Progetti senza build tool.** deptry, dependency-cruiser senza configurazione JS, `go list` sui file e `uv export --script --no-build` non sono nel codice. La prova proposta conta: import riportati; nomi di pacchetto inventati (devono essere zero); codice eseguito (deve essere zero, con un modulo esca che scrive un file quando viene importato); riuscita offline.
- **I lettori di manifest di Daodan (`build_units.py`)** restano: in REPORT.md trovano più unità di ogni strumento esterno (Verdetto, punto 5). Da decidere se, dove un comando di modello esiste, il lettore si toglie, come chiede la regola del proprietario.

## Non verificato

- Trivy: che non esegua mai un package manager; come elencare i pacchetti senza scaricare il database delle vulnerabilità.
- Syft: valore di default di `golang.use-packages-lib`.
- `cargo metadata`: che non esegua `build.rs`. `npm ls` e `pnpm list` solo lockfile: che non eseguano script. Licenza di npm.
- component-detection: chiave di `dependencyGraphs`; necessità di un runtime .NET.
- Renovate: formato dell'uscita, rete durante l'estrazione, futuro del supporto a Windows.
- deptry: che legga gli import senza importare i moduli.
- uv: se `uv build` del suo backend sa elencare i file di un pacchetto senza costruirlo.
- Linguist su Windows; bazel-bsp nel monorepo di JetBrains come server a sé.

## Fonti

- Modelli su più ecosistemi: [Trivy, linguaggi](https://trivy.dev/latest/docs/coverage/language/), [Trivy, Java](https://trivy.dev/latest/docs/coverage/language/java/), [Syft JSON](https://oss.anchore.com/docs/guides/sbom/json/), [configurazione di Syft](https://oss.anchore.com/docs/reference/syft/configuration/), [component-detection](https://github.com/microsoft/component-detection/blob/main/docs/detectors/README.md), [ScanResult.cs](https://github.com/microsoft/component-detection/blob/main/src/Microsoft.ComponentDetection.Contracts/BcdeModels/ScanResult.cs), [ORT analyzer](https://oss-review-toolkit.org/ort/docs/tools/analyzer), [Project.kt di ORT](https://github.com/oss-review-toolkit/ort/blob/main/model/src/main/kotlin/Project.kt), [BSP](https://build-server-protocol.github.io/docs/specification), [implementazioni BSP](https://build-server-protocol.github.io/docs/overview/implementations), [build-server-for-gradle](https://github.com/microsoft/build-server-for-gradle/blob/develop/ARCHITECTURE.md), [Nx project graph](https://github.com/nrwl/nx/blob/master/packages/nx/src/config/project-graph.ts), [plugin Vite di Nx](https://github.com/nrwl/nx/blob/master/packages/vite/src/plugins/plugin.ts), [moon](https://moonrepo.dev/docs/config/workspace), [Renovate locale](https://docs.renovatebot.com/modules/platform/local/), [gestori di Renovate](https://docs.renovatebot.com/modules/manager/), [gestore gradle](https://docs.renovatebot.com/modules/manager/gradle/), [gestore gomod](https://docs.renovatebot.com/modules/manager/gomod/), [pacchetto renovate](https://registry.npmjs.org/renovate/latest).
- Comandi nativi: [cmd/go](https://pkg.go.dev/cmd/go), [go.dev/ref/mod](https://go.dev/ref/mod), [cargo metadata](https://doc.rust-lang.org/cargo/commands/cargo-metadata.html), [npm ls](https://docs.npmjs.com/cli/v11/commands/npm-ls), [pnpm list](https://pnpm.io/cli/list), [uv CLI](https://docs.astral.sh/uv/reference/cli/), [opzioni di tsc](https://www.typescriptlang.org/docs/handbook/compiler-options.html), [project references](https://www.typescriptlang.org/docs/handbook/project-references.html), [commandLineParser.ts 6.0.3](https://github.com/microsoft/TypeScript/blob/v6.0.3/src/compiler/commandLineParser.ts), [comandi di gopls](https://github.com/golang/tools/blob/master/gopls/internal/protocol/command/interface.go), [Gradle Tooling API](https://docs.gradle.org/current/userguide/tooling_api.html), [estensioni Maven](https://maven.apache.org/guides/mini/guide-using-extensions.html), [dotnet package list](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-package-list), [bazel mod](https://bazel.build/external/mod-command).
- Linguaggio: [Linguist](https://github.com/github-linguist/linguist), [go-enry](https://github.com/go-enry/go-enry), [scc](https://github.com/boyter/scc), [tokei](https://github.com/XAMPPRocky/tokei), [Magika](https://github.com/google/magika).
- Toolchain: [mise, impostazioni](https://mise.jdx.dev/configuration/settings.html), [mise, versioni](https://mise.jdx.dev/dev-tools/versions.html), [Go toolchain](https://go.dev/doc/toolchain), [uv, versioni di Python](https://docs.astral.sh/uv/concepts/python-versions/), [rustup, override](https://rust-lang.github.io/rustup/overrides.html), [Gradle toolchains](https://docs.gradle.org/current/userguide/toolchains.html), [Railpack](https://railpack.com/reference/cli), [CNB detect](https://buildpacks.io/docs/for-platform-operators/concepts/lifecycle/detect/), [proto](https://moonrepo.dev/docs/proto/detection).
- Framework e servizi: [Specfy stack-analyser](https://github.com/specfy/stack-analyser), [@vercel/fs-detectors](https://raw.githubusercontent.com/vercel/vercel/main/packages/fs-detectors/src/index.ts), [@netlify/build-info](https://github.com/netlify/build/tree/main/packages/build-info), [alizer](https://github.com/devfile/alizer), [webappanalyzer](https://github.com/enthec/webappanalyzer), [deps.dev](https://docs.deps.dev/api/v3/).
- Senza build tool: [script con uv](https://docs.astral.sh/uv/guides/scripts/), [Renovate pep723](https://docs.renovatebot.com/modules/manager/pep723/), [requirements di SCALIBR](https://github.com/google/osv-scalibr/blob/main/extractor/filesystem/language/python/requirements/requirements.go), [requirements di Syft](https://github.com/anchore/syft/blob/main/syft/pkg/cataloger/python/parse_requirements.go), [deptry](https://deptry.com/rules-violations/), [FawltyDeps](https://tweag.github.io/FawltyDeps/explanation/), [pipreqs](https://github.com/bndr/pipreqs/blob/master/pipreqs/pipreqs.py), [loader di Knip](https://github.com/webpro-nl/knip/blob/main/packages/knip/src/util/loader.ts), [regole di dependency-cruiser](https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md), [opzioni di dependency-cruiser](https://github.com/sverweij/dependency-cruiser/blob/main/doc/options-reference.md), [Go fuori dai moduli](https://github.com/golang/go/blob/master/src/cmd/go/testdata/script/mod_outside.txt), [JBang](https://www.jbang.dev/documentation/jbang/latest/dependencies.html), [cargo script](https://doc.rust-lang.org/cargo/reference/unstable.html), [jspm](https://jspm.org/docs/cli/).
