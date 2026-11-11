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

## Ripresa del benchmark Phazly

Archivio del commit `46c92b28aabf833a6baa46b88f1795d6668d702c`, verificato tramite intestazione PAX. Prima del trasferimento sono esclusi tre file di firma Android e `functions-python/app/core/secrets.py`. L'esclusione di quest'ultimo modifica anche il perimetro dei sorgenti rispetto al baseline: un confronto dei conteggi deve dichiararlo. Identità del nuovo archivio e del risolutore in `results/phazly-input.json`.

```powershell
modal run benchmarks/flow-model/modal_engine_count.py --cases phazly --phazly-tar C:/Users/alfio/AppData/Local/Temp/daodan-phazly-provenance-46c92b28.tar --results-dir benchmarks/call-provenance/results
```

Il tentativo di ripresa non ha prodotto un identificativo di job: la sessione non risolve `api.modal.com` (`URLError [Errno 11001] getaddrinfo failed`). CLI interrotta; nessun nuovo risultato remoto dichiarato. Il file baseline `benchmarks/flow-model/results/engine-count-phazly.json` è invariato.

Il runner ora consente una cartella risultati separata e carica l'archivio anche quando si seleziona soltanto `phazly-react`. Verifica locale dell'entrypoint con chiamata remota simulata: archivio selezionato, nuovo risultato scritto nella destinazione scelta e baseline invariato; compilazione Python e `git diff --check` riusciti.
