# Strumenti di build: il fork contro le sorgenti della pre-mappa (T1.B.1)

Domanda: quali strumenti di build trovati dalle sorgenti di `find_modules` il fork `stack-analyser` non nomina, e quante
tecnologie perde lo stack quando gira senza le dichiarazioni della pre-mappa (come girerà `recognize_stack` prima di
`find_modules`, decisione 2 di `T1.B`). Le risposte sono l'elenco delle regole del rilascio `.6` del fork (`T1.B.4`).
Nessun LLM, nessun cambio al prodotto.

## Parametri

- **Riconoscitore:** il fork stesso, l'unico (spec, «Chi riconosce è uno solo»), con la release fissata in
  `daodan/core/stack_analyser.py` (`1.27.6-daodan.5`), sul Node e sulla release dell'immagine di `modal_stack.py`. Syft è
  escluso dal piano (già misurato, `benchmarks/project-model/REPORT.md`).
- **Corpus:** le fixture con `expected.json` di `benchmarks/project-model/fixtures/` (le reali dal loro archivio sul volume).
- **Pre-mappa:** quella registrata: la camminata e i lettori di oggi, con le risposte dei comandi di modello registrate in
  `benchmarks/project-model/results/premap-runs` (rigiocate, nessun comando del progetto gira; una fixture senza
  registrazione ha i comandi `not_run`). `results/daodan_premap_corpus.json`, che il piano nomina, non tiene le faccette
  `packages`, `services` e `docker_builds` che `stack_recognition.declarations` legge: si rigioca la registrazione, come
  `modal_stack.py`.
- **Due varianti sullo stesso snapshot e perimetro:** `with` = `stack_recognition.run` con i fatti della pre-mappa;
  `without` = gli stessi fatti senza `packages`, `services`, `docker_builds` (nessuna dichiarazione al fork).
- **Tabella del passo** (`modal_build_tools.TOOLS`): strumento di `find_modules` → voci del registro che il fork nomina,
  tipi di unità (`units[].kind`) e strumenti di workspace (`workspace[].tool`) della pre-mappa, sorgenti che lo provano
  (solo `tsc`, che non dà unità). CMake, Meson, Bazel, Make, autotools, sbt, .NET SDK e Mix non hanno voce nel registro;
  Nx sì (`nxjs`). «Nominato» = una voce con un segno del fork (o di una dichiarazione), non solo una menzione di host.
- **Calcolo:** `rows`, `lost`, `summary` di `modal_build_tools.py`, provati su righe scritte a mano in `test_build_tools.py`.

Corsa: `modal deploy benchmarks/stack-build-tools/modal_build_tools.py`, poi
`python benchmarks/stack-build-tools/modal_build_tools.py spawn` e `fetch` (scrive `results/build_tools.json`); test della
logica pura: `modal run tests/modal_pytest.py --args "benchmarks/stack-build-tools/test_build_tools.py -q"`.

## Risultati (27 novembre 2026)

Corsa sul codice di `1f2b024` (hash del codice `d1ce8a9526f25bd4`, deploy `daodan-stack-build-tools`): 184 fixture su 186,
2 senza risposta in 1800 s (`real-stack-jellyfin`, `real-stack-kuvasz`, come in `modal_stack.py`); pre-mappa `partial` in 178
(la registrazione non ha i comandi delle sorgenti nate dopo), `none` in 6; 156 fixture con almeno una dichiarazione; processi
avviati solo git e il fork su Node (`executed_project_code: no`). Dettaglio per fixture in `results/build_tools.json`.

### Strumenti di build (fixture)

| Strumento | Trovato dalle sorgenti | Nominato dal fork (senza dichiarazioni) | Entrambi | Solo le sorgenti | Solo il fork | Che cosa nomina il fork dove manca |
| --- | --- | --- | --- | --- | --- | --- |
| cargo | 17 | 17 | 17 | 0 | 0 | — |
| gradle | 26 | 26 | 26 | 0 | 0 | — |
| maven | 24 | 24 | 24 | 0 | 0 | — |
| npm (`npm`, `pnpm`, `yarn`) | 65 | 3 | 3 | **62** | 0 | `nodejs` in 62 su 62 |
| tsc (`typescript`) | 35 | 39 | 35 | 0 | 4 | — |
| python (`uv`, `pip`, `poetry`) | 39 | 1 | 1 | **38** | 0 | `python` 15, `hatchling` 13, `setuptools` 10; nessuna voce Python in 8 |
| go (`golang`) | 20 | 21 | 20 | 0 | 1 | — |
| cmake | 10 | — | 0 | **10** | 0 | nessuna voce |
| dotnet | 9 | — | 0 | **9** | 0 | `nuget` in 9 su 9 |
| mix | 4 | — | 0 | **4** | 0 | `elixir` in 4 su 4 |
| autotools | 1 | — | 0 | **1** | 0 | nessuna voce |
| sbt | 1 | — | 0 | **1** | 0 | nessuna voce |
| nx (`nxjs`) | 1 | 1 | 1 | 0 | 0 | — |
| meson, bazel, make | 0 | — | 0 | 0 | 0 | non misurati: la registrazione non ha i loro comandi (`sys-meson`, `sys-bazel`, `sys-make-plain` senza unità) |

Scoperti dal fork: CMake, autotools e sbt (nessuna voce); .NET SDK e Mix hanno una voce vicina (`nuget`, `elixir`) in ogni
fixture. npm e Python non sono scoperti ma nominati con un'altra voce: il fork dà `nodejs` e non `npm` (che nomina solo con
`package-lock.json`: 3 su 65), e per Python `python`, `hatchling`, `setuptools`; 8 fixture Python non hanno nessuna voce
Python senza dichiarazioni (`mix-poly-firebase`, `py-conda-env`, `py-pdm`, `py-poetry-groups`, `py-setup-py-dynamic`,
`py-setup-py-static`, `real-stack-atuin`, `real-stack-paperless-ngx`). Con le chiavi di oggi `build-tools.json` (`T1.B.3`)
non lega `nodejs` né `python` ad alcuna sorgente: per `T1.B.7` va scelto se legarle o aggiungere la regola al `.6`.

### Tecnologie perse senza dichiarazioni

**88 voci in 39 fixture** (framework 7, librerie 27, servizi 29, strumenti 25): 57 provate da un manifesto, 31 solo da un
workflow di CI (`.github/`). Le più frequenti: `pnpm` 7 e `github.pages` 7 (workflow), `ruff` 5, `click` 4, `python` 3,
`gcp` 3, `protobuf` 3. Sono le regole che il `.6` deve aggiungere (`T1.B.4`), ognuna con il file che la prova:

Le 31 dei workflow erano perse perché il perimetro non entrava in `.github/`. Ora entra nelle cartelle punto i cui file il
fork legge (`read_dot_directories` di `file-formats.json`: `.github`, `.maestro`), e l'espressione `(^|/)\.github/` del
`vendor.yml` di Linguist non le esclude più; da rimisurare al giro corpus. `Dockerfile.gotenberg` resta fuori: Linguist
conosce per nome solo `Dockerfile` e `Containerfile` (`linguist-catalog.json`).

| Fixture | Voce (file) |
| --- | --- |
| `jvm-gradle-computed-deps` | `jackson` (`build.gradle`, `gradle.properties`) |
| `jvm-sbt-two-subprojects` | `cats` (`build.sbt`), `scalatest` (`build.sbt`) |
| `mix-infra-gha` | `pnpm` (`.github/workflows/ci.yml`), `python` (`.github/workflows/release.yml`) |
| `mix-real-klaxon` | `testng` (`build.gradle.kts`, `klaxon/build.gradle.kts`) |
| `mix-real-tududi` | `dompurify` (`package.json`), `honojs` (`package.json`), `zod` (`package.json`) |
| `py-hatch-envs` | `pytest` (`pyproject.toml`), `ruff` (`pyproject.toml`) |
| `py-pdm` | `ruff` (`pyproject.toml`) |
| `py-pip-tools` | `ruff` (`dev-requirements.in`, `dev-requirements.txt`) |
| `py-pipenv` | `click` (`Pipfile`), `ruff` (`Pipfile`) |
| `py-requirements-includes` | `click` (`requirements/base.txt`), `numpy` (`requirements/base.txt`), `pytest` (`requirements-dev.txt`), `requests` (`requirements/base.txt`) |
| `py-setup-cfg-extras` | `click` (`setup.cfg`), `sphinx` (`setup.cfg`) |
| `py-setup-py-static` | `pyyaml` (`setup.py`), `requests` (`setup.py`) |
| `real-app-full-stack-fastapi` | `bunsh` (`.github/workflows/deploy.yml`, `.github/workflows/playwright.yml`, …) |
| `real-app-hoppscotch` | `pnpm` (`.github/workflows/build-hoppscotch-agent.yml`, `.github/workflows/build-hoppscotch-desktop.yml`, …) |
| `real-app-jhipster-sample` | `h2` (`pom.xml`), `postgresql` (`pom.xml`) |
| `real-app-kotlinconf` | `github.pages` (`.github/workflows/web-deploy.yml`) |
| `real-app-memos` | `codecov` (`.github/workflows/backend-tests.yml`), `gcp` (`go.mod`), `gcp.gce` (`go.mod`), `opentelemetry` (`go.mod`), `pnpm` (`.github/actions/setup-web/action.yml`) |
| `real-stack-ardalis-cleanarchitecture` | `github.pages` (`.github/workflows/hugo-docs.yml`), `hugo` (`.github/workflows/docs-build.yml`), `nodejs` (`.github/workflows/repro-bug.yml`) |
| `real-stack-astro-paper` | `pnpm` (`.github/workflows/ci.yml`) |
| `real-stack-bakerydemo` | `boto3` (`requirements/production.txt`), `django` (`requirements/base.txt`), `elasticsearch` (`requirements/production.txt`), `gcp` (`requirements/production.txt`), `gcp.gcs` (`requirements/production.txt`), `ruff` (`requirements/development.txt`), `wagtail` (`requirements/base.txt`) |
| `real-stack-documenso` | `gotenberg` (`docker/development/Dockerfile.gotenberg`) |
| `real-stack-docuseal` | `redis` (`Dockerfile`) |
| `real-stack-fiber-go-template` | `openapi` (`go.mod`) |
| `real-stack-gin-vue-admin` | `jsonschema` (`server/go.mod`), `openapi` (`server/go.mod`), `protobuf` (`server/go.mod`) |
| `real-stack-hexpm` | `gcp` (`.github/workflows/main.yml`) |
| `real-stack-koel` | `pnpm` (`.github/workflows/lint-frontend.yml`, `.github/workflows/release.yml`, …) |
| `real-stack-lldap` | `codecov` (`.github/workflows/rust.yml`) |
| `real-stack-localsend` | `azure` (`.github/workflows/build_windows_cli_exe.yml`, `.github/workflows/build_windows_exe.yml`, …) |
| `real-stack-mealie` | `click` (`pyproject.toml`), `depotdev` (`.github/workflows/publish.yml`), `discord` (`.github/workflows/nightly.yml`, `.github/workflows/release.yml`), `github.pages` (`.github/workflows/docs.yml`), `numpy` (`pyproject.toml`) |
| `real-stack-opengist` | `chi` (`go.mod`), `golangcilint` (`.github/workflows/go.yml`), `protobuf` (`go.mod`) |
| `real-stack-owncast` | `cobra` (`tools/go.mod`), `grpc` (`tools/go.mod`), `mysql` (`tools/go.mod`), `postgresql` (`tools/go.mod`), `protobuf` (`go.mod`, `tools/go.mod`), `urfave-cli` (`tools/go.mod`), `viper` (`tools/go.mod`) |
| `real-stack-paperless-ngx` | `github.pages` (`.github/workflows/ci-docs.yml`), `pnpm` (`.github/workflows/ci-frontend.yml`, `.github/workflows/ci-release.yml`, …), `python` (`.github/workflows/ci-backend.yml`, `.github/workflows/ci-docs.yml`, …) |
| `real-stack-peopleinspace` | `github.pages` (`.github/workflows/build-and-publish-web.yml`), `kotlin-test` (`build.gradle.kts`, `gradle/libs.versions.toml`) |
| `real-stack-plausible` | `github.pages` (`.github/workflows/publish-docs.yml`) |
| `real-stack-quarkus-super-heroes` | `azure` (`.github/workflows/azure-static-web-apps-orange-rock-0d20a680f.yml`), `azure.staticwebapps` (`.github/workflows/azure-static-web-apps-orange-rock-0d20a680f.yml`), `docker` (`.github/workflows/build-push-container-images.yml`), `github.pages` (`.github/workflows/deploy-docs-site.yml`) |
| `real-stack-umami` | `pnpm` (`.github/workflows/ci.yml`) |
| `real-stack-wger` | `coveralls` (`.github/workflows/ci.yml`), `python` (`.github/workflows/ci.yml`) |
| `real-svc-eshop` | `mstest` (`Directory.Packages.props`) |
| `real-svc-otel-demo` | `connectrpc` (`src/checkout/go.mod`, `src/product-catalog/go.mod`), `grpc-gateway` (`src/checkout/go.mod`, `src/product-catalog/go.mod`), `jackson` (`src/ad/build.gradle`), `prometheus` (`src/ad/build.gradle`), `testify` (`src/product-catalog/go.mod`) |
