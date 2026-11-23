# NestJS: `SwaggerModule.createDocument`

Stato: **aperto, non misurato**. Nessuna credenziale Modal in questa sessione: nessuna fixture è stata caricata nel container e nessun codice di NestJS è stato eseguito. Non c'è sorgente della pre-mappa, né voce in `container_runner.TOOLS`, né risposte registrate, né test: sarebbero risultati inventati. Piano: [ingressi e flussi](../../docs/plans/2026-11-20-ingressi-e-flussi.md), task 14h; spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6.

## Letto nei sorgenti, non eseguito (23 novembre 2026)

`@nestjs/swagger` 11.2.0 (`https://registry.npmjs.org/@nestjs/swagger/-/swagger-11.2.0.tgz`, sha256 `87aad2d582050994861df64ca695afdd89031e53e55b554ef9ce63b2d2d0e582`) e `@nestjs/core` 11.1.6 (`https://registry.npmjs.org/@nestjs/core/-/core-11.1.6.tgz`, sha256 `5c304658ce367917da2f9170a728ced29e3101606c539e98ab6e05cf63b53bc3`):

- `createDocument` accetta l'opzione `operationIdFactory(controllerKey, methodKey, version)` (`dist/swagger-scanner.js` riga 19, `dist/swagger-explorer.js` righe 34-49 e 187); `controllerKey` è `instance.constructor.name`. Una funzione di Daodan che restituisce classe e metodo come dati (non un testo da dividere sul `_`) darebbe il gestore con un'opzione ufficiale. File e riga non li dà: li darebbe lo snapshot per (classe, metodo).
- `NestFactory.create(AppModule, { preview: true })` non istanzia i provider (`@nestjs/core` `injector/injector.js` riga 411): niente connessione a un database. Che `createDocument` regga con i controller non istanziati (legge il prototipo dell'istanza, `swagger-explorer.js` riga 55) **non è letto né provato**.

## Da misurare su Modal, in ordine (una voce che non regge qui si ferma con la causa)

1. Trovare il modulo radice senza una convenzione scritta a mano: è nominato solo in `main.ts`, argomento di `NestFactory.create`; `nest-cli.json` dà `sourceRoot` ed `entryFile`, non il modulo. Se non c'è un modo ufficiale, la voce si ferma qui.
2. Caricare l'applicazione senza rete e senza `listen`: `preview: true`, e senza (con un database che non risponde).
3. Compilare il TypeScript nel container: `nest build` del progetto (poi lo script di Daodan carica il modulo compilato), `ts-node` se il progetto lo installa, builder swc. Servono i metadati dei decoratori.
4. `createDocument` in preview: funziona o lancia; che cosa dà per ogni rotta (metodo, percorso, `operationId` con la factory di Daodan).
5. `@nestjs/swagger` assente dal progetto: versione giusta per il major di Nest, senza toccare i `node_modules` del progetto, `reflect-metadata` e `@nestjs/common` in copia unica.
6. Ciò che `main.ts` imposta e lo script non esegue: `setGlobalPrefix`, `enableVersioning`, l'adapter.
7. Rotte nascoste o alterate: `@ApiExcludeEndpoint`, `@ApiExcludeController`, un `operationId` in `@ApiOperation`, i prefissi di `RouterModule`, `{id}` contro `:id`, percorsi in array, `@All()`.
8. Codice che gira all'import (`ConfigModule.forRoot({ validate })`, `process.exit`, timer), `timeout`, monorepo (`projects` in `nest-cli.json`), Nest 9 e 10 con swagger 7 e 8, tempo, memoria, file lasciati da `nest build`, e il comportamento con un'applicazione che non si carica (lacuna con la causa, i candidati di Noir restano).
9. Fuori dal documento: GraphQL, gateway WebSocket, microservizi (lacune da dichiarare).

Non scritto: la fixture e `modal_probe.py` (come `benchmarks/nuxt-routes/`): vanno scritti con le credenziali, per poterli lanciare subito.
