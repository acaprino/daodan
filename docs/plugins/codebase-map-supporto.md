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

La pre-mappa ha 29 fonti (`scripts/premap/`, `SOURCES`); il grafo dei moduli legge 42 manifest di 30 ecosistemi (`scripts/build_units.py`); un modulo riceve 52 toolchain dal suo ecosistema o linguaggio (`scripts/module_derive.py`); la preparazione porta 11 toolchain nel container (`scripts/preparation.py`, `NEEDS`).

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
| `next` | daodan/premap/v2 | scanner: legge ogni file | `premap/nextjs.py` | non misurato: non era nel giro |

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

| Classe | Voci riconoscibili (con segni) | Voci con la categoria scritta, fra tutte |
| --- | --- | --- |
| framework | 138 | 138 |
| library | 197 | 197 |
| tool | 127 | 130 |
| service | 700 | 103 |

Ognuna delle 479 voci `project` riconoscibili ha la sua `category` scritta: nessuna è `framework` solo per il default.

Riconoscimento dello stack sul corpus, giro del 19 novembre 2026 (`benchmarks/project-model/results/daodan_stack.json`), 178 fixture su 180 con record; per nome conta un nome una volta per fixture, per unità ogni unità che lo tiene.

| Famiglia | Fixture | Framework per nome | Framework per unità | Servizi |
| --- | --- | --- | --- | --- |
| js | 20 | 10 / 10 (100,0 %) | 11 / 11 (100,0 %), 0 sbagliati | 1 / 1 (100,0 %), 0 in più |
| py | 21 | 4 / 4 (100,0 %) | 4 / 4 (100,0 %), 0 sbagliati | 2 / 3 (66,7 %), 0 in più |
| jvm | 34 | 36 / 42 (85,7 %) | 37 / 43 (86,0 %), 0 sbagliati | 1 / 2 (50,0 %), 0 in più |
| sys | 25 | 2 / 2 (100,0 %) | 1 / 2 (50,0 %), 1 sbagliato | nessuno atteso, 0 in più |
| mix | 30 | 29 / 31 (93,5 %) | 32 / 37 (86,5 %), 0 sbagliati | 11 / 33 (33,3 %), 1 in più |
| real | 10 | 99 / 127 (78,0 %) | 177 / 251 (70,5 %), 12 sbagliati | 30 / 84 (35,7 %), 9 in più |
| stack | 38 | 182 / 352 (51,7 %) | 290 / 653 (44,4 %), 37 sbagliati | 96 / 395 (24,3 %), 55 in più |
| tutte | 178 | 362 / 568 (63,7 %) | 552 / 1.001 (55,1 %), 50 sbagliati | 141 / 518 (27,2 %), 65 in più |

Che cosa vuol dire «supportata» per una voce della tabella che segue, a livelli. Riconosciuta: un suo segno (un pacchetto, un'immagine, un file) è nel progetto; vale per ogni voce. Codice analizzato: il codice del progetto che la dichiara è letto dall'analizzatore del suo linguaggio; la colonna dà questi linguaggi fra quelli degli ecosistemi dei segni della voce, e dice quando un linguaggio non ha analizzatore. Lettura propria: ciò che Daodan legge del framework oltre al suo linguaggio, e vale solo per 4 voci (Vue.js, Svelte, Astro, Tailwind). Rotte e collegamenti fra le parti vengono dalle regole di collegamento che un modello scrive per ogni progetto e che `scripts/flows.py` applica a chiamate, decoratori e attributi, per qualunque framework. Nessun framework ha le rotte lette dal posto di un file (le pagine di Next.js, Nuxt, SvelteKit, Remix o Astro): è un buco dichiarato.

<details><summary>Framework, librerie e strumenti riconoscibili: 462 voci</summary>

| Voce | Id | Classe | Segni | Codice analizzato | Lettura propria | Fixture in cui lo step la trova (19 novembre 2026) |
| --- | --- | --- | --- | --- | --- | --- |
| .NET Aspire | `dotnet-aspire` | framework | nuget | C# | — | 3 |
| .NET MAUI | `dotnet-maui` | framework | nuget | C# | — | 1 |
| Actix Web | `actixweb` | framework | crates | Rust | — | 2 |
| AdonisJS | `adonisjs` | framework | npm | JavaScript, TypeScript | — | 0 |
| aiohttp | `aiohttp` | framework | pypi | Python | — | 1 |
| Alpine.js | `alpinejs` | framework | npm | JavaScript, TypeScript | — | 2 |
| Android | `android` | framework | maven | Java, Kotlin | — | 5 |
| Angular | `angular` | framework | npm, files | JavaScript, TypeScript | — | 4 |
| AngularJS | `angularjs` | framework | npm | JavaScript, TypeScript | — | 0 |
| Api Platform | `apiplatform` | framework | composer, npm | JavaScript, TypeScript, php: nessun analizzatore | — | 0 |
| Apollo Server | `apollo-server` | framework | npm | JavaScript, TypeScript | — | 1 |
| ASP.NET Core | `aspnetcore` | framework | nuget | C# | — | 6 |
| Assemble | `assemble` | framework | npm | JavaScript, TypeScript | — | 0 |
| Astro | `astro` | framework | npm, files | JavaScript, TypeScript | frontmatter e `<script>` nello snapshot, il template no (`languages/sfc.py`); stili con il compilatore del framework (`indexers/css_astro.py`) | 1 |
| Axum | `axum` | framework | crates | Rust | — | 3 |
| Blazor | `blazor` | framework | nuget | C# | — | 1 |
| Blitzjs | `blitzjs` | framework | npm | JavaScript, TypeScript | — | 0 |
| Capacitor | `capacitorjs` | framework | npm, files | JavaScript, TypeScript | — | 1 |
| Celery | `celery` | framework | pypi | Python | — | 2 |
| Chi | `chi` | framework | go | Go | — | 4 |
| Compose for Wear OS | `compose-for-wear-os` | framework | maven | Java, Kotlin | — | 0 |
| Compose Multiplatform | `compose-multiplatform` | framework | maven | Java, Kotlin | — | 2 |
| Connect | `connectrpc` | framework | go | Go | — | 0 |
| Cordova | `apacheCordova` | framework | npm | JavaScript, TypeScript | — | 0 |
| Dioxus | `dioxus` | framework | crates | Rust | — | 0 |
| Django | `django` | framework | pypi | Python | — | 7 |
| Django Channels | `django-channels` | framework | pypi | Python | — | 0 |
| Django REST framework | `django-rest-framework` | framework | pypi | Python | — | 0 |
| Docsify | `docsify` | framework | npm | JavaScript, TypeScript | — | 0 |
| Docus | `docus` | framework | npm | JavaScript, TypeScript | — | 0 |
| Docusaurus | `docusaurus` | framework | npm, files | JavaScript, TypeScript | — | 1 |
| Duende IdentityServer | `duende-identityserver` | framework | nuget | C# | — | 1 |
| Echo | `echo` | framework | go | Go | — | 1 |
| Electron | `electron` | framework | github-actions, npm | JavaScript, TypeScript | — | 1 |
| Eleventy | `eleventy` | framework | github-actions, npm, files | JavaScript, TypeScript | — | 0 |
| ElysiaJS | `elysiajs` | framework | npm | JavaScript, TypeScript | — | 0 |
| Ember | `emberjs` | framework | npm, files | JavaScript, TypeScript | — | 0 |
| Expo | `expojs` | framework | npm | JavaScript, TypeScript | — | 3 |
| Express | `express` | framework | npm | JavaScript, TypeScript | — | 9 |
| ExUnit | `exunit` | framework |  | — | — | 0 |
| FastAPI | `fastapi` | framework | pypi | Python | — | 6 |
| FastEndpoints | `fastendpoints` | framework | nuget | C# | — | 0 |
| Fastify | `fastify` | framework | npm | JavaScript, TypeScript | — | 0 |
| FastMCP | `fastmcp` | framework | pypi | Python | — | 1 |
| Fiber | `fiber` | framework | go | Go | — | 0 |
| Flask | `flask` | framework | pypi | Python | — | 5 |
| Flutter | `flutter` | framework | pub | dart: nessun analizzatore | — | 2 |
| flutter_test | `flutter-test` | framework | pub | dart: nessun analizzatore | — | 0 |
| FumaDocs | `fumadocs` | framework | npm | JavaScript, TypeScript | — | 1 |
| Gatsby | `gatsby` | framework | github-actions, npm, files | JavaScript, TypeScript | — | 0 |
| Gin | `gin` | framework | go | Go | — | 1 |
| Gradio | `gradio` | framework | pypi | Python | — | 1 |
| Gridsome | `gridsome` | framework | npm, files | JavaScript, TypeScript | — | 0 |
| HexoJS | `hexojs` | framework | npm | JavaScript, TypeScript | — | 0 |
| Hono | `honojs` | framework | npm | JavaScript, TypeScript | — | 2 |
| Hugo | `hugo` | framework | docker, github-actions, npm, files | JavaScript, TypeScript | — | 1 |
| Inferno | `infernojs` | framework | npm | JavaScript, TypeScript | — | 0 |
| Ionic | `ionic` | framework | npm | JavaScript, TypeScript | — | 0 |
| Jekyll | `jekyll` | framework | github-actions, rubygems, files | ruby: nessun analizzatore | — | 0 |
| Jetpack Compose | `jetpack-compose` | framework | maven | Java, Kotlin | — | 0 |
| Koa | `koa` | framework | npm | JavaScript, TypeScript | — | 0 |
| Kotlin Multiplatform | `kotlin-multiplatform` | framework | maven | Java, Kotlin | — | 3 |
| Ktor | `ktor` | framework | maven | Java, Kotlin | — | 2 |
| LangChain4j | `langchain4j` | framework | maven | Java, Kotlin | — | 0 |
| Laravel | `laravel` | framework | composer, files | php: nessun analizzatore | — | 3 |
| Lit | `litjs` | framework | npm | JavaScript, TypeScript | — | 0 |
| MapKit | `mapkit` | framework |  | — | — | 0 |
| Materialize | `materialize-css` | framework | npm | JavaScript, TypeScript | — | 0 |
| Meteor | `meteorjs` | framework | npm, files | JavaScript, TypeScript | — | 0 |
| Metro | `metro-kotlin` | framework | maven | Java, Kotlin | — | 0 |
| Micronaut | `micronaut` | framework | maven | Java, Kotlin | — | 0 |
| Mithril | `mithriljs` | framework | npm | JavaScript, TypeScript | — | 0 |
| MkDocs | `mkdocs` | framework | docker, pypi, files | Python | — | 2 |
| MudBlazor | `mudblazor` | framework | nuget | C# | — | 0 |
| MyBatis | `mybatis` | framework | maven | Java, Kotlin | — | 0 |
| NestJS | `nestjs` | framework | npm, files | JavaScript, TypeScript | — | 2 |
| Next.js | `nextjs` | framework | npm, files | JavaScript, TypeScript | — | 5 |
| Nuxt.js | `nuxtjs` | framework | npm, files | JavaScript, TypeScript | — | 2 |
| Phaser | `phaserjs` | framework | npm | JavaScript, TypeScript | — | 0 |
| Phoenix | `phoenix` | framework | hex | elixir: nessun analizzatore | — | 3 |
| Phoenix LiveView | `phoenix-liveview` | framework | hex | elixir: nessun analizzatore | — | 3 |
| Pico CSS | `pico-css` | framework | npm | JavaScript, TypeScript | — | 0 |
| Preact | `preactjs` | framework | npm | JavaScript, TypeScript | — | 1 |
| proptest | `proptest` | framework | crates | Rust | — | 0 |
| Quarkus | `quarkus` | framework | maven | Java, Kotlin | — | 1 |
| Quarkus REST | `quarkus-rest` | framework | maven | Java, Kotlin | — | 0 |
| Quarkus WebSockets Next | `quarkus-websockets-next` | framework | maven | Java, Kotlin | — | 0 |
| Qwik | `qwikjs` | framework | npm | JavaScript, TypeScript | — | 0 |
| React | `react` | framework | npm | JavaScript, TypeScript | — | 18 |
| React Native | `react-native` | framework | npm | JavaScript, TypeScript | — | 3 |
| RedwoodJs | `redwoodjs` | framework | npm, files | JavaScript, TypeScript | — | 0 |
| Refine | `refinedev` | framework | npm | JavaScript, TypeScript | — | 0 |
| Remix | `remixrun` | framework | npm | JavaScript, TypeScript | — | 0 |
| Roq | `roq` | framework | maven | Java, Kotlin | — | 0 |
| rstest | `rstest` | framework | crates | Rust | — | 0 |
| Ruby on Rails | `rails` | framework | npm, rubygems | JavaScript, TypeScript, ruby: nessun analizzatore | — | 3 |
| Scrapy | `scrapy` | framework | pypi | Python | — | 0 |
| Shopify Hydrogen | `shopify.hydrogen` | framework | npm | JavaScript, TypeScript | — | 0 |
| Sinatra | `sinatra` | framework | rubygems | ruby: nessun analizzatore | — | 1 |
| Slate | `slatedocs` | framework | docker | — | — | 0 |
| Slim | `slim` | framework | composer | php: nessun analizzatore | — | 1 |
| Solid js | `solidjs` | framework | npm | JavaScript, TypeScript | — | 0 |
| Sphinx | `sphinx` | framework | pypi | Python | — | 2 |
| Spring AI | `spring-ai` | framework | maven | Java, Kotlin | — | 0 |
| Spring AMQP | `spring-amqp` | framework | maven | Java, Kotlin | — | 0 |
| Spring Boot | `spring-boot` | framework | maven | Java, Kotlin | — | 7 |
| Spring Boot Admin | `spring-boot-admin` | framework | maven | Java, Kotlin | — | 1 |
| Spring Cloud Config | `spring-cloud-config` | framework | maven | Java, Kotlin | — | 1 |
| Spring Cloud Gateway | `spring-cloud-gateway` | framework | maven | Java, Kotlin | — | 0 |
| Spring Cloud Netflix | `spring-cloud-netflix` | framework | maven | Java, Kotlin | — | 1 |
| Spring Data Elasticsearch | `spring-data-elasticsearch` | framework | maven | Java, Kotlin | — | 0 |
| Spring Data JPA | `spring-data-jpa` | framework | maven | Java, Kotlin | — | 5 |
| Spring Data MongoDB | `spring-data-mongodb` | framework | maven | Java, Kotlin | — | 0 |
| Spring Data Redis | `spring-data-redis` | framework | maven | Java, Kotlin | — | 0 |
| Spring MVC | `spring-mvc` | framework | maven | Java, Kotlin | — | 6 |
| Spring Security | `spring-security` | framework | maven | Java, Kotlin | — | 2 |
| Spring WebFlux | `spring-webflux` | framework | maven | Java, Kotlin | — | 0 |
| Stencil | `stenciljs` | framework | npm | JavaScript, TypeScript | — | 0 |
| Stimulus | `stimulus` | framework | composer, npm | JavaScript, TypeScript, php: nessun analizzatore | — | 0 |
| Strawberry GraphQL | `strawberry-graphql` | framework | pypi | Python | — | 0 |
| Streamlit | `streamlit` | framework | pypi | Python | — | 0 |
| Svelte | `sveltejs` | framework | npm, files | JavaScript, TypeScript | componenti nell'indice di scip-typescript (`indexers/components.py`); `<script>` e template nello snapshot (`languages/sfc.py`); stili con il compilatore del framework (`indexers/css_svelte.py`) | 2 |
| SvelteKit | `sveltekit` | framework | npm | JavaScript, TypeScript | — | 1 |
| SwiftUI | `swiftui` | framework |  | — | — | 0 |
| Symfony | `symfony` | framework | composer | php: nessun analizzatore | — | 0 |
| Tanstack Start | `tanstackstart` | framework | npm | JavaScript, TypeScript | — | 0 |
| Tauri | `tauri` | framework | crates, npm, files | Rust, JavaScript, TypeScript | — | 3 |
| test | `dart-test` | framework | pub | dart: nessun analizzatore | — | 0 |
| UIKit | `uikit` | framework |  | — | — | 0 |
| UmiJS | `umijs` | framework | npm, files | JavaScript, TypeScript | — | 0 |
| VitePress | `vitepress` | framework | npm, files | JavaScript, TypeScript | — | 1 |
| Vue.js | `vue` | framework | maven, npm | Java, Kotlin, JavaScript, TypeScript | componenti nell'indice di scip-typescript (`indexers/components.py`); `<script>` e template nello snapshot (`languages/sfc.py`); stili con il compilatore del framework (`indexers/css_vue.py`) | 8 |
| VuePress | `vuepress` | framework | npm, files | JavaScript, TypeScript | — | 0 |
| Vuetify | `vuetify` | framework | npm | JavaScript, TypeScript | — | 0 |
| Wagtail | `wagtail` | framework | pypi | Python | — | 0 |
| Wasp | `wasp` | framework | files | — | — | 0 |
| Yew | `yew` | framework | crates | Rust | — | 0 |
| Yii2 | `yii2` | framework | composer | php: nessun analizzatore | — | 0 |
| _hyperscript | `hyperscript` | library | npm | JavaScript, TypeScript | — | 0 |
| Ant Design | `antd` | library | npm | JavaScript, TypeScript | — | 1 |
| Ant Design Icons | `antdicons` | library | npm | JavaScript, TypeScript | — | 1 |
| Apache Avro | `avro` | library | maven | Java, Kotlin | — | 0 |
| Apache Beam | `apache-beam` | library | go, pypi | Go, Python | — | 0 |
| Apache Thrift | `apache_thrift` | library | crates, docker, go, npm, rubygems | Rust, Go, JavaScript, TypeScript, ruby: nessun analizzatore | — | 0 |
| AriaKit UI | `ariakitui` | library | npm | JavaScript, TypeScript | — | 0 |
| Ark UI | `arkui` | library | npm | JavaScript, TypeScript | — | 0 |
| ArkType | `arktype` | library | npm | JavaScript, TypeScript | — | 0 |
| Base UI | `baseui` | library | npm | JavaScript, TypeScript | — | 0 |
| Basecoat | `basecoat` | library | npm | JavaScript, TypeScript | — | 0 |
| Bootstrap | `bootstrap` | library | composer, maven, npm | Java, Kotlin, JavaScript, TypeScript, php: nessun analizzatore | — | 5 |
| Bootstrap Icons | `bootstrapicons` | library | npm | JavaScript, TypeScript | — | 1 |
| Boto3 | `boto3` | library | pypi | Python | — | 4 |
| Broadway | `broadway` | library | hex | elixir: nessun analizzatore | — | 0 |
| BullMQ | `bullmq` | library | npm | JavaScript, TypeScript | — | 0 |
| Casbin | `casbin` | library | go | Go | — | 0 |
| Catalyst | `github-catalyst` | library | npm | JavaScript, TypeScript | — | 0 |
| Cats | `cats` | library | maven | Java, Kotlin | — | 1 |
| Chakra UI | `chakraui` | library | npm | JavaScript, TypeScript | — | 0 |
| clap | `clap` | library | crates | Rust | — | 0 |
| class-transformer | `class-transformer` | library | npm | JavaScript, TypeScript | — | 0 |
| class-validator | `class-validator` | library | npm | JavaScript, TypeScript | — | 0 |
| Click | `click` | library | pypi | Python | — | 8 |
| Cobra | `cobra` | library | go | Go | — | 2 |
| CodeMirror | `codemirror` | library | npm | JavaScript, TypeScript | — | 8 |
| Coil | `coil` | library | maven | Java, Kotlin | — | 0 |
| D3.js | `d3js` | library | npm | JavaScript, TypeScript | — | 1 |
| daisyUI | `daisyui` | library | npm | JavaScript, TypeScript | — | 1 |
| dart_mappable | `dart-mappable` | library | pub | dart: nessun analizzatore | — | 0 |
| Dask | `dask` | library | pypi | Python | — | 0 |
| Diesel | `dieselrs` | library | crates | Rust | — | 0 |
| Doctrine ORM | `doctrinephp` | library | composer | php: nessun analizzatore | — | 2 |
| DOMPurify | `dompurify` | library | maven, npm | Java, Kotlin, JavaScript, TypeScript | — | 0 |
| Drizzle ORM | `drizzleorm` | library | npm | JavaScript, TypeScript | — | 0 |
| Ecto | `ecto` | library | hex | elixir: nessun analizzatore | — | 0 |
| EffectJS | `effectjs` | library | npm | JavaScript, TypeScript | — | 0 |
| Element Plus | `element-plus` | library | npm | JavaScript, TypeScript | — | 0 |
| ELK.js | `elkjs` | library | npm | JavaScript, TypeScript | — | 0 |
| ent. | `goent` | library | go | Go | — | 0 |
| Entity Framework Core | `entity-framework-core` | library | nuget | C# | — | 5 |
| Expo Router | `expo-router` | library | npm | JavaScript, TypeScript | — | 0 |
| Exposed | `exposed` | library | maven | Java, Kotlin | — | 1 |
| Feather Icons | `feathericons` | library | npm | JavaScript, TypeScript | — | 0 |
| Fluent UI | `fluentui` | library | npm | JavaScript, TypeScript | — | 0 |
| flutter_rust_bridge | `flutter-rust-bridge` | library | crates, pub | Rust, dart: nessun analizzatore | — | 0 |
| Font Awesome | `fontawesome` | library | maven, npm | Java, Kotlin, JavaScript, TypeScript | — | 2 |
| GORM | `gorm` | library | go | Go | — | 2 |
| graphql_client | `graphql-client-rust` | library | crates | Rust | — | 0 |
| gRPC | `grpc` | library | crates, go, maven, npm, nuget, pypi | Rust, Go, Java, Kotlin, JavaScript, TypeScript, C#, Python | — | 5 |
| gRPC-Gateway | `grpc-gateway` | library | go | Go | — | 0 |
| Headless UI | `headlessui` | library | npm | JavaScript, TypeScript | — | 1 |
| Hero UI | `heroui` | library | npm | JavaScript, TypeScript | — | 0 |
| Heroicons | `heroicons` | library | npm | JavaScript, TypeScript | — | 2 |
| Hibernate | `hibernate` | library | maven | Java, Kotlin | — | 1 |
| Hibernate Reactive | `hibernate-reactive` | library | maven | Java, Kotlin | — | 0 |
| Horologist | `horologist` | library | maven | Java, Kotlin | — | 0 |
| HTMX | `htmx` | library | npm | JavaScript, TypeScript | — | 3 |
| HTTPX | `httpx` | library | pypi | Python | — | 4 |
| HugeIcons | `hugeicons` | library | npm | JavaScript, TypeScript | — | 0 |
| Hyper | `hyper-rust` | library | crates | Rust | — | 0 |
| Imago | `imago` | library | npm | JavaScript, TypeScript | — | 0 |
| Ionicons | `ionicons` | library | npm | JavaScript, TypeScript | — | 0 |
| Jackson | `jackson` | library | maven | Java, Kotlin | — | 4 |
| Jinja | `jinja` | library | pypi | Python | — | 6 |
| JMS Serializer | `jms-serializer` | library | composer | php: nessun analizzatore | — | 0 |
| Joi | `joijs` | library | npm | JavaScript, TypeScript | — | 0 |
| jOOQ | `jooq` | library | maven | Java, Kotlin | — | 0 |
| JSON Schema | `jsonschema` | library | composer, crates, go, npm, pypi, rubygems | Rust, Go, JavaScript, TypeScript, Python, php: nessun analizzatore, ruby: nessun analizzatore | — | 5 |
| Json.NET | `json-net` | library | nuget | C# | — | 0 |
| Juniper | `juniper` | library | crates | Rust | — | 0 |
| Keras | `keras` | library | pypi | Python | — | 0 |
| keyring | `keyring` | library | pypi | Python | — | 0 |
| Knex | `knex` | library | npm | JavaScript, TypeScript | — | 0 |
| Koin | `koin` | library | maven | Java, Kotlin | — | 2 |
| kotlinx.html | `kotlinx-html` | library | maven | Java, Kotlin | — | 0 |
| kotlinx.serialization | `kotlinx-serialization` | library | maven | Java, Kotlin | — | 2 |
| Kysely | `kysely` | library | npm | JavaScript, TypeScript | — | 1 |
| LangChain | `langchain` | library | npm, pypi | JavaScript, TypeScript, Python | — | 1 |
| Lexical Editor | `lexicaleditor` | library | npm | JavaScript, TypeScript | — | 0 |
| LikeC4 | `likec4` | library | npm | JavaScript, TypeScript | — | 0 |
| LlamaIndex | `llamaindex` | library | pypi | Python | — | 0 |
| Lombok | `lombok` | library | maven | Java, Kotlin | — | 2 |
| Lord Icon | `lordicon` | library | npm | JavaScript, TypeScript | — | 0 |
| Lucide Icons | `lucideicons` | library | npm | JavaScript, TypeScript | — | 7 |
| Mantine UI | `mantineui` | library | npm | JavaScript, TypeScript | — | 0 |
| MapStruct | `mapstruct` | library | maven | Java, Kotlin | — | 3 |
| Marked | `marked` | library | maven, npm | Java, Kotlin, JavaScript, TypeScript | — | 0 |
| marshmallow | `marshmallow` | library | pypi | Python | — | 0 |
| Material Design Icons | `materialdesignicons` | library | npm | JavaScript, TypeScript | — | 0 |
| Material UI | `materialui` | library | npm | JavaScript, TypeScript | — | 0 |
| Matplotlib | `matplotlib` | library | pypi | Python | — | 1 |
| MessagePack | `messagepack-dotnet` | library | nuget | C# | — | 0 |
| MiniJinja | `minijinja` | library | crates | Rust | — | 0 |
| Mlflow | `mlflow` | library | pypi | Python | — | 0 |
| Mockall | `mockall` | library | crates | Rust | — | 0 |
| Model Context Protocol SDK | `mcp` | library | npm, pypi, rubygems | JavaScript, TypeScript, Python, ruby: nessun analizzatore | — | 2 |
| Monaco Editor | `monacoeditor` | library | npm | JavaScript, TypeScript | — | 1 |
| Mongoose | `mongoose` | library | npm | JavaScript, TypeScript | — | 0 |
| Mono.Cecil | `mono-cecil` | library | nuget | C# | — | 0 |
| MUI Icons | `muiicons` | library | npm | JavaScript, TypeScript | — | 0 |
| NumPy | `numpy` | library | pypi | Python | — | 3 |
| Oban | `oban` | library | hex | elixir: nessun analizzatore | — | 0 |
| OpenAPI | `openapi` | library | composer, crates, go, npm, pypi, rubygems, files | Rust, Go, JavaScript, TypeScript, Python, php: nessun analizzatore, ruby: nessun analizzatore | — | 10 |
| OpenCV | `opencv` | library | crates, go, pypi | Rust, Go, Python | — | 0 |
| OpenTelemetry | `opentelemetry` | library | composer, crates, docker, github-actions, go, npm, nuget, pypi, rubygems, env | Rust, Go, JavaScript, TypeScript, C#, Python, php: nessun analizzatore, ruby: nessun analizzatore | — | 3 |
| Panache | `panache` | library | maven | Java, Kotlin | — | 0 |
| pandas | `pandas` | library | pypi | Python | — | 2 |
| Passport | `passport` | library | npm | JavaScript, TypeScript | — | 2 |
| Pebble | `pebble` | library | maven | Java, Kotlin | — | 0 |
| Phosphor Icons | `phosphoreicons` | library | npm | JavaScript, TypeScript | — | 0 |
| picocli | `picocli` | library | maven | Java, Kotlin | — | 1 |
| Pillow | `pillow` | library | pypi | Python | — | 5 |
| Pinia | `pinia` | library | npm | JavaScript, TypeScript | — | 0 |
| Plotly | `plotly` | library | pypi | Python | — | 0 |
| Polars | `polars` | library | crates, pypi | Rust, Python | — | 0 |
| Prisma | `prisma` | library | npm, files | JavaScript, TypeScript | — | 4 |
| Protocol Buffers | `protobuf` | library | crates, go, maven, npm, pypi | Rust, Go, Java, Kotlin, JavaScript, TypeScript, Python | — | 7 |
| Pydantic | `pydantic` | library | pypi | Python | — | 6 |
| Pytorch | `pytorch` | library | pypi | Python | — | 0 |
| PyYAML | `pyyaml` | library | pypi | Python | — | 0 |
| Qmgo | `qmgo` | library | go | Go | — | 0 |
| Qute | `qute` | library | maven | Java, Kotlin | — | 0 |
| Radix Icons | `radixicons` | library | npm | JavaScript, TypeScript | — | 0 |
| Radix UI | `radixui` | library | npm | JavaScript, TypeScript | — | 3 |
| Ratatui | `ratatui` | library | crates | Rust | — | 0 |
| Ray | `ray` | library | pypi | Python | — | 0 |
| React DOM | `react-dom` | library | npm | JavaScript, TypeScript | — | 0 |
| React Email | `react-email` | library | npm | JavaScript, TypeScript | — | 3 |
| React Email | `reactemail` | library | npm | JavaScript, TypeScript | — | 2 |
| React Flow | `react-flow` | library | npm | JavaScript, TypeScript | — | 0 |
| React Icons | `reacticons` | library | npm | JavaScript, TypeScript | — | 2 |
| React Native Elements | `react-native-elements` | library | npm | JavaScript, TypeScript | — | 0 |
| React Navigation | `react-navigation` | library | npm | JavaScript, TypeScript | — | 0 |
| React Router | `reactrouterdom` | library | npm | JavaScript, TypeScript | — | 7 |
| Refena | `refena` | library | pub | dart: nessun analizzatore | — | 0 |
| Reka UI | `rekaui` | library | npm | JavaScript, TypeScript | — | 0 |
| Remix Icons | `remixicons` | library | npm | JavaScript, TypeScript | — | 0 |
| Remix Router | `remixrouter` | library | npm | JavaScript, TypeScript | — | 0 |
| Remult | `remult` | library | npm | JavaScript, TypeScript | — | 0 |
| Requests | `requests` | library | pypi | Python | — | 9 |
| Resilience4j | `resilience4j` | library | maven | Java, Kotlin | — | 1 |
| Routerino | `routerino` | library | pub | dart: nessun analizzatore | — | 0 |
| RQ | `rq` | library | pypi | Python | — | 0 |
| Sandpack | `sandpackeditor` | library | npm | JavaScript, TypeScript | — | 0 |
| Sass parser | `sass-parser` | library | npm | JavaScript, TypeScript | — | 0 |
| scikit-learn | `scikitlearn` | library | pypi | Python | — | 1 |
| SciPy | `scipy` | library | pypi | Python | — | 0 |
| SeaORM | `sea-orm` | library | crates | Rust | — | 0 |
| Sequel | `sequelruby` | library | rubygems | ruby: nessun analizzatore | — | 0 |
| Sequelize | `sequelize` | library | npm, files | JavaScript, TypeScript | — | 1 |
| Serde | `serde` | library | crates | Rust | — | 8 |
| serde_json | `serde-json` | library | crates | Rust | — | 0 |
| Shadcn | `shadcn` | library | npm | JavaScript, TypeScript | — | 0 |
| Sidekiq | `sidekiq` | library | rubygems | ruby: nessun analizzatore | — | 2 |
| Simple Icons | `simpleicons` | library | npm | JavaScript, TypeScript | — | 0 |
| SmallRye Reactive Messaging | `smallrye-reactive-messaging` | library | maven | Java, Kotlin | — | 0 |
| Socket.io | `socketio` | library | npm, pypi | JavaScript, TypeScript, Python | — | 2 |
| Solid Queue | `solid-queue` | library | rubygems | ruby: nessun analizzatore | — | 0 |
| spaCy | `spacy` | library | pypi | Python | — | 0 |
| SQLAlchemy | `sqlalchemy` | library | pypi | Python | — | 3 |
| SQLGlot | `sqlglot` | library | pypi | Python | — | 0 |
| SQLModel | `sqlmodel` | library | pypi | Python | — | 1 |
| sqlx | `sqlx-go` | library | go | Go | — | 0 |
| SQLx | `sqlx-rust` | library | crates | Rust | — | 0 |
| Superstruct | `superstruct` | library | npm | JavaScript, TypeScript | — | 0 |
| Tabler | `tabler` | library | npm | JavaScript, TypeScript | — | 0 |
| Tabler Icons | `tablericons` | library | npm | JavaScript, TypeScript | — | 1 |
| Tailwind | `tailwind` | library | hex, npm, files | JavaScript, TypeScript, elixir: nessun analizzatore | quali classi sono sue utility, dal Tailwind del progetto nel container (`indexers/css_tailwind.py`) | 12 |
| TanStack Router | `tanstackrouter` | library | npm | JavaScript, TypeScript | — | 1 |
| tempfile | `tempfile-rust` | library | crates | Rust | — | 0 |
| Tensorflow | `tensorflow` | library | crates, docker, go, npm, pypi | Rust, Go, JavaScript, TypeScript, Python | — | 0 |
| testify | `testify` | library | go | Go | — | 0 |
| Testing Library | `testinglibrary` | library | npm | JavaScript, TypeScript | — | 11 |
| Thymeleaf | `thymeleaf` | library | maven | Java, Kotlin | — | 3 |
| Tiptap | `tiptap` | library | npm | JavaScript, TypeScript | — | 3 |
| Tokio | `tokio` | library | crates | Rust | — | 4 |
| Tree-sitter | `tree-sitter` | library | pypi | Python | — | 0 |
| Tree-sitter Language Pack | `tree-sitter-language-pack` | library | pypi | Python | — | 0 |
| TRPC | `trpc` | library | npm | JavaScript, TypeScript | — | 1 |
| ts-rest | `ts-rest` | library | npm | JavaScript, TypeScript | — | 0 |
| Turbo | `hotwire-turbo` | library | npm, rubygems | JavaScript, TypeScript, ruby: nessun analizzatore | — | 0 |
| Twig | `twigphp` | library | composer | php: nessun analizzatore | — | 1 |
| TypeBox | `typebox` | library | npm | JavaScript, TypeScript | — | 0 |
| TypeORM | `typeorm` | library | npm | JavaScript, TypeScript | — | 1 |
| Typer | `typer` | library | pypi | Python | — | 2 |
| urfave/cli | `urfave-cli` | library | go | Go | — | 0 |
| urql | `urql` | library | npm | JavaScript, TypeScript | — | 1 |
| Valibot | `valibot` | library | npm | JavaScript, TypeScript | — | 0 |
| Viper | `viper` | library | go | Go | — | 3 |
| Vue Router | `vue-router` | library | maven, npm | Java, Kotlin, JavaScript, TypeScript | — | 2 |
| WatermelonDB | `watermelondb` | library | npm | JavaScript, TypeScript | — | 0 |
| webview2-com | `webview2-com` | library | crates | Rust | — | 0 |
| Windows for Rust | `windows-rs` | library | crates | Rust | — | 0 |
| wiremock | `wiremock-rs` | library | crates | Rust | — | 0 |
| YARP | `yarp` | library | nuget | C# | — | 0 |
| Zod | `zod` | library | npm | JavaScript, TypeScript | — | 7 |
| Alembic | `alembic` | tool | pypi | Python | — | 3 |
| Ansible | `ansible` | tool | docker, github-actions, pypi | Python | — | 0 |
| Apache JMeter | `jmeter` | tool | maven | Java, Kotlin | — | 0 |
| ArchUnit | `archunit` | tool | maven | Java, Kotlin | — | 1 |
| Artillery | `artillery` | tool | npm | JavaScript, TypeScript | — | 0 |
| asdf | `asdf` | tool | files | — | — | 0 |
| Astro compiler | `astro-compiler` | tool | npm | JavaScript, TypeScript | — | 0 |
| AtlasGo | `atlasgo` | tool | docker, github-actions, terraform, files | hcl: nessun analizzatore | — | 0 |
| AWS CDK | `awscdk` | tool | go, npm, pypi | Go, JavaScript, TypeScript, Python | — | 0 |
| AWS CloudFormation | `aws.cloudformation` | tool | crates, github-actions, go, npm, pypi, rubygems, terraform-resource | Rust, Go, JavaScript, TypeScript, Python, ruby: nessun analizzatore, hcl: nessun analizzatore | — | 0 |
| Babel | `babel` | tool | npm | JavaScript, TypeScript | — | 8 |
| Biome JS | `biomejs` | tool | npm, files | JavaScript, TypeScript | — | 4 |
| Bun | `bunsh` | tool | files | — | — | 0 |
| Bundler | `bundler` | tool | rubygems | ruby: nessun analizzatore | — | 0 |
| Bytebase | `bytebase` | tool | docker, github-actions | — | — | 0 |
| Capybara | `capybara` | tool | rubygems | ruby: nessun analizzatore | — | 0 |
| Chef | `chef` | tool | docker | — | — | 0 |
| containerd | `containerd` | tool | go | Go | — | 0 |
| Create React App | `create-react-app` | tool | npm | JavaScript, TypeScript | — | 0 |
| Cypress | `cypressci` | tool | docker, github-actions, npm, rubygems | JavaScript, TypeScript, ruby: nessun analizzatore | — | 3 |
| dbt | `dbt` | tool | pypi | Python | — | 0 |
| Deno | `deno` | tool | docker, github-actions, files | — | — | 1 |
| Detox | `detox` | tool | npm | JavaScript, TypeScript | — | 0 |
| Docker | `docker` | tool | github-actions, go, npm, pypi, files | Go, JavaScript, TypeScript, Python | — | 40 |
| Esbuild | `esbuild` | tool | go, hex, npm | Go, JavaScript, TypeScript, elixir: nessun analizzatore | — | 5 |
| Eslint | `eslint` | tool | npm, files | JavaScript, TypeScript | — | 23 |
| Fern | `builtwithfern` | tool | files | — | — | 0 |
| Flyway | `flyway` | tool | docker, github-actions | — | — | 0 |
| FsCheck | `fscheck` | tool | nuget | C# | — | 0 |
| Gatling | `gatling` | tool | maven | Java, Kotlin | — | 1 |
| goenv | `goenv` | tool | files | — | — | 0 |
| Golang | `golang` | tool | docker, files | — | — | 20 |
| GolangCI Lint | `golangcilint` | tool | docker, github-actions, go, files | Go | — | 3 |
| Grafana K6 | `k6` | tool | docker, go, npm | Go, JavaScript, TypeScript | — | 0 |
| GraphiQL | `graphiql` | tool | npm | JavaScript, TypeScript | — | 0 |
| Gunicorn | `gunicorn` | tool | pypi | Python | — | 6 |
| Hatchling | `hatchling` | tool | pypi | Python | — | 0 |
| Helm | `helm` | tool | github-actions, go, rubygems, terraform, files | Go, ruby: nessun analizzatore, hcl: nessun analizzatore | — | 4 |
| Jest | `jest` | tool | npm, files | JavaScript, TypeScript | — | 9 |
| JHipster | `jhipster` | tool | maven, npm | Java, Kotlin, JavaScript, TypeScript | — | 0 |
| JUnit | `junit` | tool | maven | Java, Kotlin | — | 22 |
| JUnit Jupiter | `junit-jupiter` | tool | maven | Java, Kotlin | — | 7 |
| Jupyter | `jupyter` | tool | pypi | Python | — | 0 |
| Kotest | `kotest` | tool | maven | Java, Kotlin | — | 0 |
| kotlin.test | `kotlin-test` | tool | maven | Java, Kotlin | — | 0 |
| Lego | `goacmelego` | tool | docker, go, files | Go | — | 0 |
| Less | `less` | tool | npm | JavaScript, TypeScript | — | 0 |
| Lighthouse | `lighthouse` | tool | docker, github-actions, npm | JavaScript, TypeScript | — | 1 |
| Liquibase | `liquibase` | tool | docker, github-actions, maven | Java, Kotlin | — | 1 |
| Locust | `locust` | tool | pypi | Python | — | 2 |
| Material for MkDocs | `mkdocs-material` | tool | pypi | Python | — | 0 |
| Mintlify | `mintlify` | tool | npm, files | JavaScript, TypeScript | — | 0 |
| Mocha | `mochajs` | tool | npm | JavaScript, TypeScript | — | 1 |
| Mockito | `mockito` | tool | maven | Java, Kotlin | — | 2 |
| MockK | `mockk` | tool | maven | Java, Kotlin | — | 0 |
| MockServer | `mockserver` | tool | maven | Java, Kotlin | — | 0 |
| MSTest | `mstest` | tool | nuget | C# | — | 1 |
| NodeJS | `nodejs` | tool | docker, files | — | — | 61 |
| npm | `npm` | tool | files | — | — | 0 |
| NuGet | `nuget` | tool | files | — | — | 0 |
| NUnit | `nunit` | tool | nuget | C# | — | 1 |
| nvm | `nvm` | tool | files | — | — | 0 |
| NX | `nxjs` | tool | npm, files | JavaScript, TypeScript | — | 1 |
| oapi-codegen | `oapi-codegen` | tool | go | Go | — | 0 |
| OxLint | `oxlint` | tool | npm, pypi, files | JavaScript, TypeScript, Python | — | 1 |
| Pact | `pact` | tool | maven | Java, Kotlin | — | 0 |
| Parcel | `parceljs` | tool | npm | JavaScript, TypeScript | — | 0 |
| PHP | `php` | tool | docker, github-actions, files | — | — | 7 |
| PHP Pest | `phppest` | tool | composer | php: nessun analizzatore | — | 0 |
| phpenv | `phpenv` | tool | files | — | — | 0 |
| PHPStan | `phpstan` | tool | composer, files | php: nessun analizzatore | — | 2 |
| PHPUnit | `phpunit` | tool | composer, files | php: nessun analizzatore | — | 5 |
| pip | `pip` | tool | pypi | Python | — | 0 |
| pipenv | `pipenv` | tool | files | — | — | 0 |
| Playwright | `playwright` | tool | docker, github-actions, maven, npm, nuget, pypi, files | Java, Kotlin, JavaScript, TypeScript, C#, Python | — | 12 |
| pnpm | `pnpm` | tool | files | — | — | 0 |
| Podman | `podman` | tool | go | Go | — | 0 |
| Poetry | `poetry` | tool | files | — | — | 0 |
| Prettier | `prettier` | tool | npm, files | JavaScript, TypeScript | — | 14 |
| Pulumi | `pulumi` | tool | go, npm, pypi, files | Go, JavaScript, TypeScript, Python | — | 0 |
| pytest | `pytest` | tool | pypi | Python | — | 9 |
| Python | `python` | tool | docker, github-actions, files | — | — | 16 |
| Quinoa | `quinoa` | tool | maven | Java, Kotlin | — | 0 |
| Read The Docs | `readthedocs` | tool | docker, files | — | — | 0 |
| Renovate | `renovate` | tool | npm, files | JavaScript, TypeScript | — | 6 |
| Reqnroll | `reqnroll` | tool | nuget | C# | — | 0 |
| REST Assured | `rest-assured` | tool | maven | Java, Kotlin | — | 0 |
| Robolectric | `robolectric` | tool | maven | Java, Kotlin | — | 0 |
| Rolldown | `rolldown` | tool | crates, npm | Rust, JavaScript, TypeScript | — | 1 |
| Rollup | `rollup` | tool | npm | JavaScript, TypeScript | — | 4 |
| Rspack | `rspack` | tool | npm, files | JavaScript, TypeScript | — | 0 |
| RSpec | `rspec` | tool | rubygems | ruby: nessun analizzatore | — | 0 |
| Rubocop | `rubocop` | tool | files | — | — | 1 |
| Ruby | `ruby` | tool | docker, github-actions, files | — | — | 7 |
| rubyenv | `rubyenv` | tool | files | — | — | 0 |
| Ruff | `ruff` | tool | pypi | Python | — | 14 |
| Rust | `rust` | tool | docker, files | — | — | 17 |
| ScalaTest | `scalatest` | tool | maven | Java, Kotlin | — | 1 |
| SharpFuzz | `sharpfuzz` | tool | nuget | C# | — | 0 |
| SonarLint | `sonarlint` | tool | files | — | — | 0 |
| sqlc | `sqlc` | tool | go | Go | — | 0 |
| SQLDelight | `sqldelight` | tool | maven | Java, Kotlin | — | 0 |
| Storybook | `storybook` | tool | npm, files | JavaScript, TypeScript | — | 2 |
| Stylelint | `stylelint` | tool | files | — | — | 2 |
| Stylus | `stylus` | tool | npm | JavaScript, TypeScript | — | 0 |
| SWC | `swc` | tool | crates, npm | Rust, JavaScript, TypeScript | — | 4 |
| Terraform | `terraform` | tool | github-actions, go, npm, pypi, files | Go, JavaScript, TypeScript, Python | — | 2 |
| Terragrunt | `terragrunt` | tool | files | — | — | 0 |
| Testcontainers | `testcontainers` | tool | go, maven, nuget, pypi | Go, Java, Kotlin, C#, Python | — | 2 |
| TestNG | `testng` | tool | maven | Java, Kotlin | — | 1 |
| TravisCI | `travisci` | tool | rubygems, files | ruby: nessun analizzatore | — | 1 |
| Turborepo | `turborepo` | tool | npm, files | JavaScript, TypeScript | — | 2 |
| Typescript | `typescript` | tool | go, npm | Go, JavaScript, TypeScript | — | 35 |
| Ultracite | `ultracite` | tool | npm | JavaScript, TypeScript | — | 0 |
| UnoCSS | `unocss` | tool | npm | JavaScript, TypeScript | — | 0 |
| uv | `uv` | tool | pypi | Python | — | 1 |
| Vale | `vale` | tool | docker, github-actions, files | — | — | 1 |
| Vite | `vite` | tool | npm, files | JavaScript, TypeScript | — | 18 |
| Vite+ | `vite-plus` | tool | npm | JavaScript, TypeScript | — | 0 |
| Vitest | `vitest` | tool | npm, files | JavaScript, TypeScript | — | 11 |
| Vue SFC compiler | `vue-sfc-compiler` | tool | npm | JavaScript, TypeScript | — | 0 |
| Webpack | `webpack` | tool | npm | JavaScript, TypeScript | — | 3 |
| Webpack Encore | `webpack-encore` | tool | npm | JavaScript, TypeScript | — | 0 |
| WireMock | `wiremock-java` | tool | maven | Java, Kotlin | — | 0 |
| xUnit | `xunit` | tool | nuget | C# | — | 2 |
| Yarn | `yarn` | tool | files | — | — | 0 |
| Zig | `zig` | tool | github-actions | — | — | 0 |

</details>

## Servizi esterni

Le voci di servizio del catalogo: 833, 813 di `kind` `service` e 20 di `kind` `project` con la `category` `service` (un software che gira accanto al sistema e a cui il codice si connette); 703 con segni per riconoscerle, 444 con un marchio: 444 con il file nel prodotto (`mark`), 0 scaricato al primo uso dalla fonte ufficiale (`mark_source`). Segni per specie, sulle voci che ne hanno: `env` 179, `files` 44, `hosts` 34, `packages` 633, `patterns` 159, `source` 1. Di quelle con segni, 3 hanno un'altra categoria (`tool` 3) e stanno nella lista della sezione precedente. Il riconoscimento misurato è la colonna Servizi della sezione precedente.

| Tipo | Voci | Con segni | Con marchio |
| --- | --- | --- | --- |
| servizio o API | 640 | 518 | 336 |
| database | 123 | 115 | 77 |
| autenticazione | 29 | 29 | 10 |
| gateway | 17 | 17 | 11 |
| coda | 15 | 15 | 9 |
| filesystem | 6 | 6 | 0 |
| altro | 3 | 3 | 1 |

<details><summary>Servizi riconoscibili: 700 voci</summary>

| Servizio | Id | Tipo | Segni | Marchio | Fixture in cui lo step lo trova (19 novembre 2026) |
| --- | --- | --- | --- | --- | --- |
| 1Password | `1password` | servizio o API | npm, pypi | sì | 0 |
| Activeloop | `activeloop` | servizio o API | pypi | sì | 0 |
| Adminer | `adminer` | servizio o API | docker | sì | 2 |
| Adobe Analytics | `adobe.analytics` | servizio o API | npm, env | no | 0 |
| Adobe Experience Manager | `adobe.experiencemanager` | servizio o API | npm, env | no | 0 |
| Adyen | `adyen` | gateway | composer, npm, pypi, rubygems, env | sì | 0 |
| AfterShip | `aftership` | servizio o API | npm, pypi | sì | 0 |
| Agora | `agora` | servizio o API | npm | sì | 0 |
| Airbrake | `airbrake` | servizio o API | npm | sì | 0 |
| Airbyte | `airbyte` | servizio o API | docker, terraform | sì | 0 |
| Aircall | `aircall` | servizio o API | npm, terraform-resource, env | sì | 0 |
| Airtable | `airtable` | servizio o API | composer, npm, env | sì | 0 |
| Akahu | `akahu` | servizio o API | npm | no | 0 |
| Akamai | `akamai` | servizio o API | npm, terraform, env | sì | 0 |
| Alby | `alby` | servizio o API | npm | sì | 0 |
| Alchemy | `alchemy` | servizio o API | npm | sì | 0 |
| Algolia | `algolia` | database | composer, crates, github-actions, npm, pypi, rubygems, terraform-resource, env | sì | 1 |
| Algorand | `algorand` | servizio o API | go, npm, pypi | sì | 0 |
| Alibaba Cloud | `alibabacloud` | servizio o API | composer, github-actions, terraform | sì | 0 |
| Alipay | `alipay` | servizio o API | maven, npm | sì | 0 |
| Aliyun OSS | `aliyun-oss` | filesystem | go, maven | no | 0 |
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
| Apicurio Registry | `apicurio-registry` | coda | docker | no | 0 |
| Apideck | `apideck` | servizio o API | composer, go, npm, pypi | no | 0 |
| Apify | `apify` | servizio o API | crates, go, npm, pypi, terraform-resource, env | no | 0 |
| App Store | `app-store` | servizio o API | npm | sì | 0 |
| Apple | `apple` | servizio o API | env | sì | 0 |
| AppSignal | `appsignal` | servizio o API | docker, npm, pypi, rubygems | sì | 0 |
| AppVeyor | `appveyor` | servizio o API | files | sì | 0 |
| Appwrite | `appwrite` | servizio o API | go, npm, pypi | sì | 0 |
| ArcGIS | `arcgis` | servizio o API | npm, pypi | sì | 0 |
| Asana | `asana` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource, env | sì | 0 |
| Atlassian | `atlassian` | servizio o API | pypi | sì | 0 |
| Atlassian Bitbucket | `atlassian.bitbucket` | servizio o API | composer | no | 0 |
| Atlassian OpsGenie | `atlassian.opsgenie` | servizio o API | npm, pypi | no | 0 |
| Atlassian Trello | `atlassian.trello` | servizio o API | composer, github-actions, npm, rubygems, hosts | no | 0 |
| Atuin Hub | `atuin-hub` | servizio o API | hosts | no | 0 |
| Atuin Sync | `atuin-sync` | servizio o API | hosts | no | 0 |
| Auth0 | `auth0` | autenticazione | composer, crates, go, npm, pypi, rubygems, terraform, env | sì | 0 |
| AWS | `aws` | servizio o API | composer, crates, docker, github-actions, go, npm, rubygems, terraform | sì | 8 |
| AWS ActiveMQ | `aws.mq` | coda | crates, go, npm, rubygems, terraform-resource | sì | 0 |
| AWS Amplify Hosting | `aws.amplifyhosting` | servizio o API | npm, terraform-resource | sì | 0 |
| AWS Api Gateway | `aws.apigateway` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Athena | `aws.athena` | database | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Bedrock | `aws.bedrock` | servizio o API | npm | sì | 0 |
| AWS Block Storage | `aws.ebs` | database | crates, go, npm, rubygems, terraform-resource | sì | 0 |
| AWS CloudFront | `aws.cloudfront` | database | composer, crates, github-actions, go, npm, pypi, rubygems, terraform-resource, env | sì | 0 |
| AWS Cloudsearch | `aws.cloudsearch` | database | crates, go, npm, rubygems, terraform-resource | sì | 0 |
| AWS Cloudwatch | `aws.cloudwatch` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Code Build | `aws.codebuild` | servizio o API | crates, github-actions, go, npm, rubygems, terraform-resource | sì | 0 |
| AWS Code Pipeline | `aws.codepipeline` | servizio o API | github-actions | sì | 0 |
| AWS Cognito | `aws.cognito` | autenticazione | go, npm, rubygems | sì | 0 |
| AWS Comprehend | `aws.comprehend` | servizio o API | npm | sì | 0 |
| AWS Compute | `aws.ec2` | servizio o API | crates, github-actions, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Container | `aws.ecs` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Container Registry | `aws.ecr` | database | crates, github-actions, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Document DB | `aws.documentdb` | database | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS DynamoDB | `aws.dynamodb` | database | composer, crates, docker, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS ElastiCache | `aws.elasticache` | database | composer, crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Fargate | `aws.fargate` | servizio o API | github-actions | sì | 0 |
| AWS File System | `aws.efs` | database | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Glacier | `aws.glacier` | database | crates, go, npm, rubygems, terraform-resource | sì | 0 |
| AWS Glue | `aws.glue` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Kafka | `aws.kafka` | coda | npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Kinesis | `aws.kinesis` | coda | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Kms | `aws.kms` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Kubernetes | `aws.eks` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Lambda | `aws.lambda` | servizio o API | composer, crates, docker, github-actions, go, npm, rubygems, terraform-resource | sì | 0 |
| AWS Lightsail | `aws.lightsail` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS MemoryDB | `aws.memorydb` | database | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Neptune | `aws.neptune` | database | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Notification Service | `aws.sns` | servizio o API | composer, crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Opensearch | `aws.opensearch` | database | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Polly | `aws.polly` | servizio o API | crates, go, npm, rubygems | sì | 0 |
| AWS RDS | `aws.rds` | database | composer, crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Redshift | `aws.redshift` | database | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Rekognition | `aws.rekognition` | servizio o API | crates, go, npm, pypi, rubygems | sì | 0 |
| AWS S3 | `aws.s3` | database | composer, crates, docker, github-actions, go, hex, npm, rubygems, terraform-resource | sì | 9 |
| AWS SageMaker | `aws.sagemaker` | servizio o API | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Secrets Manager | `aws.secretsmanager` | database | crates, go, npm, pypi, rubygems, terraform-resource | sì | 1 |
| AWS Simple Email Service | `aws.ses` | servizio o API | composer, crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS SQS | `aws.sqs` | coda | composer, crates, go, hex, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Step Functions | `aws.sfn` | servizio o API | crates, go, npm, rubygems, terraform-resource | sì | 0 |
| AWS Timestream | `aws.timestream` | database | crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| AWS Transcribe | `aws.transcribe` | servizio o API | npm | sì | 0 |
| AWS Translate | `aws.translate` | servizio o API | crates, go, npm, rubygems | sì | 0 |
| Azure | `azure` | servizio o API | crates, docker, github-actions, go, npm, pypi, rubygems, terraform | sì | 1 |
| Azure AI Document Intelligence | `azure.documentintelligence` | servizio o API | pypi | no | 0 |
| Azure Application Insights | `azure.applicationinsights` | servizio o API | nuget | no | 0 |
| Azure Blob Storage | `azure.blobstorage` | filesystem | composer, crates, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Azure Container Apps | `azure.containerapps` | servizio o API | nuget | no | 0 |
| Azure Cosmos DB | `azure.cosmosdb` | database | crates, go, npm, rubygems, terraform-resource | sì | 0 |
| Azure Functions | `azure.functions` | servizio o API | crates, github-actions, npm, rubygems, terraform-resource | sì | 0 |
| Azure Key Vault | `azure.keyvault` | servizio o API | nuget, env | no | 0 |
| Azure Kubernetes | `azure.aks` | servizio o API | terraform-resource | sì | 0 |
| Azure MariaDB | `azure.mariadb` | database | crates, go, npm, rubygems, terraform-resource | sì | 0 |
| Azure MySQL | `azure.mysql` | database | crates, github-actions, go, npm, rubygems, terraform-resource | sì | 0 |
| Azure Openai | `azure.openai` | servizio o API | npm, nuget | sì | 0 |
| Azure Postgres | `azure.postgres` | database | crates, github-actions, go, npm, rubygems, terraform-resource | sì | 0 |
| Azure Redis | `azure.redis` | database | crates, go, npm, rubygems, terraform-resource | sì | 0 |
| Azure SQL | `azure.sql` | database | crates, github-actions, go, npm, rubygems, terraform-resource | sì | 0 |
| Azure Static Web Apps | `azure.staticwebapps` | servizio o API | crates, github-actions, npm, rubygems, terraform-resource | sì | 1 |
| Azure Storage | `azure.storage` | database | composer, crates, npm, rubygems, terraform-resource | sì | 1 |
| AzureCI | `azure.ci` | servizio o API | files | sì | 0 |
| Backblaze | `backblaze` | servizio o API | npm | sì | 0 |
| Backendless | `backendless` | servizio o API | npm | sì | 0 |
| Base44 | `base44` | servizio o API | npm | no | 0 |
| Beehiiv | `beehiiv` | servizio o API | npm, env | no | 0 |
| Better Auth | `betterauth` | autenticazione | npm, env | sì | 0 |
| Better Stack | `betterstack` | servizio o API | composer, npm, rubygems, terraform, env | sì | 0 |
| BigCommerce | `bigcommerce` | servizio o API | composer, npm, pypi, terraform-resource | sì | 0 |
| Binance | `binance` | servizio o API | npm, pypi | sì | 0 |
| Bing Maps | `azure.maps` | servizio o API | npm, terraform-resource, env | sì | 0 |
| Bitbucket Pipelines | `atlassian.bitbucketpipelines` | servizio o API | files | no | 0 |
| Bitly | `bitly` | servizio o API | npm | sì | 0 |
| Bitwarden | `bitwarden` | servizio o API | npm | sì | 0 |
| Blackfire | `blackfire` | servizio o API | composer, docker, env | no | 0 |
| Bluesky | `bluesky` | servizio o API | npm | sì | 0 |
| Box | `box` | servizio o API | composer, npm, pypi | sì | 0 |
| Braintree | `braintree` | servizio o API | npm | sì | 0 |
| Braintrust | `braintrust` | servizio o API | npm, pypi | sì | 0 |
| Brevo | `brevo` | servizio o API | composer, go, npm, rubygems, env | sì | 0 |
| Browser Use | `browseruse` | servizio o API | pypi | no | 0 |
| Browserbase | `browerbase` | servizio o API | composer, pypi | no | 0 |
| Browserless | `browserless` | servizio o API | docker, env | no | 0 |
| Browserstack | `browserstack` | servizio o API | npm, rubygems, files | no | 1 |
| Bugsnag | `bugsnag` | servizio o API | composer, go, npm, pypi, rubygems, env | no | 0 |
| bunq | `bunq` | servizio o API | pypi | sì | 0 |
| Caddy | `caddy` | servizio o API | docker, go | sì | 2 |
| Cal.com | `calcom` | servizio o API | npm | sì | 0 |
| Calendly | `calendly` | servizio o API | npm, env | sì | 0 |
| Campaign Monitor | `campaign-monitor` | servizio o API | npm | sì | 0 |
| Camunda | `camunda` | servizio o API | npm | sì | 0 |
| Chargebee | `chargebee` | gateway | composer, go, npm, pypi, rubygems, env | no | 0 |
| ChartMogul | `chartmogul` | servizio o API | npm, pypi | sì | 0 |
| Checkov | `checkov` | servizio o API | docker, github-actions | sì | 0 |
| ChromaDB | `chromadb` | database | pypi | no | 0 |
| Chromatic | `chromatic` | servizio o API | npm | sì | 1 |
| CircleCI | `circleci` | servizio o API | github-actions, rubygems, files | sì | 0 |
| CirrusCI | `cirrusci` | servizio o API | files | sì | 0 |
| Civo | `civo` | servizio o API | go | sì | 0 |
| Clerk | `clerk` | autenticazione | go, npm, pypi, rubygems, env | sì | 0 |
| ClickHouse | `clickhouse` | database | composer, crates, docker, go, npm, pypi, rubygems, terraform, terraform-resource | sì | 2 |
| ClickSend | `clicksend` | servizio o API | npm, env | no | 0 |
| ClickUp | `clickup` | servizio o API | env | sì | 0 |
| Cloud AI Platform | `gcp.aiplatform` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Artifact Registry | `gcp.artifactregistry` | database | go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud BigQuery | `gcp.bigquery` | database | composer, crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud BigTable | `gcp.bigtable` | database | composer, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Build | `gcp.cloudbuild` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Dataflow | `gcp.dataflow` | servizio o API | composer, go, npm, rubygems, terraform-resource | sì | 0 |
| Cloud Dataproc | `gcp.dataproc` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Datastore | `gcp.datastore` | database | composer, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Dialogflow | `gcp.dialogflow` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Functions | `gcp.functions` | servizio o API | composer, github-actions, go, npm, rubygems, terraform-resource | sì | 0 |
| Cloud Functions for Firebase | `firebase.functions` | servizio o API | npm, pypi | no | 0 |
| Cloud KMS | `gcp.kms` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | sì | 1 |
| Cloud Language | `gcp.language` | servizio o API | composer, go, npm, pypi, rubygems | sì | 0 |
| Cloud Logging | `gcp.logging` | servizio o API | composer, crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Memorystore | `gcp.memorystore` | database | composer, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Run | `gcp.cloudrun` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Secret Manager | `gcp.secretmanager` | database | composer, github-actions, go, npm, pypi, rubygems, terraform-resource | sì | 1 |
| Cloud Spanner | `gcp.spanner` | database | composer, crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Speech | `gcp.speech` | servizio o API | composer, go, npm, pypi, rubygems | sì | 0 |
| Cloud SQL | `gcp.sql` | database | composer, go, npm, rubygems, terraform-resource | sì | 0 |
| Cloud Storage | `gcp.gcs` | database | composer, crates, github-actions, go, npm, pypi, rubygems, terraform-resource | sì | 2 |
| Cloud Tasks | `gcp.tasks` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Cloud Vision | `gcp.vision` | servizio o API | composer, go, npm, pypi, rubygems | sì | 0 |
| CloudBees | `cloudbees` | servizio o API | env | sì | 0 |
| CloudBees Codeship | `cloudbees.codeship` | servizio o API | files | no | 0 |
| Cloudflare | `cloudflare` | servizio o API | composer, crates, npm, pypi, rubygems, terraform, env | sì | 0 |
| Cloudflare Pages | `cloudflare.pages` | servizio o API | github-actions, terraform-resource | sì | 0 |
| Cloudflare R2 | `cloudflare.r2` | database | npm, terraform-resource | no | 0 |
| Cloudflare Turnstile | `cloudflare.turnstile` | servizio o API | npm, env | no | 0 |
| Cloudflare Workers | `cloudflare.workers` | servizio o API | crates, github-actions, npm, terraform-resource, files | sì | 0 |
| Cloudinary | `cloudinary` | servizio o API | composer, go, npm, pypi, rubygems, env | sì | 0 |
| Cockroach Labs | `cockroach-labs` | database | go | sì | 0 |
| CockroachDB | `cockroachdb` | database | composer, terraform | no | 0 |
| Code Climate | `codeclimate` | servizio o API | github-actions, files | sì | 0 |
| Codecov | `codecov` | servizio o API | github-actions, files | sì | 5 |
| CodeSandbox | `codesandbox` | servizio o API | npm | sì | 0 |
| Cohere AI | `cohereai` | servizio o API | go, npm, pypi, env | no | 0 |
| Coinbase | `coinbase` | servizio o API | npm | sì | 0 |
| Commercetools | `commercetools` | servizio o API | npm | no | 0 |
| Composio | `composio` | servizio o API | npm, pypi, env | no | 0 |
| Concourse CI | `concourseci` | servizio o API | files | no | 0 |
| Conekta | `conekta` | servizio o API | npm, pypi | sì | 0 |
| Confluence | `atlassian.confluence` | servizio o API | docker, github-actions, npm | sì | 0 |
| Consul | `consul` | servizio o API | docker, go | sì | 0 |
| Contentful | `contentful` | servizio o API | composer, npm, pypi, env | sì | 0 |
| Contentstack | `contentstack` | servizio o API | npm | sì | 0 |
| Convex | `convexdb` | database | crates, npm, pypi, terraform-resource, env | sì | 0 |
| CoreDNS | `coredns` | altro | docker | no | 0 |
| Couchbase | `couchbase` | database | composer, crates, docker, go, npm, pypi, rubygems, terraform, terraform-resource | sì | 0 |
| Coveralls | `coveralls` | servizio o API | github-actions, go, npm, rubygems | sì | 1 |
| Coze | `coze` | servizio o API | npm | sì | 0 |
| CrateDB | `cratedb` | database | docker | sì | 0 |
| Crawl4AI | `crawl4ai` | servizio o API | docker, pypi, env | no | 0 |
| Crowdin | `crowdin` | servizio o API | composer, npm, files | sì | 6 |
| D-Wave Systems | `d-wave-systems` | servizio o API | pypi | sì | 0 |
| Databricks | `databricks` | servizio o API | github-actions, go, pypi, terraform, terraform-resource, env | sì | 0 |
| Databuddy | `databuddy` | servizio o API | npm, env | no | 0 |
| Datadog | `datadog` | servizio o API | composer, crates, docker, github-actions, go, npm, pypi, rubygems, terraform, terraform-resource, env | sì | 1 |
| DataDome | `datadome` | servizio o API | composer, go, npm, pypi, rubygems | no | 0 |
| Dataiku | `dataiku` | servizio o API | pypi | sì | 0 |
| Datastax | `datastax` | database | composer, terraform, terraform-resource | sì | 0 |
| Dato CMS | `datocms` | servizio o API | npm | sì | 0 |
| Deepgram | `deepgram` | servizio o API | npm, pypi | sì | 0 |
| DeepL | `deepl` | servizio o API | npm, pypi | sì | 0 |
| Deepseek | `deepseek` | servizio o API | npm, pypi, env | sì | 0 |
| Deepsource | `deepsource` | servizio o API | github-actions, files | no | 0 |
| Deno Deploy | `denodeploy` | servizio o API | deno, github-actions | sì | 0 |
| Dependabot | `dependabot` | servizio o API | github-actions, rubygems | sì | 0 |
| Depot.dev | `depotdev` | servizio o API | github-actions, files | no | 2 |
| diagrams.net | `diagrams-net` | servizio o API | hosts | no | 0 |
| DigitalOcean | `digitalocean` | servizio o API | github-actions, npm, pypi, terraform | sì | 0 |
| Directus | `directus` | servizio o API | npm | sì | 0 |
| Discord | `discord` | servizio o API | github-actions, npm, env | sì | 1 |
| Discord OAuth | `discord.oauth` | autenticazione | composer | no | 0 |
| Discourse | `discourse` | servizio o API | docker | sì | 0 |
| Docusign | `docusign` | servizio o API | composer, npm, rubygems, env | no | 0 |
| Dodo Payments | `dodo-payments` | servizio o API | npm, pypi | sì | 0 |
| Dokku | `dokku` | servizio o API | docker, github-actions, env | sì | 0 |
| DroneCI | `droneci` | servizio o API | docker, files | no | 0 |
| Dropbox | `dropbox` | servizio o API | composer, pypi, env | sì | 0 |
| Drupal | `drupal` | servizio o API | composer, docker | sì | 0 |
| DuckDB | `duckdb` | database | go, npm, pypi, terraform-resource | sì | 0 |
| DuckDuckGo Icons | `duckduckgo-icons` | servizio o API | hosts | no | 0 |
| Dynatrace | `dynatrace` | servizio o API | npm, env | sì | 0 |
| eID Easy | `eideasy` | servizio o API | npm, hosts | no | 0 |
| Elastic Cloud | `elasticcloud` | servizio o API | terraform | sì | 0 |
| Elasticsearch | `elasticsearch` | database | composer, crates, docker, github-actions, go, npm, pypi, rubygems, terraform, terraform-resource, env | sì | 2 |
| Elevenlabs | `elevenlabs` | servizio o API | npm, pypi, env | sì | 0 |
| Enable Banking | `enable-banking` | servizio o API | hosts | no | 0 |
| Envoy | `envoy` | gateway | docker, go | no | 0 |
| Equinix | `equinix` | servizio o API | terraform | no | 0 |
| etcd | `etcd` | database | go | sì | 0 |
| Event Store | `event-store` | database | go, npm | sì | 0 |
| Evernote | `evernote` | servizio o API | npm | sì | 0 |
| Expo.dev | `expodev` | servizio o API | github-actions, files | sì | 0 |
| Facebook | `facebook` | servizio o API | npm, env | sì | 0 |
| FastAPI Cloud | `fastapi-cloud` | servizio o API | env | no | 0 |
| Fastly | `fastly` | servizio o API | crates, go, npm, pypi, rubygems, env | sì | 0 |
| Fathom | `fathom` | servizio o API | npm, env | sì | 0 |
| Figma | `figma` | servizio o API | npm, env | sì | 0 |
| Firebase | `firebase` | servizio o API | crates, github-actions, npm, pypi, rubygems, files, env | sì | 1 |
| Firebase Analytics | `firebase.analytics` | servizio o API | maven | no | 0 |
| Firebase Cloud Messaging | `firebase.messaging` | servizio o API | maven | no | 0 |
| Firebase Firestore | `firebase.firestore` | database | composer, terraform-resource | no | 0 |
| Firecrawl | `firecrawl` | servizio o API | composer, crates, go, pypi, env | no | 0 |
| Firepit | `firepit` | servizio o API | docker | no | 0 |
| flagd | `flagd` | servizio o API | crates, docker, go, maven | no | 0 |
| Fluentd | `fluentd` | servizio o API | docker, go | sì | 0 |
| Flyio | `flyio` | servizio o API | github-actions, terraform, files | sì | 1 |
| Formbricks | `formbricks` | servizio o API | npm | sì | 0 |
| FoundationDB | `foundationdb` | database | pypi | no | 0 |
| Freshdesk | `freshdesk` | servizio o API | composer, go, npm, pypi, rubygems, env | no | 0 |
| Friendly Captcha | `friendly-captcha` | servizio o API | npm, env | no | 0 |
| Frontegg | `frontegg` | autenticazione | npm, pypi, terraform | no | 0 |
| Fusionauth | `fusionauth` | autenticazione | composer, go, npm, pypi, rubygems | sì | 0 |
| GCP | `gcp` | servizio o API | composer, github-actions, npm, pypi, terraform, env | sì | 3 |
| Gemini AI | `geminiai` | servizio o API | npm, pypi, env, hosts | no | 0 |
| Ghost | `ghost` | servizio o API | docker, npm, env | sì | 0 |
| GIPHY | `giphy` | servizio o API | npm | sì | 0 |
| Gitbook | `gitbook` | servizio o API | npm | sì | 0 |
| Gitea | `gitea` | servizio o API | go | sì | 0 |
| GitGuardian | `gitguardian` | servizio o API | docker, github-actions, go | no | 0 |
| GitHub | `github` | servizio o API | composer, npm, pypi, rubygems, terraform, terraform-resource, files, hosts | sì | 1 |
| GitHub CodeQL | `github.codeql` | servizio o API | github-actions | no | 0 |
| GitHub OAuth | `github.oauth` | autenticazione | npm | no | 0 |
| Github Pages | `github.pages` | servizio o API | github-actions, files | sì | 7 |
| Gitlab | `gitlab` | servizio o API | composer, crates, npm, pypi, rubygems, terraform, terraform-resource | sì | 0 |
| Gitlab CI | `gitlab.ci` | servizio o API | files | no | 0 |
| GitLab OAuth | `gitlab.oauth` | autenticazione | composer | no | 0 |
| Gmail | `google.gmail` | servizio o API | npm, rubygems, env | sì | 0 |
| GoCardless Bank Account Data | `gocardless-bank-account-data` | servizio o API | hosts | no | 0 |
| Google Ads | `google-ads` | servizio o API | npm, pypi | sì | 0 |
| Google Analytics | `google.analytics` | servizio o API | composer, npm, pypi, terraform-resource, env, hosts | sì | 0 |
| Google App Engine | `gcp.appengine` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Google Calendar | `google.calendar` | servizio o API | composer, npm, pypi, rubygems | sì | 0 |
| Google Chat | `google.chat` | servizio o API | npm, rubygems, terraform-resource | sì | 0 |
| Google Compute | `gcp.gce` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform-resource | sì | 1 |
| Google DNS | `gcp.dns` | servizio o API | go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Google Docs | `google.docs` | servizio o API | npm, rubygems | sì | 0 |
| Google Drive | `google.drive` | servizio o API | crates, npm, rubygems, terraform-resource | sì | 0 |
| Google Earth Engine | `google-earth-engine` | servizio o API | npm | sì | 0 |
| Google Forms | `google.forms` | servizio o API | npm, rubygems, terraform-resource | sì | 0 |
| Google Keep | `google.keep` | servizio o API | rubygems | sì | 0 |
| Google Kubernetes | `gcp.gke` | servizio o API | github-actions, terraform-resource | sì | 0 |
| Google Maps | `gcp.maps` | servizio o API | go, npm, pypi, rubygems, env | sì | 0 |
| Google Meet | `google.meet` | servizio o API | npm, pypi, rubygems | sì | 0 |
| Google OAuth | `google.oauth` | autenticazione | npm | no | 0 |
| Google Pay | `google.pay` | gateway | npm, env | sì | 0 |
| Google reCAPTCHA | `google.recaptcha` | servizio o API | pypi, env | no | 0 |
| Google Sheets | `google.sheets` | servizio o API | composer, crates, npm, rubygems, terraform-resource | sì | 0 |
| Google Slides | `google.slides` | servizio o API | npm, rubygems | sì | 0 |
| Google Tasks | `google.tasks` | servizio o API | npm, rubygems | sì | 0 |
| Google Translate | `gcp.translate` | servizio o API | composer, go, npm, pypi, rubygems | sì | 0 |
| Gotenberg | `gotenberg` | servizio o API | docker, pypi | no | 0 |
| Grafana | `grafana` | servizio o API | docker, terraform | sì | 1 |
| Grafana LGTM | `grafana.lgtm` | servizio o API | docker | no | 0 |
| Gravatar | `gravatar` | servizio o API | env | no | 0 |
| Graylog | `graylog` | altro | nuget | sì | 0 |
| GreenMail | `greenmail` | servizio o API | docker | no | 0 |
| Groq | `groq` | servizio o API | npm, pypi, env | no | 0 |
| H2 | `h2` | database | maven | no | 3 |
| Hanko | `hanko` | autenticazione | npm | no | 0 |
| HAProxy | `haproxy` | servizio o API | docker | sì | 0 |
| HashiCorp Vault | `vault` | servizio o API | go | sì | 0 |
| hCaptcha | `hcaptcha` | servizio o API | env | no | 0 |
| Help Scout | `help-scout` | servizio o API | env | no | 0 |
| HERE Maps | `heremaps` | servizio o API | npm, env | no | 0 |
| Heroku | `heroku` | servizio o API | composer, github-actions, rubygems, terraform | no | 0 |
| Hetzner | `hetzner` | servizio o API | composer, go, pypi, rubygems, terraform | sì | 0 |
| Honeybadger | `honeybadger` | servizio o API | composer, go, npm, pypi, rubygems, env | sì | 0 |
| Honeycomb | `honeycomb` | servizio o API | go, pypi | no | 0 |
| Hostinger | `hostinger` | servizio o API | composer, npm, pypi | sì | 0 |
| Hotjar | `hotjar` | servizio o API | npm, env | sì | 0 |
| HSQLDB | `hsqldb` | database | maven | no | 1 |
| HTTPD | `httpd` | servizio o API | docker, files | no | 0 |
| Huawei Cloud OBS | `huawei-obs` | filesystem | go | no | 0 |
| HubSpot | `hubspot` | servizio o API | composer, npm | sì | 0 |
| Hugging Face | `huggingface` | servizio o API | npm, pypi, env | sì | 1 |
| HyperDX | `hyperdx` | servizio o API | go, npm | no | 0 |
| Hypertune | `hypertune` | servizio o API | npm | no | 0 |
| IBM Cloud | `ibmcloud` | servizio o API | terraform | no | 0 |
| ifttt | `ifttt` | servizio o API | env | sì | 0 |
| Immich | `immich` | servizio o API | npm | sì | 0 |
| Inbucket | `inbucket` | servizio o API | docker | no | 0 |
| Infisical | `infisical` | servizio o API | docker, npm, files, env | no | 0 |
| InfluxDB | `influxdb` | database | composer, crates, docker, go, npm, pypi, rubygems | sì | 0 |
| Inngest | `inngest` | servizio o API | crates, go, npm, pypi, env | no | 1 |
| Instagram | `instagram` | servizio o API | env | sì | 0 |
| Instana | `instana` | altro | composer, docker, maven, npm, pypi | no | 0 |
| Integration.app | `integrationapp` | servizio o API | npm | no | 0 |
| Intercom | `intercom` | servizio o API | composer, npm, rubygems, env | sì | 0 |
| Internet Archive | `internet-archive` | servizio o API | pypi | sì | 0 |
| Internet Computer | `internet-computer` | servizio o API | npm | sì | 0 |
| Intuit | `intuit` | gateway | env | sì | 0 |
| Ionos | `ionos` | servizio o API | go, pypi | sì | 0 |
| IOTA | `iota` | servizio o API | npm, pypi | sì | 0 |
| IPinfo | `ipinfo` | servizio o API | hosts | no | 0 |
| Jaeger | `jaeger` | servizio o API | docker, go | sì | 0 |
| Jellyfin | `jellyfin` | servizio o API | npm | sì | 1 |
| Jenkins | `jenkins` | servizio o API | docker, pypi, rubygems, files | sì | 0 |
| JFrog | `jfrog` | servizio o API | go | sì | 0 |
| JHipster Control Center | `jhipster-control-center` | servizio o API | docker | no | 0 |
| Jira | `atlassian.jira` | servizio o API | composer, crates, docker, github-actions, npm, rubygems, terraform-resource | sì | 0 |
| Jira Software | `jira-software` | servizio o API | npm | sì | 0 |
| Jitsi | `jitsi` | servizio o API | npm | sì | 0 |
| Joomla! | `joomla` | servizio o API | composer, docker | sì | 0 |
| Kafka | `kafka` | coda | maven, nuget | no | 1 |
| Kaggle | `kaggle` | servizio o API | pypi | sì | 0 |
| Keeper | `keeper` | servizio o API | npm, pypi | sì | 0 |
| Kentico | `kentico` | servizio o API | npm, rubygems | sì | 0 |
| Keycloak | `keycloak` | autenticazione | docker, npm, pypi | sì | 0 |
| Kibana | `kibana` | servizio o API | docker, env | sì | 1 |
| Kinde | `kinde` | autenticazione | composer, npm, pypi, rubygems | no | 0 |
| Klarna | `klarna` | gateway | rubygems, terraform-resource, env | sì | 0 |
| Klaviyo | `klaviyo` | servizio o API | composer, terraform-resource | no | 0 |
| Koala Analytics | `koalaanalytics` | servizio o API | npm | no | 0 |
| Kong | `kong` | servizio o API | docker, files | sì | 0 |
| Koyeb | `koyeb` | servizio o API | npm, files | sì | 0 |
| Kubernetes | `kubernetes` | servizio o API | composer, crates, github-actions, npm, pypi, rubygems, terraform, files | sì | 1 |
| Lago | `lago` | servizio o API | docker, go, npm, pypi, rubygems, env | no | 0 |
| LangChain Corporate | `langchain-corporate` | servizio o API | npm, pypi | sì | 1 |
| Laravel Nightwatch | `laravel-nightwatch` | servizio o API | composer | no | 0 |
| Last.fm | `lastfm` | servizio o API | hosts | no | 0 |
| LaunchDarkly | `launchdarkly` | servizio o API | composer, crates, github-actions, go, npm, rubygems, terraform, env | no | 0 |
| Lemon Squeezy | `lemonsqueezy` | gateway | composer, go, npm, rubygems, env, hosts | sì | 0 |
| Let's Encrypt | `lets-encrypt` | servizio o API | pypi, hosts | sì | 0 |
| libSQL | `libsql` | database | composer, crates, go, npm, pypi, rubygems | no | 0 |
| LINE | `line` | servizio o API | npm, pypi | sì | 0 |
| Linear | `linear` | servizio o API | npm, pypi, env | sì | 0 |
| Linkedin | `linkedin` | servizio o API | env | no | 0 |
| ListenBrainz | `listenbrainz` | servizio o API | hosts | no | 0 |
| LiteFS | `litefs` | database | docker, npm | no | 0 |
| LiveChat | `livechat` | servizio o API | npm | sì | 0 |
| LiveKit | `livekit` | servizio o API | go, npm, pypi | sì | 1 |
| LM Studio | `lm-studio` | servizio o API | npm, pypi | sì | 0 |
| LogRocket | `logrocket` | servizio o API | npm | no | 0 |
| LogSnag | `logsnag` | servizio o API | npm, pypi, env | no | 0 |
| Logstash | `logstash` | servizio o API | docker, go, npm, rubygems | sì | 1 |
| Logto | `logtoio` | autenticazione | composer, go, npm, pypi, rubygems, env | no | 0 |
| Looker | `looker` | servizio o API | npm | sì | 0 |
| Loom | `loom` | servizio o API | npm | sì | 0 |
| Loops | `loops` | servizio o API | npm | sì | 0 |
| Lovable | `lovable` | servizio o API | npm | no | 0 |
| Magento | `magento` | servizio o API | composer, npm | no | 0 |
| Magic | `magic` | autenticazione | npm | sì | 0 |
| MailChannels | `mailchannels` | servizio o API | env | no | 0 |
| Mailchimp | `mailchimp` | servizio o API | composer, npm, rubygems, terraform-resource, env | sì | 0 |
| MailDev | `maildev` | servizio o API | npm | no | 0 |
| Mailgun | `mailgun` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource, env | sì | 0 |
| Mailhog | `mailhog` | servizio o API | docker, go | no | 1 |
| Mailjet | `mailjet` | servizio o API | composer, crates, npm, rubygems, env | no | 0 |
| Mailpit | `mailpit` | servizio o API | docker | no | 0 |
| Mailtrap | `mailtrap` | servizio o API | npm, pypi | sì | 0 |
| MajorLeagueCyber | `majorleaguecyber` | servizio o API | hosts | no | 0 |
| Mandrill | `mandrill` | servizio o API | env | no | 0 |
| Mapbox | `mapbox` | servizio o API | composer, crates, npm, pypi, rubygems, env | sì | 0 |
| MapTiler | `maptiler` | servizio o API | npm | sì | 0 |
| MariaDB | `mariadb` | database | docker, npm, rubygems | sì | 6 |
| Matomo | `matomo` | servizio o API | docker, env | sì | 0 |
| Matrix | `matrix` | servizio o API | npm | sì | 0 |
| Mattermost | `mattermost` | servizio o API | npm | sì | 0 |
| MaxMind | `maxmind` | servizio o API | env | no | 0 |
| Meilisearch | `meilisearch` | database | composer, crates, docker, go, npm, pypi, rubygems, env | sì | 1 |
| Memcached | `memcached` | database | crates, docker, npm, rubygems, env | no | 0 |
| Mercado Pago | `mercado-pago` | servizio o API | go, npm, pypi | sì | 0 |
| Merge.dev | `mergedev` | servizio o API | composer, go, npm, pypi, rubygems | no | 0 |
| Metabase | `metabase` | servizio o API | docker, npm | sì | 0 |
| Microsoft Entra ID OAuth | `microsoft-entra-oauth` | autenticazione | composer | no | 0 |
| Microsoft OAuth | `microsoft.oauth` | autenticazione | npm | no | 0 |
| Microsoft Outlook | `microsoft.outlook` | servizio o API | env | no | 0 |
| Microsoft SQL Server | `microsoft-sql-server` | database | go, nuget | no | 0 |
| MicroStrategy | `microstrategy` | servizio o API | pypi | sì | 0 |
| MilvusDB | `milvusdb` | database | docker, go, npm, pypi, terraform-resource, env | no | 0 |
| MinIO | `minio` | database | docker, go, maven | sì | 0 |
| Miro | `miro` | servizio o API | npm, env | sì | 0 |
| Mistral AI | `mistralai` | servizio o API | go, npm, pypi, env | sì | 0 |
| Mixpanel | `mixpanel` | servizio o API | composer, go, npm, pypi, rubygems, terraform-resource, env | sì | 0 |
| mock-oauth2-server | `mock-oauth2-server` | autenticazione | docker | no | 0 |
| Modal | `modal` | servizio o API | pypi | sì | 0 |
| ModelScope | `modelscope` | servizio o API | pypi | sì | 0 |
| Monday | `monday` | servizio o API | npm | no | 0 |
| Mongo Express | `mongoexpress` | servizio o API | docker | no | 2 |
| MongoDB | `mongodb` | database | composer, crates, docker, go, maven, npm, nuget, pypi, rubygems, terraform-resource, env | sì | 4 |
| MongoDB Atlas | `mongodbatlas` | servizio o API | npm, pypi, terraform | no | 0 |
| MS SQL | `mssql` | database | npm, rubygems | no | 0 |
| MusicBrainz | `musicbrainz` | servizio o API | env | no | 0 |
| Mysql | `mysql` | database | crates, docker, go, maven, npm, nuget, pypi, rubygems, terraform-resource, env | sì | 9 |
| n8n | `n8n` | servizio o API | docker, npm, env | sì | 0 |
| Nango | `nango` | servizio o API | docker, npm, files, env | no | 0 |
| Nats | `nats` | coda | composer, crates, docker, go, npm, pypi, rubygems | no | 0 |
| Neo4j | `neo4j` | database | crates, docker, go, npm, pypi, rubygems | sì | 0 |
| NeonDB | `neondb` | database | docker, npm, pypi | no | 0 |
| NetBox Census | `netbox-census` | servizio o API | hosts | no | 0 |
| NetBox Copilot | `netbox-copilot` | servizio o API | env, hosts | no | 0 |
| Netlify | `netlify` | servizio o API | github-actions, npm, files | sì | 3 |
| New Relic | `newrelic` | servizio o API | composer, go, npm, pypi, rubygems, terraform, env | sì | 0 |
| Nextcloud | `nextcloud` | servizio o API | docker | sì | 0 |
| Nginx | `nginx` | servizio o API | docker, files | sì | 7 |
| Nhost | `nhost` | servizio o API | npm | sì | 0 |
| Nomad | `nomad` | servizio o API | go | sì | 0 |
| Notion | `notion` | servizio o API | composer, crates, npm, rubygems, env | sì | 0 |
| Novy | `novu` | servizio o API | composer, docker, go, npm, pypi, rubygems | sì | 0 |
| NX Cloud | `nxcloud` | servizio o API | npm | no | 0 |
| Oceanbase | `oceanbase` | database | docker | sì | 0 |
| Okta | `okta` | autenticazione | composer, crates, npm, pypi, rubygems, terraform, env | sì | 1 |
| Okta OAuth | `okta.oauth` | autenticazione | composer | no | 0 |
| Ollama | `ollama` | servizio o API | npm, nuget, pypi, env | sì | 0 |
| OMDb | `omdb` | servizio o API | hosts | no | 0 |
| OneDrive | `microsoft.onedrive` | servizio o API | composer, crates, npm, terraform-resource | no | 0 |
| OnlineOrNot | `onlineornot` | servizio o API | npm | no | 0 |
| Open Food Facts | `open-food-facts` | servizio o API | pypi | no | 0 |
| Openai | `openai` | servizio o API | composer, go, npm, pypi, env, hosts | no | 5 |
| OpenCage | `opencage` | servizio o API | pypi | sì | 0 |
| OpenLDAP | `openldap` | autenticazione | docker | no | 0 |
| OpenRouter | `openrouter` | gateway | npm, pypi | sì | 0 |
| OpenSea | `opensea` | servizio o API | npm | sì | 0 |
| OpenSearch | `opensearch` | database | docker, go, pypi | sì | 0 |
| OpenStack Swift | `openstack.swift` | filesystem | pypi | no | 0 |
| OpenTelemetry Collector | `otel-collector` | servizio o API | docker | no | 0 |
| OpenTelemetry eBPF Profiler | `otel-ebpf-profiler` | servizio o API | docker | no | 0 |
| OpenZeppelin | `openzeppelin` | servizio o API | npm | sì | 0 |
| Opsgenie | `opsgenie` | servizio o API | hosts | no | 0 |
| Optimizely | `optimizely` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, env | no | 0 |
| Oracle Cloud | `oraclecloud` | servizio o API | composer, npm, rubygems, terraform | no | 0 |
| Oracle Database | `oracledatabase` | database | go, pypi | no | 0 |
| Orb | `withorb` | servizio o API | go, npm, pypi | no | 0 |
| Ory | `orysh` | autenticazione | composer, go, npm | sì | 0 |
| OVH | `ovh` | servizio o API | composer, npm, terraform, env | sì | 0 |
| OVH Database | `ovh.database` | database | terraform-resource | no | 0 |
| OVH Dedicated Server | `ovh.dedicated` | servizio o API | terraform-resource | no | 0 |
| OVH Kubernetes | `ovh.kubernetes` | servizio o API | terraform-resource | no | 0 |
| OVH Storage | `ovh.storage` | database | terraform-resource | no | 0 |
| OVH VPS | `ovh.vps` | servizio o API | terraform-resource | no | 0 |
| Paddle | `paddle` | gateway | composer, go, npm, pypi, env, hosts | sì | 0 |
| Pagerduty | `pagerduty` | servizio o API | composer, crates, npm, pypi, rubygems, terraform, env, hosts | sì | 0 |
| PagerTree | `pagertree` | servizio o API | env | no | 0 |
| Papercut SMTP | `papercut-smtp` | servizio o API | docker | no | 0 |
| Papertrail | `papertrail` | servizio o API | composer, go, npm, rubygems, env | no | 0 |
| Paragon | `useparagon` | servizio o API | npm | no | 0 |
| Patreon | `patreon` | servizio o API | npm, pypi | sì | 0 |
| Payload | `payloadcms` | servizio o API | npm | sì | 0 |
| Paypal | `paypal` | gateway | composer, crates, go, npm, pypi, rubygems, env | sì | 0 |
| Paystack | `paystack` | gateway | npm, env | no | 0 |
| Percona | `percona` | database | docker | no | 0 |
| Percy | `percy` | servizio o API | npm | sì | 0 |
| Perplexity | `perplexity` | servizio o API | npm, pypi | sì | 0 |
| Perplexity AI | `perplexityai` | servizio o API | npm, env | no | 0 |
| Pexels | `pexels` | servizio o API | npm | sì | 0 |
| Pinecone | `pinecone` | database | crates, go, npm, pypi, terraform, terraform-resource, env | sì | 0 |
| Pingdom | `pingdom` | servizio o API | terraform, env | sì | 0 |
| Pirsch Analytics | `pirschanalytics` | servizio o API | composer, go, npm, rubygems | no | 0 |
| PlaceKit | `placekit` | servizio o API | npm | no | 0 |
| Plain | `plain` | servizio o API | npm | no | 0 |
| PlanetScale | `planetscale` | database | github-actions | sì | 0 |
| Platform.sh | `platformsh` | servizio o API | files | sì | 0 |
| Plausible | `plausible` | servizio o API | composer, docker, go, npm, rubygems, env | no | 0 |
| Pluggy | `pluggy` | servizio o API | npm | no | 0 |
| PocketBase | `pocketbase` | database | npm, pypi | sì | 0 |
| Poe | `poe` | servizio o API | pypi | sì | 0 |
| Polar | `polarsh` | gateway | composer, go, npm, pypi, env | no | 0 |
| Polkadot | `polkadot` | servizio o API | npm | sì | 0 |
| Postgres | `postgresql` | database | composer, crates, deno, docker, go, hex, maven, npm, nuget, pypi, rubygems, terraform-resource, env | sì | 32 |
| Postgrest | `postgrest` | servizio o API | docker | no | 0 |
| PostHog | `posthog` | servizio o API | composer, crates, go, npm, pypi, rubygems, env | sì | 2 |
| Postman | `postman` | servizio o API | npm | sì | 0 |
| Postmark | `postmark` | servizio o API | composer, hex, npm, rubygems | no | 0 |
| PowerSync | `powersync` | servizio o API | env | no | 0 |
| Prestashop | `prestashop` | servizio o API | composer | sì | 0 |
| Prisma Cloud | `prismacloud` | servizio o API | terraform | no | 0 |
| Prismic | `prismic` | servizio o API | npm | sì | 0 |
| Prometheus | `prometheus` | servizio o API | composer, crates, docker, go, maven, npm, pypi, rubygems | sì | 2 |
| PropelAuth | `propelauth` | autenticazione | crates, go, npm, pypi | no | 0 |
| PubSub | `gcp.pubsub` | coda | composer, crates, go, npm, pypi, rubygems, terraform-resource | sì | 0 |
| Puppeteer | `puppeteer` | servizio o API | docker, npm | sì | 1 |
| Pushbullet | `pushbullet` | servizio o API | hosts | no | 0 |
| Pusher | `pusher` | servizio o API | go, npm, pypi | sì | 1 |
| Pushover | `pushover` | servizio o API | hosts | no | 0 |
| Qase | `qase` | servizio o API | npm, pypi | sì | 0 |
| Qdrant | `qdrant` | database | composer, crates, docker, go, npm, pypi, terraform-resource, env | sì | 0 |
| Qlik | `qlik` | servizio o API | npm | sì | 0 |
| Qovery | `qovery` | servizio o API | docker, github-actions, go, npm, terraform | no | 0 |
| Qovery Cluster | `qovery.cluster` | servizio o API | terraform-resource | no | 0 |
| Qovery Database | `qovery.database` | database | terraform-resource | no | 0 |
| QuestDB | `questdb` | database | crates, docker, go, npm, pypi | no | 0 |
| RabbitMQ | `rabbitmq` | coda | composer, crates, docker, maven, npm, nuget, pypi, rubygems, env | sì | 4 |
| Railway | `railway` | servizio o API | github-actions, npm, pypi, terraform, files, env | sì | 1 |
| Rarible | `rarible` | servizio o API | npm | sì | 0 |
| Razorpay | `razorpay` | servizio o API | go, npm, pypi | sì | 0 |
| ReadMe | `readme` | servizio o API | npm, pypi | sì | 0 |
| Reddit | `reddit` | servizio o API | npm, env | sì | 0 |
| Redis | `redis` | database | composer, crates, docker, go, maven, npm, nuget, pypi, rubygems, terraform, terraform-resource, env | sì | 19 |
| RelativeCI | `relativeci` | servizio o API | github-actions, npm, files | no | 0 |
| remove.bg | `removebg` | servizio o API | npm | sì | 0 |
| Render | `render` | servizio o API | files | sì | 1 |
| Replicate | `replicate` | servizio o API | go, npm, pypi, env | sì | 0 |
| Replit | `replit` | servizio o API | npm, files | sì | 0 |
| Replit Database | `replit.database` | database | npm, pypi | no | 0 |
| Resend | `resend` | servizio o API | composer, crates, go, npm, pypi, rubygems, env | sì | 1 |
| RethinkDB | `rethinkdb` | database | composer, docker, go, npm, pypi, rubygems | no | 0 |
| RevenueCat | `revenuecat` | gateway | npm, env | sì | 0 |
| Roboflow | `roboflow` | servizio o API | pypi | sì | 0 |
| Rocket.Chat | `rocket-chat` | servizio o API | npm | sì | 0 |
| Rollbar | `rollbar` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform, env | sì | 1 |
| Salesforce | `salesforce` | servizio o API | npm, terraform, env | no | 0 |
| Sanity | `sanity` | servizio o API | npm | sì | 0 |
| SAP | `sap` | servizio o API | npm | sì | 0 |
| SAS | `sas` | servizio o API | pypi | no | 0 |
| Sauce Labs | `sauce-labs` | servizio o API | npm | sì | 0 |
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
| Schedules Direct | `schedules-direct` | servizio o API | hosts | no | 0 |
| Scout APM | `scoutapm` | servizio o API | composer, npm, rubygems | no | 0 |
| Segment | `segment` | servizio o API | composer, go, npm, pypi, rubygems, env | no | 0 |
| Selenium | `selenium` | servizio o API | composer, crates, docker, github-actions, go, npm, pypi, rubygems | sì | 0 |
| Sendgrid | `sendgrid` | servizio o API | composer, go, npm, pypi, rubygems | no | 0 |
| Sentry | `sentry` | servizio o API | composer, crates, docker, github-actions, go, hex, npm, pypi, rubygems, env | sì | 4 |
| ServiceNow | `servicenow` | servizio o API | rubygems | no | 0 |
| Shopify | `shopify` | servizio o API | composer, npm, pypi, rubygems | sì | 0 |
| Shortcut | `shortcut` | servizio o API | npm | sì | 0 |
| Sign in with Apple | `apple.signin` | autenticazione | npm | no | 0 |
| Signoz | `signoz` | servizio o API | docker, env | no | 0 |
| Simple Analytics | `simpleanalytics` | servizio o API | npm, env | sì | 0 |
| SimpleFIN Bridge | `simplefin` | servizio o API | hosts | no | 0 |
| SimpleSAMLphp | `simplesamlphp` | servizio o API | docker, env | no | 0 |
| Sitecore | `sitecore` | servizio o API | npm | sì | 0 |
| Sitecore XM cloud | `sitecore.xmlcloud` | servizio o API | npm | no | 0 |
| Slack | `slack` | servizio o API | composer, crates, docker, github-actions, go, npm, pypi, rubygems, terraform, env | no | 0 |
| SmartThings | `smartthings` | servizio o API | npm | sì | 0 |
| Snowflake | `snowflake` | database | crates, npm, pypi, rubygems, terraform, terraform-resource | sì | 0 |
| Snyk | `snyk` | servizio o API | docker, github-actions, npm, terraform, files, env | sì | 0 |
| Solana | `solana` | servizio o API | npm | sì | 0 |
| SonarCloud | `sonarcloud` | servizio o API | github-actions | no | 0 |
| SonarQube | `sonarqube` | servizio o API | docker, files | no | 0 |
| SparkPost | `sparkpost` | servizio o API | npm, pypi | sì | 0 |
| Split | `splitio` | servizio o API | go, npm, rubygems | no | 0 |
| Splunk | `splunk` | servizio o API | pypi, terraform, env | sì | 0 |
| Spotify | `spotify` | servizio o API | composer, npm, env | sì | 0 |
| SQLite | `sqlite` | database | composer, crates, deno, go, npm, nuget, rubygems, files | sì | 4 |
| Sqreen | `sqreen` | servizio o API | npm, rubygems, env | no | 0 |
| Square | `squareup` | gateway | composer, env | sì | 0 |
| Squarespace | `squarespace` | servizio o API | npm | sì | 0 |
| Storyblok | `storyblok` | servizio o API | composer, npm, pypi, rubygems | sì | 0 |
| Strapi | `strapi` | servizio o API | docker, npm, env | sì | 0 |
| Stripe | `stripe` | gateway | composer, go, npm, pypi, rubygems, env | sì | 3 |
| StyleCI | `styleci` | servizio o API | files | no | 0 |
| Stytch | `stytch` | autenticazione | crates, go, npm, pypi, rubygems | no | 0 |
| Supabase | `supabase` | servizio o API | docker, github-actions, npm, pypi, env | sì | 0 |
| Supabase Auth | `supabase.auth` | autenticazione | docker, npm | sì | 0 |
| Supabase Functions | `supabase.functions` | servizio o API | npm | sì | 0 |
| Supabase Postgres | `supabase.postgres` | database | composer, docker, github-actions, npm | sì | 0 |
| Supabase Realtime | `supabase.realtime` | coda | docker, npm | sì | 0 |
| Supabase Storage | `supabase.storage` | database | docker, npm | sì | 0 |
| SuperTokens | `supertokens` | autenticazione | go, npm, pypi | no | 0 |
| SurrealDB | `surrealdb` | database | crates, docker, npm, pypi | sì | 0 |
| Swiftype | `swiftype` | database | composer, npm, pypi, rubygems | no | 0 |
| Tailscale | `tailscale` | servizio o API | github-actions, npm, pypi | sì | 0 |
| TDengine | `tdengine` | database | crates, docker, go, npm | no | 0 |
| TeamCity | `teamcity` | servizio o API | files | sì | 0 |
| Teamspeak | `teamspeak` | servizio o API | docker | sì | 0 |
| Telegraf | `telegraf` | servizio o API | docker | no | 0 |
| Telegram | `telegram` | servizio o API | composer, crates, docker, github-actions, go, npm, rubygems, env, hosts | sì | 0 |
| Tencent Cloud | `tencentcloud` | servizio o API | composer, pypi, terraform | no | 0 |
| Tencent COS | `tencent-cos` | filesystem | go | no | 0 |
| Teradata | `teradata` | database | pypi | sì | 0 |
| The Space Devs API | `space-devs` | servizio o API | hosts | no | 0 |
| thirdweb | `thirdweb` | servizio o API | npm | sì | 0 |
| Ticketmaster | `ticketmaster` | servizio o API | hosts | no | 0 |
| TiDB | `tidb` | database | docker | sì | 0 |
| Tigris | `tigris` | filesystem | hosts | no | 0 |
| Tika | `apachetika` | servizio o API | docker, pypi | no | 1 |
| TimescaleDB | `timescaledb` | database | docker, terraform | no | 0 |
| Tinybird | `tinybird` | servizio o API | npm, env | no | 0 |
| TMDb | `tmdb` | servizio o API | nuget | no | 0 |
| Todoist | `todoist` | servizio o API | npm, pypi | sì | 0 |
| Traefik | `traefik` | servizio o API | docker, go, files | no | 1 |
| Tray.ai | `trayio` | servizio o API | npm | no | 0 |
| Trino | `trino` | database | pypi | sì | 0 |
| Truffle Security | `trufflesecurity` | servizio o API | docker, github-actions | no | 0 |
| Turso | `tursodb` | database | npm, env | sì | 0 |
| Twenty CRM | `twentycrm` | servizio o API | docker | sì | 0 |
| Twilio | `twilio` | servizio o API | composer, github-actions, go, npm, pypi, rubygems, terraform-resource, env, hosts | no | 0 |
| Twitch | `twitch` | servizio o API | npm, env | sì | 0 |
| Twitch OAuth | `twitch.oauth` | autenticazione | composer | no | 0 |
| Typesense | `typesense` | database | composer, crates, docker, go, npm, pypi, rubygems, terraform-resource | no | 0 |
| Unsplash | `unsplash` | servizio o API | npm | sì | 0 |
| Upstash | `upstash` | servizio o API | npm | sì | 1 |
| Upstash Kafka | `upstash.kafka` | coda | npm, env | no | 0 |
| Upstash QStash | `upstash.qstash` | coda | npm | no | 0 |
| Upstash Redis | `upstash.redis` | database | npm, pypi, env | no | 1 |
| Uptime Kuma | `uptimekuma` | servizio o API | docker | sì | 0 |
| Use Autumn | `useautumn` | gateway | npm, env | no | 0 |
| Valkey | `valkey` | database | docker, go, npm, pypi, env | no | 0 |
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
| Vertex AI | `gcp.vertex` | servizio o API | npm, pypi, env | sì | 1 |
| VictoriaMetrics | `victoriametrics` | database | docker | sì | 0 |
| Vimeo | `vimeo` | servizio o API | npm | sì | 0 |
| VirusTotal | `virustotal` | servizio o API | pypi | sì | 0 |
| Vonage | `vonage` | servizio o API | npm, pypi | sì | 0 |
| WakaTime | `wakatime` | servizio o API | pypi | sì | 0 |
| Weaviate | `weaviate` | database | go, pypi | no | 0 |
| Webex | `webex` | servizio o API | npm | sì | 0 |
| Webflow | `webflow` | servizio o API | npm, pypi, terraform-resource, env | sì | 0 |
| Weights & Biases | `wandb` | servizio o API | pypi | sì | 0 |
| what3words | `what3words` | servizio o API | npm, pypi | sì | 0 |
| WhatsApp | `whatsapp` | servizio o API | npm, env | sì | 0 |
| Where the ISS At API | `where-the-iss-at` | servizio o API | hosts | no | 0 |
| Wikipedia | `wikipedia` | servizio o API | npm, pypi, env | sì | 0 |
| Wiz | `wiz` | servizio o API | terraform, env | no | 0 |
| Wolfram Alpha | `wolframalpha` | servizio o API | pypi, env | no | 0 |
| WooCommerce | `woocommerce` | servizio o API | composer, terraform-resource, env | sì | 0 |
| Wordpress | `wordpress` | servizio o API | composer, docker, github-actions, npm, env | sì | 0 |
| WorkOS | `workos` | autenticazione | composer, go, npm, pypi, rubygems, env | no | 0 |
| X | `twitter` | servizio o API | npm, pypi, terraform-resource, env | sì | 0 |
| X AI | `xai` | servizio o API | npm, pypi, env | no | 0 |
| Xendit | `xendit` | servizio o API | npm | sì | 0 |
| Yandex Cloud | `yandex-cloud` | servizio o API | pypi | sì | 0 |
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

Oltre al riconoscimento: i componenti Vue e Svelte entrano nell'indice di scip-typescript (`indexers/components.py`) e il loro `<script>` nello snapshot (`languages/sfc.py`); il grafo dei fogli di stile (`indexers/css.py`) legge questi file con i parser fissati in `daodan/core/indexers/css_engines/package.json`: @astrojs/compiler 4.0.0, @vue/compiler-sfc 3.5.45, less 4.9.1, sass-parser 0.5.6, stylus 0.64.0, svelte 5.57.3, typescript 5.9.3. La sua misura è la riga `stylesheet` della sezione Analizzatori.

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
