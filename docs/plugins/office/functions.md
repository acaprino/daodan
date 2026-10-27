# Funzioni Office

[Indice Office](../office.md) · [Esempi d'uso](examples.md) · [Percorso di lavoro](workflow.md)

Scegli l'ingresso dal risultato che vuoi ricevere e descrivi materiali, destinatario e vincoli in linguaggio naturale. Office organizza il lavoro necessario per ottenere file Word, PowerPoint o Excel modificabili, oppure un rapporto di verifica.

## I sette ingressi

La notazione `/daodan:…` qui sotto è quella di Claude. Negli altri host usa il mapping in [Host](../../hosts.md) e il [riferimento generato del plugin](../office.md#source-derived-reference). In Codex gli ingressi sono workflow skill, per esempio `document-workflow` del plugin `daodan`: non sono comandi da eseguire nel terminale. Gli ingressi appartengono a `daodan`; Office fornisce i metodi che caricano.

| Se vuoi… | Ingresso | Risultato richiesto |
|---|---|---|
| Partire da materiali misti o ricevere più formati | [`/daodan:start`](../../../plugins/daodan/workflows/start.md) | Individua destinazioni e operazioni, poi esegue i metodi pertinenti condividendo le decisioni |
| Creare, derivare, aggiornare, leggere o esportare un documento | [`/daodan:document`](../../../plugins/daodan/workflows/document.md) | DOCX modificabile, review o export secondo la richiesta |
| Creare, derivare, aggiornare, leggere o esportare una presentazione | [`/daodan:presentation`](../../../plugins/daodan/workflows/presentation.md) | PPTX modificabile, review o export secondo la richiesta |
| Costruire, aggiornare o analizzare un foglio di lavoro | [`/daodan:workbook`](../../../plugins/daodan/workflows/workbook.md) | XLSX con formule e oggetti nativi, oppure analisi in sola lettura |
| Controllare un file senza cambiarlo | [`/daodan:verify`](../../../plugins/daodan/workflows/verify.md) | Difetti, gravità, posizione, possibili riparazioni e controlli non effettuati |
| Riparare difetti di un file | [`/daodan:fix`](../../../plugins/daodan/workflows/fix.md) | Candidato separato, confronto prima/dopo e problemi rimasti aperti |
| Ottenere basi riutilizzabili per Word o PowerPoint | [`/daodan:theme`](../../../plugins/daodan/workflows/theme.md) | DOTX e/o POTX richiesti, esempi nativi, sistema visivo e istruzioni di riuso |

Le richieste copiabili sono negli [esempi d'uso](examples.md). L'[intake](workflow.md#che-cosa-raccoglie-lintake) legge prima gli input e chiede soltanto decisioni sostanziali ancora aperte. Un brief completo o un'autonomia già autorizzata non richiedono una nuova conferma a ogni passaggio.

## Contenuti adatti al lettore

Per DOCX e PPTX il progetto editoriale stabilisce che cosa comunicare, con quale profondità e in quale sequenza. Pubblico, obiettivo, settore, lettura autonoma o presentazione dal vivo, ampiezza, lunghezza, densità e tono sono decisioni distinte. Accorciare un rapporto non autorizza a eliminare le condizioni che rendono corretta un'affermazione.

Il record `CONTENT.md` collega fonti, fatti e unità di testo alle destinazioni richieste. I permessi possono variare per blocco: una citazione resta letterale mentre un'altra sezione può essere riorganizzata o sintetizzata. Conflitti e dati mancanti restano visibili; non vengono colmati con numeri o prove inventate. La fedeltà delle trasformazioni richiede anche confronto con le fonti, oltre alla validazione del record. Vedi il [metodo editoriale](../../../plugins/office/skills/content/SKILL.md).

## Un'identità visiva, composizioni diverse

Quando serve un nuovo aspetto, Office prepara normalmente due o tre proposte complete su contenuti reali e rappresentativi. Il confronto HTML mostra tipografia, gerarchia, colori, immagini e trattamento dei dati; una sola copertina o una preview cromatica non bastano. La scelta esplicita, oppure quella compiuta entro un'autonomia già concessa, viene registrata in `DESIGN.md`. Brand e template vincolanti precedono i cataloghi di ispirazione. Vedi il [metodo di design](../../../plugins/office/skills/design/SKILL.md).

Un rapporto e il suo deck condividono contenuti e identità del progetto, con le stesse revisioni dei record editoriali e visivi. La composizione rimane specifica: Word usa sezioni, stili e flusso su pagine; PowerPoint usa slide, geometrie e oggetti. Una pagina non diventa automaticamente una slide. I rispettivi [metodi DOCX](../../../plugins/office/skills/docx/SKILL.md) e [PPTX](../../../plugins/office/skills/pptx/SKILL.md) producono composizione e review distinte.

XLSX segue il [proprio metodo](../../../plugins/office/skills/xlsx/SKILL.md): definizioni dei dati, formule modificabili, calcolo e confronto dei risultati con un riferimento indipendente. Non acquisisce automaticamente le fasi editoriali e visive di documenti e deck.

## Conservare, modificare, riutilizzare

I file forniti restano integri; ogni modifica salva un candidato separato. Prima di intervenire su un file esistente vengono ispezionate le sue caratteristiche e verificata la capacità del motore di conservarle. Per DOCX/PPTX le procedure di [WordCraft](../../../plugins/office/skills/wordcraft/SKILL.md) e [DeckCraft](../../../plugins/office/skills/deckcraft/SKILL.md) richiedono un round-trip senza modifiche su copia, confronto e resa effettiva prima delle modifiche sostanziali. Anche XLSX richiede confronto del round-trip su copia, secondo il proprio metodo. Commenti, revisioni, campi, master o formule non si considerano preservati soltanto perché il file si apre.

La portata decide il lavoro: aggiornare alcuni dati eredita il look accettato; un restyle conserva contenuti e sequenza; una modifica locale interessa solo l'elemento autorizzato. Review ed export conservano la sorgente. La [tabella delle operazioni](workflow.md#il-percorso-cambia-con-loperazione) distingue questi casi.

Stili, temi e layout nativi incorporano il design scelto. Un normale DOCX/PPTX non richiede un template separato. Per riutilizzarlo in altri lavori chiedi `theme`, indicando i formati e i materiali di brand: la consegna comprende le basi DOTX/POTX richieste, esemplari da aprire e istruzioni di sostituzione. Un template fornito e vincolante viene ereditato. Le caratteristiche dichiarate devono risultare dal report del kit e da un campione nativo aperto e renderizzato.

## Che cosa rende completa una consegna

Il file nativo salvato viene riaperto e controllato. Per documenti e deck, la review indipendente usa la copia esatta e le sue pagine o slide renderizzate. Per un workbook, formule conservate e formule effettivamente ricalcolate sono evidenze diverse. `verify` aggiunge i controlli statici del [metodo integrity](../../../plugins/office/skills/integrity/SKILL.md), che da soli non dimostrano impaginazione o correttezza dei calcoli.

Produzione e rendering richiedono motori esterni disponibili nel contesto del lavoro. Se manca una capacità, il rapporto deve indicare la consegna bloccata e i controlli non effettuati: un piano o una preview HTML non equivalgono al file Office verificato. Consulta [dipendenze](dependencies.md) e [verifiche e limiti](verification.md).

Per i manutentori: il [manifest](../../../plugins/office/plugin.toml) registra dieci skill e cinque ruoli, senza workflow propri. La [struttura del plugin](structure.md) e il [riferimento generato](../office.md#registered-components) ne descrivono responsabilità e sorgenti. La presenza di questi componenti negli export non prova l'esecuzione del percorso su ogni host.
