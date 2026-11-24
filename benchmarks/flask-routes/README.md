# Flask: `ScriptInfo.load_app`, `app.url_map` e `app.view_functions`

**Stato:** Provato, non nel prodotto. La sorgente [`daodan/core/premap/flask_app.py`](../../daodan/core/premap/flask_app.py) con lo script `flask_routes.py` è scritta e ha i suoi test (`tests/test_codebase_map_premap_flask.py`, `tests/test_codebase_map_flows_flask_routes.py`), ma non è in `premap.SOURCES` né in `FRAMEWORK_SOURCES` e `entry-queries.json` non ha la tabella `flask`: i test le iniettano. Resta la voce `flask` di `container_runner.TOOLS`. Motivo: su quattro applicazioni vere non aggiunge a Noir quanto costa («Applicazioni vere»). Nel prodotto le rotte di Flask sono quelle di Noir.

Per ricollegarla: l'import e le due voci in `premap/__init__.py` (`SOURCES`, `FRAMEWORK_SOURCES`), `{"flask": {"route": {"kind": "rotta"}}}` in `daodan/data/entry-queries.json`, e le righe `flask` dei test che elencano le sorgenti (`tests/test_codebase_map_premap.py`, `..._premap_container_runner.py`).

## Domanda

Che cosa dà Flask, caricato nel container senza rete, per ogni rotta (metodo, percorso, funzione con file e riga), come la sorgente lo lega alle funzioni dello snapshot, e se aggiunge abbastanza a Noir da essere collegata. Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14c del piano).

## Strumento ufficiale provato

Flask 3.1.3 con Werkzeug 3.1.9, CPython 3.12.1 di Modal; misurato su Modal il 23 e il 24 novembre 2026, immagine del runner, rete bloccata.

- **`flask routes` è ufficiale e non basta:** una tabella di testo `Endpoint  Methods  Rule`, senza funzione, file, riga né JSON (`results/flask-routes-command.json`); leggerne le colonne sarebbe un lettore di un formato stampato.
- **Usati:** gli oggetti che il comando stesso interroga, `app.url_map.iter_rules()` e `app.view_functions`, dopo `ScriptInfo(app_import_path=None).load_app()` (documentato), che onora `FLASK_APP`, `.flaskenv` e `.env` come il comando.
- **Le parti di una regola:** nessun attributo pubblico dà il convertitore di ogni argomento (`Rule.arguments` ha solo i nomi, `Rule.build` esegue i `to_url` dei convertitori). Lo script legge `Rule._trace` e `Rule._converters`, privati: se la versione installata non li ha, la riga non ha schema. Werkzeug 2.2.3, 3.0.3, 3.1.8 e 3.1.9 li hanno tutti (misurato sulle applicazioni vere).

## Parametri

| Parametro | Valori |
| --- | --- |
| Come si trova l'applicazione | `wsgi.py`; `app.py`; nessuno dei due; `FLASK_APP=other:app`; `.flaskenv` senza e con `python-dotenv`; una factory `create_app()`; una factory con un argomento; due istanze di `Flask` nel modulo; `app = Dash(...)` (una classe che non è Flask) con `server = app.server`; `import app` con `server = app.app`; un `DispatcherMiddleware` come `application`, come `server`, su `app.wsgi_app`, con l'applicazione caricata come applicazione principale e come montata |
| Come si vede la rotta | `@app.route` con `methods`, `@app.post`, `@app.get`, blueprint con `url_prefix`, blueprint creato in una funzione, `add_url_rule` con metodo legato, lambda, `functools.partial`, oggetto con `__call__`; `functools.wraps` sotto `@app.get`; un decoratore senza `wraps`; `MethodView` (`get`, `post`) e `View` con `dispatch_request`; `OPTIONS`, `HEAD` e `GET`+`OPTIONS` dichiarati; `build_only`; `redirect_to`; la rotta `static` di Flask |
| Come non si carica | il modulo solleva (`RuntimeError`), importa un pacchetto assente, non termina (`timeout` di 5 secondi), non ha nessuna regola (`static_folder=None`), stampa mentre si carica |
| Dopo il JSON | un thread non daemon che non finisce, una funzione `atexit` che stampa, un progetto che sostituisce `sys.stdout` |
| Il comando ufficiale | `flask routes` e `flask routes --all-methods` nello stesso ambiente |
| Il ripristino del runner | le righe di `container_runner._python` per la fixture (`requirements.txt` e `pyproject.toml`, nessun lockfile: `pip`, cioè `uv venv` e `uv pip install -r`) e per i quattro layout (`uv sync`, `poetry install`); `uv venv` su percorsi con e senza la cartella madre (`--mode venv-dir`) |
| I parametri della regola | `<int:id>`, `<string:name>`, `<uuid:u>`, `<path:rest>` (metodi GET e PUT), `SlugConverter(BaseConverter)` con `regex` senza `/`, `TailConverter(PathConverter)` che eredita, `TailRegexConverter(PathConverter)` con `regex = ".+"`, `PairConverter(BaseConverter)` con un `/` nella `regex`, `/<a>-<b>`, `/<int:x>/<int:y>`, `/strict/`, `/loose`, `/relaxed/` con `strict_slashes=False`; `host_matching=True` con `host="api.example.com"` e `host="<sub>.example.com"` |
| Dove sta la vista | nel progetto; in `site-packages` (la rotta `static` di Flask, `werkzeug.utils.redirect`, un pacchetto locale installato); nella libreria standard (`json.dumps`); senza file (`functools.partial`, oggetto con `__call__`) |
| Scala | 3000 regole con due metodi |
| Ambiente | quello del runner (`preparation.ENV`), `python -I`, `timeout --kill-after=10 900` (5 nelle varianti che non terminano), `cwd` la cartella che dichiara Flask |

File: `fixture/` (un caso per forma), `layouts/` (quattro progetti in cui il Python del comando non è quello della cartella: `uv-workspace`, `poetry`, `root-and-sub`, `installed-copy`), `plan.py` (i comandi che il runner darebbe), `modal_probe.py` (registra `tests/fixtures/premap/flask/`), `apps.py`, `modal_real.py`, `real_summary.py` (le applicazioni vere), `results/` e `results/real/`. `results/before-the-fix/` e `results/before-review/` sono esecuzioni precedenti a correzioni ormai nel codice.

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/flask-routes/modal_probe.py
... modal_probe.py --mode venv-dir | --mode lock | --only environment,werkzeug-source
DAODAN_FLASK_APPS=<cartella fuori dal repository> PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/flask-routes/modal_real.py
python -I benchmarks/flask-routes/real_summary.py <cartella dei sorgenti> <cartella di lavoro> [casi]
```

## Risultato

**Che cosa stampa lo script.** Un solo documento JSON sullo standard output, `{"called": true, "dispatch": null, "routes": [...]}`: lo script salva il descrittore 1 (a un numero da 100 in su) prima che giri il codice del progetto ed esce con `os._exit`, così stampe, thread e funzioni `atexit` non lo sporcano né lo trattengono (`thread`, `atexit-print`, `replaced-stdout`: uscita 0 in 0,2-0,3 secondi). Un errore scrive `Tipo: messaggio` ed esce con 3; un documento che non si può scrivere esce con 4. Ogni regola è `{rule, methods, build_only, redirect_to, static, parts, arguments, handler}`.

| Regola della fixture | Che cosa dà Flask | Riga della sorgente |
| --- | --- | --- |
| `/` GET, `/items` POST, `/admin/stats` GET, `/admin/users/<int:user_id>` GET e POST | la funzione, `file` `wsgi.py` o `admin/blueprint.py`, `qualname` `index`, `user`... | una riga per metodo, sul `def` |
| `/wrapped` (`@app.get` sopra `@guarded`, che usa `functools.wraps`) | `inspect.unwrap` arriva a `wrapped` | la funzione decorata |
| `/unwrapped` (decoratore senza `wraps`) | la funzione che Flask esegue è `plain.<locals>.wrapper` | una riga su `plain.wrapper`: è ciò che Flask chiama; la funzione decorata non è raggiungibile |
| `/page` (`Pages().show`) | il metodo legato diventa la sua funzione: `qualname` `Pages.show` | una riga su `Pages.show` |
| `/nested/inner` (funzione dentro `make_blueprint`) | `qualname` `make_blueprint.<locals>.inner` | una riga con `handler` `inner` alla riga del suo `def`: il legatore dei collegamenti la lega alla sola funzione con quel nome che contiene la riga (`make_blueprint.inner`) |
| `/docs` (un metodo) e `/nested-doc` (funzione annidata e decorata) con una riga a colonna 0 in una stringa | `line` alla riga del `def` | una riga sul `def` (dal parse del modulo intero: il `def` il cui primo decoratore o `def` è `co_firstlineno`) |
| `/lambda` | `qualname` `<lambda>`, `file` `wsgi.py` | una riga su `wsgi.py::<module>` con la lacuna del legatore («reports this entry without a unique snapshot handler»: lo snapshot la chiama `(lambda)`) |
| `/partial` (`functools.partial`) e `/callable` (oggetto con `__call__`) | `qualname` e `file` nulli, `type` `functools.partial` e `wsgi.Counter` | nessuna riga, una lacuna `outside_snapshot` che dice che cos'è |
| `/orders` (`MethodView`), `/hello` (`View`) | `kind` `class`, `qualname` `Orders` e `Hello`, `methods` quelli della regola | una riga per metodo su `wsgi.py::<module>` con la lacuna: quale metodo risponde a quale verbo non è letto |
| `/options` (`methods=["OPTIONS"]`), `/head-only` (`["HEAD"]`), `/get-options` (`["GET", "OPTIONS"]`) | `["OPTIONS"]`, `["HEAD"]`, `["GET", "OPTIONS"]` | una riga per metodo dichiarato, sul `def` |
| `/built` (`build_only=True`), `/old` (`redirect_to="/new"`) | nessuna vista, `build_only` e `redirect_to` veri | nessuna riga e nessuna lacuna: werkzeug non incontra mai la prima, la seconda risponde con un rinvio |
| `/static/<path:filename>` | la lambda `Flask.__init__.<locals>.<lambda>` in `.../site-packages/flask/app.py`, `environment` vero, `static` vero | nessuna riga e nessuna lacuna (sotto) |
| `/assets/files/<path:filename>` (un blueprint con `static_folder="files"`) | il `send_static_file` del blueprint, in `site-packages/flask/blueprints.py`, `environment` vero, `static` vero | nessuna riga e nessuna lacuna (sotto) |
| `/third-party` (`werkzeug.utils.redirect`) | `file` in `site-packages/werkzeug/utils.py`, `environment` vero | contata in una lacuna `model_partial` della cartella (sotto) |
| `/stdlib` (`json.dumps`) | `file` in `/usr/local/lib/python3.12/json/__init__.py`, `environment` falso | una lacuna `outside_snapshot` con la funzione e il file: fuori dallo snapshot e fuori dall'ambiente |

- **I metodi:** lo script toglie solo ciò che il framework aggiunge: `OPTIONS` se `provide_automatic_options`, `HEAD` se c'è `GET`. Un `HEAD` dichiarato accanto a `GET` si perde.
- **Le viste dei pacchetti dell'ambiente:** le regole `static` di Flask (dell'applicazione e dei blueprint) sono silenziose; una copia installata del progetto (PEP 610) è una lacuna `outside_snapshot` con la cartella; il resto una sola lacuna `model_partial` per cartella.

**Lo schema del percorso** si fa dalle parti che Werkzeug ha ricavato, mai dal testo di `rule`: un buco per ogni argomento il cui convertitore ha `part_isolating` vero, l'attributo documentato di `BaseConverter`. Il percorso che il matcher accetta segue l'attributo in ogni caso provato (`results/url-matching.json`).

| Regola | Convertitore, `part_isolating` | `url_map` accetta | `schema` |
| --- | --- | --- | --- |
| `/admin/users/<int:user_id>` | `IntegerConverter`, vero | `/admin/users/7` | `/admin/users/{}` (come `/admin/users/:user_id` di Noir) |
| `/string/<string:name>`, `/uuid/<uuid:u>`, `/int/<int:id>` | `UnicodeConverter`, `UUIDConverter`, `IntegerConverter`, vero | un segmento (`/string/a/b`: non trovato) | `/string/{}`, `/uuid/{}`, `/int/{}` |
| `/slug/<slug:s>` | `SlugConverter(BaseConverter)`, `regex` senza `/`: vero | `/slug/a-b`; `/slug/a/b` no | `/slug/{}` |
| `/files/<path:name>` (GET, PUT) | `PathConverter`, falso | `/files/a/b` | nessuno: due lacune dei collegamenti, una per metodo |
| `/tail/<tail:rest>` | `TailConverter(PathConverter)` che eredita: falso | `/tail/a/b` | nessuno |
| `/tailre/<tailre:rest>` | `TailRegexConverter(PathConverter)` con `regex = ".+"`: **vero** (`"/" not in ".+"`) | `/tailre/a`; `/tailre/a/b` **no** | `/tailre/{}`: il matcher lo prende per un solo segmento |
| `/pair/<pair:p>` | `PairConverter(BaseConverter)`, un `/` nella `regex`: falso | `/pair/a/b`; `/pair/a` no | nessuno |
| `/glued/<a>-<b>` | due `UnicodeConverter`, vero | `/glued/x-y` | `/glued/{}-{}`: `path_schema` lo scrive, e nessuna chiamata lo incontra (`flows._rest_meet` valuta un buco incollato a un testo solo dal lato della chiamata) |
| `/strict/`, `/loose`, `/relaxed/` (`strict_slashes=False`) | nessun argomento | `/strict/` sì, `/strict` con un rinvio; `/loose` sì, `/loose/` no; `/relaxed/` e `/relaxed` sì | `/strict`, `/loose`, `/relaxed`: la barra finale non conta per lo schema |

**Come non si carica.**

| Variante | Uscita | Che cosa scrive Flask o lo script |
| --- | --- | --- |
| nessun `wsgi.py` né `app.py` | 3 | `NoAppException: Could not locate a Flask application. Use the 'flask --app' option, 'FLASK_APP' environment variable, or a 'wsgi.py' or 'app.py' file in the current directory.` |
| `FLASK_APP=other:app` | 0 | le rotte di `other.py`: la variabile si legge come la legge il comando |
| `.flaskenv` con `FLASK_APP`, senza `python-dotenv` | 3 | ` * Tip: There are .env files present. Install python-dotenv to use them.` e poi lo stesso `NoAppException`: il file è ignorato, e il ripristino del runner non installa `python-dotenv` (extra `flask[dotenv]`) |
| lo stesso con `python-dotenv` installato | 0 | le rotte: `.flaskenv` è letto da `load_dotenv` |
| `app.py` al posto di `wsgi.py` | 0 | le stesse rotte (il pacchetto della fixture è `admin/`, non `app/`, perché un pacchetto `app/` accanto a `app.py` avrebbe preso il posto del modulo: dal comportamento di Python, non provato) |
| una factory `create_app()` | 0 | le rotte della factory (`create_app.<locals>.made`) |
| una factory con un argomento | 3 | `NoAppException: Detected factory 'create_app' in module 'wsgi', but could not call it without arguments. Use 'wsgi:create_app(args)' to specify arguments.` |
| due istanze di `Flask` | 3 | `NoAppException: Detected multiple Flask applications in module 'wsgi'. Use 'wsgi:name' to specify the correct one.` |
| il modulo solleva `RuntimeError('boom')` | 3 | `RuntimeError: boom`: Flask non lo avvolge, lo script stampa `Tipo: messaggio` senza traccia |
| il modulo importa un pacchetto assente | 3 | `NoAppException: While importing 'wsgi', an ImportError was raised:` e la traccia, che finisce con `ModuleNotFoundError: No module named 'not_installed'` (`frameworks.excerpt` tiene l'inizio e la fine: il nome del pacchetto resta) |
| il modulo non termina | 124 | nessun testo; `timeout` ferma dopo 5,05 secondi |
| il modulo stampa mentre si carica | 0 | niente sullo standard output (che è il JSON da solo): una stampa non svuotata muore con il suo buffer, una svuotata sta sullo standard error |
| nessuna regola | 0 | `{"called": true, "dispatch": null, "routes": []}` (con `static_folder=None`; con il valore predefinito la regola `static` c'è sempre) |

**`DispatcherMiddleware`.** Una regola `/hello` di un'applicazione montata a `/sub` si serve a `/sub/hello` (`results/dispatcher-serves.json`), e il caricatore di Flask può scegliere proprio l'applicazione montata. Lo script cerca i dispatcher per classe (su `app.wsgi_app` e fra le variabili globali del modulo) e dice dove sta l'applicazione caricata:

| Caso | `loaded` | Righe | Lacuna |
| --- | --- | --- | --- |
| nessun dispatcher (`app = Dash(...)` con `server = app.server`, `import app` con `server = app.app`: l'`app` non è Flask) | nullo | sì | nessuna |
| `application = DispatcherMiddleware(Flask("main"), {"/sub": sub})` con `sub` caricata, o la stessa con un altro nome (`server`) | `mounted`, `prefixes` `["/sub"]` | nessuna: le regole mancano del prefisso | `model_partial`: «the loaded application is mounted by a DispatcherMiddleware at /sub: its rules lack the prefix, so none is read», e le altre applicazioni Flask che serve |
| `application = DispatcherMiddleware(app, {"/sub": sub})`, o `app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/sub": sub})` | `main` | sì: le regole dell'applicazione principale sono servite come sono | `model_partial` che nomina le applicazioni montate con le loro regole come le serve (`/sub/hello`), non come righe |
| un dispatcher che non tiene l'applicazione caricata ma serve altre applicazioni Flask | `other` | nessuna: non si sa a che percorsi sia servita | `model_partial` |

Un avvolgimento che non è un `DispatcherMiddleware` non si vede.

**Il Python del comando** è quello dell'ambiente che il ripristino fa per la cartella più vicina in alto (`preparation.python_environment` e `python_interpreter`, lo stesso codice del passo dinamico dei test Python); il `cwd` resta la cartella che dichiara Flask.

| Layout | Cartella che dichiara Flask, ambiente | Uscita | Risultato |
| --- | --- | --- | --- |
| `uv-workspace` | `api`, la radice (`uv sync --all-packages`: le dipendenze dei membri sono nell'ambiente della radice) | 0 in 0,53 s, 53 MB | `/hello` e `static`, la riga su `api/wsgi.py` |
| `poetry` | la radice, Poetry (`"$(cd /work/. && poetry env info -e)"`) | 0 in 1,73 s, 88 MB | `/hello` e `static`; Flask è dichiarato solo in `pyproject.toml` (la sorgente `requirements` non lo legge: lo dice il grafo dei moduli) |
| `root-and-sub` | `api`, la radice (`pip`: installa le dipendenze di `pyproject.toml`, non `api/requirements.txt`) | 3 in 0,15 s | `ModuleNotFoundError: No module named 'flask'`; la lacuna lo dice con l'ambiente («the Python of the environment restored for '.'») |
| `installed-copy` | la radice | 0 in 0,64 s | `/own` è una riga, `/shared` una lacuna: copia installata del progetto |

`uv venv <madre>/.` fallisce quando `<madre>` non esiste (uv 0.11.28, `results/venv-dir.json`): `container_runner._python` fa precedere il ripristino da `mkdir -p <venvs>`, e `preparation.restores` ordina la radice per prima.

**Tempo e memoria** (memoria: `ru_maxrss` massimo dei processi figli):

| Caso | Tempo | Picco |
| --- | --- | --- |
| lo script sulla fixture (37 regole), varianti che caricano | 0,2-0,7 s | 48-54 MB |
| 3000 regole, 6000 metodi (1.207.317 caratteri di JSON) | 1,25 s | 76 MB |
| un progetto Poetry (con `poetry env info -e`) | 1,73 s | 88 MB |
| `flask routes` | 0,6-0,7 s | 53 MB |
| tutto il setup (spacchettamento di `uv`, `uv venv` e `uv pip install` di Flask, rete aperta) | 1-2 s | non misurato |

Nella cartella del progetto restano i `__pycache__`; nessun file esistente cambia.

## Applicazioni vere

Gli oggetti di Flask danno rotte che il Noir fissato (1.5.0) non dà? Il fixture e quattro applicazioni pubbliche a un commit fissato, scaricate mentre l'immagine si costruisce (`apps.py`); ripristino del runner, poi la riscrittura dei `.env`, poi `noir scan /work -f json --no-log` o il comando di `flask_app.commands`. Confronto con il codice di Daodan (`premap.write` con le risposte registrate, poi `binder.bind`). Chiave di una rotta: metodo e `flows.path_schema` del percorso. «Legata»: una funzione unica dello snapshot, con file e riga. I conteggi di Noir sono dei suoi endpoint di file `.py`.

| | CTFd | Redash | shhh | microblog-api |
| --- | --- | --- | --- | --- |
| repository | `CTFd/CTFd` | `getredash/redash` | `smallwat3r/shhh` | `miguelgrinberg/microblog-api` |
| commit | `f9fa28b2f17b` | `f561a53dc55e` | `448acf4bed05` | `e250d7115b47` |
| licenza (SPDX di GitHub, file `LICENSE`) | Apache-2.0 | BSD-2-Clause | MIT | MIT |
| file, di cui `.py` | 1.051, 357 | 1.976, 309 | 66, 28 | 50, 30 |
| Flask, Werkzeug, Python | 2.2.5, 2.2.3, 3.11.15 (`uv` lo scarica: `requires-python = ">=3.11,<3.12"`) | 3.1.3, 3.1.8, 3.13.14 (scaricato) | 3.1.3, 3.1.9, 3.12.1 (quello di Modal) | 3.0.3, 3.0.3, 3.12.1 |
| ripristino | `uv sync --locked`, 9 s, 93 pacchetti | `uv sync --locked`: **fallisce**, 7 s (vedi sotto); con `--frozen` 10 s, 103 pacchetti | `uv pip install -r requirements.txt`, 3 s, 37 pacchetti | idem, 2 s, 35 pacchetti |

Le forme che un lettore statico può sbagliare, e che cosa danno i due:

| Forma | Dove | Che cosa danno Flask e Noir |
| --- | --- | --- |
| `url_prefix` dato a `register_blueprint` | `microblog-api`: `api/app.py:33`, `:35`, `:37` (`app.register_blueprint(tokens, url_prefix='/api')`) | 28 rotte per entrambi, stessi percorsi, stessa funzione, stessa riga |
| `url_prefix` letto dalla configurazione | **nessuna delle quattro** (cercato `url_prefix` e `register_blueprint`): non misurato | |
| blueprint dentro un blueprint | `CTFd`: `CTFd/views.py:75` (`views.register_blueprint(git)`), `CTFd/git.py:19` (`url_prefix="/setup/git"`) | le 7 regole di `/setup` e `/setup/git/...` (11 rotte): le stesse, con funzione e riga |
| application factory | `CTFd/__init__.py:195`, `redash/app.py:25`, `shhh/entrypoint.py:28`, `api/app.py:16` | Flask la carica con il suo caricatore (`create_app` o `wsgi.py` che la chiama); Noir non la esegue e dà gli stessi percorsi |
| `add_url_rule` | `shhh/api/api.py:42` (con `Api.as_view`), `CTFd/plugins/__init__.py:42` e `:64` (una per cartella di plugin: 3 rotte `/plugins/<nome>/assets/<path:path>` nell'esecuzione) | shhh: uguali; **le 3 dei plugin le dà solo Flask** (con funzione e riga). `add_url_rule` dentro un ciclo: **non c'è** nelle quattro, non misurato |
| vista a classe, `MethodView` | `shhh/api/api.py:30` (`class Api(MethodView)`); 90 classi `Resource` in `CTFd/api/` (90 regole); 71 regole di classi `Resource` in Redash | la sorgente dà una **riga con la lacuna della classe** per ogni metodo HTTP (279 righe su 443); Noir dà il metodo (`Api.get`, file e riga) |
| estensione che registra rotte | `CTFd`: Flask-RESTX (`CTFd/api/__init__.py:56`, `add_namespace(ns, "/challenges")`); `Redash`: Flask-RESTful (`redash/handlers/api.py:101`, `add_org_resource`, 66 righe `api.add_org_resource(...)`); `microblog-api`: APIFairy (`/docs`, `/apispec.json`). Flask-Admin e flask-smorest: **non misurati** | le rotte delle classi: le stesse; le viste delle estensioni (2 di RESTX, 2 di APIFairy) le dà solo Flask, **senza funzione del progetto** (una lacuna `model_partial`, nessuna riga) |
| decoratori attorno alle viste | `CTFd/utils/decorators/__init__.py:14`, `:85`, `:125` (`during_ctf_time_only`, `authed_only`, `admins_only`, con `functools.wraps`); `redash/permissions.py:78` (`require_permission`); `@authenticate(token_auth)` e `@response(...)` di APIFairy; `functools.partial(use_kwargs, ...)` in `shhh/api/api.py:26` | Flask dà la funzione sotto il decoratore (`inspect.unwrap`) e Noir la stessa: su 160 delle 164 righe con funzione (le altre 4 sono rotte che Noir non ha) |

**Come girano, nelle condizioni di Daodan:**

| | CTFd | Redash | shhh | microblog-api |
| --- | --- | --- | --- | --- |
| script del framework, come lo lancia il runner | **carica**, 5,97 s, 291 MB | **non carica**, uscita 3, 0,35 s: `ModuleNotFoundError: No module named 'flask'` (il ripristino è fallito: `error: The lockfile at uv.lock needs to be updated, but --locked was provided`, nessun ambiente) | **non carica**, uscita 3, 3,0 s: `RuntimeError: env=None specified in FLASK_ENV is not supported` (`wsgi.py` fa `create_app(os.environ.get("FLASK_ENV"))`) | **carica**, 2,46 s, 152 MB (`FLASK_APP` da `.flaskenv`; `python-dotenv` è fra i pacchetti) |
| con quel che manca messo (una variante per passo) | | `--frozen`: `NoAppException: Could not locate a Flask application` (nessun `wsgi.py` né `app.py` alla radice: l'applicazione è `redash/wsgi.py`); con `FLASK_APP=redash.wsgi`: `Exception: You must set the REDASH_COOKIE_SECRET` (alle impostazioni); con un segreto: `ConnectionError: Error 111 connecting to localhost:6379` (`create_app` chiede la versione di Redis); **con un Redis sul loopback** (`redis-server` di apt, nell'immagine): carica, 4,32 s, 234 MB, 100 regole. PostgreSQL non serve per caricare | con `FLASK_ENV=testing` (SQLite in memoria): carica, 3,26 s, 102 MB, 6 regole | |
| Noir (1.5.0) | 253 endpoint (251 http, 2 cli), 1,91 s, 171 MB | 318 (311 http, 7 cli), 2,81 s, 250 MB | 6, 0,92 s, 148 MB | 28, 0,67 s, 149 MB |
| lasciato nel progetto dallo script | `.ctfd_secret_key` e `.data/filesystem_cache/` (3 file) | niente | 4 file compilati in `shhh/static/dist/` | niente |

Due applicazioni su quattro caricano come Daodan le lancia (CTFd, microblog-api); shhh chiede una variabile che il suo `wsgi.py` legge; Redash quattro cose (un lockfile in regola, `FLASK_APP`, un segreto e un Redis). Noir gira su tutte e quattro in meno di 3 s senza preparazione. Il ripristino di Redash fallisce perché il suo `uv.lock` non segue la versione del `pyproject.toml` e Daodan usa `uv sync --locked` (`preparation.RESTORES`); con `--frozen` riesce.

**Il confronto** (Flask: l'esecuzione che carica, con quel che manca per Redash e shhh; le rotte sono una per regola e metodo, senza le regole `static`):

| | CTFd | Redash | shhh | microblog-api |
| --- | --- | --- | --- | --- |
| regole di Flask / rotte | 174 (172 non statiche) / 254 | 100 (99) / 157 | 6 (5) / 6 | 31 (30) / 30 |
| righe della sorgente | 252 | 157 | 6 | 28 |
| di cui legate a una funzione | 98 | 34 | 4 | 28 |
| di cui la lacuna della classe | 154 (61 %) | 123 (78 %) | 2 | 0 |
| viste di un pacchetto (una lacuna `model_partial`, nessuna riga) | 2 (`flask_restx`) | 0 | 0 | 2 (`apifairy`) |
| endpoint di Noir, di file `.py` | 249 | 160 | 6 | 28 |
| legati a una funzione (`name` o `qualified_name` alla riga citata) | **249** | **160** | **6** | 28 |
| rotte che entrambi danno (metodo e schema) | 248 | 157 | 6 | 28 |
| ... di cui stessa funzione, stesso file e riga | 94 | 34 | 4 | 28 |
| ... di cui la sorgente dà la classe, Noir il metodo (file e riga) | 154 | 123 | 2 | 0 |
| ... stessa funzione sotto un altro percorso | 0 | 0 | 0 | 0 |
| **solo Flask** | **6**: 3 plugin (`add_url_rule`), 1 copia di una regola (`themes_beta`, `CTFd/views.py:548`, stesso metodo e percorso di `themes`, `:526`), 2 viste di RESTX | **0** | **0** | **2**: le viste di APIFairy, senza funzione del progetto |
| **solo Noir** | **1**: `HEAD /api/v1/notifications` (una `def head` che la sorgente toglie, `declared()` toglie `HEAD` con `GET`) | **3**: `/oidc`, `/<org_slug>/oidc`, `/oidc/callback` (il blueprint di `create_oidc_blueprint` esiste solo con `OIDC_ENABLED`: Noir dà il codice di un profilo spento) | **0** | **0** |

Il legatore lega un endpoint di Noir il cui nome è il `name` o il `qualified_name` della dichiarazione alla riga citata (`Api.get`): tutti gli endpoint di Noir che hanno un nome si legano. La stessa misura su 25 applicazioni è in [noir-binding](../noir-binding/README.md).

Sul fixture (`results/real/fixture-summary.json`): 38 rotte per metodo in comune, 27 con la stessa funzione; Flask dà la funzione dove Noir no per 2 (`/page` e `/docs`, un metodo legato); per `/unwrapped` Flask dà `plain.wrapper`, ciò che esegue, Noir la funzione decorata; nessuno dei due dà una funzione per 8.

**Verdetto: no.** Delle 443 righe della sorgente 164 hanno una funzione, e Noir dà la stessa, con lo stesso file e la stessa riga, su 160; le 4 in più sono di CTFd (3 asset dei plugin, una regola copiata). Per le altre 279 rotte, i metodi delle classi (`MethodView`, `Resource`), la sorgente dà una lacuna della classe e Noir la funzione. Solo Flask: 8 rotte su 447 (4 con funzione del progetto, 4 viste di estensioni senza); solo Noir: 4. Il costo è un ambiente da ripristinare (2-10 s), il codice del progetto eseguito, e nessuna riga su 2 applicazioni su 4. Anche con una sorgente che risolvesse le classi (`getattr(view_class, verbo.lower())`: non scritto) resterebbe a +4 rotte con funzione su 447.

## Aperto

- **Le rotte che nessuno dei due strumenti statici lega** (lambda, `functools.partial`, oggetti con `__call__`): se il passo dinamico le osserva non è misurato ([call-provenance](../call-provenance/README.md) misura le chiamate dei test, non il legame rotta-gestore).
- **Non misurato sulle applicazioni vere:** `url_prefix` letto dalla configurazione, `add_url_rule` in un ciclo, Flask-Admin e flask-smorest; le quattro applicazioni sono scelte, non campionate; il Docker di Daodan (`buildpack-deps:noble`).
- **Difetti noti, non corretti:**
  - `flask_routes.declared()` toglie `HEAD` con `GET` anche quando la classe lo dichiara (`def head`): una rotta su 447. Il dato c'è (`view_class.methods`); correggerlo cambia `VERSION` e le risposte registrate.
  - `uv sync --locked` non dà un ambiente a un progetto il cui lock non segue la versione (Redash).
  - Un pacchetto costruito su Flask (Dash, Flask-RESTX) dichiarato al posto di `flask` non avvia la sorgente: parte dai pacchetti dichiarati, e la pre-mappa non legge i pacchetti risolti di un lock Python.
  - `flask` scritto `Flask>=3` in un `pyproject.toml` non avvia la sorgente: il nome non è normalizzato come fa la sorgente di Django (letto nel codice, provato solo per Django).
- **Limiti dei collegamenti:** una chiamata a `/loose/` incontra `/loose` (Werkzeug risponde «non trovato»); i convertitori tipati sono tutti un buco; `/<a>-<b>` non incontra mai una chiamata; host e sottodominio non separano le rotte; `.env` è riscritto dal container e `.flaskenv` no.
- **Non provati:** `uv.lock` fuori da un workspace, Poetry con più cartelle, `async def`, più applicazioni nello stesso progetto, rotte aggiunte dopo l'avvio, un'uscita grande con il motore (3000 regole sono 1,2 MB di JSON).
