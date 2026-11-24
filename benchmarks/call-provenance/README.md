# Benchmark: il passo dinamico e la provenienza delle chiamate

**Stato:** In uso. I registri esatti di JavaScript e di Python sono quelli del prodotto (`daodan/core/dynamic/javascript_record.js`, `python_record.py`). Il passo dei motori per posizione, che dà il denominatore di tududi, non è più nel prodotto: resta qui come termine di confronto (sezione 4).

## Domanda

Quante delle chiamate che il passo statico lascia senza bersaglio ricevono un bersaglio dall'esecuzione dei test del progetto in un container, senza contraddire un arco statico, e a quale costo?

Che cosa dà il passo statico e dove lascia un buco è misurato in [`inference-audit`](../inference-audit/README.md). Spec: [passo dinamico](../../docs/specs/2026-11-12-passo-dinamico.md).

## Parametri

| Parametro | Valore |
| --- | --- |
| JavaScript | tududi `71da9d7b`, backend: 314 file di test, 4.352 test Jest, Postgres 16 |
| Python | python-semver `b6e83e3e40d3a7570386e8d694ae8011477a55c1`: 534 test pytest, Python 3.13.3 |
| registro JavaScript | `daodan/core/dynamic/javascript_record.js`: plugin Babel nella copia del container e modulo precaricato che chiede all'inspector di Node dove è definita la funzione chiamata |
| registro Python | `daodan/core/dynamic/python_record.py`: `sys.monitoring`, eventi `CALL` e `PY_START`, caricato da un `sitecustomize.py` in `PYTHONPATH` |
| isolamento | container senza rete durante i test (`--network none` su Kiri, `block_network=True` su Modal); la rete è aperta solo nella preparazione |
| soglia | 70% di chiamate risolte su risolvibili con gli archi osservati, la soglia della misura 0 di [`flow-model`](../flow-model/README.md); nessun arco osservato contraddice un arco provato |
| validità | passano gli stessi test con e senza registro; ogni sito registrato coincide con una chiamata dello snapshot |

| Script | Che cosa fa | Risultati |
| --- | --- | --- |
| `modal_dynamic.py`, `dynamic_tests.sh` | tududi su Modal: 12 blocchi di Jest in parallelo, un container ciascuno (2 CPU, 4 GB) con il suo Postgres | volume `daodan-flow-results`, `dynamic/exact-20261112/`; nessun file in `results/` |
| `dynamic_map.js` | riporta ai siti di chiamata i profili di V8 (misura con il profiler); `--sites` conta i siti omonimi in ogni funzione | come sopra |
| `dynamic_join.py` | unisce i siti osservati alle posizioni e ai verdetti del passo per posizione (`positions-<caso>.json.gz`, scritte da `benchmarks/flow-model/modal_engine_count.py`) | come sopra |
| `modal_dynamic_python.py` | python-semver su Modal: registro, unione con le righe dell'indice e di Jedi, verifica a mano | `results/dynamic-python-semver.json`; volume `dynamic/python-exact-20261114c/` |
| `test_dynamic_record.py` | il registro Python su `fixtures/python` (8 test, Python 3.12 o successivo) | — |
| `probe-typescript.cjs` | il servizio del compilatore TypeScript su sorgenti virtuali (sezione 4) | stampa |

Mancano dal repository:

- il file dei risultati della misura di tududi (profiler e registro esatto): i numeri della sezione 1 stanno solo qui e sul volume;
- `modal_kiri.py`, lo script della prova di Kiri su Modal, e uno script per la prova di Kiri su Windows (sezione 3);
- `inference-audit/strong-python/semver.json`, le righe dell'indice e di Jedi che `modal_dynamic_python.py` legge dal volume: nessuno script del repository le scrive.

## Risultati validi oggi

| Caso | Passo statico | Con il registro esatto | Chiamate senza bersaglio che ne ricevono uno | Contraddizioni | Costo |
| --- | --- | --- | --- | --- | --- |
| tududi, JavaScript (12 novembre 2026) | 11.148 risolte su 29.382 risolvibili, 37,9% (passo per posizione) | 11.824 su 16.381, 72,2%: soglia raggiunta | 13.677 su 16.527 (82,8%): 13.001 verso una libreria, 676 verso il progetto | 46, nessuna un errore del motore; 2 da guardare | 274 s con 12 blocchi in parallelo |
| python-semver, Python (14 novembre 2026) | grafo dall'indice: 19 chiamate mancate, 16 senza bersaglio da nessuna fonte statica, 64 buchi | 16 su 16 con la destinazione osservata; 31 buchi su 64 | come a sinistra | 0 con l'indice, 0 con Jedi | da 6 a 10 volte il tempo della suite |

Dove il registro tace: una chiamata che i test non eseguono; in Python dove non gira codice Python (attributi semplici, `__slots__`); in JavaScript chiamate opzionali (`?.`), metodi privati, `super`, `import`, `require`, `eval`, membri calcolati e le chiamate sull'oggetto `jest`.

## Che cosa resta aperto dopo l'intera pipeline

| Che cosa resta | Quanto | Passo successivo | Misura |
| --- | --- | --- | --- |
| tududi JavaScript: chiamate senza bersaglio anche dopo il registro | 2.850 (16.527 meno 13.677): 2.431 nei sorgenti, 419 nei test | esplorazione dell'app avviata, poi il modello | non misurato dopo l'esplorazione né dopo il modello |
| tududi JavaScript: archi provati verso il progetto dove il registro ha visto una funzione nativa | 2 | lettura a mano | non fatta |
| tududi: il registro unito ai buchi dell'indice, non ai verdetti del passo per posizione | 15.445 chiamate senza occorrenza nell'indice | la pipeline del prodotto | il passo dinamico chiude 691, 2.329 e 2.073 buchi JavaScript in tre giri del 16 novembre 2026 (`benchmarks/project-model/results/pipeline/2026-11-16-conferma.json`, `-ci-steps.json`, `-dotenv.json`, campo `steps.dynamic.languages.javascript.closed`). **Aperta: da approfondire:** perché molti meno dei 13.677 di questa misura non è spiegato in nessun documento |
| python-semver: buchi senza destinazione osservata | 33 su 64: 28 letture senza codice Python, 5 chiamate non eseguite | il modello | non misurato |
| Python su un progetto con test che eseguono meno | semver esegue il 97,8% delle chiamate | lo stesso registro su un altro caso | non misurato; nella pipeline del prodotto python-semver chiude 32 buchi con 1.046 siti (`2026-11-16-conferma.json`) |
| Memoria di picco dei container e crediti Modal della misura di tududi | — | — | non misurati |

## 1. Registro esatto, JavaScript: tududi

### Base statica

Da `results/environment/engine-count-tududi.json` (passo per posizione, typescript-language-server 4.3.3): JavaScript 72.842 chiamate, 11.148 risolte su 29.382 risolvibili (37,9%).

- Senza bersaglio 16.527: verdetto `unresolved` 15.077, `project-not-a-symbol` 1.082, `ambiguous-target` 368 (`UNRESOLVED` in `dynamic_join.py`). È il denominatore di questa misura.
- I nomi più frequenti fra gli `unresolved`: `create` (1.625), `send` (1.587), `get` (1.312), `post` (1.183), `map` (734), `findOne` (570). Sono metodi di libreria chiamati su valori senza tipo, con la destinazione decisa a runtime.
- I conteggi dell'indice sulle stesse chiamate (15.445 senza occorrenza, 15.104 senza risposta da entrambe le fonti) sono spiegati in [`inference-audit`](../inference-audit/README.md#i-conteggi-delle-chiamate-senza-bersaglio-su-tududi-javascript).

Dopo la correzione dell'estrattore sui bersagli delle assegnazioni (`daodan/core/languages/semantic.py`, `binding`) la base è 72.890 chiamate, 11.258 risolte su 29.350 (38,4%); la lettura lessicale ne risolve 5.878 invece di 3.304. Un bersaglio come `obj.x = …` o `a[i] += …` marcava lo scope come non risolto: su tududi 935 file JavaScript e TypeScript su 1.648 avevano uno scope bloccato, ora 14, tutti per i parametri di tipo generici di TypeScript. Misura: `benchmarks/flow-model/modal_engine_count.py`, tag `assign-20261112` sul volume. Il registro è stato unito alla base precedente.

### Misura

`modal run --detach benchmarks/call-provenance/modal_dynamic.py --shards 12 --out <dir> --tag <nome>`. L'immagine contiene l'archivio del commit e il suo `npm ci`; in ogni blocco `dynamic_tests.sh /work/src backend /out 12 exact`. Un mock di Jest risulta definito in `jest-mock` e non conta.

| JavaScript | Risolte | Risolvibili | Copertura |
| --- | --- | --- | --- |
| Passo per posizione | 11.148 | 29.382 | 37,9% |
| Con il profiler di V8, conteggio largo | 11.447 | 24.315 | 47,1% |
| Con il registro esatto | 11.824 | 16.381 | 72,2% |

- **Test.** 4.352 su 4.352 passati.
- **Risposte.** Delle 16.527 chiamate senza bersaglio il registro ne risolve 13.677 (82,8%): 13.001 vanno a una libreria ed escono dal denominatore, 676 al progetto. Nei file sorgente 3.735 su 6.166 (60,6%), nei file di test 9.942 su 10.361 (96,0%). I nomi più frequenti sono `create`, `send`, `get` e `post`: database e richieste HTTP dei test.
- **Contraddizioni.** 46, nessuna è un errore del motore: 37 vanno a `backend/shared/crypto/secretCipher.js`, che lo snapshot di allora escludeva; 7 a doppioni definiti nei file di test (pagamenti, captcha, mock di `nanoid`). Restano da guardare 2 archi provati verso il progetto per cui il registro ha visto una funzione nativa.
- **Validità.** I siti registrati senza chiamata nello snapshot sono 45: 34 in `secretCipher.js`, 11 dentro il lato sinistro di un'assegnazione (`getConfig().hosted.enabled = true`), che l'estrattore di allora non registrava. La copertura non cambia: quelle chiamate non entravano nel denominatore.

Il file con «secret» nel nome: lo snapshot non leggeva i file il cui nome contiene «secret». Ora per nome si escludono solo i file ovvi (`FORBIDDEN_GLOBS`, `daodan/core/source_files.py`); un altro nome con «secret» o «credential» esclude il file solo se il contenuto ha un valore generato (`source_files.is_forbidden`, test in `tests/test_codebase_map_secret_files.py`).

### Seconda fonte: il profiler di V8

Il profiler campiona; nel prodotto resta una seconda fonte dichiarata a parte (`sampled`), solo dove il registro non ha un aggancio (`daodan/core/dynamic/javascript.py`). Misurato su Kiri il 12 novembre 2026: `dynamic_tests.sh /work/src backend /out 12 200`, Jest in 12 blocchi, un processo alla volta (`--runInBand --shard`), un campione ogni 200 µs; `dynamic_map.js` riporta ogni profilo ai siti di chiamata.

| JavaScript | Risolte | Risolvibili | Copertura |
| --- | --- | --- | --- |
| Conteggio stretto: solo i siti senza omonimi nella loro funzione | 11.320 | 26.726 | 42,4% |
| Conteggio largo: ogni sito riportato | 11.447 | 24.315 | 47,1% |

- **Soglia del 70%: non raggiunta** in nessuno dei due conteggi. 314 file, 4.352 test, tutti passati.
- **Risposte.** Nel conteggio largo ne ricevono una 5.366 chiamate: 5.067 vanno a una libreria, 299 a una funzione del progetto. I nomi più frequenti verso le librerie: `create` (1.495), `send` (486), `findOne` (453), `json` (344), `findAll` (343).
- **Il limite è il campionamento.** Delle 16.527 chiamate senza bersaglio, 15.140 (91,6%) stanno in file che i test eseguono, e il profiler ne vede il 35%. Una chiamata breve non cade in nessun campione. Quanta parte di ogni file venga eseguita non è misurato.
- **Contraddizioni.** 41, nessuna un errore del motore: 34 verso `secretCipher.js`, 2 da doppioni dei test (un `jest.mock` di `stripe`, una richiesta HTTP finta), 5 da chiamate omonime nella stessa funzione (`has`, `sign`, `create`), che il conteggio stretto esclude.
- **Costo.** Preparazione 64 s, di cui 55 s per `npm ci` (1.731 pacchetti), picco 1,8 GB, 913 MB su disco. Test con il profiler, mappatura compresa: 3.699 s (61,7 min), picco 1,7 GB; profili da 43 a 84 MB per blocco, 737 MB in tutto, cancellati dopo la mappatura. La memoria è il picco del container, cache dei file compresa.
- **Deviazioni.** Oltre a quelle sotto: il database è avviato a mano, e nella copia del container `backend/babel.config.js` contiene solo `retainLines`, perché le righe del profilo coincidano con il sorgente.

### Costo del registro esatto

| Fase | Durata |
| --- | --- |
| Immagine, una volta | 30 s, di cui 17 s per `npm ci` |
| 12 blocchi in parallelo su Modal | 274 s dal lancio all'ultimo risultato; un blocco dura da 140 a 263 s |
| Stessi test in un solo processo su Kiri | fermata dopo 5 blocchi su 12: 1.774 s, contro 1.800 s del profiler sugli stessi blocchi |
| Stessi test con 4 processi su Kiri, limite 6 GB | fermata dopo 22 minuti, a 138 file su 314: memoria al limite, 3 processi di Jest uccisi, 30 attese scadute nei test |

La durata dei test senza registro né profiler non è misurata.

### Deviazioni dalla spec

- La copia viene dall'archivio del commit, non dal perimetro dello snapshot.
- La rete è aperta verso tutto mentre si costruisce l'immagine, non solo verso i registri dei pacchetti.
- Node 22 e Postgres girano su Debian 12, non su Alpine.

## 2. Registro esatto, Python: python-semver

**Verdetto.** Il registro chiude ciò che l'analisi statica lascia aperto: 16 mancati veri su 16 ricevono la destinazione osservata, e anche 31 dei 64 buchi. Non contraddice mai un arco statico, né dell'indice né di Jedi. Costa da 6 a 10 volte il tempo della suite: 534 test passano in 16 s invece che in 2,5 s.

I 16 sono le chiamate a cui nessuna fonte statica dà un bersaglio del progetto (`modal_dynamic_python.py`); il grafo dall'indice da solo ne manca 19 ([`inference-audit`](../inference-audit/README.md#python-python-semver)): i 3 in più sono `cli.py:46` e i due di `version.py:65`.

| Parametro | Valore |
| --- | --- |
| caso | lo stesso commit del grafo dall'indice; copia dall'archivio che `lang_python.py` ha lasciato sul volume (`inference-audit/graph-python/semver/work.tar.gz`, symlink compresi) |
| caricamento | `sitecustomize.py` scritto da `python_record.py site <dir>`: parte prima del codice del progetto, vale anche per i sottoprocessi e non tocca progetto né venv. `-X` non carica moduli; un plugin di pytest partirebbe dopo e solo sotto pytest |
| sito | istruzione di un file del progetto; `co_positions` dà inizio e fine dell'espressione, in righe e colonne UTF-8, quindi due chiamate sulla stessa riga sono due siti. Il sito si pone con `ast` sul nome della chiamata con quello span; il formato è quello del registro JavaScript, con in più `role`, `wraps` e `mock` |
| preparazione | immagine Modal con la rete aperta: venv con le 14 dipendenze dichiarate e le versioni dell'esecuzione dell'indice come vincoli (72 pacchetti, nessuna versione diversa, 6,9 s) |
| esecuzione | funzione Modal con `block_network=True`, 2 CPU, 4 GB; una connessione a `1.1.1.1:443` fallisce con «Network is unreachable». La suite parte come la configura il progetto (`.pytest.ini`, copertura e doctest compresi): una corsa di riscaldamento, tre coppie senza e con registro, poi due coppie con `--no-cov` |
| unione | le 2.343 righe di `inference-audit/strong-python/semver.json` (ogni riferimento dello snapshot, con le fini dell'indice e i bersagli di Jedi) e i 64 buchi di `graph-python-semver.json`, alla stessa posizione e con lo stesso nome |
| verifica a mano | 16 mancati veri e 4 siti, attese scritte in `HAND` prima della prima esecuzione |

Comandi: `modal deploy benchmarks/call-provenance/modal_dynamic_python.py`, poi `python benchmarks/call-provenance/modal_dynamic_python.py spawn --tag exact-20261114c`, `fetch --tag exact-20261114c` e `report`. Test del registro: `python -m unittest benchmarks/call-provenance/test_dynamic_record.py`.

**Test.** 534 su 534 passati in tutte le 11 corse, 6 senza registro e 5 con: nessun fallimento, errore o salto (il salto di `test_optional_native_backend.py` non scatta perché `fast-semver-rs-backend` è installato). Le 5 corse con il registro danno gli stessi siti.

**Costo.** Mediane; due corse precedenti, su altre macchine, danno rapporti da 6,2 a 6,3 e da 8,9 a 9,3.

| Suite | Senza registro | Con registro | Rapporto | Memoria di picco |
| --- | --- | --- | --- | --- |
| come configurata, con copertura | 2,52 s | 16,27 s | 6,5 | 60 → 79 MB |
| `--no-cov` | 1,55 s | 15,15 s | 9,8 | 59 → 70 MB |

Il tempo comprende l'avvio di pytest e la scrittura del file all'uscita. Registrati 26.999 eventi `CALL` dal codice del progetto e 9.349 chiamate implicite; 1.559 siti, 226 destinazioni, 0 errori. Costo fatturato da Modal: 0,019 USD per tre deploy e tre corse.

**I 16 mancati veri: tutti con destinazione osservata.**

- Valori creati da `deprecated`, 7 (`tests/test_pysemver-cli.py:41 createparser`; `main` alle righe 109, 116, 124, 129, 133, 156): `deprecated.<locals>.wrapper`, con `wraps` su `cli.createparser` e `cli.main`.
- Parametri chiamati, 4. `tests/test_pysemver-cli.py:104 func`: il wrapper di quattro `cli.cmd_*`. `src/semver/_deprecated.py:81 func`: 24 funzioni, tutte quelle decorate con `deprecated` più tre `mock_func` dei test. `src/semver/version.py:68 operator`: i sei metodi di confronto di `Version`. `tests/test_deprecated_functions.py:63 func`: il wrapper di 20 funzioni.
- Attributi dinamici, 2. `src/semver/cli.py:152 args.func`: `cmd_bump`, `cmd_check`, `cmd_compare` e il wrapper di `cmd_compare`. `src/semver/version.py:556 getattr(...)()`: `bump_major`, `bump_minor`, `bump_patch`.
- `src/semver/version.py:807 type(self)(**version)`: `Version` e due sottoclassi definite nei test.
- Fixture senza tipo, 2: `tests/test_semver.py:30 version.to_dict` e `:36 version.to_tuple` vanno a `Version.to_dict` e `Version.to_tuple`.

**Buchi: 31 su 64 con destinazione osservata.**

- Chiamate, 21 su 26. Al progetto 5: `cli.py:152`, `version.py:556`, `:807`, `test_semver.py:30`, `:36`. Esterne 16: `str.format` 4 (`_deprecated.py:72`, `version.py:134`, `:139`, `:157`), `argparse.ArgumentParser.parse_args` 2 e `print_help` 1, `_pytest.capture.CaptureFixture.readouterr` 4, `str.startswith` 2, `str.rstrip` 1, `importlib.util.find_spec` 1, `unittest.mock.NonCallableMock.assert_called_once` 1.
- Le altre 5 chiamate non vengono eseguite: `__main__.py:29 sys.exit`, `pytest.fail` e il suo `.format` (`test_deprecated_functions.py:65`), `pytest.skip`, `test_subclass.py:11 .format`.
- Letture, 10 su 38: le cinque property lette su una fixture (`tests/test_semver.py:43`-`47`) e i cinque `@x.setter` (`version.py:217`-`253`, `property.setter`). Le altre 28 sono letture di attributi semplici e di nomi di modulo (`args.*`, `__file__`, `func.__name__`): lì non gira codice Python e il registro tace.

**Contraddizioni con un arco statico: nessuna.** Dove l'indice ha un bersaglio del progetto (468 chiamate) il registro concorda su 460. In altre 3 vede anche sottoclassi definite nei test (`cls` in `version.py:373`, `:769`, `:788`): bersaglio giusto ma incompleto. Una è un mock (`__main__.py:25 cli.main`, sostituito da `patch`), 4 non vengono eseguite. Dove l'indice dà un esterno (487 chiamate), 474 hanno lo stesso pacchetto e 13 non vengono eseguite. Delle 474:

- 396 nominano la stessa funzione.
- 73 sono `pytest.mark.parametrize`: l'indice si ferma all'attributo `MARK_GEN.parametrize`, il registro vede l'istanza `MarkDecorator` chiamata. È lo stesso oggetto.
- 5 nominano una funzione precisa dove l'indice si ferma al modulo o sbaglia simbolo: `patch` ×2 (`unittest.mock/__init__`), `_native_parse_parts` (`parse_parts`), `operator.lt` e `operator.gt`.

Gli archi dell'indice che il registro non vede non sono contraddizioni: in `version.py:479` e `:833` l'indice dà a `cls.parse` anche i quattro override di `SemVerWithVPrefix.parse`, e nessun test arriva lì con una sottoclasse. Jedi, senza le sue risposte che sono tipi di valori (`int`, `Callable`, `partial`, `NoneType`): 0 contraddizioni, 414 chiamate concordi.

Tre difetti trovati nelle prime due corse hanno un test nella fixture, visto fallire prima della correzione:

- un wrapper fuori dal progetto (`contextlib.contextmanager`) non veniva riportato alla funzione che avvolge, e `functools.wraps` copia `__module__`, quindi il wrapper prendeva il modulo del test;
- in 3.13 l'uscita da un blocco `with` è un'istruzione `CALL` posta sull'espressione del contesto, quindi `__exit__` finiva nel sito del costruttore;
- `super()` cadeva sull'attributo `super().parse`: `LOAD_SUPER_ATTR` porta lo span dell'attributo.

**I tre bersagli sbagliati dell'indice.**

- Attributi di `__slots__` (23 letture, l'indice punta alla classe `Version`): nulla di osservato, perché un attributo di slot si legge in C. Il registro non conferma né smentisce; il sorgente dà ragione a Jedi (un valore).
- `operator.lt`, `operator.gt` (`tests/test_compare_invalid_operands.py:52`, `:67`): osservate le funzioni C `_operator.lt` e `_operator.gt` della libreria standard, non `_operator/index()`.
- `pytest.skip`, `pytest.fail`: non eseguite in questo ambiente, quindi nulla di osservato.

**Polimorfismo reale: 12 siti con più di una destinazione.**

- `_deprecated.py:81 func` 24, `version.py:68 operator` 6, `cli.py:46 func` 5 (`bump_*`), `cli.py:152 args.func` 4, `version.py:769 cls` 4, `version.py:556` 3, `:788 cls` 3, `:807` 3, `:373 cls` 2.
- Tre chiamate implicite: `__hash__` e il wrapper di `__eq__` in `tests/test_parsing.py:159` (scrittura in un dict) e `:163` (`in`); due `__enter__` diversi in `tests/test_pysemver-cli.py:103` (`with expectation`).
- In più, lo stesso wrapper ne avvolge molte: 20 funzioni in `tests/test_deprecated_functions.py:63` e 4 in `tests/test_pysemver-cli.py:104`.

**Quanto eseguono i test.** 973 chiamate su 995 (97,8%): `src` 291 su 293, `tests` 673 su 681, `docs` 9 su 21. Le 22 non eseguite:

- le 11 chiamate delle copie in `docs/advanced/` dei due file collegati da symlink, che girano dal percorso `tests/`;
- la guardia `__main__` (2);
- rami di errore mai percorsi (`docs/conf.py:43`, `test_subclass.py:10`, `:11`, `:41`);
- `pytest.fail` e il suo `.format`, `pytest.skip`;
- `getmodules` in `test_docstrings.py:18`-`19`, che nessuno chiama.

Delle 1.348 letture se ne vedono solo 90: le altre non eseguono codice Python e il registro non sa se sono state lette. I 496 siti osservati senza riferimento nello snapshot sono chiamate implicite: confronti 127, decoratori 92, property 77, indici 71, ingressi e uscite di `with` 103, `__build_class__` 8, un'espressione generatrice e 17 fra operatori, slice e scritture di attributi o indici. Nessuno è una chiamata esplicita che manca allo snapshot.

**Verifica a mano: 19 giusti su 20.** Il parziale è `version.py:807`: l'attesa era solo `Version`, e il registro vede anche `SemVerWithVPrefix` di `tests/test_subclass.py:26` e `Release` di `tests/test_next_version_legacy_order.py:36`. `replace` chiamato su un'istanza di sottoclasse costruisce la sottoclasse: l'attesa era troppo stretta, il registro ha ragione.

**Limiti del registro.**

- Non vede le funzioni Python chiamate da una funzione C: la chiave di `sorted`, `__init__` sotto la chiamata della classe; il sito tiene la funzione C o la classe.
- Non vede le letture di attributi senza codice Python, i passi di un generatore dopo la chiamata, gli import, il codice senza file (doctest, `exec` di una stringa), i processi avviati con `-I` o `-E` e quanto segue `os._exit`.
- Il riconoscimento dell'uscita da `with` dipende dal bytecode di CPython 3.12-3.13.

**Non verificato.**

- Un altro progetto Python: semver ha test che eseguono quasi tutto, quindi la quota di buchi chiusi non vale per un progetto meno coperto.
- La causa del sovraccosto: non è profilato. Probabilmente pesa `PY_START`, che scatta a ogni avvio di funzione, anche in pytest.
- Quanti dei 534 test sono doctest, le cui chiamate non diventano siti.
- Python 3.14, dove l'uscita da `with` si compila diversamente.
- Dopo l'ultima corsa `modal_dynamic_python.py` è cambiato in una lambda diventata funzione e il registro nel docstring: non rieseguiti.

**Deviazioni dalla spec.** Durante la preparazione la rete era aperta verso tutto, non solo verso i registri dei pacchetti. La copia viene dall'archivio salvato dal benchmark dell'indice, non dal perimetro dello snapshot.

## 3. Isolamento e motore dei container

Misurato su Kiri 0.2.0 (Windows 11, WSL 2, riga di comando `docker` 29.9.2, immagine `alpine` da 3,85 MB), il 12 novembre 2026. Nessuno script di queste prove è nel repository.

```powershell
docker --context kiri run --rm --network none --memory 256m --pids-limit 64 alpine wget -q -T 3 -O- http://example.com
docker --context kiri run --rm --network none -v <cartella>:/src:ro alpine sh -c "echo x > /src/b.txt"
```

- La richiesta di rete fallisce.
- La scrittura è rifiutata con `Read-only file system`; nella cartella dell'host resta il solo file di partenza.
- Avvio a freddo, con la VM a riposo: 5,3 s. A caldo, tre lanci di `alpine true`: 186, 172 e 170 ms, misurati dalla riga di comando di Windows.

### Kiri portato da Daodan, su Windows

Windows 11, WSL 2 con kernel 6.18, cgroup v2, senza `/dev/kvm`, con il Kiri dell'utente attivo nella sua distribuzione.

1. **Scaricare.** `kiri-lite_0.2.0_amd64.deb` (2,7 MB) e `SHA256SUMS` dalla release, poi la base `alpine-minirootfs-3.24.4-x86_64.tar.gz` con il suo sha256: entrambi i checksum tornano. Il pacchetto contiene `data.tar.zst`; lo estrae il `tar.exe` di Windows, perché il `tarfile` di Python 3.13 non legge zstd. Il motore sono `kiri` e `kiri-init`, 8,2 MB.
2. **Distribuzione propria.** `wsl --import daodan-kiri-probe %LOCALAPPDATA%\Daodan\kiri-probe <base> --version 2` impiega 1 s; dopo le prove il disco della distribuzione pesa 140 MB.
3. **Senza demone.** `kiri raw run --rm alpine echo raw-ok` scarica l'immagine e risponde in 1,6 s, accanto al Kiri dell'utente.
4. **Con il demone.** `kiri daemon` è pronto in 2 ms e serve l'API di Docker 1.47 su `/root/.kiri/run/docker.sock`. Un container creato dall'API con rete `none`, 256 MB di memoria, 64 processi e la copia montata in sola lettura legge la copia, non può scriverci e non raggiunge la rete; creazione, avvio e fine richiedono 5,1 s. I domini dei container restano spenti: le porte 80 e 443 e `*.kiri.local` sono del Kiri dell'utente.
5. **Togliere.** `wsl --unregister daodan-kiri-probe` toglie distribuzione e disco in meno di un secondo.

**Nessuna traccia nell'utente.** In un secondo giro completo, dall'importazione alla rimozione, l'ambiente dell'utente in `HKCU\Environment`, `PATH` compreso, la configurazione e i contesti di Docker, la cartella Esecuzione automatica e la chiave `Run` sono identici prima e dopo, byte per byte. Il Kiri dell'utente risponde come prima.

**Non provato.** Un Windows senza WSL, dove attivarlo richiede l'amministratore una volta; una macchina senza Kiri; Daodan che chiama il motore da Windows attraverso `wsl.exe` invece che dall'interno della distribuzione.

### Kiri su Linux, in un container Modal

Un container Modal (gVisor, root, senza `/dev/kvm`) scarica `kiri-lite_0.2.0_amd64.deb` e `SHA256SUMS` dalla release, verifica il checksum, estrae il pacchetto con `dpkg-deb -x` senza installarlo e usa `HOME=/tmp/home`.

- **Scaricare e usare senza installare: funziona.** Il pacchetto estratto pesa 8,2 MB. `kiri daemon` parte in 3 ms e serve l'API di Docker su `$HOME/.kiri/run/docker.sock`.
- **Eseguire un container: non funziona su Modal.** `kiri raw run --rm alpine echo` si ferma dopo 0,9 s con «Kiri needs cgroup v2 at /sys/fs/cgroup (this machine has cgroup v1 or a hybrid tree there)».
- **Conseguenza.** Su Modal il passo dinamico usa i container di Modal, come in `modal_dynamic.py`.

## 4. Termine di confronto: il passo dei motori per posizione

Il passo che chiedeva a un motore la destinazione di ogni chiamata, una posizione per volta (Jedi, typescript-language-server), non è più nel prodotto: ogni linguaggio si legge dall'indice del suo indicizzatore (`engine_pass.index_stage`), e lo stadio per posizione resta solo per un indice SCIP dato a mano (`resolve_edges.py --engine scip`). Le misure qui sotto restano perché danno il denominatore della sezione 1 e il motivo dell'ambiente che Daodan prepara.

### Classificazione per provenienza

Requisito 23 di `docs/specs/2026-11-08-risoluzione-chiamate-motore.md`: una chiamata si classifica per la provenienza della funzione chiamata, mai per il nome. Il criterio è in `daodan/core/edge_grading.py`; i test in `tests/test_codebase_map_resolve_edges.py` (`PassLifecycleTests`, `HomonymHolderTests`, `ProvenanceGradingTests`), con risposte dei motori controllate: provano la classificazione comune, non l'inferenza reale di ogni linguaggio.

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

Sul compilatore vero: `node benchmarks/call-provenance/probe-typescript.cjs /percorso/typescript/lib/typescript.js`. Con TypeScript 5.9.3 entrambi gli assert passano: la prima navigazione identifica il contenitore destrutturato, la seconda raggiunge la funzione del provider esterno; il provider generico che restituisce il parametro conserva la destinazione interna della callback. Le sorgenti sono virtuali e non dipendono da React o altre librerie. La verifica usa il servizio del compilatore, non il trasporto LSP.

### Misura 0 con il criterio di provenienza, senza e con l'ambiente

Modal, 4 CPU e 16 GB per caso, 11-12 novembre 2026, stessi commit della misura 0 di [`flow-model`](../flow-model/README.md). Phazly da `git archive 46c92b28 react-app shared functions-python`, senza file `.env`, `functions-python/app/core/secrets.py` e tre file di firma Android; identità dell'archivio in `results/phazly-input.json`. Valori per caso in `results/engine-count-<caso>.json` (senza ambiente) e `results/environment/` (con). Dove un proxy HTTPS intercetta il traffico, il client di Modal va lanciato con le variabili del proxy vuote.

Con l'ambiente Daodan installa i pacchetti dichiarati dal progetto (requisito 24): Python da `uv.lock`, `pyproject.toml` e `requirements*.txt`, soli wheel; JavaScript per ogni cartella con il suo `package.json`, senza i pacchetti presi da un percorso locale.

| Caso | Senza ambiente | Con ambiente | Per linguaggio | Passaggio motore |
| --- | --- | --- | --- | --- |
| polar `server/` | 41,8% (34.587 su 82.731) | 82,4% (34.301 su 41.642) | Python 82,4% | 57 → 156 min |
| tududi | 41,4% (17.267 su 41.739) | 41,4% (17.267 su 41.742) | JavaScript 37,9%, TypeScript 49,5% | 26 → 18 min |
| phazly | 47,8% (13.304 su 27.842) | 67,5% (13.338 su 19.768) | Python 77,1%, TypeScript 51,1% | 30 → 36 min |

- Senza ambiente il motore non prova l'origine esterna di un nome e la chiamata resta fra le risolvibili: polar Python 44.192 posizioni senza risposta, phazly Python 5.674 e TypeScript 2.286.
- polar: 234 pacchetti installati su 236 dichiarati; le posizioni senza risposta scendono da 44.202 a 2.743 e le definizioni provate esterne salgono da 16.697 a 57.819. Le chiamate risolte scendono di 286: con le librerie il motore prova esterne destinazioni che prima cadevano su un simbolo del progetto. Un'installazione JavaScript di polar è fallita su un conflitto di dipendenze di npm; le altre cartelle hanno i loro pacchetti.
- phazly: con i pacchetti il server TypeScript prova esterne 1.807 chiamate `t()` e gli hook di React; restano `project-not-a-symbol` 246 `t()` e 255 `useAppStore` con destinazione ambigua. 269 posizioni non chieste.
- tududi aveva già i pacchetti alla radice e non cambia: quello che resta lo chiude il registro esatto (sezione 1).

Soglia del 70%: la raggiunge polar; phazly è al 67,5%; tududi la raggiunge solo con il registro esatto.
