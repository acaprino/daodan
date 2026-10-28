# Confronto meccanico HTML → PPTX e DOCX

27 ottobre 2026. **OpenSlide è il più fedele visivamente su questo campione; nessuno dei DOCX conserva la composizione originale.** Il progetto chiamato html2pptx produce difetti più gravi degli altri due esportatori PPTX.

[Apri il confronto affiancato](http://127.0.0.1:8771/). Sono disponibili tutte le pagine e i file Office effettivamente convertiti.

## PPTX: tre motori, tre slide ciascuno

| Motore | Testi nativi rilevati | Tabella | Risultato osservato |
|---|---:|---|---|
| OpenSlide 2.3.1 | 73/73 | Caselle e forme separate, senza tabella nativa | Il più vicino all’originale: colori, ritaglio, rotazione e composizione largamente conservati. Restano differenze tipografiche e negli elenchi. |
| dom-to-pptx 2.1.2 | 72/73 | Nativa, valori e celle unite corretti | Composizione riconoscibile; perde la didascalia della tabella, cambia ritaglio e rotazione, spezza alcuni testi e perde l’evidenziazione di una riga. |
| junyuaini/html2pptx 1.1.0 | 71/73 | Nativa ma con griglia incoerente e celle unite perse | Due didascalie mancanti, titoli con parole unite e parti duplicate, sfondo errato. Gli SVG sono incorporati ma DeckCraft mostra immagini rotte. |

Il conteggio PPTX misura la presenza delle unità testuali nel file, ignorando maiuscole, spazi e interruzioni di riga. **Non misura la fedeltà del testo o della grafica.** In particolare html2pptx conserva spesso le lettere ma introduce parole unite e duplicazioni, confermate negli oggetti nativi. La sua tabella dichiara due colonne mentre le righe contengono fino a cinque celle; il difetto è nel file, non soltanto nell’anteprima.

OpenSlide usa un esportatore interno, fissato a commit, con un contenitore scalato uniformemente da 1280×720 a 1920×1080. Non viene presentato come API pubblica di importazione HTML. Illustrazione e grafico diventano immagini raster; i testi restano oggetti modificabili. dom-to-pptx conserva una vera tabella. Nessun motore ricostruisce un grafico Office con i suoi dati.

## DOCX: due motori e una variante automatica

| Motore | Testi nativi | Tabella | Pagine e risultato |
|---|---:|---|---|
| WordCraft 0.8.0 | 73/73, nell’ordine originale | Nativa, valori e celle unite corretti | 5 pagine; perde quasi tutti gli stili e trasforma la composizione in flusso verticale. Anche il CSS calcolato e inserito automaticamente negli elementi produce 5 pagine, senza miglioramento sostanziale. |
| docx/html 9.14.0 | 73/73, nell’ordine originale | Nativa, valori e celle unite corretti | 7 pagine; conserva più colori e tipografia, ma perde griglia e posizioni. |

Tutti i DOCX confrontati hanno la stessa normalizzazione meccanica della pagina a 16:9 e zero margini. Le conversioni grezze sono conservate: prima della normalizzazione WordCraft dichiara 4 pagine e docx/html 6. La verifica indipendente conferma che cambiano soltanto dimensioni e margini della pagina, senza ritoccare contenuto o stile.

WordCraft perde le figure SVG come immagini; le etichette del grafico diventano testo. docx/html incorpora i due SVG con un PNG trasparente di ripiego, che non rappresenta le figure. WordCraft li mostra vuoti: questo non dimostra perdita degli SVG né identica resa in Microsoft Word. Zero avvisi da docx/html non significano conversione fedele.

## Una sorgente congelata, nessuna riparazione grafica

La sorgente contiene tre tavole di 1280×720 con griglia e flex, titoli grandi, gradienti, sovrapposizioni, PNG ritagliato, due SVG, tabella con celle unite, testo lungo e simboli italiani. Marca e dati sono fittizi. Tutti i motori leggono gli stessi byte dell’HTML.

SHA-256 HTML: `cb1ba3e3d1faa6c832ebc0189ca8bba59bbebeb60695a20bd90cb7a884d71d1d`.

Sono dichiarati gli adattamenti automatici necessari: selezione delle tavole, scala uniforme OpenSlide, risoluzione delle immagini e normalizzazione pagina DOCX. La variante WordCraft con CSS inline è distinta dalla sorgente grezza. Nessun file convertito riceve correzioni grafiche manuali.

Il confronto contiene 9 slide PPTX e 17 pagine DOCX renderizzate dai file salvati, oltre alle tre immagini originali del browser. Ispezione visiva e controllo indipendente del contenuto nativo sono verifiche separate. I file XML parsabili e gli archivi integri non provano da soli conformità completa allo standard o apertura senza errori in Microsoft Office.

## Tempi, token e limiti

Le singole esecuzioni misurano circa 21,39 s per dom-to-pptx, 38,42 s per OpenSlide e 10,30 s per html2pptx; WordCraft 0,11 s, docx/html 1,15 s, WordCraft con CSS inline 0,25 s. **Non sono una classifica di velocità:** html2pptx comprende tre avvii browser e immagini di controllo; gli altri confini di misura differiscono. Installazione, preparazione, rendering e revisione non sono inclusi; la preparazione CSS inline è esclusa dal relativo tempo.

La conversione è meccanica e non invoca modelli. Il costo complessivo in token della preparazione e della verifica esiste; il risparmio rispetto a una generazione LLM equivalente non è misurato. Non viene dichiarata una percentuale di risparmio.

Anteprime PPTX: DeckCraft 0.8.0. Anteprime DOCX: WordCraft 0.8.0. Microsoft Word e PowerPoint non sono installati: la fedeltà delle loro applicazioni resta da verificare. Le osservazioni sugli SVG vuoti o rotti mantengono questa distinzione; difetti testuali e della tabella rilevati nei file sono invece confermati strutturalmente.

Repository, versioni fissate, licenze, lock e provenienze sono documentati in `dependencies.md` e nei rapporti dei singoli motori. I driver riproducibili, i log e le evidenze native restano nella cartella del benchmark. La revisione indipendente è conservata nel run del confronto.

Questo esperimento non modifica il plugin Office e non adotta alcun motore. Per questo HTML, OpenSlide offre il miglior risultato visivo PPTX con il limite della tabella; il problema della conversione grafica DOCX rimane aperto.
