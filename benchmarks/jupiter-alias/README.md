# Benchmark: un nome reale che la validazione rifiuta, in una review

Il caso iniziale era indipendente dalla costruzione del metodo, come chiede la spec [della review](../../docs/specs/2026-11-03-semantic-review-foundation.md). Ora è usato per correggerlo: le nuove run sono calibrazione sullo stesso caso, non validazione indipendente. Viene da un repository privato, Jupiter: un difetto reale arrivato in produzione e poi corretto. La validazione di `get_market_candles` rifiuta lo spazio, e l'alias reale di ogni broker IBKR lo contiene. Il codice di Jupiter non è copiato qui; le run e i loro artefatti restano fuori dal repository.

## Parametri

| Parametro | Valore |
|---|---|
| target | commit `3a02b5201` di Jupiter (`feat(chart)`) contro il genitore: 28 file, +2318 −5. La copia ha solo due commit, senza la storia successiva |
| fix | commit `121806b12` |
| difetto atteso | J1, `jupiter-core/jupiter_core/middleware/command_handlers/get_market_candles_handler.py:21`. `_IDENTIFIER_RE = [A-Za-z0-9_.\-]{1,64}`, applicata a `broker_alias` (`:141`), rifiuta `"Interactive Brokers"`, l'alias di `bin/agent_configs/production/*.json:12` (chiave `broker.alias`). Ogni grafico di un segnale IBKR risponde «broker_alias is required and must be an identifier». I test passano perché usano `Interactive_Brokers` |
| criterio | J1 trovato se un finding con `file:line` sul controllo afferma che rifiuta `Interactive Brokers` o un altro alias reale. Pieno se è almeno Medium, perché l'utente non può più fare un'azione (`reviewer-common.md`) |
| difetto atteso J2 | `jupiter-desktop/src-react/src/components/organisms/ChartPanel/chartModel.ts:248`, nel commit congelato: il ciclo di `niceTicks` non termina quando `hi` e `lo` distano uno o due passi in virgola mobile. Aggiunto dopo le run: vedi «J2» |
| criterio J2 | trovato se un finding con `file:line` su `niceTicks` afferma la non terminazione e il suo trigger (intervallo di uno o due ulp). Nessuna severità minima |
| variabili | membri per job: 1, 27 (`code-auditor`), 47 (il vecchio job light con tutti gli obblighi); testo dei controlli, modificato singolarmente nelle prove dei ruoli e insieme nei controlli da 27/47. Il job unico da 47 è il comportamento della light; quello da 27 è `code-auditor` senza gli obblighi |
| ruoli da soli | `api-contract-auditor`, `local-correctness-auditor`, `input-validation-auditor`, `testing-auditor` |
| strumenti | sulla copia: ruff 0.15.20, pytest 8.4.2, tsc 5.9.3, eslint 9.39.2, vitest 4.1.11. Rust non compilato |
| esecuzione | copia fuori da questo repository, senza rete; i revisori non vedono questo README. Senza mappa Codebase Map del candidato, quindi niente `symbols-at`, `edit-impact` né `stale-callers` |

## Limite del caso

Il repository è privato: il caso si ripete solo dove ne esiste la copia locale.

## Misure iniziali, testi invariati

Run del 2026-11-16, Opus 5.5, stessa copia, brief con gli stessi campi.

I brief recuperati dalle trascrizioni confermano una differenza: i ruoli singoli non avevano il pacchetto di risultati degli strumenti, la light sì. Il confronto fra 27 e 47 membri conserva quel pacchetto; quello fra 1 e 47 non varia soltanto il numero di membri.

| Run | Membri per job | J1 | Severità | Token | Durata |
|---|---|---|---|---|---|
| `api-contract-auditor` da solo | 1 | pieno | High | 172.092 | 868 s |
| `local-correctness-auditor` da solo | 1 | pieno | High | 173.734 | 786 s |
| `input-validation-auditor` da solo | 1 | trovato | Low, confidenza 30 | 132.846 | 763 s |
| `testing-auditor` da solo | 1 | no | — | 130.513 | 611 s |
| light, `job-01` | 47 | no | — | 400.539 | 2.174 s |
| `code-auditor`, stesso brief della light | 27 | pieno | High, confidenza 88 | 299.369 | 1.002 s |

- **I quattro ruoli da soli:** 609.185 token in tutto, in parallelo.
- **`input-validation-auditor`:** la premessa «Production agent configs are not in the repo» è falsa. Ha cercato il nome sul filo, `broker_alias`, mentre nelle config la chiave è `broker.alias`.
- **`testing-auditor`:** ha confrontato le chiavi della fixture con il modello, non i valori con le config.
- **Light:** verdetto PASS, con 7 finding (2 Medium, 5 Low) e nessuno su J1. Ha letto per intero 12 file su 28, gli altri 16 a pezzi.
  - Nel suo job, `input-validation-auditor` ha controllato solo cosa la regex lascia passare («Regex, enum and bounds checks precede the Mongo filter»).
  - `api-contract-auditor` ha confrontato i tipi tra Python, TypeScript e Rust, non i valori.
  - L'avviso del roster («required specialist obligations must fit the single discovery; otherwise review-branch is required») esce in ogni light su codice con il catalogo, perché il pavimento di `code-auditor` crea sempre obblighi, salvo esclusioni provate.
- **Fatti appresi:** non disponibili nelle run iniziali. Il provider installato cercava job con `input_mode == "discovery"` e chiave `id`, mentre `composition.py` scriveva `job_id` e `input_mode: independent`.

Il job da 27 membri mantiene modello (`claude-opus-5-5`), ruoli, convenzioni e pacchetto strumenti della light; cambiano solo identità/output del job, membri e digest. Il body SHA-256 è `d4994ae6a7c3da14f1fe4969e7796db4f3ade6ccd189b81ec8afaa85b676155d`. La copia è stata trasferita fuori dallo scratchpad, senza il junction `node_modules`; i comandi di test non sono stati rieseguiti. Token e durata sono quelli riportati dal worker; il processo completo ha richiesto 1.030 s.

## Correzioni dei controlli

Ogni prova singola riparte dal provider congelato e cambia un solo file: valori dei produttori in `api-contract-auditor`, nomi del campo in `reviewer-common`, valori delle fixture in `testing-auditor`. Stessa copia, modello e brief originario del ruolo, salvo percorsi; nessun pacchetto strumenti, come nelle singole iniziali. Nei job composti il pacchetto strumenti resta presente.

| Run con testi aggiornati | Membri | J1 | Token worker | Durata worker |
|---|---|---|---|---|
| API, valori reali | 1 | pieno, High | 199.201 | 594 s |
| Input validation, nomi del campo | 1 | pieno, High | 168.994 | 604 s |
| Testing, valori delle fixture | 1 | pieno, High; finding sulla fixture con rimando al validatore `:21`, `:141` | 223.270 | 839 s |
| `code-auditor`, testi aggiornati, run 1 | 27 | pieno, High | 324.932 | 1.011 s |
| `code-auditor`, testi aggiornati, run 2 | 27 | pieno, High | 318.497 | 1.006 s |
| Monolite di controllo, testi aggiornati, run 1 | 47 | pieno, High | 400.078 | 1.300 s |
| Monolite di controllo, testi aggiornati, run 2 | 47 | pieno, High | 369.633 | 1.174 s |
| Secondo job della light ripartita | 20 | pieno, High | 273.069 | 1.218 s |

Il digest del corpo aggiornato da 27 è `8b701bab3ebca4f489a9dc1d94f2a2432438ee09d500b64243aef96ef936f5db`; `testing-auditor` non è uno dei suoi membri. Il controllo da 47 usa `86d48421bfc255334a6ae098686edf26faa35beb94047248d236f40de339fc21`. Token e durate vengono dal blocco nativo `<usage>` del worker, non dalla somma degli eventi in streaming. Quando il sistema ha impedito la scrittura al worker, il coordinatore ha conservato il suo report senza modificarlo; non è stata ripetuta la discovery.

Entrambe le ripetizioni di ciascuna configurazione trovano J1. Il precedente confronto 27 trovato / 47 perso non dimostra quindi una soglia di affidabilità. La seconda run da 47 ha consegnato il report completo del worker (47 risultati membro); il processo coordinatore ha poi terminato con il limite settimanale del provider. Il report è recuperato dal payload originale di scrittura, con provenienza conservata. Le misure del worker sono disponibili; non si dichiara riuscito quel processo completo.

## Ripartizione della light

Il primo tentativo rifiutava i job oltre 27 membri: 27 ammessi (uscita 0, 0,265 s), 47 rifiutati (uscita 2, 0,382 s). È stato sostituito perché respingeva quasi tutte le light sul codice. Il secondo tentativo divideva i membri in job da al massimo 27, senza omettere controlli; le misure qui sotto lo descrivono. È stato ritirato dopo il confronto di «J2»: `bind` è tornato al job unico.

Conteggio sui 60 commit non-merge più recenti di ciascun repository, senza esclusioni di applicabilità; solo i commit con file classificati `production`. La misura confrontava il rifiuto con il `bind` che allora divideva i job, verificando membri, unicità, stato bound e conformità del dispatch.

| Repository e HEAD del campione | Commit con codice | Rifiutati dal limite | Rifiutati con la divisione | Job per review con la divisione |
|---|---|---|---|---|
| Jupiter, `121806b1285c4e0bc822606135c37ab5c4c978c7` | 46 | 41 | 0 | 5 con un job; 41 con due |
| daodan, `a8a1ebdb562184495623dfb657e7b990359974d0` | 55 | 54 | 0 | 1 con un job; 54 con due |

Nessun membro perso o duplicato nei 101 changeset. La mediana iniziale è 32 membri; massimo 47 su Jupiter e 42 su daodan. È una verifica della preparazione, non 101 review LLM. I conteggi dipendono dai segnali del roster, non dimostrano l'applicabilità di ogni ruolo.

Con la divisione, `bind` produceva per il caso Jupiter due job, 27 + 20. Il secondo è stato eseguito senza vedere i risultati del primo: digest `d9c205e464e733593ed63cb605aefaf2f80eb34763b6788f382eb4d0fdbcba13`, tutti i 20 risultati membro consegnati. Sommando questa esecuzione a una delle due componenti da 27 si ottengono **591.566–598.001 token worker**, contro **369.633–400.078** dei monoliti aggiornati. La divisione costa di più in questo caso e non migliora il rilevamento di J1, trovato da entrambe le configurazioni. I componenti sono stati misurati separatamente: non è una misura del tempo complessivo di un'ondata parallela, né dell'intera review.

**27 non è una soglia di affidabilità dimostrata.** Due run aggiornate per configurazione sono entrambe positive su J1; non dimostrano un vantaggio di rilevazione della ripartizione. Occorrono altri difetti e altri repository per generalizzare.

Le correzioni ai fatti appresi (`brief`, `record`) non fanno parte degli input LLM di questo benchmark, privo di target legati alla mappa e di fatti appresi; le copre `tests/test_senior_review_experience.py`.

## J2, aggiunto dopo le run

**Riproduzione confermata.** Con `lo = 1.1043` (`1.1043000000000001`) e `hi = 1.1043000000000003`, il double successivo, `niceTicks(lo, hi, 4)` non termina: esecuzione fermata a 1.000.000 di tick. Lo stesso con `count = 2`. Dalla radice della copia congelata, senza copiare il codice qui:

```text
node -e "const s=require('fs').readFileSync(process.argv[1],'utf8');const m=s.match(/function niceTicks[\s\S]*?\n}/)[0].replace(/: number(\[\])?/g,'').replace('out.push(value)','{out.push(value);if(out.length>1e6){console.log(out.length);process.exit(3)}}');const f=new Function(m+';return niceTicks')();console.log(f(1.0995,1.1043,4).length);f(1.1043,1.1043000000000003,4)" jupiter-desktop/src-react/src/components/organisms/ChartPanel/chartModel.ts
```

Stampa `5` (intervallo normale), poi `1000001` ed esce con codice 3. Il comando toglie i tipi e aggiunge solo il tetto di tick.

**Raggiungibilità reale non confermata: resta dedotta.** I chiamanti allargano l'intervallo di una frazione (`chartDraw.ts:285`, 6%; `chartDraw.ts:462`, 12%) che su questi due valori non cambia né `lo` né `hi`, quindi l'intervallo arriva a `niceTicks` (`chartDraw.ts:294`, `:472`) largo un passo. Nessun dato reale con una finestra visibile così stretta è stato osservato; l'applicazione non è stata eseguita. Il riferimento è il commit congelato: su develop (`121806b12`) la funzione non c'è più.

**Criterio retrospettivo.** J2 è stato scelto dopo aver letto i report, perché distingue le configurazioni: il confronto non è una previsione. I difetti distinti sono raggruppati dal coordinatore; a parte J1, i finding non sono verificati.

| Run | Membri | J2 | Difetti distinti | File letti per intero | `coverage` per membro |
|---|---|---|---|---|---|
| `input-validation-auditor` da solo, testi invariati | 1 | trovato, Medium | — | — | — |
| `input-validation-auditor` da solo, nomi del campo | 1 | trovato, Low | — | — | — |
| `code-auditor`, testi invariati | 27 | no | 4 | 14 su 28 | sì |
| light, `job-01`, testi invariati | 47 | no | 7 | 12 su 28 | no |
| `code-auditor`, testi aggiornati, run 1 | 27 | no | 3 | 12 su 28 | sì |
| `code-auditor`, testi aggiornati, run 2 | 27 | no | 2 | 13 su 28 | no |
| Monolite di controllo, run 1 | 47 | no | 9 | 14 su 28 | no |
| Monolite di controllo, run 2 | 47 | no | 8 | 14 su 28 | no |
| Secondo job della light ripartita | 20 | no | 8 | 28 su 28 | sì |

- **J2:** 2 su 2 con il ruolo da solo, 0 su 7 nei job composti, benché `input-validation-auditor` sia membro dei job da 27 e da 47. L'effetto del carico visibile qui è tra un ruolo e un job composto, non tra 27 e 47.
- **Light ripartita (27 + 20):** 8 difetti distinti con entrambe le run da 27, contro 9 e 8 dei monoliti.
- **Esito:** su questo caso i risultati sostengono il job unico come default. `bind` è tornato al job unico e `LIGHT_MAX_MEMBERS` è stato tolto; restano le correzioni dei ruoli, l'enum di `input_mode` e quelle dei fatti appresi. Il job unico con i testi aggiornati non trova J2: è un limite noto dei job composti.
- **Consegne:** finding e copertura dichiarata sono misure separate. Quattro report su sette non dichiarano `coverage` per membro, e nessun controllo lo rileva nei job light: il controllo delle consegne resta necessario.

Non misurati: la team-review completa con la scelta dei revisori del passo 2 e la verifica completa dei finding. Richiedono il contesto e i prerequisiti del metodo; questi sono esperimenti di discovery isolata.
