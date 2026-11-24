# Nuxt: `nuxt prepare`, `@nuxt/kit` e le rotte del progetto

**Stato:** In uso. La sorgente [`daodan/core/premap/nuxt.py`](../../daodan/core/premap/nuxt.py) con lo script `nuxt_pages.mjs` è in `premap.SOURCES` e `FRAMEWORK_SOURCES`, ha la voce `nuxt` in `container_runner.TOOLS` e la tabella `nuxt` in `daodan/data/entry-queries.json`. Aperto: le rotte del server scritte come `export default defineEventHandler(...)` restano sul file con una lacuna, e la sorgente non offre rotte ai collegamenti («Aperto»).

## Domanda

Che dati dà `nuxt prepare` (la cartella `.nuxt/`) per le pagine e per le rotte del server di un progetto Nuxt, e che cosa ne ricava la sorgente. Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 13d del piano).

## Strumento ufficiale provato

Nuxt 3.21.11 (`nuxi` 3.37.0, Nitro 2.13.6) e Nuxt 4.6.4 (`@nuxt/cli` 4.1.0, Nitro 2.13.6); Node 24.22.3, npm 11.19.1. Misurato su Modal il 23 novembre 2026, rete bloccata.

- **Le rotte del server:** `nuxt prepare` scrive `.nuxt/types/nitro-routes.d.ts` con percorso, metodo e file del gestore, in Nuxt 3 e in Nuxt 4.
- **Le pagine:** nessun file che `prepare` scrive per impostazione predefinita le nomina. Le dà l'API ufficiale di `@nuxt/kit` che il progetto installa (`loadNuxt`, `buildNuxt` e l'hook `pages:resolved`): lo script di Daodan la chiama nel container.
- **Valutati e non usati:** la CLI non ha un comando che elenchi le rotte; `nuxt build --prepare` costruisce tutta l'app (5,9 e 5,2 secondi, 727 e 958 MB); `experimental.typedPages: true` dà `typed-router.d.ts` con rotte e file ma cambia la configurazione del progetto; `nuxt prepare --extends <layer>` dà lo stesso file eseguendo un `nuxt.config.ts` in più, nostro; `.nuxt/server-routes.d.ts` di Nuxt 4 ha i percorsi come albero di oggetti a segmenti e non è letto.

## Parametri

| Parametro | Valori |
| --- | --- |
| Comando | `nuxt prepare`; `nuxt build --prepare`; `nuxt prepare --extends <layer fuori dal progetto>`; `nuxt --help`, `nuxi --help`, `nuxt prepare --help`, `nuxt build --help`, `nuxt info`; uno script con `loadNuxt` e `buildNuxt` di `@nuxt/kit` e gli hook `pages:extend` e `pages:resolved` scritto nella sonda (`kit-pages`) e lo script di Daodan `daodan-nuxt` (`pages`); la risoluzione di `@nuxt/kit` e di `nuxt` dalla cartella del progetto (`kit-resolve`) |
| Versioni | Nuxt 3.21.11 (`nuxi` 3.37.0, Nitro 2.13.6, `unplugin-vue-router` 0.19.2) e Nuxt 4.6.4 (`@nuxt/cli` 4.1.0, Nitro 2.13.6, rotte tipate di `vue-router` 4.6.5); Node 24.22.3, npm 11.19.1 |
| Dove stanno i file | `pages/` alla radice (Nuxt 3); `app/pages/` (Nuxt 4); la cartella `app/` di Nuxt 4 spostata alla radice (`nuxt4-root-layout`); `server/` alla radice in tutti; un layer locale con una pagina (`extends: ['./layers/base']`, `layer` e `layer-nuxt4`) |
| Configurazione | con `telemetry: false` e `devtools: { enabled: false }`; senza quelle due righe (`default-config`); senza `nuxt.config.ts`; con `experimental.typedPages: true`; con `buildDir` diverso da `.nuxt`; con una configurazione che lancia; con un hook `pages:extend` il cui file non c'è; con una rotta senza file nello stesso hook (`redirect`); senza la cartella `pages/` |
| Ambiente | quello del runner di Daodan (`PATH`, `HOME`, `npm_config_update_notifier`); con `CI=1`, `NO_COLOR=1`, `NUXT_TELEMETRY_DISABLED=1`; con e senza `npm_config_offline=true`; lo script di Daodan sotto `timeout` (900 secondi, e 0,3 secondi per provare che lo ferma) |
| Stato del progetto | con `.nuxt/` come l'ha lasciata il ripristino (il `postinstall`); con `.nuxt/` tolta; una seconda esecuzione sopra la prima; i pacchetti non installati |

File: `fixture/nuxt3/` e `fixture/nuxt4/` (pagine, layout, gestori del server, una rotta da `pages:extend`, una da `nitro.handlers`; Nuxt 4 ha in più il gruppo `(shop)/checkout`), `modal_probe.py` (`--mode lock`, `--mode probes`, `--mode source`, che registra `tests/fixtures/premap/nuxt/answers.json`), `scan_summary.py`, `results/` (`00_env.json` dà le versioni, `source-run.json` tempi e memoria dei comandi della sorgente, `pipeline-scan.json` il passo `scan` della pipeline).

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/nuxt-routes/modal_probe.py --mode lock
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/nuxt-routes/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/nuxt-routes/modal_probe.py --mode source
DAODAN_FOLDER=<copia di fixture/nuxt3> PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/project-model/modal_pipeline.py --folder-out DIR --folder-stop scan
python benchmarks/nuxt-routes/scan_summary.py DIR
```

## Risultato

**Che cosa dà `nuxt prepare`.**

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

Non dà le righe né le esportazioni: il file del gestore, sempre `.default`.

**Le pagine, dallo script di Daodan.** `nuxt_pages.mjs` (`daodan-nuxt` nel container) risolve `@nuxt/kit` dalla cartella del progetto, chiama `loadNuxt({ overrides: { _prepare: true } })` e `buildNuxt` e ascolta `pages:resolved`; stampa come ultima riga `{"called", "pages": [{name, path, file, children}]}`.

| Misura | Risultato | Uscita |
| --- | --- | --- |
| tempo e memoria | esce 0 in 1,06 (Nuxt 3) e 0,90 secondi (Nuxt 4) nella sonda, 1,37-1,69 nelle registrazioni della sorgente (stesso container, altro momento); memoria massima 274-296 MB; scrive `.nuxt/` come `prepare` (28 file in Nuxt 3, uno in più nel manifesto; 38 in Nuxt 4) e riscrive `types/layouts.d.ts`, ma non genera `.nuxt/dist/` (`_prepare`) | `nuxt3-pages.json`, `nuxt4-pages.json`, `source-run.json` |
| le pagine | 11 rotte in Nuxt 3 e 12 in Nuxt 4, ognuna con il suo file: `quokka` (`/quokka-path`, da `definePageMeta`), `from-hook` (`/from-hook`, da `pages:extend`, dello stesso file di `about`), il gruppo `(shop)/checkout`, `[[page]]`, `[...slug]`; le stesse della strada dei tipi con `typedPages` e della sonda `kit-pages` | `nuxt3-pages.json`, `nuxt4-pages.json`, `*-kit-pages.json`, `*-typed-pages.json` |
| il percorso | di un figlio è relativo al padre (`parent/child` ha `child`), come lo legge vue-router; la sintassi è quella di vue-router (`/users/:id()`, `/:slug(.*)*`, `/blog/:page?`) | `nuxt3-pages.json` |
| un layer | una pagina di un layer locale (`layers/base/pages/from-layer.vue`; in Nuxt 4 `layers/base/app/pages/from-layer.vue`) è nell'elenco con il suo file relativo alla cartella del progetto | `answers.json` (`layer`, `layer-nuxt4`) |
| una rotta senza file | una rotta aggiunta in codice con `redirect` (`/old`) è nell'elenco con `file: null` | `answers.json` (`redirect`) |
| `buildDir` diverso da `.nuxt` | non cambia nulla per lo script (non legge `.nuxt/`): le stesse 11 pagine; `prepare` invece scrive in un'altra cartella | `answers.json` (`build-dir`) |
| senza cartella `pages/` | esce 0 con `{"called":false,"pages":[]}`: Nuxt non chiama l'hook | `answers.json` (`no-pages`) |

**Quando fallisce `prepare`.**

| Caso | Misura | Uscita |
| --- | --- | --- |
| `nuxt.config.ts` che lancia (`nuxt.config needs a database`) | esce 1 in 1,1 e 0,9 secondi, la causa è la prima riga di standard error (`ERROR  nuxt.config needs a database`), la pila dopo; `.nuxt/` non è scritta | `*-config-throws.json` |
| una rotta dell'hook `pages:extend` il cui file non c'è | esce 1 in 1,8 e 1,5 secondi con `ENOENT: no such file or directory, open '/work/.../pages/about.vue'` (`augmentPages`): una rotta con il file mancante fa fallire il comando, a differenza di `react-router routes` | `*-hook-file-missing.json` |
| il comando non è installato, `npx --no-install` | esce 1 dopo **70,4 secondi** con `EAI_AGAIN` su `registry.npmjs.org` (npx chiede comunque il pacchetto `nuxt` al registro) | `nuxt3-not-installed-no-offline.json` |
| lo stesso con `npm_config_offline=true` | esce 1 dopo **0,4 secondi** con `ENOTCACHED … cache mode is 'only-if-cached' but no cached response is available` per `nuxt` | `nuxt3-not-installed.json`, `nuxt4-not-installed.json` |
| senza `pages/` e senza la rotta dell'hook | esce 0 in 1,6-2,0 secondi, `nitro-routes.d.ts` c'è: un'app senza pagine ha comunque le rotte del server (e le due di Nuxt) | `*-no-pages.json` |
| `buildDir` diverso da `.nuxt` | esce 0 e scrive tutto nell'altra cartella: `.nuxt/types/nitro-routes.d.ts` non c'è (`cat`: exit 1) | `answers.json` (variante `build-dir`) |

**Quando fallisce lo script di Daodan** (`answers.json`).

| Caso | Misura | Uscita |
| --- | --- | --- |
| `nuxt.config.ts` che lancia (`nuxt.config needs a database`) | esce 1 in 1,1 e 0,9 secondi, la causa è la prima riga di standard error (`ERROR  nuxt.config needs a database`), la pila dopo; `.nuxt/` non è scritta | `*-config-throws.json` |
| una rotta dell'hook `pages:extend` il cui file non c'è | esce 1 in 1,8 e 1,5 secondi con `ENOENT: no such file or directory, open '/work/.../pages/about.vue'` (`augmentPages`): una rotta con il file mancante fa fallire il comando, a differenza di `react-router routes` | `*-hook-file-missing.json` |
| il comando non è installato, `npx --no-install` | esce 1 dopo **70,4 secondi** con `EAI_AGAIN` su `registry.npmjs.org` (npx chiede comunque il pacchetto `nuxt` al registro) | `nuxt3-not-installed-no-offline.json` |
| lo stesso con `npm_config_offline=true` | esce 1 dopo **0,4 secondi** con `ENOTCACHED … cache mode is 'only-if-cached' but no cached response is available` per `nuxt` | `nuxt3-not-installed.json`, `nuxt4-not-installed.json` |
| senza `pages/` e senza la rotta dell'hook | esce 0 in 1,6-2,0 secondi, `nitro-routes.d.ts` c'è: un'app senza pagine ha comunque le rotte del server (e le due di Nuxt) | `*-no-pages.json` |
| `buildDir` diverso da `.nuxt` | esce 0 e scrive tutto nell'altra cartella: `.nuxt/types/nitro-routes.d.ts` non c'è (`cat`: exit 1) | `answers.json` (variante `build-dir`) |

**La sorgente.** Comandi: `npx --no-install nuxt prepare` con `npm_config_offline=true`, `cat .nuxt/types/nitro-routes.d.ts`, `timeout --kill-after=10 900 daodan-nuxt`. Le risposte registrate per variante sono in `tests/fixtures/premap/nuxt/answers.json`, che `tests/test_codebase_map_premap_nuxt.py` legge.

| Misura | Risultato |
| --- | --- |
| righe che la sorgente ne ricava da `nuxt3` | 22: 11 rotte del server (1 sulla funzione che l'esportazione `default` nomina, `server/api/plain.get.ts`, riga 1, `export default function plain`; **10 sul file con la lacuna**: `export default defineEventHandler(...)` e `eventHandler(...)` sono chiamate, e i record di esportazione dello snapshot non legano la chiamata a una funzione: la ragione è `export-missing`, che non si scrive, e la lacuna elenca i nomi cercati, `default`) e 11 pagine, ognuna sul suo file senza riga e senza lacuna; `nuxt4`: 23 (con `/checkout`) |
| lacune della sorgente | 2, `outside_snapshot`: i file che Nuxt stesso importa per le sue rotte (`node_modules/@nuxt/nitro-server/...`, `server/#internal/nuxt/island-renderer`) |
| il metodo | `GET`, `POST`, `DELETE` dalle chiavi del file; nessuno per `default` (`/api/health`, `/sitemap.xml`) e nessuno per le pagine |
| il percorso delle pagine | l'intero, composto dagli antenati: `/parent/child` per `child` sotto `/parent` (provato con alberi più fondi e con un figlio che comincia con `/` nei test) |

**La pre-mappa intera** (`modal_pipeline.py --folder-stop scan` su `fixture/nuxt3`, `results/pipeline-scan.json`; misurata con la sorgente `v1`, oggi `VERSION` è `daodan/premap/v2`: non rimisurata):

| Misura | Risultato |
| --- | --- |
| `scan`, tutto | 146,1 secondi (con `tsc` 21,3 s, `npm` 6,8 s, `noir` 12,6 s) |
| sorgente `nuxt@daodan/premap/v1` | `ran`, 29,1 secondi, compreso il ripristino dei pacchetti e i tre comandi |
| `framework_entries` in `premap.json` | 22 righe (11 rotte del server, di cui 1 sulla funzione e 10 con la lacuna, e 11 pagine), 2 lacune della sorgente: le stesse della risposta registrata |
| `next`, `react-router` e `angular` | `not_needed`: la fixture non li dichiara |
| Noir sulla stessa fixture | 10 endpoint `http` negli stessi file, con il suo metodo (`ANY` per `health.ts` e `sitemap.xml.ts`) e il suo modo di scrivere il percorso (`/api/files/:path`), senza il nome del gestore, e senza `/api/from-config` (è nel config, non nel nome di un file); nessuna pagina: nei collegamenti sono 10 lacune «noir reports this entry without a unique snapshot handler at its site», non ingressi |
| collegamenti | 12 ingressi (`nuxt rotta`: 11 pagine, ognuna sul suo file, e `GET /api/plain` su `server/api/plain.get.ts:1`), `routes` `{offered: 0, called: 0, linked: 0}`, 20 lacune: le 10 di Noir e le 10 righe di lacuna di Nuxt |

## Aperto

- **Le rotte del server senza funzione.** 10 gestori su 11 della fixture sono `export default defineEventHandler(...)`: una chiamata, che i record di esportazione dello snapshot non legano a una funzione; la riga resta sul file con la lacuna. Se il passo dinamico osserva la funzione che risponde non è misurato.
- **Le rotte offerte.** Le righe sono ingressi: la sorgente non alimenta `routes.offered`. Servirebbero la funzione del gestore, la conversione del percorso (`**:path` sta per più schemi), il significato di `default` (ogni metodo) e lo `schema` sulle righe, che `flows._declared_routes` chiede.
- **Noir e Nuxt sulla stessa rotta.** Oggi `flows.link_facts` unisce una rotta di Noir a una riga legata e senza lacuna di una sorgente di `FRAMEWORK_SOURCES`, sullo stesso percorso e nello stesso file o sulla stessa funzione. La misura sopra è precedente (le righe non si univano) e non è rifatta: quante righe di Noir e di Nuxt si uniscono, con Nitro che scrive `:id` e Noir il suo schema, non è misurato.
- **Un progetto reale:** la sorgente è stata eseguita solo sulle due fixture; tempo e memoria su un progetto con molti moduli non sono misurati (massimo misurato 0,4 GB, contro `memory: 3` di `TOOLS`).
- **Non provati:** Nuxt 2, Nuxt 3 prima della 3.21, Nitro 3; `@nuxt/kit` con pnpm o Yarn (la disposizione stretta di pnpm può non averlo nella cartella del progetto); i moduli che aggiungono rotte (`addServerHandler`, `extendPages`), i layer con un loro `server/`, `srcDir` e `serverDir` diversi dal predefinito, un gestore `.mts`, `.mjs` o `.cjs`; un'app dove `loadNuxt` apre connessioni.
