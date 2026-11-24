# Laravel: `php artisan route:list` elenca le rotte con metodo, percorso e gestore?

**Stato:** Aperta: da approfondire. Il comando c'è e dà il gestore come simbolo, ma Daodan non legge PHP: la domanda è se un lettore PHP venga prima di `route:list`. Strumento letto, mai eseguito: nessuna fixture, nessuna sorgente della pre-mappa. Nel prodotto le rotte di Laravel sono quelle di Noir, e nessuna si lega a una funzione.

## Domanda

Laravel ha un comando documentato, con un'uscita per le macchine, che elenchi le rotte registrate con metodo, percorso e gestore, da usare nel container? Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14d del piano).

## Strumento letto

Sola lettura, 23 novembre 2026: nessun `artisan` lanciato, nessun PHP eseguito.

| Fonte | Versione | Come letta |
| --- | --- | --- |
| `laravel/framework` | v13.43.0 (ultima stabile in Packagist, 17 novembre 2026) | `https://raw.githubusercontent.com/laravel/framework/v13.43.0/src/Illuminate/<percorso>`; l'archivio (`codeload.github.com`, `api.github.com/.../zipball`, `github.com/.../archive`) risponde 403 dal proxy, quindi solo i file singoli |
| `laravel/docs` | ramo `13.x`, `routing.md` | `https://raw.githubusercontent.com/laravel/docs/13.x/routing.md` |

sha256 di `Foundation/Console/RouteListCommand.php`: `7c2f37d0131ae79beff31f2e95a49c4bbf9b0b77385c0cf3df9fb51fad01cfac`. Percorsi sotto relativi a `src/Illuminate/` della v13.43.0.

## Risultato

Sì per il comando e per metodo, percorso e gestore come simbolo (`Classe@metodo`); file e riga ci sono solo per le closure.

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

Una riga di `php artisan route:list --json` (nessuna parte del comando usa la rete) porterebbe:

- **metodo:** `method`, da spezzare su `|` (`GET|HEAD` è una rotta GET);
- **percorso:** `uri` (con `domain` se presente);
- **gestore:** `action` come simbolo `Classe@metodo` (`Classe@__invoke` per gli invocabili); per le closure `path` = `file:riga`; per `view` e `redirect` il gestore è una classe del framework, quindi la rotta non ha un gestore del progetto;
- **contorno:** `name`, `middleware`.

## Che cosa lo ferma oggi

Daodan non ha né adattatore né indicizzatore PHP (verificato in `daodan/core/languages/` e `daodan/core/indexers/`): di PHP ci sono solo la voce `"php": "php"` in `daodan/core/languages/_treesitter.py` e il gestore di pacchetti `composer` in `daodan/core/support_table.py`. Lo snapshot non ha simboli PHP e un `Classe@metodo` non si lega a nessuna dichiarazione.

Misurato su due applicazioni vere in [noir-binding](../noir-binding/README.md), «Laravel e Rails»: Noir dà già controller, azione, file e riga per la gran parte degli endpoint, `route:list` aggiungerebbe il gestore a poche rotte, e nessun endpoint si lega finché lo snapshot non ha dichiarazioni PHP. I numeri sono lì. Se il passo dinamico osserva i gestori: non misurato (nessun osservatore PHP in `daodan/core/dynamic/`).

## Aperto

- **Prima un lettore PHP:** un adattatore tree-sitter PHP (da valutare se `Classe@metodo` si risolve con `namespace` e `use`; che la grammatica si carichi dal pacchetto usato da `_treesitter.py` non è provato) oppure un indicizzatore ufficiale (`scip-php`, non letto, da provare nel container).
- **Poi una prova su Modal**, su un'applicazione vera e una con rotte miste (controller, invocabile, closure, `view`, `redirect`, gruppi con prefisso e dominio, rotte di un pacchetto):
  1. avvio senza rete e senza database, con `.env` assente o di esempio; quali provider toccano rete o database in `boot()`; le rotte lette da `bootstrap/cache/routes-v7.php` contano come lettura fedele?
  2. forma reale dell'uscita: il JSON è l'unico contenuto su stdout, i sette campi, `middleware` con e senza `-vv`, `[]` senza rotte;
  3. quanti `Classe@metodo` si legano a una dichiarazione e quanti no (controller di pacchetti, alias, azioni dinamiche);
  4. tempo e memoria su un'applicazione grande, e le rotte rispetto a quelle di Noir;
  5. il test di isolamento di `AGENTS.md`: un file del progetto che, eseguito, lascia un segno.
- **Non verificato:** `--json` è nel sorgente ma non in `routing.md` né in `artisan.md` (13.x), e la sua stabilità fra le versioni non è confrontata (letta solo la v13.43.0); la documentazione è letta dal ramo, non da un tag; dell'archivio del framework sono letti solo i file citati (il proxy rispondeva 403 all'archivio).
