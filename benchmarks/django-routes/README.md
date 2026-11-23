# Django: il URLconf caricato

Piano, task 14b. **Stato: solo fixture e note, il 23 novembre 2026; nessuna sorgente, nessuna misura.**

## Letto dal sorgente (django 6.1.3; wheel scaricato, non eseguito)

- Nessun comando di `django-admin` elenca gli URL (`show_urls` è di django-extensions, terzi, non valutato).
- Pubblico: `django.urls.get_resolver()` (in `__all__`), `URLResolver.url_patterns`, `URLPattern.pattern`, `.callback`, `.name`. Esiste anche `django.contrib.admindocs.views.extract_views_from_urlpatterns` (ufficiale, non documentata, restituisce `(callback, regex, namespace, name)`): da misurare se si importa con `admindocs` fuori da `INSTALLED_APPS`; altrimenti si percorre l'albero pubblico, e va scritto accanto quale è stata valutata.
- Le impostazioni: `python manage.py shell -c "<codice>"` (`shell` ha `-c/--command`) usa il `manage.py` del progetto, che imposta `DJANGO_SETTINGS_MODULE`: nessuna convenzione sul nome.
- I pattern non portano il metodo HTTP: una vista a funzione non lo dichiara (`require_http_methods` lo nasconde), una a classe ha `view_class`. Nessun metodo è dedotto: la riga non ha metodo.

## Da misurare

Cosa dà `get_resolver()` sulla fixture (`include`, `app_name`, `re_path`, una vista a classe, `require_http_methods`, una lambda); file e nome della funzione per ciascuna; se `manage.py shell -c` esce 0 senza database; tempo e memoria.
