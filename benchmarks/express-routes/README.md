# Express: esiste un'interfaccia pubblica che elenca le rotte?

Domanda: Express (o il suo `router`) ha un'interfaccia o un comando documentato che elenchi le rotte registrate, da usare nel container come il task 14 chiede per gli altri framework? Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14j; spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6.

**Risultato in una riga:** no. Nelle pagine ufficiali e nei sorgenti letti nessuna interfaccia pubblica elenca le rotte; l'unico accesso è la pila interna del router (`router.stack`), che la documentazione non descrive. Le rotte di Express restano quelle di Noir, con la lacuna e la causa. **Nessun codice nuovo, nessuna sorgente della pre-mappa.**

**Metodo e limite: sola lettura.** Niente di Express è stato eseguito (nessuna applicazione caricata, nessun `router.stack` stampato): la risposta viene dalla documentazione e dal testo dei sorgenti. È la risposta che la voce chiede («prima si cerca un'interfaccia pubblica»), ma non misura che cosa `router.stack` contiene a runtime.

## Fonti lette (23 novembre 2026)

| Pacchetto | Tarball del registro | sha256 del `.tgz` |
| --- | --- | --- |
| `express` 4.21.2 | `https://registry.npmjs.org/express/-/express-4.21.2.tgz` | `fc43a91e7dc7affb53c6ad7123a4f35485ed3c45226ae7a3847b7738e783e008` |
| `express` 5.1.0 | `https://registry.npmjs.org/express/-/express-5.1.0.tgz` | `dd6bdb4d4e54d520c78443d5c35aa4ae552be1837e8650d2ec1641df99393e1b` |
| `router` 2.2.0 | `https://registry.npmjs.org/router/-/router-2.2.0.tgz` | `b144af37b39a9517f7a89f1d867e9c2cf29f13f4147d3e80c499fe6ffab69461` |
| `express-list-endpoints` 7.1.1 (terzi) | `https://registry.npmjs.org/express-list-endpoints/-/express-list-endpoints-7.1.1.tgz` | `f051987be8fde75e68fd0fb4d7495620c993b27dc23c214612067e48db13ecfa` |

Per ripetere la lettura (da una cartella vuota; i tarball sono dati, non si installano né si eseguono): `curl -fsSLO <url>` per ognuno, `sha256sum *.tgz`, `tar xzf`, poi i `grep` sotto.

## Che cosa dicono

| Affermazione | Dove | Estratto |
| --- | --- | --- |
| In Express 4 la pila è `app._router`, creata dalla funzione marcata privata | `express-4.21.2/lib/application.js` righe 142-146 | `@private` / `app.lazyrouter = function lazyrouter() { if (!this._router) {` |
| In Express 5 `app.router` è una proprietà pigra, documentata come «istanza del router», non come elenco | `express-5.1.0/lib/application.js` righe 69-80; pagina `https://expressjs.com/en/5x/api/application` | «The application's in-built instance of router. This is created lazily, on first access.» |
| La pagina Application di Express 4 non ha `app.router`: le proprietà sono `app.locals` e `app.mountpath` | `https://expressjs.com/en/4x/api/application` | (assenza) |
| Le pagine Router (4.x e 5.x) documentano `Router()`, `router.all`, `router.METHOD`, `router.param`, `router.route`, `router.use`; né `stack` né un modo di elencare | `https://expressjs.com/en/4x/api/router`, `https://expressjs.com/en/5x/api/router` | (assenza) |
| Il pacchetto `router` ha `router.stack`, ma il README non lo documenta | `router-2.2.0/index.js` riga 70; `README.md`: l'unica occorrenza di «stack» (riga 116) parla di `.use` | `router.stack = []` |
| `express-list-endpoints` legge `app.stack` o `app._router.stack` e ricostruisce il percorso con quattro espressioni regolari sul testo di `layer.regexp` | `express-list-endpoints-7.1.1/dist/index.js` righe 3-6, 66, 103-106 | `const stack = app.stack \|\| (app._router && app._router.stack);` |
| Lo stesso strumento dichiara di non funzionare con Express 5 | `express-list-endpoints-7.1.1/README.md` riga 4 | «This package only works for express 4.* versions. It's not compatible with express 5 yet.» |
| In `router` 2.x il `Layer` non ha `regexp`: ha `matchers` (funzioni) | `router-2.2.0/lib/layer.js` riga 93 | `this.matchers = Array.isArray(path) ? path.map(matcher) : [matcher(path)]` |

`express-list-endpoints` non è un'interfaccia del framework: è un lettore scritto a mano su campi interni (con espressioni regolari sul testo di un'espressione regolare), non dà il file né la riga del gestore, e per Express 5 non funziona. Contro la regola d'oro di `AGENTS.md` («mai una regola scritta a mano sulla forma di un caso»): valutato, non usato.

## Non verificato

- Le pagine API sono state lette da un agente che ha ricevuto le pagine troncate (circa 40.000 di 66.000 caratteri per la pagina Application): la parte oltre il troncamento è un riassunto di un modello e non vale come prova. Le citazioni letterali sopra sono nella parte letta; l'assenza di `stack` in tutta la pagina non è provata, e va riletta nel sorgente della documentazione (`expressjs/expressjs.com`) prima di citarla come definitiva.
- Nulla è stato eseguito: nessun `router.stack` stampato, nessuna applicazione caricata, nessuna misura di tempo o memoria.
- `express-list-endpoints` su Express 5 non è provato (lo dice il suo README); altre versioni (`router` 1.x, Express 4 sotto la 4.21) e altri strumenti di terzi non sono letti.
- Il risolutore di Express e Hono di GitNexus (task 17) resta «da valutare eseguendolo».

## Metodo di GitNexus (27 novembre 2026, `T1.C.2`)

**Versione di partenza:** `abhigyanpatwari/GitNexus`, commit `acf755a1b70ea91208aac9437c2a552579a62b70` (27 novembre 2026), pacchetto `gitnexus` 1.6.12 (`gitnexus/package.json`). Licenza PolyForm Noncommercial 1.0.0 (`LICENSE`): qui c'è solo il metodo, descritto con parole nostre; nessuna riga di codice, query o tabella è copiata. Lettura da un clone in una cartella temporanea, nulla eseguito. A ogni versione nuova si rileggono le novità di questi file e si aggiorna questa sezione (e il modulo di `T1.C.8`).

File letti (sotto `gitnexus/src/core/ingestion/route-extractors/`): `framework-route-types.ts` (i fatti), `framework-route-facts.ts` (dall'albero ai fatti, per file), `framework-route-resolver.ts` (i fatti di tutti i file risolti insieme), `framework-route-paths.ts` (composizione dei prefissi), `route-path.ts` (unione di prefisso e percorso).

**Il metodo in due tempi.**

1. *Per file, dall'albero tree-sitter già letto (nessun secondo parser):* ogni dichiarazione, import (ESM e `require`), esportazione (`export`, `export *`, `module.exports`/`exports.x`) e ogni assegnazione diventano un piccolo valore simbolico (sconosciuto, funzione, array, nome legato, import, membro, chiamata). Si registrano le chiamate a membro con nome `get`, `post`, `put`, `delete`, `patch`, `all`, `route`, `use` (destinatario, argomenti, percorso del primo argomento se è una stringa letterale che inizia con `/` o un array di sole stringhe così, riga), le chiamate a funzioni semplici o importate (per i parametri inoltrati, sotto) e le scritture di proprietà su un valore (che lo rendono incerto).
2. *Su tutto il progetto:* i valori si valutano seguendo nomi, import ed esportazioni fra file (con il risolutore di moduli del progetto, non con ipotesi sul file system; un `export *` ambiguo non dà valore), con limiti di profondità e di passi.

**Come riconosce un'app o un router.** Un valore è un'app se è la chiamata del valore predefinito importato dal pacchetto `express` (import, `require` o namespace), un router se è la chiamata di `Router` importato da `express` o letto come membro di esso; un'istanza di Hono è `new` di `Hono` importato da `hono`. Se il risolutore del progetto manda lo specificatore a un file del repository (alias di `tsconfig`), quel file vince sul nome del pacchetto. Ogni chiamata che crea un'istanza ne è l'identità; un nome legato a più valori, o un'istanza su cui il codice scrive una proprietà, non si risolve più (incerta, non indovinata).

**Come compone i prefissi di `use` fra file.** `x.use(prefisso?, ...figli)` su un'app o un router dà un arco «montaggio» da `x` a ogni figlio che si valuta a un router o un'app (anche dentro array, anche importato da un altro file); il prefisso è il percorso letterale, oppure vuoto se il primo argomento è già un gestore o un router, oppure *ignoto* se non è letterale. Poi, per ogni gruppo di istanze collegate, si parte dalle istanze che nessuno monta e si scende accumulando i prefissi (più prefissi danno più percorsi; i cicli si fermano; oltre un tetto di espansioni il gruppo non dà rotte). Un figlio montato con prefisso ignoto non ha prefissi: le sue rotte non escono, invece di uscire alla radice. Un solo salto attraverso una funzione: se il destinatario, il percorso o il figlio di una chiamata è un parametro di una funzione con nome, si prende l'argomento di ciascuna chiamata a quella funzione (niente catene di inoltri).

**Che cosa fa di:**

- *un gestore scritto sul posto:* è un valore «funzione» identificato dalla posizione nel file; il nome dato alla rotta è quello posizionale che il resto del grafo dà alla funzione senza nome;
- *un gestore con nome:* il nome resta solo se è un identificatore legato, nello stesso file e una sola volta, a una dichiarazione di funzione; un parametro, un alias importato o un valore ignoto non prendono il nome di un'altra funzione omonima;
- *un array di gestori o una catena di middleware:* conta l'ultimo argomento della chiamata come gestore; gli altri non sono rotte;
- *`route(p).get(h).post(h2)`:* `route` con percorso letterale su un'app o un router dà un costruttore che porta il percorso; ogni verbo concatenato registra una rotta su quel percorso e sul destinatario originale (con un solo argomento basta);
- *un percorso non letterale* (variabile, template, concatenazione): la rotta non esce; un `use` con prefisso non letterale fa sparire le rotte del figlio (sopra);
- *Hono:* solo i verbi con percorso letterale su `new Hono()`; `route` e `basePath` di Hono non compongono prefissi (le rotte escono con il percorso scritto).

I metodi sono `get`, `post`, `put`, `delete`, `patch` e `all` (che diventa «ogni metodo»); `head`, `options` e gli altri verbi di Express non sono letti. Le rotte uguali (file, riga, metodo, percorso, nome) si fondono.

**Che cosa ne prende Daodan (`T1.C.8`):** il metodo (valori simbolici dall'albero, montaggi come archi, prefissi composti dalle radici, prefisso ignoto come lacuna con la causa), non il codice. Il legame al gestore in Daodan è lo `span` della funzione (uguaglianza di due dati), non il nome posizionale di GitNexus; le forme di chiamata e i metodi sono dati in `daodan/data/entry-queries.json`, sezione `express`.

**Strumenti valutati, accanto:** nessuna interfaccia pubblica di Express elenca le rotte (sezioni sopra); `express-list-endpoints` 7.1.1 legge campi interni (`app._router.stack`, `layer.regexp` con espressioni regolari), non dà file né riga del gestore e non regge Express 5 (sopra); Noir 1.5.0 dà le rotte ma lega male i gestori (la base sotto). Per questo il lettore resta un modulo nostro (`T1.C.8`).

### La base da battere: Noir 1.5.0 sulle tre applicazioni Express

Dai risultati già nel repository (`benchmarks/noir-binding/results/summary.json`, `by_framework.express`; `results/after.json`, `applications`), applicazioni e commit di `benchmarks/noir-binding/apps.py`, Noir 1.5.0 (`apps.NOIR`). Nessuna corsa nuova.

| Applicazione | Commit | Noir | `http` | con nome del gestore | legati per nome (prima misura) | legati dal legatore di oggi | non legati |
| --- | --- | --- | --- | --- | --- | --- | --- |
| node-express-boilerplate | `179ae84efec6` | 15 | 15 | 13 | 0 | 13 | 2 |
| anything-llm | `593c0943facb` | 426 | 424 | 354 | 4 | 354 | 70 |
| juice-shop | `c9f99228d9d5` | 206 | 188 | 117 | 1 | 106 | 82 |
| **Totale** | | **647** | **627** | **484** | **5** | **473** | **154** |

«Legati dal legatore di oggi» è `bound_now` di `after.json`: la seconda versione del legatore (posizione e nome concorde), misurata con una copia congelata il 24 novembre; `daodan/core/binder.py` di develop (`d8bf191`) ha la stessa impronta registrata nel README di `noir-binding` (`ffc1518965192abd`), mentre `flows.py` e `premap/noir.py` sono cambiati da allora: la cifra vale per quel legatore, non è rimisurata qui. Dei 627 `http`, 143 non hanno un nome di gestore da Noir (70 di anything-llm vengono da un `.json`), e dei 484 con nome 11 di juice-shop sono fabbriche non legate (`servePublicFiles()`). **Il modulo di `T1.C.8` si collega (`T1.C.9`) solo se lega almeno 473 rotte su queste tre applicazioni, senza legami sbagliati nel campione.**
