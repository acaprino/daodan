# Gin: `(*Engine).Routes()` e gli hook di debug, senza modificare il progetto

**Stato: sonda scritta il 23 novembre 2026, eseguita su Modal il 24 novembre 2026 (fixture, `results/`), poi misurata su tre applicazioni vere (sezione «Applicazioni vere», `results/real/`).** Il codice dei progetti è costruito ed eseguito solo nei container di Modal, mai su questa macchina; nulla è compilato qui. Ciò che segue «Letto dal sorgente» viene dalla lettura di Gin 1.12.0 (zip del proxy dei moduli) ed è confermato dalla misura dove è detto. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14g.

Domanda: `Routes()` si chiama sul motore del progetto senza modificare il progetto? Se no, che cosa dà un modo ufficiale che non ha bisogno del motore (metodo, percorso, funzione del gestore, file e riga), e dove `Run` si ferma. Sulle applicazioni vere: dei 237 endpoint per cui Noir 1.5.0 non dà il gestore ([noir-binding](../noir-binding/README.md)), quanti ne lega Gin a una funzione dello snapshot, e a che costo.

**Risultato in una riga:** la sorgente di Gin **non vale la pena di scriverla**. Come Daodan la lancerebbe (nessun argomento, più il costruttore che go/types trova) lega 149 dei 237 a una funzione con nodo proprio, su 2 applicazioni su 3 e con due vie diverse, e **solo 14 con il dato ufficiale di Gin** (pc o nome del simbolo): gli altri 135 sono metodi legati, piazzati togliendo `-fm` dal nome del wrapper del compilatore. Con l'argv del Dockerfile, i tag di costruzione della CI e i servizi scritti a mano 214. Dove resta il lavoro lo mostra un confronto che non collega binari né esegue codice del progetto: **la chiamata di Gin alla riga che Noir cita e la funzione che il suo ultimo argomento nomina secondo go/types ne legano 213**, su 3 applicazioni su 3, la stessa funzione di Gin in 302 casi su 302 e la stessa del legatore in 94 su 94.

| File | Contenuto |
| --- | --- |
| `fixture/` | un modulo Go (`gin v1.12.0`, Go 1.25): gestori con nome, un metodo legato (`srv.List`, nome `…(*Server).List-fm`), chiusure (`/ping`, `auth()`), gruppi annidati con prefisso e middleware, la stessa funzione su due percorsi, `Any`, `Match`, `Static`, `StaticFile`, `NoRoute`, `Run` che blocca. Interruttori da variabile d'ambiente: `FIXTURE_FAIL=panic\|db\|block` (l'applicazione non si carica: panic, database `db.invalid:5432`, attesa senza fine prima delle rotte) e `FIXTURE_RELEASE=1` (`gin.SetMode(gin.ReleaseMode)` in `main()`). `go.sum` non c'è: lo fa `go mod tidy` nell'immagine |
| `hooks/hook_names.go` | un file che esiste solo nella compilazione di una copia (`go build -overlay`): imposta `gin.DebugPrintRouteFunc` e `gin.DebugPrintFunc`, scrive ogni rotta in un file e, alla riga «Listening and serving…» che ogni `Run*` stampa prima di legare la porta, esce con `os.Exit(0)` |
| `hooks/routes_in_init.go` | lo stesso meccanismo: nel suo `init` chiama il `setupRouter()` della fixture, scrive `Routes()` con file e riga (`runtime.FuncForPC(pc).FileLine(pc)`) ed esce prima di `main` (il nome `setupRouter` è una convenzione della documentazione dei test di Gin, non di ogni progetto) |
| `modal_probe.py` | costruisce l'immagine con la rete aperta (`go mod tidy`, `go mod download`, una `go build`), poi esegue ogni sonda senza rete; scrive `results/<sonda>.json`. Corretto per l'esecuzione: la risposta torna in pezzi compressi (una chiamata con la rete bloccata non restituisce più di circa 8 KB) e un nome che finisce in `-fm` è cercato anche senza |
| `modal_real.py`, `real.py`, `prepare.py` | le applicazioni vere (sezione «Applicazioni vere»): l'immagine di ciascuna (rete aperta: il Go di `preparation.GO`, il ripristino di Daodan, Noir, il finder), poi `real.py` senza rete: `--stage noir` (lo snapshot, Noir e il legatore di `noir-binding`) e `--stage go` (finder, costruzioni, esecuzioni) |
| `finder/main.go` | strumento di misura, non di Daodan: con `golang.org/x/tools/go/packages` (il caricatore del team di Go, tipi di go/types) elenca le funzioni che restituiscono `*gin.Engine`, le chiamate di `gin.New`/`gin.Default`, i pacchetti `main` che dipendono da Gin, ogni chiamata di Gin con un parametro `...gin.HandlerFunc` (scelta per tipo) con ciò che il suo ultimo argomento nomina; con `-names` divide un nome di simbolo con `debug/gosym` |
| `hooks/route_hook.go` | l'hook per le applicazioni vere: solo `DebugPrintRouteFunc` (c'è da Gin 1.4; `DebugPrintFunc` no), una riga JSON per rotta con i frame che hanno chiamato Gin (`runtime.CallersFrames`); non ferma il processo |
| `hooks/engine_probe.go.tmpl` | la via (a): un `main` aggiunto in una cartella nuova della copia che chiama il costruttore elencato dal finder e scrive `Routes()` con il pc di ogni `HandlerFunc` e `FileLine(pc)` |
| `real_summary.py` | dalle risposte (fuori dal repository) ai conteggi di `results/real/<applicazione>.json` e `results/real/summary.json` |
| `results/` | le sonde della fixture (uscite della fixture stessa); `results/real/` solo conteggi ed estratti brevi (rotta, nome del gestore, file:riga), nessun sorgente delle applicazioni |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/gin-routes/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 GIN_ROUTES_EVIDENCE=<cartella fuori dal repository> DAODAN_CODE=<copia di daodan/ fatta all'inizio> \
  uv run --no-project --with modal modal run benchmarks/gin-routes/modal_real.py --stage noir|go [--only go-admin]
python -I benchmarks/gin-routes/real_summary.py <la stessa cartella>
```

## Letto dal sorgente di Gin 1.12.0

- `Routes()` (`gin.go:390`) percorre gli alberi per metodo (`iterate`, `gin.go:397`) e dà `RoutesInfo`, una lista di `RouteInfo{Method, Path, Handler string, HandlerFunc}` (`gin.go:68-76`). Per ogni nodo con gestori prende **solo l'ultimo** della catena (`root.handlers.Last()`, `gin.go:400`): i middleware di gruppo e di motore non compaiono. Non è nominata né nel README né in `docs/doc.md`: è documentata solo dal commento godoc. `RouteInfo.HandlerFunc` c'è anche in Gin 1.4.0 (letto nel `vendor/` di go-gin-example).
- `Handler` è `nameOfFunction(f)` = `runtime.FuncForPC(reflect.ValueOf(f).Pointer()).Name()` (`utils.go:131`): un nome di simbolo, non un file. File e riga si ottengono da `HandlerFunc`, che è nel risultato: `fn.FileLine(pc)` con lo stesso `pc`. Chi ha solo il nome (gli hook) non ha né `HandlerFunc` né la riga.
- Che nome dà (misurato sulla fixture): funzione con nome `main.listItems`; metodo legato `main.(*Server).List-fm` (il wrapper del compilatore); chiusura `main.setupRouter.func1`, e `main.auth.func1` per una fabbrica di middleware; `Static` registra una chiusura dentro Gin (`…(*RouterGroup).createStaticHandler.func1`, file e riga **di Gin**); `StaticFile` dà `main.setupRouter.(*RouterGroup).StaticFile.func5`: un nome che comincia con `main.` per codice di Gin (inlinato), quindi «fuori dal progetto» si decide dal file, non dal nome.
- Gruppi: `Group` (`routergroup.go:72`) ha `basePath` e `Handlers`; `handle` (`routergroup.go:86`) calcola il percorso assoluto e combina i gestori: `Routes()` dà il percorso già completo, il gestore è l'ultimo. `Any` registra nove metodi, `Match` uno per metodo, `Static` `GET` e `HEAD` su `/*filepath`.
- `NoRoute` (`gin.go:326`) scrive `engine.noRoute` (campo non esportato): **non è in `Routes()`** né negli hook (misurato: assente). Anche `NoMethod`.
- `gin.DebugPrintRouteFunc` (`debug.go:27`) è una variabile pubblica, documentata in `docs/doc.md` («Define format for the log of routes»): `func(httpMethod, absolutePath, handlerName string, nuHandlers int)`. La chiama `addRoute` a ogni registrazione **solo se `IsDebugging()`**: dà il nome del gestore (l'ultimo) e quanti gestori ha la catena, non `HandlerFunc`, non il file. `gin.DebugPrintFunc` (`debug.go:30`, non in Gin 1.4) riceve ogni altra riga di debug, e ogni `Run*` stampa «Listening and serving …» **prima** di legare (`gin.go:549, 562, 582, 608, 631, 646`). Senza l'hook il testo è `[GIN-debug] GET /items --> main.listItems (3 handlers)` (`debug.go:37`) su `gin.DefaultWriter` (standard output); in Gin 1.4.0 su standard error (`fmt.Fprintf(os.Stderr, …)`, misurato su go-gin-example).
- La modalità: `GIN_MODE` (`mode.go`, `init`), predefinita `debug`; `gin.SetMode` in `main()` la cambia dopo l'`init` di qualunque file aggiunto: se l'applicazione chiama `gin.SetMode(gin.ReleaseMode)`, gli hook tacciono e `Run` resta in ascolto (misurato).

## Il problema: come si ottiene il motore senza modificare il progetto

Gin non ha un registro dei motori: il motore sta in una variabile di `main()` (o dove il progetto lo mette) e `Run` blocca. Non esiste un modo ufficiale di chiamare `Routes()` su un progetto qualsiasi; l'unico dato ufficiale che non chiede il motore sono i due hook sopra.

| Via | Che cos'è | Dà | Limite (misurato) |
| --- | --- | --- | --- |
| (c) Hook con `-overlay` | `-overlay` è un flag documentato di `go build`: il file esiste solo per quella compilazione, l'albero non cambia; il binario non è quello che il progetto distribuisce. **Deciso dal proprietario il 23 novembre 2026:** conta come «senza modificare il progetto» | metodo, percorso completo, nome dell'ultimo gestore, numero di gestori; dai frame di `runtime.CallersFrames`, la riga del progetto che registra | niente `HandlerFunc`: file e riga dal nome (`go tool nm`, `go tool addr2line`); tace in release; `NoRoute` assente; il programma deve arrivare a registrare le rotte con gli argomenti e i servizi che vuole |
| (a) `Routes()` da un `main` aggiunto | lo stesso `-overlay`, un `main` in una cartella nuova che chiama una funzione del progetto | `HandlerFunc`, quindi il pc e `FileLine(pc)` | nessun dato ufficiale nomina la funzione: la elenca go/types (funzioni esportate senza argomenti che restituiscono `*gin.Engine`), se ce n'è una; la funzione gira senza l'inizializzazione che `main` farebbe prima |
| (b) Testo di debug | l'uscita dell'applicazione, nessun file aggiunto | le stesse righe dell'hook, in testo | formato di un log; stesso arresto e stessi limiti di (c), senza i frame |
| Delve, una copia modificata di Gin | debugger di terzi; un `-overlay` che sostituisce un file di Gin | in principio il motore | non ufficiali, non sondati |

## Risultati sulla fixture

`modal_probe.py`, immagine `golang:1.25-bookworm` (**Go 1.25.14, non il 1.27.3 di `preparation.GO`**), Gin 1.12.0, rete bloccata, 2 CPU e 4 GB; un tempo limite di 20 s per esecuzione. Ogni sonda costruisce una copia della fixture con il suo file di `hooks/` per `-overlay`; in nessuna resta un file nuovo o cambiato nella copia.

| Sonda | Uscita, tempo, memoria | Porta | Rotte |
| --- | --- | --- | --- |
| `hook-names` (hook, `DAODAN_STOP`) | exit 0 in 0,02 s, 71 MB | nessuna: ferma alla riga «Listening and serving» | **22** (9 di `Any`, 2 di `Match`, `GET`+`HEAD` di `Static` e di `StaticFile`); `NoRoute` assente |
| `hook-no-stop` | exit 124 al limite | 8080 | 22 |
| `hook-release-env` (`GIN_MODE=release`), `hook-release-code` (`SetMode` in `main`) | exit 124 al limite | 8080 | **0**: gli hook tacciono |
| `debug-stdout` (nessun file aggiunto) | exit 124 al limite | 8080 | 22 righe `[GIN-debug] … -->` sullo standard output |
| `routes-in-init` (`Routes()`) | exit 0 in 0,02 s | nessuna | 22 righe con pc e `FileLine(pc)` |
| `app-panic`, `app-panic-routes-in-init` | exit 2 in 0,02-0,04 s, la traccia del panic | nessuna | 0 |
| `app-db` | exit 1 in 0,02 s (`lookup db.invalid … network is unreachable`) | nessuna | 0 |
| `app-block` | exit 124 al limite, nessun processo rimasto | nessuna | 0 |

- **File e riga.** Per le funzioni con nome e le chiusure `FileLine(pc)` e `go tool nm` + `go tool addr2line` danno la stessa riga, quella del `func` (`main.go:19`, `:20`, `:21`, `:47`, `:57`). **Per il metodo legato `srv.List` (`main.(*Server).List-fm`) danno entrambi `<autogenerated>:1`**, e il simbolo del metodo senza `-fm` non c'è nel binario (inlinato nel wrapper). `Static` e `StaticFile` puntano al file di Gin nella cache dei moduli (`routergroup.go:220` e `:167`).
- **Middleware.** La catena ha 2-4 gestori (`logger`, `auth()` dei gruppi, il gestore); il nome è sempre l'ultimo, il gestore della rotta.
- **Costruzione.** Con le cache dell'immagine 1,3-2,4 s e circa 320 MB; da cache vuote, con la rete, `go mod download` 1,9 s e `go build` 23,5 s, 977 MB.

## Applicazioni vere

Misurato il 24 novembre 2026 (`modal_real.py`, `real.py`, `real_summary.py`, `results/real/`). Le tre applicazioni Gin di [noir-binding](../noir-binding/README.md), agli stessi commit (completi in `noir-binding/apps.py`, che `modal_real.py` importa); scaricate al commit mentre l'immagine si costruisce (rete aperta) e lì sole; nel repository solo indirizzo, commit, licenza e conteggi. Licenze lette al commit (`gh api repos/<repo>/license?ref=<commit>`): tutte permettono di eseguire il codice e di pubblicare misure.

| | gin-vue-admin | go-admin | go-gin-example |
| --- | --- | --- | --- |
| repository, commit | `flipped-aurora/gin-vue-admin`, `dcac232afb56` | `go-admin-team/go-admin`, `f24c303f6156` | `eddycjy/go-gin-example`, `4f5174ca325b` |
| licenza | Apache-2.0 (`LICENSE`) | MIT (`LICENSE.md`) | MIT (`LICENSE`) |
| Gin, `go` del `go.mod` | 1.10.0, 1.26.10 | 1.12.0, 1.27.1 | 1.4.0, 1.13 (`vendor/` presente; con `go 1.13` Go costruisce dalla cache dei moduli, non dal `vendor/`) |
| moduli | `server/` | `.`, `example/app-order`, `test/e2e-apporder` | `.` |
| funzioni Go nello snapshot | 1.431 | 1.930 | 129 |
| Noir: endpoint `http`, senza gestore, con nome | 217, **207**, 1 | 139, **15**, 93 | 29, **15**, 0 |

**Taratura:** con la copia di Daodan congelata all'inizio (le stesse impronte di `binder.py`, `flows.py`, `premap/noir.py` di `noir-binding/results/after.json`), `measure.py` e `causes.py` di `noir-binding` danno di nuovo 385 endpoint `http`, **237 senza gestore** (207 + 15 + 15) e 94 con nome, che il legatore lega tutti (1 + 93).

### Preparazione e costruzione

Go 1.27.3 di `preparation.GO` (sha256 verificato). La preparazione è quella di Daodan: `preparation.restores` sul perimetro dà le cartelle, `preparation.restore("go", …)` la riga (`go mod download`), con `GOFLAGS=-mod=readonly GOTOOLCHAIN=local` e la rete. Poi, senza rete, una copia del progetto, `GOPROXY=off`, `CGO_ENABLED=1`, 4 CPU e 16 GB.

| | gin-vue-admin | go-admin | go-gin-example |
| --- | --- | --- | --- |
| ripristino (rete): cartelle, tempo, cache dei moduli | `server`, 10,4 s, 1,05 GB, exit 0 | 3 cartelle, 17,5 s, 868 MB, exit 0 | `.`, 2,2 s, 245 MB, exit 0 (il `vendor/` non è nel perimetro) |
| finder (go/packages; x/tools chiesto `@latest` mentre l'immagine si costruisce, risolto v0.53.0) | 31,4 s, 634 MB, 0 errori | 22,0 + 8,7 + 1,9 s, fino a 1,2 GB, 0 errori | 12,5 s, 367 MB, 0 errori |
| prima costruzione del `main` con l'hook (cache vuota) | 29,8 s, 1,0 GB | 21,9 s, 1,06 GB; con `-tags sqlite3,json1` (cgo) 38,5 s in più | 15,5 s, 412 MB |
| costruzioni successive (cache calda) | 2,5-4,2 s | 3,2-5,5 s | 1,6 s |

Tutte e tre costruiscono senza rete dopo il ripristino di Daodan, senza `-mod=vendor`.

### Dove nasce il motore (finder, go/types)

| | gin-vue-admin | go-admin | go-gin-example |
| --- | --- | --- | --- |
| funzioni che restituiscono `*gin.Engine` | 1: `initialize.Routers()`, esportata, senza argomenti | 4, tutte con argomenti (`*gin.Engine`, `*jwtauth.GinJWTMiddleware`), 2 non esportate | 1: `routers.InitRouter()`, esportata, senza argomenti |
| chiamate di `gin.New` / `gin.Default` | 1, in `initialize.Routers` | 2: `cmd/api.initRouter` (il motore va nel registro di go-admin-core, `sdk.Runtime.SetEngine`) e `app/demo/router.InitRouter` | 1, in `routers.InitRouter` |
| funzioni che registrano (`*gin.Engine`, `*gin.RouterGroup`, `IRouter` fra i parametri) | 41 | 37 + 1 | 0 |
| pacchetti `main` che dipendono da Gin | 3: `server`, `server/cmd/mcp`, `server/plugin/announcement/gen` | 2: `.`, `test/e2e-apporder` (più `tools/checksilent`, senza Gin) | 1 |

Il nome del costruttore non è un dato ufficiale; go/types trova un candidato chiamabile senza argomenti in 2 applicazioni su 3, e uno solo.

### Le tre vie

Ogni `main` che dipende da Gin è costruito con l'hook (`-overlay`) ed eseguito con `GIN_MODE=debug` nella sua cartella; **l'arresto è del contorno, non di Gin**: al primo socket in LISTEN che compare (`/proc/net/tcp`, letto ogni 5 ms) il gruppo di processi è ucciso, quindi a differenza della fixture una porta resta legata fino a quel momento (sul loopback: la rete è bloccata). Nessuna delle tre applicazioni chiama `Run`: nelle tre esecuzioni senza hook il processo ascolta e la riga «Listening and serving» di Gin non è nella sua uscita (misurato; dal sorgente, `http.Server.ListenAndServe`). Le colonne «da dove vengono gli argomenti»: **nessuno** (come `go run .`), **Dockerfile** (argv e il file che un `COPY` mette dove il `CMD` lo cerca), **CI** (anche i tag di costruzione del workflow), **a mano** (scritto per questa misura).

| | gin-vue-admin | go-admin | go-gin-example |
| --- | --- | --- | --- |
| (c) nessun argomento | **139 rotte**, LISTEN su 8888 dopo 53 ms, 114 MB; il database non c'è e l'applicazione parte lo stesso | exit 255: cobra vuole un comando (`requires at least one arg`) | exit 1 in `init`, prima di ogni rotta: `models.Setup err: dial tcp 127.0.0.1:3306: connection refused` |
| (c) Dockerfile | `-c config.docker.yaml`: le stesse 139 | `server -c config/settings.demo.yml` (SQLite, il file del database è nel repository): exit 1, `database driver "sqlite3" is not in this build, rebuild with -tags sqlite3` | `ENTRYPOINT` senza argomenti: come sopra |
| (c) CI | — | lo stesso con `-tags sqlite3,json1` (`.github/workflows/build.yml`; `Makefile`, `build-sqlite`): **109 rotte**, LISTEN dopo 45 ms | — |
| (c) a mano | `config.yaml` con `db-type: sqlite` e un file in `/tmp`: **205 rotte** (i plugin registrano le loro solo quando c'è un database: `InstallPlugin` aspetta l'evento del database pronto) | `server` da solo: exit 1, MySQL a `127.0.0.1:3306` | MariaDB con utente, password e database di `conf/app.ini`: **21 rotte** |
| (b) testo di Gin, senza hook | 139 righe `[GIN-debug] … -->` | 109 (con i tag della CI) | 21 su standard error (con MariaDB) |
| (a) `Routes()` dal costruttore | **panic** dopo 3 rotte: `'/swagger/*any' … conflicts with existing wildcard '/*filepath'` (senza la configurazione che `main` carica, il prefisso di `Static` è vuoto) | nessun candidato | **21 rotte**, senza database: le stesse 21 della corsa con MariaDB, tutte con pc (`FileLine` alla riga del `func`) |
| gli altri `main` | `cmd/mcp` ascolta su 8889 con 0 rotte Gin; **`plugin/announcement/gen` è un generatore di codice: scrive 2 file nella copia** ed esce 0 | `test/e2e-apporder`: cobra, exit 255 | — |
| lasciato nella copia | `server/log/<data>/info.log` e i 2 file generati | `temp/logs/app.log`; **`go-admin-db.db` cambiato**, `-shm` e `-wal` nuovi | `runtime/logs/log<data>.log` |

Ogni esecuzione che registra rotte è fermata entro 0,25 s (il generatore di gin-vue-admin esce da solo in 2,0 s), con 99-121 MB. Il testo di Gin (b) ha in tutte e tre lo stesso numero di righe dell'hook; che dopo l'ascolto non si registrino altre rotte non è verificato (il processo è fermato lì).

### Dal nome del gestore alla funzione dello snapshot

| | gin-vue-admin (205 rotte) | go-admin (109) | go-gin-example (21) |
| --- | --- | --- | --- |
| dal pc (`Routes()`) | — | — | 21 |
| dal nome, `go tool nm` + `addr2line` | 4 | 11 | — |
| **metodo legato (`-fm`): `<autogenerated>:1`, piazzato solo cercando il nome senza `-fm`** | **200** | **88** | 0 |
| `-fm` il cui metodo non ha simbolo (inlinato) | 1 (`(*info).GetInfoPublic`) | 0 | 0 |
| nome generico senza simbolo (`actions.Index[...].func1`: la runtime abbrevia i tipi) | 0 | **10** | 0 |
| fuori dal progetto (gestori di Gin, di gin-swagger, di go-admin-core) | 3 | 9 | 7 |
| **una funzione dello snapshot parte alla riga** | **201** | **90** | **14** |
| di quelle, nodo proprio e di una sola funzione (`Facts.node`) | 201 | 88 (2 su un nodo condiviso) | 14 |
| il nome che `debug/gosym` divide concorda con lo snapshot (`(*T).M` → `T.M`) | 201 su 201 | 90 su 90 | 14 su 14 |

- **Il dato ufficiale non basta per i metodi legati.** `FileLine(pc)` e il simbolo del nome danno `<autogenerated>:1` per un metodo legato (fixture), e 289 dei 335 gestori delle tre applicazioni sono metodi legati: 288 si piazzano solo togliendo `-fm`, una regola sul nome che il compilatore dà al wrapper (non un'interfaccia), 1 non ha simbolo. La via (a) non ha incontrato metodi legati (go-gin-example ha solo funzioni).
- **Middleware.** Catene di 3-14 gestori; il nome è sempre il gestore della rotta: concorda con lo snapshot in 305 casi su 305 e, dove Noir nomina il gestore, con la funzione del legatore in 90 su 90.

### Gin contro Noir

Una riga di Noir incontra una rotta di Gin per metodo e schema del percorso (`flows.path_schema`), altrimenti per metodo e riga di registrazione (la riga di `code_paths` di Noir, il primo frame fuori da Gin dell'hook). **La riga di registrazione coincide su ogni riga di codice incontrata:** 321 su 324; le 3 diverse sono righe che Noir prende da un `swagger.json`. Noir scrive senza il prefisso del gruppo 7 percorsi (`/demo-product` per `/api/v1/demo-product` in go-admin, `/emailTest` per `/email/emailTest` in gin-vue-admin): li incontra la riga di registrazione.

Colonne cumulative: ogni livello aggiunge le esecuzioni del successivo.

| Da dove vengono argomenti e servizi | Rotte di Gin | Endpoint `http` incontrati (di 385) | **I 237 senza gestore: incontrati** | **legati a una funzione con nodo proprio** | I 94 con nome: incontrati, stessa funzione del legatore |
| --- | --- | --- | --- | --- | --- |
| nessuno, più (a) | 160 (gin-vue-admin 139, go-gin-example 21 da (a)) | 151 | 150 | **149** (135 + 0 + 14) | 1, 1 |
| + Dockerfile | 160 | 151 | 150 | 149 | 1, 1 |
| + CI | 269 | 256 | 165 | 149 | 90, 90 |
| + a mano | 335 | 324 | 231 | **214** (200 + 0 + 14) | 90, 90 |

- **Come Daodan la lancerebbe** (nessun argomento, più il costruttore che go/types elenca): **149 dei 237, su 2 applicazioni su 3, ognuna con una via diversa** (l'hook in gin-vue-admin, `Routes()` in go-gin-example); go-admin 0 finché non si leggono il Dockerfile e la CI, e anche allora 0 dei suoi 15 (5 gestori di librerie, 10 nomi generici). **Dei 149, 14 sono piazzati dal dato ufficiale (il pc di `Routes()`, go-gin-example) e 135 solo togliendo `-fm`**; dei 214 con tutto a mano, 14 e 200.
- **Che cosa resta dei 237 con tutto a mano (23):** 6 rotte di `server/mcp/server.go` che Noir attribuisce a Gin e sono di un altro server; i 10 gestori generici e 5 di librerie di go-admin; 1 metodo inlinato; 1 di gin-swagger in go-gin-example.
- **Solo di Gin** (13 con tutto a mano): i file statici (`Static`, `GET`+`HEAD`) e gin-swagger, tutti fuori dal progetto. **Solo di Noir** (61): righe di `swagger.json` e di un ingress Kubernetes, 19 file statici di go-admin, le 4 rotte di `example/app-order` (un modulo senza `main`), le 6 MCP.

### Il confronto che non esegue codice del progetto

La riga di registrazione coincide sempre: a Noir manca solo il gestore scritto su quella riga. Il finder (go/types, lo stesso caricamento di sopra: nessun binario collegato, nessun codice del progetto eseguito, nessun `main`, argv, tag o servizio da scegliere; il caricatore compila però i pacchetti per i dati di esportazione, nel container) elenca ogni chiamata di una funzione o di un metodo di Gin il cui ultimo parametro è `...gin.HandlerFunc` (scelta per tipo, non per nome: `GET`, `Handle`, `Any`, `Group`, `Use`…) e risolve l'ultimo argomento: una funzione o un metodo (la sua posizione), una funzione scritta sul posto (la sua), una chiamata (una fabbrica), una variabile. Il legame per riga si fa con la riga di `code_paths` di Noir.

| | gin-vue-admin | go-admin | go-gin-example | Totale |
| --- | --- | --- | --- | --- |
| chiamate di Gin con `...gin.HandlerFunc` | 347 | 220 | 19 | 586 |
| **dei 237: una funzione dello snapshot parte alla riga, nodo proprio** | **199** di 207 | 0 di 15 | **14** di 15 | **213** |
| il resto | 6 nessuna chiamata di Gin alla riga (MCP), 2 l'argomento è una variabile | 12 l'argomento è una chiamata (10 fabbriche generiche `actions.Index(…)`, `ginSwagger.WrapHandler`, `transfer.Handler` di go-admin-core), 3 metodi di go-admin-core | 1 chiamata (`ginSwagger.WrapHandler`) | 24 |
| dei 94 con nome: la stessa funzione del legatore | 1 su 1 | 93 su 93 | — | **94 su 94** |
| contro Gin, dove entrambi danno una funzione | 199 su 199 uguali | 89 su 89 | 14 su 14 | **302 su 302** |

Sui 237: Gin con tutto a mano ne lega 2 che il tipo non lega (due gestori del plugin email passati in una variabile), il tipo 1 che Gin non lega (il metodo inlinato). Il costo è quello del finder: 12,5-31,4 s e 0,37-1,2 GB per modulo, quanto una costruzione da cache vuota, sulla cache dei moduli del ripristino di Daodan; nulla resta nella copia. Il finder non è codice di Daodan e sceglie per un tipo di Gin: è un confronto, non una proposta misurata dentro Daodan.

### Verdetto

**Non vale la pena di scrivere la sorgente di Gin**, sulle misure:

- Come Daodan la lancerebbe recupera 149 dei 237 su 2 applicazioni su 3, con due meccanismi diversi (l'hook nel `main` dove l'applicazione parte senza database, il costruttore dove `main` non parte); la terza applicazione vuole l'argv di un Dockerfile rimappato da un `COPY` e i tag di costruzione della CI, e anche allora non aggiunge nulla ai 237. Con servizi e impostazioni scritti a mano arriva a 214.
- Il dato ufficiale di Gin (pc, `FileLine`, nome del simbolo) non piazza i metodi legati, che sono 289 dei 335 gestori: serve una regola sul nome del wrapper del compilatore (`-fm`), e i nomi generici restano senza file.
- Costa una costruzione per `main` (15-30 s e 0,4-1 GB da cache vuota, 38 s in più per cgo), l'esecuzione del codice del progetto (un generatore che scrive nella copia, un database SQLite cambiato, file di log) e la scelta di quale `main` lanciare con quali argomenti.
- Il verdetto sta sui numeri di Gin: 14 dei 237 con il suo dato ufficiale, 149 con la regola `-fm`, su 2 applicazioni su 3. Il confronto con il tipo dell'argomento alla riga che Noir cita (213, su tutte e tre, senza binari né esecuzione, d'accordo con Gin in 302 casi su 302 e con il legatore in 94 su 94) dice dove sta il lavoro che resta per i 237: nel legame, non in una sorgente che esegue il progetto (vedi «Non coperto»).

## Decisioni

- **Gli hook come sorgente:** no. Danno metodo, percorso e nome dell'ultimo gestore a ogni applicazione che arriva a registrare le rotte, ma il nome non porta al file per i metodi legati senza una regola sul nome e i generici restano senza file; quante applicazioni ci arrivano senza argomenti, servizi o tag dipende dal progetto (1 su 3 qui).
- **`go tool addr2line` e `FileLine(pc)`** danno la riga del `func` (la dichiarazione dello snapshot parte lì: 305 su 305), tranne per un metodo legato (`<autogenerated>:1`).
- **Nessuna voce `go` in `container_runner.TOOLS`** per Gin. Ciò che si misura dopo è il legame per tipo alla riga di Noir (sotto).

## Letto fuori da Modal

Per orientarsi, prima di scrivere le sonde, il testo dei sorgenti delle tre applicazioni è stato scaricato su questa macchina (in una cartella fuori dal repository, mai eseguito né compilato, cancellata a fine lavoro) e letto, anche con `grep` sui `.go`. Nessun numero viene da lì. Sono letti, non misurati: che `InstallPlugin` di gin-vue-admin aspetti il database; che go-admin metta il motore in `sdk.Runtime.SetEngine` e chiami `gin.SetMode(gin.ReleaseMode)` solo con `mode: prod`; le righe del Dockerfile, del `Makefile` e del workflow della CI citate sopra; che le tre usino `http.Server.ListenAndServe` (misurato invece che `Run` non stampa la sua riga).

## Non coperto (aperto)

- **Il confronto statico dentro Daodan:** misurato con il finder di questa cartella, non con il codice di Daodan; se l'indice di scip-go che Daodan già costruisce dà la stessa definizione per l'identificatore alla riga citata non è misurato. La scelta per tipo è di Gin (`gin.HandlerFunc`); la forma generica («l'ultimo argomento di tipo funzione della chiamata alla riga citata», per echo, chi, fiber e `net/http`) non è misurata.
- Le 10 fabbriche generiche di go-admin (`actions.Index[T](…)`, la funzione restituita è una chiusura condivisa da molte rotte): né Gin né il tipo danno una funzione propria della rotta.
- La via (a) su un metodo legato (nessuna delle applicazioni lo ha); generici con `Routes()`; rotte registrate dopo l'ascolto (il processo è fermato al primo socket in LISTEN).
- Applicazioni che chiamano `gin.SetMode(gin.ReleaseMode)` prima di registrare (go-admin lo fa solo con `mode: prod`), più motori in un processo, `go.work`, `cgo` fuori da SQLite, Gin più vecchi di 1.4.
- Il Docker di Daodan: la misura usa l'immagine di Modal con il Go di Daodan, non il container del motore.
- Sulla fixture la sonda usa Go 1.25.14, non il 1.27.3 fissato.
