# Anagrafica del corpus

Scritta da `catalog.py` con [cases.json](cases.json) e i `fixtures/*/expected.json`: non si modifica a mano.
Si rigenera con `python catalog.py`.

140 progetti, 61 casi in 7 gruppi.

## Dominio dei casi

Assegnazione: "dai dati" se il caso segue da `expected.json`, e `python score.py --check all` fallisce quando la lista e i dati non concordano; "letto" se l'ha assegnato chi ha letto i file della fixture.
Incidente misurato: il caso misurato nella [ricerca](../../docs/research/2026-11-14-project-model-detection.md), §3.2, da cui il caso viene.

| Gruppo | Caso | Definizione | Progetti | Assegnazione | Incidente misurato |
| --- | --- | --- | --- | --- | --- |
| Struttura | `workspace-glob` | I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco. | 10 | letto |  |
| Struttura | `virtual-root` | La radice del workspace non è un'unità o non ha un file di build proprio. | 5 | letto |  |
| Struttura | `nested-module` | Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede. | 10 | letto | chi: moduli Go annidati in _examples/* che ./... salta |
| Struttura | `independent-units` | Più unità nella stessa cartella, senza un workspace che le unisca. | 10 | letto |  |
| Struttura | `shared-root` | Due sistemi di build o due ecosistemi nella stessa cartella. | 10 | dai dati |  |
| Struttura | `one-unit-many-parts` | Una sola unità contiene parti con ruoli diversi: frontend e backend, browser e server, più entry point. | 2 | letto | tududi: frontend e backend si installano da un solo package.json radice |
| Struttura | `targets-as-units` | Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno. | 15 | letto |  |
| Struttura | `no-build-file` | Codice senza file di build, oppure nessun codice. | 14 | dai dati |  |
| Struttura | `unit-no-name` | Un'unità senza nome dichiarato, nominata per radice. | 26 | dai dati |  |
| Struttura | `shared-name` | Due unità con lo stesso nome. | 6 | dai dati |  |
| Struttura | `name-mismatch` | Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto. | 15 | letto |  |
| Struttura | `custom-source-roots` | Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build. | 11 | letto |  |
| Struttura | `source-sets` | Più source set o target in un'unità, con dipendenze e task di compilazione propri. | 5 | letto | Kotlin: più task di compilazione, overload referenziati fra loro |
| Struttura | `path-alias` | Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti. | 10 | letto | app React: alias @/ in tsconfig.app.json sopra un tsconfig base |
| Struttura | `file-in-several-units` | Lo stesso file sorgente è compilato in più unità o target. | 7 | letto | workspace Rust: un modulo di test condiviso fra più crate di test |
| Struttura | `inherited-settings` | Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore. | 9 | letto |  |
| Struttura | `build-variants` | Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma. | 15 | letto |  |
| Versioni | `version-disagree` | La stessa toolchain è chiesta in più file con valori diversi. | 18 | letto |  |
| Versioni | `version-in-wrapper` | La versione del build tool è scritta solo nel wrapper. | 7 | letto |  |
| Versioni | `version-matrix` | Più versioni da una matrice CI o di ambienti di test, una voce per versione. | 7 | letto |  |
| Versioni | `version-range` | La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file. | 11 | letto |  |
| Versioni | `version-absent` | Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna. | 36 | letto |  |
| Versioni | `version-in-image` | La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI. | 12 | letto |  |
| Versioni | `toolchain-in-dependencies` | L'interprete o l'SDK compare fra le dipendenze (python, php, sdk: flutter), ma è una toolchain. | 6 | letto |  |
| Versioni | `platform-sdk` | L'unità chiede un SDK di piattaforma (Android, Xcode, MAUI, Flutter) che non è un pacchetto. | 5 | letto | Android Gradle: serve l'SDK di Android e chiama cargo |
| Dipendenze | `no-lockfile` | Nessun lockfile, quindi le versioni risolte restano vuote. | 72 | letto |  |
| Dipendenze | `locked-versions` | Le versioni risolte si leggono da un lockfile. | 33 | letto | progetto Python con le versioni in uv.lock |
| Dipendenze | `transitive-not-direct` | Il lock o il manifesto elenca pacchetti transitivi che non sono dipendenze dirette. | 8 | letto |  |
| Dipendenze | `version-from-bom` | Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto. | 11 | letto |  |
| Dipendenze | `version-indirect` | La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza. | 13 | letto |  |
| Dipendenze | `internal-link` | Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on. | 18 | letto |  |
| Dipendenze | `git-dependency` | Dipendenza presa da un URL git, un tarball o un sottomodulo, non dal registro. | 6 | letto |  |
| Dipendenze | `computed-dependencies` | Le dipendenze nascono da codice del progetto (cicli, condizioni, funzioni): leggere le righe non basta a trovarle tutte. | 4 | letto |  |
| Dipendenze | `declared-in-source` | Dipendenze dichiarate dentro un file sorgente: PEP 723, %pip, import map in HTML, #Requires. | 3 | letto |  |
| Dipendenze | `undeclared-imports` | Pacchetti importati dal codice e dichiarati da nessun file. | 4 | letto |  |
| Dipendenze | `scope-from-groups` | Lo scope si legge da gruppi, extra o configurazioni del build tool. | 11 | letto |  |
| Dipendenze | `build-only-dependency` | Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires. | 43 | dai dati |  |
| Dipendenze | `two-package-managers` | Due gestori di pacchetti dichiarano le dipendenze della stessa unità. | 2 | letto |  |
| Dipendenze | `included-requirement-files` | Liste divise su file inclusi (-r) o su vincoli (-c) che non aggiungono dipendenze. | 3 | letto |  |
| Linguaggi e file | `ambiguous-extension` | L'estensione non dice il linguaggio: lo dice il contenuto. | 17 | letto |  |
| Linguaggi e file | `shebang-only` | File senza estensione, riconoscibile solo dalla riga #!. | 5 | letto |  |
| Linguaggi e file | `generated-file` | File generato da escludere. | 16 | dai dati |  |
| Linguaggi e file | `false-generated` | File che sembra generato ma è sorgente del progetto. | 5 | letto |  |
| Linguaggi e file | `vendored-code` | Codice di terzi copiato nel repository. | 16 | dai dati |  |
| Linguaggi e file | `documentation-tree` | Albero di documentazione da escludere. | 17 | dai dati |  |
| Linguaggi e file | `binary-file` | File binari da escludere. | 16 | dai dati |  |
| Linguaggi e file | `committed-ignored` | File committato anche se .gitignore lo esclude. | 2 | letto |  |
| Linguaggi e file | `symlinks` | Link simbolici nel repository. | 2 | letto |  |
| Linguaggi e file | `templated-config` | Configurazione che un parser rigido non legge: JSON con commenti, YAML con template, ERB. | 4 | letto |  |
| Linguaggi e file | `dot-folder-facts` | Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config). | 10 | letto |  |
| Esecuzione | `needs-build` | Il modello completo esiste solo eseguendo la build, quindi in un container. | 24 | dai dati |  |
| Esecuzione | `install-scripts` | Installare le dipendenze esegue codice del progetto. | 2 | letto |  |
| Esecuzione | `build-generates-code` | Parte del codice o della configurazione esiste solo dopo un passo di build. | 15 | letto |  |
| Esecuzione | `submodule-absent` | Un sottomodulo Git dichiarato ma assente. | 2 | dai dati | sottomoduli Git assenti da un archivio |
| Esecuzione | `missing-file` | Un file nominato dalla configurazione non è nel repository. | 14 | letto |  |
| Servizi e framework | `service-in-infra` | Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze. | 11 | letto |  |
| Servizi e framework | `service-from-config` | Servizio riconoscibile solo da un URL di connessione o da una variabile d'ambiente. | 7 | letto |  |
| Servizi e framework | `saas-service` | Servizio gestito esterno, visibile solo da un SDK client o dalla configurazione. | 8 | letto |  |
| Servizi e framework | `framework-from-files` | Framework riconoscibile da file, SDK o CDN, non da una dipendenza dichiarata. | 5 | letto |  |
| Collegamenti | `undeclared-connections` | Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections. | 13 | dai dati |  |
| Collegamenti | `shared-contract` | Un file di contratto (proto, OpenAPI, GraphQL) unisce unità diverse. | 7 | letto |  |

## Progetti

### js (20 progetti)

#### js-angular

- Origine: scritto a mano per il benchmark.
- Linguaggi: CSS, HTML, TypeScript.
- Unità: angular-project (2), npm-package.
- Workspace: angular.
- File delle dipendenze: package.json, projects/ui-kit/package.json.
- Versioni dichiarate: nessuna.
- Framework: Angular.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.

#### js-bun

- Origine: scritto a mano per il benchmark.
- Linguaggi: TypeScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - bun: 1.2.2 (`.bun-version`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `templated-config`: Configurazione che un parser rigido non legge: JSON con commenti, YAML con template, ERB.

#### js-cjs-esm-exports

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript, TypeScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `false-generated`: File che sembra generato ma è sorgente del progetto.

#### js-deno

- Origine: scritto a mano per il benchmark.
- Linguaggi: TypeScript.
- Unità: deno-project.
- Workspace: nessuno.
- File delle dipendenze: import_map.json.
- Versioni dichiarate:
  - deno: 2.0.2 (`.tool-versions`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### js-lerna

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript.
- Unità: npm-package (3).
- Workspace: lerna.
- File delle dipendenze: package.json.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.

#### js-local-and-git-deps

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript.
- Unità: npm-package (2).
- Workspace: nessuno.
- File delle dipendenze: packages/app/package.json.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.
  - `git-dependency`: Dipendenza presa da un URL git, un tarball o un sottomodulo, non dal registro.

#### js-nextjs

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript, TSX, TypeScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate: nessuna.
- Framework: Next.js, React.
- Servizi: PostgreSQL.
- Casi:
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `generated-file`: File generato da escludere.
  - `service-from-config`: Servizio riconoscibile solo da un URL di connessione o da una variabile d'ambiente.

#### js-node-scripts

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript, Markdown.
- Unità: source-tree.
- Workspace: nessuno.
- File delle dipendenze: scripts/fetch.js.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `undeclared-imports`: Pacchetti importati dal codice e dichiarati da nessun file.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `shebang-only`: File senza estensione, riconoscibile solo dalla riga #!.

#### js-npm-single

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - node: >=18 (`package.json#engines`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.

#### js-npm-workspaces

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript.
- Unità: npm-package (3).
- Workspace: npm.
- File delle dipendenze: package.json, packages/cli/package.json, packages/core/package.json.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.

#### js-nx

- Origine: scritto a mano per il benchmark.
- Linguaggi: TypeScript.
- Unità: npm-package, nx-project (2).
- Workspace: nx.
- File delle dipendenze: package.json.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### js-pnpm-workspace

- Origine: scritto a mano per il benchmark.
- Linguaggi: TypeScript.
- Unità: npm-package (3).
- Workspace: pnpm.
- File delle dipendenze: pnpm-workspace.yaml.
- Versioni dichiarate:
  - node: >=20 (`package.json#engines`)
  - pnpm: 9.12.0 (`package.json#packageManager`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.

#### js-static-html

- Origine: scritto a mano per il benchmark.
- Linguaggi: CSS, HTML, JavaScript.
- Unità: source-tree.
- Workspace: nessuno.
- File delle dipendenze: index.html.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `declared-in-source`: Dipendenze dichiarate dentro un file sorgente: PEP 723, %pip, import map in HTML, #Requires.

#### js-sveltekit

- Origine: scritto a mano per il benchmark.
- Linguaggi: HTML, JavaScript, Svelte, TypeScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - node: >=18.13 (`package.json#engines`)
- Framework: Svelte, SvelteKit, Vite.
- Servizi: nessuno.
- Casi:
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.

#### js-turborepo

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript.
- Unità: npm-package (4).
- Workspace: npm.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - npm: 10.8.2 (`package.json#packageManager`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.

#### js-vendored-generated

- Origine: scritto a mano per il benchmark.
- Linguaggi: GraphQL, TypeScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `generated-file`: File generato da escludere.
  - `vendored-code`: Codice di terzi copiato nel repository.

#### js-version-conflict

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - node: >=18.17 <21 (`package.json#engines`); 22.1.0 (`.nvmrc`); 20.11.1 (`package.json#volta`)
  - pnpm: 9.1.0 (`package.json#packageManager`); 8.15.4 (`package.json#volta`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### js-vite-react-ts

- Origine: scritto a mano per il benchmark.
- Linguaggi: HTML, TSX, TypeScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate: nessuna.
- Framework: React, Vite.
- Servizi: nessuno.
- Casi:
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `false-generated`: File che sembra generato ma è sorgente del progetto.

#### js-vue-pnpm

- Origine: scritto a mano per il benchmark.
- Linguaggi: HTML, TypeScript, Vue.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - pnpm: 9.12.2 (`package.json#packageManager`)
- Framework: Vite, Vue.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.

#### js-yarn-berry

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript.
- Unità: npm-package (3).
- Workspace: yarn.
- File delle dipendenze: packages/app/package.json, packages/lib/package.json.
- Versioni dichiarate:
  - yarn: 4.5.0 (`package.json#packageManager`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.

### py (21 progetti)

#### py-conda-env

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: environment.yml, requirements-extra.txt.
- Versioni dichiarate:
  - python: 3.11 (`environment.yml`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `toolchain-in-dependencies`: L'interprete o l'SDK compare fra le dipendenze (python, php, sdk: flutter), ma è una toolchain.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `two-package-managers`: Due gestori di pacchetti dichiarano le dipendenze della stessa unità.
  - `included-requirement-files`: Liste divise su file inclusi (-r) o su vincoli (-c) che non aggiungono dipendenze.

#### py-django

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: requirements.txt.
- Versioni dichiarate: nessuna.
- Framework: Django.
- Servizi: SQLite.
- Casi:
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `false-generated`: File che sembra generato ma è sorgente del progetto.
  - `service-from-config`: Servizio riconoscibile solo da un URL di connessione o da una variabile d'ambiente.
  - `framework-from-files`: Framework riconoscibile da file, SDK o CDN, non da una dipendenza dichiarata.

#### py-fastapi-compose

- Origine: scritto a mano per il benchmark.
- Linguaggi: Dockerfile, Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: pyproject.toml.
- Versioni dichiarate:
  - python: >=3.11 (`pyproject.toml`); 3.12 (`Dockerfile`)
- Framework: FastAPI.
- Servizi: PostgreSQL, Redis.
- Casi:
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.

#### py-hatch-envs

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: pyproject.toml.
- Versioni dichiarate:
  - python: >=3.10 (`pyproject.toml`); 3.10, 3.11, 3.12 (`pyproject.toml#tool.hatch.envs.test.matrix`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `version-matrix`: Più versioni da una matrice CI o di ambienti di test, una voce per versione.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### py-monorepo-path-deps

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project (3).
- Workspace: nessuno.
- File delle dipendenze: apps/api/pyproject.toml, libs/common/pyproject.toml, libs/models/pyproject.toml.
- Versioni dichiarate:
  - python: >=3.11 (`libs/common/pyproject.toml`); >=3.11 (`libs/models/pyproject.toml`); >=3.11 (`apps/api/pyproject.toml`)
- Framework: FastAPI.
- Servizi: nessuno.
- Casi:
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### py-namespace-packages

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project (2).
- Workspace: nessuno.
- File delle dipendenze: packages/acme-core/pyproject.toml, packages/acme-plugins/pyproject.toml.
- Versioni dichiarate:
  - python: >=3.10 (`packages/acme-core/pyproject.toml`); >=3.10 (`packages/acme-plugins/pyproject.toml`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### py-notebooks

- Origine: scritto a mano per il benchmark.
- Linguaggi: Jupyter Notebook, Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: notebooks/analysis.ipynb, pyproject.toml.
- Versioni dichiarate:
  - python: >=3.10 (`pyproject.toml`); 3.11.4 (`notebooks/analysis.ipynb`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `declared-in-source`: Dipendenze dichiarate dentro un file sorgente: PEP 723, %pip, import map in HTML, #Requires.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### py-pdm

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: pyproject.toml.
- Versioni dichiarate:
  - python: >=3.9 (`pyproject.toml`); 3.11 (`.python-version`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### py-pep723-scripts

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: source-tree.
- Workspace: nessuno.
- File delle dipendenze: scripts/fetch.py, scripts/report.py.
- Versioni dichiarate:
  - python: >=3.11 (`scripts/fetch.py`); >=3.10 (`scripts/report.py`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `declared-in-source`: Dipendenze dichiarate dentro un file sorgente: PEP 723, %pip, import map in HTML, #Requires.

#### py-pip-tools

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: dev-requirements.in, requirements.in.
- Versioni dichiarate:
  - python: 3.12 (`requirements.txt`)
- Framework: Django.
- Servizi: nessuno.
- Casi:
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `transitive-not-direct`: Il lock o il manifesto elenca pacchetti transitivi che non sono dipendenze dirette.
  - `included-requirement-files`: Liste divise su file inclusi (-r) o su vincoli (-c) che non aggiungono dipendenze.
  - `framework-from-files`: Framework riconoscibile da file, SDK o CDN, non da una dipendenza dichiarata.

#### py-pipenv

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: Pipfile.
- Versioni dichiarate:
  - python: 3.11 (`Pipfile`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `transitive-not-direct`: Il lock o il manifesto elenca pacchetti transitivi che non sono dipendenze dirette.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.

#### py-poetry-groups

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: pyproject.toml.
- Versioni dichiarate:
  - poetry: 1.8.4 (`poetry.lock`)
  - python: ^3.10 (`pyproject.toml`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `toolchain-in-dependencies`: L'interprete o l'SDK compare fra le dipendenze (python, php, sdk: flutter), ma è una toolchain.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `transitive-not-direct`: Il lock o il manifesto elenca pacchetti transitivi che non sono dipendenze dirette.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### py-requirements-includes

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project (2).
- Workspace: nessuno.
- File delle dipendenze: libs/localpkg/pyproject.toml, requirements-dev.txt, requirements.txt, requirements/base.txt.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.
  - `git-dependency`: Dipendenza presa da un URL git, un tarball o un sottomodulo, non dal registro.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `included-requirement-files`: Liste divise su file inclusi (-r) o su vincoli (-c) che non aggiungono dipendenze.

#### py-setup-cfg-extras

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: pyproject.toml, setup.cfg.
- Versioni dichiarate:
  - python: >=3.9 (`setup.cfg`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### py-setup-py-dynamic

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `computed-dependencies`: Le dipendenze nascono da codice del progetto (cicli, condizioni, funzioni): leggere le righe non basta a trovarle tutte.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### py-setup-py-static

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: setup.py.
- Versioni dichiarate:
  - python: >=3.8 (`setup.py`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### py-undeclared-scripts

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: source-tree.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `undeclared-imports`: Pacchetti importati dal codice e dichiarati da nessun file.

#### py-uv-src-layout

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: pyproject.toml.
- Versioni dichiarate:
  - python: >=3.11 (`pyproject.toml`); 3.12 (`.python-version`)
  - uv: >=0.4.20 (`pyproject.toml`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `transitive-not-direct`: Il lock o il manifesto elenca pacchetti transitivi che non sono dipendenze dirette.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### py-uv-workspace

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project (2).
- Workspace: uv.
- File delle dipendenze: packages/app/pyproject.toml, packages/core/pyproject.toml.
- Versioni dichiarate:
  - python: >=3.11 (`packages/core/pyproject.toml`); >=3.11 (`packages/app/pyproject.toml`); 3.12 (`.python-version`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `virtual-root`: La radice del workspace non è un'unità o non ha un file di build proprio.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `transitive-not-direct`: Il lock o il manifesto elenca pacchetti transitivi che non sono dipendenze dirette.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### py-vendored-generated

- Origine: scritto a mano per il benchmark.
- Linguaggi: Protocol Buffer, Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: pyproject.toml.
- Versioni dichiarate:
  - python: >=3.10 (`pyproject.toml`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `generated-file`: File generato da escludere.
  - `vendored-code`: Codice di terzi copiato nel repository.

#### py-version-disagree

- Origine: scritto a mano per il benchmark.
- Linguaggi: Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: pyproject.toml.
- Versioni dichiarate:
  - python: >=3.9 (`pyproject.toml`); 3.10.14 (`.python-version`); 3.11.9 (`runtime.txt`); 3.8.18 (`.tool-versions`); 3.12 (`pyproject.toml#tool.pyright.pythonVersion`); 3.9 (`pyproject.toml#tool.mypy.python_version`); py310 (`pyproject.toml#tool.ruff.target-version`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

### jvm (34 progetti)

#### jvm-android-app-lib

- Origine: scritto a mano per il benchmark.
- Linguaggi: Kotlin.
- Unità: gradle-project (3).
- Workspace: gradle.
- File delle dipendenze: app/build.gradle.kts, build.gradle.kts, core/build.gradle.kts.
- Versioni dichiarate:
  - android-build-tools: 34.0.0 (`app/build.gradle.kts`); 34.0.0 (`core/build.gradle.kts`)
  - android-sdk: 35 (`app/build.gradle.kts`); 35 (`core/build.gradle.kts`)
  - gradle: 8.11.1 (`gradle/wrapper/gradle-wrapper.properties`)
  - java: 17 (`app/build.gradle.kts`); 17 (`core/build.gradle.kts`)
- Framework: Android, Firebase.
- Servizi: Firebase Analytics.
- Casi:
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `source-sets`: Più source set o target in un'unità, con dipendenze e task di compilazione propri.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-in-wrapper`: La versione del build tool è scritta solo nel wrapper.
  - `platform-sdk`: L'unità chiede un SDK di piattaforma (Android, Xcode, MAUI, Flutter) che non è un pacchetto.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.
  - `saas-service`: Servizio gestito esterno, visibile solo da un SDK client o dalla configurazione.

#### jvm-gradle-computed-deps

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: gradle.properties.
- Versioni dichiarate: nessuna.
- Framework: Jackson.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `computed-dependencies`: Le dipendenze nascono da codice del progetto (cicli, condizioni, funzioni): leggere le righe non basta a trovarle tutte.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### jvm-gradle-groovy-wrapper

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.
- Versioni dichiarate:
  - gradle: 8.11.1 (`gradle/wrapper/gradle-wrapper.properties`)
  - java: 17 (`build.gradle#java.sourceCompatibility`); 17 (`build.gradle#java.targetCompatibility`)
- Framework: JUnit Jupiter.
- Servizi: nessuno.
- Casi:
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `version-in-wrapper`: La versione del build tool è scritta solo nel wrapper.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.

#### jvm-gradle-kts-catalog-composite

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project (5).
- Workspace: gradle.
- File delle dipendenze: domain/build.gradle.kts, gradle/libs.versions.toml, libs/money/settings.gradle.kts, settings.gradle.kts.
- Versioni dichiarate:
  - gradle: 8.11.1 (`gradle/wrapper/gradle-wrapper.properties`)
  - java: 21 (`buildSrc/src/main/kotlin/inventory.java-conventions.gradle.kts`); 17 (`libs/money/build.gradle.kts`)
- Framework: Jackson, JUnit Jupiter.
- Servizi: nessuno.
- Casi:
  - `virtual-root`: La radice del workspace non è un'unità o non ha un file di build proprio.
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `inherited-settings`: Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore.
  - `version-in-wrapper`: La versione del build tool è scritta solo nel wrapper.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### jvm-gradle-locking

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.
- Versioni dichiarate:
  - java: 17 (`build.gradle`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.

#### jvm-java-version-conflict

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project, maven-module.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - java: 17 (`.java-version`); 21.0.5-tem (`.sdkmanrc`); 11 (`pom.xml#properties.maven.compiler.release`); 23 (`build.gradle.kts`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.

#### jvm-kmp-common-jvm

- Origine: scritto a mano per il benchmark.
- Linguaggi: Kotlin.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.kts.
- Versioni dichiarate:
  - java: 17 (`build.gradle.kts`)
- Framework: Kotlin Multiplatform.
- Servizi: nessuno.
- Casi:
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `source-sets`: Più source set o target in un'unità, con dipendenze e task di compilazione propri.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### jvm-kotlin-source-sets

- Origine: scritto a mano per il benchmark.
- Linguaggi: Kotlin.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.kts.
- Versioni dichiarate:
  - java: 21 (`build.gradle.kts`)
- Framework: JUnit Jupiter.
- Servizi: nessuno.
- Casi:
  - `source-sets`: Più source set o target in un'unità, con dipendenze e task di compilazione propri.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### jvm-maven-multi-bom-profile

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module (4).
- Workspace: maven.
- File delle dipendenze: model/pom.xml, pom.xml, service/pom.xml.
- Versioni dichiarate:
  - java: 21 (`pom.xml#properties.maven.compiler.release`); 17 (`model/pom.xml#properties.maven.compiler.release`)
- Framework: Jackson, JUnit Jupiter, picocli.
- Servizi: nessuno.
- Casi:
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `inherited-settings`: Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### jvm-maven-release-apt

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 21 (`pom.xml#maven-compiler-plugin.configuration.release`); 17 (`pom.xml#properties.java.version`)
- Framework: JUnit Jupiter, Lombok, MapStruct.
- Servizi: nessuno.
- Casi:
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.

#### jvm-maven-wrapper

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 17 (`pom.xml#properties.maven.compiler.release`)
  - maven: 3.9.9 (`.mvn/wrapper/maven-wrapper.properties`)
- Framework: JUnit Jupiter.
- Servizi: nessuno.
- Casi:
  - `version-in-wrapper`: La versione del build tool è scritta solo nel wrapper.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `vendored-code`: Codice di terzi copiato nel repository.

#### jvm-mixed-java-kotlin

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java, Kotlin.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 17 (`pom.xml#properties.maven.compiler.release`); 17 (`pom.xml#properties.kotlin.compiler.jvmTarget`)
- Framework: JUnit Jupiter.
- Servizi: nessuno.
- Casi:
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.

#### jvm-no-build

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: source-tree.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.

#### jvm-protobuf-generated

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java, Protocol Buffer.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.
- Versioni dichiarate:
  - java: 17 (`build.gradle`)
- Framework: Protocol Buffers.
- Servizi: nessuno.
- Casi:
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `generated-file`: File generato da escludere.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.

#### jvm-sbt-two-subprojects

- Origine: scritto a mano per il benchmark.
- Linguaggi: Scala.
- Unità: sbt-project (3).
- Workspace: sbt.
- File delle dipendenze: build.sbt, project/plugins.sbt.
- Versioni dichiarate:
  - sbt: 1.10.5 (`project/build.properties`)
  - scala: 3.3.4 (`build.sbt`)
- Framework: Cats, ScalaTest.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.

#### jvm-spring-boot-managed

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.kts.
- Versioni dichiarate:
  - java: 17 (`build.gradle.kts`)
- Framework: Hibernate, JUnit Jupiter, Spring Boot, Spring Data JPA, Spring MVC.
- Servizi: PostgreSQL.
- Casi:
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.

#### jvm-ver-gradle-mixed-tc8

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java, Kotlin.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.kts.
- Versioni dichiarate:
  - java: 8 (`build.gradle.kts#kotlin.jvmToolchain`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### jvm-ver-gradle-src6

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.
- Versioni dichiarate:
  - java: 1.6 (`build.gradle#java.sourceCompatibility`); 1.6 (`build.gradle#java.targetCompatibility`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-gradle-src8

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.
- Versioni dichiarate:
  - java: 1.8 (`build.gradle#java.sourceCompatibility`); 1.8 (`build.gradle#java.targetCompatibility`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-gradle-tc11

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.
- Versioni dichiarate:
  - java: 11 (`build.gradle#java.toolchain.languageVersion`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-gradle-tc21

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.
- Versioni dichiarate:
  - java: 21 (`build.gradle#java.toolchain.languageVersion`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-gradle-tc25

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.
- Versioni dichiarate:
  - java: 25 (`build.gradle#java.toolchain.languageVersion`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-gradle-tc8

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: gradle-project.
- Workspace: nessuno.
- File delle dipendenze: build.gradle.
- Versioni dichiarate:
  - java: 8 (`build.gradle#java.toolchain.languageVersion`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-11

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 11 (`pom.xml#properties.maven.compiler.source`); 11 (`pom.xml#properties.maven.compiler.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-14

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 14 (`pom.xml#properties.maven.compiler.source`); 14 (`pom.xml#properties.maven.compiler.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-21

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 21 (`pom.xml#properties.maven.compiler.source`); 21 (`pom.xml#properties.maven.compiler.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-25

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 25 (`pom.xml#properties.maven.compiler.source`); 25 (`pom.xml#properties.maven.compiler.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-5

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 1.5 (`pom.xml#properties.maven.compiler.source`); 1.5 (`pom.xml#properties.maven.compiler.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-6

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 1.6 (`pom.xml#properties.maven.compiler.source`); 1.6 (`pom.xml#properties.maven.compiler.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-7

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 1.7 (`pom.xml#properties.maven.compiler.source`); 1.7 (`pom.xml#properties.maven.compiler.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-8

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 1.8 (`pom.xml#properties.maven.compiler.source`); 1.8 (`pom.xml#properties.maven.compiler.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-9

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 9 (`pom.xml#properties.maven.compiler.source`); 9 (`pom.xml#properties.maven.compiler.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

#### jvm-ver-mvn-cfg6

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 1.6 (`pom.xml#maven-compiler-plugin.configuration.source`); 1.6 (`pom.xml#maven-compiler-plugin.configuration.target`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### jvm-ver-mvn-rel8

- Origine: scritto a mano per il benchmark.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 8 (`pom.xml#properties.maven.compiler.release`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.

### sys (25 progetti)

#### sys-bazel

- Origine: scritto a mano per il benchmark.
- Linguaggi: C++, Starlark.
- Unità: bazel-module, bazel-target (3).
- Workspace: bazel.
- File delle dipendenze: MODULE.bazel.
- Versioni dichiarate:
  - bazel: 7.4.1 (`.bazelversion`)
  - c++: 17 (`.bazelrc`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.

#### sys-c-macro-annotations

- Origine: scritto a mano per il benchmark.
- Linguaggi: C, C++, CMake.
- Unità: cmake-target (2).
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - c: 90 (`CMakeLists.txt#CMAKE_C_STANDARD`)
  - c++: 17 (`CMakeLists.txt#CMAKE_CXX_STANDARD`)
  - cmake: 3.16 (`CMakeLists.txt#cmake_minimum_required`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `file-in-several-units`: Lo stesso file sorgente è compilato in più unità o target.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.

#### sys-cmake-presets

- Origine: scritto a mano per il benchmark.
- Linguaggi: C, CMake.
- Unità: cmake-target (3).
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - c: 11 (`CMakeLists.txt#CMAKE_C_STANDARD`)
  - cmake: 3.25.0 (`CMakePresets.json`); 3.21 (`CMakeLists.txt#cmake_minimum_required`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.

#### sys-cmake-targets

- Origine: scritto a mano per il benchmark.
- Linguaggi: C++, CMake.
- Unità: cmake-target (2).
- Workspace: nessuno.
- File delle dipendenze: CMakeLists.txt.
- Versioni dichiarate:
  - c++: 17 (`CMakeLists.txt#CMAKE_CXX_STANDARD`)
  - cmake: 3.20 (`CMakeLists.txt#cmake_minimum_required`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `inherited-settings`: Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.

#### sys-cpp-header-only

- Origine: scritto a mano per il benchmark.
- Linguaggi: C++, CMake.
- Unità: cmake-target (2).
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - c++: 20 (`CMakeLists.txt#target_compile_features`)
  - cmake: 3.21 (`CMakeLists.txt#cmake_minimum_required`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.

#### sys-cpp-vcpkg-conan

- Origine: scritto a mano per il benchmark.
- Linguaggi: C++, CMake.
- Unità: cmake-target.
- Workspace: nessuno.
- File delle dipendenze: conanfile.txt, vcpkg.json.
- Versioni dichiarate:
  - c++: 20 (`CMakeLists.txt#CMAKE_CXX_STANDARD`)
  - cmake: 3.24 (`CMakeLists.txt#cmake_minimum_required`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `two-package-managers`: Due gestori di pacchetti dichiarano le dipendenze della stessa unità.

#### sys-git-submodule-absent

- Origine: scritto a mano per il benchmark.
- Linguaggi: C++, CMake.
- Unità: cmake-target.
- Workspace: nessuno.
- File delle dipendenze: .gitmodules.
- Versioni dichiarate:
  - c++: 17 (`CMakeLists.txt#CMAKE_CXX_STANDARD`)
  - cmake: 3.16 (`CMakeLists.txt#cmake_minimum_required`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `git-dependency`: Dipendenza presa da un URL git, un tarball o un sottomodulo, non dal registro.
  - `submodule-absent`: Un sottomodulo Git dichiarato ma assente.

#### sys-go-buildtags

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go.
- Unità: go-module.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - go: 1.22 (`go.mod`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.

#### sys-go-cgo

- Origine: scritto a mano per il benchmark.
- Linguaggi: C, Go.
- Unità: go-module.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - go: 1.22 (`go.mod`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.

#### sys-go-generated

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go.
- Unità: go-module.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - go: 1.22 (`go.mod`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `generated-file`: File generato da escludere.
  - `false-generated`: File che sembra generato ma è sorgente del progetto.

#### sys-go-nested

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go.
- Unità: go-module (2).
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - go: 1.22 (`go.mod`); 1.22 (`plugins/extra/go.mod`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.
  - `documentation-tree`: Albero di documentazione da escludere.

#### sys-go-single

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go.
- Unità: go-module.
- Workspace: nessuno.
- File delle dipendenze: go.mod.
- Versioni dichiarate:
  - go: 1.22 (`go.mod`)
- Framework: chi.
- Servizi: nessuno.
- Casi:
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.

#### sys-go-toolchain

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go.
- Unità: go-module.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - go: 1.23.4 (`go.mod#go`); go1.24.1 (`go.mod#toolchain`); 1.22.5 (`.tool-versions`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.

#### sys-go-vendor

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go.
- Unità: go-module.
- Workspace: nessuno.
- File delle dipendenze: go.mod.
- Versioni dichiarate:
  - go: 1.22 (`go.mod`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `vendored-code`: Codice di terzi copiato nel repository.

#### sys-go-workspace

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go.
- Unità: go-module (3).
- Workspace: go.
- File delle dipendenze: svc/go.mod.
- Versioni dichiarate:
  - go: 1.22 (`go.work`); 1.22 (`api/go.mod`); 1.22 (`svc/go.mod`); 1.22 (`tools/go.mod`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `virtual-root`: La radice del workspace non è un'unità o non ha un file di build proprio.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.

#### sys-make-plain

- Origine: scritto a mano per il benchmark.
- Linguaggi: C, Makefile.
- Unità: make-target (2).
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - c: c99 (`Makefile`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.

#### sys-meson

- Origine: scritto a mano per il benchmark.
- Linguaggi: C, Meson.
- Unità: meson-target (3).
- Workspace: nessuno.
- File delle dipendenze: meson.build.
- Versioni dichiarate:
  - c: c11 (`meson.build#default_options.c_std`)
  - meson: >=1.1.0 (`meson.build#meson_version`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.

#### sys-rust-buildrs

- Origine: scritto a mano per il benchmark.
- Linguaggi: Rust.
- Unità: cargo-crate.
- Workspace: nessuno.
- File delle dipendenze: Cargo.toml.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.

#### sys-rust-features

- Origine: scritto a mano per il benchmark.
- Linguaggi: Rust.
- Unità: cargo-crate.
- Workspace: nessuno.
- File delle dipendenze: Cargo.toml.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.

#### sys-rust-path-git

- Origine: scritto a mano per il benchmark.
- Linguaggi: Rust.
- Unità: cargo-crate (2).
- Workspace: nessuno.
- File delle dipendenze: Cargo.toml.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.
  - `git-dependency`: Dipendenza presa da un URL git, un tarball o un sottomodulo, non dal registro.

#### sys-rust-shared-test-module

- Origine: scritto a mano per il benchmark.
- Linguaggi: Rust.
- Unità: cargo-crate.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `file-in-several-units`: Lo stesso file sorgente è compilato in più unità o target.

#### sys-rust-single

- Origine: scritto a mano per il benchmark.
- Linguaggi: Rust.
- Unità: cargo-crate.
- Workspace: nessuno.
- File delle dipendenze: Cargo.toml.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `version-absent`: Nessun file dichiara la versione di una toolchain usata, e la risposta giusta è nessuna.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.

#### sys-rust-tauri

- Origine: scritto a mano per il benchmark.
- Linguaggi: HTML, JavaScript, Rust.
- Unità: cargo-crate, npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json, src-tauri/Cargo.toml.
- Versioni dichiarate: nessuna.
- Framework: Tauri.
- Servizi: nessuno.
- Casi:
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `shared-name`: Due unità con lo stesso nome.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.

#### sys-rust-toolchain-conflict

- Origine: scritto a mano per il benchmark.
- Linguaggi: Rust.
- Unità: cargo-crate.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - rust: 1.80 (`Cargo.toml`); 1.82.0 (`rust-toolchain.toml`); 1.79.0 (`rust-toolchain`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.

#### sys-rust-workspace

- Origine: scritto a mano per il benchmark.
- Linguaggi: Rust.
- Unità: cargo-crate (4).
- Workspace: cargo.
- File delle dipendenze: Cargo.toml.
- Versioni dichiarate:
  - rust: 1.74 (`Cargo.toml`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `virtual-root`: La radice del workspace non è un'unità o non ha un file di build proprio.
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `inherited-settings`: Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.

### mix (30 progetti)

#### mix-dart-flutter

- Origine: scritto a mano per il benchmark.
- Linguaggi: Dart.
- Unità: pub-package (3).
- Workspace: nessuno.
- File delle dipendenze: app/pubspec.yaml, tools/codegen/pubspec.yaml.
- Versioni dichiarate:
  - dart: ^3.5.0 (`app/pubspec.yaml`); ^3.5.0 (`packages/shop_core/pubspec.yaml`); ^3.5.0 (`tools/codegen/pubspec.yaml`)
  - flutter: 3.24.5 (`.fvmrc`); >=3.24.0 (`app/pubspec.yaml`)
- Framework: Flutter.
- Servizi: nessuno.
- Casi:
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `inherited-settings`: Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore.
  - `toolchain-in-dependencies`: L'interprete o l'SDK compare fra le dipendenze (python, php, sdk: flutter), ma è una toolchain.
  - `platform-sdk`: L'unità chiede un SDK di piattaforma (Android, Xcode, MAUI, Flutter) che non è un pacchetto.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.

#### mix-dotnet-central

- Origine: scritto a mano per il benchmark.
- Linguaggi: C#.
- Unità: dotnet-project (2).
- Workspace: dotnet.
- File delle dipendenze: Directory.Packages.props, src/Shop.Core/Shop.Core.csproj.
- Versioni dichiarate:
  - dotnet: 8.0.404 (`global.json`)
- Framework: ASP.NET Core, Entity Framework Core.
- Servizi: PostgreSQL.
- Casi:
  - `inherited-settings`: Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `framework-from-files`: Framework riconoscibile da file, SDK o CDN, non da una dipendenza dichiarata.

#### mix-edge-deep-manifest

- Origine: scritto a mano per il benchmark.
- Linguaggi: Rust.
- Unità: cargo-crate.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - rust: 1.83.0 (`rust-toolchain.toml`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `inherited-settings`: Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore.
  - `documentation-tree`: Albero di documentazione da escludere.

#### mix-edge-empty

- Origine: scritto a mano per il benchmark.
- Linguaggi: nessuno.
- Unità: nessuna.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `documentation-tree`: Albero di documentazione da escludere.

#### mix-edge-extensions

- Origine: scritto a mano per il benchmark.
- Linguaggi: MATLAB, Objective-C, Prolog, Python, XML.
- Unità: source-tree.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `shebang-only`: File senza estensione, riconoscibile solo dalla riga #!.

#### mix-edge-scripts

- Origine: scritto a mano per il benchmark.
- Linguaggi: Batchfile, PowerShell, Shell.
- Unità: source-tree.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - powershell: 7.2 (`scripts/backup.ps1`)
- Framework: nessuno.
- Servizi: Azure Blob Storage.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `shebang-only`: File senza estensione, riconoscibile solo dalla riga #!.
  - `saas-service`: Servizio gestito esterno, visibile solo da un SDK client o dalla configurazione.

#### mix-edge-sql

- Origine: scritto a mano per il benchmark.
- Linguaggi: PLpgSQL, PLSQL, SQL, TSQL.
- Unità: source-tree.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: Microsoft SQL Server, Oracle Database, PostgreSQL.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.

#### mix-edge-submodules

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript, Python.
- Unità: npm-package, python-project.
- Workspace: nessuno.
- File delle dipendenze: .gitmodules, package.json, pyproject.toml.
- Versioni dichiarate:
  - python: >=3.11 (`pyproject.toml`)
- Framework: Preact.
- Servizi: nessuno.
- Casi:
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `git-dependency`: Dipendenza presa da un URL git, un tarball o un sottomodulo, non dal registro.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `submodule-absent`: Un sottomodulo Git dichiarato ma assente.

#### mix-edge-vendored

- Origine: scritto a mano per il benchmark.
- Linguaggi: C, HTML, JavaScript, Python.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `undeclared-imports`: Pacchetti importati dal codice e dichiarati da nessun file.
  - `generated-file`: File generato da escludere.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `committed-ignored`: File committato anche se .gitignore lo esclude.

#### mix-elixir-umbrella

- Origine: scritto a mano per il benchmark.
- Linguaggi: Elixir.
- Unità: mix-project (3).
- Workspace: mix.
- File delle dipendenze: apps/shop_core/mix.exs, apps/shop_web/mix.exs.
- Versioni dichiarate:
  - elixir: 1.17.3-otp-27 (`.tool-versions`); ~> 1.17 (`apps/shop_core/mix.exs`); ~> 1.17 (`apps/shop_web/mix.exs`)
  - erlang: 27.1.2 (`.tool-versions`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `transitive-not-direct`: Il lock o il manifesto elenca pacchetti transitivi che non sono dipendenze dirette.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### mix-infra-compose

- Origine: scritto a mano per il benchmark.
- Linguaggi: Dockerfile, JavaScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - node: >=20 (`package.json`); 20.18.1 (`Dockerfile`)
- Framework: Express.
- Servizi: PostgreSQL, RabbitMQ, Redis.
- Casi:
  - `one-unit-many-parts`: Una sola unità contiene parti con ruoli diversi: frontend e backend, browser e server, più entry point.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.

#### mix-infra-devcontainer

- Origine: scritto a mano per il benchmark.
- Linguaggi: TypeScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - node: 20 (`.devcontainer/docker-compose.yml`)
  - python: 3.12 (`.devcontainer/devcontainer.json`)
- Framework: nessuno.
- Servizi: PostgreSQL.
- Casi:
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `templated-config`: Configurazione che un parser rigido non legge: JSON con commenti, YAML con template, ERB.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.

#### mix-infra-gha

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go, JavaScript, Python.
- Unità: go-module, npm-package, source-tree.
- Workspace: nessuno.
- File delle dipendenze: nessuno.
- Versioni dichiarate:
  - go: 1.23 (`tools/go.mod#go`); go1.23.4 (`tools/go.mod#toolchain`)
  - node: >=18.18 (`package.json#engines`); 20.18.1 (`.nvmrc`); 18.x (`.github/workflows/ci.yml#jobs.test.strategy.matrix.node`); 20.x (`.github/workflows/ci.yml#jobs.test.strategy.matrix.node`); 22.x (`.github/workflows/ci.yml#jobs.test.strategy.matrix.node`)
  - pnpm: 9.12.3 (`package.json#packageManager`); 9.15.0 (`.github/workflows/ci.yml`)
  - python: 3.12.7 (`.github/workflows/release.yml`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-matrix`: Più versioni da una matrice CI o di ambienti di test, una voce per versione.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).

#### mix-infra-k8s-helm

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go Template, YAML.
- Unità: helm-chart.
- Workspace: nessuno.
- File delle dipendenze: charts/shop/Chart.yaml.
- Versioni dichiarate: nessuna.
- Framework: nessuno.
- Servizi: Kubernetes, PostgreSQL, Redis.
- Casi:
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `templated-config`: Configurazione che un parser rigido non legge: JSON con commenti, YAML con template, ERB.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.

#### mix-infra-tool-versions

- Origine: scritto a mano per il benchmark.
- Linguaggi: JavaScript, Python.
- Unità: npm-package, python-project.
- Workspace: nessuno.
- File delle dipendenze: api/pyproject.toml, package.json.
- Versioni dichiarate:
  - node: 20.11.1 (`.tool-versions`); 22.12.0 (`mise.toml`); ^20.11.0 (`package.json#engines`); 20.18.1 (`package.json#volta`)
  - python: 3.11.9 (`.tool-versions`); 3.12 (`mise.toml`); >=3.10,<3.12 (`api/pyproject.toml`); 3.11.9 (`api/.python-version`)
- Framework: Flask.
- Servizi: PostgreSQL.
- Casi:
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `service-from-config`: Servizio riconoscibile solo da un URL di connessione o da una variabile d'ambiente.

#### mix-php-laravel

- Origine: scritto a mano per il benchmark.
- Linguaggi: Blade, CSS, JavaScript, PHP.
- Unità: composer-package, npm-package.
- Workspace: nessuno.
- File delle dipendenze: composer.json, package.json.
- Versioni dichiarate:
  - php: ^8.2 (`composer.json`)
- Framework: Laravel, Tailwind CSS, Vite.
- Servizi: MySQL, Redis, SMTP.
- Casi:
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `toolchain-in-dependencies`: L'interprete o l'SDK compare fra le dipendenze (python, php, sdk: flutter), ma è una toolchain.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `shebang-only`: File senza estensione, riconoscibile solo dalla riga #!.
  - `install-scripts`: Installare le dipendenze esegue codice del progetto.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.
  - `service-from-config`: Servizio riconoscibile solo da un URL di connessione o da una variabile d'ambiente.

#### mix-poly-firebase

- Origine: scritto a mano per il benchmark.
- Linguaggi: HTML, Kotlin, Python, Rust, TSX, TypeScript.
- Unità: cargo-crate, gradle-project (2), npm-package (2), python-project, source-tree.
- Workspace: gradle.
- File delle dipendenze: android/app/build.gradle.kts, android/build.gradle.kts, functions-python/pyproject.toml, functions/package.json, react-app/package.json, react-app/src-tauri/Cargo.toml.
- Versioni dichiarate:
  - android-build-tools: 34.0.0 (`android/app/build.gradle.kts`)
  - android-sdk: 35 (`android/app/build.gradle.kts`)
  - gradle: 8.10.2 (`android/gradle/wrapper/gradle-wrapper.properties`)
  - java: 17 (`android/app/build.gradle.kts`)
  - node: 20 (`functions/package.json`); nodejs20 (`firebase.json`)
  - python: python312 (`firebase.json`); >=3.12 (`functions-python/pyproject.toml`)
  - rust: 1.77.2 (`react-app/src-tauri/Cargo.toml`)
- Framework: Android, Firebase, React, Tauri, Vite.
- Servizi: Cloud Firestore, Cloud Functions for Firebase, Firebase Authentication, Firebase Hosting, Stripe.
- Casi:
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `file-in-several-units`: Lo stesso file sorgente è compilato in più unità o target.
  - `platform-sdk`: L'unità chiede un SDK di piattaforma (Android, Xcode, MAUI, Flutter) che non è un pacchetto.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `binary-file`: File binari da escludere.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.
  - `saas-service`: Servizio gestito esterno, visibile solo da un SDK client o dalla configurazione.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.

#### mix-poly-grpc

- Origine: scritto a mano per il benchmark.
- Linguaggi: Go, Protocol Buffer, Python.
- Unità: buf-module, go-module, python-project.
- Workspace: nessuno.
- File delle dipendenze: client-py/pyproject.toml, server/go.mod.
- Versioni dichiarate:
  - go: 1.23 (`server/go.mod`)
  - python: >=3.10 (`client-py/pyproject.toml`)
- Framework: gRPC.
- Servizi: nessuno.
- Casi:
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `generated-file`: File generato da escludere.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.
  - `shared-contract`: Un file di contratto (proto, OpenAPI, GraphQL) unisce unità diverse.

#### mix-poly-openapi

- Origine: scritto a mano per il benchmark.
- Linguaggi: Makefile, OASv3-yaml, Python, TypeScript.
- Unità: npm-package, python-project.
- Workspace: nessuno.
- File delle dipendenze: backend/pyproject.toml, frontend/package.json.
- Versioni dichiarate:
  - python: >=3.11 (`backend/pyproject.toml`)
- Framework: FastAPI.
- Servizi: nessuno.
- Casi:
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `undeclared-imports`: Pacchetti importati dal codice e dichiarati da nessun file.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `generated-file`: File generato da escludere.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.
  - `shared-contract`: Un file di contratto (proto, OpenAPI, GraphQL) unisce unità diverse.

#### mix-real-chi

- Origine: [github.com/go-chi/chi](https://github.com/go-chi/chi.git) al commit `c64ed7d6635f33a8b2feaff7dcfa55677023ac7d`, licenza MIT.
- Linguaggi: Go, Makefile.
- Unità: go-module (3).
- Workspace: nessuno.
- File delle dipendenze: _examples/rest/go.mod, _examples/versions/go.mod.
- Versioni dichiarate:
  - go: 1.24 (`go.mod`); 1.22 (`_examples/rest/go.mod`); 1.16 (`_examples/versions/go.mod`); 1.24.x (`.github/workflows/ci.yml#jobs.test.strategy.matrix.go-version`); 1.25.x (`.github/workflows/ci.yml#jobs.test.strategy.matrix.go-version`); 1.26.x (`.github/workflows/ci.yml#jobs.test.strategy.matrix.go-version`); 1.27.x (`.github/workflows/ci.yml#jobs.test.strategy.matrix.go-version`)
- Framework: chi.
- Servizi: nessuno.
- Casi:
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `version-matrix`: Più versioni da una matrice CI o di ambienti di test, una voce per versione.
  - `transitive-not-direct`: Il lock o il manifesto elenca pacchetti transitivi che non sono dipendenze dirette.
  - `generated-file`: File generato da escludere.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.

#### mix-real-javapoet

- Origine: [github.com/square/javapoet](https://github.com/square/javapoet.git) al commit `b9017a9503b76e11b4ad4c1a9f050e2d29112cb0`, licenza Apache-2.0.
- Linguaggi: Java.
- Unità: maven-module.
- Workspace: nessuno.
- File delle dipendenze: pom.xml.
- Versioni dichiarate:
  - java: 1.8 (`pom.xml#properties.java.version`); 8 (`.github/workflows/build.yml`)
- Framework: JUnit.
- Servizi: nessuno.
- Casi:
  - `inherited-settings`: Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### mix-real-klaxon

- Origine: [github.com/cbeust/klaxon](https://github.com/cbeust/klaxon.git) al commit `1173bdc568a6d339b45cf24a6a9c5c2f6847f42d`, licenza Apache-2.0.
- Linguaggi: Batchfile, Java, JavaScript, Kotlin, Shell.
- Unità: gradle-project (4), kobalt-project (2).
- Workspace: gradle.
- File delle dipendenze: build.gradle.kts, buildSrc/src/main/kotlin/KlaxonConfig.kt, klaxon-jackson/build.gradle.kts, klaxon/build.gradle.kts, kobalt/src/Build.kt.
- Versioni dichiarate:
  - gradle: 7.3 (`gradle/wrapper/gradle-wrapper.properties`)
  - java: 1.8 (`build.gradle.kts#java.sourceCompatibility`); 1.8 (`build.gradle.kts#java.targetCompatibility`); 8 (`.github/workflows/gradle.yml#jobs.build.strategy.matrix.java`); 9 (`.github/workflows/gradle.yml#jobs.build.strategy.matrix.java`); openjdk8 (`.travis.yml#jdk`); 1.7 (`kobalt/src/Build.kt#javaCompiler.args`)
  - kobalt: 1.0.129 (`kobalt/wrapper/kobalt-wrapper.properties`)
- Framework: TestNG.
- Servizi: nessuno.
- Casi:
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `version-in-wrapper`: La versione del build tool è scritta solo nel wrapper.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `computed-dependencies`: Le dipendenze nascono da codice del progetto (cicli, condizioni, funzioni): leggere le righe non basta a trovarle tutte.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `binary-file`: File binari da escludere.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### mix-real-python-semver

- Origine: [github.com/python-semver/python-semver](https://github.com/python-semver/python-semver.git) al commit `b6e83e3e40d3a7570386e8d694ae8011477a55c1`, licenza BSD-3-Clause.
- Linguaggi: Makefile, Python.
- Unità: python-project.
- Workspace: nessuno.
- File delle dipendenze: docs/requirements.txt, pyproject.toml.
- Versioni dichiarate:
  - python: >=3.10 (`pyproject.toml#project.requires-python`); 3.10 (`.github/workflows/python-testing.yml#jobs.tests.strategy.matrix.python-version`); 3.11 (`.github/workflows/python-testing.yml#jobs.tests.strategy.matrix.python-version`); 3.12 (`.github/workflows/python-testing.yml#jobs.tests.strategy.matrix.python-version`); 3.13 (`.github/workflows/python-testing.yml#jobs.tests.strategy.matrix.python-version`); 3.14 (`.github/workflows/python-testing.yml#jobs.tests.strategy.matrix.python-version`); 3.15 (`.github/workflows/python-testing.yml#jobs.tests.strategy.matrix.python-version`); 3.10 (`.github/workflows/python-testing.yml#jobs.check.steps`); 3.11 (`.readthedocs.yaml#build.tools.python`)
- Framework: pytest, Sphinx.
- Servizi: nessuno.
- Casi:
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-matrix`: Più versioni da una matrice CI o di ambienti di test, una voce per versione.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `symlinks`: Link simbolici nel repository.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.

#### mix-real-semver

- Origine: [github.com/dtolnay/semver](https://github.com/dtolnay/semver.git) al commit `280ebcb6edac3aa4cdc545dbff8a26c5ac4861fe`, licenza MIT OR Apache-2.0.
- Linguaggi: Rust.
- Unità: cargo-crate (2).
- Workspace: cargo.
- File delle dipendenze: Cargo.toml, fuzz/Cargo.toml.
- Versioni dichiarate:
  - rust: 1.68 (`Cargo.toml#package.rust-version`); nightly (`.github/workflows/ci.yml#jobs.test.strategy.matrix.rust`); beta (`.github/workflows/ci.yml#jobs.test.strategy.matrix.rust`); stable (`.github/workflows/ci.yml#jobs.test.strategy.matrix.rust`); 1.86.0 (`.github/workflows/ci.yml#jobs.test.strategy.matrix.rust`); 1.68.0 (`.github/workflows/ci.yml#jobs.test.strategy.matrix.rust`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `file-in-several-units`: Lo stesso file sorgente è compilato in più unità o target.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-matrix`: Più versioni da una matrice CI o di ambienti di test, una voce per versione.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### mix-real-tinyxml2

- Origine: [github.com/leethomason/tinyxml2](https://github.com/leethomason/tinyxml2.git) al commit `9148bdf719e997d1f474be6bcc7943881046dba1`, licenza Zlib.
- Linguaggi: C++, CMake, Makefile, Meson, Python.
- Unità: cmake-target (3), make-target (2), meson-target (2).
- Workspace: nessuno.
- File delle dipendenze: test/CMakeLists.txt.
- Versioni dichiarate:
  - cmake: 3.15 (`CMakeLists.txt#cmake_minimum_required`); 3.15 (`test/CMakeLists.txt#cmake_minimum_required`); 3.15 (`.github/workflows/test.yml#jobs.test.strategy.matrix.cmake`); 3.x (`.github/workflows/test.yml#jobs.test.strategy.matrix.cmake`)
  - meson: >= 0.49.0 (`meson.build#meson_version`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `shared-name`: Due unità con lo stesso nome.
  - `file-in-several-units`: Lo stesso file sorgente è compilato in più unità o target.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-matrix`: Più versioni da una matrice CI o di ambienti di test, una voce per versione.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### mix-real-tududi

- Origine: [github.com/chrisvel/tududi](https://github.com/chrisvel/tududi.git) al commit `71da9d7b34dfd1600657e9c5ddf40420206fd263`, licenza MIT.
- Linguaggi: CSS, Dockerfile, EJS, HTML, JavaScript, Shell, TSX, TypeScript.
- Unità: npm-package.
- Workspace: nessuno.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - node: 22 (`Dockerfile`); 22 (`.github/workflows/ci.yml`)
- Framework: Express, Jest, Playwright, React, Sequelize, Tailwind CSS, webpack.
- Servizi: Apprise, Lemon Squeezy, OpenAI, OpenID Connect provider, Paddle, PostgreSQL, SMTP, Stripe, Telegram Bot API, Web Push.
- Casi:
  - `one-unit-many-parts`: Una sola unità contiene parti con ruoli diversi: frontend e backend, browser e server, più entry point.
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.
  - `saas-service`: Servizio gestito esterno, visibile solo da un SDK client o dalla configurazione.

#### mix-real-zlib

- Origine: [github.com/madler/zlib](https://github.com/madler/zlib.git) al commit `51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf`, licenza Zlib.
- Linguaggi: Ada, Assembly, C, C#, C++, CMake, DIGITAL Command Language, HTML, M4Sugar, Makefile, Module Management System, Pascal, Roff Manpage, Shell.
- Unità: cmake-target (6), dotnet-project (2), make-target (78), msbuild-project (36).
- Workspace: dotnet.
- File delle dipendenze: contrib/dotzlib/DotZLib/DotZLib.csproj, contrib/nuget/nuget.csproj.
- Versioni dichiarate:
  - cmake: 2.4.4...3.15.0 (`CMakeLists.txt#cmake_minimum_required`)
  - gcc: 11 (`.github/workflows/cmake.yml#jobs.ci-cmake.strategy.matrix.include.compiler`)
- Framework: NUnit.
- Servizi: nessuno.
- Casi:
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `shared-name`: Due unità con lo stesso nome.
  - `file-in-several-units`: Lo stesso file sorgente è compilato in più unità o target.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-matrix`: Più versioni da una matrice CI o di ambienti di test, una voce per versione.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.

#### mix-ruby-rails

- Origine: scritto a mano per il benchmark.
- Linguaggi: HTML+ERB, Ruby.
- Unità: bundler-project.
- Workspace: nessuno.
- File delle dipendenze: Gemfile.
- Versioni dichiarate:
  - ruby: 3.3.6 (`.ruby-version`)
- Framework: Ruby on Rails, Sidekiq.
- Servizi: PostgreSQL, Redis.
- Casi:
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `shebang-only`: File senza estensione, riconoscibile solo dalla riga #!.
  - `templated-config`: Configurazione che un parser rigido non legge: JSON con commenti, YAML con template, ERB.
  - `service-from-config`: Servizio riconoscibile solo da un URL di connessione o da una variabile d'ambiente.

#### mix-swift-spm

- Origine: scritto a mano per il benchmark.
- Linguaggi: Swift.
- Unità: swift-package.
- Workspace: nessuno.
- File delle dipendenze: Package.swift.
- Versioni dichiarate:
  - swift: 5.9 (`Package.swift`); 5.10.1 (`.swift-version`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `source-sets`: Più source set o target in un'unità, con dipendenze e task di compilazione propri.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.

#### mix-terraform-modules

- Origine: scritto a mano per il benchmark.
- Linguaggi: HCL.
- Unità: terraform-module (2).
- Workspace: nessuno.
- File delle dipendenze: main.tf, modules/network/main.tf, versions.tf.
- Versioni dichiarate:
  - terraform: >= 1.6.0 (`versions.tf`); 1.9.8 (`.terraform-version`)
- Framework: nessuno.
- Servizi: nessuno.
- Casi:
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `version-range`: La versione scritta è un minimo o un intervallo; quella usata sta in un lock, in una regola di selezione o in nessun file.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.

### real (10 progetti)

#### real-app-full-stack-fastapi

- Origine: [github.com/fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) al commit `aabb90126964a164e02aff39e7c385bb0598236d`, licenza MIT.
- Linguaggi: CSS, Dockerfile, HTML, Mako, Python, Shell, TSX, TypeScript.
- Unità: npm-package (3), python-project (2).
- Workspace: bun, uv.
- File delle dipendenze: backend/pyproject.toml, packages/react-email/package.json.
- Versioni dichiarate:
  - bun: 1 (`backend/Dockerfile`); 1.3.12 (`.github/workflows/deploy.yml`); 1.3.12 (`.github/workflows/playwright.yml`); 1.3.12 (`.github/workflows/pre-commit.yml`)
  - python: >=3.14,<4.0 (`backend/pyproject.toml#project.requires-python`); py314 (`backend/pyproject.toml#tool.ruff.target-version`); 3.14 (`.python-version`); 3.14 (`backend/Dockerfile`)
  - uv: 0.9.26 (`backend/Dockerfile`); latest-known (`.github/workflows/bump-pre-commit-hooks.yml`); latest-known (`.github/workflows/create-draft-release.yml`); latest-known (`.github/workflows/deploy.yml`); latest-known (`.github/workflows/playwright.yml`); latest-known (`.github/workflows/pre-commit.yml`); latest-known (`.github/workflows/prepare-release.yml`); latest-known (`.github/workflows/smokeshow.yml`); latest-known (`.github/workflows/test-backend.yml`)
- Framework: FastAPI, Playwright, pytest, React, React Email, SQLModel, Tailwind CSS, TanStack Router, Vite.
- Servizi: Adminer, FastAPI Cloud, Let's Encrypt, Mailpit, PostgreSQL, Sentry, SMTP, Traefik.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `scope-from-groups`: Lo scope si legge da gruppi, extra o configurazioni del build tool.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `generated-file`: File generato da escludere.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `symlinks`: Link simbolici nel repository.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `saas-service`: Servizio gestito esterno, visibile solo da un SDK client o dalla configurazione.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.
  - `shared-contract`: Un file di contratto (proto, OpenAPI, GraphQL) unisce unità diverse.

#### real-app-hoppscotch

- Origine: [github.com/hoppscotch/hoppscotch](https://github.com/hoppscotch/hoppscotch) al commit `55908a76a1d0555c9bbb5d74244c14173df95b06`, licenza MIT.
- Linguaggi: CSS, Dockerfile, Go, GraphQL, Handlebars, HTML, JavaScript, Nix, PLpgSQL, Prisma, Rust, SCSS, Shell, SQL, Svelte, TypeScript, Vue.
- Unità: cargo-crate (8), go-module, npm-package (15).
- Workspace: pnpm.
- File delle dipendenze: packages/codemirror-lang-graphql/package.json, packages/hoppscotch-relay/Cargo.toml, packages/hoppscotch-selfhost-web/webapp-server/go.mod.
- Versioni dichiarate:
  - go: 1.24.0 (`packages/hoppscotch-selfhost-web/webapp-server/go.mod`); go1.24.1 (`packages/hoppscotch-selfhost-web/webapp-server/go.mod`); 1.26.7 (`prod.Dockerfile`); go_1_25 (`devenv.nix`)
  - node: >=22 (`packages/hoppscotch-cli/package.json#engines`); >=22 (`packages/hoppscotch-js-sandbox/package.json#engines`); >=24.22.1-r0 (`prod.Dockerfile`); 22 (`packages/hoppscotch-backend/Dockerfile`); lts (`packages/hoppscotch-selfhost-web/Dockerfile`); lts (`packages/hoppscotch-sh-admin/Dockerfile`); 18 (`.devcontainer/devcontainer.json`); 14 (`netlify.toml`); nodejs_22 (`devenv.nix`); nodejs_22 (`packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-appload/devenv.nix`); nodejs_22 (`packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-relay/devenv.nix`); 20 (`.github/workflows/build-hoppscotch-agent.yml`); 20 (`.github/workflows/build-hoppscotch-desktop.yml`); 22 (`.github/workflows/tests.yml#jobs.test.strategy.matrix.node-version`)
  - npm: 11.19.0 (`prod.Dockerfile`)
  - pnpm: 10.34.5 (`package.json#packageManager`); 10.34.5 (`prod.Dockerfile`); 10.15.0 (`.github/workflows/build-hoppscotch-agent.yml`); 10.18.3 (`.github/workflows/build-hoppscotch-desktop.yml`); 10 (`.github/workflows/tests.yml`)
  - rust: nightly (`devenv.nix`); nightly (`packages/hoppscotch-desktop/plugin-workspace/relay/devenv.nix`); nightly (`packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-appload/devenv.nix`); nightly (`packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-relay/devenv.nix`); 1.77.2 (`packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-appload/Cargo.toml`); 1.85 (`packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-relay/Cargo.toml`); 1.77.2 (`packages/hoppscotch-desktop/plugin-workspace/tauri-plugin-appload/examples/tauri-app/src-tauri/Cargo.toml`); stable (`.github/workflows/build-hoppscotch-agent.yml`); nightly (`.github/workflows/build-hoppscotch-desktop.yml`)
- Framework: Apollo Server, Axum, Express, Jest, NestJS, Passport, Prisma, Tailwind CSS, Tauri, Tokio, urql, Vite, Vitest, Vue.
- Servizi: Caddy, Cloud Firestore, Firebase Hosting, GitHub OAuth, Google OAuth, Microsoft OAuth, Netlify, PostgreSQL, PostHog, SMTP.
- Casi:
  - `workspace-glob`: I membri del workspace vengono da un glob o dalla scoperta dei file, con esclusioni o ricorsione, non da un elenco.
  - `nested-module`: Un modulo con il suo manifesto sta dentro la cartella di un altro, e il comando del genitore non lo vede.
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `shared-name`: Due unità con lo stesso nome.
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `git-dependency`: Dipendenza presa da un URL git, un tarball o un sottomodulo, non dal registro.
  - `generated-file`: File generato da escludere.
  - `false-generated`: File che sembra generato ma è sorgente del progetto.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `install-scripts`: Installare le dipendenze esegue codice del progetto.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.
  - `shared-contract`: Un file di contratto (proto, OpenAPI, GraphQL) unisce unità diverse.

#### real-app-jhipster-sample

- Origine: [github.com/jhipster/jhipster-sample-app](https://github.com/jhipster/jhipster-sample-app) al commit `6b000b5d23a36c45e01472471b84a44fa2464044`, licenza Apache-2.0.
- Linguaggi: CSS, Dockerfile, HTML, Java, JavaScript, SCSS, Shell, TypeScript.
- Unità: angular-project, maven-module, npm-package.
- Workspace: angular.
- File delle dipendenze: package.json.
- Versioni dichiarate:
  - java: 21 (`pom.xml#properties.java.version`); 25-jre-noble (`pom.xml#properties.jib-maven-plugin.image`); 17.x (`.github/workflows/github-actions.yml`); 21 (`.devcontainer/devcontainer.json#build.args.VARIANT`); 17 (`.devcontainer/Dockerfile`)
  - maven: 3.9.16 (`.mvn/wrapper/maven-wrapper.properties`); 3.2.5 (`pom.xml#properties.maven.version`)
  - node: v24.21.0 (`pom.xml#properties.node.version`); >=24.21.0 (`package.json#engines`); 20.15.0 (`.github/workflows/github-actions.yml`); 24.21.0 (`.devcontainer/devcontainer.json#build.args.NODE_VERSION`)
  - npm: 12.0.2 (`pom.xml#properties.npm.version`)
- Framework: Angular, ArchUnit, Bootstrap, Cypress, Gatling, Hibernate, JHipster, JUnit Jupiter, Liquibase, MapStruct, Spring Boot, Spring Data JPA, Spring MVC, Spring Security, Testcontainers, Thymeleaf, Vitest.
- Servizi: Grafana, H2, JHipster Control Center, PostgreSQL, Prometheus, SMTP, SonarQube.
- Casi:
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `shared-name`: Due unità con lo stesso nome.
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `path-alias`: Import risolti da alias di percorso (paths di tsconfig, alias del bundler, import map), non da pacchetti.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-in-wrapper`: La versione del build tool è scritta solo nel wrapper.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.

#### real-app-kotlinconf

- Origine: [github.com/JetBrains/kotlinconf-app](https://github.com/JetBrains/kotlinconf-app) al commit `146e891c150cd1062c6f6c78847ea0aa17fb379d`, licenza Apache-2.0.
- Linguaggi: HTML, JavaScript, Kotlin, Shell, SQL, Swift.
- Unità: gradle-project (10), swift-package (2), xcode-target.
- Workspace: gradle.
- File delle dipendenze: app/iosApp/KotlinMultiplatformLinkedPackage/subpackages/io_github_mirzemehdi_kmpnotifier_push_firebase_2_0_2/Package.swift, gradle/libs.versions.toml.
- Versioni dichiarate:
  - android-sdk: 37 (`gradle/libs.versions.toml#versions.android-compileSdk`)
  - gradle: 9.9.1 (`gradle/wrapper/gradle-wrapper.properties`)
  - java: 21 (`core/build.gradle.kts`); 21 (`app/shared/build.gradle.kts`); 21 (`app/ui-components/build.gradle.kts`); 21 (`app/desktopApp/build.gradle.kts`); 21 (`.github/workflows/build-all.yml`); 21 (`.github/workflows/web-deploy.yml`); 1-21 (`.devcontainer/devcontainer.json#image`)
  - maven: 3.8.6 (`.devcontainer/devcontainer.json#features.mavenVersion`)
  - node: 22.22.0 (`build.gradle.kts`)
  - swift: 5.9 (`app/iosApp/KotlinMultiplatformLinkedPackage/Package.swift`); 5.9 (`app/iosApp/KotlinMultiplatformLinkedPackage/subpackages/io_github_mirzemehdi_kmpnotifier_push_firebase_2_0_2/Package.swift`); 5.0 (`app/iosApp/KotlinConf.xcodeproj/project.pbxproj#SWIFT_VERSION`)
  - xcode: 26.2 (`.github/workflows/build-all.yml`)
- Framework: Android, Compose Multiplatform, Exposed, Firebase, JUnit, Koin, Kotlin Multiplatform, kotlinx.serialization, Ktor, Metro, SwiftUI.
- Servizi: Firebase Cloud Messaging, GitHub Pages, H2, Heroku, PostgreSQL, Sessionize.
- Casi:
  - `virtual-root`: La radice del workspace non è un'unità o non ha un file di build proprio.
  - `targets-as-units`: Le unità sono target dichiarati in un file di build (CMake, Meson, Make, Bazel, sbt, angular.json, Xcode), non pacchetti con un manifesto ciascuno.
  - `source-sets`: Più source set o target in un'unità, con dipendenze e task di compilazione propri.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `platform-sdk`: L'unità chiede un SDK di piattaforma (Android, Xcode, MAUI, Flutter) che non è un pacchetto.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `generated-file`: File generato da escludere.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `service-from-config`: Servizio riconoscibile solo da un URL di connessione o da una variabile d'ambiente.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.

#### real-app-memos

- Origine: [github.com/usememos/memos](https://github.com/usememos/memos) al commit `509e41bd1a1b2882404ad804ce2f2954cfad236a`, licenza MIT.
- Linguaggi: CSS, Dockerfile, Go, HTML, JavaScript, Protocol Buffer, Shell, SQL, TSX, TypeScript.
- Unità: buf-module, go-module, npm-package.
- Workspace: nessuno.
- File delle dipendenze: go.mod, web/package.json.
- Versioni dichiarate:
  - go: 1.27.2 (`go.mod`); 1.27.2 (`scripts/Dockerfile`)
  - golangci-lint: v2.14.0 (`.github/workflows/backend-tests.yml`)
  - node: >=24 (`web/package.json#engines`); 24 (`.github/actions/setup-web/action.yml`)
  - pnpm: 11.0.1 (`web/package.json#packageManager`)
- Framework: Cobra, Connect, gRPC, gRPC-Gateway, Protocol Buffers, React, React Router, Tailwind CSS, Testcontainers, testify, Vite, Vitest.
- Servizi: Amazon S3, Google Gemini, MySQL, OAuth2, OpenAI, PostgreSQL, SMTP, SQLite.
- Casi:
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `generated-file`: File generato da escludere.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `committed-ignored`: File committato anche se .gitignore lo esclude.
  - `saas-service`: Servizio gestito esterno, visibile solo da un SDK client o dalla configurazione.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.
  - `shared-contract`: Un file di contratto (proto, OpenAPI, GraphQL) unisce unità diverse.

#### real-svc-eshop

- Origine: [github.com/dotnet/eShop](https://github.com/dotnet/eShop) al commit `913acea66708a59595351174cee9b29f37179d29`, licenza MIT.
- Linguaggi: C#, CSS, HTML, HTML+Razor, JavaScript, PowerShell, Protocol Buffer, Text, TypeScript, XML.
- Unità: dotnet-project (28), npm-package.
- Workspace: dotnet.
- File delle dipendenze: Directory.Packages.props, package.json, src/HybridApp/HybridApp.csproj.
- Versioni dichiarate:
  - dotnet: 10.0.302 (`global.json#sdk.version`); 10.0.x (`.github/workflows/playwright.yml`)
  - node: lts/* (`.github/workflows/playwright.yml`); 20.x (`.github/workflows/markdownlint.yml`)
- Framework: .NET Aspire, .NET MAUI, ASP.NET Core, Blazor, Duende IdentityServer, Entity Framework Core, gRPC, MSTest, OpenTelemetry, Playwright, xUnit, YARP.
- Servizi: Azure Container Apps, Azure OpenAI, Google Maps, Ollama, PostgreSQL, RabbitMQ, Redis.
- Casi:
  - `file-in-several-units`: Lo stesso file sorgente è compilato in più unità o target.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `platform-sdk`: L'unità chiede un SDK di piattaforma (Android, Xcode, MAUI, Flutter) che non è un pacchetto.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `generated-file`: File generato da escludere.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `dot-folder-facts`: Fatti che stanno solo in cartelle che iniziano con un punto (.github, .devcontainer, .mvn, .config).
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.
  - `saas-service`: Servizio gestito esterno, visibile solo da un SDK client o dalla configurazione.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.
  - `shared-contract`: Un file di contratto (proto, OpenAPI, GraphQL) unisce unità diverse.

#### real-svc-otel-demo

- Origine: [github.com/open-telemetry/opentelemetry-demo](https://github.com/open-telemetry/opentelemetry-demo) al commit `b825c7c257268081dcfeff52d0f053fce1ef2561`, licenza Apache-2.0.
- Linguaggi: Batchfile, C#, C++, CMake, CSS, Dockerfile, Elixir, Go, HTML+EEX, HTML+ERB, Java, JavaScript, Kotlin, Makefile, PHP, Protocol Buffer, Python, Ruby, Rust, Shell, SQL, TSX, TypeScript.
- Unità: bundler-project (2), cargo-crate, cmake-target (2), composer-package, dotnet-project (3), go-module (3), gradle-project (3), mix-project, npm-package (4), python-project (6), source-tree.
- Workspace: dotnet.
- File delle dipendenze: internal/tools/go.mod, src/cart/Directory.Packages.props, src/payment/package.json.
- Versioni dichiarate:
  - cmake: 3.26 (`src/currency/CMakeLists.txt#cmake_minimum_required`); 3.26 (`src/currency/genproto/CMakeLists.txt#cmake_minimum_required`)
  - composer: 2.11.1 (`src/quote/Dockerfile`)
  - cypress: 16.2.1 (`src/frontend/Dockerfile.cypress`)
  - dotnet: 10.0.403 (`src/accounting/Dockerfile#builder`); 10.0.14 (`src/accounting/Dockerfile#stage 2`); 10.0.403 (`src/cart/src/Dockerfile#base`); 10.0.12 (`src/cart/src/Dockerfile#stage 4`)
  - elixir: 1.20.1 (`src/flagd-ui/Dockerfile`); ~> 1.20 (`src/flagd-ui/mix.exs`); 1.20.1 (`.github/workflows/fossa.yml`)
  - erlang: 28.5 (`src/flagd-ui/Dockerfile`); 28.4 (`.github/workflows/fossa.yml`)
  - go: 1.27.3 (`src/checkout/Dockerfile`); 1.27.3 (`src/checkout/genproto/Dockerfile`); 1.27.3 (`src/product-catalog/Dockerfile`); 1.27.3 (`src/product-catalog/genproto/Dockerfile`); 1.27.1 (`src/opamp-server/Dockerfile`); 1.26.0 (`src/checkout/go.mod`); 1.26.0 (`src/product-catalog/go.mod`); 1.12 (`internal/tools/go.mod`); 1.27.1 (`.github/workflows/checks.yml`); 1.27.1 (`.github/workflows/codeql-analysis.yml`); 1.27.1 (`.github/workflows/changelog.yml`)
  - gradle: 9.9.0 (`src/ad/gradle/wrapper/gradle-wrapper.properties`); 9.9.0 (`src/recommendation/gradle/wrapper/gradle-wrapper.properties`); 9.8.2 (`src/fraud-detection/Dockerfile`); 9.9.0 (`src/fraud-detection/gradle/wrapper/gradle-wrapper.properties`)
  - java: 24.0.2_12 (`src/ad/Dockerfile#builder`); 24.0.2_12 (`src/ad/Dockerfile#stage 1`); 21.0 (`src/ad/.java-version`); 21 (`src/ad/build.gradle#sourceCompatibility`); 21 (`src/ad/build.gradle#targetCompatibility`); 24.0.2_12 (`src/recommendation/Dockerfile#builder`); 24.0.2_12 (`src/recommendation/Dockerfile#stage 1`); 21 (`src/recommendation/build.gradle#options.release`); 17 (`src/fraud-detection/Dockerfile`); 17 (`src/fraud-detection/build.gradle.kts#kotlin.compilerOptions.jvmTarget`)
  - node: 26.12.1 (`src/frontend/Dockerfile#builder`); 24 (`src/frontend/Dockerfile#stage 2`); 26.12.1 (`src/frontend/genproto/Dockerfile`); 26.12.1 (`src/payment/Dockerfile#builder`); 24 (`src/payment/Dockerfile#stage 2`); 24 (`.github/workflows/react-native-build.yml`)
  - npm: 11 (`src/react-native-app/android.Dockerfile`)
  - php: 8.5.12 (`src/quote/Dockerfile`); >= 8.5 (`src/quote/composer.json#require.php`)
  - python: 3.14 (`src/agent/Dockerfile`); 3.14 (`src/chatbot/Dockerfile`); 3.14 (`src/mcp/Dockerfile`); 3.15.0 (`src/load-generator/Dockerfile`); 3.15.0 (`src/telemetry-docs/Dockerfile`); 3.12 (`test/telemetry/Dockerfile`); 3.14 (`src/agent/requirements.txt`); 3.14 (`src/chatbot/requirements.txt`); 3.14 (`src/mcp/requirements.txt`); 3.14 (`src/load-generator/requirements.txt`); 3.14 (`src/telemetry-docs/requirements.txt`); 3.14 (`test/telemetry/requirements.txt`); 3.x (`.github/workflows/checks.yml`)
  - ruby: 4.0.5 (`src/email/Dockerfile`); 4.0.5 (`src/react-native-app/.ruby-version`)
  - rust: 1.99.1 (`src/shipping/Dockerfile`)
  - weaver: 0.28.0 (`src/telemetry-docs/Dockerfile`)
- Framework: Actix Web, ASP.NET Core, Cypress, Entity Framework Core, Expo, FastAPI, FastMCP, Gradio, gRPC, LangChain, Locust, MkDocs, Next.js, Phoenix, Phoenix LiveView, Playwright, pytest, React, React Native, Sinatra, Slim, Spring Boot, Tailwind CSS, xUnit.
- Servizi: Envoy, Firepit, flagd, Grafana, Jaeger, Kafka, NGINX, OpAMP server, OpenAI API, OpenSearch, OpenTelemetry Collector, OpenTelemetry eBPF Profiler, PostgreSQL, Prometheus, Valkey.
- Casi:
  - `independent-units`: Più unità nella stessa cartella, senza un workspace che le unisca.
  - `shared-root`: Due sistemi di build o due ecosistemi nella stessa cartella.
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `shared-name`: Due unità con lo stesso nome.
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `custom-source-roots`: Le radici dei sorgenti non sono quelle di default e si leggono dalla configurazione del build.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `toolchain-in-dependencies`: L'interprete o l'SDK compare fra le dipendenze (python, php, sdk: flutter), ma è una toolchain.
  - `locked-versions`: Le versioni risolte si leggono da un lockfile.
  - `transitive-not-direct`: Il lock o il manifesto elenca pacchetti transitivi che non sono dipendenze dirette.
  - `computed-dependencies`: Le dipendenze nascono da codice del progetto (cicli, condizioni, funzioni): leggere le righe non basta a trovarle tutte.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `generated-file`: File generato da escludere.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `missing-file`: Un file nominato dalla configurazione non è nel repository.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.
  - `saas-service`: Servizio gestito esterno, visibile solo da un SDK client o dalla configurazione.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.
  - `shared-contract`: Un file di contratto (proto, OpenAPI, GraphQL) unisce unità diverse.

#### real-svc-petclinic-microservices

- Origine: [github.com/spring-petclinic/spring-petclinic-microservices](https://github.com/spring-petclinic/spring-petclinic-microservices) al commit `e8b747ab522721076cacb5cf688eb8a54ba8c5c9`, licenza Apache-2.0.
- Linguaggi: Dockerfile, HTML, Java, JavaScript, SCSS, Shell, SQL.
- Unità: maven-module (9).
- Workspace: maven.
- File delle dipendenze: pom.xml, spring-petclinic-admin-server/pom.xml, spring-petclinic-config-server/pom.xml, spring-petclinic-discovery-server/pom.xml.
- Versioni dichiarate:
  - java: 17 (`pom.xml#properties.java.version`); 17 (`docker/Dockerfile`); 17 (`.github/workflows/maven-build.yml#jobs.build.strategy.matrix.java`); 17 (`.devcontainer/devcontainer.json`)
  - maven: 3.9.8 (`.mvn/wrapper/maven-wrapper.properties`)
- Framework: Bootstrap, Hibernate, JUnit Jupiter, Resilience4j, Spring AI, Spring Boot, Spring Boot Admin, Spring Cloud Config, Spring Cloud Gateway, Spring Cloud Netflix, Spring Data JPA, Spring MVC, Spring WebFlux, Vue Router, Vue.js.
- Servizi: Grafana, HSQLDB, MySQL, OpenAI, Prometheus, Zipkin.
- Casi:
  - `name-mismatch`: Il nome di un pacchetto o di un'unità è diverso da come lo scrivono il codice, la cartella o l'artefatto.
  - `inherited-settings`: Impostazioni di un'unità che vengono da un file di una cartella superiore o da un genitore: rust-toolchain, Directory.Build.props, [workspace.package], pom genitore.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-in-wrapper`: La versione del build tool è scritta solo nel wrapper.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `version-indirect`: La versione sta in una proprietà, un catalogo o un file centrale, non accanto alla dipendenza.
  - `internal-link`: Una dipendenza punta a un'altra unità del repository (workspace:, path, in_umbrella, project()), quindi è un arco depends_on.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `generated-file`: File generato da escludere.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `needs-build`: Il modello completo esiste solo eseguendo la build, quindi in un container.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.
  - `framework-from-files`: Framework riconoscibile da file, SDK o CDN, non da una dipendenza dichiarata.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.

#### real-svc-robot-shop

- Origine: [github.com/instana/robot-shop](https://github.com/instana/robot-shop) al commit `55292e2199f2fb00a165b1f7d3045fe7f8922038`, licenza Apache-2.0.
- Linguaggi: CSS, Dockerfile, Go, HTML, Java, JavaScript, PHP, Python, Shell, SQL.
- Unità: composer-package, helm-chart, maven-module, npm-package (3), python-project (2), source-tree (4).
- Workspace: nessuno.
- File delle dipendenze: cart/package.json, catalogue/package.json, load-gen/requirements.txt, payment/requirements.txt, ratings/html/composer.json, shipping/pom.xml, user/package.json.
- Versioni dichiarate:
  - go: 1.17 (`dispatch/Dockerfile`)
  - java: 8 (`shipping/Dockerfile`); 1.8 (`shipping/pom.xml#properties.java.version`)
  - node: 14 (`cart/Dockerfile`); 14 (`catalogue/Dockerfile`); 14 (`user/Dockerfile`)
  - php: 7.4 (`ratings/Dockerfile`); ^7.4 (`ratings/html/composer.json`)
  - python: 3.9 (`payment/Dockerfile`); 3.9 (`load-gen/Dockerfile`)
- Framework: AngularJS, Express, Flask, Hibernate, Locust, Spring Boot, Spring Data JPA, Spring MVC, Symfony.
- Servizi: DC/OS, Docker Swarm, Elasticsearch, Fluentd, Instana, Instana EUM, Istio, Kubernetes, MongoDB, MySQL, nginx, OpenShift, PayPal, RabbitMQ, Redis.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `toolchain-in-dependencies`: L'interprete o l'SDK compare fra le dipendenze (python, php, sdk: flutter), ma è una toolchain.
  - `version-from-bom`: Nessuna versione è scritta nel progetto: la fissano un BOM, un genitore o un plugin del build esterni al progetto.
  - `build-only-dependency`: Dipendenze che servono solo a costruire: plugin, processori di annotazioni, build-dependencies, tool_requires.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `documentation-tree`: Albero di documentazione da escludere.
  - `binary-file`: File binari da escludere.
  - `build-generates-code`: Parte del codice o della configurazione esiste solo dopo un passo di build.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.
  - `service-from-config`: Servizio riconoscibile solo da un URL di connessione o da una variabile d'ambiente.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.

#### real-svc-voting-app

- Origine: [github.com/dockersamples/example-voting-app](https://github.com/dockersamples/example-voting-app) al commit `63e9150ca17af4ed05880d4245e486481f73fcb4`, licenza Apache-2.0.
- Linguaggi: C#, CSS, Dockerfile, HTML, JavaScript, Python, Shell.
- Unità: dotnet-project, npm-package, python-project, source-tree.
- Workspace: nessuno.
- File delle dipendenze: result/package.json, vote/requirements.txt, worker/Worker.csproj.
- Versioni dichiarate:
  - dotnet: 7.0 (`worker/Dockerfile`)
  - node: 18 (`result/Dockerfile`); 8.9 (`result/tests/Dockerfile`)
  - python: 3.11 (`vote/Dockerfile`); 3.9 (`seed-data/Dockerfile`)
- Framework: AngularJS, Express, Flask, Socket.IO.
- Servizi: PostgreSQL, Redis.
- Casi:
  - `no-build-file`: Codice senza file di build, oppure nessun codice.
  - `unit-no-name`: Un'unità senza nome dichiarato, nominata per radice.
  - `build-variants`: Unità, file o dipendenze cambiano con un'opzione di build: tag, feature, profilo, preset, flavor, piattaforma.
  - `version-disagree`: La stessa toolchain è chiesta in più file con valori diversi.
  - `version-in-image`: La versione di una toolchain sta solo nell'immagine di un Dockerfile, di un dev container o di un'azione CI.
  - `no-lockfile`: Nessun lockfile, quindi le versioni risolte restano vuote.
  - `ambiguous-extension`: L'estensione non dice il linguaggio: lo dice il contenuto.
  - `vendored-code`: Codice di terzi copiato nel repository.
  - `binary-file`: File binari da escludere.
  - `service-in-infra`: Servizi dichiarati solo da compose, Helm, Kubernetes o dev container, non dalle dipendenze.
  - `framework-from-files`: Framework riconoscibile da file, SDK o CDN, non da una dipendenza dichiarata.
  - `undeclared-connections`: Le unità si collegano fuori dai manifesti (rotte, RPC, code, tabelle, codice generato), elencate in connections.

## Copertura

### Progetti per caso

- `workspace-glob` (10): js-lerna, js-npm-workspaces, js-nx, js-pnpm-workspace, js-turborepo, js-yarn-berry, mix-elixir-umbrella, real-app-full-stack-fastapi, real-app-hoppscotch, sys-rust-workspace
- `virtual-root` (5): jvm-gradle-kts-catalog-composite, py-uv-workspace, real-app-kotlinconf, sys-go-workspace, sys-rust-workspace
- `nested-module` (10): jvm-gradle-kts-catalog-composite, mix-poly-firebase, mix-real-chi, mix-real-semver, mix-real-tinyxml2, mix-real-zlib, real-app-hoppscotch, sys-go-nested, sys-rust-tauri, sys-rust-workspace
- `independent-units` (10): js-local-and-git-deps, mix-dart-flutter, mix-poly-firebase, py-monorepo-path-deps, py-namespace-packages, real-app-hoppscotch, real-app-memos, real-svc-otel-demo, sys-go-nested, sys-rust-path-git
- `shared-root` (10): jvm-java-version-conflict, mix-edge-submodules, mix-php-laravel, mix-real-klaxon, mix-real-tinyxml2, mix-real-zlib, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-jhipster-sample, real-svc-otel-demo
- `one-unit-many-parts` (2): mix-infra-compose, mix-real-tududi
- `targets-as-units` (15): js-angular, jvm-sbt-two-subprojects, mix-real-tinyxml2, mix-real-zlib, real-app-jhipster-sample, real-app-kotlinconf, sys-bazel, sys-c-macro-annotations, sys-cmake-presets, sys-cmake-targets, sys-cpp-header-only, sys-cpp-vcpkg-conan, sys-git-submodule-absent, sys-make-plain, sys-meson
- `no-build-file` (14): js-node-scripts, js-static-html, jvm-no-build, mix-edge-empty, mix-edge-extensions, mix-edge-scripts, mix-edge-sql, mix-infra-gha, mix-poly-firebase, py-pep723-scripts, py-undeclared-scripts, real-svc-otel-demo, real-svc-robot-shop, real-svc-voting-app
- `unit-no-name` (26): js-deno, js-node-scripts, js-static-html, js-yarn-berry, jvm-no-build, mix-edge-extensions, mix-edge-scripts, mix-edge-sql, mix-elixir-umbrella, mix-infra-gha, mix-php-laravel, mix-poly-firebase, mix-poly-grpc, mix-ruby-rails, mix-terraform-modules, py-django, py-pep723-scripts, py-pip-tools, py-pipenv, py-requirements-includes, py-undeclared-scripts, real-app-full-stack-fastapi, real-app-memos, real-svc-otel-demo, real-svc-robot-shop, real-svc-voting-app
- `shared-name` (6): mix-real-tinyxml2, mix-real-zlib, real-app-hoppscotch, real-app-jhipster-sample, real-svc-otel-demo, sys-rust-tauri
- `name-mismatch` (15): jvm-android-app-lib, jvm-gradle-groovy-wrapper, jvm-maven-multi-bom-profile, jvm-sbt-two-subprojects, mix-real-semver, mix-swift-spm, py-namespace-packages, py-undeclared-scripts, real-app-full-stack-fastapi, real-svc-otel-demo, real-svc-petclinic-microservices, sys-go-single, sys-meson, sys-rust-single, sys-rust-workspace
- `custom-source-roots` (11): jvm-kmp-common-jvm, jvm-mixed-java-kotlin, jvm-protobuf-generated, mix-real-klaxon, mix-real-python-semver, py-namespace-packages, py-setup-py-static, py-uv-src-layout, real-app-full-stack-fastapi, real-app-jhipster-sample, real-svc-otel-demo
- `source-sets` (5): jvm-android-app-lib, jvm-kmp-common-jvm, jvm-kotlin-source-sets, mix-swift-spm, real-app-kotlinconf
- `path-alias` (10): js-angular, js-deno, js-nextjs, js-nx, js-sveltekit, js-vite-react-ts, mix-real-tududi, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-jhipster-sample
- `file-in-several-units` (7): mix-poly-firebase, mix-real-semver, mix-real-tinyxml2, mix-real-zlib, real-svc-eshop, sys-c-macro-annotations, sys-rust-shared-test-module
- `inherited-settings` (9): jvm-gradle-kts-catalog-composite, jvm-maven-multi-bom-profile, mix-dart-flutter, mix-dotnet-central, mix-edge-deep-manifest, mix-real-javapoet, real-svc-petclinic-microservices, sys-cmake-targets, sys-rust-workspace
- `build-variants` (15): jvm-android-app-lib, jvm-maven-multi-bom-profile, mix-real-semver, mix-real-tinyxml2, mix-real-zlib, real-svc-otel-demo, real-svc-petclinic-microservices, real-svc-voting-app, sys-c-macro-annotations, sys-cmake-presets, sys-cpp-header-only, sys-go-buildtags, sys-go-cgo, sys-meson, sys-rust-features
- `version-disagree` (18): js-version-conflict, jvm-java-version-conflict, jvm-maven-release-apt, mix-infra-gha, mix-infra-tool-versions, mix-real-python-semver, py-version-disagree, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-jhipster-sample, real-app-kotlinconf, real-svc-eshop, real-svc-otel-demo, real-svc-robot-shop, real-svc-voting-app, sys-cmake-presets, sys-go-toolchain, sys-rust-toolchain-conflict
- `version-in-wrapper` (7): jvm-android-app-lib, jvm-gradle-groovy-wrapper, jvm-gradle-kts-catalog-composite, jvm-maven-wrapper, mix-real-klaxon, real-app-jhipster-sample, real-svc-petclinic-microservices
- `version-matrix` (7): mix-infra-gha, mix-real-chi, mix-real-python-semver, mix-real-semver, mix-real-tinyxml2, mix-real-zlib, py-hatch-envs
- `version-range` (11): js-nextjs, jvm-gradle-locking, mix-dotnet-central, mix-real-zlib, mix-swift-spm, mix-terraform-modules, sys-bazel, sys-cmake-targets, sys-go-single, sys-rust-features, sys-rust-single
- `version-absent` (36): js-angular, js-lerna, js-node-scripts, js-npm-single, js-npm-workspaces, js-nx, js-vite-react-ts, js-vue-pnpm, js-yarn-berry, jvm-gradle-computed-deps, jvm-gradle-locking, jvm-java-version-conflict, jvm-no-build, jvm-sbt-two-subprojects, jvm-ver-gradle-mixed-tc8, jvm-ver-gradle-src6, jvm-ver-gradle-src8, jvm-ver-gradle-tc11, jvm-ver-gradle-tc21, jvm-ver-gradle-tc25, jvm-ver-gradle-tc8, jvm-ver-mvn-11, jvm-ver-mvn-14, jvm-ver-mvn-21, jvm-ver-mvn-25, jvm-ver-mvn-5, jvm-ver-mvn-6, jvm-ver-mvn-7, jvm-ver-mvn-8, jvm-ver-mvn-9, jvm-ver-mvn-cfg6, jvm-ver-mvn-rel8, py-pdm, py-requirements-includes, sys-cmake-presets, sys-rust-single
- `version-in-image` (12): mix-infra-compose, mix-infra-devcontainer, mix-infra-gha, mix-real-tududi, py-fastapi-compose, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-jhipster-sample, real-app-kotlinconf, real-svc-otel-demo, real-svc-robot-shop, real-svc-voting-app
- `toolchain-in-dependencies` (6): mix-dart-flutter, mix-php-laravel, py-conda-env, py-poetry-groups, real-svc-otel-demo, real-svc-robot-shop
- `platform-sdk` (5): jvm-android-app-lib, mix-dart-flutter, mix-poly-firebase, real-app-kotlinconf, real-svc-eshop
- `no-lockfile` (72): js-angular, js-cjs-esm-exports, js-deno, js-lerna, js-nextjs, js-nx, js-sveltekit, js-turborepo, js-vendored-generated, js-version-conflict, js-vite-react-ts, js-vue-pnpm, jvm-android-app-lib, jvm-gradle-computed-deps, jvm-kmp-common-jvm, jvm-kotlin-source-sets, jvm-maven-release-apt, jvm-maven-wrapper, jvm-mixed-java-kotlin, jvm-protobuf-generated, jvm-sbt-two-subprojects, jvm-ver-gradle-mixed-tc8, jvm-ver-gradle-src6, jvm-ver-gradle-src8, jvm-ver-gradle-tc11, jvm-ver-gradle-tc21, jvm-ver-gradle-tc25, jvm-ver-gradle-tc8, jvm-ver-mvn-11, jvm-ver-mvn-14, jvm-ver-mvn-21, jvm-ver-mvn-25, jvm-ver-mvn-5, jvm-ver-mvn-6, jvm-ver-mvn-7, jvm-ver-mvn-8, jvm-ver-mvn-9, jvm-ver-mvn-cfg6, jvm-ver-mvn-rel8, mix-dotnet-central, mix-edge-submodules, mix-edge-vendored, mix-infra-compose, mix-infra-devcontainer, mix-infra-k8s-helm, mix-infra-tool-versions, mix-php-laravel, mix-poly-firebase, mix-poly-openapi, mix-real-javapoet, mix-real-klaxon, mix-real-semver, mix-ruby-rails, py-conda-env, py-django, py-fastapi-compose, py-hatch-envs, py-monorepo-path-deps, py-namespace-packages, py-notebooks, py-pep723-scripts, py-requirements-includes, py-setup-cfg-extras, py-setup-py-static, py-vendored-generated, py-version-disagree, real-app-jhipster-sample, real-svc-eshop, real-svc-voting-app, sys-bazel, sys-cmake-targets, sys-rust-tauri
- `locked-versions` (33): js-bun, js-local-and-git-deps, js-npm-single, js-npm-workspaces, js-pnpm-workspace, js-yarn-berry, jvm-gradle-locking, mix-dart-flutter, mix-elixir-umbrella, mix-real-python-semver, mix-real-tududi, mix-swift-spm, mix-terraform-modules, py-pdm, py-pip-tools, py-pipenv, py-poetry-groups, py-uv-src-layout, py-uv-workspace, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-kotlinconf, real-app-memos, real-svc-otel-demo, sys-cpp-vcpkg-conan, sys-go-single, sys-go-vendor, sys-go-workspace, sys-rust-buildrs, sys-rust-features, sys-rust-path-git, sys-rust-single, sys-rust-workspace
- `transitive-not-direct` (8): mix-elixir-umbrella, mix-real-chi, py-pip-tools, py-pipenv, py-poetry-groups, py-uv-src-layout, py-uv-workspace, real-svc-otel-demo
- `version-from-bom` (11): jvm-android-app-lib, jvm-gradle-groovy-wrapper, jvm-gradle-kts-catalog-composite, jvm-kmp-common-jvm, jvm-kotlin-source-sets, jvm-maven-multi-bom-profile, jvm-spring-boot-managed, mix-real-klaxon, real-app-jhipster-sample, real-svc-petclinic-microservices, real-svc-robot-shop
- `version-indirect` (13): js-pnpm-workspace, jvm-gradle-computed-deps, jvm-gradle-kts-catalog-composite, jvm-maven-multi-bom-profile, jvm-maven-release-apt, jvm-mixed-java-kotlin, mix-dotnet-central, mix-real-javapoet, mix-real-klaxon, real-app-kotlinconf, real-svc-eshop, real-svc-petclinic-microservices, sys-rust-workspace
- `internal-link` (18): js-lerna, js-local-and-git-deps, js-npm-workspaces, js-pnpm-workspace, js-turborepo, js-yarn-berry, jvm-maven-multi-bom-profile, mix-dart-flutter, mix-elixir-umbrella, mix-terraform-modules, py-monorepo-path-deps, py-requirements-includes, py-uv-workspace, real-svc-petclinic-microservices, sys-go-nested, sys-go-workspace, sys-rust-path-git, sys-rust-workspace
- `git-dependency` (6): js-local-and-git-deps, mix-edge-submodules, py-requirements-includes, real-app-hoppscotch, sys-git-submodule-absent, sys-rust-path-git
- `computed-dependencies` (4): jvm-gradle-computed-deps, mix-real-klaxon, py-setup-py-dynamic, real-svc-otel-demo
- `declared-in-source` (3): js-static-html, py-notebooks, py-pep723-scripts
- `undeclared-imports` (4): js-node-scripts, mix-edge-vendored, mix-poly-openapi, py-undeclared-scripts
- `scope-from-groups` (11): jvm-spring-boot-managed, mix-real-python-semver, mix-ruby-rails, py-hatch-envs, py-pdm, py-pipenv, py-poetry-groups, py-setup-cfg-extras, py-uv-src-layout, real-app-full-stack-fastapi, sys-bazel
- `build-only-dependency` (43): jvm-android-app-lib, jvm-gradle-kts-catalog-composite, jvm-kmp-common-jvm, jvm-kotlin-source-sets, jvm-maven-multi-bom-profile, jvm-maven-release-apt, jvm-maven-wrapper, jvm-mixed-java-kotlin, jvm-protobuf-generated, jvm-sbt-two-subprojects, jvm-spring-boot-managed, jvm-ver-gradle-mixed-tc8, jvm-ver-mvn-cfg6, mix-edge-submodules, mix-infra-tool-versions, mix-poly-firebase, mix-poly-grpc, mix-poly-openapi, mix-real-javapoet, mix-real-klaxon, mix-real-python-semver, mix-real-zlib, py-fastapi-compose, py-hatch-envs, py-monorepo-path-deps, py-namespace-packages, py-notebooks, py-pdm, py-poetry-groups, py-requirements-includes, py-setup-cfg-extras, py-uv-src-layout, py-uv-workspace, py-vendored-generated, py-version-disagree, real-app-full-stack-fastapi, real-app-kotlinconf, real-svc-petclinic-microservices, real-svc-robot-shop, sys-bazel, sys-cpp-vcpkg-conan, sys-rust-buildrs, sys-rust-tauri
- `two-package-managers` (2): py-conda-env, sys-cpp-vcpkg-conan
- `included-requirement-files` (3): py-conda-env, py-pip-tools, py-requirements-includes
- `ambiguous-extension` (17): js-cjs-esm-exports, js-node-scripts, js-vue-pnpm, jvm-sbt-two-subprojects, mix-edge-extensions, mix-edge-sql, mix-infra-k8s-helm, mix-php-laravel, mix-poly-openapi, mix-real-tinyxml2, mix-real-zlib, real-app-full-stack-fastapi, real-svc-otel-demo, real-svc-voting-app, sys-c-macro-annotations, sys-cmake-targets, sys-cpp-header-only
- `shebang-only` (5): js-node-scripts, mix-edge-extensions, mix-edge-scripts, mix-php-laravel, mix-ruby-rails
- `generated-file` (16): js-nextjs, js-vendored-generated, jvm-protobuf-generated, mix-edge-vendored, mix-poly-grpc, mix-poly-openapi, mix-real-chi, py-vendored-generated, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-kotlinconf, real-app-memos, real-svc-eshop, real-svc-otel-demo, real-svc-petclinic-microservices, sys-go-generated
- `false-generated` (5): js-cjs-esm-exports, js-vite-react-ts, py-django, real-app-hoppscotch, sys-go-generated
- `vendored-code` (16): js-vendored-generated, jvm-android-app-lib, jvm-gradle-groovy-wrapper, jvm-gradle-kts-catalog-composite, jvm-maven-wrapper, mix-edge-vendored, mix-real-tududi, py-vendored-generated, real-app-jhipster-sample, real-app-kotlinconf, real-svc-eshop, real-svc-otel-demo, real-svc-petclinic-microservices, real-svc-robot-shop, real-svc-voting-app, sys-go-vendor
- `documentation-tree` (17): mix-edge-deep-manifest, mix-edge-empty, mix-edge-vendored, mix-real-python-semver, mix-real-tinyxml2, mix-real-tududi, mix-real-zlib, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-jhipster-sample, real-app-kotlinconf, real-app-memos, real-svc-eshop, real-svc-otel-demo, real-svc-petclinic-microservices, real-svc-robot-shop, sys-go-nested
- `binary-file` (16): mix-edge-vendored, mix-poly-firebase, mix-real-klaxon, mix-real-tinyxml2, mix-real-tududi, mix-real-zlib, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-jhipster-sample, real-app-kotlinconf, real-app-memos, real-svc-eshop, real-svc-otel-demo, real-svc-petclinic-microservices, real-svc-robot-shop, real-svc-voting-app
- `committed-ignored` (2): mix-edge-vendored, real-app-memos
- `symlinks` (2): mix-real-python-semver, real-app-full-stack-fastapi
- `templated-config` (4): js-bun, mix-infra-devcontainer, mix-infra-k8s-helm, mix-ruby-rails
- `dot-folder-facts` (10): mix-infra-devcontainer, mix-infra-gha, mix-real-chi, mix-real-javapoet, mix-real-python-semver, mix-real-semver, real-app-full-stack-fastapi, real-app-jhipster-sample, real-app-kotlinconf, real-svc-eshop
- `needs-build` (24): jvm-android-app-lib, jvm-gradle-computed-deps, jvm-gradle-groovy-wrapper, jvm-gradle-kts-catalog-composite, jvm-maven-multi-bom-profile, jvm-spring-boot-managed, mix-dotnet-central, mix-elixir-umbrella, mix-poly-firebase, mix-real-javapoet, mix-real-klaxon, mix-real-semver, mix-real-tinyxml2, mix-real-zlib, mix-swift-spm, py-setup-py-dynamic, real-app-hoppscotch, real-app-jhipster-sample, real-app-kotlinconf, real-svc-eshop, real-svc-otel-demo, real-svc-petclinic-microservices, sys-rust-buildrs, sys-rust-tauri
- `install-scripts` (2): mix-php-laravel, real-app-hoppscotch
- `build-generates-code` (15): js-angular, js-sveltekit, jvm-maven-release-apt, jvm-protobuf-generated, mix-poly-firebase, mix-real-zlib, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-kotlinconf, real-svc-eshop, real-svc-otel-demo, real-svc-petclinic-microservices, real-svc-robot-shop, sys-rust-buildrs, sys-rust-tauri
- `submodule-absent` (2): mix-edge-submodules, sys-git-submodule-absent
- `missing-file` (14): jvm-android-app-lib, jvm-gradle-groovy-wrapper, jvm-mixed-java-kotlin, mix-infra-compose, mix-infra-devcontainer, mix-php-laravel, mix-poly-firebase, mix-real-chi, mix-real-python-semver, mix-real-zlib, real-app-hoppscotch, real-svc-eshop, real-svc-otel-demo, sys-rust-tauri
- `service-in-infra` (11): jvm-spring-boot-managed, mix-infra-compose, mix-infra-devcontainer, mix-infra-k8s-helm, mix-real-tududi, py-fastapi-compose, real-app-jhipster-sample, real-svc-otel-demo, real-svc-petclinic-microservices, real-svc-robot-shop, real-svc-voting-app
- `service-from-config` (7): js-nextjs, mix-infra-tool-versions, mix-php-laravel, mix-ruby-rails, py-django, real-app-kotlinconf, real-svc-robot-shop
- `saas-service` (8): jvm-android-app-lib, mix-edge-scripts, mix-poly-firebase, mix-real-tududi, real-app-full-stack-fastapi, real-app-memos, real-svc-eshop, real-svc-otel-demo
- `framework-from-files` (5): mix-dotnet-central, py-django, py-pip-tools, real-svc-petclinic-microservices, real-svc-voting-app
- `undeclared-connections` (13): mix-poly-firebase, mix-poly-grpc, mix-poly-openapi, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-jhipster-sample, real-app-kotlinconf, real-app-memos, real-svc-eshop, real-svc-otel-demo, real-svc-petclinic-microservices, real-svc-robot-shop, real-svc-voting-app
- `shared-contract` (7): mix-poly-grpc, mix-poly-openapi, real-app-full-stack-fastapi, real-app-hoppscotch, real-app-memos, real-svc-eshop, real-svc-otel-demo

### Casi con meno di due progetti

Nessuno.
