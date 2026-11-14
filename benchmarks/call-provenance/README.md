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

- 34 vanno a `backend/shared/crypto/secretCipher.js`, che il motore classifica esterno. Lo snapshot non legge i file con «secret» nel nome (`FORBIDDEN_GLOBS`, `plugins/codebase-map/skills/map/scripts/snapshot.py:170`). In tududi la regola esclude 5 file tracciati: questo, che è codice, e quattro esempi di configurazione. Ora per nome si escludono solo i file ovvi (`.env`, `secrets.*`, `credentials.*`, chiavi); un altro nome con «secret» o «credential» esclude il file solo se il contenuto ha un valore generato (`snapshot.is_forbidden`, test in `tests/test_codebase_map_secret_files.py`).
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

### Registro esatto su tududi: misura, 12 novembre 2026

Eseguita su Modal con `modal_dynamic.py`: 12 blocchi in parallelo, un container ciascuno (2 CPU, 4 GB) con il suo Postgres e la rete bloccata. L'immagine contiene l'archivio del commit `71da9d7b` e il suo `npm ci`. Ogni blocco tiene i suoi file anche sul volume `daodan-flow-results`, in `dynamic/exact-20261112/`.

| JavaScript | Risolte | Risolvibili | Copertura |
| --- | --- | --- | --- |
| Passi 1 e 2 | 11.148 | 29.382 | 37,9% |
| Con il profiler, conteggio largo | 11.447 | 24.315 | 47,1% |
| Con il registro esatto | 11.824 | 16.381 | 72,2% |

- **Soglia del 70%: raggiunta.** Il registro esatto non distingue conteggio stretto e largo: ogni sito è registrato con la funzione che ha chiamato.
- **Test.** 4.352 su 4.352 passati, gli stessi della misura con il profiler.
- **Risposte.** Delle 16.527 chiamate che il motore lascia senza risposta il registro ne risolve 13.677 (82,8%): 13.001 vanno a una libreria, 676 al progetto. Nei file sorgente sono 3.735 su 6.166 (60,6%), nei file di test 9.942 su 10.361 (96,0%). I nomi più frequenti sono `create`, `send`, `get` e `post`: database e richieste HTTP dei test.
- **Contraddizioni.** 46, nessuna è un errore del motore: 37 vanno a `secretCipher.js`, escluso dallo snapshot; 7 a doppioni definiti nei file di test (pagamenti, captcha, mock di `nanoid`). Restano da guardare 2 archi provati verso il progetto per cui il registro ha visto una funzione nativa.
- **Validità.** Rispettata per i test. I siti registrati senza chiamata nello snapshot sono 45: 34 stanno in `secretCipher.js`. Gli altri 11 sono chiamate dentro il lato sinistro di un'assegnazione, come `getConfig().hosted.enabled = true` o `counts[effectiveRole(row)] += 1`, e su quelle righe lo snapshot non ha nessuna chiamata. È una lacuna dell'estrattore JavaScript; la copertura non cambia, perché queste chiamate non entrano nemmeno nel denominatore. Corretta lo stesso giorno: sezione «Estrattore JavaScript: bersagli delle assegnazioni».

**Costo.**

| Fase | Durata |
| --- | --- |
| Immagine, una volta | 30 s, di cui 17 s per `npm ci` |
| 12 blocchi in parallelo | 274 s dal lancio all'ultimo risultato; un blocco dura da 140 a 263 s |
| Stessi test in un solo processo su Kiri | Fermata dopo 5 blocchi su 12: 1.774 s, contro 1.800 s del profiler sugli stessi blocchi |
| Stessi test con 4 processi su Kiri, limite 6 GB | Fermata dopo 22 minuti, a 138 file su 314: memoria al limite, 3 processi di Jest uccisi, 30 attese scadute nei test |

La memoria di picco dei container e i crediti spesi su Modal non sono misurati.

**Deviazioni.** Come nella misura con il profiler: la copia viene dall'archivio del commit, non dal perimetro dello snapshot, e la rete è aperta mentre si costruisce l'immagine. Node 22 e Postgres girano su Debian 12, non su Alpine.

### Kiri portato da Daodan, lato Windows, 12 novembre 2026

Prova 5 della spec, su questo PC (Windows 11, WSL 2 con kernel 6.18, cgroup v2, senza `/dev/kvm`), con il Kiri dell'utente attivo nella sua distribuzione.

1. **Scaricare.** `kiri-lite_0.2.0_amd64.deb` (2,7 MB) e `SHA256SUMS` dalla release, poi la base `alpine-minirootfs-3.24.4-x86_64.tar.gz` con il suo sha256: entrambi i checksum tornano. Il pacchetto contiene `data.tar.zst`; lo estrae il `tar.exe` di Windows, perché il `tarfile` di Python 3.13 non legge zstd. Il motore sono `kiri` e `kiri-init`, 8,2 MB.
2. **Distribuzione propria.** `wsl --import daodan-kiri-probe %LOCALAPPDATA%\Daodan\kiri-probe <base> --version 2` impiega 1 s; dopo le prove il disco della distribuzione pesa 140 MB.
3. **Senza demone.** `kiri raw run --rm alpine echo raw-ok` scarica l'immagine e risponde in 1,6 s, accanto al Kiri dell'utente.
4. **Con il demone.** `kiri daemon` è pronto in 2 ms e serve l'API di Docker 1.47 su `/root/.kiri/run/docker.sock`. Un container creato dall'API con rete `none`, 256 MB di memoria, 64 processi e la copia montata in sola lettura legge la copia, non può scriverci e non raggiunge la rete; creazione, avvio e fine richiedono 5,1 s. I domini dei container restano spenti: le porte 80 e 443 e `*.kiri.local` sono del Kiri dell'utente.
5. **Togliere.** `wsl --unregister daodan-kiri-probe` toglie distribuzione e disco in meno di un secondo.

**Nessuna traccia nell'utente.** In un secondo giro completo, dall'importazione alla rimozione, l'ambiente dell'utente in `HKCU\Environment`, `PATH` compreso, la configurazione e i contesti di Docker, la cartella Esecuzione automatica e la chiave `Run` sono identici prima e dopo, byte per byte. Il Kiri dell'utente risponde come prima.

**Non provato.** Un Windows senza WSL, dove attivarlo richiede l'amministratore una volta; una macchina senza Kiri; Daodan che chiama il motore da Windows attraverso `wsl.exe` invece che dall'interno della distribuzione.

### Estrattore JavaScript: bersagli delle assegnazioni, 12 novembre 2026

Un bersaglio come `obj.x = …` o `a[i] += …` marcava lo scope come non risolto: la lettura lessicale di ogni nome in quello scope si fermava, e le chiamate dentro il bersaglio non venivano registrate. Su tududi 935 file JavaScript e TypeScript su 1.648 avevano uno scope bloccato, 686 lo scope del modulo, perché basta `module.exports = …`. Dopo la correzione (`languages/semantic.py`, `binding`) ne restano 14, tutti per i parametri di tipo generici di TypeScript.

| JavaScript su tududi | Prima | Dopo |
| --- | --- | --- |
| Chiamate | 72.842 | 72.890 |
| Risolte dalla lettura lessicale | 3.304 | 5.878 |
| Risolte in tutto | 11.148 su 29.382 (37,9%) | 11.258 su 29.350 (38,4%) |

Le chiamate che lo scope bloccato fermava le risolveva quasi tutte il motore: la copertura sale di 0,4 punti. Senza motore la lettura lessicale ne risolve il 78% in più. Misura: `benchmarks/flow-model/modal_engine_count.py`, tag `assign-20261112` sul volume `daodan-flow-results`.

### Kiri portato da Daodan, lato Linux su Modal, 12 novembre 2026

Prova 5 della spec, solo la parte Linux: un container Modal (gVisor, root, senza `/dev/kvm`) scarica `kiri-lite_0.2.0_amd64.deb` e `SHA256SUMS` dalla release, verifica il checksum, estrae il pacchetto con `dpkg-deb -x` senza installarlo e usa `HOME=/tmp/home`. Script: `modal_kiri.py`, tenuto fuori dal repository.

- **Scaricare e usare senza installare: funziona.** Il pacchetto estratto pesa 8,2 MB. `kiri daemon` parte senza finestre in 3 ms e serve l'API di Docker su `$HOME/.kiri/run/docker.sock`.
- **Eseguire un container: non funziona su Modal.** `kiri raw run --rm alpine echo` si ferma dopo 0,9 s con «Kiri needs cgroup v2 at /sys/fs/cgroup (this machine has cgroup v1 or a hybrid tree there)».
- **Conseguenza.** Su Modal il passo dinamico usa i container di Modal, come in `modal_dynamic.py`. La parte Windows della prova 5, con una distribuzione WSL propria, è ancora da fare sul PC.

## Registro esatto per Python su python-semver, 14 novembre 2026

**Verdetto.** Il registro esatto chiude ciò che l'analisi statica lascia aperto: 16 mancati veri su 16 ricevono la destinazione osservata, e anche 31 dei 64 buchi. Non contraddice mai un arco statico, né dell'indice né di Jedi. Costa da 6 a 10 volte il tempo della suite: 534 test passano in 16 s invece che in 2,5 s. Tace dove a runtime non gira codice Python: attributi di `__slots__`, attributi semplici, rami che i test non percorrono.

| Parametro | Valore |
| --- | --- |
| caso | python-semver `b6e83e3e40d3a7570386e8d694ae8011477a55c1`, lo stesso del grafo dall'indice; copia dall'archivio che `lang_python.py` ha lasciato sul volume (`inference-audit/graph-python/semver/work.tar.gz`, symlink compresi) |
| registro | `dynamic_record.py`: `sys.monitoring`, eventi `CALL` (istruzione, oggetto chiamato) e `PY_START` (funzione Python avviata da un'istruzione che non è una chiamata: property, `__lt__`, `__enter__`, `__hash__`) |
| caricamento | `sitecustomize.py` scritto da `dynamic_record.py site <dir>` e messo in `PYTHONPATH`: parte prima del codice del progetto, vale anche per i sottoprocessi e non tocca progetto né venv. `-X` non carica moduli; un plugin di pytest partirebbe dopo e solo sotto pytest |
| sito | istruzione di un file del progetto; `co_positions` dà inizio e fine dell'espressione, in righe e colonne UTF-8, quindi due chiamate sulla stessa riga sono due siti. Il solo offset non dice dove si trova sulla riga. Il sito si pone con `ast` sul nome della chiamata con quello span; il formato è quello di `dynamic_record.js`, con in più `role`, `wraps` e `mock` |
| preparazione | immagine Modal con la rete aperta: Python 3.13.3, venv con le 14 dipendenze dichiarate e le versioni dell'esecuzione dell'indice come vincoli (72 pacchetti, nessuna versione diversa, 6,9 s) |
| esecuzione | funzione Modal con `block_network=True`, 2 CPU, 4 GB: il container di Modal è l'isolamento. Una connessione a `1.1.1.1:443` fallisce con «Network is unreachable». La suite parte come la configura il progetto (`.pytest.ini`, copertura e doctest compresi): una corsa di riscaldamento, tre coppie senza e con registro, poi due coppie con `--no-cov` |
| unione | `modal_dynamic_python.py`: le 2.343 righe di `inference-audit/strong-python/semver.json` (ogni riferimento dello snapshot, con le fini dell'indice e i bersagli di Jedi) e i 64 buchi di `graph-python-semver.json`, alla stessa posizione e con lo stesso nome |
| verifica a mano | 16 mancati veri e 4 siti, attese scritte in `HAND` prima della prima esecuzione |

Comandi: `modal deploy benchmarks/call-provenance/modal_dynamic_python.py`, poi `python benchmarks/call-provenance/modal_dynamic_python.py spawn --tag exact-20261114c`, `fetch --tag exact-20261114c` e `report`. Risultato in `results/dynamic-python-semver.json`; registri, junit e log sul volume in `dynamic/python-exact-20261114c/`. Test del registro: `python -m unittest benchmarks/call-provenance/test_dynamic_record.py` (8 test, meno di un secondo, Python 3.12 o successivo).

**Test.** 534 su 534 passati in tutte le 11 corse, 6 senza registro (il controllo) e 5 con: nessun fallimento, nessun errore, nessun salto. Il salto di `test_optional_native_backend.py` non scatta perché `fast-semver-rs-backend` è installato. Le 5 corse con il registro danno gli stessi siti.

**Costo.** Mediane della corsa buona; le due corse precedenti, su altre macchine, danno rapporti da 6,2 a 6,3 e da 8,9 a 9,3.

| Suite | Senza registro | Con registro | Rapporto | Memoria di picco |
| --- | --- | --- | --- | --- |
| come configurata, con copertura | 2,52 s | 16,27 s | 6,5 | 60 → 79 MB |
| `--no-cov` | 1,55 s | 15,15 s | 9,8 | 59 → 70 MB |

Il tempo comprende l'avvio di pytest e la scrittura del file all'uscita. Registrati 26.999 eventi `CALL` dal codice del progetto e 9.349 chiamate implicite; 1.559 siti, 226 destinazioni, 0 errori.

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

La prima corsa (`python-exact-20261114`) contava 10 contraddizioni. Erano un difetto dell'unione: `does_not_raise` (`tests/test_pysemver-cli.py:52`-`88`) è avvolta da `contextlib.contextmanager`, e il wrapper fuori dal progetto non veniva riportato alla funzione che avvolge. C'erano anche due difetti del registro:
- `functools.wraps` copia `__module__`, quindi il wrapper prendeva il modulo del test;
- in 3.13 l'uscita da un blocco `with` è un'istruzione `CALL` posta sull'espressione del contesto, quindi `__exit__` finiva nel sito del costruttore (per esempio `pytest.warns` con `WarningsChecker.__exit__`).

La seconda corsa (`python-exact-20261114b`) ha mostrato che `super()` cadeva sull'attributo `super().parse`: `LOAD_SUPER_ATTR` porta lo span dell'attributo. Tutti e tre i difetti hanno un test nella fixture, visto fallire prima della correzione.

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

**Verifica a mano: 19 giusti su 20.** Il parziale è `version.py:807`: mi aspettavo solo `Version`, e il registro vede anche `SemVerWithVPrefix` di `tests/test_subclass.py:26` e `Release` di `tests/test_next_version_legacy_order.py:36`. `replace` chiamato su un'istanza di sottoclasse costruisce la sottoclasse: l'attesa era troppo stretta, il registro ha ragione.

**Limiti del registro.**
- Non vede le funzioni Python chiamate da una funzione C: la chiave di `sorted`, `__init__` sotto la chiamata della classe; il sito tiene la funzione C o la classe.
- Non vede le letture di attributi senza codice Python, i passi di un generatore dopo la chiamata, gli import, il codice senza file (doctest, `exec` di una stringa), i processi avviati con `-I` o `-E` e quanto segue `os._exit`.
- Il riconoscimento dell'uscita da `with` dipende dal bytecode di CPython 3.12-3.13.

**Costo fatturato.** 0,019 USD per l'app `daodan-dynamic-python` (`modal billing report`): tre deploy e tre corse, di cui le prime due da rifare per i difetti sopra.

**Non verificato.**
- Un altro progetto Python. semver ha test che eseguono quasi tutto (97,8% delle chiamate), quindi la quota di buchi chiusi non vale per un progetto meno coperto.
- La causa del sovraccosto: non è profilato. Probabilmente pesa `PY_START`, che scatta a ogni avvio di funzione, anche in pytest.
- Quanti dei 534 test sono doctest, le cui chiamate non diventano siti.
- Python 3.14, dove l'uscita da `with` si compila diversamente.
- Dopo la terza corsa `modal_dynamic_python.py` è cambiato solo in una lambda diventata funzione (stesso comportamento), e `dynamic_record.py` solo nel docstring: non rieseguiti.

**Deviazioni dalla spec.** Durante la preparazione la rete era aperta verso tutto, non solo verso i registri dei pacchetti. La copia viene dall'archivio salvato dal benchmark dell'indice, non dal perimetro dello snapshot.
