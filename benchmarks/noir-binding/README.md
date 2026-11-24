# Noir contro il legatore: quanti endpoint di Noir si legano a una funzione, su applicazioni vere

**Stato:** In uso. La regola misurata qui è nel codice ([`binder.py`](../../daodan/core/binder.py): `_placed`, `_started`, `_agrees`, `_name_handlers`; `flows.bind_declared`). Le impronte registrate in `results/after.json` coincidono con i file di oggi (`binder.py`, `flows.py`, `premap/noir.py`, `entries.py`, `languages/semantic.py`, `edge_view.py`, `snapshot.py`).

**Domanda.** Sulle applicazioni vere, di quanti endpoint di OWASP Noir (il 1.5.0 fissato in [`premap/noir.py`](../../daodan/core/premap/noir.py)) il legatore trova una funzione unica dello snapshot, e perché non trova le altre?

**Parametri.** 25 applicazioni di 11 framework a un commit fissato, più `shhh` come taratura; Noir 1.5.0; snapshot di Daodan; Modal, rete bloccata. Nessun codice dei progetti è eseguito, né sull'host né su Modal. Nessun modello.

**Risultato valido oggi (24 novembre 2026).** Noir dà 4.706 endpoint; 3.994 arrivano al legatore; **2.297 si legano a una funzione unica** (1.631 per nome, 666 per posizione con il nome che concorda). Restano 1.697 non legati: 1.044 perché Noir non dà il gestore, 642 perché nessuna funzione dello snapshot parte alla riga citata (629 sono `.php`), 11 fabbriche rifiutate dal controllo. Nessuna delle 1.631 righe legate per nome ha cambiato simbolo; nessun arco in uscita dai nuovi legati cade fuori dalla funzione legata.

**Passo successivo della pipeline.** Questo benchmark misura un passo solo: la sorgente statica delle rotte (Noir) e il legatore. Dove Noir non dà il gestore, il dato viene dal framework caricato nel container (le rotte che nascono all'avvio, task 14 del [piano degli ingressi e dei flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md)), misurato per framework in [`fastapi-routes`](../fastapi-routes/README.md), [`django-routes`](../django-routes/README.md), [`flask-routes`](../flask-routes/README.md), [`gin-routes`](../gin-routes/README.md), [`express-routes`](../express-routes/README.md), [`nestjs-routes`](../nestjs-routes/README.md), [`expo-router-routes`](../expo-router-routes/README.md), [`laravel-routes`](../laravel-routes/README.md), [`rails-routes`](../rails-routes/README.md) e [`spring-actuator-mappings`](../spring-actuator-mappings/README.md). Quanti dei 1.697 chiude quel passo su queste 25 applicazioni non è misurato.

## Cartelle e file

| File | Contenuto |
| --- | --- |
| `apps.py` | le applicazioni (`APPS`): repository, commit, licenza (SPDX di GitHub al commit), una nota; il Noir fissato (`NOIR`). Nulla delle applicazioni è nel repository |
| `modal_binding.py` | l'immagine di ogni applicazione (rete aperta solo qui) e il lancio su Modal, rete bloccata, in parallelo; scrive la risposta di ognuna in `$NOIR_BINDING_EVIDENCE/<nome>.json`, fuori dal repository |
| `measure.py` | ciò che gira nel container: lo snapshot, Noir, `noir.read` per ogni endpoint, `binder.bind`, e per ogni riga i fatti da cui si trova la causa. Non scrive nulla sotto `/work` |
| `warm.py` | durante la costruzione dell'immagine: il pacchetto di grammatiche fissato nella cache di Daodan; ogni linguaggio dello snapshot deve dare un parser |
| `causes.py` | le cause (predicati meccanici in ordine, nessuna regola per un framework) e le correzioni candidate |
| `summarize.py` | dalla risposta di Modal ai conteggi: `results/<nome>.json` e `results/summary.json`; rifiuta una risposta il cui Noir non è quello fissato |
| `after.py`, `summarize_after.py` | la misura con il legatore di oggi: `modal_binding.py --mode after`, `results/after.json` (con le impronte della copia di `daodan/`) |
| `nodes.py`, `summarize_nodes.py` | il livello del nodo: `modal_binding.py --mode nodes`, `results/nodes.json` |
| `sample_check.py` | un campione, da leggere a occhio, degli endpoint che una correzione legherebbe. Scarica il **testo** dei sorgenti sull'host, in una cartella fuori dal repository, mai eseguito: è l'unica lettura dei progetti fuori da Modal |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NOIR_BINDING_EVIDENCE=<cartella fuori dal repository> DAODAN_CODE=<copia di daodan/ fatta all'inizio> \
  uv run --no-project --with modal modal run benchmarks/noir-binding/modal_binding.py [--only shhh,bookstack] [--mode after|nodes]
python -I benchmarks/noir-binding/summarize.py <la stessa cartella> [nome,nome]
python -I benchmarks/noir-binding/sample_check.py <la cartella> <una cartella per i sorgenti, fuori dal repository> <applicazione> <correzione> [quanti]
```

## Parametri

- **Noir:** `noir scan /work -f json --no-log`, gli argomenti che dà `premap/noir.py`, il binario del rilascio 1.5.0 con sha256 `4e176c92ee16…`, verificato durante la costruzione dell'immagine. Rete bloccata, memoria 12 GB, 4 CPU, un'ora.
- **Snapshot:** `snapshot.write_snapshot` di Daodan su `/work`, con le grammatiche del pacchetto fissato (`tree-sitter==0.26.0`, `tree-sitter-language-pack==1.13.5`).
- **Dal report al legatore:** per ogni endpoint `noir.read` (un candidato, o la lacuna che lo scarta: file fuori dallo snapshot, riga assente), poi `binder.bind` sulle righe di forma `http`. Un endpoint di un altro protocollo (`cli`, `ws`, `grpc`, `android-intent`) è contato a parte.
- **Applicazioni:** due per framework (tre per Gin, NestJS, Express ed Expo Router), con licenza permissiva verificata al commit. `shhh` (Flask, MIT) è la taratura: 6 endpoint su 6 legati, come in [flask-routes](../flask-routes/README.md).
- **Copia del codice:** la misura con il legatore di oggi usa una copia congelata di `daodan/` (1.059 file di `core` e `data`, sha256 complessivo `625bba1e3227133e…`), le cui impronte sono in `results/after.json`. Con un altro legatore la prova va rifatta con una nuova copia.

| Applicazione | Framework | Repository | Commit | Licenza | File, di cui di codice nello snapshot |
| --- | --- | --- | --- | --- | --- |
| shhh | Flask | `smallwat3r/shhh` | `448acf4bed05` | MIT | 66 |
| BookStack | Laravel | `BookStackApp/BookStack` | `0326409ecde0` | MIT | 2.625: 1.845 `.php` |
| koel | Laravel | `koel/koel` | `f0d5bc79d308` | MIT | 3.210: 1.775 `.php` |
| rubygems.org | Rails | `rubygems/rubygems.org` | `6f51e3246343` | MIT | 1.934: nessun `.rb` nello snapshot |
| Lobsters | Rails | `lobsters/lobsters` | `d23941fd73b7` | BSD-3-Clause (GitHub: NOASSERTION) | 827: nessun `.rb` nello snapshot |
| gin-vue-admin | Gin | `flipped-aurora/gin-vue-admin` | `dcac232afb56` | Apache-2.0 | 778: 412 `.go` |
| go-admin | Gin | `go-admin-team/go-admin` | `f24c303f6156` | MIT | 412: 336 `.go` |
| go-gin-example | Gin | `eddycjy/go-gin-example` | `4f5174ca325b` | MIT | 1.073: 36 `.go` |
| nestjs-boilerplate | NestJS | `brocoders/nestjs-boilerplate` | `9620f159eefe` | MIT | 489: 170 `.ts` |
| nest-admin | NestJS | `buqiyuan/nest-admin` | `5b549e540d52` | MIT | 274: 240 `.ts` |
| nestjs-realworld | NestJS | `mikro-orm/nestjs-realworld-example-app` | `30b709d9f21a` | MIT | 69: 43 `.ts` |
| node-express-boilerplate | Express | `hagopj13/node-express-boilerplate` | `179ae84efec6` | MIT | 78: 50 `.js` |
| anything-llm | Express | `Mintplex-Labs/anything-llm` | `593c0943facb` | MIT | 1.624: 801 `.js` |
| juice-shop | Express (TS) | `juice-shop/juice-shop` | `c9f99228d9d5` | MIT | 1.498: 664 `.ts` |
| litecast | Expo Router | `dylsteck/litecast` | `e73b95374d4b` | MIT | 87 (4 moduli `+api`) |
| uni-stack | Expo Router | `bidah/uni-stack` | `96d62ca4c6d5` | MIT | 145 (4 moduli `+api`, tRPC) |
| expo-template | Expo Router | `mrmeg/expo-template` | `4571ece79f22` | MIT | 1.268 (6 moduli `+api`) |
| spring-petclinic | Spring (Java) | `spring-projects/spring-petclinic` | `500158f73241` | Apache-2.0 | 132: 50 `.java` |
| RuoYi | Spring (Java) | `yangzongzhuan/RuoYi` | `d6708994364b` | MIT | 696: 287 `.java` |
| spring-petclinic-kotlin | Spring (Kotlin) | `spring-petclinic/spring-petclinic-kotlin` | `9823b3aa9798` | Apache-2.0 | 108: 38 `.kt` |
| eShopOnWeb | ASP.NET Core | `dotnet-architecture/eShopOnWeb` | `4da8212117e8` | MIT | 459: 254 `.cs` (archiviato) |
| eShop | ASP.NET Core | `dotnet/eShop` | `669682e72430` | MIT | 1.110: 547 `.cs` (API minime) |
| healthchecks | Django | `healthchecks/healthchecks` | `c1039ad23395` | BSD-3-Clause | 1.276: 658 `.py` |
| DefectDojo | Django | `DefectDojo/django-DefectDojo` | `cd0a4483a224` | BSD-3-Clause | 6.659: 2.599 `.py` |
| full-stack-fastapi-template | FastAPI | `fastapi/full-stack-fastapi-template` | `77e550a73bb4` | MIT | 248: 43 `.py` |
| Dispatch | FastAPI | `Netflix/dispatch` | `dd2837e82a0b` | Apache-2.0 | 1.569: 717 `.py` (archiviato) |

I commit completi sono in `apps.py`. Tempo e memoria: Noir 0,6-3,7 s e 153-479 MB; lo snapshot da 0,9 s (nestjs-realworld) a 131 s (RuoYi) e 128 s (DefectDojo).

## La regola del legatore

Per una riga di Noir con un nome di gestore:

1. il nome per posizione, come prima: una funzione dello snapshot con quel `name` o `qualified_name` che copre la riga;
2. altrimenti l'unica funzione che parte alla riga del gestore (`handler.line`), purché **il nome concordi**: stesso nome o nome qualificato; la parte dopo l'ultimo punto uguale (`api.GetPage` per `SysApi.GetPage`); la classe che la possiede; `x.f()` per una fabbrica `f` le cui funzioni interne si ripiegano tutte in essa; una funzione senza nome accetta ogni nome. Se più funzioni partono alla riga vale quella che nessun'altra tiene per estensione; più funzioni esterne sono una lacuna;
3. una funzione anonima legata prende come nome la sua rotta (`Facts.route_named`: `METHOD percorso`), così ha un nodo suo;
4. una riga senza nome non si lega mai per posizione.

Perché questa e non un'altra, dai dati (prima misura, sulle 1.631 righe legate per nome e sui 2.363 non legati di allora):

| Alternativa | Misura | Esito |
| --- | --- | --- |
| la riga del gestore da sola (`starts-at-line`) | 670 non legati hanno una funzione unica, 7 ambigui; 0 delle righe già legate cambia funzione | adottata, con il nome che concorda |
| il nodo senza il nome della rotta | solo 288 dei 670 finiscono su un nodo proprio e di una sola funzione: 326 si ripiegano sulla funzione che registra le rotte (57 rotte su `systemEndpoints` in anything-llm), 46 non hanno nodo, 10 dividono il nodo con una funzione sorella | per questo la funzione anonima prende il nome della rotta |
| la funzione più interna che copre la riga, senza gestore di Noir (`innermost-covering`) | darebbe una funzione a 321 endpoint, ma sono 48 funzioni di registrazione | scartata: sbagliata per costruzione |
| la funzione 1-3 righe sotto un decoratore (`nested-below`) | lega 39 endpoint di DefectDojo, ma sulle righe con un gestore si applica 4 volte e sbaglia 4 | scartata: lo snapshot non distingue la riga di un decoratore da quella della definizione |
| il nome unico nel file (`name-in-file`) | 209 legati, ma 21 righe già legate diventano ambigue | scartata |
| il nome unico nel progetto (`name-in-project`) | 127 unici e 274 ambigui sui non legati, 600 ambigui sulle già legate | scartata |

Un legame a una funzione senza nodo romperebbe i link (`flows.link_facts` fallisce con un simbolo `None`): la regola non lo fa.

## Risultati con il legatore di oggi

`modal_binding.py --mode after` e `summarize_after.py`, sulle 25 applicazioni più `shhh`. Colonne: **Noir** gli endpoint del report; **scartati** quelli che non arrivano al legatore (altro protocollo, file fuori dallo snapshot, nessun percorso); **http** quelli che arrivano; **nome** quelli con un nome di gestore, `closure` compreso; **per nome** i legati con la sola regola 1; **ora** i legati; **nodi** i nodi distinti fra i legati, prima e ora.

| Applicazione | Noir | scartati | http | nome | per nome | ora | nodi | non legati |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BookStack | 349 | 4 | 345 | 341 | 0 | 0 | 0 → 0 | 345 |
| koel | 368 | 29 | 339 | 288 | 0 | 0 | 0 → 0 | 339 |
| rubygems.org | 256 | 244 | 12 | 0 | 0 | 0 | 0 → 0 | 12 |
| Lobsters | 245 | 237 | 8 | 0 | 0 | 0 | 0 → 0 | 8 |
| gin-vue-admin | 222 | 5 | 217 | 1 | 0 | 1 | 0 → 1 | 216 |
| go-admin | 152 | 13 | 139 | 93 | 0 | 93 | 0 → 93 | 46 |
| go-gin-example | 29 | 0 | 29 | 0 | 0 | 0 | 0 → 0 | 29 |
| nestjs-boilerplate | 22 | 0 | 22 | 22 | 22 | 22 | 22 → 22 | 0 |
| nest-admin | 97 | 3 | 94 | 94 | 88 | 94 | 88 → 94 | 0 |
| nestjs-realworld | 40 | 0 | 40 | 21 | 21 | 21 | 21 → 21 | 19 |
| node-express-boilerplate | 15 | 0 | 15 | 13 | 0 | 13 | 0 → 13 | 2 |
| anything-llm | 426 | 2 | 424 | 354 | 4 | 354 | 2 → 340 | 70 |
| juice-shop | 206 | 18 | 188 | 117 | 1 | 106 | 1 → 88 | 82 |
| litecast | 5 | 0 | 5 | 4 | 4 | 4 | 4 → 4 | 1 |
| uni-stack | 15 | 0 | 15 | 15 | 13 | 15 | 9 → 11 | 0 |
| expo-template | 19 | 3 | 16 | 15 | 15 | 15 | 15 → 15 | 1 |
| spring-petclinic | 45 | 13 | 32 | 17 | 17 | 17 | 17 → 17 | 15 |
| RuoYi | 508 | 67 | 441 | 304 | 304 | 304 | 300 → 300 | 137 |
| spring-petclinic-kotlin | 49 | 16 | 33 | 18 | 18 | 18 | 18 → 18 | 15 |
| eShopOnWeb | 54 | 0 | 54 | 35 | 25 | 32 | 21 → 28 | 22 |
| eShop | 66 | 5 | 61 | 56 | 37 | 46 | 34 → 43 | 15 |
| healthchecks | 258 | 0 | 258 | 257 | 257 | 257 | 132 → 132 | 1 |
| DefectDojo | 691 | 13 | 678 | 572 | 492 | 572 | 250 → 305 | 106 |
| full-stack-fastapi-template | 34 | 3 | 31 | 23 | 23 | 23 | 23 → 23 | 8 |
| Dispatch | 535 | 37 | 498 | 290 | 290 | 290 | 290 → 290 | 208 |
| **Totale (25)** | **4.706** | **712** | **3.994** | **2.950** | **1.631** | **2.297** | **1.247 → 1.858** | **1.697** |

- **I 666 legati per posizione:** 391 con una funzione senza nome, 107 con il nome dopo l'ultimo punto, 91 fabbriche, 77 classi. Il nome non ha negato nessuna legatura: la causa «Noir names X, the function at the line is Y» non si presenta mai.
- **Le 1.631 già legate:** 0 con il simbolo cambiato, in due confronti (con un secondo `Facts` intatto e con i nodi della misura precedente). Nessuna è tornata non legata.
- **I link:** `flows.link_facts(manifest, [])` costruisce senza errori in 26 applicazioni su 26, e le voci `rotta` di Noir hanno gli stessi simboli delle righe del legatore.
- **Gli archi dei nuovi legati:** 117 endpoint con almeno un arco in uscita, 269 archi, **0 fuori dalle righe della funzione legata**. Per le 1.631 di prima: 1.022 righe, 3.064 archi, 10 fuori in 9 righe (i sovraccarichi di RuoYi, eShopOnWeb, eShop: due metodi con lo stesso nome qualificato).
- **Il gruppo più grande di endpoint su un nodo fra i nuovi** è 7, ed è una sola funzione che risponde a sette metodi: `serveQuarantineFiles()` in juice-shop e le due `app.all("/*")` di anything-llm. Fra tutti i legati resta `hc/api/views.py::ping`, 12 endpoint, una funzione.
- **Per linguaggio del file citato,** con la sola regola 1 (endpoint che arrivano; fra parentesi con un nome, legati per nome): `.py` 1.243 (1.139, 1.062); `.php` 666 (629, 0); `.js` 472 (370, 4); `.ts` 359 (288, 164); `.go` 331 (94, 0); `.java` 323 (321, 321); `.yaml` 226 (0, 0); `.json` 125 (0, 0); `.cs` 83 (81, 62); `.kt` 18 (18, 18); `.cshtml` 18; `.xml` 18; `.css` 47; `.html` 18.

### Le 11 fabbriche rifiutate

Una fabbrica (`f()`: la funzione che costruisce il gestore) è legata solo se tutte le funzioni scritte dentro di lei si ripiegano in lei. In juice-shop cinque non passano il controllo:

| Fabbrica (righe) | Endpoint | Dentro: la funzione restituita | Dentro: funzioni con nome che non si ripiegano |
| --- | --- | --- | --- |
| `servePublicFiles()` (13-59) | 7 (`/ftp/:file`, ogni metodo) | `(anonymous)` 14-23, ripiegata | `verify`, `verifySuccessfulPoisonNullByteExploit`, `endsWithAllowlistedFileType` |
| `login()` (18-83) | 1 (`POST /rest/user/login`) | `(anonymous)` 32-55, ripiegata | `afterLogin`, `verifyPreLoginChallenges`, `verifyPostLoginChallenges` |
| `getLanguageList()` (12-90) | 1 (`GET /rest/languages`) | `(anonymous)` 13-78, ripiegata | `calcPercentage` |
| `b2bOrder()` (16-47) | 1 (`POST /b2b/v2/orders`) | `(anonymous)` 17-38, ripiegata | `uniqueOrderNumber`, `dateTwoWeeksFromNow` |
| `promotionVideo()` (50-78) | 1 (`GET /promotion`) | `(anonymous)` 51-74, ripiegata | `favicon` |

Giudizio dai dati: sono gestori veri persi, non legature false evitate. Il controllo è conservativo e costa 11 endpoint su 677 (1,6%). Gli altri 91 endpoint di fabbrica di juice-shop restano legati; per una fabbrica legata il nodo porta le chiamate della funzione anonima che restituisce, ripiegata in essa.

### I tre dubbi, sui 391 endpoint legati a una funzione senza nome

Dalle estensioni dello snapshot e dall'albero sintattico della funzione legata (tutti gli alberi letti).

1. **Una funzione legata mentre la riga ha prima un middleware o un guard: 0 su 391.** La funzione legata è l'ultimo argomento della sua chiamata in 390 casi (l'altro è un `export default`); nessun argomento prima di lei contiene una funzione; nessuna è un elemento di un array.
2. **Un registrar anonimo sulla stessa riga della closure che registra: 0.** Per nessuna delle 391 un'altra funzione parte alla sua riga. `module.exports = (app) => app.get(...)` non è fra queste applicazioni.
3. **Due endpoint di metodi diversi sulla stessa funzione senza nome: 2 funzioni, 14 endpoint, ed è giusto.** Sono le due `app.all("/*", ...)` di anything-llm (`collector/index.js:221`, `server/index.js:192`): Noir scrive un endpoint per metodo.

Dieci nuovi endpoint scelti a caso (seme 24) fra quelli con un arco in uscita: tutti gli archi letti cadono dentro le righe della funzione legata.

| Applicazione | Rotta | Gestore di Noir | Nodo (righe della funzione) | Archi |
| --- | --- | --- | --- | --- |
| juice-shop | GET /rest/repeat-notification | `repeatNotification()` | `repeatNotification` (9-20) | 2 |
| juice-shop | POST /rest/2fa/disable | `twoFactorAuth.disable` | `disable` (142-170) | 2 |
| juice-shop | PUT /rest/continue-code-fixIt/apply/:con | `restoreProgress.restoreProgres` | `restoreProgressFixIt` (61-80) | 1 |
| go-admin | GET /api/v1/server-monitor | `api.ServerInfo` | `ServerMonitor.ServerInfo` (46-70) | 7 |
| go-admin | POST /api/v1/logout | `handler.LogOut` | `LogOut` (156-163) | 1 |
| eshoponweb | GET /api/catalog-brands | `closure` | `GET /api/catalog-brands` (28-31) | 1 |
| eshoponweb | GET /api/catalog-types | `closure` | `GET /api/catalog-types` (28-31) | 1 |
| defectdojo | POST /product/{product_id}/import_scan_re | `ImportScanResultsView` | `ImportScanResultsView.post` (1063-1103) | 4 |
| defectdojo | POST /jira/advanced | `AdvancedJiraView` | `AdvancedJiraView.post` (437-466) | 3 |
| defectdojo | POST /jira/{tid}/delete | `DeleteJiraView` | `DeleteJiraView.post` (563-599) | 5 |

## Perché non si legano

I 1.697 non legati di oggi sono gli 11 delle fabbriche più 1.686 che nessun dato di Noir lega. Il legatore li dice in due cause («null handler» 1.044, «no function starts at the line» 642); la prima misura (`causes.py`, predicati in ordine) li divide per natura:

### Nessuna funzione del progetto serve l'endpoint: 207

- **Noir cita un file e nessuna riga** (204): un file statico che il framework serve (`public/400.html` in rubygems.org e Lobsters; 133 file di `static/js` e `static/css` in RuoYi), la collezione Postman di nestjs-realworld (19), `docs/netlify.toml` di DefectDojo.
- **Noir nomina una closure e nessuna funzione parte alla riga** (3): `MapHealthChecks` di eShopOnWeb e `MapDefaultEndpoints` di eShop, una risposta del framework.

### Lo snapshot non ha una funzione dove Noir cita: 1.090

- **Il file citato non è letto dallo snapshot** (1.010): 664 `.php` (BookStack e koel: i file sono nell'inventario perché `source_files.STACK_SOURCE_LANGUAGES` elenca `.php`, senza lingua né dichiarazioni), 226 `.yaml` (207 la specifica OpenAPI di Dispatch), 104 `.json` (specifiche Swagger che Noir etichetta `spec-only`), 16 `.xml` (`pom.xml` di spring-petclinic: gli endpoint di Actuator che Noir deduce dalla dipendenza).
- **Il file citato è markup** (32): `.cshtml` (18) e `.razor` (14): il gestore sta in un blocco `@code`.
- **Il file di codice non ha funzioni** (48): 14 `build.gradle.kts`, 27 `.ts` di juice-shop in `data/static/codefixes/`, 5 `urls.py` di Django, 2 altri.

### Noir non dà il gestore: 389

- **Noir cita la riga della registrazione, dentro una funzione** (282): in Gin 207 + 15 + 15, juice-shop 39, DefectDojo 3, RuoYi 2, eShop 1. Esempio: `{"url":"/api/createApi","method":"POST","handler":null,"details":{"code_paths":[{"path":"server/router/system/sys_api.go","line":20}]}}`, e lo snapshot ha `ApiRouter.InitApiRouter` alle righe 10-35, la funzione che registra 20 rotte.
- **Noir cita l'intestazione di una classe** (50, DefectDojo): un viewset le cui azioni sono ereditate da una classe del framework. Il gestore è la classe, non una funzione.
- **Noir cita la riga di un decoratore** (39, DefectDojo, `api_v3/routes.py`): `@router.post("/import")` alla riga 193 e `import_endpoint` alla 194, dentro `build_import_router`.
- **Noir non dà gestore e nessuna funzione copre la riga** (18): fra questi 7 rotte di pagina del frontend di fastapi-template (`createFileRoute`), che non sono rotte del server.

Le altre 677 righe non legate della prima misura erano discordanze di nome o di riga fra Noir e lo snapshot: oggi 666 sono legate e 11 sono le fabbriche.

## Per framework

- **Laravel** (BookStack, koel): Noir dà 685 endpoint `http`, 624 con `Classe@azione` più file e riga del controller e 5 closure con file e riga; **0 si legano**, perché i `.php` sono nell'inventario senza lingua né dichiarazioni. `php artisan route:list` aggiungerebbe controller e azione a 34 rotte e non una funzione legabile: serve prima un lettore di PHP e delle sue dichiarazioni.
- **Rails** (rubygems.org, Lobsters): Noir dà 501 endpoint, 441 con `controller#azione` più file e riga del controller; 481 non arrivano al legatore (478 sono `.rb`, fuori dallo snapshot) e i 20 che arrivano sono file statici. `bin/rails routes` darebbe gli stessi `controller#azione`, senza un'uscita per le macchine: non aggiunge dati.
- **Gin:** per 237 endpoint su 385 Noir non dà il gestore (cita la riga della registrazione); dove lo dà (94: 91 con una variabile davanti, `api.GetPage`; 3 closure) il legatore lega 94 su 94. `(*Engine).Routes()` dà il gestore proprio dove Noir non lo dà: [`gin-routes`](../gin-routes/README.md).
- **NestJS:** 137 su 137 nominati si legano (6 di nest-admin con la fine del nome qualificato, la classe è dentro una funzione); 19 vengono da una collezione Postman.
- **Express:** 473 legati su 627 (13, 354 e 106); 353 gestori sono `closure`, legati alla funzione anonima che parte alla riga, con il nome della rotta. 91 legami di juice-shop sono alla fabbrica che costruisce il gestore.
- **Expo Router:** Noir legge solo i moduli `+api`: 34 su 34 nominati si legano. Le schermate non sono nel report.
- **Spring, Django, FastAPI:** dove Noir nomina il gestore il legatore lega il 100% (Spring Java 321 su 321, Kotlin 18 su 18, FastAPI 313 su 313, healthchecks 257 su 257, DefectDojo 572 su 572). I non legati sono file statici, `pom.xml`, `.yaml` di specifica, `urls.py`, intestazioni di viewset e decoratori.
- **ASP.NET Core:** 78 legati su 115 (32 e 46), comprese le closure delle API minime; 33 endpoint sono `.cshtml` o `.razor`.

## Laravel e Rails: il comando ufficiale, e che cosa manca a Noir

Il comando, letto senza eseguire nulla ([laravel-routes](../laravel-routes/README.md), [rails-routes](../rails-routes/README.md)):

| | Laravel (BookStack + koel) | Rails (rubygems.org + Lobsters) |
| --- | --- | --- |
| endpoint `http` nel report | 685 | 501 |
| gestore `Classe@azione` / `controller#azione`, con file e riga **del controller** | 624 (91%) | 441 (88%) |
| closure con file e riga | 5 (`route:list` dà `Closure` e `file:riga`: lo stesso) | 0 |
| senza gestore | 56: 18 solo dalla specifica `api-docs/api.yaml`, 34 in file di rotte, 4 altri | 60: 37 in `config/routes.rb` (reindirizzamenti, motori montati, `to:` con lambda), 23 file di `public/` |

Mancano a Noir meno dati di quanti ne manchino a Daodan per usarli: i 624 e i 441 hanno già il file e la riga del controller, ma lo snapshot non ha dichiarazioni PHP né Ruby. Eseguire il framework non cambia questo. Con un lettore PHP o Ruby il confronto va rifatto: `articles#show` contro `ArticlesController.show` è una forma che la regola di oggi non copre.

## Non coperto

- **btcpayserver** (`btcpayserver/btcpayserver`, MIT, commit `da4b5935c160`) è in `apps.py` e **non è nei conteggi**: il suo snapshot non è finito in un'ora (`results/btcpayserver.json` ha solo la causa). Non è indagato dove stia il tempo.
- **Le applicazioni sono scelte, non campionate,** a un commit solo, con Noir 1.5.0. La regola è un dato, non una regola di framework, ma i numeri valgono per queste 25.
- **Che il legame sia giusto** è verificato sulle 1.631 righe già legate (0 cambiate), sugli archi (0 fuori dalla funzione) e su 59 endpoint letti a occhio con `sample_check.py`. Non è misurato se il metodo e il percorso di Noir siano giusti: solo se il gestore si lega.
- **Le rotte che Noir non vede** (prefissi dinamici, `Route::resource` non espanso, rotte dei pacchetti): non misurate qui, perché nulla è eseguito.
- **Expo Router:** solo i moduli `+api`, 36 endpoint in tutto.
- **Python 3.12 dell'immagine:** i file con una sintassi più nuova sono letti con un altro Python che Daodan scarica, e nel container senza rete non c'è; l'effetto sui conteggi non è misurato.
- **Il ritorno dei risultati da Modal:** una chiamata con la rete bloccata non restituisce più di circa 8 KB; la risposta è un generatore di pezzi di 6.000 byte (`modal_binding.py`).
