# Flask: `ScriptInfo.load_app`, `app.url_map` e `app.view_functions`

Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14c. **Stato: scritto il 23 novembre 2026, mai eseguito** (nessuna credenziale Modal dove è stato scritto). Nessun numero di questa cartella è misurato.

## Letto dal sorgente di Flask 3.1.3 (wheel scaricato, non eseguito)

- `flask routes` **è un comando ufficiale** (`flask/cli.py`, `routes_command`): stampa una tabella di testo `Endpoint  Methods  Rule` (più `Host` o `Subdomain` se ci sono), senza funzione, file, riga né JSON. Per questo non si usa: la sorgente chiama `app.url_map.iter_rules()` e `app.view_functions`, come il comando.
- Il caricamento è `flask.cli.ScriptInfo(app_import_path=None).load_app()` (documentato): `wsgi.py`, poi `app.py`; nel modulo `app`, `application`, l'unica istanza di `Flask`, poi la factory `create_app` o `make_app`. `FLASK_APP` è la variabile di `--app`; `flask.cli.load_dotenv()` carica `.flaskenv` e `.env` come il comando.
- Il comando nasconde `HEAD` e `OPTIONS` (`--all-methods` li mostra): lo script fa lo stesso.

## Da misurare con `modal_probe.py` (9 varianti, rete bloccata)

Che cosa stampa lo script sulla fixture e se `inspect.unwrap` e `getsourcefile` danno per ogni gestore il file e il nome giusti (metodo legato, lambda, `functools.wraps`); se la riga del record dello snapshot di una funzione decorata sta sul `def` o sul decoratore, e se il nome di un metodo è `Classe.metodo`; cosa dice `flask routes` (stessa tabella?); la causa che Flask scrive senza `wsgi.py`, con un modulo che solleva, con un pacchetto mancante; `FLASK_APP`; tempo, memoria e file lasciati nel progetto; l'ambiente ripristinato da `restores: "python"` del runner (`container_runner._python`).

Non provati e non scritti come fatto: una factory con argomenti, `view_class` (una riga sulla classe con la lacuna del metodo), più applicazioni nello stesso modulo, Poetry, `uv sync` con un workspace.
