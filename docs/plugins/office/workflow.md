# Intake del lavoro e percorso di produzione

[Indice Office](../office.md) · [Funzioni](functions.md) · [Esempi d'uso](examples.md)

Parti dai materiali e dal risultato che vuoi ottenere. Office legge le fonti, riusa le decisioni già disponibili e attiva le fasi necessarie all'operazione. Per una richiesta mista o ancora senza formato usa l'ingresso `start`; quando il formato è deciso puoi usare `document`, `presentation` o `workbook`.

Questa pagina descrive l'intake di un lavoro Office. L'[intake di componenti esterni](upstream-intake.md) riguarda invece la manutenzione del plugin.

## Dalla richiesta al file

| Passaggio | Decisione o risultato | Responsabile |
|---|---|---|
| Intake | Materiali, operazione, pubblico, obiettivo, formati, vincoli e dipendenze | Coordinatore con `office:intake` |
| Progetto editoriale DOCX/PPTX | Fatti, fonti, messaggi, sequenza, trasformazioni e proiezioni dei formati richiesti | `office:content` e `content-strategist` |
| Progetto visivo DOCX/PPTX | Direzioni sul contenuto reale tramite Taste v2 e contratto Office | `office:design` |
| Prova delle proposte | Composizione, campioni nativi rappresentativi e critica prima della galleria e della scelta | Designer, coordinatore e reviewer DOCX/PPTX esistenti |
| Composizione finale | Distribuzione restante in sezioni Word o slide secondo la scelta registrata | Designer DOCX o PPTX |
| Produzione | Candidato nativo separato dalla sorgente, salvato e riaperto | Coordinatore e runtime del formato |
| Revisione | Fedeltà alle fonti, preservazione, modificabilità e risultato renderizzato | Reviewer del formato e coordinatore |

Il progetto visivo riceve il brief già risolto e contenuti completi con identità stabili. Le prove usano proposte ancora non selezionate; la composizione finale usa le revisioni accettate. Una consegna Word e PowerPoint condivide fatti e identità, ma conserva una distribuzione diversa: non impone una corrispondenza pagina-slide.

XLSX segue il proprio metodo. La richiesta di un workbook non attiva automaticamente il progetto editoriale e visivo DOCX/PPTX.

## Che cosa raccoglie l'intake

Ogni materiale ha un ruolo dichiarato: fonte informativa, brand o template vincolante, riferimento estetico, file da trasformare oppure asset utilizzabile. Lo stesso file può svolgere più ruoli. La provenienza e i diritti vengono verificati per l'uso richiesto.

L'intake chiarisce intento, pubblico, settore, fruizione, ampiezza, profondità, estensione, densità, tono e formati. Registra anche quali parti possono essere riscritte, sintetizzate o riorganizzate e quali devono restare identiche. Un budget di pagine non autorizza a eliminare condizioni decisive.

Si leggono prima i materiali; si chiedono in una sola tornata le sole decisioni sostanziali rimaste aperte. Un brief completo o un incarico autonomo non richiedono domande ripetute. La mancanza di una dipendenza viene registrata con il lavoro che blocca e la relativa recovery, secondo la [pagina dipendenze](dependencies.md).

## Il percorso cambia con l'operazione

| Operazione | Contenuto | Identità visiva e composizione |
|---|---|---|
| Creare | Piano completo | Progetto ad hoc nei formati richiesti |
| Derivare | Nuova proiezione per scopo o pubblico, preservando i claim ereditati | Look ereditato o nuovo secondo il brief |
| Ampliare | Piano delle aggiunte e dei contenuti mossi | Decisioni accettate ereditate; composizione del delta |
| Revisionare o condensare | Trasformazioni e tagli consentiti tracciati | Aspetto ereditato; unità interessate |
| Restyle | Testi, fatti e sequenza conservati | Nuovo progetto visivo entro lo scopo |
| Modifica locale | Solo contenuti autorizzati | Nessun riavvio globale del design |
| Review o export | Nessuna rielaborazione implicita | Sorgente invariata; rapporto o export richiesto |

Una richiesta combinata esegue l'unione dei passaggi necessari. Se il contenuto non entra nello spazio disponibile, la soluzione torna a contenuto e composizione: redistribuzione, appendice o decisione sulle priorità. Ridurre il testo fino a renderlo illeggibile non risolve il problema.

## Record e autorità

| Record o artefatto | Che cosa conserva |
|---|---|
| Brief e sezione dipendenze | Richiesta, materiali, decisioni, autorizzazioni e capacità disponibili; sono parti del record esistente |
| `CONTENT.md` | Fonti identificate, claim, unità editoriali, permessi di trasformazione e proiezioni DOCX/PPTX |
| Confronto HTML e `DESIGN.md` | Alternative visive e scelta esplicita, oppure scelta autonoma già autorizzata |
| Piani del formato | Struttura e composizione Word; plan e geometrie PowerPoint |
| Candidato e review | File effettivo, identità, verifiche, differenze e limiti |

`CONTENT.md` e `DESIGN.md` vengono caricati e validati esplicitamente: il loro nome non prova che un agente li abbia letti. Identità del progetto, revisione del contenuto e formati richiesti devono coincidere. La proiezione PPTX si lega al plan effettivo; non introduce uno schema slide concorrente.

Il confronto HTML v2 mostra normalmente due o tre proposte tramite render esatti di campioni nativi sugli stessi contenuti rappresentativi: apertura e lavoro più difficile di lettura, evidenza, tabella o processo. I reviewer verificano prima carattere, pertinenza, immagini, forme, tipografia e contenuto denso. Una proposta insufficiente torna in revisione prima della scelta. Il precedente sampler v1 resta limitato ai temi e non soddisfa questa prova creativa. La scelta deve essere registrata; evidenziare una proposta nel browser non equivale, da solo, a restituire una decisione al coordinatore.

Taste restituisce direzioni e critica ai record e ai ruoli Office tramite il [contratto canonico](../../../plugins/office/skills/design/references/art-direction.md), senza un nuovo intake. Il controllo del risultato finale avviene ancora sul file Office salvato, secondo [verifiche e limiti](verification.md).

## Fonti del contratto

- [Intake e tabella delle operazioni](../../../plugins/office/skills/intake/SKILL.md).
- [Metodo editoriale](../../../plugins/office/skills/content/SKILL.md) e [contratto dei record](../../../plugins/office/skills/content/references/records.md).
- [Design condiviso](../../../plugins/office/skills/design/SKILL.md) e [confronto completo](../../../plugins/office/skills/design/references/records.md).
- Metodi [DOCX](../../../plugins/office/skills/docx/SKILL.md), [PPTX](../../../plugins/office/skills/pptx/SKILL.md) e [XLSX](../../../plugins/office/skills/xlsx/SKILL.md).
