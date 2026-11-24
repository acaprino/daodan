# FastAPI: il caricatore di `fastapi-cli`, `iter_route_contexts` e gli oggetti di rotta

**Stato:** Provato, non nel prodotto. La sorgente [`daodan/core/premap/fastapi_app.py`](../../daodan/core/premap/fastapi_app.py) con lo script `fastapi_routes.py` è scritta e ha i suoi test (`tests/test_codebase_map_premap_fastapi.py`, `tests/test_codebase_map_flows_fastapi_routes.py`), ma non è in `premap.SOURCES` né in `FRAMEWORK_SOURCES`, non ha una voce in `container_runner.TOOLS` né una tabella in `entry-queries.json`: le patch per collegarla sono in `wiring/`, e tre test sui file veri sono `xfail(strict)` finché non lo è. Motivo: su due applicazioni vere non dà nessuna rotta con una funzione del progetto che Noir non dia, e come Daodan le lancia non carica nessuna delle due («Applicazioni vere»). Nel prodotto le rotte di FastAPI sono quelle di Noir.

## Domanda

Dove sta l'applicazione, senza una convenzione scritta a mano; che cosa dà FastAPI, caricato nel container senza rete, per ogni rotta (metodo, percorso, funzione con file e riga); come la sorgente lo lega alle funzioni dello snapshot; e se aggiunge abbastanza a Noir da essere collegata. Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14a del piano).

## Strumento ufficiale provato

FastAPI 0.165.0 con Starlette 1.10.0, fastapi-cli 0.0.34, uvicorn 0.54.0, pydantic 2.14.4, CPython 3.12.1; lo stesso fixture su FastAPI 0.115.14 (Starlette 0.46.2) e 0.137.1. Misurato su Modal il 24 novembre 2026, immagine del runner, rete bloccata.

**Come si trova l'applicazione.** Nessun comando elenca le rotte (`fastapi dev` e `fastapi run` avviano un server). Il caricatore ufficiale è quello di `fastapi-cli` (arriva con `fastapi[standard]`); lo script chiama le stesse tre funzioni del suo `_run`, pubbliche per nome e non documentate come API (`results/cli-source.json`):

- `FastAPIConfig.resolve()` legge `[tool.fastapi] entrypoint` dal `pyproject.toml` della cartella corrente (documentato in `fastapi.tiangolo.com/fastapi-cli/`);
- con un `entrypoint`, `get_import_data_from_import_string` lo divide e non importa nulla: l'oggetto lo carica `uvicorn.importer.import_from_string`;
- senza, `get_import_data()` prova `main.py`, `app.py`, `api.py`, `app/main.py`, `app/app.py`, `app/api.py`, importa il modulo e prende l'oggetto FastAPI chiamato `app` o `api`, altrimenti il primo che `dir()` dà.

Il caricatore sceglie in silenzio dove non ha un nome: con `first = FastAPI()` e `second = FastAPI()` risponde `main:first`; con `app = CORSMiddleware(inner)` risponde `main:inner`. Lo script lo dice (`competing`) e la sorgente fa della cartella una lacuna e nessuna riga. Una fabbrica non si trova (`fastapi-cli` non ha `--factory`). Senza `fastapi[standard]` non c'è il caricatore: la lacuna dice il pacchetto.

**Che cosa lega una rotta alla sua funzione.** Gli oggetti di rotta, non `app.openapi()`:

- `app.openapi()` dà percorso, metodo e `operationId`, mai file né riga, toglie il convertitore (`/files/{file_path}` per `/files/{file_path:path}`) e fallisce dove un modello non ha schema JSON mentre le rotte ci sono (`results/openapi-fails-openapi.json`). Non si usa.
- `fastapi.routing.iter_route_contexts(routes)` (da 0.137.2, nominata nelle note di rilascio, non nelle pagine di riferimento) dà un `RouteContext` per rotta con percorso effettivo, `path_format`, `methods`, `endpoint`. Prima di 0.137.0 `app.routes` è piatta e ha gli stessi attributi: lo stesso codice legge entrambi. In 0.137.0 e 0.137.1 `app.routes` ha `_IncludedRouter` (privato): lo script li nomina in `unread` e la cartella ha una lacuna.
- Privati, non usati: `_IncludedRouter`, `_iter_routes_with_context`, `_RouterIncludeContext`, `_EffectiveRouteContext`, `APIRouter._low_priority_routes`, `Mount._base_app`.

| Immagine | `iter_route_contexts` | Rotte lette | Non lette |
| --- | --- | --- | --- |
| FastAPI 0.165.0, Starlette 1.10.0 | sì | 42 | `/static` (`StaticFiles`), `/raw` (funzione ASGI) |
| 0.137.1 | no, `app.routes` ha `_IncludedRouter` | 37 | `_IncludedRouter` (senza percorso), `/static`, `/raw`: mancano le rotte di `/api` |
| 0.115.14, Starlette 0.46.2 | no, `app.routes` è piatta | 41: le stesse, senza `/api/embedded/leaf` | `/static`, `/raw` (`include_router` di quella versione butta un `mount` di un router incluso) |

## Parametri

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

File: `fixture/` (un caso per forma), `plan.py` (i comandi che il runner darebbe, e `TOOL`, la voce `container_runner.TOOLS["fastapi"]` con cui la sonda ha girato), `modal_probe.py` (il fixture e tre copie: `plain` senza `[standard]`, `old` 0.115.14, `mid` 0.137.1; registra `tests/fixtures/premap/fastapi/`), `apps.py`, `modal_real.py`, `real_summary.py` (le applicazioni vere), `results/` e `results/real/`, `wiring/` (le patch dei file condivisi e quella con cui Flask userebbe `python_script.py`).

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/fastapi-routes/modal_probe.py
... modal_probe.py --only environment,cli-source        alcune varianti, niente registrato
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/fastapi-routes/modal_real.py
python benchmarks/fastapi-routes/real_summary.py <cartella fuori dal repository per i sorgenti> <cartella di lavoro>
```

## Risultato

**Che cosa stampa lo script.** Un solo documento JSON sullo standard output (`python_script.run`, il codice condiviso con Flask: descrittore 1 salvato, uscita con `os._exit`): `{"called": true, "application": "app.main:app", "found": "entrypoint-pyproject", "root_path": "", "competing": {...}, "routes": [...], "unread": [...]}`. Ogni rotta è `{kind, path, methods, docs, parts, arguments, handler}`. Un errore scrive `Tipo: messaggio` sullo standard error ed esce con 3.

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

- La riga è quella del `def`, presa dal parse del modulo con `ast` (`co_firstlineno` è quella del primo decoratore).
- Le quattro rotte che `FastAPI.setup` registra per sé sono silenziose solo se la vista sta nei pacchetti dell'ambiente; `docs_url=None` con una rotta del progetto su `/docs` dà una riga.
- Una vista nei pacchetti dell'ambiente è contata in una lacuna `model_partial` per cartella; una copia installata del progetto (PEP 610) è una lacuna con la cartella (non provata su FastAPI: il codice è quello provato per Flask).
- Caricare non è avviare: una `lifespan` non gira, e una rotta che aggiunge non si legge. `root_path` dà le stesse rotte e una lacuna `model_partial`.

**Lo schema del percorso** si fa da `path_format` e `param_convertors`, mai dal testo di `path`. Starlette non ha un `part_isolating`: `str`, `int`, `float`, `uuid` tengono un segmento, `path` più di uno, ogni altro convertitore non lo dice e la rotta non ha schema.

| Rotta | Convertitore, `arguments` | Schema |
| --- | --- | --- |
| `/api/users/{user_id}`, `/items/{item_id}`, `/two/{a}/{b}` | `StringConvertor`, vero | `/api/users/{}`, `/items/{}`, `/two/{}/{}` (come `/admin/users/:user_id` di Noir) |
| `/typed/{n:int}`, `/uuid/{u:uuid}` | `IntegerConvertor`, `UUIDConvertor`, vero | `/typed/{}`, `/uuid/{}` |
| `/glued/{a}-{b}` | due `StringConvertor`, vero | `/glued/{}-{}`: `path_schema` lo scrive, e nessuna chiamata lo incontra (`flows._rest_meet`) |
| `/files/{file_path:path}` | `PathConvertor`, falso | nessuno |
| `/slug/{s:slug}`, `/pair/{p:pair}` | un convertitore del progetto, nullo | nessuno |
| `/t/{tenant_id}/info` (un mount con un parametro) | `tenant_id` vero; il `path` che `Mount` aggiunge (`PathConvertor`) non c'è: il prefisso è `compile_path(mount.path)` e non il `path_format` del mount | `/t/{}/info` |
| `/strict/`, `/loose` | nessun argomento | `/strict`, `/loose`: la barra finale non conta per lo schema; `/strict` e `/loose/` danno 307 (`matches.json`) |

**Come non si carica.**

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

**Tempo e memoria** (memoria: `ru_maxrss` massimo dei processi figli):

| Caso | Tempo | Picco |
| --- | --- | --- |
| lo script sul fixture (42 rotte), varianti che caricano | 0,6-1,9 s | 64-75 MB |
| 3000 rotte con due metodi più 1000 incluse da un router (1.415.401 caratteri di JSON) | 3,75 s | 122 MB |
| `fastapi dev --help` | 2-2,8 s | 94 MB |
| `app.openapi()` sul fixture | 1,3 s | 71 MB |
| tutto il setup (spacchettamento di `uv`, `uv venv` e `uv pip install` di FastAPI, rete aperta) | 1-4 s | non misurato |

Nella cartella del progetto restano i `__pycache__`; nessun file esistente cambia.

## Applicazioni vere

Gli oggetti del framework danno rotte che il Noir fissato (1.5.0) non dà? Il fixture e due applicazioni pubbliche a un commit fissato, scaricate mentre l'immagine si costruisce (`apps.py`); ripristino del runner; confronto con il codice di Daodan (`premap.write` con le risposte registrate, poi `binder.bind`). Chiave di una rotta: metodo e `flows.path_schema` del percorso. «Lega»: una funzione unica dello snapshot, con file e riga.

| Applicazione | Commit | Licenza | Perché sta qui | Ambiente del ripristino |
| --- | --- | --- | --- | --- |
| `fastapi/full-stack-fastapi-template`, cartella `backend/` di un workspace uv | `77e550a73bb4` | MIT | `app.include_router(api_router, prefix=settings.API_V1_STR)`, un router che include router con il proprio prefisso, una `lifespan`, dipendenze sugli endpoint, `app.frontend(...)` | `uv sync --locked`, CPython 3.14.6 scaricato da `uv`, FastAPI 0.141.1, Starlette 1.3.1, fastapi-cli 0.0.32 (77 pacchetti, 5 s) |
| `fastapi-users/fastapi-users`, cartella `examples/sqlalchemy` | `e9c57ff7ff2f` | MIT | ogni router lo fa una funzione della libreria (`fastapi_users.get_auth_router(...)`, `get_users_router(...)`) e lo include con un prefisso; `fastapi` dichiarato senza `[standard]` | `uv pip install -r requirements.txt`, CPython 3.12.1, FastAPI 0.165.0 (37 pacchetti, 3 s) |
| il fixture (sopra) | questo repository | | i casi che un lettore statico può sbagliare, scritti apposta: `add_route`, `api_route` con due metodi, metodo legato, lambda, `partial`, oggetto con `__call__`, un decoratore senza `functools.wraps`, un `mount` su un router incluso, convertitori | `uv pip install -r pyproject.toml`, FastAPI 0.165.0 |

**Come girano, nelle condizioni di Daodan** (con la riscrittura dei `.env` che il runner fa prima di ogni comando):

| Applicazione | Noir (1,1 s, 147-191 MB) | Script del framework |
| --- | --- | --- |
| template | 34 endpoint: **23 rotte FastAPI**, 7 rotte di React (`frontend/src/routes`), 1 voce di `compose.deploy.yml`, 3 comandi; le 23 FastAPI hanno gestore con nome, file e riga e si legano tutte (con il prefisso `/api/v1` che viene da `settings.API_V1_STR`: Noir lo risolve) | **non carica, uscita 3, 3,0 s**: `ValidationError: 6 validation errors for Settings` (`FASTAPI_ENV`, `DATABASE_URL`, `SMTP_*`, `FIRST_SUPERUSER`): il `.env` che il progetto ha nel repository è riscritto con segnaposto (`./daodan-dotenv-...`) e le impostazioni non li accettano. Con il `.env` com'è (`template-script-env`): **non carica, uscita 3, 4,3 s**: `RuntimeError: Frontend directory '/work/backend/app/frontend' does not exist` (`app.frontend(...)` chiede la cartella che la compilazione del front end crea) |
| users | 1 endpoint (`GET /authenticated-route`, legato); nessuna delle rotte dei router della libreria | **non carica, uscita 3, 0,1 s**: `ModuleNotFoundError: No module named 'fastapi_cli'` (`fastapi` senza `[standard]`: il caricatore non c'è). Con `fastapi-cli` aggiunto all'ambiente (`users-cli-script`): **non carica, uscita 3, 1,2 s**: `Could not find FastAPI app in module`: dei percorsi di default il primo che c'è è `main.py`, che è il lanciatore (`uvicorn.run("app.app:app")`), e `fastapi dev` fallirebbe uguale |
| fixture | 40 endpoint (39 http, 1 `ws`) | 42 rotte, carica, 1,7 s, 74 MB |

**Con i due ostacoli tolti** (`template-script-stub`: `.env` com'è e una cartella `backend/app/frontend` vuota; `users-cli-script-declared`: `fastapi-cli` e un `entrypoint` dichiarato):

| | Rotte del framework | di cui progetto, legate a una funzione | Endpoint FastAPI di Noir | legati | Entrambi (metodo e percorso) | stessa funzione | stesso file e riga | Solo il framework | Solo Noir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| template | 27 (4 della documentazione) | 23 su 23 | 23 | 23 su 23 | **23** | 23 | 23 | **0** | **0** (gli 8 che non sono FastAPI: React, compose) |
| users | 17 (4 della documentazione, 12 della libreria) | 1 su 1 (le 12 hanno la vista in `site-packages/fastapi_users`: nessuna riga, una lacuna che le conta) | 1 | 1 su 1 | 1 | 1 | 1 | 0 rotte di funzioni del progetto; **12 rotte che Noir non vede** (`/auth/jwt/login`, `/auth/register`, `/users/me`, `/users/{id}`, ...), senza funzione del progetto | 0 |
| fixture | 41 http + 1 websocket (8 della documentazione) | 31 su 33 (restano `/lambda` e `/endpoint`, una classe) | 39 http + 1 `ws` | 27 su 39 | 31 | 24 | 25 (6 nello stesso file) | 1 (`/endpoint`: la classe, senza funzione) | 7 (6 senza funzione del progetto; `/leaf`, un duplicato con il percorso sbagliato) |

Sul fixture, scritto per rompere un lettore statico: Noir non lega 5 rotte che il framework lega (`GET` e `POST` di `/plain`, `add_route` di Starlette; `HEAD` di `/both` e `POST` di `/multi`, il secondo metodo di un `api_route`; `GET /page`, un metodo legato); scrive `/api/users/embedded/leaf` per `/api/embedded/leaf` (`results/matches.json`: 200 e 404); per `/unwrapped` dà la funzione decorata, il framework `plain.wrapper`, ciò che FastAPI esegue.

**Verdetto: no, su questa prova.** Su due applicazioni vere il framework non dà nessuna rotta con una funzione del progetto che Noir non dia (template 23 su 23 identiche per metodo, percorso, funzione, file e riga; users 1 su 1), e come Daodan le lancia non carica nessuna delle due. In users trova 12 rotte dei router della libreria che Noir non vede, senza funzione del progetto: nessuna riga. Costo sul template: lo script 3,0-4,3 s e 132-147 MB, Noir 1,1 s e 191 MB.

Le due applicazioni non hanno i costrutti su cui Noir perde nel fixture (nessun `add_route`, `api_route`, `add_api_route`, `.mount(`, lambda, `functools.partial`, `HTTPEndpoint` né websocket nei sorgenti fissati): provano dove Noir regge, non dove la sorgente vince.

## Aperto

- **Che cosa ribalterebbe il verdetto:** (1) una forma di riga per le rotte con la vista in un pacchetto (metodo e percorso, nessuna funzione) che i collegamenti sappiano offrire, e un caricatore che le trovi nelle condizioni di Daodan; oppure (2) applicazioni vere con `add_route`, `api_route` con più metodi o metodi legati: da cercare.
- **Le rotte che nessuno dei due strumenti statici lega** (`/lambda`, `/partial`, `/callable`, le classi `HTTPEndpoint`): se il passo dinamico le osserva non è misurato ([call-provenance](../call-provenance/README.md) misura le chiamate dei test, non il legame rotta-gestore).
- Un adattatore di Noir che dia al secondo metodo di un `api_route` il gestore del primo (stessa riga) recupererebbe `/multi` e `/both`: non provato.
- **Limiti dichiarati:** senza `fastapi[standard]` nessuna riga; `competing` guarda solo i nomi `app` e `api`; i convertitori propri non hanno schema; host e sottodominio non separano le rotte; un `HEAD` dichiarato su una `Route` di Starlette non si distingue da quello aggiunto; le rotte di `app.frontend(...)` e di `not_found` non sono in `app.routes` (dedotto, non letto); `--root-path` di `fastapi run` non è in nessun file che Daodan legga.
- **Non provati:** un'applicazione grande o che chiede un servizio mentre si carica; `uv.lock` fuori da un workspace, Poetry, un workspace uv con FastAPI in un membro (solo `commands` con file in linea); un'altra versione di `fastapi-cli`; FastAPI prima della 0.115 o con pydantic v1; una `route_class` propria; più applicazioni nello stesso progetto; il Docker di Daodan (`buildpack-deps:noble`).
