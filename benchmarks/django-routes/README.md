# Django: il URLconf caricato (`get_resolver()` dentro `manage.py shell -c`)

Domanda: che cosa dà Django, caricato nel container senza rete, per ogni rotta (metodo, percorso, vista con file e riga), e come la sorgente della pre-mappa
[`daodan/core/premap/django_app.py`](../../daodan/core/premap/django_app.py) lo lega alle funzioni dello snapshot. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14b.
**Misurato il 24 novembre 2026 su Modal** (Django 6.1.3, 5.2.19 e 4.2.30, immagine del runner, rete bloccata); i numeri sotto sono di quelle esecuzioni. La sorgente è scritta e provata,
**non è collegata** (`premap/__init__.py`, `container_runner.TOOLS`, `entry-queries.json` sono di altri: le righe da aggiungere sono nel rapporto del task; i test le iniettano).
Il confronto con Noir sulle stesse cartelle è in fondo («Applicazioni vere») e decide il collegamento.

Il codice del progetto (la fixture, i layout, i progetti pubblici, Django e i loro pacchetti) gira solo nel container, mai su questa macchina: le immagini si costruiscono con la rete aperta
(l'unico momento in cui lo è) e ogni variante gira in una copia della cartella con la rete bloccata.

| Cartella o file | Contenuto |
| --- | --- |
| `fixture/` | un progetto Django 6.1.3 (`manage.py`, `config/`, `shop/`): `path` con `int`, `slug`, `str` e `path`, due convertitori propri (`FourDigits` con `regex` senza `/`, `Pair` con un `/`), `re_path` con gruppi con nome, un gruppo opzionale e un `\|`, `include()` con `app_name`, con un parametro nel prefisso (`<str:tenant>/dash/`) e con la forma `("modulo", "app")`, `i18n_patterns` con e senza `prefix_default_language` e una rotta tradotta, viste a classe (`View`, una sottoclasse di `ListView`, un mixin del progetto in un altro file, `head` e `options` dichiarati), `require_http_methods`, `require_GET` su una `async def`, `csrf_exempt` sopra `login_required`, una `functools.partial`, un decoratore senza `wraps`, due lambda, `TemplateView.as_view()` e `RedirectView.as_view()` scritte nell'URLconf, `admin.site.urls`, `static()` |
| `layouts/` | sei progetti: `subfolder` (`requirements.txt` alla radice, `src/manage.py`), `two-projects` (due `manage.py`, uno con `requirements.txt` e uno con `pyproject.toml`), `no-manage` (dichiara Django, nessun `manage.py`), `custom-launcher` (un `manage.py` che usa `ManagementUtility` da sé, come django-configurations), `installed-copy` (un pacchetto locale installato non in modalità modificabile, `direct_url.json`), `drf` (`DefaultRouter`, `ModelViewSet`, `ReadOnlyModelViewSet`, `@action`, `APIView`, `ListCreateAPIView`, `@api_view`) |
| `probe/` | gli script esplorativi: `launch.py` (tre modi di far girare il `manage.py` del progetto) e `dump.py` (l'albero del URLconf, un livello per volta, con la normalizzazione di Django) |
| `plan.py` | stampa, con il Python che ha le dipendenze di Daodan, per una cartella: il comando di setup di `container_runner.plan`, le righe di ripristino di `container_runner._python`, il Python di ogni ambiente e i comandi di `django_app.commands` (e il comando di Noir): legge solo i nomi dei file; la voce `TOOLS["django"]` che il collegamento aggiunge è qui (`setdefault`) |
| `modal_probe.py` | `--mode explore`: gli script di `probe/` sulle varianti; `--mode record`: lo script della sorgente (`premap/django_routes.py`) sulle varianti che i test leggono, scritte in `tests/fixtures/premap/django/` con l'impronta dello script e la `VERSION` (`script.json`) |
| `real_probe.py`, `compare.py` | la fixture e tre progetti pubblici, Django e Noir sugli stessi alberi, e il confronto (sotto) |
| `results/<variante>.json` | `argv`, `cwd`, `returncode`, `stdout` (i primi 60.000 caratteri; 1.000.000 per `dump*`), `stderr`, secondi, memoria di picco, file lasciati e cambiati nel progetto; `results/real/` i conteggi dei confronti (senza il sorgente dei progetti) |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/django-routes/modal_probe.py --mode explore
... modal_probe.py --mode record                    (tests/fixtures/premap/django/)
... real_probe.py                                    (poi: python benchmarks/django-routes/compare.py fixture healthchecks defectdojo bakerydemo)
```

## Parametri provati

| Parametro | Valori |
| --- | --- |
| Come si trovano le impostazioni | `python manage.py shell -c` con il descrittore 1 spostato dalla shell (`exec 3>&1 1>&2`); lo script principale che salva il descrittore e lancia `manage.py` con `runpy` e `shell -c`; lo script che sostituisce `execute_from_command_line` e lancia `manage.py` con `runpy`; `-I` sul comando; `manage.py` che chiama `ManagementUtility`; `manage.py` che non lancia nulla; nessun `manage.py` |
| Come non si carica | impostazioni che sollevano, che leggono una variabile d'ambiente, un URLconf che solleva, un `include()` che non si importa, un `include()` senza `urlpatterns`, un'app il cui `ready()` interroga il database, un URLconf che lo interroga, un modulo che non termina (5 secondi), che stampa, che lascia un thread, una funzione `atexit` che stampa, che sostituisce `sys.stdout` |
| Il database | nessun `DATABASES`; `postgresql` senza il driver; `postgresql` con il driver e senza server; sqlite in memoria |
| Come si vede la rotta | `path()`, `re_path()`, `include()` (modulo, tupla, namespace, parametro nel prefisso), `i18n_patterns`, `static()` con `DEBUG`, `admin.site.urls`; vista a funzione, decorata con e senza `wraps`, `partial`, lambda, `async`; vista a classe, `http_method_names`, mixin, `head` e `options` dichiarati, `TemplateView`, `RedirectView`; DRF: router, viewset, `@action`, `APIView`, generica, `@api_view` |
| Dove sta la vista | nel progetto; in un altro file del progetto (il mixin); in `site-packages` (Django, DRF); in un pacchetto locale installato (PEP 610) |
| Versioni | Django 6.1.3, 5.2.19, 4.2.30 (Python 3.12.1 di Modal); DRF (la più recente alla data) |
| Ambiente | quello del runner (`preparation.ENV`), `python -I` per lo script, `timeout --kill-after=10 900`, `cwd` la cartella del `manage.py` |

## Un elenco ufficiale degli schemi (la domanda del piano)

Nessun comando di `django-admin` elenca gli URL: `show_urls` è di django-extensions (terzi, non valutato). Che cosa c'è, letto dal sorgente di Django 6.1.3 e misurato:

| Dato | Che cosa dà | Uso |
| --- | --- | --- |
| `django.urls.get_resolver()` e `URLResolver.url_patterns` | l'albero: `URLResolver` (`include()`, `admin.site.urls`, `i18n_patterns`) e `URLPattern` (`callback`, `name`, `pattern`) | **usato**: la ricorsione di `django_routes.walk` |
| `URLPattern.lookup_str` | il nome puntato della vista (`functools.partial.func`, `view_class`) | la regola che Django applica per sapere che cosa è la vista, ripresa in `function` |
| `django.contrib.admindocs.views.extract_views_from_urlpatterns` | la ricorsione di Django per `admindocs`: `(callback, str(pattern) unito, namespace, name)`; **si importa anche con l'admin fuori da `INSTALLED_APPS`** (31 viste sulla fixture senza admin, 60 con; `results/dump-no-admin.json`) | valutata e non usata: non dà i convertitori dei livelli (nessuno schema), non dice la classe del pattern (`re_path`, `i18n_patterns`) e salta in silenzio un `ImportError` |
| `URLResolver.reverse_dict` | le stesse forme di `normalize`, chiavi per `callback` e per nome | valutato e non usato: non è per rotta |
| `django.utils.regex_helper.normalize` | la forma con un buco per ogni argomento (`shop/products/%(pk)s/`) del regex compilato, la funzione che usa `reverse()` | **usato** per le parti del percorso (sotto) |
| `RoutePattern.converters` | `{argomento: convertitore}` di ogni livello | **usato** per gli argomenti |

## Come si trovano le impostazioni, senza una convenzione sul nome (misurato)

Le impostazioni sono quelle che il `manage.py` del progetto imposta (`DJANGO_SETTINGS_MODULE`): nessun dato ufficiale le dà senza eseguirlo (`wsgi.py` e `asgi.py` hanno la loro riga, e il valore sta in un `os.environ.setdefault`, nel codice). La sorgente non legge `manage.py`: lo esegue, con il comando che la documentazione dà (`django-admin shell --command`, `-c`). Tre modi confrontati, 26 varianti ciascuno (`results/launch-*.json`):

| Modo | Esito |
| --- | --- |
| **a** `python manage.py shell -c "<chiama lo script>"`, la shell sposta il descrittore 1 sull'errore (`exec 3>&1 1>&2`) e la risposta va al 3 | stesso documento della fixture e dei sei layout, anche con un `manage.py` che usa `ManagementUtility`; ma gli errori escono come li lascia Django: 3 con `Tipo: messaggio` per un modulo che non si importa, **1 con una traccia intera** per `KeyError` e per il driver mancante (l'errore sta in `ManagementUtility`, prima del nostro codice), **0 con l'uscita vuota** per un `manage.py` che non lancia nulla; con `-I` **non si importa `config`** (`-I` toglie la cartella dello script da `sys.path`, e `python manage.py` ce la mette) |
| **b** (scelto) lo script principale: salva il descrittore 1 e lo punta sull'errore (il blocco di Flask), mette la cartella di `manage.py` in testa a `sys.path` (quello che fa `python manage.py`), poi `runpy.run_path("manage.py", run_name="__main__")` con `sys.argv = shell -c "import daodan_django_routes; daodan_django_routes.deliver()"` | stesso documento, e gli errori sono uniformi: 3 con `Tipo: messaggio` (`ModuleNotFoundError`, `KeyError: 'SECRET_KEY'`, `ImproperlyConfigured`), 4 per un `manage.py` che non lancia il comando, 124 al tempo |
| **c** sostituisce `django.core.management.execute_from_command_line` con una funzione sua | stesso documento per un `manage.py` che la chiama, **4 per quello che usa `ManagementUtility`** (non la chiama mai: la forma di django-configurations) |

Scelto **b**: è il più piccolo che regge un `manage.py` qualsiasi (il progetto fa quello che ha scritto, `ManagementUtility` chiama `django.setup()` e il comando), con un solo punto in cui il progetto può scrivere sullo standard output prima di noi che il blocco comune chiude (`os.dup`, `os.dup2`, `os._exit`). `shell -c` importa i modelli dell'app nel suo spazio dei nomi (Django 5.0 in poi stampa «N objects imported automatically»: nel nostro caso va sull'errore). `--no-imports` esiste solo da Django 5.0 e non si passa. Django 6.1.3, 5.2.19 e 4.2.30 danno lo stesso documento (stessi percorsi, stesse funzioni e righe del progetto; le righe delle funzioni di Django cambiano).

## Che cosa stampa lo script (misurato)

Un solo documento JSON, e nient'altro, sullo standard output: `{"called": true, "routes": [...], "unread": [...], "locale": null}`. Prima che giri il codice del progetto, lo script salva il descrittore 1 e lo punta sull'errore: ciò che il progetto stampa (anche prima di `django.setup()`), i suoi processi figli, o un `sys.stdout` sostituito non arrivano all'uscita; il documento va al descrittore salvato e lo script esce con `os._exit`, così un thread che non finisce o una funzione `atexit` non lo tengono vivo né scrivono dopo (`thread`, `atexit-print`, `replaced-stdout`, `prints`: uscita 0, 0,5-1,4 secondi, lo stesso documento). Un errore scrive `Tipo: messaggio` sull'errore ed esce con 3.

Ogni rotta (una foglia di `get_resolver().url_patterns`) è `{path, parts, arguments, view, handlers}`: `path` il testo come Django lo scrive (`str(pattern)` di ogni livello, senza il `^` che Django toglie componendo: `/shop/products/<int:pk>/`; `/legacy/(?P<year>[0-9]{4})/$` per un `re_path`), `parts` e `arguments` per lo schema, `view` la classe di una vista a classe, `handlers` una voce per metodo HTTP con `{kind, type, module, qualname, file, line, environment, distribution, owners}` (`line` è la riga del `def`, dal parse del modulo con `ast`, come per Flask; `owners` le distribuzioni che contengono il modulo, `importlib.metadata.packages_distributions`). Un `include()` il cui URLconf non dà i pattern è in `unread`, e le altre rotte restano; `locale` dice la lingua in cui si è caricato il progetto se c'è un `i18n_patterns`.

## I metodi HTTP: che cosa c'è di ufficiale e che cosa no (misurato)

Django non ha un metodo per rotta.
- **Vista a classe**: la regola di `View.dispatch` (e di `View.view_is_async`, che la ripete) è «ogni nome di `http_method_names` che la classe ha come attributo»; lo script la legge e dà, per ogni metodo, **la funzione che risponde** (`getattr(cls, nome)`, `inspect.unwrap`): `ProductList.get` e `ProductList.post`, il `get` di un mixin del progetto nel suo file (`shop/mixins.py`), `Mixed.post`. `options` c'è su ogni `View` (`View.options`): è lasciato dove è di Django e tenuto dove la classe lo dichiara (`OwnHead.options`); `head` è ciò che `View.setup` dà come `get` (`self.head = self.get`): lasciato dove la sua funzione è quella di `get`, tenuto dove la classe lo dichiara. Un metodo la cui funzione sta in un pacchetto (`BaseListView.get` per una sottoclasse di `ListView`) è una riga **sulla classe del progetto** (file e riga della `class`) con la lacuna che lo dice: nessuna funzione del progetto risponde.
- **DRF**: `ViewSetMixin.as_view` mette sulla vista `cls` e `actions` (metodo HTTP, nome del metodo della classe): la regola è la stessa (`getattr(cls, nome)`), e per un `APIView` `view_class`. `ItemViewSet.list` e `ItemViewSet.publish` sono righe sulle funzioni del progetto; `CreateModelMixin.create`, `RetrieveModelMixin.retrieve` righe sulla classe con la lacuna. `@api_view` tiene la funzione del progetto in una chiusura di DRF (`WrappedAPIView.get` è `handler` di `rest_framework/decorators.py`): **riga sulla classe `WrappedAPIView` del file del progetto, senza riga di `class`, con la lacuna**; la funzione non si legge senza leggere la chiusura. Non letto: `EndpointEnumerator` di DRF (`rest_framework.schemas.generators`, il suo elenco ufficiale dei metodi con `callback.cls().allowed_methods`) istanzia la vista; non provato.
- **Vista a funzione**: nessun dato. `require_http_methods`, `require_GET`, `require_POST`, `require_safe` tengono la lista nella chiusura di `inner` (letto da `django/views/decorators/http.py` 6.1.3: nessun attributo, `functools.wraps` copia solo `__dict__`): una voce **senza metodo**. Leggere la chiusura per nome sarebbe una regola scritta a mano sulla forma di un decoratore. I collegamenti dicono per ognuna «declared route None /...: it has no method» (`flows._declared_routes`); la proposta è nel rapporto.

## Lo schema del percorso, dalle parti che Django ha ricavato (misurato)

Una riga offre una rotta ai collegamenti solo se ha `schema`, il percorso come lo legge `REST` (`/shop/products/{}`), e un metodo suo. Django non ha `part_isolating`: ha, per ogni argomento di `path()`, un convertitore con `regex` (attributo documentato) e nessun attributo dice se può contenere una `/`. Lo schema si fa così, mai dal testo della rotta:

- **Le parti**: `normalize` (`django.utils.regex_helper`) dei regex compilati dei livelli composti come li compone `URLResolver._populate` (`p.pattern.regex.pattern` senza il `^`): `shop/products/%(pk)s/` e `["pk"]`; il modulo si formatta con una mappa che dà a ogni argomento il suo nome fra due NUL (nessuna rotta ne ha) e si divide: nessuna lettura del testo. Solo se **ogni livello è un `RoutePattern`** (`path()`) e `normalize` dà una forma sola; `re_path`, `i18n_patterns` e una classe di pattern del progetto non hanno parti (`results/dump.json`: `^optional/(?:(?P<n>[0-9]+)/)?$` dà due forme, `^(alpha\|beta)/$` dà `%(_0)s/`).
- **Gli argomenti**: il convertitore di ogni livello, il prefisso compreso (`<str:tenant>/dash/report/<int:n>/` ha `tenant` e `n`). Un argomento è un buco solo se il convertitore è uno dei `DEFAULT_CONVERTERS` di Django e **Django stesso** non gli fa accettare un percorso di due segmenti: la domanda è un `RoutePattern("<nome:x>", is_endpoint=True).match("a/b")` (il metodo con cui il resolver confronta una rotta; il nome è quello con cui il convertitore è registrato, `get_converters()`), misurato su `int`, `str`, `slug` e `uuid` (no: un buco), `path` (`.+`) e `Pair` (`[^/]+/[^/]+`) (sì: nessuno schema) e `FourDigits` (`[0-9]{4}`), del progetto: nessun dato dice che è un segmento, nessuno schema. Nessuna espressione regolare nello script (il controllo del nucleo ne vieta di nuove) e nessun analizzatore.

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

## Le viste dei pacchetti dell'ambiente: l'admin non è silenziosa (misurato)

Flask registra da sé una rotta (`static`) e il dato ufficiale la dice (`has_static_folder`); **Django non registra nessuna rotta da sé**: l'admin, `TemplateView.as_view()`, `RedirectView`, `LoginView`, `static()` sono rotte che il progetto monta e la cui risposta non è nello snapshot. Tre casi, per dato ufficiale:
- **Una copia installata del progetto** (`direct_url.json`, PEP 610: `file:///work/libs/shared`): una lacuna `outside_snapshot` con la distribuzione e la cartella (`layouts/installed-copy`: `/shared/view/` sì, `/own/` è una riga).
- **Il resto** (l'admin, le generiche, le rotte di un'estensione, `django.views.static.serve`): **una sola lacuna `model_partial` per cartella, per distribuzione** (`Django (31: /admin/, /admin/login/, /admin/logout/ and 28 more)`, `djangorestframework (...)`): il dato è la distribuzione che contiene il file (`importlib.metadata.packages_distributions`), nessun elenco di app. Sulla fixture sono 31 rotte di Django (29 dell'admin con due modelli, `/about/`, `/go/`); con `DEBUG` si aggiunge `static()` (`debug-static`).
- **Nessuna è silenziosa**: non esiste un dato che dica «questa rotta è di Django e nessuno la monta».

## `include()`, namespace, `i18n_patterns` (misurato)

- **`include()`** importa il modulo subito, dove si legge `urls.py`: un modulo che non si importa fa fallire tutto l'URLconf (`broken-include`: uscita 3, `ModuleNotFoundError`); quello che fallisce dopo è un modulo senza `urlpatterns` (`URLResolver.url_patterns` solleva `ImproperlyConfigured: The included URLconf ... does not appear to have any patterns`; una lista vuota è accettata): è in `unread` e le altre rotte restano (`no-patterns-include`: 58 rotte invece di 60, una lacuna con il prefisso). `hasattr(pattern, "url_patterns")` solleva per un URLconf così: si usa `isinstance(pattern, URLResolver)`.
- **Namespace**: `app_name` e `namespace` non cambiano il percorso: non sono nel documento. La stessa funzione montata tre volte (healthchecks monta `api_urls` come `api/v1/`, `v2/` e `v3/`) sono tre rotte.
- **`i18n_patterns`**: il regex di `LocalePrefixPattern` dipende dalla lingua attiva (`en/` nella fixture, `it/` con `translation.override("it")`): le rotte sono quelle della lingua del caricamento (`LANGUAGE_CODE`), senza schema, e **una lacuna** dice quante altre lingue di `LANGUAGES` hanno rotte proprie che non si elencano (senza `LANGUAGES` sono le 100 di Django). Con `prefix_default_language=False` il prefisso della lingua predefinita è vuoto. Una rotta tradotta (`gettext_lazy`) fuori da `i18n_patterns` mostra il testo della lingua attiva: non provato.

## Come non si carica (misurato)

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

## Il Python del comando e la cartella (misurato)

La cartella del comando è quella del `manage.py` (non la cartella che dichiara Django: `requirements.txt` alla radice e `src/manage.py` è il caso comune, `layouts/subfolder`), l'ambiente quello che `preparation.python_environment` dà per quella cartella (il codice del passo dinamico dei test Python e della sorgente di Flask), per Poetry quello che dice `poetry env info -e`. Due `manage.py` sotto cartelle con un manifesto proprio sono due comandi in due ambienti (`two-projects`: `a` con `requirements.txt`, `b` con `pyproject.toml`) che si dividono i 900 secondi. Il nome di Django nel `pyproject.toml` è come lo scrive il progetto (`Django>=5`): la sorgente lo normalizza (PEP 503); **la sorgente di Flask no** (`p.get("name") == "flask"`: un `Flask>=3` di un `pyproject.toml` non la avvia, provato per Django con `Django>=5`).

## Tempo e memoria (misurati)

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

La memoria è la massima dei processi figli del comando (`ru_maxrss`, `timeout` compreso). Nella cartella del progetto restano i `__pycache__` dei moduli importati; nessun file esistente cambia.

## Applicazioni vere

Domanda (del coordinatore, 24 novembre 2026, dopo la misura di Spring: lì Noir 1.5.0 dava le stesse rotte con lo stesso file e la stessa riga delle strutture del framework, 337 su 337): la sorgente
aggiunge abbastanza a Noir da essere collegata? Stesso albero, stessa copia, rete bloccata: `real_probe.py` fa girare lo script (`<nome>-script`) e `noir scan /work -f json --no-log` (`<nome>-noir`, il comando di `premap/noir.py`,
Noir 1.5.0) e `compare.py` legge le due risposte con le due sorgenti della pre-mappa e il legatore di Daodan. I tre progetti sono pubblici, con licenza permissiva, presi durante la costruzione dell'immagine al commit indicato e mai copiati qui
(`git fetch --depth 1 <url> <commit>`, senza `.git`); i risultati interi stanno fuori dal repository (`DAODAN_REAL_OUT`), qui solo i conteggi (`results/real/`). La fixture e `layouts/drf` (una rotta nota per ogni caso) sono i controlli.

| Progetto | Repository, commit, licenza | Che cosa mette alla prova |
| --- | --- | --- |
| `healthchecks` | [healthchecks/healthchecks](https://github.com/healthchecks/healthchecks) `c1039ad23395162c5e2f17d324d8ccdaa60a1d14`, BSD-3-Clause; Django 6.1.3 | `include()` annidati, lo stesso elenco incluso tre volte (`api/v1/`, `v2/`, `v3/`), `include(<lista>)`, un prefisso calcolato in un f-string (`path(f"{prefix}admin/", ...)`), convertitori propri (`quoted`, `sha1`), `admin.site.urls`, `manage.py` con `try`/`except` |
| `defectdojo` | [DefectDojo/django-DefectDojo](https://github.com/DefectDojo/django-DefectDojo) `cd0a4483a224707f72a0fc3112359089c1446b55`, BSD-3-Clause; Django 5.2.17, DRF 3.18.3, drf-spectacular, django-ninja | `DefaultRouter` con i viewset registrati da funzioni (`add_<nome>_urls(v2_api)` in ogni modulo), `re_path`, URL di UI in liste importate con altri nomi, django-ninja; 6.662 file, 281 MB |
| `bakerydemo` | [wagtail/bakerydemo](https://github.com/wagtail/bakerydemo) `890285b95dcf980215ab9e9942d64ed2b47c48c3`, BSD-3-Clause; Django 6.0, Wagtail 8.1 | URL di terzi montati dal progetto (`wagtailadmin_urls`, `wagtaildocs_urls`, `wagtail_urls`, i router dell'API di Wagtail, `debug_toolbar.urls`), rotte generate da hook |

Nessuno dei tre ha bisogno, per `django.setup()`, di un servizio esterno o di un segreto (sqlite o nessun database; `SECRET_KEY` ha un valore di ripiego in `healthchecks` e in DefectDojo; `bakerydemo` usa `dev`): **le condizioni sotto non sono del progetto ma del ripristino**.

| | `fixture` | `healthchecks` | `defectdojo` | `bakerydemo` |
| --- | --- | --- | --- | --- |
| Il ripristino come lo fa il runner (`uv pip install -r requirements.txt`) | riesce, 3 s | riesce, 4 s | **fallisce** (`uwsgi`, `psycopg[c]`, `pycurl`: «command 'clang' failed»), 3 s | **fallisce** (`uwsgi`), 6 s |
| Lo script (`<nome>-script`) | 0 | 0 | **3** `No module named 'django'` | **non parte**: la sorgente non dà il comando (Django è dichiarato in `requirements/base.txt` dietro un `-r`); forzato, 3 `No module named 'dotenv'` |
| Il ripristino con `CC=gcc CXX=g++` (`<venvs>-fixed`: gli stessi comandi, nessun file del progetto cambiato) | non serve | non serve | riesce, 65 s | riesce, 14 s |
| Lo script in quell'ambiente (`<nome>-script-fixed`) | | | 0, **12-18 s, 229 MB**, 583 KB di JSON | 0, **5-8 s, 194 MB**, 390 KB |
| Lo script, quando parte | 0, 1,0-1,5 s, 72 MB | 0, 2,1-2,4 s, 117 MB, 132 KB | (sopra) | (sopra) |
| Noir 1.5.0 | 0, 0,9-1,0 s, 149 MB | 0, 0,6-1,0 s, 161 MB | 0, 2,7-3,5 s, 461-472 MB | 0, 0,5-1,1 s, 151 MB |

(Due esecuzioni complete: gli intervalli sono i loro estremi.) Il Python della prova è quello di Modal (3.12.1, compilato con Clang; nell'immagine c'è GCC e basta: ogni pacchetto che si costruisce dal sorgente fallisce, `sysconfig` dice `clang`). Nel container di Daodan il Python è quello dell'immagine (GCC): **non misurato**; la riga con GCC è quello che il ripristino darebbe lì. Quando lo script non parte, resta il risultato di Noir (statico: non ha bisogno del ripristino) e la lacuna `model_failed` con la causa.

**Rotte** (una rotta è una foglia del URLconf; «del progetto» è quella con almeno una funzione o classe in un file dello snapshot; le altre sono viste dei pacchetti, contate in una lacuna per distribuzione):

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

**Insieme** (`compare.py`: una rotta del framework è cercata nella lista di Noir dalla posizione della sua funzione, il `file:riga` che i due strumenti citano, portato alla riga del `def` o del `class` che lo contiene, perché Noir cita una riga di decoratore e `inspect` quella del primo decoratore di una classe; poi il percorso). Una rotta con `re_path` ha il percorso scritto come espressione regolare (Django) o come modello `{nome}` (Noir) e nessuno dei due si legge per farlo uguale all'altro: è «stessa funzione, percorso scritto diversamente».

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

Che cosa fa ciascuno, dagli esempi (`results/real/<nome>.json`, `examples`):
- **`healthchecks`**: Noir dà tutto quello che dà il framework, stessa funzione, stesso percorso, stessa riga, **anche con `include(<lista>)`, lo stesso elenco montato tre volte, il prefisso calcolato (era `""`) e i convertitori propri**; in più dà un metodo per ogni vista a funzione (178 su 178: il framework non ne ha nessuno), ma non l'admin (una riga di `hc/urls.py` e nessuna delle 77 rotte che Django genera). Che il metodo di Noir sia dedotto o di ripiego non è provato.
- **`drf` (il controllo)**: con il router nello stesso `urls.py` Noir dà le rotte del router (`/v1/items/`, `/v1/items/{pk}/`, `publish`), i metodi del progetto (`ItemViewSet.list` alla riga 15, `publish` alla 19), la riga della classe per i metodi di DRF (11, 23, 36) e, dove il framework dà la classe `WrappedAPIView` senza riga, la funzione di `@api_view` alla riga del suo `def` (42): **qui Noir ha più del framework**.
- **`defectdojo`**: i viewset registrati da `add_<nome>_urls(v2_api)`, che Noir non vede: 225 rotte (quattro scritture per viewset: lista e dettaglio, con e senza `.formato`), cioè **71 funzioni** (le azioni `close`, `generate_report`, `accept_risks`...) e 42 classi che Noir non cita. Noir scrive 84 percorsi con un prefisso non risolto (`/{}api/v2/...`), attribuisce le rotte di più viewset al metodo di un mixin (`dojo/api_v2/mixins.py:143`: il mixin è la funzione, il percorso è di un altro viewset), legge quattro reindirizzamenti di `docs/netlify.toml` come endpoint e **cita 72 funzioni che il framework non elenca**: nei primi 40 siti, le rotte di django-ninja (`dojo/*/api_v3/routes.py`, funzioni del progetto che per Django sono viste di ninja, nella lacuna delle 44) e quelle di UI di `dojo/endpoint/ui/views.py` (perché il framework non le abbia caricate non è verificato). Il framework non dà il metodo di 302 viste a funzione; Noir ne dà uno per 240.
- **`bakerydemo`**: le 459 rotte di Wagtail (generate da hook e router) sono nel framework e nessuna è nello snapshot: una lacuna. Le tre del progetto che Noir non vede sono i viewset dell'API di Wagtail (`PersonApiViewSet`, riga sulla classe con la lacuna); Noir dà le 12 righe di `urls.py` come endpoint senza funzione.
- **`fixture`**: Noir non vede `functools.partial(pages.generic, ...)` (cita la riga dell'URLconf) e per un decoratore senza `wraps` cita la funzione avvolta, non quella che Django esegue; il framework non dà i metodi di `require_http_methods` (Noir sì: `GET` e `POST` su `cart`).

**Verdetto sul collegamento: no.** Il numero che decide è `healthchecks`, dove tutto gira come lo farebbe il runner: la sorgente aggiunge a Noir **0 funzioni su 132 (0 rotte su 178)** e perde i metodi di 178 viste a funzione che Noir dà. L'unica aggiunta vera è DefectDojo, dove i viewset di DRF sono registrati da funzioni: **+71 funzioni su 356 (20%)** e 42 classi che sono lacune, e in cambio **−72 funzioni** che solo Noir cita (ninja e UI) e 240 metodi che solo Noir dà, a 12-18 s e 229 MB contro 2,7-3,5 s e 462-472 MB di Noir. Nel controllo di DRF Noir ha più del framework (`@api_view`). Se si collega comunque, solo come **complemento di Noir per i progetti che dichiarano `djangorestframework`**, e dopo aver detto che Django dichiarato dietro un `-r` (`bakerydemo`) non la avvia. Il ripristino che fallisce per il compilatore dell'immagine di prova (2 progetti su 3) **non entra nel verdetto**: è un limite dell'immagine di Modal, non misurato nel container di Daodan.

## Limiti dichiarati e non corretti

- **Un `manage.py` che sceglie le impostazioni da una variabile d'ambiente** (`DJANGO_SETTINGS_MODULE` della shell, un `.env`) le prende dal container, che non ha quella del progetto: l'ambiente della prova è quello del runner (`.env` è riscritto con segnaposto).
- **Più URLconf**: solo `ROOT_URLCONF`; un URLconf scelto per richiesta (`request.urlconf`, django-hosts) non si legge.
- **Django dichiarato altrove che in `pyproject.toml` o `requirements.txt` di una cartella** (`requirements/base.txt` dietro un `-r`, come bakerydemo): la sorgente non parte e non dice nulla (la lettura dei pacchetti della pre-mappa non segue `-r`).
- **`api_view` di DRF**: la funzione del progetto sta nella chiusura di DRF: una riga sulla classe `WrappedAPIView` e la lacuna.
- **`re_path` e router di DRF**: nessuno schema, quindi nessun incontro con una chiamata (una lacuna per rotta e metodo nei collegamenti).
- **Un convertitore del progetto**: nessuno schema, anche se la sua `regex` è di un segmento solo (nessun dato lo prova).
- **Funzioni di Django** (`BaseListView.get`...): la riga è sulla classe del progetto; la classe non è una funzione e il legatore non la lega (la riga ha la lacuna).
- **`i18n_patterns`**: una sola lingua; le altre una lacuna.
- **Il Docker di Daodan** (`buildpack-deps:noble`, il proxy dei registri): la prova gira su Modal, nella stessa immagine, con il setup eseguito con la rete aperta e il comando con la rete bloccata; il Python della prova è quello di Modal (3.12.1, compilato con Clang).
- **Non provati**: Python diverso dal 3.12; Django 3.x o più vecchio (`path()` c'è dalla 2.0); un URLconf molto grande (le 255 rotte di healthchecks e le 700 di DefectDojo sono le misure); `async` view con `View` miste; rotte aggiunte dopo l'avvio (middleware, segnali).
