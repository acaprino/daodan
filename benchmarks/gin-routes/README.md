# Gin: `(*Engine).Routes()` e gli hook di debug, senza modificare il progetto

**Stato:** Scartato: la sorgente di Gin non si scrive. Il dato ufficiale di Gin (pc, `FileLine`, nome del simbolo) piazza 14 dei 237 gestori che Noir non dà; gli altri sono metodi legati, piazzati solo con una regola sul nome del wrapper del compilatore (`-fm`), e serve eseguire il progetto con argomenti e servizi suoi. Nessuna sorgente della pre-mappa, nessuna voce `go` per Gin in `container_runner.TOOLS`. Nel prodotto le rotte di Gin sono quelle di Noir. Aperto: il legame per tipo alla riga che Noir cita («Aperto»).

## Domanda

`Routes()` si chiama sul motore del progetto senza modificarlo? Se no, che cosa dà un modo ufficiale che non ha bisogno del motore (metodo, percorso, funzione del gestore, file e riga)? Sulle applicazioni vere: dei 237 endpoint per cui Noir 1.5.0 non dà il gestore ([noir-binding](../noir-binding/README.md)), quanti ne lega Gin a una funzione dello snapshot, e a che costo. Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14g del piano).

## Strumento ufficiale provato

Gin 1.12.0 (letto dallo zip del proxy dei moduli, confermato dalla misura dove è detto); le applicazioni vere usano Gin 1.10.0, 1.12.0 e 1.4.0. Misurato su Modal il 24 novembre 2026, rete bloccata.

- `Routes()` (`gin.go:390`) dà `RouteInfo{Method, Path, Handler string, HandlerFunc}`, con il percorso completo e solo l'ultimo gestore della catena. Documentata solo dal commento godoc. `Handler` è un nome di simbolo; file e riga si hanno da `HandlerFunc` con `runtime.FuncForPC(pc).FileLine(pc)`.
- `gin.DebugPrintRouteFunc` (`debug.go:27`, pubblica, documentata in `docs/doc.md`) riceve metodo, percorso assoluto, nome dell'ultimo gestore e numero di gestori a ogni registrazione, solo in modalità debug: niente `HandlerFunc`, niente file. `gin.DebugPrintFunc` (`debug.go:30`, non in Gin 1.4) riceve le altre righe di debug; ogni `Run*` stampa «Listening and serving …» prima di legare la porta.
- `NoRoute` e `NoMethod` non sono in `Routes()` né negli hook (misurato).
- `gin.SetMode(gin.ReleaseMode)` in `main()` fa tacere gli hook (misurato).

Gin non ha un registro dei motori e `Run` blocca: nessun modo ufficiale chiama `Routes()` su un progetto qualsiasi.

| Via | Che cos'è | Dà | Limite (misurato) |
| --- | --- | --- | --- |
| (c) Hook con `-overlay` | `-overlay` è un flag documentato di `go build`: il file esiste solo per quella compilazione, l'albero non cambia; il binario non è quello che il progetto distribuisce. **Deciso dal proprietario il 23 novembre 2026:** conta come «senza modificare il progetto» | metodo, percorso completo, nome dell'ultimo gestore, numero di gestori; dai frame di `runtime.CallersFrames`, la riga del progetto che registra | niente `HandlerFunc`: file e riga dal nome (`go tool nm`, `go tool addr2line`); tace in release; `NoRoute` assente; il programma deve arrivare a registrare le rotte con gli argomenti e i servizi che vuole |
| (a) `Routes()` da un `main` aggiunto | lo stesso `-overlay`, un `main` in una cartella nuova che chiama una funzione del progetto | `HandlerFunc`, quindi il pc e `FileLine(pc)` | nessun dato ufficiale nomina la funzione: la elenca go/types (funzioni esportate senza argomenti che restituiscono `*gin.Engine`), se ce n'è una; la funzione gira senza l'inizializzazione che `main` farebbe prima |
| (b) Testo di debug | l'uscita dell'applicazione, nessun file aggiunto | le stesse righe dell'hook, in testo | formato di un log; stesso arresto e stessi limiti di (c), senza i frame |
| Delve, una copia modificata di Gin | debugger di terzi; un `-overlay` che sostituisce un file di Gin | in principio il motore | non ufficiali, non sondati |

## Parametri

- **Fixture** (`fixture/`): un modulo Go con gestori con nome, un metodo legato, chiusure, gruppi annidati, `Any`, `Match`, `Static`, `StaticFile`, `NoRoute`, `Run` che blocca; interruttori `FIXTURE_FAIL=panic|db|block` e `FIXTURE_RELEASE=1`. Immagine `golang:1.25-bookworm` (Go 1.25.14, non il 1.27.3 di `preparation.GO`), 2 CPU e 4 GB, 20 s per esecuzione.
- **Applicazioni vere:** Go 1.27.3 di `preparation.GO`, il ripristino di Daodan (`go mod download`), poi senza rete una copia del progetto, `GOPROXY=off`, `CGO_ENABLED=1`, 4 CPU e 16 GB.
- **File:** `hooks/` (i file aggiunti con `go build -overlay`: `hook_names.go`, `routes_in_init.go`, `route_hook.go`, `engine_probe.go.tmpl`), `finder/main.go` (strumento di misura con `golang.org/x/tools/go/packages`, non di Daodan), `modal_probe.py`, `modal_real.py`, `real.py`, `prepare.py`, `real_summary.py`, `results/` e `results/real/` (solo conteggi ed estratti brevi).

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal modal run benchmarks/gin-routes/modal_probe.py
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 GIN_ROUTES_EVIDENCE=<cartella fuori dal repository> DAODAN_CODE=<copia di daodan/ fatta all'inizio> \
  uv run --no-project --with modal modal run benchmarks/gin-routes/modal_real.py --stage noir|go [--only go-admin]
python -I benchmarks/gin-routes/real_summary.py <la stessa cartella>
```

## Risultato sulla fixture

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

- **File e riga:** per le funzioni con nome e le chiusure `FileLine(pc)` e `go tool nm` + `go tool addr2line` danno la riga del `func`. Per il metodo legato `srv.List` (`main.(*Server).List-fm`) danno `<autogenerated>:1`, e il simbolo senza `-fm` non c'è nel binario. `Static` e `StaticFile` puntano al file di Gin.
- **Nessun file** nuovo o cambiato resta nella copia.
- **Costruzione:** con le cache dell'immagine 1,3-2,4 s e circa 320 MB; da cache vuote `go mod download` 1,9 s e `go build` 23,5 s, 977 MB.

## Applicazioni vere

Le tre applicazioni Gin di [noir-binding](../noir-binding/README.md), agli stessi commit, scaricate mentre l'immagine si costruisce; nel repository solo indirizzo, commit, licenza e conteggi.

| | gin-vue-admin | go-admin | go-gin-example |
| --- | --- | --- | --- |
| repository, commit | `flipped-aurora/gin-vue-admin`, `dcac232afb56` | `go-admin-team/go-admin`, `f24c303f6156` | `eddycjy/go-gin-example`, `4f5174ca325b` |
| licenza | Apache-2.0 (`LICENSE`) | MIT (`LICENSE.md`) | MIT (`LICENSE`) |
| Gin, `go` del `go.mod` | 1.10.0, 1.26.10 | 1.12.0, 1.27.1 | 1.4.0, 1.13 (`vendor/` presente; con `go 1.13` Go costruisce dalla cache dei moduli, non dal `vendor/`) |
| moduli | `server/` | `.`, `example/app-order`, `test/e2e-apporder` | `.` |
| funzioni Go nello snapshot | 1.431 | 1.930 | 129 |
| Noir: endpoint `http`, senza gestore, con nome | 217, **207**, 1 | 139, **15**, 93 | 29, **15**, 0 |

Taratura: con la stessa copia di Daodan di `noir-binding/results/after.json` si ritrovano 385 endpoint `http`, 237 senza gestore (207 + 15 + 15) e 94 con nome, che il legatore lega tutti.

**Preparazione e costruzione.** Tutte e tre costruiscono senza rete dopo il ripristino di Daodan.

| | gin-vue-admin | go-admin | go-gin-example |
| --- | --- | --- | --- |
| ripristino (rete): cartelle, tempo, cache dei moduli | `server`, 10,4 s, 1,05 GB, exit 0 | 3 cartelle, 17,5 s, 868 MB, exit 0 | `.`, 2,2 s, 245 MB, exit 0 (il `vendor/` non è nel perimetro) |
| finder (go/packages; x/tools chiesto `@latest` mentre l'immagine si costruisce, risolto v0.53.0) | 31,4 s, 634 MB, 0 errori | 22,0 + 8,7 + 1,9 s, fino a 1,2 GB, 0 errori | 12,5 s, 367 MB, 0 errori |
| prima costruzione del `main` con l'hook (cache vuota) | 29,8 s, 1,0 GB | 21,9 s, 1,06 GB; con `-tags sqlite3,json1` (cgo) 38,5 s in più | 15,5 s, 412 MB |
| costruzioni successive (cache calda) | 2,5-4,2 s | 3,2-5,5 s | 1,6 s |

**Dove nasce il motore** (finder, go/types). Il nome del costruttore non è un dato ufficiale; go/types trova un candidato chiamabile senza argomenti in 2 applicazioni su 3.

| | gin-vue-admin | go-admin | go-gin-example |
| --- | --- | --- | --- |
| funzioni che restituiscono `*gin.Engine` | 1: `initialize.Routers()`, esportata, senza argomenti | 4, tutte con argomenti (`*gin.Engine`, `*jwtauth.GinJWTMiddleware`), 2 non esportate | 1: `routers.InitRouter()`, esportata, senza argomenti |
| chiamate di `gin.New` / `gin.Default` | 1, in `initialize.Routers` | 2: `cmd/api.initRouter` (il motore va nel registro di go-admin-core, `sdk.Runtime.SetEngine`) e `app/demo/router.InitRouter` | 1, in `routers.InitRouter` |
| funzioni che registrano (`*gin.Engine`, `*gin.RouterGroup`, `IRouter` fra i parametri) | 41 | 37 + 1 | 0 |
| pacchetti `main` che dipendono da Gin | 3: `server`, `server/cmd/mcp`, `server/plugin/announcement/gen` | 2: `.`, `test/e2e-apporder` (più `tools/checksilent`, senza Gin) | 1 |

**Le tre vie.** Ogni `main` che dipende da Gin è costruito con l'hook ed eseguito con `GIN_MODE=debug`; al primo socket in LISTEN il gruppo di processi è ucciso (nessuna delle tre chiama `Run`). Gli argomenti vengono da: nessuno, il Dockerfile, la CI (anche i tag di costruzione), o scritti a mano per questa misura.

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

**Dal nome del gestore alla funzione dello snapshot.**

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

289 dei 335 gestori sono metodi legati: 288 si piazzano solo togliendo `-fm` dal nome del wrapper, 1 non ha simbolo. Il nome dell'hook è sempre il gestore della rotta (305 casi su 305 concordano con lo snapshot).

**Gin contro Noir.** Una riga di Noir incontra una rotta di Gin per metodo e schema del percorso, altrimenti per metodo e riga di registrazione, che coincide su 321 righe di codice su 324 (le 3 diverse vengono da un `swagger.json`). Colonne cumulative:

| Da dove vengono argomenti e servizi | Rotte di Gin | Endpoint `http` incontrati (di 385) | **I 237 senza gestore: incontrati** | **legati a una funzione con nodo proprio** | I 94 con nome: incontrati, stessa funzione del legatore |
| --- | --- | --- | --- | --- | --- |
| nessuno, più (a) | 160 (gin-vue-admin 139, go-gin-example 21 da (a)) | 151 | 150 | **149** (135 + 0 + 14) | 1, 1 |
| + Dockerfile | 160 | 151 | 150 | 149 | 1, 1 |
| + CI | 269 | 256 | 165 | 149 | 90, 90 |
| + a mano | 335 | 324 | 231 | **214** (200 + 0 + 14) | 90, 90 |

**Il confronto che non esegue codice del progetto.** A Noir manca solo il gestore scritto sulla riga di registrazione. Il finder elenca ogni chiamata di Gin il cui ultimo parametro è `...gin.HandlerFunc` (scelta per tipo) e risolve l'ultimo argomento con go/types; il legame si fa con la riga di `code_paths` di Noir. Nessun binario collegato, nessun codice del progetto eseguito; costo 12,5-31,4 s e 0,37-1,2 GB per modulo.

| | gin-vue-admin | go-admin | go-gin-example | Totale |
| --- | --- | --- | --- | --- |
| chiamate di Gin con `...gin.HandlerFunc` | 347 | 220 | 19 | 586 |
| **dei 237: una funzione dello snapshot parte alla riga, nodo proprio** | **199** di 207 | 0 di 15 | **14** di 15 | **213** |
| il resto | 6 nessuna chiamata di Gin alla riga (MCP), 2 l'argomento è una variabile | 12 l'argomento è una chiamata (10 fabbriche generiche `actions.Index(…)`, `ginSwagger.WrapHandler`, `transfer.Handler` di go-admin-core), 3 metodi di go-admin-core | 1 chiamata (`ginSwagger.WrapHandler`) | 24 |
| dei 94 con nome: la stessa funzione del legatore | 1 su 1 | 93 su 93 | — | **94 su 94** |
| contro Gin, dove entrambi danno una funzione | 199 su 199 uguali | 89 su 89 | 14 su 14 | **302 su 302** |

**Verdetto.**

- Come Daodan la lancerebbe (nessun argomento, più il costruttore che go/types trova) la sorgente lega 149 dei 237, su 2 applicazioni su 3 e con due vie diverse; solo 14 con il dato ufficiale di Gin, 135 togliendo `-fm`. Con argomenti, tag e servizi scritti a mano 214.
- Costa una costruzione per `main` (15-30 s e 0,4-1 GB da cache vuota, 38 s in più per cgo), l'esecuzione del codice del progetto (un generatore che scrive nella copia, un database SQLite cambiato, file di log) e la scelta di quale `main` lanciare con quali argomenti.
- Il tipo dell'argomento alla riga che Noir cita ne lega 213, su 3 applicazioni su 3, senza eseguire nulla, d'accordo con Gin in 302 casi su 302 e con il legatore in 94 su 94: il lavoro che resta è nel legame, non in una sorgente che esegue il progetto.

## Aperto

- **Aperta: da approfondire. Il legame per tipo alla riga di Noir, dentro Daodan.** È misurato con il finder di questa cartella, non con il codice di Daodan: se l'indice di scip-go che Daodan già costruisce dà la stessa definizione per l'identificatore alla riga citata non è misurato. La forma generica («l'ultimo argomento di tipo funzione della chiamata alla riga citata», per echo, chi, fiber e `net/http`) non è misurata.
- **I 237 dopo il passo dinamico:** non misurato. L'osservatore Go (`daodan/core/dynamic/go.py`) registra ciò che i test chiamano; se dà il gestore di una rotta non è misurato.
- Le 10 fabbriche generiche di go-admin (`actions.Index[T](…)`): né Gin né il tipo danno una funzione propria della rotta.
- Non provati: la via (a) su un metodo legato; rotte registrate dopo l'ascolto; applicazioni che chiamano `gin.SetMode(gin.ReleaseMode)` prima di registrare; più motori in un processo; `go.work`; Gin più vecchi di 1.4; il Docker di Daodan (la misura usa l'immagine di Modal con il Go di Daodan).
- Letti nei sorgenti delle applicazioni e non misurati: che `InstallPlugin` di gin-vue-admin aspetti il database; che go-admin metta il motore in `sdk.Runtime.SetEngine`; le righe di Dockerfile, `Makefile` e workflow citate nella tabella delle vie.
