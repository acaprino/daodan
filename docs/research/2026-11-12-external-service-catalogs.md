# Cataloghi pubblici di servizi e progetti esterni

**Verifica delle fonti:** 12 novembre 2026. **Natura del documento:** ricognizione mirata per il registro della [mappa del sistema](../specs/2026-11-12-mappa-del-sistema.md), non esaustiva. I numeri sono contati alla fonte, salvo dove è scritto il contrario.

## In breve

Nessun catalogo dà da solo ciò che serve al registro: nome, tipo, sito, marchio e i segni da cui riconoscere un servizio nel codice. Uno dà i segni, uno i marchi, due allargano la copertura. Insieme superano il migliaio di voci.

## Cataloghi

| Catalogo | Cosa contiene | Quante voci | Licenza | Cosa manca |
| --- | --- | --- | --- | --- |
| [specfy/stack-analyser](https://github.com/specfy/stack-analyser) | Regole che riconoscono una tecnologia dal codice: nome, tipo, pacchetti per ecosistema, prefissi delle variabili di configurazione | 798 regole in `src/rules`, divise per tipo: database 95, hosting 45, CI 33, SaaS 33, cloud 31, AI 30 e altri | MIT | Sito e marchio. La copertura fra ecosistemi è disuguale: la regola di Stripe elenca npm, PHP, Ruby e Go, non Python |
| [Simple Icons](https://github.com/simple-icons/simple-icons) 16.37.0 | Marchi: nome, disegno, colore | 3.470 | CC0-1.0; i marchi restano dei loro titolari | Tipo, sito, segni nel codice |
| [CNCF Landscape](https://github.com/cncf/landscape) | Prodotti e progetti di cloud e infrastruttura: nome, categoria, sito, logo | 2.447 voci in 15 categorie e 80 sottocategorie | Dati CC BY 4.0, repository Apache-2.0 | Segni nel codice |
| [APIs.guru OpenAPI Directory](https://github.com/APIs-guru/openapi-directory) | API pubbliche raggruppate per fornitore | 2.529 API di 677 fornitori | CC0-1.0 per il repository secondo un indice terzo; ogni definizione ha la sua licenza; chiede un link di attribuzione | Tipo, segni nel codice |
| [enthec/webappanalyzer](https://github.com/enthec/webappanalyzer) | Tecnologie con categoria e sito, riconosciute da un sito in esecuzione; continua Wappalyzer | Non contate | GPL-3.0 | Riconosce siti, non codice; la licenza non permette di copiarne i dati in un plugin con altra licenza |

Cercati e non confermati: i cataloghi di integrazioni di Pipedream, Nango e Airbyte.

## Esempio di regola di stack-analyser

```ts
register({
  tech: 'stripe', name: 'Stripe', type: 'payment',
  dotenv: ['STRIPE_'],
  dependencies: [{ type: 'npm', name: 'stripe' }, { type: 'ruby', name: 'stripe' }, { type: 'golang', name: 'github.com/stripe/stripe-go' }],
});
```

## Uso proposto

- Base: le regole di stack-analyser, che hanno già tipo e segni.
- Marchi: Simple Icons, agganciati per nome.
- Allargamento: le voci del CNCF Landscape per l'infrastruttura.
- Il modello propone solo ciò che manca: sito, tipo dove assente, pacchetti degli ecosistemi non coperti. Resta ciò che la macchina verifica.
- Da rispettare: la nota di licenza MIT e l'attribuzione CC BY 4.0.

## Fonti

- [specfy/stack-analyser](https://github.com/specfy/stack-analyser), README e albero `src/rules` letti il 12 novembre 2026
- [@specfy/stack-analyser su npm](https://www.npmjs.com/package/@specfy/stack-analyser)
- [simple-icons 16.37.0 su jsDelivr](https://cdn.jsdelivr.net/npm/simple-icons@16.37.0/package.json), `data/simple-icons.json`
- [cncf/landscape](https://github.com/cncf/landscape), `landscape.yml`
- [APIs.guru, metriche](https://api.apis.guru/v2/metrics.json) e [README del repository](https://github.com/APIs-guru/openapi-directory/blob/main/README.md)
- [enthec/webappanalyzer](https://github.com/enthec/webappanalyzer)
