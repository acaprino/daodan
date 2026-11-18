# Codebase Map: che cosa supporta

Scritto da `plugins/codebase-map/skills/map/scripts/support_table.py` con i dati del prodotto e i risultati dei benchmark nel repository: non si modifica a mano, si riscrive con `python support_table.py build`, e `tests/test_codebase_map_support_table.py` fallisce se il file non è quello che lo script scrive.

Misure, ognuna con il suo file e la sua data:

- Esito: i casi del giro in cui l'analizzatore è finito `fresh` sui casi del giro che hanno il linguaggio.
- Copertura delle chiamate: i siti con una risposta sui siti del linguaggio (`benchmarks/project-model/README.md`, «Il grafo completo sul corpus»).
- File nell'indice: i file indicizzati sui file dello snapshot.
- Riconoscimento: le voci attese trovate sulle voci attese di `expected.json`.
- Il resto sono conteggi; dove non c'è misura la cella dice «non misurato».

## Linguaggi

17 linguaggi letti dallo snapshot con 63 estensioni (`scripts/languages/__init__.py`), 9 analizzatori (`scripts/indexers/`) e 7 osservatori del passo dinamico (`scripts/dynamic/`). Schede: aperte / buchi dichiarati / risolte del registro dei difetti ([2026-11-16-registro-difetti.md](../verification/2026-11-16-registro-difetti.md)) con quel linguaggio fra i tag.

| Linguaggio | Estensioni | Analizzatore | Osservatore | Schede |
| --- | --- | --- | --- | --- |
| Python | `.py` `.pyi` | scip-python | dynamic-record-python | 2 / 3 / 30 |
| Java | `.java` | scip-java | dynamic-record-jvm | 2 / 12 / 34 |
| JavaScript | `.js` `.mjs` `.cjs` `.jsx` | scip-typescript | dynamic-record-javascript | 0 / 4 / 30 |
| TypeScript | `.ts` `.tsx` `.mts` `.cts` | scip-typescript | dynamic-record-javascript | 1 / 1 / 24 |
| SQL | `.sql` `.ddl` `.dml` | nessuno | nessuno | 0 / 0 / 0 |
| PLSQL | `.pks` `.pkb` `.plsql` `.pls` `.pck` `.prc` `.fnc` `.trg` | nessuno | nessuno | 0 / 0 / 0 |
| Rust | `.rs` | scip-rust | dynamic-callgrind-rust | 0 / 3 / 16 |
| Go | `.go` | scip-go | dynamic-record-go | 1 / 2 / 13 |
| CSS | `.css` `.scss` `.sass` `.less` `.pcss` `.postcss` | stylesheet | nessuno | 1 / 1 / 2 |
| Kotlin | `.kt` `.kts` | scip-kotlin | dynamic-record-jvm | 3 / 8 / 27 |
| C# | `.cs` | scip-dotnet | dynamic-record-dotnet | 3 / 2 / 14 |
| Vue | `.vue` | stylesheet, scip-typescript | nessuno | 0 / 0 / 8 |
| Svelte | `.svelte` | stylesheet, scip-typescript | nessuno | 0 / 0 / 6 |
| Astro | `.astro` | stylesheet | nessuno | 0 / 0 / 0 |
| Markup | `.cshtml` `.ejs` `.erb` `.ftl` `.handlebars` `.hbs` `.htm` `.html` `.j2` `.jinja` `.jsp` `.jspx` `.liquid` `.mustache` `.njk` `.razor` `.twig` `.vm` `.xhtml` | stylesheet | nessuno | 0 / 0 / 0 |
| C | `.c` `.h` | scip-clang | dynamic-callgrind-clang | 0 / 8 / 29 |
| C++ | `.cc` `.cpp` `.cxx` `.hpp` `.hh` `.hxx` | scip-clang | dynamic-callgrind-clang | 1 / 6 / 30 |

Linguaggi che il registro nomina e lo snapshot non legge: dart (1 scheda), elixir (1 scheda), php (1 scheda), ruby (1 scheda), scala (4 schede), swift (1 scheda).

## Analizzatori e passo dinamico, misurati

Giro della pipeline del 16 novembre 2026 su 122 casi (`benchmarks/project-model/results/pipeline/2026-11-16-finale.report.json`; il passo dinamico da `benchmarks/project-model/results/pipeline/2026-11-16-finale.json`). Il linguaggio è quello del giro: `stylesheet` è il grafo dei fogli di stile, su CSS, markup, Vue e Svelte. Il registro dei difetti e il README del benchmark dicono che cosa è cambiato dopo il giro.

| Linguaggio | Analizzatore | Esito | Copertura delle chiamate | File nell'indice | Passo dinamico: casi osservati, siti |
| --- | --- | --- | --- | --- | --- |
| c | scip-clang | 6 / 9 (66,7 %) | 4.183 / 10.271 (40,7 %) | 49 / 72 (68,1 %) | 2 / 9 casi, 149 siti |
| cpp | scip-clang | 6 / 9 (66,7 %) | 2.364 / 2.651 (89,2 %) | 18 / 19 (94,7 %) | 0 / 9 casi, 0 siti |
| csharp | scip-dotnet | 4 / 5 (80,0 %) | 8.366 / 14.909 (56,1 %) | 561 / 561 (100,0 %) | nessun osservatore nel giro |
| go | scip-go | 14 / 15 (93,3 %) | 166.826 / 167.639 (99,5 %) | 678 / 679 (99,9 %) | 5 / 15 casi, 13.365 siti |
| java | scip-java | 16 / 18 (88,9 %) | 19.087 / 19.141 (99,7 %) | 261 / 278 (93,9 %) | 9 / 18 casi, 7.695 siti |
| javascript | scip-typescript | 31 / 32 (96,9 %) | 126.359 / 173.277 (72,9 %) | 1.254 / 1.254 (100,0 %) | 4 / 32 casi, 763 siti |
| kotlin | scip-kotlin | 4 / 11 (36,4 %) | 4.090 / 4.393 (93,1 %) | 103 / 115 (89,6 %) | 4 / 11 casi, 1.796 siti |
| python | scip-python | 34 / 34 (100,0 %) | 6.640 / 7.453 (89,1 %) | 185 / 185 (100,0 %) | 2 / 34 casi, 70 siti |
| rust | scip-rust | 13 / 13 (100,0 %) | 6.679 / 7.546 (88,5 %) | 145 / 154 (94,2 %) | 1 / 13 casi, 1 sito |
| stylesheet | stylesheet | 23 / 24 (95,8 %) | 17.663 / 67.251 (26,3 %) | 3.336 / 3.402 (98,1 %) | nessun osservatore nel giro |
| svelte | scip-typescript | 1 / 2 (50,0 %) | 4 / 15 (26,7 %) | 0 / 4 (0,0 %) | nessun osservatore nel giro |
| typescript | scip-typescript | 20 / 21 (95,2 %) | 246.275 / 272.308 (90,4 %) | 2.965 / 2.967 (99,9 %) | 3 / 21 casi, 73.230 siti |
| vue | scip-typescript | 2 / 2 (100,0 %) | 7.190 / 25.502 (28,2 %) | 0 / 410 (0,0 %) | nessun osservatore nel giro |

Nel giro senza analizzatore: plsql (1 caso, 1 file), sql (7 casi, 51 file).

## Build tool e toolchain

La pre-mappa ha 27 fonti (`scripts/premap/`, `SOURCES`); il grafo dei moduli legge 42 manifest di 30 ecosistemi (`scripts/build_units.py`); un modulo riceve 52 toolchain dal suo ecosistema o linguaggio (`scripts/module_derive.py`); la preparazione porta 11 toolchain nel container (`scripts/preparation.py`, `NEEDS`).

### Fonti della pre-mappa

Stati di ogni fonte nei casi del giro del 16 novembre 2026 (`benchmarks/project-model/results/pipeline/2026-11-16-finale.json`): `ran` ha girato, `not_needed` il caso non aveva i suoi file.

| Fonte | Versione | Modo | Modulo | Casi per stato |
| --- | --- | --- | --- | --- |
| `modules.py` | daodan/module-graph/v1 | lettore: legge i file | `premap/module_graph.py` | ran 122 |
| `python-build` | daodan/premap/v1 | lettore: legge i file | `premap/python_build.py` | not_needed 110, ran 12 |
| `requirements` | daodan/premap/v2 | lettore: legge i file | `premap/requirements.py` | not_needed 114, ran 8 |
| `python-tests` | daodan/premap/v1 | lettore: legge i file | `premap/python_tests.py` | not_needed 115, ran 7 |
| `npm-files` | daodan/premap/v1 | lettore: legge i file | `premap/npm_lock.py` | not_needed 86, ran 36 |
| `npm-tests` | daodan/premap/v6 | lettore: legge i file | `premap/npm_tests.py` | not_needed 113, ran 9 |
| `jvm-files` | daodan/premap/v3 | lettore: legge i file | `premap/jvm_files.py` | not_needed 100, ran 22 |
| `project-files` | daodan/premap/v2 | lettore: legge i file | `premap/project_files.py` | not_needed 115, ran 7 |
| `gitmodules` | daodan/premap/v1 | lettore: legge i file | `premap/gitmodules.py` | not_needed 120, ran 2 |
| `autotools` | daodan/premap/v1 | lettore: legge i file | `premap/autotools.py` | non misurato: non era nel giro |
| `go-enry` | v2.9.6 | scanner: legge ogni file | `premap/enry.py` | ran 122 |
| `renovate` | 44.239.1 | lettore: legge i file | `premap/renovate.py` | ran 122 |
| `compose` | 5.6.1 | modello: il comando del build tool, nel container | `premap/compose.py` | non misurato: non era nel giro |
| `buildkit` | v0.34.2 | modello: il comando del build tool, nel container | `premap/dockerfile.py` | non misurato: non era nel giro |
| `go` | 1.27.3 | modello: il comando del build tool, nel container | `premap/go.py` | not_needed 108, ran 14 |
| `cargo` | 1.99.1 | modello: il comando del build tool, nel container | `premap/cargo.py` | not_needed 109, ran 13 |
| `uv` | 0.11.28 | modello: il comando del build tool, nel container | `premap/uv.py` | not_needed 118, ran 4 |
| `tsc` | 6.0.3 | modello: il comando del build tool, nel container | `premap/tsc.py` | not_needed 105, ran 17 |
| `npm` | bundled with Node | modello: il comando del build tool, nel container | `premap/npm.py` | not_needed 86, ran 36 |
| `cmake` | 4.4.5 | modello: il comando del build tool, nel container | `premap/cmake.py` | not_needed 113, ran 9 |
| `meson` | 1.12.1 | modello: il comando del build tool, nel container | `premap/meson.py` | not_needed 120, ran 2 |
| `bazel` | 9.3.1 | modello: il comando del build tool, nel container | `premap/bazel.py` | not_needed 121, ran 1 |
| `make` | 4.3 | modello: il comando del build tool, nel container | `premap/make.py` | not_needed 115, ran 7 |
| `gradle` | 9.9.1 | modello: il comando del build tool, nel container | `premap/gradle.py` | not_needed 108, ran 14 |
| `maven` | 3.10.0 | modello: il comando del build tool, nel container | `premap/maven.py` | not_needed 113, ran 9 |
| `sbt` | 1.13.1 | modello: il comando del build tool, nel container | `premap/sbt.py` | not_needed 121, ran 1 |
| `dotnet` | 10.0.404 | modello: il comando del build tool, nel container | `premap/dotnet.py` | not_needed 117, ran 5 |

### Pre-mappa per faccia

Dallo stesso giro (`benchmarks/project-model/results/pipeline/2026-11-16-finale.report.json`, `premap`): ogni faccia contro `expected.json` dei casi che la danno.

| Faccia | Riconoscimento | In più | Sbagliati |
| --- | --- | --- | --- |
| `languages` | 307 / 313 (98,1 %) | 279 | 0 |
| `excluded` | 377 / 463 (81,4 %) | 210 | 16 |
| `units` | 344 / 447 (77,0 %) | 3 | 8 |
| `units.depends_on` | 131 / 210 (62,4 %) | 0 | 0 |
| `units.source_roots` | 147 / 328 (44,8 %) | 96 | 0 |
| `units.config` | 171 / 726 (23,6 %) | 0 | 50 |
| `workspace` | 25 / 33 (75,8 %) | 21 | 2 |
| `workspace.members` | 107 / 111 (96,4 %) | 3 | 0 |
| `toolchains` | 168 / 381 (44,1 %) | 117 | 22 |
| `services` | 1 / 10 (10,0 %) | 0 | 0 |

### Manifest di build

Riconoscimento per ecosistema: non misurato (il giro misura le unità tutte insieme, faccia `units`).

| Ecosistema | Manifest |
| --- | --- |
| angular | `angular.json` |
| buf | `buf.yaml` |
| bundler | `Gemfile` |
| cabal | `*.cabal` |
| cargo | `Cargo.toml` |
| cmake | `CMakeLists.txt` |
| composer | `composer.json` |
| daodan | `plugin.toml` |
| deno | `deno.json` `deno.jsonc` |
| dotnet | `*.csproj` `*.fsproj` `*.sln` `*.slnx` `*.vbproj` |
| dune | `dune-project` |
| go | `go.mod` `go.work` |
| gradle | `build.gradle` `build.gradle.kts` `settings.gradle` `settings.gradle.kts` |
| julia | `Project.toml` |
| lerna | `lerna.json` |
| maven | `pom.xml` |
| melos | `melos.yaml` |
| mix | `mix.exs` |
| msbuild | `*.vcproj` `*.vcxproj` |
| npm | `package.json` |
| nx | `project.json` |
| pnpm | `pnpm-workspace.yaml` |
| pub | `pubspec.yaml` |
| python | `pyproject.toml` `setup.cfg` `setup.py` |
| rubygems | `*.gemspec` |
| sbt | `build.sbt` |
| stack | `stack.yaml` |
| swiftpm | `Package.swift` |
| terraform | `*.tf` |
| zig | `build.zig.zon` |

### Toolchain

Riconosciute: `android-build-tools` `android-sdk` `autotools` `bazel` `buf` `bun` `bundler` `c` `c#` `c++` `cabal` `cargo` `cmake` `composer` `dart` `deno` `dotnet` `dotnet-target` `dune` `elixir` `ghc` `go` `gradle` `java` `julia` `kotlin` `make` `maven` `melos` `meson` `mix` `msbuild` `node` `npm` `nx` `ocaml` `php` `pnpm` `pub` `python` `ruby` `rubygems` `rust` `sbt` `scala` `stack` `swift` `terraform` `typescript` `uv` `yarn` `zig`.

| Toolchain della preparazione | Versione |
| --- | --- |
| arm-none-eabi | 15.2.rel1 |
| cmdline-tools | 15859902 |
| conan | 2.34.0 |
| dotnet | 10.0.404 |
| git | debian |
| go | 1.27.3 |
| node | 24.22.3 |
| poetry | 2.1.3 |
| rust | 1.99.1 |
| uv | 0.11.28 |
| vcpkg | 2026-10-29 |

## Framework, librerie e strumenti

Lo step `stack` (`scripts/technologies.py`) dà a ogni unità `frameworks`, `libraries`, `services` e `tools`. La classe di una voce del catalogo (`data/service-registry.json`) la decide `service_registry.entry_category`: la `category` della voce se c'è, altrimenti `service` per una voce `service` e `framework` per ogni altra. Le `libraries` sono tutti i pacchetti che l'unità dichiara, nel catalogo o no: il catalogo non ha voci di classe `library`.

| Classe | Voci riconoscibili (con segni) | Voci con la categoria scritta, fra tutte |
| --- | --- | --- |
| framework | 313 | 68 |
| tool | 23 | 26 |
| service | 491 | 2 |
| library | 0 | 0 |

Il catalogo non distingue un framework da una libreria: delle 332 voci `project` riconoscibili, 245 sono `framework` solo per il default, senza una `category` scritta. Per distinguerli servirebbe una `category` (`framework`, `library` o `tool`) su ogni voce `project` con segni.

Riconoscimento dello stack sul corpus, giro del 17 novembre 2026 (`benchmarks/project-model/results/daodan_stack.json`), 178 fixture su 180 con record; per nome conta un nome una volta per fixture, per unità ogni unità che lo tiene.

| Famiglia | Fixture | Framework per nome | Framework per unità | Servizi |
| --- | --- | --- | --- | --- |
| js | 20 | 10 / 10 (100,0 %) | 11 / 11 (100,0 %), 0 sbagliati | 1 / 1 (100,0 %), 0 in più |
| py | 21 | 4 / 4 (100,0 %) | 4 / 4 (100,0 %), 0 sbagliati | 2 / 3 (66,7 %), 0 in più |
| jvm | 34 | 36 / 42 (85,7 %) | 37 / 43 (86,0 %), 0 sbagliati | 1 / 2 (50,0 %), 0 in più |
| sys | 25 | 2 / 2 (100,0 %) | 1 / 2 (50,0 %), 1 sbagliato | nessuno atteso, 0 in più |
| mix | 30 | 29 / 31 (93,5 %) | 32 / 37 (86,5 %), 0 sbagliati | 11 / 33 (33,3 %), 1 in più |
| real | 10 | 99 / 127 (78,0 %) | 177 / 251 (70,5 %), 12 sbagliati | 29 / 84 (34,5 %), 8 in più |
| stack | 38 | 182 / 352 (51,7 %) | 290 / 653 (44,4 %), 37 sbagliati | 93 / 395 (23,5 %), 53 in più |
| tutte | 178 | 362 / 568 (63,7 %) | 552 / 1.001 (55,1 %), 50 sbagliati | 137 / 518 (26,4 %), 62 in più |

<details><summary>Framework e strumenti riconoscibili: 336 voci</summary>

| Voce | Id | Classe | Segni | Fixture in cui lo step la trova (17 novembre 2026) |
| --- | --- | --- | --- | --- |
| .NET Aspire | `dotnet-aspire` | framework | nuget | 3 |
| .NET MAUI | `dotnet-maui` | framework | nuget | 1 |
| Actix Web | `actixweb` | framework | crates | 2 |
| AdonisJS | `adonisjs` | framework | npm | 0 |
| aiohttp | `aiohttp` | framework | pypi | 1 |
| Alembic | `alembic` | framework | pypi | 3 |
| Alpine.js | `alpinejs` | framework | npm | 2 |
| Android | `android` | framework | maven | 5 |
| Angular | `angular` | framework | npm, files | 4 |
| AngularJS | `angularjs` | framework | npm | 0 |
| Ansible | `ansible` | framework | docker, github-actions, pypi | 0 |
| Ant Design | `antd` | framework | npm | 1 |
| Ant Design Icons | `antdicons` | framework | npm | 1 |
| Apache Beam | `apache-beam` | framework | go, pypi | 0 |
| Apache Thrift | `apache_thrift` | framework | crates, docker, go, npm, rubygems | 0 |
| Api Platform | `apiplatform` | framework | composer, npm | 0 |
| Apollo Server | `apollo-server` | framework | npm | 1 |
| ArchUnit | `archunit` | framework | maven | 1 |
| AriaKit UI | `ariakitui` | framework | npm | 0 |
| Ark UI | `arkui` | framework | npm | 0 |
| ArkType | `arktype` | framework | npm | 0 |
| asdf | `asdf` | framework | files | 0 |
| ASP.NET Core | `aspnetcore` | framework | nuget | 6 |
| Assemble | `assemble` | framework | npm | 0 |
| Astro | `astro` | framework | npm, files | 1 |
| AtlasGo | `atlasgo` | framework | docker, github-actions, terraform, files | 0 |
| AWS CDK | `awscdk` | framework | go, npm, pypi | 0 |
| AWS CloudFormation | `aws.cloudformation` | framework | crates, github-actions, go, npm, pypi, rubygems, terraform-resource | 0 |
| Axum | `axum` | framework | crates | 3 |
| Base UI | `baseui` | framework | npm | 0 |
| Biome JS | `biomejs` | framework | npm, files | 4 |
| Blazor | `blazor` | framework | nuget | 1 |
| Blitzjs | `blitzjs` | framework | npm | 0 |
| Bootstrap | `bootstrap` | framework | npm | 5 |
| Bootstrap Icons | `bootstrapicons` | framework | npm | 1 |
| Boto3 | `boto3` | framework | pypi | 4 |
| Bun | `bunsh` | framework | files | 0 |
| Bundler | `bundler` | framework | rubygems | 0 |
| Bytebase | `bytebase` | framework | docker, github-actions | 0 |
| Capacitor | `capacitorjs` | framework | npm, files | 1 |
| Cats | `cats` | framework | maven | 1 |
| Chakra UI | `chakraui` | framework | npm | 0 |
| Chef | `chef` | framework | docker | 0 |
| Chi | `chi` | framework | go | 4 |
| Click | `click` | framework | pypi | 8 |
| Cobra | `cobra` | framework | go | 2 |
| CodeMirror | `codemirror` | framework | npm | 8 |
| Compose Multiplatform | `compose-multiplatform` | framework | maven | 2 |
| containerd | `containerd` | framework | go | 0 |
| Cordova | `apacheCordova` | framework | npm | 0 |
| CypressCI | `cypressci` | framework | docker, github-actions, npm, rubygems, files | 3 |
| D3.js | `d3js` | framework | npm | 1 |
| daisyUI | `daisyui` | framework | npm | 1 |
| Dask | `dask` | framework | pypi | 0 |
| dbt | `dbt` | framework | pypi | 0 |
| Deno | `deno` | framework | docker, github-actions, files | 1 |
| Diesel | `dieselrs` | framework | crates | 0 |
| Dioxus | `dioxus` | framework | crates | 0 |
| Django | `django` | framework | pypi | 7 |
| Docsify | `docsify` | framework | npm | 0 |
| Doctrine | `doctrinephp` | framework | composer | 2 |
| Docusaurus | `docusaurus` | framework | npm, files | 1 |
| Drizzle ORM | `drizzleorm` | framework | npm | 0 |
| Duende IdentityServer | `duende-identityserver` | framework | nuget | 1 |
| Echo | `echo` | framework | go | 1 |
| EffectJS | `effectjs` | framework | npm | 0 |
| Electron | `electron` | framework | github-actions, npm | 1 |
| Eleventy | `eleventy` | framework | github-actions, npm, files | 0 |
| ElysiaJS | `elysiajs` | framework | npm | 0 |
| Ember | `emberjs` | framework | npm, files | 0 |
| ent. | `goent` | framework | go | 0 |
| Entity Framework Core | `entity-framework-core` | framework | nuget | 5 |
| Envoy | `envoy` | framework | go | 0 |
| etcd | `etcd` | framework | go | 0 |
| ExpoJS | `expojs` | framework | npm | 3 |
| Exposed | `exposed` | framework | maven | 1 |
| Express | `express` | framework | npm | 9 |
| FastAPI | `fastapi` | framework | pypi | 6 |
| Fastify | `fastify` | framework | npm | 0 |
| FastMCP | `fastmcp` | framework | pypi | 1 |
| Feather Icons | `feathericons` | framework | npm | 0 |
| Fern | `builtwithfern` | framework | files | 0 |
| Flask | `flask` | framework | pypi | 5 |
| Fluent UI | `fluentui` | framework | npm | 0 |
| Fluentd | `fluentd` | framework | go | 0 |
| Flutter | `flutter` | framework | pub | 2 |
| Flyway | `flyway` | framework | docker, github-actions | 0 |
| Font Awesome | `fontawesome` | framework | npm | 2 |
| FoundationDB | `foundationdb` | framework | pypi | 0 |
| FumaDocs | `fumadocs` | framework | npm | 1 |
| Gatling | `gatling` | framework | maven | 1 |
| Gatsby | `gatsby` | framework | github-actions, npm, files | 0 |
| Gin | `gin` | framework | go | 1 |
| Gitlab | `gitlab` | framework | composer, crates, npm, pypi, rubygems, terraform, terraform-resource | 0 |
| goenv | `goenv` | framework | files | 0 |
| GolangCI Lint | `golangcilint` | framework | docker, github-actions, go, files | 3 |
| GORM | `gorm` | framework | go | 2 |
| Gradio | `gradio` | framework | pypi | 1 |
| Grafana K6 | `k6` | framework | docker, go, npm | 0 |
| Gridsome | `gridsome` | framework | npm, files | 0 |
| gRPC | `grpc` | framework | go, maven, npm, nuget, pypi | 5 |
| Gunicorn | `gunicorn` | framework | pypi | 6 |
| Headless UI | `headlessui` | framework | npm | 1 |
| Hero UI | `heroui` | framework | npm | 0 |
| Heroicons | `heroicons` | framework | npm | 2 |
| HexoJS | `hexojs` | framework | npm | 0 |
| Hibernate | `hibernate` | framework | maven | 1 |
| Honeycomb | `honeycomb` | framework | go, pypi | 0 |
| HonoJS | `honojs` | framework | npm | 2 |
| HTMX | `htmx` | framework | npm | 3 |
| HTTPX | `httpx` | framework | pypi | 4 |
| HugeIcons | `hugeicons` | framework | npm | 0 |
| Hugo | `hugo` | framework | docker, github-actions, npm, files | 1 |
| Inferno | `infernojs` | framework | npm | 0 |
| Ionic | `ionic` | framework | npm | 0 |
| Ionicons | `ionicons` | framework | npm | 0 |
| Jackson | `jackson` | framework | maven | 4 |
| Jaeger | `jaeger` | framework | go | 0 |
| Jekyll | `jekyll` | framework | github-actions, rubygems, files | 0 |
| Jest | `jest` | framework | npm, files | 9 |
| Jinja | `jinja` | framework | pypi | 6 |
| Joi | `joijs` | framework | npm | 0 |
| JSON Schema | `jsonschema` | framework | composer, crates, go, npm, pypi, rubygems | 5 |
| JUnit | `junit` | framework | maven | 22 |
| JUnit Jupiter | `junit-jupiter` | framework | maven | 7 |
| Jupyter | `jupyter` | framework | pypi | 0 |
| Kafka | `kafka` | framework | maven, nuget | 1 |
| Keras | `keras` | framework | pypi | 0 |
| Keycloak | `keycloak` | framework | npm, pypi | 0 |
| Knex | `knex` | framework | npm | 0 |
| Koa | `koa` | framework | npm | 0 |
| Koin | `koin` | framework | maven | 2 |
| Kotlin Multiplatform | `kotlin-multiplatform` | framework | maven | 3 |
| kotlinx.serialization | `kotlinx-serialization` | framework | maven | 2 |
| Ktor | `ktor` | framework | maven | 2 |
| Kysely | `kysely` | framework | npm | 1 |
| LangChain | `langchain` | framework | npm, pypi | 1 |
| Laravel | `laravel` | framework | composer, files | 3 |
| Lego | `goacmelego` | framework | docker, go, files | 0 |
| Lexical Editor | `lexicaleditor` | framework | npm | 0 |
| Lighthouse | `lighthouse` | framework | docker, github-actions, npm | 1 |
| Liquibase | `liquibase` | framework | docker, github-actions, maven | 1 |
| Lit | `litjs` | framework | npm | 0 |
| LlamaIndex | `llamaindex` | framework | pypi | 0 |
| Locust | `locust` | framework | pypi | 2 |
| Lombok | `lombok` | framework | maven | 2 |
| Lord Icon | `lordicon` | framework | npm | 0 |
| Lucide Icons | `lucideicons` | framework | npm | 7 |
| Mailhog | `mailhog` | framework | docker, go | 1 |
| Mantine UI | `mantineui` | framework | npm | 0 |
| MapStruct | `mapstruct` | framework | maven | 3 |
| Material Design Icons | `materialdesignicons` | framework | npm | 0 |
| Material UI | `materialui` | framework | npm | 0 |
| Matplotlib | `matplotlib` | framework | pypi | 1 |
| MCP | `mcp` | framework | npm, pypi, rubygems | 2 |
| Meteor | `meteorjs` | framework | npm, files | 0 |
| Micronaut | `micronaut` | framework | maven | 0 |
| Mintlify | `mintlify` | framework | npm, files | 0 |
| Mithril | `mithriljs` | framework | npm | 0 |
| MkDocs | `mkdocs` | framework | docker, pypi, files | 2 |
| Mlflow | `mlflow` | framework | pypi | 0 |
| Mocha | `mochajs` | framework | npm, files | 1 |
| Mockito | `mockito` | framework | maven | 2 |
| Monaco Editor | `monacoeditor` | framework | npm | 1 |
| MSTest | `mstest` | framework | nuget | 1 |
| MUI Icons | `muiicons` | framework | npm | 0 |
| NestJS | `nestjs` | framework | npm, files | 2 |
| Next.js | `nextjs` | framework | npm, files | 5 |
| Nomad | `nomad` | framework | go | 0 |
| NuGet | `nuget` | framework | files | 0 |
| NumPy | `numpy` | framework | pypi | 3 |
| NUnit | `nunit` | framework | nuget | 1 |
| Nuxt.js | `nuxtjs` | framework | npm, files | 2 |
| nvm | `nvm` | framework | files | 0 |
| NX | `nxjs` | framework | npm, files | 1 |
| OpenAPI | `openapi` | framework | composer, crates, go, npm, pypi, rubygems, files | 10 |
| OpenCV | `opencv` | framework | crates, go, pypi | 0 |
| OpenSearch | `opensearch` | framework | go, pypi | 0 |
| OpenTelemetry | `opentelemetry` | framework | composer, crates, docker, github-actions, go, npm, pypi, rubygems, env | 3 |
| OxLint | `oxlint` | framework | npm, pypi, files | 1 |
| pandas | `pandas` | framework | pypi | 2 |
| Parcel | `parceljs` | framework | npm | 0 |
| Passport | `passport` | framework | npm | 2 |
| Phaser | `phaserjs` | framework | npm | 0 |
| Phoenix | `phoenix` | framework | hex | 3 |
| Phoenix LiveView | `phoenix-liveview` | framework | hex | 3 |
| Phosphor Icons | `phosphoreicons` | framework | npm | 0 |
| PHP | `php` | framework | docker, github-actions, files | 7 |
| PHP Pest | `phppest` | framework | composer | 0 |
| phpenv | `phpenv` | framework | files | 0 |
| PHPUnit | `phpunit` | framework | composer, files | 5 |
| picocli | `picocli` | framework | maven | 1 |
| Pillow | `pillow` | framework | pypi | 5 |
| pip | `pip` | framework | pypi | 0 |
| pipenv | `pipenv` | framework | files | 0 |
| Playwright | `playwright` | framework | docker, github-actions, maven, npm, nuget, pypi, files | 12 |
| Plotly | `plotly` | framework | pypi | 0 |
| Podman | `podman` | framework | go | 0 |
| Poetry | `poetry` | framework | files | 0 |
| Polars | `polars` | framework | crates, pypi | 0 |
| Preact | `preactjs` | framework | npm | 1 |
| Prisma | `prisma` | framework | npm, files | 4 |
| Protocol Buffers | `protobuf` | framework | crates, go, pypi | 7 |
| Pulumi | `pulumi` | framework | go, npm, pypi, files | 0 |
| Pydantic | `pydantic` | framework | pypi | 6 |
| pytest | `pytest` | framework | pypi | 9 |
| Pytorch | `pytorch` | framework | pypi | 0 |
| Quarkus | `quarkus` | framework | maven | 1 |
| Qwik | `qwikjs` | framework | npm | 0 |
| Radix Icons | `radixicons` | framework | npm | 0 |
| Radix UI | `radixui` | framework | npm | 3 |
| Ray | `ray` | framework | pypi | 0 |
| React | `react` | framework | npm | 18 |
| React Email | `react-email` | framework | npm | 3 |
| React Email | `reactemail` | framework | npm | 2 |
| React Icons | `reacticons` | framework | npm | 2 |
| React Native | `react-native` | framework | npm | 3 |
| React Router | `reactrouterdom` | framework | npm | 7 |
| Read The Docs | `readthedocs` | framework | docker, files | 0 |
| RedwoodJs | `redwoodjs` | framework | npm, files | 0 |
| Refine | `refinedev` | framework | npm | 0 |
| Reka UI | `rekaui` | framework | npm | 0 |
| Remix | `remixrun` | framework | npm | 0 |
| Remix Icons | `remixicons` | framework | npm | 0 |
| Remix Router | `remixrouter` | framework | npm | 0 |
| Remult | `remult` | framework | npm | 0 |
| Requests | `requests` | framework | pypi | 9 |
| Resilience4j | `resilience4j` | framework | maven | 1 |
| Rolldown | `rolldown` | framework | crates, npm | 1 |
| Rspack | `rspack` | framework | npm, files | 0 |
| Ruby | `ruby` | framework | docker, github-actions, files | 7 |
| Ruby on Rails | `rails` | framework | npm, rubygems | 3 |
| rubyenv | `rubyenv` | framework | files | 0 |
| Sandpack | `sandpackeditor` | framework | npm | 0 |
| ScalaTest | `scalatest` | framework | maven | 1 |
| scikit-learn | `scikitlearn` | framework | pypi | 1 |
| SciPy | `scipy` | framework | pypi | 0 |
| Scrapy | `scrapy` | framework | pypi | 0 |
| Sequel | `sequelruby` | framework | rubygems | 0 |
| Sequelize | `sequelize` | framework | npm, files | 1 |
| Serde | `serde` | framework | crates | 8 |
| Shadcn | `shadcn` | framework | npm | 0 |
| Shopify Hydrogen | `shopify.hydrogen` | framework | npm | 0 |
| Sidekiq | `sidekiq` | framework | rubygems | 2 |
| Simple Icons | `simpleicons` | framework | npm | 0 |
| Sinatra | `sinatra` | framework | rubygems | 1 |
| Slate | `slatedocs` | framework | docker | 0 |
| Slim | `slim` | framework | composer | 1 |
| Socket.io | `socketio` | framework | npm, pypi | 2 |
| Solid js | `solidjs` | framework | npm | 0 |
| SonarLint | `sonarlint` | framework | files | 0 |
| spaCy | `spacy` | framework | pypi | 0 |
| Sphinx | `sphinx` | framework | pypi | 2 |
| Spring AI | `spring-ai` | framework | maven | 0 |
| Spring Boot | `spring-boot` | framework | maven | 7 |
| Spring Boot Admin | `spring-boot-admin` | framework | maven | 1 |
| Spring Cloud Config | `spring-cloud-config` | framework | maven | 1 |
| Spring Cloud Gateway | `spring-cloud-gateway` | framework | maven | 0 |
| Spring Cloud Netflix | `spring-cloud-netflix` | framework | maven | 1 |
| Spring Data JPA | `spring-data-jpa` | framework | maven | 5 |
| Spring MVC | `spring-mvc` | framework | maven | 6 |
| Spring Security | `spring-security` | framework | maven | 2 |
| Spring WebFlux | `spring-webflux` | framework | maven | 0 |
| SQLAlchemy | `sqlalchemy` | framework | pypi | 3 |
| SQLModel | `sqlmodel` | framework | pypi | 1 |
| Stencil | `stenciljs` | framework | npm | 0 |
| Storybook | `storybook` | framework | npm, files | 2 |
| Streamlit | `streamlit` | framework | pypi | 0 |
| Superstruct | `superstruct` | framework | npm | 0 |
| Svelte | `sveltejs` | framework | npm, files | 2 |
| SvelteKit | `sveltekit` | framework | npm | 1 |
| SWC | `swc` | framework | crates, npm | 4 |
| Symfony | `symfony` | framework | composer | 0 |
| Tabler | `tablericons` | framework | npm | 1 |
| Tailwind | `tailwind` | framework | npm, files | 12 |
| TanStack Router | `tanstackrouter` | framework | npm | 1 |
| Tanstack Start | `tanstackstart` | framework | npm | 0 |
| Tauri | `tauri` | framework | crates, npm, files | 3 |
| Tensorflow | `tensorflow` | framework | crates, docker, go, npm, pypi | 0 |
| Terragrunt | `terragrunt` | framework | files | 0 |
| Testcontainers | `testcontainers` | framework | maven, nuget, pypi | 2 |
| Testing Library | `testinglibrary` | framework | npm | 11 |
| TestNG | `testng` | framework | maven | 1 |
| Thymeleaf | `thymeleaf` | framework | maven | 3 |
| Tiptap | `tiptap` | framework | npm | 3 |
| Tokio | `tokio` | framework | crates | 4 |
| Trino | `trino` | framework | pypi | 0 |
| TRPC | `trpc` | framework | npm | 1 |
| Turborepo | `turborepo` | framework | npm, files | 2 |
| Twig | `twigphp` | framework | composer | 1 |
| TypeBox | `typebox` | framework | npm | 0 |
| TypeORM | `typeorm` | framework | npm | 1 |
| Typer | `typer` | framework | pypi | 2 |
| Typescript | `typescript` | framework | go, npm, files | 35 |
| Ultracite | `ultracite` | framework | npm | 0 |
| UmiJS | `umijs` | framework | npm, files | 0 |
| urql | `urql` | framework | npm | 1 |
| uv | `uv` | framework | pypi | 1 |
| Vale | `vale` | framework | docker, github-actions, files | 1 |
| Valibot | `valibot` | framework | npm | 0 |
| Viper | `viper` | framework | go | 3 |
| VitePress | `vitepress` | framework | npm, files | 1 |
| Vitest | `vitest` | framework | npm, files | 11 |
| Vue Router | `vue-router` | framework | npm | 2 |
| Vue.js | `vue` | framework | npm | 8 |
| VuePress | `vuepress` | framework | npm, files | 0 |
| Wasp | `wasp` | framework | files | 0 |
| Weaviate | `weaviate` | framework | go, pypi | 0 |
| xUnit | `xunit` | framework | nuget | 2 |
| YARP | `yarp` | framework | nuget | 0 |
| Yii2 | `yii2` | framework | composer | 0 |
| Zig | `zig` | framework | github-actions | 0 |
| Zod | `zod` | framework | npm | 7 |
| Babel | `babel` | tool | npm | 8 |
| Docker | `docker` | tool | github-actions, go, npm, pypi, files | 40 |
| Esbuild | `esbuild` | tool | go, npm | 5 |
| Eslint | `eslint` | tool | npm, files | 23 |
| Golang | `golang` | tool | docker, files | 20 |
| Helm | `helm` | tool | github-actions, go, rubygems, terraform, files | 4 |
| NodeJS | `nodejs` | tool | docker, files | 61 |
| npm | `npm` | tool | files | 0 |
| PHPStan | `phpstan` | tool | composer, files | 2 |
| pnpm | `pnpm` | tool | files | 0 |
| Prettier | `prettier` | tool | npm, files | 14 |
| Python | `python` | tool | docker, github-actions, files | 16 |
| Renovate | `renovate` | tool | npm, files | 6 |
| Rollup | `rollup` | tool | npm | 4 |
| Rubocop | `rubocop` | tool | files | 1 |
| Ruff | `ruff` | tool | pypi | 14 |
| Rust | `rust` | tool | docker, files | 17 |
| Stylelint | `stylelint` | tool | files | 2 |
| Terraform | `terraform` | tool | github-actions, go, npm, pypi, files | 2 |
| TravisCI | `travisci` | tool | rubygems, files | 1 |
| Vite | `vite` | tool | npm | 18 |
| Webpack | `webpack` | tool | npm | 3 |
| Yarn | `yarn` | tool | files | 0 |

</details>

## Servizi esterni

Le voci `service` del catalogo: 625, 495 con segni per riconoscerle, 227 con un marchio (`icon`). Segni per specie, sulle voci che ne hanno: `env` 160, `files` 48, `packages` 457, `patterns` 159. Di quelle con segni, 4 hanno la categoria `framework` o `tool` e stanno nella lista della sezione precedente. Il riconoscimento misurato è la colonna Servizi della sezione precedente.

| Tipo | Voci | Con segni | Con marchio |
| --- | --- | --- | --- |
| servizio o API | 469 | 347 | 175 |
| database | 111 | 103 | 32 |
| autenticazione | 16 | 16 | 6 |
| gateway | 15 | 15 | 10 |
| coda | 14 | 14 | 4 |

<details><summary>Servizi riconoscibili: 491 voci</summary>

| Servizio | Id | Tipo | Segni | Marchio | Fixture in cui lo step lo trova (17 novembre 2026) |
| --- | --- | --- | --- | --- | --- |
| Adminer | `adminer` | servizio o API | docker | sì | 2 |
| Adobe Analytics | `adobe.analytics` | servizio o API | npm, env | no | 0 |
| Adobe Experience Manager | `adobe.experiencemanager` | servizio o API | npm, env | no | 0 |
| Adyen | `adyen` | gateway | composer, npm, pypi, rubygems, env | sì | 0 |
| Airbyte | `airbyte` | servizio o API | docker, terraform | sì | 0 |
| Aircall | `aircall` | servizio o API | npm, terraform-resource, env | sì | 0 |
| Airtable | `airtable` | servizio o API | composer, npm, env | sì | 0 |
| Akamai | `akamai` | servizio o API | npm, terraform, env | sì | 0 |
| Algolia | `algolia` | database | composer, crates, github-actions, npm, pypi, rubygems, terraform-resource, env | sì | 1 |
| Alibaba Cloud | `alibabacloud` | servizio o API | composer, github-actions, terraform | sì | 0 |
| Amplitude Analytics | `amplitude` | servizio o API | composer, go, npm, terraform-resource, env | no | 0 |
| Anthropic | `anthropic` | servizio o API | go, npm, pypi, env | sì | 0 |
| Apache Airflow | `apache_airflow` | servizio o API | docker | sì | 0 |
| Apache Cassandra | `apache_cassandra` | database | crates, docker, npm, pypi | sì | 0 |
| Apache CouchDB | `apache_couchdb` | database | composer, docker | sì | 0 |
| Apache Flink | `apache_flink` | servizio o API | docker, pypi | sì | 0 |
| Apache Hadoop | `apache_hadoop` | database | docker, rubygems | sì | 0 |
| Apache Hive | `apache_hive` | database | docker | sì | 0 |
| Apache Iceberg | `apache_iceberg` | database | docker | no | 0 |
| Apache Kafka | `apache_kafka` | coda | composer, docker, npm, rubygems, terraform | sì | 1 |
| Apache Pulsar | `apache-pulsar` | coda | pypi | sì | 0 |
| Apache Solr | `apache_solr` | database | docker | sì | 0 |
| Apache Spark | `apache_spark` | database | docker, pypi | sì | 0 |
| Apache Storm | `apache_storm` | servizio o API | docker | sì | 0 |
| Apideck | `apideck` | servizio o API | composer, go, npm, pypi | no | 0 |
| Apify | `apify` | servizio o API | crates, go, npm, pypi, terraform-resource, env | no | 0 |
| Apple | `apple` | servizio o API | env | sì | 0 |
| AppSignal | `appsignal` | servizio o API | docker, npm, pypi, rubygems | sì | 0 |
| AppVeyor | `appveyor` | servizio o API | files | sì | 0 |
| Asana | `asana` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource, env | sì | 0 |
| Atlassian | `atlassian` | servizio o API | pypi | sì | 0 |
| Atlassian Bitbucket | `atlassian.bitbucket` | servizio o API | composer | no | 0 |
| Atlassian OpsGenie | `atlassian.opsgenie` | servizio o API | npm, pypi | no | 0 |
| Atlassian Trello | `atlassian.trello` | servizio o API | composer, github-actions, npm, rubygems | no | 0 |
| Auth0 | `auth0` | autenticazione | composer, crates, go, npm, pypi, rubygems, terraform, env | sì | 0 |
| AWS | `aws` | servizio o API | composer, crates, docker, github-actions, go, npm, rubygems, terraform | no | 8 |
| AWS ActiveMQ | `aws.mq` | coda | crates, go, npm, rubygems, terraform-resource | no | 0 |
| AWS Amplify Hosting | `aws.amplifyhosting` | servizio o API | npm, terraform-resource | no | 0 |
| AWS Api Gateway | `aws.apigateway` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Athena | `aws.athena` | database | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Bedrock | `aws.bedrock` | servizio o API | npm | no | 0 |
| AWS Block Storage | `aws.ebs` | database | crates, go, npm, rubygems, terraform-resource | no | 0 |
| AWS CloudFront | `aws.cloudfront` | database | composer, crates, github-actions, go, npm, pypi, rubygems, terraform-resource, env | no | 0 |
| AWS Cloudsearch | `aws.cloudsearch` | database | crates, go, npm, rubygems, terraform-resource | no | 0 |
| AWS Cloudwatch | `aws.cloudwatch` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Code Build | `aws.codebuild` | servizio o API | crates, github-actions, go, npm, rubygems, terraform-resource | no | 0 |
| AWS Code Pipeline | `aws.codepipeline` | servizio o API | github-actions | no | 0 |
| AWS Cognito | `aws.cognito` | autenticazione | go, npm, rubygems | no | 0 |
| AWS Comprehend | `aws.comprehend` | servizio o API | npm | no | 0 |
| AWS Compute | `aws.ec2` | servizio o API | crates, github-actions, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Container | `aws.ecs` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Container Registry | `aws.ecr` | database | crates, github-actions, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Document DB | `aws.documentdb` | database | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS DynamoDB | `aws.dynamodb` | database | composer, crates, docker, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS ElastiCache | `aws.elasticache` | database | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Fargate | `aws.fargate` | servizio o API | github-actions | no | 0 |
| AWS File System | `aws.efs` | database | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Glacier | `aws.glacier` | database | crates, go, npm, rubygems, terraform-resource | no | 0 |
| AWS Glue | `aws.glue` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Kafka | `aws.kafka` | coda | npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Kinesis | `aws.kinesis` | coda | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Kms | `aws.kms` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Kubernetes | `aws.eks` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Lambda | `aws.lambda` | servizio o API | composer, crates, docker, github-actions, go, npm, rubygems, terraform-resource | no | 0 |
| AWS Lightsail | `aws.lightsail` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS MemoryDB | `aws.memorydb` | database | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Neptune | `aws.neptune` | database | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Notification Service | `aws.sns` | servizio o API | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Opensearch | `aws.opensearch` | database | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Polly | `aws.polly` | servizio o API | crates, go, npm, rubygems | no | 0 |
| AWS RDS | `aws.rds` | database | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Redshift | `aws.redshift` | database | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Rekognition | `aws.rekognition` | servizio o API | crates, go, npm, pypi, rubygems | no | 0 |
| AWS S3 | `aws.s3` | database | composer, crates, docker, github-actions, go, npm, rubygems, terraform-resource | no | 9 |
| AWS SageMaker | `aws.sagemaker` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Secrets Manager | `aws.secretsmanager` | database | crates, go, npm, pypi, rubygems, terraform-resource | no | 1 |
| AWS Simple Email Service | `aws.ses` | servizio o API | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS SQS | `aws.sqs` | coda | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Step Functions | `aws.sfn` | servizio o API | crates, go, npm, rubygems, terraform-resource | no | 0 |
| AWS Timestream | `aws.timestream` | database | crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| AWS Transcribe | `aws.transcribe` | servizio o API | npm | no | 0 |
| AWS Translate | `aws.translate` | servizio o API | crates, go, npm, rubygems | no | 0 |
| Azure | `azure` | servizio o API | crates, docker, github-actions, go, npm, pypi, rubygems, terraform | no | 1 |
| Azure Cosmos DB | `azure.cosmosdb` | database | crates, go, npm, rubygems, terraform-resource | no | 0 |
| Azure Functions | `azure.functions` | servizio o API | crates, github-actions, npm, rubygems, terraform-resource | no | 0 |
| Azure Kubernetes | `azure.aks` | servizio o API | terraform-resource | no | 0 |
| Azure MariaDB | `azure.mariadb` | database | crates, go, npm, rubygems, terraform-resource | no | 0 |
| Azure MySQL | `azure.mysql` | database | crates, github-actions, go, npm, rubygems, terraform-resource | no | 0 |
| Azure Openai | `azure.openai` | servizio o API | npm | no | 0 |
| Azure Postgres | `azure.postgres` | database | crates, github-actions, go, npm, rubygems, terraform-resource | no | 0 |
| Azure Redis | `azure.redis` | database | crates, go, npm, rubygems, terraform-resource | no | 0 |
| Azure SQL | `azure.sql` | database | crates, github-actions, go, npm, rubygems, terraform-resource | no | 0 |
| Azure Static Web Apps | `azure.staticwebapps` | servizio o API | crates, github-actions, npm, rubygems, terraform-resource | no | 1 |
| Azure Storage | `azure.storage` | database | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 1 |
| AzureCI | `azure.ci` | servizio o API | files | no | 0 |
| Base44 | `base44` | servizio o API | npm | no | 0 |
| Beehiiv | `beehiiv` | servizio o API | npm, env | no | 0 |
| Better Auth | `betterauth` | autenticazione | npm, env | sì | 0 |
| Better Stack | `betterstack` | servizio o API | composer, npm, rubygems, terraform, env | sì | 0 |
| BigCommerce | `bigcommerce` | servizio o API | composer, npm, pypi, terraform-resource | sì | 0 |
| Bing Maps | `azure.maps` | servizio o API | npm, terraform-resource, env | no | 0 |
| Bitbucket Pipelines | `atlassian.bitbucketpipelines` | servizio o API | files | no | 0 |
| Blackfire | `blackfire` | servizio o API | composer, docker, env | no | 0 |
| Box | `box` | servizio o API | composer, npm, pypi | sì | 0 |
| Brevo | `brevo` | servizio o API | composer, go, npm, rubygems, env | sì | 0 |
| Browser Use | `browseruse` | servizio o API | pypi | no | 0 |
| Browserbase | `browerbase` | servizio o API | composer, pypi | no | 0 |
| Browserstack | `browserstack` | servizio o API | npm, rubygems, files | no | 1 |
| Bugsnag | `bugsnag` | servizio o API | composer, go, npm, pypi, rubygems, env | no | 0 |
| Caddy | `caddy` | servizio o API | docker, go, files | sì | 2 |
| Cal.com | `calcom` | servizio o API | npm | sì | 0 |
| Calendly | `calendly` | servizio o API | npm, env | sì | 0 |
| Celery | `celery` | coda | pypi | sì | 2 |
| Chargebee | `chargebee` | gateway | composer, go, npm, pypi, rubygems, env | no | 0 |
| Checkov | `checkov` | servizio o API | docker, github-actions | no | 0 |
| ChromaDB | `chromadb` | database | pypi | no | 0 |
| CircleCI | `circleci` | servizio o API | github-actions, rubygems, files | sì | 0 |
| CirrusCI | `cirrusci` | servizio o API | files | sì | 0 |
| Clerk | `clerk` | autenticazione | go, npm, pypi, rubygems, env | sì | 0 |
| ClickHouse | `clickhouse` | database | composer, crates, docker, go, npm, pypi, rubygems, terraform, terraform-resource | sì | 2 |
| ClickSend | `clicksend` | servizio o API | npm, env | no | 0 |
| ClickUp | `clickup` | servizio o API | env | sì | 0 |
| Cloud AI Platform | `gcp.aiplatform` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Artifact Registry | `gcp.artifactregistry` | database | go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud BigQuery | `gcp.bigquery` | database | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud BigTable | `gcp.bigtable` | database | composer, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Build | `gcp.cloudbuild` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Dataflow | `gcp.dataflow` | servizio o API | composer, go, npm, rubygems, terraform-resource | no | 0 |
| Cloud Dataproc | `gcp.dataproc` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Datastore | `gcp.datastore` | database | composer, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Dialogflow | `gcp.dialogflow` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Functions | `gcp.functions` | servizio o API | composer, github-actions, go, npm, rubygems, terraform-resource | no | 0 |
| Cloud KMS | `gcp.kms` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | no | 1 |
| Cloud Language | `gcp.language` | servizio o API | composer, go, npm, pypi, rubygems | no | 0 |
| Cloud Logging | `gcp.logging` | servizio o API | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Memorystore | `gcp.memorystore` | database | composer, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Run | `gcp.cloudrun` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Secret Manager | `gcp.secretmanager` | database | composer, github-actions, go, npm, pypi, rubygems, terraform-resource | no | 1 |
| Cloud Spanner | `gcp.spanner` | database | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Speech | `gcp.speech` | servizio o API | composer, go, npm, pypi, rubygems | no | 0 |
| Cloud SQL | `gcp.sql` | database | composer, go, npm, rubygems, terraform-resource | no | 0 |
| Cloud Storage | `gcp.gcs` | database | composer, crates, github-actions, go, npm, pypi, rubygems, terraform-resource | no | 2 |
| Cloud Tasks | `gcp.tasks` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Cloud Vision | `gcp.vision` | servizio o API | composer, go, npm, pypi, rubygems | no | 0 |
| CloudBees | `cloudbees` | servizio o API | env | sì | 0 |
| CloudBees Codeship | `cloudbees.codeship` | servizio o API | files | no | 0 |
| Cloudflare | `cloudflare` | servizio o API | composer, crates, npm, pypi, rubygems, terraform, env | sì | 0 |
| Cloudflare Pages | `cloudflare.pages` | servizio o API | github-actions, terraform-resource | sì | 0 |
| Cloudflare R2 | `cloudflare.r2` | database | npm, terraform-resource | no | 0 |
| Cloudflare Workers | `cloudflare.workers` | servizio o API | crates, github-actions, npm, terraform-resource, files | sì | 0 |
| Cloudinary | `cloudinary` | servizio o API | composer, go, npm, pypi, rubygems, env | sì | 0 |
| CockroachDB | `cockroachdb` | database | composer, terraform | no | 0 |
| Code Climate | `codeclimate` | servizio o API | github-actions, files | sì | 0 |
| Codecov | `codecov` | servizio o API | github-actions, files | sì | 5 |
| CodeSandboxCI | `codesandboxci` | servizio o API | files | no | 0 |
| Cohere AI | `cohereai` | servizio o API | go, npm, pypi, env | no | 0 |
| Commercetools | `commercetools` | servizio o API | npm | no | 0 |
| Composio | `composio` | servizio o API | npm, pypi, env | no | 0 |
| Concourse CI | `concourseci` | servizio o API | files | no | 0 |
| Confluence | `atlassian.confluence` | servizio o API | docker, github-actions, npm | sì | 0 |
| Consul | `consul` | servizio o API | docker, go | sì | 0 |
| Contentful | `contentful` | servizio o API | composer, npm, pypi, env | sì | 0 |
| Convex | `convexdb` | database | crates, npm, pypi, terraform-resource, env | sì | 0 |
| Couchbase | `couchbase` | database | composer, crates, docker, go, npm, pypi, rubygems, terraform, terraform-resource | sì | 0 |
| Coveralls | `coveralls` | servizio o API | github-actions, go, npm, rubygems | sì | 1 |
| CrateDB | `cratedb` | database | docker | sì | 0 |
| Crawl4AI | `crawl4ai` | servizio o API | docker, pypi, env | no | 0 |
| Crowdin | `crowdin` | servizio o API | composer, npm, files | sì | 6 |
| Databricks | `databricks` | servizio o API | github-actions, go, pypi, terraform, terraform-resource, env | sì | 0 |
| Databuddy | `databuddy` | servizio o API | npm, env | no | 0 |
| Datadog | `datadog` | servizio o API | composer, crates, docker, github-actions, go, npm, pypi, rubygems, terraform, terraform-resource, env | sì | 1 |
| DataDome | `datadome` | servizio o API | composer, go, npm, pypi, rubygems | no | 0 |
| Dataiku | `dataiku` | servizio o API | pypi | sì | 0 |
| Datastax | `datastax` | database | composer, terraform, terraform-resource | sì | 0 |
| Dato CMS | `datocms` | servizio o API | npm | sì | 0 |
| Deepseek | `deepseek` | servizio o API | npm, pypi, env | sì | 0 |
| Deepsource | `deepsource` | servizio o API | github-actions, files | no | 0 |
| Deno Deploy | `denodeploy` | servizio o API | deno, github-actions | sì | 0 |
| Dependabot | `dependabot` | servizio o API | github-actions, rubygems, files | sì | 0 |
| Depot.dev | `depotdev` | servizio o API | github-actions, files | no | 2 |
| DigitalOcean | `digitalocean` | servizio o API | github-actions, npm, pypi, terraform | sì | 0 |
| Discord | `discord` | servizio o API | github-actions, npm, env | sì | 1 |
| Discourse | `discourse` | servizio o API | docker | sì | 0 |
| Docusign | `docusign` | servizio o API | composer, npm, rubygems, env | no | 0 |
| Dokku | `dokku` | servizio o API | docker, github-actions, env | no | 0 |
| DroneCI | `droneci` | servizio o API | docker, files | no | 0 |
| Dropbox | `dropbox` | servizio o API | composer, pypi, env | sì | 0 |
| Drupal | `drupal` | servizio o API | composer, docker | sì | 0 |
| DuckDB | `duckdb` | database | go, npm, pypi, terraform-resource | sì | 0 |
| Dynatrace | `dynatrace` | servizio o API | npm, env | sì | 0 |
| Elastic Cloud | `elasticcloud` | servizio o API | terraform | sì | 0 |
| Elasticsearch | `elasticsearch` | database | composer, crates, docker, github-actions, go, npm, pypi, rubygems, terraform, terraform-resource, env | sì | 2 |
| Elevenlabs | `elevenlabs` | servizio o API | npm, pypi, env | sì | 0 |
| Equinix | `equinix` | servizio o API | terraform | no | 0 |
| Expo.dev | `expodev` | servizio o API | github-actions, files | no | 0 |
| Facebook | `facebook` | servizio o API | npm, env | sì | 0 |
| Fastly | `fastly` | servizio o API | crates, go, npm, pypi, rubygems, env | sì | 0 |
| Fathom | `fathom` | servizio o API | npm, env | sì | 0 |
| Figma | `figma` | servizio o API | npm, env | sì | 0 |
| Firebase | `firebase` | servizio o API | crates, github-actions, npm, pypi, rubygems, files, env | sì | 1 |
| Firebase Firestore | `firebase.firestore` | database | composer, terraform-resource | no | 0 |
| Firecrawl | `firecrawl` | servizio o API | composer, crates, go, pypi, env | no | 0 |
| Flyio | `flyio` | servizio o API | github-actions, terraform, files | sì | 1 |
| Freshdesk | `freshdesk` | servizio o API | composer, go, npm, pypi, rubygems, env | no | 0 |
| Frontegg | `frontegg` | autenticazione | npm, pypi, terraform | no | 0 |
| Fusionauth | `fusionauth` | autenticazione | composer, go, npm, pypi, rubygems | sì | 0 |
| GCP | `gcp` | servizio o API | composer, github-actions, npm, pypi, terraform, env | no | 3 |
| Gemini AI | `geminiai` | servizio o API | npm, pypi, env | no | 0 |
| Ghost | `ghost` | servizio o API | docker, npm, env | sì | 0 |
| Gitbook | `gitbook` | servizio o API | npm | sì | 0 |
| Gitea | `gitea` | servizio o API | go | sì | 0 |
| GitGuardian | `gitguardian` | servizio o API | docker, github-actions, go | no | 0 |
| GitHub | `github` | servizio o API | composer, npm, pypi, rubygems, terraform, terraform-resource, files | sì | 1 |
| GitHub CodeQL | `github.codeql` | servizio o API | github-actions | no | 0 |
| Github Pages | `github.pages` | servizio o API | github-actions, files | sì | 7 |
| Gitlab CI | `gitlab.ci` | servizio o API | files | no | 0 |
| Gmail | `google.gmail` | servizio o API | npm, rubygems | sì | 0 |
| Google Analytics | `google.analytics` | servizio o API | composer, npm, pypi, terraform-resource, env | sì | 0 |
| Google App Engine | `gcp.appengine` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Google Calendar | `google.calendar` | servizio o API | composer, npm, pypi, rubygems | sì | 0 |
| Google Chat | `google.chat` | servizio o API | npm, rubygems, terraform-resource | sì | 0 |
| Google Compute | `gcp.gce` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform-resource | no | 1 |
| Google DNS | `gcp.dns` | servizio o API | go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Google Docs | `google.docs` | servizio o API | npm, rubygems | sì | 0 |
| Google Drive | `google.drive` | servizio o API | crates, npm, rubygems, terraform-resource | sì | 0 |
| Google Forms | `google.forms` | servizio o API | npm, rubygems, terraform-resource | sì | 0 |
| Google Keep | `google.keep` | servizio o API | rubygems | sì | 0 |
| Google Kubernetes | `gcp.gke` | servizio o API | github-actions, terraform-resource | no | 0 |
| Google Maps | `gcp.maps` | servizio o API | go, npm, pypi, rubygems, env | sì | 0 |
| Google Meet | `google.meet` | servizio o API | npm, pypi, rubygems | sì | 0 |
| Google Pay | `google.pay` | gateway | npm, env | sì | 0 |
| Google Sheets | `google.sheets` | servizio o API | composer, crates, npm, rubygems, terraform-resource | sì | 0 |
| Google Slides | `google.slides` | servizio o API | npm, rubygems | sì | 0 |
| Google Tasks | `google.tasks` | servizio o API | npm, rubygems | sì | 0 |
| Google Translate | `gcp.translate` | servizio o API | composer, go, npm, pypi, rubygems | sì | 0 |
| Grafana | `grafana` | servizio o API | docker, terraform | sì | 1 |
| Groq | `groq` | servizio o API | npm, pypi, env | no | 0 |
| H2 | `h2` | database | maven | no | 3 |
| Hanko | `hanko` | autenticazione | npm | no | 0 |
| HAProxy | `haproxy` | servizio o API | docker | sì | 0 |
| HashiCorp Vault | `vault` | servizio o API | go | sì | 0 |
| HERE Maps | `heremaps` | servizio o API | npm, env | no | 0 |
| Heroku | `heroku` | servizio o API | composer, github-actions, rubygems, terraform | no | 0 |
| Hetzner | `hetzner` | servizio o API | composer, go, pypi, rubygems, terraform | sì | 0 |
| Honeybadger | `honeybadger` | servizio o API | composer, go, npm, pypi, rubygems, env | sì | 0 |
| Hostinger | `hostinger` | servizio o API | composer, npm, pypi | sì | 0 |
| Hotjar | `hotjar` | servizio o API | npm, env | sì | 0 |
| HSQLDB | `hsqldb` | database | maven | no | 1 |
| HTTPD | `httpd` | servizio o API | docker, files | no | 0 |
| HubSpot | `hubspot` | servizio o API | composer, npm | sì | 0 |
| Hugging Face | `huggingface` | servizio o API | npm, pypi, env | sì | 1 |
| HyperDX | `hyperdx` | servizio o API | go, npm | no | 0 |
| Hypertune | `hypertune` | servizio o API | npm | no | 0 |
| IBM Cloud | `ibmcloud` | servizio o API | terraform | no | 0 |
| ifttt | `ifttt` | servizio o API | env | sì | 0 |
| Infisical | `infisical` | servizio o API | docker, npm, files, env | no | 0 |
| InfluxDB | `influxdb` | database | composer, crates, docker, go, npm, pypi, rubygems | sì | 0 |
| Inngest | `inngest` | servizio o API | crates, go, npm, pypi, env | no | 1 |
| Instagram | `instagram` | servizio o API | env | sì | 0 |
| Integration.app | `integrationapp` | servizio o API | npm | no | 0 |
| Intercom | `intercom` | servizio o API | composer, npm, rubygems, env | sì | 0 |
| Intuit | `intuit` | gateway | env | sì | 0 |
| Jenkins | `jenkins` | servizio o API | docker, pypi, rubygems, files | sì | 0 |
| Jira | `atlassian.jira` | servizio o API | composer, crates, docker, github-actions, npm, rubygems, terraform-resource | sì | 0 |
| Joomla! | `joomla` | servizio o API | composer, docker | sì | 0 |
| Kentico | `kentico` | servizio o API | npm, rubygems | sì | 0 |
| Kibana | `kibana` | servizio o API | docker, env | sì | 1 |
| Kinde | `kinde` | autenticazione | composer, npm, pypi, rubygems | no | 0 |
| Klarna | `klarna` | gateway | rubygems, terraform-resource, env | sì | 0 |
| Klaviyo | `klaviyo` | servizio o API | composer, terraform-resource | no | 0 |
| Koala Analytics | `koalaanalytics` | servizio o API | npm | no | 0 |
| Kong | `kong` | servizio o API | docker, files | sì | 0 |
| Koyeb | `koyeb` | servizio o API | npm, files | sì | 0 |
| Kubernetes | `kubernetes` | servizio o API | composer, crates, github-actions, npm, pypi, rubygems, terraform, files | sì | 1 |
| Lago | `lago` | servizio o API | docker, go, npm, pypi, rubygems, env | no | 0 |
| LaunchDarkly | `launchdarkly` | servizio o API | composer, crates, github-actions, go, npm, rubygems, terraform, env | no | 0 |
| Lemon Squeezy | `lemonsqueezy` | gateway | composer, go, npm, rubygems, env | sì | 0 |
| libSQL | `libsql` | database | composer, crates, go, npm, pypi, rubygems | no | 0 |
| Linear | `linear` | servizio o API | npm, pypi, env | sì | 0 |
| Linkedin | `linkedin` | servizio o API | env | no | 0 |
| LogRocket | `logrocket` | servizio o API | npm | no | 0 |
| LogSnag | `logsnag` | servizio o API | npm, pypi, env | no | 0 |
| Logstash | `logstash` | servizio o API | docker, go, npm, rubygems | sì | 1 |
| Logto | `logtoio` | autenticazione | composer, go, npm, pypi, rubygems, env | no | 0 |
| Lovable | `lovable` | servizio o API | npm | no | 0 |
| Magento | `magento` | servizio o API | composer, npm | no | 0 |
| Mailchimp | `mailchimp` | servizio o API | composer, npm, rubygems, terraform-resource, env | sì | 0 |
| Mailgun | `mailgun` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Mailjet | `mailjet` | servizio o API | composer, crates, npm, rubygems, env | no | 0 |
| Mapbox | `mapbox` | servizio o API | composer, crates, npm, pypi, rubygems, env | sì | 0 |
| MariaDB | `mariadb` | database | docker, npm, rubygems | sì | 6 |
| Matomo | `matomo` | servizio o API | docker, env | sì | 0 |
| Mattermost | `mattermost` | servizio o API | npm | sì | 0 |
| Meilisearch | `meilisearch` | database | composer, crates, docker, go, npm, pypi, rubygems, env | sì | 1 |
| Memcached | `memcached` | database | crates, docker, npm, rubygems, env | no | 0 |
| Merge.dev | `mergedev` | servizio o API | composer, go, npm, pypi, rubygems | no | 0 |
| Metabase | `metabase` | servizio o API | docker, npm | sì | 0 |
| MilvusDB | `milvusdb` | database | docker, go, npm, pypi, terraform-resource, env | no | 0 |
| Miro | `miro` | servizio o API | npm, env | sì | 0 |
| Mistral AI | `mistralai` | servizio o API | go, npm, pypi, env | sì | 0 |
| Mixpanel | `mixpanel` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource, env | sì | 0 |
| Monday | `monday` | servizio o API | npm | no | 0 |
| Mongo Express | `mongoexpress` | servizio o API | docker | no | 2 |
| MongoDB | `mongodb` | database | composer, crates, docker, maven, npm, nuget, pypi, rubygems, terraform-resource, env | sì | 4 |
| MongoDB Atlas | `mongodbatlas` | servizio o API | npm, pypi, terraform | no | 0 |
| MS SQL | `mssql` | database | npm, rubygems | no | 0 |
| Mysql | `mysql` | database | crates, docker, maven, npm, nuget, pypi, rubygems, terraform-resource, env | sì | 9 |
| n8n | `n8n` | servizio o API | docker, npm, env | sì | 0 |
| Nango | `nango` | servizio o API | docker, npm, files, env | no | 0 |
| Nats | `nats` | coda | composer, crates, docker, go, npm, pypi, rubygems | no | 0 |
| Neo4j | `neo4j` | database | crates, docker, go, npm, pypi, rubygems | sì | 0 |
| NeonDB | `neondb` | database | docker, npm, pypi | no | 0 |
| Netlify | `netlify` | servizio o API | github-actions, npm, files | sì | 3 |
| New Relic | `newrelic` | servizio o API | composer, go, npm, pypi, rubygems, terraform, env | sì | 0 |
| Nextcloud | `nextcloud` | servizio o API | docker | sì | 0 |
| Nginx | `nginx` | servizio o API | docker, files | sì | 7 |
| Notion | `notion` | servizio o API | composer, crates, npm, rubygems, env | sì | 0 |
| Novy | `novu` | servizio o API | composer, docker, go, npm, pypi, rubygems | sì | 0 |
| NX Cloud | `nxcloud` | servizio o API | npm | no | 0 |
| Oceanbase | `oceanbase` | database | docker | sì | 0 |
| Okta | `okta` | autenticazione | composer, crates, npm, pypi, rubygems, terraform, env | sì | 1 |
| Ollama | `ollama` | servizio o API | npm, pypi, env | sì | 0 |
| OneDrive | `microsoft.onedrive` | servizio o API | composer, crates, npm, terraform-resource | no | 0 |
| OnlineOrNot | `onlineornot` | servizio o API | npm | no | 0 |
| Openai | `openai` | servizio o API | composer, go, npm, pypi, env | no | 5 |
| Optimizely | `optimizely` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, env | no | 0 |
| Oracle Cloud | `oraclecloud` | servizio o API | composer, npm, rubygems, terraform | no | 0 |
| Oracle Database | `oracledatabase` | database | pypi | no | 0 |
| Orb | `withorb` | servizio o API | go, npm, pypi | no | 0 |
| Ory | `orysh` | autenticazione | composer, go, npm | sì | 0 |
| OVH | `ovh` | servizio o API | composer, npm, terraform, env | sì | 0 |
| OVH Database | `ovh.database` | database | terraform-resource | no | 0 |
| OVH Dedicated Server | `ovh.dedicated` | servizio o API | terraform-resource | no | 0 |
| OVH Kubernetes | `ovh.kubernetes` | servizio o API | terraform-resource | no | 0 |
| OVH Storage | `ovh.storage` | database | terraform-resource | no | 0 |
| OVH VPS | `ovh.vps` | servizio o API | terraform-resource | no | 0 |
| Paddle | `paddle` | gateway | composer, go, npm, pypi, env | sì | 0 |
| Pagerduty | `pagerduty` | servizio o API | composer, crates, npm, pypi, rubygems, terraform, env | sì | 0 |
| Papertrail | `papertrail` | servizio o API | composer, go, npm, rubygems, env | no | 0 |
| Paragon | `useparagon` | servizio o API | npm | no | 0 |
| Payload | `payloadcms` | servizio o API | npm | sì | 0 |
| Paypal | `paypal` | gateway | composer, crates, go, npm, pypi, rubygems, env | sì | 0 |
| Paystack | `paystack` | gateway | npm, env | no | 0 |
| Percona | `percona` | database | docker | no | 0 |
| Perplexity AI | `perplexityai` | servizio o API | npm, env | no | 0 |
| Pinecone | `pinecone` | database | crates, go, npm, pypi, terraform, terraform-resource, env | no | 0 |
| Pingdom | `pingdom` | servizio o API | terraform, env | sì | 0 |
| Pirsch Analytics | `pirschanalytics` | servizio o API | composer, go, npm, rubygems | no | 0 |
| PlaceKit | `placekit` | servizio o API | npm | no | 0 |
| PlanetScale | `planetscale` | database | github-actions | sì | 0 |
| Platform.sh | `platformsh` | servizio o API | files | sì | 0 |
| Plausible | `plausible` | servizio o API | composer, docker, go, npm, rubygems, env | no | 0 |
| Polar | `polarsh` | gateway | composer, go, npm, pypi, env | no | 0 |
| Postgres | `postgresql` | database | composer, crates, deno, docker, hex, maven, npm, nuget, rubygems, terraform-resource, env | sì | 32 |
| Postgrest | `postgrest` | servizio o API | docker | no | 0 |
| PostHog | `posthog` | servizio o API | composer, crates, go, npm, pypi, rubygems, env | sì | 2 |
| Postman | `postman` | servizio o API | npm | sì | 0 |
| Postmark | `postmark` | servizio o API | composer, npm, rubygems | no | 0 |
| Prestashop | `prestashop` | servizio o API | composer | sì | 0 |
| Prisma Cloud | `prismacloud` | servizio o API | terraform | no | 0 |
| Prometheus | `prometheus` | servizio o API | composer, crates, docker, go, npm, rubygems | sì | 2 |
| PropelAuth | `propelauth` | autenticazione | crates, go, npm, pypi | no | 0 |
| PubSub | `gcp.pubsub` | coda | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Puppeteer | `puppeteer` | servizio o API | docker, npm | sì | 1 |
| Qdrant | `qdrant` | database | composer, crates, docker, go, npm, pypi, terraform-resource, env | sì | 0 |
| Qovery | `qovery` | servizio o API | docker, github-actions, go, npm, terraform | no | 0 |
| Qovery Cluster | `qovery.cluster` | servizio o API | terraform-resource | no | 0 |
| Qovery Database | `qovery.database` | database | terraform-resource | no | 0 |
| QuestDB | `questdb` | database | crates, docker, go, npm, pypi | no | 0 |
| RabbitMQ | `rabbitmq` | coda | composer, crates, docker, maven, npm, nuget, pypi, rubygems, env | sì | 4 |
| Railway | `railway` | servizio o API | github-actions, npm, pypi, terraform, files, env | sì | 1 |
| Reddit | `reddit` | servizio o API | npm, env | sì | 0 |
| Redis | `redis` | database | composer, crates, docker, go, maven, npm, nuget, pypi, rubygems, terraform, terraform-resource, env | sì | 19 |
| RelativeCI | `relativeci` | servizio o API | github-actions, npm, files | no | 0 |
| Render | `render` | servizio o API | files | sì | 1 |
| Replicate | `replicate` | servizio o API | go, npm, pypi, env | sì | 0 |
| Replit | `replit` | servizio o API | npm, files | sì | 0 |
| Replit Database | `replit.database` | database | npm, pypi | no | 0 |
| Resend | `resend` | servizio o API | composer, crates, go, npm, pypi, rubygems, env | sì | 1 |
| RethinkDB | `rethinkdb` | database | composer, docker, go, npm, pypi, rubygems | no | 0 |
| RevenueCat | `revenuecat` | gateway | npm, env | sì | 0 |
| Rollbar | `rollbar` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform, env | sì | 1 |
| Salesforce | `salesforce` | servizio o API | npm, terraform, env | no | 0 |
| Sanity | `sanity` | servizio o API | npm | sì | 0 |
| SAP | `sap` | servizio o API | npm | sì | 0 |
| SAS | `sas` | servizio o API | pypi | no | 0 |
| Scaleway | `scaleway` | servizio o API | github-actions, go, npm, pypi, terraform | sì | 0 |
| Scaleway Container | `scaleway.container` | servizio o API | terraform-resource | no | 0 |
| Scaleway Database | `scaleway.database` | database | terraform-resource | no | 0 |
| Scaleway DocumentDB | `scaleway.documentdb` | database | terraform-resource | no | 0 |
| Scaleway Elastic Metal | `scaleway.elasticmetal` | servizio o API | terraform-resource | no | 0 |
| Scaleway Function | `scaleway.function` | servizio o API | terraform-resource | no | 0 |
| Scaleway Kubernetes | `scaleway.kubernetes` | servizio o API | terraform-resource | no | 0 |
| Scaleway M&Q | `scaleway.mq` | coda | terraform-resource | no | 0 |
| Scaleway Redis | `scaleway.redis` | database | terraform-resource | no | 0 |
| Scaleway Secret Manager | `scaleway.secretmanager` | database | terraform-resource | no | 0 |
| Scaleway Storage | `scaleway.storage` | database | terraform-resource | no | 0 |
| Scout APM | `scoutapm` | servizio o API | composer, npm, rubygems | no | 0 |
| Segment | `segment` | servizio o API | composer, go, npm, pypi, rubygems, env | no | 0 |
| Selenium | `selenium` | servizio o API | composer, crates, docker, github-actions, go, npm, pypi, rubygems | sì | 0 |
| Sendgrid | `sendgrid` | servizio o API | composer, go, npm, pypi, rubygems | no | 0 |
| Sentry | `sentry` | servizio o API | composer, crates, docker, github-actions, go, npm, pypi, rubygems, env | sì | 4 |
| ServiceNow | `servicenow` | servizio o API | rubygems | no | 0 |
| Shopify | `shopify` | servizio o API | composer, npm, pypi, rubygems | sì | 0 |
| Signoz | `signoz` | servizio o API | docker, env | no | 0 |
| Simple Analytics | `simpleanalytics` | servizio o API | npm, env | sì | 0 |
| Sitecore | `sitecore` | servizio o API | npm | sì | 0 |
| Sitecore XM cloud | `sitecore.xmlcloud` | servizio o API | npm | no | 0 |
| Slack | `slack` | servizio o API | composer, crates, docker, github-actions, go, npm, pypi, rubygems, terraform, env | no | 0 |
| Snowflake | `snowflake` | database | crates, npm, pypi, rubygems, terraform, terraform-resource | sì | 0 |
| Snyk | `snyk` | servizio o API | docker, github-actions, npm, terraform, files, env | sì | 0 |
| SonarCloud | `sonarcloud` | servizio o API | github-actions | no | 0 |
| SonarQube | `sonarqube` | servizio o API | docker, files | no | 0 |
| Split | `splitio` | servizio o API | go, npm, rubygems | no | 0 |
| Splunk | `splunk` | servizio o API | pypi, terraform, env | sì | 0 |
| Spotify | `spotify` | servizio o API | npm, env | sì | 0 |
| SQLite | `sqlite` | database | crates, deno, npm, rubygems, files | sì | 4 |
| Sqreen | `sqreen` | servizio o API | npm, rubygems, env | no | 0 |
| Square | `squareup` | gateway | composer, env | sì | 0 |
| Squarespace | `squarespace` | servizio o API | npm | sì | 0 |
| Storyblok | `storyblok` | servizio o API | composer, npm, pypi, rubygems | sì | 0 |
| Strapi | `strapi` | servizio o API | docker, npm, env | sì | 0 |
| Stripe | `stripe` | gateway | composer, go, npm, pypi, rubygems, env | sì | 3 |
| StyleCI | `styleci` | servizio o API | files | no | 0 |
| Stytch | `stytch` | autenticazione | crates, go, npm, pypi, rubygems | no | 0 |
| Supabase | `supabase` | servizio o API | docker, github-actions, npm, pypi, env | sì | 0 |
| Supabase Auth | `supabase.auth` | autenticazione | docker, npm | no | 0 |
| Supabase Functions | `supabase.functions` | servizio o API | npm | no | 0 |
| Supabase Postgres | `supabase.postgres` | database | composer, docker, github-actions, npm | no | 0 |
| Supabase Realtime | `supabase.realtime` | coda | docker, npm | no | 0 |
| Supabase Storage | `supabase.storage` | database | docker, npm | no | 0 |
| SuperTokens | `supertokens` | autenticazione | go, npm, pypi | no | 0 |
| SurrealDB | `surrealdb` | database | crates, docker, npm, pypi | sì | 0 |
| Swiftype | `swiftype` | database | composer, npm, pypi, rubygems | no | 0 |
| Tailscale | `tailscale` | servizio o API | github-actions, npm, pypi | sì | 0 |
| TDengine | `tdengine` | database | crates, docker, go, npm | no | 0 |
| TeamCity | `teamcity` | servizio o API | files | sì | 0 |
| Teamspeak | `teamspeak` | servizio o API | docker | sì | 0 |
| Telegraf | `telegraf` | servizio o API | docker | no | 0 |
| Telegram | `telegram` | servizio o API | composer, crates, docker, github-actions, go, npm, rubygems, env | sì | 0 |
| Tencent Cloud | `tencentcloud` | servizio o API | composer, pypi, terraform | no | 0 |
| TiDB | `tidb` | database | docker | sì | 0 |
| Tika | `apachetika` | servizio o API | docker, pypi | no | 1 |
| TimescaleDB | `timescaledb` | database | docker, terraform | no | 0 |
| Tinybird | `tinybird` | servizio o API | npm, env | no | 0 |
| Traefik | `traefik` | servizio o API | docker, go, files | no | 1 |
| Tray.ai | `trayio` | servizio o API | npm | no | 0 |
| Truffle Security | `trufflesecurity` | servizio o API | docker, github-actions | no | 0 |
| Turso | `tursodb` | database | npm, env | sì | 0 |
| Twenty CRM | `twentycrm` | servizio o API | docker | no | 0 |
| Twilio | `twilio` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform-resource, env | no | 0 |
| Twitch | `twitch` | servizio o API | npm, env | sì | 0 |
| Typesense | `typesense` | database | composer, crates, docker, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Upstash | `upstash` | servizio o API | npm | sì | 1 |
| Upstash Kafka | `upstash.kafka` | coda | npm, env | no | 0 |
| Upstash QStash | `upstash.qstash` | coda | npm | no | 0 |
| Upstash Redis | `upstash.redis` | database | npm, pypi, env | no | 1 |
| Uptime Kuma | `uptimekuma` | servizio o API | docker | sì | 0 |
| Use Autumn | `useautumn` | gateway | npm, env | no | 0 |
| Valkey | `valkey` | database | go, npm, pypi, env | no | 0 |
| Vault | `hashicorp_vault` | database | composer, crates, docker, github-actions, npm, pypi, rubygems, terraform | sì | 0 |
| Vercel | `vercel` | servizio o API | crates, github-actions, npm, terraform, terraform-resource, files | sì | 1 |
| Vercel AI | `vercel.ai` | servizio o API | npm | no | 0 |
| Vercel Analytics | `vercel.analytics` | servizio o API | npm | no | 0 |
| Vercel Blob | `vercel.blob` | database | crates, npm | no | 0 |
| Vercel Edge | `vercel.edge` | servizio o API | npm | no | 0 |
| Vercel Functions | `vercel.functions` | servizio o API | npm | no | 0 |
| Vercel KV | `vercel.kv` | database | npm | no | 1 |
| Vercel Postgres | `vercel.postgres` | database | npm | no | 0 |
| Veriff | `veriff` | servizio o API | npm, rubygems | no | 0 |
| Vertex AI | `gcp.vertex` | servizio o API | npm, pypi, env | no | 1 |
| VictoriaMetrics | `victoriametrics` | database | docker | sì | 0 |
| Webflow | `webflow` | servizio o API | npm, pypi, terraform-resource, env | sì | 0 |
| Weights & Biases | `wandb` | servizio o API | pypi | sì | 0 |
| WhatsApp | `whatsapp` | servizio o API | npm, env | sì | 0 |
| Wikipedia | `wikipedia` | servizio o API | npm, pypi, env | sì | 0 |
| Wiz | `wiz` | servizio o API | terraform, env | no | 0 |
| Wolfram Alpha | `wolframalpha` | servizio o API | pypi, env | no | 0 |
| WooCommerce | `woocommerce` | servizio o API | composer, terraform-resource, env | sì | 0 |
| Wordpress | `wordpress` | servizio o API | composer, docker, github-actions, npm, env | sì | 0 |
| WorkOS | `workos` | autenticazione | composer, go, npm, pypi, rubygems, env | no | 0 |
| X | `twitter` | servizio o API | npm, pypi, terraform-resource, env | sì | 0 |
| X AI | `xai` | servizio o API | npm, pypi, env | no | 0 |
| Yousign | `yousign` | servizio o API | composer | no | 0 |
| Youtube | `youtube` | servizio o API | pypi, env | sì | 0 |
| Zapier | `zapier` | servizio o API | npm, env | sì | 0 |
| Zendesk | `zendesk` | servizio o API | composer, npm, rubygems, env | sì | 0 |
| Zipkin | `zipkin` | servizio o API | composer, docker, go, npm, rubygems | no | 1 |
| Zookeeper | `zookeeper` | servizio o API | composer, crates, docker, rubygems | no | 0 |
| Zoom | `zoom` | servizio o API | npm, terraform-resource, env | sì | 0 |
| Zuora | `zuora` | gateway | npm, pypi, env | no | 0 |

</details>

## Letture proprie di framework e dialetti

Oltre al riconoscimento: i componenti Vue e Svelte entrano nell'indice di scip-typescript (`indexers/components.py`) e il loro `<script>` nello snapshot (`languages/sfc.py`); il grafo dei fogli di stile (`indexers/css.py`) legge questi file con i parser fissati in `plugins/codebase-map/skills/map/scripts/indexers/css_engines/package.json`: @astrojs/compiler 4.0.0, @vue/compiler-sfc 3.5.45, less 4.9.1, sass-parser 0.5.6, stylus 0.64.0, svelte 5.57.3, typescript 5.9.3. La sua misura è la riga `stylesheet` della sezione Analizzatori.

| Estensioni | Lettura |
| --- | --- |
| `.css` `.scss` `.sass` `.less` `.pcss` `.postcss` `.styl` `.stylus` | fogli di stile, nel dialetto del suffisso |
| `.html` `.htm` `.ejs` | markup: classi, id e blocchi `<style>` |
| `.astro` | componenti, con il compilatore del framework (`indexers/css_astro.py`) |
| `.svelte` | componenti, con il compilatore del framework (`indexers/css_svelte.py`) |
| `.vue` | componenti, con il compilatore del framework (`indexers/css_vue.py`) |
| `.xhtml` | non letti; il motivo nel codice: «XHTML: no reader» |
| `.cshtml` `.erb` `.ftl` `.handlebars` `.hbs` `.j2` `.jade` `.jinja` `.jsp` `.jspx` `.liquid` `.mustache` `.njk` `.pug` `.razor` `.twig` `.vm` | non letti; il motivo nel codice: «template language: no reader» |

## Collegamenti dei flussi

`scripts/flows.py` applica regole di collegamento di 6 specie: `scrive` `legge` `rotta` `offre` `attiva` `ingresso`; un nodo di store ha uno di 10 tipi: `attore` `schermata` `funzionalità` `servizio o API` `gateway` `database` `coda` `autenticazione` `dispositivo` `altro`. Il censimento ([2026-11-14-punti-di-connessione.md](../research/2026-11-14-punti-di-connessione.md)) cataloga 26 tipi di punto di connessione; quali il prodotto unisce lo dice la sua sezione «Stato». Riconoscimento per tipo: non misurato.

| Coppia | Tipi nel censimento | Tipi |
| --- | --- | --- |
| Chiama / offre | 9 | REST; GraphQL; gRPC, RPC; Comando IPC; Sottoprocesso, CLI; Funzione o job remoto; Navigazione, deep link; Webhook; Stored procedure |
| Scrive / legge | 8 | Tabella, collezione; Stato dell'app; Cache, chiave-valore; File; Object storage; Storage del browser, cookie; Configurazione, variabili, flag; Contesto della richiesta |
| Emette / ascolta | 9 | Coda AMQP; Log di eventi; Coda di lavori; Canale in tempo reale; Evento nel processo; Notifica push; Cambiamento di un dato; Orario; Hook del ciclo di vita |
