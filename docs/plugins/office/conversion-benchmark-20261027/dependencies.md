# Dipendenze del confronto

Esperimento locale del 27 ottobre 2026. Nessuna di queste prove aggiunge una dipendenza al plugin Office. Le installazioni temporanee sono sotto `runtime/`; il lock effettivo è conservato in `runtime-records/shared-package-lock.json`.

| Componente | Versione usata | Repository ufficiale | Licenza dichiarata | Ruolo |
|---|---|---|---|---|
| dom-to-pptx | 2.1.2 | [atharva9167j/dom-to-pptx](https://github.com/atharva9167j/dom-to-pptx) | MIT | Conversione del DOM in PPTX |
| OpenSlide core | 2.3.1; sorgente `82349cf2d07d37b75975170503a82fcaacae9298` | [open-slide/open-slide](https://github.com/open-slide/open-slide/tree/82349cf2d07d37b75975170503a82fcaacae9298) | MIT del repository | Esportatore interno DOM → scena → OOXML, con adattatore sperimentale |
| html2pptx | 1.1.0; commit `e52aeaa223d8fe47534a6e9f70accd384022600c` | [junyuaini/html2pptx](https://github.com/junyuaini/html2pptx/tree/e52aeaa223d8fe47534a6e9f70accd384022600c) | MIT | Terza conversione PPTX meccanica, aggiunta su richiesta; sorgente fissata al commit ufficiale |
| docx, modulo HTML | 9.14.0 | [dolanmiu/docx](https://github.com/dolanmiu/docx) | MIT | Conversione semantica HTML in DOCX |
| WordCraft | 0.8.0 installata | [storytold/wordcraft](https://github.com/storytold/wordcraft/tree/v0.8.0) | MIT oppure Apache-2.0; [testo MIT della versione](https://github.com/storytold/wordcraft/blob/v0.8.0/LICENSE-MIT) | Conversione HTML e rendering dei DOCX salvati |
| DeckCraft | 0.8.0 installata | [storytold/deckcraft](https://github.com/storytold/deckcraft) | MIT oppure Apache-2.0 dichiarata dal progetto; [riferimento conservato](https://github.com/storytold/deckcraft/blob/v0.10.0/LICENSE-MIT) | Rendering dei PPTX salvati |

## Strumenti e materiali

Node 24.14.1, npm 11.11.0; Vite 8.3.3 come strumento per il caricamento dei moduli nel browser. Playwright 1.62.1 dal runtime Codex disponibile. Chrome installato sul sistema; versione effettiva in `outputs/reference/browser-reference.json` e nei rapporti di conversione. Vite è MIT, Playwright Apache-2.0; Chrome ha i propri termini di distribuzione.

Le licenze principali disponibili nei pacchetti sono copiate in `runtime-records/licenses/`. Le dipendenze transitive, con versioni e integrità, restano nel lock; questa prova non costituisce un audit completo delle licenze transitive. In particolare la provenienza secondaria del WASM WOFF2 incluso da dom-to-pptx resta da verificare prima di un’eventuale adozione. L’eventuale uso di moduli interni OpenSlide richiede ulteriore manutenzione rispetto a un’API pubblica stabile.

L’HTML usa caratteri di sistema Arial, Arial Black e Georgia: nessun file font viene scaricato o redistribuito dalla sorgente. Il PNG è una copia immutata del marchio del progetto Daodan, riutilizzata nel campione autorizzato; il manifest conserva origine e hash. SVG, testi e dati del campione sono creati per il test. Darsena è una marca fittizia.

## Riproducibilità e limiti

Le installazioni npm hanno escluso script automatici e download di browser. La sorgente OpenSlide è un archivio ufficiale fissato a commit; hash dell’archivio ed esclusioni dei soli collegamenti simbolici sono in `runtime-records/openslide-source.json`. L’implementazione dell’esportatore non viene modificata.

I driver e i log registrano gli adattamenti meccanici richiesti dai formati: selezione delle tre tavole, dimensioni pagina, risoluzione delle immagini locali ed eventuale scala uniforme. Ogni variante derivata viene distinta dall’HTML grezzo. Non vengono applicate correzioni grafiche manuali ai file convertiti.

Word e PowerPoint Microsoft non sono disponibili. Il confronto visivo usa i renderer dichiarati e non prova la resa delle applicazioni Microsoft. Non viene dichiarata una percentuale di risparmio di token senza una baseline equivalente misurata.
