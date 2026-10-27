# Licenze e provenienza

Consultare l'[indice delle fonti Office](../../../plugins/office/README.md#sources-pins-and-licenses) per collegare ogni contributo ai suoi termini e alla revisione ispezionata. I pin restano in quell'indice e nei record di provenienza, senza una seconda tabella da sincronizzare qui.

[Torna alla guida Office](../office.md).

## Licenza locale e materiale di terzi

Il [manifest Office](../../../plugins/office/plugin.toml) dichiara MIT; il [LICENSE del repository](../../../LICENSE) conserva il testo MIT e il copyright locale. Il README precisa che questa licenza non sostituisce i termini degli adattamenti esterni.

La [skill design](../../../plugins/office/skills/design/SKILL.md) conserva `license: Apache-2.0` e attribuisce i materiali adattati Agentit e Theme Factory. La dichiarazione MIT del plugin non elimina tale indicazione o le notice distribuite insieme alle guide.

Le informazioni sotto descrivono i record e i testi conservati nel repository. Non attestano termini o release correnti di siti esterni e non formulano un'interpretazione legale delle licenze.

## Contributi conservati

| Contributo | Record locale | Termini conservati e confine |
|---|---|---|
| Guide editoriali e tipografiche Agentit | [agentit-upstream.md](../../../plugins/office/skills/design/references/agentit-upstream.md) | [Apache-2.0](../../../plugins/office/skills/design/references/LICENSE-APACHE-2.0.txt), con modifiche Office dichiarate e lineage MIT conservato. Il perimetro è la coppia di guide, non l'harness Agentit. |
| Lineage RampStack e Peter Bamuhigire | Lo stesso record Agentit identifica fonti, revisioni e contributi | Testi integrali [RampStack MIT](../../../plugins/office/skills/design/references/LICENSE-rampstackco-MIT.txt) e [Peter Bamuhigire MIT](../../../plugins/office/skills/design/references/LICENSE-peterbamuhigire-MIT.txt), con i rispettivi copyright. |
| Seed Theme Factory | [theme-factory-upstream.md](../../../plugins/office/skills/design/references/theme-factory-upstream.md) | [Termini Apache-2.0 e notice conservati](../../../plugins/office/skills/design/references/LICENSE-theme-factory-APACHE-2.0.txt). Restano quattro palette nelle direzioni Q–T; skill, preset e showcase precedenti sono ritirati. |
| Sketch PPT Visual | [Provenienza dei layout PPTX](../../../plugins/office/skills/pptx/references/layout-patterns.md#provenance) | [MIT integrale](../../../plugins/office/skills/pptx/references/LICENSE-ppt-visual-MIT.txt), copyright Claude Office Skills Contributors. L'adattamento riguarda sketch e handoff alla specifica. |
| Motore di conversione open-slide | [UPSTREAM.md](../../../plugins/office/skills/pptx/lib/open-slide-pptx/UPSTREAM.md) con pin, hash e protocollo di refresh | [MIT, Copyright (c) 2026 Yiwei Ho](../../../plugins/office/skills/pptx/lib/open-slide-pptx/LICENSE-open-slide-MIT.txt), più le notice di [fflate](../../../plugins/office/skills/pptx/lib/open-slide-pptx/LICENSE-fflate-MIT.txt) e [html-to-image](../../../plugins/office/skills/pptx/lib/open-slide-pptx/LICENSE-html-to-image-MIT.txt) incluse nel bundle. Undici file copiati byte per byte sotto autorizzazione scoped del proprietario; entry, driver, rebuild e bridge sono codice Office. |

Il record Agentit conserva anche gli hash delle due fonti prima dell'adattamento e descrive le modifiche per stili Word, canvas PPTX, font, immagini e review. Il README è l'indice visibile; i testi completi e le attribuzioni restano presso i file distribuiti sotto le skill.

La sezione storica del record Theme Factory conserva dettagli della precedente importazione. La nota di ritiro iniziale definisce ciò che rimane distribuito; i riferimenti storici a preset e PDF non ne provano la presenza attuale.

## Provider esterno, ispirazione originale e candidati

Taste v2 è una dipendenza esplicita per direzione artistica e critica, installata separatamente. L'[indice delle fonti](../../../plugins/office/README.md#sources-pins-and-licenses) conserva versione, revisione esaminata e link ai termini MIT completi. Office non ne ridistribuisce testo, codice o asset. Il [bridge](../../../plugins/office/skills/design/references/art-direction.md) delimita l'uso della conoscenza; identità e risorse installate si verificano sull'host attivo.

La [provenienza DOCX](../../../plugins/office/skills/docx/references/layout-patterns.md#provenance) dichiara guida locale originale informata da `tivojn/Office`. Registra che i README della fonte indicavano MIT, mentre mancavano testo completo e copyright nella repository ispezionata. Nessun testo, codice, preset numerico, template, asset o font upstream è redistribuito da quella reference. Non è un target di sincronizzazione di copie.

PPT Design resta un candidato. Le dichiarazioni della relazione originale (§11) restano attribuite a quella ricerca, senza una nuova verifica dei termini in questa guida. Il precedente record di valutazione Taste è storico; la dipendenza dichiarata e il bridge definiscono l'uso adottato.

Il divieto di nuove copie vendorizzate resta applicabile anche a materiale con licenza permissiva. L'unica deroga in vigore riguarda il motore di conversione open-slide, autorizzata in modo esplicito e delimitato dal proprietario il 2026-10-27: undici file a un pin preciso, notice conservate, hash di controllo e nessuna estensione all'applicazione upstream o ad altre fonti. Per una nuova capacità vedere [intake esterno](upstream-intake.md); per gli adattamenti già registrati vedere [aggiornamenti](upstream-updates.md).

## Runtime, font e asset

WordCraft, DeckCraft e GridCraft sono runtime forniti separatamente. Il README li distingue dagli adattamenti copiati: Office non distribuisce i loro motori. Il motore di conversione HTML→PPTX è invece distribuito dentro il plugin: pin, notice e protocollo stanno nella tabella dei contributi conservati. I [contratti delle dipendenze](dependencies.md) guidano la scoperta di versione e capacità; la licenza Office non sostituisce i termini del runtime fornito.

Le [regole tipografiche locali](../../../plugins/office/skills/design/references/typography.md#establish-constraints) richiedono verifica di famiglia, versione, pesi reali, glifi e uso consentito nell'output previsto. Un nome nel catalogo o un font visibile in un PDF non prova installazione, incorporabilità o diritto di redistribuzione.

La [skill design](../../../plugins/office/skills/design/SKILL.md#fonts-and-final-file-evidence) richiede controllo di licenze e permessi di incorporamento prima della costruzione. Gli helper e il loro esito vanno verificati nel lavoro concreto; una flag richiesta non dimostra che il font sia entrato nella copia consegnata. Font installati e asset ricevuti conservano i propri termini: il brief e i record delle [dipendenze](dependencies.md) devono rendere visibili disponibilità, autorità d'uso e limiti pertinenti.

## Conservazione durante la manutenzione

La [policy canonica di intake](../../../.claude/skills/external-repo-intake/SKILL.md#3-license-compliance-gate), la [procedura di sync](../../../.claude/skills/upstream-sync/SKILL.md) e i record locali definiscono i controlli da applicare nel perimetro autorizzato:

1. Conservare header di attribuzione, copyright, testi completi e notice associati al materiale distribuito.
2. Conservare revisione, percorso di origine, destinazione, modalità di adozione e modifiche locali; per Agentit riesaminare anche il lineage secondario prima di avanzare il pin.
3. Leggere termini e notice della revisione proposta, senza trasformare una licenza dichiarata o incompleta in autorizzazione a copiare.
4. Mantenere i testi necessari sotto le skill che distribuiscono il materiale; rigenerare i pacchetti quando cambia il kernel e verificarne i percorsi inclusi.
5. Registrare controlli eseguiti e limiti. Un elenco di licenze, una validazione di record o una compilazione riuscita non attestano l'esecuzione dei runtime o la resa dei file Office.

Questa pagina indicizza la provenienza conservata. Le decisioni operative seguono la policy canonica e l'autorizzazione del lavoro concreto.
