# Nuxt: `nuxt prepare`, `@nuxt/kit` e le rotte del progetto

Domanda: che dati dà `nuxt prepare` (la cartella `.nuxt/`) per le pagine e per le rotte del server di un progetto Nuxt, e che cosa ne ricava la sorgente
della pre-mappa [`daodan/core/premap/nuxt.py`](../../daodan/core/premap/nuxt.py). Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md),
task 13d («prima si verifica che i tipi generati nominino le pagine: la documentazione non lo dice»); spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6.

**Risultato in una riga:** `nuxt prepare` dà, per le rotte **del server** (Nitro), il percorso, il metodo e il file del gestore, in Nuxt 3 e in Nuxt 4; **non dà le pagine**: nessun
file che scrive per impostazione predefinita le nomina. Le pagine con il loro file le dà l'API ufficiale di `@nuxt/kit` (`loadNuxt`, `buildNuxt` e l'hook `pages:resolved`), che
il progetto installa: uno script di Daodan (`daodan/core/premap/nuxt_pages.mjs`, come `angular_templates.mjs`) la chiama nel container, e la sorgente legge le due uscite.

Tutto gira su Modal, in un container con la rete bloccata: il codice del progetto (`nuxt.config.ts`, i moduli, i layer, `node_modules`) gira solo lì, e i pacchetti sono ripristinati dal
`package-lock.json` mentre l'immagine si costruisce, l'unico momento con la rete aperta. Niente di tutto questo gira su questo PC.

| Cartella | Contenuto |
| --- | --- |
| `fixture/nuxt3/` | Nuxt 3.21.11 con `package-lock.json` (ogni `resolved` punta a `registry.npmjs.org`), `postinstall: nuxt prepare` come nel progetto di partenza di Nuxt: `app.vue`, due layout, un middleware, dieci pagine (`index`, `about`, `[...slug]`, `users/[id]`, `foo/index`, `foo/bar`, `parent` con il figlio `parent/child`, `blog/[[page]]`, `legacy` con `definePageMeta({ path, name, layout })`), una rotta aggiunta dall'hook `pages:extend` del config, undici gestori del server (`server/api/*.get.ts`, `*.post.ts`, `*.delete.ts`, uno senza metodo nel nome, uno scritto come `export default function`, un catch-all `[...path]`, `server/routes/sitemap.xml.ts` e `feed.get.ts`, un middleware del server) e una rotta del server dichiarata nel config (`nitro.handlers`: `POST /api/from-config`) |
| `fixture/nuxt4/` | Nuxt 4.6.4 con la sua cartella `app/` (`app/pages`, `app/layouts`, `app/app.vue`) e `server/` alla radice; le stesse pagine più un gruppo di rotte `(shop)/checkout`, gli stessi gestori |
| `results/` | l'uscita di ogni comando provato su Modal il 23 novembre 2026 (`00_env.json` dà le versioni), `source-run.json` (tempi, memoria e file lasciati dei comandi della sorgente, variante per variante) e `pipeline-scan.json`, il passo `scan` della pipeline intera. Ogni file di `modal_probe.py` ha, per comando: `argv`, uscita, secondi, memoria massima, i file che il comando ha scritto nel progetto, in `node_modules/.cache` e nella `HOME`, l'elenco di `.nuxt/` con le dimensioni e il testo dei file di `.nuxt/` che nominano una pagina, un gestore o un segno della fixture |
| `modal_probe.py` | `--mode lock` scrive i `package-lock.json`; `--mode probes` esegue le varianti di `COMMANDS` (e `VARIANTS=a,b` ne sceglie alcune); `--mode source` esegue la sorgente di Daodan e registra le risposte in `tests/fixtures/premap/nuxt/answers.json` |
| `scan_summary.py` | riassume in `results/pipeline-scan.json` ciò che `scan` ha scritto per `fixture/nuxt3` |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/nuxt-routes/modal_probe.py --mode lock
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/nuxt-routes/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/nuxt-routes/modal_probe.py --mode source
DAODAN_FOLDER=<copia di fixture/nuxt3> PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/project-model/modal_pipeline.py --folder-out DIR --folder-stop scan
python benchmarks/nuxt-routes/scan_summary.py DIR
```

## Parametri provati

| Parametro | Valori |
| --- | --- |
| Comando | `nuxt prepare`; `nuxt build --prepare`; `nuxt prepare --extends <layer fuori dal progetto>`; `nuxt --help`, `nuxi --help`, `nuxt prepare --help`, `nuxt build --help`, `nuxt info`; uno script con `loadNuxt` e `buildNuxt` di `@nuxt/kit` e gli hook `pages:extend` e `pages:resolved` scritto nella sonda (`kit-pages`) e lo script di Daodan `daodan-nuxt` (`pages`); la risoluzione di `@nuxt/kit` e di `nuxt` dalla cartella del progetto (`kit-resolve`) |
| Versioni | Nuxt 3.21.11 (`nuxi` 3.37.0, Nitro 2.13.6, `unplugin-vue-router` 0.19.2) e Nuxt 4.6.4 (`@nuxt/cli` 4.1.0, Nitro 2.13.6, rotte tipate di `vue-router` 4.6.5); Node 24.22.3, npm 11.19.1 |
| Dove stanno i file | `pages/` alla radice (Nuxt 3); `app/pages/` (Nuxt 4); la cartella `app/` di Nuxt 4 spostata alla radice (`nuxt4-root-layout`); `server/` alla radice in tutti; un layer locale con una pagina (`extends: ['./layers/base']`, `layer` e `layer-nuxt4`) |
| Configurazione | con `telemetry: false` e `devtools: { enabled: false }`; senza quelle due righe (`default-config`); senza `nuxt.config.ts`; con `experimental.typedPages: true`; con `buildDir` diverso da `.nuxt`; con una configurazione che lancia; con un hook `pages:extend` il cui file non c'è; con una rotta senza file nello stesso hook (`redirect`); senza la cartella `pages/` |
| Ambiente | quello del runner di Daodan (`PATH`, `HOME`, `npm_config_update_notifier`); con `CI=1`, `NO_COLOR=1`, `NUXT_TELEMETRY_DISABLED=1`; con e senza `npm_config_offline=true`; lo script di Daodan sotto `timeout` (900 secondi, e 0,3 secondi per provare che lo ferma) |
| Stato del progetto | con `.nuxt/` come l'ha lasciata il ripristino (il `postinstall`); con `.nuxt/` tolta; una seconda esecuzione sopra la prima; i pacchetti non installati |

## Che cosa dà `nuxt prepare`, misurato (rete bloccata)

| Misura | Risultato | Uscita |
| --- | --- | --- |
| tempo e memoria | esce 0 in 1,79-2,0 secondi (Nuxt 3) e 1,57-1,76 (Nuxt 4), in ogni variante che ha le sue dipendenze; memoria massima 287-318 MB, 398 MB in Nuxt 3 e 310 MB in Nuxt 4 senza le due righe del config che spengono gli strumenti di sviluppo (`default-config`); sullo standard output una riga (`Types generated in .nuxt.`), standard error vuoto | `nuxt3-prepare.json`, `nuxt4-prepare.json`, `*-default-config.json` |
| che cosa scrive | `.nuxt/`: 27 file (Nuxt 3) e 38 (Nuxt 4), tutti dichiarazioni di tipi, `tsconfig*.json` e `manifest/`; solo Nuxt 3 lascia anche `node_modules/.cache/jiti/<config>.mjs`; in `HOME` solo il registro di `npx` (`.npm/_logs/`); nel progetto, fuori da `.nuxt/` e dalla cache, niente | `nuxt3-prepare.json`, `nuxt4-prepare.json` |
| il ripristino l'ha già eseguito | con `postinstall: nuxt prepare` (come nel progetto di partenza di Nuxt) `npm ci` con gli script lascia `.nuxt/` con gli stessi 27 e 38 file, `nitro-routes.d.ts` compreso; una seconda esecuzione ne riscrive due (`layouts.d.ts`, `nitro-imports.d.ts`) in 1,6-1,8 secondi. Il container di Daodan ripristina con gli script: la sorgente lancia il comando comunque, perché il progetto può non avere il `postinstall` | `*-after-restore.json`, `*-prepare-again.json` |
| l'ambiente non cambia nulla | con o senza `CI=1`, `NO_COLOR=1`, `NUXT_TELEMETRY_DISABLED=1`, con o senza `npm_config_offline`, e senza le due righe del config che spengono telemetria e strumenti di sviluppo: stessa uscita, esce 0, standard error vuoto (nessun tentativo di rete visibile) | `*-prepare-ci-no-telemetry.json`, `*-prepare-no-offline.json`, `*-default-config.json` |
| **le rotte del server** | `.nuxt/types/nitro-routes.d.ts` (2057 byte in Nuxt 3 e in Nuxt 4, scritto da Nitro): l'interfaccia `InternalApi` ha una proprietà per rotta (11: le 9 del progetto e 2 di Nuxt) e, dentro, una per metodo (13 coppie): la chiave è `get`, `post`, `delete` o `default` (il gestore senza metodo nel nome del file: `health.ts`, `sitemap.xml.ts`), il valore contiene `typeof import('../../server/api/users/[id].get').default`: il file del gestore, relativo a `.nuxt/types/` e senza estensione. Il percorso è come lo scrive Nitro: `/api/users/:id`, `/api/files/**:path` | `nuxt3-prepare.json`, `nuxt4-prepare.json` |
| da dove vengono le rotte del server | `server/api/`, `server/routes/` e le `nitro.handlers` del config: `/api/from-config` (`post`, `server/custom/config-handler`) c'è, e il config è codice che il comando ha eseguito. `server/middleware/log.ts` non c'è (non è una rotta) | `nuxt3-prepare.json` |
| due rotte di Nuxt | `/__nuxt_error` (importa `node_modules/@nuxt/nitro-server/dist/runtime/handlers/renderer`) e `/__nuxt_island/**` (importa `server/#internal/nuxt/island-renderer`, un modulo virtuale): in ogni progetto, e nessuno dei due è un file del progetto | `nuxt3-prepare.json` |
| Nuxt 4 in più | `.nuxt/server-routes.d.ts` (8591 byte, `fetchdts`): gli stessi gestori con il metodo in maiuscole, ma i percorsi sono un albero di oggetti a segmenti (`[DynamicParam]`, `[WildcardParam]`): non è letto | `nuxt4-prepare.json` |
| la cartella dell'app | gli `import` sono relativi a `.nuxt/types/`, quindi `../../server/...` per qualunque posizione dell'app (`app/`, radice): le due disposizioni di Nuxt 4 danno lo stesso file | `nuxt4-root-layout.json` (in `answers.json`) |

## Che cosa non dà

| Dato | Misura | Uscita |
| --- | --- | --- |
| **le pagine** | nessuno dei file di `.nuxt/` scritti per impostazione predefinita le nomina, in Nuxt 3 e in Nuxt 4: né `routes.mjs`, né un file di tipi con `about`, `foo/bar`, `users/:id`, `quokka` o `from-hook`; i soli file che contengono `pages/` sono i componenti di Nuxt (`node_modules/nuxt/dist/pages/runtime/...`). `layouts.d.ts` nomina i layout (`admin`, `default`), che non sono rotte, con percorsi assoluti del container | `nuxt3-prepare.json`, `nuxt4-prepare.json` |
| le righe | nessuna: il file del gestore e basta | `nuxt3-prepare.json` |
| le esportazioni | sempre `.default`: non dice se il file esporta una funzione dichiarata o una chiamata (`defineEventHandler(...)`) | `nuxt3-prepare.json` |
| un comando che elenchi le rotte | la CLI non ne ha: `nuxi` 3.37.0 ha `add`, `add-template`, `analyze`, `build`, `cleanup`, `dev`, `devtools`, `generate`, `info`, `init`, `module`, `prepare`, `preview`, `start`, `test`, `typecheck`, `upgrade`; `@nuxt/cli` 4.1.0 ha gli stessi meno `init` e `start`, più `curl`, `docs` e `task`; `nuxt info` stampa l'ambiente e il config. `typecheck` chiede `vue-tsc` (non installato nelle fixture), `curl` e `task` il server di sviluppo: non eseguiti | `nuxt3-help.json`, `nuxt4-help.json` |
| `nuxt build --prepare` | non è una preparazione: costruisce tutta l'app (5,9 e 5,2 secondi, 727 e 958 MB di memoria, 87 e 93 file in più in `.nuxt/`, quasi tutti in `.nuxt/dist/`, 331 e 345 file nuovi nel progetto fuori da `node_modules`), e non scrive `typed-router.d.ts`. Scartato | `nuxt3-build-prepare.json`, `nuxt4-build-prepare.json` |

## Le pagine: `@nuxt/kit`, lo script di Daodan

`nuxt_pages.mjs` (`daodan-nuxt` nel container) risolve `@nuxt/kit` dalla cartella del progetto (npm lo mette accanto a `nuxt`: misurato in Nuxt 3.21.11 e 4.6.4; `nuxt` stesso non si risolve con
`require.resolve`, `ERR_PACKAGE_PATH_NOT_EXPORTED`, e basta `@nuxt/kit`), chiama `loadNuxt({ overrides: { _prepare: true } })` e `buildNuxt`, e ascolta l'hook `pages:resolved`: Nuxt lo chiama con le
rotte che ha ricavato dalle pagine, dopo gli hook `pages:extend` del progetto, i suoi moduli e i suoi layer. Stampa come ultima riga `{"called", "pages": [{name, path, file, children}]}` con il `file`
relativo alla cartella del progetto (null per una rotta senza file).

| Misura | Risultato | Uscita |
| --- | --- | --- |
| tempo e memoria | esce 0 in 1,06 (Nuxt 3) e 0,90 secondi (Nuxt 4) nella sonda, 1,37-1,69 nelle registrazioni della sorgente (stesso container, altro momento); memoria massima 274-296 MB; scrive `.nuxt/` come `prepare` (28 file in Nuxt 3, uno in più nel manifesto; 38 in Nuxt 4) e riscrive `types/layouts.d.ts`, ma non genera `.nuxt/dist/` (`_prepare`) | `nuxt3-pages.json`, `nuxt4-pages.json`, `source-run.json` |
| le pagine | 11 rotte in Nuxt 3 e 12 in Nuxt 4, ognuna con il suo file: `quokka` (`/quokka-path`, da `definePageMeta`), `from-hook` (`/from-hook`, da `pages:extend`, dello stesso file di `about`), il gruppo `(shop)/checkout`, `[[page]]`, `[...slug]`; le stesse della strada dei tipi con `typedPages` e della sonda `kit-pages` | `nuxt3-pages.json`, `nuxt4-pages.json`, `*-kit-pages.json`, `*-typed-pages.json` |
| il percorso | di un figlio è relativo al padre (`parent/child` ha `child`), come lo legge vue-router; la sintassi è quella di vue-router (`/users/:id()`, `/:slug(.*)*`, `/blog/:page?`) | `nuxt3-pages.json` |
| un layer | una pagina di un layer locale (`layers/base/pages/from-layer.vue`; in Nuxt 4 `layers/base/app/pages/from-layer.vue`) è nell'elenco con il suo file relativo alla cartella del progetto | `answers.json` (`layer`, `layer-nuxt4`) |
| una rotta senza file | una rotta aggiunta in codice con `redirect` (`/old`) è nell'elenco con `file: null` | `answers.json` (`redirect`) |
| `buildDir` diverso da `.nuxt` | non cambia nulla per lo script (non legge `.nuxt/`): le stesse 11 pagine; `prepare` invece scrive in un'altra cartella | `answers.json` (`build-dir`) |
| senza cartella `pages/` | esce 0 con `{"called":false,"pages":[]}`: Nuxt non chiama l'hook | `answers.json` (`no-pages`) |

Le altre due strade (valutate prima, non usate):

| Strada | Misura | Uscita |
| --- | --- | --- |
| `experimental.typedPages: true` nel config del progetto | `.nuxt/types/typed-router.d.ts` (4230 byte in Nuxt 3, 5143 in Nuxt 4), esce 0 in 1,7-1,8 secondi: `RouteNamedMap` ha nome, percorso e parametri di 11 (Nuxt 3) e 12 rotte (Nuxt 4); `_RouteFileInfoMap` lega ogni file (relativo alla radice del progetto) ai nomi delle rotte: 10 e 11 file. I layout non ci sono. Cambia la configurazione del progetto | `nuxt3-typed-pages.json`, `nuxt4-typed-pages.json` |
| `nuxt prepare --extends <cartella>` | l'opzione ufficiale `-e, --extends=<layer-name>` accetta un layer fuori dal progetto: con un layer che ha solo `experimental: { typedPages: true }` la stessa `typed-router.d.ts` (4230 e 5143 byte) in 1,7-1,9 secondi, 302-364 MB. Il comando esegue un `nuxt.config.ts` in più, nostro | `nuxt3-extends-layer.json`, `nuxt4-extends-layer.json` |

Quando fallisce, `prepare`:

| Caso | Misura | Uscita |
| --- | --- | --- |
| `nuxt.config.ts` che lancia (`nuxt.config needs a database`) | esce 1 in 1,1 e 0,9 secondi, la causa è la prima riga di standard error (`ERROR  nuxt.config needs a database`), la pila dopo; `.nuxt/` non è scritta | `*-config-throws.json` |
| una rotta dell'hook `pages:extend` il cui file non c'è | esce 1 in 1,8 e 1,5 secondi con `ENOENT: no such file or directory, open '/work/.../pages/about.vue'` (`augmentPages`): una rotta con il file mancante fa fallire il comando, a differenza di `react-router routes` | `*-hook-file-missing.json` |
| il comando non è installato, `npx --no-install` | esce 1 dopo **70,4 secondi** con `EAI_AGAIN` su `registry.npmjs.org` (npx chiede comunque il pacchetto `nuxt` al registro) | `nuxt3-not-installed-no-offline.json` |
| lo stesso con `npm_config_offline=true` | esce 1 dopo **0,4 secondi** con `ENOTCACHED … cache mode is 'only-if-cached' but no cached response is available` per `nuxt` | `nuxt3-not-installed.json`, `nuxt4-not-installed.json` |
| senza `pages/` e senza la rotta dell'hook | esce 0 in 1,6-2,0 secondi, `nitro-routes.d.ts` c'è: un'app senza pagine ha comunque le rotte del server (e le due di Nuxt) | `*-no-pages.json` |
| `buildDir` diverso da `.nuxt` | esce 0 e scrive tutto nell'altra cartella: `.nuxt/types/nitro-routes.d.ts` non c'è (`cat`: exit 1) | `answers.json` (variante `build-dir`) |

Quando fallisce lo script di Daodan (le risposte come le restituisce il container, `answers.json`):

| Caso | Misura |
| --- | --- |
| `nuxt.config.ts` che lancia | exit 5 in 0,44-0,77 secondi, `daodan-nuxt: loadNuxt failed: nuxt.config needs a database` (la prima riga dell'errore, non la pila) |
| `@nuxt/kit` non installato | exit 3 in 0,07-0,10 secondi, `daodan-nuxt: @nuxt/kit is not installed for <cartella>: Cannot find module '@nuxt/kit'` |
| una rotta dell'hook con il file mancante | exit 6, `daodan-nuxt: buildNuxt failed: ENOENT: no such file or directory, open '<cartella>/pages/about.vue'` |
| tempo scaduto | `timeout` con 0,3 secondi esce 124 dopo 0,37 secondi, senza uscita (la passata normale dura 0,9-1,7 secondi: con 1 secondo non si fermava) |

## La sorgente su Modal

`--mode source`: la sorgente dà i comandi per ogni fixture (una funzione con la rete aperta, perché il pacchetto delle grammatiche di Daodan si scarica), poi ogni comando gira con
la rete bloccata, con l'`argv` e l'ambiente che la sorgente ha scritto (`npx --no-install nuxt prepare` con `npm_config_offline=true`, `cat .nuxt/types/nitro-routes.d.ts`, e
`timeout --kill-after=10 900 daodan-nuxt`), in una copia del progetto con i suoi pacchetti e `.nuxt/` come l'ha lasciata il ripristino, in copie con un cambiamento che le interessa e in una copia senza i pacchetti. Le risposte, come le restituisce il
container, sono in `tests/fixtures/premap/nuxt/answers.json`, che `tests/test_codebase_map_premap_nuxt.py` legge (Python puro, senza motore); i tempi e la memoria sono in `results/source-run.json`.

| Variante | Risposta (`prepare`, `cat`, `daodan-nuxt`) |
| --- | --- |
| `nuxt3`, `nuxt4`, `nuxt4-root-layout` | esce 0, 0, 0: 2057 byte di `cat` nei tre casi, 890, 1026 e 978 byte dello script |
| `layer`, `layer-nuxt4`, `redirect` | esce 0, 0, 0: 989, 1129 e 945 byte dello script (una pagina in più, una pagina in più, una rotta senza file) |
| `no-pages` | esce 0, 0, 0: 1909 byte di `cat` (senza `/api/from-config`, che era nel config), lo script `called: false` |
| `config-throws` | `prepare` esce 1 (`ERROR  nuxt.config needs a database`); il `cat` trova ancora il file che il ripristino aveva scritto, e la sorgente non lo guarda; lo script esce 5 |
| `build-dir` | `prepare` esce 0, `cat` esce 1 (`No such file or directory`), lo script esce 0 con le 11 pagine |
| `hook-file-missing` | `prepare` esce 1, `cat` esce 1, lo script esce 6 |
| `not-installed` | `prepare` esce 1 in 0,4-0,6 secondi (`ENOTCACHED`), lo script esce 3 |
| `timeout` | `prepare` e `cat` esce 0, lo script esce 124 |

| Misura | Risultato |
| --- | --- |
| righe che la sorgente ne ricava da `nuxt3` | 22: 11 rotte del server (1 sulla funzione che l'esportazione `default` nomina, `server/api/plain.get.ts`, riga 1, `export default function plain`; **10 sul file con la lacuna**: `export default defineEventHandler(...)` e `eventHandler(...)` sono chiamate, e i record di esportazione dello snapshot non legano la chiamata a una funzione: la ragione è `export-missing`, che non si scrive, e la lacuna elenca i nomi cercati, `default`) e 11 pagine, ognuna sul suo file senza riga e senza lacuna; `nuxt4`: 23 (con `/checkout`) |
| lacune della sorgente | 2, `outside_snapshot`: i file che Nuxt stesso importa per le sue rotte (`node_modules/@nuxt/nitro-server/...`, `server/#internal/nuxt/island-renderer`) |
| il metodo | `GET`, `POST`, `DELETE` dalle chiavi del file; nessuno per `default` (`/api/health`, `/sitemap.xml`) e nessuno per le pagine |
| il percorso delle pagine | l'intero, composto dagli antenati: `/parent/child` per `child` sotto `/parent` (provato con alberi più fondi e con un figlio che comincia con `/` nei test) |

### La pre-mappa intera, nel container di Daodan

`DAODAN_FOLDER=<copia di fixture/nuxt3> … modal_pipeline.py --folder-out DIR --folder-stop scan` esegue il passo `scan` della pipeline su Modal con la sorgente registrata: il ripristino dei pacchetti dal
`package-lock.json` con la rete aperta ai soli registri (il `postinstall` compreso), poi i comandi con la rete bloccata, come li lancia `container_runner`. `results/pipeline-scan.json`
tiene gli stati delle sorgenti, le righe di `framework_entries`, le lacune della sorgente e i collegamenti che `flows.link_facts` ne ricava.

| Misura | Risultato |
| --- | --- |
| `scan`, tutto | 146,1 secondi (con `tsc` 21,3 s, `npm` 6,8 s, `noir` 12,6 s) |
| sorgente `nuxt@daodan/premap/v1` | `ran`, 29,1 secondi, compreso il ripristino dei pacchetti e i tre comandi |
| `framework_entries` in `premap.json` | 22 righe (11 rotte del server, di cui 1 sulla funzione e 10 con la lacuna, e 11 pagine), 2 lacune della sorgente: le stesse della risposta registrata |
| `next`, `react-router` e `angular` | `not_needed`: la fixture non li dichiara |
| Noir sulla stessa fixture | 10 endpoint `http` negli stessi file, con il suo metodo (`ANY` per `health.ts` e `sitemap.xml.ts`) e il suo modo di scrivere il percorso (`/api/files/:path`), senza il nome del gestore, e senza `/api/from-config` (è nel config, non nel nome di un file); nessuna pagina: nei collegamenti sono 10 lacune «Noir reports this endpoint without a unique snapshot handler», non ingressi |
| collegamenti | 12 ingressi (`nuxt rotta`: 11 pagine, ognuna sul suo file, e `GET /api/plain` su `server/api/plain.get.ts:1`), `routes` `{offered: 0, called: 0, linked: 0}`, 20 lacune: le 10 di Noir e le 10 righe di lacuna di Nuxt |

## Non provato

- Un progetto reale: la sorgente è stata eseguita solo su queste due fixture; nessuna riga è stata confrontata a mano con un'app esistente, e il tempo e la memoria di `prepare` e dello script su un progetto con molti moduli non sono misurati (l'impostazione `memory: 3` di `TOOLS` è quella di Next.js: l'uso massimo misurato è 0,4 GB sulle fixture, 1 GB per `nuxt build --prepare`, che non si usa).
- Nuxt 2 (non ha `prepare` né `@nuxt/kit` 3: il comando uscirebbe con un errore e la sorgente darebbe una lacuna `model_failed`, non eseguito), una versione di Nuxt 3 prima della 3.21 e Nitro 3 (se Nuxt lo adotta, il nome e il formato del file possono cambiare: una lacuna «non scritto» o «non letto per intero»); l'hook `pages:resolved` in una versione che non lo chiama darebbe `called: false`.
- `@nuxt/kit` con pnpm o Yarn: lo script lo risolve dalla cartella del progetto, dove npm lo mette; la disposizione stretta di pnpm può non averlo lì (exit 3 e una lacuna con la causa, non provato). I `package-lock.json` delle fixture sono di npm.
- I moduli che aggiungono rotte (`addServerHandler`, `extendPages`), i layer con un loro `server/`, `srcDir` e `serverDir` diversi dal predefinito, un gestore `.mts`, `.mjs` o `.cjs`: nessun caso è in una fixture (il layer con una pagina sì).
- Un progetto che dichiara `nuxt` in due cartelle: una serie di righe per cartella, provato solo con i test sulle risposte registrate.
- Un'app dove `loadNuxt` apre connessioni (un modulo che si collega a un servizio): la rete è bloccata, il comando fallirebbe con la causa del modulo, non provato.
- Le rotte offerte. Le righe sono ingressi: il file dà il metodo, ma la sorgente non alimenta `routes.offered`. Servirebbero: la funzione del gestore (oggi 10 su 11 sono una chiamata che lo snapshot non lega), la conversione del percorso (`:id` è già uno schema, `**:path` sta per più schemi come il catch-all di Next.js e sarebbe una lacuna), il significato di `default` (ogni metodo) per la chiave dell'unione, e la tavola `http` di `flows._declared_routes`, che oggi nomina solo Noir e Next.js. Le pagine non hanno un metodo né sono rotte offerte.
- Noir e Nuxt sulla stessa rotta: le righe non si uniscono, perché l'unione di `flows.link_facts` riguarda solo le rotte di Next.js; nel caso misurato Noir non dà il nome del gestore e le sue 10 righe sono lacune, ma un progetto dove lo dà avrebbe due ingressi per rotta.
- Il campo `page` delle righe: lo introdurrà la rifattorizzazione 8.13; oggi una pagina è una riga di forma `page` e tipo «rotta» (`QUERIES["nuxt"]`), come una pagina di Next.js.
