# Strumenti di build: il fork contro le sorgenti della pre-mappa (T1.B.1)

Domanda: quali strumenti di build trovati dalle sorgenti di `find_modules` il fork `stack-analyser` non nomina, e quante
tecnologie perde lo stack quando gira senza le dichiarazioni della pre-mappa (come girerà `recognize_stack` prima di
`find_modules`, decisione 2 di `T1.B`). Le risposte sono l'elenco delle regole del rilascio `.6` del fork (`T1.B.4`).
Nessun LLM, nessun cambio al prodotto.

## Parametri

- **Riconoscitore:** il fork stesso, l'unico (spec, «Chi riconosce è uno solo»), con la release fissata in
  `daodan/core/stack_analyser.py` (`1.27.6-daodan.5`), sul Node e sulla release dell'immagine di `modal_stack.py`. Syft è
  escluso dal piano (già misurato, `benchmarks/project-model/REPORT.md`).
- **Corpus:** le fixture con `expected.json` di `benchmarks/project-model/fixtures/` (le reali dal loro archivio sul volume).
- **Pre-mappa:** quella registrata: la camminata e i lettori di oggi, con le risposte dei comandi di modello registrate in
  `benchmarks/project-model/results/premap-runs` (rigiocate, nessun comando del progetto gira; una fixture senza
  registrazione ha i comandi `not_run`). `results/daodan_premap_corpus.json`, che il piano nomina, non tiene le faccette
  `packages`, `services` e `docker_builds` che `stack_recognition.declarations` legge: si rigioca la registrazione, come
  `modal_stack.py`.
- **Due varianti sullo stesso snapshot e perimetro:** `with` = `stack_recognition.run` con i fatti della pre-mappa;
  `without` = gli stessi fatti senza `packages`, `services`, `docker_builds` (nessuna dichiarazione al fork).
- **Tabella del passo** (`modal_build_tools.TOOLS`): strumento di `find_modules` → voci del registro che il fork nomina,
  tipi di unità (`units[].kind`) e strumenti di workspace (`workspace[].tool`) della pre-mappa, sorgenti che lo provano
  (solo `tsc`, che non dà unità). CMake, Meson, Bazel, Make, autotools, sbt, .NET SDK e Mix non hanno voce nel registro;
  Nx sì (`nxjs`). «Nominato» = una voce con un segno del fork (o di una dichiarazione), non solo una menzione di host.
- **Calcolo:** `rows`, `lost`, `summary` di `modal_build_tools.py`, provati su righe scritte a mano in `test_build_tools.py`.

Corsa: `modal deploy benchmarks/stack-build-tools/modal_build_tools.py`, poi
`python benchmarks/stack-build-tools/modal_build_tools.py spawn` e `fetch` (scrive `results/build_tools.json`); test della
logica pura: `modal run tests/modal_pytest.py --args "benchmarks/stack-build-tools/test_build_tools.py -q"`.
