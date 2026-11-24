# FastAPI: il caricatore di `fastapi-cli`, `iter_route_contexts` e gli oggetti di rotta

Domanda: dove sta l'applicazione, senza una convenzione scritta a mano; che cosa dà FastAPI, caricato nel container senza rete, per ogni rotta (metodo, percorso,
funzione con file e riga); e come la sorgente della pre-mappa [`daodan/core/premap/fastapi_app.py`](../../daodan/core/premap/fastapi_app.py) lo lega alle funzioni
dello snapshot. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14a.
**Misurato il 24 novembre 2026 su Modal** (FastAPI 0.165.0 con Starlette 1.10.0, fastapi-cli 0.0.34, uvicorn 0.54.0, pydantic 2.14.4, CPython 3.12.1; immagine del
runner, rete bloccata); lo stesso fixture su FastAPI 0.115.14 (Starlette 0.46.2) e 0.137.1. I numeri sotto sono di quelle esecuzioni. **La sorgente è scritta e provata e non è
collegata** (`premap/__init__.py`, `container_runner.TOOLS`, `entry-queries.json` sono file condivisi: le patch stanno in `wiring/`). **Verdetto sulle applicazioni vere (sotto): no, non aggiunge abbastanza a Noir per essere collegata** —
su due applicazioni pubbliche il framework non dà nessuna rotta con una funzione del progetto che Noir non dia, e nelle condizioni di Daodan non carica nessuna delle due.

Il codice del progetto (il fixture, FastAPI, i loro pacchetti) gira solo nel container, mai su questa macchina: le immagini si costruiscono con la rete aperta (l'unico
momento in cui lo è) e ogni variante gira in una copia della cartella con la rete bloccata.

| Cartella o file | Contenuto |
| --- | --- |
| `fixture/` | `pyproject.toml` (solo questo: `fastapi[standard]==0.165.0` e `[tool.fastapi] entrypoint = "app.main:app"`, nessun `requirements.txt`), `app/main.py` (rotte con `@app.get`, `@app.post`, `@app.api_route`, `add_api_route` con funzione, lambda, metodo legato, oggetto con `__call__`, `functools.partial`, `json.dumps` e una funzione di `fastapi.utils`, `functools.wraps` e un decoratore senza; i parametri `{x:int}`, `{x:uuid}`, `{x:path}`, `{a}/{b}`, `{a}-{b}`, due convertitori propri, uno con un `/` nella `regex`; `/strict/` e `/loose`; `@app.websocket`; `add_route` di Starlette con funzione e con `HTTPEndpoint`; `mount` di `StaticFiles`, di una funzione ASGI, di una sotto-applicazione FastAPI e di una con un parametro nel prefisso), `app/routers/users.py` (un router con prefisso, un router incluso in lui, un `operation_id`, e un `mount` su di lui), `app/orders.py`, `app/sub.py`, `app/convertors.py`, `static/` |
| `plan.py` | stampa, con il Python che ha le dipendenze di Daodan (`DAODAN_PYTHON`, di default `python`; `DAODAN_PROBE_TMP` per i file di lavoro), per una cartella: i comandi di `fastapi_app.commands`, il comando di setup di `container_runner.plan`, le righe di ripristino di `container_runner._python` e i file che il setup spacchetta; legge solo i nomi dei file. Porta anche `TOOL`, la voce `container_runner.TOOLS["fastapi"]` con cui la sonda ha girato (finché il runner non l'ha, la sonda e i test la mettono lì) |
| `modal_probe.py` | costruisce un'immagine del runner (`container_runner.IMAGE`, con il Python di Modal accanto) per il fixture e per tre copie con un altro modo di dipendere da FastAPI (`plain`: `fastapi` senza `[standard]` in un `requirements.txt`; `old`: 0.115.14; `mid`: 0.137.1), esegue il setup di `plan.py` come lo esegue il runner, con il progetto in `/work`, poi ogni variante con la rete bloccata e nel `cwd` che il comando della sorgente dice; scrive `results/` e, per le varianti in `RECORDED`, `tests/fixtures/premap/fastapi/` con `script.json` (impronta dei due file dello script e `VERSION`) |
| `results/<variante>.json` | `argv`, `cwd`, `returncode`, `stdout` (i primi 20.000 caratteri, tutto per le varianti in `FULL`), `stderr`, secondi, memoria di picco, file lasciati e cambiati nel progetto |
| `apps.py`, `modal_real.py`, `real_summary.py`, `results/real/` | le applicazioni vere (sotto): dove stanno e a quale commit, l'esecuzione su Modal del Noir fissato da `premap/noir.py` e dello script, il confronto; `results/real/<caso>-summary.json` ha i conteggi e gli esempi |
| `wiring/` | le patch dei file condivisi che questa sorgente non possiede (registro, `container_runner.TOOLS`, `entry-queries.json`, il test che elenca le sorgenti) e quella con cui Flask userebbe `python_script.py` |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/fastapi-routes/modal_probe.py
... modal_probe.py --only environment,cli-source        alcune varianti, niente registrato
... modal_probe.py --label before-review                le risposte vanno in `results/before-review/`, niente registrato
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/fastapi-routes/modal_real.py
python benchmarks/fastapi-routes/real_summary.py <cartella fuori dal repository per i sorgenti> <cartella di lavoro>
```

## Applicazioni vere

Domanda (del coordinatore, 24 novembre 2026): sulle applicazioni vere, gli oggetti del framework danno rotte che il Noir fissato (1.5.0, `premap/noir.py`) non dà? A Spring, su tre applicazioni vere, Noir dava le stesse rotte con lo stesso
file e la stessa riga del gestore (337 su 337) e la sorgente non fu scritta. Qui: il fixture e due applicazioni FastAPI pubbliche con licenza permissiva, ognuna a un commit fissato e scaricata durante la costruzione dell'immagine (`apps.py`:
nulla del loro codice è nel repository; restano i conteggi e le risposte). Su Modal, rete bloccata nelle esecuzioni; il ripristino è quello del runner (`plan.py` sui nomi dei file, `uv sync` per un workspace, `uv pip install` per un `requirements.txt`).
Il confronto passa per il codice di Daodan: `premap.write` con le risposte registrate (`noir.read`, `fastapi_app.read`), poi il legatore dei collegamenti (`binder.bind`) sullo snapshot dei sorgenti (testo, mai eseguito qui). Chiave di una rotta:
metodo e `flows.path_schema` del percorso come lo scrive ogni strumento. «Lega» vuol dire: una funzione unica dello snapshot, con file e riga.

| Applicazione | Commit | Licenza | Perché sta qui | Ambiente del ripristino |
| --- | --- | --- | --- | --- |
| `fastapi/full-stack-fastapi-template`, cartella `backend/` di un workspace uv | `77e550a73bb4` | MIT | `app.include_router(api_router, prefix=settings.API_V1_STR)`, un router che include router con il proprio prefisso, una `lifespan`, dipendenze sugli endpoint, `app.frontend(...)` | `uv sync --locked`, CPython 3.14.6 scaricato da `uv`, FastAPI 0.141.1, Starlette 1.3.1, fastapi-cli 0.0.32 (77 pacchetti, 5 s) |
| `fastapi-users/fastapi-users`, cartella `examples/sqlalchemy` | `e9c57ff7ff2f` | MIT | ogni router lo fa una funzione della libreria (`fastapi_users.get_auth_router(...)`, `get_users_router(...)`) e lo include con un prefisso; `fastapi` dichiarato senza `[standard]` | `uv pip install -r requirements.txt`, CPython 3.12.1, FastAPI 0.165.0 (37 pacchetti, 3 s) |
| il fixture (sopra) | questo repository | | i casi che un lettore statico può sbagliare, scritti apposta: `add_route`, `api_route` con due metodi, metodo legato, lambda, `partial`, oggetto con `__call__`, un decoratore senza `functools.wraps`, un `mount` su un router incluso, convertitori | `uv pip install -r pyproject.toml`, FastAPI 0.165.0 |

**Come girano, nelle condizioni di Daodan** (la riga `script`: la riscrittura dei `.env` che il runner fa prima di ogni comando, `container.named`; Noir su `/work`):

| Applicazione | Noir (1,1 s, 147-191 MB) | Script del framework |
| --- | --- | --- |
| template | 34 endpoint: **23 rotte FastAPI**, 7 rotte di React (`frontend/src/routes`), 1 voce di `compose.deploy.yml`, 3 comandi; le 23 FastAPI hanno gestore con nome, file e riga e si legano tutte (con il prefisso `/api/v1` che viene da `settings.API_V1_STR`: Noir lo risolve) | **non carica, uscita 3, 3,0 s**: `ValidationError: 6 validation errors for Settings` (`FASTAPI_ENV`, `DATABASE_URL`, `SMTP_*`, `FIRST_SUPERUSER`): il `.env` che il progetto ha nel repository è riscritto con segnaposto (`./daodan-dotenv-...`) e le impostazioni non li accettano. Con il `.env` com'è (`template-script-env`): **non carica, uscita 3, 4,3 s**: `RuntimeError: Frontend directory '/work/backend/app/frontend' does not exist` (`app.frontend(...)` chiede la cartella che la compilazione del front end crea) |
| users | 1 endpoint (`GET /authenticated-route`, legato); nessuna delle rotte dei router della libreria | **non carica, uscita 3, 0,1 s**: `ModuleNotFoundError: No module named 'fastapi_cli'` (`fastapi` senza `[standard]`: il caricatore non c'è). Con `fastapi-cli` aggiunto all'ambiente (`users-cli-script`): **non carica, uscita 3, 1,2 s**: `Could not find FastAPI app in module`: dei percorsi di default il primo che c'è è `main.py`, che è il lanciatore (`uvicorn.run("app.app:app")`), e `fastapi dev` fallirebbe uguale |
| fixture | 40 endpoint (39 http, 1 `ws`) | 42 rotte, carica, 1,7 s, 74 MB |

**Se i due ostacoli sono tolti** (varianti che cambiano l'ingresso, non l'applicazione: `template-script-stub` ha il `.env` com'è e una cartella `backend/app/frontend` vuota; `users-cli-script-declared` ha `fastapi-cli` e un `pyproject.toml` con `[tool.fastapi] entrypoint = "app.app:app"`), e per il fixture:

| | Rotte del framework | di cui progetto, legate a una funzione | Endpoint FastAPI di Noir | legati | Entrambi (metodo e percorso) | stessa funzione | stesso file e riga | Solo il framework | Solo Noir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| template | 27 (4 della documentazione) | 23 su 23 | 23 | 23 su 23 | **23** | 23 | 23 | **0** | **0** (gli 8 che non sono FastAPI: React, compose) |
| users | 17 (4 della documentazione, 12 della libreria) | 1 su 1 (le 12 hanno la vista in `site-packages/fastapi_users`: nessuna riga, una lacuna che le conta) | 1 | 1 su 1 | 1 | 1 | 1 | 0 rotte di funzioni del progetto; **12 rotte che Noir non vede** (`/auth/jwt/login`, `/auth/register`, `/users/me`, `/users/{id}`, ...), senza funzione del progetto | 0 |
| fixture | 41 http + 1 websocket (8 della documentazione) | 31 su 33 (restano `/lambda` e `/endpoint`, una classe) | 39 http + 1 `ws` | 27 su 39 | 31 | 24 | 25 (6 nello stesso file) | 1 (`/endpoint`: la classe, senza funzione) | 7 (6 senza funzione del progetto; `/leaf`, un duplicato con il percorso sbagliato) |

Dove i due non concordano (fixture): **Noir non lega** 5 rotte che il framework lega: `GET` e `POST` di `/plain` (`add_route` di Starlette), `HEAD` di `/both` e `POST` di `/multi` (il secondo metodo di un `api_route`: Noir dà il gestore solo al primo), `GET /page` (un metodo legato);
**percorso sbagliato di Noir**: `/api/users/embedded/leaf`, mentre FastAPI lo serve in `/api/embedded/leaf` (`results/matches.json`: 200 e 404), più un `/leaf` che non esiste; **funzione diversa**: `/unwrapped`, il decoratore senza `functools.wraps`: il framework dà `plain.wrapper`, ciò che FastAPI esegue, Noir `read_unwrapped`, la funzione
decorata, che per chi cerca il gestore è la più utile. Nessuno dei due ha una funzione del progetto per `/lambda`, `/partial`, `/callable`, `/stdlib`, `/third-party`.
Le 5 rotte che Noir non lega hanno il gestore al secondo metodo o non lo hanno: la riga di Noir per il secondo metodo ha lo stesso `code_paths` del primo (riga del decoratore), senza `handler`: un adattatore di Noir che dà al secondo metodo il gestore del primo (stessa riga) ne recupererebbe due (`/multi`, `/both`); non è provato.

**Che cosa dicono i numeri: no, su questa prova.** Su due applicazioni vere il framework non dà **nessuna** rotta con una funzione del progetto che Noir non dia (template 23 su 23 identiche per metodo, percorso, funzione, file e riga; users 1 su 1), con tutte le condizioni favorevoli; come Daodan le farebbe girare non dà nulla su nessuna delle due (`.env` riscritti e cartella del front end,
`fastapi` senza `[standard]` e un lanciatore al posto di `main.py`). **Ma le due applicazioni non hanno i costrutti su cui Noir ha perso nel fixture**: in `template/backend/app` (21 file `.py`) e `examples/sqlalchemy` (5) non c'è nessun `add_route`, `api_route`, `add_api_route`, `.mount(`, lambda, `functools.partial`, `HTTPEndpoint` né websocket (una ricerca di testo sui sorgenti
fissati); ci sono 6 e 5 `include_router` (nel template con `prefix=settings.API_V1_STR`, in users sono fabbriche della libreria) e un `app.frontend(` nel template. Le due applicazioni non provano dove la sorgente vince; provano dove Noir regge (prefissi da variabili e da impostazioni, router annidati, un ripristino che chiede Python 3.14), e che la sorgente, come Daodan la fa girare, non carica.
Sul fixture, scritto per rompere un lettore statico, aggiunge 5 rotte legate su 31 (`add_route`, il secondo metodo di un `api_route`, un metodo legato) e il percorso giusto di un mount in un router incluso, e ne perde una (`/unwrapped`).
**users**: le rotte che il framework trova e Noir no sono 12 su 13 (le 12 dei router della libreria, `/auth/jwt/login`, `/auth/register`, `/users/me`, `/users/{id}`, ...; la tredicesima è la sua sola rotta del progetto, che Noir ha); le righe che la sorgente aggiunge sono **0**, e quello zero viene dalla regola presa da Flask (una vista nei pacchetti dell'ambiente non è una riga, è contata in una lacuna), non dalla misura. Una rotta senza funzione del progetto non è un ingresso né una rotta offerta (una rotta offerta ha un simbolo). **Che cosa ribalterebbe il verdetto**:
(1) una forma di riga per le rotte con la vista in un pacchetto (metodo e percorso, nessuna funzione) che i collegamenti sappiano offrire, e il caricatore che le trova nelle condizioni di Daodan (un `entrypoint` dichiarato, `fastapi[standard]`, nessun `.env` che le impostazioni rifiutino, nessuna cartella da compilare); oppure (2) applicazioni vere con `add_route`, `api_route` con più metodi o metodi legati, dove Noir non lega e il framework sì: da cercare, non cercate qui. Costo: lo script 3,0-4,3 s e 132-147 MB sul template (Noir 1,1 s e 191 MB); il ripristino di un progetto che chiede Python 3.14 funziona (`uv sync` scarica l'interprete con la rete aperta).
(Che la riscrittura dei `.env` giri prima di ogni comando a rete chiusa: `container.run_commands`, riga 1847: `carry = placed + ...` e `prepare=[... placed ...]`; letto nel codice e visto negli effetti, `template-script`.)

## Le due domande

**1. Come si trova l'applicazione.** Il caricatore ufficiale è quello di `fastapi-cli`, il pacchetto del comando `fastapi` (arriva con `fastapi[standard]`; non c'è
nessun comando che elenchi le rotte: `fastapi dev` e `fastapi run` avviano un server, `results/cli-*.json`). Il suo `_run` (`fastapi_cli/cli.py`, privato)
risolve in quest'ordine, scritto nel suo commento: un argomento di percorso o `--app`, poi `[tool.fastapi] entrypoint` del `pyproject.toml` della cartella, poi la
ricerca automatica. Lo script chiama le stesse tre funzioni, tutte con nome pubblico e nessuna documentata come API (`results/cli-source.json`):

- `fastapi_cli.config.FastAPIConfig.resolve()` legge `[tool.fastapi]` dal `pyproject.toml` della cartella corrente (`Path.cwd()`); l'`entrypoint` è documentato nella
  pagina di FastAPI sul CLI (`fastapi.tiangolo.com/fastapi-cli/`).
- con un `entrypoint`, `get_import_data_from_import_string` lo divide in modulo e nome, mette la cartella in `sys.path` e **non importa nulla**: l'oggetto lo carica
  `uvicorn.importer.import_from_string`, il caricatore di `modulo:nome` di uvicorn (che `fastapi-cli` richiede sempre: `Requires-Dist: uvicorn[standard]>=0.15.0` senza
  extra, `results/environment.json`), cioè quello che `fastapi run` dà al server.
- senza, `get_import_data()` prova `main.py`, `app.py`, `api.py`, `app/main.py`, `app/app.py`, `app/api.py` (l'elenco di `fastapi dev --help`; la pagina della
  documentazione dice solo «`main.py` o un paio di altre varianti»), importa il modulo (`importlib`) e prende l'oggetto FastAPI chiamato `app` o `api`, altrimenti il
  primo che `dir()` dà.

Misurato (`recorded`, `tests/fixtures/premap/fastapi/`): `entrypoint-pyproject` → `app.main:app`; senza `[tool.fastapi]` → `app/main.py`, o `main.py` se c'è (viene
prima); `api = FastAPI()` → `main:api`; una sola istanza di nome `server` → `main:server`. **Non sceglie in silenzio solo dove ha un nome**: con `first = FastAPI()` e
`second = FastAPI()` risponde `main:first` senza errore; con `inner = FastAPI()` e `app = CORSMiddleware(inner)` risponde `main:inner`, cioè un'applicazione senza il
suo involucro. Lo script lo dice (`competing`: `others`, le altre istanze FastAPI del modulo; `shadowed`, un nome preferito che contiene altro) solo quando il
caricatore è caduto sul «primo oggetto FastAPI» (`app_name_config_source` è `auto-discovery` e il nome non è `app` né `api`, i due nomi che l'aiuto del CLI elenca),
e la sorgente fa della cartella una lacuna e nessuna riga: righe di un'applicazione che il progetto potrebbe non servire, o senza il prefisso di chi la monta, sarebbero
sbagliate. Non si trova: nessun file (`Could not find a default file to run`), nessun oggetto (`Could not find FastAPI app in module`), un `entrypoint` che nomina un
modulo che non c'è (`Could not import module "nothing"`) o un oggetto senza `routes` (una stringa: lo script dice `TypeError`), un modulo che solleva o importa un
pacchetto assente. **Una fabbrica non si trova**: `fastapi-cli` non ha `--factory`. **Senza `fastapi[standard]` non c'è il caricatore** (`plain-routes`: `ModuleNotFoundError:
No module named 'fastapi_cli'`, uscita 3): la lacuna dice il pacchetto. Proposta, non fatta: leggere `[tool.fastapi] entrypoint` (e l'argomento di `uvicorn` dei
comandi di avvio) senza il CLI sarebbe un lettore a mano di un formato che `FastAPIConfig` legge già; si valuta quando un progetto vero lo chiede.

**2. Che cosa lega una rotta alla sua funzione.** `app.openapi()` dà percorso, metodo e `operationId` (`results/openapi.json`: `read_user_api_users__user_id__get`, `remove_user`), mai file
né riga, **toglie il convertitore** (`/files/{file_path}` per `/files/{file_path:path}`: l'informazione che il parametro attraversa le barre è persa), ha avvisi di `operationId`
duplicati (`/multi` e `/added`, con più metodi) e **fallisce dove un modello non ha schema JSON** mentre le rotte ci sono (`results/openapi-fails-openapi.json`:
`PydanticInvalidForJsonSchema`; `openapi-fails-routes` dà le stesse rotte del fixture più `/strange`). Non si usa. Il legame con la funzione sta negli oggetti di rotta, e in FastAPI
0.165.0 `app.routes` **non è più una lista piatta**:

- prima di 0.137.0, `include_router` copia ogni rotta del router nell'applicazione col prefisso e `app.routes` è piatta (misurato solo su 0.115.14, `results/old-dump.json`; il «prima» di 0.137.0 è delle note di rilascio);
- da 0.137.0 `include_router` tiene il router (`_IncludedRouter`, privato) e `router.routes` «va considerato un dettaglio di implementazione» (le note di rilascio di 0.137.0);
- 0.137.2 aggiunge `fastapi.routing.iter_route_contexts(routes)` «per usi avanzati che prima usavano `router.routes`» (le note di rilascio): dà un `RouteContext` per rotta, col
  percorso effettivo, `path_format`, `name`, `methods`, `endpoint`, `original_route` e `route`; gli altri attributi (`param_convertors`, `routes`, `app`) li inoltra, per
  `__getattr__`, alla rotta che rappresenta. È la funzione che anche `get_openapi` chiama. Non è nelle pagine di riferimento (letti i primi 100.000 caratteri di quella di
  `APIRouter`, e le note di rilascio per intero solo per le voci 0.137.x): è documentata solo nelle note. In 0.137.0 e 0.137.1 non c'è e `app.routes` ha `_IncludedRouter`: lo script
  li nomina (`unread`, tipo `fastapi.routing._IncludedRouter`) e la cartella ha una lacuna, con le rotte che si leggono (`mid-routes`).

Lo script usa `iter_route_contexts` se `fastapi.routing` ce l'ha, altrimenti la lista piatta: la stessa porzione di codice legge entrambi perché una rotta e un `RouteContext` hanno
gli stessi nomi. Pubblico, per nome (nessun trattino basso) e per uso, ma non documentato come API fuori dalle note: `Route.path`, `.endpoint`, `.methods`, `.name`, `.path_format`,
`.param_convertors` e `.path_regex` di Starlette (assegnati in `__init__`, `results/api-source.json`; `path_format` e `param_convertors` sono ciò che `url_path_for` usa), `Mount.path`, `.app`, `.routes`,
`Host.host`, `.app`, `.routes`, `starlette.routing.compile_path`, `APIRoute` e `APIWebSocketRoute` di FastAPI (che il manuale li citi, come `APIRoute.name` e `app.routes` per cambiare gli `operationId`, è dalla memoria e non riletto in questa prova; neppure che la documentazione di Starlette elenchi le classi dei convertitori). **Privato**: `_IncludedRouter`,
`_iter_routes_with_context`, `_RouterIncludeContext`, `_EffectiveRouteContext`, `APIRouter._low_priority_routes`, `Mount._base_app`.

## Parametri provati

| Parametro | Valori |
| --- | --- |
| Come si trova l'applicazione | `[tool.fastapi] entrypoint` (`app.main:app`, `other:service`, un modulo che non c'è, un oggetto che non è un'applicazione); nessun `[tool.fastapi]` con `app/main.py`, con `main.py` che riesporta `app`, con `api`, con un solo oggetto di altro nome, con due oggetti e nessun `app`/`api`, con `app = CORSMiddleware(inner)`, con un `main.py` senza oggetti, senza nessun file |
| Come si vede la rotta | `@app.get`/`post`/`api_route` (anche `["GET","HEAD"]`), `add_api_route` con funzione, lambda, metodo legato, oggetto con `__call__`, `functools.partial`, `json.dumps` e una funzione di `fastapi.utils`; `functools.wraps` e un decoratore senza; `include_router` con prefisso, un router in un router, un `mount` su un router incluso; `add_route` di Starlette (funzione e `HTTPEndpoint`); `@app.websocket`; `include_in_schema=False`; `operation_id`; `app.router.host(...)`; `app.frontend(...)` |
| Come non si carica | il modulo solleva (`RuntimeError`), importa un pacchetto assente, non termina (`timeout` di 5 secondi), non ha nessuna rotta (`openapi_url=None`, `docs_url=None`, `redoc_url=None`), stampa mentre si carica, `fastapi` senza `fastapi-cli` |
| Dopo il JSON | un thread non daemon che non finisce, una funzione `atexit` che stampa, un progetto che sostituisce `sys.stdout` |
| Che cosa è l'applicazione | `FastAPI(docs_url=None, redoc_url=None)` con una rotta del progetto su `/docs`; `FastAPI(root_path="/proxy")`; una `lifespan` che scrive un file; una sotto-applicazione montata con i suoi `docs_url`; una montata senza (`docs_url=None`) |
| I parametri della rotta | `{x}`, `{x:int}`, `{x:uuid}`, `{x:path}`, `{s:slug}` (convertitore proprio senza `/`), `{p:pair}` (con un `/` nella `regex`), `/{a}/{b}`, `/{a}-{b}`, `{tenant_id}` nel prefisso di un mount; `/strict/` e `/loose` |
| Dove sta la vista | nel progetto; in `site-packages` (le quattro rotte di FastAPI, `fastapi.utils.is_body_allowed_for_status_code`); nella libreria standard (`json.dumps`); senza file (`functools.partial`, oggetto con `__call__`); in un mount senza rotte (`StaticFiles`, una funzione ASGI) |
| Scala | 3000 rotte con due metodi e 1000 incluse da un router |
| Versioni | FastAPI 0.165.0 (Starlette 1.10.0), 0.137.1, 0.115.14 (Starlette 0.46.2); `fastapi-cli` 0.0.34 in tutte |
| Ambiente | quello del runner (`preparation.ENV`), `python -I`, `timeout --kill-after=10 900` (5 nelle varianti che non terminano), `cwd` la cartella che dichiara FastAPI |

## Che cosa stampa lo script (misurato)

Un solo documento JSON, e nient'altro, sullo standard output: `{"called": true, "application": "app.main:app", "found": "entrypoint-pyproject", "root_path": "", "competing": {...}, "routes": [...], "unread": [...]}`.
Prima che giri il codice del progetto, lo script salva il descrittore 1 e lo punta sullo standard error; il documento va al descrittore salvato e lo script esce con `os._exit` (il codice
condiviso con la sorgente di Flask: `python_script.run`). Un errore scrive `Tipo: messaggio` sullo standard error e esce con 3.

Ogni rotta è `{kind, path, methods, docs, parts, arguments, handler}`: `kind` è `http` o `websocket`; `path` è il percorso come lo scrive FastAPI col prefisso dei mount sopra di lui (`/files/{file_path:path}`,
`/t/{tenant_id}/info`); `methods` quelli che dichiara; `docs` se è una delle quattro rotte che FastAPI registra per sé; `parts` il percorso come coppie `[dinamico, testo]` e `arguments` ogni
argomento con ciò che il suo convertitore dice (sotto); `handler` è `{kind, type, module, qualname, file, line, environment, distribution}` (come quello di Flask: `python_script.describe`) o nullo.
`unread` elenca ciò che lo script non legge, col tipo.

| Rotta del fixture | Che cosa dà FastAPI | Riga della sorgente |
| --- | --- | --- |
| `/items`, `/items/{item_id}`, `/api/users/{user_id}` GET e DELETE, `/api/users/orders/`, `/api/users/orders/{order_id}/ship` | la funzione, `file` `app/main.py`, `app/routers/users.py`, `app/orders.py`, con il prefisso di ogni inclusione (`/api` + `/users` + `/orders`) | una riga per metodo, sul `def` |
| `/api/embedded/leaf` (un `mount` su un router incluso) | FastAPI lo serve in `/api/embedded/leaf`, non in `/api/users/embedded/leaf` (il prefisso del router non conta per i mount: `matches.json`, 200 e 404) | una riga, sul `def` di `embedded_leaf` |
| `/sub/hello`, `/sub/items/{item_id}`, `/t/{tenant_id}/info` | una sotto-applicazione FastAPI montata: le sue rotte sono dentro `Mount.routes`; il prefisso e il suo parametro li dà `compile_path(mount.path)` | una riga per metodo, col percorso intero |
| `/logged` (`@app.get` sopra `@logged`, con `functools.wraps`) | `inspect.unwrap` arriva a `read_logged` | la funzione decorata |
| `/unwrapped` (decoratore senza `wraps`) | la funzione che FastAPI esegue è `plain.<locals>.wrapper` | una riga su `plain.wrapper`: è ciò che FastAPI chiama |
| `/page` (`Pages().show`) | il metodo legato diventa la sua funzione: `qualname` `Pages.show` | una riga su `Pages.show` |
| `/multi` (`api_route`, GET e POST), `/added` (PUT e PATCH) | i metodi dichiarati, senza ordine (`sorted`) | una riga per metodo |
| `/both` (`api_route`, `["GET", "HEAD"]`), `/plain` (`add_route`, `["GET", "POST"]`) | `APIRoute.methods` non aggiunge `HEAD` e il `HEAD` dichiarato resta; la `Route` di Starlette lo aggiunge accanto a `GET` e lo script lo toglie solo lì (`/plain` dà `GET`, `HEAD`, `POST` in `route.methods`) | una riga per metodo |
| `/lambda` | `qualname` `<lambda>`, `file` `app/main.py` | una riga su `app/main.py::<module>` con la lacuna del legatore (lo snapshot la chiama `(lambda)`) |
| `/partial` (`functools.partial`) e `/callable` (oggetto con `__call__`) | `qualname` e `file` nulli, `type` `functools.partial` e `app.main.Counter` | nessuna riga, una lacuna `outside_snapshot` che dice che cos'è |
| `/endpoint` (`HTTPEndpoint`) | `kind` `class`, `methods` nulli | una riga senza metodo su `app/main.py::<module>` con la lacuna: quale metodo risponde a quale verbo non è letto |
| `/ws` (`@app.websocket`) | `kind` `websocket`, nessun metodo | una riga di forma `websocket` senza `schema` né metodo: è un ingresso, non offre una rotta (un `schema` e nessun metodo sarebbe una lacuna dei collegamenti) |
| `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc` (e `/sub/...`) | quattro `Route` di Starlette (`FastAPI.setup`), `docs` vero, la vista in `site-packages/fastapi/applications.py` | nessuna riga e nessuna lacuna (sotto) |
| `/third-party` (`fastapi.utils.is_body_allowed_for_status_code`) | `file` in `site-packages/fastapi/utils.py`, `environment` vero | contata in una lacuna `model_partial` della cartella (sotto) |
| `/stdlib` (`json.dumps`) | `file` in `/usr/local/lib/python3.12/json/__init__.py`, `environment` falso | una lacuna `outside_snapshot` con la funzione e il file |
| `/static` (`StaticFiles`) e `/raw` (funzione ASGI) | mount senza `routes` | una lacuna `model_partial` che li nomina con il tipo |

Lo snapshot: il record di una funzione decorata sta sulla riga del `def`, mentre `co_firstlineno` di Python è quella del primo decoratore; lo script prende la riga del `def` dal parse del modulo con `ast`.

**I metodi**: lo script dichiara i metodi di `route.methods` e toglie `HEAD` dove c'è `GET` solo se la rotta non è un `APIRoute`. Un `HEAD` dichiarato accanto a `GET` su una `Route` di Starlette non si distingue da quello aggiunto: si perde.

## Le quattro rotte di FastAPI e le altre viste dell'ambiente (misurato)

`FastAPI.setup` registra `openapi_url`, `docs_url` (se c'è `openapi_url`), `swagger_ui_oauth2_redirect_url` (se c'è `docs_url`) e `redoc_url` (se c'è `openapi_url`) con `add_route`: sono `Route` di Starlette,
non `APIRoute`, con una funzione locale di `fastapi/applications.py`. Lo script dice `docs` di una rotta che non è un `APIRoute` e il cui percorso è uno degli attributi dell'applicazione a cui appartiene (quella
montata ha i suoi: `/sub/docs`); la sorgente la tace solo se la vista sta nei pacchetti dell'ambiente. `docs_url=None` con una rotta del progetto su `/docs` (`docs-off`): `docs` falso, una riga.
Con un `Host` (`app.router.host(...)`) le rotte dell'applicazione ospitata sono righe sul percorso, senza il nome dell'host: nulla nei collegamenti ne legge uno.

Una vista il cui file sta nei pacchetti dell'ambiente ripristinato non è un file del progetto, come per Flask: una copia installata del progetto (PEP 610, `direct_url.json`) è una lacuna con la cartella da cui
viene; il resto è contato in una lacuna `model_partial` per cartella con il numero e i moduli («1 route of the application is a view of packages of the restored environment, not of the project: /third-party (fastapi)»).
La copia installata non è stata provata su FastAPI: il codice di `python_script.installed_from` è lo stesso che la sonda di Flask ha provato (`benchmarks/flask-routes/layouts/installed-copy`).

## Lo schema del percorso (misurato)

Una riga offre una rotta ai collegamenti (`flows._declared_routes`) solo se ha `schema`, il percorso come lo legge `REST` (`/api/users/{}`), e un metodo suo. Lo schema si fa da `path_format` e `param_convertors`, che
Starlette ricava da `compile_path` (mai dal testo di `path` con un'espressione regolare): lo script spezza `path_format` sui `{nome}` dei nomi che il framework ha dato (`url_path_for` sostituisce esattamente quelli; è scritto a mano perché nessuna funzione di Starlette dà le parti: `compile_path` dà regex, formato e convertitori, e `replace_params`, che `url_path_for` chiama, vuole un valore per ogni parametro ed esegue il `to_string` del convertitore, codice del progetto per un convertitore suo, con un valore inventato) e stampa
`parts` e `arguments`; la sorgente scrive un buco `{nome}` per ogni argomento vero e chiama `flows.path_schema`.

**Starlette non ha un `part_isolating`.** Ciò che dice se un parametro tiene un solo segmento è la classe del convertitore: `str`, `int`, `float`, `uuid` sono quelli di Starlette (classi esatte) e tengono un segmento;
`path` ne tiene più; ogni altro convertitore (registrato con `register_url_convertor`) non lo dice: `arguments` è `None`, e `None` come `false` è nessuno schema, una lacuna dei collegamenti e nessun incontro. Una prova con la
`regex` del convertitore sarebbe una regola scritta a mano sul caso. Il matcher di Starlette (`results/matches.json`, `TestClient` senza `lifespan`) mostra dove la classe tace: `/slug/a-b` 200 e `/slug/a/b` 404 (`SlugConvertor`, tiene un segmento, schema nullo),
`/pair/a/b` 200 e `/pair/a` 404 (`PairConvertor`, ne tiene due, schema nullo), `/files/a/b` 200 (`path`), `/typed/a` 404 (`int`), `/t/acme/b/info` 404 (un parametro di prefisso tiene un segmento).

| Rotta | Convertitore, `arguments` | Schema |
| --- | --- | --- |
| `/api/users/{user_id}`, `/items/{item_id}`, `/two/{a}/{b}` | `StringConvertor`, vero | `/api/users/{}`, `/items/{}`, `/two/{}/{}` (come `/admin/users/:user_id` di Noir) |
| `/typed/{n:int}`, `/uuid/{u:uuid}` | `IntegerConvertor`, `UUIDConvertor`, vero | `/typed/{}`, `/uuid/{}` |
| `/glued/{a}-{b}` | due `StringConvertor`, vero | `/glued/{}-{}`: `path_schema` lo scrive, e nessuna chiamata lo incontra (`flows._rest_meet`) |
| `/files/{file_path:path}` | `PathConvertor`, falso | nessuno |
| `/slug/{s:slug}`, `/pair/{p:pair}` | un convertitore del progetto, nullo | nessuno |
| `/t/{tenant_id}/info` (un mount con un parametro) | `tenant_id` vero; il `path` che `Mount` aggiunge (`PathConvertor`) non c'è: il prefisso è `compile_path(mount.path)` e non il `path_format` del mount | `/t/{}/info` |
| `/strict/`, `/loose` | nessun argomento | `/strict`, `/loose`: la barra finale non conta per lo schema; `/strict` e `/loose/` danno 307 (`matches.json`) |

## Come non si carica (misurato)

| Variante | Uscita | Che cosa scrive il caricatore o lo script |
| --- | --- | --- |
| nessun file di default e nessun `[tool.fastapi]` (`no-main`) | 3 | `FastAPICLIException: Could not find a default file to run, please provide an explicit path` |
| `main.py` senza un oggetto FastAPI (`no-app`) | 3 | `FastAPICLIException: Could not find FastAPI app in module, try using --app` |
| `entrypoint` su un modulo che non c'è (`entrypoint-missing`) | 3 | `ImportFromStringError: Could not import module "nothing".` |
| `entrypoint` su un oggetto che non è un'applicazione (`entrypoint-not-app`) | 3 | `TypeError: other:plain is a builtins.str, which has no routes` |
| il modulo solleva `RuntimeError('boom')` | 3 | `RuntimeError: boom`, senza traccia |
| il modulo importa un pacchetto assente | 3 | `ModuleNotFoundError: No module named 'not_installed'` |
| il modulo non termina | 124 | nessun testo; `timeout` ferma dopo 5,06 secondi |
| `fastapi` senza `fastapi[standard]` (`plain-routes`) | 3 | `ModuleNotFoundError: No module named 'fastapi_cli'` |
| il modulo stampa mentre si carica | 0 | niente sullo standard output (che è il JSON da solo) |
| nessuna rotta (`empty`) | 0 | `"routes": []` |

Le varianti registrate (`tests/fixtures/premap/fastapi/`) sono quelle che i test leggono; le altre stanno solo in `results/`.

## Dopo il JSON, la `lifespan`, `root_path` (misurato)

Con il descrittore salvato e `os._exit` (`thread`, `atexit-print`, `replaced-stdout`): uscita 0 in 0,6-1,1 secondi, un solo documento, le stesse rotte. **Caricare non è avviare**: la `lifespan` della variante scrive `lifespan-ran`
all'avvio, e `results/lifespan.json` non ha quel file in `left_in_the_project`; una rotta che una `lifespan` o un gestore di avvio aggiunge non si legge. `FastAPI(root_path="/proxy")` (FastAPI lo segnala come deprecato: «configure
the server's root path instead, with `fastapi run --root-path`») dà `root_path` `/proxy` e le stesse rotte: la sorgente le tiene e aggiunge una lacuna `model_partial` (il prefisso lo mette un proxy). `--root-path` di `fastapi run` non è
in nessun file del progetto che Daodan legga.

## Le versioni (misurato)

| Immagine | `iter_route_contexts` | Rotte lette | Non lette |
| --- | --- | --- | --- |
| FastAPI 0.165.0, Starlette 1.10.0 | sì | 42 | `/static` (`StaticFiles`), `/raw` (funzione ASGI) |
| 0.137.1 | no, `app.routes` ha `_IncludedRouter` | 37 | `_IncludedRouter` (senza percorso), `/static`, `/raw`: mancano le rotte di `/api` |
| 0.115.14, Starlette 0.46.2 | no, `app.routes` è piatta | 41: le stesse, senza `/api/embedded/leaf` | `/static`, `/raw` (`include_router` di quella versione butta un `mount` di un router incluso) |

**Non lette e non dette**: le rotte di `app.frontend(...)` non sono in `app.routes` né in `iter_route_contexts`; che stiano in una lista privata dell'applicazione (`_low_priority_routes`) è dedotto (il sorgente di `include_router` la legge; quello di `APIRouter.frontend` non è stato letto). `not_found`, un gestore che è una funzione del progetto, non è stato eseguito: che sia nello stesso posto è un'ipotesi (`frontend.json`: stessa risposta
senza e con `app.frontend("/ui", directory="static")`).

## Il Python del comando e il ripristino (misurato)

Il fixture ha il solo `pyproject.toml` (nessun `requirements.txt`): la riga del `pip` del ripristino installa `-r pyproject.toml` (`uv pip install`), 2-4 secondi in tutto con `fastapi[standard]` (il Python è `/daodan/state/venvs/bin/python`,
`purelib` `/daodan/state/venvs/lib/python3.12/site-packages`); `fastapi` senza `[standard]` 1 secondo (11 pacchetti, nessun `fastapi-cli` né `uvicorn`). La cartella radice non ha bisogno di niente di nuovo rispetto alla correzione di Flask (`mkdir -p <venvs>`).
`commands` è come quello di Flask: `preparation.python_environments`, `python_environment` e `python_interpreter` (uv workspace, Poetry, cartella con un lockfile suo: provati nei test con file in linea, non su Modal per FastAPI).

## Tempo e memoria (misurati)

| Caso | Tempo | Picco |
| --- | --- | --- |
| lo script sul fixture (42 rotte), varianti che caricano | 0,6-1,9 s | 64-75 MB |
| 3000 rotte con due metodi più 1000 incluse da un router (1.415.401 caratteri di JSON) | 3,75 s | 122 MB |
| `fastapi dev --help` | 2-2,8 s | 94 MB |
| `app.openapi()` sul fixture | 1,3 s | 71 MB |
| tutto il setup (spacchettamento di `uv`, `uv venv` e `uv pip install` di FastAPI, rete aperta) | 1-4 s | non misurato |

La memoria è la massima dei processi figli del comando (`ru_maxrss`, `timeout` compreso). `TOOLS["fastapi"]` ha `memory: 3` (GB) dei tool Node: nessuna misura lo cambia; il peso vero è dei moduli del progetto, non provato su un'applicazione grande.
Nella cartella del progetto (la copia del container) restano `__pycache__/*.pyc`; nessun file esistente cambia (`left_in_the_project`, `changed_in_the_project`).

## Il collegamento (da fare: file condivisi)

Le righe sono «un nome in una posizione» (`handler` e `site` `file:riga`): la sorgente non apre lo store dello snapshot. I test della sorgente (`tests/test_codebase_map_premap_fastapi.py`) mettono da sé, per ogni test, la voce di `container_runner.TOOLS` e la tabella
di `entry-queries.json` (`monkeypatch`); tre test controllano i file veri e sono `xfail(strict)` finché il collegamento non c'è: registro (`premap.SOURCES` e `FRAMEWORK_SOURCES`), `TOOLS["fastapi"]` uguale a `plan.TOOL`, tabella `fastapi` (`route` e `websocket`, `rotta`).
`tests/test_codebase_map_flows_fastapi_routes.py` prova gli effetti sui collegamenti: una rotta di FastAPI è una rotta offerta come quelle di Noir e Next.js (servizio `*`), si fonde con una di Noir sulla stessa funzione, una chiamata a `/api/users/7` incontra `/api/users/{user_id}`
e a `/sub/items/3` quella di una sotto-applicazione, una rotta con `{x:path}` o con un convertitore del progetto ha `schema` nullo (una lacuna dei collegamenti per metodo) e nessun incontro, un websocket è un ingresso e non una rotta.

## Limiti dichiarati e non corretti

- **Senza `fastapi[standard]` non c'è il caricatore**: la cartella è una lacuna. Molti progetti dichiarano `fastapi` e `uvicorn` separati; per loro nessuna riga.
- **`competing` guarda i nomi `app` e `api`** (quelli dell'aiuto del CLI): altri modi di avvolgere o montare l'applicazione (un'`app` Starlette che monta una FastAPI sotto un altro nome, con una sola istanza FastAPI nel modulo) non sono provati; né `--app`/path del CLI senza `entrypoint`, che nessun file dichiara.
- **Convertitori propri**: nessuno schema (nessun incontro) anche quando tengono un solo segmento (`SlugConvertor`); è la scelta prudente, perché Starlette non dice. Un convertitore che è una sottoclasse di uno di Starlette è «non dice».
- **I convertitori tipati sono tutti un buco** (`int`, `uuid`) e **`{a}-{b}`** non si incontra mai, come per Flask; una chiamata a `/loose/` incontra `/loose` (`flows._rest_meet` toglie la barra finale), mentre Starlette risponde 307.
- **Host e sottodominio non separano le rotte**; un `HEAD` dichiarato su una `Route` di Starlette non si distingue da quello aggiunto.
- **Un'applicazione che, mentre si carica, chiede un database o un servizio** (la rete è bloccata): il modulo solleverebbe o non terminerebbe; la lacuna dice la causa. Non provato su un'applicazione grande.
- **Rotte che nascono dopo il caricamento**: `lifespan`, `on_event("startup")`, `app.frontend`/`not_found`, un `include_router` fatto da un gestore di avvio; i `mount` di WSGI (`WSGIMiddleware`) sono mount senza rotte e finiscono nella lacuna di quelle non lette.
- **Il Docker di Daodan** (`buildpack-deps:noble`, il proxy dei registri): la prova gira su Modal, nella stessa immagine, con il setup eseguito con la rete aperta e il comando con la rete bloccata.
- **Non provati**: `uv.lock` di un progetto che non è un workspace, Poetry, un workspace uv con FastAPI in un membro (stesso codice di Flask, provato lì; qui solo `commands` con file in linea); un progetto che chiede un altro Python (la voce `fastapi` non ha `runs_on`); un'altra versione di
  `fastapi-cli` (la 0.0.34 in tutte le immagini; una anteriore ha `get_import_data` senza `FastAPIConfig`: l'import fallisce e la lacuna dice la causa); FastAPI prima della 0.115 o con pydantic v1; `async def`; rotte di `fastapi-utils` o di un router con una `route_class` propria
  (sottoclassi di `APIRoute`: lette come `APIRoute`); più applicazioni nello stesso progetto; `docs/plugins/codebase-map-supporto.md` da rigenerare (`python support_table.py build`).
