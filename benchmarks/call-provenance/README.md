# Provenienza delle chiamate

Verifica il requisito 23 di `docs/specs/2026-11-08-risoluzione-chiamate-motore.md`.

## Parametri e risultati attesi

| Caso | Risultato atteso |
| --- | --- |
| Nome assente dal progetto | Nel denominatore; viene interrogato dopo i nomi del progetto |
| Alias di una funzione interna | Arco alla funzione identificata dal motore |
| Sola variabile restituita da una libreria, Python e TypeScript | Non risolta |
| Variabile seguita da risposta sulla funzione esterna | Esterne +1, risolvibili -1, risolte invariate |
| Contenitore insieme al callable | Arco confermato conservato |
| Destinazioni interne ed esterne, oppure prova incompleta | Non risolta |
| Ciclo | Non risolta, ricerca terminata |
| Dieci contenitori con rami duplicati | Dieci interrogazioni, una destinazione |
| Grafo ampio | Al massimo 64 interrogazioni; oltre il limite resta incertezza |

## Esecuzione

Python 3.13, tree-sitter 0.26.0 e grammatica TypeScript 0.23.2. Le fixture Python usano AST stdlib. I test sono in `tests/test_codebase_map_resolve_edges.py`:

```powershell
python -m unittest discover -s tests -p test_codebase_map_resolve_edges.py -k ResolvabilityTests
python -m unittest discover -s tests -p test_codebase_map_resolve_edges.py -k HomonymHolderTests
python -m unittest discover -s tests -p test_codebase_map_resolve_edges.py -k ProvenanceGradingTests
```

## Risultati misurati, 11 novembre 2026

23 test passati in 22,270 secondi su Windows. Prima della modifica fallivano il conteggio dei nomi assenti, la loro interrogazione e il seguito della variabile; la revisione ha aggiunto regressioni per contenitore + callable, rami duplicati e budget complessivo, osservate fallire prima della correzione.

Le risposte dei motori sono controllate: questa misura prova la classificazione comune, non l'inferenza reale di ogni linguaggio. Non prova che il server TypeScript ricostruisca la funzione restituita da `useTranslation`; se restituisce ancora il contenitore, la chiamata rimane non risolta. Il precedente fallimento atteso chiedeva una classificazione esterna senza fornire la prova: è sostituito dai casi con e senza prova, senza eccezioni per librerie.

La suite completa del file ha inoltre evidenziato limiti ambientali nei test dei parser Go/Rust/Kotlin e nella creazione di junction Windows (`NativeToolchainTests.test_a_mirror_keeps_what_the_server_writes_out_of_the_project`, `TypeScriptMirrorTests.test_the_mirror_links_the_project_and_its_removal_leaves_every_target_intact`). Non viene dichiarata verde.

## Verifica del compilatore reale

```powershell
node benchmarks/call-provenance/probe-typescript.cjs /percorso/typescript/lib/typescript.js
```

Con TypeScript 5.9.3 entrambi gli assert passano: la prima navigazione identifica il contenitore destrutturato, la seconda raggiunge la funzione del provider esterno; il provider generico che restituisce il parametro conserva la destinazione interna della callback. Le sorgenti sono virtuali e non dipendono da React o altre librerie. Questa verifica usa il servizio del compilatore, non il trasporto LSP.

Verifica aggiuntiva in memoria con i pacchetti installati di Phazly: `useTranslation` restituisce una risposta sul contenitore e sulla firma `i18next/typescript/t.d.ts`; `useCallback(local, [])` sul contenitore e sulla funzione locale. Non è una rimisurazione del benchmark Phazly.

Regressioni del risolutore, conteggi, cache, contratti e passaggio multilingua: 77 test eseguiti in 81,114 secondi, 76 passati e 1 saltato perché il sandbox non consente hardlink. Il sottoinsieme mirato di 23 test è compreso in questi 77.

Anche `python -m unittest discover -s tests -p test_codebase_map_storage_queries.py` passa: 14 test in 21,474 secondi. Totale delle verifiche finali Python: 91 eseguite, 90 passate, 1 skip ambientale.

I test ambientali non verdi nella prova estesa sono `RustGoContractTests.test_go_interface_methods_are_contracts`, `RustGoContractTests.test_rust_trait_signatures_and_enum_variants_are_contracts` e `KotlinEngineTests.test_the_kotlin_engine_loads_the_snapshots_kotlin_and_java_files_only`, oltre ai due test delle junction nominati sopra. Non sono stati disabilitati o modificati per ottenere un esito verde.

## Rimisura dei tre casi, 11 novembre 2026

Modal, 4 CPU e 16 GB per caso, stessi commit della misura 0 di [`flow-model`](../flow-model/README.md). Phazly da `git archive 46c92b28 react-app shared functions-python`, senza file `.env`, `functions-python/app/core/secrets.py` e tre file di firma Android: rispetto al baseline manca `secrets.py`. Identità dell'archivio in `results/phazly-input.json`; i valori per caso in `results/`.

| Caso | Prima: risolte su risolvibili | Ora | Risolte | Passaggio motore |
| --- | --- | --- | --- | --- |
| polar `server/` | 55,9% (34.535 su 61.758) | 41,8% (34.587 su 82.731) | +52 | 41 → 57 min |
| tududi | 52,8% (17.282 su 32.717) | 41,4% (17.267 su 41.739) | −15 | 11 → 26 min |
| phazly | 59,7% (13.288 su 22.271) | 47,8% (13.304 su 27.842) | +16 | 16 → 30 min |

- Le chiamate risolte restano quasi invariate; il denominatore cresce perché i nomi assenti dal progetto restano dentro finché il motore non li prova esterni.
- Il grosso delle nuove risolvibili è `unresolved`, cioè il motore non risponde: polar Python 44.192, tududi JavaScript 15.077, phazly Python 5.674 e TypeScript 2.286. polar gira senza l'ambiente Python del progetto, phazly senza i pacchetti di `react-app`: senza librerie il motore non prova l'origine esterna.
- Phazly TypeScript: `project-not-a-symbol` passa da 4.304 a 5.621. Attraverso il server LSP 2.072 chiamate `t()` restano `project-not-a-symbol`: la verifica sul compilatore non si riproduce nel passaggio reale. Restano `project-not-a-symbol` anche `useState` (335), `useCallback` (225) e `useTranslation` (198): il motore si ferma sull'import, come quando i pacchetti di `react-app` mancano.
- Phazly: 269 posizioni non chieste.

Il comando di Modal richiede le variabili del proxy vuote: con `HTTPS_PROXY` di questa sessione il client non raggiunge `api.modal.com`.

## Con l'ambiente che Daodan prepara, 11-12 novembre 2026

Requisito 24: Daodan installa i pacchetti dichiarati dal progetto (Python da `uv.lock`, `pyproject.toml` e `requirements*.txt`, soli wheel; JavaScript per ogni cartella con il suo `package.json`, senza i pacchetti presi da un percorso locale). Stessi casi e stessa macchina; valori in `results/environment/`.

| Caso | Senza ambiente | Con ambiente | Per linguaggio | Passaggio motore |
| --- | --- | --- | --- | --- |
| polar `server/` | 41,8% (34.587 su 82.731) | 82,4% (34.301 su 41.642) | Python 82,4% | 57 → 156 min |
| tududi | 41,4% (17.267 su 41.739) | 41,4% (17.267 su 41.742) | JavaScript 37,9%, TypeScript 49,5% | 26 → 18 min |
| phazly | 47,8% (13.304 su 27.842) | 67,5% (13.338 su 19.768) | Python 77,1%, TypeScript 51,1% | 30 → 36 min |

- polar: 234 pacchetti installati su 236 dichiarati; le posizioni senza risposta scendono da 44.202 a 2.743 e le definizioni provate esterne salgono da 16.697 a 57.819. Le chiamate risolte scendono di 286: con le librerie il motore prova esterne destinazioni che prima cadevano su un simbolo del progetto. Il passaggio dura quasi tre volte tanto.
- phazly: con i pacchetti il server TypeScript prova esterne 1.807 chiamate `t()` e gli hook di React; restano `project-not-a-symbol` 246 `t()` e 255 `useAppStore` con destinazione ambigua.
- tududi aveva già i pacchetti alla radice e non cambia: le posizioni senza risposta sono metodi di libreria chiamati su valori senza tipo in JavaScript (`create`, `findOne`, `send`), con la destinazione decisa a runtime.
- La prima misura di polar con l'ambiente non lo aveva creato: i manifest si cercavano sotto la cartella del target e non dalla radice dello snapshot. Corretto con `PreparedEnvironmentTests.test_a_target_below_the_snapshot_root_still_finds_its_manifests`.
- Un'installazione JavaScript di polar è fallita su un conflitto di dipendenze di npm; le altre cartelle hanno i loro pacchetti.

Soglia della misura 0 di [`flow-model`](../flow-model/README.md), 70%: la raggiunge polar; phazly è al 67,5%, tududi no.

## Passo dinamico: parametri e prova del container, 12 novembre 2026

Verifica la [spec del passo dinamico](../../docs/specs/2026-11-12-passo-dinamico.md): i test del progetto girano in un container e le chiamate osservate si contano con lo stesso criterio.

| Misura | Parametro | Risultato atteso |
| --- | --- | --- |
| Isolamento | Container con `--network none` e una cartella montata `:ro` | Richiesta di rete fallita, scrittura rifiutata, nessun file sull'host |
| Avvio | `run --rm` di un comando vuoto, a freddo e a caldo | Riportato |
| Copertura | tududi, JavaScript: risolte su risolvibili con e senza gli archi osservati | 70% con gli archi osservati, la soglia della misura 0; nessun arco osservato contraddice un arco provato |
| Costo | Durata di preparazione ed esecuzione, RAM di picco, spazio su disco | Riportato |

Base di partenza, da `results/environment/engine-count-tududi.json`: JavaScript 11.148 risolte su 29.382 risolvibili (37,9%). Il verdetto `unresolved` conta 15.077 posizioni; i nomi più frequenti sono `create` (1.625), `send` (1.587), `get` (1.312), `post` (1.183), `map` (734) e `findOne` (570).

Isolamento e avvio, misurati su Kiri 0.2.0 (Windows 11, WSL 2, riga di comando `docker` 29.9.2, immagine `alpine` da 3,85 MB):

```powershell
docker --context kiri run --rm --network none --memory 256m --pids-limit 64 alpine wget -q -T 3 -O- http://example.com
docker --context kiri run --rm --network none -v <cartella>:/src:ro alpine sh -c "echo x > /src/b.txt"
```

- La richiesta di rete fallisce.
- La scrittura è rifiutata con `Read-only file system`; nella cartella dell'host resta il solo file di partenza.
- Avvio a freddo, con la VM a riposo: 5,3 s. A caldo, tre lanci di `alpine true`: 186, 172 e 170 ms, misurati dalla riga di comando di Windows.

### Copertura osservata su tududi, 12 novembre 2026

Esecuzione, tutta su Kiri:

1. **Preparazione.** In un container `node:22-alpine` (Node 22.23.5): archivio del commit `71da9d7b` da GitHub e `npm ci` (1.731 pacchetti).
2. **Servizio.** Postgres 16 in un secondo container, sulla rete interna `dyn-int`, che non ha uscita verso l'esterno.
3. **Test.** `dynamic_tests.sh /work/src backend /out 12 200` sulla stessa rete: Jest in 12 blocchi, un processo alla volta (`--runInBand --shard`), con il profiler di V8 ogni 200 µs. `dynamic_map.js` riporta ogni profilo ai siti di chiamata.
4. **Unione.** `dynamic_map.js --sites` conta i siti omonimi in ogni funzione. `dynamic_join.py` unisce i siti alle posizioni e ai verdetti del passaggio del motore; le posizioni le scrive `benchmarks/flow-model/modal_engine_count.py` (`positions-<caso>.json.gz`).

| JavaScript | Risolte | Risolvibili | Copertura |
| --- | --- | --- | --- |
| Passi 1 e 2 | 11.148 | 29.382 | 37,9% |
| Con gli archi osservati, conteggio stretto | 11.320 | 26.726 | 42,4% |
| Con gli archi osservati, conteggio largo | 11.447 | 24.315 | 47,1% |

- **Conteggi.** Lo stretto usa solo i siti senza omonimi nella loro funzione; il largo usa ogni sito riportato.
- **Soglia del 70%: non raggiunta** in nessuno dei due conteggi.
- **Test.** 314 file, 4.352 test, tutti passati: nessuno è rimasto fuori.
- **Risposte.** Nel conteggio largo ne ricevono una 5.366 chiamate: 5.067 vanno a una libreria ed escono dal denominatore, 299 vanno a una funzione del progetto. I nomi più frequenti verso le librerie sono `create` (1.495), `send` (486), `findOne` (453), `json` (344) e `findAll` (343).
- **Il limite è il campionamento.** Delle 16.527 chiamate che il motore lascia senza risposta, 15.140 (91,6%) stanno in file che i test eseguono, e il profiler ne vede il 35%. Una chiamata breve non cade in nessun campione. Quanta parte di ogni file venga eseguita non è misurato.

**Contraddizioni.** 41 archi osservati contraddicono il verdetto del motore. Nessuna è un errore del motore:

- 34 vanno a `backend/shared/crypto/secretCipher.js`, che il motore classifica esterno. Lo snapshot non legge i file con «secret» nel nome (`FORBIDDEN_GLOBS`, `plugins/codebase-map/skills/map/scripts/snapshot.py:170`). In tududi la regola esclude 5 file tracciati: questo, che è codice, e quattro esempi di configurazione.
- 2 vengono da doppioni dei test: un `jest.mock` di `stripe` e una richiesta HTTP finta.
- 5 vengono da chiamate omonime nella stessa funzione (`has`, `sign`, `create`), che il conteggio stretto esclude.

**Costo.**

| Fase | Durata | Memoria di picco | Spazio |
| --- | --- | --- | --- |
| Preparazione | 64 s, di cui 55 s per `npm ci` | 1,8 GB | 913 MB, di cui 870 MB di `node_modules`; immagine 61,4 MB |
| Test con il profiler, mappatura compresa | 3.699 s (61,7 min) | 1,7 GB | Profili da 43-84 MB per blocco, 737 MB in tutto, cancellati dopo la mappatura; siti osservati 24 MB |
| Siti omonimi | 3 s | | |

La memoria è il picco del container, cache dei file compresa. La durata dei test senza profiler non è misurata.

**Deviazioni dalla spec.**

- Durante la preparazione la rete era aperta verso tutto, non solo verso i registri dei pacchetti.
- La copia viene dall'archivio del commit, non dal perimetro dello snapshot.
- Il database è avviato a mano, con l'URL predefinito degli helper dei test.
- Nella copia del container `backend/babel.config.js` contiene solo `retainLines`, perché le righe del profilo coincidano con il sorgente. L'host non viene scritto.

### Registro esatto: parametri, 12 novembre 2026

Il profiler campiona e vede il 35% delle chiamate che servono. `dynamic_record.js` le registra tutte: come plugin Babel, nella copia del container, fa passare da un registratore la funzione di ogni chiamata; come modulo precaricato chiede all'inspector di Node il file dove quella funzione è definita. Un mock di Jest risulta definito in `jest-mock` e non conta.

- **Comando.** `dynamic_tests.sh /work/src backend /out 12 exact`, stessi container e stessa rete della misura con il profiler.
- **Soglia.** Invariata: 70% con gli archi osservati.
- **Validità.** Passano gli stessi 4.352 test; ogni sito registrato coincide con una chiamata dello snapshot, salvo i file che lo snapshot esclude.
- **Non registrate.** Chiamate opzionali (`?.`), metodi privati, `super`, `import`, `require`, `eval`, membri calcolati e le chiamate sull'oggetto `jest`.
- **Prova su due file di test.** 10 test su 10 passati; 1.604 siti registrati con 538 richieste all'inspector; i 30 siti senza chiamata corrispondente stanno tutti in `secretCipher.js`.
