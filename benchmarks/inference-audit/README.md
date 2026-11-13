# Benchmark: cosa danno i motori di inferenza e cosa ne usa Daodan

Verifica, per ogni motore del passo di inferenza ([spec del motore](../../docs/specs/2026-11-08-risoluzione-chiamate-motore.md)), il percorso di un fatto dal motore al grafo che usano mappa e flussi: cosa si chiede, cosa il motore risponde, cosa si registra, cosa arriva ai collegamenti. Lo scopo è trovare ogni punto in cui un'informazione utile che il motore dà, o darebbe se gli si chiedesse, va persa. Nessun modello; tutto gira su Modal.

## Domande

| Punto | Cosa si conta |
| --- | --- |
| P1 Cosa non si chiede | riferimenti per tipo e stato (chiamate risolte, non risolte, letture); fra le letture, quelle che nominano una funzione, un metodo o una classe del progetto (un componente reso, una funzione passata come valore) |
| P2 Cosa si chiede | chiamate non risolte per classe (`askable`, `dynamic`, `builtin`) e per esito del passo (`edge-call`, `external-definition`, `project-not-a-symbol`, `ambiguous-target`, `unresolved`, errori, posizioni non verificate) |
| P3 Cosa il motore risponde e Daodan riduce | su un campione per esito, la risposta grezza: dove cade ogni destinazione (dichiarazione del progetto e suo tipo, contratto, valore, file del progetto senza dichiarazione, libreria esterna con il suo pacchetto, destinazione non su file) |
| P4 Cosa il motore darebbe se gli si chiedesse | sullo stesso campione, per i server LSP, `implementation` e `typeDefinition` accanto a `definition`; per Jedi, `goto` accanto a `infer`, con il nome completo delle destinazioni esterne |
| P5 Cosa si registra | archi confermati e candidati per esito e per tipo della dichiarazione di destinazione |
| P6 Cosa arriva al grafo | riferimenti risolti dal motore nella vista degli archi (`edge_view`), candidati e conflitti; fra i riferimenti risolti, quelli che diventano un collegamento dei flussi e quelli che si perdono (destinazione senza dichiarazione, chiamata fuori da un simbolo) |
| P7 Accordo con il lessicale | su un campione di chiamate già risolte dal risolutore lessicale, quante volte il motore indica la stessa dichiarazione |

## Parametri

| Parametro | Valore |
| --- | --- |
| casi | phazly (archivio privato: Python, TypeScript, Rust), tududi `71da9d7b34dfd1600657e9c5ddf40420206fd263` (JavaScript, TypeScript), javapoet `b9017a9503b76e11b4ad4c1a9f050e2d29112cb0` (Java), klaxon `1173bdc568a6d339b45cf24a6a9c5c2f6847f42d` (Kotlin), semver `280ebcb6edac3aa4cdc545dbff8a26c5ac4861fe` (Rust), chi `c64ed7d6635f33a8b2feaff7dcfa55677023ac7d` (Go) |
| passo | quello del prodotto: `snapshot.py write --no-engine --no-index`, poi `resolve_edges.py --pass`, tutte le posizioni |
| campione P3 e P4 | fino a 20 posizioni per esito e per linguaggio, a passo fisso sull'ordine degli identificativi |
| campione P1 | fino a 60 letture che nominano una funzione, un metodo o una classe del progetto, per linguaggio |
| campione P7 | fino a 30 chiamate risolte dal lessicale, per linguaggio |
| regole dei flussi (P6) | `benchmarks/phazly-flow/rules.json`, `benchmarks/tududi-flow/rules.json`; gli altri casi senza regole contano solo la vista degli archi |

Esecuzione: `modal run --detach benchmarks/inference-audit/modal_audit.py --phazly-tar PATH`; un container per caso, risultati in `results/audit-<caso>.json` e sul volume `daodan-flow-results`.

## Risultati

### 13 novembre 2026

Sei casi su Modal, un container ciascuno (app `ap-BDU0cjbbx8vImvzZqpgAFZ`), nessun modello. Valori per caso in `results/audit-<caso>.json`. Le perdite in ordine di peso:

| # | Dove si perde | Misura |
| --- | --- | --- |
| 1 | Chiamate risolte fuori da una funzione con nome (codice al livello del modulo: registrazioni delle rotte, composizione dell'app) non diventano collegamenti dei flussi | tududi 8.314 su 17.377 chiamate risolte (48%: 2.780 del motore, 5.534 del lessicale); phazly 485 su 13.339; javapoet 15; semver 3; chi 0 |
| 2 | Letture che nominano una funzione, un metodo o una classe del progetto (componenti resi, funzioni passate come valore, riferimenti) non si chiedono al motore né diventano collegamenti | tududi 29.380, phazly Python 14.071, phazly TypeScript 3.614, javapoet 296, klaxon 260, chi 181, semver 82; chieste a campione, la definizione cade su una funzione o una classe del progetto nel 25-55% dei casi |
| 3 | Archi confermati verso un metodo (anche di un contratto) scartati dalla vista degli archi, che tiene solo destinazioni `function` e `class` | tududi 2.199 su 7.681 (29%: 1.303 metodi, 896 contratti); phazly TypeScript 304 su 733 (41%); chi 156 su 783; semver 19 su 371 |
| 4 | Una risposta che cade in una libreria si registra come `external-definition`, senza il pacchetto | tududi 35.863, phazly 18.763 (Python 11.273, TypeScript 7.490), chi 2.299, javapoet 1.076, semver 242: nessun arco verso un servizio esterno nasce dall'inferenza |
| 5 | Una funzione assegnata a una costante (funzione freccia, espressione di funzione) è graduata `project-not-a-symbol`: il motore indica il nome della costante, che è un valore | tududi JavaScript 1.087, metà dei casi a campione cadono su una funzione; phazly TypeScript 2.072, in parte valori veri (setter di `useState`), in parte funzioni (`handleClose`); restano candidati che i flussi non usano |
| 6 | Il motore Kotlin non si installa | phazly e klaxon: «could not install the Kotlin Analysis API: HTTP Error 403: Forbidden»; klaxon resta al 17,7% |
| 7 | `implementation` non si chiede mai | dove la definizione cade su un contratto o su un valore, a campione trova la funzione concreta in 11 casi su 20 (phazly TypeScript, chiamate), 11 su 20 (tududi JavaScript, destinazioni ambigue), 5 su 20 (phazly TypeScript, non simboli); `type_definition` non aggiunge destinazioni utili |

- Il motore tace (`unresolved`) su tududi JavaScript 15.109, phazly Python 2.868, javapoet 1.213: a campione sono metodi di librerie su valori senza tipo (`res.status`, `dict.get`, collezioni di Motor). Non sono collegamenti persi, ma contano fra le chiamate risolvibili e abbassano la copertura dichiarata.
- Il risolutore lessicale e il motore indicano la stessa dichiarazione in 28-30 casi su 30 per caso (semver 25 su 30).
- Jedi `goto` e `infer` danno le stesse destinazioni a campione.
- Nessun conflitto fra lessicale e motore in nessun caso.
