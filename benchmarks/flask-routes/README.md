# Flask: `ScriptInfo.load_app`, `app.url_map` e `app.view_functions`

Domanda: che cosa dà Flask, caricato nel container senza rete, per ogni rotta (metodo, percorso, funzione con file e riga), e come la sorgente della pre-mappa
[`daodan/core/premap/flask_app.py`](../../daodan/core/premap/flask_app.py) lo lega alle funzioni dello snapshot. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14c.
**Misurato il 23 e il 24 novembre 2026 su Modal** (Flask 3.1.3 con Werkzeug 3.1.9, immagine del runner, rete bloccata); i numeri sotto sono di quelle esecuzioni. **La sorgente non è collegata** (decisione del 24 novembre 2026, dopo «Applicazioni vere»): scritta, misurata e provata, fuori da `premap.SOURCES`, `premap.FRAMEWORK_SOURCES` e `entry-queries.json`; vedi «Il collegamento».

Il codice del progetto (la fixture, i layout, Flask, i loro pacchetti) gira solo nel container, mai su questa macchina: le immagini si costruiscono con la rete aperta (l'unico momento in cui lo è) e ogni variante gira in una copia della cartella con la rete bloccata.

| Cartella o file | Contenuto |
| --- | --- |
| `fixture/` | `wsgi.py` (rotte con `@app.route`, `@app.post`, `@app.get`, `functools.wraps` e un decoratore senza, un metodo legato, una lambda, una `functools.partial`, un oggetto con `__call__`, `MethodView` e `View.as_view`, `methods=["OPTIONS"]`, `["HEAD"]` e `["GET", "OPTIONS"]`, `build_only` e `redirect_to`, un convertitore per ogni caso: `int`, `string`, `uuid`, `path`, tre convertitori propri, due parametri in un segmento, barra finale con e senza `strict_slashes`, un sottodominio, una funzione di `json` e una di `werkzeug.utils`, un metodo e una funzione annidata decorata con una riga a colonna 0 in una stringa), `admin/blueprint.py` (un blueprint con prefisso, uno con una cartella statica e uno creato in una funzione), `requirements.txt` e `pyproject.toml` |
| `layouts/` | quattro progetti in cui il Python del comando non è `<venvs>/<cartella>/bin/python`: `uv-workspace` (la radice ha `uv.lock` e il workspace, `api` dichiara Flask), `poetry` (Flask solo in `pyproject.toml`, con `poetry.lock`), `root-and-sub` (un `pyproject.toml` alla radice e `api/requirements.txt`), `installed-copy` (`requirements.txt` con `./libs/shared`, un pacchetto locale installato non in modalità modificabile). I due lockfile sono fatti una volta con `--mode lock` |
| `plan.py` | stampa, con il Python che ha le dipendenze di Daodan (`DAODAN_PYTHON`, di default `python`; `DAODAN_PROBE_TMP` per i file di lavoro), per una cartella: i comandi di `flask_app.commands`, il comando di setup di `container_runner.plan`, le righe di ripristino di `container_runner._python` e i file che il setup spacchetta: legge solo i nomi dei file |
| `modal_probe.py` | costruisce un'immagine del runner (`container_runner.IMAGE`, con il Python di Modal accanto) per la fixture e per ogni layout, esegue il setup di `plan.py` come lo esegue il runner, con il progetto in `/work` (`container.WORKDIR`: Poetry lega il suo ambiente al percorso del progetto), poi ogni variante con la rete bloccata e nel `cwd` che il comando della sorgente dice; scrive `results/` e, per le varianti in `RECORDED`, `tests/fixtures/premap/flask/` con `script.json` (impronta dello script e `VERSION`) |
| `apps.py`, `modal_real.py`, `real_summary.py` | le applicazioni vere (indirizzo, commit, licenza), il lanciatore su Modal che ne costruisce le immagini e le fa girare con Noir, e il confronto fra le due risposte: vedi «Applicazioni vere» |
| `results/<variante>.json` | `argv`, `cwd`, `returncode`, `stdout` (i primi 20.000 caratteri), `stderr`, secondi, memoria di picco, file lasciati e cambiati nel progetto; `venv-dir.json` per `--mode venv-dir`; `before-the-fix/` la prima esecuzione (prima di correggere il ripristino), `before-review/` l'esecuzione prima delle correzioni della revisione (Python scelto dalla cartella, uscita dopo il JSON) |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/flask-routes/modal_probe.py
... modal_probe.py --mode venv-dir | --mode lock | --only environment,werkzeug-source | --label before-review
DAODAN_FLASK_APPS=<cartella fuori dal repository> PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/flask-routes/modal_real.py   (le applicazioni vere; `--only <varianti>`)
python -I benchmarks/flask-routes/real_summary.py <cartella dei sorgenti> <cartella di lavoro> [casi]                                                                     (il confronto, `results/real/<caso>-summary.json`)
```

## Parametri provati

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

## `flask routes` è ufficiale, e non basta

`flask routes` esiste (`flask/cli.py`, `routes_command`) e dà una tabella di testo `Endpoint  Methods  Rule` ordinata per endpoint, senza funzione, file né riga e senza JSON (`results/flask-routes-command.json`). Nasconde `HEAD` e `OPTIONS`; `--all-methods` li mostra (`results/flask-routes-all-methods.json`). Non si usa: leggerne le colonne sarebbe un lettore di un formato stampato. La sorgente chiama gli oggetti che il comando stesso interroga, `app.url_map.iter_rules()` e `app.view_functions`, dopo averli caricati con `ScriptInfo(app_import_path=None).load_app()` (la funzione di `flask`, documentata) dal Python dell'ambiente ripristinato.

## Che cosa stampa lo script (misurato)

Un solo documento JSON, e nient'altro, sullo standard output: `{"called": true, "dispatch": null, "routes": [...]}`. Prima che giri il codice del progetto, lo script salva il descrittore 1 (a un numero da 100 in su, `fcntl.F_DUPFD_CLOEXEC`: i file che il progetto apre prendono i numeri bassi) e lo punta sullo standard error (`os.dup2`): ciò che il progetto stampa, o i suoi processi figli, o un `sys.stdout` sostituito, non arriva allo standard output; il documento va al descrittore salvato e lo script esce con `os._exit`, così un thread che non finisce, una funzione `atexit` o un buffer che non si svuota non lo tengono vivo né scrivono dopo. Un errore scrive `Tipo: messaggio` sullo standard error e esce con 3. Se il documento non si può scrivere (la pipe si è rotta, o il progetto ha chiuso o sostituito il descrittore salvato: lo script controlla che sia ancora quello, con `fstat`) esce con 4, nello stesso modo, senza lasciare che l'interprete esca da sé (traccia, `atexit`, thread): la sorgente lo dice con parole sue («could not write its answer»). Un progetto che chiude quel descrittore apposta è una lacuna (`results/closes-answer.json`: `OSError: descriptor 100 is not the one saved`).

Ogni regola è `{rule, methods, build_only, redirect_to, static, parts, arguments, handler}`; `handler` è `{kind, type, module, qualname, file, line, environment, distribution}` o nullo. `methods` sono quelli che la regola dichiara; `parts` e `arguments` servono allo schema (sotto); `type` è la classe dell'oggetto (dice che cos'è una vista senza nome né file); `line` è la riga del `def` della funzione; `environment` dice se il file sta nei pacchetti dell'interprete (`purelib` e `platlib` di `sysconfig`, `/daodan/state/venvs/lib/python3.12/site-packages`); `distribution` è la distribuzione che lo contiene, se `direct_url.json` (PEP 610, `importlib.metadata`) dice che è stata installata da una cartella locale. Un documento di tipo sbagliato in uno qualsiasi di questi valori è la lacuna della sua cartella (`_printed` controlla tutto ciò che `read` usa) e non un'eccezione che perde le righe delle altre.

| Regola della fixture | Che cosa dà Flask | Riga della sorgente |
| --- | --- | --- |
| `/` GET, `/items` POST, `/admin/stats` GET, `/admin/users/<int:user_id>` GET e POST | la funzione, `file` `wsgi.py` o `admin/blueprint.py`, `qualname` `index`, `user`... | una riga per metodo, sul `def` |
| `/wrapped` (`@app.get` sopra `@guarded`, che usa `functools.wraps`) | `inspect.unwrap` arriva a `wrapped` | la funzione decorata |
| `/unwrapped` (decoratore senza `wraps`) | la funzione che Flask esegue è `plain.<locals>.wrapper` | una riga su `plain.wrapper`: è ciò che Flask chiama; la funzione decorata non è raggiungibile |
| `/page` (`Pages().show`) | il metodo legato diventa la sua funzione: `qualname` `Pages.show` | una riga su `Pages.show` |
| `/nested/inner` (funzione dentro `make_blueprint`) | `qualname` `make_blueprint.<locals>.inner` | una riga con `handler` `inner` alla riga del suo `def`: il legatore dei collegamenti la lega alla sola funzione con quel nome che contiene la riga (`make_blueprint.inner`) |
| `/docs` (un metodo) e `/nested-doc` (funzione annidata e decorata) con una riga a colonna 0 in una stringa | `line` alla riga del `def` | una riga sul `def` (il parse della sola funzione, `dedent` e `ast.parse`, falliva e ricadeva sulla riga del decoratore: ora si fa il parse del modulo intero e si sceglie il `def` il cui primo decoratore o `def` è `co_firstlineno`) |
| `/lambda` | `qualname` `<lambda>`, `file` `wsgi.py` | una riga su `wsgi.py::<module>` con la lacuna del legatore («reports this entry without a unique snapshot handler»: lo snapshot la chiama `(lambda)`) |
| `/partial` (`functools.partial`) e `/callable` (oggetto con `__call__`) | `qualname` e `file` nulli, `type` `functools.partial` e `wsgi.Counter` | nessuna riga, una lacuna `outside_snapshot` che dice che cos'è |
| `/orders` (`MethodView`), `/hello` (`View`) | `kind` `class`, `qualname` `Orders` e `Hello`, `methods` quelli della regola | una riga per metodo su `wsgi.py::<module>` con la lacuna: quale metodo risponde a quale verbo non è letto |
| `/options` (`methods=["OPTIONS"]`), `/head-only` (`["HEAD"]`), `/get-options` (`["GET", "OPTIONS"]`) | `["OPTIONS"]`, `["HEAD"]`, `["GET", "OPTIONS"]` | una riga per metodo dichiarato, sul `def` |
| `/built` (`build_only=True`), `/old` (`redirect_to="/new"`) | nessuna vista, `build_only` e `redirect_to` veri | nessuna riga e nessuna lacuna: werkzeug non incontra mai la prima, la seconda risponde con un rinvio |
| `/static/<path:filename>` | la lambda `Flask.__init__.<locals>.<lambda>` in `.../site-packages/flask/app.py`, `environment` vero, `static` vero | nessuna riga e nessuna lacuna (sotto) |
| `/assets/files/<path:filename>` (un blueprint con `static_folder="files"`) | il `send_static_file` del blueprint, in `site-packages/flask/blueprints.py`, `environment` vero, `static` vero | nessuna riga e nessuna lacuna (sotto) |
| `/third-party` (`werkzeug.utils.redirect`) | `file` in `site-packages/werkzeug/utils.py`, `environment` vero | contata in una lacuna `model_partial` della cartella (sotto) |
| `/stdlib` (`json.dumps`) | `file` in `/usr/local/lib/python3.12/json/__init__.py`, `environment` falso | una lacuna `outside_snapshot` con la funzione e il file: fuori dallo snapshot e fuori dall'ambiente |

Lo snapshot (misurato in locale, lettura del testo con tree-sitter, nessun codice della fixture eseguito): il record di una funzione decorata sta sulla riga del `def`, non su quella del decoratore, mentre `co_firstlineno` di Python è quella del primo decoratore. Un metodo è `Classe.metodo` (`Pages.show`), una funzione annidata `esterna.interna`.

**I metodi** (`declared` nello script): Werkzeug aggiunge `HEAD` accanto a `GET` (`routing/rules.py:496`, «if "HEAD" not in methods and "GET" in methods»), Flask aggiunge `OPTIONS` e lo scrive sulla regola (`rule.provide_automatic_options`, `sansio/app.py:651`). Lo script toglie solo questi: `OPTIONS` se `provide_automatic_options`, `HEAD` se c'è `GET`; `methods=["OPTIONS"]` o `["HEAD"]` restano. Dai dati della regola non si distingue un `HEAD` dichiarato accanto a `GET`: si perde.

## Le viste dei pacchetti dell'ambiente (misurato)

Una vista il cui file sta nei pacchetti dell'ambiente ripristinato non è un file del progetto. Tre casi, per dato ufficiale:

- **Le regole `static` di Flask**: quella dell'applicazione la registra `Flask.__init__` quando `has_static_folder`, con endpoint `static` (il Quickstart lo documenta: `url_for('static', filename=...)`); quella di un blueprint con una cartella statica la registra `Blueprint.register` con endpoint `<blueprint>.static` e `send_static_file` del blueprint come vista (misurato: `flask/blueprints.py`). Lo script dice `static` di una regola quando `app.has_static_folder` e l'endpoint è `static`, o quando la sua vista è il `send_static_file` di un blueprint di `app.blueprints` con `has_static_folder`; con la vista nell'ambiente è silenziosa (prima la regola del blueprint finiva nel conteggio: una falsa lacuna `model_partial`). Se una cartella non ha altro, la sua lacuna lo dice («no rule of the project»): non resta vuota.
- **Una copia installata del progetto**: la distribuzione che contiene il file ha un `direct_url.json` (PEP 610) con `url` `file:///work/libs/shared` e `dir_info`: è codice del progetto copiato in `site-packages`, non il file dello snapshot. Lacuna `outside_snapshot` con la distribuzione e la cartella da cui è stata installata (`layouts/installed-copy`: `/shared` sì, `/own` è una riga). Un'installazione modificabile non cade qui (il file resta nella cartella del progetto).
- **Il resto** (le rotte di un'estensione, un decoratore senza `functools.wraps` di una libreria): una sola lacuna `model_partial` per cartella con il numero e i moduli («1 rule of the application is a view of packages of the restored environment, not of the project: /third-party (werkzeug)»).

## Lo schema del percorso, dai convertitori di Werkzeug (misurato)

Una riga offre una rotta ai collegamenti (`flows._declared_routes`) solo se ha `schema`, il percorso come lo legge `REST` (`/admin/users/{}`), e un metodo suo. Lo schema si fa dalle parti della regola che Werkzeug ha ricavato, mai dal testo di `rule`: lo script stampa `parts` (`[[false, "/"], [false, "admin"], [false, "/"], [true, "user_id"]]`, dopo il `|` che chiude la parte dell'host: gli argomenti dell'host non fanno buchi) e `arguments` (ogni argomento con il `part_isolating` del suo convertitore); la sorgente scrive un buco `{nome}` per ogni argomento con `part_isolating` vero e chiama `flows.path_schema` su quel percorso.

- **`part_isolating`** è l'attributo documentato di `BaseConverter` (Werkzeug 3.1.9, `routing/converters.py`: «`part_isolating` defaults to `False` if `regex` contains a `/`», versione 2.3); falso vuol dire che l'argomento può contenere una `/`, e lo legge il matcher (`routing/matcher.py`, `routing/rules.py`). `PathConverter` lo imposta falso; una classe che definisce la sua `regex` senza `part_isolating` ottiene `"/" not in regex` (`__init_subclass__`). Misurato: il percorso che il matcher accetta (`results/url-matching.json`) segue l'attributo in ogni caso provato.
- **Le strutture**: nessun attributo pubblico dà il convertitore di ogni argomento (`Rule.arguments` ha solo i nomi, `Rule.build` vuole un valore per ognuno ed esegue i `to_url` dei convertitori, `Rule.get_converter` costruisce un convertitore dai nomi). Lo script legge `Rule._trace` (`list[tuple[bool, str]]`, le parti: statica o dinamica e il testo) e `Rule._converters` (argomento, istanza), quello che l'analisi della regola di Werkzeug ha lasciato e che `Rule.build` e `__eq__` usano. Sono privati: se la versione installata non li ha, `parts` o `arguments` sono nulli e la riga non ha schema (nessuna ricostruzione dal testo). La versione letta e misurata è la 3.1.9 (con Flask 3.1.3); un'altra non è provata.

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

## Come non si carica (misurato)

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

Le varianti registrate (`tests/fixtures/premap/flask/`) sono quelle che i test leggono; le altre stanno solo in `results/`.

## Dopo il JSON (misurato, prima e dopo)

Con lo script che scriveva con `print` e usciva normalmente (`results/before-review/`): un thread non daemon che non finisce teneva vivo il processo fino a `timeout` (uscita 124 dopo 5,04 secondi con il JSON già stampato, e `read` scarta lo standard output di un'uscita diversa da 0); una funzione `atexit` che stampa lasciava `goodbye` come ultima riga (la sorgente leggeva l'ultima riga: nessun JSON); un `sys.stdout` sostituito lasciava lo standard output vuoto. Con il descrittore salvato e `os._exit` (`thread`, `atexit-print`, `replaced-stdout`): uscita 0 in 0,2-0,3 secondi, un solo documento, le stesse rotte; `read` non cerca più «l'ultima riga».

## `DispatcherMiddleware` (misurato)

Un `DispatcherMiddleware` (`werkzeug.middleware.dispatcher`, pubblico e documentato, con i suoi `app` e `mounts`; letto nel sorgente di Werkzeug 3.1.9 dentro il container, `results/werkzeug-source.json`) risponde a `/sub/hello` con l'applicazione montata a `/sub` e le dà il percorso dopo il prefisso (lo sposta in `SCRIPT_NAME`): misurato con il client di test, `/sub/hello` dà 200 e `/hello` 404 (`results/dispatcher-serves.json`). Quindi una regola `/hello` di un'applicazione montata a `/sub` si serve a `/sub/hello`. Il caricatore di Flask (`find_best_app`: `app` e `application` se sono `Flask`, poi l'unica istanza nel modulo) può scegliere proprio quell'applicazione montata, e le sue regole sono `/hello` e `static`, senza il prefisso (`results/before-review/dispatcher.json`).

Lo script non guarda i nomi: cerca i `DispatcherMiddleware` per la classe, su `app.wsgi_app` dell'applicazione caricata (il modo che la documentazione di Flask dà per avvolgerla: `app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {...})`) e fra le variabili globali del modulo che la contiene (quello che `Flask.import_name` nomina e ogni modulo che la tiene come variabile: `ScriptInfo` non espone il modulo che ha importato, solo `load_app`, `results/werkzeug-source.json`), apre i dispatcher uno dentro l'altro (`app` e `mounts`) e guarda dove sta l'applicazione caricata. Il campo `dispatch` del documento è nullo, o `{loaded, prefixes, mounts}`:

| Caso | `loaded` | Righe | Lacuna |
| --- | --- | --- | --- |
| nessun dispatcher (`app = Dash(...)` con `server = app.server`, `import app` con `server = app.app`: l'`app` non è Flask) | nullo | sì | nessuna (prima del cambiamento il nome `app` dava una falsa lacuna e perdeva ogni riga) |
| `application = DispatcherMiddleware(Flask("main"), {"/sub": sub})` con `sub` caricata, o la stessa con un altro nome (`server`) | `mounted`, `prefixes` `["/sub"]` | nessuna: le regole mancano del prefisso | `model_partial`: «the loaded application is mounted by a DispatcherMiddleware at /sub: its rules lack the prefix, so none is read», e le altre applicazioni Flask che serve |
| `application = DispatcherMiddleware(app, {"/sub": sub})`, o `app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/sub": sub})` | `main` | sì: le regole dell'applicazione principale sono servite come sono | `model_partial` che nomina le applicazioni montate con le loro regole come le serve (`/sub/hello`), non come righe |
| un dispatcher che non tiene l'applicazione caricata ma serve altre applicazioni Flask | `other` | nessuna: non si sa a che percorsi sia servita | `model_partial` |

Le righe delle applicazioni montate non si emettono: il percorso servito è `prefisso + regola` (misurato), ma la funzione di una vista montata e il suo snapshot non sono quelli dell'applicazione caricata, e nessuna prova li lega. Un avvolgimento che non è un `DispatcherMiddleware` (un middleware proprio che sposta i percorsi, un'applicazione WSGI che ne contiene un'altra) non si vede: dichiarato, non corretto.

## Il Python del comando (misurato)

`preparation.restores` fa un ambiente per la radice, per ogni cartella con un lockfile suo e per le cartelle marcate che nessun'altra cartella marcata contiene; l'ambiente di Poetry sta nella cache di Poetry. La prima versione della sorgente usava sempre `<venvs>/<cartella che dichiara Flask>/bin/python` (`results/before-review/`): per un membro di un workspace uv, per un progetto Poetry e per un `api/requirements.txt` sotto un `pyproject.toml` alla radice ogni comando usciva con 127, `timeout: failed to run command '/daodan/state/venvs/api/bin/python': No such file or directory` (per Poetry `.../venvs/./bin/python`), senza dire perché. Ora la sorgente chiede a `preparation.python_environment` (lo stesso codice del passo dinamico dei test Python, `dynamic/python.py`) la cartella più vicina, in alto, che il ripristino rende un ambiente, e a `preparation.python_interpreter` la parola della shell del suo Python (`poetry env info -e` per Poetry); il `cwd` resta la cartella che dichiara Flask; i lockfile sono quelli del checkout (`context.root`), come per la sorgente `uv`.

| Layout | Cartella che dichiara Flask, ambiente | Uscita | Risultato |
| --- | --- | --- | --- |
| `uv-workspace` | `api`, la radice (`uv sync --all-packages`: le dipendenze dei membri sono nell'ambiente della radice) | 0 in 0,53 s, 53 MB | `/hello` e `static`, la riga su `api/wsgi.py` |
| `poetry` | la radice, Poetry (`"$(cd /work/. && poetry env info -e)"`) | 0 in 1,73 s, 88 MB | `/hello` e `static`; Flask è dichiarato solo in `pyproject.toml` (la sorgente `requirements` non lo legge: lo dice il grafo dei moduli) |
| `root-and-sub` | `api`, la radice (`pip`: installa le dipendenze di `pyproject.toml`, non `api/requirements.txt`) | 3 in 0,15 s | `ModuleNotFoundError: No module named 'flask'`; la lacuna lo dice con l'ambiente («the Python of the environment restored for '.'»). Da T1.B.9d `api/requirements.txt` ha il suo ambiente (`preparation.RESTORES["pip"]["alone"]`): misura da rifare |
| `installed-copy` | la radice | 0 in 0,64 s | `/own` è una riga, `/shared` una lacuna: copia installata del progetto |

Il progetto sta in `/work` anche nella prova (il ripristino e il comando si fanno lì: l'ambiente di Poetry è chiave del percorso).

## Il ripristino del runner: una causa trovata e corretta

La prima esecuzione, con il setup del runner com'era, finì con l'uscita 127 per ogni comando sotto `timeout` (lo script e `flask routes`): `timeout: failed to run command '/daodan/state/venvs/./bin/python': No such file or directory` (`results/before-the-fix/`, registrata come `tests/fixtures/premap/flask/no-environment.json`; la sonda non può più riprodurla, il ripristino è corretto). Il setup usciva con 0 (la riga di ripristino finisce con `true`) e scriveva `DAODAN-RESTORE-FAILED pip .` con `failed to create directory /daodan/state/venvs/.: No such file or directory`.
`--mode venv-dir` (uv 0.11.28, `results/venv-dir.json`) dice perché: `uv venv <madre>/.` fallisce quando `<madre>` non esiste (anche `/a/k/x/.` con `/a/k` presente), mentre `uv venv /a/d/x` e `/a/h/i/g` creano le cartelle madri; con la cartella già presente `uv venv /a/c/.` riesce. Il setup del runner crea `tools/bin` e `home`, non `venvs`: la sola cartella radice (`$f` uguale a `.`, l'ambiente è `venvs/.`) falliva, le altre no.
Correzione: `container_runner._python` fa precedere le righe di ripristino da `mkdir -p <venvs>`. Dopo la correzione, setup con uscita 0, 1-2 secondi in tutto (spacchettamento di `uv`, ambiente e installazione di Flask), nessun testo sullo standard error.
Un ambiente della cartella radice è la cartella `venvs` stessa: `venvs/api` ci sta dentro se viene dopo (`/m/.` poi `/m/api`: riesce), mentre l'ordine inverso fallisce (`/n/api` poi `/n/.`: «A directory already exists»). `preparation.restores` ordina per profondità e poi per nome: la radice va per prima.

## Tempo e memoria (misurati)

| Caso | Tempo | Picco |
| --- | --- | --- |
| lo script sulla fixture (37 regole), varianti che caricano | 0,2-0,7 s | 48-54 MB |
| 3000 regole, 6000 metodi (1.207.317 caratteri di JSON) | 1,25 s | 76 MB |
| un progetto Poetry (con `poetry env info -e`) | 1,73 s | 88 MB |
| `flask routes` | 0,6-0,7 s | 53 MB |
| tutto il setup (spacchettamento di `uv`, `uv venv` e `uv pip install` di Flask, rete aperta) | 1-2 s | non misurato |

La memoria è la massima dei processi figli del comando (`ru_maxrss`, `timeout` compreso): lo script è piccolo, il peso vero è quello dei moduli del progetto, non provato su un'applicazione grande. `TOOLS["flask"]` tiene `memory: 3` (GB) dei tool Node: nessuna misura lo cambia. Nella cartella del progetto (la copia del container) restano `__pycache__/*.pyc` accanto ai moduli importati; nessun file esistente cambia.

## L'ambiente (misurato)

Il Python dell'ambiente di Flask nella prova è quello che Modal installa in `/usr/local/bin`: CPython 3.12.1 (Clang 17.0.6), `base_prefix` `/usr/local`, e prima di `/usr/bin` in `preparation.PATH`, per cui è il `python3` che `uv venv --python python3` sceglie; ambiente in `/daodan/state/venvs`, pacchetti Flask 3.1.3, Werkzeug 3.1.9, Jinja2 3.1.6, MarkupSafe 3.0.4, blinker 1.9.0, click 8.5.1, itsdangerous 2.2.0; `purelib` e `platlib` di `sysconfig` sono `/daodan/state/venvs/lib/python3.12/site-packages` (`preparation.VENVS`), la libreria standard `/usr/local/lib/python3.12`. Nel container di Daodan (`buildpack-deps:noble`) sarebbe quello dei pacchetti dell'immagine: non provato qui.

## Il collegamento (fatto il 23 novembre 2026, tolto il 24 novembre 2026)

**Tolto il 24 novembre 2026**: dopo «Applicazioni vere» la sorgente non aggiunge a Noir quanto costa, e `flask_app` non è più in `premap.SOURCES` né in `FRAMEWORK_SOURCES`, né l'import in `premap/__init__.py`, né la tabella `flask` in `entry-queries.json`. Restano: `premap/flask_app.py` e `flask_routes.py`, la voce `flask` di `container_runner.TOOLS` (com'era prima del collegamento), i miglioramenti condivisi (`preparation.python_environments`, `python_interpreter`, `perimeter_files` e il passo dinamico che li usa, `frameworks.stopped`, `mkdir -p <venvs>` in `_python`) e i test della sorgente, che le danno la tabella e il posto fra le sorgenti di framework (`wired` in `tests/test_codebase_map_premap_flask.py`, il contesto di `links` in `tests/test_codebase_map_flows_flask_routes.py`, come per Django e FastAPI): la sorgente non cade all'importazione e quanto è misurato resta provato. Per ricollegarla: le tre righe di `premap/__init__.py`, `{"flask": {"route": {"kind": "rotta"}}}` in `entry-queries.json`, e le righe `flask` dei test che elencano le sorgenti (`tests/test_codebase_map_premap.py`, `..._premap_container_runner.py`). Quel che segue è com'era collegata.

Le righe delle funzioni sono «un nome in una posizione» (`handler` e `site` `file:riga`), la forma che il legatore (`binder.bind`, spec 8.13 punto 2) lega alla funzione: la sorgente non apre lo store dello snapshot (un test lo impone a ogni sorgente di `FRAMEWORK_SOURCES`). `flask_app` è nell'elenco `from premap import (...)`, in `SOURCES` fra `sveltekit` e `angular` e in `FRAMEWORK_SOURCES`; la tabella `flask` è in `daodan/data/entry-queries.json` (`{"route": {"kind": "rotta"}}`, letta da `read` come le altre sorgenti). Effetti, provati in `tests/test_codebase_map_flows_flask_routes.py`: `flow_entries.evidence` legge le righe e le lacune; la chiave dei collegamenti in cache dipende da `flask_app.py` (`flows._links_reader_digest`); una rotta Flask è una rotta offerta come quelle di Noir e Next.js (servizio `*`, `flows._declared_routes`: ha `schema` e un metodo suo); una rotta di Noir sulla stessa funzione, con lo stesso metodo e lo stesso `schema`, è la stessa voce; una chiamata a `/admin/users/7` incontra la rotta `<int:user_id>`; una rotta con un convertitore che può contenere `/` ha `schema` nullo, una lacuna dei collegamenti per metodo (`declared route GET /files/<path:name>: the tool's path is no single path schema...`, con il sito della funzione) e nessun incontro. Le righe non portano `host`: nulla nei collegamenti lo legge.

## Applicazioni vere

Domanda (del coordinatore, 24 novembre 2026): sulle applicazioni vere, gli oggetti di Flask (`url_map`, `view_functions`) danno rotte che il Noir fissato (1.5.0, `premap/noir.py`) non dà? A Spring, su tre applicazioni vere, Noir dava le stesse rotte con lo stesso file e la stessa riga del gestore (337 su 337) e la sorgente non fu scritta; per FastAPI il framework non dava nessuna rotta con funzione del progetto che Noir non desse. Qui: il fixture e quattro applicazioni Flask pubbliche con licenza permissiva, ognuna a un commit fissato e scaricata durante la costruzione dell'immagine (`apps.py`: nulla del loro codice è nel repository, restano i conteggi e le risposte in `results/real/`). Le tre scelte per le forme che un lettore statico può sbagliare sono CTFd, Redash e shhh; **microblog-api è una quarta, aggiunta** perché nessuna delle tre ha un `url_prefix` dato a `register_blueprint`, una delle forme da mettere alla prova.
Su Modal, rete bloccata nelle esecuzioni (`modal_real.py`); il ripristino è quello del runner (`plan.py` sui nomi dei file: `uv sync --locked --all-packages` per un `uv.lock`, `uv pip install -r requirements.txt` per un `requirements.txt`; per l'immagine la rete è aperta), poi la riscrittura dei `.env` di `container.named`, poi `noir scan /work -f json --no-log` o il comando di `flask_app.commands`. Il confronto passa per il codice di Daodan: `premap.write` con le risposte registrate (`noir.read`, `flask_app.read`), poi il legatore (`binder.bind`) sullo snapshot dei sorgenti (testo, mai eseguito qui). Chiave di una rotta: metodo e `flows.path_schema` del percorso come lo scrive ogni strumento (`/api/v1/challenges/<challenge_id>` e Noir hanno lo stesso schema). «Legata» vuol dire: una funzione unica dello snapshot, con file e riga. I conteggi di Noir sono dei suoi endpoint di file `.py` (il front end e i file di configurazione dello stesso repository non sono Flask). Il codice dei progetti è girato solo nei container; sull'host sono girati `plan.py` e `real_summary.py` (codice di Daodan, che legge i sorgenti come testo).

| | CTFd | Redash | shhh | microblog-api |
| --- | --- | --- | --- | --- |
| repository | `CTFd/CTFd` | `getredash/redash` | `smallwat3r/shhh` | `miguelgrinberg/microblog-api` |
| commit | `f9fa28b2f17b` | `f561a53dc55e` | `448acf4bed05` | `e250d7115b47` |
| licenza (SPDX di GitHub, file `LICENSE`) | Apache-2.0 | BSD-2-Clause | MIT | MIT |
| file, di cui `.py` | 1.051, 357 | 1.976, 309 | 66, 28 | 50, 30 |
| Flask, Werkzeug, Python | 2.2.5, 2.2.3, 3.11.15 (`uv` lo scarica: `requires-python = ">=3.11,<3.12"`) | 3.1.3, 3.1.8, 3.13.14 (scaricato) | 3.1.3, 3.1.9, 3.12.1 (quello di Modal) | 3.0.3, 3.0.3, 3.12.1 |
| ripristino | `uv sync --locked`, 9 s, 93 pacchetti | `uv sync --locked`: **fallisce**, 7 s (vedi sotto); con `--frozen` 10 s, 103 pacchetti | `uv pip install -r requirements.txt`, 3 s, 37 pacchetti | idem, 2 s, 35 pacchetti |

**Dove le forme che un lettore statico può sbagliare sono, riga per riga** (nei sorgenti ai commit sopra):

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

**Come girano, nelle condizioni di Daodan** (la riga `script`, `container.named` prima; Noir su `/work`):

| | CTFd | Redash | shhh | microblog-api |
| --- | --- | --- | --- | --- |
| script del framework, come lo lancia il runner | **carica**, 5,97 s, 291 MB | **non carica**, uscita 3, 0,35 s: `ModuleNotFoundError: No module named 'flask'` (il ripristino è fallito: `error: The lockfile at uv.lock needs to be updated, but --locked was provided`, nessun ambiente) | **non carica**, uscita 3, 3,0 s: `RuntimeError: env=None specified in FLASK_ENV is not supported` (`wsgi.py` fa `create_app(os.environ.get("FLASK_ENV"))`) | **carica**, 2,46 s, 152 MB (`FLASK_APP` da `.flaskenv`; `python-dotenv` è fra i pacchetti) |
| con quel che manca messo (una variante per passo) | | `--frozen`: `NoAppException: Could not locate a Flask application` (nessun `wsgi.py` né `app.py` alla radice: l'applicazione è `redash/wsgi.py`); con `FLASK_APP=redash.wsgi`: `Exception: You must set the REDASH_COOKIE_SECRET` (alle impostazioni); con un segreto: `ConnectionError: Error 111 connecting to localhost:6379` (`create_app` chiede la versione di Redis); **con un Redis sul loopback** (`redis-server` di apt, nell'immagine): carica, 4,32 s, 234 MB, 100 regole. PostgreSQL non serve per caricare | con `FLASK_ENV=testing` (SQLite in memoria): carica, 3,26 s, 102 MB, 6 regole | |
| Noir (1.5.0) | 253 endpoint (251 http, 2 cli), 1,91 s, 171 MB | 318 (311 http, 7 cli), 2,81 s, 250 MB | 6, 0,92 s, 148 MB | 28, 0,67 s, 149 MB |
| lasciato nel progetto dallo script | `.ctfd_secret_key` e `.data/filesystem_cache/` (3 file) | niente | 4 file compilati in `shhh/static/dist/` | niente |

Su quattro applicazioni vere, **due caricano come Daodan le lancia** (CTFd, microblog-api); shhh carica con una variabile che il suo `wsgi.py` legge da sé; Redash chiede quattro cose (un lockfile in regola, `FLASK_APP`, un segreto e un Redis). Senza il loro aiuto resta Noir, che gira su tutte e quattro in meno di 3 s senza preparazione. Il ripristino fallito di Redash è un fatto del suo repository (il `uv.lock` ha il pacchetto `redash` alla versione `26.10.0.dev0` e il `pyproject.toml` a `26.11.0-dev`: la versione del progetto è stata alzata senza rifare il lock, mentre `requires-dist`, i gruppi e `requires-python` sono uguali, letti come testo) e della riga `--locked` di Daodan (`preparation.RESTORES`, riga 380, un file condiviso: non toccato): il setup lo scrive (`DAODAN-RESTORE-FAILED uv .`, con il messaggio) e la sorgente dà una lacuna `model_failed` senza rotte. Il Python 3.11 e 3.13 che CTFd e Redash chiedono arrivano da `uv` (rete aperta nella costruzione); Werkzeug 2.2.3, 3.0.3, 3.1.8 e 3.1.9 hanno tutti le due strutture private di cui la sorgente fa lo schema (`parts` e `arguments` non sono mai `None`); lo schema è `None` solo per un argomento che può contenere una `/` (9 regole su 174 in CTFd).

**Il confronto** (Flask: l'esecuzione che carica, con quel che manca per Redash e shhh; la riga «Flask» conta le rotte, una per regola e metodo, senza le regole `static`):

| | CTFd | Redash | shhh | microblog-api |
| --- | --- | --- | --- | --- |
| regole di Flask / rotte | 174 (172 non statiche) / 254 | 100 (99) / 157 | 6 (5) / 6 | 31 (30) / 30 |
| righe della sorgente | 252 | 157 | 6 | 28 |
| di cui legate a una funzione | 98 | 34 | 4 | 28 |
| di cui la lacuna della classe | 154 (61 %) | 123 (78 %) | 2 | 0 |
| viste di un pacchetto (una lacuna `model_partial`, nessuna riga) | 2 (`flask_restx`) | 0 | 0 | 2 (`apifairy`) |
| endpoint di Noir, di file `.py` | 249 | 160 | 6 | 28 |
| legati prima della correzione del legatore (il nome di Noir contro `name`) | 94 | 37 | 4 | 28 |
| legati dopo (`name` o `qualified_name`, alla riga della riga) | **249** | **160** | **6** | 28 |
| rotte che entrambi danno (metodo e schema) | 248 | 157 | 6 | 28 |
| ... di cui stessa funzione, stesso file e riga | 94 | 34 | 4 | 28 |
| ... di cui la sorgente dà la classe, Noir il metodo (file e riga) | 154 | 123 | 2 | 0 |
| ... stessa funzione sotto un altro percorso | 0 | 0 | 0 | 0 |
| **solo Flask** | **6**: 3 plugin (`add_url_rule`), 1 copia di una regola (`themes_beta`, `CTFd/views.py:548`, stesso metodo e percorso di `themes`, `:526`), 2 viste di RESTX | **0** | **0** | **2**: le viste di APIFairy, senza funzione del progetto |
| **solo Noir** | **1**: `HEAD /api/v1/notifications` (una `def head` che la sorgente toglie, `declared()` toglie `HEAD` con `GET`) | **3**: `/oidc`, `/<org_slug>/oidc`, `/oidc/callback` (il blueprint di `create_oidc_blueprint` esiste solo con `OIDC_ENABLED`: Noir dà il codice di un profilo spento) | **0** | **0** |

**Il legatore, prima e dopo** (24 novembre 2026): `binder._position` legava un endpoint di Noir se il suo `handler` era uguale al `name` della dichiarazione dello snapshot alla riga data; Noir scrive un metodo `Classe.metodo` (`Api.get`), la dichiarazione ha `name` `get` e `qualified_name` `Api.get`. Ora il confronto è con l'uno o l'altro. Misurato sulle risposte registrate di Noir e sugli snapshot costruiti con il codice di Daodan, senza rifare Modal (`real_summary.py`, `noir_report` di `results/real/<caso>-summary.json`; «prima» è la riga di allora, rifatta nello script):

| Endpoint di Noir di file `.py` | CTFd | Redash | shhh | microblog-api | fixture |
| --- | --- | --- | --- | --- | --- |
| totale | 249 | 160 | 6 | 28 | 40 |
| con il nome qualificato (`Classe.metodo`) | 155 | 123 | 2 | 0 | 3 |
| legati a una funzione unica, prima | 94 | 37 | 4 | 28 | 28 |
| legati, dopo (`name` o `qualified_name`) | **249** | **160** | **6** | **28** | **31** |
| legati con il solo nome del metodo (`get`) | 249 | 160 | 6 | 28 | 31 |
| non legati, dopo | 0 | 0 | 0 | 0 | 9 |
| legati dal solo nome e non dal nome qualificato | 0 | 0 | 0 | 0 | 0 |

Il nome qualificato lega **tutti** gli endpoint che il nome del solo metodo lega, e nessuno in meno: dove il metodo è ereditato (`QueryListResource` e `QueryArchiveResource` di Redash non hanno `get`, Noir cita `BaseQueryListResource.get` alla riga 132 della classe base) il nome qualificato dà la dichiarazione della classe base, una sola, e la stessa del nome del solo metodo. Un caso in cui il nome di Noir e il `qualified_name` dello snapshot differiscano (una classe annidata, `Esterna.Interna.metodo`) non c'è fra le quattro applicazioni: non misurato; ogni endpoint che ha un nome è legato. I 9 non legati sono del fixture, e hanno tutti `handler` nullo nella risposta di Noir (nessun nome da cercare alla riga): `/page` e `/docs` (un metodo legato: `Pages().show`, `Docs().page`), `/lambda` (una `(lambda)` copre la riga 78, ma Noir non la nomina), `/partial`, `/callable`, `/stdlib`, `/third-party` (nessuna `def` del progetto), `/built` e `/old` (una regola `build_only` e una che reindirizza: nessuna funzione). Il dato che li distingue sta nella risposta di Noir e non c'è: il nome. Con la correzione la comparazione «com'è» coincide con quella «con il solo nome del metodo» in tutti i casi (stesse cifre per «stessa funzione», «solo Flask», «solo Noir»).

Fixture, stessa misura (`results/real/fixture-summary.json`): 38 rotte per metodo in comune, 27 con la stessa funzione; Flask dà la funzione dove Noir no per 2 (`/page` e `/docs`, un metodo legato); la funzione è diversa per 1 (`/unwrapped`, un decoratore senza `functools.wraps`: Flask dà `plain.wrapper`, ciò che esegue; Noir la funzione decorata, che per chi cerca il gestore è la più utile); nessuno dei due dà una funzione per 8 (`/lambda`, `/partial`, `/callable`, `/stdlib`, `/third-party`, e i tre metodi delle viste a classe); solo Noir ha `/built` e `/old` (una regola `build_only` e una che reindirizza, che Flask non serve).

**Verdetto: no, la sorgente di Flask non aggiunge a Noir quanto costa; il verdetto è lo stesso in tre stati.**

1. **Prima della correzione del legatore** (misurato per primo). Delle 443 righe della sorgente 164 hanno una funzione, e Noir dà la stessa funzione, con lo stesso file e la stessa riga, su 160; la sorgente ne ha in più 4, tutte di CTFd (3 asset dei plugin, una regola copiata). Per le altre 279 rotte, i metodi delle classi (il 63 % delle righe: CTFd 154, Redash 123, shhh 2), nessuno dei due dava una funzione: la sorgente una lacuna della classe, Noir un endpoint che il legatore non legava. Solo Flask: 8 rotte su 447 (4 con funzione del progetto, 4 viste di estensioni senza); solo Noir: 4 (una `def head` e tre di un profilo spento). Il costo: un ambiente da ripristinare (2-10 s, e con un Python scaricato), il codice del progetto eseguito, e **su 2 applicazioni su 4 la sorgente non dà nulla come Daodan la lancia** (shhh: `FLASK_ENV`; Redash: lockfile, punto d'ingresso, segreto e Redis); Noir ha 4 su 4.
2. **Oggi, con il legatore corretto** (`name` o `qualified_name`, tabella sopra): Noir dà una funzione per tutte le 279 rotte, con la stessa classe e lo stesso file che la lacuna della sorgente nomina per 277 su 279 (le altre 2, `QueryArchiveResource` e `QueryListResource` di Redash, ereditano `get` da `BaseQueryListResource`, `redash/handlers/queries.py:132`: Noir dà la definizione, che è la funzione che gira). Noir è avanti di 279, la sorgente di 4 su 447.
3. **Con la sorgente che risolve le classi** (`view_class` lo dice, e per una `MethodView` o una `Resource` il metodo che risponde a un verbo è `getattr(view_class, verbo.lower())`; non scritto, non provato): le 279 pareggiano e la sorgente resta a +4 rotte con funzione (e 4 viste di estensioni senza) su 447, contro le 4 solo di Noir: meno dell'1 % per un ambiente da ripristinare e il codice del progetto eseguito.

Dove la sorgente vale qualcosa è dove un lettore statico sbaglia di proposito: sul fixture, scritto per rompere (2 gestori che Noir non lega, un metodo legato), e su CTFd per le 3 regole dei plugin (`add_url_rule` con un percorso composto in una funzione chiamata per cartella). Sul codice che le applicazioni vere scrivono (blueprint con prefisso dato alla registrazione o alla creazione, blueprint annidati, factory, Flask-RESTX e Flask-RESTful, `MethodView`, decoratori) Noir ha gli stessi percorsi, gli stessi metodi e la stessa funzione.

**Trovato a parte** (il codice non è di questa cartella; ognuno cambia un numero sopra; il primo è corretto, gli altri no):

- `noir.rows` dà al legatore il nome che Noir scrive per un metodo (`Api.get`, `ChallengeList.get`: 155 su 249 endpoint di CTFd, 123 su 160 di Redash, 2 su 6 di shhh, 3 su 40 del fixture), e `binder._position` lo confrontava con il nome della funzione dello snapshot (`get`): «without a unique snapshot handler at its site» per ogni metodo di una classe. **Corretto il 24 novembre 2026** nel legatore (`name` o `qualified_name` della dichiarazione, alla riga della riga; `noir.rows` non è cambiato): la tabella «Il legatore, prima e dopo».
- `flask_routes.declared()` toglie `HEAD` con `GET` anche quando la classe lo dichiara (`def head`, `CTFd/api/v1/notifications.py:104`): una rotta su 447, quella che Noir dà e la sorgente no; Werkzeug aggiunge `HEAD` a ogni regola con `GET` e la regola non dice chi l'ha messo (il dato c'è: `view_class.methods` di una `MethodView` elenca i verbi definiti). Non corretto: cambia lo script, quindi `VERSION` e tutte le risposte registrate da rifare su Modal, per una sorgente che non è più collegata.
- `preparation.RESTORES` (riga 380, un file condiviso, come per Maven): `uv sync --locked` non dà un ambiente a Redash per la sola versione del progetto non rifatta nel lock; con `--frozen` il ripristino riesce (10 s, 103 pacchetti).
- La lacuna della classe della sorgente è la parte dominante delle sue righe sulle applicazioni vere (63 %), non un caso di bordo.

**Aperto, non misurato**: `url_prefix` letto dalla configurazione, `add_url_rule` in un ciclo, Flask-Admin e flask-smorest (le quattro applicazioni non li hanno); altre applicazioni (le quattro sono state scelte, non campionate); la regola copiata di CTFd (quale delle due risponde); il Docker di Daodan (la prova gira nell'immagine del runner su Modal); `FLASK_APP` o `.flaskenv` per Redash non esistono: chi avvia Redash con `flask --app redash.wsgi` lo sa e Daodan no. I `results/real/<nome>-plan.json` sono l'uscita di `plan.py` per la cartella (`modal_real.py` la tiene in `DAODAN_FLASK_APPS/<nome>-plan.json`, per nome e non per commit: si cancella per rifarla, e la riscrive in `results/real/` a ogni esecuzione).

## Limiti dichiarati e non corretti

- **Un pacchetto costruito su Flask** (Dash, Flask-RESTX) dichiarato al posto di `flask` non fa di una cartella una cartella Flask: la sorgente parte dai pacchetti dichiarati (`flask`) e non da quelli risolti. Il dato ufficiale c'è, il lockfile (`uv.lock`, `poetry.lock`) elenca i pacchetti risolti, ma la pre-mappa non ne legge nessuno per i pacchetti Python: `premap/uv.py` esporta il lock di uv in `pylock.toml` (`uv export --frozen`, con `tomllib`) e ne tiene solo i pacchetti locali, e quello di Poetry non è letto; nessun lettore nuovo è stato aggiunto. Quando un lettore dirà i pacchetti di un lock, una cartella il cui lock ha `flask` e il manifesto no è una cartella Flask.
- **I lockfile ignorati da git**: il container riceve il perimetro del progetto (i file non tracciati che git ignora non ci sono) e ripristina da quello; il comando sceglie il Python dallo stesso insieme di file (`preparation.perimeter_files`, in un posto solo). Prima il comando guardava `(context.root / lock).is_file()` e il ripristino il perimetro: con un lockfile ignorato i due sceglievano gestori diversi e falliva il comando. Lo stesso modo di guardare è in `premap/uv.py` (`(context.root / f / "uv.lock").is_file()`, riga 45) e nel passo dinamico dei test Python (`read(lock)`): segnalato, non cambiato.

- **Una chiamata a `/loose/` incontra la rotta `/loose`**, mentre Werkzeug risponde «non trovato» (`results/url-matching.json`): `flows._rest_meet` toglie la barra finale. Lo schema non distingue `/strict/` da `/strict`.
- **I convertitori tipati sono tutti un buco**: `int`, `uuid`, `any(a,b)` diventano `{}`. Con il servizio `*`, una rotta `/<any(about,help):page>` può incontrare una qualsiasi chiamata di un segmento che non abbia una rotta letterale (letto nel codice, non provato).
- **Due parametri in un segmento** (`/<a>-<b>`) hanno schema `/{}-{}` che nessuna chiamata incontra (provato).
- **Host e sottodominio non separano le rotte**: lo schema è del solo percorso, e il campo non c'è più sulle righe; due rotte uguali su host diversi sono due voci con lo stesso schema (letto nel codice).
- **`.env` è riscritto dal container** (`container.named`: ogni `.env` e `.env.*` dà un segnaposto al posto del valore, nella copia), **`.flaskenv` no**: un progetto che mette `FLASK_APP` in `.flaskenv` ne ha il valore vero (e senza `python-dotenv` Flask lo ignora); uno che lo mette in `.env` ha un segnaposto (letto nel codice, non provato).
- **Uscita grande**: 3000 regole sono 1,2 MB di JSON; `container.run_commands` legge ogni flusso intero (il tetto di 1 GiB, `OUTPUT_CAP`, è delle uscite dichiarate): non provato con il motore.
- **Ordine del ripristino**: una cartella di profondità 0 con un lockfile suo il cui nome si ordina prima di `.` (per esempio `-api`) sarebbe ripristinata prima della radice e la radice fallirebbe («A directory already exists», misurato nell'ordine inverso); una sottocartella che si chiama `bin`, `lib` o `include` finisce dentro l'ambiente della radice, che ha quelle cartelle (letto nel codice, non provato).
- **Il Docker di Daodan** (`buildpack-deps:noble`, il proxy dei registri): la prova gira su Modal, nella stessa immagine, con il setup eseguito con la rete aperta e il comando con la rete bloccata.
- **Non provati**: `uv.lock` con un progetto che non è un workspace, Poetry con più cartelle, una cartella con il solo `pyproject.toml` senza `requirements.txt` per il `pip`; `async def`, più applicazioni nello stesso progetto, rotte aggiunte dopo l'avvio; la vista a classe dà una riga con la lacuna del metodo (quale metodo di una `MethodView` risponde a quale verbo non è letto); una rotta di Noir sulla stessa funzione di una rotta `<path:...>` non si fonde (la chiave di Flask è il testo della regola) e offre il suo schema (letto nel codice, non provato).
