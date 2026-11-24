# Django: il URLconf caricato (`get_resolver()` dentro `manage.py shell -c`)

**Stato:** Provato, non nel prodotto. La sorgente [`daodan/core/premap/django_app.py`](../../daodan/core/premap/django_app.py) con lo script `django_routes.py` è scritta e ha i suoi test (`tests/test_codebase_map_premap_django.py`, `tests/test_codebase_map_flows_django_routes.py`), ma non è in `premap.SOURCES` né in `FRAMEWORK_SOURCES`, non ha una voce in `container_runner.TOOLS` né una tabella in `entry-queries.json`: i test le iniettano. Motivo: sulle applicazioni vere non aggiunge a Noir quanto costa («Applicazioni vere»). Nel prodotto le rotte di Django sono quelle di Noir.

## Domanda

Che cosa dà Django, caricato nel container senza rete, per ogni rotta (metodo, percorso, vista con file e riga), come la sorgente lo lega alle funzioni dello snapshot, e se aggiunge abbastanza a Noir da essere collegata. Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14b del piano).

## Strumento ufficiale provato

Django 6.1.3, 5.2.19 e 4.2.30 (Python 3.12.1 di Modal), DRF la più recente alla data; misurato su Modal il 24 novembre 2026, immagine del runner, rete bloccata. Nessun comando di `django-admin` elenca gli URL (`show_urls` è di django-extensions, terzi, non valutato).

| Dato | Che cosa dà | Uso |
| --- | --- | --- |
| `django.urls.get_resolver()` e `URLResolver.url_patterns` | l'albero: `URLResolver` (`include()`, `admin.site.urls`, `i18n_patterns`) e `URLPattern` (`callback`, `name`, `pattern`) | **usato**: la ricorsione di `django_routes.walk` |
| `URLPattern.lookup_str` | il nome puntato della vista (`functools.partial.func`, `view_class`) | la regola che Django applica per sapere che cosa è la vista, ripresa in `function` |
| `django.contrib.admindocs.views.extract_views_from_urlpatterns` | la ricorsione di Django per `admindocs`: `(callback, str(pattern) unito, namespace, name)`; **si importa anche con l'admin fuori da `INSTALLED_APPS`** (31 viste sulla fixture senza admin, 60 con; `results/dump-no-admin.json`) | valutata e non usata: non dà i convertitori dei livelli (nessuno schema), non dice la classe del pattern (`re_path`, `i18n_patterns`) e salta in silenzio un `ImportError` |
| `URLResolver.reverse_dict` | le stesse forme di `normalize`, chiavi per `callback` e per nome | valutato e non usato: non è per rotta |
| `django.utils.regex_helper.normalize` | la forma con un buco per ogni argomento (`shop/products/%(pk)s/`) del regex compilato, la funzione che usa `reverse()` | **usato** per le parti del percorso (sotto) |
| `RoutePattern.converters` | `{argomento: convertitore}` di ogni livello | **usato** per gli argomenti |

**Le impostazioni** sono quelle che il `manage.py` del progetto imposta: la sorgente non lo legge, lo esegue con il comando documentato `shell -c`. Tre modi confrontati, 26 varianti ciascuno (`results/launch-*.json`):

| Modo | Esito |
| --- | --- |
| **a** `python manage.py shell -c "<chiama lo script>"`, la shell sposta il descrittore 1 sull'errore (`exec 3>&1 1>&2`) e la risposta va al 3 | stesso documento della fixture e dei sei layout, anche con un `manage.py` che usa `ManagementUtility`; ma gli errori escono come li lascia Django: 3 con `Tipo: messaggio` per un modulo che non si importa, **1 con una traccia intera** per `KeyError` e per il driver mancante (l'errore sta in `ManagementUtility`, prima del nostro codice), **0 con l'uscita vuota** per un `manage.py` che non lancia nulla; con `-I` **non si importa `config`** (`-I` toglie la cartella dello script da `sys.path`, e `python manage.py` ce la mette) |
| **b** (scelto) lo script principale: salva il descrittore 1 e lo punta sull'errore (il blocco di Flask), mette la cartella di `manage.py` in testa a `sys.path` (quello che fa `python manage.py`), poi `runpy.run_path("manage.py", run_name="__main__")` con `sys.argv = shell -c "import daodan_django_routes; daodan_django_routes.deliver()"` | stesso documento, e gli errori sono uniformi: 3 con `Tipo: messaggio` (`ModuleNotFoundError`, `KeyError: 'SECRET_KEY'`, `ImproperlyConfigured`), 4 per un `manage.py` che non lancia il comando, 124 al tempo |
| **c** sostituisce `django.core.management.execute_from_command_line` con una funzione sua | stesso documento per un `manage.py` che la chiama, **4 per quello che usa `ManagementUtility`** (non la chiama mai: la forma di django-configurations) |

Scelto **b**: regge un `manage.py` qualsiasi e dà errori uniformi. Le tre versioni di Django danno lo stesso documento.

## Parametri

| Parametro | Valori |
| --- | --- |
| Come si trovano le impostazioni | `python manage.py shell -c` con il descrittore 1 spostato dalla shell (`exec 3>&1 1>&2`); lo script principale che salva il descrittore e lancia `manage.py` con `runpy` e `shell -c`; lo script che sostituisce `execute_from_command_line` e lancia `manage.py` con `runpy`; `-I` sul comando; `manage.py` che chiama `ManagementUtility`; `manage.py` che non lancia nulla; nessun `manage.py` |
| Come non si carica | impostazioni che sollevano, che leggono una variabile d'ambiente, un URLconf che solleva, un `include()` che non si importa, un `include()` senza `urlpatterns`, un'app il cui `ready()` interroga il database, un URLconf che lo interroga, un modulo che non termina (5 secondi), che stampa, che lascia un thread, una funzione `atexit` che stampa, che sostituisce `sys.stdout` |
| Il database | nessun `DATABASES`; `postgresql` senza il driver; `postgresql` con il driver e senza server; sqlite in memoria |
| Come si vede la rotta | `path()`, `re_path()`, `include()` (modulo, tupla, namespace, parametro nel prefisso), `i18n_patterns`, `static()` con `DEBUG`, `admin.site.urls`; vista a funzione, decorata con e senza `wraps`, `partial`, lambda, `async`; vista a classe, `http_method_names`, mixin, `head` e `options` dichiarati, `TemplateView`, `RedirectView`; DRF: router, viewset, `@action`, `APIView`, generica, `@api_view` |
| Dove sta la vista | nel progetto; in un altro file del progetto (il mixin); in `site-packages` (Django, DRF); in un pacchetto locale installato (PEP 610) |
| Versioni | Django 6.1.3, 5.2.19, 4.2.30 (Python 3.12.1 di Modal); DRF (la più recente alla data) |
| Ambiente | quello del runner (`preparation.ENV`), `python -I` per lo script, `timeout --kill-after=10 900`, `cwd` la cartella del `manage.py` |

File: `fixture/` (un progetto Django con un caso per forma), `layouts/` (sei progetti: `subfolder`, `two-projects`, `no-manage`, `custom-launcher`, `installed-copy`, `drf`), `probe/` (gli script esplorativi), `plan.py` (i comandi che il runner darebbe), `modal_probe.py`, `real_probe.py` e `compare.py`, `results/` (`results/real/` ha solo i conteggi dei progetti veri).

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/django-routes/modal_probe.py --mode explore
... modal_probe.py --mode record                    (tests/fixtures/premap/django/)
... real_probe.py                                    (poi: python benchmarks/django-routes/compare.py fixture healthchecks defectdojo bakerydemo)
```

## Risultato

**Che cosa stampa lo script.** Un solo documento JSON sullo standard output, `{"called": true, "routes": [...], "unread": [...], "locale": null}`: lo script salva il descrittore 1 prima che giri il codice del progetto ed esce con `os._exit`, così stampe, thread e funzioni `atexit` del progetto non lo sporcano né lo trattengono (varianti `thread`, `atexit-print`, `replaced-stdout`, `prints`: uscita 0 in 0,5-1,4 secondi, lo stesso documento). Ogni rotta è una foglia di `get_resolver().url_patterns`: `{path, parts, arguments, view, handlers}`, con una voce di `handlers` per metodo HTTP (`file`, `line` del `def`, `environment`, `distribution`, `owners`).

**I metodi HTTP.** Django non ha un metodo per rotta.

- Vista a classe: la regola di `View.dispatch` («ogni nome di `http_method_names` che la classe ha come attributo»); per ogni metodo la funzione che risponde. `options` e `head` restano solo dove la classe li dichiara. Un metodo la cui funzione sta in un pacchetto (`BaseListView.get`) è una riga sulla classe del progetto con la lacuna.
- DRF: `ViewSetMixin.as_view` mette sulla vista `cls` e `actions`; i metodi del progetto sono righe sulle funzioni, quelli dei mixin di DRF righe sulla classe con la lacuna. `@api_view` tiene la funzione in una chiusura di DRF: una riga sulla classe `WrappedAPIView`, senza riga di `class`, con la lacuna. `EndpointEnumerator` di DRF istanzia la vista: non provato.
- Vista a funzione: nessun dato (`require_http_methods` tiene la lista in una chiusura): una voce senza metodo, che i collegamenti dicono come rotta dichiarata senza metodo.

**Lo schema del percorso** si fa dalle parti che Django ha ricavato, mai dal testo della rotta: `normalize` sui regex compilati dei livelli, solo se ogni livello è un `RoutePattern`; un argomento è un buco solo se il convertitore è uno dei `DEFAULT_CONVERTERS` e `RoutePattern("<nome:x>", is_endpoint=True).match("a/b")` non accetta due segmenti.

| Rotta | Convertitore | `schema` |
| --- | --- | --- |
| `/shop/products/<int:pk>/` | `IntConverter`, un segmento | `/shop/products/{}` (come `/shop/products/:pk/` di Noir) |
| `/blog/<int:year>/<slug:slug>/` | `int` e `slug` | `/blog/{}/{}` |
| `/<str:tenant>/dash/report/<int:n>/` | `str` del prefisso e `int` | `/{}/dash/report/{}` |
| `/files/<path:rest>`, `/assets/<path:name>` | `PathConverter`, `.+` | nessuno |
| `/pair/<pair:p>/` | `Pair`, accetta `a/b` | nessuno |
| `/year/<yyyy:year>/` | `FourDigits`, del progetto | nessuno |
| `/legacy/(?P<year>[0-9]{4})/$`, `/optional/...`, `/(alpha\|beta)/$`, `/regex-class/$`, i router di DRF (`^items/(?P<pk>[^/.]+)/$`) | `re_path` | nessuno |
| `/en/localized/`, `/noprefix/` (`i18n_patterns`) | il prefisso dipende dalla lingua | nessuno |

**Le viste dei pacchetti.** Django non registra nessuna rotta da sé, quindi nessuna è silenziosa: una copia installata del progetto (PEP 610) è una lacuna `outside_snapshot`; il resto (admin, generiche, estensioni) una sola lacuna `model_partial` per cartella, per distribuzione (sulla fixture 31 rotte di Django).

**`include()` e `i18n_patterns`.** Un `include()` che non si importa fa fallire tutto l'URLconf (uscita 3); uno senza `urlpatterns` va in `unread` e le altre rotte restano (58 rotte invece di 60). Le rotte sotto `i18n_patterns` sono quelle della lingua del caricamento, senza schema, e una lacuna dice quante altre lingue non si elencano.

**Come non si carica.**

| Variante | Uscita | Che cosa scrive lo script |
| --- | --- | --- |
| impostazioni che importano un pacchetto assente | 3 | `ModuleNotFoundError: No module named 'not_installed'` |
| impostazioni che leggono `os.environ["SECRET_KEY"]` | 3 | `KeyError: 'SECRET_KEY'` (il container non ha le variabili del progetto; `.env` è riscritto dal container) |
| un URLconf che solleva; un `include()` che non si importa | 3 | `ModuleNotFoundError` |
| un URLconf che interroga il database; un `ready()` che lo fa | 3 | `OperationalError: no such table: shop_product` (con avviso `RuntimeWarning` di Django per il `ready()`) |
| `postgresql` senza `psycopg` | 3 | `ImproperlyConfigured: Error loading psycopg2 or psycopg module`: **`django.setup()` carica il modulo del backend** (`Options.contribute_to_class`) anche senza aprire una connessione |
| `postgresql` con il driver e senza server | 0 | le rotte (87 MB, 1,7 secondi): nessuna connessione è aperta |
| `DATABASES = {}` | 0 | le rotte |
| `manage.py` che non lancia il comando | 4 | `manage.py ran and did not run the shell command` |
| un modulo che non termina | 124 | nessun testo; `timeout` ferma dopo 5,05 secondi |
| nessun `manage.py` | nessun comando | la sorgente non lancia nulla (il comando si dà per i `manage.py` dello snapshot sotto una cartella che dichiara Django): una cartella che dichiara Django e non ha `manage.py` non ha righe né lacune |

**Il Python del comando.** La cartella è quella del `manage.py`, l'ambiente quello che `preparation.python_environment` dà per quella cartella (per Poetry `poetry env info -e`). Il nome `Django>=5` di un `pyproject.toml` è normalizzato (PEP 503); la sorgente di Flask non lo fa (`p.get("name") == "flask"`).

**Tempo e memoria** (memoria: `ru_maxrss` massimo dei processi figli):

| Caso | Tempo | Picco |
| --- | --- | --- |
| fixture, 61 rotte (29 dell'admin) | 0,5-1,6 s | 70-72 MB |
| con `postgresql` e il suo driver | 1,7 s | 87 MB |
| DRF, 15 rotte | 2,0 s | 69 MB |
| un solo `manage.py` con una rotta | 0,8-1,1 s | 59-61 MB |
| Django 4.2.30 e 5.2.19 | 1,5-2,3 s | 69-70 MB |
| `healthchecks`, 255 rotte | 2,1-2,4 s | 117 MB |
| `bakerydemo`, 466 rotte (459 di Wagtail) | 5,3-8,1 s | 194 MB |
| `defectdojo`, 852 rotte, 583 KB di JSON | 12,2-17,6 s | 229 MB |
| tutto il setup (spacchettamento di `uv`, `uv venv` e `uv pip install` di Django, rete aperta) | 3 s | non misurato |
| il ripristino dei progetti veri (rete aperta): `healthchecks` 4 s, `bakerydemo` 14 s, DefectDojo 65 s (con GCC) | | |

Nella cartella del progetto restano i `__pycache__`; nessun file esistente cambia.

## Applicazioni vere

La sorgente aggiunge abbastanza a Noir da essere collegata? Stesso albero, rete bloccata: `real_probe.py` fa girare lo script e `noir scan /work -f json --no-log` (Noir 1.5.0), `compare.py` legge le due risposte con le due sorgenti della pre-mappa e il legatore. I progetti sono pubblici, presi al commit mentre l'immagine si costruisce, mai copiati qui; `results/real/` ha i conteggi.

| Progetto | Repository, commit, licenza | Che cosa mette alla prova |
| --- | --- | --- |
| `healthchecks` | [healthchecks/healthchecks](https://github.com/healthchecks/healthchecks) `c1039ad23395162c5e2f17d324d8ccdaa60a1d14`, BSD-3-Clause; Django 6.1.3 | `include()` annidati, lo stesso elenco incluso tre volte (`api/v1/`, `v2/`, `v3/`), `include(<lista>)`, un prefisso calcolato in un f-string (`path(f"{prefix}admin/", ...)`), convertitori propri (`quoted`, `sha1`), `admin.site.urls`, `manage.py` con `try`/`except` |
| `defectdojo` | [DefectDojo/django-DefectDojo](https://github.com/DefectDojo/django-DefectDojo) `cd0a4483a224707f72a0fc3112359089c1446b55`, BSD-3-Clause; Django 5.2.17, DRF 3.18.3, drf-spectacular, django-ninja | `DefaultRouter` con i viewset registrati da funzioni (`add_<nome>_urls(v2_api)` in ogni modulo), `re_path`, URL di UI in liste importate con altri nomi, django-ninja; 6.662 file, 281 MB |
| `bakerydemo` | [wagtail/bakerydemo](https://github.com/wagtail/bakerydemo) `890285b95dcf980215ab9e9942d64ed2b47c48c3`, BSD-3-Clause; Django 6.0, Wagtail 8.1 | URL di terzi montati dal progetto (`wagtailadmin_urls`, `wagtaildocs_urls`, `wagtail_urls`, i router dell'API di Wagtail, `debug_toolbar.urls`), rotte generate da hook |

| | `fixture` | `healthchecks` | `defectdojo` | `bakerydemo` |
| --- | --- | --- | --- | --- |
| Il ripristino come lo fa il runner (`uv pip install -r requirements.txt`) | riesce, 3 s | riesce, 4 s | **fallisce** (`uwsgi`, `psycopg[c]`, `pycurl`: «command 'clang' failed»), 3 s | **fallisce** (`uwsgi`), 6 s |
| Lo script (`<nome>-script`) | 0 | 0 | **3** `No module named 'django'` | **non parte**: la sorgente non dà il comando (Django è dichiarato in `requirements/base.txt` dietro un `-r`); forzato, 3 `No module named 'dotenv'` |
| Il ripristino con `CC=gcc CXX=g++` (`<venvs>-fixed`: gli stessi comandi, nessun file del progetto cambiato) | non serve | non serve | riesce, 65 s | riesce, 14 s |
| Lo script in quell'ambiente (`<nome>-script-fixed`) | | | 0, **12-18 s, 229 MB**, 583 KB di JSON | 0, **5-8 s, 194 MB**, 390 KB |
| Lo script, quando parte | 0, 1,0-1,5 s, 72 MB | 0, 2,1-2,4 s, 117 MB, 132 KB | (sopra) | (sopra) |
| Noir 1.5.0 | 0, 0,9-1,0 s, 149 MB | 0, 0,6-1,0 s, 161 MB | 0, 2,7-3,5 s, 461-472 MB | 0, 0,5-1,1 s, 151 MB |

Il Python della prova è quello di Modal (compilato con Clang, mentre l'immagine ha solo GCC): i pacchetti che si costruiscono dal sorgente falliscono. Nel container di Daodan il Python è quello dell'immagine: non misurato. Quando lo script non parte restano Noir e la lacuna `model_failed`.

**Rotte** (una rotta è una foglia del URLconf; «del progetto» ha almeno una funzione o classe in un file dello snapshot):

| | `fixture` | `drf` | `healthchecks` | `defectdojo` | `bakerydemo` |
| --- | --- | --- | --- | --- | --- |
| Rotte che Django riporta | 61 | 15 | 255 | 852 | 466 |
| di cui viste dei pacchetti (admin, generiche, DRF, ninja, Wagtail) | 31 | 2 | 77 | 88 | 459 |
| di cui del progetto | 30 | 13 | 178 | 764 | 7 |
| con `schema` (nessun `re_path`, nessun convertitore del progetto) | 35 su 61 | 4 su 15 | 200 su 255 | 0 su 852 (tutto `re_path`) | 417 su 466 |
| Righe (rotta e metodo) | 37 | 24 | 178 | 1.194 | 4 |
| legate a una sola funzione, con file e riga | 33 | 6 | 178 | 722 | 1 |
| sulla classe del progetto, con file e riga e la lacuna (il metodo è di DRF o di Django) | 2 | 16 | 0 | 471 | 3 |
| non legate | 2 (due lambda) | 2 (`@api_view`) | 0 | 1 | 0 |
| Rotte del progetto con una riga legata o di classe | 28 | 12 | 178 | 762 | 4 |
| Endpoint di Noir | 39 | 15 | 258 | 684 (678 HTTP, 5 CLI, 1 Android) | 13 |
| con il nome del gestore | 31 | 6 | 257 | 572 | 1 |
| legati dal legatore a una sola funzione | 17 | 4 | 257 | 492 | 1 |

**Insieme**, per funzione (`compare.py`: `file:riga` portato alla riga del `def` o del `class`, poi il percorso):

| Rotte del progetto, per funzione | `fixture` | `drf` | `healthchecks` | `defectdojo` | `bakerydemo` |
| --- | --- | --- | --- | --- | --- |
| Rotte del framework con una riga | 30 | 13 | 178 | 763 | 4 |
| Noir cita la stessa funzione | 28 | 12 | 178 | 538 | 1 |
| con lo stesso percorso (schema o testo) | 21 | 2 | **178 (stesso file e riga)** | 12 | 1 |
| con il percorso scritto diversamente | 7 | 10 | 0 | 526 | 0 |
| **Solo il framework** (Noir non cita quella funzione) | 2 (`functools.partial`, un decoratore senza `wraps`) | 1 (`@api_view`: la classe, senza riga) | **0** | **225** | 3 (i viewset dell'API di Wagtail) |

| Funzioni distinte (`file:riga`), righe senza lacuna | `fixture` | `drf` | `healthchecks` | `defectdojo` | `bakerydemo` |
| --- | --- | --- | --- | --- | --- |
| Il framework | 23 | 4 | 132 | 356 | 1 |
| Noir (siti distinti) | 29 | 8 | 133 | 373 | 13 |
| in tutti e due | 21 | 4 | 132 | 285 | 1 |
| solo il framework | 2 | 0 | 0 | **71** | 0 |
| solo Noir (fuori dai file di documentazione) | 6 | 1 (la funzione di `@api_view`) | 1 (`/admin/`, una riga di `hc/urls.py`) | **72** | 12 (righe di `urls.py` senza funzione) |
| classi del progetto con la lacuna (non sono ingressi: una riga con la lacuna è una lacuna dei collegamenti) | 2 (Noir le cita) | 4 (Noir ne cita 3) | 0 | 57 (Noir ne cita 15) | 1 (Noir non la cita) |
| viste a funzione senza metodo nel framework | 17 | 0 | 178 | 302 | 1 |
| di cui Noir dà un metodo alla stessa funzione | 15 | | 178 | 240 | 1 |

- **`healthchecks`:** Noir dà tutto quello che dà il framework, anche con `include(<lista>)`, lo stesso elenco montato tre volte, il prefisso calcolato e i convertitori propri; in più un metodo per ogni vista a funzione, ma non l'admin. Che il metodo di Noir sia dedotto o di ripiego non è provato.
- **`drf`:** Noir dà la funzione di `@api_view` alla riga del suo `def`, dove il framework dà la classe senza riga.
- **`defectdojo`:** il framework vede i viewset registrati da `add_<nome>_urls(v2_api)`, che Noir non vede (225 rotte, 71 funzioni); Noir cita 72 funzioni che il framework non elenca (django-ninja e UI: perché il framework non le abbia caricate non è verificato), scrive 84 percorsi con un prefisso non risolto e attribuisce rotte di più viewset al metodo di un mixin.
- **`bakerydemo`:** le 459 rotte di Wagtail sono nel framework e nessuna è nello snapshot: una lacuna.

**Verdetto: no.** Su `healthchecks`, dove tutto gira come lo farebbe il runner, la sorgente aggiunge a Noir 0 funzioni su 132 (0 rotte su 178) e perde i metodi di 178 viste a funzione. L'unica aggiunta è DefectDojo: +71 funzioni su 356 (20%) e 42 classi che sono lacune, contro 72 funzioni che solo Noir cita e 240 metodi che solo Noir dà, a 12-18 s e 229 MB contro i 2,7-3,5 s di Noir (la memoria è nella tabella del ripristino). Se si collega, solo come complemento di Noir per i progetti che dichiarano `djangorestframework`.

## Aperto

- **Le rotte e i gestori che nessuno dei due strumenti statici lega** (lambda, `@api_view`, le classi con la lacuna, i viewset che Noir non vede): se il passo dinamico li osserva non è misurato ([call-provenance](../call-provenance/README.md) misura le chiamate dei test, non il legame rotta-gestore).
- **Il ripristino:** 2 progetti su 3 non si ripristinano nell'immagine di prova (compilatore), e Django dichiarato dietro un `-r` (`requirements/base.txt`, `bakerydemo`) non avvia la sorgente, che non dice nulla. Da misurare nel container di Daodan (`buildpack-deps:noble`).
- **Limiti dichiarati:** un `manage.py` che sceglie le impostazioni da una variabile d'ambiente le prende dal container (`.env` riscritto con segnaposto); solo `ROOT_URLCONF` (non `request.urlconf`, django-hosts); `re_path`, router di DRF e convertitori del progetto non hanno schema; `i18n_patterns` una sola lingua.
- **Non provati:** Python diverso dal 3.12; Django 3.x o più vecchio; `async` view con `View` miste; rotte aggiunte dopo l'avvio; una rotta tradotta fuori da `i18n_patterns`.
