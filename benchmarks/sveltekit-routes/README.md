# SvelteKit: `svelte-kit sync` del comando che il progetto installa

**Stato:** In uso. La sorgente [`daodan/core/premap/sveltekit.py`](../../daodan/core/premap/sveltekit.py) è in `premap.SOURCES` e `FRAMEWORK_SOURCES`, ha la voce `sveltekit` in `container_runner.TOOLS` e la tabella `sveltekit` in `daodan/data/entry-queries.json`. Aperto: i membri di `actions` non si legano a una funzione, la sorgente non offre rotte ai collegamenti, e il file che legge non è l'uscita documentata del comando («Aperto»).

## Domanda

Che dati dà `svelte-kit sync` per le rotte di un progetto, e che cosa ne ricava la sorgente. Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 13c del piano).

## Strumento ufficiale provato

`@sveltejs/kit` 2.70.4 (Svelte 5.59.1, Vite 7.3.8), e 2.0.0, 2.15.0, 2.40.0 sugli stessi file; Node 24.22.3, npm 11.19.1. Misurato su Modal il 23 novembre 2026, rete bloccata.

La sorgente legge `.svelte-kit/types/route_meta_data.json`, `{id della rotta: [file, …]}`. Non è l'uscita che svelte.dev/docs/kit/cli promette (`tsconfig.json` e i tipi): è la memoria che il tool tiene per rigenerare solo le rotte cambiate. È uguale, byte per byte, nelle quattro versioni misurate; una versione che ne cambia la forma è una lacuna.

Valutati e non usati: `$types.d.ts` (l'id e i tipi di una cartella, nessun nome di file né metodo di un `+server`), `non-ambient.d.ts` (`RouteId()` elenca anche 6 cartelle che non sono rotte), `generated/client/app.js` con `nodes/N.js` (solo le pagine, mai un file `.server.` né un `+server`).

## Parametri

| Parametro | Valori |
| --- | --- |
| Comando | `svelte-kit --help`, `svelte-kit sync --help`, `svelte-kit sync` (due volte di seguito) |
| Dove stanno le rotte e l'uscita | `src/routes` (predefinita); `kit.files.routes: 'src/pages'`; `kit.outDir: '.kit-out'`; nessuna cartella `src/routes` |
| Che cosa manca o si rompe | `svelte.config.js` che lancia; con un errore di sintassi; due rotte che si scontrano (`(a)/x`, `(b)/x`); `[id=nomatcher]` senza il confronto in `src/params`; un `+page.server.ts` con un errore di sintassi; un sync che fallisce dopo uno riuscito; due rotte tolte fra un sync e l'altro |
| Versione | SvelteKit 2.0.0, 2.15.0, 2.40.0, 2.70.4 |
| Pacchetti | installati; non installati, con `npx --no-install` senza e con `npm_config_offline=true` (rete bloccata) |

File: `fixture/routes/` (SvelteKit 2.70.4: layout, pagine, `load`, `actions`, endpoint `+server.ts`, segmenti dinamici, un gruppo `(shop)`, una riesportazione, `GET = make('get')`), `fixture/kit-2.0.0/`, `kit-2.15.0/`, `kit-2.40.0/` (solo `package.json` e lockfile: i loro pacchetti girano sui file di `fixture/routes/`), `modal_probe.py` (`--mode lock`, `--mode probes`, `--mode source`, che registra `tests/fixtures/premap/sveltekit/answers.json`), `scan_summary.py`, `results/` (`00_env.json` dà le versioni).

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/sveltekit-routes/modal_probe.py --mode lock
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/sveltekit-routes/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/sveltekit-routes/modal_probe.py --mode source
DAODAN_FOLDER=<copia di fixture/routes> PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/project-model/modal_pipeline.py --folder-out DIR --folder-stop scan
python benchmarks/sveltekit-routes/scan_summary.py DIR
```

## Risultato

**Che cosa dà `svelte-kit sync`.**

| Misura | Risultato | Uscita |
| --- | --- | --- |
| uscita del comando | niente sullo standard output e sullo standard error, esce 0 in 1,0-2,4 secondi nelle corse (1,4-1,8 nell'ultima serie di sonde) | `sync.json` |
| che cosa scrive | solo `.svelte-kit/`, 58 file: `ambient.d.ts`, `env.d.ts`, `non-ambient.d.ts`, `tsconfig.json`, `generated/` (23: `client/app.js`, `matchers.js`, 17 `nodes/N.js`, `root.js`, `root.svelte`, `server/internal.js`, `shared/error-template.js`) e `types/` (31: `route_meta_data.json`, 20 `$types.d.ts`, 10 copie `proxy+…` dei moduli del progetto); nient'altro nel progetto (`left_in_the_project`); una seconda volta niente di nuovo e lo stesso testo di tutti i file (42 confrontati) | `sync.json` |
| `ambient.d.ts` | elenca i **nomi** delle variabili d'ambiente del processo, con il tipo `string` (i `.env` del progetto non sono stati provati); nei file dei risultati non è tenuto | `sync.json` |
| `types/route_meta_data.json` | `{id della rotta: [file, …]}`: 20 id, 18 file distinti; per ogni rotta i moduli da cui il tool genera i tipi (il sorgente del tool, letto nel container: `input_files` dal nodo della foglia e dei suoi genitori, poi dal layout, poi l'endpoint), con il percorso relativo al progetto e l'estensione vera (`src/routes/api/pay/+server.ts`, `src/routes/legacy/+page.js`); ogni rotta elenca anche i layout sopra di sé, quindi `src/routes/+layout.server.ts` è elencato da 15 rotte su 20, e `src/routes/+layout.ts` due volte da `/` | `sync.json`, `kit-source.json` |
| a chi appartiene un file | il tool non lo dice: la rotta col minor numero di segmenti che lo elenca è sempre quella la cui cartella lo contiene (18 file su 18, nessun pareggio); un layout di `(shop)` è elencato da 3 rotte, non da `/(shop)/receipt`, la cui pagina lo azzera con `+page@.svelte` | `sync.json` |
| `types/src/routes/**/$types.d.ts` | uno per ogni cartella con una pagina, un layout o un endpoint (20): `RouteId`, `RouteParams` e i tipi che quella cartella ha (`PageServerLoad`, `Actions`, `RequestHandler`…): nessun nome di file, tranne dove il tipo importa il modulo (`reexport`); non dà il metodo di un `+server`, che ha un solo tipo `RequestHandler` | `sync.json` |
| `non-ambient.d.ts` | `RouteId()` elenca 26 id: le 20 rotte e 6 cartelle che non sono rotte (`/api`, `/api/items`, `/components`, `/docs`, `/items`, `/lang`); `Pathname()` è un'unione a parte, con i segmenti dinamici come `${string}`: nessun legame fra l'id e il percorso | `sync.json` |
| `generated/client/app.js` e `nodes/N.js` | `dictionary` ha 14 rotte (le pagine: né gli endpoint, né un layout senza pagina) e per ognuna i nodi; ogni nodo nomina `+page.svelte`, `+page.ts` o `.js`, i layout `.svelte` e `+layout.ts`, `+error.svelte`: mai un file `.server.` né un `+server`; `~` davanti a un nodo dice che c'è un `load` sul server | `sync.json` |
| la cartella delle rotte | `kit.files.routes: 'src/pages'`: i file sono nominati `src/pages/…` (20 id, 2029 byte di JSON): non serve leggerla | `routes-in-pages.json` |
| `kit.outDir` | scrive in `.kit-out/`, con lo stesso contenuto, e dice a stderr `"extends": "./.kit-out/tsconfig.json"`; il file in `.svelte-kit/` non c'è | `out-dir.json` |
| progetto senza rotte | esce 0 e scrive `{"/": []}` (12 byte) | `no-routes.json` |
| rotte tolte fra due sync | il secondo sync toglie i tipi e le voci di ciò che non c'è più (1943 byte, `/about` e `/api/health` non ci sono più) | `stale.json` |
| un errore di sintassi in un `+page.server.ts` | esce 0: il file è elencato lo stesso | `server-syntax-error.json` |
| versioni | lo stesso JSON, byte per byte, da SvelteKit 2.0.0 (Svelte 4), 2.15.0, 2.40.0 e 2.70.4; il comando esce 0 in 1,4-1,7 secondi e scrive 34 file invece di 58 | `old-kit-*.json` |

**Che cosa non dà.**

| Dato | Misura | Uscita |
| --- | --- | --- |
| le esportazioni del modulo | né `load`, né `actions`, né `GET`/`POST`…: `route_meta_data.json` nomina i file, mai i loro membri | `sync.json` |
| le righe | nessuna: il file e basta | `sync.json` |
| il metodo HTTP | nessuno: `RequestHandler` è un tipo solo per tutti i metodi di un `+server` | `sync.json` |
| il nome delle azioni di un modulo | nessuno: `ActionData` e `Actions` sono tipi sull'oggetto `actions` della copia `proxy+page.server.ts` | `sync.json` |
| `+page.svelte` | non è in `route_meta_data.json`: una pagina senza modulo suo (`/about`, `/lang/[[opt]]`, `/items/[id=integer]`, `/(shop)/receipt`) è una chiave con i soli layout sopra di sé (nella fixture i layout con un modulo ci sono; senza, la chiave potrebbe avere una lista vuota: non provato); il componente è nominato solo in `generated/client/nodes/N.js` | `sync.json` |
| che cos'è ogni file | nessun campo: il ruolo è il nome del file (`+server`, `+page.server`, `+page`, `+layout.server`, `+layout`) | `sync.json` |
| il percorso URL | l'id tiene il gruppo (`/(shop)/checkout`) e i segmenti come sono scritti (`[slug]`, `[...rest]`, `[[opt]]`, `[id=integer]`) | `sync.json` |
| la cartella d'uscita | `kit.outDir` sta in `svelte.config.js`: è codice, e il comando che stampa il file la suppone `.svelte-kit` | `out-dir.json` |

Una `+page.svelte` senza `+page.server` né `+page` non dà righe: il componente non è un modulo con funzioni che lo strumento nomina (in React Router il `default` di un modulo di rotta è un ingresso perché il comando nomina il modulo). Le sue azioni sono dei lettori del markup.

**Quando fallisce.**

| Caso | Misura | Uscita |
| --- | --- | --- |
| `svelte.config.js` che lancia | esce 1, lo standard error comincia con `Loading Svelte config from Vite config failed: Error: svelte.config.js needs a secret` e la pila; lascia solo `.svelte-kit/tsconfig.json` | `config-throws.json` |
| `svelte.config.js` con un errore di sintassi | esce 1, `SyntaxError: Unexpected end of input`, nessun file | `config-broken.json` |
| due rotte che si scontrano | esce 1, `The "/(a)/x" and "/(b)/x" routes conflict with each other` | `route-conflict.json` |
| `[id=nomatcher]` | esce 1, `No matcher found for parameter 'nomatcher' in route /nomatch/[id=nomatcher]` | `bad-matcher.json` |
| un sync che fallisce dopo uno riuscito | esce 1 (la configurazione lancia) e `route_meta_data.json` del primo c'è ancora: `cat` lo stampa con exit 0 (2079 byte) | `failed-after-a-good-sync.json` |
| il comando non è installato, `npx --no-install` | esce 1 dopo **70,6 secondi**, con `EAI_AGAIN` su `registry.npmjs.org`: npx chiede comunque il pacchetto `svelte-kit` al registro | `not-installed.json` |
| lo stesso con `npm_config_offline=true` | esce 1 dopo **0,6 secondi**, con `ENOTCACHED … cache mode is 'only-if-cached' but no cached response is available` | `not-installed-offline.json` |

**La sorgente.** Comandi, per cartella: `timeout --kill-after=10 900 npx --no-install svelte-kit sync` con `npm_config_offline=true` (le cartelle si dividono i 900 secondi) e `cat .svelte-kit/types/route_meta_data.json`. Le risposte registrate sono in `tests/fixtures/premap/sveltekit/answers.json`, che `tests/test_codebase_map_premap_sveltekit.py` legge.

| Misura | Risultato |
| --- | --- |
| righe che la sorgente ne ricava dai 18 file | 25: 16 sulla funzione che l'esportazione nomina (7 `load`, 9 funzioni di `+server`: `GET`, `POST`, `PUT`, `DELETE`, `fallback`), 3 sul file di un layout (tipo «nessun ingresso»: `+layout.ts` e `+layout.server.ts` della radice, `+layout.server.ts` di `(shop)`), 6 righe di lacuna |
| le 6 lacune | `actions` di `/(shop)/cart`, `/(shop)/checkout`, `/blog/[slug]`, `/login` (`unsupported-target-kind`: `actions` è un oggetto, e le sue funzioni sono per lo snapshot anonime), `GET` di `/computed` (`unsupported-target-kind`: il risultato di una chiamata), `load` di `/reexport` (`reexport-unsupported`) |
| un file non legato | nessuna rotta ha una riga sul `.svelte`; `/about`, `/lang/[[opt]]`, `/items/[id=integer]` e `/(shop)/receipt` non hanno riga |
| `routes-in-pages` | 20 id, le stesse righe sui file `src/pages/…`, nessuna lacuna |
| `out-dir` | una lacuna `model_failed` che dice `wrote no .svelte-kit/types/route_meta_data.json`, nomina `outDir` e riporta le parole del tool (`.kit-out`) |
| `config-throws`, `config-broken`, `route-conflict`, `bad-matcher`, `failed-after-a-good-sync` | una lacuna `model_failed` con la causa che il tool ha scritto per prima; nel quinto caso il file del sync precedente non è letto |
| `not-installed` | una lacuna `model_failed` che nomina `svelte-kit` e `ENOTCACHED` (0,7 secondi sotto `timeout`) |
| `timed-out` | lo stesso comando con 0,5 secondi invece di 900 (il sync più rapido misurato dura 1,0 secondi): `timeout` lo ferma, esce 124 dopo 0,5 secondi, il `cat` esce 1 (nessun file); una lacuna `model_failed` «did not end in 900 seconds». L'uscita 137 (`--kill-after`, o la memoria del container) non è registrata: nessuna fixture l'ha esaurita, e il test scrive la risposta |
| `no-routes` | nessuna riga e nessuna lacuna |
| `server-syntax-error` | la riga di `/blog` è una riga con la lacuna (lo snapshot non legge il file) |
| nei collegamenti (`flows.cached_links`) | 16 ingressi sulle funzioni, tutti `sveltekit` di tipo «rotta»; i 3 layout non sono ingressi; `routes.offered` 0 |

**La pre-mappa intera** (`modal_pipeline.py --folder-stop scan` su `fixture/routes`, `results/pipeline-scan.json`; misurata con la sorgente `v1`, oggi `VERSION` è `daodan/premap/v2`: non rimisurata):

| Misura | Risultato |
| --- | --- |
| `scan`, tutto | 136,6 secondi (con `tsc` 17,2 s, `npm` 9,9 s, `noir` 16,1 s); la prima corsa, senza `timeout` nel comando, 118,1 |
| sorgente `sveltekit@daodan/premap/v1` | `ran`, 18,5 secondi, compreso il ripristino dei pacchetti e i comandi (15,5 nella prima corsa) |
| `framework_entries` in `premap.json` | 25 righe, 0 lacune della sorgente: le stesse 25 righe della risposta registrata |
| `next`, `react-router`, `nuxt` e `angular` | `not_needed`: la fixture non li dichiara |
| Noir sulla stessa fixture | 25 endpoint nei file di `src/routes/`, con il metodo e il percorso URL (`GET /cart` per `(shop)/cart`, `/api/items/{id}`, `/docs/{rest}`), anche per 13 `+page.svelte` (`GET`; non vede `+page@.svelte`) e per le azioni (4 `POST`, come `POST /blog/{slug}` alla riga di `actions`, la 6 del `+page.server.ts`), senza `fallback` e senza il nome del gestore: nei collegamenti sono 25 lacune «noir reports this entry without a unique snapshot handler at its site», non ingressi |
| collegamenti | 16 ingressi (`sveltekit rotta`), `routes` `{offered: 0, called: 0, linked: 0}`, 31 lacune: le 25 di Noir e le 6 righe di lacuna di SvelteKit |
| gap della pre-mappa, non di questa sorgente | `tsc --showConfig: error TS5083: Cannot read file '/work/.svelte-kit/tsconfig.json'`: la fixture non ha lo script `prepare` (`svelte-kit sync`) che i progetti creati con `sv create` hanno, e nessuna installazione crea quel file (D-156) |

## Aperto

- **`actions`:** i membri dell'oggetto non sono legati a una funzione né dallo strumento né dai record di esportazione dello snapshot (4 delle 6 lacune sulla fixture). Il controllore dei tipi di TypeScript potrebbe dare i membri: non valutato. Se il passo dinamico osserva la funzione che un'azione esegue non è misurato.
- **Le altre forme non legate:** `GET = make('get')` (il risultato di una chiamata), una riesportazione, `export const load = (async () => …) satisfies PageServerLoad` (lacuna `load: unsupported-target-kind`), un metodo con overload (lacuna `export-ambiguous`: nessuno strumento dice quale record è l'implementazione).
- **Le rotte offerte.** Le righe sono ingressi: l'id non è il percorso (il gruppo `(shop)` non è nell'URL; `[...rest]`, `[[opt]]` e `[id=integer]` stanno per più schemi) e il tool non dà il metodo. Noir dà già percorso e metodo agli stessi file e alle stesse righe delle funzioni di `+server`.
- **Noir e SvelteKit sulla stessa rotta.** Oggi `flows.link_facts` unisce una rotta di Noir a una riga legata e senza lacuna di una sorgente di `FRAMEWORK_SOURCES`, sullo stesso percorso e nello stesso file o sulla stessa funzione. La misura sopra è precedente e non è rifatta: quante righe si uniscono, con l'id di SvelteKit e lo schema di Noir, non è misurato.
- **Il `load` dei layout** è chiamato per ogni pagina sotto il layout e la tabella dice «nessun ingresso», come per i layout di React Router: deciso qui, da rivedere.
- **`kit.outDir` diverso da `.svelte-kit`:** una lacuna con la causa, non una lettura (lo standard error del tool nomina la cartella).
- **Non provati:** un progetto reale (solo questa fixture; tempo e memoria su molte rotte non misurati); SvelteKit 1 e le 2.x fra quelle misurate; un modulo di rotta che non è TypeScript né JavaScript (`+page.md`); una rotta i cui layout non hanno moduli (la chiave potrebbe avere una lista vuota); pnpm, Yarn o Bun.
