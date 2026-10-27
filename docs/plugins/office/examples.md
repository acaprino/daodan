# Esempi d'uso Office

[Indice Office](../office.md) · [Funzioni](functions.md) · [Percorso di lavoro](workflow.md) · [Verifiche](verification.md)

Scegli lo scenario e adatta la richiesta ai tuoi materiali. Gli esempi sono illustrativi e non sono stati eseguiti: non attestano l'esistenza degli input né la produzione dei file citati. I percorsi sono relativi alla cartella del tuo progetto; i nomi delle consegne sono scelte degli esempi, non output fissi dell'API.

La notazione `/daodan:…` è quella di Claude. Per gli altri host consulta [Host](../../hosts.md) e il [mapping generato](../office.md#source-derived-reference); in Codex seleziona la workflow skill corrispondente, per esempio `document-workflow` del plugin `daodan`, e fornisci lo stesso testo. Non incollare questi ingressi nel terminale.

## 1. Rapporto Word da appunti, dati e logo

**Materiali da fornire:** appunti leggibili in `materiali/appunti-progetto.md`, dati con definizioni e unità in `materiali/indicatori.xlsx`, logo utilizzabile in `materiali/logo.png` ed eventuali citazioni approvate in `materiali/testi-vincolati.txt`. Indica se il logo è solo un asset o anche un vincolo cromatico. Per produrre e renderizzare il DOCX serve WordCraft; leggere e calcolare i dati del workbook richiede le capacità XLSX pertinenti.

**Richiesta da copiare:**

```text
/daodan:document Crea un rapporto in italiano per il responsabile operativo usando materiali/appunti-progetto.md e materiali/indicatori.xlsx. Spiega stato, risultati, problemi e decisioni richieste; mantieni le condizioni e i limiti dei dati. Il logo materiali/logo.png è un asset da inserire e una fonte di colori, non un manuale di brand completo. Conserva letteralmente i blocchi di materiali/testi-vincolati.txt; puoi riorganizzare e riscrivere gli altri appunti senza aggiungere fatti. Proponi una lunghezza motivata per una lettura autonoma di circa dieci minuti. Mostrami le alternative visive complete prima della scelta. Salva il DOCX modificabile in consegne/rapporto-progetto/rapporto.docx e includi una copia PDF, i record condivisi e la review con i limiti delle verifiche. Non modificare gli input.
```

**Percorso visibile:**

1. L'agente legge i materiali, distingue dati e vincoli e segnala soltanto lacune decisive, per esempio un'unità non definita.
2. Prepara il contenuto tracciato, sviluppa le direzioni e verifica campioni Word nativi su testo, evidenze e tabella reali. Mostra i loro render nel confronto HTML. Comunica la tua scelta in chat; la sola evidenziazione nel browser non basta.
3. Compone il Word, salva la copia separata e ne controlla pagine e fedeltà alle fonti; corregge i difetti ordinari entro lo scopo.

**Consegna riconoscibile:** `rapporto.docx`, PDF richiesto, `CONTENT.md`, `DESIGN.md`, confronto e rapporti di composizione/review. Nel DOCX titoli e tabelle sono nativi e modificabili; citazioni e dati conservano significato, unità e vincoli. La review identifica la copia e le pagine effettivamente ispezionate. Se WordCraft o il renderer non sono disponibili, il lavoro preparatorio può continuare, ma DOCX/PDF o impaginazione restano esplicitamente bloccati o non verificati. Il confronto HTML non sostituisce questi risultati.

## 2. Rapporto e presentazione per due modalità di lettura

**Materiali da fornire:** un rapporto sorgente in `materiali/rapporto-tecnico.docx`, un template PPTX vincolante in `materiali/template-direzione.potx`, eventuali dati di supporto e l'indicazione dei passaggi obbligatori. WordCraft e DeckCraft devono supportare le operazioni e le caratteristiche da conservare. Il rapporto sorgente resta distinto da entrambe le consegne.

**Richiesta da copiare:**

```text
/daodan:start Da materiali/rapporto-tecnico.docx prepara un rapporto decisionale Word per lettura autonoma e un deck PowerPoint per un intervento di dodici minuti alla direzione. Usa materiali/template-direzione.potx come base vincolante del deck e mantieni un'identità coerente nel Word. Puoi sintetizzare gli approfondimenti tecnici, riportandoli in appendice quando servono a sostenere le conclusioni; conserva fatti centrali, condizioni, incertezze e citazioni letterali. Non introdurre nuove stime. Scegli autonomamente le soluzioni compatibili con questi vincoli e motiva le decisioni. Salva consegne/direzione/rapporto.docx e consegne/direzione/presentazione.pptx. Consegna anche i record condivisi e i report distinti dei due formati. Non modificare il rapporto o il template forniti.
```

**Percorso visibile:**

1. L'agente ispeziona rapporto e template, definisce le trasformazioni consentite e prepara una sola base editoriale per le due destinazioni.
2. Riusa l'identità visiva vincolante e registra le scelte; non richiede un'ulteriore approvazione per le decisioni già comprese nell'autonomia concessa.
3. Distribuisce i contenuti in sezioni Word e slide PowerPoint, poi produce e controlla separatamente i due file.

**Consegna riconoscibile:** i due file nativi, un'identità/revisione condivisa di `CONTENT.md` e `DESIGN.md`, il `plan.json` PPTX e report di composizione/review distinti. Gli stessi fatti centrali raggiungono entrambi i formati; eventuali esclusioni sono autorizzate e tracciate. Il Word può avere spiegazioni continue e appendici; il deck sviluppa il discorso senza corrispondenza pagina-slide. Testo, tabelle e oggetti richiesti restano modificabili. La review di un formato non vale per l'altro; una capacità mancante lascia aperta la sola consegna dipendente.

**Variante solo deck:** usa `/daodan:presentation` e chiedi soltanto `consegne/direzione/presentazione.pptx`, mantenendo gli stessi materiali e permessi. Non è richiesta la produzione di un nuovo DOCX.

## 3. Aggiornare contenuti oppure cambiare aspetto

**Materiali da fornire:** `materiali/rapporto-esistente.docx`, le sue decisioni già accettate se disponibili e `materiali/aggiornamenti.md` con fonti e modifiche. Per il restyle aggiungi `materiali/brand.pdf` e gli asset utilizzabili. L'ispezione iniziale deve accertare che il motore conservi le caratteristiche del file esistente.

**Revisione dei contenuti:**

```text
/daodan:document Aggiorna materiali/rapporto-esistente.docx soltanto con le informazioni documentate in materiali/aggiornamenti.md. Mantieni aspetto, ordine delle sezioni, note, commenti e citazioni letterali. Puoi riscrivere i paragrafi coinvolti per renderli coerenti con l'aggiornamento; non eliminare condizioni o contenuti estranei alla modifica. Salva consegne/aggiornamento/rapporto-aggiornato.docx e documenta variazioni, preservazione e verifiche non disponibili.
```

**Restyle degli stessi contenuti:**

```text
/daodan:document Applica a materiali/rapporto-esistente.docx una nuova identità coerente con materiali/brand.pdf. Conserva integralmente testo, dati, citazioni e sequenza. Mostrami il confronto completo delle proposte, poi applica quella che scelgo. Salva consegne/restyle/rapporto-restyle.docx con confronto di preservazione e review del file renderizzato. Non modificare la sorgente.
```

**Percorso visibile:**

1. L'agente ispeziona l'originale e verifica il round-trip su copia prima delle modifiche sostanziali; una perdita non spiegata blocca la fase interessata.
2. Nella revisione modifica il contenuto coinvolto ereditando il look. Nel restyle riapre la scelta visiva conservando contenuto e sequenza.
3. Confronta sorgente e candidato, controlla le pagine salvate e documenta tagli autorizzati, differenze e limiti.

**Consegna riconoscibile:** il candidato richiesto e i relativi rapporti. Una revisione non ridisegna tutto il documento; un restyle non sintetizza il testo per farlo entrare. La copertura letterale aiuta a rilevare omissioni, ma non certifica da sola significato o resa delle pagine. Una preservazione richiesta e non dimostrabile resta un limite bloccante, non un successo implicito.

**Variante riutilizzabile:** se vuoi il nuovo aspetto anche per lavori futuri, chiedi `/daodan:theme` con gli stessi materiali di brand, formati Word e PowerPoint e destinazioni `consegne/brand/base.dotx` e `consegne/brand/base.potx`. Richiedi esemplari modificabili, `DESIGN.md`, mappa di stili/layout e istruzioni di riuso. I campioni nativi devono essere aperti e renderizzati; una preview non prova il comportamento dei template.

## 4. Modifica locale, controllo e riparazione

**Materiale da fornire:** un file esistente, per esempio `materiali/proposta.docx`. Per applicare risultati già ottenuti, fornisci anche il report relativo allo stesso SHA-256 del file. Il controllo statico è separato dalla disponibilità del motore necessario a modificare o renderizzare.

**Modifica circoscritta:**

```text
/daodan:document In materiali/proposta.docx sostituisci solo la dicitura “Referente progetto” con “Responsabile progetto” nell'intestazione della tabella contatti. Conserva tutto il resto, inclusi formati, link e commenti. Salva consegne/proposta/proposta-corretta.docx e verifica modifica e preservazione senza avviare un restyle.
```

**Controllo senza modifica:**

```text
/daodan:verify Controlla materiali/proposta.docx senza modificarlo. Restituisci difetti con posizione, gravità e classe di riparazione, identità SHA-256 e controlli non effettuati. Copri le verifiche aggiuntive con i motori disponibili e segnala le altre come non verificate.
```

**Riparazione autorizzata:**

```text
/daodan:fix Ripara i difetti safe e content di materiali/proposta.docx senza inventare informazioni. Non applicare i finding review: elencali con la modifica proposta. Salva il candidato in consegne/proposta/proposta-riparata.docx e confronta i report prima e dopo, mantenendo la sorgente integra.
```

**Percorso visibile:**

1. L'agente distingue l'edit locale dal controllo o dalla riparazione; non riapre contenuto e tema globali per una sostituzione.
2. `verify` produce findings senza modifiche. `fix` verifica prima la sorgente, salvo report già valido per la stessa identità, poi interviene su copia.
3. La copia riparata viene consegnata solo se le correzioni sono confermate e non compaiono nuovi finding; in caso contrario vengono riportati modifica rifiutata e causa.

**Consegna riconoscibile:** nell'edit il nuovo DOCX con confronto e review mirata; in `verify` il rapporto, senza nuovo file corretto; in `fix` il candidato accettabile, entrambi i report e i problemi ancora aperti. Un `pass` statico non certifica layout o campi aggiornati. Per una review delle pagine puoi chiedere `/daodan:document Rivedi materiali/proposta.docx in sola lettura e restituisci il rapporto sulle pagine renderizzate, senza modificare il file`; richiede rendering e review indipendente effettivi.

## 5. Workbook con formule reali e controllo indipendente

**Materiali da fornire:** `materiali/interventi.csv`, con colonne `id`, `data`, `sede`, `ore_previste`, `ore_effettive`, una riga per intervento e unità definite. Specifica eventuali identificativi duplicati o rettifiche. Servono GridCraft e supporto effettivo alle formule scelte per scrivere e ricalcolare il file; l'ispezione del pacchetto da sola non esegue i calcoli.

**Richiesta da copiare:**

```text
/daodan:workbook Crea consegne/interventi/consuntivo.xlsx da materiali/interventi.csv. Mantieni gli input in un foglio Dati, crea formule modificabili per scostamento (ore effettive meno ore previste) e un riepilogo per sede con totali. Calcola l'indice complessivo come totale ore effettive diviso totale ore previste; con denominatore zero mostra “non calcolabile”. Una misura mancante resta mancante e va segnalata, non diventa zero. Usa un grafico nativo collegato agli intervalli se rende più chiaro il confronto. Verifica i totali direttamente dal CSV con un calcolo separato, controlla righe aggiunte e casi di dati mancanti o denominatore zero. Consegna il workbook e una review che distingua formule conservate, ricalcolo effettivo e controlli visivi. Non modificare il CSV.
```

**Percorso visibile:**

1. L'agente controlla colonne, tipi, unità e definizioni; segnala incongruenze che cambierebbero il risultato.
2. Costruisce il workbook con formule riferite agli input, lo salva e lo riapre con il motore disponibile.
3. Confronta i risultati con aggregazioni ricavate separatamente dai dati sorgente e controlla rappresentazione e casi limite.

**Consegna riconoscibile:** `consuntivo.xlsx` con fogli e formule ispezionabili, grafico nativo se utile e review con calcolo indipendente, motore usato ed eventuali errori o limiti. Modificando un input le formule devono mantenere la relazione prevista: totali digitati a mano non soddisfano la richiesta. Se il ricalcolo non è disponibile, deve risultare non verificato; un flag di ricalcolo futuro o una cache numerica non provano che sia avvenuto. Questo scenario segue il metodo XLSX, senza imporre `CONTENT.md` o `DESIGN.md` DOCX/PPTX.

## Contratti degli esempi

Le sequenze derivano da [intake e routing](../../../plugins/office/skills/intake/references/routing.md), dai metodi [DOCX](../../../plugins/office/skills/docx/SKILL.md), [PPTX](../../../plugins/office/skills/pptx/SKILL.md), [XLSX](../../../plugins/office/skills/xlsx/SKILL.md) e [integrity](../../../plugins/office/skills/integrity/SKILL.md). Le proposte e i template seguono il [metodo design](../../../plugins/office/skills/design/SKILL.md). Per requisiti mancanti e significato delle evidenze consulta [dipendenze](dependencies.md) e [verifiche](verification.md).
