# Struttura e responsabilità del plugin

[Indice Office](../office.md) · [Percorso del lavoro](workflow.md) · [Dipendenze](dependencies.md)

Il kernel `plugins/office/` contiene metodi, ruoli e helper. Gli ingressi utente appartengono al plugin `daodan`; Office non dichiara workflow propri. I pacchetti dei cinque host sono generati dal kernel e dagli adapter.

## Dove si trova ogni parte

| Percorso | Responsabilità |
|---|---|
| `plugin.toml` | Identità, versione, licenza, dipendenze, capacità e componenti registrati |
| `skills/` | Metodi e risorse operative, comprese reference, script e notice |
| `roles/` | Mandati degli specialisti di contenuto, composizione e review |
| `plugins/daodan/workflows/` | Ingressi come `start`, `document` e `presentation` che caricano Office |
| `docs/plugins/office.md` e `docs/plugins/office/` | Indice e documentazione per utenti e manutentori |

Il [README del kernel](../../../plugins/office/README.md) conserva un indice tecnico di provenienza. Non sostituisce i metodi, le licenze distribuite o queste guide. Le risorse necessarie durante l'esecuzione devono vivere sotto una skill, dove il compilatore le include nei pacchetti.

## Le decisioni hanno proprietari distinti

| Area | Componente | Decisione posseduta |
|---|---|---|
| Richiesta | `intake` | Operazione, materiali, vincoli, decisioni ereditate e dipendenze |
| Contenuto | `content` | Fatti, strategia editoriale, sequenza e trasformazioni in `CONTENT.md` |
| Design | `design` | Identità visiva condivisa, proposte e `DESIGN.md` |
| Formati | `docx`, `pptx`, `xlsx` | Struttura del formato, composizione e coordinamento della consegna |
| Produzione e integrità | `wordcraft`, `deckcraft`, `gridcraft`, `integrity` | Operazioni native supportate, preservazione e controlli pertinenti |

Il tema condiviso non stabilisce la geometria di ogni pagina o slide. Un designer può redistribuire il contenuto; una modifica del suo significato o delle priorità torna al proprietario editoriale. I produttori applicano il piano alle capacità effettive del runtime.

## I cinque ruoli

| Ruolo | Consegna |
|---|---|
| `content-strategist` | Record editoriale e proiezioni richieste, senza scegliere il tema o modificare il file nativo |
| `document-designer` | Composizione Word, stili, flusso e regole di crescita |
| `presentation-designer` | Composizione delle slide, pattern e geometrie degli oggetti |
| `document-reviewer` | Verifica indipendente del candidato Word e delle prove di preservazione |
| `presentation-reviewer` | Verifica indipendente del candidato PowerPoint e delle prove di modificabilità |

Il coordinatore costruisce e verifica il risultato, raccoglie le consegne e mantiene lo stato del lavoro. Un ruolo non crea automaticamente un nuovo coordinatore o una seconda pipeline.

Gli stessi designer e reviewer lavorano in modalità `proposal` sulle alternative non selezionate e in modalità `final` sul risultato scelto. `design` integra Taste v2 attraverso una sola [reference di input e output](../../../plugins/office/skills/design/references/art-direction.md): il provider contribuisce idee e critica, mentre contenuto, geometrie native, scelta e consegna restano agli owner Office. Anche `theme` dichiara questi ruoli e verifica campioni nativi.

## Reference simmetriche, composizioni diverse

DOCX e PPTX usano nomi funzionali analoghi nelle proprie cartelle:

| Reference | DOCX | PPTX |
|---|---|---|
| `structure.md` | Tipi di documento, sezioni e convenzioni dei titoli | Modalità espositive, sequenza e headline |
| `content-planning.md` | Proiezione delle unità in sezioni | Proiezione nel plan slide esistente |
| `layout-patterns.md` | Pagine, blocchi, flusso, stili e crescita | Pattern, slot, geometrie e ritmo |

Questa simmetria facilita la navigazione. I file mantengono contenuti propri: un rapporto Word e un deck richiedono densità, navigazione e verifiche differenti.

## Confine con gli host

I componenti restano neutrali; gli adapter stabiliscono nomi, percorsi e meccanismi dell'host. Il [riferimento generato nell'indice](../office.md#source-derived-reference) elenca i componenti e le dipendenze senza duplicare il manifest a mano. Consultare anche [host e distribuzione](../../hosts.md).

La compilazione di un pacchetto prova la sua coerenza strutturale. L'esecuzione installata, l'isolamento dei worker e la disponibilità dei runtime richiedono evidenze separate.

## Fonti

[Manifest Office](../../../plugins/office/plugin.toml), [ruoli](../../../plugins/office/roles/), [struttura DOCX](../../../plugins/office/skills/docx/references/structure.md) e [struttura PPTX](../../../plugins/office/skills/pptx/references/structure.md).
