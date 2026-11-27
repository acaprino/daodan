# Codebase Map: che cosa supporta

Scritto da `daodan/core/support_table.py` con i dati del prodotto e i risultati dei benchmark nel repository: non si modifica a mano, si riscrive con `python support_table.py build`, e `tests/test_codebase_map_support_table.py` fallisce se il file non è quello che lo script scrive.

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

La pre-mappa ha 35 fonti (`scripts/premap/`, `SOURCES`); il grafo dei moduli legge 42 manifest di 30 ecosistemi (`scripts/build_units.py`); un modulo riceve 52 toolchain dal suo ecosistema o linguaggio (`scripts/module_derive.py`); la preparazione porta 11 toolchain nel container (`scripts/preparation.py`, `NEEDS`).

### Fonti della pre-mappa

Stati di ogni fonte nei casi del giro del 16 novembre 2026 (`benchmarks/project-model/results/pipeline/2026-11-16-finale.json`): `ran` ha girato, `not_needed` il caso non aveva i suoi file.

| Fonte | Versione | Modo | Modulo | Casi per stato |
| --- | --- | --- | --- | --- |
| `modules.py` | daodan/module-graph/v1+compose.1.pyyaml.6.0.4.unit-resolution.3.image.2 | lettore: legge i file | `premap/module_graph.py` | ran 122 |
| `python-build` | daodan/premap/v3 | lettore: legge i file | `premap/python_build.py` | not_needed 110, ran 12 |
| `requirements` | daodan/premap/v2 | lettore: legge i file | `premap/requirements.py` | not_needed 114, ran 8 |
| `python-tests` | daodan/premap/v1 | lettore: legge i file | `premap/python_tests.py` | not_needed 115, ran 7 |
| `npm-files` | daodan/premap/v1 | lettore: legge i file | `premap/npm_lock.py` | not_needed 86, ran 36 |
| `npm-tests` | daodan/premap/v6 | lettore: legge i file | `premap/npm_tests.py` | not_needed 113, ran 9 |
| `npm-start` | daodan/premap/v1 | lettore: legge i file | `premap/npm_start.py` | non misurato: non era nel giro |
| `jvm-files` | daodan/premap/v4 | lettore: legge i file | `premap/jvm_files.py` | not_needed 100, ran 22 |
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
| `noir` | 1.5.0 | scanner: legge ogni file | `premap/noir.py` | non misurato: non era nel giro |
| `next` | daodan/premap/v4 | scanner: legge ogni file | `premap/nextjs.py` | non misurato: non era nel giro |
| `react-router` | daodan/premap/v4 | scanner: legge ogni file | `premap/react_router.py` | non misurato: non era nel giro |
| `nuxt` | daodan/premap/v2 | scanner: legge ogni file | `premap/nuxt.py` | non misurato: non era nel giro |
| `sveltekit` | daodan/premap/v2 | scanner: legge ogni file | `premap/sveltekit.py` | non misurato: non era nel giro |
| `angular` | daodan/premap/v2 | scanner: legge ogni file | `premap/angular.py` | non misurato: non era nel giro |
| `astro` | daodan/premap/v2 | scanner: legge ogni file | `premap/astro.py` | non misurato: non era nel giro |

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

Lo step `stack` (`scripts/technologies.py`) dà a ogni unità `frameworks`, `libraries`, `services` e `tools`. La classe di una voce del catalogo (`data/service-registry.json`) la decide `service_registry.entry_category`: la `category` della voce se c'è, altrimenti `service` per una voce `service` e `framework` per ogni altra. I `frameworks` di un'unità sono le voci `framework`; le `libraries` sono tutti i pacchetti che dichiara, nel catalogo o no, con l'id della voce che il catalogo ne ha. Sul grafo dell'app un modulo mostra come tessere le voci `framework` e `library` che un suo file dichiara; uno strumento non è una tessera, un servizio è un nodo esterno.

| Classe | Voci con una regola del fork | Voci con la categoria scritta, fra tutte |
| --- | --- | --- |
| framework | 139 | 139 |
| library | 196 | 196 |
| tool | 164 | 164 |
| service | 719 | 719 |

Ognuna delle 499 voci `project` con una regola del fork ha la sua `category` scritta: nessuna è `framework` solo per il default.

Riconoscimento dello stack sul corpus, giro del 27 novembre 2026 (`benchmarks/project-model/results/daodan_stack.json`), 184 fixture su 186 con record; per nome conta un nome una volta per fixture, per unità ogni unità che lo tiene.

| Famiglia | Fixture | Framework per nome | Framework per unità | Servizi |
| --- | --- | --- | --- | --- |
| js | 20 | 10 / 10 (100,0 %) | 11 / 11 (100,0 %), 0 sbagliati | 1 / 1 (100,0 %), 0 in più |
| py | 21 | 4 / 4 (100,0 %) | 4 / 4 (100,0 %), 0 sbagliati | 2 / 3 (66,7 %), 0 in più |
| jvm | 34 | 38 / 42 (90,5 %) | 39 / 43 (90,7 %), 0 sbagliati | 2 / 2 (100,0 %), 1 in più |
| sys | 25 | 2 / 2 (100,0 %) | 1 / 2 (50,0 %), 1 sbagliato | nessuno atteso, 0 in più |
| mix | 30 | 29 / 31 (93,5 %) | 32 / 37 (86,5 %), 0 sbagliati | 12 / 33 (36,4 %), 1 in più |
| real | 15 | 144 / 163 (88,3 %) | 258 / 312 (82,7 %), 13 sbagliati | 59 / 124 (47,6 %), 18 in più |
| stack | 39 | 360 / 393 (91,6 %) | 608 / 757 (80,3 %), 57 sbagliati | 180 / 451 (39,9 %), 92 in più |
| tutte | 184 | 587 / 645 (91,0 %) | 953 / 1.166 (81,7 %), 71 sbagliati | 256 / 614 (41,7 %), 112 in più |

Che cosa vuol dire «supportata» per una voce della tabella che segue, a livelli. Riconosciuta: il fork di stack-analyser ha una regola per la voce (la colonna «Regola del fork»: `sì` se la voce viene dal catalogo del suo rilascio, `no` se il registro la nomina e il fork non la riconosce) e la riconosce da ciò che il progetto mostra (un pacchetto, un'immagine, un file, un sorgente). Lettura propria: ciò che Daodan legge del framework oltre al suo linguaggio, e vale solo per 4 voci (Vue.js, Svelte, Astro, Tailwind). Rotte e collegamenti fra le parti vengono dalle regole di collegamento che un modello scrive per ogni progetto e che `scripts/flows.py` applica a chiamate, decoratori e attributi, per qualunque framework. Le rotte lette dallo strumento del framework, nel container, sono quelle di Next.js (`next typegen`), React Router e Remix (`routes --json`), le rotte del server e le pagine di Nuxt (`nuxt prepare`, `loadNuxt`) e i moduli delle rotte di SvelteKit (`svelte-kit sync`). Gli eventi dei template li legge il compilatore del framework: con il metodo che chiamano per Angular (`parseTemplate`), con la riga e la colonna ma senza la funzione per Astro (`parse`: il gestore è una stringa di JavaScript). Non sono lette le pagine di Astro (`sync()` dell'API le elenca con l'hook `astro:routes:resolved` senza avviare l'app: misurato, non scritto) né le pagine di SvelteKit che sono solo un componente: per queste la rotta dal posto di un file è un buco dichiarato.

<details><summary>Framework, librerie e strumenti: 499 voci</summary>

| Voce | Id | Classe | Regola del fork | Lettura propria | Fixture in cui lo step la trova (27 novembre 2026) |
| --- | --- | --- | --- | --- | --- |
| .NET Aspire | `dotnet-aspire` | framework | sì | — | 3 |
| .NET MAUI | `dotnet-maui` | framework | sì | — | 1 |
| Actix Web | `actixweb` | framework | sì | — | 2 |
| AdonisJS | `adonisjs` | framework | sì | — | 0 |
| aiohttp | `aiohttp` | framework | sì | — | 1 |
| Alpine.js | `alpinejs` | framework | sì | — | 2 |
| Android | `android` | framework | sì | — | 7 |
| Angular | `angular` | framework | sì | — | 4 |
| AngularJS | `angularjs` | framework | sì | — | 0 |
| Api Platform | `apiplatform` | framework | sì | — | 0 |
| Apollo Server | `apollo-server` | framework | sì | — | 1 |
| ASP.NET Core | `aspnetcore` | framework | sì | — | 6 |
| Assemble | `assemble` | framework | sì | — | 0 |
| Astro | `astro` | framework | sì | frontmatter e `<script>` nello snapshot (`languages/sfc.py`), del template solo gli eventi (`premap/astro.py`); stili con il compilatore del framework (`indexers/css_astro.py`) | 1 |
| Axum | `axum` | framework | sì | — | 3 |
| Blazor | `blazor` | framework | sì | — | 2 |
| Blitzjs | `blitzjs` | framework | sì | — | 0 |
| Capacitor | `capacitorjs` | framework | sì | — | 1 |
| Celery | `celery` | framework | sì | — | 2 |
| Chi | `chi` | framework | sì | — | 4 |
| Compose for Wear OS | `compose-for-wear-os` | framework | sì | — | 1 |
| Compose Multiplatform | `compose-multiplatform` | framework | sì | — | 2 |
| Connect | `connectrpc` | framework | sì | — | 2 |
| Cordova | `apacheCordova` | framework | sì | — | 0 |
| Dioxus | `dioxus` | framework | sì | — | 0 |
| Django | `django` | framework | sì | — | 7 |
| Django Channels | `django-channels` | framework | sì | — | 1 |
| Django REST framework | `django-rest-framework` | framework | sì | — | 3 |
| Docsify | `docsify` | framework | sì | — | 0 |
| Docus | `docus` | framework | sì | — | 0 |
| Docusaurus | `docusaurus` | framework | sì | — | 1 |
| Duende IdentityServer | `duende-identityserver` | framework | sì | — | 1 |
| Echo | `echo` | framework | sì | — | 1 |
| Electron | `electron` | framework | sì | — | 1 |
| Eleventy | `eleventy` | framework | sì | — | 0 |
| ElysiaJS | `elysiajs` | framework | sì | — | 0 |
| Ember | `emberjs` | framework | sì | — | 0 |
| Expo | `expojs` | framework | sì | — | 4 |
| Express | `express` | framework | sì | — | 9 |
| ExUnit | `exunit` | framework | sì | — | 4 |
| FastAPI | `fastapi` | framework | sì | — | 7 |
| FastEndpoints | `fastendpoints` | framework | sì | — | 1 |
| Fastify | `fastify` | framework | sì | — | 0 |
| FastMCP | `fastmcp` | framework | sì | — | 1 |
| Fiber | `fiber` | framework | sì | — | 1 |
| Flask | `flask` | framework | sì | — | 7 |
| Flutter | `flutter` | framework | sì | — | 2 |
| flutter_test | `flutter-test` | framework | sì | — | 2 |
| FumaDocs | `fumadocs` | framework | sì | — | 1 |
| Gatsby | `gatsby` | framework | sì | — | 0 |
| Gin | `gin` | framework | sì | — | 2 |
| Gradio | `gradio` | framework | sì | — | 1 |
| Gridsome | `gridsome` | framework | sì | — | 0 |
| HexoJS | `hexojs` | framework | sì | — | 0 |
| Hono | `honojs` | framework | sì | — | 2 |
| Hugo | `hugo` | framework | sì | — | 1 |
| Inferno | `infernojs` | framework | sì | — | 0 |
| Ionic | `ionic` | framework | sì | — | 0 |
| Jekyll | `jekyll` | framework | sì | — | 0 |
| Jetpack Compose | `jetpack-compose` | framework | sì | — | 1 |
| Koa | `koa` | framework | sì | — | 0 |
| Kotlin Multiplatform | `kotlin-multiplatform` | framework | sì | — | 3 |
| Ktor | `ktor` | framework | sì | — | 2 |
| LangChain4j | `langchain4j` | framework | sì | — | 1 |
| Laravel | `laravel` | framework | sì | — | 3 |
| Lit | `litjs` | framework | sì | — | 0 |
| MapKit | `mapkit` | framework | sì | — | 1 |
| Materialize | `materialize-css` | framework | sì | — | 1 |
| Meteor | `meteorjs` | framework | sì | — | 0 |
| Metro | `metro-kotlin` | framework | sì | — | 1 |
| Micronaut | `micronaut` | framework | sì | — | 0 |
| Mithril | `mithriljs` | framework | sì | — | 0 |
| MkDocs | `mkdocs` | framework | sì | — | 2 |
| MudBlazor | `mudblazor` | framework | sì | — | 1 |
| MyBatis | `mybatis` | framework | sì | — | 1 |
| NestJS | `nestjs` | framework | sì | — | 2 |
| Next.js | `nextjs` | framework | sì | — | 7 |
| Nuxt.js | `nuxtjs` | framework | sì | — | 3 |
| Phaser | `phaserjs` | framework | sì | — | 0 |
| Phoenix | `phoenix` | framework | sì | — | 3 |
| Phoenix LiveView | `phoenix-liveview` | framework | sì | — | 3 |
| Pico CSS | `pico-css` | framework | sì | — | 1 |
| Preact | `preactjs` | framework | sì | — | 1 |
| proptest | `proptest` | framework | sì | — | 1 |
| Quarkus | `quarkus` | framework | sì | — | 1 |
| Quarkus REST | `quarkus-rest` | framework | sì | — | 1 |
| Quarkus WebSockets Next | `quarkus-websockets-next` | framework | sì | — | 1 |
| Qwik | `qwikjs` | framework | sì | — | 0 |
| React | `react` | framework | sì | — | 20 |
| React Native | `react-native` | framework | sì | — | 4 |
| RedwoodJs | `redwoodjs` | framework | sì | — | 0 |
| Refine | `refinedev` | framework | sì | — | 0 |
| Remix | `remixrun` | framework | sì | — | 0 |
| Roq | `roq` | framework | sì | — | 0 |
| rstest | `rstest` | framework | sì | — | 1 |
| Ruby on Rails | `rails` | framework | sì | — | 3 |
| Scrapy | `scrapy` | framework | sì | — | 0 |
| Shopify Hydrogen | `shopify.hydrogen` | framework | sì | — | 0 |
| Sinatra | `sinatra` | framework | sì | — | 1 |
| Slate | `slatedocs` | framework | sì | — | 0 |
| Slim | `slim` | framework | sì | — | 1 |
| Solid js | `solidjs` | framework | sì | — | 0 |
| Sphinx | `sphinx` | framework | sì | — | 2 |
| Spring AI | `spring-ai` | framework | sì | — | 1 |
| Spring AMQP | `spring-amqp` | framework | sì | — | 1 |
| Spring Boot | `spring-boot` | framework | sì | — | 8 |
| Spring Boot Admin | `spring-boot-admin` | framework | sì | — | 1 |
| Spring Cloud Config | `spring-cloud-config` | framework | sì | — | 1 |
| Spring Cloud Gateway | `spring-cloud-gateway` | framework | sì | — | 1 |
| Spring Cloud Netflix | `spring-cloud-netflix` | framework | sì | — | 1 |
| Spring Data Elasticsearch | `spring-data-elasticsearch` | framework | sì | — | 1 |
| Spring Data JPA | `spring-data-jpa` | framework | sì | — | 6 |
| Spring Data MongoDB | `spring-data-mongodb` | framework | sì | — | 1 |
| Spring Data Redis | `spring-data-redis` | framework | sì | — | 1 |
| Spring MVC | `spring-mvc` | framework | sì | — | 7 |
| Spring Security | `spring-security` | framework | sì | — | 2 |
| Spring WebFlux | `spring-webflux` | framework | sì | — | 0 |
| Stencil | `stenciljs` | framework | sì | — | 0 |
| Stimulus | `stimulus` | framework | sì | — | 2 |
| Strawberry GraphQL | `strawberry-graphql` | framework | sì | — | 1 |
| Streamlit | `streamlit` | framework | sì | — | 0 |
| Svelte | `sveltejs` | framework | sì | componenti nell'indice di scip-typescript (`indexers/components.py`); `<script>` e template nello snapshot (`languages/sfc.py`); stili con il compilatore del framework (`indexers/css_svelte.py`) | 3 |
| SvelteKit | `sveltekit` | framework | sì | — | 2 |
| SwiftUI | `swiftui` | framework | sì | — | 5 |
| Symfony | `symfony` | framework | sì | — | 3 |
| Tanstack Start | `tanstackstart` | framework | sì | — | 1 |
| Tauri | `tauri` | framework | sì | — | 3 |
| test | `dart-test` | framework | sì | — | 1 |
| UIKit | `uikit` | framework | sì | — | 4 |
| UmiJS | `umijs` | framework | sì | — | 0 |
| VitePress | `vitepress` | framework | sì | — | 1 |
| Vue.js | `vue` | framework | sì | componenti nell'indice di scip-typescript (`indexers/components.py`); `<script>` e template nello snapshot (`languages/sfc.py`); stili con il compilatore del framework (`indexers/css_vue.py`) | 9 |
| VuePress | `vuepress` | framework | sì | — | 0 |
| Vuetify | `vuetify` | framework | sì | — | 1 |
| Wagtail | `wagtail` | framework | sì | — | 1 |
| Wasp | `wasp` | framework | sì | — | 0 |
| WinUI | `winui` | framework | sì | — | 1 |
| Yew | `yew` | framework | sì | — | 1 |
| Yii2 | `yii2` | framework | sì | — | 0 |
| _hyperscript | `hyperscript` | library | sì | — | 2 |
| Ant Design | `antd` | library | sì | — | 1 |
| Ant Design Icons | `antdicons` | library | sì | — | 1 |
| Apache Avro | `avro` | library | sì | — | 1 |
| Apache Beam | `apache-beam` | library | sì | — | 0 |
| Apache Thrift | `apache_thrift` | library | sì | — | 0 |
| AriaKit UI | `ariakitui` | library | sì | — | 0 |
| Ark UI | `arkui` | library | sì | — | 0 |
| ArkType | `arktype` | library | sì | — | 0 |
| Base UI | `baseui` | library | sì | — | 0 |
| Basecoat | `basecoat` | library | sì | — | 1 |
| Bootstrap | `bootstrap` | library | sì | — | 8 |
| Bootstrap Icons | `bootstrapicons` | library | sì | — | 1 |
| Broadway | `broadway` | library | sì | — | 1 |
| BullMQ | `bullmq` | library | sì | — | 1 |
| Casbin | `casbin` | library | sì | — | 1 |
| Catalyst | `github-catalyst` | library | sì | — | 1 |
| Cats | `cats` | library | sì | — | 1 |
| Chakra UI | `chakraui` | library | sì | — | 0 |
| clap | `clap` | library | sì | — | 4 |
| class-transformer | `class-transformer` | library | sì | — | 2 |
| class-validator | `class-validator` | library | sì | — | 2 |
| Click | `click` | library | sì | — | 10 |
| Cobra | `cobra` | library | sì | — | 2 |
| CodeMirror | `codemirror` | library | sì | — | 8 |
| Coil | `coil` | library | sì | — | 2 |
| D3.js | `d3js` | library | sì | — | 1 |
| daisyUI | `daisyui` | library | sì | — | 2 |
| dart_mappable | `dart-mappable` | library | sì | — | 1 |
| Dask | `dask` | library | sì | — | 0 |
| Diesel | `dieselrs` | library | sì | — | 0 |
| Doctrine ORM | `doctrinephp` | library | sì | — | 2 |
| DOMPurify | `dompurify` | library | sì | — | 7 |
| Drizzle ORM | `drizzleorm` | library | sì | — | 0 |
| Ecto | `ecto` | library | sì | — | 2 |
| EffectJS | `effectjs` | library | sì | — | 1 |
| Element Plus | `element-plus` | library | sì | — | 1 |
| ELK.js | `elkjs` | library | sì | — | 0 |
| ent. | `goent` | library | sì | — | 0 |
| Entity Framework Core | `entity-framework-core` | library | sì | — | 6 |
| Expo Router | `expo-router` | library | sì | — | 3 |
| Exposed | `exposed` | library | sì | — | 1 |
| Feather Icons | `feathericons` | library | sì | — | 0 |
| Fluent UI | `fluentui` | library | sì | — | 0 |
| flutter_rust_bridge | `flutter-rust-bridge` | library | sì | — | 1 |
| Font Awesome | `fontawesome` | library | sì | — | 4 |
| GORM | `gorm` | library | sì | — | 2 |
| graphql_client | `graphql-client-rust` | library | sì | — | 1 |
| gRPC | `grpc` | library | sì | — | 7 |
| gRPC-Gateway | `grpc-gateway` | library | sì | — | 2 |
| Headless UI | `headlessui` | library | sì | — | 1 |
| Hero UI | `heroui` | library | sì | — | 0 |
| Heroicons | `heroicons` | library | sì | — | 2 |
| Hibernate | `hibernate` | library | sì | — | 2 |
| Hibernate Reactive | `hibernate-reactive` | library | sì | — | 1 |
| Horologist | `horologist` | library | sì | — | 1 |
| HTMX | `htmx` | library | sì | — | 4 |
| HTTPX | `httpx` | library | sì | — | 5 |
| HugeIcons | `hugeicons` | library | sì | — | 0 |
| Hyper | `hyper-rust` | library | sì | — | 1 |
| Imago | `imago` | library | sì | — | 0 |
| Ionicons | `ionicons` | library | sì | — | 0 |
| Jackson | `jackson` | library | sì | — | 6 |
| Jinja | `jinja` | library | sì | — | 9 |
| JMS Serializer | `jms-serializer` | library | sì | — | 1 |
| Joi | `joijs` | library | sì | — | 0 |
| jOOQ | `jooq` | library | sì | — | 0 |
| JSON Schema | `jsonschema` | library | sì | — | 5 |
| Json.NET | `json-net` | library | sì | — | 1 |
| Juniper | `juniper` | library | sì | — | 1 |
| Keras | `keras` | library | sì | — | 0 |
| keyring | `keyring` | library | sì | — | 1 |
| Knex | `knex` | library | sì | — | 0 |
| Koin | `koin` | library | sì | — | 2 |
| kotlinx.html | `kotlinx-html` | library | sì | — | 0 |
| kotlinx.serialization | `kotlinx-serialization` | library | sì | — | 2 |
| Kysely | `kysely` | library | sì | — | 1 |
| LangChain | `langchain` | library | sì | — | 1 |
| Lexical Editor | `lexicaleditor` | library | sì | — | 0 |
| LikeC4 | `likec4` | library | sì | — | 0 |
| LlamaIndex | `llamaindex` | library | sì | — | 0 |
| Lombok | `lombok` | library | sì | — | 2 |
| Lord Icon | `lordicon` | library | sì | — | 0 |
| Lucide Icons | `lucideicons` | library | sì | — | 9 |
| Mantine UI | `mantineui` | library | sì | — | 0 |
| MapStruct | `mapstruct` | library | sì | — | 3 |
| Marked | `marked` | library | sì | — | 8 |
| marshmallow | `marshmallow` | library | sì | — | 1 |
| Material Design Icons | `materialdesignicons` | library | sì | — | 0 |
| Material UI | `materialui` | library | sì | — | 1 |
| Matplotlib | `matplotlib` | library | sì | — | 1 |
| MessagePack | `messagepack-dotnet` | library | sì | — | 1 |
| MiniJinja | `minijinja` | library | sì | — | 1 |
| Mlflow | `mlflow` | library | sì | — | 0 |
| Mockall | `mockall` | library | sì | — | 1 |
| Model Context Protocol SDK | `mcp` | library | sì | — | 4 |
| Monaco Editor | `monacoeditor` | library | sì | — | 1 |
| Mongoose | `mongoose` | library | sì | — | 1 |
| Mono.Cecil | `mono-cecil` | library | sì | — | 0 |
| MUI Icons | `muiicons` | library | sì | — | 1 |
| NumPy | `numpy` | library | sì | — | 3 |
| Oban | `oban` | library | sì | — | 2 |
| OpenAPI | `openapi` | library | sì | — | 11 |
| OpenCV | `opencv` | library | sì | — | 0 |
| OpenTelemetry | `opentelemetry` | library | sì | — | 7 |
| Panache | `panache` | library | sì | — | 1 |
| pandas | `pandas` | library | sì | — | 2 |
| Passport | `passport` | library | sì | — | 2 |
| Pebble | `pebble` | library | sì | — | 0 |
| Phosphor Icons | `phosphoreicons` | library | sì | — | 0 |
| picocli | `picocli` | library | sì | — | 1 |
| Pillow | `pillow` | library | sì | — | 6 |
| Pinia | `pinia` | library | sì | — | 2 |
| Plotly | `plotly` | library | sì | — | 0 |
| Polars | `polars` | library | sì | — | 0 |
| Prisma | `prisma` | library | sì | — | 4 |
| Protocol Buffers | `protobuf` | library | sì | — | 10 |
| Pydantic | `pydantic` | library | sì | — | 7 |
| Pytorch | `pytorch` | library | sì | — | 0 |
| PyYAML | `pyyaml` | library | sì | — | 5 |
| Qmgo | `qmgo` | library | sì | — | 1 |
| Qute | `qute` | library | sì | — | 1 |
| Radix Icons | `radixicons` | library | sì | — | 0 |
| Radix UI | `radixui` | library | sì | — | 4 |
| Ratatui | `ratatui` | library | sì | — | 2 |
| Ray | `ray` | library | sì | — | 0 |
| React DOM | `react-dom` | library | sì | — | 19 |
| React Email | `reactemail` | library | sì | — | 4 |
| React Flow | `react-flow` | library | sì | — | 0 |
| React Icons | `reacticons` | library | sì | — | 2 |
| React Native Elements | `react-native-elements` | library | sì | — | 2 |
| React Navigation | `react-navigation` | library | sì | — | 3 |
| React Router | `reactrouterdom` | library | sì | — | 7 |
| Refena | `refena` | library | sì | — | 1 |
| Reka UI | `rekaui` | library | sì | — | 0 |
| Remix Icons | `remixicons` | library | sì | — | 0 |
| Remix Router | `remixrouter` | library | sì | — | 0 |
| Remult | `remult` | library | sì | — | 0 |
| Requests | `requests` | library | sì | — | 11 |
| Resilience4j | `resilience4j` | library | sì | — | 1 |
| Rich | `rich` | library | sì | — | 5 |
| Routerino | `routerino` | library | sì | — | 1 |
| RQ | `rq` | library | sì | — | 2 |
| Sandpack | `sandpackeditor` | library | sì | — | 0 |
| Sass parser | `sass-parser` | library | sì | — | 0 |
| scikit-learn | `scikitlearn` | library | sì | — | 1 |
| SciPy | `scipy` | library | sì | — | 0 |
| SeaORM | `sea-orm` | library | sì | — | 1 |
| Sequel | `sequelruby` | library | sì | — | 0 |
| Sequelize | `sequelize` | library | sì | — | 1 |
| Serde | `serde` | library | sì | — | 8 |
| serde_json | `serde-json` | library | sì | — | 6 |
| Shadcn | `shadcn` | library | sì | — | 4 |
| Sidekiq | `sidekiq` | library | sì | — | 2 |
| Simple Icons | `simpleicons` | library | sì | — | 0 |
| SmallRye Reactive Messaging | `smallrye-reactive-messaging` | library | sì | — | 1 |
| Socket.io | `socketio` | library | sì | — | 2 |
| Solid Queue | `solid-queue` | library | sì | — | 1 |
| spaCy | `spacy` | library | sì | — | 0 |
| SQLAlchemy | `sqlalchemy` | library | sì | — | 6 |
| SQLGlot | `sqlglot` | library | sì | — | 0 |
| SQLModel | `sqlmodel` | library | sì | — | 1 |
| sqlx | `sqlx-go` | library | sì | — | 1 |
| SQLx | `sqlx-rust` | library | sì | — | 1 |
| Superstruct | `superstruct` | library | sì | — | 0 |
| Tabler | `tabler` | library | sì | — | 1 |
| Tabler Icons | `tablericons` | library | sì | — | 1 |
| Tailwind | `tailwind` | library | sì | quali classi sono sue utility, dal Tailwind del progetto nel container (`indexers/css_tailwind.py`) | 17 |
| TanStack Router | `tanstackrouter` | library | sì | — | 1 |
| tempfile | `tempfile-rust` | library | sì | — | 2 |
| Tensorflow | `tensorflow` | library | sì | — | 0 |
| testify | `testify` | library | sì | — | 6 |
| Testing Library | `testinglibrary` | library | sì | — | 12 |
| Thymeleaf | `thymeleaf` | library | sì | — | 3 |
| Tiptap | `tiptap` | library | sì | — | 3 |
| Tokio | `tokio` | library | sì | — | 4 |
| Tree-sitter | `tree-sitter` | library | sì | — | 0 |
| Tree-sitter Language Pack | `tree-sitter-language-pack` | library | sì | — | 0 |
| TRPC | `trpc` | library | sì | — | 1 |
| ts-rest | `ts-rest` | library | sì | — | 1 |
| Turbo | `hotwire-turbo` | library | sì | — | 2 |
| Twig | `twigphp` | library | sì | — | 2 |
| TypeBox | `typebox` | library | sì | — | 0 |
| TypeORM | `typeorm` | library | sì | — | 1 |
| Typer | `typer` | library | sì | — | 3 |
| urfave/cli | `urfave-cli` | library | sì | — | 2 |
| urql | `urql` | library | sì | — | 1 |
| Valibot | `valibot` | library | sì | — | 0 |
| Viper | `viper` | library | sì | — | 3 |
| Vue Router | `vue-router` | library | sì | — | 3 |
| WatermelonDB | `watermelondb` | library | sì | — | 1 |
| webview2-com | `webview2-com` | library | sì | — | 0 |
| Windows for Rust | `windows-rs` | library | sì | — | 2 |
| wiremock | `wiremock-rs` | library | sì | — | 1 |
| YARP | `yarp` | library | sì | — | 1 |
| Zod | `zod` | library | sì | — | 8 |
| Ada | `ada` | tool | sì | — | 0 |
| Alembic | `alembic` | tool | sì | — | 5 |
| Ansible | `ansible` | tool | sì | — | 0 |
| Apache JMeter | `jmeter` | tool | sì | — | 1 |
| ArchUnit | `archunit` | tool | sì | — | 1 |
| Artillery | `artillery` | tool | sì | — | 1 |
| asdf | `asdf` | tool | sì | — | 0 |
| ASP.NET | `aspnet` | tool | sì | — | 0 |
| Astro compiler | `astro-compiler` | tool | sì | — | 0 |
| AtlasGo | `atlasgo` | tool | sì | — | 0 |
| AVA | `ava` | tool | sì | — | 0 |
| AWS CDK | `awscdk` | tool | sì | — | 0 |
| AWS CloudFormation | `aws.cloudformation` | tool | sì | — | 0 |
| Babel | `babel` | tool | sì | — | 9 |
| Bash | `bash` | tool | sì | — | 0 |
| Biome JS | `biomejs` | tool | sì | — | 4 |
| Bun | `bunsh` | tool | sì | — | 1 |
| Bundler | `bundler` | tool | sì | — | 6 |
| Bytebase | `bytebase` | tool | sì | — | 0 |
| C | `c` | tool | sì | — | 0 |
| C# | `csharp` | tool | sì | — | 0 |
| C++ | `cplusplus` | tool | sì | — | 0 |
| Capybara | `capybara` | tool | sì | — | 3 |
| Cargo | `cargo` | tool | sì | — | 17 |
| Chef | `chef` | tool | sì | — | 0 |
| Clojure | `clojure` | tool | sì | — | 0 |
| COBOL | `cobol` | tool | sì | — | 0 |
| CoffeeScript | `coffeescript` | tool | sì | — | 0 |
| Composer | `phpcomposer` | tool | sì | — | 7 |
| containerd | `containerd` | tool | sì | — | 0 |
| Create React App | `create-react-app` | tool | sì | — | 1 |
| CSS | `css` | tool | sì | — | 0 |
| Cypress | `cypressci` | tool | sì | — | 3 |
| Dapr | `dapr` | tool | sì | — | 0 |
| Dart | `dart` | tool | sì | — | 2 |
| dbt | `dbt` | tool | sì | — | 0 |
| Deno | `deno` | tool | sì | — | 1 |
| Detox | `detox` | tool | sì | — | 1 |
| Docker | `docker` | tool | sì | — | 45 |
| Elixir | `elixir` | tool | sì | — | 4 |
| Esbuild | `esbuild` | tool | sì | — | 9 |
| Eslint | `eslint` | tool | sì | — | 24 |
| Fern | `builtwithfern` | tool | sì | — | 0 |
| Flyway | `flyway` | tool | sì | — | 0 |
| FsCheck | `fscheck` | tool | sì | — | 0 |
| Gatling | `gatling` | tool | sì | — | 1 |
| GLSL | `glsl` | tool | sì | — | 0 |
| goenv | `goenv` | tool | sì | — | 0 |
| Golang | `golang` | tool | sì | — | 21 |
| GolangCI Lint | `golangcilint` | tool | sì | — | 3 |
| Gradle | `gradle` | tool | sì | — | 26 |
| Grafana K6 | `k6` | tool | sì | — | 0 |
| GraphiQL | `graphiql` | tool | sì | — | 1 |
| Gunicorn | `gunicorn` | tool | sì | — | 8 |
| Haskell | `haskell` | tool | sì | — | 0 |
| Hatchling | `hatchling` | tool | sì | — | 13 |
| Helm | `helm` | tool | sì | — | 4 |
| Java | `java` | tool | sì | — | 0 |
| JavaScript | `javascript` | tool | sì | — | 0 |
| Jest | `jest` | tool | sì | — | 10 |
| JHipster | `jhipster` | tool | sì | — | 1 |
| JSX | `jsx` | tool | sì | — | 0 |
| JUnit | `junit` | tool | sì | — | 22 |
| JUnit Jupiter | `junit-jupiter` | tool | sì | — | 8 |
| Jupyter | `jupyter` | tool | sì | — | 0 |
| Kotest | `kotest` | tool | sì | — | 0 |
| Kotlin | `kotlin` | tool | sì | — | 0 |
| kotlin.test | `kotlin-test` | tool | sì | — | 2 |
| Lego | `goacmelego` | tool | sì | — | 0 |
| Less | `less` | tool | sì | — | 0 |
| Lighthouse | `lighthouse` | tool | sì | — | 1 |
| Liquibase | `liquibase` | tool | sì | — | 1 |
| Locust | `locust` | tool | sì | — | 4 |
| Lua | `lua` | tool | sì | — | 0 |
| Maestro | `maestro` | tool | sì | — | 1 |
| Material for MkDocs | `mkdocs-material` | tool | sì | — | 1 |
| MATLAB | `matlab` | tool | sì | — | 0 |
| Maven | `maven` | tool | sì | — | 24 |
| Mintlify | `mintlify` | tool | sì | — | 1 |
| Mocha | `mochajs` | tool | sì | — | 1 |
| Mockito | `mockito` | tool | sì | — | 4 |
| MockK | `mockk` | tool | sì | — | 1 |
| MockServer | `mockserver` | tool | sì | — | 0 |
| MSTest | `mstest` | tool | sì | — | 1 |
| NodeJS | `nodejs` | tool | sì | — | 66 |
| npm | `npm` | tool | sì | — | 0 |
| NuGet | `nuget` | tool | sì | — | 9 |
| NUnit | `nunit` | tool | sì | — | 1 |
| nvm | `nvm` | tool | sì | — | 0 |
| NX | `nxjs` | tool | sì | — | 1 |
| oapi-codegen | `oapi-codegen` | tool | sì | — | 1 |
| Objective-C | `objectivec` | tool | sì | — | 0 |
| OxLint | `oxlint` | tool | sì | — | 2 |
| Pact | `pact` | tool | sì | — | 1 |
| Parcel | `parceljs` | tool | sì | — | 0 |
| Perl | `perl` | tool | sì | — | 0 |
| PHP | `php` | tool | sì | — | 7 |
| PHP Pest | `phppest` | tool | sì | — | 0 |
| phpenv | `phpenv` | tool | sì | — | 0 |
| PHPStan | `phpstan` | tool | sì | — | 2 |
| PHPUnit | `phpunit` | tool | sì | — | 5 |
| pip | `pip` | tool | sì | — | 0 |
| pipenv | `pipenv` | tool | sì | — | 0 |
| Playwright | `playwright` | tool | sì | — | 15 |
| pnpm | `pnpm` | tool | sì | — | 10 |
| Podman | `podman` | tool | sì | — | 0 |
| Poetry | `poetry` | tool | sì | — | 0 |
| Prettier | `prettier` | tool | sì | — | 16 |
| Pulumi | `pulumi` | tool | sì | — | 0 |
| pytest | `pytest` | tool | sì | — | 11 |
| Python | `python` | tool | sì | — | 19 |
| Quinoa | `quinoa` | tool | sì | — | 1 |
| R | `r` | tool | sì | — | 0 |
| Read The Docs | `readthedocs` | tool | sì | — | 0 |
| Renovate | `renovate` | tool | sì | — | 6 |
| Reqnroll | `reqnroll` | tool | sì | — | 1 |
| REST Assured | `rest-assured` | tool | sì | — | 1 |
| Robolectric | `robolectric` | tool | sì | — | 2 |
| Rolldown | `rolldown` | tool | sì | — | 1 |
| Rollup | `rollup` | tool | sì | — | 4 |
| Rspack | `rspack` | tool | sì | — | 0 |
| RSpec | `rspec` | tool | sì | — | 3 |
| Rubocop | `rubocop` | tool | sì | — | 1 |
| Ruby | `ruby` | tool | sì | — | 6 |
| rubyenv | `rubyenv` | tool | sì | — | 0 |
| Ruff | `ruff` | tool | sì | — | 15 |
| Rust | `rust` | tool | sì | — | 17 |
| Scala | `scala` | tool | sì | — | 0 |
| ScalaTest | `scalatest` | tool | sì | — | 1 |
| SCSS | `scss` | tool | sì | — | 0 |
| setuptools | `setuptools` | tool | sì | — | 10 |
| SharpFuzz | `sharpfuzz` | tool | sì | — | 0 |
| SonarLint | `sonarlint` | tool | sì | — | 0 |
| sqlc | `sqlc` | tool | sì | — | 1 |
| SQLDelight | `sqldelight` | tool | sì | — | 1 |
| Storybook | `storybook` | tool | sì | — | 2 |
| Stylelint | `stylelint` | tool | sì | — | 2 |
| Stylus | `stylus` | tool | sì | — | 0 |
| SWC | `swc` | tool | sì | — | 4 |
| Swift | `swift` | tool | sì | — | 2 |
| Terraform | `terraform` | tool | sì | — | 4 |
| Terragrunt | `terragrunt` | tool | sì | — | 0 |
| Testcontainers | `testcontainers` | tool | sì | — | 4 |
| TestNG | `testng` | tool | sì | — | 1 |
| TravisCI | `travisci` | tool | sì | — | 1 |
| Turborepo | `turborepo` | tool | sì | — | 3 |
| Typescript | `typescript` | tool | sì | — | 39 |
| Ultracite | `ultracite` | tool | sì | — | 0 |
| UnoCSS | `unocss` | tool | sì | — | 2 |
| uv | `uv` | tool | sì | — | 1 |
| Vale | `vale` | tool | sì | — | 1 |
| Visual Basic .NET | `visualbasicnet` | tool | sì | — | 0 |
| Vite | `vite` | tool | sì | — | 20 |
| Vite+ | `vite-plus` | tool | sì | — | 1 |
| Vitest | `vitest` | tool | sì | — | 12 |
| Vue | `vuejs` | tool | sì | — | 0 |
| Vue SFC compiler | `vue-sfc-compiler` | tool | sì | — | 3 |
| Webpack | `webpack` | tool | sì | — | 3 |
| Webpack Encore | `webpack-encore` | tool | sì | — | 1 |
| WireMock | `wiremock-java` | tool | sì | — | 1 |
| XO | `xo` | tool | sì | — | 0 |
| xUnit | `xunit` | tool | sì | — | 4 |
| Yarn | `yarn` | tool | sì | — | 0 |
| Zig | `zig` | tool | sì | — | 0 |

</details>

## Servizi esterni

Le voci di servizio del catalogo: 833, 830 di `kind` `service` e 3 di `kind` `project` con la `category` `service` (un software che gira accanto al sistema e a cui il codice si connette); 722 con una regola del fork per riconoscerle, 453 con un marchio: 453 con il file nel prodotto (`mark`), 0 scaricato al primo uso dalla fonte ufficiale (`mark_source`); 35 hanno gli host con cui le si menziona negli URL (`hosts`). Di quelle con una regola, 3 hanno un'altra categoria (`tool` 3) e stanno nella lista della sezione precedente. Il riconoscimento misurato è la colonna Servizi della sezione precedente.

| Tipo | Voci | Con una regola del fork | Con marchio |
| --- | --- | --- | --- |
| servizio o API | 645 | 534 | 347 |
| database | 122 | 122 | 76 |
| autenticazione | 29 | 29 | 10 |
| gateway | 17 | 17 | 11 |
| coda | 14 | 14 | 9 |
| filesystem | 6 | 6 | 0 |

<details><summary>Servizi con una regola del fork: 719 voci</summary>

| Servizio | Id | Tipo | Host | Marchio | Fixture in cui lo step lo trova (27 novembre 2026) |
| --- | --- | --- | --- | --- | --- |
| 1Password | `1password` | servizio o API | — | sì | 0 |
| Activeloop | `activeloop` | servizio o API | — | sì | 0 |
| Adminer | `adminer` | servizio o API | — | sì | 2 |
| Adobe | `adobe` | servizio o API | — | no | 0 |
| Adobe Analytics | `adobe.analytics` | servizio o API | — | no | 0 |
| Adobe Commerce Cloud | `adobe.commercecloud` | servizio o API | — | no | 0 |
| Adobe Experience Manager | `adobe.experiencemanager` | servizio o API | — | no | 0 |
| Adyen | `adyen` | gateway | — | sì | 0 |
| AfterShip | `aftership` | servizio o API | — | sì | 0 |
| Agora | `agora` | servizio o API | — | sì | 0 |
| Airbrake | `airbrake` | servizio o API | — | sì | 0 |
| Airbyte | `airbyte` | servizio o API | — | sì | 0 |
| Aircall | `aircall` | servizio o API | — | sì | 0 |
| Airtable | `airtable` | servizio o API | — | sì | 0 |
| Akahu | `akahu` | servizio o API | — | no | 1 |
| Akamai | `akamai` | servizio o API | — | sì | 0 |
| Alby | `alby` | servizio o API | — | sì | 0 |
| Alchemy | `alchemy` | servizio o API | — | sì | 0 |
| Algolia | `algolia` | database | — | sì | 1 |
| Algorand | `algorand` | servizio o API | — | sì | 0 |
| Alibaba Cloud | `alibabacloud` | servizio o API | — | sì | 0 |
| Alipay | `alipay` | servizio o API | — | sì | 1 |
| Aliyun OSS | `aliyun-oss` | filesystem | — | no | 2 |
| Amplitude Analytics | `amplitude` | servizio o API | — | no | 0 |
| Anthropic | `anthropic` | servizio o API | — | sì | 1 |
| Apache Airflow | `apache_airflow` | servizio o API | — | sì | 0 |
| Apache Cassandra | `apache_cassandra` | database | — | sì | 0 |
| Apache CouchDB | `apache_couchdb` | database | — | sì | 0 |
| Apache Flink | `apache_flink` | servizio o API | — | sì | 0 |
| Apache Hadoop | `apache_hadoop` | database | — | sì | 0 |
| Apache Hive | `apache_hive` | database | — | sì | 0 |
| Apache Iceberg | `apache_iceberg` | database | — | no | 0 |
| Apache Kafka | `apache_kafka` | coda | — | sì | 2 |
| Apache Pulsar | `apache-pulsar` | coda | — | sì | 0 |
| Apache Solr | `apache_solr` | database | — | sì | 0 |
| Apache Spark | `apache_spark` | database | — | sì | 0 |
| Apache Storm | `apache_storm` | servizio o API | — | sì | 0 |
| Apicurio Registry | `apicurio-registry` | coda | — | no | 0 |
| Apideck | `apideck` | servizio o API | — | no | 0 |
| Apify | `apify` | servizio o API | — | no | 0 |
| App Store | `app-store` | servizio o API | — | sì | 0 |
| Apple | `apple` | servizio o API | — | sì | 1 |
| Apple Maps | `apple.maps` | servizio o API | — | no | 0 |
| AppSignal | `appsignal` | servizio o API | — | sì | 0 |
| AppVeyor | `appveyor` | servizio o API | — | sì | 0 |
| Appwrite | `appwrite` | servizio o API | — | sì | 0 |
| ArcGIS | `arcgis` | servizio o API | — | sì | 0 |
| Asana | `asana` | servizio o API | — | sì | 0 |
| Atlassian | `atlassian` | servizio o API | — | sì | 0 |
| Atlassian Bitbucket | `atlassian.bitbucket` | servizio o API | — | no | 0 |
| Atlassian OpsGenie | `atlassian.opsgenie` | servizio o API | — | no | 0 |
| Atlassian Trello | `atlassian.trello` | servizio o API | `api.trello.com` | no | 0 |
| Atuin Hub | `atuin-hub` | servizio o API | `hub.atuin.sh` | no | 0 |
| Atuin Sync | `atuin-sync` | servizio o API | `api.atuin.sh` | no | 0 |
| Auth0 | `auth0` | autenticazione | — | sì | 1 |
| AWS | `aws` | servizio o API | — | sì | 13 |
| AWS ActiveMQ | `aws.mq` | coda | — | sì | 0 |
| AWS Amplify Hosting | `aws.amplifyhosting` | servizio o API | — | sì | 0 |
| AWS Api Gateway | `aws.apigateway` | servizio o API | — | sì | 0 |
| AWS Athena | `aws.athena` | database | — | sì | 1 |
| AWS Bedrock | `aws.bedrock` | servizio o API | — | sì | 0 |
| AWS Block Storage | `aws.ebs` | database | — | sì | 0 |
| AWS CloudFront | `aws.cloudfront` | database | — | sì | 2 |
| AWS Cloudsearch | `aws.cloudsearch` | database | — | sì | 0 |
| AWS Cloudwatch | `aws.cloudwatch` | servizio o API | — | sì | 1 |
| AWS Code Build | `aws.codebuild` | servizio o API | — | sì | 0 |
| AWS Code Pipeline | `aws.codepipeline` | servizio o API | — | sì | 0 |
| AWS Cognito | `aws.cognito` | autenticazione | — | sì | 0 |
| AWS Comprehend | `aws.comprehend` | servizio o API | — | sì | 0 |
| AWS Compute | `aws.ec2` | servizio o API | — | sì | 0 |
| AWS Container | `aws.ecs` | servizio o API | — | sì | 1 |
| AWS Container Registry | `aws.ecr` | database | — | sì | 1 |
| AWS Document DB | `aws.documentdb` | database | — | sì | 0 |
| AWS DynamoDB | `aws.dynamodb` | database | — | sì | 1 |
| AWS ElastiCache | `aws.elasticache` | database | — | sì | 1 |
| AWS Fargate | `aws.fargate` | servizio o API | — | sì | 0 |
| AWS File System | `aws.efs` | database | — | sì | 0 |
| AWS Glacier | `aws.glacier` | database | — | sì | 0 |
| AWS Glue | `aws.glue` | servizio o API | — | sì | 1 |
| AWS Kafka | `aws.kafka` | coda | — | sì | 0 |
| AWS Kinesis | `aws.kinesis` | coda | — | sì | 0 |
| AWS Kms | `aws.kms` | servizio o API | — | sì | 1 |
| AWS Kubernetes | `aws.eks` | servizio o API | — | sì | 0 |
| AWS Lambda | `aws.lambda` | servizio o API | — | sì | 1 |
| AWS Lightsail | `aws.lightsail` | servizio o API | — | sì | 0 |
| AWS MemoryDB | `aws.memorydb` | database | — | sì | 0 |
| AWS Neptune | `aws.neptune` | database | — | sì | 0 |
| AWS Notification Service | `aws.sns` | servizio o API | — | sì | 1 |
| AWS Opensearch | `aws.opensearch` | database | — | sì | 0 |
| AWS Polly | `aws.polly` | servizio o API | — | sì | 0 |
| AWS RDS | `aws.rds` | database | — | sì | 0 |
| AWS Redshift | `aws.redshift` | database | — | sì | 0 |
| AWS Rekognition | `aws.rekognition` | servizio o API | — | sì | 0 |
| AWS S3 | `aws.s3` | database | — | sì | 12 |
| AWS SageMaker | `aws.sagemaker` | servizio o API | — | sì | 0 |
| AWS Secrets Manager | `aws.secretsmanager` | database | — | sì | 2 |
| AWS Simple Email Service | `aws.ses` | servizio o API | — | sì | 1 |
| AWS SQS | `aws.sqs` | coda | — | sì | 2 |
| AWS Step Functions | `aws.sfn` | servizio o API | — | sì | 0 |
| AWS Timestream | `aws.timestream` | database | — | sì | 0 |
| AWS Transcribe | `aws.transcribe` | servizio o API | — | sì | 0 |
| AWS Translate | `aws.translate` | servizio o API | — | sì | 0 |
| Azure | `azure` | servizio o API | — | sì | 7 |
| Azure AI Document Intelligence | `azure.documentintelligence` | servizio o API | — | no | 1 |
| Azure App Service | `azure.appservice` | servizio o API | — | no | 0 |
| Azure Application Insights | `azure.applicationinsights` | servizio o API | — | no | 0 |
| Azure Blob Storage | `azure.blobstorage` | filesystem | — | no | 2 |
| Azure Container Apps | `azure.containerapps` | servizio o API | — | no | 2 |
| Azure Cosmos DB | `azure.cosmosdb` | database | — | sì | 0 |
| Azure Functions | `azure.functions` | servizio o API | — | sì | 0 |
| Azure Key Vault | `azure.keyvault` | servizio o API | — | no | 1 |
| Azure Kubernetes | `azure.aks` | servizio o API | — | sì | 0 |
| Azure MariaDB | `azure.mariadb` | database | — | sì | 0 |
| Azure MySQL | `azure.mysql` | database | — | sì | 0 |
| Azure Openai | `azure.openai` | servizio o API | — | sì | 1 |
| Azure Postgres | `azure.postgres` | database | — | sì | 0 |
| Azure Redis | `azure.redis` | database | — | sì | 0 |
| Azure SQL | `azure.sql` | database | — | sì | 0 |
| Azure Static Web Apps | `azure.staticwebapps` | servizio o API | — | sì | 1 |
| Azure Storage | `azure.storage` | database | — | sì | 0 |
| AzureCI | `azure.ci` | servizio o API | — | sì | 0 |
| Backblaze | `backblaze` | servizio o API | — | sì | 0 |
| Backendless | `backendless` | servizio o API | — | sì | 0 |
| Base44 | `base44` | servizio o API | — | no | 0 |
| Beehiiv | `beehiiv` | servizio o API | — | no | 0 |
| Better Auth | `betterauth` | autenticazione | — | sì | 1 |
| Better Stack | `betterstack` | servizio o API | — | sì | 0 |
| BigCommerce | `bigcommerce` | servizio o API | — | sì | 0 |
| Binance | `binance` | servizio o API | — | sì | 0 |
| Bing Maps | `azure.maps` | servizio o API | — | sì | 0 |
| Bitbucket Pipelines | `atlassian.bitbucketpipelines` | servizio o API | — | no | 0 |
| Bitly | `bitly` | servizio o API | — | sì | 0 |
| Bitwarden | `bitwarden` | servizio o API | — | sì | 0 |
| Blackfire | `blackfire` | servizio o API | — | no | 0 |
| Bluesky | `bluesky` | servizio o API | — | sì | 0 |
| Boto3 | `boto3` | servizio o API | — | no | 5 |
| Box | `box` | servizio o API | — | sì | 0 |
| Braintree | `braintree` | servizio o API | — | sì | 0 |
| Braintrust | `braintrust` | servizio o API | — | sì | 0 |
| Brevo | `brevo` | servizio o API | — | sì | 0 |
| Browser Use | `browseruse` | servizio o API | — | no | 0 |
| Browserbase | `browerbase` | servizio o API | — | no | 0 |
| Browserless | `browserless` | servizio o API | — | no | 0 |
| Browserstack | `browserstack` | servizio o API | — | no | 1 |
| Bugsnag | `bugsnag` | servizio o API | — | no | 0 |
| bunq | `bunq` | servizio o API | — | sì | 0 |
| Caddy | `caddy` | servizio o API | — | sì | 3 |
| Cal.com | `calcom` | servizio o API | — | sì | 0 |
| Calendly | `calendly` | servizio o API | — | sì | 0 |
| Campaign Monitor | `campaign-monitor` | servizio o API | — | sì | 0 |
| Camunda | `camunda` | servizio o API | — | sì | 0 |
| Chargebee | `chargebee` | gateway | — | no | 0 |
| ChartMogul | `chartmogul` | servizio o API | — | sì | 0 |
| Checkov | `checkov` | servizio o API | — | sì | 0 |
| ChromaDB | `chromadb` | database | — | no | 0 |
| Chromatic | `chromatic` | servizio o API | — | sì | 1 |
| CircleCI | `circleci` | servizio o API | — | sì | 0 |
| CirrusCI | `cirrusci` | servizio o API | — | sì | 0 |
| Civo | `civo` | servizio o API | — | sì | 0 |
| Clerk | `clerk` | autenticazione | — | sì | 0 |
| ClickHouse | `clickhouse` | database | — | sì | 2 |
| ClickSend | `clicksend` | servizio o API | — | no | 0 |
| ClickUp | `clickup` | servizio o API | — | sì | 0 |
| Cloud AI Platform | `gcp.aiplatform` | servizio o API | — | sì | 0 |
| Cloud Artifact Registry | `gcp.artifactregistry` | database | — | sì | 1 |
| Cloud BigQuery | `gcp.bigquery` | database | — | sì | 0 |
| Cloud BigTable | `gcp.bigtable` | database | — | sì | 0 |
| Cloud Build | `gcp.cloudbuild` | servizio o API | — | sì | 1 |
| Cloud Container Registry | `gcp.containerregistry` | database | — | no | 0 |
| Cloud Dataflow | `gcp.dataflow` | servizio o API | — | sì | 0 |
| Cloud Dataproc | `gcp.dataproc` | servizio o API | — | sì | 0 |
| Cloud Datastore | `gcp.datastore` | database | — | sì | 0 |
| Cloud Dialogflow | `gcp.dialogflow` | servizio o API | — | sì | 0 |
| Cloud Functions | `gcp.functions` | servizio o API | — | sì | 0 |
| Cloud Functions for Firebase | `firebase.functions` | servizio o API | — | no | 1 |
| Cloud KMS | `gcp.kms` | servizio o API | — | sì | 1 |
| Cloud Language | `gcp.language` | servizio o API | — | sì | 0 |
| Cloud Logging | `gcp.logging` | servizio o API | — | sì | 0 |
| Cloud Memorystore | `gcp.memorystore` | database | — | sì | 0 |
| Cloud Run | `gcp.cloudrun` | servizio o API | — | sì | 0 |
| Cloud Secret Manager | `gcp.secretmanager` | database | — | sì | 1 |
| Cloud Spanner | `gcp.spanner` | database | — | sì | 0 |
| Cloud Speech | `gcp.speech` | servizio o API | — | sì | 0 |
| Cloud SQL | `gcp.sql` | database | — | sì | 0 |
| Cloud Storage | `gcp.gcs` | database | — | sì | 3 |
| Cloud Tasks | `gcp.tasks` | servizio o API | — | sì | 0 |
| Cloud Vision | `gcp.vision` | servizio o API | — | sì | 0 |
| CloudBees | `cloudbees` | servizio o API | — | sì | 0 |
| CloudBees Codeship | `cloudbees.codeship` | servizio o API | — | no | 0 |
| Cloudflare | `cloudflare` | servizio o API | — | sì | 2 |
| Cloudflare Pages | `cloudflare.pages` | servizio o API | — | sì | 0 |
| Cloudflare R2 | `cloudflare.r2` | database | — | no | 0 |
| Cloudflare Turnstile | `cloudflare.turnstile` | servizio o API | — | no | 1 |
| Cloudflare Workers | `cloudflare.workers` | servizio o API | — | sì | 1 |
| Cloudinary | `cloudinary` | servizio o API | — | sì | 0 |
| Cockroach Labs | `cockroach-labs` | database | — | sì | 0 |
| CockroachDB | `cockroachdb` | database | — | no | 0 |
| Code Climate | `codeclimate` | servizio o API | — | sì | 0 |
| Codecov | `codecov` | servizio o API | — | sì | 5 |
| CodeSandbox | `codesandbox` | servizio o API | — | sì | 0 |
| CodeSandboxCI | `codesandboxci` | servizio o API | — | no | 0 |
| Cohere AI | `cohereai` | servizio o API | — | no | 0 |
| Coinbase | `coinbase` | servizio o API | — | sì | 0 |
| Commercetools | `commercetools` | servizio o API | — | no | 0 |
| Composio | `composio` | servizio o API | — | no | 0 |
| Concourse CI | `concourseci` | servizio o API | — | no | 0 |
| Conekta | `conekta` | servizio o API | — | sì | 0 |
| Confluence | `atlassian.confluence` | servizio o API | — | sì | 0 |
| Consul | `consul` | servizio o API | — | sì | 0 |
| Contentful | `contentful` | servizio o API | — | sì | 0 |
| Contentstack | `contentstack` | servizio o API | — | sì | 0 |
| Convex | `convexdb` | database | — | sì | 0 |
| CoreDNS | `coredns` | servizio o API | — | no | 0 |
| Couchbase | `couchbase` | database | — | sì | 0 |
| Coveralls | `coveralls` | servizio o API | — | sì | 1 |
| Coze | `coze` | servizio o API | — | sì | 0 |
| CrateDB | `cratedb` | database | — | sì | 0 |
| Crawl4AI | `crawl4ai` | servizio o API | — | no | 0 |
| Crowdin | `crowdin` | servizio o API | — | sì | 6 |
| D-Wave Systems | `d-wave-systems` | servizio o API | — | sì | 0 |
| Databricks | `databricks` | servizio o API | — | sì | 0 |
| Databuddy | `databuddy` | servizio o API | — | no | 0 |
| Datadog | `datadog` | servizio o API | — | sì | 1 |
| DataDome | `datadome` | servizio o API | — | no | 0 |
| Datafast | `datafast` | servizio o API | — | no | 0 |
| Dataiku | `dataiku` | servizio o API | — | sì | 0 |
| Datastax | `datastax` | database | — | sì | 0 |
| Dato CMS | `datocms` | servizio o API | — | sì | 0 |
| Deepgram | `deepgram` | servizio o API | — | sì | 0 |
| DeepL | `deepl` | servizio o API | — | sì | 0 |
| Deepseek | `deepseek` | servizio o API | — | sì | 0 |
| Deepsource | `deepsource` | servizio o API | — | no | 0 |
| Deno Deploy | `denodeploy` | servizio o API | — | sì | 0 |
| Dependabot | `dependabot` | servizio o API | — | sì | 0 |
| Depot.dev | `depotdev` | servizio o API | — | no | 2 |
| diagrams.net | `diagrams-net` | servizio o API | `embed.diagrams.net` | sì | 0 |
| DigitalOcean | `digitalocean` | servizio o API | — | sì | 0 |
| Directus | `directus` | servizio o API | — | sì | 0 |
| Discord | `discord` | servizio o API | — | sì | 1 |
| Discord OAuth | `discord.oauth` | autenticazione | — | no | 1 |
| Discourse | `discourse` | servizio o API | — | sì | 0 |
| Docusign | `docusign` | servizio o API | — | no | 0 |
| Dodo Payments | `dodo-payments` | servizio o API | — | sì | 0 |
| Dokku | `dokku` | servizio o API | — | sì | 0 |
| DroneCI | `droneci` | servizio o API | — | no | 0 |
| Dropbox | `dropbox` | servizio o API | — | sì | 1 |
| Drupal | `drupal` | servizio o API | — | sì | 0 |
| DuckDB | `duckdb` | database | — | sì | 0 |
| DuckDuckGo Icons | `duckduckgo-icons` | servizio o API | `icons.duckduckgo.com` | no | 0 |
| Dynatrace | `dynatrace` | servizio o API | — | sì | 0 |
| eID Easy | `eideasy` | servizio o API | `id.eideasy.com` | no | 1 |
| Elastic Cloud | `elasticcloud` | servizio o API | — | sì | 0 |
| Elasticsearch | `elasticsearch` | database | — | sì | 3 |
| Elevenlabs | `elevenlabs` | servizio o API | — | sì | 0 |
| Enable Banking | `enable-banking` | servizio o API | `api.enablebanking.com` | no | 0 |
| Envoy | `envoy` | gateway | — | no | 1 |
| Equinix | `equinix` | servizio o API | — | no | 0 |
| etcd | `etcd` | database | — | sì | 0 |
| Event Store | `event-store` | database | — | sì | 0 |
| Evernote | `evernote` | servizio o API | — | sì | 0 |
| Expo.dev | `expodev` | servizio o API | — | sì | 0 |
| Fabric | `fabric` | servizio o API | — | no | 0 |
| Facebook | `facebook` | servizio o API | — | sì | 0 |
| FastAPI Cloud | `fastapi-cloud` | servizio o API | — | no | 0 |
| Fastly | `fastly` | servizio o API | — | sì | 0 |
| Fathom | `fathom` | servizio o API | — | sì | 0 |
| Figma | `figma` | servizio o API | — | sì | 0 |
| Firebase | `firebase` | servizio o API | — | sì | 4 |
| Firebase Analytics | `firebase.analytics` | servizio o API | — | no | 1 |
| Firebase Cloud Messaging | `firebase.messaging` | servizio o API | — | no | 2 |
| Firebase Firestore | `firebase.firestore` | database | — | no | 0 |
| Firecrawl | `firecrawl` | servizio o API | — | no | 1 |
| Firepit | `firepit` | servizio o API | — | no | 0 |
| flagd | `flagd` | servizio o API | — | no | 1 |
| Fluentd | `fluentd` | servizio o API | — | sì | 1 |
| Flyio | `flyio` | servizio o API | — | sì | 1 |
| Formbricks | `formbricks` | servizio o API | — | sì | 0 |
| FoundationDB | `foundationdb` | database | — | no | 0 |
| Freshdesk | `freshdesk` | servizio o API | — | no | 0 |
| Friendly Captcha | `friendly-captcha` | servizio o API | — | no | 1 |
| Frontegg | `frontegg` | autenticazione | — | no | 0 |
| Fusionauth | `fusionauth` | autenticazione | — | sì | 0 |
| GCP | `gcp` | servizio o API | — | sì | 6 |
| Gemini AI | `geminiai` | servizio o API | `generativelanguage.googleapis.com` | no | 0 |
| Ghost | `ghost` | servizio o API | — | sì | 0 |
| GIPHY | `giphy` | servizio o API | — | sì | 0 |
| Gitbook | `gitbook` | servizio o API | — | sì | 0 |
| Gitea | `gitea` | servizio o API | — | sì | 0 |
| GitGuardian | `gitguardian` | servizio o API | — | no | 0 |
| GitHub | `github` | servizio o API | `api.github.com` | sì | 1 |
| Github Actions | `github.actions` | servizio o API | — | sì | 0 |
| GitHub CodeQL | `github.codeql` | servizio o API | — | no | 0 |
| GitHub OAuth | `github.oauth` | autenticazione | — | no | 2 |
| Github Pages | `github.pages` | servizio o API | — | sì | 7 |
| Gitlab | `gitlab` | servizio o API | — | sì | 0 |
| Gitlab CI | `gitlab.ci` | servizio o API | — | no | 0 |
| GitLab OAuth | `gitlab.oauth` | autenticazione | — | no | 1 |
| Gmail | `google.gmail` | servizio o API | — | sì | 0 |
| GoCardless Bank Account Data | `gocardless-bank-account-data` | servizio o API | `bankaccountdata.gocardless.com` | no | 0 |
| Google | `google` | servizio o API | — | sì | 3 |
| Google Ads | `google-ads` | servizio o API | — | sì | 0 |
| Google Analytics | `google.analytics` | servizio o API | `analyticsadmin.googleapis.com` `analyticsdata.googleapis.com` | sì | 0 |
| Google App Engine | `gcp.appengine` | servizio o API | — | sì | 0 |
| Google Calendar | `google.calendar` | servizio o API | — | sì | 0 |
| Google Chat | `google.chat` | servizio o API | — | sì | 0 |
| Google Compute | `gcp.gce` | servizio o API | — | sì | 2 |
| Google DNS | `gcp.dns` | servizio o API | — | sì | 0 |
| Google Docs | `google.docs` | servizio o API | — | sì | 0 |
| Google Drive | `google.drive` | servizio o API | — | sì | 0 |
| Google Earth Engine | `google-earth-engine` | servizio o API | — | sì | 0 |
| Google Forms | `google.forms` | servizio o API | — | sì | 0 |
| Google Keep | `google.keep` | servizio o API | — | sì | 0 |
| Google Kubernetes | `gcp.gke` | servizio o API | — | sì | 0 |
| Google Maps | `gcp.maps` | servizio o API | — | sì | 0 |
| Google Meet | `google.meet` | servizio o API | — | sì | 0 |
| Google OAuth | `google.oauth` | autenticazione | — | no | 1 |
| Google Pay | `google.pay` | gateway | — | sì | 0 |
| Google reCAPTCHA | `google.recaptcha` | servizio o API | — | no | 1 |
| Google Sheets | `google.sheets` | servizio o API | — | sì | 0 |
| Google Slides | `google.slides` | servizio o API | — | sì | 0 |
| Google Tasks | `google.tasks` | servizio o API | — | sì | 0 |
| Google Translate | `gcp.translate` | servizio o API | — | sì | 0 |
| Gotenberg | `gotenberg` | servizio o API | — | no | 2 |
| Grafana | `grafana` | servizio o API | — | sì | 2 |
| Grafana LGTM | `grafana.lgtm` | servizio o API | — | no | 0 |
| Gravatar | `gravatar` | servizio o API | — | sì | 0 |
| Graylog | `graylog` | servizio o API | — | sì | 0 |
| GreenMail | `greenmail` | servizio o API | — | no | 1 |
| Groq | `groq` | servizio o API | — | no | 0 |
| H2 | `h2` | database | — | no | 3 |
| Hanko | `hanko` | autenticazione | — | no | 0 |
| HAProxy | `haproxy` | servizio o API | — | sì | 0 |
| hCaptcha | `hcaptcha` | servizio o API | — | no | 0 |
| Healthchecks.io | `healthchecksio` | servizio o API | `hc-ping.com` | no | 0 |
| Help Scout | `help-scout` | servizio o API | — | sì | 0 |
| HERE Maps | `heremaps` | servizio o API | — | no | 0 |
| Heroku | `heroku` | servizio o API | — | no | 0 |
| Hetzner | `hetzner` | servizio o API | — | sì | 0 |
| Honeybadger | `honeybadger` | servizio o API | — | sì | 0 |
| Honeycomb | `honeycomb` | servizio o API | — | no | 0 |
| Hostinger | `hostinger` | servizio o API | — | sì | 0 |
| Hotjar | `hotjar` | servizio o API | — | sì | 0 |
| HSQLDB | `hsqldb` | database | — | no | 1 |
| HTTPD | `httpd` | servizio o API | — | no | 0 |
| Huawei Cloud OBS | `huawei-obs` | filesystem | — | no | 1 |
| HubSpot | `hubspot` | servizio o API | — | sì | 0 |
| Hugging Face | `huggingface` | servizio o API | — | sì | 1 |
| HyperDX | `hyperdx` | servizio o API | — | no | 0 |
| Hypertune | `hypertune` | servizio o API | — | no | 0 |
| IBM Cloud | `ibmcloud` | servizio o API | — | no | 0 |
| ifttt | `ifttt` | servizio o API | — | sì | 0 |
| Immich | `immich` | servizio o API | — | sì | 0 |
| Inbucket | `inbucket` | servizio o API | — | no | 1 |
| Infisical | `infisical` | servizio o API | — | no | 0 |
| InfluxDB | `influxdb` | database | — | sì | 0 |
| Inngest | `inngest` | servizio o API | — | no | 1 |
| Instagram | `instagram` | servizio o API | — | sì | 0 |
| Instana | `instana` | servizio o API | — | no | 1 |
| Integration.app | `integrationapp` | servizio o API | — | no | 0 |
| Intercom | `intercom` | servizio o API | — | sì | 0 |
| Internet Archive | `internet-archive` | servizio o API | — | sì | 0 |
| Internet Computer | `internet-computer` | servizio o API | — | sì | 0 |
| Intuit | `intuit` | gateway | — | sì | 0 |
| Ionos | `ionos` | servizio o API | — | sì | 0 |
| IOTA | `iota` | servizio o API | — | sì | 0 |
| IPinfo | `ipinfo` | servizio o API | `api.ipinfo.io` | no | 0 |
| Jaeger | `jaeger` | servizio o API | — | sì | 0 |
| Jellyfin | `jellyfin` | servizio o API | — | sì | 1 |
| Jenkins | `jenkins` | servizio o API | — | sì | 0 |
| JFrog | `jfrog` | servizio o API | — | sì | 0 |
| JHipster Control Center | `jhipster-control-center` | servizio o API | — | no | 0 |
| Jira | `atlassian.jira` | servizio o API | — | sì | 0 |
| Jira Software | `jira-software` | servizio o API | — | sì | 0 |
| Jitsi | `jitsi` | servizio o API | — | sì | 0 |
| Joomla! | `joomla` | servizio o API | — | sì | 0 |
| Kaggle | `kaggle` | servizio o API | — | sì | 0 |
| Keeper | `keeper` | servizio o API | — | sì | 0 |
| Kentico | `kentico` | servizio o API | — | sì | 0 |
| Keycloak | `keycloak` | autenticazione | — | sì | 0 |
| Kibana | `kibana` | servizio o API | — | sì | 1 |
| Kinde | `kinde` | autenticazione | — | no | 0 |
| Klarna | `klarna` | gateway | — | sì | 0 |
| Klaviyo | `klaviyo` | servizio o API | — | no | 0 |
| Koala Analytics | `koalaanalytics` | servizio o API | — | no | 0 |
| Kong | `kong` | servizio o API | — | sì | 0 |
| Koyeb | `koyeb` | servizio o API | — | sì | 0 |
| Kubernetes | `kubernetes` | servizio o API | — | sì | 2 |
| Lago | `lago` | servizio o API | — | no | 0 |
| LangChain Corporate | `langchain-corporate` | servizio o API | — | sì | 1 |
| Laravel Nightwatch | `laravel-nightwatch` | servizio o API | — | no | 1 |
| Last.fm | `lastfm` | servizio o API | `ws.audioscrobbler.com` | sì | 0 |
| LaunchDarkly | `launchdarkly` | servizio o API | — | no | 0 |
| Lemon Squeezy | `lemonsqueezy` | gateway | `api.lemonsqueezy.com` | sì | 0 |
| Let's Encrypt | `lets-encrypt` | servizio o API | `acme-v02.api.letsencrypt.org` | sì | 0 |
| libSQL | `libsql` | database | — | no | 0 |
| LINE | `line` | servizio o API | — | sì | 0 |
| Linear | `linear` | servizio o API | — | sì | 0 |
| Linkedin | `linkedin` | servizio o API | — | no | 0 |
| ListenBrainz | `listenbrainz` | servizio o API | `api.listenbrainz.org` `labs.api.listenbrainz.org` | no | 0 |
| LiteFS | `litefs` | database | — | no | 1 |
| LiveChat | `livechat` | servizio o API | — | sì | 0 |
| LiveKit | `livekit` | servizio o API | — | sì | 1 |
| LM Studio | `lm-studio` | servizio o API | — | sì | 0 |
| LogRocket | `logrocket` | servizio o API | — | no | 0 |
| LogSnag | `logsnag` | servizio o API | — | no | 0 |
| Logstash | `logstash` | servizio o API | — | sì | 1 |
| Logto | `logtoio` | autenticazione | — | no | 0 |
| Looker | `looker` | servizio o API | — | sì | 0 |
| Loom | `loom` | servizio o API | — | sì | 0 |
| Loops | `loops` | servizio o API | — | sì | 0 |
| Lovable | `lovable` | servizio o API | — | no | 0 |
| Magento | `magento` | servizio o API | — | no | 0 |
| Magic | `magic` | autenticazione | — | sì | 0 |
| MailChannels | `mailchannels` | servizio o API | — | no | 0 |
| Mailchimp | `mailchimp` | servizio o API | — | sì | 0 |
| MailDev | `maildev` | servizio o API | — | no | 0 |
| Mailgun | `mailgun` | servizio o API | — | sì | 0 |
| Mailhog | `mailhog` | servizio o API | — | no | 1 |
| Mailjet | `mailjet` | servizio o API | — | no | 0 |
| Mailpit | `mailpit` | servizio o API | — | no | 2 |
| Mailtrap | `mailtrap` | servizio o API | — | sì | 0 |
| MajorLeagueCyber | `majorleaguecyber` | servizio o API | `api.majorleaguecyber.org` `auth.majorleaguecyber.org` | no | 0 |
| Mandrill | `mandrill` | servizio o API | — | no | 0 |
| Mapbox | `mapbox` | servizio o API | — | sì | 0 |
| MapTiler | `maptiler` | servizio o API | — | sì | 0 |
| MariaDB | `mariadb` | database | — | sì | 2 |
| Matomo | `matomo` | servizio o API | — | sì | 0 |
| Matrix | `matrix` | servizio o API | — | sì | 0 |
| Mattermost | `mattermost` | servizio o API | — | sì | 0 |
| MaxMind | `maxmind` | servizio o API | — | no | 0 |
| Meilisearch | `meilisearch` | database | — | sì | 2 |
| Meilisearch Cloud | `meilisearchcloud` | database | — | no | 0 |
| Memcached | `memcached` | database | — | no | 0 |
| Mercado Pago | `mercado-pago` | servizio o API | — | sì | 0 |
| Merge.dev | `mergedev` | servizio o API | — | no | 0 |
| Metabase | `metabase` | servizio o API | — | sì | 0 |
| Microsoft | `microsoft` | servizio o API | — | no | 1 |
| Microsoft Entra ID OAuth | `microsoft-entra-oauth` | autenticazione | — | no | 1 |
| Microsoft OAuth | `microsoft.oauth` | autenticazione | — | no | 1 |
| Microsoft Outlook | `microsoft.outlook` | servizio o API | — | no | 0 |
| Microsoft SQL Server | `microsoft-sql-server` | database | — | no | 2 |
| MicroStrategy | `microstrategy` | servizio o API | — | sì | 0 |
| MilvusDB | `milvusdb` | database | — | no | 0 |
| MinIO | `minio` | database | — | sì | 2 |
| Miro | `miro` | servizio o API | — | sì | 0 |
| Mistral AI | `mistralai` | servizio o API | — | sì | 0 |
| Mixpanel | `mixpanel` | servizio o API | — | sì | 0 |
| mock-oauth2-server | `mock-oauth2-server` | autenticazione | — | no | 1 |
| Modal | `modal` | servizio o API | — | sì | 0 |
| ModelScope | `modelscope` | servizio o API | — | sì | 0 |
| Monday | `monday` | servizio o API | — | no | 0 |
| Mongo Express | `mongoexpress` | servizio o API | — | no | 2 |
| MongoDB | `mongodb` | database | — | sì | 5 |
| MongoDB Atlas | `mongodbatlas` | servizio o API | — | no | 0 |
| MS SQL | `mssql` | database | — | no | 0 |
| MusicBrainz | `musicbrainz` | servizio o API | — | sì | 0 |
| Mysql | `mysql` | database | — | sì | 13 |
| n8n | `n8n` | servizio o API | — | sì | 0 |
| Nango | `nango` | servizio o API | — | no | 0 |
| Nats | `nats` | coda | — | no | 0 |
| Neo4j | `neo4j` | database | — | sì | 0 |
| NeonDB | `neondb` | database | — | no | 0 |
| NetBox Census | `netbox-census` | servizio o API | `census.netbox.oss.netboxlabs.com` | no | 0 |
| NetBox Copilot | `netbox-copilot` | servizio o API | `static.copilot.netboxlabs.ai` | no | 0 |
| Netlify | `netlify` | servizio o API | — | sì | 3 |
| New Relic | `newrelic` | servizio o API | — | sì | 0 |
| Nextcloud | `nextcloud` | servizio o API | — | sì | 0 |
| Nginx | `nginx` | servizio o API | — | sì | 7 |
| Nhost | `nhost` | servizio o API | — | sì | 0 |
| Nomad | `nomad` | servizio o API | — | sì | 0 |
| Notion | `notion` | servizio o API | — | sì | 0 |
| Novy | `novu` | servizio o API | — | sì | 0 |
| NX Cloud | `nxcloud` | servizio o API | — | no | 0 |
| Oceanbase | `oceanbase` | database | — | sì | 0 |
| Okta | `okta` | autenticazione | — | sì | 1 |
| Okta OAuth | `okta.oauth` | autenticazione | — | no | 1 |
| Ollama | `ollama` | servizio o API | — | sì | 2 |
| OMDb | `omdb` | servizio o API | `www.omdbapi.com` | no | 0 |
| OneDrive | `microsoft.onedrive` | servizio o API | — | no | 0 |
| OnlineOrNot | `onlineornot` | servizio o API | — | no | 0 |
| Open Food Facts | `open-food-facts` | servizio o API | — | no | 1 |
| Openai | `openai` | servizio o API | `api.openai.com` | no | 6 |
| OpenCage | `opencage` | servizio o API | — | sì | 0 |
| OpenLDAP | `openldap` | autenticazione | — | no | 1 |
| OpenRouter | `openrouter` | gateway | — | sì | 0 |
| OpenSea | `opensea` | servizio o API | — | sì | 0 |
| OpenSearch | `opensearch` | database | — | sì | 1 |
| OpenStack Swift | `openstack.swift` | filesystem | — | no | 1 |
| OpenTelemetry Collector | `otel-collector` | servizio o API | — | no | 0 |
| OpenTelemetry eBPF Profiler | `otel-ebpf-profiler` | servizio o API | — | no | 0 |
| OpenZeppelin | `openzeppelin` | servizio o API | — | sì | 0 |
| Opsgenie | `opsgenie` | servizio o API | `api.eu.opsgenie.com` `api.opsgenie.com` | sì | 0 |
| Optimizely | `optimizely` | servizio o API | — | no | 0 |
| Oracle Cloud | `oraclecloud` | servizio o API | — | no | 0 |
| Oracle Database | `oracledatabase` | database | — | no | 1 |
| Orb | `withorb` | servizio o API | — | no | 0 |
| Ory | `orysh` | autenticazione | — | sì | 0 |
| OVH | `ovh` | servizio o API | — | sì | 0 |
| OVH Database | `ovh.database` | database | — | no | 0 |
| OVH Dedicated Server | `ovh.dedicated` | servizio o API | — | no | 0 |
| OVH Kubernetes | `ovh.kubernetes` | servizio o API | — | no | 0 |
| OVH Storage | `ovh.storage` | database | — | no | 0 |
| OVH VPS | `ovh.vps` | servizio o API | — | no | 0 |
| Paddle | `paddle` | gateway | `api.paddle.com` `sandbox-api.paddle.com` | sì | 0 |
| Pagerduty | `pagerduty` | servizio o API | `events.pagerduty.com` | sì | 0 |
| PagerTree | `pagertree` | servizio o API | — | no | 0 |
| Papercut SMTP | `papercut-smtp` | servizio o API | — | no | 0 |
| Papertrail | `papertrail` | servizio o API | — | no | 0 |
| Paragon | `useparagon` | servizio o API | — | no | 0 |
| Patreon | `patreon` | servizio o API | — | sì | 0 |
| Payload | `payloadcms` | servizio o API | — | sì | 0 |
| Paypal | `paypal` | gateway | — | sì | 0 |
| Paystack | `paystack` | gateway | — | no | 0 |
| Percona | `percona` | database | — | no | 0 |
| Percy | `percy` | servizio o API | — | sì | 0 |
| Perplexity | `perplexity` | servizio o API | — | sì | 0 |
| Perplexity AI | `perplexityai` | servizio o API | — | no | 0 |
| Pexels | `pexels` | servizio o API | — | sì | 0 |
| Pinecone | `pinecone` | database | — | sì | 0 |
| Pingdom | `pingdom` | servizio o API | — | sì | 0 |
| Pirsch Analytics | `pirschanalytics` | servizio o API | — | no | 0 |
| PlaceKit | `placekit` | servizio o API | — | no | 0 |
| Plain | `plain` | servizio o API | — | no | 1 |
| PlanetScale | `planetscale` | database | — | sì | 0 |
| Platform.sh | `platformsh` | servizio o API | — | sì | 0 |
| Plausible | `plausible` | servizio o API | — | no | 1 |
| Pluggy | `pluggy` | servizio o API | — | no | 1 |
| PocketBase | `pocketbase` | database | — | sì | 0 |
| Poe | `poe` | servizio o API | — | sì | 0 |
| Polar | `polarsh` | gateway | — | no | 1 |
| Polkadot | `polkadot` | servizio o API | — | sì | 0 |
| Postgres | `postgresql` | database | — | sì | 38 |
| Postgrest | `postgrest` | servizio o API | — | no | 0 |
| PostHog | `posthog` | servizio o API | — | sì | 3 |
| Postman | `postman` | servizio o API | — | sì | 0 |
| Postmark | `postmark` | servizio o API | — | no | 1 |
| PowerSync | `powersync` | servizio o API | — | no | 0 |
| Prestashop | `prestashop` | servizio o API | — | sì | 0 |
| Prisma Cloud | `prismacloud` | servizio o API | — | no | 0 |
| Prismic | `prismic` | servizio o API | — | sì | 0 |
| Prometheus | `prometheus` | servizio o API | — | sì | 7 |
| PropelAuth | `propelauth` | autenticazione | — | no | 0 |
| PubSub | `gcp.pubsub` | coda | — | sì | 0 |
| Puppeteer | `puppeteer` | servizio o API | — | sì | 1 |
| Pushbullet | `pushbullet` | servizio o API | `api.pushbullet.com` | sì | 0 |
| Pusher | `pusher` | servizio o API | — | sì | 1 |
| Pushover | `pushover` | servizio o API | `api.pushover.net` | no | 0 |
| Qase | `qase` | servizio o API | — | sì | 0 |
| Qdrant | `qdrant` | database | — | sì | 0 |
| Qlik | `qlik` | servizio o API | — | sì | 0 |
| Qovery | `qovery` | servizio o API | — | no | 0 |
| Qovery Cluster | `qovery.cluster` | servizio o API | — | no | 0 |
| Qovery Database | `qovery.database` | database | — | no | 0 |
| QuestDB | `questdb` | database | — | no | 0 |
| RabbitMQ | `rabbitmq` | coda | — | sì | 5 |
| Railway | `railway` | servizio o API | — | sì | 1 |
| Railway MongoDB | `railway.mongodb` | database | — | no | 0 |
| Railway MySQL | `railway.mysql` | database | — | no | 0 |
| Railway Postgres | `railway.postgres` | database | — | no | 0 |
| Railway Redis | `railway.redis` | database | — | no | 0 |
| Rarible | `rarible` | servizio o API | — | sì | 0 |
| Razorpay | `razorpay` | servizio o API | — | sì | 0 |
| ReadMe | `readme` | servizio o API | — | sì | 0 |
| Reddit | `reddit` | servizio o API | — | sì | 0 |
| Redis | `redis` | database | — | sì | 24 |
| RelativeCI | `relativeci` | servizio o API | — | no | 0 |
| remove.bg | `removebg` | servizio o API | — | sì | 0 |
| Render | `render` | servizio o API | — | sì | 2 |
| Replicate | `replicate` | servizio o API | — | sì | 0 |
| Replit | `replit` | servizio o API | — | sì | 0 |
| Replit Database | `replit.database` | database | — | no | 0 |
| Replit Postgres | `replit.postgres` | database | — | no | 0 |
| Resend | `resend` | servizio o API | — | sì | 1 |
| RethinkDB | `rethinkdb` | database | — | no | 0 |
| RevenueCat | `revenuecat` | gateway | — | sì | 0 |
| Roboflow | `roboflow` | servizio o API | — | sì | 0 |
| Rocket.Chat | `rocket-chat` | servizio o API | — | sì | 0 |
| Rollbar | `rollbar` | servizio o API | — | sì | 1 |
| Salesforce | `salesforce` | servizio o API | — | no | 0 |
| Sanity | `sanity` | servizio o API | — | sì | 0 |
| SAP | `sap` | servizio o API | — | sì | 0 |
| SAS | `sas` | servizio o API | — | no | 0 |
| Sauce Labs | `sauce-labs` | servizio o API | — | sì | 0 |
| Scaleway | `scaleway` | servizio o API | — | sì | 0 |
| Scaleway Container | `scaleway.container` | servizio o API | — | no | 0 |
| Scaleway Database | `scaleway.database` | database | — | no | 0 |
| Scaleway DocumentDB | `scaleway.documentdb` | database | — | no | 0 |
| Scaleway Elastic Metal | `scaleway.elasticmetal` | servizio o API | — | no | 0 |
| Scaleway Function | `scaleway.function` | servizio o API | — | no | 0 |
| Scaleway Kubernetes | `scaleway.kubernetes` | servizio o API | — | no | 0 |
| Scaleway M&Q | `scaleway.mq` | coda | — | no | 0 |
| Scaleway Redis | `scaleway.redis` | database | — | no | 0 |
| Scaleway Secret Manager | `scaleway.secretmanager` | database | — | no | 0 |
| Scaleway Storage | `scaleway.storage` | database | — | no | 0 |
| Schedules Direct | `schedules-direct` | servizio o API | `json.schedulesdirect.org` | no | 0 |
| Scout APM | `scoutapm` | servizio o API | — | no | 0 |
| Segment | `segment` | servizio o API | — | no | 0 |
| Selenium | `selenium` | servizio o API | — | sì | 0 |
| Sendgrid | `sendgrid` | servizio o API | — | no | 0 |
| Sentry | `sentry` | servizio o API | — | sì | 10 |
| ServiceNow | `servicenow` | servizio o API | — | no | 0 |
| Shopify | `shopify` | servizio o API | — | sì | 0 |
| Shortcut | `shortcut` | servizio o API | — | sì | 0 |
| Sign in with Apple | `apple.signin` | autenticazione | — | no | 1 |
| Signoz | `signoz` | servizio o API | — | no | 0 |
| Simple Analytics | `simpleanalytics` | servizio o API | — | sì | 0 |
| SimpleFIN Bridge | `simplefin` | servizio o API | `bridge.simplefin.org` | no | 0 |
| SimpleSAMLphp | `simplesamlphp` | servizio o API | — | no | 0 |
| Sitecore | `sitecore` | servizio o API | — | sì | 0 |
| Sitecore XM cloud | `sitecore.xmlcloud` | servizio o API | — | no | 0 |
| Slack | `slack` | servizio o API | — | no | 0 |
| SmartThings | `smartthings` | servizio o API | — | sì | 0 |
| Snowflake | `snowflake` | database | — | sì | 0 |
| Snyk | `snyk` | servizio o API | — | sì | 0 |
| Solana | `solana` | servizio o API | — | sì | 0 |
| SonarCloud | `sonarcloud` | servizio o API | — | no | 0 |
| SonarQube | `sonarqube` | servizio o API | — | no | 0 |
| SparkPost | `sparkpost` | servizio o API | — | sì | 0 |
| Split | `splitio` | servizio o API | — | no | 0 |
| Splunk | `splunk` | servizio o API | — | sì | 0 |
| Spotify | `spotify` | servizio o API | — | sì | 1 |
| SQLite | `sqlite` | database | — | sì | 12 |
| Sqreen | `sqreen` | servizio o API | — | no | 0 |
| Square | `squareup` | gateway | — | sì | 0 |
| Squarespace | `squarespace` | servizio o API | — | sì | 0 |
| Storyblok | `storyblok` | servizio o API | — | sì | 0 |
| Strapi | `strapi` | servizio o API | — | sì | 0 |
| Stripe | `stripe` | gateway | — | sì | 5 |
| StyleCI | `styleci` | servizio o API | — | no | 0 |
| Stytch | `stytch` | autenticazione | — | no | 0 |
| Supabase | `supabase` | servizio o API | — | sì | 1 |
| Supabase Auth | `supabase.auth` | autenticazione | — | sì | 0 |
| Supabase Functions | `supabase.functions` | servizio o API | — | sì | 0 |
| Supabase Postgres | `supabase.postgres` | database | — | sì | 0 |
| Supabase Realtime | `supabase.realtime` | coda | — | sì | 0 |
| Supabase Storage | `supabase.storage` | database | — | sì | 0 |
| SuperTokens | `supertokens` | autenticazione | — | no | 0 |
| SurrealDB | `surrealdb` | database | — | sì | 0 |
| Swiftype | `swiftype` | database | — | no | 0 |
| Tailscale | `tailscale` | servizio o API | — | sì | 0 |
| TDengine | `tdengine` | database | — | no | 0 |
| TeamCity | `teamcity` | servizio o API | — | sì | 0 |
| Teamspeak | `teamspeak` | servizio o API | — | sì | 0 |
| Telegraf | `telegraf` | servizio o API | — | no | 0 |
| Telegram | `telegram` | servizio o API | `api.telegram.org` | sì | 0 |
| Tencent Cloud | `tencentcloud` | servizio o API | — | no | 0 |
| Tencent COS | `tencent-cos` | filesystem | — | no | 1 |
| Teradata | `teradata` | database | — | sì | 0 |
| The Space Devs API | `space-devs` | servizio o API | `ll.thespacedevs.com` | no | 0 |
| thirdweb | `thirdweb` | servizio o API | — | sì | 0 |
| Ticketmaster | `ticketmaster` | servizio o API | `app.ticketmaster.com` | sì | 0 |
| TiDB | `tidb` | database | — | sì | 0 |
| Tigris | `tigris` | filesystem | `fly.storage.tigris.dev` | no | 0 |
| Tika | `apachetika` | servizio o API | — | no | 1 |
| TimescaleDB | `timescaledb` | database | — | no | 0 |
| Tinybird | `tinybird` | servizio o API | — | no | 0 |
| TMDb | `tmdb` | servizio o API | — | sì | 0 |
| Todoist | `todoist` | servizio o API | — | sì | 0 |
| Traefik | `traefik` | servizio o API | — | no | 1 |
| Tray.ai | `trayio` | servizio o API | — | no | 0 |
| Trino | `trino` | database | — | sì | 0 |
| Truffle Security | `trufflesecurity` | servizio o API | — | no | 0 |
| Turso | `tursodb` | database | — | sì | 0 |
| Twenty CRM | `twentycrm` | servizio o API | — | sì | 0 |
| Twilio | `twilio` | servizio o API | `api.twilio.com` | no | 0 |
| Twitch | `twitch` | servizio o API | — | sì | 0 |
| Twitch OAuth | `twitch.oauth` | autenticazione | — | no | 1 |
| Typesense | `typesense` | database | — | no | 0 |
| Typesense Cloud | `typesensecloud` | database | — | no | 0 |
| Unsplash | `unsplash` | servizio o API | — | sì | 0 |
| Upstash | `upstash` | servizio o API | — | sì | 1 |
| Upstash Kafka | `upstash.kafka` | coda | — | no | 0 |
| Upstash QStash | `upstash.qstash` | coda | — | no | 0 |
| Upstash Redis | `upstash.redis` | database | — | no | 1 |
| Uptime Kuma | `uptimekuma` | servizio o API | — | sì | 0 |
| Use Autumn | `useautumn` | gateway | — | no | 0 |
| Valkey | `valkey` | database | — | no | 1 |
| Vault | `hashicorp_vault` | servizio o API | — | sì | 0 |
| Vercel | `vercel` | servizio o API | — | sì | 3 |
| Vercel AI | `vercel.ai` | servizio o API | — | no | 0 |
| Vercel Analytics | `vercel.analytics` | servizio o API | — | no | 0 |
| Vercel Blob | `vercel.blob` | database | — | no | 0 |
| Vercel Edge | `vercel.edge` | servizio o API | — | no | 0 |
| Vercel Functions | `vercel.functions` | servizio o API | — | no | 0 |
| Vercel KV | `vercel.kv` | database | — | no | 1 |
| Vercel Postgres | `vercel.postgres` | database | — | no | 0 |
| Veriff | `veriff` | servizio o API | — | no | 0 |
| Vertex AI | `gcp.vertex` | servizio o API | — | sì | 1 |
| Vialink | `vialink` | servizio o API | — | no | 0 |
| VictoriaMetrics | `victoriametrics` | database | — | sì | 0 |
| Vimeo | `vimeo` | servizio o API | — | sì | 0 |
| VirusTotal | `virustotal` | servizio o API | — | sì | 0 |
| Vonage | `vonage` | servizio o API | — | sì | 0 |
| WakaTime | `wakatime` | servizio o API | — | sì | 0 |
| Weaviate | `weaviate` | database | — | no | 0 |
| Webex | `webex` | servizio o API | — | sì | 0 |
| Webflow | `webflow` | servizio o API | — | sì | 0 |
| Weights & Biases | `wandb` | servizio o API | — | sì | 0 |
| what3words | `what3words` | servizio o API | — | sì | 0 |
| WhatsApp | `whatsapp` | servizio o API | — | sì | 0 |
| Where the ISS At API | `where-the-iss-at` | servizio o API | `api.wheretheiss.at` | no | 0 |
| Wikipedia | `wikipedia` | servizio o API | — | sì | 0 |
| Wiz | `wiz` | servizio o API | — | no | 0 |
| Wolfram Alpha | `wolframalpha` | servizio o API | — | no | 0 |
| WooCommerce | `woocommerce` | servizio o API | — | sì | 0 |
| Wordpress | `wordpress` | servizio o API | — | sì | 0 |
| WorkOS | `workos` | autenticazione | — | no | 0 |
| X | `twitter` | servizio o API | — | sì | 0 |
| X AI | `xai` | servizio o API | — | no | 0 |
| Xendit | `xendit` | servizio o API | — | sì | 0 |
| Yandex Cloud | `yandex-cloud` | servizio o API | — | sì | 0 |
| Yousign | `yousign` | servizio o API | — | no | 0 |
| Youtube | `youtube` | servizio o API | — | sì | 0 |
| Zapier | `zapier` | servizio o API | — | sì | 0 |
| Zendesk | `zendesk` | servizio o API | — | sì | 0 |
| Zipkin | `zipkin` | servizio o API | — | no | 1 |
| Zookeeper | `zookeeper` | servizio o API | — | no | 0 |
| Zoom | `zoom` | servizio o API | — | sì | 0 |
| Zuora | `zuora` | gateway | — | no | 0 |

</details>

## Letture proprie di framework e dialetti

Oltre al riconoscimento: i componenti Vue e Svelte entrano nell'indice di scip-typescript (`indexers/components.py`) e il loro `<script>` nello snapshot (`languages/sfc.py`); il grafo dei fogli di stile (`indexers/css.py`) legge questi file con i parser fissati in `daodan/core/indexers/css_engines/package.json`: @astrojs/compiler 4.0.0, @eslint/css-tree 4.1.3, @vue/compiler-sfc 3.5.45, less 4.9.1, sass-parser 0.5.6, stylus 0.64.0, svelte 5.57.3. La sua misura è la riga `stylesheet` della sezione Analizzatori.

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

`scripts/flows.py` applica regole di collegamento di 6 specie: `scrive` `legge` `rotta` `offre` `attiva` `ingresso`; un nodo di store ha uno di 11 tipi: `attore` `schermata` `funzionalità` `servizio o API` `gateway` `database` `coda` `autenticazione` `dispositivo` `filesystem` `altro`. Il censimento ([2026-11-14-punti-di-connessione.md](../research/2026-11-14-punti-di-connessione.md)) cataloga 26 tipi di punto di connessione; quali il prodotto unisce lo dice la sua sezione «Stato». Riconoscimento per tipo: non misurato.

| Coppia | Tipi nel censimento | Tipi |
| --- | --- | --- |
| Chiama / offre | 9 | REST; GraphQL; gRPC, RPC; Comando IPC; Sottoprocesso, CLI; Funzione o job remoto; Navigazione, deep link; Webhook; Stored procedure |
| Scrive / legge | 8 | Tabella, collezione; Stato dell'app; Cache, chiave-valore; File; Object storage; Storage del browser, cookie; Configurazione, variabili, flag; Contesto della richiesta |
| Emette / ascolta | 9 | Coda AMQP; Log di eventi; Coda di lavori; Canale in tempo reale; Evento nel processo; Notifica push; Cambiamento di un dato; Orario; Hook del ciclo di vita |
