# Expo Router: i tipi generati

**Stato:** Aperta: da approfondire. Un comando di `@expo/cli` scrive i tipi delle rotte senza avviare il server di sviluppo, e che cosa contengono? Letto nei sorgenti, mai eseguito: nessuna fixture, nessuna sonda, nessuna sorgente della pre-mappa, nessuna voce in `container_runner.TOOLS`. Nel prodotto le rotte di Expo Router sono quelle di Noir (solo i moduli `+api`).

## Domanda

Expo Router dà, con uno strumento ufficiale eseguito nel container, ogni rotta con il suo file? Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14i del piano).

## Strumento letto

`expo-router` 5.1.4 (`https://registry.npmjs.org/expo-router/-/expo-router-5.1.4.tgz`, sha256 `8f847e4d7a844997a0e553f42175b0627809e075d1cf91b83b579e2b93523d02`), letto il 23 novembre 2026:

- `build/typed-routes/index.js` scrive `router.d.ts` (`regenerateDeclarations`, riga ~80) da un `require.context` su `EXPO_ROUTER_APP_ROOT`; il file dice di essere importato da `@expo/cli`: la generazione parte dal server di sviluppo.
- `getTypedRoutesDeclarationFile` (`build/typed-routes/generate.js` riga 13) chiama `getRoutes` ignorando i layout e scrive tre unioni di tipi (`hrefInputParams`, `hrefOutputParams`, `href`) di percorsi: nessun nome di file. Ricostruire il file invertendo il percorso sarebbe una regola scritta a mano, che la regola d'oro non ammette.
- Rotta e file (`contextKey`) li dà `getRoutes`, funzione interna e non documentata: non valutata.
- `package.json` non ha `bin`: i comandi sono di `@expo/cli` (`expo customize`, `expo start`), non letto.

## Risultato valido oggi

Nessuna misura. Su tre applicazioni vere Noir dà 36 endpoint dei moduli `+api` e 32 dei 34 con nome si legano ([noir-binding](../noir-binding/README.md)); le schermate (`app/…`) non sono nel report di Noir. Se il passo dinamico le osserva (l'esplorazione nel browser di `daodan/core/dynamic/app.py` riguarda le app web): non misurato.

## Aperto, da misurare su Modal

1. Se `npx expo customize tsconfig.json` (o un altro comando di `@expo/cli`) scrive `router.d.ts` o `expo-env.d.ts` senza aprire una porta né il server di sviluppo, e in quale cartella.
2. Che cosa contiene (solo percorsi, o anche i file); come compaiono `+api.ts`, `+not-found`, `_sitemap`, i layout e i gruppi `(x)`.
3. Se un'interfaccia pubblica dà rotta e file; altrimenti la voce si chiude con la causa e restano i candidati di Noir.
4. Tempo, memoria, file lasciati nel progetto, senza rete, e con un'applicazione che non si carica; `app.json` e `app.config.ts` sono codice del progetto (solo nel container).

Da scrivere prima: la fixture e `modal_probe.py`.
