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

```
python -m unittest test_score.py     # test del punteggio
python score.py --check all          # controlla ogni expected.json
python score.py all all              # tabelle per strumento e faccetta
python score.py syft,trivy js        # alcuni strumenti, una famiglia
```

## Parametri

### Corpus

Ogni fixture mette alla prova un punto in cui un lettore ingenuo sbaglia; il dettaglio è nel suo campo `traps`.

Le famiglie `js`, `py`, `jvm`, `sys` e `mix` sono progetti in miniatura scritti per il benchmark. La famiglia `real` è fatta di repository veri di GitHub con più moduli (front end, back end, servizi, più linguaggi e build system affiancati), descritti senza copiarne i file:

- `source.json` dà repository e commit, e i runner li clonano a quel commit nel container;
- `expected.json` viene dai file del repository a quel commit ed è completo per unità, workspace, toolchain, framework, servizi ed esclusi;
- le dipendenze sono complete solo per al massimo tre unità piccole per repository (`unknown` con `known`);
- `connections` elenca i punti di contatto fra unità per il grafo unico, senza entrare nel punteggio.

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
