# Aggiornare le fonti già registrate

Consultare il [README Office](../../../plugins/office/README.md#sources-pins-and-licenses) per identificare il contributo, la revisione fissata e il record di provenienza prima di proporre un aggiornamento. Una nuova fonte segue invece il [primo intake esterno](upstream-intake.md).

[Torna alla guida Office](../office.md).

## Quando esaminare un aggiornamento

La [procedura canonica di sincronizzazione](../../../.claude/skills/upstream-sync/SKILL.md) esclude gli snapshot di design Office dai controlli periodici e dai batch generici. Il riesame è manuale, quando richiesto per Office o per una fonte specifica, oppure quando un difetto concreto richiede evidenza upstream. Una nuova release non obbliga ad adottarla.

| Contributo | Perimetro locale | Trattamento |
|---|---|---|
| Agentit editoriale e tipografia | Due guide adattate, con [pin, hash e modifiche](../../../plugins/office/skills/design/references/agentit-upstream.md) | Confrontare le fonti originali alla revisione fissata; preservare confini Office e lineage Apache/MIT. |
| Theme Factory | Quattro palette seed nelle direzioni Q–T; [record di ritiro](../../../plugins/office/skills/design/references/theme-factory-upstream.md) | Skill, preset e showcase ritirati dalla distribuzione. Nessun obbligo di sync e nessun ripristino automatico. |
| PPT Visual | Sketch e passaggio alla specifica in [layout-patterns PPTX](../../../plugins/office/skills/pptx/references/layout-patterns.md#provenance) | Riesame manuale su richiesta del solo contributo registrato; palette e produzione restano Office. |
| Ispirazione Word | [Composizioni DOCX originali](../../../plugins/office/skills/docx/references/layout-patterns.md#provenance) | Provenienza, non target di copia o merge. Le idee si valutano come ispirazione originale. |
| Motore di conversione open-slide | Undici file verbatim in [pptx/lib/open-slide-pptx](../../../plugins/office/skills/pptx/lib/open-slide-pptx/UPSTREAM.md), bundle e `manifest.json` | Unico target copied-source di Office: riesame manuale su richiesta, avanzamento deliberato del pin, ricopia verbatim, `node rebuild.mjs`, conversione della fixture e suite Office. Non modificare mai un file venduto: la guardia degli hash lo tratta come drift. |

Le versioni effettive di WordCraft, DeckCraft e GridCraft appartengono alla manutenzione dei runtime delegati. Distinguere revisione di riferimento, versione disponibile e versione installata; non ricavare compatibilità da un pin documentale. Vedere [dipendenze](dependencies.md).

## Procedura delimitata

1. **Fissare scopo e base.** Identificare richiesta o difetto, proprietario locale, percorsi registrati e revisione di partenza. Annotare modifiche locali preesistenti; ispezionare contratto, licenza completa, notice e lineage della revisione proposta. Un aggiornamento non autorizza nuovi target copiati.
2. **Confrontare soltanto il materiale pertinente.** Leggere base upstream, nuovo upstream e adattamento locale. Conservare un diff consultabile e classificare ogni differenza con la tabella sotto; una divergenza può essere intenzionale. Registrare nuove rimozioni o aggiunte senza estendere automaticamente il perimetro.
3. **Applicare edit mirati nel proprietario.** Integrare solo il contributo verificato, preservando frontmatter, namespace, attribuzioni, stile locale e contratti Office. Un conflitto sostanziale non risolto dalle decisioni esistenti richiede una decisione esplicita. Non sovrascrivere le guide con l'upstream grezzo.
4. **Verificare contenuti, termini e consumo reale.** Controllare fedeltà alle fonti, brand, font, record condivisi, composizioni native e contratti di produzione/review interessati. Riesaminare licenze e notice; usare casi pertinenti per dimostrare beneficio e assenza di regressioni. Aggiornare pin e provenienza dopo questi controlli, senza attribuire al merge una prova runtime.
5. **Rigenerare e consegnare secondo autorizzazione.** Se cambia un kernel, incrementare le versioni richieste, ricompilare tutti e cinque gli host e rigenerare i riferimenti. Eseguire i gate previsti sul candidato; registrare limiti, file modificati e prove. Commit e push avvengono solo entro l'autorizzazione di pubblicazione del compito.

### Classificare il diff

| Classe canonica | Significato | Decisione |
|---|---|---|
| `clear win` | Correzione o aggiunta utile senza conflitto locale | Integrare solo se dentro policy e perimetro già autorizzato. |
| `minor refinement` | Ritocco limitato di testo o metadati | Integrare se non altera convenzioni e contenuto locale. |
| `hard merge` | Upstream e Office hanno evoluto la stessa parte | Ricomporre il contributo mantenendo le decisioni locali valide. |
| `intentional drift` | Attribuzioni, namespace, stile o capacità sono adattamenti voluti | Conservare la divergenza motivata. |

La classificazione viene dalla procedura canonica; nessuna classe supera il divieto di nuove copie vendorizzate. I record di ispirazione restano esclusi dalle operazioni di pull e merge.

## Confini da conservare

L'adattamento Agentit fornisce guida editoriale e tipografica. Non trasferisce harness, altri agenti, installer o una seconda pipeline di report. Conservare flusso DOCX, oggetti PPTX modificabili, controllo font, render del candidato salvato e strumenti immagine dell'harness.

PPT Visual contribuisce sketch di regioni e handoff verso la specifica. Non diventa skill, motore, catalogo cromatico o owner del tema parallelo. L'ispirazione Word non trasferisce testo, asset, font o automazione macOS.

La parte storica del record Theme Factory descrive anche file un tempo conservati byte per byte. La nota iniziale di ritiro e la tabella canonica di sync definiscono il perimetro presente: non interpretare quel testo storico come inventario degli asset distribuiti o istruzione a ripristinarli.

Per ogni incremento, la relazione originale (§14.5) propone cinque criteri di coerenza: una sede normativa, contesto caricato per necessità, patrimonio locale preservato, istruzioni eseguibili e beneficio verificato. La review esamina anche i riferimenti annidati e gli export, senza dedurre risparmi di token dalla sola riduzione del testo.

## Compilazione e verifica

Gli aggiornamenti modificano `plugins/office/`; eventuali meccanismi specifici di host appartengono ad `adapters/`. Gli export e i cataloghi radice restano generati. Per una modifica effettiva al kernel, la procedura canonica indica:

```text
python scripts/daodan_build.py
python scripts/sync_plugin_docs.py
python scripts/daodan_build.py --check
python scripts/sync_plugin_docs.py --check
```

Questi comandi sono riferimenti per la manutenzione autorizzata, non operazioni eseguite da questa pagina. Restano necessari gli altri gate del repository; se cambiano le skill di workflow canoniche, si rigenerano e verificano anche le copie native Codex.

La compilazione prova riproducibilità e contratti di adattamento, non esecuzione sull'host installato o fedeltà in Word/PowerPoint. I controlli sul file nativo e la review del candidato rimangono evidenze distinte, descritte in [verifica](verification.md).

## Automazione proposta

La relazione (§14.4) propone un eventuale `office_upstream.py` per elencare revisioni e produrre diff. Non è un helper implementato né una CLI disponibile. La proposta non prevede merge, aggiornamento automatico dei pin o commit; prima di mappe stabili resta sufficiente la procedura manuale canonica.
