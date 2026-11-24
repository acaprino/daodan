# Review: perimetro, selezione dei revisori, copertura

**Stato:** In parte. In uso nella review `branch` di senior-review: la Phase 0 «Request to files» (sezione 1), la Phase 1 in tre passi con la selezione dichiarata (sezione 2), il rigor (sezione 3), le celle di copertura (sezione 4, Parte A) e le quattro regole (sezione 5). Mancano: micro skill e baseline per stack (sezione 6), il riuso della copertura fra review (sezione 4, Parte B), la validazione su casi non usati nella costruzione.

Due proprietari: Codebase Map comprende il codice e recupera il contesto, e funziona da solo; senior-review compone la review e usa la mappa. Strumenti, modello e capacità di esecuzione sono dell'host. Il codice è in `daodan/core/` (`composition.py`, `review_roster.py`, `review_experience.py`), ruoli e contratti in `daodan/review/`, i testi operativi in `plugins/senior-review/skills/`.

```text
Richiesta + Codebase Map → file da rivedere → contesto e revisori → job → verifica → un rapporto
            Phase 0                           Phase 1               Phase 2
```

Prerequisito: la mappa completa del progetto. Se manca, prima Codebase Map.

## 1. Perimetro (Phase 0)

Traduce una richiesta in parole (modulo, feature, funzione, errore, termine di dominio) nei file da rivedere. Testo operativo: `review-preparation/references/team-review.md`, «Request to files»; la `light` vi rimanda. I target già esatti (file, directory, diff, PR, documenti) non passano di qui. Quale strumento risponde a quale domanda: `plugins/codebase-map/skills/map/references/tools-guide.md`.

1. **Trova.** Dai nomi della richiesta, lo strumento più economico: file esplicito, nessuno; modulo, `codebase_map_modules`; nome o parola, `codebase_map_search`; flusso, `codebase_map_graph`, un hop alla volta dai file confermati. Una ricerca vuota si riprova una volta con un sinonimo; un indice mancante o stale è un prerequisito mancante, non una ricerca vuota.
2. **Conferma.** I limiti espliciti («solo questo file», un diff) si rispettano; altrimenti i nomi sono punti di partenza e un file entra solo con la riga che lo dimostra (`codebase_map_outline`, `codebase_map_read` del solo pezzo che decide). Una richiesta su una modifica include i chiamanti coinvolti (`codebase_map_edit_impact`). Un collegamento che il grafo non ha non si inventa: si cerca per nome, si legge, e se non si conferma lo si dice.
3. **Fermati** quando le evidenze bastano, quando non ci sono più piste, o a circa 6 interrogazioni e 10 letture, dicendo perché.
4. **Rispondi** `resolved` (i file, ciascuno con la sua evidenza), `partial` (i file trovati, che cosa serve ancora e perché) o `clarify` (la richiesta può voler dire due cose: i candidati e la domanda).

Il perimetro è ciò che la review giudica; ciò che legge per giudicarlo è contesto della Phase 1. Un'ambiguità si chiarisce solo se cambia correttezza, ampiezza o costo: altrimenti la preparazione dichiara il perimetro scelto e procede, e un'assunzione dichiarata non è un requisito confermato.

Una regola in più entra solo per un requisito obbligatorio o un errore riproducibile; un'ambiguità segnalata da un modello non è un errore.

## 2. Contesto e selezione (Phase 1)

Tre passi del coordinatore, nel suo contesto, senza dispatch.

1. **Comprendere l'oggetto nel perimetro.** Con gli strumenti della mappa: sorgenti, contratti e test pertinenti, ogni riferimento con percorso, righe e versione. Uscita: `.team-review/01-context.md`.
2. **Scegliere i revisori.** Candidati: i ruoli del catalogo (`daodan/review/catalog.toml`, `composition.py catalog`). Le descrizioni selezionano i candidati; il coordinatore legge i mandati prima di decidere. Linguaggi ed estensioni orientano, non determinano. `composition.py bind` riceve la scelta in `BINDINGS.json` (`selection`): una review `branch` senza selezione dichiarata si ferma; code review, PR review e tipi documentali dichiarano `automatic`. Il roster di `review_roster.py compute` è uno spunto.
3. **Avviare.** I revisori scelti partono insieme, ciascuno sull'intero perimetro con il proprio mandato: il mandato dice che cosa verificare, il perimetro dove. Una competenza necessaria e non disponibile, compresa la baseline di uno stack toccato, è una lacuna dichiarata. Uscita: `.team-review/02-selection.md`, letto dalla Phase 2.

Perché non una nuova analisi parziale, la derivazione cieca delle premesse e la mappa delle interconnessioni prima del primo revisore: la mappa completa è già prerequisito, e la verifica delle premesse resta per finding (Lens 0), dove costa in proporzione ai finding. `premise-auditor` Mode 1 resta su richiesta esplicita.

La completezza della scelta non è garantita: «tutto e solo ciò che serve» è l'obiettivo della misura, non una proprietà di un punteggio.

## 3. Rigor e verifica

Il rigor è `quick`, `standard` o `deep`: lo decide il modello leggendo la richiesta (`--rigor`), `standard` se non dice nulla. Stabilisce la verifica (`review_roster.VERIFICATION`): `critical` per `quick`, `critical-high` per `standard` e `light`, `all-above-floor` per `deep`. Un segnale di rischio (interfaccia pubblica, percorso sensibile, manifest, 20 chiamanti) porta a `deep` anche una richiesta `quick`; il numero di file e di moduli non alza il rigor.

## 4. Copertura dell'intero sorgente

È la review `branch` con base `content`, senza una shape nuova. La review di una modifica resta per perimetro e la `light` non ha celle.

**Parte A, in uso.**

1. **Una cella per file e revisore.** I file sono quelli del perimetro risolto; la mappa dà `sha256`, dimensione e linguaggio (`snapshot.py files`). Un file richiesto e assente dalla mappa resta `open` con il motivo.
2. **Si esclude solo ciò che è chiaramente estraneo.** `not-applicable` vale solo per i revisori di stack; configurazioni pertinenti e file di linguaggio ignoto restano da controllare.
3. **Un job per gruppo.** `bind` ordina i file per percorso e li raggruppa sotto un limite di byte; un file oltre il limite è un gruppo da solo. Un job conclude sui propri `paths` e legge altro quando serve. Il limite dimensiona i gruppi: non garantisce un costo in token.
4. **Letto non è completato.** Ogni job salva un solo risultato (`daodan/review/contracts/reviewer-result.toml`) con `read` e `partial`. `account` dà `covered` solo ai file letti per intero di un risultato valido, `delivered`, con ogni membro completo; il resto resta `open`. `covered` è un controllo concluso, non «senza problemi».
5. **Un rapporto con i limiti visibili.** Totali per revisore (`covered`, `open`, `not-applicable`), i primi 20 controlli aperti con il motivo, il percorso del registro completo. Nessun altro revisore chiude un controllo al posto dell'assegnatario.

Letture e controlli completati restano dichiarazioni del job: il prodotto ne verifica la coerenza, il benchmark confronta le letture con le trascrizioni.

**Parte B, proposta: riuso fra review.** `account` scriverebbe una registrazione per revisore e review in `.daodan/review-experience/coverage.jsonl`; la review seguente riuserebbe i controlli con `sha256`, `body_sha256` e `knowledge_selection` invariati, se il file non dipende da file cambiati (`transitive_importers` di `snapshot.py diff`), tenendo la provenienza della review che ha svolto il controllo. Nulla è nel codice. **Aperta: da approfondire:** il vantaggio della divisione in gruppi è misurato su una fixture che un solo job legge per intero; su un perimetro che un job non riesce a leggere non è misurato, e la Parte B parte solo dopo quella misura e il via del proprietario.

## 5. Quattro regole dai casi misurati

Ognuna chiude un errore visto in [`benchmarks/phazly-flow`](../../benchmarks/phazly-flow/README.md).

| Regola | Errore visto | Dove |
| --- | --- | --- |
| La prima azione di una review è caricare la preparazione; chi non può seguire il metodo lo dice nella prima riga e si ferma | Il modello ha fatto la review da solo e l'ha detto alla fine | `review-method/SKILL.md` |
| Ogni frase sul modello dei dati dice tipo e granularità, con `file:line`; una negazione cita la ricerca che la sostiene, altrimenti «non noto» | «Non esiste un tipo planned», ereditato da 49 incarichi | `review-preparation/references/team-review.md` |
| Un'informazione falsa mostrata all'utente, o un'azione che non può più fare, vale almeno Medium | Un piatto non mangiato mostrato come completato valutato Low | `daodan/review/reviewer-common.md` |
| Due segnalazioni sono lo stesso problema solo con la stessa causa e la stessa situazione che lo fa scattare | Due situazioni sulla stessa riga fuse, il difetto vero sparito | `review-consolidation/references/team-review.md` |

## 6. Micro skill, baseline per stack, embedding

**Proposta.** Una micro skill è un controllo riusabile su un problema preciso: domanda, condizioni di applicabilità, evidenza necessaria, modo di verificare, criterio del risultato. Può seguire un comportamento (un evento ripetuto duplica un effetto? due esecuzioni acquisiscono lo stesso lavoro?) o uno stack; una guida completa a un linguaggio non è una micro skill. Oggi non esistono: la selezione lavora sui ruoli del catalogo, più larghi di un controllo, e ogni review `branch` dichiara la lacuna di baseline. I ruoli per framework e libreria sono stati provati e non promossi: [revisori per framework e librerie](2026-11-19-revisori-per-framework-e-librerie.md).

Gli embedding entrano solo come recupero di candidati e solo se una misura li giustifica: la somiglianza non decide la rilevanza, e modello, costo, freschezza e invio dei dati devono essere espliciti.

## Prove

- **Perimetro:** [`benchmarks/scope-resolution`](../../benchmarks/scope-resolution/README.md): il resolver deterministico misura il protocollo, le sessioni del modello il giudizio sul perimetro (file indispensabili mancanti, inclusioni senza motivo, protocollo). Una esecuzione per caso.
- **Selezione:** lo stesso README, parametro «Phase 1»: sul caso di costruzione i revisori scelti trovano il difetto, la baseline mancante è dichiarata, il criterio di costo (meno della `light`) non è raggiunto.
- **Copertura:** [`benchmarks/whole-source-coverage`](../../benchmarks/whole-source-coverage/README.md).
- **`light`:** [`benchmarks/jupiter-alias`](../../benchmarks/jupiter-alias/README.md), che senza mappa del candidato non valida la review `branch`.

Per ogni misura: stessi casi e stesso modello, casi di costruzione separati da casi di verifica, risultati attesi verificati in modo indipendente, costo della mappa separato dal riuso, token veri e non caratteri.

## Aperto

- **Aperta: da approfondire:** il metodo è provato solo sui casi usati per costruirlo; servono casi non usati nella costruzione prima di dichiararlo valido.
- **Aperta: da approfondire:** il costo della review `branch` rispetto alla `light` sul caso di costruzione.
- Se unità e flussi fanno trovare più difetti: [flussi nella review](2026-11-09-flows-in-review.md).
