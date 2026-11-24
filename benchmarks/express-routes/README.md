# Express: esiste un'interfaccia pubblica che elenca le rotte?

**Stato:** Scartato: Express non ha un'interfaccia pubblica che elenchi le rotte. Nessuna sorgente della pre-mappa, nessun codice; nel prodotto le rotte di Express sono quelle di Noir.

## Domanda

Express (o il suo `router`) ha un'interfaccia o un comando documentato che elenchi le rotte registrate, da usare nel container? Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14j del piano).

## Strumento valutato e metodo

Sola lettura, 23 novembre 2026: documentazione ufficiale e testo dei sorgenti. Nulla di Express è stato eseguito. I tarball sono dati: `curl -fsSLO <url>`, `sha256sum`, `tar xzf`, poi `grep`.

| Pacchetto | Tarball del registro | sha256 del `.tgz` |
| --- | --- | --- |
| `express` 4.21.2 | `https://registry.npmjs.org/express/-/express-4.21.2.tgz` | `fc43a91e7dc7affb53c6ad7123a4f35485ed3c45226ae7a3847b7738e783e008` |
| `express` 5.1.0 | `https://registry.npmjs.org/express/-/express-5.1.0.tgz` | `dd6bdb4d4e54d520c78443d5c35aa4ae552be1837e8650d2ec1641df99393e1b` |
| `router` 2.2.0 | `https://registry.npmjs.org/router/-/router-2.2.0.tgz` | `b144af37b39a9517f7a89f1d867e9c2cf29f13f4147d3e80c499fe6ffab69461` |
| `express-list-endpoints` 7.1.1 (terzi) | `https://registry.npmjs.org/express-list-endpoints/-/express-list-endpoints-7.1.1.tgz` | `f051987be8fde75e68fd0fb4d7495620c993b27dc23c214612067e48db13ecfa` |

## Risultato

| Affermazione | Dove | Estratto |
| --- | --- | --- |
| In Express 4 la pila è `app._router`, creata dalla funzione marcata privata | `express-4.21.2/lib/application.js` righe 142-146 | `@private` / `app.lazyrouter = function lazyrouter() { if (!this._router) {` |
| In Express 5 `app.router` è una proprietà pigra, documentata come «istanza del router», non come elenco | `express-5.1.0/lib/application.js` righe 69-80; `https://expressjs.com/en/5x/api/application` | «The application's in-built instance of router. This is created lazily, on first access.» |
| La pagina Application di Express 4 non ha `app.router` | `https://expressjs.com/en/4x/api/application` | (assenza) |
| Le pagine Router (4.x e 5.x) documentano `Router()`, `router.all`, `router.METHOD`, `router.param`, `router.route`, `router.use`; né `stack` né un modo di elencare | `https://expressjs.com/en/4x/api/router`, `https://expressjs.com/en/5x/api/router` | (assenza) |
| Il pacchetto `router` ha `router.stack`, ma il README non lo documenta | `router-2.2.0/index.js` riga 70; `README.md` riga 116 parla solo di `.use` | `router.stack = []` |
| `express-list-endpoints` legge `app.stack` o `app._router.stack` e ricostruisce il percorso con quattro espressioni regolari sul testo di `layer.regexp` | `express-list-endpoints-7.1.1/dist/index.js` righe 3-6, 66, 103-106 | `const stack = app.stack \|\| (app._router && app._router.stack);` |
| Lo stesso strumento dichiara di non funzionare con Express 5 | `express-list-endpoints-7.1.1/README.md` riga 4 | «This package only works for express 4.* versions. It's not compatible with express 5 yet.» |
| In `router` 2.x il `Layer` non ha `regexp`: ha `matchers` (funzioni) | `router-2.2.0/lib/layer.js` riga 93 | `this.matchers = Array.isArray(path) ? path.map(matcher) : [matcher(path)]` |

`express-list-endpoints` è un lettore scritto a mano su campi interni, senza file né riga del gestore, e non funziona con Express 5: valutato, non usato (regola d'oro di `AGENTS.md`).

Le rotte di Express nel prodotto sono quelle di Noir (`daodan/core/premap/noir.py`). Quante si legano a una funzione, su tre applicazioni vere, è misurato in [noir-binding](../noir-binding/README.md). Se il passo dinamico osserva i gestori che Noir non lega: non misurato dopo il passo dinamico.

## Aperto

- Le pagine API sono state lette troncate (circa 40.000 di 66.000 caratteri per la pagina Application): l'assenza di `stack` in tutta la pagina non è provata; va riletta nel sorgente della documentazione (`expressjs/expressjs.com`) prima di citarla come definitiva.
- Che cosa `router.stack` contiene a runtime non è misurato; `express-list-endpoints` su Express 5, `router` 1.x ed Express sotto la 4.21 non sono letti.
- Il risolutore di Express e Hono di GitNexus (task 17 del piano) resta da valutare eseguendolo.
