# Dipendenze, prerequisiti e runtime

[Indice Office](../office.md) · [Intake del lavoro](workflow.md) · [Licenze](licenses.md)

Installare il plugin rende disponibili i metodi Office. La produzione dei file richiede anche le capacità e i runtime della fase richiesta. Il coordinatore verifica ciò che è realmente disponibile prima di usarlo.

## Dipendenza locale e ingressi

Il [manifest Office](../../../plugins/office/plugin.toml) richiede `work-controller`, che gestisce record, domande, decisioni, consegne e verifiche. Il plugin `daodan` espone i sette ingressi Office e carica i metodi attraverso la dipendenza locale dichiarata.

Il [riferimento generato](../office.md#source-derived-reference) è la fonte per l'inventario delle dipendenze e degli export. Per le procedure di installazione dei diversi host usare [host e distribuzione](../../hosts.md); un esempio Claude non crea lo stesso comando o strumento su un altro host.

## Direzione artistica con Taste v2

Office dichiara la dipendenza obbligatoria `taste-skill@taste-skill` e carica la skill `design-taste-frontend` soltanto per direzione artistica e critica visiva. Il [contratto unico di input e output](../../../plugins/office/skills/design/references/art-direction.md) riceve brief, contenuto, vincoli e capacità già risolti e restituisce proposte DESIGN, richieste di asset e osservazioni ai ruoli Office esistenti. Non avvia un secondo intake o workflow. Modifiche locali, contenuti con look ereditato e operazioni in sola lettura mantengono il proprio perimetro.

La revisione esaminata è Taste 2.1.5, identificata nell'[indice delle fonti](../../../plugins/office/README.md#sources-pins-and-licenses). Claude e Codex hanno pacchetti upstream; sugli altri host occorre predisporre la cartella completa della skill e verificarne l'identità nel registro effettivo. La reference canonica indica i percorsi e la recovery per ciascun host. File presenti e compilazione non provano l'esecuzione installata.

Prima delle fasi Office si rispettano i prerequisiti di attivazione dei pacchetti richiesti dall'host: un provider obbligatorio disabilitato può fermare l'intero ingresso. Saltare il lavoro creativo non aggira questo controllo. Dopo l'attivazione, l'indisponibilità della conoscenza artistica Taste ferma soltanto la fase che la richiede; il lavoro indipendente autorizzato può proseguire. Il coordinatore registra identità, versione, reference consultate e recovery nel brief esistente, senza sostituire silenziosamente il provider.

## Runtime per formato

| Risultato | Runtime previsto dal metodo | Contratto da consultare |
|---|---|---|
| DOCX modificabile, render o PDF Word | [WordCraft](https://github.com/storytold/wordcraft) | [Metodo](../../../plugins/office/skills/wordcraft/SKILL.md) e [runtime](../../../plugins/office/skills/wordcraft/references/runtime.md) |
| PPTX modificabile, render o PDF delle slide | [DeckCraft](https://github.com/storytold/deckcraft) | [Metodo](../../../plugins/office/skills/deckcraft/SKILL.md) e [runtime](../../../plugins/office/skills/deckcraft/references/runtime.md) |
| XLSX con formule e calcolo | [GridCraft](https://github.com/storytold/gridcraft) | [Metodo](../../../plugins/office/skills/gridcraft/SKILL.md) e [runtime](../../../plugins/office/skills/gridcraft/references/runtime.md) |
| PPTX nativo da un design HTML approvato | Motore open-slide incluso nel plugin, con Node, modulo Playwright 1.48 o successivo e browser Chromium esterni | [Contratto di conversione](../../../plugins/office/skills/pptx/references/html-to-pptx.md) e [provenienza](../../../plugins/office/skills/pptx/lib/open-slide-pptx/UPSTREAM.md) |

Office distribuisce metodi, bridge e inspector; gli engine, gli installer e i server MCP dei runtime non sono inclusi nel plugin. L'unica eccezione è il motore di conversione HTML→PPTX, copiato in perimetro delimitato sotto autorizzazione del proprietario e protetto dagli hash di `manifest.json`; Node, il modulo Playwright e il browser restano prerequisiti esterni con recovery esplicita.
 Il run scopre eseguibile o strumenti esposti, versione e schema effettivo dei comandi. Una versione di riferimento non dimostra che quel runtime sia installato o compatibile con ogni file.

Il metodo DOCX contempla un engine diverso soltanto con una scelta esplicita e capacità provate. Un inspector che legge il package non è un motore di scrittura. I workbook con funzionalità non preservate dal runtime richiedono una decisione sullo scopo prima dell'editing.

## Altre capacità da verificare

| Classe | Che cosa serve verificare |
|---|---|
| Host | Lettura/scrittura, shell, rete, browser e isolamento/dispatch richiesti dalla fase; i nomi effettivi degli strumenti |
| Font | Famiglie, pesi e glifi disponibili; diritti d'uso e incorporamento; fallback dichiarati |
| Asset | Origine, disponibilità e diritti per logo, fotografie, immagini e template |
| File esistenti | Identità, feature sensibili e comportamento del round-trip prima di modifiche sostanziali |
| Conoscenza esterna | Provenienza e perimetro degli adattamenti già presenti; procedura distinta per nuove adozioni |

Nella sezione dipendenze del brief si registrano identità, proprietario, fase, requisito, fonte, versione/revisione, diritti, capacità, esito osservato, limiti e recovery. Le fonti già stabili non vengono riesaminate da zero per ogni documento.

## Quando manca una dipendenza

La mancanza di un runtime ferma la produzione che ne dipende. La lettura delle fonti e il lavoro progettuale indipendente possono proseguire. Un'installazione o sostituzione non è implicita nella richiesta di creare un file.

Il risultato deve indicare la capacità mancante e il passo concreto per recuperarla. Non si consegna una preview HTML o un PDF come se soddisfacesse la richiesta di un file nativo modificabile. Anche una produzione riuscita deve rendere visibili le [verifiche non disponibili](verification.md).

## Fonte operativa

Il [preflight delle dipendenze](../../../plugins/office/skills/intake/SKILL.md#dependency-preflight) governa il record; [intake esterno](upstream-intake.md) e [aggiornamenti upstream](upstream-updates.md) governano invece l'evoluzione dei contributi del plugin.
