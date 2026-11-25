# Candidati per il corpus `real`

Raccolti il 25 novembre 2026: repository pubblici che non sono già fra le 50 cartelle `real-*`, scelti sui linguaggi, i build tool e i framework di [`codebase-map-supporto.md`](../../docs/plugins/codebase-map-supporto.md).

- **Verificato:** esistenza, licenza e stelle, da `api.deps.dev/v3/projects` il 25 novembre 2026.
- **Non verificato:** la colonna «Che cosa prova» viene da ciò che si sa del progetto, non dai file a un commit. Si conferma quando si scrive `source.json`, con il commit.
- Nessuno è ancora un caso: manca `source.json` e `expected.json`.

## Apache 2.0 e MIT (85)

### Python

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| zulip/zulip | Apache-2.0 | Django con front end TypeScript, pnpm, Puppet e SQL nello stesso albero |
| apache/superset | Apache-2.0 | Flask e SQLAlchemy, front end React in workspace npm, Celery |
| streamlit/streamlit | Apache-2.0 | Python e front end Yarn workspaces, Protocol Buffers generati |
| gradio-app/gradio | Apache-2.0 | Python e Svelte in workspace pnpm: Svelte su un progetto pubblico |
| reflex-dev/reflex | Apache-2.0 | Python che genera un'app React |
| jlowin/fastmcp | Apache-2.0 | FastMCP, uv, Pydantic |
| modelcontextprotocol/python-sdk | MIT | workspace uv, esempi come membri |
| strawberry-graphql/strawberry | MIT | Strawberry GraphQL, integrazioni con Django, FastAPI e Flask come extra |
| langchain-ai/langchain | MIT | molti pacchetti Python affiancati senza un workspace |
| mitmproxy/mitmproxy | MIT | Python e interfaccia React nello stesso repository |
| ArchiveBox/ArchiveBox | MIT | Django, dipendenze Node accanto a quelle Python |
| astral-sh/ruff | MIT | workspace Cargo, pacchetto Python con maturin, playground TypeScript |

### JavaScript, TypeScript, Vue, Svelte, Astro

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| vbenjs/vue-vben-admin | MIT | Vue 3 in monorepo pnpm con Turborepo: Vue su un progetto pubblico |
| element-plus/element-plus | MIT | libreria di componenti Vue, workspace pnpm |
| nuxt/movies | MIT | app Nuxt |
| sveltejs/realworld | MIT | app SvelteKit, `tsconfig` che estende il file di `svelte-kit sync` |
| withastro/starlight | MIT | Astro in workspace pnpm |
| solidjs/solid-start | MIT | Solid |
| QwikDev/qwik | MIT | Qwik, pnpm e un crate Rust nello stesso repository |
| honojs/hono | MIT | Hono, Bun |
| elysiajs/elysia | MIT | Elysia, test con `bun test` (`runner_not_observed`) |
| fastify/demo | MIT | app Fastify di riferimento |
| denoland/fresh | MIT | Deno, nessun `package.json` |
| denoland/std | MIT | workspace Deno |
| TryGhost/Ghost | MIT | Express e Ember, Yarn workspaces con Nx |
| excalidraw/excalidraw | MIT | React e Vite, Yarn workspaces |
| t3-oss/create-t3-turbo | MIT | Next.js, Expo e tRPC, pnpm con Turborepo |
| payloadcms/payload | MIT | Next.js, molti pacchetti pnpm, adattatori per database |
| facebook/docusaurus | MIT | Docusaurus, Yarn workspaces con Lerna |
| lerna/lerna | MIT | Lerna sopra Nx |
| ionic-team/ionic-framework | MIT | Stencil, con i pacchetti Angular, React e Vue |
| electron/fiddle | MIT | Electron con React |
| bluesky-social/social-app | MIT | Expo e React Native, con un modulo Go |
| wekan/wekan | MIT | Meteor |
| tauri-apps/tauri | Apache-2.0 | workspace Cargo e workspace pnpm affiancati, Tauri |
| spacedriveapp/spacedrive | Apache-2.0 | Tauri, Rust e React, più app in un monorepo |

### Java e Kotlin

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| appsmithorg/appsmith | Apache-2.0 | Spring WebFlux su Maven, client React su Yarn |
| kestra-io/kestra | Apache-2.0 | Micronaut su Gradle, interfaccia Vue |
| conductor-oss/conductor | Apache-2.0 | Spring Boot su Gradle a più moduli, interfaccia React |
| jenkinsci/jenkins | MIT | Maven a più moduli, front end Yarn, viste di template |
| apolloconfig/apollo | Apache-2.0 | Spring Boot su Maven, AngularJS |
| mybatis/jpetstore-6 | Apache-2.0 | MyBatis, Maven, JSP |
| spring-petclinic/spring-petclinic-rest | Apache-2.0 | Spring MVC, tre implementazioni dei repository scelte da un profilo |
| DependencyTrack/dependency-track | Apache-2.0 | Maven, Java |
| quarkusio/quarkus-quickstarts | Apache-2.0 | molte unità Maven indipendenti, Quarkus REST, Panache, Reactive Messaging |
| micronaut-projects/micronaut-starter | Apache-2.0 | Micronaut e picocli su Gradle |
| ktorio/ktor-samples | Apache-2.0 | molte build Gradle Kotlin indipendenti, Ktor |
| langchain4j/langchain4j-examples | Apache-2.0 | LangChain4j con Spring Boot e Quarkus, Maven |
| android/nowinandroid | Apache-2.0 | Android, Jetpack Compose, catalogo delle versioni, plugin di convenzione in `build-logic` |
| thunderbird/thunderbird-android | Apache-2.0 | Android a molti moduli, Kotlin e Java insieme |
| bazelbuild/examples | Apache-2.0 | Bazel su più linguaggi |

### C#

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| kgrzybek/modular-monolith-with-ddd | MIT | ASP.NET Core, moduli come progetti, SQL |
| simplcommerce/SimplCommerce | Apache-2.0 | ASP.NET Core a moduli, Entity Framework Core, viste Razor |
| umbraco/Umbraco-CMS | MIT | .NET e un backoffice TypeScript con Lit |
| MudBlazor/MudBlazor | MIT | Blazor |
| FastEndpoints/FastEndpoints | MIT | FastEndpoints |
| dotnet/aspire-samples | MIT | host Aspire: `tests_need_container_engine` |
| dotnet/maui-samples | MIT | .NET MAUI, SDK di piattaforma |
| microsoft/terminal | MIT | C++ e C# su MSBuild: nessun database di compilazione |

### Go

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| go-gitea/gitea | MIT | Go e front end Vue e TypeScript, Makefile, template |
| pocketbase/pocketbase | MIT | Go con interfaccia Svelte |
| prometheus/prometheus | Apache-2.0 | moduli Go annidati, interfaccia React in workspace npm |
| traefik/traefik | MIT | Go con un'interfaccia web separata |
| woodpecker-ci/woodpecker | Apache-2.0 | Go e Vue su pnpm |
| casdoor/casdoor | Apache-2.0 | Go e React su Yarn, Casbin |
| evcc-io/evcc | MIT | Go e Vue |
| ollama/ollama | MIT | cgo su C++ portato nel repository, CMake |
| jesseduffield/lazygit | MIT | cartella `vendor` da escludere |
| ent/ent | Apache-2.0 | ent, moduli annidati, codice generato |
| connectrpc/examples-go | Apache-2.0 | Connect, `buf.yaml`, Protocol Buffers |

### Rust

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| tokio-rs/axum | MIT | workspace Cargo, esempi come membri |
| actix/examples | Apache-2.0 | molti crate Actix Web, Diesel, SQLx |
| sharkdp/bat | Apache-2.0 | build script, dipendenze C compilate |
| DioxusLabs/dioxus | Apache-2.0 | Dioxus, workspace grande |
| SeaQL/sea-orm | Apache-2.0 | SeaORM, esempi con workspace propri |
| tree-sitter/tree-sitter | MIT | Rust e C con Cargo, Make, CMake, `Package.swift`, `build.zig.zon` e `go.mod` nella stessa radice |

### C e C++

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| libuv/libuv | MIT | CMake e Autotools nella stessa radice, C |
| nlohmann/json | MIT | CMake, Meson e Bazel nella stessa radice, solo intestazioni |
| ocornut/imgui | MIT | nessun file di build alla radice; esempi con Makefile e MSBuild |
| swaywm/sway | MIT | Meson, C |
| conan-io/examples2 | MIT | Conan 2 |
| ggml-org/llama.cpp | MIT | CMake, C++ |
| duckdb/duckdb | MIT | CMake, C++ grande, estensioni |
| godotengine/godot | MIT | SCons: un build system senza modello |

### SQL e PL/SQL

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| utPLSQL/utPLSQL | Apache-2.0 | PL/SQL: `.pks`, `.pkb`, `.sql` |

## Altre licenze con sorgente disponibile (34)

«non standard»: deps.dev non dà un identificativo; la licenza fra parentesi è quella che il progetto è noto per usare, da leggere nel suo file `LICENSE` prima di usarlo.

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| scrapy/scrapy | BSD-3-Clause | Scrapy |
| getredash/redash | non standard (BSD-2-Clause) | Flask, React, Poetry |
| open-webui/open-webui | non standard (Open WebUI License) | FastAPI e SvelteKit |
| immich-app/immich | AGPL-3.0 | NestJS, SvelteKit, Flutter e Python in un repository |
| n8n-io/n8n | non standard (Sustainable Use License) | Vue ed Express, workspace pnpm grande |
| directus/directus | non standard (BUSL-1.1) | Vue e Node su pnpm |
| twentyhq/twenty | non standard (AGPL-3.0 con parti commerciali) | NestJS e React, Nx su Yarn Berry |
| outline/outline | non standard (BUSL-1.1) | Koa, React, Sequelize |
| ionic-team/ionic-conference-app | non standard (Apache-2.0) | Angular, Ionic, Capacitor |
| gothinkster/angular-realworld-example-app | non standard (MIT) | app Angular |
| bitwarden/clients | non standard (GPL-3.0 e Bitwarden License) | Angular, Electron, più app in un workspace npm |
| tw93/Pake | GPL-3.0 | Tauri, CLI TypeScript e crate Rust |
| halo-dev/halo | GPL-3.0 | Spring WebFlux su Gradle, console Vue su pnpm |
| thingsboard/thingsboard | non standard (Apache-2.0) | Maven a molti moduli, interfaccia Angular |
| bitwarden/server | non standard (AGPL-3.0 e Bitwarden License) | ASP.NET Core, più servizi, SQL |
| OrchardCMS/OrchardCore | BSD-3-Clause | ASP.NET Core a moduli, Razor e Liquid |
| Radarr/Radarr | GPL-3.0 | .NET e React su Yarn |
| navidrome/navidrome | GPL-3.0 | Go con cgo, interfaccia React |
| BurntSushi/ripgrep | non standard (MIT o Unlicense) | workspace Cargo |
| meilisearch/meilisearch | non standard (MIT, con parti BUSL-1.1) | workspace Cargo |
| LemmyNet/lemmy | AGPL-3.0 | Actix Web, Diesel |
| rustdesk/rustdesk | AGPL-3.0 | Rust, Flutter con flutter_rust_bridge, vcpkg |
| getzola/zola | non standard (EUPL-1.2) | workspace Cargo, Sass |
| valkey-io/valkey | BSD-3-Clause | Make e CMake, C |
| jqlang/jq | non standard (MIT) | Autotools, un submodule |
| tmux/tmux | non standard (ISC) | Autotools, C |
| google/googletest | BSD-3-Clause | CMake e Bazel |
| catchorg/Catch2 | non standard (BSL-1.0) | CMake, Meson e Bazel |
| harfbuzz/harfbuzz | non standard (MIT «Old Style») | Meson e CMake, C++ |
| gabime/spdlog | non standard (MIT) | CMake, C++ |
| neovim/neovim | non standard (Apache-2.0 e licenza di Vim) | CMake che scarica le dipendenze da siti fuori dai registri |
| postgres/postgres | non standard (PostgreSQL License) | Autotools e Meson nella stessa radice, C, SQL |
| raspberrypi/pico-examples | BSD-3-Clause | CMake con arm-none-eabi |
| betaflight/betaflight | GPL-3.0 | Make con arm-none-eabi |

## Scartati

Non trovati su deps.dev, quindi senza licenza verificata: litestar-org/litestar-fullstack, trungvose/jira-clone-angular, joreilly/Confetti, dani-garcia/vaultwarden, oracle-samples/db-sample-schemas. Senza licenza dichiarata: nrwl/nx-examples.
