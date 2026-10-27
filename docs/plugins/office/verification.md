# Verifiche, prove e limiti

[Indice Office](../office.md) · [Esempi d'uso](examples.md) · [Dipendenze](dependencies.md)

Valutare il file richiede prove diverse. La validazione di un record, un confronto HTML, l'ispezione del package e l'apertura nell'applicazione Office rispondono a domande differenti.

## Che cosa dimostra ogni controllo

| Controllo | Prova fornita | Limite |
|---|---|---|
| Record `CONTENT.md` e `DESIGN.md` | Campi, riferimenti, revisioni e binding strutturali coerenti | Non dimostra da solo fedeltà semantica alle fonti |
| Confronto HTML v2 | Render esatti delle proposte native sullo stesso campione reale, con binding e provenienza | Hash e metadati da soli non provano derivazione dei render, modificabilità o qualità artistica; il campione non copre il file completo |
| Inspector e integrity checker | Struttura del package, feature inventariate, regole statiche e differenze | Non certifica layout, calcolo o conformità completa al formato |
| Render e review del candidato | Risultato visivo osservato e difetti rilevati sul file salvato | Vale per il candidato e il renderer effettivamente usati |
| Applicazione e runtime installati | Operazioni e feature realmente esercitate | Non generalizza automaticamente ad altri host, versioni o file |

La revisione confronta fonti e risultato: priorità, condizioni, incertezze, conflitti e blocchi vincolati. Una similarità testuale o una mappa compilata dal produttore non bastano a provare la conservazione del significato.

La critica visiva usa il [contratto Office/Taste](../../../plugins/office/skills/design/references/art-direction.md) sui render realmente ispezionati. Leggibilità e validità tecnica non bastano quando mancano carattere, pertinenza al soggetto o requisiti visivi del brief. Un esito positivo riguarda la prova osservata e non garantisce il gusto di ogni lettore. Il sampler HTML v1 resta una prova limitata dei temi.

## Prima e dopo una modifica

1. Inventaria la sorgente e registra le feature da preservare.
2. Verifica il round-trip senza modifiche quando richiesto dal metodo del formato.
3. Produci un candidato separato con le sole trasformazioni autorizzate.
4. Confronta contenuti, package e risultato renderizzato con la sorgente.
5. Consegna file, verifiche e limiti legati a quel candidato.

Per ristrutturazioni o condensazioni usa il controllo di coverage appropriato, con tagli autorizzati espliciti. Un confronto per posizione è adatto a modifiche locali e non sostituisce la coverage dopo un riordino.

Per XLSX, verifica formule e valori su risultati attesi indipendenti: totali derivati separatamente, identità di bilancio o casi noti. Il calcolo di GridCraft non equivale alla prova che Excel renda e ricalcoli ogni feature allo stesso modo.

## Strumenti e suite del repository

Questi sono riferimenti riproducibili per manutentori. La loro presenza non attesta che una particolare revisione abbia superato i test. I comandi seguenti sono esempi d'esecuzione dalla radice del repository; non sono eseguiti automaticamente dalla lettura della guida.

| Domanda | Fonti e controlli |
|---|---|
| I record conservano binding, lock e proiezioni? | [office_records.py](../../../plugins/office/skills/content/scripts/office_records.py), [test_office_records.py](../../../tests/test_office_records.py) |
| Le proposte usano dati reali, prove native e una selezione tracciata? | [design_compare.py](../../../plugins/office/skills/design/scripts/design_compare.py), [test v1](../../../tests/test_office_design_compare.py), [test v2](../../../tests/test_office_creative_comparison.py), [provenienza della scelta](../../../tests/test_office_creative_records.py) |
| Gli ingressi e i worker ricevono i contratti corretti? | [test_office_unified_contract.py](../../../tests/test_office_unified_contract.py) |
| Che cosa coprono gli inspector e il checker statico? | [test_office_docx.py](../../../tests/test_office_docx.py), [test_office_deckcraft.py](../../../tests/test_office_deckcraft.py), [test_office_xlsx.py](../../../tests/test_office_xlsx.py), [test_office_integrity.py](../../../tests/test_office_integrity.py) |
| Quali controlli riguardano palette, font e struttura del formato? | [test_office_palette.py](../../../tests/test_office_palette.py), [test_office_fonts.py](../../../tests/test_office_fonts.py), [test_office_document_design_contract.py](../../../tests/test_office_document_design_contract.py), [test_office_presentation_contract.py](../../../tests/test_office_presentation_contract.py) |

```text
python -m unittest discover -s tests -p test_office_records.py
python -m unittest discover -s tests -p test_office_design_compare.py
python -m unittest discover -s tests -p test_office_unified_contract.py
```

Per il checker sul file esatto e i suoi codici d'uscita consultare [office:integrity](../../../plugins/office/skills/integrity/SKILL.md). Un `pass` statico lascia esplicite le voci non controllate.

## Confronto meccanico HTML → PPTX e DOCX (2026-10-27)

Prova che ha motivato la copia del motore open-slide. Una sorgente HTML congelata di tre tavole 1280×720 (griglia e flex, gradienti, sovrapposizioni, PNG ritagliato, due SVG, tabella con celle unite, testo lungo; SHA-256 `cb1ba3e3d1faa6c832ebc0189ca8bba59bbebeb60695a20bd90cb7a884d71d1d`) è stata convertita da sei percorsi, senza chiamate a modelli e senza ritocchi grafici. Rese salvate esaminate con DeckCraft 0.8.0 e WordCraft 0.8.0; Microsoft Office non era disponibile.

| Percorso | Testi nativi | Tabella | Risultato osservato |
|---|---:|---|---|
| open-slide 2.3.1 (`82349cf2d07d37b75975170503a82fcaacae9298`, archivio SHA-256 `d8183a5f2c79d517e1793bc72e65e2e0c8936e77fbd8260486de9df944d17db8`) | 73/73 | Forme e testo, non nativa | Il più vicino all'originale; differenze tipografiche e negli elenchi |
| dom-to-pptx 2.1.2 | 72/73 | Nativa | Perde la didascalia della tabella, cambia ritaglio e rotazione |
| junyuaini/html2pptx 1.1.0 | 71/73 | Nativa ma con griglia incoerente | Parole unite, duplicazioni, sfondo errato |
| WordCraft 0.8.0 (DOCX) | 73/73 | Nativa | 5 pagine a flusso, stili quasi tutti persi |
| docx/html 9.14.0 (DOCX) | 73/73 | Nativa | 7 pagine, più colori e tipografia, griglia e posizioni perse |

I conteggi misurano la presenza delle unità testuali, non la fedeltà. Per open-slide la sorgente è stata scalata uniformemente a 1920×1080 dentro un contenitore dichiarato. Il risparmio di token rispetto a una costruzione via modello non è stato misurato. Driver, log ed evidenze native restano nella cartella locale del benchmark, non versionata; questo riepilogo è il record conservato.

## Come documentare una prova o un benchmark

Un rapporto di prova identifica revisione del plugin, fonti e loro hash, richiesta, ambiente, runtime/versione e candidato. Conserva protocollo, aspettative indipendenti, risultati, difetti e verifiche assenti. Se confronta due metodi, usa gli stessi materiali e criteri e registra anche riletture, tentativi scartati, tempo e token di tutti i partecipanti.

Le misure attribuite a un progetto esterno non diventano target Office senza un confronto pertinente. Non si deduce risparmio dal numero di righe o agenti. Un caso sintetico, un confronto visivo e un uso reale hanno portate distinte.

## Fonti e direzione di sviluppo

La relazione originaria offre una direzione di prodotto e prior art ingegneristica. Non costituisce uno studio comparativo dell'efficacia complessiva di Office. Le [fonti e licenze](licenses.md) indicano i contributi conservati; i nuovi candidati seguono l'[intake esterno](upstream-intake.md). La documentazione del metodo non promette l'esito di una prova nativa o un beneficio quantitativo non misurato.
