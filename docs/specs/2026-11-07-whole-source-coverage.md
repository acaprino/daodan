# Review per aspetto: copertura esplicita dell'intero sorgente

Descrivi cosa vuoi controllare, anche in modo incompleto. Il sistema ricava dal contesto i sorgenti e i controlli pertinenti, dichiara il perimetro scelto e procede. Divide i file in gruppi gestibili e restituisce un unico rapporto: problemi trovati, file controllati e lavoro rimasto aperto con il motivo.

Attua «Verificare e rendere visibili le lacune» del [disegno comune](2026-11-03-semantic-review-foundation.md), riusando senior-review e Codebase Map. Riferimento: `cloudflare/security-audit-skill`, per il registro di copertura e il controllo delle lacune.

## Comportamento attuale

- La base `content` (`full`, `dir` in `review-preparation/references/candidate-grounding.md`) giudica tutto il perimetro, una lista piatta di file. `composition.py bind` dà a ogni identità del roster un job sull'intero perimetro; `composition.md` chiede che una divisione per budget conservi ogni obbligo, ma nessun codice divide.
- La copertura è dichiarata in prosa (`reviewer-common.md`, «Report examined scope»). Il completeness critic (`panel-and-critic-prompts.md` §3) ne ricava i file non esaminati, e solo al rigor `deep`.
- Nessuna review ricorda cosa ha coperto una run precedente.
- I moduli della mappa non coprono il sorgente: nella mappa di questo repository (run `daodan-lite-20261107-2`) 137 file su 339 non appartengono a un modulo (test, documenti, benchmark). Il `members_digest` di un modulo di directory (`modules.py:984`) somma l'elenco dei file, non il loro contenuto.

## Proposta

È la review `branch` con base `content`, senza una shape nuova. L'aspetto è la scelta dei reviewer della Phase 1, che sul sorgente intero si orienta con la mappa (moduli, outline, ricerca) senza leggere ogni file. Cambiano il taglio dei job e il conto della copertura.

**Gestire l'ambiguità senza bloccare il lavoro.** La preparazione ricava dalla richiesta e dal contesto del progetto sia i sorgenti da esaminare sia i controlli pertinenti. Usa mappa, codice e configurazioni come riscontri, rispettando i limiti espliciti dell'utente. Dichiara brevemente il perimetro scelto e procede, senza chiedere conferma per ogni assunzione e senza includere tutto per prudenza. Chiede un chiarimento solo quando rimangono interpretazioni che cambiano sostanzialmente correttezza, ampiezza o costo; nel frattempo prosegue sulle parti indipendenti già chiare. La scelta resta correggibile: un'assunzione dichiarata non è un requisito confermato.

1. **Un controllo per file e reviewer.** Questa coppia è chiamata `cella` nei dati. I file sono quelli del perimetro già risolto (`conclusion_paths`); la mappa fornisce `sha256`, dimensione e linguaggio, senza ampliare una directory richiesta all'intero progetto. Un file richiesto ma assente dalla mappa resta `open` con il motivo e senza incarico automatico finché manca l'inventario. Il reviewer è l'identità scelta in Phase 1; una composizione conta una volta.
2. **Escludere solo ciò che è chiaramente estraneo.** `not-applicable` vale solo per reviewer di stack (TypeScript, React, Tauri). Configurazioni pertinenti, per esempio `tsconfig.json`, e file di linguaggio sconosciuto restano da controllare. Per TypeScript e React si conservano JavaScript e TypeScript; per Tauri si conservano i percorsi e le API riconosciuti dalle regole esistenti. I dubbi e gli obblighi espliciti mantengono il controllo; per gli altri reviewer l'assenza di parole chiave non esclude nulla.
3. **Un incarico per gruppo.** Dopo la Phase 1, `bind` ordina i file per percorso e li raggruppa sotto un limite di byte, tarato dal benchmark. Un file più grande del limite forma un gruppo da solo. Ogni incarico (`job`) conclude sui propri `paths` e legge altro quando serve, anche fuori dal gruppo. Il limite dimensiona i gruppi: non garantisce un costo in token né modifica il parallelismo gestito dall'host.
4. **Letto non significa completato.** Ogni job con `paths` salva un unico risultato JSON nel proprio `output_path`, usando il contratto `reviewer-result` con `read` (file letti per intero) e `partial` (file con letture o controlli incompleti, con motivo). Non esiste un secondo file di copertura del job. `account` assegna `covered` solo ai file in `read`, non in `partial`, se il risultato è valido, `status` è `delivered` e ogni membro assegnato dichiara controlli completi. Un risultato assente, non valido, fallito o con membri incompleti lascia aperto l'intero gruppo; gli altri file non letti restano `open`. Si riusano gli esiti esistenti, senza nuovi stati. `covered` significa controllo concluso, anche con difetti trovati: non significa «senza problemi».
5. **Un rapporto con limiti visibili.** `account` scrive il registro della review e i totali per reviewer: `covered`, `open`, `not-applicable`. Il rapporto finale e il critic, quando previsto, usano questo risultato: totali, primi 20 controlli aperti con motivo e percorso del registro completo. Nessun altro reviewer chiude un controllo al posto dell'assegnatario.

## Riuso successivo, solo dopo la misura

La Parte B parte dopo il benchmark e il via dell'utente; se il vantaggio non giustifica la complessità, ci si ferma alla Parte A. Il registro persistente conserva evidenze di review, non una copia del sorgente o della cache della mappa.

`account` scrive in `.daodan/review-experience/coverage.jsonl` della home del progetto, con il lock già esistente, una registrazione per reviewer e review, anche con zero celle coperte. La review seguente considera solo l'ultima registrazione: riusa i controlli con `sha256`, `body_sha256` e `knowledge_selection` invariati, se il confronto della mappa è valido e il file non dipende da file aggiunti, rimossi o modificati. Si riusa `transitive_importers` di `snapshot.py diff`, già calcolato su tutte queste modifiche; `importers` da solo non basta. Un confronto assente, incompatibile o riferito a un'altra versione impedisce il riuso e ne espone il motivo.

Ogni cella riusata conserva l'identità della review che ha realmente svolto il controllo e contiene il rimando al suo rapporto, dove restano i finding. Un controllo rifatto sostituisce la provenienza; una review interamente incompleta non fa riemergere come attuale una review più vecchia.

## Criterio

Caso di prova con difetti noti di una classe (seminati, risultati attesi fuori dalla fixture), almeno un difetto tra file di gruppi diversi e un limite che dà almeno tre gruppi per reviewer:

- senza modello (pytest): perimetro rispettato, file mancanti visibili, configurazioni conservate, gruppi entro il limite o di un solo file; file letto con controllo fallito o incompleto resta aperto;
- preparazione con il modello: richiesta incompleta risolvibile dal contesto → perimetro dei sorgenti e dei controlli dichiarato, senza conferma obbligatoria; limite esplicito → nessun ampliamento delle conclusioni; ambiguità sostanziale non risolta → domanda mirata e avanzamento sulle parti indipendenti. Registrare nel benchmark perimetri scelti e chiarimenti richiesti;
- con il modello: confrontare metodo attuale e metodo a gruppi sullo stesso commit, con stesso modello, reviewer, rigor e materiali. Per ogni cella appena coperta verificare nelle risposte degli strumenti la lettura integrale, anche in più intervalli; una chiamata o un risultato troncato non bastano. Il README riporta difetti trovati, segnalazioni errate, controlli aperti, token e tempo totali, separando mappa, review e verifica dei finding;
- Parte B: dopo una modifica, confrontare sullo stesso nuovo commit una review completa e una con riuso, a parità delle altre condizioni. Verificare quali controlli ripartono, la provenienza di quelli riusati e l'efficacia, oltre al risparmio di token e tempo.

## Gap

- La review di una modifica resta per perimetro; `light` non ha celle: se il budget non basta serve `branch`, come oggi.
- Letture e controlli completati restano dichiarazioni del job: il prodotto ne verifica la coerenza, non la verità; il benchmark confronta le letture con le trascrizioni e i difetti con i risultati attesi.
- Il riuso vede i collegamenti della mappa: link dinamici e copie sfuggono, una mappa stantia dà dipendenze false. Vale il prerequisito del README del plugin; i limiti noti restano nel rapporto.
- Il costo della verifica cresce con i finding e resta del rigor (`deep` verifica ogni finding sopra soglia): il benchmark lo misura a parte.

## Interventi

1. `snapshot.py files MANIFEST --out FILES.json` (Codebase Map): l'inventario della snapshot con `path`, `sha256`, `size`, `lines`, `language`.
2. `composition.py`: `bind` con `coverage` nei bindings (inventario, limite) crea celle e gruppi sul perimetro risolto, e senza `coverage` non cambia; `account` legge i risultati dei job e scrive il registro della review e il riepilogo.
3. `reviewer-common.md` «Deliver once» e `reviewer-result.toml`: `read` e `partial` nell'unico risultato JSON di un job con `paths`.
4. Testi della review `branch`: Phase 0 e Phase 1 in review-preparation (dedurre e dichiarare i due perimetri, chiarire solo ambiguità sostanziali), `candidate-grounding.md` (orientamento prima, lettura completa nei job), `composition.md`, brief in review-method, rapporto in review-consolidation, critic e README del plugin.
5. `benchmarks/whole-source-coverage/`: README con parametri, fixture, risultati attesi separati e misure del confronto. Dopo questi risultati e il via dell'utente, Parte B: registro di progetto e riuso.
