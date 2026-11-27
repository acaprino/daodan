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

Il replay applica `service_registry.check_packages` e `check_files` a entrambi i registri. È la registrazione di ciò che si misurò allora: lo script e le due funzioni non ci sono più dal commit `091c093`, e si leggono nel suo genitore (`091c093^`). Usa i pacchetti estratti da Renovate, le immagini dichiarate nei workflow, le immagini base di BuildKit e i percorsi di go-enry ammessi dall’inventario. Legge gli attesi solo per assegnare il punteggio. Il rilevamento per modulo, i modelli di build che richiedono una checkout, il testo delle configurazioni e i riferimenti nel sorgente si misurano con `modal_stack.py`. Ad esempio il modello Gradle archiviato per `jvm-spring-boot-managed` riporta gli starter Web e Data JPA. Lo stack completo archiviato vi trova Spring MVC e Spring Data JPA.

Il conteggio originale di Specfy usa tutti gli ID emessi, compresi quelli classificati come builder. L’identità del prodotto tiene conto di varianti come «CypressCI» e «Cypress» e, quando il nome omette il fornitore, dell’ID specifico come `gcp.gcs`. «Vite» e «Vite+» contano separatamente. Le correzioni di punteggio si applicano anche al registro di partenza. Spring Boot era già riconoscibile dai pacchetti nei sette progetti che lo attendono. I cinque con uscita Specfy originale disponibile lo omettono tutti.

Sui 122 progetti in comune, Specfy aveva omesso 143 nomi di framework e 95 servizi. Il replay recuperava rispettivamente 90 e 19 di queste omissioni con il vecchio registro, 107 e 38 con quello aggiornato. Sulle 178 registrazioni il nuovo catalogo recupera 134 occorrenze di framework, librerie o strumenti e 90 di servizi, distribuite su 47 progetti. Conserva tutti i nomi attesi già rilevati. Trova inoltre 81 nuove occorrenze di framework, librerie o strumenti fuori dagli attesi, che in questa faccetta sono selettivi. Per i servizi le annotazioni mirano alla completezza. I due nuovi servizi fuori dagli attesi sono i driver MySQL e PostgreSQL di `tools/go.mod` in Owncast, da verificare rispetto allo stack dell’applicazione. I servizi fuori dagli attesi nel complesso passano da 58 a 57.

| Perché un nome atteso resta senza riscontro nel replay | Framework, librerie e strumenti | Servizi |
| --- | ---: | ---: |
| La voce ha regole per pacchetti o file, ma nessuna dichiarazione registrata corrisponde | 84 | 149 |
| La voce non ha regole per pacchetti o file. Altri segnali possibili includono un import Swift o un URL nel sorgente | 4 | 34 |
| Il catalogo non presenta il nome nella faccetta attesa, dopo aver applicato le equivalenze documentate nel codice | 6 | 103 |

Tra gli ultimi casi figurano Firebase, atteso anche come framework e catalogato come servizio, e SMTP, atteso come servizio in 23 progetti. Una libreria compatibile con un protocollo non identifica il fornitore che un progetto usa.

Questo comando, che girava dalla radice del repository fino al commit `091c093^` (non gira più), scriveva per progetto il percorso che prova ciascun nuovo riconoscimento, i nomi mancanti e le segnalazioni aggiuntive.

```sh
python benchmarks/project-model/replay_registry_coverage.py --baseline ca89d63877f8e3f9f94d8387a4b9154c5cdf9f1f --out registry-coverage.json
```

Il comando `smoke` misura l’eseguibile originale di Specfy sul progetto indicato, nell’immagine Modal. La modalità con le regole Daodan (`specfy_daodan`) e l’adattatore del registro (`daodan_registry`) non ci sono più: i loro risultati committati restano.

```sh
modal deploy benchmarks/project-model/modal_frameworks.py
python benchmarks/project-model/modal_frameworks.py smoke --tools specfy_stack_analyser --fixtures py-fastapi-compose
```

La tabella riporta l’archivio dell’eseguibile originale e il replay dei registri. La prova end-to-end dell’adattatore Specfy aggiornato resta da misurare su Modal.

## I percorsi TypeScript di Daodan contro `tsc`

Misura quanto il lettore scritto a mano (`import_resolution.ts_path_config`: un `tsconfig.json` o `jsconfig.json` per cartella, `extends` relativo, bersagli risolti contro `baseUrl` o la cartella del file che li dichiara; una configurazione vale per i discendenti) dista da `tsc`, prima di sostituirlo. `tools/ts_paths_vs_tsc.py` legge `results/native_tsc.json` (TypeScript 6.0.3 on Node v22.23.4, un `ts.getParsedCommandLineOfConfigFile` per tsconfig, registrato su Modal) e chiama il lettore sulle cartelle `fixtures/<nome>`; legge solo JSON e non esegue codice del progetto. Scrive `results/ts_paths_vs_tsc.json`; `test_ts_paths_vs_tsc.py` lo rigenera e lo confronta.

Parametri: le 17 fixture registrate; 6 non hanno qui l'albero (solo `expected.json` e `source.json`) e restano fuori. Per ogni unità di `tsc` e ogni pattern di `paths`, i percorsi di Daodan sono quelli della configurazione più vicina, nella cartella dell'unità o sopra. Classi: `same` (stessi bersagli), `different` (stesso pattern, altri bersagli), `missing` (solo `tsc`), `extra` (solo Daodan). Il lato `tsc` è la lettura dell'API del compilatore (`tools/native_tsc.py` con `tools/native_tsc_config.cjs`, una chiamata `node` per fixture): `options.paths`, `options.baseUrl` e `options.pathsBasePath`, la cartella del file che dichiara `paths`. Il compilatore risolve i `paths` contro `baseUrl ?? pathsBasePath` (TypeScript 6.0.3: `src/compiler/moduleNameResolver.ts:1576` chiama `getPathsBasePath`, `src/compiler/utilities.ts:6611`; `pathsBasePath` è scritto in `src/compiler/commandLineParser.ts:3432` e l'unione di `extends` lo conserva, 3451 e 3481). L'API dà anche `references`, il numero di file e gli errori di configurazione, con la stessa condizione di `--showConfig` (`src/compiler/executeCommandLine.ts:655`), che quindi non serve più.

Misura: 11 fixture con albero, 6 con almeno un pattern, 5 senza pattern da nessuna parte (una con errore di `tsc`).

| Classe | Coppie unità-pattern |
| --- | ---: |
| same | 5 |
| different | 0 |
| missing | 4 |
| extra | 0 |

Prima della correzione dell'adattatore (24 novembre 2026): 4 `same`, 1 `different`, 4 `missing`, 0 `extra`; cambia solo la coppia di `js-angular` qui sotto, che passa da `different` a `same`. Fino ad allora l'adattatore leggeva `tsc --showConfig`, che non dà `pathsBasePath`, e risolveva contro la cartella del tsconfig mostrato: un `paths` ereditato da un'altra cartella usciva sbagliato.

Fixture con differenze:

- `js-nx`: `missing` x3 (`@acme/util` in tre unità); i `paths` stanno in `tsconfig.base.json`, che Daodan non legge e nessun `tsconfig.json` estende.
- `js-vite-react-ts`: `missing` (`@/*`); il `tsconfig.json` radice ha solo `references`, i `paths` stanno in `tsconfig.app.json`, che Daodan non legge.
- `js-angular` non ha più differenze: `ui-kit` nell'unità `projects/ui-kit` era `different` (`tsc` dava `projects/ui-kit/dist/ui-kit`, Daodan `dist/ui-kit`) per un errore dell'adattatore, non di Daodan. Il `paths` è dichiarato nel `tsconfig.json` radice, ereditato da `projects/ui-kit/tsconfig.lib.json`, e TypeScript lo risolve contro il file che lo dichiara; con l'API ora lo dà anche l'adattatore (`dist/ui-kit`).

Limiti:

- (a) `pathsBasePath` è un campo `@internal` di TypeScript (`src/compiler/types.ts:7512`, non è in `typescript.d.ts`): vale per la versione fissata, 6.0.3, e si ricontrolla a ogni cambio di versione.
- (b) I `paths` di un'unità li unisce l'adattatore, e per un pattern vale il primo tsconfig dell'unità che lo dichiara; lo stesso pattern con altri bersagli in un tsconfig successivo non si vede. Così in `js-angular` il tsconfig di `storefront`, che ha il `pathsBasePath` fuori dalla sua cartella, non cambia l'unità radice: `tsconfig.json` la precede e dichiara `ui-kit` per primo. Fuori dalla propria cartella il `pathsBasePath` sta anche nel tsconfig di Cypress di `real-app-jhipster-sample`, la cui unità esce uguale a prima.
- (c) Su Modal la nuova registrazione ha `output` e `raw.references` uguali alla vecchia sulle 17 fixture, tranne `paths` dell'unità `projects/ui-kit` di `js-angular`; `raw.paths_base` cambia forma, `raw.typescript` è nuovo, e il testo degli errori perde il prefisso `exit 1:`.
- (d) Solo queste fixture: nessun albero intero di un progetto reale.

## Le importazioni che la configurazione di `tsc` aggiunge

Misura quante coppie (file importatore, specificatore) risolve in più, o in modo diverso, la configurazione di `tsc` rispetto a `import_resolution.ts_path_config`, sui progetti veri (8.11, passo 5, pezzo F2). Solo misura: `modal_ts_imports.py` su Modal, niente in `daodan/`; la parte pura (quale tsconfig tiene un file, il confronto) la prova `test_modal_ts_imports.py`. Scrive `results/ts-imports/ts-imports.json`: conteggi, al massimo cinque esempi per progetto, nessun sorgente.

Parametri:

- Corpus: le 11 miniature con un `tsconfig*.json` o un `jsconfig*.json` e le 58 fixture reali con archivio sul volume; 25 delle reali ne hanno uno e girano, le altre 33 no (le due risoluzioni sono uguali per costruzione). Codice di Daodan: un clone pulito di `11f751cc1` (`DAODAN_SCRIPTS`). TypeScript 6.0.3 su Node v22.23.4, come F1; nessun pacchetto ripristinato, nessun codice del progetto eseguito (l'API legge JSON).
- Prima: `iter_resolved_imports` con `ts_path_config`, come il prodotto oggi (le impostazioni della cartella più vicina con un `tsconfig.json` o `jsconfig.json`). Dopo: per ogni file importatore, `baseUrl` e `paths` del tsconfig che lo tiene, con base `baseUrl ?? pathsBasePath`, e la lettura a mano per i file che nessun tsconfig letto tiene (`tools/ts_imports_config.cjs`, una sottoclasse di `_ImportResolver` nel benchmark).
- Quale tsconfig tiene un file: l'elenco ufficiale `fileNames` di ogni `tsconfig*.json` e `jsconfig*.json`, mai la cartella più vicina. Se più tsconfig lo tengono, quello in cui lo apre tsserver (`src/server/editorServices.ts`, 6.0.3: `forEachConfigFileLocation`, dalla cartella del file in su un `tsconfig.json` e poi un `jsconfig.json` per cartella; `tryFindDefaultConfiguredProjectForOpenScriptInfoOrClosedFileInfo`: quel tsconfig se lo elenca, altrimenti i suoi `references` in ordine e i loro, altrimenti il tsconfig delle cartelle sopra). Un file che più tsconfig tengono e nessun cammino raggiunge è ambiguo: va al più profondo, poi al primo per nome. Un tsconfig che `tsc` rifiuta (un `extends` in un `node_modules` assente) non conta.
- Moduli: `module_derive.derive` sullo snapshot (nessuna pre-mappa, nessun arco di simboli); un arco fra moduli viene dai proprietari dei due file.

Risultati (36 progetti; i 32 che non compaiono hanno 0 guadagnate, 0 perse, 0 cambiate):

| Progetto | Importatori | Uguali | Guadagnate | Perse | Cambiate | Archi file | Archi moduli |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `js-nx` | 2 | 0 | 1 | 0 | 0 | +1 / -0 | +1 / -0 |
| `js-vite-react-ts` | 6 | 0 | 3 | 0 | 0 | +3 / -0 | +0 / -0 |
| `real-app-hoppscotch` | 1584 | 4878 | 0 | 101 | 0 | +0 / -101 | +0 / -0 |
| `real-stack-mattermost-mobile` | 3352 | 17097 | 0 | 9 | 0 | +0 / -9 | +0 / -0 |
| Totale | 19003 | 64649 | 4 | 110 | 0 | +4 / -110 | +1 / -0 |

- Guadagnate: 4, tutte da un pattern di `paths`, nessuna da un `baseUrl` semplice, tutte in due miniature (`@acme/util` in `tsconfig.base.json` di `js-nx`, `@/*` in `tsconfig.app.json` di `js-vite-react-ts`): i due casi che F0 aveva già visto. Nessuna sui 25 progetti reali.
- Perse: 110, tutte da un pattern di `paths`, in 81 file importatori di test. Il tsconfig che li tiene è un `jsconfig.json` della radice, l'unico che li elenca (il tsconfig del pacchetto li esclude), e non ha il `paths` dell'alias: per `tsc` quei file non hanno alias, la lettura a mano usa quelli della cartella. Archi fra moduli persi: 0.
- Ambigui: 5713 file tenuti da più tsconfig e risolti dalla regola di tsserver; 4 che nessun cammino raggiunge (`js-nx` 2, `mix-poly-firebase` 2). In 4351 i tsconfig che li tengono hanno impostazioni diverse: 1043 in `real-app-hoppscotch`, 3260 in `real-stack-mattermost-mobile`, dove un `tsconfig.json` e un `jsconfig.json` si sovrappongono.
- Errori di `tsc`: 21 tsconfig su 125: 15 TS6053 (un `extends` in un pacchetto che non c'è), 4 TS5083 (un `extends` in un file generato, `.nuxt/` o `.svelte-kit/`), 2 TS18003 (nessun file in ingresso). Dietro un tsconfig rifiutato stanno 2623 importatori, 1649 in `real-stack-documenso`, 565 in `real-stack-mealie`; restano alla lettura a mano.
- File che nessun tsconfig tiene: 5849 importatori su 19003: i 2623 appena detti, `.vue` (1424: `tsc` non li elenca), `.js` senza `allowJs` e il resto.

Limiti:

- (a) Senza ripristino di pacchetti né generazione dei tsconfig dei framework, i 2623 importatori dietro un tsconfig rifiutato non si possono dire: la pre-mappa il ripristino lo fa (`premap/tsc.py`), e lì il risultato può essere diverso.
- (b) Lo snapshot è la lettura intera, senza pre-mappa: i file di terze parti e generati ci sono. I moduli sono quelli senza pre-mappa e senza i simboli: un arco fra moduli che passa da un simbolo non è contato.
- (c) `tsc` elenca i file radice di ogni tsconfig; un file importato e non elencato non ha tsconfig. Senza le estensioni che `vue-tsc` e simili aggiungono, `.vue`, `.svelte` e `.astro` restano alla lettura a mano.
- (d) La regola di tsserver è letta nel sorgente e rifatta con `disableSolutionSearching` e `disableReferencedProjectLoad`, senza altre opzioni (`composite`, `solution`).
- (e) Solo queste fixture e questi progetti pubblici, al commit che il corpus fissa.

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

### Casi reali completi

Regola del proprietario, 26 novembre 2026: un progetto reale misura Daodan nel complesso, non una sua parte. Un caso completo è una cartella sola con quattro file:

| File | Che cosa dice | Formato e controllo |
| --- | --- | --- |
| `source.json` | repository, commit, licenza, perché | — |
| `expected.json` | la pre-mappa: linguaggi, unità, toolchain, dipendenze, framework, servizi, esclusi | [SCHEMA.md](SCHEMA.md), `score.py --check` |
| `graph.json` | il grafo: ingressi, rotte unite ai chiamanti, chiamate esterne, store, lacune | `daodan/real-graph-expected/v1`, `../system-map/real_references.py` |
| `system.json` | la mappa di sistema con i flussi | `../system-map/reference-brief.md`, `../system-map/reference.py check` |

Completi oggi: `real-auth0-go`, `real-sveltekit-realworld`, `real-microblog`, `real-next-subscriptions`, `real-bank-of-anthos`. Le altre 51 cartelle `real-*` hanno solo `source.json` ed `expected.json`, e le 40 `real-stack-*` solo framework e servizi: sono casi parziali, da completare. I candidati per i casi nuovi sono in [CANDIDATI.md](CANDIDATI.md).

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
| `native` | il comando di modello di ogni build tool (`go list`, `cargo metadata`, `npm`/`pnpm ls`, `uv`, l’API di `tsc`, Gradle, Maven, …), `.gitmodules`, deptry, dependency-cruiser, uv per PEP 723; `modules.py` di Daodan come riferimento | `modal_native.py` |
| `versions` | mise, proto, Renovate, Railpack, `GOTOOLCHAIN`, uv, rustup, corepack | `modal_versions.py` |
| `frameworks` | Specfy stack-analyser, Vercel fs-detectors, Netlify build-info, devfile/alizer, Railpack; il registro di Daodan come riferimento resta nei risultati committati (`results/daodan_registry.json`), il suo adattatore non c'è più | `modal_frameworks.py` |

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

La registrazione di ciò che si misurò allora: `replay_stack_packages.py` e `service_registry.check_packages` non ci sono più dal commit `091c093` e si leggono nel suo genitore (`091c093^`). `replay_stack_packages.py` rilegge le risposte di Renovate conservate in `results/premap-runs`. Per ogni progetto applica il lettore della pre-mappa e misura `service_registry.check_packages` sulle coppie pacchetto PyPI/file. Il JSON di uscita contiene le triple tecnologia, pacchetto e file per fixture. I parametri sono la revisione Git, le fixture da escludere, il numero di ripetizioni del matcher e il file di uscita. Il replay legge dati archiviati senza avviare strumenti esterni di analisi o codice delle fixture.

Dal repository, al commit `091c093^`, con due percorsi di uscita a scelta (non girano più):

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

Misura lo step `stack` com'è dopo il passaggio al fork ([spec](../../docs/specs/2026-11-21-stack-dal-fork.md), «Verifica»; [piano 3](../../docs/plans/2026-11-22-stack-dal-fork-3-passaggio.md)): `stack_recognition.run` traduce i fatti della pre-mappa in dichiarazioni, le manda a stack-analyser (rilascio `1.27.6-daodan.5`) con il perimetro in un file e riporta le sue prove come voci del registro. Il registro non riconosce più nulla, quindi il codice non confronta più i due riconoscitori: il giro nuovo si confronta con l'ultimo del piano 2, che resta nei risultati committati (`results/daodan_stack_fork.json`, `results/daodan_registry.json`). Il giro nuovo su Modal non è stato fatto: «Non misurato».

### Parametri

- Corpus: le 180 fixture con `expected.json`. Giro, su Modal e mai su questo PC: `modal deploy benchmarks/project-model/modal_stack.py`, poi `python benchmarks/project-model/modal_stack.py spawn [--fixtures a,b | --families js,py,jvm,sys,mix,real]` e `fetch`, che riscrive `results/daodan_stack.json` (oggi quello del giro del 19 novembre 2026, del solo registro: la sezione «Lo step `stack` sul corpus») e confronta l'impronta del codice dei due lati. Container Linux di 1 CPU e 4 GB, 1.800 secondi per fixture e 3.000 per gruppo.
- Strumento: stack-analyser `1.27.6-daodan.5`, sha256 `e87658b2d630df6cb90de21070e86f91efdbe6a7b841dbeb3aab6add6332475c`, sul Node v22.23.4 che il prodotto avvia (`indexers.runtime.NODE_VERSION`). Lo scarica l'immagine con gli stessi comandi di `tests/modal_pytest.py`; `test_fork_stack.py` confronta i tre posti dove il rilascio è fissato (`stack_analyser.py`, `tests/modal_pytest.py`, `modal_stack.py`) e la versione di Node. Il driver mette quei due percorsi al posto di `stack_analyser.cli` e `stack_analyser.node` (`_image_tool`): l'installazione del prodotto non si misura qui, la prova la fa. Prima di ogni gruppo il rilascio gira una volta su una cartella vuota, fuori da ogni tempo, per l'avvio a freddo di Node.
- Scansione completa: la snapshot, la pre-mappa con le risposte registrate dei comandi di modello (`results/premap-runs`; `model: none` o `partial` come nelle sezioni sopra), poi `technologies.ensure(manifest)`; i suoi secondi sono `seconds.stack`. Una fixture in cui il rilascio non ha girato (`checker_failed`) è un `error`, non un progetto che non mostra nulla.
- Scansione veloce: la pre-mappa senza comandi di modello (`premap.write(runner=None)`, fuori dal tempo) e `technologies.derive` su quei fatti, che parte dal record della completa e ne conserva i segni delle fonti non eseguite (`fast_seconds`). Si deriva e non si chiama `ensure` perché un record fresco sarebbe letto, non derivato. Il tempo è quello di una chiamata (`time.monotonic()`), una misura per fixture, senza ripetizioni, con l'avvio di Node dentro. Non è il `fork_fast` del piano 2, che misurava il solo riconoscitore sui fatti della veloce: qui c'è anche la traduzione, la fusione con il record della completa e il grafo dei moduli.
- `declarations` e `perimeter`: quante dichiarazioni la scansione completa manda al rilascio, e quante voci di `skipDirs` e `ignore` insieme (`tools/fork_stack.figures`, sulla prima chiamata di `stack_analyser.run`). Il piano 2 aveva visto il tempo crescere con la lunghezza dell'`ignore` senza poterla separare dal numero delle dichiarazioni.
- Sono tre i campi nuovi di ogni fixture in `results/daodan_stack.json`: `fast_seconds`, `declarations`, `perimeter`. Il resto del formato è quello del 19 novembre; cambiano solo le stringhe `version` e `command` dell'intestazione.
- `executed_project_code`: `no` se ogni processo che il Python di Daodan ha avviato nelle due scansioni è `git` (il perimetro) o Node sul `cli.mjs` del rilascio (`tools/fork_stack.executed`); che cosa Node stesso avvii non è osservato qui, lo copre la prova.
- Prova di non esecuzione: `tests/test_codebase_map_host_programs.py`, solo su Modal (il suo rapporto avvia Node alla maniera ingenua dentro il progetto trappola, cioè ne esegue i vettori: non si fa su una macchina che non sia usa e getta). Ora scarica il rilascio e il Node di Daodan a ogni giro con `stack_analyser.cli()` e `stack_analyser.node()` (download da github.com e nodejs.org, controllo dello sha256, scompattazione e pubblicazione in una cartella `DAODAN_SHARED_DIR` del test), passa il perimetro di `stack_recognition.perimeter` e lancia `stack_analyser.run`: nulla del percorso del prodotto è sostituito. Il vettore nuovo è un `.env.example` in una cartella viva: un controllo su un progetto a sé mostra che il rilascio lo apre se non gli si dice di lasciarlo, poi nel progetto trappola il file è nel perimetro e non esce nessuna prova di tipo `env`. L'immagine tiene il proprio Node (v24.22.3) e una copia del rilascio, e li usano solo i giri ingenui del rapporto e il controllo dello sha256 dell'archivio. La prova non copre Windows né un rilascio diverso da quello fissato.
- Prova locale: `test_a_forbidden_file_of_a_live_folder_is_not_opened_by_the_real_release` (stesso file), con il rilascio vero e `node` del `PATH` al posto dell'installazione (nessuna rete), senza trappole: un progetto semplice con `web/.env.example` che nomina `ANTHROPIC_API_KEY`, la snapshot vera, `stack_recognition.run`. Passa il file in `ignore`, non esce nessun segno `env` né di `.env.example`, `react` è riconosciuto, e lo stesso rilascio lanciato senza perimetro sulla stessa cartella dà prove `env` per `anthropic`. Gira dove ci sono `DAODAN_STACK_ANALYSER` e `node`, e si salta altrimenti.

### Risultati

Verificato su questa macchina, con il rilascio `.3` vero (release in `DAODAN_STACK_ANALYSER`, `node` v22 del `PATH`, `DAODAN_CONTAINER=off`, niente rete), 24 novembre 2026:

- Il test locale sopra passa. Rosso visto: con `stack_recognition.perimeter` sostituita da una funzione che toglie dall'`ignore` ogni voce `.env*` (lanciando il test con `pytest.main` da uno script a parte), il test fallisce alla prima asserzione, `'web/.env.example' in ()`. Senza perimetro il rilascio dà la prova `env` di `anthropic` per `web/.env.example` (è il controllo del test); con il perimetro non dà nulla.
- Il corpo della prova su Modal, senza i giri ingenui e senza l'installazione (rilascio e Node al posto di `cli()` e `node()`), eseguito su una copia in cartella a parte: passa (il progetto trappola con tutti i vettori e il `.env.example`). L'installazione vera, i giri ingenui e il controllo con il Node di Daodan non sono stati eseguiti: «Non misurato».
- `modal_stack._measure` eseguita una volta qui su `py-fastapi-compose`, su una copia con i percorsi del container cambiati e con Node e rilascio locali, solo per vedere che restituisca `fast_seconds`, `declarations` e `perimeter`: li restituisce. Non è una misura e nessun numero va letto da lì.
- Test di `benchmarks/project-model` che importano ciò che è cambiato (`test_fork_stack.py`, `test_stack.py`, `test_conftest.py`), con un sostituto del modulo `modal` perché il client qui non c'è: passano. `test_modal_catalog.py`, `test_modal_pipeline.py` e `test_modal_runs.py` non si raccolgono senza il client di Modal (mancava prima di questo lavoro).
- Suite locale (`tests/`, `-n 4`, `DAODAN_CONTAINER=off`), non Modal, 24 novembre 2026, Linux: con il rilascio `.5` vero (`DAODAN_STACK_ANALYSER`, `node` v22.23.5 del `PATH`) 4.415 passati, 0 falliti, 140 saltati (lo stesso conteggio con il `.4`); senza il rilascio 4.316 passati, 0 falliti, 239 saltati.

**Giro del piano 2** (conservato come confronto). Rilascio `.2`, sha256 `57dfe8d1b2e37ecb95c331b3f74c8c2aecead59a4ef95835c71a02d5397a9774`, su Modal con `modal_stack_fork.py` (tolto dal repository con le sue misure di confronto: stava in `tools/fork_stack.py`, e si legge nella storia fino al commit `7e1b955`). Per fixture: la snapshot e la pre-mappa con le risposte registrate; poi `technologies.derive` con `service_registry.run` («prima») e con il rilascio («dopo»), dopo un `derive` di riscaldamento che fa il grafo dei moduli; nel «dopo» i fatti della pre-mappa andavano al rilascio come dichiarazioni e le sue prove tornavano come voci del registro. Perso, guadagnato: un nome di `expected.json` (come lo conta `score.score_technologies`, per nome e non per unità) che c'è solo prima, o solo dopo; `new`, `gone`: id di `technologies` solo dopo, solo prima; servizi in più: `extra` del punteggio. Scansione veloce: la pre-mappa senza comandi di modello con ogni riconoscitore da solo, ogni tempo di una chiamata, una misura per fixture. La prova di non esecuzione fu rifatta per `.2` il 22 novembre 2026 con `python tests/modal_pytest.py tests/test_codebase_map_host_programs.py tests/test_codebase_map_stack_analyser.py -q -rw`: 32 test passati, nessuno saltato; il rapporto dice che `node-options` e `planted-node` scattano se il rilascio parte alla maniera ingenua e che gli altri quattro vettori il rilascio non li esegue.

Secondo giro, 22 novembre 2026, codice `9be947a3bbf0c61d` uguale ai due lati, 180 fixture, 178 con record (le altre due: «Senza risposta»); `executed_project_code: no` in 178, `fork_failed` in 0. `model: partial` in 178: alle registrazioni mancano da 1 a 41 comandi per fixture, ai due lati allo stesso modo.

| Faccia | Attesi | Prima | Dopo |
| --- | --- | --- | --- |
| Framework per nome, trovati | 569 | 531 | 533 |
| Framework per unità, trovati (sbagliati) | 1.001 | 834 (70) | 838 (69) |
| Servizi, trovati | 518 | 227 | 228 |
| Servizi in più | | 67 | 86 |

I «prima» non sono quelli della sezione sopra (362 / 568 e 141 / 518): il codice è un altro (`c6be10745cedb94d`) e questo giro non lo spiega.

Servizi in più: da 67 a 86 (in 32 e poi in 36 fixture). Il fork ne aggiunge 22 (`azure` 6, `aws` 4, `google` 3, `gcp` 3, `firebase` 2, e uno ciascuno `microsoft`, `cloudflare`, `vercel`, `apple`) e ne toglie 3 (`okta`, `gcp`, `kafka`). Le 22 sono gli id di `new` che il punteggio conta come servizi; nessuna è un nome atteso.

Nomi persi: 0 (`fixtures_with_lost`), quindi l'elenco delle perdite accettate (`accepted-losses.json`, tolto dal repository) era `[]`. Guadagnati: 3, Meilisearch in `real-stack-koel` (`meilisearch/meilisearch-php`, `composer.json` riga 30: la regola del fork lo elenca, nel registro il pacchetto ha uno spazio in fondo e non combacia mai), Maestro in `real-stack-mattermost-mobile` (i file di flusso in `detox/maestro`, letti dal fork; id non nel registro) e WinUI in `real-stack-peopleinspace` (`UseWinUI` in un `.csproj`, letto dal fork; id non nel registro).

**Primo giro**, 21 novembre 2026, rilascio `.1`, codice `b3719332398056ec` (commit `a2613d8`): 5 nomi persi in 5 fixture (framework 531 → 530, servizi 227 → 226) e 33 coppie di id spariti. Lo zero del secondo viene dopo due correzioni:

- Spring MVC (`jvm-spring-boot-managed`, `real-stack-mall`, `real-svc-robot-shop`): `org.springframework.boot:spring-boot-starter-web` andava solo a Spring Boot (differenza registrata della porta); il proprietario ha deciso di correggerlo nel fork, e `.2` lo dà a Spring Boot e a Spring MVC (`src/rules/framework/spring-mvc.ts`).
- GitHub Pages (`real-app-kotlinconf`) e Gotenberg (`real-stack-documenso`): la traduzione scartava la prova di un file fuori dalla snapshot (`.github/workflows/web-deploy.yml`, `docker/development/Dockerfile.gotenberg`). Corretto in `tools/fork_stack.py` (`22e9b03`), che ha tolto anche altre 22 coppie dagli id spariti (da 33 a 6 con il rilascio): non lette una per una, causa verificata solo per `github.pages` in `real-stack-peopleinspace`.

Id spariti (`gone`): 6 coppie id/fixture in 6 fixture, su 4 id, nessuno un nome atteso; `fast.lost` ha 7 coppie su 5 id (gli stessi quattro e `github.pages`).

- `react-email` (3: `real-app-full-stack-fastapi`, `real-stack-documenso`, `real-stack-epic-stack`; anche nella veloce): il registro ha due id, `react-email` e `reactemail`; il fork uno, `reactemail` (`src/rules/tool/reactEmail.ts`), e la porta rinomina `react-email` in `reactemail`. Tutti i segni tornano sotto `reactemail`, nuovo solo in epic-stack, dove l'unico pacchetto, `@react-email/components`, nel registro era solo di `react-email`.
- `kafka` (1: `real-svc-otel-demo`; anche nella veloce): rinomino della porta in `apache_kafka`, che c'era già prima e la cui regola elenca i tre pacchetti di `kafka` (`src/rules/queue/apacheKafka.ts`); dopo, `apache_kafka` ha tutti i segni per valore e percorso, e il segno di `kafka-clients` che dà il rilascio non ha riga.
- `okta` (1: `real-stack-bookstack`; anche nella veloce): `socialiteproviders/okta` (`composer.json` riga 39) andava a `okta` e a `okta.oauth`; il fork lo dà a `okta.oauth` soltanto, differenza registrata della porta. Il pacchetto resta riconosciuto, e `expected.json` elenca «Okta OAuth». I cinque `OKTA_*` del «prima»: «Menzioni `env`».
- `gcp` (1: `real-stack-nestjs-boilerplate`; anche nella veloce): `google-auth-library` (`package.json` riga 77) andava a `gcp`, ora va a `google` (`src/rules/cloud/google.ts`): differenza registrata della porta. Il pacchetto resta riconosciuto.
- `github.pages` (1: `mix-real-tinyxml2`, solo nella veloce; nella completa nessuno dei due lati lo ha): per esclusione il segno è `docs/_config.yml` (il solo `_config` registrato, nessuna azione di Pages nei workflow). Nella completa go-enry lo marca documentazione e finisce fra gli esclusi, per i due lati (`premap/enry.py`); nella veloce enry non gira e il registro lo prende per `github.pages`, mentre la porta ha tolto `_config.yml` e `_config.yaml` dalla voce (configurazione di Jekyll, non prova di hosting). È l'unico degli id spariti il cui segno dichiarato non passa a un altro id; se valga come prova di Pages, i dati non lo dicono.

Menzioni `env`: il percorso tradotto non produce segni `env`. Nei 10 record letti (sul volume, ridotti a otto segni per voce) il «prima» ha segni `env` in 8 record, da 8 a 20 ciascuno (al minimo), il «dopo» 0 in tutti; per i cinque `OKTA_*` di `real-stack-bookstack` (`app/Config/services.php`, righe 82-88) il record «dopo» non ha né l'id `okta` né un segno `env`. Una menzione senza segno dichiarato non è misurabile: `derive` non porta in `technologies` una voce di sole menzioni. Il percorso tradotto ha i controlli `stack-analyser` e `host`, senza `check_env`; il rilascio legge le variabili solo nei modelli `.env*.example`, `.sample`, `.template` (`src/rules/spec/dotenv/index.ts`), file che la politica di Daodan non legge mai (`source_files.FORBIDDEN_GLOBS`, `.env.*`): li apre comunque e ne scarta la prova fra le `evidence_outside_snapshot`. Conseguenza: un token come `OKTA_CLIENT_ID` in un sorgente è una menzione per il registro (`check_env`) e non è letto dal percorso tradotto; la spec tiene gli host negli URL a `registry_hosts.py` (2.4), toglie `check_env` (2.6) e mette fuori scopo il riconoscere servizi dall'uso nel codice.

Limite trovato, non corretto: `stack_analyser.py` passa `--skip-dirs` e `--ignore` sulla riga di comando, e `fork_stack.perimeter` mette in `ignore` ogni percorso che la pre-mappa esclude, nella completa anche ogni file che go-enry chiama documentazione, binario, generato o vendored. Dalle risposte registrate di go-enry, `real-stack-owncast` ha 760 percorsi esclusi (535 generati, 192 binari, 21 documentazione, 12 vendored) e un `--ignore` di almeno 36.678 caratteri; la seconda fixture, `real-stack-quarkus-super-heroes`, 19.287. Il limite di `CreateProcess` su Windows è 32.767 caratteri per la riga intera: lì la scansione di owncast finirebbe come gap «could not start», senza riconoscimento; su Linux il limite per argomento è più alto, e il giro (`fork_failed` 0) non l'ha incontrato. Nelle 178 fixture `fork_full − fork_fast` cresce con la lunghezza di quella lista (correlazione 0,87; 0,85 con il numero dei percorsi; owncast 13,4 s, il registro 0,7 s): la causa non è stabilita, perché il numero delle dichiarazioni varia con essa e il file dei risultati non lo registrava: `modal_stack.py` ora registra `declarations` e `perimeter`. Il piano 3 passa il perimetro in un file (`--perimeter`), così la lunghezza della riga non conta più; su Windows non è provato («Non misurato»).

Id nuovi (`new`, con i tre guadagnati): 148 coppie in 106 fixture, 30 id, per fixture in `compare.new`; oltre ai servizi in più, `gradle` 26, `maven` 23, `cargo` 17. Rispetto al primo giro compaiono `pnpm` (7), `bunsh`, `nodejs` e un `azure` in più, dalle dichiarazioni che ora restano. Fuori dal registro (`not_in_registry`), in quante fixture: `gradle` 26, `setuptools` 9, `rich` 4, `maestro` 1, `winui` 1, col proprio id per nome e categoria `framework` (`entry_category`).

Gap del fork:

- `declaration_not_sent`: una dichiarazione che la traduzione non manda al rilascio (nessun file, percorso escluso dalla pre-mappa o fuori dal progetto, tipo che il rilascio non prende, nessun nome o fonte). In questo giro 213, tutte nella completa e in 9 fixture; secondo i record del primo giro sul volume la sola causa è il percorso escluso dalla pre-mappa (nuget 141, crates 23, pypi 12, docker 12, github-actions 9, npm 8, maven 7, go 1), e il registro scarta le stesse dichiarazioni senza registrare un gap (`service_registry.run`, `_is_excluded`, riga 241; `tools/fork_stack.py`, riga 98).
- `evidence_outside_snapshot`: in 69 fixture nella completa, 71 nella veloce. Prove che il rilascio legge da solo in file che Daodan non mette nella snapshot (`.dockerignore`, `.env.example`, `artisan`, `bun.lock`, la cartella `.github`; conto e primi cinque percorsi, da 1 a 21 nei 10 record letti), non tecnologie perse. Per i segni di file il registro quei file non li vede nemmeno (`check_files` legge i file della snapshot); le dichiarazioni su un percorso fuori dalla snapshot il registro le tiene, e dopo la correzione anche la traduzione.
- `not_in_registry`: 41 gap in 37 fixture, per scansione, uno per id fuori dal registro.

Tempi in secondi, sulle 178 fixture con record (completa: mediana 0,029 e massimo 5,277 `real-stack-netbox` per il registro, 0,548 e 16,736 `real-stack-owncast` per il fork):

| Scansione veloce | Mediana | Massimo | Più lente |
| --- | --- | --- | --- |
| Registro (`registry_fast`) | 0,013 | 4,972 | `real-stack-netbox` 4,972, `real-stack-plausible` 4,568, `real-stack-owncast` 4,542 |
| Fork (`fork_fast`) | 0,523 | 5,791 | `mix-real-tududi` 5,791, `real-stack-plausible` 5,611, `real-stack-actual` 4,742 |

- `fork_fast`: minimo 0,302 (registro 0,008); 149 fixture su 178 sotto 1 s, 29 da 1 s in su, 16 da 2 s, 10 da 3 s, 6 da 4 s, 2 da 5 s; `py-fastapi-compose`, il progetto di prova della spec, 0,331 (registro 0,011); mediana di `fork_fast` meno `registry_fast`, per fixture, 0,472. In `mix-real-tududi` il registro impiega 3,770.
- Nel primo giro, con lo stesso registro, `registry_fast` aveva mediana 0,013 e massimo 4,544, e `fork_fast` mediana 0,456 e massimo 4,982: fra due giri lo stesso codice si muove, e i tempi del fork si leggono con quella variazione.
- Senza risposta: `real-stack-jellyfin` e `real-stack-kuvasz`, `no answer in 1800 s`; il record dice dove stavano (`snapshot_store._unpack`, da `import_resolution.declaring`). Sono le stesse due senza record nel giro sopra e in `modal_premap.py` (D-302).

### Non misurato

Aspetta Modal (il client non raggiunge Modal da questa macchina: gRPC non passa dalla rete) e chi coordina, dopo la conferma del proprietario. Ogni comando, dalla radice del repository:

- La prova con l'installazione vera, il Node di Daodan e il `.env.example` (i giri ingenui, il controllo del vettore e il perimetro): `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python tests/modal_pytest.py tests/test_codebase_map_host_programs.py tests/test_codebase_map_stack_analyser.py -q -rw`. Il test scarica da github.com e da nodejs.org: se la rete del container non li raggiunge, fallisce con la causa. Non si sa ancora se `cli()` e `node()` veri passino con i file veri.
- La suite intera: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python tests/modal_pytest.py --shards 32 -q -n 2`.
- Il riferimento sul `develop` di oggi, `68b784e` (punto 7 di «Che cosa il piano 2 ha trovato» nel piano 3): non è stato rimisurato, e i «prima» di ogni confronto vengono dal giro del piano 2 (codice `9be947a3bbf0c61d`), non da `develop`. Con un worktree a parte, che ha ancora `modal_stack_fork.py`: `git worktree add ../daodan-68b784e 68b784e`, e lì `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal deploy benchmarks/project-model/modal_stack_fork.py`, poi `… python benchmarks/project-model/modal_stack_fork.py spawn` e `fetch`. Dà `registry_full` e `registry_fast` e i punteggi «prima» del registro sul codice di quel commit (il driver di quel commit non è stato rilanciato per questo lavoro).
- Il giro sul corpus dopo il passaggio: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal deploy benchmarks/project-model/modal_stack.py`, poi `… python benchmarks/project-model/modal_stack.py spawn` e `… python benchmarks/project-model/modal_stack.py fetch`, che riscrive `results/daodan_stack.json`; il `fetch` importa i moduli di `daodan/core`, quindi chiede un Python con le dipendenze del repository (`--with` per ciò che manca). Va rifatto se cambia il rilascio fissato: per il `.4` si cambiano i tre posti e si rilancia.
- Il tempo della scansione veloce (`fast_seconds`), `declarations` e `perimeter` sul corpus: escono dallo stesso giro. Nessuno è misurato; il confronto con `fork_fast` del piano 2 non è uno a uno (vedi «Parametri»).
- Windows: il file del perimetro (`--perimeter`) su una riga di comando che prima superava i 32.767 caratteri, l'avvio di Node e un `node.bat` piantato non sono provati con una esecuzione vera.
- La prima esecuzione su una macchina con la cache di compilazione di Node fredda: fuori da ogni tempo per costruzione. Le due fixture senza risposta nel giro del piano 2 (178 su 180); la variazione fra due giri; il tempo sotto `project_lock` e con il resto del server in funzione.
- Di quali tecnologie siano le prove scartate da `evidence_outside_snapshot` e quante menzioni `env` si perdono (il prodotto non tiene più le menzioni, scelta 2 del piano 3): `compare` contava id e nomi, non segni.
- I record completi di ogni fixture stanno sul volume Modal: `project-model/stack/<fixture>.json` (il giro nuovo) e `project-model/stack-fork/<fixture>.json` (il piano 2); il file committato ha punteggi e tempi.

### Verdetto

Una riga per ogni voce della «Verifica» della spec. Nessuna è provata sul prodotto sul corpus: il giro non c'è.

- «Nessuna perdita»: verificata il 27 novembre 2026 da `test_stack_losses.py` su Modal (`ap-lnlOs8lng0g3NjOaHADTZh`): per ogni fixture di `daodan_stack.json` e di `daodan_stack_fork_develop_68b784e.json`, nessun nome atteso di `score.frameworks_by_name.missed` o `score.services.missed` manca solo nel giro nuovo. 0 perdite su 180 fixture; le sei del 26 novembre senza un «prima» (`real-auth0-go`, `real-bank-of-anthos`, `real-microblog`, `real-next-subscriptions`, `real-stack-polar`, `real-sveltekit-realworld`) sono fuori, nominate nel test. Perdite accettate: nessuna.
- «Scansione veloce»: la regola (il risultato della fonte modificata cambia, quelli delle fonti non eseguite restano e dicono da quale scansione vengono) è provata da `test_a_fast_scan_keeps_the_signs_of_the_sources_it_did_not_run` e `test_a_kept_sign_leaves_with_its_file` in `tests/test_codebase_map_stack_sources.py`, che passano qui con un riconoscitore scritto a mano (provano la fusione, non il rilascio).
- «Senza Node»: `test_without_the_tool_the_previous_signs_stay_and_a_gap_says_why` (stesso file), che passa qui con lo stesso riconoscitore a mano; `test_an_install_that_failed_is_not_tried_again_in_the_same_process` in `tests/test_codebase_map_stack_analyser.py` per l'installazione che non si ritenta. Non provate con un Node assente vero.
- «Tempo»: mediana di `fast_seconds` 0,454 s sul giro del 27 novembre 2026 (`corpus` `45984925255`), contro 0,523 s di `614c940`; nessuna soglia. L'obiettivo della spec (meno di un secondo su `py-fastapi-compose`) resta da verificare lì; la soglia è del proprietario.
- «Nessun codice eseguito»: la prova, riscritta per l'installazione vera e il `.env.example`, non è stata eseguita su Modal. Qui gira, con il rilascio vero, il solo vettore `.env.example` (il test locale). Che nessun vettore scatti con l'installazione vera e il Node di Daodan è da provare.
- Tornano al proprietario, dal giro del piano 2: i tempi; i servizi in più (da 67 a 86: 22 aggiunti, 3 tolti); le tre differenze della porta che spostano un id senza cambiare nessun nome atteso (`okta`, `gcp`, `_config.yml` di Jekyll); le menzioni `env`, che il piano 3 non tiene; ciò che «Non misurato» non copre.

## Esplorazione dell'app avviata

Passo 11 del [piano degli ingressi](../../docs/plans/2026-11-20-ingressi-e-flussi.md): Daodan avvia l'app dichiarata nel container, apre un browser senza interfaccia, legge i controlli di ogni pagina dall'albero di accessibilità di Playwright, ne preme ognuno una volta e registra le funzioni del progetto che partono (copertura V8 fra due letture, meno ciò che la pagina ferma esegue da sola).

### Parametri

- Script: `modal_explore.py` (`DAODAN_FOLDER=<cartella> modal run benchmarks/project-model/modal_explore.py::explore_main --source <cartella del volume | folder> --out <file>`). `--source folder` prende la cartella di `DAODAN_FOLDER`. La corsa è la pipeline intera (`pipeline.run`: scan, stack, analyze, dynamic, union) su un solo snapshot, come la lancia `run_folder`: il passo dinamico avvia ed esplora l'app, e la base di confronto è lo stesso snapshot con `observed-controls.json` messo da parte (candidati, collegamenti e schede senza i controlli). Un confronto con un'analisi fatta prima, su un'altra sorgente, dava un risultato falso (117 ingressi statici invece di 823, e «13 ingressi in più» che non esistono): non vale come base.
- Potenza di Modal: le funzioni della misura 2–16 core e 4–32 GB, le sandbox 8 core, la suite di test su 16 core con `-n 16`.
- Sorgenti: `premap/npm_start.py` (`starts`, `builds`), `dynamic/app.py` e `app.cjs` (avvio, porta, arresto), `dynamic/explore.cjs` (esplorazione), `observed_entries.py` (candidati con fonte `observed`).
- Tetti di `explore.cjs`: 25 pagine, 300 pressioni, 900 s, 3 s per il click, 3 livelli di profondità, 4 schede in parallelo. I controlli che un click rivela (un menu, una finestra) hanno un budget a parte di 100 pressioni e al più 30 per click (oltre, la lacuna `explore_cap` con `revealed_per_press` dice quanti ne restano e dopo quale click), e non si cercano dopo un collegamento: un collegamento naviga o scorre, non apre. Ogni controllo si preme dopo aver ricaricato la pagina in un contesto pulito e dopo i click che lo mostrano; la lettura dei controlli aspetta che l'elenco resti fermo per un secondo (fino a 3 s). Le pressioni sono indipendenti (ognuna parte da una prima visita), quindi le schede le prendono dalla stessa lista: cambiano il tempo, non l'esito, e un test su Modal confronta 1 e 4 schede su una fixture (stati, gestori, funzioni, richieste e ordine). Vale per un'app senza stato su un server: con un backend raggiungibile, quattro schede corrono sullo stesso stato e l'esito può cambiare (detto fra i limiti dichiarati di `explore.cjs`). Una casella o un bottone di opzione che si preme non si spunta prima: il campo compilato è un altro.
- Moduli (una proposta, non una decisione: la spec lascia aperti i dati di prova): prima di premere un pulsante dentro un modulo, `explore.cjs` compila i campi di quel modulo con un valore per tipo HTML (`email`, `password`, `url`, `tel`, le date; `test` per un testo; il primo valore di una `select`; una casella si spunta) e legge `checkValidity()`: un campo che il browser rifiuta (un `pattern`, un `max`) è detto in `invalid` e il modulo non si forza. Il punto di interruzione è sul `click` e sul `submit`, e la ripetizione di un percorso che ha mostrato dei controlli compila di nuovo il modulo. Un campo fuori da un modulo non si compila (`needs_value`). Non si indovinano credenziali.
- Un controllo è un candidato `observed` se la pressione ha fatto partire una funzione del progetto o ha inviato una richiesta, e nessun candidato statico ha la stessa etichetta e lo stesso evento (una riga che il lettore statico ha scartato, su un componente o con una proprietà data a un figlio, non lo tiene). È l'elenco dei candidati; i collegamenti uniscono per funzione, sotto.
- Nella pipeline: `dynamic.run` lancia l'esplorazione dopo i test (`dynamic/app.py`, `explore`), con la sua cartella `dynamic-runs/app`, e la riusa sulla stessa istantanea, lo stesso piano e gli stessi driver; scrive `observed-controls.json` accanto al manifest. Senza app dichiarata, senza motore o con un'app che non parte è una lacuna con la causa (`no_start_command`, `build_failed`, `app_not_started`, `explore_failed`).
- Dai controlli agli ingressi dei collegamenti: `flows.link_facts` prende i controlli premuti (`_observed_entries`) con il gestore isolato. Il gestore è la funzione che comincia dove il browser dice (`callFrame.functionLocation`), non la riga dove si ferma, che è il suo primo enunciato e può stare in una funzione di richiamo annidata. Una freccia in linea è un nodo suo, attivato dalla funzione che la contiene; un gestore con nome è il suo nodo. Un gestore da cui il lettore statico parte già non si duplica, e un gestore è un solo ingresso; un candidato statico con lo stesso nome ma un'altra funzione non lo nasconde. Un gestore che nessuna funzione dello snapshot spiega è una lacuna al luogo dove il browser si è fermato.
- Semi: le pagine che Next.js dichiara (`next typegen`, `AppPageConfig`) sotto la cartella dell'app, senza i modelli (`/[id]`).
- Confronta gli ingressi con il controllo iniziale dei flussi di un riferimento (`entries_vs_reference.py <riferimento.json> <risultato.json>`; il riferimento si passa come argomento e non sta nel repository). Un controllo citato (`file:riga`) è coperto dal lettore statico se un suo ingresso sta a non più di 2 righe o se la citazione cade nelle righe della funzione da cui parte; dal browser se cade nelle righe di un gestore che ha eseguito, o a non più di 2 righe da dove il codice lo nomina (`onSubmit={handleSubmit}`). Le due parti si leggono con la stessa regola. Non misura i flussi interi.

### Soluzioni pronte valutate

- Usate: l'albero di accessibilità di Playwright (`ariaSnapshotJSON`, `getByRef`) per i controlli; il protocollo ufficiale di Chrome per il gestore (`DOMDebugger.setEventListenerBreakpoint` sul `click` e sul `submit`, con `Debugger.setBlackboxPatterns`) e per la copertura (`Profiler.takePreciseCoverage`); `SourceMap` di Node per le mappe dei sorgenti.
- L'idea dell'esplorazione a stati (Crawljax, WebExplor; studio di giugno 2026, arXiv 2606.16650): rileggere i controlli dopo ogni pressione. Non è una libreria da usare così com'è: qui ogni controllo si preme una volta, con un tetto.
- `@duckduckgo/autoconsent` (MPL-2.0) per i banner dei cookie: non usato, copre solo i fornitori con regole e non un banner scritto dall'app; i suoi pulsanti sono controlli come gli altri.

### Non fatto, deciso

- Premere solo i controlli senza la prova della stessa terna elemento, evento e stato (proposta della seconda revisione): si preme ogni controllo una volta, perché la pressione dà la prova che manca anche ai controlli che il lettore statico ha.

### Non misurato

- Un progetto con un backend raggiungibile: l'esecuzione non ha rete, e un'app con accesso mostra solo la schermata di accesso, senza credenziali di prova per entrare.
- Il motore di Daodan su Windows (Kiri in WSL, `container.own_engine`): la prova col motore vero sotto è su Linux con Docker.
- I flussi interi del riferimento: solo il loro controllo iniziale si confronta (`entries_vs_reference.py`); i passi che seguono non sono misurati.
- Un modulo che chiede un valore che nessun tipo HTML dice (un codice, un identificativo, un `pattern` stretto): resta `invalid` e non si invia; le credenziali non si indovinano. I campi fuori da un modulo non si compilano.
- pnpm, Yarn e Bun: `start_runner_not_supported`, non eseguiti.

### Col motore container vero

`modal_engine.py` avvia un demone Docker (rete normale) in una VM Sandbox di Modal e lancia `dynamic.app.observe` con `container.find_engine()`, cioè `container.run_in_container` di Daodan e non il sostituto `sandbox_run` di Modal: preparazione con i registri, `keep_root` per il browser, esecuzione senza rete, uscite riportate. Fixture: `explore-fixtures/vite-react` (la stessa del test). Risultato, `results/explore/engine.json`: motore `docker`, app `ready` su 5173, 2 controlli premuti, nessuna lacuna, 42,6 s; Save → `validate` e `save`, Reset → `reset`, con file e riga di `src/lib/actions.ts`.

## Eventi fra la pagina e il guscio Tauri

Task 11b del [piano degli ingressi](../../docs/plans/2026-11-20-ingressi-e-flussi.md). Un `emit` da una parte e un `listen` dall'altra, dello stesso nome, sono un legame con le due posizioni (`resolver` `tauri-event`, il nome come `event`), come `invoke` lo è con il comando Rust (`flows.link_facts`; lettura in `languages/semantic.py`; prova: `tests/test_codebase_map_tauri_events.py`, 7 test).

### Parametri

- Che cosa prova la chiamata: nella pagina l'import di `listen`, `once`, `emit` o `emitTo` da `@tauri-apps/api/event` (non ombreggiato da un nome locale, anche come `event.listen` con un import namespace); in Rust l'import del tratto `tauri::Emitter` (`emit`, `emit_str`, `emit_to`, `emit_str_to`, `emit_filter`, `emit_str_filter`) o `tauri::Listener` (`listen`, `once`, `listen_any`, `once_any`) nello stesso file, anche `as _`. Le firme sono quelle del `.d.ts` di `@tauri-apps/api@2` e della documentazione di `tauri` 2.12.7 (la posizione del nome: la prima, la seconda per `emitTo`, `emit_to`, `emit_str_to`).
- Una coppia è fra Rust e pagina e ogni coppia è un legame: più ascoltatori dello stesso nome sono normali. Un nome che non è un letterale è una lacuna con il punto. Un ascoltatore con funzione nominata finisce su di lei; una chiusura finisce sulla funzione che contiene il `listen`.
- Soluzione pronta valutata: `tauri-specta` tipizza gli eventi di un progetto che lo adotta, e non lo si presume; Tauri non ha uno strumento che elenchi gli eventi. Si legge dall'albero.

### Risultati

- Nessun progetto del corpus usa gli eventi di Tauri (cercati nelle sorgenti dei benchmark): la prova sono le fixture dei test, sintetiche. Eventi trovati, coppie e lacune su un progetto reale: non misurati.
- Nei test: emit in Rust e listen nella pagina (e il contrario), nomi diversi (nessun legame), un emit con due ascoltatori (due legami), un nome calcolato (lacuna con il punto), l'`emit` di un `EventEmitter` di Node, di un modulo del progetto e di un tipo Rust senza il tratto (nessun legame), e un evento fra due file della pagina (nessun legame). Suite intera su Modal in 32 container: 3929 passati.

### Non letto

- I metodi sugli oggetti finestra della pagina (`getCurrentWindow().listen`, `getCurrentWebviewWindow().emit`) e Tauri 1 (`emit_all`, `listen_global`, `Window::emit`): non c'è un import o un tratto che li provi.
- Un tipo del progetto con un `emit` suo in un file che importa il tratto di Tauri sarebbe letto (`shortcut:` in `semantic.py`: la proprietà del ricevitore è del motore).
- `use tauri::prelude::*` e ogni `use` con un carattere jolly: non provano il tratto.
- I nomi degli eventi di Tauri (`TauriEvent.*`): un nome non letterale, quindi una lacuna.

## Tre corse sullo stesso progetto, 24 novembre 2026 (task 2b del piano dell'analisi unificata)

Domanda: quanto costa una corsa della pipeline da zero, quanto senza modifiche e quanto dopo la modifica di un solo modulo, e quanti dei collegamenti attesi ritrova ognuna. Serve prima di decidere le regole della sezione 7.3 della spec.

### Parametri

- Fixture `fixtures/mix-poly-firebase`, sintetica: una pagina React con due pulsanti, un guscio Tauri con un comando nativo, funzioni Python di un backend, un modulo Android in Kotlin.
- `modal_runs.py`: una funzione Modal esegue `pipeline.run` tre volte di seguito sullo stesso progetto e sulla stessa cartella dello snapshot. Da zero; senza modifiche; dopo una riga aggiunta a `react-app/src/checkout.ts`, con lo snapshot riscritto sul vecchio (`snapshot.write_snapshot(..., previous=...)`, dopo `reset_pass`, come il rinnovo di una run di lavoro).
- Tempi, ripristini, avvii di indicizzatori e dell'app dagli eventi della pipeline e dai registri dei container (`score.py runs` in `benchmarks/system-map`). Collegamenti attesi (`EXPECTED`, scritti da una persona): il pulsante «Buy» al suo gestore, il pulsante «Receipt» al suo gestore, il gestore della ricevuta al comando nativo `save_receipt`, il gestore del pagamento alla funzione Python `create_checkout_session`.
- Su Modal i container sono Sandbox che non condividono volumi: ogni passo ripristina le dipendenze per sé, come prima del ripristino condiviso del task 1b. Questa è la base; il guadagno del ripristino condiviso non si misura qui, ma con un motore vero. CPU, picco di memoria e spazio temporaneo sono delle sandbox e nessun evento li porta: non misurati.

### Risultati

`results/runs/three-runs-2/`, una corsa di ogni tipo (nessuna ripetizione: la varianza fra corse non è misurata).

| Corsa | Secondi | Ripristini e preparazioni | Indicizzatori avviati | Avvii dell'app | Collegamenti attesi |
| --- | --- | --- | --- | --- | --- |
| Da zero | 525,6 | 10 (2 `node-restore`, 8 `prepare`) | 5 | 1 | 3 su 4 |
| Senza modifiche | 82,9 | 1 | 1 | 1 (riusata) | 3 su 4 |
| Un modulo cambiato | 501,1 | 10 | 5 | 1 | 3 su 4 |

Secondi per passo, da zero e dopo la modifica: scan 210,5 e 224,0; analyze 222,9 e 192,1; dynamic 92,0 e 84,9.

- Un solo modulo cambiato costa il 95% di una corsa da zero: la pre-mappa si rifà intera, e ripartono tutti e cinque gli indicizzatori (fogli di stile, scip-python, scip-typescript, scip-kotlin, scip-rust), non solo quello del linguaggio del file. Lo spiega `engine_pass.pass_plan`: un archivio degli archi legato a un altro snapshot non dà nessun linguaggio fresco.
- Senza modifiche ripartono solo gli indicizzatori che non hanno riuscito: Kotlin fallisce (la build Android di un progetto sintetico) e viene ritentato a ogni corsa, 72 dei 83 secondi. Gli altri quattro dicono «già freschi»; l'esplorazione dell'app è riusata.
- Il collegamento «il gestore del pagamento chiama la funzione Python» manca in tutte e tre le corse (i tre altri si trovano sempre): il gestore chiama il backend con `httpsCallable` di Firebase e nessun legame lo unisce alla funzione.
- Nessuna corsa che costa meno ritrova meno collegamenti: la corsa senza modifiche costa un sesto e ne ritrova tanti quanti la prima.

### Non misurato

- Il guadagno del ripristino condiviso (task 1b): serve un motore Docker vero in una VM Sandbox, non le sandbox di `sandbox_run`.
- CPU, picco di memoria, spazio temporaneo; la varianza fra due corse dello stesso tipo; un progetto con un frontend più grande di due pulsanti.
- Il rinnovo come lo fa la run di lavoro dell'app (`snapshot.py`, il percorso con `compare_files`): qui l'ho riprodotto con le stesse chiamate, non con la funzione stessa.

## Il costo di `scan` sul corpus, 24 novembre 2026 (8.10 della spec della pipeline)

Domande: quanti file la lettura di oggi legge e `scan` poi esclude, per motivo (8.3 punto 3, 8.11 passo 5 pezzo E1); quanto pesa la doppia lettura dei byte (8.6 punto 6); quanto costa in `scan` l'albero di ogni file TypeScript di un progetto Angular (8.11 passo 5 pezzo D); che linguaggio dà go-enry a ogni file, contro quello dell'inventario (8.3 punto 2); e il motivo `submodule` accanto agli altri.

### Parametri

- `modal_scan_cost.py`, su Modal. Una funzione per ogni progetto real; le 122 miniature a gruppi di 8 (`--chunk`). Macchina: 4 core e 16 GB, richiesta uguale al limite (`CPU`, `MEMORY`); dentro la sandbox la CPU si legge «unknown» e `os.cpu_count()` dà 4; Python 3.13.3. Codice di Daodan: un clone pulito di `68b784ee7` (`DAODAN_SCRIPTS`); HEAD all'avvio era `03161c8a6`, e `daodan/` è lo stesso (nessun commit in mezzo lo tocca).
- Nessun codice dei progetti gira: si leggono file. La pre-mappa è quella registrata (`results/premap-runs`, `tools/premap_replay.py`: `replayer`, `real_project`), quindi **nessun numero qui contiene il tempo del container**. Le registrazioni sono del 15-17 novembre e a tutti i 178 progetti manca almeno un comando di oggi (`noir` in tutti; poi `daodan-dockerfile` 103, `dotnet` 85, `renovate` 54, `gradle` 16, `cmake` 14, `make` 13, `next` 12, `maven` 9, `nuxt` 9, `angular` 8, `meson` 4, `sveltekit`, `react-router` e `bazel` 2, `sbt` e `astro` 1: i comandi, non i progetti): la `read` di quella sorgente riceve un errore. Le esclusioni vengono da go-enry e da `.gitmodules` (letto); il comando di go-enry è registrato in tutti i 178, e `.gitmodules` si legge, senza comando. Senza registrazione, quindi senza esclusioni note: `real-stack-jellyfin` e `real-stack-kuvasz` (solo misura B e ritmo di C). La prima chiamata li ha lasciati fuori (un container ha superato i 7.200 s, poi il client ha perso la rete): rifatti con `--resume --reps 1` e `TIMEOUT` di 4 ore: `real-stack-kuvasz` ha **una ripetizione, non tre** (3.392 s); `real-stack-jellyfin` non è finito dopo oltre due ore e l'ho fermato, quindi non è nel JSON (179 progetti su 180).
- **A.** `snapshot.write_snapshot` (legge tutto, senza pre-mappa), `premap.write` con la riproduzione, la funzione `excluded` di `modal_scan_cost.py` (era `pipeline.plan.excluded`, tolta dal prodotto il 24 novembre: la lettura non esclude più nulla). «Letto da un parser»: stato `parsed` o `parse-error`. Simboli dalla tabella `symbols` dello store. Import: `snapshot.resolved_imports(store)`, coppie distinte (importatore, bersaglio) da un file che resta a uno escluso. Il controllo di allora sulla lettura (`reading_leaves_out`) non si rifà più: il prodotto non esclude file. Resta nel JSON registrato.
- **B.** Sui real, tre ripetizioni di seguito, ognuna: `file_inventory.write`, `snapshot.write_reading`, `snapshot.build_manifest` (il passaggio solo; tolto dal prodotto il 24 novembre: la misura non si rifà, i numeri sono della corsa registrata). Dentro la lettura, avvolti `snapshot._read_source` (stat e byte di ogni file: quelli che l'inventario ha già letto) e `_SnapshotPass.seal` (legame dello store semantico e pubblicazione). Mediana per progetto, poi somma. **La cache del disco è calda** a ogni lettura: l'archivio è appena estratto e ogni passo segue un altro che ha letto gli stessi file, come nell'uso vero.
- **C.** `premap.angular.commands` su un `Context` nuovo (nessun testo in cache), con `premap.angular._components` (chi legge l'albero di un file) contato; la regola di prima del pezzo D (`648efd2b7`): i file `typescript` che importano `Component` da `@angular/core`, dalle intestazioni dello snapshot letto. Il ritmo: `_components` su ogni file `typescript` di ogni progetto, un file alla volta.

`code.differs` del JSON elenca tre percorsi: due file di `fixtures/mix-edge-vendored/node_modules/left-pad`, che git traccia e `git add -A` ignora, e `modal_pipeline.py`, che ha lo stesso contenuto di HEAD (blob `90381c557`): `modal_pipeline.code` dà elenchi diversi in chiamate successive senza che un file cambi, quindi la riga non prova una modifica.

- **D.** Modalità `--languages`, che non rifà A-C: per ogni progetto con la risposta registrata di `daodan-enry .`, `file_inventory.write` (il linguaggio dell'inventario, `detect_language`) contro il `language` di ogni riga di go-enry (senza le cartelle con il punto, come `premap.enry.read`). Solo i file dell'inventario. La tabella dei nomi che il codice ha è `premap.suffix_table.NAMES` (nome di Daodan → nome di Linguist, 16 nomi) con `premap.ALSO` (TSX): la usano `premap._unlisted` e `indexed_by`. Non dice `markup`, né che `css` copre Sass e Less: la mappa minima `FAMILIES` del benchmark (non in `daodan/`) aggiunge i nomi di `css` e `markup` dalla tabella delle estensioni di Daodan, e JSX a `javascript`; la tabella usata è `equivalents` del JSON. Tutti i 17 linguaggi di Daodan hanno un parser (`languages.SUPPORTED_LANGUAGES`): «Daodan legge quel nome» vuol dire che il nome è in quella tabella.
- **E.** Nella stessa modalità, le voci della faccetta `excluded` (`premap.enry.read`, poi `premap.gitmodules.run`, nell'ordine della pre-mappa) e i file dell'inventario che ognuna tiene (la stessa funzione), per motivo.

Comando (clone pulito di HEAD in `<clone>`), risultato in `results/scan-cost/scan-cost.json` (solo conteggi e tempi):

    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 DAODAN_SCRIPTS=<clone>/daodan/core \
      uv run --no-project --with modal python -m modal run benchmarks/project-model/modal_scan_cost.py

`--cases a,b` sceglie i progetti, `--resume` aggiunge a un JSON che c'è quelli che mancano; `--languages` fa solo D ed E e scrive `results/scan-cost/languages.json` (un minuto, 180 progetti). Il test della parte pura: `uv run --no-project --with modal --with pytest python -m pytest benchmarks/project-model/test_modal_scan_cost.py`.

### Risultati

**A. Quello che la lettura legge e `scan` esclude.** 122 miniature (806 file, 388 letti da un parser) e 56 real (46.737 file, 33.190 letti da un parser).

| Corpus | Motivo | Progetti | File esclusi | Letti da un parser | KB | Simboli | Import dai file che restano |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| miniature | `vendored` | 9 | 12 | 10 | 13 | 8 | 0 |
| miniature | `generated` | 10 | 12 | 6 | 13 | 15 | 1 |
| miniature | `documentation` | 4 | 6 | 1 | 0 | 0 | 0 |
| miniature | `submodule` | 0 | 0 | 0 | 0 | 0 | 0 |
| miniature | totale | 122 | 30 | 17 | 27 | 23 | 1 |
| real | `documentation` | 56 | 1.746 | 438 | 16.386 | 1.498 | 24 (23 file) |
| real | `generated` | 32 | 774 | 717 | 43.842 | 9.543 | 10 (10) |
| real | `vendored` | 43 | 462 | 339 | 8.767 | 8.838 | 60 (58) |
| real | `binary` | 2 | 2 | 2 | 729 | 4 | 2 (2) |
| real | `submodule` | 0 | 0 | 0 | 0 | 0 | 0 |
| real | totale | 56 | 2.984 | 1.496 | 69.724 | 19.883 | 96 (93) |

I file che oggi un parser legge e `scan` esclude sono il 4,4% dei letti nelle miniature e il 4,5% nei real. Nessuno dei 56 real è senza file esclusi; 40 ne hanno di letti da un parser. Gli import nell'altro verso (da un file escluso a uno che resta) sono 231 nei real: `vendored` 113, `documentation` 93, `generated` 24, `binary` 1; chi non legge i file esclusi perde quegli archi.

I progetti con più file esclusi letti da un parser:

| Progetto | File letti | Di cui da un parser | Esclusi | Esclusi letti da un parser | Simboli degli esclusi | Import verso gli esclusi | Motivi (file) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `real-stack-owncast` | 1.726 | 1.584 | 562 | 527 | 1.456 | 0 | `generated` 533, `documentation` 24, `vendored` 4, `binary` 1 |
| `real-stack-ardalis-cleanarchitecture` | 471 | 373 | 260 | 201 | 525 | 0 | `documentation` 253, `generated` 5, `vendored` 2 |
| `mix-real-tinyxml2` | 212 | 193 | 193 | 188 | 367 | 0 | `documentation` 167, `generated` 25, `vendored` 1 |
| `real-stack-mattermost-mobile` | 3.900 | 3.467 | 96 | 76 | 418 | 9 | `vendored` 73, `documentation` 20, `generated` 3 |
| `real-app-hoppscotch` | 2.244 | 1.740 | 95 | 70 | 389 | 2 | `documentation` 47, `vendored` 45, `generated` 3 |
| `real-stack-ctfd` | 791 | 751 | 82 | 63 | 3.401 | 45 | `generated` 51, `vendored` 21, `documentation` 10 |
| `real-stack-bookstack` | 2.373 | 417 | 70 | 57 | 867 | 1 | `vendored` 48, `generated` 16, `documentation` 6 |
| `real-app-memos` | 1.328 | 1.210 | 82 | 50 | 3.634 | 2 | `generated` 43, `documentation` 27, `vendored` 11, `binary` 1 |

Alcuni di quei file sono codice del progetto, non di terzi né generato. Percorsi letti con una corsa a parte (stesso codice, stesse registrazioni, dieci progetti: non sono nel JSON):

- `vendored`: `CTFd/cache/__init__.py` in `real-stack-ctfd` (la cartella `cache/`), importato da 45 file che restano (`CTFd/__init__.py`, `CTFd/api/v1/awards.py`, ...); `…/tauri-plugin-appload/src/cache/mod.rs` in `real-app-hoppscotch`, importato da `config/model.rs` e `uri/handler.rs`; `types/api/posts.d.ts` e `types/api/apps.d.ts` in `real-stack-mattermost-mobile` (le dichiarazioni dei tipi del progetto).
- `documentation`: `app/constants/license.ts` e `app/actions/remote/license.ts` in `real-stack-mattermost-mobile`, importati da `app/constants/index.ts` e `app/screens/settings/about/about.tsx`; i componenti Vue di `packages/hoppscotch-common/src/components/collections/documentation/` (`MarkdownEditor.vue`, `Preview.vue`, ...); `sample/src/NimblePros.SampleToDo.Web/Projects/List.cs` in `real-stack-ardalis-cleanarchitecture`, uno dei 194 file letti di `sample/src` e `sample/tests`; `examples/gzlog.c` e altri 11 file C di `mix-real-zlib`.
- `binary`: `web/src/components/MemoEditor/view/useSearchMatchHighlight.ts` in `real-app-memos`, un file di testo, importato da `MemoContentView.tsx` e da un test.
- `generated`: `assets/js/dashboard/stats/modals/rocket-icon.js` in `real-stack-plausible`, importato da tre `.tsx`; `resources/js/wysiwyg-tinymce/icons.js` in `real-stack-bookstack`, importato da `config.js`.

Nei dieci progetti guardati il resto dei file più grandi è di terzi o generato davvero: `public/libs/tinymce` in BookStack, i `fontawesome` di Quarkus Super Heroes, i bundle di `CTFd/themes`, i `Designer.cs` delle migrazioni di OpenBudgeteer, `proto/gen/**/*.pb.go` di Memos (695 simboli in `user_service.pb.go`: codice generato, che il progetto compila).

**B. La doppia lettura.** Somma delle mediane su 56 real, secondi.

| Progetti | File | Inventario | Lettura | di cui `seal` | Passaggio solo | Byte riletti nella lettura | Quota riletta (su inventario + lettura) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 56 | 46.737 | 33,5 | 1.936,6 | 1.358,2 | 397,8 | 10,5 s (366 MB) | 0,5% |

I cinque progetti (di quelli con tre ripetizioni) che impiegano di più, mediana:

| Progetto | File | MB | Inventario | Lettura | di cui `seal` | Passaggio solo | Byte riletti | Quota |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `real-stack-owncast` | 1.726 | 52,5 | 1,57 | 396,43 | 220,63 | 123,64 | 0,53 | 0,1% |
| `real-app-kotlinconf` | 607 | 1,7 | 0,36 | 163,01 | 160,85 | 1,60 | 0,12 | 0,1% |
| `real-stack-mattermost-mobile` | 3.900 | 26,1 | 2,84 | 158,23 | 118,51 | 28,15 | 1,03 | 0,6% |
| `real-stack-ctfd` | 791 | 14,5 | 0,65 | 146,29 | 94,73 | 25,23 | 0,20 | 0,1% |
| `real-stack-openbudgeteer` | 368 | 1,8 | 0,26 | 94,26 | 90,43 | 2,77 | 0,08 | 0,1% |

- Rileggere i byte costa lo 0,5% di inventario più lettura: 10,5 s contro i 33,5 dell'inventario che li ha letti la prima volta. Per progetto la quota va dallo 0,07% (`real-app-kotlinconf`) al 5,6% (`real-stack-wallabag`), mediana 1,0%. Con la cache calda la seconda lettura non pesa: l'inventario non ha bisogno di passare i byte a `parse`.
- Osservazione, non una misura chiesta: nei 56 progetti `seal` è il 63% di mediana del tempo di `write_reading` (dal 51% di `real-stack-bakerydemo` al 99% di `real-app-kotlinconf`) e `write_reading` dura 3,9 volte il passaggio solo di mediana (da 2,3 a 102). `real-stack-kuvasz` (una ripetizione, 1.601 file, 12,2 MB, senza registrazione) ha inventario 1,85 s, lettura 3.358,12 s, di cui `seal` 3.312,92 (98,7%, 2,4 volte i 1.358 s dei 56 messi insieme), passaggio solo 30,17 s, byte riletti 0,69 s (0,02%); nel suo log `sqlglot` segnala sintassi SQL non supportata in molti file, ma non l'ho scomposto. Il costo della lettura non sta nei byte.
- Il passaggio solo non è un termine di confronto pulito: costruisce un dizionario, non scrive uno store né il suo livello semantico, e legge con un gruppo di thread (fino a 8).
- Rumore: fra le tre ripetizioni la lettura più lunga è, di mediana, 1,12 volte la più corta; il massimo è 3,7 (`real-stack-fiber-go-template`).

**C. Angular in `scan`.** Quattro progetti dichiarano `@angular/core` o `@angular/compiler`. Secondi con il solo costo dei file (sorgente `angular` e pre-mappa con i comandi del container risposti dalla registrazione).

| Progetto | File TypeScript | Alberi letti prima | Alberi letti ora | `commands` | Stima con la regola di prima | Sorgente `angular` | Pre-mappa |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `js-angular` | 4 | 2 | 4 | 0,001 | 0,0004 | 0,059 | 0,105 |
| `real-app-jhipster-sample` | 288 | 59 | 288 | 0,234 | 0,050 | 0,458 | 2,56 |
| `real-stack-jasontaylor-cleanarchitecture` | 24 | 10 | 24 | 0,012 | 0,005 | 0,073 | 1,84 |
| `real-stack-paperless-ngx` | 446 | 124 | 446 | 0,549 | 0,172 | 1,009 | 4,48 |

- Oggi `scan` legge da 2,0 a 4,9 volte gli alberi di prima, e il costo in più è sotto il secondo nel corpus: `commands` meno la somma dei secondi di `_components` sui soli file di prima fa da 0,0006 a 0,38 s. La sorgente `angular` è il 4% (jasontaylor), il 18% (jhipster), il 23% (paperless) e il 56% (la miniatura) dei secondi della pre-mappa riprodotta.
- Gli alberi sono letti due volte per pre-mappa (`commands` e `read` chiamano `_plan`; i testi restano in cache): 8, 576, 48 e 892 chiamate a `_components`.
- Ritmo di `_components`, con la lettura del file, l'hash, la decodifica, l'albero e la query: sul progetto TypeScript più grande del corpus per byte, `real-stack-mattermost-mobile` (React Native, non Angular), 3.278 file, 18,3 MB, 5,47 s: 599 file/s e 3,35 MB/s. Su tutti i 40 progetti con file TypeScript: 15.251 file, 72,2 MB, 26,6 s, 572 file/s e 2,71 MB/s. A quel ritmo, una lettura di tutti gli alberi di un progetto di quella dimensione costerebbe 5,5 s, due volte per pre-mappa.

**D. Il linguaggio di go-enry contro quello dell'inventario** (`results/scan-cost/languages.json`: i 178 progetti con la risposta di go-enry registrata; senza `real-stack-jellyfin` e `real-stack-kuvasz`). Nessun file dell'inventario manca dalla risposta di go-enry. Le miniature hanno anche il loro `expected.json` (come le posa il container), che conta fra i `JSON`.

| Corpus | File | Stesso linguaggio | Nessuno dei due | Diversi | (a) Daodan ne dà uno e go-enry un altro o nessuno | (b) Daodan nessuno e go-enry uno che Daodan legge | Daodan nessuno e go-enry uno che non legge |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| miniature | 806 | 362 | 1 | 443 | 26 | 0 | 417 |
| real | 46.737 | 33.151 | 13 | 13.573 | 61 | 0 | 13.512 |

- (a) sono i file che oggi un parser legge: 26 nelle miniature, 61 nei real. In 5 (real) il nome di go-enry è uno che Daodan legge (`JavaScript` su file `.ts`: un altro parser li leggerebbe); in 80 (26 e 54) è uno che Daodan non legge (con quel nome sarebbero file senza parser); in 2 go-enry non dà un linguaggio.
- (b) è zero in tutti e due i corpora: nessun file senza linguaggio in Daodan è chiamato da go-enry con un nome che Daodan legge. I 13.929 file con go-enry sì e Daodan no sono linguaggi che Daodan non ha: nei real `PHP` 3.732 (8 progetti), `Elixir` 2.416 (3), `Markdown` 1.871 (55), `JSON` 1.849 (48), `YAML` 1.095 (48).

Le coppie di (a) (miniature e real insieme) e una di (b), con un esempio ciascuna:

| go-enry → Daodan | File | Progetti | Parser di Daodan per il nome di go-enry | Esempio |
| --- | ---: | ---: | --- | --- |
| `Gradle Kotlin DSL` → `kotlin` | 55 | 13 | no (i `.kts` si leggono come Kotlin) | `build.gradle.kts` in `mix-real-klaxon` |
| `PLpgSQL` → `sql` | 9 | 6 | no (SQL generico) | `packages/hoppscotch-backend/prisma/migrations/20251016080714_mock_server/migration.sql` in `real-app-hoppscotch` |
| `Fluent` → `markup` | 8 | 1 | no (`.ftl` è nella tabella dei template) | `crates/atuin/i18n/en-US/atuin.ftl` in `real-stack-atuin` |
| `JavaScript` → `typescript` | 5 | 2 | sì | `packages/ci-actions/bin/get-next-package-version.ts` in `real-stack-actual` |
| `Objective-C` → `c` | 3 | 2 | no | `app/ios/Runner/Runner-Bridging-Header.h` in `real-stack-localsend` |
| `XML` → `rust` | 3 | 2 | no | `server/src/schema.rs` in `real-stack-lldap` |
| `(none)` → `typescript` | 2 | 2 | - | `web/src/components/MemoEditor/view/useSearchMatchHighlight.ts` in `real-app-memos` (lo stesso file di `binary`) |
| `TSQL` → `sql` | 1 | 1 | no | `db/sqlserver/usp_get_orders.sql` in `mix-edge-sql` |
| `Ruby` → `python` | 1 | 1 | no | `bin/stackprof-gprof2dot.py` in `real-stack-lobsters` |
| `PHP` → `(none)` (b) | 3.732 | 8 | no | `app/Access/EmailConfirmationService.php` in `real-stack-bookstack` |

I tre suffissi che Daodan decide anche dal testo, a parte (tutti i file con quel suffisso; `=` dove i due nomi coincidono):

| Suffisso | go-enry → Daodan | File |
| --- | --- | ---: |
| `.h` | `C` → `c` `=` | 40 |
| `.h` | `C++` → `cpp` `=` | 14 |
| `.h` | `Objective-C` → `(none)` | 9 |
| `.h` | `Objective-C` → `c` | 3 |
| `.ts` | `TypeScript` → `typescript` `=` | 9.977 |
| `.ts` | `JavaScript` → `typescript` | 5 |
| `.ts` | `(none)` → `typescript` | 2 |
| `.ts` | `XML` → `(none)` (`i18n/app_it.ts` in `mix-edge-extensions`: una traduzione Qt) | 1 |
| `.sql` | `SQL` → `sql` `=` | 431 |
| `.sql` | `PLpgSQL` → `sql` | 9 |
| `.sql` | `PLSQL` → `plsql` `=` | 1 |
| `.sql` | `TSQL` → `sql` | 1 |

**E. Il motivo `submodule`.** Le voci della faccetta `excluded` che ognuno dei cinque motivi stabilisce e i file dell'inventario che tengono, sui 178 progetti con la registrazione:

| Motivo | Voci | Progetti con voci | File dell'inventario |
| --- | ---: | ---: | ---: |
| `vendored` | 549 | 71 | 474 |
| `generated` | 798 | 64 | 786 |
| `documentation` | 851 | 60 | 1.752 |
| `binary` | 1.416 | 52 | 2 |
| `submodule` | 5 | 4 | 0 |

Nessun progetto ha un submodule con file: le 5 voci (`mix-edge-submodules` 2, `sys-git-submodule-absent` 1, `real-stack-localsend` 1, `real-stack-mattermost-mobile` 1) hanno tutte la cartella assente o vuota (5 lacune `submodule_absent`). Per `submodule` i file letti, i simboli e gli import verso sono quindi zero (righe nella tabella di A), e il motivo non si può misurare sul corpus. I 3.014 file esclusi (30 e 2.984) sono gli stessi di A.

### Non misurato

- Il tempo del container nella pre-mappa (comandi registrati, non rieseguiti) e la `read` delle sorgenti i cui comandi non sono registrati (`noir` in tutti i progetti): i secondi della pre-mappa sono quindi un limite inferiore della parte che non è il container, e le sorgenti `angular` dei progetti sopra hanno letto gli alberi ma non le righe del compilatore (comandi `angular` non registrati).
- `real-stack-jellyfin` per intero (una ripetizione non è finita in oltre due ore: non so se dichiara Angular né quanti TypeScript abbia); le due ripetizioni oltre la prima di `real-stack-kuvasz` (tre superano le due ore); l'esclusione dei file di entrambi (nessuna registrazione).
- Il secondo hash dei byte: `snapshot.py` ricalcola `sha256` in `_SnapshotPass.sources` e in `file_entry`, fuori dalla misura dei byte riletti.
- La scomposizione di `seal`; i progetti con un frontend Angular più grande di 446 file TypeScript.
- D ed E su `real-stack-jellyfin` e `real-stack-kuvasz` (nessuna registrazione); in D, quanti dei file con una coppia diversa un parser legge davvero (stato `parsed`): si conta il linguaggio dell'inventario, non lo stato della lettura; nel JSON, delle coppie per suffisso restano le dieci più frequenti.
- La varianza fra corse intere: ogni progetto ha avuto una sola funzione Modal (con le ripetizioni di B dentro); il container può essere stato rilanciato dopo una prelazione (`preemption`: due volte nella corsa).
