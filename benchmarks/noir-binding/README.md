# Noir contro il legatore: quanti endpoint di Noir si legano a una funzione, su applicazioni vere

Domanda: sulle applicazioni vere, di quanti endpoint di OWASP Noir (il 1.5.0 fissato in [`premap/noir.py`](../../daodan/core/premap/noir.py)) il legatore ([`binder.py`](../../daodan/core/binder.py), `_position`) trova una funzione unica dello snapshot, e perché non trova le altre? Ogni classe di non legati è una correzione economica del legatore (o dell'adattatore) fondata su un dato, oppure un limite dichiarato. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14 (14d Laravel, 14e Rails, 14g Gin, 14h NestJS, 14i Expo Router, 14j Express; e Spring, Django, FastAPI, già confrontati fuori dal legatore). Modello di questa misura: «Applicazioni vere» di [flask-routes](../flask-routes/README.md) (dove la correzione del confronto `Classe.metodo` nacque così).

**Stato: misurato il 24 novembre 2026 su Modal.** Nessun codice dei progetti è eseguito, né sull'host né su Modal: nessun `npm install`, `composer install`, `bundle install`, costruzione o comando del framework. Leggono l'albero solo Noir (uno scanner di testo) e il codice dello snapshot di Daodan. Dei progetti non c'è nulla nel repository: restano i conteggi e brevi estratti della risposta di Noir (`results/`). Nulla è compilato qui. Il legatore misurato è quello dell'albero di lavoro del 24 novembre, con il confronto con `name` o `qualified_name` non ancora in commit (le impronte dei file di Daodan sono in `results/<app>.json`, campo `code`).

**Risultato in una riga:** su 25 applicazioni di 11 framework, Noir dà 4.706 endpoint; 3.994 arrivano al legatore, 2.950 hanno un nome di gestore, **1.631 si legano a una funzione unica** (41 % di quelli che arrivano, 55 % di quelli con un nome). Dove Noir nomina il gestore il legatore lega il 100 % in Spring (321 su 321 in Java, 18 su 18 in Kotlin), in FastAPI (313 su 313) e in healthchecks (257 su 257), il 96 % in NestJS (131 su 137), il 94 % in Expo Router (32 su 34), l'86 % in DefectDojo (492 su 572) e **0 su 94 in Gin, 5 su 484 in Express, 62 su 91 in ASP.NET**. Dei 2.363 non legati: **677 (29 %) sono una discordanza di nome o di riga fra Noir e lo snapshot, e un dato di Noir, la riga del gestore (`handler.line`), ne lega 670 a una funzione unica (7 ambigui) senza cambiare nessuna delle 1.631 righe già legate; ma 96 dei 670 legano la funzione che costruisce il gestore (nome con `()`, juice-shop), non il gestore; e a livello di nodo (seconda misura, «A livello di nodo») solo 288 dei 670 finiscono su un nodo proprio e di una sola funzione: 326 si ripiegano sulla funzione che registra le rotte (57 rotte su un nodo in anything-llm), 46 non hanno nodo, 10 dividono il nodo con una funzione sorella; dando alla funzione anonima il nome della rotta, come già fanno i link, 660 su 670 hanno un nodo proprio**; 1.090 non hanno una funzione nello snapshot (664 sono PHP, che Daodan non legge); 389 sono endpoint per cui Noir non nomina il gestore; 207 non hanno una funzione del progetto (file statici, risposte del framework). **Con la regola scritta nell'albero («Dopo la correzione»): 2.308 legati su 3.994 (+677) con la prima versione del legatore, 2.297 (+666) con la seconda (il nome deve concordare), 0 dei 1.631 già legati con il simbolo cambiato, i link si costruiscono in 26 applicazioni su 26.**

## Cartelle e file

| File | Contenuto |
| --- | --- |
| `apps.py` | le applicazioni (`APPS`): repository, commit, licenza (SPDX di GitHub al commit, con il nome del file), una nota; il Noir fissato (`NOIR`). Nulla delle applicazioni è nel repository |
| `modal_binding.py` | l'immagine di ogni applicazione (rete aperta solo qui) e il lancio su Modal, rete bloccata, in parallelo; scrive la risposta di ognuna in `$NOIR_BINDING_EVIDENCE/<nome>.json` (fuori dal repository: contiene gli endpoint di Noir) |
| `measure.py` | ciò che gira nel container: lo snapshot, Noir, `noir.read` per ogni endpoint, `binder.bind`, e per ogni riga i fatti da cui si trova la causa. Non scrive nulla sotto `/work` (l'elenco dei file prima e dopo è confrontato: nessun file lasciato né cambiato, in tutte le applicazioni) |
| `warm.py` | durante la costruzione dell'immagine: il caricatore di Daodan (`languages/_treesitter.py`) mette il pacchetto di grammatiche fissato (sha256 verificato) nella sua cache e ogni linguaggio dello snapshot deve dare un parser, altrimenti la costruzione fallisce |
| `causes.py` | le cause (predicati meccanici in ordine, nessuna regola per un framework) e le correzioni candidate, ognuna una funzione dei soli fatti registrati |
| `summarize.py` | dalla risposta di Modal ai conteggi: `results/<nome>.json` e `results/summary.json`, e la tabella; rifiuta una risposta il cui Noir non è quello fissato |
| `after.py`, `summarize_after.py` | la misura dopo la correzione (sezione «Dopo la correzione»): `modal_binding.py --mode after` con il codice dell'albero, senza sostituire il legatore; `results/after.json` (con le impronte della copia di `daodan/`) |
| `nodes.py`, `summarize_nodes.py` | il livello del nodo (sezione «A livello di nodo»): `modal_binding.py --mode nodes` scrive `<nome>.nodes.json` (fuori dal repository), `summarize_nodes.py` scrive `results/nodes.json` |
| `compare_after.py` | i difetti del legatore (sezione «Difetti del legatore»): due corse di `modal_binding.py --mode after`, il legatore di un commit (`DAODAN_CODE`) e quello dell'albero, riga per riga; scrive `results/t1c6.json` |
| `sample_check.py` | un campione, da leggere a occhio, degli endpoint che una correzione legherebbe: che cosa cita Noir, la funzione scelta, le righe del sorgente. Scarica il **testo** dei sorgenti sull'host (in una cartella fuori dal repository, mai eseguito): è l'unica lettura dei progetti fuori da Modal. Stampa, non scrive |
| `results/<nome>.json` | per applicazione: conteggi, cause con 3 esempi ciascuna (estratti della risposta di Noir e dichiarazioni dello snapshot: nome e righe, mai sorgente), correzioni, impronte del codice di Daodan |
| `results/summary.json` | gli stessi conteggi per framework e in totale (senza `shhh`, la taratura) |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 NOIR_BINDING_EVIDENCE=<cartella fuori dal repository> DAODAN_CODE=<copia di daodan/ fatta all'inizio> \
  uv run --no-project --with modal modal run benchmarks/noir-binding/modal_binding.py [--only shhh,bookstack]
python -I benchmarks/noir-binding/summarize.py <la stessa cartella> [nome,nome]
python -I benchmarks/noir-binding/sample_check.py <la cartella> <una cartella per i sorgenti, fuori dal repository> <applicazione> <correzione> [quanti]
```

## Parametri provati

- **Noir:** `noir scan /work -f json --no-log`, gli argomenti che dà `premap/noir.py` (`commands`, letti dal codice), il binario del rilascio 1.5.0 con sha256 `4e176c92ee16…`, verificato durante la costruzione dell'immagine. Rete bloccata, memoria 12 GB, 4 CPU, un'ora.
- **Snapshot:** `snapshot.write_snapshot` di Daodan su `/work` (la radice del progetto, come nel container di Daodan), con le grammatiche del pacchetto fissato (`tree-sitter==0.26.0`, `tree-sitter-language-pack==1.13.5`).
- **Dal report al legatore:** per ogni endpoint del report, `noir.read` (lo stesso passo della pre-mappa: un candidato, o la lacuna che lo scarta: file fuori dallo snapshot, riga assente), poi `binder.bind` sulle righe di forma `http`. Un endpoint di un altro protocollo (`cli`, `ws`, `grpc`, `android-intent`) non è una rotta: è contato a parte.
- **Applicazioni:** due vere per framework (tre per Gin, NestJS, Express ed Expo Router, dove era facile), a un commit fissato, con licenza permissiva (verificata al commit con `gh api repos/<repo>/license?ref=<commit>`; Lobsters dà `NOASSERTION`: il file letto per intero è la licenza BSD a tre clausole, la terza nomina l'autore). Più `shhh` (Flask, MIT), la taratura: la risposta nota è 6 endpoint su 6 legati ([flask-routes](../flask-routes/README.md), «Il legatore, prima e dopo»), e così è uscita.

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

I commit completi sono in `apps.py`. Tempo e memoria (seconda esecuzione, quella dei `results/`): Noir 0,6-3,7 s e 153-479 MB; lo snapshot da 0,9 s (nestjs-realworld, 69 file) a 131 s (RuoYi) e 128 s (DefectDojo, 6.659 file); nella prima esecuzione DefectDojo 161 s. Le due esecuzioni complete (la seconda con i campi `code_site` in più) danno gli stessi conteggi.

## Risultati

Colonne: **Noir** gli endpoint del report; **prima** quelli che non arrivano al legatore (altro protocollo, file fuori dallo snapshot, nessun percorso); **http** quelli che arrivano; **nome** quelli con un nome di gestore, `closure` compreso (la parola di Noir per una funzione scritta sul posto); **legati** a una funzione unica; poi i non legati per gruppo di causa (sotto).

| Applicazione | Noir | prima | http | nome | legati | non legati | senza funzione del progetto | senza funzione nello snapshot | Noir senza gestore | discordanza di nome o riga |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| shhh (taratura) | 6 | 0 | 6 | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| BookStack | 349 | 4 | 345 | 341 | 0 | 345 | 1 | 344 | 0 | 0 |
| koel | 368 | 29 | 339 | 288 | 0 | 339 | 1 | 338 | 0 | 0 |
| rubygems.org | 256 | 244 | 12 | 0 | 0 | 12 | 12 | 0 | 0 | 0 |
| Lobsters | 245 | 237 | 8 | 0 | 0 | 8 | 8 | 0 | 0 | 0 |
| gin-vue-admin | 222 | 5 | 217 | 1 | 0 | 217 | 0 | 9 | 207 | 1 |
| go-admin | 152 | 13 | 139 | 93 | 0 | 139 | 19 | 12 | 15 | 93 |
| go-gin-example | 29 | 0 | 29 | 0 | 0 | 29 | 0 | 14 | 15 | 0 |
| nestjs-boilerplate | 22 | 0 | 22 | 22 | 22 | 0 | 0 | 0 | 0 | 0 |
| nest-admin | 97 | 3 | 94 | 94 | 88 | 6 | 0 | 0 | 0 | 6 |
| nestjs-realworld | 40 | 0 | 40 | 21 | 21 | 19 | 19 | 0 | 0 | 0 |
| node-express-boilerplate | 15 | 0 | 15 | 13 | 0 | 15 | 0 | 1 | 1 | 13 |
| anything-llm | 426 | 2 | 424 | 354 | 4 | 420 | 0 | 70 | 0 | 350 |
| juice-shop | 206 | 18 | 188 | 117 | 1 | 187 | 0 | 27 | 44 | 116 |
| litecast | 5 | 0 | 5 | 4 | 4 | 1 | 1 | 0 | 0 | 0 |
| uni-stack | 15 | 0 | 15 | 15 | 13 | 2 | 0 | 0 | 0 | 2 |
| expo-template | 19 | 3 | 16 | 15 | 15 | 1 | 1 | 0 | 0 | 0 |
| spring-petclinic | 45 | 13 | 32 | 17 | 17 | 15 | 1 | 14 | 0 | 0 |
| RuoYi | 508 | 67 | 441 | 304 | 304 | 137 | 133 | 2 | 2 | 0 |
| spring-petclinic-kotlin | 49 | 16 | 33 | 18 | 18 | 15 | 1 | 14 | 0 | 0 |
| eShopOnWeb | 54 | 0 | 54 | 35 | 25 | 29 | 2 | 20 | 0 | 7 |
| eShop | 66 | 5 | 61 | 56 | 37 | 24 | 1 | 13 | 1 | 9 |
| healthchecks | 258 | 0 | 258 | 257 | 257 | 1 | 0 | 1 | 0 | 0 |
| DefectDojo | 691 | 13 | 678 | 572 | 492 | 186 | 6 | 4 | 96 | 80 |
| full-stack-fastapi-template | 34 | 3 | 31 | 23 | 23 | 8 | 1 | 0 | 7 | 0 |
| Dispatch | 535 | 37 | 498 | 290 | 290 | 208 | 0 | 207 | 1 | 0 |
| **Totale (senza shhh)** | **4.706** | **712** | **3.994** | **2.950** | **1.631** | **2.363** | **207** | **1.090** | **389** | **677** |

Per framework (le righe sopra sommate):

| Framework | Applicazioni | Noir | http | nome | legati | Che cosa lega, che cosa no |
| --- | --- | --- | --- | --- | --- | --- |
| Laravel | 2 | 717 | 684 | 629 | **0** | tutti `.php`: nello snapshot, senza lingua né dichiarazioni |
| Rails | 2 | 501 | 20 | 0 | **0** | 481 su 501 scartati prima del legatore (478 sono `.rb`, fuori dallo snapshot); i 20 che arrivano sono file statici |
| Gin | 3 | 403 | 385 | 94 | **0** | per 237 Noir non dà il gestore; per 94 lo dà (91 con una variabile davanti, `api.GetPage`; 3 closure) |
| NestJS | 3 | 159 | 156 | 137 | 131 | 131 su 137 nominati; 6 hanno la classe annidata in una funzione; 19 vengono da una collezione Postman |
| Express | 3 | 647 | 627 | 484 | **5** | 479 sono discordanze: 353 closure, 102 `f()`, 10 con un oggetto davanti, 14 `ctrl.azione` o procedure con una funzione anonima |
| Expo Router | 3 | 39 | 36 | 34 | 32 | 2 sono procedure tRPC (funzione anonima) |
| Spring (Java) | 2 | 553 | 473 | 321 | 321 | 321 su 321 nominati; 134 endpoint sono file statici |
| Spring (Kotlin) | 1 | 49 | 33 | 18 | 18 | 18 su 18 nominati; 14 sono `build.gradle.kts` (Actuator, etichetta `framework-provided`) |
| ASP.NET Core | 2 | 120 | 115 | 91 | 62 | 16 closure (API minime) con una funzione che parte alla riga; 33 in `.cshtml` o `.razor` |
| Django | 2 | 949 | 936 | 829 | 749 | 77 viste a classe che Noir nomina con la classe; 96 senza gestore |
| FastAPI | 2 | 569 | 529 | 313 | 313 | 313 su 313 nominati; 207 da un file di specifica OpenAPI (`.yaml`) |

Per linguaggio del file citato (endpoint che arrivano al legatore, tutte le applicazioni; fra parentesi con un nome, legati): `.py` 1.243 (1.139, 1.062); `.php` 666 (629, **0**); `.js` 472 (370, **4**); `.ts` 359 (288, 164); `.go` 331 (94, **0**); `.java` 323 (321, 321); `.yaml` 226 (0, 0); `.json` 125 (0, 0); `.cs` 83 (81, 62); `.kt` 18 (18, 18); `.cshtml` 18; `.xml` 18; `.css` 47; `.html` 18. I file `.yaml`, `.json`, `.xml`, `.css`, `.html` sono specifiche, collezioni Postman, `pom.xml`, file statici: non sono codice di un gestore.

## Perché non si legano (misurato)

I gruppi sono i predicati di `causes.cause`, in ordine; ogni non legato ha il primo che vale. Nessun non legato è rimasto non classificato.

### Nessuna funzione del progetto serve l'endpoint: 207

- **Noir cita un file e nessuna riga** (204): un file statico che il framework serve (`public/400.html` in rubygems.org e Lobsters; in RuoYi 133 file di `static/js` e `static/css`; i `.css`, `.html`, `.txt` di go-admin), la collezione Postman `e2e/Conduit.postman_collection.json` di nestjs-realworld (19), `docs/netlify.toml` di DefectDojo. Il legatore legge il sito `file` senza `:riga` come il file `""` e non trova funzioni: è giusto che non leghi. Esempio, rubygems.org: `{"url":"/400.html","handler":null,"details":{"code_paths":[{"path":"public/400.html"}]}}`.
- **Noir nomina una closure e nessuna funzione parte alla riga** (3): `MapHealthChecks` di eShopOnWeb e `MapDefaultEndpoints` di eShop, una risposta del framework.

### Lo snapshot non ha una funzione dove Noir cita: 1.090

- **Il file citato non è letto dallo snapshot** (1.010): 664 `.php` (BookStack e koel: i file sono nell'inventario perché `source_files.STACK_SOURCE_LANGUAGES` elenca `.php`, senza lingua né dichiarazioni), 226 `.yaml` (207 la specifica OpenAPI di Dispatch, 18 `api-docs/api.yaml` di koel, un ingress Kubernetes di gin-vue-admin), 104 `.json` (70 `server/swagger/openapi.json` di anything-llm e 34 `swagger.json` di gin-vue-admin, go-admin e go-gin-example: specifiche che Noir etichetta `spec-only`), 16 `.xml` (`pom.xml` di spring-petclinic: gli endpoint di Actuator che Noir deduce dalla dipendenza).
- **Il file citato è markup** (32): `.cshtml` (18) e `.razor` (14): il gestore, `OnInitializedAsync`, sta in un blocco `@code`; la lingua dell'inventario è `markup`.
- **Il file di codice non ha funzioni** (48): 14 `build.gradle.kts` (Actuator, spring-petclinic-kotlin), 27 `.ts` di juice-shop in `data/static/codefixes/` (frammenti di codice delle sue sfide), 5 `urls.py` di Django (4 in DefectDojo e `hc/urls.py` in healthchecks, `/admin/`: Noir cita il file delle rotte, con un gestore di libreria senza percorso, `auth_views.PasswordResetDoneView`), 2 altri (`.cs`, `.js`).

### Noir non dà il gestore: 389

- **Noir cita la riga della registrazione, dentro una funzione** (282): `{"url":"/api/createApi","method":"POST","handler":null,"details":{"code_paths":[{"path":"server/router/system/sys_api.go","line":20}]}}` e lo snapshot ha `ApiRouter.InitApiRouter` alle righe 10-35 (la funzione che registra 20 rotte, non il gestore). Gin: 207 (gin-vue-admin) + 15 + 15; juice-shop 39; DefectDojo 3; ruoyi 2; eShop 1.
- **Noir cita l'intestazione di una classe** (50, tutte DefectDojo): `AppAnalysisViewSet` alla riga 204 (204-218); le azioni (`list`, `create`…) sono ereditate da una classe del framework, fuori dallo snapshot: il gestore è la classe, non una funzione.
- **Noir cita la riga di un decoratore, e sotto parte una funzione dentro quella che copre la riga** (39, tutte DefectDojo, `api_v3/routes.py`): `@router.post("/import")` alla riga 193 e `import_endpoint` alla 194, dentro `build_import_router` 189-276. Vedi la correzione 6: non è una correzione.
- **Noir non dà gestore e nessuna funzione copre la riga** (18): DefectDojo 4; fastapi-template 7, che sono rotte di pagina di un frontend (`createFileRoute("/_layout/admin")` in `frontend/src/routes/`, riga 20: non sono rotte del server); juice-shop 5; Dispatch 1; node-express-boilerplate 1.

### Noir cita o nomina il gestore e lo snapshot ha la funzione: 677

Sono le discordanze di nome o di posizione. Ogni riga ha il file e la riga del gestore (`handler.path`, `handler.line`) e lo snapshot ha una funzione che copre la riga:

| Causa | Endpoint | Dove | Noir dice | Lo snapshot ha |
| --- | --- | --- | --- | --- |
| Noir nomina una closure e una funzione parte alla riga citata | 375 | anything-llm 350, ASP.NET 16, juice-shop 3, go-admin 2, gin-vue-admin 1, DefectDojo 3 | `{"name":"closure","path":"server/endpoints/embedManagement.js","line":37}` | `embedManagementEndpoints.(anonymous)` 37-52 |
| Il nome ha le parentesi di una chiamata | 102 | juice-shop | `recycles.blockRecycleItems()`, `routes/recycles.ts:23` | `blockRecycleItems` 23-26 (la funzione che restituisce il gestore) |
| L'ultima parte del nome è il nome di una funzione che copre la riga, con una variabile o un oggetto davanti | 101 | go-admin 91, juice-shop 10 | `api.GetPage`, `app/admin/apis/sys_api.go:33` | `SysApi.GetPage` 33-56 (il `name` di un metodo Go è `Tipo.Metodo`) |
| Il nome è la classe che possiede la funzione che copre la riga | 77 | DefectDojo (viste a classe) | `ListFindingGroups`, `dojo/finding_group/views.py:288` | `ListFindingGroups.get` 288-303 |
| Nessuna dichiarazione ha quell'ultima parte e una funzione parte alla riga (funzione anonima) | 16 | node-express-boilerplate 13, uni-stack 2, juice-shop 1 | `authController.register`, `src/controllers/auth.controller.js:5` | `(anonymous)` 5-9 (`const register = catchAsync(async (req, res) => {`) |
| Il nome è la fine del nome qualificato (la classe è dentro una funzione) | 6 | nest-admin | `BaseController.list`, `src/helper/crud/crud.factory.ts:55` | `BaseCrudFactory.BaseController.list` 55-57 |

Mai visti dove Noir nomina un gestore: il nome perso fra Noir e la riga (`handler` con nome e senza percorso), la riga citata sopra la dichiarazione (`name-above` lega 0), la riga del file delle rotte invece di quella del controller (quando Noir nomina un gestore, `handler.path` è il file del controller), due funzioni dello stesso nome sulla riga. **La riga di un decoratore c'è dove Noir non nomina il gestore** (i 39 di DefectDojo, sopra); in Spring, Kotlin e ASP.NET la dichiarazione dello snapshot comincia alla prima annotazione o attributo e Noir cita la riga della firma, 1-4 righe sotto (le 304 righe di RuoYi, tutte legate dal nome): per questo `starts-at-line` non si applica a 388 righe già legate.

## Correzioni candidate, in ordine di endpoint recuperati

Ogni correzione è un dato di Noir uguale a un dato di una dichiarazione dello snapshot, applicata a un non legato e valida solo se dà **una** funzione (qui si contano funzioni; che il nodo che il legatore restituisce sia quella funzione, e solo quella, è misurato in «A livello di nodo» sotto: lì i 670 diventano 288 senza il nome della rotta e 660 con). Misurata su 2.363 non legati e sulle 1.631 righe già legate (devono dare la stessa funzione: «diversa» sarebbe un legame sbagliato). Le righe già legate per framework sono 321 + 18 (Spring), 749 (Django), 313 (FastAPI), 131 (NestJS), 62 (ASP.NET), 32 (Expo Router), **5 (Express) e 0 (Gin)**: per Gin ed Express la prova è il campione letto, non questo confronto.

| # | Correzione | Dato di Noir = dato della dichiarazione | Non legati: una funzione | più funzioni | Già legati: stessa / nessuna / diversa |
| --- | --- | --- | --- | --- | --- |
| 1 | **`starts-at-line`** | `handler.line` (con `handler.path`: la riga della definizione del gestore, che `noir.rows` mette nel `site`) = `line` di una funzione dello snapshot in quel file | **670** (609 funzioni distinte; **96 hanno il nome con `()`: legano la funzione che costruisce il gestore**) | 7 | 1.243 / 388 / **0** |
| 2 | `last-part-covering` | l'ultimo identificatore di `handler.name` = l'ultimo identificatore del `name` di una funzione che copre la riga | 209 (185; 102 con `()`) | 0 | 1.631 / 0 / **0** |
| 3 | `qualified-suffix` | gli identificatori di `handler.name` = gli ultimi del `qualified_name` di una funzione che copre la riga | 91 (67; 85 con `()`) | 0 | 1.631 / 0 / **0** |
| 4 | `class-of-covering` | `handler.name` = il `qualified_name` della classe che possiede una funzione che copre la riga | 81 (56) | 0 | 0 / 1.631 / 0 (non si applica dove il nome è già della funzione) |
| | **le quattro insieme** (`combined`) | tutte quelle che danno una funzione, e si fermano se ne danno due diverse | **670** | 7 | **1.631 / 0 / 0** |
| 6 | `nested-below` (solo dove Noir non dà il gestore) | un'unica funzione parte 1-3 righe sotto la riga che Noir cita per la rotta (`code_paths`), dentro la funzione che copre quella riga | 39 (DefectDojo) | 0 | **0 / 1.627 / 4**: dove si applica a righe con un gestore, 4 su 4 volte sceglie una funzione annidata che non è il gestore |

- La 2 comprende la 3; la 4 e la 1 si sovrappongono (la vista a classe di DefectDojo: la classe è il nome, la riga è quella del metodo). La 1 sola recupera 670 dei 677 discordanti; 7 sono ambigui: in juice-shop la funzione che costruisce il gestore (`blockRecycleItems`) e quella anonima che restituisce partono alla stessa riga: il nome le separa, ma la funzione che il nome sceglie è la fabbrica, non il gestore.
- **Le due «correzioni» che legano la fabbrica** (96 dei 670 con la 1, 102 dei 209 con la 2): per un nome `f()` Noir cita la definizione della funzione che restituisce il gestore, non il gestore. È una scelta da fare: legare l'endpoint alla fabbrica, che è dove vive la logica della rotta e la sola funzione con un nome, oppure lasciarlo non legato. Senza questi 96, la 1 lega **574**.
- **Quanti legherebbero la funzione sbagliata.** Su 1.631 righe già legate nessuna delle prime quattro dà una funzione diversa (0 su 1.631; la 1 non si applica a 388 righe, dove nessuna funzione parte alla riga citata: vedi sopra). Sui non legati, **0 su 670** legano una funzione con un nome diverso da quello di Noir (le funzioni anonime e le classi sono escluse da questo confronto). Letti a occhio con `sample_check.py`: 51 endpoint delle correzioni 1-4 (anything-llm 8, node-express-boilerplate 4, uni-stack 2, eShop 6, eShopOnWeb 5, go-admin 6 + 3, juice-shop 8, nest-admin 4, DefectDojo 5): nessuna funzione è di un altro gestore; in 43 è la funzione che risponde alla richiesta, negli 8 di juice-shop è la fabbrica. Letti 8 su 39 della 6 (DefectDojo): in tutti la funzione sotto il decoratore è il gestore.
- **Perché la 6 non è una correzione.** Funziona sui 39 (e su 8 letti), ma sulle righe con un gestore si applica 4 volte e sbaglia 4: la riga citata è l'`def` del gestore stesso e la funzione sotto è un aiuto annidato (`access_file` e `check_file_belongs_to_object` in DefectDojo, `projects_menu` e una lambda in healthchecks). Dallo snapshot non si distingue «la riga è un decoratore» da «la riga è la definizione»: serve un dato sintattico (la riga citata cade nel decoratore della funzione), che lo snapshot non registra. Le rotte di pagina di fastapi-template (`createFileRoute`, 7, funzione `beforeLoad` anonima a 2-3 righe) e `/swagger/admin/*any` di go-admin (funzione sorella, non annidata) sono falsi positivi che la condizione «annidata nella funzione che copre la riga» esclude; non è provato che la condizione basti altrove.
- **Il limite che rende valida la 1:** vale solo se Noir dà un gestore con percorso e riga (`handler` non nullo); dove il gestore è nullo, Noir cita la riga della registrazione e la funzione che la copre è la funzione che registra. Controllo: la funzione più interna che copre la riga, senza guardare il nome (`innermost-covering`), darebbe una funzione a 321 endpoint senza gestore di Noir, ma sono **48 funzioni di registrazione** (`ApiRouter.InitApiRouter` per 20 rotte, `InitRouter` per tutte quelle di go-gin-example): sbagliate per costruzione.
- **Non correzioni.** `name-in-file` (il nome di una funzione unica nel file, senza guardare la riga): 209 come la 2, ma 21 righe già legate diventano ambigue. `name-in-project` (il nome è unico nel progetto): 127 unici e 274 ambigui sui non legati, 600 ambigui sulle 1.631 già legate: inutilizzabile.
- **Che cosa non è una correzione del legatore.** Gin: 237 su 385 endpoint senza gestore di Noir (nessun dato da confrontare). Laravel e Rails: l'adattatore non legge PHP né Ruby. DefectDojo: 50 endpoint citano l'intestazione di una classe (viewset): legarli alla classe esce dal contratto «una funzione».

### A livello di nodo (seconda misura, 24 novembre 2026)

`binder._position` non restituisce una dichiarazione: restituisce `facts.node(id)`, il simbolo che i link usano. `Facts.node` ripiega una funzione `(anonymous)` sulla funzione che la contiene (o sulla proprietà di cui è il valore), dà `None` a una funzione anonima senza proprietario con nome, e non distingue due dichiarazioni con lo stesso nome qualificato (le `(lambda)` di un metodo C#, i `(func)` di Go sono la stessa stringa). Una rotta legata a un nodo che molte rotte condividono porterebbe i passi di tutte: una prova falsa, non un legame. Misurato nel container (`nodes.py`), con la stessa copia del codice di Daodan:

1. `premap.write` con la risposta di Noir; `flows.Facts` costruito come lo costruisce `flows.link_facts`; `binder._position` sostituita nel processo di misura (non nel repository) con la regola di oggi e, per una riga la cui posizione è quella di `handler` e che la regola di oggi non lega, l'unica funzione che parte alla riga se il suo nodo non è `None`.
2. `flows.link_facts(manifest, [])` con la stessa sostituzione: le voci `rotta` di Noir hanno gli stessi nodi delle righe del legatore in 26 applicazioni su 26; da lì gli archi in uscita da ogni nodo (`chiama`, `attiva`).

Parole: un endpoint è su un nodo **proprio** se `facts.node(dichiarazione)` è il nome della dichiarazione (`facts.named`); è **ripiegato** se il nodo è un altro simbolo; è **senza nodo** se `None`; il nodo è **di una sola funzione** se nessun'altra funzione dello snapshot ha lo stesso nome qualificato. Una funzione che risponde a più rotte non è una collisione: è una dichiarazione.

Per applicazione («oggi»: le righe già legate; «nuovi»: le righe che la regola `starts-at-line` lega, 670 in tutto; «ripiegati»: su un nodo che non è la funzione trovata; «su nodo condiviso»: su un nodo che due o più dichiarazioni hanno in comune; le applicazioni senza righe legate né nuove, Laravel, Rails e go-gin-example, non sono in tabella):

| Applicazione | Oggi: legati | nodi | gruppo più grande (nodo) | su nodo condiviso | Nuovi | nodi | gruppo più grande (nodo) | senza nodo | ripiegati | su nodo condiviso | proprio e di una sola funzione |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gin-vue-admin | 0 | 0 | | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| go-admin | 0 | 0 | | 0 | 93 | 92 | 2 (`RegisterMonitorRouter.(func)`) | 0 | 0 | 2 | 91 |
| nestjs-boilerplate | 22 | 22 | 1 | 0 | 0 | | | | | | |
| nest-admin | 88 | 88 | 1 | 0 | 6 | 6 | 1 | 0 | 0 | 0 | 6 |
| nestjs-realworld | 21 | 21 | 1 | 0 | 0 | | | | | | |
| node-express-boilerplate | 0 | 0 | | 0 | 13 | 0 | | 13 | 0 | 0 | 0 |
| anything-llm | 4 | 2 | 2 (`downloadGeneratedFile`) | 0 | 350 | 42 | **57** (`system.js::systemEndpoints`) | 25 | 325 | 322 | 0 |
| juice-shop | 1 | 1 | 1 | 0 | 109 | 82 | 7 (`fileServer.ts::servePublicFiles`, una funzione) | 3 | 1 | 0 | 105 |
| litecast | 4 | 4 | 1 | 0 | 0 | | | | | | |
| uni-stack | 13 | 9 | 5 (`hello.ts::handler`, una funzione) | 0 | 2 | 0 | | 2 | 0 | 0 | 0 |
| expo-template | 15 | 15 | 1 | 0 | 0 | | | | | | |
| spring-petclinic | 17 | 17 | 1 | 0 | 0 | | | | | | |
| RuoYi | 304 | 300 | 2 | 6 | 0 | | | | | | |
| spring-petclinic-kotlin | 18 | 18 | 1 | 0 | 0 | | | | | | |
| eShopOnWeb | 25 | 21 | 2 | 8 | 7 | 7 | 1 | 0 | 0 | 0 | 7 |
| eShop | 37 | 34 | 2 | 6 | 9 | 4 | 4 (`WebHooksApi.MapWebHooksApiV1.(lambda)`) | 0 | 0 | 8 | 1 |
| healthchecks | 257 | 132 | 12 (`hc/api/views.py::ping`, una funzione) | 0 | 0 | | | | | | |
| DefectDojo | 492 | 250 | 8 (`DeletePreviewModelMixin.delete_preview`) | 0 | 80 | 52 | 4 (`ListOpenFindings.get`) | 3 | 0 | 0 | 77 |
| full-stack-fastapi-template | 23 | 23 | 1 | 0 | 0 | | | | | | |
| Dispatch | 290 | 290 | 1 | 0 | 0 | | | | | | |
| **Totale** | **1.631** | **1.247** | 12 | **20** | **670** | **286** | **57** | **46** | **326** | **332** | **288** |

Le righe già legate non sono mai ripiegate né senza nodo (0 su 1.631); le 20 su nodo condiviso sono sovraccarichi (RuoYi 6, eShopOnWeb 8, eShop 6: due metodi con lo stesso nome qualificato), già così oggi. Dei nodi dei 670, 155 hanno un arco in uscita nei link (contro 1.022 delle 1.631 già legate): molte chiamate non sono risolte dallo snapshot.

**Le classi dei 670**, per come finiscono sul nodo:

| Classe | Endpoint | Nodo | Esito |
| --- | --- | --- | --- |
| funzione con nome, nodo proprio e di una sola funzione: Gin `api.GetPage` (91), viste a classe di DefectDojo (77), `f()` di juice-shop (95), nome con oggetto davanti di juice-shop (10), nest-admin (6), una lambda o un `(func)` sola nel metodo (9) | 288 | proprio | legabile |
| closure `(anonymous)` di JavaScript e TypeScript che registrano le rotte (anything-llm, juice-shop) | 353 | ripiegato sulla funzione che le registra (326, di cui 322 su un nodo con più closure) o senza nodo (27) | **resta una lacuna**, salvo il nome della rotta (sotto) |
| funzione anonima di primo livello, che Noir nomina `ctrl.azione` o come procedura (node-express-boilerplate 13, uni-stack 2, DefectDojo 3, juice-shop 1) | 19 | senza nodo | **resta una lacuna**, salvo il nome della rotta |
| `(lambda)` o `(func)` sorelle nello stesso metodo (eShop 8, go-admin monitor 2) | 10 | proprio, ma lo stesso testo per più funzioni | **resta una lacuna** |

**Senza nodo, un legame rompe i link.** Una riga legata a una funzione senza nodo ha `symbol: None`; con un solo simbolo `None` fra le voci `flows.link_facts` fallisce (`TypeError: '<' not supported between instances of 'NoneType' and 'str'`, nell'ordinamento delle voci): è successo in anything-llm e juice-shop alla prima prova. La regola non lega una funzione il cui nodo è `None`; il legatore di oggi non ha il caso (0 righe su 1.631), perché lega solo funzioni con nome.

**Le fabbriche (domanda 4).** Per 6 dei 96 `f()` di juice-shop (`quantityCheckBeforeBasketItemUpdate`, `addBasketItem`, `getPaymentMethods`, `delPaymentMethodById`, `getPaymentMethodById`, `getDeliveryMethods`; letti dai link, senza regole) il nodo è la fabbrica, con nome proprio. La fabbrica non ha chiamate sue (`own_calls` 0): le chiamate del nodo (8, 14, 8, 5, 8, 7) sono quelle della funzione anonima che restituisce, che `Facts.node` ripiega sul nodo della fabbrica; in `getPaymentMethods` anche quelle di una funzione annidata nella prima (4 + 4). Gli archi in uscita dal nodo sono 2, 2, 0, 0, 0, 1 (`solveIf`, `parseJsonCustom`, `isDeluxe`: chiamate risolte; le altre non sono risolte dallo snapshot). Quindi il nodo porta il corpo del gestore vero: la funzione restituita non ha un nodo suo, e nessun dato di Noir la lega (Noir cita la fabbrica); la lega il ripiegamento dello snapshot. Un limite: due closure annidate più in basso (`(anonymous).(anonymous)`) hanno nodo `None`, e le loro chiamate vanno al livello del modulo, non alla fabbrica. 95 dei 96 sono su un nodo proprio e di una sola funzione; 1 è senza nodo.

**Le closure di anything-llm e `api.GetPage` di Gin (domanda 5).**

- anything-llm: il nodo è la funzione che registra (per `collector/extensions/index.js`, `extensions`): 85 chiamate da 10 dichiarazioni, 7-13 delle quali sono quelle di una closure. La rotta `GET /agent-skills/filesystem-agent/is-available` (righe 24-36 di `agentSkillWhitelist.js`) sul nodo `agentSkillWhitelistEndpoints` porta un arco verso `isCustomSkillsAndMcpAvailable` il cui sito è la riga 81, che è di un'altra closure: **una prova falsa**; 57 rotte stanno su `systemEndpoints`.
- Gin `api.GetPage` e simili (go-admin, 5 letti più 3 con archi): nodo proprio (`SysApi.GetPage`), una sola dichiarazione che chiama dentro il nodo, le sue chiamate (15, 11, 12, 12, 11), nessun'altra. Gli archi risolti sono pochi (4 dei 91 nodi hanno almeno un arco, perché lo snapshot non risolve le chiamate sui metodi di `e`): `Gen.Preview` (righe 50-166) ha archi verso `parseGenTemplate` (siti 107, 113) e `renderAll` (148), `SysTable.Insert` (158-202) verso `genTableInit` (180) e `tablesToImport` (168), `LogOut` (156-163) verso `LoginLogToDB` (157): tutti dentro il corpo della funzione.

**Il nome della rotta come nome della funzione anonima.** I link danno già un nome a una funzione scritta sul posto come gestore (`Facts.route_named`: `GET /percorso`, nodo proprio, e le funzioni annidate vi si ripiegano). Se il legatore lo facesse per le 372 funzioni `(anonymous)` che la regola trova, prima di chiedere il nodo: **372 nodi, 0 su un nodo di due o più rotte, 0 senza nodo**, e `flows.link_facts` regge (anything-llm: 354 voci di Noir e 352 simboli distinti, contro 329 voci prima: le 25 senza nodo diventano rotte). Gli archi in uscita sono dentro la closure (esempio: `POST /v1/workspace/:slug/vector-search`, riga 902, verso `parseSimilarityThreshold` e `parseTopN`, siti 1003 e 1004; `GET /agent-skills/custom-skills-and-mcp/is-available`, riga 77, verso `isCustomSkillsAndMcpAvailable`, sito 81). Solo 9 dei 372 hanno un arco in uscita, perché le chiamate sono per lo più non risolte: il nodo è giusto, non è più ricco. Misurato in anything-llm, node-express-boilerplate, juice-shop, uni-stack e DefectDojo; **non provato** per le `(lambda)` e i `(func)` sorelle (le 10 collisioni).

**Una regola o quattro (domanda 2).** Le correzioni 2, 3 e 4 non sono un sottoinsieme della 1 per 7 righe, tutte di juice-shop, dove la 1 è ambigua (la funzione che costruisce il gestore e quella anonima che restituisce partono alla stessa riga) e il nome sceglie la fabbrica. Il resto è dentro la 1. Esatti, sui 677 non legati con una discordanza:

| Regione | Endpoint |
| --- | --- |
| solo 1 | 391 |
| 1 e 2 (non 3, non 4) | 115 |
| 1, 2 e 3 | 87 |
| 1 e 4 (non 2, non 3) | 77 |
| 2, 3 e 4 (non 1) | 4 |
| solo 2 | 3 |
| solo 3, solo 4, ogni altra combinazione | 0 |
| **unione** | **677** |

La 1 ha 670; le 7 mancanti hanno le funzioni candidate (2) sullo stesso nodo (7 su 7): una regola a livello di nodo («tutte le funzioni che partono alla riga finiscono sullo stesso nodo: lega quel nodo») le lega e **l'unione coincide con la 1**. Dove la 1 e un'altra correzione danno entrambe una funzione, è la stessa (279 righe su 279).

**La posizione viene dal gestore (domanda 3).** Delle 670, 670 hanno la posizione di `handler`: `noir.rows` legge il nome solo se la posizione è quella del gestore, e la regola vale solo per righe con un nome. Delle 1.044 righe senza nome e senza `handler.path`, che usano `code_paths[0]` (la riga della registrazione), la regola con la guardia ne lega 0; senza la guardia ne legherebbe 8 (6 `/health` di gin-vue-admin, `/robots.txt` di DefectDojo, `/infrastructure` di juice-shop: non letti). Nei dati non c'è nessuna riga con `handler.path` e nome nullo, quindi oggi «nome non nullo» e «posizione del gestore» coincidono, ma non è garantito. La riga di `noir.rows` oggi non dice da dove viene la posizione quando il nome è nullo: dovrebbe portare **un campo, per esempio `"position": "handler"` oppure `"code_paths"`**, che `noir.rows` conosce già (`where is handler`); la regola si applicherebbe solo a `"handler"`.

**Raccomandazione, una regola.** *`handler.line` di Noir (posizione presa da `handler`, mai da `code_paths`) = `line` dell'unica funzione di `handler.path` che parte a quella riga (o delle funzioni che partono a quella riga e finiscono sullo stesso nodo), il cui nodo, `facts.node`, è proprio: o è una funzione con nome, sola del suo nome qualificato, o è anonima e prende il nome della rotta (`METHOD path` di Noir) come `Facts.route_named`.* Misurata: 660 dei 670 su un nodo proprio, **0 su un nodo di due o più rotte, 0 senza nodo**, 0 delle 1.631 righe già legate cambiate; più i 7 ambigui a livello di nodo. **Restano lacune:** le `(lambda)` e i `(func)` sorelle nello stesso metodo (10: eShop 8, go-admin monitor 2) finché non hanno un nome per rotta; i 389 endpoint senza gestore di Noir (237 Gin); le 96 fabbriche, da decidere (si legano a una funzione che costruisce il gestore e non è il gestore: la funzione restituita non ha un nodo suo). Senza il nome della rotta la regola lega 288: i restanti 382 (326 ripiegati, 46 senza nodo, 10 collisioni) restano lacune, e **sono le closure di Express, le funzioni anonime di primo livello e le sorelle di C# e Go**.

## Dopo la correzione (24 novembre 2026, seconda versione del legatore)

Il legatore è cambiato dopo una review (le legature false sono tolte): per una riga di Noir con un nome, oltre alla riga conta che **il nome concordi** con la funzione che parte a quella riga (`binder._placed`, `_started`, `_agrees`, `_name_handlers`; `flows.bind_declared`). Prima il nome per posizione, invariato; altrimenti l'unica funzione che parte alla riga citata (se più funzioni partono lì, quella che nessun'altra tiene per estensione; più funzioni esterne sono una lacuna), purché il nome concordi: stesso nome o nome qualificato; la parte dopo l'ultimo punto uguale (`api.GetPage` per `SysApi.GetPage`); la classe che la possiede; `x.f()` per una fabbrica `f` le cui funzioni interne si ripiegano tutte in essa; una funzione senza nome accetta ogni nome. Il campo `position` non c'è più: una riga senza nome non si lega mai per posizione. Rifatta la misura sulle 25 applicazioni (più `shhh`) con **la copia congelata `D:\daodan-work\final-code\daodan`** (non l'albero vivo), senza sostituire nulla: `modal_binding.py --mode after` (`after.py`: `premap.write` con la risposta di Noir, `flows.bind_declared` su tutte le righe, un secondo `flows.Facts` intatto, poi `flows.link_facts(manifest, [])` così com'è) e `summarize_after.py` (`results/after.json`). Impronte della copia (1059 file di `core` e `data`, sha256 complessivo `625bba1e3227133e…`, rilevate alle 07:43 del 24 novembre): `binder.py` `ffc1518965192abd`, `flows.py` `b8fa8057fd9e2712`, `premap/noir.py` `b4ab1ae505c13e74`, `entries.py` `bc8eb540d3d7d374`, `languages/semantic.py` `9b5311b23f354c83`, `edge_view.py` `32636f764bf7a6b5`, `snapshot.py` `ad51da178e49e16c` (`results/after.json`, campo `fingerprints`). Con un altro legatore la prova va rifatta con una nuova copia.

**In una riga:** legati **1.631 prima, 2.308 con la prima correzione, 2.297 ora su 3.994** (666 per posizione: 391 con una funzione senza nome, 107 con il nome dopo l'ultimo punto, 91 fabbriche, 77 classi; **11 in meno della prima correzione, tutti di juice-shop e tutti fabbriche**); i nodi distinti da 1.247 a 1.858; **0 delle 1.631 righe già legate ha cambiato simbolo**; `flows.link_facts` costruisce in 26 applicazioni su 26; **0 archi in uscita dai nodi dei nuovi legati fuori dalle righe della funzione legata** (269 archi su 117 endpoint). Il nome non ha negato nessuna legatura in queste 25 applicazioni: la causa «Noir names X, the function at the line is Y» non si presenta mai.

Per applicazione (endpoint `http`; prima = per nome, come oggi; dopo la prima correzione = i legati della misura di prima; ora; nuovi = per posizione; nodi distinti fra i legati; gruppo più grande di endpoint su un nodo fra i nuovi; persi = legati dalla prima correzione e non da questa):

| Applicazione | http | prima | prima correzione | ora | nuovi | nodi | gruppo più grande dei nuovi | persi | non legati |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bookstack | 345 | 0 | 0 | 0 | 0 | 0 → 0 |  | 0 | 345 |
| koel | 339 | 0 | 0 | 0 | 0 | 0 → 0 |  | 0 | 339 |
| rubygems | 12 | 0 | 0 | 0 | 0 | 0 → 0 |  | 0 | 12 |
| lobsters | 8 | 0 | 0 | 0 | 0 | 0 → 0 |  | 0 | 8 |
| gin-vue-admin | 217 | 0 | 1 | 1 | 1 | 0 → 1 | 1 | 0 | 216 |
| go-admin | 139 | 0 | 93 | 93 | 93 | 0 → 93 | 1 | 0 | 46 |
| go-gin-example | 29 | 0 | 0 | 0 | 0 | 0 → 0 |  | 0 | 29 |
| nestjs-boilerplate | 22 | 22 | 22 | 22 | 0 | 22 → 22 |  | 0 | 0 |
| nest-admin | 94 | 88 | 94 | 94 | 6 | 88 → 94 | 1 | 0 | 0 |
| nestjs-realworld | 40 | 21 | 21 | 21 | 0 | 21 → 21 |  | 0 | 19 |
| node-express-boilerplate | 15 | 0 | 13 | 13 | 13 | 0 → 13 | 1 | 0 | 2 |
| anything-llm | 424 | 4 | 354 | 354 | 350 | 2 → 340 | 7 (`DELETE /*`, 1 funzione) | 0 | 70 |
| juice-shop | 188 | 1 | 117 | 106 | 105 | 1 → 88 | 7 (`serveQuarantineFiles`, 1 funzione) | 11 | 82 |
| litecast | 5 | 4 | 4 | 4 | 0 | 4 → 4 |  | 0 | 1 |
| uni-stack | 15 | 13 | 15 | 15 | 2 | 9 → 11 | 1 | 0 | 0 |
| expo-template | 16 | 15 | 15 | 15 | 0 | 15 → 15 |  | 0 | 1 |
| petclinic | 32 | 17 | 17 | 17 | 0 | 17 → 17 |  | 0 | 15 |
| ruoyi | 441 | 304 | 304 | 304 | 0 | 300 → 300 |  | 0 | 137 |
| petclinic-kotlin | 33 | 18 | 18 | 18 | 0 | 18 → 18 |  | 0 | 15 |
| eshoponweb | 54 | 25 | 32 | 32 | 7 | 21 → 28 | 1 | 0 | 22 |
| eshop | 61 | 37 | 46 | 46 | 9 | 34 → 43 | 1 | 0 | 15 |
| healthchecks | 258 | 257 | 257 | 257 | 0 | 132 → 132 |  | 0 | 1 |
| defectdojo | 678 | 492 | 572 | 572 | 80 | 250 → 305 | 4 (`ListOpenFindings.get`, 1 funzione) | 0 | 106 |
| fastapi-template | 31 | 23 | 23 | 23 | 0 | 23 → 23 |  | 0 | 8 |
| dispatch | 498 | 290 | 290 | 290 | 0 | 290 → 290 |  | 0 | 208 |
| **Totale (25)** | **3.994** | **1.631** | **2.308** | **2.297** | **666** | **1.247 → 1.858** | **7** (`serveQuarantineFiles`, 1 funzione) | **11** | **1.697** |

(Laravel, Rails e go-gin-example non hanno righe legate; shhh, la taratura, ha 6 su 6 come prima. Il gruppo più grande dei nuovi, 7 endpoint, è **una sola funzione** che risponde a sette metodi, uno per metodo: `serveQuarantineFiles()` in juice-shop, e in anything-llm le due `app.all("/*")` di `collector/index.js` e `server/index.js`. Il gruppo più grande fra tutti i legati resta quello di prima: 12 endpoint di `hc/api/views.py::ping`, una funzione. Gli endpoint su un nodo di due o più funzioni sono ancora i sovraccarichi di prima: RuoYi, eShopOnWeb, eShop.)

**Persi rispetto alla prima correzione: 11 endpoint, una sola causa.** «Noir names `f()`, a function that builds the handler: the one it returns is not folded into `f`» (la fabbrica è legata solo se *tutte* le funzioni scritte dentro di lei si ripiegano in lei): juice-shop, 5 fabbriche. Dalla misura, per ognuna, le funzioni scritte direttamente dentro:

| Fabbrica (righe) | Endpoint persi | Dentro: la funzione restituita | Dentro: funzioni con nome che non si ripiegano |
| --- | --- | --- | --- |
| `servePublicFiles()` (13-59) | 7 (`/ftp/:file`, ogni metodo) | `(anonymous)` 14-23, ripiegata | `verify`, `verifySuccessfulPoisonNullByteExploit`, `endsWithAllowlistedFileType` |
| `login()` (18-83) | 1 (`POST /rest/user/login`) | `(anonymous)` 32-55, ripiegata | `afterLogin`, `verifyPreLoginChallenges`, `verifyPostLoginChallenges` |
| `getLanguageList()` (12-90) | 1 (`GET /rest/languages`) | `(anonymous)` 13-78, ripiegata | `calcPercentage` |
| `b2bOrder()` (16-47) | 1 (`POST /b2b/v2/orders`) | `(anonymous)` 17-38, ripiegata | `uniqueOrderNumber`, `dateTwoWeeksFromNow` |
| `promotionVideo()` (50-78) | 1 (`GET /promotion`) | `(anonymous)` 51-74, ripiegata | `favicon` |

Giudizio dai dati: **è un gestore vero perso, non una legatura falsa evitata.** Il nome di Noir (`f()`) e la riga concordano con la fabbrica; la funzione restituita (`(anonymous)`) è ripiegata nel nodo, che ne porta le chiamate; le funzioni con nome sono nodi propri, raggiunti da un arco di chiamata (nella misura precedente gli archi di questi cinque nodi erano tutti dentro le righe della fabbrica, 0 fuori: per esempio `servePublicFiles` → `servePublicFiles.verify`, `promotionVideo` → `promotionVideo.favicon`). Il controllo è conservativo: costa 11 endpoint su 677 (1,6 %). Gli altri 91 endpoint di fabbrica di juice-shop, le cui funzioni scritte dentro si ripiegano tutte, restano legati.

**Non legati ora: 1.697.** «null handler» 1.044 (Noir non dà il gestore, e senza nome una riga non si lega mai per posizione); «no function starts at the line» 642 (629 `.php`, che lo snapshot non legge, 10 `.cshtml`/`.razor`, 3 risposte del framework in C#); «a function that builds the handler, not folded» 11. Le cause che il legatore sa dire e che non si presentano in nessuna delle 25 applicazioni: «Noir names X, the function at the line is Y», «several functions start at the line and none holds the others», «folded into», «anonymous and its route is another function's», «shares its node», «has no node»: **0** righe ciascuna.

**Le 1.631 già legate.** 0 con il simbolo cambiato, in due confronti: con un secondo `Facts` intatto (nessuna funzione nominata dalla rotta) e con i nodi della misura precedente (righe raccontate dal sito del gestore, dal metodo, dal percorso e dal nome: l'ordine delle righe di Noir cambia da una prova all'altra, in uni-stack per i moduli tRPC). Nessuna è tornata non legata.

**I link.** `flows.link_facts(manifest, [])` costruisce senza errori in 26 applicazioni su 26, e le voci `rotta` di Noir hanno gli stessi simboli delle righe del legatore in tutte. **Gli archi** dei nuovi legati: 117 endpoint con almeno un arco in uscita, 269 archi, **0 fuori dalle righe della funzione legata** (per le 1.631 di prima: 1.022 righe, 3.064 archi, 10 fuori in 9 righe, i sovraccarichi).

### I tre dubbi (misurati su 391 endpoint legati per posizione a una funzione senza nome)

Per ognuno, dalle estensioni dello snapshot e dall'albero sintattico della funzione legata (tutti gli alberi letti: 0 non letti); il testo dei sorgenti non è servito.

1. **Una funzione senza nome legata mentre la riga citata ha prima un middleware o un guard, o è la prima di un array di gestori: non si presenta, 0 su 391.** La funzione legata è l'ultimo argomento della sua chiamata in 390 casi su 391 (gli altri: `export default` di una funzione, 1: `routes/authenticatedUsers.ts:37` di juice-shop); è uno fra più argomenti in 375 casi e **nessun argomento prima di lei contiene una funzione** (i guard sono nomi o chiamate senza funzione, `[validatedRequest]`, `flexUserRoleValid([...])`); è l'unico argomento in 15; nessuna è un elemento di un array (0), e nessun argomento *dopo* di lei contiene una funzione (0). Nessun'altra funzione parte alla sua riga (391 su 391); dove due funzioni partirebbero alla stessa riga senza che una tenga l'altra (un guard e un gestore sulla stessa riga) il legatore dà lacuna, e nessuna riga ha quella causa.
2. **Un registrar anonimo sulla stessa riga della closure che registra, legato come se fosse il gestore: non si presenta, 0.** Per nessuna delle 391 funzioni legate un'altra funzione parte alla sua riga (0 tengono una funzione che parte alla loro riga: la regola «la più esterna» non ha mai scelto fra due). Nessun caso nei dati: `module.exports = (app) => app.get(...)` non è fra queste applicazioni.
3. **Due endpoint di metodi diversi legati a una funzione senza nome per cui Noir cita la stessa riga: 2 funzioni, 14 endpoint, e sono una funzione sola.** Sono le due `app.all("/*", ...)` di anything-llm (`collector/index.js:221`, `server/index.js:192`): `all` risponde a ogni metodo, Noir scrive un endpoint per metodo (DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT) con la stessa riga di dichiarazione e di registrazione, e la funzione legata è l'argomento della chiamata `all`. Nessuna catena `.get(...).post(...)`: nessuna funzione senza nome è legata a due endpoint di metodi diversi in nessun altro caso.

Dieci nuovi endpoint scelti a caso (seme 24) fra quelli con un arco in uscita, Express, Gin, C# e DefectDojo; fino a tre archi per ciascuno, con il sito, e se cade dentro le righe della funzione legata:

| Gruppo | Applicazione | Rotta | Gestore di Noir | Nodo (righe della funzione) | Archi | Primi archi (a funzione, sito) |
| --- | --- | --- | --- | --- | --- | --- |
| Express | juice-shop | GET /rest/repeat-notification | `repeatNotification()` | `repeatNotification` (9-20) | 2 | `findChallengeByName` a repeatNotification.ts:12 (dentro); `sendNotification` a repeatNotification.ts:15 (dentro) |
| Express | juice-shop | POST /rest/2fa/disable | `twoFactorAuth.disable` | `disable` (142-170) | 2 | `hash` a 2fa.ts:152 (dentro); `queryResultToJson` a 2fa.ts:164 (dentro) |
| Express | juice-shop | PUT /rest/continue-code-fixIt/apply/:con | `restoreProgress.restoreProgres` | `restoreProgressFixIt` (61-80) | 1 | `solveFixIt` a restoreProgress.ts:72 (dentro) |
| Gin | go-admin | GET /api/v1/server-monitor | `api.ServerInfo` | `ServerMonitor.ServerInfo` (46-70) | 7 | `GetHourDiffer` a sys_server_monitor.go:68 (dentro); `getCPUInfo` a sys_server_monitor.go:52 (dentro); `getDiskInfo` a sys_server_monitor.go:53 (dentro) |
| Gin | go-admin | POST /api/v1/logout | `handler.LogOut` | `LogOut` (156-163) | 1 | `LoginLogToDB` a auth.go:157 (dentro) |
| C# | eshoponweb | GET /api/catalog-brands | `closure` | `GET /api/catalog-brands` (28-31) | 1 | `CatalogBrandListEndpoint.HandleAsync` a CatalogBrandListEndpoint.cs:30 (dentro) |
| C# | eshoponweb | GET /api/catalog-types | `closure` | `GET /api/catalog-types` (28-31) | 1 | `CatalogTypeListEndpoint.HandleAsync` a CatalogTypeListEndpoint.cs:30 (dentro) |
| DefectDojo | defectdojo | POST /product/{product_id}/import_scan_re | `ImportScanResultsView` | `ImportScanResultsView.post` (1063-1103) | 4 | `add_error_message_to_response` a views.py:1080 (dentro); `add_error_message_to_response` a views.py:1084 (dentro); `add_error_message_to_response` a views.py:1088 (dentro) |
| DefectDojo | defectdojo | POST /jira/advanced | `AdvancedJiraView` | `AdvancedJiraView.post` (437-466) | 3 | `user_has_configuration_permission` a views.py:438 (dentro); `get_jira_connection_raw` a views.py:448 (dentro); `create_notification` a views.py:458 (dentro) |
| DefectDojo | defectdojo | POST /jira/{tid}/delete | `DeleteJiraView` | `DeleteJiraView.post` (563-599) | 5 | `user_has_configuration_permission` a views.py:564 (dentro); `create_notification` a views.py:577 (dentro); `add_breadcrumb` a views.py:593 (dentro) |

**Rispetto alle misure precedenti:** i 670 recuperabili e i 660 su nodo proprio restano veri (le 677 funzioni trovate dal dato `handler.line` sono ora 666 legate, perché 11 fabbriche sono rifiutate da un controllo più prudente); nessuna contraddizione. Nei dati il nome non ha mai disconfermato una posizione: le 666 sono tutte concordanti.

## Difetti del legatore (T1.C.6, 28 novembre 2026)

Quattro difetti del legatore ([piano](../../docs/plans/refactoring.md), passo `T1.C.6`), corretti o fissati:

- **(a) Una funzione senza nome dentro un gestore nominato dalla rotta si ripiega nel suo nodo.** `Facts.folds` ripiegava solo `(anonymous)`; ora anche gli altri `NAMELESS` (`(lambda)` di C# e Python, `(func)` di Go, `(closure)`), ma solo quando una funzione che li contiene è in `route_named`: le chiamate di `go func() { a() }()` dentro la closure di `GET /health` sono di `GET /health`, non di un nodo `Register.(func).(func)` di tutte le rotte. Le altre lambda tengono il loro nodo, come nel resto del grafo.
- **(b) Più funzioni alla riga citata.** La regola «la più esterna» resta solo dove quella ha un nome, che deve concordare con quello di Noir (le 7 fabbriche di juice-shop `const f = () => (req, res) => …`, `f()`). Dove la più esterna è scritta senza nome (prende qualunque nome, `_agrees`) la riga è una lacuna, «several functions start at the line»: un registratore anonimo (`export default (app) => app.get(…, (req, res) => …)`) non è mai legato come gestore. Togliere la regola del tutto, come diceva il piano, faceva perdere quelle 7 fabbriche legate giuste (misurato in una prima corsa: juice-shop da 106 a 99 legate, «several functions start at the line»).
- **(c) `export default` di una funzione senza nome.** Lo snapshot non ne registra l'esportazione e lo annota (`semantic.ANONYMOUS_DEFAULT`); `binder._exports` dà la lacuna «default: anonymous default export is unresolved» invece di far sparire la riga (con `exports_optional` o accanto a un'altra esportazione legata). Le sorgenti con `exports` (Next.js, Nuxt, React Router, SvelteKit) non sono in questa misura, che è di Noir: provato dai test.
- **(d) Una funzione senza nome legata con qualunque nome** resta com'è (0 su 391, «I tre dubbi», 1), fissata da un test.

**Misura** (Modal, 26 applicazioni di `apps.py` senza btcpayserver, Noir 1.5.0; corse `after` `ap-acf7eMgC6OisNqbMaa7IcC` e `ap-xlcTguZYkTEbasYXodWCYG` col legatore di `98a01c1`, `ap-veAExmOH8NGOIQWF77O1o9` con quello di questo passo; `compare_after.py`, `results/t1c6.json`):

| | Righe HTTP | Legate prima | Legate ora | Simbolo cambiato | Perse | Nuove | Righe senza nome legate per posizione | Archi in uscita | Fuori dalle righe del gestore |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Totale** | 4.000 | 2.303 | 2.301 | **0** (di cui 0 delle 1.637 legate per nome) | **0** | 0 | 389 | 24 → 24 | **0 → 0** |

Le 2 legate in meno e le 3 righe «mancanti» non sono del legatore: Noir scrive un ordine diverso fra due corse (uni-stack: le rotte tRPC di `with-tamagui` o di `with-nativewind`; fastapi-template: `compose.yml` o `compose.deploy.yml`), come già notato sopra. Le 11 «sorelle» di eShop (9) e go-admin (2) sono legate a un nodo proprio prima e dopo, con **0 archi**: lo snapshot non risolve nessuna chiamata dentro di loro, quindi (a) non cambia nulla qui e il ripiegamento è provato solo dai test. `flows.link_facts` costruisce in 26 su 26, con gli stessi simboli delle righe del legatore. La corsa di `modal_binding.py` (prova, `ap-AsZPrWP5Qo0LmUlofRnVTj`) con il legatore di questo passo dà **2.297 legati su 3.994**, come «Dopo la correzione»; i `results/<app>.json` restano quelli del 24 novembre (il legatore di allora).

## Laravel e Rails: il comando ufficiale, e che cosa manca a Noir

Il comando (letto il 23 novembre, senza eseguire nulla: [laravel-routes](../laravel-routes/README.md), [rails-routes](../rails-routes/README.md)):

- **Laravel:** `php artisan route:list` (documentato, opzioni `-v`, `-vv`, `--path`, `--except-vendor`, `--only-vendor`); `--json` è nel codice di `RouteListCommand` ma non in `routing.md`. Per rotta: `domain`, `method`, `uri`, `name`, `action` (`App\Http\Controllers\X@metodo`, `X@__invoke`, `Closure`), `middleware`; `path` (`file:riga`) solo per le closure. Carica l'intera applicazione.
- **Rails:** `bin/rails routes` (documentato; `-c/--controller`, `-g/--grep`, `-E/--expanded`, `--unused`); **nessuna uscita per le macchine** (tabella o vista verticale); per rotta `Prefix`, `Verb`, `URI`, `Controller#Action`, e con `-E` la riga di `config/routes.rb` solo in sviluppo; carica l'applicazione.

Che cosa hanno i dati di Noir (quattro applicazioni, 685 + 501 endpoint `http` del report):

| | Laravel (BookStack + koel) | Rails (rubygems.org + Lobsters) |
| --- | --- | --- |
| endpoint `http` nel report | 685 | 501 |
| gestore `Classe@azione` / `controller#azione`, con file e riga **del controller** | 624 (91 %) | 441 (88 %) |
| closure con file e riga | 5 (`route:list` dà `Closure` e `file:riga`: lo stesso) | 0 |
| senza gestore | 56: 18 solo dalla specifica `api-docs/api.yaml` (etichetta `spec-only`), 34 in file di rotte (`routes/api.base.php` 30, `routes/web.php` 3, `routes/web.base.php` 1), 4 altri (`public/index.php` 2, `bootstrap/app.php`, `_redirects`) | 60: 37 in `config/routes.rb` (reindirizzamenti, motori montati, `to:` con lambda: `bin/rails routes` darebbe `Redirect` o il nome del motore, non un controller), 23 file di `public/` |

Quindi `route:list` aggiungerebbe controller e azione a una trentina di rotte (34, 5 %) e il nome pieno della classe (Noir dà il nome del file), e `bin/rails routes` quasi nulla (gli stessi `controller#azione`). **Mancano a Noir meno dati di quanti ne manchino a Daodan per usarli:** i 624 e i 441 hanno già il file e la riga del controller, ma lo snapshot non ha dichiarazioni PHP né Ruby (`.php` è nell'inventario come file di stack, senza lingua; nessun `.rb` è nell'inventario: i 478 endpoint con un `.rb` sono scartati da `noir.read` come «file fuori dallo snapshot»). Eseguire il framework non cambia questo.

## Per il piano

- **14d Laravel:** su BookStack e koel (MIT) Noir dà 685 endpoint `http`, 624 con `Classe@azione` più file e riga del controller e 5 closure con file e riga (quanto darebbe `route:list`), 56 senza gestore (18 solo da `api-docs/api.yaml`, 34 in file di rotte); **0 su 684 si legano**, perché i `.php` sono nell'inventario dello snapshot senza lingua né dichiarazioni. `route:list` aggiungerebbe controller e azione a 34 rotte e non una funzione legabile: eseguire il framework non serve finché Daodan non legge PHP (un lettore tree-sitter di PHP e delle sue dichiarazioni, `Classe.metodo`, prima di `route:list`).
- **14e Rails:** su rubygems.org e Lobsters (MIT, BSD) Noir dà 501 endpoint, 441 con `controller#azione` più file e riga del controller; **481 su 501 non arrivano al legatore** (478 sono `.rb`: nessun `.rb` è nell'inventario dello snapshot) e i 20 che arrivano sono file statici. `bin/rails routes` darebbe gli stessi `controller#azione` e nessun file e riga fuori dallo sviluppo: non aggiunge dati. Il limite è che lo snapshot non ha file né dichiarazioni Ruby.
- **14g Gin:** su gin-vue-admin, go-admin, go-gin-example (Apache-2.0, MIT) Noir dà 385 endpoint `http`: per **237 non dà il gestore** (cita la riga della registrazione dentro `InitApiRouter` o `InitRouter`, che non è il gestore); per 94 lo dà (91 con una variabile davanti, `api.GetPage`, `e.Get`; 3 closure), e lo snapshot ha `SysApi.GetPage` alla riga citata: l'ultimo identificatore del nome più la riga ne lega **91 su 91, e 94 su 94 con la riga della definizione** (`starts-at-line`), 0 errati nei 9 letti. Restano i 237: nessun dato di Noir da confrontare, e la funzione che copre la riga è quella che registra (48 funzioni di registrazione per 321 endpoint senza gestore, sbagliate). `(*Engine).Routes()` di 14g dà il gestore proprio dove Noir non lo dà: è la parte che vale misurare.
- **14h NestJS:** su nestjs-boilerplate, nest-admin e nestjs-realworld (MIT) Noir dà 156 endpoint `http`, 137 con nome e riga del metodo; **131 su 137 si legano**; 6 (nest-admin, `BaseController.list` con la classe dentro `BaseCrudFactory`) si legano con la fine del nome qualificato; 19 vengono da una collezione Postman (`e2e/*.postman_collection.json`, nessuna riga). Noir basta; `SwaggerModule.createDocument` darebbe di più solo per le rotte che Noir non vede, non per il legame.
- **14i Expo Router:** Noir legge solo i moduli `+api` (le schermate non sono endpoint); su litecast, uni-stack, expo-template (MIT) dà 36 endpoint, 34 con nome, **32 si legano**; 2 sono procedure tRPC (`health`, `firstPost`) che lo snapshot ha come funzioni anonime alle righe citate. Le rotte delle schermate (il file `app/…`) non sono nel report di Noir: non misurate. Prova piccola: 36 endpoint.
- **14j Express:** su node-express-boilerplate, anything-llm e juice-shop (MIT) Noir dà 627 endpoint `http`, 484 con nome (353 sono `closure`): **solo 5 si legano**, ma **479 sono discordanze di nome o di riga**, risolte da `handler.line` (un'unica funzione parte alla riga: una funzione anonima) o dall'ultimo identificatore: 0 funzioni di un altro gestore in 20 campioni letti (anything-llm 8, node-express-boilerplate 4, juice-shop 8), ma **102 di quei legami sono alla funzione che costruisce il gestore** (`chat()`, in juice-shop). Ne restano 45 senza gestore e 98 senza funzione nello snapshot. Dove i 5 legati sono l'unico confronto, la prova è il campione.
- **Spring (14f), Django (14b), FastAPI (14a):** dove Noir nomina il gestore il legatore lega il 100 % (Spring Java 321 su 321, Kotlin 18 su 18, FastAPI 313 su 313, healthchecks 257 su 257); in DefectDojo 492 su 572, e gli 80 che mancano sono 77 viste a classe che Noir nomina con la classe e 3 closure di un `.js` di test (correzioni 4 e 1). I non legati di queste applicazioni sono file statici, `pom.xml`, `.yaml` di specifica, `urls.py`, e in DefectDojo 50 intestazioni di classe di viewset e 39 decoratori: non sono funzioni dichiarate.
- **ASP.NET Core:** eShopOnWeb e eShop: 62 su 91 nominati si legano; i 16 che non si legano sono closure delle API minime con una funzione che parte alla riga citata (correzione 1; anche con l'attributo sulla stessa riga); 33 sono `.cshtml`/`.razor` (il gestore è in un blocco `@code`, lo snapshot ha il file come `markup`).

## Non coperto

- **btcpayserver** (`btcpayserver/btcpayserver`, MIT, commit `da4b5935c160`, controller MVC) è in `apps.py` come terza applicazione ASP.NET Core e **non è nei conteggi**: il suo snapshot non è finito in un'ora (il registro mostra la lettura dei file SQL, «contains unsupported syntax … Falling back to parsing as a 'Command'», e poi nulla) (`FunctionTimeoutError` del limite di 3.600 s; nessuna risposta di Noir né del legatore, perché la funzione le dà dopo lo snapshot: `results/btcpayserver.json` ha solo la causa). Non è indagato dove stia il tempo.
- **Le applicazioni sono scelte, non campionate**, e a un commit solo; Noir 1.5.0 solo. Un'applicazione diversa può avere un'altra forma di gestore: le correzioni sono dati, non regole di framework, ma i 670 sono misurati su queste 25.
- **Che il legame sia giusto è verificato in due modi:** le 1.631 righe già legate danno la stessa funzione con ogni correzione (0 diverse; per Express e Gin sono 5 e 0), e 59 endpoint non legati sono stati letti a occhio. Gli altri non sono verificati uno per uno: sono giusti per costruzione dei dati di Noir (la riga che cita è dove parte una funzione). Non è misurato se il metodo e il percorso di Noir siano giusti: solo se il gestore si lega.
- **Le rotte che Noir non vede** (prefissi dinamici, `Route::resource` non espanso, rotte dei pacchetti): non misurate; non c'è un secondo elenco (il framework) da confrontare, perché nulla è eseguito.
- **PHP e Ruby:** il legatore non ha nulla da confrontare (nessuna dichiarazione): si conta quanti endpoint portano nome, file e riga (624 e 441), non quanti si legherebbero. Con un lettore PHP o Ruby il confronto va rifatto: per Rails il nome è `articles#show` e la dichiarazione `ArticlesController.show`, una forma che nessuna delle correzioni sopra copre; per Laravel `ArticleController@show` ha lo stesso problema.
- **Expo Router:** solo i moduli `+api`; le tre applicazioni hanno 4-6 moduli ciascuna (36 endpoint in tutto). Le schermate non sono nel report.
- **Python 3.12 dell'immagine:** i file con una sintassi più nuova sono letti da Daodan con un altro Python che scarica (nel container senza rete non c'è: il registro dello snapshot riporta `installing uv … (first use)`); l'effetto sui conteggi non è misurato (i 5 `.py` senza funzioni sono file di rotte).
- **Il livello del nodo** è misurato con la stessa copia del codice di Daodan e con Noir 1.5.0. Il nome della rotta come nome della funzione anonima è provato nei link in 5 applicazioni (anything-llm, node-express-boilerplate, juice-shop, uni-stack, DefectDojo), non per le `(lambda)` e i `(func)` sorelle; un percorso duplicato nello stesso file (stesso metodo e percorso) darebbe lo stesso nodo a due rotte: nei dati non c'è. I nodi di fabbrica e quelli di Gin sono letti dai link, non verificati a mano uno per uno.
- **Il legatore misurato non è in commit** (`binder.py`, `flows.py`, `edge_view.py` e `languages/semantic.py` dell'albero di lavoro del 24 novembre sono modificati rispetto a `HEAD`): i conteggi valgono per quei file (impronte nei `results/`); la taratura su `shhh` (6 su 6) conferma che il confronto con `qualified_name` è attivo.
- **Il ritorno dei risultati da Modal:** una chiamata con la rete bloccata non può restituire più di circa 8 KB; la risposta è un generatore di pezzi di 6.000 byte (`modal_binding.py`).
- **Dove si legge un progetto fuori da Modal:** solo in `sample_check.py` (testo dei sorgenti sull'host, fuori dal repository, mai eseguito, cancellato a fine lavoro).
