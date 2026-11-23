# Gin: `(*Engine).Routes()` e gli hook di debug, senza modificare il progetto

**Stato: sonda scritta il 23 novembre 2026, NON ESEGUITA.** La sessione che l'ha scritta non ha le credenziali di Modal e la regola del progetto vieta di compilare o eseguire il progetto su quella macchina. Nessun numero di questa pagina è una misura: le tabelle dicono che cosa la sonda misurerà; ciò che segue «Letto dal sorgente» viene dalla lettura di Gin 1.12.0 (zip del proxy dei moduli, non eseguito). Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14g.

Domanda: `Routes()` si chiama sul motore del progetto senza modificare il progetto? Se no, che cosa dà un modo ufficiale che non ha bisogno del motore (metodo, percorso, funzione del gestore, file e riga), e dove `Run` si ferma.

| Cartella | Contenuto |
| --- | --- |
| `fixture/` | un modulo Go (`gin v1.12.0`, Go 1.25): gestori con nome, un metodo legato (`srv.List`, nome `…(*Server).List-fm`), chiusure (`/ping`, `auth()`), gruppi annidati con prefisso e middleware, la stessa funzione su due percorsi, `Any`, `Match`, `Static`, `StaticFile`, `NoRoute`, `Run` che blocca. Interruttori da variabile d'ambiente: `FIXTURE_FAIL=panic\|db\|block` (l'applicazione non si carica: panic, database `db.invalid:5432`, attesa senza fine prima delle rotte) e `FIXTURE_RELEASE=1` (`gin.SetMode(gin.ReleaseMode)` in `main()`). `go.sum` non c'è: lo fa `go mod tidy` nell'immagine |
| `hooks/hook_names.go` | un file che esiste solo nella compilazione di una copia (`go build -overlay`): imposta `gin.DebugPrintRouteFunc` e `gin.DebugPrintFunc`, scrive ogni rotta in un file e, alla riga «Listening and serving…» che ogni `Run*` stampa prima di legare la porta, esce con `os.Exit(0)` |
| `hooks/routes_in_init.go` | lo stesso meccanismo: nel suo `init` chiama il `setupRouter()` della fixture, scrive `Routes()` con file e riga (`runtime.FuncForPC(pc).FileLine(pc)`) ed esce prima di `main` (il nome `setupRouter` è una convenzione della documentazione dei test di Gin, non di ogni progetto) |
| `modal_probe.py` | costruisce l'immagine con la rete aperta (`go mod tidy`, `go mod download`, una `go build`), poi esegue ogni sonda senza rete; scrive `results/<sonda>.json` |

```
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 uv run --no-project --with modal python -m modal run benchmarks/gin-routes/modal_probe.py
```

## Letto dal sorgente di Gin 1.12.0 (non eseguito)

- `Routes()` (`gin.go:390`) percorre gli alberi per metodo (`iterate`, `gin.go:397`) e dà `RoutesInfo`, una lista di `RouteInfo{Method, Path, Handler string, HandlerFunc}` (`gin.go:68-76`). Per ogni nodo con gestori prende **solo l'ultimo** della catena (`root.handlers.Last()`, `gin.go:400`): i middleware di gruppo e di motore non compaiono. Non è nominata né nel README né in `docs/doc.md`: è documentata solo dal commento godoc.
- `Handler` è `nameOfFunction(f)` = `runtime.FuncForPC(reflect.ValueOf(f).Pointer()).Name()` (`utils.go:131`): un nome di simbolo, non un file. File e riga si ottengono da `HandlerFunc`, che è nel risultato: `fn.FileLine(pc)` con lo stesso `pc`. Chi ha solo il nome (gli hook) non ha né `HandlerFunc` né la riga.
- Che nome dà: funzione con nome `main.listItems`; metodo legato `main.(*Server).List-fm` (il nome del wrapper del compilatore: da misurare dove punta la riga); chiusura `main.setupRouter.func1`, e `main.auth.func1` per una fabbrica di middleware; `Static` registra una chiusura dentro Gin (`createStaticHandler`, `routergroup.go:216`: nome `…(*RouterGroup).createStaticHandler.func1`, file e riga **di Gin**, non del progetto); `StaticFile` idem.
- Gruppi: `Group` (`routergroup.go:72`) ha `basePath` e `Handlers`; `handle` (`routergroup.go:86`) calcola il percorso assoluto (`calculateAbsolutePath`) e combina i gestori (`combineHandlers`): `Routes()` dà il percorso già completo, il gestore è l'ultimo. `Any` (`routergroup.go:147`) registra nove metodi (`anyMethods`, `routergroup.go:19`: nove righe, stesso gestore); `Match` uno per metodo; `StaticFS` registra `GET` e `HEAD` su `/*filepath`.
- `NoRoute` (`gin.go:326`) scrive `engine.noRoute` (campo non esportato): **non è in `Routes()`**, nessuna interfaccia pubblica lo dà. Anche `NoMethod`.
- `gin.DebugPrintRouteFunc` (`debug.go:27`) è una variabile pubblica, documentata in `docs/doc.md` («Define format for the log of routes», da riga 2330, con l'esempio): `func(httpMethod, absolutePath, handlerName string, nuHandlers int)`. La chiama `addRoute` a ogni registrazione (`gin.go:364-369` → `debugPrintRoute`, `debug.go:32`) **solo se `IsDebugging()`**: dà il nome del gestore (l'ultimo) e quanti gestori ha la catena, non `HandlerFunc`, non il file. `gin.DebugPrintFunc` (`debug.go:30`) riceve ogni altra riga di debug, e `Run`, `RunTLS`, `RunUnix`, `RunFd`, `RunQUIC`, `RunListener` stampano «Listening and serving …» **prima** di legare (`gin.go:549, 562, 582, 608, 631, 646`): un `os.Exit` da lì ferma il processo prima che la porta si apra. Senza l'hook il testo è `[GIN-debug] GET /items --> main.listItems (3 handlers)` (`debug.go:37`) su `gin.DefaultWriter` (standard output): formato di un log, non un contratto, ma il formato del log delle rotte è quello che la documentazione descrive.
- La modalità: `GIN_MODE` (`mode.go`, `init`), predefinita `debug`; `gin.SetMode` in `main()` la cambia dopo l'`init` di qualunque file aggiunto: se l'applicazione chiama `gin.SetMode(gin.ReleaseMode)`, gli hook tacciono (`IsDebugging()` falso) e `Run` resta in ascolto.

## Il problema: come si ottiene il motore senza modificare il progetto

Gin non ha un registro dei motori: il motore sta in una variabile di `main()` (o dove il progetto lo mette) e `Run` blocca. Non esiste un modo ufficiale di chiamare `Routes()` su un progetto qualsiasi; l'unico dato ufficiale che non chiede il motore sono i due hook sopra.

| Via | Che cos'è | Dà | Limite |
| --- | --- | --- | --- |
| Hook (`hook_names.go`) con `-overlay` | `-overlay` è un flag documentato di `go build` (`go help build`: «provides an overlay for build operations»): il file esiste solo per quella compilazione, l'albero non cambia; ma è comunque una compilazione della copia con un file in più nel pacchetto `main`. Va detto così: il progetto non è modificato, il suo binario non è quello che si distribuisce | metodo, percorso completo, nome del gestore, numero di gestori | niente `HandlerFunc` né file e riga (si risolvono dal nome con `go tool nm` e `go tool addr2line`, o dallo snapshot); tace con `SetMode(release)` o `GIN_MODE=release`; `NoRoute` assente; funziona solo se `Run*` è chiamato (con `http.Server{Handler: r}` a mano non c'è il segnale d'arresto: resta il tempo limite) |
| `Routes()` da un file aggiunto | lo stesso `-overlay`, un `init` che chiama una funzione del progetto | `HandlerFunc`, quindi file e riga dalla runtime | serve il nome della funzione che dà il motore: una convenzione, non un'interfaccia; non si generalizza |
| Testo di debug (`GIN_MODE=debug`, nessun file aggiunto) | l'uscita standard dell'applicazione | le stesse righe dell'hook, in testo | formato di log; `Run` lega la porta e va ucciso con un tempo limite |
| Delve | debugger di terzi, punto di arresto su `Run` e chiamata di `Routes()` sul motore | in principio tutto | non ufficiale, ha bisogno di `ptrace`, fragile; non sondato |
| Copia modificata di Gin (un `engine` che si registra) | un `-overlay` che sostituisce un file di Gin | il motore | modifica il framework, non il progetto; non è «lo strumento ufficiale»: non sondato |

Raccomandazione (da confermare con la misura): gli hook ufficiali con `-overlay`, fermati alla riga «Listening and serving» e con un tempo limite; il file e la riga si ricavano dal nome (`go tool nm` e `go tool addr2line` sul binario, o lo snapshot); `Routes()` resta il dato più ricco ma non si chiama in generale. Il progetto non è modificato nei file; è compilato con un file in più, in una copia, nel container.

## Che cosa la sonda misura (parametri)

| Domanda | Sonda | Che cosa si legge |
| --- | --- | --- |
| Gli hook danno ogni rotta, in che forma, e `Run` si ferma prima di legare? | `hook-names`; controllo `hook-no-stop` (la porta compare) | `written` (una riga JSON per rotta e per riga di debug), `ports_listening` (da `/proc/net/tcp`, ogni 50 ms), exit 0, `peak_memory_mb`, `seconds` |
| Il nome dà file e riga? | `hook-names`, campo `symbols` (`go tool nm` e `go tool addr2line`) | per ogni nome indirizzo e `file:line`, per funzione, metodo legato (`-fm`), chiusura, chiusura dentro Gin |
| Che cosa dà `Routes()` e dove punta `FileLine`? | `routes-in-init` | `Handler`, nome della runtime, file, riga, a confronto con `symbols`; i middleware assenti; `Any` = 9 righe; `NoRoute` assente |
| Gli hook tacciono in release? | `hook-release-env`, `hook-release-code` | nessuna rotta scritta, `Run` lega la porta, uscita 124 o 137 dal tempo limite |
| Senza file aggiunto? | `debug-stdout` | le righe `[GIN-debug]` sullo standard output |
| L'albero resta intatto? | ogni sonda | `left_in_the_project`, `changed_in_the_project` (vuoti attesi) |
| Un'applicazione che non si carica? | `app-panic`, `app-db`, `app-block`, `app-panic-routes-in-init` | exit, coda dello standard error, secondi al fallimento, nessuna rotta; `app-block` esce dal tempo limite con `processes_left` vuoto |
| Compilare senza rete | ogni sonda (`GOPROXY=off`) e `cold-build` (con la rete, cache vuote) | exit della compilazione, secondi, memoria; se `go mod download` basta come ripristino |

## Non coperto dalla sonda (aperto)

Progetti con `vendor/`, più moduli o `go.work`, `cgo`, tag di compilazione e `main` fuori dalla radice (`cmd/…`: l'argomento del pacchetto), Gin più vecchi di 1.12 (`go` 1.25 richiesto qui; i campi di `RouteInfo` sono anche in 1.9-1.11, da leggere), `gin.New()` creato dentro un pacchetto non `main`, più motori in un processo, `engine.Handler()` usato con `http.Server` propri, il legame del nome del simbolo con la funzione dello snapshot di scip-go (metodi legati `-fm`, chiusure, generici), il costo di una compilazione per ogni avvio, e Delve.

## Decisioni che aspettano la misura

Se gli hook con `-overlay` bastano come sorgente (e in quanti progetti veri `SetMode(release)` o un avvio che non arriva a `Run` li lascia muti: in quel caso resta una lacuna con la causa e i candidati di Noir), se `go tool addr2line` dà la riga della dichiarazione o della prima istruzione, la voce `go` in `container_runner.TOOLS` (immagine, cache, `GOPROXY=off`, `GOFLAGS=-mod=readonly`).

**Deciso dal proprietario il 23 novembre 2026:** costruire una copia del progetto con un file in più (`go build -overlay`, l'albero del progetto non cambia) conta come «senza modificare il progetto».
