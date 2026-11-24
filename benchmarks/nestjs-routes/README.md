# NestJS: `SwaggerModule.createDocument`

**Stato:** Aperta: da approfondire. `createDocument`, con l'applicazione caricata in `preview`, dà rotte che Noir non vede? Letto nei sorgenti, mai eseguito: nessuna fixture, nessuna sonda, nessuna sorgente della pre-mappa, nessuna voce in `container_runner.TOOLS`. Nel prodotto le rotte di NestJS sono quelle di Noir.

## Domanda

NestJS dà, con uno strumento ufficiale eseguito nel container, ogni rotta con metodo, percorso e gestore? Spec: [ingressi e scoperta dei flussi](../../docs/specs/2026-11-20-ingressi-e-scoperta-dei-flussi.md), sezione 6 (task 14h del piano).

## Strumento letto

`@nestjs/swagger` 11.2.0 (`https://registry.npmjs.org/@nestjs/swagger/-/swagger-11.2.0.tgz`, sha256 `87aad2d582050994861df64ca695afdd89031e53e55b554ef9ce63b2d2d0e582`) e `@nestjs/core` 11.1.6 (`https://registry.npmjs.org/@nestjs/core/-/core-11.1.6.tgz`, sha256 `5c304658ce367917da2f9170a728ced29e3101606c539e98ab6e05cf63b53bc3`), letti il 23 novembre 2026:

- `createDocument` accetta `operationIdFactory(controllerKey, methodKey, version)` (`dist/swagger-scanner.js` riga 19, `dist/swagger-explorer.js` righe 34-49 e 187); `controllerKey` è `instance.constructor.name`. Una funzione di Daodan che restituisce classe e metodo come dati darebbe il gestore con un'opzione ufficiale; file e riga li darebbe lo snapshot per (classe, metodo).
- `NestFactory.create(AppModule, { preview: true })` non istanzia i provider (`@nestjs/core` `injector/injector.js` riga 411): nessuna connessione a un database. Che `createDocument` regga con i controller non istanziati (legge il prototipo dell'istanza, `swagger-explorer.js` riga 55) non è letto né provato.

## Risultato valido oggi

Nessuna misura dello strumento. Su tre applicazioni vere Noir dà 156 endpoint `http`, 137 con nome e riga del metodo, e 131 su 137 si legano ([noir-binding](../noir-binding/README.md)): `createDocument` aggiungerebbe solo le rotte che Noir non vede, che non sono contate. Se il passo dinamico le osserva: non misurato.

## Aperto, da misurare su Modal, in ordine

Una voce che non regge chiude la prova con la causa.

1. Trovare il modulo radice senza una convenzione scritta a mano: è nominato solo in `main.ts`, argomento di `NestFactory.create`; `nest-cli.json` dà `sourceRoot` ed `entryFile`, non il modulo.
2. Caricare l'applicazione senza rete e senza `listen`: con `preview: true`, e senza (con un database che non risponde).
3. Compilare il TypeScript nel container: `nest build` del progetto, `ts-node` se il progetto lo installa, builder swc. Servono i metadati dei decoratori.
4. `createDocument` in preview: funziona o lancia; che cosa dà per rotta (metodo, percorso, `operationId` con la factory di Daodan).
5. `@nestjs/swagger` assente dal progetto: la versione giusta per il major di Nest, senza toccare i `node_modules` del progetto, `reflect-metadata` e `@nestjs/common` in copia unica.
6. Ciò che `main.ts` imposta e lo script non esegue: `setGlobalPrefix`, `enableVersioning`, l'adapter.
7. Rotte nascoste o alterate: `@ApiExcludeEndpoint`, `@ApiExcludeController`, un `operationId` in `@ApiOperation`, i prefissi di `RouterModule`, `{id}` contro `:id`, percorsi in array, `@All()`.
8. Codice che gira all'import (`ConfigModule.forRoot({ validate })`, `process.exit`, timer), `timeout`, monorepo (`projects` in `nest-cli.json`), Nest 9 e 10 con swagger 7 e 8, tempo, memoria, file lasciati da `nest build`, un'applicazione che non si carica.
9. Fuori dal documento: GraphQL, gateway WebSocket, microservizi (lacune da dichiarare).

Da scrivere prima: la fixture e `modal_probe.py`, sul modello di [nuxt-routes](../nuxt-routes/README.md).
