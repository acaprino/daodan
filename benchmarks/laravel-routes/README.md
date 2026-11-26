# Laravel: `php artisan route:list` elenca le rotte con metodo, percorso e gestore?

Domanda: Laravel ha un comando documentato che elenchi le rotte registrate, da usare nel container come il task 14 chiede per gli altri framework? Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14d («prima si verifica un'uscita per le macchine»); forma come in [express-routes](../express-routes/README.md); spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6.

**Stato: verifica in sola lettura del 23 novembre 2026; nulla eseguito.** Nessuna applicazione Laravel caricata, nessun `artisan` lanciato, nessun PHP eseguito: la risposta viene dal testo dei sorgenti e della documentazione. Nessun codice nuovo, nessuna fixture, nessuna sorgente della pre-mappa.

**Risultato in una riga:** sì per il comando e per metodo, percorso e gestore come simbolo (`Classe@metodo`); il file e la riga ci sono solo per le closure. Il collegamento del simbolo a una dichiarazione del grafo oggi non è possibile: Daodan non ha né adattatore né indicizzatore PHP.

## Fonti lette

| Fonte | Versione | Come letta |
| --- | --- | --- |
| `laravel/framework` | v13.43.0 (ultima stabile in Packagist, 17 novembre 2026) | `https://raw.githubusercontent.com/laravel/framework/v13.43.0/src/Illuminate/<percorso>`; l'archivio (`codeload.github.com`, `api.github.com/.../zipball`, `github.com/.../archive`) risponde 403 dal proxy, quindi solo i file singoli |
| `laravel/docs` | ramo `13.x`, `routing.md` | `https://raw.githubusercontent.com/laravel/docs/13.x/routing.md` |

sha256 di `Foundation/Console/RouteListCommand.php`: `7c2f37d0131ae79beff31f2e95a49c4bbf9b0b77385c0cf3df9fb51fad01cfac`. Percorsi sotto relativi a `src/Illuminate/` della v13.43.0.

## Che cosa dicono

| Affermazione | Dove | Estratto |
| --- | --- | --- |
| Il comando è documentato, con `-v`, `-vv`, `--path`, `--except-vendor`, `--only-vendor` | `laravel/docs` 13.x `routing.md` righe 186-217 | «The `route:list` Artisan command can easily provide an overview of all of the routes» |
| `--json` esiste nel comando ma **non compare in `routing.md`** (nessuna occorrenza di «json»; cercata anche in `artisan.md`: nessuna) | `Foundation/Console/RouteListCommand.php` riga 29 | `{--json : Output the route list as JSON}` |
| Campi per rotta: il JSON è l'array `getRouteInformation` filtrato sulle colonne di `$headers` | righe 61, 156-168, 198-203, 390-400 | `domain`, `method`, `uri`, `name`, `action`, `middleware`, `path` (`vendor` è calcolato ma tolto da `pluckColumns`) |
| `method`: i metodi uniti da `\|` (es. `GET\|HEAD`); in JSON non viene sostituito da `ANY` (lo fa solo l'uscita per la console) | righe 160, 413 | `implode('\|', $route->methods())` |
| `middleware` in JSON è una lista; senza `-vv` i gruppi non sono espansi (`flushMiddlewareGroups`) | righe 106-108, 394 | `explode("\n", ...)` |
| `action` di un metodo di controller: `App\Http\Controllers\X@method` (senza `\` iniziale) | righe 163; `Routing/Route.php` righe 971-974; `Routing/RouteAction.php` righe 33-36 | `ltrim($route->getActionName(), '\\')`; `$action[0].'@'.$action[1]` |
| Controller invocabile: `Classe@__invoke` | `Routing/RouteAction.php` righe 45-47, 89-96 | `return $action.'@__invoke';` |
| Closure: `action` è la stringa `Closure`, e **solo qui** compare `path` = `file:riga` (relativo a `base_path()`, riga = `getStartLine()`) | `Route.php` riga 973; `RouteListCommand.php` righe 258-269 | `?? 'Closure'`; `ReflectionFunction` ... `.':'.$reflection->getStartLine()` |
| `Route::view`: `action` = `Illuminate\Routing\ViewController` (senza `@`), `path` nullo; il nome della vista sta nei default della rotta e non esce nell'elenco | `Routing/Router.php` righe 299-308; `RouteListCommand.php` righe 260-262 | `match(['GET','HEAD'], $uri, '\Illuminate\Routing\ViewController')` |
| `Route::redirect`: `action` = `Illuminate\Routing\RedirectController`, metodo `ANY` (tutti i verbi), `path` nullo, destinazione non nell'elenco | `Routing/Router.php` righe 270-275 | `any($uri, '\Illuminate\Routing\RedirectController')` |
| Rotta senza azione: closure interna che lancia `LogicException` | `Routing/RouteAction.php` righe 61-66 | `Route for [...] has no action.` |
| File e riga del **metodo** di un controller non compaiono: `-v` mostra solo il middleware, `--except-vendor`/`--only-vendor` filtrano e usano il file di una classe per decidere `vendor`, senza emetterlo | righe 277-297, 462 | `(new ReflectionClass($route->getControllerClass()))->getFileName()` (solo per il filtro) |
| Artisan avvia l'applicazione: carica `.env`, configurazione, registra e avvia tutti i provider; le rotte si caricano all'avvio del `RouteServiceProvider` (da `routes/*.php`, o da `bootstrap/cache/routes-v7.php` se in cache) | `Foundation/Console/Kernel.php` righe 127-135, 509-513; `Foundation/Support/Providers/RouteServiceProvider.php` righe 53-66 | `LoadEnvironmentVariables`, `LoadConfiguration`, ..., `RegisterProviders`, `BootProviders` |
| Senza `.env` il comando non si ferma: il caricamento è `safeLoad()`; si ferma (`exit(1)`) solo con un `.env` malformato | `Foundation/Bootstrap/LoadEnvironmentVariables.php` righe 29-31, 108 | `->safeLoad()` |

## Che cosa porterebbe una riga

Da `php artisan route:list --json` (rete non necessaria: nessuna parte del comando la usa):

- **metodo:** `method`, da spezzare su `|` (`GET|HEAD` è una rotta GET; `HEAD` è implicito);
- **percorso:** `uri` (con `domain` se presente; i campi di binding come `{post:slug}`);
- **gestore:** `action` come simbolo `Classe@metodo` (per gli invocabili `Classe@__invoke`); per le closure `path` = `file:riga`; per `view` e `redirect` il gestore è una classe del framework, quindi la rotta non ha un gestore del progetto (la vista o la destinazione sono dati della rotta, fuori dall'elenco);
- **contorno:** `name`, `middleware`.

La regola del task 14 («una riga ha metodo, percorso e funzione del gestore, con file e riga o un simbolo che lo snapshot sa trovare») è soddisfatta dalle closure (file e riga) e dai controller se lo snapshot trova `Classe::metodo`; non lo è per `view` e `redirect`, che restano rotte senza gestore proprio.

## La lacuna del linguaggio

Verificato in `daodan/core/languages/` e `daodan/core/indexers/`: nessun adattatore PHP (i moduli sono cfamily, csharp, go, java, javascript, kotlin, markup, plsql, python, rust, sfc, sql, stylesheet, typescript) e nessun indicizzatore PHP (clang, csharp, css*, go, java, jvm, kotlin, python, rust, typescript). Di PHP c'è solo la voce `"php": "php"` in `daodan/core/languages/_treesitter.py` riga 73 e il gestore di pacchetti `composer` in `daodan/core/support_table.py` riga 58. Quindi lo snapshot non ha simboli PHP e un `Classe@metodo` non si lega oggi a nessuna dichiarazione del grafo; le sole righe collegabili sarebbero le closure, e solo per file e riga.

Per chiudere servirebbe (senza deciderlo qui): un adattatore tree-sitter PHP (la grammatica esiste nel pacchetto di grammatiche già usato; da valutare se `Classe@metodo` si risolve con il suo `namespace` e il `use`), oppure un indicizzatore ufficiale (`scip-php`, da valutare nel container) per i simboli e le dichiarazioni.

## Che cosa deve misurare una prova su Modal prima di scrivere una sorgente

La prova gira nel container, mai sull'host: l'applicazione carica codice del progetto (provider, `routes/*.php`, `composer install` con script), quindi vale la regola invalicabile di `AGENTS.md`. Da misurare, su almeno un'applicazione Laravel vera e una con rotte miste (controller, invocabile, closure, `view`, `redirect`, gruppi con prefisso e dominio, rotte di un pacchetto):

1. **Avvio senza rete e senza database:** `php artisan route:list --json` parte con un `.env` assente o di esempio (`APP_KEY` mancante, `DB_*` non raggiungibile)? Quali provider del progetto o dei pacchetti toccano la rete o il database all'avvio (`boot()`), e che cosa succede allora (eccezione, uscita non zero, JSON vuoto)? Con `bootstrap/cache/routes-v7.php` presente le rotte vengono dalla cache: contano come lettura fedele?
2. **Forma reale dell'uscita:** il JSON è l'unico contenuto su stdout (nessun avviso, nessuna intestazione prima dell'array)? Presenza e valore dei sette campi, `method` con `|`, `middleware` con e senza `-vv`, `path` solo per le closure, `[]` senza rotte (riga 112) contro il testo d'errore.
3. **Il simbolo trova la dichiarazione:** per ogni `Classe@metodo` quante righe si legano a una dichiarazione (con l'adattatore o lo SCIP scelto) e quante no (controller di pacchetti, alias, azioni dinamiche); quante rotte sono `view`/`redirect` e restano senza gestore.
4. **Costo:** tempo e memoria dell'avvio su un'applicazione grande, e il numero di rotte rispetto a quelle trovate da Noir sulla stessa applicazione (a cui questa sorgente si aggiungerebbe o si sostituirebbe: da misurare, non deciso).
5. **Isolamento:** il test di AGENTS.md per ogni strumento lanciato: un file del progetto (un provider o un `routes/web.php`) che, eseguito, lascia un segno, e la prova che fuori dal container il segno non compare.

## Non verificato

- Nulla è stato eseguito: forma reale dell'uscita, comportamento senza `.env` oltre `safeLoad()`, senza database o con provider che toccano la rete non sono misurati (solo letti).
- `--json` è nel sorgente ma non in `routing.md` (13.x) né in `artisan.md`: non è provato che sia documentato altrove (per esempio nell'aiuto `php artisan route:list --help`, che lo stampa dal `$signature`); la stabilità dell'opzione tra le versioni non è confrontata (letta solo la v13.43.0; versioni 10-12 non lette).
- Il testo del ramo `13.x` della documentazione è stato letto dal ramo, non da un tag.
- L'archivio del framework non è scaricabile dal proxy (403): letti solo i file `RouteListCommand.php`, `Route.php`, `RouteAction.php`, `Router.php`, `Foundation/Console/Kernel.php`, `RouteServiceProvider.php`, `LoadEnvironmentVariables.php`.
- Non provato se la grammatica PHP è disponibile nel pacchetto di grammatiche usato da `_treesitter.py` (c'è la voce di mappa, non la prova che si carichi); `scip-php` non letto.
