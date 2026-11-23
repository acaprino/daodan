# Expo Router: i tipi generati

Stato: **aperto, non misurato**. Nessuna credenziale Modal in questa sessione: nessuna fixture è stata caricata nel container e nessun codice di Expo è stato eseguito. Non c'è sorgente della pre-mappa, né voce in `container_runner.TOOLS`, né risposte registrate, né test. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14i; spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6.

## Letto nei sorgenti, non eseguito (23 novembre 2026)

`expo-router` 5.1.4 (`https://registry.npmjs.org/expo-router/-/expo-router-5.1.4.tgz`, sha256 `8f847e4d7a844997a0e553f42175b0627809e075d1cf91b83b579e2b93523d02`):

- `build/typed-routes/index.js` scrive `router.d.ts` in una cartella di uscita (`regenerateDeclarations`, riga ~80), da un `require.context` su `EXPO_ROUTER_APP_ROOT`; il file dice di essere importato da `@expo/cli`: la generazione parte dall'interno del server di sviluppo.
- `getTypedRoutesDeclarationFile` (`build/typed-routes/generate.js` riga 13) chiama `getRoutes` ignorando i layout (`_layout`), e scrive solo tre unioni di tipi (`hrefInputParams`, `hrefOutputParams`, `href`) di **percorsi**: nessun nome di file. I gruppi `(x)` sono modelli di testo. Quindi, se la lettura regge, i tipi generati danno le rotte ma non il file di ciascuna: il file si ricostruirebbe solo invertendo a mano il percorso, una regola scritta a mano che la regola d'oro non ammette.
- Il file che dà rotta e file (`contextKey`) è il risultato di `getRoutes`, una funzione interna di `expo-router`, non un'interfaccia documentata: **non valutata**.
- `package.json` non ha una voce `bin` (letto): nessun comando proprio di `expo-router`; i comandi sono di `@expo/cli` (`expo customize`, `expo start`), che non è stato letto.

## Da misurare su Modal

1. Se `npx expo customize tsconfig.json` (o altro comando di `@expo/cli`) scrive `router.d.ts` / `expo-env.d.ts` senza aprire una porta né il server di sviluppo, e in quale cartella.
2. Che cosa contiene davvero (percorsi soltanto, o anche i file); se `+api.ts`, `+not-found`, `_sitemap`, i layout e i gruppi `(x)` compaiono, e con quale forma.
3. Se un'interfaccia pubblica (non interna) dà rotta e file; altrimenti la voce si ferma con la causa e restano i candidati di Noir.
4. Tempo, memoria, file lasciati nel progetto, senza rete, e con un'applicazione che non si carica; `app.json` / `app.config.ts` è codice del progetto (solo nel container).

Non scritto: la fixture e `modal_probe.py`.
