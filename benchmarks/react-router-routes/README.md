# React Router e Remix: `routes --json` del comando che il progetto installa

**Stato:** In uso. La sorgente [`daodan/core/premap/react_router.py`](../../daodan/core/premap/react_router.py) è in `premap.SOURCES` e `FRAMEWORK_SOURCES`, ha la voce `react-router` in `container_runner.TOOLS` e la tabella `react-router` in `daodan/data/entry-queries.json`. Aperto: la cartella dell'app diversa da `app`, il `basename`, le rotte offerte, e la regola della radice e dei layout, letta dal sorgente e mai eseguita su un'app («Aperto»).

## Domanda

Che dati dà `react-router routes --json` (e `remix routes --json`) per le rotte di un progetto, e che cosa ne ricava la sorgente. Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 13b del piano).

## Strumento ufficiale provato

`@react-router/dev` 7.18.6 e `@remix-run/dev` 2.17.5; Node 24.22.3, npm 11.19.1. Misurato su Modal il 23 novembre 2026, rete bloccata. Il comando è di `@react-router/dev`: un progetto che dichiara solo `react-router` o `react-router-dom` (rotte scritte nel codice) non ha un comando che le elenchi, e la sorgente lo dice in una lacuna.

Valutato e non usato: `react-router typegen` nomina la cartella dell'app nei file che scrive, ma è un secondo comando che scrive 20 file in `.react-router/types/`, e Remix 2 non lo ha.

## Parametri

| Parametro | Valori |
| --- | --- |
| Comando | `react-router routes` (testo) e `--json`; `--mode production`; il progetto come argomento (`routes --json /percorso`); `--help`; `remix routes` e `--json`; `react-router typegen` |
| Come si scrivono le rotte | `routes.ts` con `route`, `index`, `layout`, `prefix`; `flatRoutes()` di `@react-router/fs-routes`; Remix 2 classico (`remix.config.js`, convenzione a file e una rotta in codice); Remix 2 con Vite (`vite.config.ts`, la stessa rotta in codice) |
| Dove sta la cartella dell'app | `app` (predefinita); `appDirectory: "src"`; `appDirectory: "src/web"` |
| Percorsi | relativi (`users`, `:id`); un figlio con percorso assoluto (`/users/:id` sotto `users`), con un figlio relativo sotto di lui (`details`), e uno che non comincia con il percorso del padre (`/elsewhere` sotto `other`); `basename: "/base/"` in `react-router.config.ts` |
| Che cosa manca o si rompe | un file di rotta che non esiste; `routes.ts` con un errore di sintassi; `routes.ts` che lancia un'eccezione; `routes.ts` assente; nessun `vite.config.ts`; nessun `react-router.config.ts`; un `routes.ts` che aspetta per sempre (`await new Promise(r => setTimeout(r, 3_600_000))`), anche con `process.on("SIGTERM", () => {})`, sotto `timeout --kill-after` |
| Pacchetti | installati; non installati, con `npx --no-install`, con `npx --no`, e con `npm_config_offline=true` (rete bloccata) |

File: `fixture/framework/` (React Router 7.18.6 con `routes.ts`), `fixture/flat/` (`flatRoutes()`), `fixture/remix/` (Remix 2.17.5 classico), `fixture/remix-vite/` (con il plugin Vite), `modal_probe.py` (`--mode lock`, `--mode probes`, `--mode source`, che registra `tests/fixtures/premap/react-router/answers.json`), `scan_summary.py`, `results/` (`00_env.json` dà le versioni). Le sonde di `COMMANDS` sono precedenti a quattro modifiche dei file della fixture `framework` che non cambiano `routes.ts` né l'uscita di `routes --json`; le risposte di `--mode source` e `pipeline-scan.json` sono successive.

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/react-router-routes/modal_probe.py --mode lock
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/react-router-routes/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/react-router-routes/modal_probe.py --mode source
DAODAN_FOLDER=<copia di fixture/framework> PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/project-model/modal_pipeline.py --folder-out DIR --folder-stop scan
python benchmarks/react-router-routes/scan_summary.py DIR
```

## Risultato

**Che cosa dà `routes --json`.**

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

**Che cosa non dà.**

| Dato | Misura | Uscita |
| --- | --- | --- |
| la cartella dell'app | il `file` è relativo a una cartella che l'uscita non nomina: con `appDirectory` predefinita, `"src"` e `"src/web"` l'uscita è identica, byte per byte, e `root.tsx` sta ogni volta in un posto diverso. La sorgente prende `app` e pretende che il file della radice (il primo che il comando stampa) ci sia: dove non c'è lo dice in una lacuna sola, e i file che stanno sotto `app/` per caso non si legano (un `app/routes/about.tsx` rimasto, con `appDirectory: "src"`, era letto come la rotta `/about`); se la radice c'è e la cartella è un'altra, resta il rischio che i file di entrambe si leghino senza una lacuna (`# shortcut:` in `react_router.py`). `react-router typegen` la nomina nel percorso dei file che scrive (`.react-router/types/app/+types/root.ts`, e `src/` con `appDirectory: "src"`): **non usato** (vedi «Strumento ufficiale provato») | `app-directory-src.json`, `app-directory-nested.json`, `typegen.json`, `typegen-app-directory-src.json` |
| l'esistenza del file | una rotta il cui file non c'è (`routes/about.tsx` cancellato) è nell'uscita e il comando esce 0: lo dice solo lo snapshot | `file-missing.json` |
| le righe | nessuna: il `file` e basta | `framework.json` |
| le esportazioni del modulo | né `default`, né `loader`, né `action`, né i `client…`: non sa se una rotta è una pagina o una rotta risorsa, non nomina i gestori | `framework.json` |
| il metodo HTTP | nessuno: `loader` e `action` non sono nell'uscita | `framework.json` |
| che cos'è un layout | nessun campo: una rotta senza `path` e senza `index` è un layout (o la radice) | `framework.json` |
| `react-router` come libreria | `routes` è un comando di `@react-router/dev`: un progetto che dichiara solo `react-router` o `react-router-dom` (rotte scritte nel codice con `createBrowserRouter` o `<Routes>`) non ha alcun comando che le elenchi: la sorgente non lancia nulla e dice la causa in una lacuna per ogni `package.json` (dalle dipendenze che la pre-mappa ha già) | — |

**Quando fallisce.**

| Caso | Misura | Uscita |
| --- | --- | --- |
| `routes.ts` con un errore di sintassi | esce 1, lo standard error comincia con `Route config in "routes.ts" is invalid.` e la causa (`Expected ")" but found end of file`), poi una pila di chiamate | `routes-ts-broken.json` |
| `routes.ts` che lancia (`routes.ts needs a database`) | esce 1, la causa è in testa e le righe della pila dopo: la coda dello standard error non la contiene | `routes-ts-throws.json` |
| `routes.ts` assente | esce 1, `Route config file not found at "app/routes.ts".` | `routes-ts-absent.json` |
| un `routes.ts` che aspetta per sempre, sotto `timeout --kill-after=2 5` | esce **124 dopo 5,03 secondi** e `ps` dopo il comando non mostra altro che i processi del container; con un config che installa un gestore di `SIGTERM` che non esce (`term-seen.txt` esiste: il gestore è girato) e `timeout --kill-after=2 3`: 124 dopo 3,03 secondi e nessun processo resta, senza che il segnale 9 serva (come il processo finisca prima dei 2 secondi di grazia non è stato indagato). Il 137 (l'uccisione dopo il tempo di grazia) non è riprodotto in nessuno dei due casi: la sorgente lo tratta come il 124 perché è il codice con cui `timeout` dice di aver dovuto uccidere il comando (il test lo prova su una risposta sintetica). | `hang.json`, `hang-ignores-term.json` |
| il comando non è installato, `npx --no-install` | esce 1 dopo **70,7 secondi** (70,6 per `remix`), con `EAI_AGAIN` su `registry.npmjs.org`: npx chiede comunque il pacchetto `react-router` al registro; `npx --no` fa lo stesso (70,9 secondi) | `not-installed.json`, `remix-not-installed.json`, `not-installed-npx-no.json` |
| lo stesso con `npm_config_offline=true` | esce 1 dopo **0,6 secondi**, con `ENOTCACHED … cache mode is 'only-if-cached' but no cached response is available` per `react-router`; con i pacchetti installati esce 0 in 1,6 secondi | `not-installed-offline.json`, `offline-installed.json` |

**La sorgente.** Comando: `timeout --kill-after=10 300 npx --no-install react-router routes --json` (o `… remix routes --json`) con `npm_config_offline=true`. Le risposte registrate per variante sono in `tests/fixtures/premap/react-router/answers.json`, che `tests/test_codebase_map_premap_react_router.py` legge.

| Misura | Risultato |
| --- | --- |
| righe che la sorgente ne ricava dalle 18 rotte di `framework` | 23: 19 sulla funzione che l'esportazione nomina (10 `default`, 4 `loader`, 3 `action` più 2 `default` di un indice), 2 sul file di un layout (tipo «nessun ingresso»), 2 righe di lacuna (`docs.tsx`, che esporta un `default` anonimo, e `legacy.jsx`, che lo riesporta: `default: reexport-unsupported`) |
| rotta risorsa | `api/pay` dà `loader` e `action` e nessun `default`; `api/health` solo `loader`; `api.pay` della convenzione a file e di Remix solo `action` |
| arrow e variabile | `export const loader = async () => {}` e `const About = () => …; export default About` sono legati alla funzione (`order.tsx::loader`, riga 2; `about.tsx::About`, riga 2) |
| stessa rotta due volte | `/en/hello` e `/it/hello`: due righe sullo stesso `hello.tsx:1` |
| `flat` | 12 rotte, nessuna lacuna; `remix` e `remix-vite`: 7 rotte, nessuna lacuna |
| nei collegamenti (`flows.cached_links`) | 19 ingressi sulle funzioni, tutti `react-router` di tipo «rotta»; i due layout non sono ingressi; `routes.offered` 0 |

**La pre-mappa intera** (`modal_pipeline.py --folder-stop scan` su `fixture/framework`, `results/pipeline-scan.json`; misurata con la sorgente `v2`, oggi `VERSION` è `daodan/premap/v4`: non rimisurata):

| Misura | Risultato |
| --- | --- |
| `scan`, tutto | 134,0 secondi, con il comando sotto `timeout` (con `tsc` 15,3 s, `npm` 9,4 s, `noir` 19,4 s); la prima esecuzione, senza `timeout`, 116,1 secondi (`tsc` 12,9 s, `npm` 7,2 s, `noir` 16,7 s): anche le fonti che non c'entrano sono più lente in questa run, quindi la differenza non è del solo `timeout` |
| sorgente `react-router@daodan/premap/v2` | `ran`, 17,0 secondi, compreso il ripristino dei pacchetti e il comando (14,7 senza `timeout`); `timeout` esiste nel container (l'immagine `buildpack-deps`, coreutils) e il comando ha girato |
| `framework_entries` in `premap.json` | 23 righe, 0 lacune della sorgente: le stesse 23 righe della risposta registrata; `test_the_premap_the_whole_pipeline_wrote_on_modal_holds_the_rows_of_the_recorded_answer` lo verifica |
| `next` e `angular` | `not_needed`: la fixture non li dichiara |
| Noir sulla stessa fixture | 25 endpoint `http` negli stessi file, con il suo metodo (`GET` per ogni modulo; `GET`, `POST`, `PUT`, `PATCH`, `DELETE` per `api/pay`, `checkout` e `users/edit`, che esportano `action`) e il suo modo di scrivere il percorso (`/orders/{id}`, `/docs/{splat}`, `/{lang}/blog`), senza il nome del gestore: nei collegamenti sono 25 lacune «noir reports this entry without a unique snapshot handler at its site», non ingressi |
| collegamenti | 19 ingressi (`react-router rotta`), `routes` `{offered: 0, called: 0, linked: 0}`, 27 lacune: le 25 di Noir e le 2 righe di lacuna di React Router |

**La radice e un layout senza percorso.** Letto nel sorgente di `react-router` 7.18.6 (`npm pack --ignore-scripts`), nessun codice eseguito:

| Che cosa | Dal sorgente | Scelta |
| --- | --- | --- |
| bersaglio di un invio | `getTargetMatch` (~5699) prende l'ultimo match che contribuisce al percorso (`getPathContributingMatches`, ~983: `index === 0` o `route.path` non vuoto), o la rotta indice con `?index` | l'`action` e la `clientAction` della radice sono ingressi (un POST a `/` senza `?index` le chiama); quelle di un layout senza percorso non sono mai il bersaglio: codice che il framework non chiama, né ingresso né lacuna |
| `loader` | tutti i match di una richiesta di documento o di dati di una pagina lo eseguono; una rotta risorsa (`queryRoute`, ~3789) esegue solo il match bersaglio, e sul client decide anche `shouldRevalidate` | il `loader` e il `clientLoader` della radice e di un layout senza percorso sono ingressi, con il percorso che è il prefisso sotto cui girano (`/` per la radice e per un layout sotto di lei) |
| forme | la riga sul file del layout resta (forma `layout`, «nessun ingresso»); le funzioni sono righe di forma `root-data` e `layout-data` (`entry-queries.json`), perché il registro dà un tipo per forma; senza `loader` nessuna riga in più, una funzione non legata dallo snapshot è una riga di lacuna con la stessa forma | `default` non c'è: un componente di layout non avvia un flusso, i suoi controlli li legge il lettore JSX |

## Aperto

- **La regola della radice e dei layout** è letta dal sorgente, non eseguita su un'app: da provare su Modal con richieste a `/`, a una pagina e a una rotta risorsa; per Remix serve `@remix-run/router` 1.x, non letto. Il `middleware` della radice (`future.v8_middleware`) non è letto.
- **Il `basename`.** Nessuno strumento ufficiale lo dà senza un build: `routes` non lo stampa (misurato con `/base/`), `typegen` ne scrive solo il tipo, il valore sta nel modulo virtuale `virtual:react-router/server-build`. Un lettore di `react-router.config.ts` non è scritto: è codice che può calcolare il valore.
- **Le rotte offerte.** Le righe sono ingressi: il comando non dà il metodo e la sorgente non lo inventa. Servirebbero la tabella dei metodi per esportazione (`loader` per `GET` e `HEAD`, `action` per gli altri, dalla documentazione: non misurato) e la conversione del percorso (`*` e `:lang?` stanno per più schemi).
- **Noir e React Router sulla stessa rotta.** Oggi `flows.link_facts` unisce una rotta di Noir a una riga legata e senza lacuna di una sorgente di `FRAMEWORK_SOURCES`, sullo stesso percorso e nello stesso file o sulla stessa funzione. La misura sopra è precedente e non è rifatta: quante righe si uniscono non è misurato.
- **I gestori che lo strumento non lega** (un `export default` anonimo, una riesportazione: 2 righe di lacuna sulla fixture): se il passo dinamico li osserva non è misurato.
- **Limiti dichiarati**, ognuno con il suo `# shortcut:` in `react_router.py`:

| Limite | Quando si toglie |
| --- | --- |
| il `middleware` della radice (`future.v8_middleware`) gira a ogni richiesta e non è letto; `loader` e `action` della radice e di un layout senza percorso sono righe (vedi «La radice e un layout senza percorso»), ma la regola è letta dal sorgente e non eseguita su un'app | quando si serve la fixture su Modal: `react-router build` con un server, richieste a `/` e a una pagina; per Remix, `@remix-run/router` |
| lo standard output si legge intero: una riga di log del config lo rende una lacuna `model_failed` per la cartella, con l'uscita | quando un config scrive sullo standard output: si legge l'ultimo documento JSON |
| la cartella dell'app è `app` se il file della radice c'è; con un'altra `appDirectory` e un file della radice anche sotto `app/` (una seconda app, un avanzo) i file di entrambe si legano senza una lacuna | quando un progetto lo fa: si legge la cartella dai file che `react-router typegen` scrive (misurato) |
| il percorso è quello del comando: senza il `basename` del config (misurato con `/base/`: l'uscita non lo ha); nessuno strumento ufficiale lo dà senza un build (vedi «Aperto») | quando un consumatore usa il percorso come URL: si prende dal modulo `virtual:react-router/server-build` |
| un figlio assoluto che non comincia con il percorso del padre si legge come scritto, anche se React Router lo direbbe non valido | quando un progetto lo fa: si controlla il prefisso |
| la lacuna della libreria scatta anche per un pacchetto di componenti di un monorepo che dichiara `react-router-dom` | quando un monorepo ne ha: solo un manifesto la cui cartella ha un avvio o una costruzione (`npm-start`) |
| più di 90 cartelle che dichiarano il pacchetto chiedono più dei 900 secondi che si dividono (300 ciascuna fino a tre cartelle, poi 900 divisi fra loro, mai meno di 10) | quando un progetto ne ha tante: si alza il totale |
| il comando si lancia in ogni cartella che dichiara `@react-router/dev` o `@remix-run/dev`, anche la radice di un workspace dove il pacchetto è sollevato e l'app sta in una cartella sotto (il comando esce 1 con «Route config file not found» ed è una lacuna) | quando un monorepo dichiara il pacchetto nella radice: le cartelle che hanno un `app/routes.ts` |

- **Non provati:** un progetto reale (solo le quattro fixture); il percorso assoluto con Remix 2; il codice 137 di `timeout`; `@react-router/dev` e `@remix-run/dev` dichiarati insieme; Remix 1 e React Router prima della 7; moduli di rotta `.mdx`; `ssr: false`; pnpm, Yarn o Bun.
