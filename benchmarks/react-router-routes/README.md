# React Router e Remix: `routes --json` del comando che il progetto installa

Domanda: che dati dà `react-router routes --json` (e `remix routes --json`, dove esiste) per le rotte di un progetto, e che cosa ne ricava la
sorgente della pre-mappa [`daodan/core/premap/react_router.py`](../../daodan/core/premap/react_router.py). Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md),
task 13b; spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6.

Tutto gira su Modal, in un container con la rete bloccata: il codice del progetto (`routes.ts`, `react-router.config.ts`, `remix.config.js`,
`vite.config.ts`, `node_modules`) gira solo lì, e i pacchetti sono ripristinati dal `package-lock.json` mentre l'immagine si costruisce, l'unico momento con la
rete aperta. Niente di tutto questo gira su questo PC.

| Cartella | Contenuto |
| --- | --- |
| `fixture/framework/` | React Router 7.18.6 in modalità framework, con `package-lock.json` (ogni `resolved` punta a `registry.npmjs.org`): `app/routes.ts` con `route()`, `index()`, `layout()` e `prefix()`, un ciclo che scrive due rotte dello stesso modulo, un id scritto a mano, `caseSensitive`, un segmento opzionale (`:lang?`), uno splat (`docs/*`), una rotta risorsa (`api/pay`, `api/health`: nessun `export default`), un layout senza percorso, un indice, un'estensione `.jsx`, un `loader` scritto come `export const` con una funzione freccia, un componente scritto come variabile, un `export default` anonimo e una riesportazione |
| `fixture/flat/` | la convenzione a file (`@react-router/fs-routes` 7.18.6, `flatRoutes()`): `_index`, un layout senza percorso (`_auth`), `blog.$slug`, uno splat (`files.$`), un segmento opzionale (`($lang).docs`), una rotta risorsa (`api.pay`), una cartella con `route.tsx` |
| `fixture/remix/` | Remix 2.17.5 classico, `remix.config.js` con una rotta in più scritta nel codice (`routes(defineRoutes)`) e la convenzione a file di v2 |
| `fixture/remix-vite/` | gli stessi file con il plugin Vite (`vite.config.ts` con `routes(defineRoutes)`), senza `remix.config.js` |
| `results/` | l'uscita di ogni comando provato su Modal il 23 novembre 2026 (`00_env.json` dà le versioni), e `pipeline-scan.json`, il passo `scan` della pipeline intera. Le sonde di `COMMANDS` sono precedenti a quattro modifiche dei file della fixture `framework` (`about.tsx`, `docs.tsx`, `legacy.jsx`, `shop/order.tsx`: la funzione freccia, l'`export default` anonimo e la riesportazione): non cambiano i nomi dei file né `routes.ts`, e l'uscita di `routes --json` è quella di prima (le risposte di `--mode source` e `pipeline-scan.json` sono dopo) |
| `modal_probe.py` | `--mode lock` scrive i `package-lock.json`; `--mode probes` esegue i comandi di `COMMANDS` (e `VARIANTS=a,b` ne sceglie alcuni); `--mode source` esegue la sorgente di Daodan e registra le risposte in `tests/fixtures/premap/react-router/answers.json` |
| `scan_summary.py` | riassume in `results/pipeline-scan.json` ciò che `scan` ha scritto per `fixture/framework` |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/react-router-routes/modal_probe.py --mode lock
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/react-router-routes/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/react-router-routes/modal_probe.py --mode source
DAODAN_FOLDER=<copia di fixture/framework> PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/project-model/modal_pipeline.py --folder-out DIR --folder-stop scan
python benchmarks/react-router-routes/scan_summary.py DIR
```

## Parametri provati

| Parametro | Valori |
| --- | --- |
| Comando | `react-router routes` (testo) e `--json`; `--mode production`; il progetto come argomento (`routes --json /percorso`); `--help`; `remix routes` e `--json`; `react-router typegen` |
| Come si scrivono le rotte | `routes.ts` con `route`, `index`, `layout`, `prefix`; `flatRoutes()` di `@react-router/fs-routes`; Remix 2 classico (`remix.config.js`, convenzione a file e una rotta in codice); Remix 2 con Vite (`vite.config.ts`, la stessa rotta in codice) |
| Dove sta la cartella dell'app | `app` (predefinita); `appDirectory: "src"`; `appDirectory: "src/web"` |
| Percorsi | relativi (`users`, `:id`); un figlio con percorso assoluto (`/users/:id` sotto `users`), con un figlio relativo sotto di lui (`details`), e uno che non comincia con il percorso del padre (`/elsewhere` sotto `other`); `basename: "/base/"` in `react-router.config.ts` |
| Che cosa manca o si rompe | un file di rotta che non esiste; `routes.ts` con un errore di sintassi; `routes.ts` che lancia un'eccezione; `routes.ts` assente; nessun `vite.config.ts`; nessun `react-router.config.ts`; un `routes.ts` che aspetta per sempre (`await new Promise(r => setTimeout(r, 3_600_000))`), anche con `process.on("SIGTERM", () => {})`, sotto `timeout --kill-after` |
| Pacchetti | installati; non installati, con `npx --no-install`, con `npx --no`, e con `npm_config_offline=true` (rete bloccata) |

## Che cosa dà `routes --json`, misurato (Node 24.22.3, npm 11.19.1, `@react-router/dev` 7.18.6, `@remix-run/dev` 2.17.5, rete bloccata)

| Misura | Risultato | Uscita |
| --- | --- | --- |
| uscita | un array JSON sullo standard output, con una sola radice (`id: "root"`, `path: ""`, `file: "root.tsx"`) e le rotte in `children`; ogni rotta ha `id`, `file` e, quando li ha, `path`, `index: true`, `caseSensitive: true` e `children`; nessun altro campo (le chiavi di tutte le rotte: `caseSensitive`, `children`, `file`, `id`, `index`, `path`) | `framework.json`, `flat.json`, `remix.json` |
| rotte della fixture `framework` | 18, di cui 2 indici e 2 senza `path` né `index` (la radice e `layout("routes/shop/layout.tsx")`); profondità massima 2; esce 0 in 1,3 secondi | `framework.json` |
| il percorso | ogni rotta dà solo il suo segmento (`orders/:id` sotto un layout senza percorso, `nested` e `child`): il percorso intero lo compone chi legge, dagli antenati | `framework.json` |
| un percorso assoluto | un figlio scritto `route("/users/:id", …)` sotto `route("users", …)` esce `"path": "/users/:id"`, come scritto (non `users/:id` né `users/users/:id`), e un figlio relativo sotto di lui esce `details`; `/about` al primo livello esce `/about`. La regola di React Router è che il percorso assoluto è il percorso intero (la sorgente la applica, e anche ai figli): `users` > `/users/:id` > `details` è `/users/:id/details`. Un figlio assoluto che non comincia con il percorso del padre (`/elsewhere` sotto `other`), che React Router dichiara non valido, il comando lo stampa lo stesso, exit 0, senza una parola | `absolute-child.json`, `absolute-child-elsewhere.json` |
| la regola del percorso assoluto, dal testo del pacchetto | misurata sul sorgente del `react-router` installato (7.18.6), solo letto, nessuna app avviata: il suo `matchRoutes` fa `meta.relativePath.startsWith("/")` e `invariant(startsWith(parentPath), "Absolute route path … nested under path … is not valid. An absolute child route path must start with the combined path of all its parent routes.")`, poi `relativePath.slice(parentPath.length)` e `joinPaths([parentPath, relativePath])`: il percorso è quello assoluto. Con padri che hanno segmenti opzionali, un figlio assoluto che non comincia con il percorso del padre è saltato senza errore (`return`): la sorgente lo stampa come scritto | `rule-source.json` |
| il `basename` | `basename: "/base/"` in `react-router.config.ts` non cambia l'uscita: i percorsi sono quelli di prima, senza il prefisso | `basename.json` |
| due rotte dello stesso modulo | due righe con lo stesso `file` e id diversi (`hello-en`, `hello-it`, scritte da un ciclo di `routes.ts`) | `framework.json` |
| un id scritto a mano e `caseSensitive` | `user-detail`, `user-edit` con `caseSensitive: true`; l'id predefinito è il file senza estensione (`routes/home`) | `framework.json` |
| `routes.ts` è codice | il ciclo e la costruzione dei percorsi con una variabile sono eseguiti: le rotte `en/hello` e `it/hello` sono nell'uscita | `framework.json` |
| la convenzione a file | 12 rotte per `flatRoutes()`: `_auth` è una rotta senza `path` con `login` figlio, `_index` e `blog._index` sono indici, `blog.$slug` dà `:slug` dentro `blog`, `files.$` dà `files/*`, `($lang).docs` dà `:lang?/docs`, `shop/route.tsx` dà `shop` | `flat.json` |
| Remix 2.17.5 | lo stesso comando (`remix routes --json`) e lo stesso schema, esce 0 in 1,5-1,7 secondi, sia con `remix.config.js` sia con il plugin Vite: la rotta scritta nel codice (`custom/:id`, file `custom.tsx`, id `custom-route`) c'è in entrambi. 7 rotte. Lo standard error ha avvisi (l'API CJS di Vite, i `future flag`), lo standard output solo il JSON | `remix.json`, `remix-vite.json` |
| il testo | `routes` senza `--json` dà un albero `<Route path=… file=…/>` con gli stessi dati | `framework.json` |
| `--mode production` e il progetto come argomento | la stessa uscita | `framework.json`, `framework-root-argument.json` |
| senza `vite.config.ts` e senza `react-router.config.ts` | la stessa uscita, esce 0 | `no-vite-config.json`, `no-react-router-config.json` |
| che cosa lascia nel progetto | niente, fuori da `node_modules`, per ogni variante (`left_in_the_project` è vuoto); `react-router typegen` invece scrive 20 file in `.react-router/types/` | tutti, `typegen.json` |

## Che cosa non dà

| Dato | Misura | Uscita |
| --- | --- | --- |
| la cartella dell'app | il `file` è relativo a una cartella che l'uscita non nomina: con `appDirectory` predefinita, `"src"` e `"src/web"` l'uscita è identica, byte per byte, e `root.tsx` sta ogni volta in un posto diverso. La sorgente prende `app` e pretende che il file della radice (il primo che il comando stampa) ci sia: dove non c'è lo dice in una lacuna sola, e i file che stanno sotto `app/` per caso non si legano (un `app/routes/about.tsx` rimasto, con `appDirectory: "src"`, era letto come la rotta `/about`); se la radice c'è e la cartella è un'altra, resta il rischio che i file di entrambe si leghino senza una lacuna (`# shortcut:` in `react_router.py`). `react-router typegen` la nomina nel percorso dei file che scrive (`.react-router/types/app/+types/root.ts`, e `src/` con `appDirectory: "src"`): **non usato** (vedi «Non provato») | `app-directory-src.json`, `app-directory-nested.json`, `typegen.json`, `typegen-app-directory-src.json` |
| l'esistenza del file | una rotta il cui file non c'è (`routes/about.tsx` cancellato) è nell'uscita e il comando esce 0: lo dice solo lo snapshot | `file-missing.json` |
| le righe | nessuna: il `file` e basta | `framework.json` |
| le esportazioni del modulo | né `default`, né `loader`, né `action`, né i `client…`: non sa se una rotta è una pagina o una rotta risorsa, non nomina i gestori | `framework.json` |
| il metodo HTTP | nessuno: `loader` e `action` non sono nell'uscita | `framework.json` |
| che cos'è un layout | nessun campo: una rotta senza `path` e senza `index` è un layout (o la radice) | `framework.json` |
| `react-router` come libreria | `routes` è un comando di `@react-router/dev`: un progetto che dichiara solo `react-router` o `react-router-dom` (rotte scritte nel codice con `createBrowserRouter` o `<Routes>`) non ha alcun comando che le elenchi: la sorgente non lancia nulla e dice la causa in una lacuna per ogni `package.json` (dalle dipendenze che la pre-mappa ha già) | — |

Quando fallisce:

| Caso | Misura | Uscita |
| --- | --- | --- |
| `routes.ts` con un errore di sintassi | esce 1, lo standard error comincia con `Route config in "routes.ts" is invalid.` e la causa (`Expected ")" but found end of file`), poi una pila di chiamate | `routes-ts-broken.json` |
| `routes.ts` che lancia (`routes.ts needs a database`) | esce 1, la causa è in testa e le righe della pila dopo: la coda dello standard error non la contiene | `routes-ts-throws.json` |
| `routes.ts` assente | esce 1, `Route config file not found at "app/routes.ts".` | `routes-ts-absent.json` |
| un `routes.ts` che aspetta per sempre, sotto `timeout --kill-after=2 5` | esce **124 dopo 5,03 secondi** e `ps` dopo il comando non mostra altro che i processi del container; con un config che installa un gestore di `SIGTERM` che non esce (`term-seen.txt` esiste: il gestore è girato) e `timeout --kill-after=2 3`: 124 dopo 3,03 secondi e nessun processo resta, senza che il segnale 9 serva (come il processo finisca prima dei 2 secondi di grazia non è stato indagato). Il 137 (l'uccisione dopo il tempo di grazia) non è riprodotto in nessuno dei due casi: la sorgente lo tratta come il 124 perché è il codice con cui `timeout` dice di aver dovuto uccidere il comando (il test lo prova su una risposta sintetica). | `hang.json`, `hang-ignores-term.json` |
| il comando non è installato, `npx --no-install` | esce 1 dopo **70,7 secondi** (70,6 per `remix`), con `EAI_AGAIN` su `registry.npmjs.org`: npx chiede comunque il pacchetto `react-router` al registro; `npx --no` fa lo stesso (70,9 secondi) | `not-installed.json`, `remix-not-installed.json`, `not-installed-npx-no.json` |
| lo stesso con `npm_config_offline=true` | esce 1 dopo **0,6 secondi**, con `ENOTCACHED … cache mode is 'only-if-cached' but no cached response is available` per `react-router`; con i pacchetti installati esce 0 in 1,6 secondi | `not-installed-offline.json`, `offline-installed.json` |

## La sorgente su Modal

`--mode source`: la sorgente dà i comandi per ogni fixture (una funzione con la rete aperta, perché il pacchetto delle grammatiche di Daodan si scarica), poi
ogni comando gira con la rete bloccata, con l'`argv` e l'ambiente che la sorgente ha scritto (`timeout --kill-after=10 300 npx --no-install react-router routes --json` o `… remix routes --json`, `npm_config_offline=true`; per le varianti che aspettano per sempre i tempi sono 2 e 3 secondi), in una copia del progetto con i suoi pacchetti,
in una copia con un cambiamento che le interessa e in una copia senza i pacchetti. Le risposte, come le restituisce il container, sono in `tests/fixtures/premap/react-router/answers.json`,
che `tests/test_codebase_map_premap_react_router.py` legge (48 test, Python puro, senza motore).

| Variante | Risposta |
| --- | --- |
| `framework`, `flat`, `remix`, `remix-vite` | esce 0 in 1,6-2,0 secondi sotto `timeout`: 2189, 1432, 766 e 766 byte di JSON |
| `absolute-child`, `absolute-child-elsewhere` | esce 0, 827 e 364 byte: i percorsi come scritti (`/users/:id`, `/users/new`, `/about`, `details`; `/other`, `/elsewhere`); la sorgente dà `/users/:id/details`, `/users`, `/about` e `/elsewhere` |
| `hang`, `hang-ignores-term` | esce 124 dopo 3,05 secondi (tempi 2 e 3 secondi invece di 10 e 300): una lacuna `model_failed` che dice «did not end in 300 seconds» e nessuna riga |
| `app-directory-src` | esce 0, la stessa uscita di `framework`: la sorgente non trova il file della radice sotto `app/` e dà una lacuna sola |
| `file-missing` | esce 0, la stessa uscita: la sorgente dà `outside_snapshot` per `app/routes/about.tsx` e legge le altre rotte |
| `routes-ts-throws`, `routes-ts-broken`, `routes-ts-absent` | esce 1: una lacuna `model_failed` con la causa che lo strumento ha scritto per prima e la coda del messaggio |
| `not-installed` | esce 1 in 0,5-0,6 secondi (`ENOTCACHED`): una lacuna `model_failed` che nomina `react-router` |

| Misura | Risultato |
| --- | --- |
| righe che la sorgente ne ricava dalle 18 rotte di `framework` | 23: 19 sulla funzione che l'esportazione nomina (10 `default`, 4 `loader`, 3 `action` più 2 `default` di un indice), 2 sul file di un layout (tipo «nessun ingresso»), 2 righe di lacuna (`docs.tsx`, che esporta un `default` anonimo, e `legacy.jsx`, che lo riesporta: `default: reexport-unsupported`) |
| rotta risorsa | `api/pay` dà `loader` e `action` e nessun `default`; `api/health` solo `loader`; `api.pay` della convenzione a file e di Remix solo `action` |
| arrow e variabile | `export const loader = async () => {}` e `const About = () => …; export default About` sono legati alla funzione (`order.tsx::loader`, riga 2; `about.tsx::About`, riga 2) |
| stessa rotta due volte | `/en/hello` e `/it/hello`: due righe sullo stesso `hello.tsx:1` |
| `flat` | 12 rotte, nessuna lacuna; `remix` e `remix-vite`: 7 rotte, nessuna lacuna |
| nei collegamenti (`flows.cached_links`) | 19 ingressi sulle funzioni, tutti `react-router` di tipo «rotta»; i due layout non sono ingressi; `routes.offered` 0 |

### La pre-mappa intera, nel container di Daodan

`DAODAN_FOLDER=<copia di fixture/framework> … modal_pipeline.py --folder-out DIR --folder-stop scan` esegue il passo `scan` della pipeline su Modal con la sorgente registrata: il
ripristino dei pacchetti dal `package-lock.json` con la rete aperta ai soli registri, poi il comando con la rete bloccata, come lo lancia `container_runner`.
`results/pipeline-scan.json` tiene gli stati delle sorgenti, le righe di `framework_entries`, le lacune della sorgente e i collegamenti che `flows.link_facts` ne ricava.

| Misura | Risultato |
| --- | --- |
| `scan`, tutto | 134,0 secondi, con il comando sotto `timeout` (con `tsc` 15,3 s, `npm` 9,4 s, `noir` 19,4 s); la prima esecuzione, senza `timeout`, 116,1 secondi (`tsc` 12,9 s, `npm` 7,2 s, `noir` 16,7 s): anche le fonti che non c'entrano sono più lente in questa run, quindi la differenza non è del solo `timeout` |
| sorgente `react-router@daodan/premap/v2` | `ran`, 17,0 secondi, compreso il ripristino dei pacchetti e il comando (14,7 senza `timeout`); `timeout` esiste nel container (l'immagine `buildpack-deps`, coreutils) e il comando ha girato |
| `framework_entries` in `premap.json` | 23 righe, 0 lacune della sorgente: le stesse 23 righe della risposta registrata; `test_the_premap_the_whole_pipeline_wrote_on_modal_holds_the_rows_of_the_recorded_answer` lo verifica |
| `next` e `angular` | `not_needed`: la fixture non li dichiara |
| Noir sulla stessa fixture | 25 endpoint `http` negli stessi file, con il suo metodo (`GET` per ogni modulo; `GET`, `POST`, `PUT`, `PATCH`, `DELETE` per `api/pay`, `checkout` e `users/edit`, che esportano `action`) e il suo modo di scrivere il percorso (`/orders/{id}`, `/docs/{splat}`, `/{lang}/blog`), senza il nome del gestore: nei collegamenti sono 25 lacune «noir reports this entry without a unique snapshot handler at its site», non ingressi |
| collegamenti | 19 ingressi (`react-router rotta`), `routes` `{offered: 0, called: 0, linked: 0}`, 27 lacune: le 25 di Noir e le 2 righe di lacuna di React Router |

## La radice e un layout senza percorso

Letto, non eseguito: `react-router` 7.18.6 e `@react-router/dev` 7.18.6 scaricati con `npm pack --ignore-scripts` ed estratti, nessun codice girato (parametro da provare su Modal: richieste a `/`, a una pagina e a una rotta risorsa con un `loader` e un'`action` in radice e in un layout senza percorso).

| Che cosa | Dal sorgente | Scelta |
| --- | --- | --- |
| bersaglio di un invio | `getTargetMatch` (~5699) prende l'ultimo match che contribuisce al percorso (`getPathContributingMatches`, ~983: `index === 0` o `route.path` non vuoto), o la rotta indice con `?index` | l'`action` e la `clientAction` della radice sono ingressi (un POST a `/` senza `?index` le chiama); quelle di un layout senza percorso non sono mai il bersaglio: codice che il framework non chiama, né ingresso né lacuna |
| `loader` | tutti i match di una richiesta di documento o di dati di una pagina lo eseguono; una rotta risorsa (`queryRoute`, ~3789) esegue solo il match bersaglio, e sul client decide anche `shouldRevalidate` | il `loader` e il `clientLoader` della radice e di un layout senza percorso sono ingressi, con il percorso che è il prefisso sotto cui girano (`/` per la radice e per un layout sotto di lei) |
| forme | la riga sul file del layout resta (forma `layout`, «nessun ingresso»); le funzioni sono righe di forma `root-data` e `layout-data` (`entry-queries.json`), perché il registro dà un tipo per forma; senza `loader` nessuna riga in più, una funzione non legata dallo snapshot è una riga di lacuna con la stessa forma | `default` non c'è: un componente di layout non avvia un flusso, i suoi controlli li legge il lettore JSX |

Non misurato: Remix (`@remix-run/router` 1.x non è nel pacchetto letto), l'esecuzione su un'app, il numero di righe in più su un progetto reale. La fixture `framework` non cambia (la sua radice e il suo layout non esportano funzioni di dati): restano 23 righe; i test usano file sostituiti.

## `basename`

Non c'è uno strumento ufficiale che lo dia senza un build, valutati su `@react-router/dev` 7.18.6 (letto): `routes` stampa solo `configResult.value.routes` (`cli/index.js` ~2368, e con `basename: "/base/"` l'uscita non cambiava); `./config` esporta solo tipi; `typegen` scrive `export const basename: ServerBuild["basename"]` (il tipo, `+server-build.d.ts`); i comandi sono `routes`, `build`, `reveal`, `dev`, `typegen`. Il valore sta nel modulo virtuale `virtual:react-router/server-build` (`vite.js` ~3294), cioè in un build o in un dev server di Vite. Un lettore di `react-router.config.ts` non è scritto: è codice che può calcolare il valore (`process.env`, un preset). Nessuna lacuna a runtime: quasi ogni progetto ha quel file, sarebbe rumore, e il percorso delle righe non ha oggi un consumatore che lo usi come URL (`routes.offered` è 0). Il punto resta aperto e dichiarato.

## Limiti dichiarati

Ognuno ha il suo `# shortcut: <limite>, <quando>` in [`react_router.py`](../../daodan/core/premap/react_router.py).

| Limite | Quando si toglie |
| --- | --- |
| il `middleware` della radice (`future.v8_middleware`) gira a ogni richiesta e non è letto; `loader` e `action` della radice e di un layout senza percorso sono righe (vedi «La radice e un layout senza percorso»), ma la regola è letta dal sorgente e non eseguita su un'app | quando si serve la fixture su Modal: `react-router build` con un server, richieste a `/` e a una pagina; per Remix, `@remix-run/router` |
| lo standard output si legge intero: una riga di log del config lo rende una lacuna `model_failed` per la cartella, con l'uscita | quando un config scrive sullo standard output: si legge l'ultimo documento JSON |
| la cartella dell'app è `app` se il file della radice c'è; con un'altra `appDirectory` e un file della radice anche sotto `app/` (una seconda app, un avanzo) i file di entrambe si legano senza una lacuna | quando un progetto lo fa: si legge la cartella dai file che `react-router typegen` scrive (misurato) |
| il percorso è quello del comando: senza il `basename` del config (misurato con `/base/`: l'uscita non lo ha); nessuno strumento ufficiale lo dà senza un build (vedi «`basename`») | quando un consumatore usa il percorso come URL: si prende dal modulo `virtual:react-router/server-build` |
| un figlio assoluto che non comincia con il percorso del padre si legge come scritto, anche se React Router lo direbbe non valido | quando un progetto lo fa: si controlla il prefisso |
| la lacuna della libreria scatta anche per un pacchetto di componenti di un monorepo che dichiara `react-router-dom` | quando un monorepo ne ha: solo un manifesto la cui cartella ha un avvio o una costruzione (`npm-start`) |
| più di 90 cartelle che dichiarano il pacchetto chiedono più dei 900 secondi che si dividono (300 ciascuna fino a tre cartelle, poi 900 divisi fra loro, mai meno di 10) | quando un progetto ne ha tante: si alza il totale |
| il comando si lancia in ogni cartella che dichiara `@react-router/dev` o `@remix-run/dev`, anche la radice di un workspace dove il pacchetto è sollevato e l'app sta in una cartella sotto (il comando esce 1 con «Route config file not found» ed è una lacuna) | quando un monorepo dichiara il pacchetto nella radice: le cartelle che hanno un `app/routes.ts` |

## Non provato

- Una cartella dell'app diversa da `app` è una lacuna, non una lettura: `react-router typegen` la nomina nei file che scrive (misurato su `app` e `src`), ma è un secondo comando che scrive 20 file e un elenco di cartelle da leggere, e Remix 2 non ha `typegen`; non è stato scritto né provato come fonte.
- Un progetto reale: la sorgente è stata eseguita solo su queste quattro fixture; nessuna riga è stata confrontata a mano con un'app esistente, e il tempo del comando su un progetto con molte rotte non è misurato.
- Le rotte offerte. Le righe sono ingressi: il comando non dà il metodo e la sorgente non lo inventa. Servirebbero la tabella dei metodi per esportazione (la documentazione dice `loader` per `GET` e `HEAD`, `action` per gli altri metodi: non misurato, e un `export default` non risponde a una richiesta con un metodo), la conversione del percorso (`:id` è già uno schema, `*` e `:lang?` stanno per più schemi, come i `[...x]` di Next.js), e la tavola `http` di `flows._declared_routes`, che oggi nomina solo Noir e Next.js.
- Noir e React Router sulla stessa rotta: le righe non si uniscono, perché l'unione di `flows.link_facts` riguarda solo le rotte di Next.js; nel caso misurato Noir non dà il nome del gestore e le sue 25 righe sono lacune, ma un progetto dove lo dà avrebbe due ingressi per rotta.
- Il percorso assoluto con Remix 2 (misurato solo con React Router 7.18.6), e il codice 137 di `timeout` (nessuno dei due casi provati lo dà).
- Un progetto che dichiara `@react-router/dev` e `@remix-run/dev` insieme: due comandi nella stessa cartella e due serie di righe.
- Remix 1 e le versioni di Remix 2 senza `routes --json`; React Router prima della 7; i moduli di rotta che non sono script (`.mdx`: lo snapshot non li ha, la lacuna dice che il file non c'è); `react-router.config.ts` con `ssr: false`.
- Progetti con pnpm, Yarn o Bun: il ripristino dei pacchetti è quello che il container già fa, e `npx --no-install` non è stato provato con la loro disposizione di `node_modules`; i `package-lock.json` delle fixture sono di npm.
- `npx --no-install` e la sua attesa di 70 secondi senza i pacchetti: misurato per `react-router` e `remix`, non per `next`; `premap/nextjs.py` ora ha `npm_config_offline=true` (un test prova l'ambiente, l'attesa non è misurata).
