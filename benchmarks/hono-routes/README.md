# Hono: `inspectRoutes` di `hono/dev` contro Noir

Domanda: l'interfaccia ufficiale di Hono che elenca le rotte di un'app (`inspectRoutes` di `hono/dev`), chiamata nel container di Daodan sul modulo che esporta l'app, può essere la sorgente delle rotte di Hono al posto di Noir? Piano: [refactoring](../../docs/plans/refactoring.md), passo `T1.C.1` (punto 14, `T1.14`); l'esito decide `T1.C.10`.

**Risultato in una riga:** **la regola non passa**: il modulo dell'app è dichiarato solo in `ramen-api` (`main` di `package.json` e di Wrangler), e anche lì Node non lo carica senza un caricatore che il progetto non ha; dove `inspectRoutes` risponde, i gestori sono senza nome (`[handler]`) in 70 rotte su 70 di Documenso e 7 su 7 di `ramen-api`, legabili per nome solo 5 su 8 in `hono-open-api-starter`, e lo strumento non dà posizioni. **Hono passa al modulo di `T1.C.8` (`T1.C.10`).** I percorsi di `inspectRoutes`, invece, sono completi dove Noir perde i prefissi di `route()` fra file (Documenso).

## Regola di decisione (scritta il 27 novembre 2026, prima della corsa)

`inspectRoutes` diventa una sorgente di Daodan (`T1.C.10`, `entry_points/hono.py` con `commands`) **solo se, su ognuna delle tre applicazioni reali**:

1. **il modulo dell'app si trova da un dato dichiarato**: il campo `main` o `exports` di un `package.json` che dipende da `hono` (risolto da Node, non da noi), oppure il `main` della configurazione di Wrangler letto da Wrangler stesso (`unstable_readConfig`); uno script (`dev`, `start`), una configurazione che è codice (`rollup.config.mjs`, `vite.config.ts`) o la conoscenza del progetto non valgono;
2. **dà almeno le rotte di Noir**: ogni rotta `http` di Noir 1.5.0 (metodo e `flows.path_schema` del percorso) è fra quelle di `inspectRoutes` caricato da quel modulo (le rotte di Noir che non sono di Hono, in un monorepo, non contano: si contano a parte);
3. **lega i gestori senza indovinare**: ogni rotta di `inspectRoutes` dà un gestore legabile con un'uguaglianza di dati: un nome di funzione che nello snapshot di Daodan è di una sola funzione (`name`, o l'ultima parte del nome qualificato), oppure una posizione. Un gestore senza nome (`[handler]`), o un nome di più funzioni, è indovinare.

Altrimenti Hono passa al modulo di `T1.C.8` (`T1.C.10`, lettore dell'albero con le forme di Hono come dati in `entry-queries.json`). La fixture (`fixture/`) è il controllo che lo strumento funziona e che la misura conta giusto; non entra nella regola.

## Che cosa si misura

| Parametro | Valori |
| --- | --- |
| Applicazioni (`apps.py`) | `real-stack-documenso` (commit di `benchmarks/project-model/fixtures/real-stack-documenso/source.json`, AGPL-3.0: solo letta e caricata nel container, nulla nel repository); `ramen-api` (`yusukebe/ramen-api`, MIT, Cloudflare Workers); `hono-open-api-starter` (`w3cj/hono-open-api-starter`, MIT, `OpenAPIHono` di `@hono/zod-openapi`); `fixture/` |
| Ripristino | le righe di Daodan per i pacchetti Node (`container_runner._node`, `container_runner.plan("next", ...)`: Node di `preparation.NODE`, `npm ci`/`pnpm install` con gli script) eseguite in `/work` mentre l'immagine si costruisce, con la rete aperta (nel container di Daodan la rete è quella dei registri) |
| Esecuzione | rete bloccata, ambiente del runner (`preparation.ENV`); uno script nostro in Node importa il modulo, risolve `hono/dev` dal modulo stesso (il pacchetto del progetto) e stampa `inspectRoutes` di ogni esportazione che è un'app Hono (`routes` e `fetch`): `path`, `method`, `name`, `isMiddleware`; tempo e memoria massima |
| Modulo | quello dichiarato (`main`/`exports` risolti da Node, `main` di Wrangler letto da Wrangler), e quello scelto a mano (marcato, per sapere che cosa darebbe lo strumento se il modulo fosse noto) |
| Caricatore | `node` (Node 24 toglie i tipi di TypeScript da sé) e `node --import tsx` quando il progetto installa `tsx` (strumento del progetto) |
| Noir | `noir scan /work -f json --no-log` 1.5.0 (`noir.commands`) sull'albero pulito, le righe come le legge `noir.read` e legate da `binder.bind` |
| Conteggi (`summarize.py`, provati in `test_hono_routes.py`) | per applicazione: rotte di `inspectRoutes` (senza middleware), di Noir, comuni per metodo e schema, solo dell'uno o dell'altro; gestori legabili (nome unico, senza nome, ambiguo, assente) e quanti di quelli comuni legano la stessa funzione del legatore su Noir |

```
export PATH=<venv con modal[api-proxy-support]>/bin:$PATH PYTHONUTF8=1 PYTHONIOENCODING=utf-8
modal run benchmarks/hono-routes/modal_probe.py --mode lock        # una volta: fixture/package-lock.json, rete aperta, nessuno script
modal run benchmarks/hono-routes/modal_probe.py                    # tutte le applicazioni; --only fixture,ramen-api per alcune
modal run tests/modal_pytest.py --args "benchmarks/hono-routes/test_hono_routes.py -q"
```

`results/<applicazione>.json`: le risposte (comandi, uscite, tempi, memoria, rotte di `inspectRoutes` e di Noir, nessun sorgente) e il riassunto di `summarize.py`.

## Esito (Modal, 27 novembre 2026, rete bloccata all'esecuzione; Node 24.22.3, Noir 1.5.0)

| Applicazione | Ripristino di Daodan | Modulo da un dato dichiarato | Carica (`inspectRoutes`) | Rotte `inspectRoutes` / Noir / comuni | Gestori di `inspectRoutes` | Noir legati dal legatore |
| --- | --- | --- | --- | --- | --- | --- |
| fixture | `npm ci`, 2,8 s | sì: `main` (`src/index.js`) | `node`, 0,12 s, 127 MB | 4 / 4 / 4 | 2 nome unico, 2 senza nome | 4 su 4; 2 comuni legano la stessa funzione |
| `ramen-api` | `pnpm install`, 10 s | sì: `main` di `package.json` e `main` di `wrangler.jsonc` (letto da Wrangler), `src/index.ts` | `node`: no (`./mcp` senza estensione, alias `@/`); il progetto non ha `tsx`; con il `tsx` 4.20.6 della sonda sì, 1,3 s, 196 MB | 7 / 19 / 6 | 7 senza nome | 19 su 19 |
| `hono-open-api-starter` | `pnpm install`: **`DAODAN-RESTORE-FAILED` (`ERR_PNPM_IGNORED_BUILDS`)**, i pacchetti ci sono | no: nessun `main`/`exports`, solo lo script `dev` (`tsx watch src/index.ts`) | `node`: no (alias `@/`); `tsx` del progetto: esce 1 (`DATABASE_URL`, `LOG_LEVEL` mancanti); con i valori di `.env.example`: sì, 1,8 s, 337 MB (`src/app.ts`, scelto a mano) | 8 / 7 / 7 | 5 nome unico (`list`, `create`, `getOne`, `patch`, `remove`), 3 senza nome | 0 su 7 (Noir non dà il gestore di `openapi(route, handler)`) |
| `real-stack-documenso` | `npm ci`, 79 s | no: `apps/remix` non ha `main`; i `main` di `packages/auth` e `packages/ee` (dipendono da `hono`) caricano ma non esportano un'app | sorgente: no con `node` (import senza estensione), no con `tsx` (manca `@documenso/prisma/generated/zod`: il `post-install` del pacchetto non è uno script npm), no anche dopo `prisma:generate` (`jobsClient` non esportato, CommonJS letto da `tsx`); **sì solo dall'uscita della build del server del progetto** (`prisma:generate`, `translate`, `build:server`, poi `node apps/remix/build/server/hono/server/router.js` con `.env.example`): 9,2 s, 518 MB | 70 / 423 / 11 | 70 senza nome | 162 su 423 schemi (163 su 425 righe) |

Lettura per criterio:

1. **Modulo dichiarato:** 1 applicazione su 3 (`ramen-api`). Documenso e `hono-open-api-starter` non dichiarano dove sta l'app: lo dice uno script o la configurazione di rollup, che sono codice.
2. **Almeno le rotte di Noir:** fixture 4 su 4, `hono-open-api-starter` 7 su 7 (più `GET /doc` che Noir non vede), `ramen-api` 6 su 19: le 13 di Noir in più sono 6 file statici di `content/` (Noir legge la cartella degli asset, non sono rotte di Hono) e 7 metodi di `/mcp`, che `inspectRoutes` dà come una sola rotta `ALL /mcp` (`app.route('/mcp', mcpApp)` di `@hono/mcp`). In Documenso 84 righe di Noir sono in file di Hono (`packages/auth/server` 36, `apps/remix/server` 21, `packages/ee/.../csc/hono` 3, `packages/api/hono.ts` 24) e Noir le dà **senza il prefisso del `route()` che le monta da un altro file** (`GET /accounts` dove l'app risponde a `GET /api/auth/accounts`): solo 11 coincidono; `inspectRoutes` dà i 70 percorsi completi (con `basePath` e i prefissi). Le altre 341 righe di Noir non sono di Hono (tRPC 270, `apps/openpage-api` 38 di Next.js, il contratto ts-rest `packages/api/v1/contract.ts` 19, anteprime, documentazione e una pagina 14).
3. **Gestori legabili senza indovinare:** 0 su 70 (Documenso), 0 su 7 (`ramen-api`), 5 su 8 (`hono-open-api-starter`). `inspectRoutes` dà solo `handler.name` (o `[handler]`/`[middleware]` per una funzione senza nome) e `isMiddleware` dal numero di parametri: nessun file, nessuna riga. Un gestore scritto sul posto, la forma più comune di Hono, non è legabile.

**Decisione:** la regola non passa (criteri 1 e 3; il 2 regge dove lo strumento carica). `inspectRoutes` non diventa una sorgente; Hono va nel modulo di `T1.C.8` (`T1.C.10`), che deve comporre `route()` e `basePath` fra file, la cosa che Noir sbaglia in Documenso e che il metodo di GitNexus 1.6.12 non fa per Hono (`benchmarks/express-routes/README.md`, «Metodo di GitNexus»).

Fuori dalla regola, da sapere:

- Il ripristino di Daodan segna fallito `pnpm install` di `hono-open-api-starter` per `ERR_PNPM_IGNORED_BUILDS` (pnpm che rifiuta gli script di build non approvati) anche se i pacchetti sono installati e l'app si carica: è un difetto della preparazione (`preparation.restore`, famiglia `pnpm`), non di Hono.
- Il caricamento esegue il modulo: `hono-open-api-starter` esce se l'ambiente non ha le variabili che il suo `env.ts` valida, Documenso solo dall'uscita di una build. Nel container di Daodan i valori di `.env.example` non sono dati che la sorgente avrebbe.
- `results/<applicazione>.json`: ogni comando con uscita, secondi e memoria, le risposte di `DECLARED` e di `INSPECT`, le righe di Noir legate, e `loads` con i conteggi di `summarize.compare`. La fixture prova lo strumento e i conteggi: 4 rotte, 2 nomi unici che legano la stessa funzione del legatore su Noir.

## File

| File | Che cosa fa |
| --- | --- |
| `apps.py` | applicazioni, commit, licenze, moduli scelti a mano |
| `modal_probe.py` | le immagini (ripristino di Daodan; Noir e snapshot), le sonde in Node (`DECLARED`, `INSPECT`), le varianti fuori regola (`EXTRA`, `GENERATE`), `--mode lock` |
| `summarize.py` | conteggi puri (rotte senza middleware, gestore legabile, confronto per metodo e `flows.path_schema`) |
| `test_hono_routes.py` | `summarize.py` su righe scritte a mano: 3 test, verdi su Modal |
| `fixture/` | `new Hono()`, `app.route('/api', sub)`, `basePath('/v1')`, gestori con nome e scritti sul posto, un middleware; `package-lock.json` fatto su Modal |

## Il modulo nostro contro Noir (`T1.C.10`)

`inspectRoutes` non è passato (sopra): il modulo di `T1.C.8` (`daodan/core/entry_points/express.py`) legge anche Hono, dalla sezione `hono` di `daodan/data/entry-queries.json` (`new Hono()` e `new OpenAPIHono()`, `route(prefisso, app)` che monta, `basePath(prefisso)` che dà un'app con il prefisso, i verbi che restituiscono l'app stessa); stesso codice, nessun ramo per libreria oltre ai dati.

### Regola di decisione (scritta il 28 novembre 2026, prima della corsa)

La stessa di `T1.C.9` (`benchmarks/express-routes/README.md`, «Il modulo contro Noir»): una rotta legata è una terna distinta (metodo, schema o percorso, funzione); il modulo **si collega per l'id `honojs`** solo se, **in ognuna delle tre applicazioni reali** (`real-stack-documenso`, `ramen-api`, `hono-open-api-starter`), lega almeno tante rotte quante Noir ne lega **nei file che importano un pacchetto della sezione `hono`** (le righe di Noir di tRPC, Next.js, ts-rest o dei file statici non sono di Hono e non contano, come in `T1.C.1`), e se il campione (fino a 20 rotte legate solo dal modulo, seme 24, lette a mano sul sorgente) ha 0 legami sbagliati. La fixture prova lo strumento e non entra nella regola.

```
modal run benchmarks/hono-routes/modal_probe.py --compare      # results/<applicazione>.module.json
modal run benchmarks/hono-routes/modal_probe.py --compare --sample
```

### Esito (Modal, 28 novembre 2026, app `ap-pQcQvvrDYHJTCLyh5Yc3Vj`; campione `ap-ZFL4Ez2miN2x3oNoB4cR3H`)

| Applicazione | Righe del modulo | Legate dal modulo | Righe `http` di Noir nei file di Hono (fuori) | Legate da Noir | Stessa rotta e funzione | Stessa funzione, percorso diverso | Solo del modulo / solo di Noir | Tempo del modulo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `real-stack-documenso` | 61 | **35** | 84 (341) | 84 | 8 | 27 | 0 / 49 | 50,7 s |
| `ramen-api` | 13 | **12** | 19 (0) | 19 | 11 | 0 | 1 / 8 | 0,1 s |
| `hono-open-api-starter` | 1 | **0** | 6 (1) | 0 | 0 | 0 | 0 / 0 | 0,0 s |
| fixture | 4 | 4 | 4 (0) | 4 | 4 | 0 | 0 / 0 | 0,0 s |

**Decisione: non collegato** per `honojs`. Il criterio delle rotte non passa in Documenso (35 contro 84) né in `ramen-api` (12 contro 19); il campione (l'unica rotta solo del modulo, `ALL /mcp` di `ramen-api`, `app.all('/', ...)` di `src/mcp.ts` montato su `/mcp`) ha 0 legami sbagliati. In `hono-open-api-starter` nessuno dei due lega (le rotte sono `openapi(route, handler)`, che la sezione non legge; l'unica riga, `GET /reference`, ha per gestore il valore di un pacchetto, `Scalar(...)`).

Le cause:

- **Documenso: il prefisso base viene dall'ambiente.** L'app radice è `new Hono().basePath(basePath || '/')` con `basePath` da `NEXT_PUBLIC_BASE_PATH` (`apps/remix/server/router.ts:51-53`): ogni `route()` su di essa ha un prefisso non letterale, e le sue rotte e quelle delle app che monta sono lacune («mounted under a prefix that is no literal», 15; «mounted by no app the reader reaches», 9; «the base path of its app is no literal», 2). È la risposta giusta del metodo: il percorso vero dipende da una variabile d'ambiente. Noir dà le stesse rotte senza nessun prefisso (`GET /accounts` per `GET /api/auth/accounts`), e le lega; dove il modulo lega, compone i prefissi di `route()` e `basePath` fra file (27 rotte con la stessa funzione di Noir e il percorso completo).
- **`all` contro i metodi uno per uno:** Noir scrive `app.all('/mcp', ...)` come sette righe (una per metodo), il modulo come una sola rotta di ogni metodo; il conteggio per terne dà a Noir 7 rotte dove il modulo ne ha 1 (`ramen-api`, e le tre `zapier` di Documenso). Anche contando `all` una volta, `ramen-api` resta 12 contro 13: la rotta di `test/mockApp.ts` ha un percorso scritto con un template (lacuna «the path is no literal»).

Il modulo per Hono resta nel codice, provato dalla fixture (`tests/test_codebase_map_entry_points_hono.py`), fuori dallo step come quello di Express (`T1.C.9`).

### Dopo `T1.C.13` (Modal, 28 novembre 2026, app `ap-4b0RnrGU7M2P28XWlZ4nTu`)

Gestori metodo di un oggetto, chiamata e router passato (`benchmarks/express-routes/README.md`, «Gestori metodo, chiamata e router passato»): sulle tre applicazioni di Hono nulla cambia (Documenso 35 contro 84, `ramen-api` 12 contro 19, `hono-open-api-starter` 0 e 0; la sola rotta solo del modulo è ancora `ALL /mcp`, già letta nel campione). Le cause sono quelle sopra, e `openapi()` e `on()` restano fuori dalla sezione. **Non collegato** per `honojs`.
