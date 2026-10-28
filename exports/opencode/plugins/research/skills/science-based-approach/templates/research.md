<daodan_host_binding host="opencode">
This binding governs execution of this package and its loaded references. It takes
precedence over executable examples written for another host. Use only registered
tools and their actual input schema; an example never creates a tool, argument,
permission, model alias or nested worker capability. Preserve the generated worker
allowlist, dependency closure, scope and delivery contracts.

Bodies name operations, never tools: repository read, file discovery, content
search, repository write, repository edit, shell execution, network fetch, network
search, user question and worker dispatch. The host binding below maps each one to
a registered tool. An operation it leaves unbound, or whose tool is absent from
this session, is unavailable: report it as missing, never search for a tool named
after the operation.

OpenCode V2 binding: repository reads use read/glob/grep, writes use write/edit/patch,
shell execution uses shell, network fetch uses webfetch, network search uses
websearch, and a user question uses the registered question tool. shell takes command, optional workdir, timeout
in milliseconds and background. It does not provide interactive stdin. Persistent
capture uses background: true and an explicit noninteractive stop signal.
Load skills with skill using id: "<plugin>:<skill>". Dispatch registered roles with
subagent using agent: "<owner>:<role>", description and prompt; optional sessionID
continues that child, and background: true requests asynchronous completion.
Use only roles allowed by the current harness and permissions. A child cannot
dispatch nested workers when its permissions or the configured depth deny it.
Workflow entries are /<plugin>:<workflow>, registered by the package loader.
Inherit the session model; an override requires its authorized, actually available
provider/model identity, not another host's short model alias.
The loader includes required local providers and registers plugin-declared MCP
servers. Qualified foreign providers need a compatible V2 plugin/skill provisioned
through this host, never a Claude marketplace command. Check the active registry:
registration metadata alone does not prove a connected server or usable tool.
Inherit the active session's model and default variant. A source model alias such
as sonnet is not a portable override; request a different model only through an
explicit adapter mapping to a valid host identity and user authorization.

The executing agent and its coordinator own continuation, recovery, verification
and delivery. Skills supply knowledge and method instructions; they are not
executors or a runtime persistence mechanism.

Resolve each component by kind and exact installed identity. A role is dispatched
as a worker, a skill loads instructions, and a workflow starts its declared method.
Kernel owner-qualified skill references are logical provider identities: resolve
them to the actual host registry name and verified installed provider path. Do not
invent a registry string by adding an owner's prefix when the host does not use it.
Do not load an agent identity as a skill or execute a workflow name as a shell
command. Declared required foreign providers remain mandatory. If a required
provider or capability (including required MCP access or isolation) is unavailable,
stop its dependent phase and report the missing capability. Optional external
providers follow the method's declared selection and absence behavior; their
absence alone does not block the base workflow. Report any explicitly requested
but unavailable provider contribution as unfulfilled and continue independent
work. Do not install a different host's plugin or
substitute unrelated skills to claim coverage.

Shell execution alone does not establish interactive stdin. Before a capture or
checkpoint, use an available session-control mechanism. When stdin is unavailable,
keep user-driven capture in a supported background process with bounded output and
an explicit stop signal controlled by the coordinator after the user's completion
message. Close owned browser/process resources on completion or cancellation.

Continue working within the current authorization while the requested result is
achievable. After a tool error, inspect its cause, correct the relevant input or
implementation, retry when justified and verify the outcome; never repeat a
failing action blindly. Do not close the turn with a promise or a partial result
when an authorized next step can still produce or verify the requested result.
Stop only for a documented real impediment, a missing required capability, an
unresolved human decision or the caller's stop request. At that boundary, report
completed results, remaining work and the concrete prerequisite for continuation;
continue any independent work that the blocker does not prevent.

A tool's successful exit, a worker stop or an idle session is not the deliverable.
Return final text naming observed findings, artifact paths, executed checks and
blockers. An empty worker result is missing delivery: inspect or resume that worker
when permitted, or record failure. Verify required artifacts and candidate gates
before marking the requested outcome complete.

This is an execution binding, not a rewrite of source examples. Preserve programming
language fences, domain code and host APIs that are the subject of marketplace-ops
or agent-sdk-builder. A host-as-subject API is not a tool provided to this session.
Compiled binding and static checks do not prove an installed host executed a run.
</daodan_host_binding>

# Template della ricerca scientifica

Template canonico distribuito con science-based-approach.
Compilare solo dati effettivamente osservati. I segnaposto qui sotto non sono
risultati. Cercare prima documenti affini e aggiornare lo stesso Markdown
corrente; non creare un'altra pagina per una nuova conversazione sul tema.
Le revisioni immutabili restano nello storico separato. La pagina corrente
mostra il testo completo e i dati dell'ultimo controllo.

---

# «Titolo della ricerca»

| Campo | Valore |
|---|---|
| Identità / revisione | «ID stabile» / «r0001» |
| Temi | «algoritmi, dominio, tecnologie pertinenti» |
| Proprietario / destinazione | «owner e percorso canonico» |
| Contesto e richiesta | «problema, compito, specifica/ADR/FRD che hanno motivato la ricerca» |
| Domanda | «domanda concreta a cui rispondere» |
| Creazione | «data e ora ISO 8601 con offset; fuso IANA» |
| Esecuzione della ricerca / aggiornamento | «data e ora ISO 8601 con offset» |
| Ultimo aggiornamento sostanziale | «data e ora ISO 8601 con offset» |
| Controllo alla pubblicazione | «ID ricevuta, data/ora, esito, copertura» |
| Stato alla pubblicazione | «corrente / da riesaminare / superata, con motivo» |
| Precedente / sostituisce | «link e revisione; nessuna alla prima pubblicazione» |
| Stato e controlli successivi | «link al README corrente e alle ricevute» |

## TL;DR

«Risposta alla domanda, scelta suggerita, condizioni di applicabilità, solidità
delle evidenze e principale limite. Poche frasi autosufficienti, con riferimenti
alle conclusioni C-... e senza introdurre affermazioni assenti nel documento.»

## Contesto e metodo

«Perché è stata svolta la ricerca; destinatari; decisione supportata; vincoli;
tecnologia/versione; ambito incluso/escluso; criteri di selezione delle fonti;
budget previsto/usato; motivo per cui la ricerca si è fermata.»

| Query / domanda | Sito e filtri | Data e ora | Esito e selezione/esclusione | Limiti |
|---|---|---|---|---|
| «query priva di dati riservati» | «sito, periodo, filtri» | «timestamp» | «paper selezionati o motivo di esclusione» | «accesso, copertura» |

## Paper di riferimento

Una riga per lavoro, con versioni correlate identificate; espandere in una scheda
breve se la tabella diventa illeggibile. Le fonti soltanto scoperte o inaccessibili
restano riconoscibili e non sostengono conclusioni oltre quanto effettivamente letto.

| ID | Autori, titolo, anno e sede | DOI / URL primario e versione | Lettura | Sinossi e risultato pertinente | Limiti / avvisi |
|---|---|---|---|---|---|
| P-001 | «autori; titolo; anno; sede; preprint/pubblicazione» | «identità; link; versione; data accesso» | «full-text / selected-sections / abstract-only / metadata-only / unavailable; sezioni» | «domanda, metodo e contributo in poche frasi» | «limiti; avviso editoriale con fonte/data oppure controllo limitato senza avvisi trovati» |

Documentazione tecnica e standard eventualmente usati vanno in una tabella
separata, con identità D-..., versione e fatti supportati. Non etichettarli come paper.

## Sintesi ragionata

Quando una conclusione diventa obsoleta, conservare il passaggio interessato
visibilmente barrato, per esempio «~~conclusione precedente~~», e affiancare
sostituzione, motivo, fonte e data. Non lasciare una tesi superata nella sintesi
corrente come se fosse ancora valida. Non barrare indiscriminatamente il documento.

«Spiegare il tema nell'ordine utile alla decisione: concetti necessari, risultati,
confronto delle alternative e conseguenze nel progetto. Citare P-... con pagina,
sezione o tabella. Esplicitare le inferenze. Conservare risultati contrari e
distinguere condizioni non comparabili. Collegare gli approfondimenti lunghi.»

| Conclusione | Fonti e localizzatori | Tipo di supporto e confidenza motivata | Controevidenze / limiti | Applicabilità |
|---|---|---|---|---|
| C-001: «affermazione circoscritta» | «P-001, sezione/pagina; D-... se pertinente» | «teorico/empirico/documentale; alta/media/bassa e ragione» | «fonti contrarie o ricerca eseguita senza evidenze trovate» | «condizioni, tecnologia/versione; applicabile/da rivalutare/non applicabile» |

## Verifica locale

Se non serve un esperimento o non è eseguibile, spiegare il motivo e ciò che
resta non verificato. Non compilare risultati attesi come misure osservate.

| Campo | Esperimento E-001 |
|---|---|
| Ipotesi e conclusioni coinvolte | «ipotesi falsificabile; C-...» |
| Confronto e dati | «baseline; casi/dataset, provenienza, versione e limiti» |
| Metrica e criterio fissato prima del test | «metrica, unità, soglia o confronto; motivazione» |
| Procedura riproducibile | «comando o procedura; link al protocollo» |
| Ambiente | «codice/revisione, software/versioni, hardware se rilevante, seed se usato» |
| Stato ed esecuzione | «planned / executed / not-run; data/ora e tentativo; motivo se non eseguito» |
| Risultato osservato | «misure, variabilità pertinente; sostenuta/non sostenuta/inconcludente; nessun valore se non eseguito» |
| Artefatti e limiti | «log/dati consentiti, identità o hash, riproduzione, limiti di generalizzazione» |

## Decisioni supportate e impatto

| Documento / compito | Revisione e conclusioni usate | Conseguenza | Azione da valutare |
|---|---|---|---|
| «link a specifica, ADR, FRD o test» | «ricerca rN; C-...» | «scelta o ipotesi supportata» | «nessuna / riesame / test da rieseguire, con motivo» |

«Distinguere la raccomandazione della ricerca da una decisione approvata.
Indicare la copertura dei consumatori conosciuti e gli eventuali riferimenti
non verificati. Non modificare automaticamente record accettati.»

## Changelog delle revisioni

| Revisione | Data e ora | Motivo e fonte dell'aggiornamento | Conclusioni cambiate | Impatto e verifica |
|---|---|---|---|---|
| «r0001» | «timestamp» | «prima ricerca; fonti» | «C-...» | «documenti coinvolti; esperimenti eseguiti/da eseguire» |

«Alle revisioni successive conservare le righe precedenti. Un superamento
identifica ambito, motivo e collegamento alla revisione/fonte sostitutiva.
Il solo passare del tempo non costituisce una smentita.»

## Cronologia dei controlli e limiti aperti

«Collegare le ricevute disponibili alla pubblicazione e l'indice corrente dei
controlli successivi. Dichiarare quesiti irrisolti, fonti non accessibili e
condizioni che richiederebbero un nuovo controllo.»

---

## Modello della ricevuta di controllo

Questa sezione è un secondo modello: ogni esecuzione la compila in un file
`checks/«check-id».md`; non aggiunge controlli futuri a una revisione immutabile.

| Campo | Valore |
|---|---|
| Controllo / ricerca / revisione esaminata | «ID controllo; ID ricerca; rN e digest iniziale» |
| Inizio / fine / fuso | «timestamp ISO 8601 con offset; IANA» |
| Origine | «comando esplicito oppure workflow/fase; identità del compito» |
| Contesto esaminato | «domanda, tecnologie/versioni e cambiamenti pertinenti» |
| Copertura | «fonti, query, versioni e avvisi realmente controllati; link alle prove» |
| Esito | «completed-no-change / completed-with-change / partial / failed / cancelled» |
| Limiti | «fonti non controllate, accessi mancanti, interruzione, budget» |
| Variazioni e impatto | «conclusioni, avvisi, consumatori e verifiche locali coinvolti» |
| Revisione risultante | «rN invariata oppure link a rN+1 pubblicata; nessuna pubblicazione se fallita» |

Il README corrente deriva dalle ricevute l'ultimo tentativo e l'ultimo controllo
completo riuscito, separandoli dall'ultimo aggiornamento sostanziale. I controlli
senza novità e quelli falliti rimangono nella cronologia con il proprio esito.
