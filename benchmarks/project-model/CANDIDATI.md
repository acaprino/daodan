# Candidati per il corpus `real`

Raccolti il 25 novembre 2026: repository pubblici che non sono già fra le 50 cartelle `real-*`, scelti sui linguaggi, i build tool e i framework di [`codebase-map-supporto.md`](../../docs/plugins/codebase-map-supporto.md).

- **Verificato:** esistenza, licenza e stelle, da `api.deps.dev/v3/projects` il 25 novembre 2026.
- **Non verificato:** la colonna «Che cosa prova» viene da ciò che si sa del progetto, non dai file a un commit. Si conferma quando si scrive `source.json`, con il commit.
- Nessuno è ancora un caso: manca `source.json` e `expected.json`.

## Selezione rivista sul `support`

Rivista il 25 novembre 2026 sul `support` di ogni voce del registro (`docs/specs/architettura.md`, «Nodi del grafo»): che cosa un progetto deve provare dipende dal livello della tecnologia che porta. I repository senza nota stanno nelle sezioni sotto; i 10 marcati «nuovo» sono Apache 2.0 o MIT, verificati su deps.dev lo stesso giorno.

### `full` con un lettore: si prova la lettura

Le 10 voci di `registry_build.READERS`. Sono i casi da scrivere per primi: qui Daodan promette rotte, eventi dei template o stili, e un caso misura se li dà.

| Voce | Candidati |
| --- | --- |
| Next.js | vercel/commerce, vercel/nextjs-subscription-payments, t3-oss/create-t3-turbo, boxyhq/saas-starter-kit, payloadcms/payload |
| Nuxt | nuxt/movies, atinux/atidone (nuovo) |
| React Router | remix-run/react-router (nuovo): i modelli e i progetti di prova in modalità framework |
| Remix | remix-run/indie-stack (nuovo), remix-run/blues-stack (nuovo) |
| SvelteKit | sveltejs/realworld, sveltejs/kit (nuovo) |
| Svelte | gradio-app/gradio, pocketbase/pocketbase |
| Angular | akveo/ngx-admin (nuovo), angular/components (nuovo, con Bazel), auth0-samples/auth0-angular-samples, ionic-team/ionic-framework |
| Astro | withastro/starlight, onwidget/astrowind (nuovo, con Tailwind) |
| Tailwind | shadcn-ui/ui (nuovo), onwidget/astrowind |
| Vue | vbenjs/vue-vben-admin, element-plus/element-plus, vuejs/pinia, vuejs/vitepress |

### `partial`: si prova il riconoscimento, la lettura è attesa come buco

Framework e librerie con una regola del fork e nessun lettore. Un caso misura che siano riconosciuti; le rotte restano un buco dichiarato finché il lettore non c'è. Prima i tre che il piano integra in T1.

| Voce | Candidati |
| --- | --- |
| Django | zulip/zulip, ArchiveBox/ArchiveBox |
| FastAPI | fastapi/fastapi (nuovo: gli esempi di `docs_src`), fastapi/sqlmodel, jlowin/fastmcp |
| Flask | miguelgrinberg/microblog, apache/superset |
| Express, Koa, Fastify, Hono, Elysia | expressjs/express, koajs/koa, fastify/demo, honojs/hono, elysiajs/elysia |
| Spring Boot, MVC, WebFlux | spring-guides/gs-rest-service, spring-petclinic/spring-petclinic-rest, appsmithorg/appsmith |
| Quarkus, Micronaut, Ktor | quarkusio/quarkus-quickstarts, micronaut-projects/micronaut-starter, ktorio/ktor-samples |
| ASP.NET Core, Blazor, .NET MAUI | kgrzybek/modular-monolith-with-ddd, MudBlazor/MudBlazor, dotnet/maui-samples |
| Gin, Echo, Fiber, Chi | labstack/echo, gofiber/recipes, go-gitea/gitea |
| Axum, Actix Web, Dioxus | tokio-rs/axum, actix/examples, DioxusLabs/dioxus |
| Electron, Tauri, Expo, React Native | electron/fiddle, tauri-apps/tauri, bluesky-social/social-app |
| ORM e code (librerie) | fastapi/sqlmodel, go-gorm/gorm, SeaQL/sea-orm, JetBrains/Exposed, MassTransit/MassTransit |

### `full` senza lettore: si prova solo che il servizio sia visto

Servizi e strumenti: un caso misura il nodo e le frecce, niente altro. Vanno bene i progetti più semplici delle sezioni «Servizi esterni e pipeline di rilascio» e «Scelti sulle tipologie del registro»: i quickstart di Firebase, gli esempi di Auth0 e di Stripe, `keycloak-quickstarts`, `rabbitmq-tutorials`, `nikoksr/notify`, `rclone/rclone`.

### `none`: misurano un buco, non sono casi di regressione

La tecnologia principale non ha una regola del fork, o nemmeno una voce nel registro: il caso fallisce finché la regola non c'è, e serve a dire quando arriva. temporalio/samples-python e gli altri `samples-*`, langfuse/langfuse, Unleash/unleash, zitadel/zitadel, goauthentik/authentik, plaid/quickstart, svix/svix-webhooks, triggerdotdev/trigger.dev, growthbook/growthbook.

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

## Servizi esterni e pipeline di rilascio, Apache 2.0 e MIT (46)

Aggiunti su richiesta del proprietario: progetti che chiamano servizi esterni o che rilasciano con una pipeline.

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| firebase/quickstart-js | Apache-2.0 | Firebase dal browser, un'unità per prodotto |
| firebase/quickstart-android | Apache-2.0 | Firebase su Android, Gradle a più moduli |
| firebase/quickstart-nodejs | Apache-2.0 | Firebase Admin SDK da Node |
| firebase/functions-samples | Apache-2.0 | Cloud Functions, molte unità npm indipendenti |
| firebase/friendlyeats-web | Apache-2.0 | Firestore e Auth da un'app web |
| firebase/firebase-tools | MIT | CLI TypeScript sulle API di Firebase e Google Cloud, rilascio su npm |
| GoogleCloudPlatform/microservices-demo | Apache-2.0 | servizi Go, C#, Java, Python e Node uniti da gRPC |
| GoogleCloudPlatform/bank-of-anthos | Apache-2.0 | Spring Boot e Python, JWT, due database |
| GoogleCloudPlatform/python-docs-samples | Apache-2.0 | client Google Cloud, centinaia di `requirements.txt` indipendenti |
| GoogleCloudPlatform/golang-samples | Apache-2.0 | client Google Cloud, moduli Go annidati |
| GoogleCloudPlatform/nodejs-docs-samples | Apache-2.0 | client Google Cloud, unità npm indipendenti |
| GoogleCloudPlatform/java-docs-samples | Apache-2.0 | client Google Cloud, unità Maven indipendenti |
| awsdocs/aws-doc-sdk-examples | Apache-2.0 | SDK di AWS in ogni linguaggio supportato |
| aws-samples/aws-cdk-examples | Apache-2.0 | CDK in TypeScript, Python, Java, Go e C# |
| awslabs/aws-lambda-web-adapter | Apache-2.0 | Rust per Lambda, esempi in più linguaggi |
| awspring/spring-cloud-aws | Apache-2.0 | Spring su S3, SQS, SNS e DynamoDB, Maven |
| sst/sst | MIT | infrastruttura AWS e Cloudflare da TypeScript, con una parte Go |
| pulumi/examples | Apache-2.0 | AWS, Azure e Google Cloud da TypeScript, Python, Go e C# |
| terraform-aws-modules/terraform-aws-vpc | Apache-2.0 | solo Terraform |
| keycloak/keycloak | Apache-2.0 | Maven grande con Quarkus, console React su pnpm |
| keycloak/keycloak-quickstarts | Apache-2.0 | client di Keycloak in Spring Boot, Jakarta EE e Node |
| auth0-samples/auth0-react-samples | MIT | Auth0 da React |
| auth0-samples/auth0-angular-samples | MIT | Auth0 da Angular |
| auth0-samples/auth0-express-api-samples | MIT | Auth0 su un'API Express |
| auth0-samples/auth0-golang-web-app | MIT | Auth0 da Go |
| auth0/nextjs-auth0 | MIT | SDK di Auth0 per Next.js, rilascio su npm |
| clerk/javascript | MIT | SDK di Clerk, workspace pnpm con Changesets |
| vercel/commerce | MIT | Next.js su Shopify, pensato per Vercel |
| vercel/examples | MIT | molte app indipendenti su Vercel, con servizi diversi |
| vercel/nextjs-subscription-payments | MIT | Next.js, Stripe e Supabase |
| boxyhq/saas-starter-kit | Apache-2.0 | Next.js, Prisma, SAML, Stripe, webhook |
| supabase/supabase | Apache-2.0 | Next.js in pnpm con Turborepo, molti servizi |
| Azure-Samples/azure-search-openai-demo | MIT | Python e React su Azure OpenAI e Azure AI Search |
| cloudflare/workers-sdk | Apache-2.0 | Wrangler, workspace pnpm, rilascio con Changesets |
| cloudflare/templates | MIT | molti Worker indipendenti: D1, R2, KV |
| netlify/next-runtime | MIT | adattatore di Next.js per Netlify |
| resend/react-email | MIT | React Email, workspace pnpm |

Pipeline di rilascio come oggetto del progetto:

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| goreleaser/goreleaser | MIT | Go, rilascia se stesso con GoReleaser |
| cli/cli | MIT | Go, rilascio a più piattaforme, chiama l'API di GitHub |
| charmbracelet/gum | MIT | Go piccolo con GoReleaser |
| semantic-release/semantic-release | MIT | rilascio su npm da CI |
| changesets/changesets | MIT | Changesets, Yarn workspaces |
| googleapis/release-please | Apache-2.0 | TypeScript, rilascio da pull request |
| jreleaser/jreleaser | Apache-2.0 | Java su Gradle a molti moduli |
| axodotdev/cargo-dist | Apache-2.0 | Rust, genera i workflow di rilascio |
| pypa/sampleproject | MIT | il progetto Python minimo, con pubblicazione su PyPI |

## Progetti semplici, Apache 2.0 e MIT (31)

Uno o pochi moduli, un build tool.

| Repository | Licenza | Che cosa prova |
| --- | --- | --- |
| fastapi/typer | MIT | Python, Click |
| fastapi/sqlmodel | MIT | Python, SQLModel su SQLAlchemy e Pydantic |
| psf/requests | Apache-2.0 | Python, `setup.py` |
| Textualize/rich | MIT | Python, Poetry |
| miguelgrinberg/microblog | MIT | app Flask piccola, SQLAlchemy, posta, ricerca, traduzione |
| expressjs/express | MIT | JavaScript senza tipi |
| koajs/koa | MIT | Koa |
| sindresorhus/got | MIT | TypeScript, solo ESM |
| vuejs/pinia | MIT | Pinia, workspace pnpm piccolo |
| vuejs/vitepress | MIT | VitePress, Vue |
| labstack/echo | MIT | Echo, un modulo Go |
| charmbracelet/bubbletea | MIT | Go, esempi in un modulo annidato |
| go-gorm/gorm | MIT | GORM |
| gofiber/recipes | MIT | molti moduli Go indipendenti, Fiber con servizi diversi |
| sharkdp/fd | Apache-2.0 | un crate Rust |
| ratatui/ratatui | MIT | Ratatui, workspace Cargo piccolo |
| clap-rs/clap | Apache-2.0 | clap, macro procedurali |
| google/gson | Apache-2.0 | Maven a pochi moduli |
| square/okhttp | Apache-2.0 | Gradle Kotlin, Kotlin Multiplatform |
| InsertKoinIO/koin | Apache-2.0 | Koin, Kotlin Multiplatform |
| JetBrains/Exposed | Apache-2.0 | Exposed, Gradle |
| spring-projects/spring-data-examples | Apache-2.0 | Spring Data JPA, MongoDB, Redis, Elasticsearch |
| spring-guides/gs-rest-service | Apache-2.0 | Spring Boot minimo, Maven e Gradle nella stessa radice |
| android/architecture-samples | Apache-2.0 | app Android a un modulo, Jetpack Compose |
| JamesNK/Newtonsoft.Json | MIT | una soluzione .NET a più target |
| DaveGamble/cJSON | MIT | C, CMake e Make nella stessa radice |
| zserge/jsmn | MIT | C, una sola intestazione, Make |
| yhirose/cpp-httplib | MIT | C++, una sola intestazione, CMake e Meson |
| jarro2783/cxxopts | MIT | C++, CMake e Bazel |
| jbeder/yaml-cpp | MIT | C++, CMake |
| google/benchmark | Apache-2.0 | C++, CMake e Bazel |

## Scelti sulle tipologie del registro, Apache 2.0 e MIT (42)

Scelti leggendo `daodan/data/service-registry.json`, per coprire le sue tipologie con servizi diversi.

| Tipologia | Repository | Licenza | Che cosa prova |
| --- | --- | --- | --- |
| database | mem0ai/mem0 | Apache-2.0 | database vettoriali: Qdrant, Chroma, Pinecone, Milvus, Weaviate |
| database | infiniflow/ragflow | Apache-2.0 | Python e React; Elasticsearch, MinIO, MySQL, Redis |
| database | deepset-ai/haystack | Apache-2.0 | Python, archivi di documenti e fornitori di modelli |
| database | dbt-labs/dbt-core | Apache-2.0 | Python e SQL, adattatori per data warehouse |
| database | neo4j-examples/movies-java-spring-data-neo4j | Apache-2.0 | Spring Boot minimo su Neo4j |
| coda | rabbitmq/rabbitmq-tutorials | Apache-2.0 | RabbitMQ da ogni linguaggio, unità indipendenti |
| coda | ThreeDotsLabs/watermill | MIT | Go: Kafka, NATS, RabbitMQ, Pub/Sub, SQS |
| coda | dapr/quickstarts | Apache-2.0 | code e archivi di stato da Go, C#, Java, Python e Node |
| coda | spring-cloud/spring-cloud-stream-samples | Apache-2.0 | Kafka e RabbitMQ da Spring, unità Maven indipendenti |
| coda | confluentinc/kafka-streams-examples | Apache-2.0 | Kafka Streams, Maven, con una parte Scala |
| coda | kafbat/kafka-ui | Apache-2.0 | Spring WebFlux e React su Kafka |
| coda | MassTransit/MassTransit | Apache-2.0 | C#: RabbitMQ, Azure Service Bus, SQS, Kafka |
| coda | dotnetcore/CAP | MIT | C#: un pacchetto per ogni coda e database |
| coda | triggerdotdev/trigger.dev | Apache-2.0 | job in background, workspace pnpm |
| gateway | killbill/killbill | Apache-2.0 | Maven a molti moduli, pagamenti |
| gateway | plaid/quickstart | MIT | Plaid da Node, Python, Go e Java, con un front end React |
| gateway | plaid/pattern | MIT | app Node e React su Plaid |
| gateway | stripe/stripe-cli | Apache-2.0 | Go su Stripe, rilascio con GoReleaser |
| gateway | stripe-samples/checkout-one-time-payments | MIT | Stripe Checkout, un server per linguaggio |
| gateway | stripe-samples/subscription-use-cases | MIT | abbonamenti Stripe, un server per linguaggio |
| gateway | svix/svix-webhooks | MIT | server Rust, client in ogni linguaggio |
| autenticazione | ory/kratos | Apache-2.0 | Go, provider OIDC |
| autenticazione | dexidp/dex | Apache-2.0 | Go: LDAP, GitHub, GitLab, Google, Microsoft |
| autenticazione | oauth2-proxy/oauth2-proxy | MIT | Go: un provider OAuth per file |
| autenticazione | better-auth/better-auth | MIT | TypeScript, workspace pnpm, provider sociali |
| filesystem | rclone/rclone | MIT | Go: S3, Azure Blob, OSS, COS, OBS, Swift, Dropbox, Drive |
| filesystem | juicedata/juicefs | Apache-2.0 | Go: object storage e database di metadati |
| filesystem | apache/opendal | Apache-2.0 | Rust con binding per Python, Node, Java, Go e C |
| filesystem | thanos-io/thanos | Apache-2.0 | Go, object storage di più fornitori |
| servizio o API | nikoksr/notify | MIT | Go piccolo: decine di servizi di notifica |
| servizio o API | danny-avila/LibreChat | MIT | Node e React; MongoDB, Meilisearch, fornitori di modelli, OAuth |
| servizio o API | simonw/llm | Apache-2.0 | Python piccolo, fornitori di modelli come plugin |
| servizio o API | sanity-io/sanity | MIT | TypeScript, workspace pnpm, Sanity |
| servizio o API | discordjs/discord.js | Apache-2.0 | Discord, workspace pnpm |
| servizio o API | slackapi/bolt-js | MIT | Slack da Node |
| servizio o API | slackapi/bolt-python | MIT | Slack da Python, adattatori per Flask, Django, FastAPI e Lambda |
| servizio o API | temporalio/samples-python | MIT | Temporal, unità indipendenti |
| servizio o API | spotDL/spotify-downloader | MIT | Python su Spotify e YouTube |
| servizio o API | open-telemetry/opentelemetry-collector-contrib | Apache-2.0 | centinaia di moduli Go annidati, un esportatore per servizio |
| servizio o API | fluent/fluent-bit | Apache-2.0 | C su CMake, un plugin di uscita per servizio |
| servizio o API | influxdata/telegraf | MIT | Go, un plugin per servizio |
| servizio o API | terraform-google-modules/terraform-google-kubernetes-engine | Apache-2.0 | Terraform su Google Cloud |

## Altre licenze con sorgente disponibile (63)

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
| aws-samples/aws-serverless-airline-booking | non standard (MIT-0) | Lambda, AppSync, Cognito e Stripe; Vue e Python |
| aws-powertools/powertools-lambda-python | non standard (MIT-0) | Python per Lambda, rilascio su PyPI da CI |
| serverless/examples | non standard | funzioni su AWS, Azure e Google Cloud, unità indipendenti |
| localstack/localstack | non standard (Apache-2.0) | Python, emula i servizi AWS |
| novuhq/novu | non standard (MIT, con parti commerciali) | NestJS e React, decine di fornitori di notifiche |
| nextauthjs/next-auth | non standard (ISC) | decine di provider di identità, workspace pnpm |
| PostHog/posthog | non standard (MIT, con parti commerciali) | Django e React; ClickHouse, Kafka, Redis; parti Rust e Go |
| langgenius/dify | non standard (Dify Open Source License) | Flask e Next.js, database vettoriali e fornitori di modelli |
| medusajs/medusa | non standard (MIT) | commercio in Yarn workspaces, moduli di pagamento |
| saleor/saleor | BSD-3-Clause | Django e GraphQL, pagamenti |
| supertokens/supertokens-core | non standard (Apache-2.0) | Java su Gradle |
| logto-io/logto | non standard (MPL-2.0) | workspace pnpm, un connettore per provider |
| goauthentik/authentik | non standard (MIT, con parti commerciali) | Django, Go e TypeScript in un repository |
| zitadel/zitadel | AGPL-3.0 | Go e Angular |
| caronc/apprise | non standard (BSD-2-Clause) | Python: un file per servizio di notifica |
| activepieces/activepieces | non standard (MIT, con parti commerciali) | Nx, centinaia di pacchetti, uno per servizio |
| BerriAI/litellm | non standard (MIT, con parti commerciali) | Python, ogni fornitore di modelli |
| vercel/ai | non standard (Apache-2.0) | workspace pnpm, un pacchetto per fornitore |
| vectordotdev/vector | non standard (MPL-2.0) | Rust, una destinazione per servizio |
| anymail/django-anymail | BSD-3-Clause | Django, ogni fornitore di posta |
| knadh/listmonk | AGPL-3.0 | Go e Vue; SMTP e S3 |
| temporalio/samples-go | non standard (MIT) | Temporal da Go |
| temporalio/samples-typescript | non standard (MIT) | Temporal, molte unità npm |
| temporalio/samples-java | non standard (MIT) | Temporal da Java, Gradle |
| Unleash/unleash | AGPL-3.0 | Node e React, feature flag |
| langfuse/langfuse | non standard (MIT, con parti commerciali) | Next.js; ClickHouse, Redis, S3 |
| growthbook/growthbook | non standard (MIT, con parti commerciali) | Node, Next.js e Python |
| eclipse-mosquitto/mosquitto | non standard (EPL-2.0 o EDL-1.0) | C su CMake e Make, MQTT |
| Infisical/infisical | non standard (MIT, con parti commerciali) | Node e React, integrazioni con i cloud |

## Buchi del registro trovati

Cercando nel registro i servizi che questi progetti usano, per nome e per ID, sul registro di `develop` del 25 novembre 2026 (`stack-analyser` 1.27.6-daodan.5). Le regole di riconoscimento sono del fork: un buco si chiude con una regola lì, non in `daodan/data/`.

- **Senza voce:** Plaid, Mollie, Svix, Ably, Mux, imgix, UploadThing, Trigger.dev, GrowthBook, Doppler, Descope, Auth.js (NextAuth), Lucia, LangSmith, LiteLLM, Azure Service Bus, MQTT e Mosquitto, ZeroMQ, ActiveMQ fuori da AWS, SeaweedFS, Mastodon, OpenStreetMap, OpenWeather, Medusa, Saleor, Kill Bill, MassTransit, rclone, Apprise, listmonk, Activepieces.
- **`support: none`**, cioè una voce senza regola del fork: Temporal, Langfuse, Unleash, Hasura, Zitadel, authentik, Authelia, Casdoor, Dex, Dify, Redpanda, EMQX, Grafana Loki, Ceph, Azure Event Hubs, Vector, Argo.

## Scartati

Non trovati su deps.dev, quindi senza licenza verificata: litestar-org/litestar-fullstack, trungvose/jira-clone-angular, joreilly/Confetti, dani-garcia/vaultwarden, oracle-samples/db-sample-schemas. aws-samples/retail-store-sample-app, aws-samples/aws-serverless-shopping-cart, ivangfr/springboot-react-keycloak, auth0-samples/auth0-python-web-app, auth0-samples/auth0-aspnetcore-mvc-samples, auth0-samples/auth0-vue-samples, auth0-samples/auth0-spring-security5-api-sample, stripe-samples/accept-a-payment, ixartz/SaaS-Boilerplate, vercel/ai-chatbot, vercel/next-forge, vercel/platforms, Azure-Samples/todo-nodejs-mongo, twilio-labs/function-templates, Shopify/hydrogen, contentful/the-example-app.nodejs. Senza licenza dichiarata: nrwl/nx-examples.
