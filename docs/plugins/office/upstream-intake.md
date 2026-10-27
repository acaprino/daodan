# Valutare una nuova fonte esterna

Partire dalla capacità Office mancante e dal suo proprietario locale, prima di scegliere una fonte esterna. Questa pagina riguarda il primo esame di un contributo; per raccogliere la richiesta di un documento usare il [flusso di lavoro](workflow.md), per aggiornare adattamenti registrati usare [gli aggiornamenti upstream](upstream-updates.md).

[Torna alla guida Office](../office.md).

## Confine di policy

La [policy canonica di intake](../../../.claude/skills/external-repo-intake/SKILL.md) vieta nuove copie vendorizzate. Una richiesta di importazione, una licenza permissiva o una riga di provenienza non rimuovono questo vincolo. Le possibilità correnti sono:

| Modalità | Applicazione | Responsabilità da conservare |
|---|---|---|
| Delegazione | Un fornitore esterno offre già la capacità | Dipendenza dichiarata, contratto di ingresso/uscita, disponibilità e recupero sull'host attivo. Il metodo resta al fornitore. |
| Ispirazione locale originale | Idee esterne motivano un metodo locale distinto | Testo e implementazione originali, attribuzione delle idee e responsabilità Office esplicita. |
| Adattamento storico con materiale copiato | Esiste già un perimetro registrato | Provenienza, licenze e modifiche si conservano; la manutenzione segue il perimetro esistente. Questa storia non apre nuovi target. |

WordCraft, DeckCraft e GridCraft sono runtime forniti separatamente, non motori copiati nel kernel. Il loro uso e le prove necessarie sono descritti nelle [dipendenze](dependencies.md).

## Percorso di valutazione

1. **Descrivere la lacuna osservata.** Indicare il risultato atteso, il caso reale che manca e quale metodo Office ne è responsabile. La direzione della [relazione originale](../../../Relazione%20sul%20sistema%20unificato%20Office%20per%20contenuti%20e%20design%20DOCX%20e%20PPTX.md) (§§11 e 18–20) prevede prima una prova completa DOCX/PPTX con gli strumenti presenti, poi contributi selettivi per lacune dimostrate.
2. **Scegliere il modo di integrazione.** Riutilizzare autorizzazioni e decisioni del compito. Verificare sovrapposizione, proprietario canonico e consumo effettivo; una delegazione richiede disponibilità e contratto eseguibile sull'host, un'ispirazione richiede contenuto originale.
3. **Ispezionare fonte e termini senza importare.** Registrare repository, percorsi, revisione consultata, licenza completa, copyright, eventuali notice e provenienza secondaria. La policy contiene il gate applicabile: l'ispezione non autorizza copie e una fonte senza termini completi non diventa materiale distribuibile.
4. **Definire un contributo delimitato.** Indicare destinazioni nel proprietario esistente, consumatori, parti escluse, adattamento DOCX/PPTX e controlli. Conservare fonti, claim, trasformazioni autorizzate, brand e contenuti reali; la valutazione non consente dettagli inventati per completare l'esempio.
5. **Verificare e consegnare nel perimetro autorizzato.** Confrontare qualità e costo con la baseline. Conservare decisione, limiti e provenienza nel record del lavoro. Modifiche al kernel richiedono versionamento, compilazione di tutti gli host e verifiche; commit e pubblicazione richiedono l'autorizzazione del compito.

L'eventuale apertura di nuovi adattamenti copiati richiede una modifica formale della policy canonica e delle istruzioni collegate, oppure un'eccezione esplicita e circoscritta. La relazione e questa guida non costituiscono tale autorizzazione.

## Candidati Office e contributi proposti

Il [README Office](../../../plugins/office/README.md#sources-pins-and-licenses) è l'indice dei contributi integrati. Taste v2 è adottato come dipendenza esplicita per direzione artistica e critica. Questa delegazione già autorizzata non riapre un intake per ogni lavoro Office. PPT Design resta un candidato.

| Fonte | Proposta attribuita alla relazione | Stato e confine |
|---|---|---|
| Taste v2 | Idea, direzione e critica sul render | Delegazione adottata tramite il contratto Office; nessuna copia vendorizzata. Contenuti e workflow restano Office. |
| PPT Design | Trasferimento delle reference e controllo compositivo PPTX | Candidato distinto; nessun secondo proprietario di tema o produzione. |
| PPT Visual e Word Document Design Agent | Miglioramenti mirati alla specifica PPTX o alle ricette Word | PPT Visual ha un adattamento delimitato esistente. Per Word esiste ispirazione originale; i termini completi mancavano nella fonte ispezionata. |
| Convenzione DESIGN.md | Idee per il record visivo | Il contratto locale Office è già presente. Non implica adozione di cataloghi, CLI o MCP esterni. |
| [open-slide](https://github.com/open-slide/open-slide) (`@open-slide/core` 2.3.1, MIT) | Conversione meccanica di un design HTML approvato in PPTX nativo | Copia delimitata autorizzata dal proprietario il 2026-10-27, unica eccezione al divieto di nuove copie: undici file verbatim al pin `82349cf2d07d37b75975170503a82fcaacae9298`, bundle con `fflate` e `html-to-image` (MIT), hash di controllo, [contratto](../../../plugins/office/skills/pptx/references/html-to-pptx.md) e [protocollo di refresh](../../../plugins/office/skills/pptx/lib/open-slide-pptx/UPSTREAM.md). Scelto dopo il [confronto tra sei percorsi](verification.md#confronto-meccanico-html--pptx-e-docx-2026-10-27); nessuna estensione all'applicazione upstream. |
| Motore DOCX sul modello di open-slide | Stessa misura del DOM, serializzatore WordprocessingML a pagina fissa | Rimandato dal proprietario il 2026-10-27; nessuna implementazione. Nel confronto nessun percorso DOCX (WordCraft, `docx/html`) conservava la composizione; i documenti restano costruiti con WordCraft. |

GenOffice, Presenton, OfficeAgent.NET, DITA-OT, Pandoc, Unstructured, Semantic Kernel e librerie di templating sono alternative emerse dalla ricerca della relazione, non adottate né fallback impliciti. Una loro eventuale adozione richiede una valutazione separata.

### Perimetro adottato per Taste

Il [contratto canonico di direzione artistica](../../../plugins/office/skills/design/references/art-direction.md) definisce input, output, esclusioni e critica attraverso i ruoli Office esistenti. Le [dipendenze](dependencies.md#direzione-artistica-con-taste-v2) descrivono installazione e recovery; l'indice delle fonti conserva revisione e licenza esaminate. Il precedente record di valutazione resta storico e non autorizza copie o trasferimenti di contenuto, intake, tooling web e preset nel workflow Office.

## Registrare la decisione

La policy distingue i registri: una delegazione non aggiunge un target di sincronizzazione; un'ispirazione originale registra fonte, idee e revisione come osservazione, esclusa da pull e merge. Gli adattamenti storici mantengono i propri record.

Il gate di coerenza della relazione (§14.5) richiede un proprietario per regola, letture mirate, conservazione del patrimonio locale, istruzioni eseguibili e beneficio misurato. È una direzione di adozione da verificare sul contributo concreto, non prova che un'integrazione sia stata eseguita. Per termini conservati e verifiche vedere [licenze](licenses.md) e [verifica](verification.md).
